# coding=utf-8
import csvkit
import logging
from optparse import make_option

from django.conf import settings
from django.core.management import BaseCommand
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from bilanci.models import Voce, ValoreBilancio

##
# extract values for a single Voce, for all cities and given years
##

class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('--site-url',
                    dest='site_url',
                    default='http://www.openbilanci.it',
                    help='The site homepage URL, to test in development or staging environments'),
        make_option('--voce-slug',
                    dest='voce-slug',
                    default='',
                    help='Slug of the voce to extract as CSV'),
        make_option('--years',
                    dest='years',
                    default='',
                    help='Years to fetch. From 2002 to 2012. Use one of this formats: 2012 or 2003-2006 or 2002,2004,2006'),
        make_option('--dry-run',
                    dest='dryrun',
                    action='store_true',
                    default=False,
                    help='Set the dry-run command mode: nothing is written in the db'),

    )

    help = """
        Compute indicators value for all cities and spits them out as CSV
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
        # check that the voce has been specified
        ###
        voce_slug = options['voce-slug']
        if not voce_slug:
           raise Exception("Missing voce-slug parameter")


        ###
        # dry run
        ###
        dryrun = options['dryrun']

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
            years = [int(y.strip()) for y in years.split(",") if 2001 < int(y.strip()) < 2014]

        if not years:
            raise Exception("No suitable year found in {0}".format(years))

        # site_url
        site_url = options['site_url']


        self.logger.info("Processing voce: {0} for years: {1}".format(voce_slug, years))
        self.voce_slug = voce_slug
        self.years = years

 
        voce = Voce.objects.get(slug=self.voce_slug)

        for year in years:
            self.logger.info("Processing year: {0}".format(year))
            self.logger.debug(" reading voce values")
            valori = ValoreBilancio.objects.filter(voce=voce, anno=year)\
                .values('territorio__denominazione', 'territorio__istat_id', 'valore', 'valore_procapite') 
  
            self.logger.debug(" writing output to {0}_{1}.csv".format(voce_slug, year))
            with open("{0}_{1}.csv".format(voce_slug, year), 'wb') as csvfile:
                writer = csvkit.py2.CSVKitWriter(csvfile, delimiter=",")
                writer.writerow(["comune","codice_istat","valore","valore_procapite"])
                for v in valori:
                    writer.writerow([
                        v['territorio__denominazione'], 
                        v['territorio__istat_id'],
                        "{0}".format(v['valore']),
                        "{0:.2f}".format(v['valore_procapite'])
                    ])
