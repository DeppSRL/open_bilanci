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

        self.logger.info(u"Start charges import with dryrun: {0}".format(dryrun))

        if delete:
            self.logger.info(u"Deleting all Incarico...".format(dryrun))
            Incarico.objects.all().delete()
            self.logger.info(u"Done.".format(dryrun))

        self.handle_incarichi(territori_type, dryrun)
        self.logger.info(u"End import charges script")


    def get_incarichi_api(self, territorio_opid, incarico_type):

        api_results_json = requests.get(
            settings.OP_API_HOST +"/politici/instcharges?charge_type_id={0}&location_id={1}&order_by=date".\
                format(incarico_type, territorio_opid)
            ).json()

        if 'results' not in api_results_json:
            return None

        return api_results_json['results']


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

            # get incarichi for sindaco
            sindaci_api_results = self.get_incarichi_api(territorio.op_id, "14")

            # get incarichi for commissario
            commissari_api_results = self.get_incarichi_api(territorio.op_id, "16")

            # unite data and check for data integrity
            api_results = sindaci_api_results
            api_results.extend(commissari_api_results)

            if len(api_results) == 0:
                self.logger.warning('Incarichi missing for {0}'.format(unidecode(territorio.denominazione)).upper())
                return

            # if data is ok transform data format to fit Visup widget specs
            date_check, incarichi_set = self.incarichi_date_check(api_results)

            if date_check:

                for incarico_dict in incarichi_set:
                    if not dryrun:
                        is_commissario = False
                        if incarico_dict['charge_type'] == settings.OP_API_HOST + '/politici/chargetypes/16':
                            is_commissario =  True

                        # save incarico

                        #looks for existing incarico, if exists: updates, else creates

                        try:
                            incarico = Incarico.objects.get(
                                nome__iexact = incarico_dict['politician']['first_name'],
                                cognome__iexact = incarico_dict['politician']['last_name'],
                                territorio = territorio,
                                is_commissario = is_commissario,
                            )
                        except ObjectDoesNotExist:
                            # self.logger.info(u"Creating Incarico: {0}".format(self.format_incarico(incarico_dict)))
                            self.create_incarico(incarico_dict, territorio, is_commissario)

                        else:
                            # self.logger.info(u"Updating Incarico:{0}".format(self.format_incarico(incarico_dict)))

                            incarico.data_fine = incarico_dict['date_end']
                            incarico.data_inizio = incarico_dict['date_start']
                             # motivo commissariamento
                            if 'description' in incarico_dict.keys():
                                incarico.motivo_commissariamento = incarico_dict['description']

                            if incarico_dict['party']['acronym']:
                                incarico.party_acronym = incarico_dict['party']['acronym'].upper()

                            if incarico_dict['party']['name'] and incarico_dict['party']['name'].lower() != 'non specificato':
                                incarico.party_name = re.sub(r'\([^)]*\)', '', incarico_dict['party']['name']).upper()

                            incarico.save()

            else:
                self.logger.warning("TERRITORIO: {0} OVERLAPPING INCARICHI:".format(unidecode(territorio.denominazione.upper())))
                for incarichi_tuple in incarichi_set:

                    incarico_0_str = self.format_incarico(incarichi_tuple[0])
                    incarico_1_str = self.format_incarico(incarichi_tuple[1])

                    self.logger.warning("Incarico: {0} is overlapping with {1}".format(incarico_0_str, incarico_1_str))


        return

    def format_incarico(self,incarico_dict):

        return "{0}.{1} OPID: {2} - ({3} - {4})".\
                        format(
                            unidecode(incarico_dict['politician']['first_name'][0].title()),
                            unidecode(incarico_dict['politician']['last_name'].title()),
                            incarico_dict['politician']['self'].replace(settings.OP_API_HOST+'/politici/politicians/',''),
                            datetime.strftime(incarico_dict['date_start'], self.date_fmt ),
                            datetime.strftime(incarico_dict['date_end'], self.date_fmt ),

                        )


    def create_incarico(self, incarico_dict, territorio, is_commissario):

        incarico = Incarico()
        incarico.nome = incarico_dict['politician']['first_name']
        incarico.cognome = incarico_dict['politician']['last_name']
        incarico.territorio = territorio
        incarico.is_commissario = is_commissario
        incarico.data_inizio = incarico_dict['date_start']
        incarico.data_fine = incarico_dict['date_end']

        # motivo commissariamento
        if 'description' in incarico_dict.keys():
            incarico.motivo_commissariamento = incarico_dict['description']

        if incarico_dict['party']['acronym']:
            incarico.party_acronym = incarico_dict['party']['acronym'].upper()

        if incarico_dict['party']['name'] and incarico_dict['party']['name'].lower() != 'non specificato':
            incarico.party_name = re.sub(r'\([^)]*\)', '', incarico_dict['party']['name']).upper()

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

        if territori_type == 'all' or territori_type == 'capoluoghi':
            self.get_incarichi(capoluoghi_provincia, dryrun)
            self.get_incarichi(altri_capoluoghi, dryrun)

        if territori_type =='all' or territori_type == 'others':
            self.get_incarichi(altri_territori, dryrun)


        return




