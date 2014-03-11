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

        per_capita_affix = "-PC"
        # check that all the slugs mentioned in the meta-formula are present in the simplified tree
        # if some voice slug contains the substring "-PC" then that should be considered as a per-capita value
        # so the "-PC" substring must be removed from slug to check the existance of the voice in the simple tree
        voices_raw_list = re.findall(r'"(.*?)"',indicator.formula)

        # voices list is a list of dicts that
        # keeps track of every slug present in the original formula, the real slug to look for in the db
        # and a boolean flag that tells if the absolute value or the per-capita value should be used
        # voices_list = [{'raw_slug': 'voice-slug-PC', 'real_slug': 'voice-slug", 'is_per_capita':True},]

        voices_list = []


        # transform a list of city codes, "cities" in a list of Territori obj
        territori = []
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
                continue

            territori.append(territorio)

        # adds the bogus Territori Cluster so the indicator is calculed for clusters too
        territori.extend(Territorio.objects.filter(territorio=Territorio.TERRITORIO.L))


        for voice in voices_raw_list:
            real_slug = voice
            is_per_capita = False

            # if "-PC" is found at the end of the voice then it's removed
            if voice.find(per_capita_affix) == len(voice)-len(per_capita_affix):
                real_slug = voice[:-len(per_capita_affix)]
                is_per_capita = True

            voices_list.append(
                {
                    'raw_slug':voice,
                    'real_slug': real_slug,
                    'is_per_capita': is_per_capita
                }
            )

            try:
                Voce.objects.get(
                    slug = real_slug
                )
            except ObjectDoesNotExist:
                self.logger.error("Voce with slug:{0} not present in simplified tree. Skipping indicator {1}".\
                    format(real_slug, indicator.denominazione))
                return

        for territorio in territori:
            for year in years:

                # create a dictionary which has the Voce slug as key which is associated
                # with the value the Voce had for that
                # year in that city
                voci = {}
                all_values_found = True
                for voice_dict in voices_list:
                    try:
                        valore_bilancio = ValoreBilancio.objects.get(
                            voce__slug = voice_dict['real_slug'],
                            anno = year,
                            territorio = territorio,
                        )
                    except ObjectDoesNotExist:
                        self.logger.error("Voce with slug:{0} does not exist for Comune:{1}, year:{2}, skipping this year".\
                            format( voice_dict['real_slug'], territorio.denominazione, year))
                        all_values_found = False
                        break

                    if voice_dict['is_per_capita']:
                        voci[voice_dict['raw_slug']] = valore_bilancio.valore_procapite
                    else:
                        voci[voice_dict['raw_slug']] = valore_bilancio.valore

                if all_values_found is False:
                    self.logger.warning("Formula cannot be calculed for Comune:{0}, year:{1}, indicator {2}, skipping this year".\
                        format(city, year, indicator.denominazione))
                    continue

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
                    indicator_result = eval(indicator_formula)
                except ValueError:
                    self.logger.error("Indicator formula: {0} is malformed".format(indicator_formula))
                    return

                self.logger.debug("Comune:{0}, year:{1}, Indicator {2}: {3}".\
                    format(city, year, indicator.denominazione, indicator_result)
                    )


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








