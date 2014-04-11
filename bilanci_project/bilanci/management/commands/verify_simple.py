from django.utils.text import slugify
import math
from bilanci.tree_dict_models import deep_sum
from bilanci.utils import couch, nearly_equal
from bilanci.utils.comuni import FLMapper

from django.test import TestCase
from django.core.management import BaseCommand
from django.conf import settings

from collections import OrderedDict
from optparse import make_option
import logging

__author__ = 'guglielmo'

class Command(BaseCommand, TestCase):

    option_list = BaseCommand.option_list + (
        make_option('--years',
                    dest='years',
                    default='',
                    help='Years to fetch. From 2002 to 2012. Use one of this formats: 2012 or 2003-2006 or 2002,2004,2006'),
        make_option('--cities',
                    dest='cities',
                    default='',
                    help='Cities codes or slugs. Use comma to separate values: Roma,Napoli,Torino or  "All"'),
        make_option('--couchdb-server',
                    dest='couchdb_server',
                    default=settings.COUCHDB_DEFAULT_SERVER,
                    help='CouchDB server to connect to (defaults to staging).'),

    )

    help = 'Verify the bilanci_simple values and sums.'

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

        cities_codes = options['cities']
        if not cities_codes:
            raise Exception("Missing city parameter")

        mapper = FLMapper(settings.LISTA_COMUNI_PATH)
        cities = mapper.get_cities(cities_codes)
        if cities_codes.lower() != 'all':
            self.logger.info("Processing cities: {0}".format(cities))

        years = options['years']
        if not years:
            raise Exception("Missing years parameter")

        if "-" in years:
            (start_year, end_year) = years.split("-")
            years = range(int(start_year), int(end_year)+1)
        else:
            years = [int(y.strip()) for y in years.split(",") if 2001 < int(y.strip()) < 2014]

        if not years:
            raise Exception("No suitable year found in {0}".format(years))

        self.logger.info("Processing years: {0}".format(years))

        couchdb_server_name = options['couchdb_server']
        if couchdb_server_name not in settings.COUCHDB_SERVERS:
            raise Exception("Unknown couchdb server name.")

        ###
        #   Couchdb connections
        ###
        couchdb_server_alias = options['couchdb_server']
        if couchdb_server_alias not in settings.COUCHDB_SERVERS:
            raise Exception("Unknown couchdb server alias.")

        # hook to simple DB
        simple_db_name = 'bilanci_simple'
        simple_db = couch.connect(
            simple_db_name,
            couchdb_server_settings=settings.COUCHDB_SERVERS[couchdb_server_alias]
        )
        self.logger.info("Hooked to simple DB: {0}".format(simple_db_name))

        # hook to normalized DB (for comparisons)
        norm_db_name = 'bilanci_voci'
        norm_db = couch.connect(
            norm_db_name,
            couchdb_server_settings=settings.COUCHDB_SERVERS[couchdb_server_alias]
        )
        self.logger.info("Hooked to normalized DB: {0}".format(norm_db_name))


        entrate_sections = OrderedDict([
            ('Accertamenti', 0),
            ('Riscossioni in conto competenza', 1),
            ('Riscossioni in conto residui', 2),
        ])

        spese_sections = OrderedDict([
            ('Impegni', 0),
            ('Pagamenti in conto competenza', 1),
            ('Pagamenti in conto residui', 2),
        ])

        # totali_* will hold a list of all voices to be compared
        # norm refers to the normalized tree
        # simp refers to the simple tree
        totali_preventivo_entrate = [
            {'norm': ('preventivo', '02',
                      'quadro-2-entrate-entrate-tributarie',
                      'data', 'totale titolo i', 0),
             'simp': ('preventivo', 'ENTRATE', 'Imposte e tasse', 'TOTALE')},
            {'norm': ('preventivo', '02',
                      'quadro-2-entrate-entrate-derivanti-da-contributi-e-trasferimenti-correnti-dello-stato-della-regione-e-di-altri-enti-pubblici-anche-in-rapporto-funzioni-delegate-dalla-regione',
                      'data', 'totale titolo ii', 0),
             'simp': ('preventivo', 'ENTRATE', 'Contributi pubblici', 'TOTALE')},
            {'norm': ('preventivo', '02',
                      'quadro-2-entrate-entrate-extratributarie',
                      'data', 'totale titolo iii', 0),
             'simp': ('preventivo', 'ENTRATE', 'Entrate extratributarie', 'TOTALE')},
            {'norm': ('preventivo', '02',
                      'quadro-2-entrate-entrate-derivanti-da-alienazione-da-trasferimenti-di-capitali-e-da-riscossioni-di-crediti',
                      'data', 'totale titolo iv', 0),
             'simp': ('preventivo', 'ENTRATE', 'Vendite e trasferimenti di capitali', 'TOTALE')},
            {'norm': ('preventivo', '02',
                      'quadro-2-entrate-entrate-derivanti-da-accensioni-di-prestiti',
                      'data', 'totale titolo v', 0),
             'simp': ('preventivo', 'ENTRATE', 'Prestiti')},
            {'norm': ('preventivo', '02',
                      'quadro-2-entrate-entrate-derivanti-da-servizi-per-conto-di-terzi',
                      'data', 'totale titolo vi', 0),
             'simp': ('preventivo', 'ENTRATE', 'Entrate per conto terzi')},
        ]

        totali_consuntivo_entrate = []

        for section_name, section_idx in entrate_sections.items():
            totali_consuntivo_entrate.extend([
                {'norm': ('consuntivo', '02',
                          'quadro-2-entrate-titolo-i-entrate-tributarie',
                          'data', 'totale  entrate  tributarie', section_idx),
                 'simp': ('consuntivo', 'ENTRATE', section_name, 'Imposte e tasse', 'TOTALE')},
                {'norm': ('consuntivo', '02',
                          'quadro-2-entrate-titolo-ii-entrate-derivanti-da-contributi-e-trasferimenti-correnti',
                          'data', 'totale entrate derivanti da contributi e trasferimenti correnti', section_idx),
                 'simp': ('consuntivo', 'ENTRATE', section_name, 'Contributi pubblici', 'TOTALE')},
                {'norm': ('consuntivo', '02',
                          'quadro-2-entrate-titolo-iii-entrate-extratributarie',
                          'data', 'totale entrate extratributarie', section_idx),
                 'simp': ('consuntivo', 'ENTRATE', section_name, 'Entrate extratributarie', 'TOTALE')},
                {'norm': ('consuntivo', '02',
                          'quadro-2-entrate-titolo-iv-entrate-derivanti-da-alienazione-da-trasfer-di-capitali-e-da-riscossioni-di-crediti',
                          'data', 'totale entrate derivanti da alienazione, trasferimenti di capitali e da riscossioni di crediti', section_idx),
                 'simp': ('consuntivo', 'ENTRATE', section_name, 'Vendite e trasferimenti di capitali', 'TOTALE')},
                {'norm': ('consuntivo', '02',
                          'quadro-2-entrate-titolo-v-entrate-derivanti-da-accensione-di-prestiti',
                          'data', 'totale entrate derivanti da accensione di prestiti', section_idx),
                 'simp': ('consuntivo', 'ENTRATE', section_name, 'Prestiti')},
                {'norm': ('consuntivo', '02',
                          'quadro-2-entrate-titolo-vi-entrate-da-servizi-per-conto-di-terzi',
                          'data', 'totale entrate  da servizi per conto di terzi', section_idx),
                 'simp': ('consuntivo', 'ENTRATE', section_name, 'Entrate per conto terzi')},
            ])


        totali_consuntivo_spese = []

        # quadro 3
        # section_name and section_idx contains the Impegni/Competenze/Residui name and indexes
        for section_name, section_idx in spese_sections.items():
            totali_consuntivo_spese.extend([
                {'norm': ('consuntivo', '03',
                          'quadro-3-riepilogo-generale-delle-spese',
                          'data', 'totale generale delle spese', section_idx),
                 'simp': ('consuntivo', 'SPESE', section_name, 'TOTALE')},
                {'norm': ('consuntivo', '03',
                          'quadro-3-riepilogo-generale-delle-spese',
                          'data', 'titolo i - spese correnti', section_idx),
                 'simp': ('consuntivo', 'SPESE', section_name, 'Spese correnti', 'TOTALE')},
                {'norm': ('consuntivo', '03',
                          'quadro-3-riepilogo-generale-delle-spese',
                          'data', 'titolo ii - spese in c/capitale', section_idx),
                 'simp': ('consuntivo', 'SPESE', section_name, 'Spese per investimenti', 'TOTALE')},
                {'norm': ('consuntivo', '03',
                          'quadro-3-riepilogo-generale-delle-spese',
                          'data', 'titolo iii - spese per rimborso di prestiti', section_idx),
                 'simp': ('consuntivo', 'SPESE', section_name, 'Prestiti')},
                {'norm': ('consuntivo', '03',
                          'quadro-3-riepilogo-generale-delle-spese',
                          'data', 'titolo iv - spese per servirzi per conto di terzi', section_idx),
                 'simp': ('consuntivo', 'SPESE', section_name, 'Spese per conto terzi')},
            ])

        # quadro 4
        totali_consuntivo_spese.extend([
            {'norm': ('consuntivo', '04',
                      'quadro-4-a-impegni',
                      'data', 'totale', -1),
             'simp': ('consuntivo', 'SPESE', 'Impegni', 'Spese correnti', 'TOTALE')},
            {'norm': ('consuntivo', '04',
                      'quadro-4-b-pagamenti-in-conto-competenza',
                      'data', 'totali', -1),
             'simp': ('consuntivo', 'SPESE', 'Pagamenti in conto competenza', 'Spese correnti', 'TOTALE')},
            {'norm': ('consuntivo', '04',
                      'quadro-4-c-pagamenti-in-conto-residui',
                      'data', 'totali', -1),
             'simp': ('consuntivo', 'SPESE', 'Pagamenti in conto residui', 'Spese correnti', 'TOTALE')},
        ])

        # quadro 5
        totali_consuntivo_spese.extend([
            {'norm': ('consuntivo', '05',
                      'quadro-5-a-impegni',
                      'data', 'totale', -1),
             'simp': ('consuntivo', 'SPESE', 'Impegni', 'Spese per investimenti', 'TOTALE')},
            {'norm': ('consuntivo', '05',
                      'quadro-5-b-pagamenti-in-conto-competenza',
                      'data', 'totale', -1),
             'simp': ('consuntivo', 'SPESE', 'Pagamenti in conto competenza', 'Spese per investimenti', 'TOTALE')},
            {'norm': ('consuntivo', '05',
                      'quadro-5-c-pagamenti-in-conto-residui',
                      'data', 'totale', -1),
             'simp': ('consuntivo', 'SPESE', 'Pagamenti in conto residui', 'Spese per investimenti', 'TOTALE')},
        ])


        for city in cities:

            for year in years:
                self.logger.info("Processing city of {0}, year {1}".format(
                    city, year
                ))
                code = "{}_{}".format(year, city)

                norm_doc_id = "{}_{}".format(year, city)
                simple_doc_id = city

                # both documents need to exist in the dbs
                self.assertTrue(self.test_couch_doc_exists(norm_db, norm_doc_id),
                                "Could not find {}".format(norm_doc_id))
                self.assertTrue(self.test_couch_doc_exists(simple_db, simple_doc_id))

                norm_doc = norm_db[norm_doc_id]
                simple_doc = simple_db[simple_doc_id]

                # preventivo tests
                if len(simple_doc[str(year)]['preventivo'].keys()) > 0:
                    self.test_totali(totali_preventivo_entrate, simple_doc, norm_doc, year)

                    for tipo_spese in (u'Spese correnti', u'Spese per investimenti'):
                        node = simple_doc[str(year)]['preventivo']['SPESE'][tipo_spese]
                        label = u"/Preventivo/{0}".format(tipo_spese)
                        self.test_totale_funzioni_interventi(label, node, year)

                # consuntivo tests
                if len(simple_doc[str(year)]['consuntivo'].keys()) > 0:
                    self.test_totali(totali_consuntivo_entrate, simple_doc, norm_doc, year)
                    self.test_totali(totali_consuntivo_spese, simple_doc, norm_doc, year)
                    for section_name in spese_sections.keys():
                        for tipo_spese in ('Spese correnti', 'Spese per investimenti'):
                            node = simple_doc[str(year)]['consuntivo']['SPESE'][section_name][tipo_spese]
                            label = u"/Consuntivo/{0}/{1}".format(section_name, tipo_spese)
                            self.test_totale_funzioni_interventi(label, node, year)



    ###
    # TESTS
    ###

    def test_couch_doc_exists(self, couch_db, doc_id):
        """
        couch db connection is correct and document exists
        """
        return doc_id in couch_db


    ###
    # totals for first level sections in normalized and
    # simplified trees are compared
    ###
    def test_totali(self, totali, simple_doc, norm_doc, year):
        """
        totals for 1st level sections of the preventivo/entrate in the normalized tree (quadro 2)
        are compared with the corresponding values in the simplified tree
        """

        for tot in totali:
            # extract year section from the simple doc (simple docs contain all years)
            tot_simp = simple_doc[str(year)]
            tot_norm = norm_doc

            # drill through the tree to fetch the leaf value in tot['simp']
            for t in tot['simp']:
                tot_simp = tot_simp[t]

            # drill through the tree to fetch the leaf value in tot['simp']
            # catch exception om totale/totali, trying both before failing
            # in the normalized tree
            for t in tot['norm']:
                if t == 'totale':
                    try:
                        tot_norm = tot_norm['totale']
                    except KeyError:
                        try:
                            tot_norm = tot_norm['totali']
                        except KeyError:
                            # log a warning and break away from the inner for loop
                            # do not execute the else section
                            self.logger.warning(
                                "totale/i key not found in bilanci_voce. node: {0}".format(
                                    tot['norm']
                                )
                            )
                            break
                else:
                    tot_norm = tot_norm[t]
            else:
                # transform the string representation in the normalized doc,
                # into an integer (used in the simplified doc)
                # so that the comparison is possible
                tot_norm = int(round(float(tot_norm.replace('.', '').replace(',','.'))))

                if tot_simp != tot_norm:
                    self.logger.warning("Totals are different.\n\tnorm val:{0}, node: {1}\n\tsimp val:{2}, node: {3}".format(
                        tot_norm, tot['norm'],
                        tot_simp, tot['simp'],
                    ))


    ###
    # sum of funzioni, interventi and the explicit totals in
    # the simplified tree are compared
    ###
    def test_totale_funzioni_interventi(self, simple_tree_label, simple_tree_node, year):

        totale = simple_tree_node['TOTALE']
        somma_funzioni = deep_sum(simple_tree_node['funzioni'])
        somma_interventi = deep_sum(simple_tree_node['interventi'])

        if self.nearly_equal(totale, somma_interventi) and \
           self.nearly_equal(totale, somma_funzioni):
            self.logger.debug(u"node: {0}. OK. totale: {1}".format(
                simple_tree_label, totale
            ))
        else:
            self.logger.warning(u"\nnode: {0}. NOT OK.\n  totale:\t\t {1}\n  somma_funzioni:\t {2}\n  somma_interventi:\t {3}".format(
                simple_tree_label, totale, somma_funzioni, somma_interventi
            ))

            # dump non-matching details to logger
            if not self.nearly_equal(totale, somma_funzioni):
                _ = deep_sum(simple_tree_node['funzioni'], logger=self.logger)
            if not self.nearly_equal(totale, somma_interventi):
                _ = deep_sum(simple_tree_node['interventi'], logger=self.logger)



    def nearly_equal(self, a, b):
        """
        Return true if the numbers are equals or close matches
        """
        return nearly_equal(a, b, threshold=settings.NEARLY_EQUAL_THRESHOLD)