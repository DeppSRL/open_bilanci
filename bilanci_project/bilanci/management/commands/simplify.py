import logging
import time
import multiprocessing
from optparse import make_option
from django.core.management import BaseCommand
from django.conf import settings
from bilanci.tree_dict_models import *
from bilanci.utils import couch, gdocs, email_utils
from bilanci.utils.comuni import FLMapper

__author__ = 'guglielmo'

simplified_subtrees_leaves = None
voci_map = None


def simplify(destination_document, city_bilanci):
    logger = logging.getLogger('management')
    for element in city_bilanci:
        year = element['year']
        source_doc = element['data']

        # build the sub-trees, using the mapping and the source doc
        # catch exceptions for non-existing sections in source doc
        preventivo_tree = {}
        consuntivo_tree = {}
        try:
            if 'preventivo' in source_doc and source_doc['preventivo']:
                preventivo_entrate_tree = PreventivoEntrateBudgetTreeDict(
                    logger=logger
                ).build_tree(
                    leaves=simplified_subtrees_leaves['preventivo-entrate'],
                    mapping=(voci_map['preventivo'], source_doc)
                )
                preventivo_tree.update(preventivo_entrate_tree)

                preventivo_spese_tree = PreventivoSpeseBudgetTreeDict(
                    logger=logger
                ).build_tree(
                    leaves=simplified_subtrees_leaves['preventivo-spese'],
                    mapping=(
                        voci_map['preventivo'],
                        voci_map['interventi'],
                        source_doc
                    )
                )
                preventivo_tree.update(preventivo_spese_tree)
            else:
                logger.warning(
                    u"Could not find preventivo in source doc [{}]".format(
                        source_doc.get('_id')
                    )
                )

            if 'consuntivo' in source_doc and source_doc['consuntivo']:
                consuntivo_entrate_tree = ConsuntivoEntrateBudgetTreeDict(
                    logger=logger
                ).build_tree(
                    leaves=simplified_subtrees_leaves['consuntivo-entrate'],
                    mapping=(voci_map['consuntivo'], source_doc)
                )
                consuntivo_tree.update(consuntivo_entrate_tree)

                consuntivo_spese_tree = ConsuntivoSpeseBudgetTreeDict(
                    logger=logger
                ).build_tree(
                    leaves=simplified_subtrees_leaves['consuntivo-spese'],
                    mapping=(
                        voci_map['consuntivo'],
                        voci_map['interventi'],
                        source_doc
                    )
                )
                consuntivo_tree.update(consuntivo_spese_tree)

                # creates branch RIASSUNTIVO

                consuntivo_riassuntivo_tree = \
                    ConsuntivoRiassuntivoBudgetTreeDict(
                        logger=logger
                    ).build_tree(
                        leaves=simplified_subtrees_leaves[
                            'consuntivo-riassuntivo'
                        ],
                        mapping=(voci_map['consuntivo'], source_doc)
                    )
                consuntivo_tree.update(consuntivo_riassuntivo_tree)

            else:
                logger.warning(
                    u"Could not find consuntivo in source doc [{}]".format(
                        source_doc.get('_id')
                    )
                )

        except (SubtreeDoesNotExist, SubtreeIsEmpty) as e:
            logger.error(e)

        year_tree = {
            'preventivo': preventivo_tree,
            'consuntivo': consuntivo_tree,
        }

        destination_document[str(year)] = year_tree

    return destination_document


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--dry-run',
                    dest='dryrun',
                    action='store_true',
                    default=False,
                    help='Set the dry-run command mode: '
                    'nothing is written in the couchdb'),
        make_option('--years',
                    dest='years',
                    default='',
                    help='Years to fetch. From 2002 to current. '
                    'Use one of this formats: 2012 or '
                    '2003-2006 or 2002,2004,2006'),
        make_option('--cities',
                    dest='cities',
                    default='',
                    help='Cities codes or slugs. Use comma to separate values: '
                    'Roma,Napoli,Torino or  "All"'),
        make_option('--couchdb-server',
                    dest='couchdb_server',
                    default=settings.COUCHDB_DEFAULT_SERVER,
                    help='CouchDB server to connect to (defaults to staging).'),
        make_option('--source-db-name',
                    dest='source_db_name',
                    default='bilanci_voci',
                    help='The name of the source couchdb instance '
                    '(defaults to bilanci_voci'),
        make_option('--skip-existing',
                    dest='skip_existing',
                    action='store_true',
                    default=False,
                    help='Skip existing documents. Use to speed '
                    'up long import of many cities, when errors occur'),
        make_option('--force-google',
                    dest='force_google',
                    action='store_true',
                    default=False,
                    help='Force reloading mapping file and simplified '
                    'subtrees leaves from gdocs '
                    '(invalidate the csv cache)'),
        make_option('--append',
                    dest='append',
                    action='store_true',
                    default=False,
                    help='Use the log file appending instead of '
                    'overwriting (used when launching shell scripts)'),
    )

    help = 'Read the simplification mappings from a Google Doc ' \
        'and maps the normalized couchdb instance into a simplified one.'

    logger = logging.getLogger('management')
    comuni_dicts = {}
    cbw = None
    city = None
    year = None

    def pass_to_bulkwriter(self, results):
        for r in results:
            # gets result dict from ApplyResult object and
            # write doc to couchdb dest
            ret = self.cbw.write(r.get())
            if ret is False:
                email_utils.send_notification_email(
                    msg_string='simplify has encountered problems')
                self.logger.critical("Write critical problem. Quit")
                exit()

    def handle(self, *args, **options):
        global voci_map
        global simplified_subtrees_leaves

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
        # get the timestamp to ensure the document will be written in couchdb,
        # this is a workaround for a bug,
        # see later comment
        timestamp = time.time()

        if options['append'] is True:
            self.logger = logging.getLogger('management_append')

        force_google = options['force_google']
        skip_existing = options['skip_existing']

        cities_codes = options['cities']
        if not cities_codes:
            raise Exception("Missing city parameter")

        mapper = FLMapper()
        cities = mapper.get_cities(cities_codes)
        if cities_codes.lower() != 'all':
            self.logger.info(u"Processing cities: {0}".format(cities))

        years = options['years']
        if not years:
            raise Exception("Missing years parameter")

        if "-" in years:
            (start_year, end_year) = years.split("-")
            years = range(int(start_year), int(end_year) + 1)
        else:
            years = [
                int(y.strip()) for y in years.split(",")
                if 2001 < int(y.strip()) < 2020
            ]

        if not years:
            raise Exception("No suitable year found in {0}".format(years))

        self.logger.info("Processing years: {0}".format(years))

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
        # hook to source DB
        source_db_name = options['source_db_name']
        source_db = couch.connect(
            source_db_name,
            couchdb_server_settings=settings.COUCHDB_SERVERS[
                couchdb_server_alias
            ]
        )
        self.logger.info("Hooked to source DB: {0}".format(source_db_name))

        # hook to dest DB (creating it if non-existing)
        couchdb_dest_name = settings.COUCHDB_SIMPLIFIED_NAME
        couchdb_dest_settings = settings.COUCHDB_SERVERS[couchdb_server_alias]
        couchdb_dest = couch.connect(
            couchdb_dest_name,
            couchdb_server_settings=couchdb_dest_settings
        )

        # create couch bulk writer
        self.cbw = couch.CouchBulkWriter(
            logger=self.logger, couchdb_dest=couchdb_dest
        )
        self.logger.info(
            "Hooked to destination DB: {0}".format(couchdb_dest_name)
        )

        ###
        #   Mapping file and simplified leaves subtrees
        ###
        # connect to google account and fetch tree mapping
        # and simple tree structure
        voci_map = gdocs.get_simple_map(
            n_header_lines=2, force_google=force_google
        )
        simplified_subtrees_leaves = gdocs.get_simplified_leaves(
            force_google=force_google
        )

        # multiprocessing basics
        params = []
        pool = multiprocessing.Pool()

        for city_id in cities:
            city_bilanci = []
            dest_doc_id = city_id
            if skip_existing:
                if dest_doc_id in couchdb_dest:
                    self.logger.info(
                        u"Skipping city of {}, as "
                        u"already existing".format(city_id)
                    )
                    continue

            # create destination document, to REPLACE old one
            # NB: the useless timestamps serves the only function
            # to work around a bug in COUCHDB that
            # if the written doc is exactly the same as the
            # new doc then it will not be written
            destination_document = {
                '_id': city_id,
                'useless_timestamp': timestamp
            }

            # if a doc with that id already exists on the destination document,
            # gets the _rev value
            # and insert it in the dest. document.
            # this avoids document conflict on writing
            # otherwise you should delete the old doc before writing the new one
            old_destination_doc = couchdb_dest.get(city_id, None)
            if old_destination_doc:
                revision = old_destination_doc.get('_rev', None)
                if revision:
                    destination_document['_rev'] = revision
                    self.logger.debug("Adds rev value to doc")

            self.logger.debug(u"Processing city of {0}".format(city_id, ))
            for year in years:
                # need this for logging
                self.city = city_id
                self.year = year

                # get the source doc
                doc_id = "{0}_{1}".format(year, city_id)
                if doc_id not in source_db:
                    self.logger.warning(
                        u"Could not find {} in bilanci_voci "
                        u"couchdb instance. Skipping.".format(doc_id)
                    )
                    continue

                source_doc = source_db.get(doc_id)
                city_bilanci.append({'year': year, 'data': source_doc})

            params.append((destination_document, city_bilanci))

            if len(params) % settings.COUCH_TRANSLATION_BULK_SIZE == 0 \
                and len(params) != 0:
                self.logger.info(
                    u"Reached {}, time to write to Couch...".format(city_id)
                )
                results = [pool.apply_async(simplify, p) for p in params]
                params = []
                if not dryrun:
                    self.pass_to_bulkwriter(results)
                self.logger.debug("Writing done")

        if not dryrun:
            # if the buffer in CBW is non-empty, flushes the docs to the db
            if len(params) > 0:
                results = [pool.apply_async(simplify, p) for p in params]
                self.pass_to_bulkwriter(results)

            ret = self.cbw.close()

            if ret is False:
                email_utils.send_notification_email(
                    msg_string='simplify has encountered problems'
                )
                self.logger.critical("Write critical problem. Quit")
                exit()

        email_utils.send_notification_email(msg_string="Simplify has finished")
