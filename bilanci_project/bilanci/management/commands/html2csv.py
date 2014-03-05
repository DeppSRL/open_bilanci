import json
import logging
from optparse import make_option
import os
from pprint import pprint
import zipfile
from django.core.management import BaseCommand
from django.conf import settings
import shutil
from bilanci.utils import unicode_csv
from bilanci.utils.comuni import FLMapper
from bilanci.utils.converters import FLScraper, FLCSVEmitter
from bilanci.utils.zipper import zipdir

__author__ = 'guglielmo'

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
        make_option('--base-url',
                    dest='base_url',
                    default='http://finanzalocale.mirror.openpolis.it',
                    help='Base URL for HTML files (mirror)'),
        make_option('--csv-base-dir',
                    dest='csv_base_dir',
                    default='data/csv/',
                    help='PAth to the directory where the CSV files will be written.'),
        make_option('--compress',
                    dest='compress',
                    action='store_true',
                    default=False,
                    help="Generate compressed zip archive of the directory for each city, remove directory structure"),
    )

    help = 'Read the data for given cities and years, tranforming HTML into CSV.'

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
            years = [int(y.strip()) for y in years.split(",") if 2001 < int(y.strip()) < 2013]

        if not years:
            raise Exception("No suitable year found in {0}".format(years))

        self.logger.info("Processing years: {0}".format(years))

        base_url = options['base_url']
        csv_base_dir = options['csv_base_dir']
        compress = options['compress']

        # instantiate scraper and emitter
        # to parse finanzalocale and emit CSV files
        scraper = FLScraper(self.logger)
        emitter = FLCSVEmitter(self.logger)

        csv_base_path = os.path.abspath(csv_base_dir)

        for city in cities:

            self.logger.info("City: {}".format(city))

            # check city path
            city_path = os.path.join(csv_base_path, city)
            if not os.path.exists(city_path):
                os.makedirs(city_path)

            for year in years:

                # check year path
                year_path = os.path.join(city_path, str(year))
                if not os.path.exists(year_path):
                    os.mkdir(year_path)

                self.logger.info("  Year: {}".format(year))

                #
                ## Preventivo
                #

                self.logger.info("    Preventivo")
                prev_path = os.path.join(year_path, 'preventivo')
                if not os.path.exists(prev_path):
                    os.mkdir(prev_path)

                # prepare list and mirror url
                q_list = ["%02d"%i for i in range(1, 10)]
                url = "{0}/{1}/{2}/Preventivo".format(
                        base_url, year, city
                )

                # scrape data from mirror into q_data structure
                q_data = scraper.scrape(
                    url,
                    pages=(q_list)
                )

                # emit q_data as CSV files in a directory tree
                # under prev_path
                emitter.emit(q_data=q_data, base_path=prev_path)


                #
                ## Consuntivo
                #

                self.logger.info("    Consuntivo")
                cons_path = os.path.join(year_path, 'consuntivo')
                if not os.path.exists(cons_path):
                    os.mkdir(cons_path)

                # prepare list and mirror url
                q_list = ["%02d" % (i,) for i in range(1, 20)]
                q_list.append("50")
                url = "{0}/{1}/{2}/Consuntivo".format(
                    base_url, year, city
                )

                # scrape data from mirror into q_data structure
                q_data = scraper.scrape(
                    url,
                    pages=(q_list)
                )

                # emit q_data as CSV files in a directory tree
                # under prev_path
                emitter.emit(q_data=q_data, base_path=cons_path)


            if compress:
                csv_path = os.path.join('data', 'csv')
                zip_path = os.path.join('data', 'zip')
                if not os.path.exists(zip_path):
                    os.mkdir(zip_path)

                zipfilename = os.path.join(zip_path, "{}.zip".format(city))

                zipdir(city, zipfile.ZipFile(zipfilename, "w", zipfile.ZIP_DEFLATED), root_path=csv_path)
                self.logger.info("  Compressed!")

                # remove all tree under city_path
                # with security control
                if 'data' in city_path and 'csv' in city_path:
                    shutil.rmtree(city_path)

