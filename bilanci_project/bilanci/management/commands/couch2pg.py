from collections import OrderedDict
import logging
import multiprocessing
from optparse import make_option
import os
from pprint import pprint
from os import listdir
from os.path import isfile, join
from django import db
from django.conf import settings
from django.core.management import BaseCommand, call_command
from django.utils.text import slugify
from bilanci import tree_models
from bilanci.models import Voce, ValoreBilancio, ImportXmlBilancio
from bilanci.utils import couch, gdocs, email_utils
from bilanci.utils.comuni import FLMapper
from territori.models import Territorio, ObjectDoesNotExist
from .somma_funzioni import SommaFunzioniMixin


def patch_somma_funzioni(city_year_budget_dict, certificati_to_import):
    """Patches city_year_budget_dict with sums for Spese correnti and Investimenti

    Args:
        city_year_budget_dict (dict): dictionary containing the budget from couch
        certificati_to_import (list): which type, preventivo, consuntivo or both
    """

    def somma_funzioni(cor_dict, inv_dict, somma_dict):
        """Internal function that sums the dictionary keys recursively

        Non-existing dictionary keys, are assigned default zero values

        Args:
            cor_dict (dict): spese correnti dict (first addendum)
            inv_dict (dict): investimenti dict (second addendum)
            somma_dict (dict): dict that will contain the sum
        """
        for k in cor_dict:
            # get values corresponding to the key or zero
            # if the key is not present in the dict
            cor = cor_dict.get(k, 0)
            inv = inv_dict.get(k, 0)
            if isinstance(cor, dict) and isinstance(inv, dict):
                somma_dict[unicode(k)] = {}
                somma_funzioni(cor, inv, somma_dict[unicode(k)])
            elif isinstance(cor, dict) or isinstance(inv, dict):
                print "WARNING Errore in somma funzioni: chiave {0}. Skipping".format(k)
                continue
            else:
                somma_dict[unicode(k)] = cor + inv


    if 'preventivo' in certificati_to_import:
        if 'preventivo' in city_year_budget_dict and \
                        'SPESE' in city_year_budget_dict['preventivo']:
            prev_spese_dict = city_year_budget_dict['preventivo']['SPESE']
            prev_spese_dict[u'Spese somma funzioni'] = {}

            somma_funzioni(
                prev_spese_dict['Spese correnti']['funzioni'],
                prev_spese_dict['Spese per investimenti']['funzioni'],
                prev_spese_dict[u'Spese somma funzioni']
            )

    if 'consuntivo' in certificati_to_import:
        if 'consuntivo' in city_year_budget_dict and \
                        'SPESE' in city_year_budget_dict['consuntivo'] and \
                        'Impegni' in city_year_budget_dict['consuntivo']['SPESE']:
            cons_spese_cassa_dict = city_year_budget_dict['consuntivo']['SPESE']['Impegni']
            cons_spese_cassa_dict[u'Spese somma funzioni'] = {}
            somma_funzioni(
                cons_spese_cassa_dict['Spese correnti']['funzioni'],
                cons_spese_cassa_dict['Spese per investimenti']['funzioni'],
                cons_spese_cassa_dict[u'Spese somma funzioni']
            )

        if 'consuntivo' in city_year_budget_dict and \
                        'SPESE' in city_year_budget_dict['consuntivo'] and \
                        'Cassa' in city_year_budget_dict['consuntivo']['SPESE']:
            cons_spese_impegni_dict = city_year_budget_dict['consuntivo']['SPESE']['Cassa']
            cons_spese_impegni_dict[u'Spese somma funzioni'] = {}
            somma_funzioni(
                cons_spese_impegni_dict['Spese correnti']['funzioni'],
                cons_spese_impegni_dict['Spese per investimenti']['funzioni'],
                cons_spese_impegni_dict[u'Spese somma funzioni']
            )


