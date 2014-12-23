# -*- coding: utf-8 -*-
import csv
from itertools import chain
import logging
from datetime import datetime
import re
from unidecode import unidecode
from optparse import make_option
from django.core.management import BaseCommand
from django.conf import settings
from territori.models import Territorio, Incarico

__author__ = 'stefano'


def dump(qs, outfile_path):
    # """
    # Takes in a Django queryset and spits out a CSV file.
    #
    # Usage::
    #
    # 	>> from utils import dump2csv
    # 	>> from dummy_app.models import *
    # 	>> qs = DummyModel.objects.all()
    # 	>> dump2csv.dump(qs, './data/dump.csv')
    #
    # Based on a snippet by zbyte64::
    #
    # 	http://www.djangosnippets.org/snippets/790/
    #
    # """

    model = qs.model
    writer = csv.writer(open(outfile_path, 'w'))

    headers = []
    for field in model._meta.fields:
        headers.append(field.name)
    writer.writerow(headers)

    for obj in qs:
        row = []
        for field in headers:
            val = getattr(obj, field)
            if callable(val):
                val = val()
            if type(val) == unicode:
                val = val.encode("utf-8")
            row.append(val)
        writer.writerow(row)


class Command(BaseCommand):

    accepted_types = ['all', 'capoluoghi', 'others']

    option_list = BaseCommand.option_list + (

        make_option('--territori', '-t',
                    dest='territori',
                    action='store',
                    default='all',
                    help='Type of Territorio: ' + ' | '.join(accepted_types)),

        make_option('--output', '-o',
                    dest='output_file',
                    action='store',
                    default='',
                    help='Path to output file + filename', ),

        make_option('--dry-run',
                    dest='dryrun',
                    action='store_true',
                    default=False,
                    help='Set the dry-run command mode: nothing is written on db'),

    )

    help = 'Export political charges into csv file'
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

        dryrun = options['dryrun']
        territori_type = options['territori']
        output_file = options['output_file']

        if output_file == '':
            self.logger.error(u"Output file path is required")
            return

        self.logger.info(u"Start charges export with dryrun: {0}".format(dryrun))
        self.handle_export(territori_type, output_file, dryrun)
        self.logger.info(u"End import charges script")

    def handle_export(self, territori_type, output_file, dryrun):

        # prende tutte le citta' capoluogo di provincia
        capoluoghi_provincia = Territorio.objects.\
                                    filter(slug__in=settings.CAPOLUOGHI_PROVINCIA).\
                                    order_by('-cluster', 'denominazione')
        altri_territori = list(
            Territorio.objects.filter(territorio=Territorio.TERRITORIO.C).
            exclude(id__in=capoluoghi_provincia).
            order_by('-cluster', 'denominazione'))


        # depending on the territori_type value runs the import only for capoluoghi di provincia or for all Territori
        # prioritize the territori list getting first the capoluoghi di provincia and then all the rest

        if territori_type == 'capoluoghi':
            self.export_incarichi(capoluoghi_provincia, output_file, dryrun)

        if territori_type == 'others':
            self.export_incarichi(altri_territori, output_file, dryrun)

        if territori_type == 'all':
            all_territori = sorted(
                chain(capoluoghi_provincia, altri_territori, ),
                key=lambda instance: instance.denominazione)

            self.export_incarichi(all_territori, output_file, dryrun)

    def export_incarichi(self, territori_set, output_file, dryrun):

        # export to csv incarichi for territorio
        queryset = Incarico.objects.filter(territorio__in=territori_set).order_by('territorio__denominazione')
        dump(qs=queryset, outfile_path=output_file)




