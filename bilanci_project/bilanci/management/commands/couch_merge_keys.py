# coding: utf-8

import logging
from optparse import make_option
from couchdb.http import ResourceNotFound
from django.core.management import BaseCommand
from django.conf import settings
import gspread
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
        couchdb_server_alias = options['couchdb_server']
        merge_type = options['type']
        tipo_bilancio = options['tipobilancio']
        output = options['output']

        if options['append'] is True:
            self.logger = logging.getLogger('management_append')


        if merge_type in ['t','v','s']:
    
            if couchdb_server_alias in settings_local.accepted_servers.keys():

                # Login with the script Google account
                gc = gspread.login(settings_local.g_user, settings_local.g_password)
    
                # open the list worksheet
                list_sheet = None
                try:
                    list_sheet = gc.open_by_key(settings_local.gdoc_keys[merge_type])
                except gspread.exceptions.SpreadsheetNotFound:
                    logging.error("Error: gdoc url not found")
                    return
    
                worksheet = list_sheet.worksheet(tipo_bilancio).get_all_values()[2:]


                # set couch source and destination names
                view_name = 'voci_{0}'.format(tipo_bilancio)

                if merge_type == 't':
                    couch_db_name = settings.COUCHDB_RAW_NAME
                    view_name = 'titoli_{0}'.format(tipo_bilancio)
                elif merge_type == 'v':
                    couch_db_name = settings.COUCHDB_NORMALIZED_TITOLI_NAME
                elif merge_type =='s':
                    couch_db_name = settings.COUCHDB_NORMALIZED_VOCI_NAME
                else:
                    self.logger.error("Merge type not accepted")
                    return

                if couchdb_server_alias not in settings.COUCHDB_SERVERS:
                    raise Exception("Unknown couchdb server alias.")



                self.logger.info("Connecting to couch db: {0}".format(couchdb_server_alias))
                try:
                    couchdb_source = couch.connect(
                        couch_db_name,
                        couchdb_server_settings=settings.COUCHDB_SERVERS[couchdb_server_alias]
                    )
                except ResourceNotFound:
                    self.logger.error("Could not find couch db. Quitting")
                    return

                # connessione a couchdb
                # costruisce la stringa per la connessione al server aggiungendo user/passw se necessario
                host = settings_local.accepted_servers[couchdb_server_alias]['host']
                server_connection_address ='http://{0}:5984/{1}/_design/{2}/_view/{3}?group_level=4'.format(host,couch_db_name, view_name,view_name)
                logging.info("Getting Json data from couch View:{0}".format(view_name))
    
    
                user = passw = None
                if settings_local.accepted_servers[couchdb_server_alias]['user']:
                    user = settings_local.accepted_servers[couchdb_server_alias]['user']
                    if settings_local.accepted_servers[couchdb_server_alias]['password']:
                        passw =settings_local.accepted_servers[couchdb_server_alias]['password']
    
    
                if user is None and passw is None:
                    r = requests.get(server_connection_address)
                else:
                    r = requests.get(server_connection_address, auth=(user,passw))
    
                result_set = merge(view_data=r.json(), worksheet=worksheet, merge_type=merge_type, tipo_bilancio=tipo_bilancio)
                write_csv(result_set=result_set, output_filename=output_filename, merge_type=merge_type, tipo_bilancio=tipo_bilancio)
    
    
            else:
                logging.error("server not accepted:"+couchdb_server_alias)
        else:
            logging.error("Type not accepted: " + merge_type)
    

