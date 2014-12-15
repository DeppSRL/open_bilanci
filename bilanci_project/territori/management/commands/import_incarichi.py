# -*- coding: utf-8 -*-
from django.conf import settings
import logging
from optparse import make_option
from django.core.exceptions import ObjectDoesNotExist
from django.core.management import BaseCommand
import re
import requests
from datetime import datetime
from unidecode import unidecode
from bilanci.utils.comuni import FLMapper
from territori.models import Territorio, Incarico

__author__ = 'stefano'


class Command(BaseCommand):


    #     sets the start / end of graphs
    timeline_start = settings.APP_START_DATE
    timeline_end = settings.APP_END_DATE
    date_fmt = '%Y-%m-%d'
    apidomain = None
    max_n_days_incarico_length = 1826

    # determines max n.days between charges without being logged as error
    max_n_days_charges_discontinuty = 60

    # determines max n.days between commissari charges to be united as a unique charge
    max_n_days_between_commissari = max_n_days_charges_discontinuty

    overlapping_dict = {}
    incarichi_longer_5yrs = []
    baseurl = None
    # territori with charges discontinuity longer than max discontinuity lenght
    territori_discontinuity = []

    accepted_types = ['all', 'capoluoghi', 'others']
    logger = logging.getLogger('management')
    comuni_dicts = {}

    option_list = BaseCommand.option_list + (

        make_option('--territori-type',
                    dest='territori_type',
                    action='store',
                    default='',
                    help='Type of Territorio: ' + ' | '.join(accepted_types)),
        make_option('--cities',
                    dest='cities',
                    default='',
                    help='Cities codes or slugs. Use comma to separate values: Roma,Napoli,Torino or  "All"'),
        make_option('--dry-run',
                    dest='dryrun',
                    action='store_true',
                    default=False,
                    help='Set the dry-run command mode: nothing is written on db'),
        make_option('--auth',
                    dest='auth',
                    default='',
                    help='Auth, as user,pass. Separated by a comma, no space.'),
        make_option('--api-domain',
                    dest='apidomain',
                    default='api3.openpolis.it',
                    help='The domain of the API. Defaults to api3.openpolis.it'),
        make_option('--delete',
                    dest='delete',
                    action='store_true',
                    default=False,
                    help='Deletes all current charges before import'),

    )

    help = 'Import political charges for Territori into Postgres db'

    def convert_to_date(self, date_string):
        return datetime.strptime(date_string, self.date_fmt)

    def format_incarico(self, incarico_dict):

        date_start = datetime.strftime(incarico_dict['date_start'], self.date_fmt)
        date_end = None
        if incarico_dict['date_end']:
            date_end = datetime.strftime(incarico_dict['date_end'], self.date_fmt)

        opid = re.search(r'^.*/([0-9]+)$', incarico_dict['op_link']).groups()[0]

        return "{0}.{1} - {2} ({3} - {4})". \
            format(
                unidecode(incarico_dict['first_name'][0].title()),
                unidecode(incarico_dict['last_name'].title()),
                opid,
                date_start,
                date_end
            )
    def get_territori_from_finloc(self, cities_finloc):
        return Territorio.objects.filter(cod_finloc__in=cities_finloc, territorio="C").order_by('-cluster')

    def get_territori_from_types(self, territori_type):

        if territori_type not in self.accepted_types:
            self.logger.error(
                "Territori type not accepted. Choose between:{0},{1},{2}".
                format(self.accepted_types[0], self.accepted_types[1], self.accepted_types[2]))
            return

        # prende tutte le citta' capoluogo di provincia
        capoluoghi_provincia = Territorio.objects.\
                                    filter(slug__in=settings.CAPOLUOGHI_PROVINCIA).\
                                    order_by('-cluster', 'denominazione')
        altri_territori = list(
            Territorio.objects.filter(territorio=Territorio.TERRITORIO.C).
            exclude(id__in=capoluoghi_provincia).
            order_by('-cluster', 'denominazione'))

        # depending on the territori_type value runs the import only for capoluoghi di provincia or for all Territori
        # prioritize the territori list getting first the capoluoghi di provincia and then all the rest

        if territori_type == 'others':
            return altri_territori

        elif territori_type == 'capoluoghi':
            return capoluoghi_provincia

        elif territori_type == 'all':
            all_cities = capoluoghi_provincia[:]
            all_cities.extend(altri_territori)
            return all_cities

    def get_incarichi_api(self, territorio_opid):

        # get incarichi from politici/city_mayors for the considered time period

        api_request = requests.get(
            "{0}/politici/city_mayors/{1}?date_from={2}&date_to={3}". \
                format(self.baseurl, territorio_opid, self.timeline_start.date(), self.timeline_end.date()))
        api_results_json = api_request.json()

        if 'sindaci' not in api_results_json:
            return []

        for incarico in api_results_json['sindaci']:
            incarico['date_start'] = self.convert_to_date(incarico['date_start'])

            if incarico['date_end']:
                incarico['date_end'] = self.convert_to_date(incarico['date_end'])

        # return charges ordered by date start
        return sorted(api_results_json['sindaci'], key=lambda k: k['date_start'])

    def date_integrity_check(self, incarichi_set):

        # check & log if incarico.lenght > 5 yrs
        # check & log if timespan between incarico1 and incarico2 > 60days

        added_ids = []
        for idx, incarico in enumerate(incarichi_set):

            if incarico['date_end']:
                diff = ( incarico['date_end'] - incarico['date_start']).days
                if diff > self.max_n_days_incarico_length:
                    self.incarichi_longer_5yrs.append(incarico)

            if idx < len(incarichi_set) - 1 and incarico['date_start'] and incarico['date_end']:
                diff_next = (incarichi_set[idx + 1]['date_start'] - incarico['date_end']).days
                if diff_next > self.max_n_days_charges_discontinuty:
                    if idx not in added_ids and idx + 1 not in added_ids:
                        self.territori_discontinuity.append(
                            {'incarico_1': incarichi_set[idx + 1], 'incarico_2': incarico, 'diff': diff_next})
                        added_ids.append(idx)
                        added_ids.append(idx + 1)

            if idx > 0:
                if incarichi_set[idx - 1]['date_end']:
                    diff_previous = (incarico['date_start'] - incarichi_set[idx - 1]['date_end']).days
                    if diff_previous > self.max_n_days_charges_discontinuty:

                        if idx not in added_ids and idx - 1 not in added_ids:
                            self.territori_discontinuity.append(
                                {'incarico_1': incarico, 'incarico_2': incarichi_set[idx - 1], 'diff': diff_previous})
                            added_ids.append(idx)
                            added_ids.append(idx - 1)

    def check_overlapping_incarichi(self, incarichi_set):

        """
        Incarichi check checks that incarichi for a given Comune are not overlapping

        Return a tuple (Bool, incarichi_set)

        if bool is True: incarichi_set is a list of interesting incarichi for the considered timespan
        if bool is False: incarichi_set is a list of tuples of overlapping incarichi for the considered timespan

        """

        overlapping_incarichi = []

        # checks if interesting_incarichi are overlapping
        # if incarichi are overlapping, appends them in the overlapping_incarichi list
        for incarico_considered in incarichi_set:
            considered_start = incarico_considered['date_start']
            considered_end = incarico_considered['date_end']

            for incarico_inner in incarichi_set:
                if incarico_inner is not incarico_considered:
                    inner_start = incarico_inner['date_start']
                    inner_end = incarico_inner['date_end']

                    if inner_end:
                        if inner_start < considered_start < inner_end:

                            if (incarico_inner, incarico_considered) not in overlapping_incarichi and \
                                            (incarico_considered, incarico_inner) not in overlapping_incarichi:
                                overlapping_incarichi.append((incarico_inner, incarico_considered))
                        else:
                            if considered_end:

                                if inner_end > considered_end > inner_start:
                                    if (incarico_inner, incarico_considered) not in overlapping_incarichi and \
                                                    (incarico_considered, incarico_inner) not in overlapping_incarichi:
                                        overlapping_incarichi.append((incarico_inner, incarico_considered))

                    # if the inner incarico has no end date and neither has the considered incarico,
                    # they are overlapping: there cannot be 2+ incarico open at the same time for the same
                    # person

                    elif not considered_end:
                        overlapping_incarichi.append((incarico_inner, incarico_considered))

        if len(overlapping_incarichi) > 0:
            return False, overlapping_incarichi

        return True, incarichi_set

    def commissari_regroup(self, incarichi_set):

        contigue_commissari_id = []
        same_period_commissari_id = []
        incarichi_clean_set = []
        regrouped_set = []

        # removes commissari which are starting/ending on the same date.
        # fills in incarichi_clean_set
        for outer_idx, incarico_outer in enumerate(incarichi_set):
            if incarico_outer['charge_type'] == u'Commissario':
                if outer_idx not in same_period_commissari_id:

                    for inner_idx, incarico_inner in enumerate(incarichi_set):
                        if inner_idx != outer_idx and incarico_inner['charge_type'] == u'Commissario':
                            if inner_idx not in same_period_commissari_id:
                                if incarico_inner['date_start'] == incarico_outer['date_start'] \
                                        and incarico_inner['date_end'] == incarico_outer['date_end']:
                                    same_period_commissari_id.append(inner_idx)
                                    self.logger.debug(
                                        "Merge commissario {0} with {1}: same date_start/date_end".
                                        format(self.format_incarico(incarico_inner),
                                        self.format_incarico(incarico_outer))
                                    )

        for idx, incarico in enumerate(incarichi_set):
            if idx not in same_period_commissari_id:
                incarichi_clean_set.append(incarico)

        # based on previous operation loops over incarichi_clean_set and unites commissari which are
        # less than max_n_days_between_commissari days apart in one single incarico

        for idx, incarico_outer in enumerate(incarichi_clean_set):
            if incarico_outer['charge_type'] == u'Commissario':
                if idx not in contigue_commissari_id:
                    if idx < len(incarichi_clean_set) - 1 and incarico_outer['date_end']:
                        idx_next = idx + 1
                        if idx_next not in contigue_commissari_id:
                            while idx_next < len(incarichi_clean_set):
                                next_incarico = incarichi_clean_set[idx_next]

                                if next_incarico['charge_type'] != u'Commissario':
                                    break
                                else:
                                    diff_next = (next_incarico['date_start'] - incarico_outer['date_end']).days

                                    # if the next incarico is a commissario and the difference between them is < max_n
                                    # then merges them

                                    if diff_next < self.max_n_days_between_commissari:
                                        incarico_outer['date_end'] = next_incarico['date_end']
                                        contigue_commissari_id.append(idx)
                                        contigue_commissari_id.append(idx_next)
                                        idx_next += 1

                                        self.logger.debug("Merge commissario {0} with {1}: closer than {2} days". \
                                            format(self.format_incarico(incarico_outer),
                                                   self.format_incarico(next_incarico),
                                                   self.max_n_days_between_commissari))
                                    else:
                                        break

                    regrouped_set.append(incarico_outer)
            else:
                regrouped_set.append(incarico_outer)

        return regrouped_set

    def process_cities(self, territori_set, dryrun):

        for territorio in territori_set:
            self.logger.info('Getting incarichi for territorio:{0},opid: {1}'.format(territorio, territorio.op_id))
            # get incarichi for territorio
            incarichi_set = self.get_incarichi_api(territorio.op_id)

            if len(incarichi_set) == 0:
                self.logger.error(
                    'No incarico available for city: {0}, skipping'.format(unidecode(territorio.denominazione)).upper())
                continue

            # check for data integrity
            self.date_integrity_check(incarichi_set)

            incarichi_set = self.commissari_regroup(incarichi_set)

            # if data is ok transform data format to be stored in the db
            date_check, incarichi_set = self.check_overlapping_incarichi(incarichi_set)

            if date_check:

                for incarico_dict in incarichi_set:
                    if not dryrun:

                        tipologia = ''
                        if incarico_dict['charge_type'] == "Sindaco":
                            tipologia = Incarico.TIPOLOGIA.sindaco
                        elif incarico_dict['charge_type'] == "Commissario":
                            tipologia = Incarico.TIPOLOGIA.commissario
                        elif incarico_dict['charge_type'] == "Vicesindaco f.f.":
                            tipologia = Incarico.TIPOLOGIA.vicesindaco_ff

                        if tipologia == '':
                            self.logger.error(u"Incarico charge_type not accepted: {0} for {1}". \
                                format(incarico_dict['charge_type'], self.format_incarico(incarico_dict)))

                        #looks for existing incarico, if exists: pass, else creates
                        party_acronym = None
                        party_name = None

                        if tipologia != Incarico.TIPOLOGIA.commissario:

                            if 'party_acronym' in incarico_dict:
                                party_acronym = incarico_dict['party_acronym'].upper()

                            if 'party_name' in incarico_dict:
                                party_name = re.sub(r'\([^)]*\)', '', incarico_dict['party_name']).upper()

                        try:
                            incarico = Incarico.objects.get(
                                nome__iexact=incarico_dict['first_name'],
                                cognome__iexact=incarico_dict['last_name'],
                                data_inizio=incarico_dict['date_start'],
                                data_fine=incarico_dict['date_end'],
                                territorio=territorio,
                                tipologia=tipologia,
                                party_acronym=party_acronym,
                                party_name=party_name,
                            )
                        except ObjectDoesNotExist:
                            # self.logger.debug(u"Creating Incarico: {0}".format(self.format_incarico(incarico_dict)))
                            self.create_incarico(incarico_dict, territorio, tipologia)

            else:
                self.overlapping_dict[territorio.denominazione.upper()] = incarichi_set

        return

    def create_incarico(self, incarico_dict, territorio, tipologia):

        incarico = Incarico()
        incarico.nome = incarico_dict['first_name']
        incarico.cognome = incarico_dict['last_name']
        incarico.territorio = territorio
        incarico.tipologia = tipologia
        incarico.data_inizio = incarico_dict['date_start']
        incarico.data_fine = incarico_dict['date_end']
        incarico.op_link = incarico_dict['op_link']

        if 'picture_url' in incarico_dict:
            # checks that the pic is attually there before writing the url in the db
            pic_data = requests.get(incarico_dict['picture_url'])
            if pic_data.content != '':
                incarico.pic_url = incarico_dict['picture_url']

        # motivo commissariamento
        if 'description' in incarico_dict.keys():
            incarico.motivo_commissariamento = incarico_dict['description']

        if 'party_acronym' in incarico_dict:
            incarico.party_acronym = incarico_dict['party_acronym'][:50].upper()

        if 'party_name' in incarico_dict:
            if incarico_dict['party_name'].lower() != 'non specificato':
                incarico.party_name = re.sub(r'\([^)]*\)', '', incarico_dict['party_name']).upper()

        incarico.save()

    def log_errors(self):

        for incarico in self.incarichi_longer_5yrs:
            self.logger.warning("Incarico:{0} is longer than {1} days".format(
                self.format_incarico(incarico), self.max_n_days_incarico_length
            ))

        for disc_dict in self.territori_discontinuity:
            self.logger.warning("Incarico {0} and Incarico {1} are {2} days apart".format(
                self.format_incarico(disc_dict['incarico_1']),
                self.format_incarico(disc_dict['incarico_2']),
                disc_dict['diff']))

        self.logger.warning("Incarico over max lenght:{0}".format(len(self.incarichi_longer_5yrs)))
        self.logger.warning("Incarichi couple over max days apart:{0}".format(len(self.territori_discontinuity)))

        for denominazione_territorio, single_dict in self.overlapping_dict.iteritems():
            self.logger.warning("TERRITORIO: {0} OVERLAPPING INCARICHI:".format(unidecode(denominazione_territorio)))
            for incarichi_tuple in single_dict:
                incarico_0_str = self.format_incarico(incarichi_tuple[0])
                incarico_1_str = self.format_incarico(incarichi_tuple[1])

                self.logger.warning("Incarico: {0} is overlapping with {1}".format(incarico_0_str, incarico_1_str))

    def handle(self, *args, **options):
        verbosity = options['verbosity']
        if verbosity == '0':
            self.logger.setLevel(logging.ERROR)
        elif verbosity == '1':
            self.logger.setLevel(logging.WARNING)
        elif verbosity == '2':
            self.logger.setLevel(logging.INFO)
        elif verbosity == '3':
            self.logger.setLevel(logging.DEBUG)

        mapper = FLMapper(settings.LISTA_COMUNI_PATH)
        dryrun = options['dryrun']
        delete = options['delete']
        territori_type = options['territori_type']
        ###
        # cities
        ###
        cities_codes = options['cities']

        if territori_type != '' and cities_codes != '':
            self.logger.error("Cannot specify both territori_type and cities. Choose one")
            return

        self.apidomain = options['apidomain']
        if options['auth']:
            (user, pwd) = options['auth'].split(",")
            self.baseurl = "http://{0}:{1}@{2}".format(user, pwd, self.apidomain)
        else:
            self.baseurl = "http://{0}".format(self.apidomain)

        # sets cities_to_process: if territorio_type is set uses the macro-category: all, capoluoghi, other
        # otherwise uses cities: single cities codes
        if territori_type != '':
            cities_to_process = self.get_territori_from_types(territori_type)

        elif cities_codes != '':
            cities = mapper.get_cities(cities_codes)
            cities_to_process = self.get_territori_from_finloc(cities)

        else:
            self.logger.error("Must specify territory_type or cities")
            return

        self.logger.info(u"Start charges import with dryrun: {0}".format(dryrun))


        if delete:
            self.logger.info(u"Deleting all Incarico for considered cities")
            Incarico.objects.filter(territorio__in=cities_to_process).delete()
            self.logger.info(u"Done.")

        self.process_cities(cities_to_process, dryrun)
        self.log_errors()