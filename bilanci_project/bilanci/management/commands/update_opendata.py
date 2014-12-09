from collections import OrderedDict
import logging
from optparse import make_option
import os
import zipfile
from django.conf import settings
from django.core.management import BaseCommand
import shutil
from bilanci import tree_models
from bilanci.models import Voce, ValoreBilancio
from bilanci.utils import couch, gdocs
from bilanci.utils import unicode_csv
from bilanci.utils.comuni import FLMapper
from bilanci.utils.zipper import zipdir
from territori.models import Territorio, ObjectDoesNotExist


class Command(BaseCommand):
    """
     Export values from the simplified couchdb database into a set of CSV files or ZIP files
    """

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
                    help='CouchDB server alias to connect to (staging | localhost). Defaults to staging.'),
        make_option('--skip-existing',
                    dest='skip_existing',
                    action='store_true',
                    default=False,
                    help='Skip existing cities. Use to speed up long import of many cities, when errors occur'),
        make_option('--output-path',
                    dest='output_path',
                    default=settings.OPENDATA_ROOT,
                    help='Path to the base directory where the file(s) will be created: default to opendata folder'),
        make_option('--compress',
                    dest='compress',
                    action='store_true',
                    default=False,
                    help="Generate compressed zip archive of the directory for each city, remove directory structure"),
        make_option('--append',
                    dest='append',
                    action='store_true',
                    default=False,
                    help='Use the log file appending instead of overwriting (used when launching shell scripts)'),
    )

    help = 'Export values from the simplified couchdb database into a set of CSV files'

    logger = logging.getLogger('management')
    comuni_dicts = {}
    voci_dict = None
    years = None

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
        output_path = options['output_path']
        compress = options['compress']
        skip_existing = options['skip_existing']

        if options['append'] is True:
            self.logger = logging.getLogger('management_append')

        ###
        # cities
        ###
        cities_codes = options['cities']
        if not cities_codes:
            raise Exception("Missing cities parameter")

        mapper = FLMapper(settings.LISTA_COMUNI_PATH)
        cities = mapper.get_cities(cities_codes)

        if not cities:
            self.logger.error("Cities cannot be null")
            return

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

        ###
        # connect to couchdb
        ###

        couchdb_server_alias = options['couchdb_server']
        couchdb_dbname = settings.COUCHDB_SIMPLIFIED_NAME

        if couchdb_server_alias not in settings.COUCHDB_SERVERS:
            raise Exception("Unknown couchdb server alias.")

        couchdb = couch.connect(
            couchdb_dbname,
            couchdb_server_settings=settings.COUCHDB_SERVERS[couchdb_server_alias]
        )

        output_abs_path = os.path.abspath(output_path)
        csv_path = os.path.join(output_abs_path, 'csv')
        zip_path = os.path.join(output_abs_path, 'zip')

        # build the map of slug to pk for the Voce tree
        self.voci_dict = Voce.objects.get_dict_by_slug()

        for city in cities:

            # check city path (skip if existing and skip-existing active)
            city_path = os.path.join(csv_path, city)
            if not os.path.exists(city_path):
                os.makedirs(city_path)
            else:
                # if the file for the city already exists and
                # skip-existing was specified then skips
                if skip_existing:
                    self.logger.info(u"Skipping city of {}, as already processed".format(city))
                    continue

            # get all budgets for the city
            city_budget = couchdb.get(city)

            if city_budget is None:
                self.logger.warning(u"City {} not found in couchdb instance. Skipping.".format(city))
                continue

            # get territorio corrsponding to city (to compute percapita values)
            try:
                territorio = Territorio.objects.get(cod_finloc=city)
            except ObjectDoesNotExist:
                territorio = None
                self.logger.warning(u"City {0} not found among territories in DB. Skipping.".format(city))
                continue

            self.logger.info(u"Processing city of {0}".format(city))

            for year in years:
                if str(year) not in city_budget:
                    self.logger.warning(u"- Year {} not found. Skipping.".format(year))
                    continue

                self.logger.info(u"- Processing year: {}".format(year))

                # check year path
                year_path = os.path.join(city_path, str(year))
                if not os.path.exists(year_path):
                    os.mkdir(year_path)

                # fetch valid population, starting from this year
                # if no population found, set it to None, as not to break things
                try:
                    (pop_year, population) = territorio.nearest_valid_population(year)
                except TypeError:
                    population = None
                self.logger.debug("::Population: {0}".format(population))

                # build a BilancioItem tree, out of the couch-extracted dict
                # for the given city and year
                # add the totals by extracting them from the dict, or by computing
                city_year_budget_dict = city_budget[str(year)]
                city_year_preventivo_tree = tree_models.make_tree_from_dict(
                    city_year_budget_dict['preventivo'], self.voci_dict, path=[u'preventivo'],
                    population=population
                )
                city_year_consuntivo_tree = tree_models.make_tree_from_dict(
                    city_year_budget_dict['consuntivo'], self.voci_dict, path=[u'consuntivo'],
                    population=population
                )

                # write csv file
                csv_filename = os.path.join(year_path, "preventivo.csv")
                csv_file = open(csv_filename, 'w')
                csv_writer = unicode_csv.UnicodeWriter(csv_file, dialect=unicode_csv.excel_semicolon)

                # build and emit header
                row = ['Path', 'Valore', 'Valore procapite']
                csv_writer.writerow(row)

                # emit preventivo content
                _list = []
                city_year_preventivo_tree.emit_as_list(_list, ancestors_separator="/")
                csv_writer.writerows(_list)

                # open csv file
                csv_filename = os.path.join(year_path, "consuntivo.csv")
                csv_file = open(csv_filename, 'w')
                csv_writer = unicode_csv.UnicodeWriter(csv_file, dialect=unicode_csv.excel_semicolon)

                # build and emit header
                row = ['Path', 'Valore', 'Valore procapite']
                csv_writer.writerow(row)

                # emit preventivo content
                _list = []
                city_year_consuntivo_tree.emit_as_list(_list, ancestors_separator="/")
                csv_writer.writerows(_list)

            # if the zip file is requested, creates the zip folder,
            # creates zip file
            if compress:

                if not os.path.exists(zip_path):
                    os.mkdir(zip_path)

                zipfilename = os.path.join(zip_path, "{}.zip".format(city))

                zipdir(city, zipfile.ZipFile(zipfilename, "w", zipfile.ZIP_DEFLATED), root_path=csv_path)
                self.logger.info("Compressed!")

    def write_csv(self, path, name, tree):

        # open csv file
        csv_filename = os.path.join(path, "{0}.csv".format(name))
        csv_file = open(csv_filename, 'w')
        csv_writer = unicode_csv.UnicodeWriter(csv_file, dialect=unicode_csv.excel_semicolon)

        # build and emit header
        row = ['Path', 'Valore', 'Valore procapite']
        csv_writer.writerow(row)

        # emit preventivo content
        _list = []
        tree.emit_as_list(_list, ancestors_separator="/")
        csv_writer.writerows(_list)
