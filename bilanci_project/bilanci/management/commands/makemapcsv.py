# coding=utf-8
import csvkit
import logging
from optparse import make_option

from django.conf import settings
from django.core.management import BaseCommand
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from bilanci.models import Indicatore, ValoreIndicatore, Voce, ValoreBilancio

##
# compute specific indicatore and budget voices values for all cities, in given years
##

class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('--site-url',
                    dest='site_url',
                    default='http://www.openbilanci.it',
                    help='The site homepage URL, to test in development or staging environments'),
        make_option('--year',
                    dest='year',
                    default='',
                    help='Year to fetch. From 2002.'),
        make_option('--dry-run',
                    dest='dryrun',
                    action='store_true',
                    default=False,
                    help='Set the dry-run command mode: nothing is written in the db'),
        make_option('--indicators',
                    dest='indicators',
                    default='autonomia-finanziaria,rigidita-della-spesa,spesa-personale-per-abitante,' +\
                            'affidabilita-residui-attivi,investimenti-per-abitante,debito-complessivo-entrate-correnti',
                    help='Indicators slugs. Use comma to separate values: autonomia-finanziaria,affidabilita-residui-attivi,...'),
        make_option('--voices',
                    dest='voices',
                    default='consuntivo-spese-cassa-spese-somma-funzioni-amministrazione,' +\
                            'consuntivo-spese-cassa-spese-somma-funzioni-sociale-asili-nido,' +\
                            'consuntivo-entrate-cassa-imposte-e-tasse,' +\
                            'consuntivo-entrate-cassa-entrate-extratributarie-utili-delle-aziende-partecipate',
                    help='Budget value voices\' slugs. Use comma to separate values, may use none'),
    )

    help = """
        Compute indicators and budget voices values for all cities and spits them out as CSV in the current directory. 
        Used to build data to be uploaded to CartoDB.
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
        # year
        ###
        year = options['year']
        if not year:
            raise Exception("Missing year parameter")

        # site_url
        site_url = options['site_url']


        self.logger.info("Processing years: {0}".format(year))
        self.year = year

        self.logger.info("Processing year: {0}".format(self.year))

        indicators_slugs = options['indicators'].split(',')
        indicatori = Indicatore.objects.filter(slug__in=indicators_slugs)

        voices_slugs = options['voices'].split(',')
        voices = Voce.objects.filter(slug__in=voices_slugs)
 
        indicatori_voci_year = {}

        self.logger.debug(" reading indicatori values")
        for i in indicatori: 
            # extracts indicator values for all locations
            iv = ValoreIndicatore.objects.filter(indicatore__slug=i.slug, anno=year).values('territorio__istat_id', 'territorio__slug', 'valore')
            for v in iv:
                t_id = v['territorio__istat_id']
                t_slug = v['territorio__slug']
                t_url = "{0}/bilanci/{1}?year={2}".format(site_url, t_slug, year)
                val = v['valore']
                if t_id not in indicatori_voci_year:
                    indicatori_voci_year[t_id] = { 'url': t_url, 'values': {}}
                indicatori_voci_year[t_id]['values'][i.id] = val


        self.logger.debug(" adding voci values")
        for vo in voices: 
            vv = ValoreBilancio.objects.filter(voce__slug=vo.slug, anno=year).values('territorio__istat_id', 'territorio__slug', 'valore')
            for v in vv:
                t_id = v['territorio__istat_id']
                t_slug = v['territorio__slug']
                t_url = "{0}/bilanci/{1}?year={2}".format(site_url, t_slug, year)
                val = v['valore']
                if t_id not in indicatori_voci_year:
                    indicatori_voci_year[t_id] = { 'url': t_url, 'values': {}}
                indicatori_voci_year[t_id]['values'][vo.id] = val

  
        self.logger.debug(" writing output to map_{0}.csv".format(self.year))
        with open("map_{0}.csv".format(self.year), 'wb') as csvfile:
            writer = csvkit.py2.CSVKitWriter(csvfile, delimiter=";")
            writer.writerow(["istat_id", "url"] + [i.denominazione for i in indicatori] + [vo.denominazione for vo in voices])
            for t_id, iv  in indicatori_voci_year.items():
                writer.writerow([t_id, iv['url']] + ["%.2f" % iv['values'][i.id] if i.id in iv['values'] else '0' for i in indicatori])
