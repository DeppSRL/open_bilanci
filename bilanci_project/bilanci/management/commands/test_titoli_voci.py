# coding: utf-8
import logging
from pprint import pprint
from optparse import make_option
from django.core.management import BaseCommand
import itertools
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
        make_option('--force',
                    dest='force',
                    action='store_true',
                    default=False,
                    help='Checks for errors but continues even if errors are found'),
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
        force = options['force']

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

        references = gdocs.read_from_csv(folder, csv_base_dir='data/reference_test/')

        for bil_type in bilancio_types:
            gdoc_mapping = normalized_map[bil_type]

            # checks if the reference list has no repetitions
            reference_list = [tuple(l) for l in references[bil_type]]
            reference_set = set(reference_list)
            if len(reference_list) != len(reference_set):
                self.logger.critical("reference list not univoque for bilancio:{}".format(bil_type))
                exit()

            # remove the n-1 col from gdoc mapping:
            # this leaves us with
            # FOR TITOLI
            # tipo bilancio, quadro number, normalized titolo name (last col of GDOC)
            # FOR VOCI
            # tipo bilancio, quadro number, normalized titolo name,normalized voce name (last col of GDOC)

            x = ['',u'',None]
            if translation_type == 't':
                actual_mapping = set(r for r in ((row[0], row[1], row[3]) for row in gdoc_mapping) if r[idx] not in x)
            else:
                actual_mapping = set(r for r in ((row[0], row[1], row[2], row[4]) for row in gdoc_mapping) if r[idx] not in x)

            not_in_reference = actual_mapping-reference_set
            not_in_mapping= reference_set-actual_mapping

            if len(not_in_mapping):
                self.logger.error("Following rows not present in GDOC mapping")
                pprint(not_in_mapping)
                error_found=True

            if len(not_in_reference):
                self.logger.error("Following rows not present in REFERENCE mapping")
                pprint(not_in_reference)
                error_found=True

        if error_found:
            if force:
                self.logger.critical("The test encountered errors. Force flag is TRUE, so continue")
            else:
                self.logger.critical("The test encountered errors. Quit")