def map_tree(territorio, populations, city_budget, city_years, partial_import, tree_node_slug, couch_path, voci_dict):
    results = []
    city_finloc = territorio.cod_finloc
    for year, certificati_to_import in city_years.iteritems():
        if str(year) not in city_budget:
            # logger.warning(u" {} - {} not found. Skip".format(city_finloc, year))
            print "WARNING '{}' YEAR:{} not found".format(city_finloc, year)
            continue

        # POPULATION
        # fetch valid population, starting from this year
        # if no population found, set it to None, as not to break things
        population = populations.get(year, None)

        # build a BilancioItem tree, out of the couch-extracted dict
        # for the given city and year
        # add the totals by extracting them from the dict, or by computing
        city_year_budget_dict = city_budget[str(year)]

        # patch by adding Spese Somma Funzioni nodes, with subnodes,
        # summing Spese correnti and Spese per investimenti to a new
        # key within the budget dict
        patch_somma_funzioni(city_year_budget_dict, certificati_to_import)

        if partial_import is True:
            # start from a custom node
            path_not_found = False
            city_year_budget_node_dict = city_year_budget_dict.copy()

            # get the starting node in couchdb data
            for k in couch_path:
                try:
                    city_year_budget_node_dict = city_year_budget_node_dict[k]
                except KeyError:
                    print "couch path:{} not present for {}, anno:{}".format(couch_path, territorio.cod_finloc,
                                                                             str(year))
                    path_not_found = True
                    break

            # if data path is found in the couch document, write data into postgres db
            if not path_not_found:
                city_year_node_tree_patch = tree_models.make_tree_from_dict(
                    city_year_budget_node_dict, voci_dict, path=[tree_node_slug],
                    population=population
                )

                # writes new sub-tree
                results.append((territorio, year, city_year_node_tree_patch))
        else:
            # import tipo_bilancio considered
            # normally is preventivo and consuntivo
            # otherwise only one of them
            for tipo_bilancio in certificati_to_import:
                certificato_tree = tree_models.make_tree_from_dict(
                    city_year_budget_dict[tipo_bilancio], voci_dict, path=[unicode(tipo_bilancio)],
                    population=population
                )
                if len(certificato_tree.children) == 0:
                    continue
                results.append((territorio, year, certificato_tree))

    return results


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--dry-run',
                    dest='dryrun',
                    action='store_true',
                    default=False,
                    help='Set the dry-run command mode: nothing is written in the couchdb'),
        make_option('--complete',
                    dest='complete',
                    action='store_true',
                    default=False,
                    help='After data import calculate indicators and updates opendata zip file'),
        make_option('--years',
                    dest='years',
                    default='',
                    help='Years to fetch. From 2002 to 2012. Use one of this formats: 2012 or 2003-2006 or 2002,2004,2006'),
        make_option('--cities',
                    dest='cities',
                    default='',
                    help='Cities codes or slugs. Use comma to separate values: Roma,Napoli,Torino or  "All"'),
        make_option('--couchdb-server',
                    dest='couchdb_server',
                    default=settings.COUCHDB_DEFAULT_SERVER,
                    help='CouchDB server alias to connect to (staging | localhost). Defaults to staging.'),
        make_option('--create-tree',
                    dest='create_tree',
                    action='store_true',
                    default=False,
                    help='Force recreating simplified tree leaves from csv file or gdocs (remove all values)'),
        make_option('--force-google',
                    dest='force_google',
                    action='store_true',
                    default=False,
                    help='Force reloading mapping file and simplified subtrees leaves from gdocs (invalidate the csv cache)'),
        make_option('--tree-node-slug',
                    dest='tree_node_slug',
                    default=None,
                    help='Voce slug of the tree model to start the import from. Example: consuntivo-entrate-imposte-e-tasse'),
        make_option('--couch-path',
                    dest='couch_path_string',
                    default=None,
                    help='CouchDB keys sequence (CSV) to identify the import starting point. '
                         'Must be specified together with the treee-node-slug option. '
                         'Example: consuntivo,entrate,imposte'),
        make_option('--append',
                    dest='append',
                    action='store_true',
                    default=False,
                    help='Use the log file appending instead of overwriting (used when launching shell scripts)'),
    )

    help = 'Import values from the simplified couchdb database into a Postgresql server'
    dryrun = False
    logger = logging.getLogger('management')
    partial_import = False
    couch_path = None
    accepted_bilanci_types = ['preventivo', 'consuntivo']
    somma_funzioni_branches = [
        'preventivo-spese-spese-somma-funzioni',
        'consuntivo-spese-cassa-spese-somma-funzioni',
        'consuntivo-spese-impegni-spese-somma-funzioni',
    ]
    considered_tipo_bilancio = accepted_bilanci_types
    considered_somma_funzioni = somma_funzioni_branches

    #if the import is partial root_treenode is the root node of the sub-tree to be imported
    root_treenode = None
    root_descendants = None
    import_set = OrderedDict()
    imported_xml = None
    years = None
    cities_param = None
    cities = None
    cities_not_found = []
    voci_dict = None
    couchdb = None
    comuni_dicts = {}

    def create_voci_tree(self, force_google):
        """
        Create a Voci tree. If the tree exists, then it is deleted.
        """
        if Voce.objects.count() > 0:
            Voce.objects.all().delete()

        # get simplified leaves (from csv or gdocs), to build the voices tree
        simplified_leaves = gdocs.get_simplified_leaves(force_google=force_google)

        self.create_voci_preventivo_tree(simplified_leaves)

        self.create_voci_consuntivo_tree(simplified_leaves)

        sf = SommaFunzioniMixin()
        sf.create_somma_funzioni()

    def create_voci_preventivo_tree(self, simplified_leaves):

        # create preventivo root
        subtree_node = Voce(denominazione='Preventivo', slug='preventivo')
        subtree_node.insert_at(None, save=True, position='last-child')

        # the preventivo subsections
        subtrees = OrderedDict([
            ('preventivo-entrate', 'Preventivo entrate'),
            ('preventivo-spese', 'Preventivo spese'),
        ])

        # add all leaves from the preventivo sections under preventivo
        # entrate and spese are already considered
        for subtree_slug, subtree_denominazione in subtrees.items():

            for leaf_bc in simplified_leaves[subtree_slug]:
                # add this leaf to the subtree, adding all needed intermediate nodes
                self.add_leaf(leaf_bc, subtree_node)

    def create_voci_consuntivo_tree(self, simplified_leaves):
        # create consuntivo root
        subtree_node = Voce(denominazione='Consuntivo', slug='consuntivo')
        subtree_node.insert_at(None, save=True, position='last-child')

        subtrees = OrderedDict([
            ('consuntivo-entrate', {
                'denominazione': u'Consuntivo entrate',
                'sections': [u'Accertamenti', u'Riscossioni in conto competenza', u'Riscossioni in conto residui',
                             u'Cassa']
            }),
            ('consuntivo-spese', {
                'denominazione': u'Consuntivo spese',
                'sections': [u'Impegni', u'Pagamenti in conto competenza', u'Pagamenti in conto residui', u'Cassa']
            }),
        ])

        for subtree_slug, subtree_structure in subtrees.items():

            for section_name in subtree_structure['sections']:
                for leaf_bc in simplified_leaves[subtree_slug]:
                    bc = leaf_bc[:]
                    bc.insert(1, section_name)
                    self.add_leaf(bc, subtree_node, section_slug=slugify(section_name))

    def add_leaf(self, breadcrumbs, subtree_node, section_slug=''):
        """
        Add a leaf to the subtree, given the breadcrumbs list.
        Creates the needed nodes in the process.
        """
        self.logger.info(u"adding leaf {}".format(",".join(breadcrumbs)))

        # skip 'totale' leaves (as totals values are attached to non-leaf nodes)
        if 'totale' in [bc.lower() for bc in breadcrumbs]:
            self.logger.info(u"skipped leaf {}".format(",".join(breadcrumbs)))
            return

        # copy breadcrumbs and remove last elements if empty
        bc = breadcrumbs[:]
        while not bc[-1]:
            bc.pop()

        prefix_slug = subtree_node.slug

        current_node = subtree_node
        for item in bc:
            if current_node.get_children().filter(denominazione__iexact=item).count() == 0:

                slug = u"{0}-{1}".format(prefix_slug, u"-".join(slugify(unicode(i)) for i in bc[0:bc.index(item) + 1]))
                node = Voce(denominazione=item, slug=slug)
                node.insert_at(current_node, save=True, position='last-child')
                if bc[-1] == item:
                    return
            else:
                node = current_node.get_children().get(denominazione__iexact=item)

            current_node = node

    def couch_connect(self, couchdb_server):
        # connect to couch database
        couchdb_server_alias = couchdb_server
        couchdb_dbname = settings.COUCHDB_SIMPLIFIED_NAME

        if couchdb_server_alias not in settings.COUCHDB_SERVERS:
            raise Exception("Unknown couchdb server alias.")

        self.couchdb = couch.connect(
            couchdb_dbname,
            couchdb_server_settings=settings.COUCHDB_SERVERS[couchdb_server_alias]
        )

    def set_years(self, years):
        # set considered years considering cases with - and ,
        # Example
        # 2003-2006
        # or 2003,2004,2010

        if not years:
            raise Exception("Missing years parameter")

        if "-" in years:
            (start_year, end_year) = years.split("-")
            years_list = range(int(start_year), int(end_year) + 1)
        else:
            years_list = [int(y.strip()) for y in years.split(",") if
                          settings.APP_START_YEAR <= int(y.strip()) <= settings.APP_END_YEAR]

        if not years_list:
            raise Exception("No suitable year found in {0}".format(years))

        self.years = years_list

    def set_cities(self, cities_codes):
        # set considered cities
        mapper = FLMapper()

        if not cities_codes:
            raise Exception("Missing cities parameter or start-from parameter")

        else:
            cities_finloc = mapper.get_cities(cities_codes, logger=self.logger)

        finloc_numbers = [c[-10:] for c in cities_finloc]

        territorio_finlocs = {t['cod_finloc'][-10:]: t['slug'] for t in
                              Territorio.objects.filter(territorio="C").order_by('slug').values('cod_finloc', 'slug')}

        slug_list = []
        for numb in finloc_numbers:
            if numb == "ICE_COMUNE":
                continue
            if numb in territorio_finlocs.keys():
                slug_list.append(territorio_finlocs[numb])
            else:
                self.logger.warning(u"City with codfinloc:'{}' not found in Postgres DB, skip".format(numb))
                self.cities_not_found.append(numb)

        self.cities = Territorio.objects.filter(territorio="C", slug__in=slug_list)


    def checks_partial_import(self, tree_node_slug, couch_path_string):
        # based on the type of import set the type of bilancio that is considered
        # sets branches of somma funzioni considered by the import

        self.partial_import = True

        #depending on tree node slug, couch path string sets considered tipo bilancio
        self.couch_path = [unicode(x) for x in couch_path_string.split(",")]

        # check that tree_node_slug exists in the Voce tree
        try:
            self.root_treenode = Voce.objects.get(slug=tree_node_slug)
        except ObjectDoesNotExist:
            self.logger.error(
                "Voce with slug:{0} not present in Voce table. "
                "Run update_bilancio_tree before running couch2pg".format(
                    tree_node_slug))
            exit()

        self.root_descendants = self.root_treenode.get_descendants(include_self=True)

        self.considered_tipo_bilancio = self.root_treenode. \
            get_ancestors(include_self=True, ascending=False). \
            get(slug__in=self.accepted_bilanci_types).slug

        # checks which branches of somma-funzioni are interested by the import
        self.considered_somma_funzioni = self.root_descendants. \
            filter(slug__in=self.somma_funzioni_branches). \
            values_list('slug', flat=True)

    def prepare_for_import(self):
        ##
        # prepare_for_import
        # 1) creates the import_set: the complete dict of cities, years and tipo bilancio that will be imported by the
        #    task
        # 2) creates values_to_delete: a queryset that includes all ValoriBilancio
        #    that correspond to the bilancio selected by the import
        # 3) gets the info about Xml import and removes the keys relative to cities, years and tipo_bilancio
        #    that have been imported via Xml
        # 4) excludes from values_to_delete the values of bilancio imported via XML: they won't be deleted
        # 5) fills somma_funzioni_slug_baseset with a dict that associates the slug of the root node of a
        #    somma-funzioni branch with the set of slugs needed to create it

        # creates a dict with year as a key and value: a list of considered_bilancio_type(s)
        years_dict = OrderedDict((year, self.considered_tipo_bilancio) for year in self.years)

        # creates a dict in which for each city considered the value is the previous dict
        self.import_set = OrderedDict((territorio, years_dict) for territorio in self.cities)

        # construct values_to_delete
        values_to_delete = ValoreBilancio.objects.filter(territorio__in=self.cities, anno__in=self.years)
        if self.partial_import:
            values_to_delete = values_to_delete.filter(voce__in=self.root_descendants)

        # get data about ImportXml: if there is data that has been imported from XML for a city/ year
        # then the couch import must NOT overwrite that data
        self.imported_xml = ImportXmlBilancio.objects. \
            filter(territorio__in=self.cities, anno__in=self.years, tipologia__in=self.considered_tipo_bilancio). \
            order_by('territorio', 'anno')

        if len(self.imported_xml) > 0:
            for i in self.imported_xml:
                self.logger.warning(
                    "BILANCIO:{} YEAR:{} CITY:{} will have to be reimported again: it was imported with xml". \
                        format(i.tipologia.title(), i.anno, i.territorio.denominazione))

        # deletes ValoriBilanci that will be imported afterwards: this speeds up the import
        if self.partial_import:
            self.logger.info("Deleting values for selected cities, years and subtree")
        else:
            self.logger.info("Deleting values for selected cities, years")

        if not self.dryrun and ValoreBilancio.objects.all().count() > 0:
            if self.partial_import is False and self.cities_param.lower() == 'all':
                # sql query to delete all values in ValoreBilancio table: this should cut the time
                cursor = db.connection.cursor()
                cursor.execute("TRUNCATE bilanci_valorebilancio", )

            else:
                values_to_delete.delete()

        self.logger.info("Done deleting")


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

        self.dryrun = options['dryrun']
        complete = options['complete']
        force_google = options['force_google']
        create_tree = options['create_tree']

        tree_node_slug = options['tree_node_slug']
        couch_path_string = options['couch_path_string']

        if tree_node_slug and couch_path_string is None or couch_path_string and tree_node_slug is None:
            self.logger.error("Couch path and tree node must be both specified. Quitting")
            exit()

        if options['append'] is True:
            self.logger = logging.getLogger('management_append')

        ###
        # connect to couchdb
        ###
        self.couch_connect(options['couchdb_server'])

        ###
        # cities
        ###
        self.cities_param = options['cities']

        self.set_cities(self.cities_param)

        if len(self.cities) == 0:
            self.logger.info("No cities to process. Quit")
            return

        # check if debug is active: the task may fail
        if settings.DEBUG is True and settings.INSTANCE_TYPE != 'development' and len(self.cities) > 4000:
            self.logger.error("DEBUG settings is True, task will fail. Disable DEBUG and retry")
            exit()

        ###
        # set considered years
        ###
        self.set_years(options['years'])

        # if it's a partial import
        # * checks which kind of bilancio is considered
        # * checks which branch of somma-funzioni has to be calculated

        if tree_node_slug and couch_path_string:
            tree_node_slug = unicode(tree_node_slug)
            couch_path_string = unicode(couch_path_string)
            self.checks_partial_import(tree_node_slug, couch_path_string)

        # create the tree if it does not exist or if forced to do so
        if create_tree or Voce.objects.count() == 0:
            if not self.dryrun:
                self.create_voci_tree(force_google=force_google)

        # build the map of slug to pk for the Voce tree
        self.voci_dict = Voce.objects.get_dict_by_slug()

        # considering years,cities and limitations set creates a comprehensive map of all bilancio to be imported,
        # deletes old values before import
        self.prepare_for_import()
        # multiprocessing basics
        params = []
        pool = multiprocessing.Pool()
        self.logger.info("Start import")
        for territorio, city_years in self.import_set.iteritems():
            populations = {year: territorio.nearest_valid_population(year)[1] for year, budgets in city_years.iteritems()}
            city_finloc = territorio.cod_finloc
            # get all budgets data for the city
            city_budget = self.couchdb.get(city_finloc)
            # self.logger.info("Execution time for couch get: %.2gs seconds" % (time.clock()-start_time))

            if city_budget is None:
                # if city budget is not found, try again taking out apostrophe and re-slugging, this deals with
                # slug name changes from finanza locale
                if "'" in territorio.nome:
                    nome_senza_apostrofo = territorio.nome.replace("'", "")
                    finloc_number = city_finloc[-10:]
                    city_finloc_noapostrophe = u"{}--{}".format(slugify(nome_senza_apostrofo), finloc_number).upper()
                    city_budget = self.couchdb.get(city_finloc_noapostrophe)

                    if city_budget is None:
                        self.logger.warning(
                            u"Document '{}' or '{}' not found in couchdb instance. Skipping.".format(city_finloc,
                                                                                                     city_finloc_noapostrophe))
                        continue

                else:
                    self.logger.warning(u"Document '{}' not found in couchdb instance. Skipping.".format(city_finloc))
                    continue

            self.logger.debug(u"City of {0}".format(city_finloc))
            # map the Couch document tree into memory struct that will be written on Postgres DB later
            params.append((
                territorio, populations, city_budget, city_years, self.partial_import, tree_node_slug, self.couch_path,
                self.voci_dict))

            if len(params) == 100:
                self.logger.info(u"Reached city of '{0}', continuing...".format(city_finloc))
                maptree_results = [pool.apply_async(map_tree, p) for p in params]
                params = []

                for mtr in maptree_results:
                    results = mtr.get()
                    for result in results:
                        (territorio, year, certificato_tree) = result

                        if self.dryrun is False:
                            tree_models.write_tree_to_vb_db(territorio, year, certificato_tree, self.voci_dict)

                if self.dryrun is False:
                    tree_models.flush_values_to_vb()

        self.logger.info("Done importing couchDB values into postgres")

        if self.cities_param.lower() != 'all':
            for bilancio_xml in self.imported_xml:
                self.logger.info(
                    "IMPORTANT: Re-import XML bilancio {},{},{}".format(bilancio_xml.territorio, bilancio_xml.anno,
                                                                        bilancio_xml.tipologia))
        else:
            # directly import xml files in default folder for bilancio XML
            xml_path = settings.OPENDATA_XML_ROOT

            # if the folder doesnt exist, create the folder
            if not os.path.exists(xml_path):
                self.logger.error("XML folder {} not found! Created now".format(xml_path))
                os.makedirs(xml_path)

            xml_files = [f for f in listdir(xml_path) if isfile(join(xml_path, f))]
            for f in xml_files:
                self.logger.info(u"Import XML bilancio file:'{}'".format(f))
                call_command('xml2pg', verbosity=1, file=f, interactive=False)

            if len(xml_files) != len(self.imported_xml):
                self.logger.error(
                    "Found {} Xml files compared to {} objs in ImportXML table in DB!!".format(len(xml_files),
                                                                                               len(self.imported_xml)))
        if len(self.cities_not_found) > 0:
            self.logger.warning(
                "Following COD FINLOC NOT FOUND and not imported:{}".format(",".join(self.cities_not_found)))

        if complete and not self.dryrun and not self.partial_import:

            ##
            # complete the import with medians, indicators and update opendata (zip files)
            ##

            self.logger.info(u"Update indicators medians")
            call_command('data_completion', verbosity=2, years=options['years'], cities=options['cities'],
                         interactive=False)

            email_utils.send_notification_email(
                msg_string="Couch2pg, update opendata, indicators and medians has finished.")

        else:
            email_utils.send_notification_email(msg_string="Couch2pg has finished.")