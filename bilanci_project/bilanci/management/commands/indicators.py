from django.conf import settings
from django.core.management import BaseCommand
from django.utils.module_loading import import_by_path
from bilanci.utils.comuni import FLMapper
from  bilanci import indicators
import logging
from optparse import make_option
from territori.models import Territorio


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
        make_option('--skip-existing',
                    dest='skip_existing',
                    action='store_true',
                    default=False,
                    help='Skip existing documents. Use to speed up long import of many cities, when errors occur'),
    )

    help = 'Compute indicators for given cities and years.'

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

        skip_existing = options['skip_existing']

        cities_codes = options['cities']
        if not cities_codes:
            raise Exception("Missing city parameter")

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

        base_class = import_by_path('bilanci.indicators.BaseIndicator')
        indicators_instances = []
        for attr_name in dir(indicators):
            if attr_name.endswith("Indicator") and attr_name != base_class.__name__:
                indicator_class = import_by_path("bilanci.indicators.{0}".format(attr_name))
                indicators_instances.append(indicator_class())

        for indicator in indicators_instances:
            self.logger.debug("Indicator: {0}".format(
                indicator
            ))
            for city in cities:
                self.logger.debug("City: {0}".format(
                    city
                ))
                results_over_years = indicator.compute((city,), years)
                print results_over_years