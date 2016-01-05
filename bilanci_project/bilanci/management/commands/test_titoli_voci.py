# coding: utf-8
import logging
from pprint import pprint
from optparse import make_option
from django.core.management import BaseCommand
from bilanci.utils import gdocs

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
        error_found = False
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
            folder = "titoli_map"
            idx = 2
        else:
            folder = "voci_map"
            idx = 3

        ###
        #   Mapping files from gdoc
        ###
        # connect to Drive and get the mapping: the original titolo/voce and the mapping
        normalized_map = gdocs.get_normalized_map(translation_type, n_header_lines=2, force_google=force_google)


        references = gdocs.read_from_csv(folder,csv_base_dir='data/reference_test/')

        for bil_type in bilancio_types:
            gdoc_mapping = normalized_map[bil_type]

            # checks if the reference list has no repetitions
            reference_list =[tuple(l) for l in references[bil_type]]
            reference_set = set(reference_list)
            if len(reference_list)!=len(reference_set):
                self.logger.error("reference list not univoque for bilancio:{}".format(bil_type))
                exit()

            for unique_row in references[bil_type]:
                found = False
                for gdoc_row in gdoc_mapping:

                    normalized = gdoc_row[:idx]
                    normalized.append(gdoc_row[idx+1])
                    if normalized == unique_row:
                        found = True
                        break

                if not found:
                    self.logger.critical(u"Simplified row {} not found in GDOC map ".format(unique_row))
                    error_found = True

        if error_found:
            self.logger.critical("The test encountered errors. Quit")