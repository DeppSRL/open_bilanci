import logging
from optparse import make_option
from django.conf import settings
from django.core.management import BaseCommand
from bs4 import BeautifulSoup
from bilanci.utils import gdocs


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (

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

        dryrun = options['dryrun']
        force_google = options['force_google']

        if options['append'] is True:
            self.logger = logging.getLogger('management_append')



        ###
        #   Mapping files from gdoc
        ###
        # connect to google account and fetch tree mapping and simple tree structure
        codes_map = gdocs.get_bilancio_codes_map(n_header_lines=2, force_google=force_google)
