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
    dryrun = False
    bilancio_year = None

    def save_voce_codice(self, voce_slug, voce_cod, quadro_cod, colonna_cod, denominazione_voce, denominazione_colonna ):

        try:
            voce = Voce.objects.get(slug = voce_slug)
        except ObjectDoesNotExist:
            self.logger.error("Voce with slug:{0} is not present in DB and Codice voce cannot be saved".format(voce_slug))
            return

        if self.dryrun is False:

            cod_voce, created = CodiceVoce.objects.get_or_create(
                voce = voce,
                voce_cod = voce_cod,
                anno = self.bilancio_year,
                colonna_cod = colonna_cod,
                quadro_cod = quadro_cod,
                denominazione_voce = denominazione_voce,
                denominazione_colonna = denominazione_colonna
            )

            if created:
                self.logger.info("CodiceVoce created: {0}:{1}-{2}-{3}".format(voce.slug, voce_cod, quadro_cod, colonna_cod))


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

        self.dryrun = options['dryrun']
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
            voce_cod = voce[5]
            quadro_denominazione_voce = voce[0]
            voce_slug = voce[6]

            if not voce_slug:
                # self.logger.debug(u"Voce slug not present for voce:{0}".format(denominazione_voce))
                continue

            colonne_quadro = []
            if (quadro_denominazione_voce,quadro_cod,) in colonne_regroup.keys():
                colonne_quadro = colonne_regroup[(quadro_denominazione_voce,quadro_cod,)]

            n_colonne_quadro = len(colonne_quadro)
            # if the quadro / titolo considered is associated with N colonne then generates a set of N slugs from voce
            # else
            # writes the current voce_slug in the db
            if n_colonne_quadro > 0:

                if quadro_cod == '04' or quadro_cod == '05':
                    # deal with funzioni / interventi

                    if denominazione_voce.lower() != 'totale':
                        ##
                        # FUNZIONI:
                        # for each funzione the grand total is the only data that gets imported, so the
                        # code for the total column is found and associated with the funzione
                        ##

                        # finds the colonna with label 'totale' and gets the colonna code
                        colonna_totale = None
                        for colonna in colonne_quadro:
                            if colonna[3].lower() == 'totale':
                                colonna_totale = colonna

                        if colonna_totale:
                            colonna_totale_cod = colonna_totale[2]
                        else:
                            self.logger.error(u'Colonna totale not found for Q:{0}, cod_voce:{1}, voce_slug {2}. Skipping'.\
                                format(quadro_cod,voce_cod,voce_slug))
                            continue

                        self.save_voce_codice(voce_slug, voce_cod, quadro_cod,colonna_totale_cod, denominazione_voce,'')

                    else:

                        ##
                        # INTERVENTI:
                        # similarly to funzioni the only data associated with interventi is the grand total so once
                        # the "Totale" row is reached all the interventi cols are associated with the row code and saved
                        ##

                        for colonna in colonne_quadro:
                            colonna_cod = colonna[2]
                            denominazione_colonna = colonna[3]
                            colonna_slug = colonna[4]
                            if denominazione_colonna.lower() != 'totale':
                                colonna_voce_slug = "{0}-{1}".format(voce_slug, colonna_slug)
                                self.save_voce_codice(colonna_voce_slug, voce_cod, quadro_cod, colonna_cod, denominazione_voce, denominazione_colonna)

                else:

                    first_colonna_slug = colonne_quadro[0][4]
                    for colonna in colonne_quadro:

                        ##
                        # generate a slug for each colonna based on the slug of the first colonna:
                        # example: if the slug in the voci sheet is
                        # consuntivo-entrate-accertamenti-imposte-e-tasse-imposte-casa-e-fabbricati (Q02)
                        # and Q02 has three colonna: accertamenti, riscossioni-in-conto-competenza, riscossioni-in-conto-residui
                        # then 3 slugs will be generated using "accertamenti" as the reference string to be replaced
                        # consuntivo-entrate-accertamenti-imposte-e-tasse-imposte-casa-e-fabbricati
                        # consuntivo-entrate-riscossioni-in-conto-competenza-imposte-e-tasse-imposte-casa-e-fabbricati
                        # consuntivo-entrate-riscossioni-in-conto-residui-imposte-e-tasse-imposte-casa-e-fabbricati
                        ##

                        colonna_cod = colonna[2]
                        denominazione_colonna = colonna[3]
                        colonna_slug = colonna[4]

                        colonna_voce_slug = voce_slug.replace(first_colonna_slug, colonna_slug)

                        self.save_voce_codice(colonna_voce_slug,voce_cod, quadro_cod,colonna_cod, denominazione_voce, denominazione_colonna)

            else:

                self.save_voce_codice(voce_slug, voce_cod, quadro_cod,'1',denominazione_voce,'')

        return