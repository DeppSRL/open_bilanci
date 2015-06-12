import logging
from optparse import make_option
from pprint import pprint
from django.conf import settings
from django.core.management import BaseCommand
from bilanci.utils import couch, gdocs
from bilanci.utils.comuni import FLMapper


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--dry-run',
                    dest='dryrun',
                    action='store_true',
                    default=False,
                    help='Set the dry-run command mode: nothing is written in the couchdb'),
        make_option('--couchdb-server',
                    dest='couchdb_server',
                    default=settings.COUCHDB_DEFAULT_SERVER,
                    help='CouchDB server alias to connect to (staging | localhost). Defaults to staging.'),

    )

    help = 'Patches bilanci_voci for Consuntivo 2013 documents applying ' \
           '"Residui passivi" patch and "Totale a pareggio" patch'
    dryrun = False
    logger = logging.getLogger('management')

    def couch_connect(self, couchdb_server):
        # connect to couch database
        couchdb_server_alias = couchdb_server
        couchdb_dbname = settings.COUCHDB_SIMPLIFIED_NAME

        if couchdb_server_alias not in settings.COUCHDB_SERVERS:
            raise Exception("Unknown couchdb server alias.")

        self.couchdb = couch.connect(
            couchdb_dbname,
            couchdb_server_settings=settings.COUCHDB_SERVERS[couchdb_server_alias]
        )

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

        ###
        # connect to couchdb
        ###
        self.couch_connect(options['couchdb_server'])
        mapper = FLMapper()
        all_cities = mapper.get_cities('all', logger=self.logger)
        return