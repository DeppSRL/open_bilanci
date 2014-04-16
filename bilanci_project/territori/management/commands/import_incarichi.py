# -*- coding: utf-8 -*-
from django.conf import settings
import logging
from optparse import make_option
from pprint import pprint
from django.core.exceptions import ObjectDoesNotExist
from django.core.management import BaseCommand
from django.utils.datastructures import SortedDict
import re
import requests
from datetime import datetime
import time
from unidecode import unidecode
from territori.models import Territorio, Incarico
__author__ = 'stefano'



class Command(BaseCommand):

    #     sets the start / end of graphs
    timeline_start = settings.APP_START_DATE
    timeline_end = settings.APP_END_DATE
    date_fmt = '%Y-%m-%d'

    accepted_types = ['all', 'capoluoghi', 'others']

    option_list = BaseCommand.option_list + (

        make_option('--territori','-t',
            dest='territori',
            action='store',
            default='all',
            help='Type of Territorio: '+  ' | '.join(accepted_types)),
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

    logger = logging.getLogger('management')
    comuni_dicts = {}


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

        dryrun = options['dryrun']
        delete = options['delete']
        territori_type = options['territori']
        self.apidomain = options['apidomain']

        if options['auth']:
            (user, pwd) = options['auth'].split(",")
            self.baseurl = "http://{0}:{1}@{2}".format(user, pwd, self.apidomain)
        else:
            self.baseurl = "http://{0}".format(self.apidomain)

        self.logger.info(u"Start charges import with dryrun: {0}".format(dryrun))

        if delete:
            self.logger.info(u"Deleting all Incarico...".format(dryrun))
            Incarico.objects.all().delete()
            self.logger.info(u"Done.".format(dryrun))

        self.handle_incarichi(territori_type, dryrun)
        self.logger.info(u"End import charges script")


    def get_incarichi_api(self, territorio_opid):

        # get incarichi from politici/city_mayors
        api_request = requests.get("{0}/politici/city_mayors/{1}".\
                                   format(self.baseurl, territorio_opid))
        api_results_json = api_request.json()

        if 'sindaci' not in api_results_json:
            return []

        return api_results_json['sindaci']


    def incarichi_date_check(self, incarichi_set):

        """
        Incarichi check checks that incarichi for a given Comune are not overlapping and
        sets incarichi beginnings and end based on the start / end of web app timeline.

        Return a tuple (Bool, incarichi_set)

        if bool is True: incarichi_set is a list of interesting incarichi for the considered timespan
        if bool is False: incarichi_set is a list of tuples of overlapping incarichi for the considered timespan

        """
        # converts all textual data to datetime obj type and
        # discards incarichi out of timeline scope: happened before timeline_start or after timeline_end

        interesting_incarichi = []
        overlapping_incarichi = []
        for incarico_dict in incarichi_set:

            incarico_dict['date_start'] = datetime.strptime(incarico_dict['date_start'], self.date_fmt)
            if incarico_dict['date_end']:
                incarico_dict['date_end'] = datetime.strptime(incarico_dict['date_end'], self.date_fmt)

            # considers only charges which are contained between self.timeline_start / end
            if ( incarico_dict['date_end'] is None or incarico_dict['date_end'] > self.timeline_start) and incarico_dict['date_start'] < self.timeline_end:

                if incarico_dict['date_end'] is None or incarico_dict['date_end'] > self.timeline_end:
                    incarico_dict['date_end'] = self.timeline_end

                if incarico_dict['date_start']  < self.timeline_start:
                    incarico_dict['date_start']  = self.timeline_start

                interesting_incarichi.append(incarico_dict)


        # checks if interesting_incarichi are overlapping
        # in incarichi are overlapping, appends them in the overlapping_incarichi list
        for incarico_considered in interesting_incarichi:
            considered_start = incarico_considered['date_start']
            considered_end = incarico_considered['date_end']

            for incarico_inner in interesting_incarichi:
                if incarico_inner is not incarico_considered:
                    inner_start = incarico_inner['date_start']
                    inner_end = incarico_inner['date_end']

                    if inner_start < considered_start < inner_end:

                        if (incarico_inner, incarico_considered) not in overlapping_incarichi and\
                            (incarico_considered, incarico_inner) not in overlapping_incarichi:

                            overlapping_incarichi.append((incarico_inner, incarico_considered))

                    elif inner_end > considered_end > inner_start:
                        if (incarico_inner, incarico_considered) not in overlapping_incarichi and\
                            (incarico_considered, incarico_inner) not in overlapping_incarichi:

                            overlapping_incarichi.append((incarico_inner, incarico_considered))


        if len(overlapping_incarichi) > 0:
            return False, overlapping_incarichi

        return True, interesting_incarichi

    def get_incarichi(self, territori_set, dryrun):

        for territorio in territori_set:
            self.logger.info('Getting incarichi for territorio:{0},opid: {1}'.format(territorio,territorio.op_id))
            # get incarichi for territorio
            incarichi_api_results = self.get_incarichi_api(territorio.op_id)

            # check for data integrity

            if len(incarichi_api_results) == 0:
                self.logger.warning('Incarichi missing for {0}'.format(unidecode(territorio.denominazione)).upper())
                return

            # if data is ok transform data format to fit Visup widget specs
            date_check, incarichi_set = self.incarichi_date_check(incarichi_api_results)

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
                            self.logger.error(u"Incarico charge_type not accepted: {0} for {1}".\
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
                                nome__iexact = incarico_dict['first_name'],
                                cognome__iexact = incarico_dict['last_name'],
                                data_inizio = incarico_dict['date_start'],
                                data_fine = incarico_dict['date_end'],
                                territorio = territorio,
                                tipologia = tipologia,
                                party_acronym = party_acronym,
                                party_name = party_name,
                            )
                        except ObjectDoesNotExist:
                            # self.logger.info(u"Creating Incarico: {0}".format(self.format_incarico(incarico_dict)))
                            self.create_incarico(incarico_dict, territorio, tipologia)

            else:
                self.logger.warning("TERRITORIO: {0} OVERLAPPING INCARICHI:".format(unidecode(territorio.denominazione.upper())))
                for incarichi_tuple in incarichi_set:

                    incarico_0_str = self.format_incarico(incarichi_tuple[0])
                    incarico_1_str = self.format_incarico(incarichi_tuple[1])

                    self.logger.warning("Incarico: {0} is overlapping with {1}".format(incarico_0_str, incarico_1_str))


        return

    def format_incarico(self,incarico_dict):

        date_start = datetime.strftime(incarico_dict['date_start'], self.date_fmt)
        date_end = datetime.strftime(incarico_dict['date_end'], self.date_fmt)
        opid = re.search(r'^.*/([0-9]+)$', incarico_dict['op_link']).groups()[0]


        return "{0}.{1} - {2} ({3} - {4})".\
                        format(
                            unidecode(incarico_dict['first_name'][0].title()),
                            unidecode(incarico_dict['last_name'].title()),
                            opid,
                            date_start,
                            date_end
                        )


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


    def handle_incarichi(self, territori_type, dryrun):

        province = Territorio.objects.\
            filter(territorio=Territorio.TERRITORIO.P).values_list('denominazione', flat=True)
        # prende tutte le citta' che hanno il nome = alla provincia di appartenenza
        capoluoghi_provincia = Territorio.objects.\
            filter(territorio = Territorio.TERRITORIO.C, denominazione__in = province).order_by('-cluster','denominazione')

        # aggiunge i capoluoghi a capo di una provincia che non ha il loro stesso nome
        altri_nomi_capoluoghi = [
            'Barletta',
            'Andria',
            'Trani',
            'Carbonia',
            'Iglesias',
            'Forlì',
            'Massa',
            'Villacidro',
            'Sanluri',
            'Monza',
            'Tortolì',
            'Lanusei',
            'Olbia',
            'Tempio Pausania',
            'Pesaro',
            'Urbino',
            'Aosta',
            'Verbania'
        ]

        altri_capoluoghi = Territorio.objects.filter(
            territorio=Territorio.TERRITORIO.C, denominazione__in = altri_nomi_capoluoghi).\
            order_by('-cluster','denominazione')

        altri_territori = Territorio.objects.filter(territorio=Territorio.TERRITORIO.C).\
            exclude(denominazione__in = province).exclude(denominazione__in = altri_nomi_capoluoghi).order_by('-cluster','denominazione')

        # depending on the territori_type value runs the import only for capoluoghi di provincia or for all Territori
        # prioritize the territori list getting first the capoluoghi di provincia and then all the rest

        if territori_type != 'others':
            self.get_incarichi(capoluoghi_provincia, dryrun)
            self.get_incarichi(altri_capoluoghi, dryrun)

        if territori_type !='capoluoghi':
            self.get_incarichi(altri_territori, dryrun)


        return




