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
                    dest='bilancio_type',
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
    bilancio_type = None
    voci = None
    added_voce_slug = []
    fill_in_mapping = {}

    def save_codice_voce(self, voce_slug, voce_cod, quadro_cod, colonna_cod, denominazione_voce, denominazione_colonna ):

        try:
            voce = Voce.objects.get(slug = voce_slug)
        except ObjectDoesNotExist:
            self.logger.error(u"Voce with slug:{0} is not present in DB and Codice voce cannot be saved".format(voce_slug))
            return

        if voce_slug not in self.added_voce_slug:
            self.added_voce_slug.append(voce_slug)

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
                self.logger.info(u"CodiceVoce created: {0}:{1}-{2}-{3}".format(voce.slug, voce_cod, quadro_cod, colonna_cod))
            else:
                self.logger.info(u"CodiceVoce already present: {0}:{1}-{2}-{3}".format(voce.slug, voce_cod, quadro_cod, colonna_cod))

        return


    def get_voci_titolo(self, cod_quadro, quadro_denominazione_contains, slug_startswith=None):
        # get voci from Quadro / titolo
        # using
        # x[0] == quadro_denominazione
        # x[4] == quadro_cod
        # x[6] == voce_slug

        lambda_cod_denominazione_slug = lambda x: x[4] == cod_quadro and quadro_denominazione_contains.lower() in x[0].lower() and x[6].startswith(slug_startswith)
        lambda_cod_denominazione = lambda x: x[4] == cod_quadro and quadro_denominazione_contains.lower() in x[0].lower()

        if slug_startswith is None:
            lambda_func = lambda_cod_denominazione
        else:
            lambda_func = lambda_cod_denominazione_slug

        return filter(lambda_func, self.voci)

    def convert_slugs(self, voci_set, old_subslug, new_subslug):

        #  given a set of voci and a substring of slug
        # gets the Voce with denominazione contained in the fill_in_mapping
        # then gets the impegni slug (voce_impegni_slug) substitutes 'impegni' with the substring
        # and sets the new slug for the voce in self.voci

        for v in voci_set:
            voce_denominazione = v[3]
            if voce_denominazione in self.fill_in_mapping.keys():
                voce_impegni_slug = self.fill_in_mapping[voce_denominazione]
                voce_replaced_slug = voce_impegni_slug.replace(old_subslug, new_subslug)
                v[6] = voce_replaced_slug

        return

    def fill_in_voci(self):

        # fills in the voci mapping table using the Q4 impegni as reference to complete the
        #  q4 conto competenza, conto residui and q5 impegni, conto competenza, residui

        voci_q4_impegni = self.get_voci_titolo(cod_quadro='04', quadro_denominazione_contains='QUADRO 4 - SPESE CORRENTI - (A) - IMPEGNI', slug_startswith='consuntivo-spese-impegni-')
        voci_q4_cc = self.get_voci_titolo(cod_quadro='04', quadro_denominazione_contains='QUADRO 4 - SPESE CORRENTI - (B) - PAGAMENTI IN CONTO COMPETENZA',)
        voci_q4_cr = self.get_voci_titolo(cod_quadro='04', quadro_denominazione_contains='QUADRO 4 - SPESE CORRENTI - (C) - PAGAMENTI IN CONTO RESIDUI',)

        voci_q5_impegni = self.get_voci_titolo(cod_quadro='05', quadro_denominazione_contains='QUADRO 5 - SPESE IN CONTO CAPITALE - (A) - IMPEGNI')
        voci_q5_cc = self.get_voci_titolo(cod_quadro='05', quadro_denominazione_contains='QUADRO 5 - SPESE IN CONTO CAPITALE - (B) - PAGAMENTI IN CONTO COMPETENZA')
        voci_q5_cr = self.get_voci_titolo(cod_quadro='05', quadro_denominazione_contains='QUADRO 5 - SPESE IN CONTO CAPITALE - (C) - PAGAMENTI IN CONTO RESIDUI')

        # creates a map that links voce_denominazione with voce_slug
        for voce_q4 in voci_q4_impegni:
            self.fill_in_mapping[voce_q4[3]] = voce_q4[6]

        # convert slugs for q4 conto competenza, residui
        self.convert_slugs(voci_set=voci_q4_cc, old_subslug='impegni', new_subslug='pagamenti-in-conto-competenza')
        self.convert_slugs(voci_set=voci_q4_cr, old_subslug='impegni', new_subslug='pagamenti-in-conto-residui')
        # convert slugs for q5 impegni, conto competenza, residui
        self.convert_slugs(voci_set=voci_q5_impegni, old_subslug='impegni-spese-correnti', new_subslug='impegni-spese-per-investimenti')
        self.convert_slugs(voci_set=voci_q5_cc, old_subslug='impegni-spese-correnti', new_subslug='pagamenti-in-conto-competenza-spese-per-investimenti')
        self.convert_slugs(voci_set=voci_q5_cr, old_subslug='impegni-spese-correnti', new_subslug='pagamenti-in-conto-residui-spese-per-investimenti')


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
        bilancio_type = options['bilancio_type']

        if bilancio_type.lower() == 'c':
            bilancio_type = 'consuntivo'
        elif bilancio_type.lower() == 'p':
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

        self.voci = codes_map['voci']
        # metadata colonne
        # quadro_denominazione, quadro_cod, col_cod, col_denominazione
        colonne = codes_map['colonne']

        # regroup colonne on (quadro_denominazione, quadro_cod)
        q_keygen = lambda x: (x[0], x[1] )
        colonne_regroup = dict((k,list(v)) for k,v in groupby(colonne, key=q_keygen))

        # function fill-in-voci creates the mapping for Q4 (conto competenza / conto residui) and Q5 (impegni /conto competenza / conto residui)
        # from Q4 impegni where the mapping has been made by the operator on the gdoc file

        self.fill_in_voci()

        for voce in self.voci:
            denominazione_voce = voce[3]
            quadro_cod = voce[4]
            voce_cod = voce[5]
            quadro_denominazione_voce = voce[0]
            voce_slug = voce[6]

            if voce_slug is None or voce_slug == '' or voce_slug == u'':
                # if voce slug is empty skip row
                continue

            colonne_quadro = []
            if (quadro_denominazione_voce,quadro_cod,) in colonne_regroup.keys():
                colonne_quadro = colonne_regroup[(quadro_denominazione_voce,quadro_cod,)]

            n_colonne_quadro = len(colonne_quadro)
            # if the quadro / titolo considered is associated with 0 colonne
            # writes the current voce_slug in the db
            # else
            # generates a set of N slugs from voce
            if n_colonne_quadro == 0:

                self.save_codice_voce(voce_slug, voce_cod, quadro_cod,'1',denominazione_voce,'')

            else:

                if quadro_cod == '04' or quadro_cod == '05':
                    # deal with funzioni / interventi

                    if denominazione_voce.lower() == 'totale':
                        ##
                        # INTERVENTI:
                        # the only data associated with interventi is the grand total so once the "Totale" row
                        # is reached all the interventi cols are associated with the 'totale' row code and saved
                        ##
                        funzioni_string = '-funzioni'
                        root_voce_slug = voce_slug
                        if funzioni_string in root_voce_slug:
                            root_voce_slug = root_voce_slug.replace(funzioni_string,'')

                        for colonna in colonne_quadro:
                            colonna_cod = colonna[2]
                            denominazione_colonna = colonna[3]
                            colonna_slug = colonna[4]

                            if denominazione_colonna.lower() != 'totale':

                                colonna_root_slug = colonna_slug
                                if root_voce_slug in colonna_root_slug:
                                    colonna_root_slug = colonna_root_slug.replace(root_voce_slug,'')

                                colonna_voce_slug = "{0}{1}".format(root_voce_slug, colonna_root_slug)
                                self.save_codice_voce(colonna_voce_slug, voce_cod, quadro_cod, colonna_cod, denominazione_voce, denominazione_colonna)
                    else:

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
                                break

                        if colonna_totale:
                            colonna_totale_cod = colonna_totale[2]
                        else:
                            self.logger.error(u'Colonna totale not found for Q:{0}, cod_voce:{1}, voce_slug {2}. Skipping'.\
                                format(quadro_cod,voce_cod,voce_slug))
                            continue

                        self.save_codice_voce(voce_slug, voce_cod, quadro_cod,colonna_totale_cod, denominazione_voce,'')




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

                        if colonna_slug == '':
                            continue


                        colonna_voce_slug = voce_slug.replace(first_colonna_slug, colonna_slug)

                        self.save_codice_voce(colonna_voce_slug,voce_cod, quadro_cod,colonna_cod, denominazione_voce, denominazione_colonna)

        self.logger.info("Added {0} unique Voce slug".format(len(self.added_voce_slug)))

        return