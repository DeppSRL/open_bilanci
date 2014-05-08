# coding=utf-8
import logging
from optparse import make_option
import re

from django.conf import settings
from django.core.management import BaseCommand
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

from bilanci.utils.comuni import FLMapper
from territori.models import Territorio, Contesto
from bilanci.utils import couch


class Command(BaseCommand):

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
        couchdb = couch.connect(
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

            for year in years:

                self.logger.info(u"Setting context for city: {0}, year:{1}".format(territorio,year))
                bilancio_id = "{0}_{1}".format(year, territorio.cod_finloc)

                # read data from couch
                if bilancio_id in couchdb:
                    bilancio_data = couchdb[bilancio_id]
                    titoli = [
                        "quadro-1-dati-generali-al-31-dicembrenotizie-varie",
                        "quadro-1-dati-generali-al-31-dicembre-notizie-varie",
                        "quadro-1-dati-generali-al-31-dicembre-1-notizie-varie"
                    ]
                    if "01" in bilancio_data['consuntivo']:
                        for titolo in titoli:
                            if titolo in bilancio_data["consuntivo"]["01"]:
                                break
                        else:
                            titolo = None

                        if titolo:
                            contesto_couch = bilancio_data["consuntivo"]["01"]\
                                [titolo]["data"]

                            # if the contesto data is not present, inserts the data in the db
                            # otherwise skips
                            contesto_pg = None
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


                                # contesto_keys maps the key in the couch doc and the name of
                                # the field in the model

                                contesto_keys = {
                                    "popolazione residente (ab.)":"bil_popolazione_residente",

                                    # note: the following keys will not be stored in the db because
                                    # the number format is not constant through the years
                                    #
                                    # "nuclei familiari (n)":"bil_nuclei_familiari",
                                    # "superficie urbana (ha)":"bil_superficie_urbana",
                                    # "superficie totale del comune (ha)":"bil_superficie_totale",
                                    # "lunghezza delle strade esterne (km)":"bil_strade_esterne",
                                    # "lunghezza delle strade interne centro abitato (km)":"bil_strade_interne",
                                    # "di cui: in territorio montano (km)":"bil_strade_montane",
                                    }

                                for contesto_key, contesto_value in contesto_keys.iteritems():
                                    if contesto_key in contesto_couch:
                                        value = clean_data(contesto_couch[contesto_key])
                                        setattr(contesto_pg, contesto_value, value)
                                        self.logger.debug(u"    key: {0}, value:{1}".format(contesto_key, value))


                                contesto_pg.territorio = territorio
                                contesto_pg.anno = year

                                contesto_pg.save()



                        else:
                            self.logger.warning(u"Titolo 'quadro-1-dati-generali-al-31-dicembre[-]notizie-varie' not found for id:{0}, skipping". format(bilancio_id))
                    else:
                        self.logger.warning(u"Quadro '01' not found for id:{0}, skipping".format(bilancio_id))

                else:
                    self.logger.warning(u"Bilancio obj not found for id:{0}, skipping". format(bilancio_id))

        if len(missing_territories)>0:
            self.logger.error(u"Following cities could not be found in Territori DB and could not be processed:")
            for missing_city in missing_territories:
                self.logger.error("{0}".format(missing_city))


def clean_data(data_list):
    data = data_list[0]
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



