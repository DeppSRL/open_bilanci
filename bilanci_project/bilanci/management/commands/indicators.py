from django.conf import settings
from django.core.management import BaseCommand
from django.utils.module_loading import import_by_path
from bilanci.models import Indicatore
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
                    help='Cities codes or slugs. Use comma to separate values: Roma,Napoli,Torino or "All"'),
        make_option('--indicators',
                    dest='indicators',
                    default='all',
                    help='Indicators slugs. Use comma to separate values: grado-rigidita-strutturale-spesa,autonomia-finanziaria or "All"'),
        make_option('--skip-existing',
                    dest='skip_existing',
                    action='store_true',
                    default=False,
                    help='Skip existing documents. Use to speed up long import of many cities, when errors occur'),
        make_option('--append',
                    dest='append',
                    action='store_true',
                    default=False,
                    help='Use the log file appending instead of overwriting (used when launching shell scripts)'),
    )

    help = 'Compute indicators\' values for given cities and years.'

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

        if options['append'] is True:
            self.logger = logging.getLogger('management_append')


        # massaging cities option and getting cities finloc codes
        cities_codes = options['cities']
        if not cities_codes:
            raise Exception("Missing city parameter")
        mapper = FLMapper(settings.LISTA_COMUNI_PATH)
        cities = mapper.get_cities(cities_codes)
        if cities_codes.lower() != 'all':
            self.logger.info("Processing cities: {0}".format(cities))

        # massaging years option
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

        # massaging indicators option
        indicators_slugs = options['indicators']
        indicators_slugs = [(i.strip()) for i in indicators_slugs.split(",")]

        # meta-programming
        # using the bilanci.indicators module to read indicators and their formulas
        # generating records in the DB, if not existing
        base_class = import_by_path('bilanci.indicators.BaseIndicator')
        indicators_instances = []
        for attr_name in dir(indicators):
            if attr_name.endswith("Indicator") and attr_name != base_class.__name__:
                indicator_class = import_by_path("bilanci.indicators.{0}".format(attr_name))
                indicator_instance = indicator_class()

                # skip indicators not in --indicators slugs
                if indicators_slugs != ['all'] and not indicator_instance.slug in indicators_slugs:
                    continue
                indicators_instances.append(indicator_instance)

                # singleton - create indicator record in the DB, if non existing
                #             update existing denominazione, with label in class, if existing
                indicator_obj, created = Indicatore.objects.get_or_create(
                    slug=indicator_instance.slug,
                    defaults={
                        'denominazione': indicator_instance.label
                    }
                )
                if not created:
                    indicator_obj.denominazione = indicator_instance.label
                    indicator_obj.save()

        # actual computation of the values
        for indicator in indicators_instances:
            self.logger.info(u"Indicator: {0}".format(
                indicator.label
            ))
            if dryrun:
                # no db storage
                _ = indicator.compute(cities, years, logger=self.logger)
            else:
                # db storage
                indicator.compute_and_commit(cities, years, logger=self.logger, skip_existing=skip_existing)
