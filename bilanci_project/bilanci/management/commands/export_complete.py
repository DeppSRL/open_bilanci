# coding=utf-8
import zipfile

__author__ = 'stefano'
import os
from collections import OrderedDict
from pprint import pprint
from bilanci.utils import unicode_csv

import csvkit
import logging
from itertools import groupby
from optparse import make_option
from django.conf import settings
from django.core.management import BaseCommand
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from bilanci.models import Voce, ValoreBilancio
from territori.models import Territorio, Contesto, Incarico

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
        # entrate
        'preventivo-entrate',
        'consuntivo-entrate-riscossioni-in-conto-competenza',
        'consuntivo-entrate-cassa',
        # spese
        'preventivo-spese-spese-somma-funzioni',
        'preventivo-spese-disavanzo-di-amministrazione',
        'preventivo-spese-prestiti',
        'preventivo-spese-spese-per-conto-terzi',
        'consuntivo-spese-cassa-spese-somma-funzioni',
        'consuntivo-spese-cassa-prestiti',
        'consuntivo-spese-cassa-spese-per-conto-terzi',
        'consuntivo-spese-pagamenti-in-conto-competenza-spese-per-conto-terzi',
        'consuntivo-spese-pagamenti-in-conto-competenza-prestiti',
        'consuntivo-spese-pagamenti-in-conto-competenza-spese-correnti',
        'consuntivo-spese-pagamenti-in-conto-competenza-spese-per-investimenti',
        'consuntivo-spese-pagamenti-in-conto-competenza-spese-correnti-interventi',
        'consuntivo-spese-pagamenti-in-conto-competenza-spese-per-investimenti-interventi'
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

        # gathers all the data with few queries
        self.logger.info("Gathering data...")
        voce_nodes = Voce.objects.filter(slug__in=self.node_slugs).order_by('slug')
        # get data for Comuni
        comuni = Territorio.objects.filter(territorio="C")
        comuni_values = comuni.values('slug', 'denominazione', 'regione', 'cluster', 'prov')
        comuni_dict = convert(comuni_values, 'slug')

        # get data for Comuni Valore bilancio
        valore_bilancio = ValoreBilancio.objects.filter(voce__in=voce_nodes, territorio__in=comuni,
                                                        anno__in=years). \
            values('valore', 'valore_procapite', 'anno', 'territorio__slug', 'voce__slug')
        vb_dict = convert(valore_bilancio, ('territorio__slug', 'voce__slug', 'anno'))

        # get data for CLUSTER Valore bilancio
        valore_bilancio_cluster = ValoreBilancio.objects.filter(voce__in=voce_nodes, territorio__territorio="L",
                                                                anno__in=years). \
            values('valore', 'valore_procapite', 'anno', 'territorio__cluster', 'voce__slug')
        vb_cluster_dict = convert(valore_bilancio_cluster, ('cluster', 'voce__slug', 'anno'))

        # get data for Comune context (abitanti)
        contexts = Contesto.objects.filter(territorio__in=comuni).values('anno', 'territorio__slug',
                                                                         'bil_popolazione_residente')
        contexts_dict = convert(contexts, ('territorio__slug', 'anno'))
        self.logger.info("Done")
        folder_path = 'data/export_complete/'
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        counter=0
        for node in voce_nodes:
            for voce in node.get_descendants(include_self=True):
                self.logger.info("Processing voce: {0}".format(voce))
                for anno in years:
                # get incarichi for yr
                    incarichi = Incarico.get_incarichi_fineanno(comuni, anno).values('territorio__slug', 'nome',
                                                                                     'cognome', 'party_name',
                                                                                     'party_acronym', 'tipologia')
                    incarichi_dict = convert(incarichi, 'territorio__slug')
                    # create csv file
                    filename = "{}/{}_{}.csv".format(folder_path, voce.slug, anno)
                    csv_file = open(filename, 'w')
                    csv_writer = unicode_csv.UnicodeWriter(csv_file, dialect=unicode_csv.excel_semicolon)
                    # write file header
                    csv_writer.writerow(
                        ['cluster', 'nome_comune', 'prov', 'regione', 'pop', 'valore', 'valore_pc', 'valore_cluster',
                         'valore_cluster_pc', 'nome', 'cognome', 'party_name', 'party_acronym', 'tipo_incarico',
                         'n_incarichi'])
                    empty_file = True
                    for comune in comuni:
                        try:
                            vb = vb_dict[(comune.slug, voce.slug, anno)][0]
                        except KeyError:
                            self.logger.debug(
                                u"Bilancio data for {},{},{} not found in DB".format(voce, anno, comune))
                            continue

                        # add comune context data
                        comune_data = comuni_dict[vb['territorio__slug']][0]
                        comune_data.pop('slug', None)
                        od = OrderedDict(sorted(comune_data.items(), key=lambda t: t[0]))
                        try:
                            od['pop'] = str(
                                contexts_dict[(vb['territorio__slug'], anno)][0]['bil_popolazione_residente'])
                        except KeyError:
                            self.logger.debug("Population not found for {},{}".format(vb['territorio__slug'], anno))
                            od['pop']='-'

                        # get value for comune
                        od['valore'] = str("%.2f" % vb['valore'])
                        od['valore_procapite'] = str("%.2f" % vb['valore_procapite'])
                        # get values for cluster
                        try:
                            vb_cluster = vb_cluster_dict[(comune.cluster, voce.slug, anno)][0]
                        except KeyError:
                            self.logger.debug(
                                u"Cluster data for {},{},{} not found in DB".format(voce, anno, comune.cluster))
                            od['valore_cluster'] = ''
                            od['valore_cluster_procapite'] = ''
                        else:
                            od['valore_cluster'] = str("%.2f" % vb_cluster['valore'])
                            od['valore_cluster_procapite'] = str("%.2f" % vb_cluster['valore_procapite'])

                        #  get incarichi data for comune (sindaco, vicesindaco, ecc) in charge at 31/12
                        incarichi_comune = []
                        try:
                            incarichi_comune = incarichi_dict[vb['territorio__slug']]
                        except KeyError:
                            self.logger.warning(u"Incarichi for {},{} not found in DB".format(anno, comune))

                            od['nome'] = ''
                            od['cognome'] = ''
                            od['party_name'] = ''
                            od['party_acronym'] = ''
                            od['tipologia'] = ''
                            od['n_incarichi'] = '0'
                        else:
                            incarico_to_write = incarichi_comune[0]
                            incarico_to_write.pop('territorio__slug', None)
                            od.update(incarico_to_write)
                            od['n_incarichi'] = str(len(incarichi_comune))

                        csv_writer.writerow(od.values())
                        empty_file = False

                    csv_file.close()
                    # exit()
                    if empty_file:
                        # delete the empty file
                        self.logger.warning(u"No data for {},{}!".format(voce.slug, anno))
                        os.remove(filename)
                    else:
                        counter+=1

        # create the zip file
        self.logger.info("Start creating zip file")
        zipfile_path = "data/export_complete"
        import shutil
        shutil.make_archive(zipfile_path, 'zip', folder_path)
        self.logger.info("Created zip file {}".format(zipfile_path))
