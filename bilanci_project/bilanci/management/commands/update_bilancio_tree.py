# coding=utf-8
__author__ = 'stefano'
import logging
from optparse import make_option
import csv
from bilanci import utils
from django.conf import settings
from django.core.management import BaseCommand
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from bilanci.models import Voce


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (

        make_option('--file',
                    dest='filepath',
                    default='',
                    help="""
                        Bilancio tree structure csv file
                        """),

        make_option('--delete',
                    dest='delete',
                    action='store_true',
                    default=False,
                    help='Deletes the Voce specified in the file'),

        make_option('--dry-run',
                    dest='dryrun',
                    action='store_true',
                    default=False,
                    help='Set the dry-run command mode: nothing is written in the db'),

    )

    help = """
        Updates Bilancio Voce table to structure defined in the input csv file
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
        delete = options['delete']

        # read input csv

        filepath = options['filepath']
        self.logger.info("Opening input file {0}".format(filepath))
        csv_file = open(filepath, "r")
        udr = utils.UnicodeDictReader(csv_file, dialect=csv.excel, encoding="utf-8")

        c_new_nodes = 0
        c_not_created = 0
        for row in udr:

            # for each row get the parent node, if exists
            # adds the new node in the tree

            parent_node = None
            try:
                parent_node = Voce.objects.get(slug=row['slug_parent'])
            except ObjectDoesNotExist:
                self.logger.error(u"Cannot find Voce with slug {0} as parent node for {1}".format(
                    row['slug_parent'],row['slug']
                ))

            # update tree based on csv data

            if not delete:
                if not dryrun:
                    new_node, created = Voce.objects.get_or_create(slug=row['slug'], parent = parent_node, defaults={'denominazione': row['denominazione']})

                    if created:
                        self.logger.info(u"Created new node with slug {0}".format(row['slug']))
                        c_new_nodes+=1
                    else:
                        self.logger.info(u"Node with slug {0} already exists".format(row['slug']))
                        c_not_created+=1
            else:

                try:
                    voce = Voce.objects.get(slug = row['slug'], parent = parent_node, denominazione = row['denominazione'])
                except ObjectDoesNotExist:
                    self.logger.error(u"Node with slug {0} doesn't exist".format(row['slug']))
                else:
                    self.logger.info(u"Deleted node with slug {0}".format(row['slug']))
                    voce.delete()


        if not delete:
            self.logger.info(u"Updated tree correctly: {0} nodes created, {1} nodes already existed".format(c_new_nodes,c_not_created))


        # Corrects branches with name "Istruzione " => "Istruzione"
        self.logger.info(u"Updated tree branches with name 'Istruzione ' to 'Istruzione'")
        if not dryrun:
            Voce.objects.filter(denominazione="Istruzione ").update(denominazione='Istruzione')
        
        return