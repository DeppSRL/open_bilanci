import logging
from optparse import make_option
from couchdb.http import ResourceNotFound
from django.core.management import BaseCommand
from django.conf import settings
from bilanci.utils import couch
from bilanci.utils.comuni import FLMapper
from bilanci.utils.converters import FLScraper, FLCouchEmitter

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
        make_option('--base-url',
                    dest='base_url',
                    default='http://finanzalocale.mirror.openpolis.it',
                    help='Base URL for HTML files (mirror)'),
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

    help = 'Import the data for given cities and years, from HTML code into Couchdb'

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

        cities_codes = options['cities']
        if not cities_codes:
            raise Exception("Missing city parameter")

        self.logger.info("Opening Lista Comuni")
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
            years = [int(y.strip()) for y in years.split(",") if 2001 < int(y.strip()) < 2014]

        if not years:
            raise Exception("No suitable year found in {0}".format(years))

        self.logger.info("Processing years: {0}".format(years))

        base_url = options['base_url']

        ###
        # couchdb
        ###

        couchdb_server_alias = options['couchdb_server']
        couchdb_dbname = settings.COUCHDB_RAW_NAME

        if couchdb_server_alias not in settings.COUCHDB_SERVERS:
            raise Exception("Unknown couchdb server alias.")


        self.logger.info("Connecting to db: {0}".format(couchdb_dbname))

        try:
            couchdb = couch.connect(
                couchdb_dbname,
                couchdb_server_settings=settings.COUCHDB_SERVERS[couchdb_server_alias]
            )
        except ResourceNotFound:
            self.logger.error("Could not find the db. Quitting")
            return


        # instantiate the scraper to parse finanzalocale
        scraper = FLScraper(self.logger)
        emitter = FLCouchEmitter(logger=self.logger, couchdb=couchdb)


        for city in cities:
            for year in years:

                # Preventivo
                q_list = ["%02d" % (i,) for i in range(1, 10)]
                url = "{0}/{1}/{2}/Preventivo".format(
                        base_url, year, city
                )
                self.logger.info("Scraping Preventivo: {0}".format(url))
                preventivo = scraper.scrape(
                    url,
                    pages=q_list
                )

                # Consuntivo
                q_list = ["%02d" % (i,) for i in range(1, 20)]
                q_list.append("50")
                url = "{0}/{1}/{2}/Consuntivo".format(
                    base_url, year, city
                )
                self.logger.info("Scraping Consuntivo: {0}".format(url))
                consuntivo = scraper.scrape(
                    url,
                    pages=q_list
                )

                # prepare global data
                bilancio_id = "{0}_{1}".format(year, city)
                bilancio_data = {
                    'anno': year,
                    'city_name': city.split("--")[0],
                    'preventivo': preventivo,
                    'consuntivo': consuntivo
                }

                if not dryrun:
                    emitter.emit(id=bilancio_id, data=bilancio_data)
                    self.logger.info("Data written to couchdb")
                else:
                    self.logger.info("Couchdb writing skipped because of --dry-run")


