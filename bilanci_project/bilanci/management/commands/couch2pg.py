from collections import OrderedDict
import logging
from optparse import make_option
from pprint import pprint
from django.conf import settings
from django.core.management import BaseCommand, call_command
from django.db.transaction import set_autocommit, commit
from django.utils.text import slugify
from bilanci import tree_models
from bilanci.models import Voce, ValoreBilancio, ImportXmlBilancio
from bilanci.utils import couch, gdocs, email_utils
from bilanci.utils.comuni import FLMapper
from territori.models import Territorio, ObjectDoesNotExist
from .somma_funzioni import SommaFunzioniMixin


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
        make_option('--start-from',
                    dest='start_from',
                    default='',
                    help='Start importing cities from such city. Use codfinloc: GARAGUSO--4170470090'),
        make_option('--couchdb-server',
                    dest='couchdb_server',
                    default=settings.COUCHDB_DEFAULT_SERVER,
                    help='CouchDB server alias to connect to (staging | localhost). Defaults to staging.'),
        make_option('--skip-existing',
                    dest='skip_existing',
                    action='store_true',
                    default=False,
                    help='Skip existing cities. Use to speed up long import of many cities, when errors occur'),
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
    # somma_funzioni_slug_baseset: dict that stores the slugs needed to compute somma funzioni branches
    somma_funzioni_slug_baseset = {}

    #if the import is partial root_treenode is the root node of the sub-tree to be imported
    root_treenode = None
    root_descendants = None
    import_set = OrderedDict()
    years = None
    cities_finloc = None
    skip_existing = None
    voci_dict = None
    couchdb = None
    comuni_dicts = {}

    def apply_somma_funzioni_patch(self, voce_sum, vb_filters, vb_dict):
        """
        Compute spese correnti and spese per investimenti for funzioni, and write into spese-somma

        Overwrite values if found.
        """

        components = voce_sum.get_components_somma_funzioni()
        self.logger.debug("Applying somma_funzioni_patch to {0}".format(voce_sum.slug))

        vb = []
        for c in components:
            try:
                vb.append(vb_dict[c.slug])
            except KeyError:
                self.logger.error("Somma funz: cannot find slug: {} in vb_dict".format(c.slug))
                return

        valore = vb[0]['valore'] + vb[1]['valore']
        valore_procapite = vb[0]['valore_procapite'] + vb[1]['valore_procapite']

        ValoreBilancio.objects.create(
            territorio=vb_filters['territorio'],
            anno=vb_filters['anno'],
            voce=voce_sum,
            valore=valore,
            valore_procapite=valore_procapite
        )

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
            years_list = [int(y.strip()) for y in years.split(",") if settings.APP_START_YEAR <= int(y.strip()) <= settings.APP_END_YEAR]

        if not years_list:
            raise Exception("No suitable year found in {0}".format(years))

        self.years = years_list

    def set_cities(self, cities_codes, start_from):
        # set considered cities
        mapper = FLMapper()

        if not cities_codes:
            if start_from:
                cities_codes = 'all'
                all_cities = mapper.get_cities(cities_codes, logger=self.logger)
                try:
                    self.cities_finloc = all_cities[all_cities.index(start_from):]
                except ValueError:
                    raise Exception("Start-from city not found in cities complete list, use name--cod_finloc. "
                                    "Example: ZUNGRI--4181030500")
                else:
                    self.logger.info("Processing cities starting from: {0}".format(start_from))
            else:
                raise Exception("Missing cities parameter or start-from parameter")

        else:
            self.cities_finloc = mapper.get_cities(cities_codes, logger=self.logger)

        # if skip-existing flag is true: removes already present cities from the cities set
        if self.skip_existing:
            existing_cities_finloc = ValoreBilancio.objects.\
                filter(territorio__cod_finloc__in=self.cities_finloc).\
                distinct('territorio__cod_finloc').\
                order_by('territorio__cod_finloc').\
                values_list('territorio__cod_finloc', flat=True)

            if len(existing_cities_finloc) > 0:

                self.logger.info(u"Skipping following cities {}, because already in db".format(existing_cities_finloc))
                self.cities_finloc = filter(lambda c: c not in existing_cities_finloc, self.cities_finloc)

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

        self.considered_tipo_bilancio = self.root_treenode.\
            get_ancestors(include_self=True, ascending=False).\
            get(slug__in=self.accepted_bilanci_types).slug

        # checks which branches of somma-funzioni are interested by the import
        self.considered_somma_funzioni = self.root_descendants.\
            filter(slug__in=self.somma_funzioni_branches).\
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
        import_set = OrderedDict((cod_finloc, years_dict) for cod_finloc in self.cities_finloc)

        # construct values_to_delete
        values_to_delete = ValoreBilancio.objects.filter(territorio__cod_finloc__in=self.cities_finloc, anno__in=self.years)
        if self.partial_import:
            values_to_delete = values_to_delete.filter(voce__in=self.root_descendants)

        # get data about ImportXml: if there is data that has been imported from XML for a city/ year
        # then the couch import must NOT overwrite that data
        imported_xml = ImportXmlBilancio.objects.\
            filter(territorio__cod_finloc__in=self.cities_finloc, anno__in=self.years, tipologia__in=self.considered_tipo_bilancio).\
            order_by('territorio', 'anno')

        if len(imported_xml) > 0:
            for i in imported_xml:
                self.logger.info("BILANCIO:{} YEAR:{} CITY:{} will be skipped: was imported with xml".\
                    format(i.tipologia.title(), i.anno, i.territorio.denominazione))

                #    bilancio type is removed from import set
                import_set[i.territorio.cod_finloc][i.anno] = filter(lambda x: x != i.tipologia, import_set[i.territorio.cod_finloc][i.anno])
                #    bilancio xml is removed from values_to_delete
                values_to_delete = values_to_delete.exclude(territorio=i.territorio, anno=i.anno, voce__slug__startswith=i.tipologia)
                if len(import_set[i.territorio.cod_finloc][i.anno]) == 0:
                    import_set[i.territorio.cod_finloc].pop(i.anno)

        # set the import_set
        self.import_set = import_set
        # deletes ValoriBilanci that will be imported afterwards: this speeds up the import
        if self.partial_import:
            self.logger.info("Deleting values for selected cities, years and subtree")
        else:
            self.logger.info("Deleting values for selected cities, years")

        if not self.dryrun and ValoreBilancio.objects.all().count()>0:
            values_to_delete.delete()
        self.logger.info("Done deleting")

        # creates somma_funzioni_slug_baseset
        for slug in self.considered_somma_funzioni:
            components = Voce.objects.get(slug=slug).get_components_somma_funzioni()
            descendants = []
            for c in components:
                descendants.extend(c.get_descendants(include_self=True))

            self.somma_funzioni_slug_baseset[slug] = descendants

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
        self.skip_existing = options['skip_existing']

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
        cities_codes = options['cities']
        start_from = options['start_from']

        self.set_cities(cities_codes, start_from)

        if len(self.cities_finloc) == 0:
            self.logger.info("No cities to process. Quit")
            return

        # check if debug is active: the task may fail
        if settings.DEBUG is True and settings.INSTANCE_TYPE != 'development' and len(self.cities_finloc) > 4000:
            self.logger.error("DEBUG settings is True, task will fail. Disable DEBUG and retry")
            exit()

        if cities_codes.lower() != 'all':
            self.logger.info("Processing cities: {0}".format(self.cities_finloc))

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
            self.checks_partial_import(tree_node_slug, couch_path_string )

        # create the tree if it does not exist or if forced to do so
        if create_tree or Voce.objects.count() == 0:
            if not self.dryrun:
                self.create_voci_tree(force_google=force_google)

        # build the map of slug to pk for the Voce tree
        self.voci_dict = Voce.objects.get_dict_by_slug()

        # considering years,cities and limitations set creates a comprehensive map of all bilancio to be imported,
        # deletes old values before import
        self.prepare_for_import()

        for city_finloc, city_years in self.import_set.iteritems():

            try:
                territorio = Territorio.objects.get(cod_finloc=city_finloc)
            except ObjectDoesNotExist:
                self.logger.warning(u"City {0} not found among territories in DB. Skipping.".format(city_finloc))

            # get all budgets for the city
            city_budget = self.couchdb.get(city_finloc)

            if city_budget is None:
                self.logger.warning(u"City {} not found in couchdb instance. Skipping.".format(city_finloc))
                continue

            self.logger.info(u"Processing city of {0}".format(city_finloc))

            for year, certificati_to_import in city_years.iteritems():
                if str(year) not in city_budget:
                    self.logger.warning(u"- Year {} not found. Skipping.".format(year))
                    continue

                # POPULATION
                # fetch valid population, starting from this year
                # if no population found, set it to None, as not to break things
                try:
                    (pop_year, population) = territorio.nearest_valid_population(year)
                except TypeError:
                    population = None

                self.logger.debug("::Population: {0}".format(population))

                # build a BilancioItem tree, out of the couch-extracted dict
                # for the given city and year
                # add the totals by extracting them from the dict, or by computing
                city_year_budget_dict = city_budget[str(year)]

                if self.partial_import is True:
                    self.logger.info(u"- Processing year: {}, subtree: {}".format(year, tree_node_slug))
                    # start from a custom node
                    path_not_found = False
                    city_year_budget_node_dict = city_year_budget_dict.copy()

                    # get the starting node in couchdb data
                    for k in self.couch_path:
                        try:
                            city_year_budget_node_dict = city_year_budget_node_dict[k]
                        except KeyError:
                            self.logger.warning(
                                "Couch path:{0} not present for {1}, anno:{2}".format(self.couch_path, territorio.cod_finloc,
                                                                                      str(year)))
                            path_not_found = True
                            break

                    # if data path is found in the couch document, write data into postgres db
                    if path_not_found is False:
                        city_year_node_tree_patch = tree_models.make_tree_from_dict(
                            city_year_budget_node_dict, self.voci_dict, path=[tree_node_slug],
                            population=population
                        )

                        # writes new sub-tree
                        if not self.dryrun:
                            tree_models.write_tree_to_vb_db(territorio, year, city_year_node_tree_patch, self.voci_dict)
                else:
                    # import tipo_bilancio considered
                    # normally is preventivo and consuntivo
                    # otherwise only one of them

                    for tipo_bilancio in certificati_to_import:
                        certificato_tree = tree_models.make_tree_from_dict(
                            city_year_budget_dict[tipo_bilancio], self.voci_dict, path=[unicode(tipo_bilancio)],
                            population=population
                        )
                        if len(certificato_tree.children) == 0:
                            continue
                        self.logger.debug(u"- Processing year: {} bilancio: {}".format(year, tipo_bilancio))
                        if not self.dryrun:
                            tree_models.write_tree_to_vb_db(territorio, year, certificato_tree, self.voci_dict)

                # actually save data into posgres
                self.logger.debug("Write valori bilancio to postgres")
                tree_models.db_flush()
                
                # applies somma-funzioni patch only to the interested somma-funzioni branches (if any)
                if len(self.considered_somma_funzioni) > 0:
                    self.logger.debug("Somma funzioni patch")

                    vb_filters = {
                        'territorio': territorio,
                        'anno': year,
                    }
                    for somma_funzioni_branch in self.considered_somma_funzioni:

                        # get data for somma-funzioni patch, getting only the needed ValoreBilancio using the
                        # somma_funzioni_slug_baseset
                        needed_slugs = self.somma_funzioni_slug_baseset[somma_funzioni_branch]
                        vb = ValoreBilancio.objects.\
                            filter(**vb_filters).\
                            filter( voce__slug__in=needed_slugs).\
                            values_list('voce__slug', 'valore', 'valore_procapite')

                        if len(vb) == 0:
                            self.logger.debug("Skipping {} branch: no values in db".format(somma_funzioni_branch))
                            continue

                        vb_dict = dict((v[0], {'valore': v[1], 'valore_procapite': v[2]}) for v in vb)

                        if not self.dryrun:
                            for voce_slug in Voce.objects.get(slug=somma_funzioni_branch).get_descendants(include_self=True):
                                self.apply_somma_funzioni_patch(voce_slug, vb_filters, vb_dict)
                        del vb_dict

        self.logger.info("Done importing into postgres")

        if complete and not self.dryrun and not self.partial_import:

            ##
            # Update voci medians
            ##

            self.logger.info(u"Update indicators medians")
            call_command('median', verbosity=2, years=options['years'], cities=",".join(self.cities_finloc), type='voci',
                         interactive=False)

            ##
            # Compute Indicators
            ##
            if not self.partial_import:
                self.logger.info(u"Compute indicators for selected Comuni")

                call_command('indicators', verbosity=2, years=options['years'], cities=",".join(self.cities_finloc), indicators='all',
                             interactive=False)

            ##
            # Update indicators medians
            ##

            self.logger.info(u"Update indicators medians")
            call_command('median', verbosity=2, years=options['years'], cities=",".join(self.cities_finloc), type='indicatori',
                         interactive=False)


            ##
            # Update opendata zip files
            ##

            self.logger.info(u"Update opendata zip files for selected Comuni")
            call_command('update_opendata', verbosity=2, years=options['years'], cities=",".join(self.cities_finloc), compress=True,
                         interactive=False)

        email_utils.send_notification_email(msg_string="Couch2pg has finished.")