import pprint
import couchdb
from django.test import TestCase

__author__ = 'guglielmo'

class SimplifyBaseTestCaseMixin(object):
    def setUp(self):
        couch_uri = 'http://staging:5984'
        self.couch_server = couchdb.Server(couch_uri)

        self.norm_couch = self.couch_server['bilanci_voci']
        self.simple_couch = self.couch_server['bilanci_simple']


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


    def test_totali_consuntivo_entrate(self):
        """
        totals for 1st level sections of the entrate consuntivo subtree are compared

        normalized and simplified totals
        """
        sections = {
            'Accertamenti': 0,
            'Riscossioni in conto competenza': 1,
            'Riscossioni in conto residui': 2,
        }
        for section_name, section_idx in sections.items():
            totali = [
                {'norm': ('consuntivo', '02',
                          'quadro-2-entrate-titolo-vi-entrate-da-servizi-per-conto-di-terzi',
                          'data', 'totale generale delle entrate', section_idx),
                 'simp': ('consuntivo', 'ENTRATE', section_name, 'TOTALE')},
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
                tot_simp = self.simp_doc[self.year]
                tot_norm = self.norm_doc
                for t in tot['simp']:
                    tot_simp = tot_simp[t]
                for t in tot['norm']:
                    tot_norm = tot_norm[t]
                tot_norm = int(tot_norm.replace(',00', '').replace('.',''))

                self.assertEqual(tot_simp, tot_norm, "Totals are different. norm: {0}, simp: {1}".format(
                    tot['norm'], tot['simp']
                ))





class Roma2004TestCase(SimplifyBaseTestCaseMixin, TestCase):

    def setUp(self):
        self.year = '2004'
        super(Roma2004TestCase, self).setUp()
        self.normalized_doc_id = "{}_ROMA--3120700900".format(self.year)
        self.simplified_doc_id = 'ROMA--3120700900'
        self.norm_doc = self.norm_couch[self.normalized_doc_id]
        self.simp_doc = self.simple_couch[self.simplified_doc_id]


class Roma2008TestCase(SimplifyBaseTestCaseMixin, TestCase):

    def setUp(self):
        self.year = '2008'
        super(Roma2008TestCase, self).setUp()
        self.normalized_doc_id = "{}_ROMA--3120700900".format(self.year)
        self.simplified_doc_id = 'ROMA--3120700900'
        self.norm_doc = self.norm_couch[self.normalized_doc_id]
        self.simp_doc = self.simple_couch[self.simplified_doc_id]

