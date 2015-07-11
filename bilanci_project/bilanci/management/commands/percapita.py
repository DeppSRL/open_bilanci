# coding=utf-8
import logging
from optparse import make_option

from django.conf import settings
from django.core.management import BaseCommand
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from bilanci.models import ValoreBilancio

from bilanci.utils.comuni import FLMapper
from territori.models import Territorio, Contesto
from bilanci.utils import couch

##
# recalculates per capita values for all values bilancio in the pg db
##

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
        make_option('--dry-run',
                    dest='dryrun',
                    action='store_true',
                    default=False,
                    help='Set the dry-run command mode: nothing is written in the db'),

    )

    help = """
        Recalculates per capita values for all Valore Bilancio
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

        ###
        # cities
        ###
        cities_codes = options['cities']
        if not cities_codes:
            raise Exception("Missing cities parameter")

        mapper = FLMapper()
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

        # set contesto and filter out missing territories
        missing_territories = []

        for city in cities:

            try:
                territorio = Territorio.objects.get(cod_finloc=city)
            except ObjectDoesNotExist:
                self.logger.warning(u"City {0} not found among territories in DB. Skipping.".format(city))

            for year in years:
                popolazione = None

                self.logger.info(u"Calculating percapita for city: {0}, year:{1}".format(territorio,year))

                # read data from db
                valore_yearset = ValoreBilancio.objects.filter(territorio=territorio, anno=year,)

                population_tuple = territorio.nearest_valid_population(year)
                if population_tuple is not None:
                    popolazione = population_tuple[1]
                    self.logger.debug(u"City:{0},year:{1},population:{2}".format(territorio,year, popolazione))
                else:
                    self.logger.error(u"Cannot find valid population data for city:{0}, year:{1}".format(territorio,year))
                    missing_territories.append((city,year))
                    continue

                for valore_obj in valore_yearset:

                    valore_obj.valore_procapite = valore_obj.valore*1.0/popolazione*1.0

                    if not dryrun:
                        valore_obj.save()

        if len(missing_territories)>0:
            self.logger.error(u"Following context could not be found in DB and could not be processed:")

            for missing_city, missing_yr in missing_territories:
                self.logger.error("City:{0}, Year:{1}".format(missing_city, missing_yr))

