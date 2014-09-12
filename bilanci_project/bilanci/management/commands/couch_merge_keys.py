# coding: utf-8

import logging
from optparse import make_option
from couchdb.http import ResourceNotFound
from django.core.management import BaseCommand
from django.conf import settings
from bilanci.utils import couch
from bilanci.utils import gdocs
from bilanci.utils.comuni import FLMapper

__author__ = 'stefano'

class Command(BaseCommand):
    """
    get json data from couchdb view
    transform json view into table
    get data from google drive spreadsheet
    merge the two tables
    """

    option_list = BaseCommand.option_list + (
        make_option('--dry-run',
                    dest='dryrun',
                    action='store_true',
                    default=False,
                    help='Set the dry-run command mode: nothing is written in the couchdb'),

        make_option('--couchdb-server',
                    dest='couchdb_server',
                    default=settings.COUCHDB_DEFAULT_SERVER,
                    help='CouchDB server to connect to (defaults to staging).'),

        make_option('--type',
                    dest='type',
                    help='Select translation type: [(v)oce | (t)itolo | (s)imple ]'),

        make_option('--tipobilancio',
                    dest='tipobilancio',
                    help='Select bilancio type: [(p)reventivo | (c)onsuntivo ]'),

        make_option('--output',
                    dest='output',
                    help='Output file. Example: /output/myfile.csv'),

        make_option('--append',
                    dest='append',
                    action='store_true',
                    default=False,
                    help='Use the log file appending instead of overwriting (used when launching shell scripts)'),
    )

    help = 'Merges the couchdb view and the related Gdoc and merges view keys and gdoc rows'

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

        if options['append'] is True:
            self.logger = logging.getLogger('management_append')



