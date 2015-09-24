# coding=utf-8
import csvkit
import logging
from optparse import make_option

from django.conf import settings
from django.core.management import BaseCommand
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from bilanci.models import Indicatore, ValoreIndicatore

##
# compute indicators value for all cities, for given years
##

class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('--site-url',
                    dest='site_url',
                    default='http://www.openbilanci.it',
                    help='The site homepage URL, to test in development or staging environments'),
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


        self.logger.info("Processing years: {0}".format(years))
        self.years = years

        indicatori = Indicatore.objects.all()
        indicatori_year = {}

        for year in years:
            self.logger.info("Processing year: {0}".format(year))
            self.logger.debug(" reading indicatori values")
            for i in indicatori: 
                iv = ValoreIndicatore.objects.filter(indicatore__slug=i.slug, anno=year).values('territorio__istat_id', 'territorio__slug', 'valore')
                for v in iv:
                    t_id = v['territorio__istat_id']
                    t_slug = v['territorio__slug']
                    t_url = "{0}/bilanci/{1}?year={2}".format(site_url, t_slug, year)
                    val = v['valore']
                    if t_id not in indicatori_year:
                        indicatori_year[t_id] = { 'url': t_url, 'values': {}}
                    indicatori_year[t_id]['values'][i.id] = val
 
  
            self.logger.debug(" writing output to ind_{0}.csv".format(year))
            with open("ind_{0}.csv".format(year), 'wb') as csvfile:
                writer = csvkit.py2.CSVKitWriter(csvfile, delimiter=";")
                writer.writerow(["istat_id", "url"] + [i.denominazione for i in indicatori])
                for t_id, iv  in indicatori_year.items():
                    writer.writerow([t_id, iv['url']] + ["%.2f" % iv['values'][i.id] if i.id in iv['values'] else '0' for i in indicatori])
