from itertools import groupby
import logging
from optparse import make_option
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.management import BaseCommand
from bs4 import BeautifulSoup
from bilanci.models import CodiceVoce, Voce
from bilanci.utils import gdocs


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (

        make_option('--year',
                    dest='year',
                    default='2013',
                    help='Year to fetch'),

        make_option('--type',
                    dest='type',
                    default='c',
                    help='Select bilancio type: [(p)reventivo | (c)onsuntivo]'),

        make_option('--force-google',
                    dest='force_google',
                    action='store_true',
                    default=False,
                    help='Force reloading mapping files from gdocs (invalidate the csv cache)'),

        make_option('--append',
                    dest='append',
                    action='store_true',
                    default=False,
                    help='Use the log file appending instead of overwriting (used when launching shell scripts)'),

        make_option('--dry-run',
                    dest='dryrun',
                    action='store_true',
                    default=False,
                    help='Set the dry-run command mode: nothing is written on the db'),

    )

    help = 'Associates xml bilancio codes to simplified tree slugs'

    logger = logging.getLogger('management')
    comuni_dicts = {}
    bilancio_year = None

    def save_voce_codice(self, voce_slug, quadro_cod, colonna_cod, denominazione_voce, denominazione_colonna ):

        cod_voce = CodiceVoce()

        try:
            voce = Voce.objects.get(slug = voce_slug)
        except ObjectDoesNotExist:
            self.logger.error("Voce with slug:{0} is not present in DB and Codice voce cannot be saved")
            return

        cod_voce.voce = voce
        cod_voce.anno = self.bilancio_year
        cod_voce.colonna_cod = colonna_cod
        cod_voce.quadro_cod = quadro_cod
        cod_voce.denominazione_voce = denominazione_voce
        cod_voce.denominazione_colonna = denominazione_colonna
        cod_voce.save()
        return


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
        force_google = options['force_google']
        self.bilancio_year = options['year']
        type = options['type']

        if type.lower() == 'c':
            bilancio_type = 'consuntivo'
        elif type.lower() == 'p':
            bilancio_type = 'preventivo'
        else:
            self.logger.error("Bilancio type must be C or P")
            return

        if options['append'] is True:
            self.logger = logging.getLogger('management_append')



        ###
        #   Mapping files from gdoc
        ###
        # connect to google account and fetch tree mapping and simple tree structure
        codes_map = gdocs.get_bilancio_codes_map(n_header_lines=1, force_google=force_google, bilancio_type=bilancio_type, bilancio_year=self.bilancio_year)

        # metadata voci
        # quadro_denominazione, titolo_denominazione , cat_cod, voce_denominazione, quadro_cod, voce_cod, voce_slug

        voci = codes_map['voci']
        # metadata colonne
        # quadro_denominazione, quadro_cod, col_cod, col_denominazione
        colonne = codes_map['colonne']

        # regroup colonne on (quadro_denominazione, quadro_cod)
        q_keygen = lambda x: (x[0], x[1] )
        colonne_regroup = dict((k,list(v)) for k,v in groupby(colonne, key=q_keygen))

        for voce in voci:
            denominazione_voce = voce[3]
            quadro_cod = voce[4]
            quadro_denominazione_voce = voce[0]
            voce_slug = voce[6]

            if not voce_slug:
                self.logger.debug(u"Voce slug not present for voce:{0}".format(denominazione_voce))
                continue

            colonne_quadro = []
            if (quadro_denominazione_voce,quadro_cod,) in colonne_regroup.keys():
                colonne_quadro = colonne_regroup[(quadro_denominazione_voce,quadro_cod,)]

            n_colonne_quadro = len(colonne_quadro)
            # if the quadro / titolo considered is associated with N colonne then generates a set of N slugs from voce
            # else
            # writes the current voce_slug in the db
            if n_colonne_quadro > 0:

                for colonna in colonne_quadro:
                    pass

            else:

                self.save_voce_codice(voce_slug,quadro_cod,'',denominazione_voce,'')



            self.logger.debug(u"Voce:{0}, Q:{1} con n.colonne:{2}".format(denominazione_voce, quadro_cod, n_colonne_quadro))



        return
