from itertools import groupby
import logging
from optparse import make_option
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.management import BaseCommand
from bilanci.models import CodiceVoce, Voce
from bilanci.utils import gdocs


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (

        make_option('--year',
                    dest='year',
                    default='2013',
                    help='Year to fetch'),

        make_option('--type',
                    dest='self.bilancio_type',
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
    colonne = None
    di_cui_string = ' di cui:'
    added_voce_slug = []
    fill_in_mapping_voci = {}
    fill_in_mapping_colonne = {'04':{}, '05':{}}

    def save_codice_voce(self, voce_slug, voce_cod, quadro_cod, colonna_cod, denominazione_voce, denominazione_colonna ):

        try:
            voce = Voce.objects.get(slug = voce_slug)
        except ObjectDoesNotExist:
            self.logger.error(u"Voce with slug:{0} is not present in DB and Codice voce cannot be saved".format(voce_slug))
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
                self.logger.debug(u"CodiceVoce created: {0}:{1}-{2}-{3}".format(voce.slug, voce_cod, quadro_cod, colonna_cod))
                if voce_slug not in self.added_voce_slug:
                    self.added_voce_slug.append(voce_slug)

            else:
                self.logger.debug(u"CodiceVoce already present: {0}:{1}-{2}-{3}".format(voce.slug, voce_cod, quadro_cod, colonna_cod))

        return


    def get_voci_titolo(self, cod_quadro, quadro_denominazione, slug_startswith=None):
        # get voci from Quadro / denominazione
        # using
        # x[0] == quadro_denominazione
        # x[4] == quadro_cod
        # x[6] == voce_slug

        lambda_cod_denominazione_slug = lambda x: x[4] == cod_quadro and quadro_denominazione.lower() in x[0].lower() and x[6].startswith(slug_startswith)
        lambda_cod_denominazione = lambda x: x[4] == cod_quadro and quadro_denominazione.lower() in x[0].lower()

        if slug_startswith is None:
            lambda_func = lambda_cod_denominazione
        else:
            lambda_func = lambda_cod_denominazione_slug

        return filter(lambda_func, self.voci)


    def convert_voci_slugs(self, cod_quadro,quadro_denominazione , old_subslug, new_subslug):

        #  given a set of voci and a substring of slug
        # gets the Voce with denominazione contained in the fill_in_mapping
        # then gets the impegni slug (voce_impegni_slug) substitutes 'impegni' with the substring
        # and sets the new slug for the voce in self.voci

        voci_set = self.get_voci_titolo(cod_quadro=cod_quadro, quadro_denominazione=quadro_denominazione)

        for v in voci_set:
            voce_denominazione = v[3].replace(self.di_cui_string,'')
            if voce_denominazione in self.fill_in_mapping_voci.keys():
                voce_impegni_slug = self.fill_in_mapping_voci[voce_denominazione]
                voce_replaced_slug = voce_impegni_slug.replace(old_subslug, new_subslug)
                v[6] = voce_replaced_slug

        return


    def get_colonne_titolo(self, cod_quadro, quadro_denominazione):
        # get colonne from Quadro / denominazione
        # using
        # x[0] == quadro_denominazione
        # x[1] == quadro_cod
        # x[2] == col_cod
        # x[3] == col_denominazione
        # x[4] == slug
        lambda_colonne = lambda x: x[1] == cod_quadro and quadro_denominazione.lower() in x[0].lower()
        return filter(lambda_colonne, self.colonne)


    def convert_colonne_slugs(self, cod_quadro, quadro_denominazione, old_subslug, new_subslug):
        # same as convert_voci_slugs for columns
        colonne_set = self.get_colonne_titolo(cod_quadro, quadro_denominazione)
        considered_col_mapping = self.fill_in_mapping_colonne[cod_quadro]
        for c in colonne_set:
            colonna_denominazione = c[3]
            if colonna_denominazione in considered_col_mapping.keys():
                colonna_impegni_slug = considered_col_mapping[colonna_denominazione]
                colonna_replaced_slug = colonna_impegni_slug.replace(old_subslug, new_subslug)
                c[4] = colonna_replaced_slug

        return

    def fill_in_voci(self):

        # fills in the voci mapping table using the Q4 impegni as reference to complete the
        #  q4 conto competenza, conto residui and q5 impegni, conto competenza, residui

        voci_q4_impegni = self.get_voci_titolo(cod_quadro='04', quadro_denominazione='QUADRO 4 - SPESE CORRENTI - (A) - IMPEGNI', slug_startswith='consuntivo-spese-impegni-')

        # creates a map that links voce_denominazione with voce_slug
        for voce_q4 in voci_q4_impegni:
            # skips voce with denominazione == di cui:
            if voce_q4[3] == 'di cui:':
                continue
            # if voce denominazione contains " di cui:" then removes the " di cui:"
            # so the voce "EXAMPLE di cui:" is associated to "EXAMPLE"

            if self.di_cui_string in voce_q4[3]:
                voce_q4[3] = voce_q4[3].replace(self.di_cui_string,"")

            self.fill_in_mapping_voci[voce_q4[3]] = voce_q4[6]

        # convert slugs for q4 conto competenza, residui
        self.convert_voci_slugs(cod_quadro='04', quadro_denominazione='QUADRO 4 - SPESE CORRENTI - (B) - PAGAMENTI IN CONTO COMPETENZA', old_subslug='impegni', new_subslug='pagamenti-in-conto-competenza')
        self.convert_voci_slugs(cod_quadro='04', quadro_denominazione='QUADRO 4 - SPESE CORRENTI - (C) - PAGAMENTI IN CONTO RESIDUI', old_subslug='impegni', new_subslug='pagamenti-in-conto-residui')

        # convert slugs for q5 impegni, conto competenza, residui
        self.convert_voci_slugs(cod_quadro='05', quadro_denominazione='QUADRO 5 - SPESE IN CONTO CAPITALE - (A) - IMPEGNI', old_subslug='impegni-spese-correnti', new_subslug='impegni-spese-per-investimenti')
        self.convert_voci_slugs(cod_quadro='05', quadro_denominazione='QUADRO 5 - SPESE IN CONTO CAPITALE - (B) - PAGAMENTI IN CONTO COMPETENZA', old_subslug='impegni-spese-correnti', new_subslug='pagamenti-in-conto-competenza-spese-per-investimenti')
        self.convert_voci_slugs(cod_quadro='05', quadro_denominazione='QUADRO 5 - SPESE IN CONTO CAPITALE - (C) - PAGAMENTI IN CONTO RESIDUI', old_subslug='impegni-spese-correnti', new_subslug='pagamenti-in-conto-residui-spese-per-investimenti')

    def fill_in_colonne(self):
        # fills in the colonne mapping table using the Q4 impegni as reference to complete the
        #  q4 conto competenza, conto residui and q5 impegni, conto competenza, residui

        colonne_q4_impegni = self.get_colonne_titolo(cod_quadro='04', quadro_denominazione = 'QUADRO 4 - SPESE CORRENTI - (A) - IMPEGNI')
        colonne_q5_impegni = self.get_colonne_titolo(cod_quadro='05', quadro_denominazione = 'QUADRO 5 - SPESE IN CONTO CAPITALE - (A) - IMPEGNI')

        # creates two mapping dictionaries for spese correnti / investimenti (q4/q5)
        for col_q4 in colonne_q4_impegni:
            self.fill_in_mapping_colonne['04'][col_q4[3]] = col_q4[4]

        for col_q5 in colonne_q5_impegni:
            self.fill_in_mapping_colonne['05'][col_q5[3]] = col_q5[4]

        self.convert_colonne_slugs(cod_quadro='04', quadro_denominazione='QUADRO 4 - SPESE CORRENTI - (B) - PAGAMENTI IN CONTO COMPETENZA', old_subslug='impegni', new_subslug='pagamenti-in-conto-competenza')
        self.convert_colonne_slugs(cod_quadro='04',quadro_denominazione='QUADRO 4 - SPESE CORRENTI - (C) - PAGAMENTI IN CONTO RESIDUI', old_subslug='impegni', new_subslug='pagamenti-in-conto-residui')

        # convert slugs for q5 impegni, conto competenza, residui
        self.convert_colonne_slugs(cod_quadro='05', quadro_denominazione='QUADRO 5 - SPESE IN CONTO CAPITALE - (B) - PAGAMENTI IN CONTO COMPETENZA', old_subslug='impegni-spese-per-investimenti', new_subslug='pagamenti-in-conto-competenza-spese-per-investimenti')
        self.convert_colonne_slugs(cod_quadro='05', quadro_denominazione='QUADRO 5 - SPESE IN CONTO CAPITALE - (C) - PAGAMENTI IN CONTO RESIDUI', old_subslug='impegni-spese-per-investimenti', new_subslug='pagamenti-in-conto-residui-spese-per-investimenti')



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
        self.bilancio_type = options['self.bilancio_type']

        if self.bilancio_type.lower() == 'c':
            self.bilancio_type = 'consuntivo'
        elif self.bilancio_type.lower() == 'p':
            self.bilancio_type = 'preventivo'
        else:
            self.logger.error("Bilancio type must be C or P")
            return

        if options['append'] is True:
            self.logger = logging.getLogger('management_append')


        # delete CodiceVoce for the specified bilancio, if any
        CodiceVoce.objects.filter(anno=int(self.bilancio_year), voce__slug__startswith=self.bilancio_type).delete()

        ###
        #   Mapping files from gdoc
        ###
        # connect to google account and fetch tree mapping and simple tree structure
        codes_map = gdocs.get_bilancio_codes_map(n_header_lines=1, force_google=force_google, bilancio_type=self.bilancio_type, bilancio_year=self.bilancio_year)

        # metadata voci
        # quadro_denominazione, titolo_denominazione , cat_cod, voce_denominazione, quadro_cod, voce_cod, voce_slug

        self.voci = codes_map['voci']
        # metadata colonne
        # quadro_denominazione, quadro_cod, col_cod, col_denominazione
        self.colonne = codes_map['colonne']

        # regroup colonne on (quadro_denominazione, quadro_cod)
        q_keygen = lambda x: (x[0], x[1] )
        colonne_regroup = dict((k,list(v)) for k,v in groupby(self.colonne, key=q_keygen))

        # function fill-in-voci creates the mapping for Q4 (conto competenza / conto residui) and Q5 (impegni /conto competenza / conto residui)
        # from Q4 impegni where the mapping has been made by the operator on the gdoc file

        self.fill_in_voci()
        self.fill_in_colonne()

        # write file voci_filled.csv: the complete mapping of voci codes with slugs
        gdocs.write_to_csv(path_name='bilancio_{0}_{1}'.format(self.bilancio_type, self.bilancio_year), contents={'voci_filled':self.voci, 'colonne_filled': self.colonne})

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

        # check insertion: have all the nodes of the bilancio tree been mapped?
        self.logger.info("Added {0} unique Voce slug".format(len(self.added_voce_slug)))

        if self.bilancio_type == 'consuntivo':
            tree_slugs = set(
                Voce.objects.get(slug=self.bilancio_type).get_descendants().\
                    exclude(slug__contains='consuntivo-entrate-cassa').\
                    exclude( slug__contains='consuntivo-spese-cassa').\
                    exclude(slug__contains='-spese-somma-funzioni').values_list('slug',flat=True))
        else:
            tree_slugs = set(
                Voce.objects.get(slug=self.bilancio_type).get_descendants().\
                    exclude(slug__contains='-spese-somma-funzioni').values_list('slug',flat=True))


        # gets the voci slugs that have not been mapped in the process

        not_mapped_slugs = sorted(tree_slugs - set(self.added_voce_slug))
        if len(not_mapped_slugs)>0:
            not_mapped_path = "data/gdocs_csv_cache/bilancio_{0}_{1}/{2}.csv".format(self.bilancio_type, self.bilancio_year, 'not_mapped_slugs')

            self.logger.warning("THERE ARE {0} VOCE SLUG FROM BILANCIO TREE HAS NOT BEEN MAPPED (Bilancio subtree has {1} nodes) ".format(len(not_mapped_slugs), len(tree_slugs)))
            self.logger.warning("{0} file written for check".format(not_mapped_path))


            file_not_mapped = open(not_mapped_path, mode='wb')
            for item in not_mapped_slugs:
                file_not_mapped.write("%s\n" % item)


        return