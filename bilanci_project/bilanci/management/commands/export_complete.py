# coding=utf-8
import os
from pprint import pprint
from bilanci.utils import unicode_csv

__author__ = 'stefano'

import csvkit
import logging
from itertools import groupby
from optparse import make_option
from django.conf import settings
from django.core.management import BaseCommand
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from bilanci.models import Voce, ValoreBilancio
from territori.models import Territorio,Contesto,Incarico

##
# extract values for selected Voce, all published indicators and creates a zip file for massive download.
# the selected voce are the following
#
# Vengono estratte le stessi voci per preventivo e consuntivo (cassa e competenza), in particolare:
# - entrate: tutte
# - spese-funzioni: tutte
# - spese-interventi (solo i nodi e le voci seguenti):
# - spese-interventi-spese correnti
# - spese-interventi-spese correnti-personale
# - spese-interventi-spese correnti-interessi passivi e oneri finanziari diversi
# - spese-interventi-spese per investimenti
# - spese-interventi-spese per investimenti-connessioni di crediti e anticipazioni
##

# converts a qset into a dict using the key field
def convert(queryset, key_field):
    if type(key_field) == tuple or type(key_field) == list:
        if len(key_field) == 0:
            raise Exception
        else:
            indice_keygen = lambda x: tuple(x[key] for key in key_field)

    else:
        indice_keygen = lambda x: x[key_field]

    return dict((k, list(v)) for k, v in groupby(queryset, key=indice_keygen))



class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--years',
                    dest='years',
                    default='',
                    help='Years to fetch. From 2002 to 2012. Use one of this formats: 2012 or 2003-2006 or 2002,2004,2006'),
    )

    help = """
        extract values for selected Voce, all published indicators and creates a zip file for massive download
        """

    logger = logging.getLogger('management')
    comuni_dicts = {}
    node_slugs = [
        'preventivo-entrate',
        'consuntivo-entrate-riscossioni-in-conto-competenza',
        'consuntivo-entrate-cassa',
    ]


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
        # years
        ###
        years = options['years']
        if not years:
            raise Exception("Missing years parameter")

        if "-" in years:
            (start_year, end_year) = years.split("-")
            years = range(int(start_year), int(end_year) + 1)
        else:
            years = [int(y.strip()) for y in years.split(",") if 2001 < int(y.strip()) < 2020]

        if not years:
            raise Exception("No suitable year found in {0}".format(years))

        self.years = years
        # gathers all the data with few queries
        self.logger.info("Gathering data...")
        voce_nodes = Voce.objects.filter(slug__in=self.node_slugs).order_by('slug')
        comuni = Territorio.objects.filter(territorio="C").order_by('slug')
        valore_bilancio = ValoreBilancio.objects.filter(voce__in=voce_nodes, territorio__in=comuni, anno__in=self.years).values('valore','valore_procapite','anno','territorio__slug','voce__slug')
        vb_dict = convert(valore_bilancio,('territorio__slug','voce__slug','anno'))
        contexts = Contesto.objects.filter(territorio__in=comuni).values('anno','territorio__slug','bil_popolazione_residente')
        contexts_dict = convert(contexts,('territorio__slug','anno'))
        self.logger.info("Done")
        folder_path = 'data/export_complete_temp/'
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        for node in voce_nodes:
            for voce in node.get_descendants(include_self=True):
                self.logger.info("Processing voce: {0}".format(voce))
                for anno in years:
                     # create csv file
                    filename="{}/{}_{}.csv".format(folder_path, voce.slug,anno)
                    csv_file = open(filename, 'w')
                    csv_writer = unicode_csv.UnicodeWriter(csv_file, dialect=unicode_csv.excel_semicolon)
                    empty_file = True
                    for comune in comuni:
                        try:
                            vb = vb_dict[(comune.slug,voce.slug,anno)]
                        except KeyError:
                            self.logger.debug(u"Data for {},{},{} not found in DB".format(voce,anno,comune))
                        else:
                            vb=vb[0]
                            vb['valore']=str("%.2f" % vb['valore'])
                            vb['valore_procapite']=str("%.2f" % vb['valore_procapite'])
                            csv_writer.writerow([vb['territorio__slug'], vb['valore'], vb['valore_procapite']])
                            empty_file=False

                    csv_file.close()
                    if empty_file:
                        # delete the empty file
                        os.remove(filename)