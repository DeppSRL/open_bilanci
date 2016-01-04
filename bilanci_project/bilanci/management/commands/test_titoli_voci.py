# coding: utf-8

import logging
import time
from optparse import make_option
from django.core.management import BaseCommand, call_command
from django.conf import settings
from bilanci.utils import couch
from bilanci.utils import gdocs, email_utils

__author__ = 'stefano'


class Command(BaseCommand):
    """
    Test about titoli and voci normalization
    1) checks that all titoli/voci present in the reference CSV are mapped in the GDOC
    2) checks that all titoli/voci present in the GDOC are present in the reference CSV
    """

    option_list = BaseCommand.option_list + (
        make_option('--type',
                    dest='type',
                    help='Select translation type: [(v)oce | (t)itolo]'),
        make_option('--force-google',
                    dest='force_google',
                    action='store_true',
                    default=False,
                    help='Force reloading mapping files from gdocs (invalidate the csv cache)'),
    )

    help = """
    Test about titoli and voci normalization
    1) checks that all titoli/voci present in the reference CSV are mapped in the GDOC
    2) checks that all titoli/voci present in the GDOC are present in the reference CSV"""

    logger = logging.getLogger('management')

    def handle(self, *args, **options):
        bilancio_types = ['preventivo', 'consuntivo']

        verbosity = options['verbosity']
        force_google = options['force_google']

        if verbosity == '0':
            self.logger.setLevel(logging.ERROR)
        elif verbosity == '1':
            self.logger.setLevel(logging.WARNING)
        elif verbosity == '2':
            self.logger.setLevel(logging.INFO)
        elif verbosity == '3':
            self.logger.setLevel(logging.DEBUG)

        # type option, different values are accepted:
        #  v, V, voce, Voce, VOCE or
        #  t, T, titolo, Titolo, TITOLO, Title
        if 'type' not in options:
            raise Exception("Missing type parameter")
        if options['type'].lower()[0] not in ('v', 't'):
            raise Exception("Wrong type parameter value (voce|titolo)")
        translation_type = options['type'][0].lower()

        # reads the references list from CSV file
        if translation_type == 't':
            filename = "titoli/{}.csv"
            idx = 2
        else:
            filename = "voci/{}.csv"
            idx = 3

        ###
        #   Mapping files from gdoc
        ###
        # connect to Drive and get the mapping: the original titolo/voce and the mapping
        normalized_map = gdocs.get_normalized_map(translation_type, n_header_lines=2, force_google=force_google)

        normalized_sheet = {'preventivo': [(row[idx], row[idx + 1]) for row in normalized_map['preventivo']],
                            'consuntivo': [(row[idx], row[idx + 1]) for row in normalized_map['consuntivo']],
        }

        for bil_type in bilancio_types:
            reference_list = gdocs.read_from_csv('reference_test',csv_base_dir='data/')
            from pprint import pprint

            pprint(reference_list)
            # pprint(normalized_sheet)




