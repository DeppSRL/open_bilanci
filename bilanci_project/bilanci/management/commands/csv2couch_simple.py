import zipfile
import logging
from optparse import make_option

import pandas as pd
import time

from django.conf import settings
from django.core.management import BaseCommand, call_command

from bilanci.models import CodiceVoce, ValoreBilancio
from bilanci.utils.comuni import FLMapper
from bilanci.models import Territorio
from bilanci.utils import couch


#
# this is still in development and should not be used
#

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--dry-run',
                    dest='dryrun',
                    action='store_true',
                    default=False,
                    help='Set the dry-run command mode: nothing is written on the db'),
        make_option('--update-open-data',
                    dest='update_opendata',
                    action='store_true',
                    default=False,
                    help='Update open data zip files'),
        make_option('--file',
                    dest='input_file',
                    default='',
                    help='zip file to decompress and parse'),
        make_option('--cities',
                    dest='cities',
                    default='all',
                    help='Cities codes or slugs. Use comma to separate values: Roma,Napoli,Torino or  "All"'),
        make_option('--skip-existing',
                    dest='skip_existing',
                    action='store_true',
                    default=False,
                    help='Skip existing documents. Use to speed up long import of many cities, when errors occur'),
        make_option('--couchdb-server',
                    dest='couchdb_server',
                    default=settings.COUCHDB_DEFAULT_SERVER,
                    help='CouchDB server to connect to (defaults to staging).'),
        make_option('--append',
                    dest='append',
                    action='store_true',
                    default=False,
                    help='Use the log file appending instead of overwriting (used when launching shell scripts)'),
    )

    help = 'Import bilanci data from zip files containing ' \
            'files into couchdb bilanci_simple database'
    dryrun = None
    logger = logging.getLogger('management')


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
        self.update_opendata = options['update_opendata']
        self.input_file_path = options['input_file']
        self.skip_existing = options['skip_existing']

        if options['append'] is True:
            self.logger = logging.getLogger('management_append')

        ###
        # cities
        ###
        self.cities = options['cities']
        if self.cities != 'all':
            self.cities = self.cities.split(',')

        # check if debug is active: the task may fail
        if settings.DEBUG is True and settings.INSTANCE_TYPE != 'development' and len(self.cities) > 4000:
            self.logger.error("DEBUG settings is True, task will fail. Disable DEBUG and retry")
            exit()


        # extract certificate type from zip file name (p or c)
        certificate_type = self.input_file_path.split('/')[-1][0].lower()

        # extract year from zip file name (int)
        year = int(self.input_file_path.split('/')[-1].split('.')[0][-4:])

        # get voci mapping for that type
        cv = CodiceVoce.get_bilancio_codes(year, certificate_type).\
            values_list('quadro_cod', 'voce_cod', 'colonna_cod', 'voce_id')

        # transform it into a dict, with the tuple (q, v, c) as key
        # voce_id = cv_map[(q, v, c)]
        cv_map = dict(((i[0], i[1], i[2]), i[3]) for i in cv)

        # we'll be neeing the FinLoc mapper
        mapper = FLMapper()


        couchdb_server_name = options['couchdb_server']
        if couchdb_server_name not in settings.COUCHDB_SERVERS:
            raise Exception("Unknown couchdb server name.")

        ###
        #   Couchdb connections
        ###

        couchdb_server_alias = options['couchdb_server']
        if couchdb_server_alias not in settings.COUCHDB_SERVERS:
            raise Exception("Unknown couchdb server alias.")

        self.logger.info("Connect to server: {0}".format(couchdb_server_alias))
        # hook to bilanci_simple DB (creating it if non-existing)
        couchdb_dest_name = settings.COUCHDB_SIMPLIFIED_NAME
        couchdb_dest_settings = settings.COUCHDB_SERVERS[couchdb_server_alias]
        couchdb_dest = couch.connect(
            couchdb_dest_name,
            couchdb_server_settings=couchdb_dest_settings
        )
        # create couch bulk writer
        self.cbw = couch.CouchBulkWriter(logger=self.logger, couchdb_dest=couchdb_dest)
        self.logger.info("Hooked to destination DB: {0}".format(couchdb_dest_name))


        # read csv files
        self.logger.info(u'Reading file {} ....'.format(self.input_file_path))

        with zipfile.ZipFile(self.input_file_path) as zfile:
            for f in zfile.namelist():

                if f.endswith('_dati.txt'):
                    province = " " .join(f.split('/')[3].split('_')[:-1]).lower()
                    if self.cities == 'all' or province in self.cities:
                        self.logger.info(u"Processing file {0}. Province    : {1}".format(f, province))
                        df = pd.read_csv(
                            zfile.open(f),
                            sep='#',
                            header=None,
                            low_memory=True,
                            dtype=object,
                            encoding='utf-8',
                            keep_default_na=False,
                        )
                        city_code = ''
                        territorio = None
                        for row in df.itertuples():
                            anno = int(row[2])
                            quadro = row[5]
                            voce = row[6]
                            colonna = row[7]

                            # compute territorio
                            # only when switching to a new one
                            if city_code != row[3]:
                                city_code = row[3]
                                city_id = mapper.get_city(city_code)
                                territorio = Territorio.objects.get(
                                    cod_finloc=city_id
                                )


                                if self.skip_existing:
                                    if city_id in couchdb_dest:
                                        self.logger.info(u"Skipping city of {}, as already existing".format(city_id))
                                        continue

                                # create destination document, to REPLACE old one
                                # NB: the useless timestamps serves the only function to work around a bug in COUCHDB that
                                # if the written doc is exactly the same as the new doc then it will not be written
                                destination_document = {'_id': city_id, 'useless_timestamp': time.time()}

                                # if a doc with that id already exists on the destination document, gets the _rev value
                                # and insert it in the dest. document.
                                # this avoids document conflict on writing
                                # otherwise you should delete the old doc before writing the new one
                                old_destination_doc = couchdb_dest.get(city_id, None)
                                if old_destination_doc:
                                    revision = old_destination_doc.get('_rev', None)
                                    if revision:
                                        destination_document['_rev'] = revision
                                        self.logger.debug("Adds rev value to doc")

                                self.logger.info(u'Importing data for city {0}.'.format(territorio))


                            try:
                                voce_id = cv_map[(quadro, voce, colonna)]
                            except KeyError:
                                self.logger.debug(
                                    u'Skipping {0}, {2}, {2}.'.format(
                                        quadro, voce, colonna
                                    )
                                )
                                continue

                            vb, created = ValoreBilancio.objects.get_or_create(
                                anno=anno,
                                territorio=territorio,
                                voce_id=voce_id,
                            )
                            vb.valore += float(row[8])
                            vb.save()


                        self.logger.info(u'Done reading {0}.'.format(f))
