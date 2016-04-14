# coding=utf-8
__author__ = 'stefano'
import zipfile
import csvkit
import shutil
import os
import logging
from collections import OrderedDict
from pprint import pprint
from bilanci.utils import unicode_csv
from itertools import groupby
from optparse import make_option
from django.core.management import BaseCommand
from bilanci.models import Voce, ValoreBilancio, Indicatore, ValoreIndicatore
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
import pdb
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
        make_option('--zip_filename',
                    dest='zip_filename',
                    default='complete',
                    help='Name of the file to be produced. Defaults to "complete". Zip extension is added automatically.'),
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

    def export_voci_bilancio(self, folder_path):

        for voce in self.voce_nodes:
                self.logger.info("Processing voce: {0}".format(voce))
                for anno in self.years:
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
                    for comune in self.comuni:
                        try:
                            vb = self.vb_dict[(comune.slug, voce.slug, anno)][0]
                        except KeyError:
                            self.logger.debug(
                                u"Bilancio data for {},{},{} not found in DB".format(voce, anno, comune))
                            continue

                        # add comune context data
                        comune_data = self.comuni_dict[vb['territorio__slug']][0]
                        comune_data.pop('slug', None)
                        od = OrderedDict(sorted(comune_data.items(), key=lambda t: t[0]))
                        try:
                            od['pop'] = str(
                                self.contexts_dict[(vb['territorio__slug'], anno)][0]['bil_popolazione_residente'])
                        except KeyError:
                            self.logger.debug("Population not found for {},{}".format(vb['territorio__slug'], anno))
                            od['pop']='-'

                        # get value for comune
                        od['valore'] = str("%.2f" % vb['valore'])
                        od['valore_procapite'] = str("%.2f" % vb['valore_procapite'])
                        # get values for cluster
                        try:
                            vb_cluster = self.vb_cluster_dict[(comune.cluster, voce.slug, anno)][0]
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
                            incarichi_comune = self.incarichi_dict[anno][vb['territorio__slug']]
                        except KeyError:
                            self.logger.debug(u"Incarichi for {},{} not found in DB".format(anno, comune))

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
                    if empty_file:
                        # delete the empty file
                        self.logger.warning(u"No data for {},{}!".format(voce.slug, anno))
                        os.remove(filename)

    def export_indicatori(self, folder_path):

        for ind in Indicatore.objects.all():
            self.logger.info("Processing ind: {0}".format(ind.slug))
            for anno in self.years:
                # create csv file

                filename = "{}/{}_{}.csv".format(folder_path, ind.slug, anno)
                csv_file = open(filename, 'w')
                csv_writer = unicode_csv.UnicodeWriter(csv_file, dialect=unicode_csv.excel_semicolon)
                # write file header
                csv_writer.writerow(
                    ['cluster', 'nome_comune', 'prov', 'regione', 'pop', 'valore', 'valore_cluster', 'nome', 'cognome', 'party_name', 'party_acronym', 'tipo_incarico',
                     'n_incarichi'])
                empty_file = True
                for comune in self.comuni:
                    try:
                        vi = self.ind_dict[(comune.slug, ind.slug, anno)][0]
                    except KeyError:
                        self.logger.debug(
                            u"Indicator data for {},{},{} not found in DB".format(ind.slug, anno, comune))
                        continue

                    # add comune context data
                    comune_data = self.comuni_dict[vi['territorio__slug']][0]
                    comune_data.pop('slug', None)
                    od = OrderedDict(sorted(comune_data.items(), key=lambda t: t[0]))
                    try:
                        od['pop'] = str(
                            self.contexts_dict[(vi['territorio__slug'], anno)][0]['bil_popolazione_residente'])
                    except KeyError:
                        self.logger.debug("Population not found for {},{}".format(vi['territorio__slug'], anno))
                        od['pop']='-'

                    # get value for comune
                    od['valore'] = str("%.2f" % vi['valore'])
                    # get values for cluster
                    try:
                        vb_cluster = self.ind_cluster_dict[(comune.cluster, ind.slug, anno)][0]
                    except KeyError:
                        self.logger.debug(
                            u"Cluster data for {},{},{} not found in DB".format(ind.slug, anno, comune.cluster))
                        od['valore_cluster'] = ''
                    else:
                        od['valore_cluster'] = str("%.2f" % vb_cluster['valore'])

                    #  get incarichi data for comune (sindaco, vicesindaco, ecc) in charge at 31/12
                    incarichi_comune = []
                    try:
                        incarichi_comune = self.incarichi_dict[anno][vi['territorio__slug']]
                    except KeyError:
                        self.logger.debug(u"Incarichi for {},{} not found in DB".format(anno, comune))

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
                if empty_file:
                    # delete the empty file
                    self.logger.warning(u"No data for {},{}!".format(ind.slug, anno))
                    os.remove(filename)

    def gather_data(self):
        self.logger.info("- fetch voci")
        self.voce_nodes = []
        for node in Voce.objects.filter(slug__in=self.node_slugs).order_by('slug'):
            self.voce_nodes.append(node)

        # get data for Comunia
        self.logger.info("- fetch comuni")
        self.comuni = Territorio.objects.filter(territorio="C")
        comuni_values = self.comuni.values('slug', 'denominazione', 'regione', 'cluster', 'prov')
        self.comuni_dict = convert(comuni_values, 'slug')

        # get data for Valore bilancio
        self.logger.info("- fetch valori")
        valore_bilancio = ValoreBilancio.objects.filter(
            voce__in=self.voce_nodes, 
            territorio__in=self.comuni,
            anno__in=self.years
        ).order_by('territorio__slug', 'voce__slug', 'anno').\
          values('valore', 'valore_procapite', 'anno', 'territorio__slug', 'voce__slug')
        self.vb_dict = convert(valore_bilancio, ('territorio__slug', 'voce__slug', 'anno'))

        # get data for CLUSTER Valore bilancio
        self.logger.info("- fetch valori for clusters")
        valore_bilancio_cluster = ValoreBilancio.objects.filter(
            voce__in=self.voce_nodes, 
            territorio__territorio="L",
            anno__in=self.years
        ).order_by('territorio__cluster', 'voce__slug', 'anno')\
         .values('valore', 'valore_procapite', 'anno', 'territorio__cluster', 'voce__slug')
        self.vb_cluster_dict = convert(valore_bilancio_cluster, ('territorio__cluster', 'voce__slug', 'anno'))

        # get data for Comune context (abitanti)
        self.logger.info("- fetch contesti")
        contexts = Contesto.objects.filter(territorio__in=self.comuni)\
        .order_by('territorio__slug', 'anno')\
        .values('anno', 'territorio__slug','bil_popolazione_residente')
        self.contexts_dict = convert(contexts, ('territorio__slug', 'anno'))

        # get data indicatori
        self.logger.info("- fetch indicatori")
        valore_ind = ValoreIndicatore.objects.filter(
            territorio__in=self.comuni, anno__in=self.years
        ).order_by('indicatore__slug', 'territorio__slug','anno')\
         .values('valore', 'indicatore__slug', 'territorio__slug','anno')
        self.ind_dict = convert(valore_ind, ('territorio__slug','indicatore__slug', 'anno'))

        # get data for CLUSTER Indicatori
        self.logger.info("- fetch indicatori for clusters")
        valore_bilancio_cluster = ValoreIndicatore.objects.filter(
            territorio__territorio="L", 
            anno__in=self.years
        ).order_by('territorio__cluster', 'indicatore__slug', 'anno')\
         .values('valore', 'anno', 'territorio__cluster', 'indicatore__slug')
        self.ind_cluster_dict = convert(valore_bilancio_cluster, ('territorio__cluster', 'indicatore__slug', 'anno'))

        # get incarichi sindaci
        self.incarichi_dict = {}
        for anno in self.years:  
            incarichi = Incarico.get_incarichi_fineanno(self.comuni, anno)\
                .values('territorio__slug', 'nome',
	                'cognome', 'party_name',
			'party_acronym', 'tipologia')
            self.incarichi_dict[anno] = convert(incarichi, 'territorio__slug')


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

        self.years=years

        self.zip_filename = options['zip_filename']

        # gathers all the data with few queries
        self.logger.info("Gathering data...")
        self.gather_data()
        self.logger.info("Data fetched")

        folder_path = 'data/export_complete/'
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        # export voci bilancio
        self.logger.info("exporting voci")
        self.export_voci_bilancio(folder_path)

        #         export indicatori
        self.logger.info("exporting indicatori")
        self.export_indicatori(folder_path)

        #         create zip file
        self.logger.info("Start creating zip file")

        shutil.make_archive("data/{0}".format(self.zip_filename), 'zip', folder_path)
        self.logger.info("Created zip file {}".format(self.zip_filename))
        shutil.rmtree(folder_path)
