# coding=utf-8
import logging
from optparse import make_option
from django.core.exceptions import ObjectDoesNotExist
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
                    original_slug = row['slug old']
                    linked_slugs = (row[k] for k in [
                        'slug consuntivo competenza', 'slug consuntivo cassa', 'slug preventivo',
                        'slug preventivo spese correnti',
                        'slug consuntivo competenza impegni spese correnti',
                        'slug consuntivo cassa spese correnti'
                    ])
                    title = row['titolo']
                    definition = row['descrizione']

                    original_term, created = Term.objects.get_or_create(
                        slug=original_slug,
                        defaults=dict(
                            term=original_slug,
                            popover_title=title,
                            definition=definition
                        )
                    )
                    if created:
                        self.logger.info('Created: %s' % original_slug)
                    else:
                        original_term.popover_title = title
                        original_term.definition = definition
                        original_term.save() #auto-save term as slug

                    for linked_slug in linked_slugs:
                        if linked_slug:
                            try:
                                linked_term = Term.objects.get(slug=linked_slug)
                                original_term.linked_terms.add(linked_term)
                                self.logger.info('  existing term: %s added to linked_terms' % linked_slug)
                            except ObjectDoesNotExist:
                                original_term.linked_terms.create(
                                    slug=linked_slug,
                                    term=linked_slug
                                )
                                self.logger.info('  non-existing term: %s added to linked_terms' % linked_slug)


                if options['dryrun']:
                    raise DryRunExecution()
        except DryRunExecution:
            pass