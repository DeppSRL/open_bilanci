from ast import literal_eval
from pprint import pprint
import re
from django.core.exceptions import ObjectDoesNotExist
import logging
from optparse import make_option
from django.conf import settings
from django.core.management import BaseCommand
from bilanci.models import Voce, ValoreBilancio, Indicatore, ValoreIndicatore
from bilanci.utils.comuni import FLMapper
from territori.models import Territorio, Contesto
from bilanci.utils import couch


class Command(BaseCommand):

    accepted_indicators = Indicatore.objects.all().values_list('denominazione',flat=True)

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
                        """),

        make_option('--indicator','-i',
                    dest='indicator',
                    action='store',
                    default='',
                    help='Indicator to calculate: all | '+  ' | '.join(accepted_indicators)+".Use comma to separate values"),


        make_option('--dry-run',
                    dest='dryrun',
                    action='store_true',
                    default=False,
                    help='Set the dry-run command mode: nothing is written in the db'),

    )

    help = """
        Compute indicators values for Bilanci in the db
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

        indicator_string = options['indicator']
        indicators = []
        if indicator_string:
            if indicator_string.lower() == "all":
                all_indicators = Indicatore.objects.all()
                indicators.extend(all_indicators)

            else:

                # separates the indicator_string by ","
                indicator_names = indicator_string.split(",")

                for indicator_name in indicator_names:

                    ##
                    # get indicatore from indicator_name
                    ##

                    try:
                        indicators.append(Indicatore.objects.get(denominazione = indicator_name))

                    except ObjectDoesNotExist:
                        self.logger.error("Indicator: {0} not found in db".format(indicator_name))
                        return

        else:
            self.logger.error("Missing indicator parameter")
            return


        ###
        # dry run
        ###

        dryrun = options['dryrun']

        ###
        # cities
        ###

        cities_codes = options['cities']

        if not cities_codes:
            self.logger.error("Missing city parameter")
            return

        self.logger.info("Opening Lista Comuni")
        mapper = FLMapper(settings.LISTA_COMUNI_PATH)
        cities = mapper.get_cities(cities_codes)
        if cities_codes.lower() != 'all':
            self.logger.info("Considering cities: {0}".format(cities))


        ###
        # years
        ###
        years = options['years']
        if not years:
            self.logger.error("Missing years parameter")
            return

        if "-" in years:
            (start_year, end_year) = years.split("-")
            years = range(int(start_year), int(end_year)+1)
        else:
            years = [int(y.strip()) for y in years.split(",") if 2001 < int(y.strip()) < 2013]

        if not years:
            self.logger.error("No suitable year found in {0}".format(years))
            return

        self.logger.info("Considering years: {0}".format(years))

        for indicator in indicators:
            self.logger.info("Calculating values for indicator: {0}".format(indicator.denominazione))
            self.compute_indicator(indicator, cities, years, dryrun)






    def compute_indicator(self, indicator, cities, years, dryrun):


        # check that all the slugs mentioned in the meta-formula are present in the simplified tree
        voices_list = re.findall(r'"(.*?)"',indicator.formula)
        for voice in voices_list:
            try:
                Voce.objects.get(
                    slug = voice
                )
            except ObjectDoesNotExist:
                self.logger.error("Voce with slug:{0} not present in simplified tree".\
                    format(voice))
                return




        for year in years:
            for city in cities:

                territorio = None
                # looks for territorio in db
                try:
                    territorio = Territorio.objects.get(
                        territorio = 'C',
                        cod_finloc = city,
                    )
                except ObjectDoesNotExist:
                    self.logger.error("Territorio {0} does not exist in Territori db".format(city))
                    return

                # create a dictionary which has the Voce slug as key which is associated with the value the Voce had for that
                # year in that city
                voci = {}
                for voice in voices_list:
                    try:
                        voci[voice] = ValoreBilancio.objects.get(
                            voce__slug = voice,
                            anno = year,
                            territorio = territorio,
                        )
                    except ObjectDoesNotExist:
                        self.logger.error("Voce with slug:{0} does not exist for Comune:{1}, year:{2}".\
                            format(voice, territorio.denominazione, year))
                        return

                ##
                # convert indicator formula from redational meta-language to operational string
                # Example:
                # from:
                # '("valore-a" + "valore-b") / ("valore-c" - "valore-d")'
                # to:
                # "(voci['valore-a'] + voci['valore-b']) / (voci['valore-c'] - voci['valore-d'])"
                ##

                meta_formula = indicator.formula
                indicator_formula = re.sub(r'"(.*?)"', r"voci['\1']", meta_formula )
                # compute the result applying the formula
                try:
                    indicator_result = literal_eval(indicator_formula)
                except ValueError:
                    self.logger.error("Indicator formula: {0} is malformed".format(indicator_formula))
                    return
                pprint(indicator_result)


                ##
                # save the value into db
                ##
                if dryrun is False:
                    indicator_value = None
                    try:
                        indicator_value = ValoreIndicatore.objects.get(
                            anno = year,
                            territorio = territorio,
                            indicatore = indicator,
                        )

                    except ObjectDoesNotExist:
                        indicator_value = ValoreIndicatore()
                        indicator_value.indicatore = indicator
                        indicator_value.anno = year
                        indicator_value.territorio = territorio


                    indicator_value.valore = indicator_result
                    indicator_value.save()








