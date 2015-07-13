from itertools import groupby
import logging
from optparse import make_option
import os
from pprint import pprint
import zipfile
import shutil

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.management import BaseCommand

from bilanci.models import Voce, ValoreBilancio, Indicatore, ValoreIndicatore
from bilanci.utils import unicode_csv
from bilanci.utils.comuni import FLMapper
from bilanci.utils.zipper import zipdir
from territori.models import Territorio

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
                    help='Cities codes or slugs. Use comma to separate values: Roma,Napoli,Torino or  "all" or "capoluoghi"'),
        make_option('--single-file',
                    dest='single_file',
                    action='store_true',
                    default=False,
                    help='Outputs all data in a single csv file'),
        make_option('--skip-existing',
                    dest='skip_existing',
                    action='store_true',
                    default=False,
                    help='Skip existing cities. Use to speed up long import of many cities, when errors occur'),
        make_option('--indicators',
                    dest='indicators',
                    default='all',
                    help='Indicators slugs. Use comma to separate values: Roma,Napoli,Torino or  "All"'),
        make_option('--csv-base-dir',
                    dest='csv_base_dir',
                    default='data/csv/',
                    help='Path to the directory where the CSV files will be written.'),
        make_option('--compress',
                    dest='compress',
                    action='store_true',
                    default=False,
                    help="Generate compressed zip archive of the directory for each city, remove directory structure"),
    )

    help = 'Export indicatori values from the database into a set of CSV files (one per indicator)'

    logger = logging.getLogger('management')
    years = None
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

        valori_complete = []
        dryrun = options['dryrun']
        compress = options['compress']
        single_file = options['single_file']
        skip_existing = options['skip_existing']

        csv_base_path = os.path.abspath(options['csv_base_dir'])
        indicators_path = os.path.join(csv_base_path, "indicators")
        if not os.path.exists(indicators_path):
            os.makedirs(indicators_path)

        ###
        # cities
        ###
        cities_codes = options['cities']
        if not cities_codes:
            raise Exception("Missing cities parameter")

        mapper = FLMapper()
        # gets capoluoghi privincia finloc list from settings
        if cities_codes == 'capoluoghi':
            cities = Territorio.objects.\
                filter(slug__in=settings.CAPOLUOGHI_PROVINCIA).\
                order_by('cod_finloc').values_list('cod_finloc', flat=True)
        else:
            cities = mapper.get_cities(cities_codes)

        if cities_codes.lower() != 'all':
            self.logger.info("Processing cities: {0}".format(cities))

        ###
        # years
        ###
        years = options['years']
        if not years:
            raise Exception("Missing years parameter")

        if "-" in years:
            (start_year, end_year) = years.split("-")
            years = range(int(start_year), int(end_year) + 1)
        else:
            years = [int(y.strip()) for y in years.split(",") if 2001 < int(y.strip()) < 2013]

        if not years:
            raise Exception("No suitable year found in {0}".format(years))

        self.logger.info("Processing years: {0}".format(years))
        self.years = years

        # massaging indicators option
        indicators_slugs = options['indicators']
        if indicators_slugs == 'all':
            indicators_slugs = Indicatore.objects.all().values_list('slug', flat=True)
        else:
            indicators_slugs = [(i.strip()) for i in indicators_slugs.split(",")]

        for indicator_slug in indicators_slugs:
            indicator = Indicatore.objects.get(slug=indicator_slug)
            self.logger.info(u"Indicatore:::: {0} ::::".format(indicator.denominazione))

            if not single_file:
                # check if files for this indicator exists and skip if
                # the skip-existing option was required
                csv_filename = os.path.join(indicators_path, "{0}.csv".format(indicator_slug))
                if skip_existing and os.path.exists(csv_filename):
                    self.logger.info(u"Skipping indicator {}, as already processed".format(indicator_slug))
                    continue

                valori = groupby(
                    indicator.valoreindicatore_set.values('territorio__cod_finloc', 'anno', 'valore').order_by(
                        'territorio__cod_finloc', 'anno'),
                    lambda x: (x['territorio__cod_finloc'])
                )

                valori_dict = {}
                for k, g in valori:
                    valori_dict[k] = dict([(it['anno'], it['valore']) for it in g])

                # open csv file
                csv_file = open(csv_filename, 'w')
                csv_writer = unicode_csv.UnicodeWriter(csv_file, dialect=unicode_csv.excel_semicolon)

                # build and emit header
                row = ['City', 'Cluster', 'Region']
                row.extend(map(str, years))
                csv_writer.writerow(row)

                for city in cities:
                    if city not in valori_dict:
                        continue

                    try:
                        territorio = Territorio.objects.get(cod_finloc=city)
                    except ObjectDoesNotExist:
                        self.logger.warning(u"City {0} not found among territories in DB. Skipping.".format(city))

                    # emit
                    cluster = territorio.cluster if territorio.cluster else ''
                    region = territorio.regione if territorio.regione else ''
                    row = [city, cluster, region]
                    for year in years:
                        if year not in valori_dict[city]:
                            row.append('')
                        else:
                            row.append(str(valori_dict[city][year]))

                    csv_writer.writerow(row)
                    self.logger.debug(",".join(row))

            else:

                indicator_set = ValoreIndicatore.objects.filter(territorio__cod_finloc__in=cities,
                                                                indicatore=indicator). \
                    values_list('indicatore__slug', 'territorio__cod_finloc', 'territorio__istat_id', 'anno',
                                'valore').order_by('territorio__cod_finloc', 'anno')

                valori_list = []
                for t in indicator_set:
                    valori_list.append([str(element) for element in t])

                valori_complete.extend(valori_list)

        if single_file:
        #     write a single file with all indicators and values for cities
            csv_filename = os.path.join(indicators_path, "indicators.csv")

            # open csv file
            csv_file = open(csv_filename, 'w')
            csv_writer = unicode_csv.UnicodeWriter(csv_file, dialect=unicode_csv.excel_semicolon)
            # build and emit header
            row = ['indicatore', 'territorio', 'codice_istat', 'anno', 'valore']
            csv_writer.writerow(row)

            for row in valori_complete:
                row[2] = row[2].zfill(6)
                csv_writer.writerow(row)

            csv_file.close()
            self.logger.info("Written file {}".format(csv_filename))

        if compress:
            csv_path = os.path.join('data', 'csv')
            zip_path = os.path.join('data', 'zip')
            if not os.path.exists(zip_path):
                os.mkdir(zip_path)

            zipfilename = os.path.join(zip_path, "indicators.zip")

            zipdir("indicators", zipfile.ZipFile(zipfilename, "w", zipfile.ZIP_DEFLATED), root_path=csv_path)
            self.logger.info("Compressed file {}".format(zipfilename))

            # remove all tree under city_path
            # with security control
            if 'data' in indicators_path and 'csv' in indicators_path:
                shutil.rmtree(indicators_path)
