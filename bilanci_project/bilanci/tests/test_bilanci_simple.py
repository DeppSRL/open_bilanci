# -*- coding: utf-8 -*-
"""
Tests the consistence of the bilanci_simple tree in the couchdb instance.
"""
from collections import OrderedDict
import logging
import couchdb
from django.conf import settings
from bilanci.tree_dict_models import deep_sum
from bilanci.utils.comuni import FLMapper
from django.test import TestCase

__author__ = 'guglielmo'

class BilanciSimpleBaseTestCaseMixin(object):
    code = ''

    def setUp(self):
        couch_uri = 'http://staging:5984'
        self.couch_server = couchdb.Server(couch_uri)

        self.norm_couch = self.couch_server['bilanci_voci']
        self.simple_couch = self.couch_server['bilanci_simple']

        self.entrate_sections = OrderedDict([
            ('Accertamenti', 0),
            ('Riscossioni in conto competenza', 1),
            ('Riscossioni in conto residui', 2),
        ])

        self.spese_sections = OrderedDict([
            ('Impegni', 0),
            ('Pagamenti in conto competenza', 1),
            ('Pagamenti in conto residui', 2),
        ])

        (self.year, self.city) = self.code.split("_")
        self.normalized_doc_id = "{}_{}".format(self.year, self.city)
        self.simplified_doc_id = self.city
        self.norm_doc = self.norm_couch[self.normalized_doc_id]
        self.simp_doc = self.simple_couch[self.simplified_doc_id]

        self.logger = logging.getLogger('test')
        self.logger.setLevel(logging.INFO)


    def test_normalized_couch_doc_exists(self):
        """
        couch db connection is correct and document exists
        """
        self.assertTrue(self.normalized_doc_id in self.norm_couch, "Could not find {}".format(self.normalized_doc_id))


    def test_simplified_couch_doc_exists(self):
        """
        couch db connection is correct and document exists
        """
        self.assertTrue(self.simplified_doc_id in self.simple_couch, "Could not find {}".format(self.simplified_doc_id))


    def test_totali_consuntivo_spese(self):
        """
        totals for 1st level sections of the consuntivo/spese in the normalized tree (quadri 3, 4, 5)
        are compared with the corresponding values in the simplified tree
        """

        # totali will hold a list of all voices to be compared
        # norm refers to the normalized tree
        # simp refers to the simple tree
        totali = []

        # quadro 3
        # section_name and section_idx contains the Impegni/Competenze/Residui name and indexes
        for section_name, section_idx in self.spese_sections.items():
            totali.extend([
                {'norm': ('consuntivo', '03',
                          'quadro-3-riepilogo-generale-delle-spese',
                          'data', 'totale generale delle spese', section_idx),
                 'simp': ('consuntivo', 'SPESE', section_name, 'TOTALE')},
                {'norm': ('consuntivo', '03',
                          'quadro-3-riepilogo-generale-delle-spese',
                          'data', 'titolo i - spese correnti', section_idx),
                 'simp': ('consuntivo', 'SPESE', section_name, 'Spese correnti')},
                {'norm': ('consuntivo', '03',
                          'quadro-3-riepilogo-generale-delle-spese',
                          'data', 'titolo ii - spese in c/capitale', section_idx),
                 'simp': ('consuntivo', 'SPESE', section_name, 'Spese per investimenti')},
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
        totali.extend([
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
        totali.extend([
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

        for tot in totali:
            # extract year section from the simple doc (simple docs contain all years)
            tot_simp = self.simp_doc[self.year]
            tot_norm = self.norm_doc

            # drill through the tree to fetch the leaf value in tot['simp']
            for t in tot['simp']:
                tot_simp = tot_simp[t]

            # drill through the tree to fetch the leaf value in tot['norm']
            for t in tot['norm']:
                if t == 'totale':
                    try:
                        tot_norm = tot_norm['totale']
                    except KeyError:
                        tot_norm = tot_norm['totali']
                else:
                    tot_norm = tot_norm[t]

            # transform the string representation in the normalized doc,
            # into an integer (used in the simplified doc)
            # so that the comparison is possible
            tot_norm = int(round(float(tot_norm.replace('.', '').replace(',','.'))))

            self.assertEqual(tot_simp, tot_norm, "Totals are different.\n norm: {0}={1}, \n simp: {2}={3}".format(
                tot['norm'], tot_norm, tot['simp'], tot_simp
            ))


    def test_totali_consuntivo_entrate(self):
        """
        totals for 1st level sections of the consuntivo/entrate in the normalized tree (quadro 2)
        are compared with the corresponding values in the simplified tree
        """

        # totali will hold a list of all voices to be compared
        # norm refers to the normalized tree
        # simp refers to the simple tree
        for section_name, section_idx in self.entrate_sections.items():
            totali = [
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
                          'data', 'totale entrate derivanti da  alienazione, trasferimenti di capitali e da riscossioni di crediti', section_idx),
                 'simp': ('consuntivo', 'ENTRATE', section_name, 'Vendite e trasferimenti di capitale', 'TOTALE')},
                {'norm': ('consuntivo', '02',
                          'quadro-2-entrate-titolo-v-entrate-derivanti-da-accensione-di-prestiti',
                          'data', 'totale entrate derivanti da  accensione di prestiti', section_idx),
                 'simp': ('consuntivo', 'ENTRATE', section_name, 'Prestiti')},
                {'norm': ('consuntivo', '02',
                          'quadro-2-entrate-titolo-vi-entrate-da-servizi-per-conto-di-terzi',
                          'data', 'totale entrate  da servizi per conto di terzi', section_idx),
                 'simp': ('consuntivo', 'ENTRATE', section_name, 'Entrate per conto terzi')},
            ]

            for tot in totali:
                # extract year section from the simple doc (simple docs contain all years)
                tot_simp = self.simp_doc[self.year]
                tot_norm = self.norm_doc

                # drill through the tree to fetch the leaf value in tot['simp']
                for t in tot['simp']:
                    tot_simp = tot_simp[t]

                # drill through the tree to fetch the leaf value in tot['simp']
                for t in tot['norm']:
                    tot_norm = tot_norm[t]

                # transform the string representation in the normalized doc,
                # into an integer (used in the simplified doc)
                # so that the comparison is possible
                tot_norm = int(round(float(tot_norm.replace('.', '').replace(',','.'))))

                self.assertEqual(tot_simp, tot_norm, "Totals are different. norm: {0}, simp: {1}".format(
                    tot['norm'], tot['simp']
                ))


    def test_somme_consuntivo_entrate(self):
        """
        Tests the sum of sections of the entrate tree, against the totals.
        This verifies the consistency of the simplified tree,
        and, indirectly, the completeness and correctness of the
        data fetched from the normalized tree.
        """
        nodes = []
        for section_name in self.entrate_sections.keys():
            nodes.extend([
                ('consuntivo', 'ENTRATE', section_name, 'Imposte e tasse'),
                ('consuntivo', 'ENTRATE', section_name, 'Imposte e tasse', 'Imposte'),
                ('consuntivo', 'ENTRATE', section_name, 'Imposte e tasse', 'Tasse'),
                ('consuntivo', 'ENTRATE', section_name, 'Contributi pubblici'),
                ('consuntivo', 'ENTRATE', section_name, 'Entrate extratributarie'),
                ('consuntivo', 'ENTRATE', section_name, 'Entrate extratributarie', 'Servizi pubblici'),
                ('consuntivo', 'ENTRATE', section_name, 'Entrate extratributarie', 'Proventi di beni dell\'ente'),
                ('consuntivo', 'ENTRATE', section_name, 'Vendite e trasferimenti di capitale'),
                ('consuntivo', 'ENTRATE', section_name, 'Vendite e trasferimenti di capitale', 'Trasferimenti di capitali da privati'),
            ])

        # set level to logging.DEBUG to show debug messages
        self.logger.setLevel(logging.INFO)
        self.logger.debug(" ")
        for node in nodes:
            simp = self.simp_doc[self.year]
            for t in node:
                simp = simp[t]

            somma = deep_sum(simp)
            totale = simp['TOTALE']

            msg = u"section: {0}, node: {1}, totale: {2}, somma: {3}".format(
                node[2], node[-1], totale, somma
            )
            self.logger.debug(msg)
            self.assertEqual(totale, somma, msg)


    def test_somme_consuntivo_spese(self):
        """
        Tests the sum of sections of the spese trees, against the totals.
        This verifies the consistency of the simplified tree,
        and, indirectly, the completeness and correctness of the
        data fetched from the normalized tree.
        """
        nodes = []
        for section_name in self.spese_sections.keys():
            for tipo_spese in ('Spese correnti', 'Spese per investimenti'):
                nodes.extend([
                    ('consuntivo', 'SPESE', section_name, tipo_spese, 'funzioni', 'Amministrazione'),
                    ('consuntivo', 'SPESE', section_name, tipo_spese, 'funzioni', 'Sociale'),
                    ('consuntivo', 'SPESE', section_name, tipo_spese, 'funzioni', 'Territorio e ambiente'),
                    ('consuntivo', 'SPESE', section_name, tipo_spese, 'funzioni', u'Viabilità e trasporti'),
                    ('consuntivo', 'SPESE', section_name, tipo_spese, 'funzioni', 'Istruzione'),
                    ('consuntivo', 'SPESE', section_name, tipo_spese, 'funzioni', 'Cultura'),
                    ('consuntivo', 'SPESE', section_name, tipo_spese, 'funzioni', 'Sport'),
                ])

        # set level to logging.DEBUG to show debug messages
        self.logger.setLevel(logging.INFO)
        self.logger.debug(" ")
        for node in nodes:
            simp = self.simp_doc[self.year]
            for t in node:
                simp = simp[t]

            somma = deep_sum(simp)
            totale = simp['TOTALE']

            msg = u"section: {0}-{1}, node: {2}, totale: {3}, somma: {4}".format(
                node[2], node[3], node[-1], totale, somma
            )
            self.logger.debug(msg)
            self.assertEqual(totale, somma, msg)

        # tests spese correnti and spese per investimenti global totals (for funzioni and interventi)

        # set level to logging.DEBUG to show debug messages
        self.logger.setLevel(logging.INFO)
        self.logger.debug(" ")
        for section_name in self.spese_sections.keys():
            for tipo_spese in ('Spese correnti', 'Spese per investimenti'):
                node = self.simp_doc[self.year]['consuntivo']['SPESE'][section_name][tipo_spese]
                totale = node['TOTALE']
                somma_funzioni = deep_sum(node['funzioni'])
                somma_interventi = deep_sum(node['interventi'])
                self.logger.debug(u"section: {0}, node: {1}, totale: {2}, somma_funzioni: {3}, somma_interventi: {4}".format(
                    section_name, tipo_spese, totale, somma_funzioni, somma_interventi
                ))
                self.assertEqual(totale, somma_funzioni)
                self.assertEqual(totale, somma_interventi)


# To avoid repetitions in the testing code, as:
#
# class Roma2006TestCase(SimplifyBaseTestCaseMixin, TestCase):
#     code = "2006_ROMA--3120700900"
#
# class Roma2008TestCase(SimplifyBaseTestCaseMixin, TestCase):
#     code = "2008_ROMA--3120700900"
#
# ...
#
# and to allow for *parametric testing*, a bit of meta-programming is used.
#
# This loop generates TestCase subclasses, so that the python manage.py test
# can discover and launch the test suite for all of them.
#
# Invocation:
#     python manage.py test bilanci --settings=bilanci.settings.testnodb [-v2]
mapper = FLMapper(settings.LISTA_COMUNI_PATH)
for year in (2004, 2008, 2010, 2012):
    for city_name in ('Roma', 'Milano'):
        name = "{}{}TestCase".format(city_name, year)
        city = mapper.get_city(city_name)
        code = "{}_{}".format(year, city)

        Class = type(name, (BilanciSimpleBaseTestCaseMixin, TestCase), dict(city=city, code=code))
        globals()[name] = Class

# The Class variable contains a *TestCase type, at this point
# so we clear it, in order to avoid repeating an already
# performed TestCase
Class = None