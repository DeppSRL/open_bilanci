# -*- coding: utf-8 -*-
"""
Tests the main functionalities of the tree_models module.
"""

import logging
import couchdb
from django.utils.unittest.case import TestCase
from bilanci import tree_models
from bilanci.models import Voce

__author__ = 'guglielmo'

class MakeTreeFromDictTestCase(TestCase):
    code = "2004_ROMA--3120700900"

    def setUp(self):

        # connect to couchdb bilanci_simple database
        couch_uri = 'http://staging:5984'
        self.couch_server = couchdb.Server(couch_uri)
        self.simple_couch = self.couch_server['bilanci_simple']

        # extract the doc corresponding to the city
        (self.year, self.city) = self.code.split("_")
        self.normalized_doc_id = "{}_{}".format(self.year, self.city)
        self.simplified_doc_id = self.city
        self.simp_doc = self.simple_couch[self.simplified_doc_id]

        # extract the python data structure for the given year
        city_budget = self.simple_couch.get(self.city)
        self.city_year_budget_dict = city_budget[str(self.year)]

        # get the mapping to the MPTT Voce class
        self.voci_dict = Voce.objects.get_dict_by_slug()

        self.logger = logging.getLogger('test')
        self.logger.setLevel(logging.INFO)

    def test_tree_is_of_correct_instance(self):
        city_year_budget_tree = tree_models.make_tree_from_dict(
            self.city_year_budget_dict['preventivo'], self.voci_dict,
            path=[u'preventivo']
        )
        self.assertIsInstance(city_year_budget_tree, tree_models.BilancioItem)

    def test_subtree_is_built_correctly(self):
        city_year_budget_tree = tree_models.make_tree_from_dict(
            self.city_year_budget_dict['preventivo']['ENTRATE']['Vendite e trasferimenti di capitali'],
            self.voci_dict,
            path=[u'preventivo', u'ENTRATE', u'Vendite e trasferimenti di capitali']
        )
        self.assertEqual(city_year_budget_tree.slug, u'preventivo-entrate-vendite-e-trasferimenti-di-capitali')
        self.assertEqual(len(city_year_budget_tree.children), 6)


    def test_subtree_handles_missing_slug_correctly(self):
        city_year_budget_tree = tree_models.make_tree_from_dict(
            self.city_year_budget_dict['consuntivo']['ENTRATE']['Riscossioni in conto competenza']['Entrate extratributarie']['Servizi pubblici'],
            self.voci_dict,
            path=[u'consuntivo', u'ENTRATE', u'Riscossioni in conto competenza', u'Entrate extratributarie', u'Servizi pubblici']
        )
        self.assertEqual(city_year_budget_tree.slug, u'consuntivo-entrate-riscossioni-in-conto-competenza-entrate-extratributarie-servizi-pubblici')
        self.assertEqual(len(city_year_budget_tree.children), 11)
