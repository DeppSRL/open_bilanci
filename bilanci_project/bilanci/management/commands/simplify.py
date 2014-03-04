import logging
from optparse import make_option
from django.core.management import BaseCommand
from django.conf import settings
from bilanci.tree_dict_models import *
from bilanci.utils import couch
from bilanci.utils import gdocs
from bilanci.utils.comuni import FLMapper

__author__ = 'guglielmo'

class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('--dry-run',
                    dest='dryrun',
                    action='store_true',
                    default=False,
                    help='Set the dry-run command mode: nothing is written in the couchdb'),
        make_option('--years',
                    dest='years',
                    default='',
                    help='Years to fetch. From 2002 to 2012. Use one of this formats: 2012 or 2003-2006 or 2002,2004,2006'),
        make_option('--cities',
                    dest='cities',
                    default='',
                    help='Cities codes or slugs. Use comma to separate values: Roma,Napoli,Torino or  "All"'),
        make_option('--couchdb-server',
                    dest='couchdb_server',
                    default=settings.COUCHDB_DEFAULT_SERVER,
                    help='CouchDB server to connect to (defaults to staging).'),
        make_option('--source-db-name',
                    dest='source_db_name',
                    default='bilanci_voci',
                    help='The name of the source couchdb instance (defaults to bilanci_voci'),
        make_option('--delete',
                    dest='delete',
                    action='store_true',
                    default=False,
                    help='Delete a city document before adding it (use only for full years coverage)'),
        make_option('--skip-existing',
                    dest='skip_existing',
                    action='store_true',
                    default=False,
                    help='Skip existing documents. Use to speed up long import of many cities, when errors occur'),
        make_option('--dest-db-name',
                    dest='dest_db_name',
                    default='bilanci_simple',
                    help='The name of the destination couchdb instance (defaults to bilanci_simple)'),
        make_option('--force-google',
                    dest='force_google',
                    action='store_true',
                    default=False,
                    help='Force reloading mapping file and simplified subtrees leaves from gdocs (invalidate the csv cache)'),


    )

    help = 'Read the simplification mappings from a Google Doc and maps the normalized couchdb instance into a simplified one.'

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
        skip_existing = options['skip_existing']

        cities_codes = options['cities']
        if not cities_codes:
            raise Exception("Missing city parameter")

        mapper = FLMapper(settings.LISTA_COMUNI_PATH)
        cities = mapper.get_cities(cities_codes)
        if cities_codes.lower() != 'all':
            self.logger.info("Processing cities: {0}".format(cities))


        years = options['years']
        if not years:
            raise Exception("Missing years parameter")

        if "-" in years:
            (start_year, end_year) = years.split("-")
            years = range(int(start_year), int(end_year)+1)
        else:
            years = [int(y.strip()) for y in years.split(",") if 2001 < int(y.strip()) < 2013]

        if not years:
            raise Exception("No suitable year found in {0}".format(years))

        self.logger.info("Processing years: {0}".format(years))

        couchdb_server_name = options['couchdb_server']

        if couchdb_server_name not in settings.COUCHDB_SERVERS:
            raise Exception("Unknown couchdb server name.")



        ###
        #   Couchdb connections
        ###

        ###
        # couchdb
        ###

        couchdb_server_alias = options['couchdb_server']

        if couchdb_server_alias not in settings.COUCHDB_SERVERS:
            raise Exception("Unknown couchdb server alias.")

        # hook to source DB
        source_db_name = options['source_db_name']
        source_db = couch.connect(
            source_db_name,
            couchdb_server_settings=settings.COUCHDB_SERVERS[couchdb_server_alias]
        )
        self.logger.info("Hooked to source DB: {0}".format(source_db_name))

        # hook to dest DB (creating it if non-existing)
        dest_db_name = options['dest_db_name']
        dest_db = couch.connect(
            dest_db_name,
            couchdb_server_settings=settings.COUCHDB_SERVERS[couchdb_server_alias]
        )
        self.logger.info("Hooked to destination DB: {0}".format(dest_db_name))


        ###
        #   Mapping file and simplified leaves subtrees
        ###
        # connect to google account and fetch tree mapping and simple tree structure
        voci_map = gdocs.get_simple_map(n_header_lines=2, force_google=force_google)
        simplified_subtrees_leaves = gdocs.get_simplified_leaves(force_google=force_google)

        for city in cities:

            dest_doc_id = city
            if dest_doc_id in dest_db and skip_existing:
                self.logger.info("Skipping city of {}, as already existing".format(city))
                continue


            complete_tree = {}

            for year in years:
                # need this for logging
                self.city = city
                self.year = year

                self.logger.info("Processing city of {0}, year {1}".format(
                    city, year
                ))

                # get the source doc
                doc_id = "{0}_{1}".format(year, city)
                source_doc = source_db.get(doc_id)


                # build the sub-trees, using the mapping and the source doc
                # catch exceptions for non-existing sections in source doc
                preventivo_tree = {}
                consuntivo_tree = {}
                try:
                    if 'preventivo' in source_doc and source_doc['preventivo']:
                        preventivo_entrate_tree = PreventivoEntrateBudgetTreeDict(logger=self.logger).build_tree(
                            leaves=simplified_subtrees_leaves['preventivo-entrate'],
                            mapping=(voci_map['preventivo'], source_doc)
                        )
                        preventivo_tree.update(preventivo_entrate_tree)

                        preventivo_spese_tree = PreventivoSpeseBudgetTreeDict(logger=self.logger).build_tree(
                            leaves=simplified_subtrees_leaves['preventivo-spese'],
                            mapping=(voci_map['preventivo'], voci_map['interventi'], source_doc)
                        )
                        preventivo_tree.update(preventivo_spese_tree)
                    else:
                        self.logger.warning(u"Could not find preventivo in source doc [{}]".format(
                            source_doc.get('_id')
                        ))

                    if 'consuntivo' in source_doc and source_doc['consuntivo']:
                        consuntivo_entrate_tree = ConsuntivoEntrateBudgetTreeDict(logger=self.logger).build_tree(
                            leaves=simplified_subtrees_leaves['consuntivo-entrate'],
                            mapping=(voci_map['consuntivo'], source_doc)
                        )
                        consuntivo_tree.update(consuntivo_entrate_tree)


                        consuntivo_spese_tree = ConsuntivoSpeseBudgetTreeDict(logger=self.logger).build_tree(
                            leaves=simplified_subtrees_leaves['consuntivo-spese'],
                            mapping=(voci_map['consuntivo'], voci_map['interventi'], source_doc)
                        )
                        consuntivo_tree.update(consuntivo_spese_tree)
                    else:
                        self.logger.warning(u"Could not find consuntivo in source doc [{}]".format(
                            source_doc.get('_id')
                        ))

                except (SubtreeDoesNotExist, SubtreeIsEmpty) as e:
                    self.logger.error(e)

                year_tree = {
                    'preventivo': preventivo_tree,
                    'consuntivo': consuntivo_tree,
                }

                complete_tree[str(year)] = year_tree

            # update the tree, deleting it if required
            # create the tree, when non-existing
            if dest_doc_id in dest_db:
                dest_doc = dest_db[dest_doc_id]
                if options['delete']:
                    dest_db.delete(dest_doc)
                    dest_db[dest_doc_id] = complete_tree
                else:
                    dest_doc.update(complete_tree)
                    dest_db.save(dest_doc)
            else:
                dest_db[dest_doc_id] = complete_tree



