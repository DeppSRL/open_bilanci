# -*- coding: utf-8 -*-
import logging
from optparse import make_option
from pprint import pprint
from django.core.exceptions import ObjectDoesNotExist
from django.core.management import BaseCommand
from django.conf import settings
from django.utils.datastructures import SortedDict
from bilanci.utils.comuni import FLMapper
from bilanci.utils import couch
from territori.models import Territorio, Contesto
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
        make_option('--dry-run',
                    dest='dryrun',
                    action='store_true',
                    default=False,
                    help='Set the dry-run command mode: nothing is written on db'),

    )

    help = 'Assign to Comuni in Territori Contesto values read from bilanci_voci Database'

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
            self.logger.debug("Analyzing following cities: {0}".format(cities))


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

        self.logger.debug("Analyzing years: {0}".format(years))

        if dryrun:
            self.logger.info("Dry run is: {0}".format(dryrun))


        ###
        # couchdb
        ###

        couchdb_server_alias = options['couchdb_server']
        couchdb_dbname = settings.COUCHDB_NORMALIZED_VOCI_NAME

        if couchdb_server_alias not in settings.COUCHDB_SERVERS:
            raise Exception("Unknown couchdb server alias.")


        self.logger.info("Connecting to db: {0}".format(couchdb_dbname))
        couchdb = couch.connect(
            couchdb_dbname,
            couchdb_server_settings=settings.COUCHDB_SERVERS[couchdb_server_alias]
        )


        self.get_contesto(couchdb, cities, years, dryrun)

        self.logger.info(u"End get contesto script")



    def get_contesto(self, couchdb, cities, years, dryrun):

        for city in cities:
            for year in years:
                self.logger.info(u"Setting Comune: {0}, year:{1}".format(city,year))

                bilancio_id = "{0}_{1}".format(year, city)
                # read data from couch
                if bilancio_id in couchdb:
                    bilancio_data = couchdb[bilancio_id]
                    if "01" in bilancio_data['consuntivo']:
                        if "quadro-1-dati-generali-al-31-dicembrenotizie-varie" in bilancio_data["consuntivo"]["01"]:
                            contesto_couch = bilancio_data["consuntivo"]["01"]\
                                ["quadro-1-dati-generali-al-31-dicembrenotizie-varie"]["data"]


                            # looks for territorio in db
                            try:
                                territorio = Territorio.objects.get(
                                    territorio = 'C',
                                    cod_finloc = city,
                                )
                            except ObjectDoesNotExist:
                                self.logger.error("Territorio {0} does not exist in Territori db, quitting".format(city))
                                return

                            # if the contesto data is not present, inserts the data in the db
                            # otherwise skips
                            try:
                                contesto_pg = Contesto.objects.get(
                                    anno = year,
                                    territorio = territorio,
                                )
                            except ObjectDoesNotExist:

                                # write data on postgres
                                if dryrun is False:
                                    contesto_pg = Contesto()
                                    contesto_pg.territorio = territorio
                                    contesto_pg.anno = year

                                    contesto_pg.nuclei_familiari = clean_data(contesto_couch["nuclei familiari (n)"])
                                    contesto_pg.superficie_urbana = clean_data(contesto_couch["superficie urbana (ha)"])
                                    contesto_pg.superficie_totale = clean_data(contesto_couch["superficie totale del comune (ha)"])
                                    contesto_pg.popolazione_residente = clean_data(contesto_couch["popolazione residente (ab.)"])
                                    contesto_pg.strade_esterne = clean_data(contesto_couch["lunghezza delle strade esterne (km)"])
                                    contesto_pg.strade_interne = clean_data(contesto_couch["lunghezza delle strade interne centro abitato (km)"])
                                    contesto_pg.strade_montane = clean_data(contesto_couch["di cui: in territorio montano (km)"])
                                    contesto_pg.save()



                        else:
                            self.logger.warning("Titolo 'quadro-1-dati-generali-al-31-dicembrenotizie-varie' not found for id:{0}, skipping". format(bilancio_id))
                    else:
                        self.logger.warning("Quadro '01' not found for id:{0}, skipping".format(bilancio_id))

                else:
                    self.logger.warning("Bilancio obj not found for id:{0}, skipping". format(bilancio_id))



        return


def clean_data(data):
    c_data = data[0]
    if c_data:
        if c_data == "N.C.":
            return None
        else:
            # if the number contains a comma, it strips the decimal values
            if c_data.find(",") != -1:
                c_data = c_data[:c_data.find(",")]

            # removes the thousand-delimiter point and converts to int
            return int(c_data.replace(".",""))


