from collections import OrderedDict
import logging
from optparse import make_option
import os
import subprocess
import couchdb
from django.core.management import BaseCommand
from django.conf import settings
from bilanci.utils.comuni import FLMapper

__author__ = 'stefano'

class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
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
        make_option('--output-path',
                    dest='output_path',
                    default='./',
                    help='The path where putput files are written. Defaults to the current path (.).'),
    )

    help = """
    Given a list of cities and years outputs a list of instructions to
    scrape missing bilanci and a list of cities codes and years,
    to be loaded in various management tasks (html2couch, simplify, ...)
    """

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

        # lista dei bilanci mancanti con citta,anno,tipo che viene usata per scrapy
        missing_bilanci_tipo = []
        # dizionari bilanci mancanti per citta e anno che viene usata per html2couch
        missing_bilanci = OrderedDict([])

        # open output filenames
        if not 'output_path' in options:
            raise Exception("output-path option is needed")
        output_path = options['output_path']
        scrapy_instructions_filename = os.path.join(output_path, "scrape_missing_bilanci")
        missing_bilanci_args_filename = os.path.join(output_path, "missing_bilanci_args")
        self.logger.info("Opening output files in : {0}".format(output_path))
        scrapy_instructions_file = open(scrapy_instructions_filename,'w')
        missing_bilanci_args_file = open(missing_bilanci_args_filename,'w')

        cities_codes = options['cities']
        if not cities_codes:
            raise Exception("Missing city parameter")

        mapper = FLMapper(settings.LISTA_COMUNI_PATH)
        cities = mapper.get_cities(cities_codes)
        if cities_codes.lower() != 'all':
            self.logger.info("Analyzing following cities: {0}".format(cities))


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

        self.logger.info("Analyzing years: {0}".format(years))

        couchdb_server_name = options['couchdb_server']

        if couchdb_server_name not in settings.COUCHDB_SERVERS:
            raise Exception("Unknown couchdb server name.")



        ###
        #   Couchdb connections
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

        tipologie_bilancio = ['preventivo', 'consuntivo']
        for city in cities:
            # city: MILANO--1030491450 -> city_name: MILANO, city_code: 1030491450
            city_name, city_code = city.split("--")

            for year in years:
                # need this for logging
                self.city = city
                self.year = year

                self.logger.debug("Processing city of {0}, year {1}".format(
                    city, year
                ))

                document_id = str(year)+"_"+city
                source_document = source_db.get(document_id)
                if source_document is None:
                    self.logger.error("Missing preventivo and consuntivo for Comune:{0}, yr:{1}".format(
                        city,year
                    ))
                    missing_bilanci_tipo.append({'year':year, 'city_name': city_name, 'type': 'P'})
                    missing_bilanci_tipo.append({'year':year, 'city_name': city_name, 'type': 'C'})

                    if city_name not in missing_bilanci:
                        missing_bilanci[city_code]=[]
                    if year not in missing_bilanci[city_code]:
                        missing_bilanci[city_code].append(str(year))
                else:
                    anno_is_missing = False

                    for tipologia in tipologie_bilancio:
                        tipologia_is_missing = False

                        if tipologia not in source_document.keys():
                            tipologia_is_missing=True
                            anno_is_missing = True
                        else:
                            if source_document[tipologia] == {}:
                                tipologia_is_missing=True
                                anno_is_missing = True

                        if tipologia_is_missing:
                            self.logger.error("Missing {0} for Comune:{1}, yr:{2}".format(
                                    tipologia, city, year
                                ))
                            if tipologia.lower() == "preventivo":
                                short_tipologia = 'P'
                            else:
                                short_tipologia = 'C'

                            missing_bilanci_tipo.append({'year':year, 'city_name': city_name, 'type': short_tipologia})

                    # in missing_bilanci ho un dizionario con chiave il nome citta' e come valori gli anni
                    # in cui manca almeno un tipo di bilancio.
                    # in questo modo se mancano prev. e cons. in missing_bilanci ho una sola riga per il comune e non 2
                    if anno_is_missing:
                        if city_code not in missing_bilanci:
                            missing_bilanci[city_code]=[]
                        if year not in missing_bilanci[city_code]:
                            missing_bilanci[city_code].append(str(year))



        # scrapy instruction file (executable)
        scrapy_instructions_file.write('cd ../scraper_project/\n')
        for missing_bilancio in missing_bilanci_tipo:
            scrapy_instructions_file.write(
                "scrapy crawl bilanci_pages -a cities={0} -a years={1} -a type={2}\n".format(
                    missing_bilancio['city_name'],missing_bilancio['year'],missing_bilancio['type']
                )
            )
        subprocess.call(["chmod", "a+x", scrapy_instructions_filename])

        # missing bilanci arguments list
        for city_code in missing_bilanci.keys():
            missing_bilanci_args_file.write(
                "--cities={0} --years={1}\n".format(
                    city_code, ",".join(missing_bilanci[city_code])
                )
            )

