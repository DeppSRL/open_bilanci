import logging
from optparse import make_option
from urllib2 import URLError
import couchdb
import gspread
from  gspread.exceptions import SpreadsheetNotFound
from django.core.management import BaseCommand
from django.conf import settings
from bilanci.utils.comuni import FLMapper

__author__ = 'guglielmo'

class TreeDict(dict):
    """
    Extends the standard dict, with an add_leaf method.
    """


    def add_leaf(self, breadcrumbs, default_val = 0):
        """
        Add a leaf to a tree, starting from the breadcrumbs list.
        Creates the needed nodes in the process.

        The default value of the list can be specified in the arguments.
        """
        current_node = self
        for item in breadcrumbs:
            if item not in current_node:
                if breadcrumbs[-1] == item:
                    current_node[item] = default_val
                    return
                else:
                    current_node[item] = {}
            current_node = current_node[item]



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
                    default='localhost',
                    help='CouchDB server to connect to (defaults to localhost).'),
        make_option('--source-db-name',
                    dest='source_db_name',
                    default='bilanci_voci',
                    help='The name of the source couchdb instance (defaults to bilanci_voci'),
        make_option('--dest-db-name',
                    dest='dest_db_name',
                    default='bilanci_simple',
                    help='The name of the destination couchdb instance (defaults to bilanci_simple)'),


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

        cities_codes = options['cities']
        if not cities_codes:
            raise Exception("Missing city parameter")

        mapper = FLMapper(settings.LISTA_COMUNI_PATH)
        cities = mapper.get_cities(cities_codes)
        if cities_codes.lower() != 'all':
            self.logger.info("Scraping cities: {0}".format(cities))


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

        self.logger.info("Scraping years: {0}".format(years))

        couchdb_server_name = options['couchdb_server']

        if couchdb_server_name not in settings.COUCHDB_SERVERS:
            raise Exception("Unknown couchdb server name.")



        ###
        #   Setup couchdb connections
        ###

        couchdb_server_settings = settings.COUCHDB_SERVERS[couchdb_server_name]

        # builds connection URL
        server_connection_address = "http://"
        if 'user' in couchdb_server_settings and 'password' in couchdb_server_settings:
            server_connection_address += "{0}:{1}@".format(
                couchdb_server_settings['user'],
                couchdb_server_settings['password']
            )
        server_connection_address += "{0}:{1}".format(
            couchdb_server_settings['host'],
            couchdb_server_settings['port']
        )
        self.logger.info("Connecting to: {0} ...".format(server_connection_address))

        # open connection to couchdb server and create instance
        server = couchdb.Server(server_connection_address)
        self.logger.info("Connected!")

        # hook to source DB
        source_db_name = options['source_db_name']
        source_db = server[source_db_name]
        self.logger.info("Hooked to source DB: {0}".format(source_db_name))

        # hook to dest DB (creating it if non-existing)
        dest_db_name = options['dest_db_name']
        if dest_db_name not in server:
            destination_db = server.create(dest_db_name)
            self.logger.info("Created destination DB: {0}".format(dest_db_name))
        dest_db = server[dest_db_name]
        self.logger.info("Hooked to destination DB: {0}".format(dest_db_name))


        ###
        #   Get mapping data from gdoc spreadsheet
        ###

        # get all gdocs keys
        gdoc_keys = settings.GDOC_KEYS

        # log into Google account
        gc = gspread.login(settings.GOOGLE_USER, settings.GOOGLE_PASSWORD)

        # open the list worksheet
        list_sheet = None
        try:
            list_sheet = gc.open_by_key(gdoc_keys['simple_map'])
        except SpreadsheetNotFound:
            raise Exception("Error: gdoc url not found: {0}".format(
                gdoc_keys['simple_map']
            ))

        self.logger.info("Spreadsheet gdoc read: {0}".format(
            gdoc_keys['simple_map']
        ))

        # put the mapping into the voci_map dict
        # preventivo and consuntivo sheets are appended in a single list
        # the first two rows are removed (labels)
        try:
            self.logger.info("reading preventivo ...")
            voci_map = list_sheet.worksheet("preventivo").get_all_values()[2:]
            self.logger.info("reading consuntivo ...")
            voci_map.extend(list_sheet.worksheet("consuntivo").get_all_values()[2:])
        except URLError:
            raise Exception("Connection error to Gdrive")

        self.logger.info("done with reading the mapping list.")

        ###
        #   get the simplified tree structure from gDoc
        ###

        # open the list worksheet
        list_sheet = None
        try:
            list_sheet = gc.open_by_key(gdoc_keys['simple_tree'])
        except SpreadsheetNotFound:
            raise Exception("Error: gdoc url not found: {0}".format(
                gdoc_keys['simple_tree']
            ))

        self.logger.info("Spreadsheet gdoc read: {0}".format(
            gdoc_keys['simple_tree']
        ))

        # get the tree voices from gDoc spreadsheet
        try:
            self.logger.info("reading preventivo entrate ...")
            preventivo_entrate = list_sheet.worksheet("Entrate prev").get_all_values()
            self.logger.info("reading consuntivo entrate ...")
            consuntivo_entrate = list_sheet.worksheet("Entrate cons").get_all_values()
            self.logger.info("reading preventivo uscite ...")
            preventivo_uscite = list_sheet.worksheet("Uscite prev").get_all_values()
            self.logger.info("reading consuntivo uscite ...")
            consuntivo_uscite = list_sheet.worksheet("Uscite cons").get_all_values()
        except URLError:
            raise Exception("Connection error to Gdrive")

        self.logger.info("done with reading the tree list.")

        for city in cities:
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

                # build the tree pieces, using the mapping and the source doc
                preventivo_tree = self.build_entrate_tree(preventivo_entrate, mapping = (voci_map, source_doc))
                consuntivo_tree = self.build_entrate_tree(consuntivo_entrate, mapping = (voci_map, source_doc))

                # remove the dest db and re-create the empty simplified tree
                if doc_id in dest_db:
                    dest_doc = dest_db[doc_id]
                    dest_db.delete(dest_doc)
                dest_db[doc_id] = {
                    'preventivo': preventivo_tree,
                    'consuntivo': consuntivo_tree,
                }

    def build_entrate_tree(self, items_list, mapping=None, city='', year=''):
        """
        Build and return a TreeDict object, out of a list of items.
        Each item is a sequence of paths.

        Leaf values are computed using the mapping tuple (voci_map, source_doc), if specified.
        The default value (0) is assigned to leaf if the mapping tuple is not specified.
        """
        ret = TreeDict()
        for item_bc in items_list:

            # remove last element if empty
            if not item_bc[-1]:
                item_bc.pop()

            self.logger.debug("processing {0}".format(item_bc))

            value = 0
            if mapping:
                (voci_map, source_doc) = mapping
                value = self.compute_sum(item_bc, voci_map, source_doc)

            # add this leaf to the tree, with the computed value
            ret.add_leaf(item_bc, value)

        return ret


    def compute_sum(self, simplified_bc, voci_map, normalized_doc):
        """
        Compute the sum of all voices in the normalized budget doc
        that corresponds to the simplified voice
        (identified by the simplified_bc breadcrumbs),
        according to the voci_map mapping.
        """
        ret = 0

        ###
        #   get matching voices (uses mapping)
        ###

        # pad with empty value, if needed,
        if len(simplified_bc) == 3:
            simplified_bc.append('')
        # reverse and lowercase breadcrumbs
        bc = [i.lower() for i in simplified_bc][::-1]

        # fetch matches in the mapping
        voci_matches = []
        for voce_map in voci_map:
            if [i.lower() for i in voce_map[-4:]] == bc:
                voci_matches.append(voce_map[:4])

        if not voci_matches:
            self.logger.warning(u"No matching voci found for: {0}.".format(
                bc
            ))

        # compute the sum of the matching voices
        for voce_match in voci_matches:

            tipo = voce_match[0]
            quadro = "{:02d}".format(int(voce_match[1]))
            normalized_quadro = normalized_doc[tipo][quadro]

            titolo = voce_match[2]
            if titolo not in normalized_quadro:
                self.logger.warning(u"Titolo {0} not found for {1}, quadro: {2}.".format(
                    titolo, tipo, quadro
                ))
                continue
            normalized_titolo = normalized_quadro[titolo]

            voce = voce_match[3]
            if voce not in normalized_titolo['data']:
                self.logger.warning(u"Voce {0} not found for {1}, quadro: {2}, titolo: {3}.".format(
                    voce, tipo, quadro, titolo
                ))
                continue
            normalized_voce = normalized_titolo['data'][voce]

            if len(normalized_voce) == 1:
                val = normalized_voce[0]
                ret += int(val.replace(',00', '').replace('.',''))
            else:
                self.logger.warning(u"More than one value found for tipo:{0}, quadro: {1}, titolo: {2}, voce: {3}.".format(
                    tipo, quadro, titolo, voce
                ))

        return ret
