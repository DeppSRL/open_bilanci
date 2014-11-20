"""
Gets parametri deficitari from Q50 from couchdb

"""
# coding=utf-8
from collections import OrderedDict
from itertools import groupby

import logging
import math
import numpy
from optparse import make_option

from django.core.management import BaseCommand

from territori.models import Territorio, ParametriDeficitari


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--years',
                    dest='years',
                    default='',
                    help='Years to fetch. From 2003 to 2013. Use one of this formats: 2013 or 2003-2006 or 2003,2004,2006'),

        make_option('--skip-existing',
                    dest='skip_existing',
                    action='store_true',
                    default=False,
                    help='Skip existing cities. Use to speed up long import of many cities, when errors occur'),
        make_option('--dry-run',
                    dest='dryrun',
                    action='store_true',
                    default=False,
                    help='Set the dry-run command mode: nothing is written in the db'),

    )

    help = """
        Import Parametri deficitari from couchdb
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
        # starting node slug
        ##

        slug = options['slug']

        ###
        # type
        ###
        values_type = options['type']
        if values_type not in ['voci', 'indicatori']:
            self.logger.error(u"Type parameter not accepted. Choose between 'voci' and 'indicatori'.")
            return

        ###
        # years
        ###
        years = options['years']
        if not years:
            self.logger.error(u"Missing years parameter")
            return

        if "-" in years:
            (start_year, end_year) = years.split("-")
            years = range(int(start_year), int(end_year) + 1)
        else:
            years = [int(y.strip()) for y in years.split(",") if 2001 < int(y.strip()) < 2014]

        if not years:
            self.logger.error(u"No suitable year found in {0}".format(years))
            return

        self.logger.info(u"Considering years: {0}".format(years))
        self.years = years

        ###
        # other options
        ###
        dryrun = options['dryrun']
        skip_existing = options['skip_existing']
