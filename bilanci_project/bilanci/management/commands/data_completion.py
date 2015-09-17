# coding=utf-8

import logging
from optparse import make_option

from django.core.management import BaseCommand, call_command

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

        make_option('--dry-run',
                    dest='dryrun',
                    action='store_true',
                    default=False,
                    help='Set the dry-run command mode: nothing is written in the db'),

    )

    help = """
        Completes the import after couch2pg: calculates indicators, medians and update opendata (zip)
        """

    logger = logging.getLogger('management')


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

        ##
        # Update voci medians
        ##

        self.logger.info(u"Update indicators medians")
        call_command('median', verbosity=2, autocommit=True, years=options['years'], cities=options['cities'], type='voci',
                     interactive=False)

        ##
        # Compute Indicators
        ##
        self.logger.info(u"Compute indicators for selected Comuni")

        call_command('indicators', verbosity=2, autocommit=True, years=options['years'], cities=options['cities'], indicators='all',
                     interactive=False)

        ##
        # Update indicators medians
        ##

        self.logger.info(u"Update indicators medians")
        call_command('median', verbosity=2, autocommit=True, years=options['years'], cities=options['cities'], type='indicatori',
                     interactive=False)


        ##
        # Update opendata zip files
        ##

        self.logger.info(u"Update opendata zip files for selected Comuni")
        call_command('update_opendata', verbosity=2, autocommit=True, years=options['years'], cities=options['cities'], compress=True,
                     interactive=False)