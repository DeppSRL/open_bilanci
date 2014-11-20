__author__ = 'stefano'
import logging
from optparse import make_option
from bilanci import utils
from django.conf import settings
from django.core.management import BaseCommand
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from bilanci.models import Voce

class Command(BaseCommand):

    option_list = BaseCommand.option_list + (

        make_option('--dry-run',
                    dest='dryrun',
                    action='store_true',
                    default=False,
                    help='Set the dry-run command mode: nothing is changed in the db'),

    )

    help = """
        Bilancio Voce: updates spese-prestiti objects denominazione from 'Prestiti' to 'Rimborso prestiti'
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

        dryrun = options['dryrun']

        if not dryrun:
            Voce.objects.filter(denominazione='Prestiti', slug__contains='spese').update(denominazione='Rimborso prestiti')

        self.logger.info(u"Update done")
