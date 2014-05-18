# coding=utf-8
import logging
from optparse import make_option
from django.core.management import BaseCommand
from django.db import transaction
from bilanci.utils import UnicodeDictReader
from idioticon.models import Term


class DryRunExecution(Exception):
    pass


class Command(BaseCommand):

    couchdb = None
    logger = logging.getLogger('management')
    comuni_dicts = {}

    option_list = BaseCommand.option_list + (
        make_option('--dry-run',
                    dest='dryrun',
                    action='store_true',
                    default=False,
                    help='Set the dry-run command mode: nothing is written in the db'),
    )

    help = """
        Import terms into idioticon.
        """


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

        filename = args[0]
        reader = UnicodeDictReader(open(filename, 'r'))

        try:
            with transaction.atomic():
                for row in reader:
                    term, created = Term.objects.get_or_create(
                        slug=row['Slug'],
                        defaults=dict(
                            term=row['Slug'],
                            popover_title=row['Titolo'],
                            definition=row['Descrizione']
                        )
                    )
                    if created:
                        self.logger.info('Created: %s' % term)
                if options['dryrun']:
                    raise DryRunExecution()
        except DryRunExecution:
            pass