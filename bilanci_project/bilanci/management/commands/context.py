# coding=utf-8
import logging
from optparse import make_option
from pprint import pprint
import re
import numpy
import math

from django.conf import settings
from django.core.management import BaseCommand
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

from bilanci.utils.comuni import FLMapper
from territori.models import Territorio, Contesto
from bilanci.utils import couch


class Command(BaseCommand):

    couchdb = None
    logger = logging.getLogger('management')
    comuni_dicts = {}

    option_list = BaseCommand.option_list + (
        make_option('--years',
                    dest='years',
                    default='',
                    help='Years to fetch. From 2002 to 2012. Use one of this formats: 2012 or 2003-2006 or 2002,2004,2006'),
        make_option('--cities',
                    dest='cities',
                    default='',
                    help="""
                        Cities codes or slugs. Use comma to separate values: Roma,Napoli,Torino or  "All".
                        NOTE: Cities are considered only for set_contesto function
                        """),
        make_option('--couchdb-server',
                    dest='couchdb_server',
                    default=settings.COUCHDB_DEFAULT_SERVER,
                    help='CouchDB server to connect to (defaults to staging).'),
        make_option('--skip-existing',
                    dest='skip_existing',
                    action='store_true',
                    default=False,
                    help='Skip existing cities. Use to speed up long import of many cities, when errors occur'),
        make_option('--dry-run',
                    dest='dryrun',
                    action='store_true',
                    default=False,
                    help='Set the dry-run command mode: nothing is written in the db'),
        make_option('--append',
                    dest='append',
                    action='store_true',
                    default=False,
                    help='Use the log file appending instead of overwriting (used when launching shell scripts)'),
    )

    help = """
        Compute territorial context data for the Bilanci db:
        """



    def clean_data(self,data):

        if data:
            if data == "N.C.":
                return None
            else:


                # removes the decimals, if any
                regex = re.compile("^.+,([\d]{2})$")
                matches = regex.findall(data)
                if len(matches) > 0:
                    data = data[:-3]

                # removes the thousand-delimiter point and the comma and converts to int
                ret =  int(data.replace(".","").replace(",",""))

                if ret > 10 * 1000 * 1000:
                    return None
                else:
                    return ret



    def get_data(self, territorio, years, key_name):

        # gets the context data relative to the provided key_name
        # from couchdb objects and checks that the numeric data on the values provided.
        # If some value is out of the line of the mean and variance then the value is discarded.
        # Return value: a list of tuple [(year, value), ...] of correct values

        value_set = []
        value_dict = {}
        results = []

        titoli_possibile_names = [
            "quadro-1-dati-generali-al-31-dicembrenotizie-varie",
            "quadro-1-dati-generali-al-31-dicembre-notizie-varie",
            "quadro-1-dati-generali-al-31-dicembre-1-notizie-varie"
        ]

        #     generates bilancio ids
        bilancio_ids = ["{0}_{1}".format(year, territorio.cod_finloc) for year in years]

        # read data from couch
        for bilancio_id in bilancio_ids:
            if bilancio_id in self.couchdb:
                bilancio_data = self.couchdb[bilancio_id]

                if "01" in bilancio_data['consuntivo']:
                    for titolo_name in titoli_possibile_names:
                        if titolo_name in bilancio_data["consuntivo"]["01"]:
                            break
                    else:
                        titolo_name = None

                    if titolo_name:
                        contesto_couch = bilancio_data["consuntivo"]["01"]\
                            [titolo_name]["data"]

                        if key_name in contesto_couch:
                            clean_data = self.clean_data(contesto_couch[key_name][0])

                            # clean_data is None if the contesto_data is = "N.C", so I set it for deletion
                            if clean_data is None:
                                results.append((bilancio_id[0:4],None))
                            else:
                                value_set.append(clean_data)
                                value_dict[int(bilancio_id[0:4])] = self.clean_data(contesto_couch[key_name][0])
                    else:
                        self.logger.warning(u"Titolo 'quadro-1-dati-generali-al-31-dicembre[-]notizie-varie' not found for id:{0}, skipping". format(bilancio_id))
                else:
                    self.logger.warning(u"Quadro '01' Consuntivo not found for id:{0}, skipping".format(bilancio_id))

            else:
                    self.logger.warning(u"Bilancio obj not found for id:{0}, skipping". format(bilancio_id))

        if len(value_set) == 0:
            self.logger.warning(u"Cannot find data about {0} for city:{1} during the years:{2}".format(key_name, territorio, years))
            return

        mean = numpy.mean(value_set)
        variance = numpy.var(value_set)

        # Coherence check on values.
        # if the value is in line with the values in the serie then it's accepted and it will be saved,
        # otherwise the value is discarded
        for anno, value in value_dict.iteritems():
            if pow((value-mean),2) < variance*4:
                results.append((anno, value))
            else:
                results.append((anno, None))

        return results




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

        ###
        # dry run
        ###
        dryrun = options['dryrun']
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
            years = range(int(start_year), int(end_year)+1)
        else:
            years = [int(y.strip()) for y in years.split(",") if 2001 < int(y.strip()) < 2013]

        if not years:
            raise Exception("No suitable year found in {0}".format(years))

        self.logger.info("Processing years: {0}".format(years))
        self.years = years


        ###
        # couchdb
        ###

        couchdb_server_alias = options['couchdb_server']
        couchdb_dbname = settings.COUCHDB_NORMALIZED_VOCI_NAME

        if couchdb_server_alias not in settings.COUCHDB_SERVERS:
            self.logger.error(u"Unknown couchdb server alias.")
            return


        self.logger.info(u"Connecting to db: {0}".format(couchdb_dbname))
        self.couchdb = couch.connect(
            couchdb_dbname,
            couchdb_server_settings=settings.COUCHDB_SERVERS[couchdb_server_alias]
        )


        # set contesto and filter out missing territories
        missing_territories = []

        for city in cities:

            try:
                territorio = Territorio.objects.get(cod_finloc=city)
            except ObjectDoesNotExist:
                self.logger.warning(u"City {0} not found among territories in DB. Skipping.".format(city))
                missing_territories.append(city)
                continue

            # if skip_existing and the territorio has 1+ contesto then skip territorio
            if skip_existing and Contesto.objects.filter(territorio=territorio).count() > 0:
                    self.logger.info(u"Skip Existing - City:{0} already has context, skipping".format(territorio.denominazione))
                    continue

            self.logger.info(u"Setting context for city: {0}".format(territorio,))

            # note: the following keys will not be stored in the db because
            # the number format is not constant through the years
            #
            # "nuclei familiari (n)":"bil_nuclei_familiari",
            # "superficie urbana (ha)":"bil_superficie_urbana",
            # "superficie totale del comune (ha)":"bil_superficie_totale",
            # "lunghezza delle strade esterne (km)":"bil_strade_esterne",
            # "lunghezza delle strade interne centro abitato (km)":"bil_strade_interne",
            # "di cui: in territorio montano (km)":"bil_strade_montane",

            key_name = "popolazione residente (ab.)"
            data_results = self.get_data(territorio, years, key_name)

            for data_result in data_results:
                contesto_pg = None
                year, value = data_result

                # if value is None it means that the year selected had a value for the key that is not acceptable or wrong
                # then if the value for that specific year is already in the db, it has to be deleted
                if value is None:

                    self.logger.warning(u"Deleting wrong value for city:{0} year:{1}".format(territorio.denominazione, year))
                    _ = Contesto.objects.filter(
                        anno = year,
                        territorio = territorio,
                    ).delete()
                    continue


                # if the contesto data is not present, inserts the data in the db
                # otherwise skips

                try:
                    contesto_pg = Contesto.objects.get(
                        anno = year,
                        territorio = territorio,
                    )
                except ObjectDoesNotExist:
                    contesto_pg = Contesto()
                    pass


                # write data on postgres
                if dryrun is False:
                    contesto_pg.bil_popolazione_residente = value
                    self.logger.debug(u"year:{0}, value:{1}".format(year, value,))

                    contesto_pg.territorio = territorio
                    contesto_pg.anno = year
                    contesto_pg.save()


        if len(missing_territories)>0:
            self.logger.error(u"Following cities could not be found in Territori DB and could not be processed:")
            for missing_city in missing_territories:
                self.logger.error("{0}".format(missing_city))

