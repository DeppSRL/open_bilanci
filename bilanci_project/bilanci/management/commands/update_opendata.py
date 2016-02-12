import logging
from optparse import make_option
import os
import zipfile
from django.conf import settings
from django.core.management import BaseCommand
from bilanci.models import Voce, ValoreBilancio, ImportXmlBilancio
from bilanci.utils import couch
from bilanci.utils.comuni import FLMapper
from bilanci.utils.converters import FLCSVEmitter
from bilanci.utils.zipper import zipdir_prefix
from territori.models import ObjectDoesNotExist


class Command(BaseCommand):
    """
     Export values from the simplified couchdb database into a set of ZIP files
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
        make_option('--append',
                    dest='append',
                    action='store_true',
                    default=False,
                    help='Use the log file appending instead of overwriting (used when launching shell scripts)'),
    )

    help = 'Export values from the raw couchdb database into a set of CSV files'

    logger = logging.getLogger('management')
    comuni_dicts = {}
    voci_dict = None
    years = None

    def connect_to_couch(self, couchdb_server):
        couchdb_server_alias = couchdb_server
        couchdb_dbname = settings.COUCHDB_RAW_NAME

        if couchdb_server_alias not in settings.COUCHDB_SERVERS:
            raise Exception("Unknown couchdb server alias.")

        return couch.connect(
            couchdb_dbname,
            couchdb_server_settings=settings.COUCHDB_SERVERS[couchdb_server_alias]
        )

    def create_if_not_exist(self, path):
        if not os.path.exists(path):
            os.makedirs(path)
            return False
        return True

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
        skip_existing = options['skip_existing']

        if options['append'] is True:
            self.logger = logging.getLogger('management_append')

        ###
        # cities
        ###
        cities_codes = options['cities']
        if not cities_codes:
            raise Exception("Missing cities parameter")

        mapper = FLMapper()
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
            years = [int(y.strip()) for y in years.split(",") if settings.APP_START_YEAR < int(y.strip()) < settings.APP_END_YEAR]

        if not years:
            raise Exception("No suitable year found in {0}".format(years))

        self.logger.info("Processing years: {0}".format(years))
        self.years = years

        # instantiate emitter
        # to emit CSV files
        emitter = FLCSVEmitter(self.logger)

        ###
        # connect to couchdb
        ###
        couchdb = self.connect_to_couch(couchdb_server=options['couchdb_server'])

        output_abs_path = os.path.abspath(output_path)
        csv_path = os.path.join(output_abs_path, 'csv')
        xml_path = os.path.join(output_abs_path, 'xml')
        zip_path = os.path.join(output_abs_path, 'zip')

        self.create_if_not_exist(csv_path)
        self.create_if_not_exist(xml_path)
        self.create_if_not_exist(zip_path)

        # build the map of slug to pk for the Voce tree
        self.voci_dict = Voce.objects.get_dict_by_slug()

        for city in cities:

            # check city path (skip if existing and skip-existing active)
            city_path = os.path.join(csv_path, city)
            if self.create_if_not_exist(city_path):
                # if the folder for the city already exists and
                # skip-existing was specified then skips
                if skip_existing:
                    self.logger.info(u"Skipping city of {}, as already processed".format(city))
                    continue

            self.logger.info(u"Processing city: {}".format(city))
            for year in years:

                # get year budgets for the city
                key = u"{}_{}".format(year, city)
                city_budget = couchdb.get(key)

                if city_budget is None:
                    self.logger.warning(u"Budget for:{} not found in couchdb. Skipping.".format(key))
                    continue

                self.logger.debug(u"Processing: {}".format(key))

                # check year path
                year_path = os.path.join(city_path, str(year))
                self.create_if_not_exist(year_path)

                # if for current city/year was imported a XML bilancio, then skips the Couchdb data, xml file
                # will be provided instead
                try:
                    ImportXmlBilancio.objects.\
                        get(territorio__cod_finloc=city, anno=year, tipologia=ImportXmlBilancio.TIPO_CERTIFICATO.preventivo)
                except ObjectDoesNotExist:
                    pass
                else:
                    self.logger.info(u"Budget:{} for:{} will be provided only in xml".format('preventivo', key))

                # save preventivo
                self.logger.debug("    Preventivo")
                prev_path = os.path.join(year_path, 'preventivo')
                self.create_if_not_exist(prev_path)

                preventivo = city_budget.get('preventivo', None)
                if preventivo:
                    emitter.emit(q_data=preventivo, base_path=prev_path)

                # if for current city/year was imported a XML bilancio, then skips the Couchdb data, xml file
                # will be provided instead
                try:
                    ImportXmlBilancio.objects.\
                        get(territorio__cod_finloc=city, anno=year, tipologia=ImportXmlBilancio.TIPO_CERTIFICATO.consuntivo)
                except ObjectDoesNotExist:
                    pass
                else:
                    self.logger.info(u"Budget:{} for:{} will be provided only in xml".format('consuntivo', key))

                # save consuntivo

                self.logger.debug("    Consuntivo")
                cons_path = os.path.join(year_path, 'Consuntivo')
                self.create_if_not_exist(cons_path)

                consuntivo = city_budget.get('consuntivo', None)

                # emit q_data as CSV files in a directory tree
                if consuntivo:
                    emitter.emit(q_data=consuntivo, base_path=cons_path)

            # creates the zip folder, creates zip file
            zipfilename = os.path.join(zip_path, "{}.zip".format(city))

            # zips the csv and the xml folders and creates a zip file containing both
            # zipdir(city, zipfile.ZipFile(zipfilename, "w", zipfile.ZIP_DEFLATED), root_path=csv_path)
            opendata_zipfile = zipfile.ZipFile(zipfilename, "w", zipfile.ZIP_DEFLATED)
            zipdir_prefix(opendata_zipfile, csv_path, city, "csv")
            zipdir_prefix(opendata_zipfile, xml_path, city, "xml")
            opendata_zipfile.close()
            # remove the CSV file directory
            import shutil
            shutil.rmtree(csv_path)

            self.logger.info("Created zip file: {}".format(zipfilename))