from collections import OrderedDict
import logging
from optparse import make_option
from django.conf import settings
from django.core.management import BaseCommand
from django.utils.text import slugify
from bilanci import tree_models
from bilanci.models import Voce, ValoreBilancio
from bilanci.utils import couch, gdocs
from bilanci.utils.comuni import FLMapper
from territori.models import Territorio, ObjectDoesNotExist


class Command(BaseCommand):


    option_list = BaseCommand.option_list + (
        make_option('--dry-run',
                    dest='dryrun',
                    action='store_true',
                    default=False,
                    help='Set the dry-run command mode: nothing is written in the couchdb'),
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
        make_option('--patch-somma-funzioni-only',
                    dest='patch_somma_funzioni_only',
                    action='store_true',
                    default=False,
                    help='Only apply the patch to compute somma-funzioni. Does not import other budget data.'),
        make_option('--append',
                    dest='append',
                    action='store_true',
                    default=False,
                    help='Use the log file appending instead of overwriting (used when launching shell scripts)'),
    )

    help = 'Import values from the simplified couchdb database into a Postgresql server'

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
        create_tree = options['create_tree']
        skip_existing = options['skip_existing']
        patch_somma_funzioni_only = options['patch_somma_funzioni_only']

        if options['append'] is True:
            self.logger = logging.getLogger('management_append')


        ###
        # cities
        ###
        cities_codes = options['cities']
        if not cities_codes:
            raise Exception("Missing cities parameter")

        mapper = FLMapper(settings.LISTA_COMUNI_PATH)
        cities = mapper.get_cities(cities_codes)
        if cities_codes.lower() != 'all':
            self.logger.info("Processing cities: {0}".format(cities))


        ###
        # years
        ###
        years = options['years']
        if not years:
            raise Exception("Missing years parameter")

        if "-" in years:
            (start_year, end_year) = years.split("-")
            years = range(int(start_year), int(end_year)+1)
        else:
            years = [int(y.strip()) for y in years.split(",") if 2001 < int(y.strip()) < 2013]

        if not years:
            raise Exception("No suitable year found in {0}".format(years))

        self.logger.info("Processing years: {0}".format(years))
        self.years = years


        ###
        # couchdb
        ###

        couchdb_server_alias = options['couchdb_server']
        couchdb_dbname = settings.COUCHDB_SIMPLIFIED_NAME

        if couchdb_server_alias not in settings.COUCHDB_SERVERS:
            raise Exception("Unknown couchdb server alias.")

        couchdb = couch.connect(
            couchdb_dbname,
            couchdb_server_settings=settings.COUCHDB_SERVERS[couchdb_server_alias]
        )


        # create the tree if it does not exist or if forced to do so
        if create_tree or Voce.objects.count() == 0:
            self.create_voci_tree()


        # build the map of slug to pk for the Voce tree
        self.voci_dict = Voce.objects.get_dict_by_slug()

        for city in cities:

            try:
                territorio = Territorio.objects.get(cod_finloc=city)
            except ObjectDoesNotExist:
                self.logger.warning(u"City {0} not found among territories in DB. Skipping.".format(city))

            # get all budgets for the city
            city_budget = couchdb.get(city)

            if city_budget is None:
               self.logger.warning(u"City {} not found in couchdb instance. Skipping.".format(city))
               continue

            # check values for the city inside ValoreBilancio,
            # skip if values are there and the skip-existing option was required
            try:
                _ = ValoreBilancio.objects.filter(territorio=territorio)[0]
                if skip_existing:
                    self.logger.info(u"Skipping city of {}, as already processed".format(city))
                    continue
            except IndexError:
                pass

            self.logger.info(u"Processing city of {0}".format(city))

            for year in years:
                if str(year) not in city_budget:
                    self.logger.warning(u"- Year {} not found. Skipping.".format(year))
                    continue

                self.logger.info(u"- Processing year: {}".format(year))


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
                city_year_preventivo_tree = tree_models.make_tree_from_dict(
                    city_year_budget_dict['preventivo'], self.voci_dict, path=[u'preventivo'],
                    population=population
                )
                city_year_consuntivo_tree = tree_models.make_tree_from_dict(
                    city_year_budget_dict['consuntivo'], self.voci_dict, path=[u'consuntivo'],
                    population=population
                )


                if not patch_somma_funzioni_only:

                    ### persist the BilancioItem values

                    # previously remove all values for a city and a year
                    # used to speed up records insertion
                    ValoreBilancio.objects.filter(territorio=territorio, anno=year).delete()

                    # add values fastly, without checking their existance
                    # do that for the whole tree (preventivo, consuntivo, ...)
                    tree_models.write_tree_to_vb_db(territorio, year, city_year_preventivo_tree, self.voci_dict)
                    tree_models.write_tree_to_vb_db(territorio, year, city_year_consuntivo_tree, self.voci_dict)


                vb_filters = {
                    'territorio': territorio,
                    'anno': year,
                }

                ##
                # insert/overwrite compute somma-funzioni in preventivo
                ##
                f_correnti = self.voci_dict['preventivo-spese-spese-correnti-funzioni']
                for voce_c in f_correnti.get_descendants(include_self=True):
                    self.apply_somma_funzioni_patch(voce_c, vb_filters)

                f_correnti = self.voci_dict['consuntivo-spese-cassa-spese-correnti-funzioni']
                for voce_c in f_correnti.get_descendants(include_self=True):
                    self.apply_somma_funzioni_patch(voce_c, vb_filters)

                f_correnti = self.voci_dict['consuntivo-spese-impegni-spese-correnti-funzioni']
                for voce_c in f_correnti.get_descendants(include_self=True):
                    self.apply_somma_funzioni_patch(voce_c, vb_filters)


    def apply_somma_funzioni_patch(self, voce_corr, vb_filters):
        """
        Compute spese correnti and spese per investimenti for funzioni, and write into spese-somma

        Overwrite values if found.
        """
        voce_i = self.voci_dict[voce_corr.slug.replace('spese-correnti-funzioni', 'spese-per-investimenti-funzioni')]
        voce_sum = self.voci_dict[voce_corr.slug.replace('spese-correnti-funzioni', 'spese-somma-funzioni')]
        self.logger.debug("Applying somma_funzioni_patch to {0}".format(voce_sum.slug))

        try:
            vb_c = voce_corr.valorebilancio_set.get(**vb_filters)
            vb_i = voce_i.valorebilancio_set.get(**vb_filters)

            # remove all values for the somma_funzioni voce,
            # so that values can be added with a faster create
            voce_sum.valorebilancio_set.filter(**vb_filters).delete()

            valore = vb_c.valore + vb_i.valore
            valore_procapite = vb_c.valore_procapite + vb_i.valore_procapite

            ValoreBilancio.objects.create(
                territorio=vb_filters['territorio'],
                anno=vb_filters['anno'],
                voce=voce_sum,
                valore=valore,
                valore_procapite=valore_procapite
            )

        except ObjectDoesNotExist:
            pass


    def create_voci_tree(self):
        """
        Create a Voci tree. If the tree exists, then it is deleted.
        """
        if Voce.objects.count() > 0:
            Voce.objects.all().delete()

        # get simplified leaves (from csv or gdocs), to build the voices tree
        self.simplified_subtrees_leaves = gdocs.get_simplified_leaves()

        self.create_voci_preventivo_tree()

        self.create_voci_consuntivo_tree()


    def create_voci_preventivo_tree(self):

        # create preventivo root
        subtree_node = Voce(denominazione='Preventivo', slug='preventivo')
        subtree_node.insert_at(None, save=True, position='last-child')

        # the preventivo subsections
        subtrees = OrderedDict([
            ('preventivo-entrate', 'Preventivo entrate'),
            ('preventivo-spese',   'Preventivo spese'),
        ])

        # add all leaves from the preventivo sections under preventivo
        # entrate and spese are already considered
        for subtree_slug, subtree_denominazione in subtrees.items():

            for leaf_bc in self.simplified_subtrees_leaves[subtree_slug]:
                # add this leaf to the subtree, adding all needed intermediate nodes
                self.add_leaf(leaf_bc, subtree_node)


    def create_voci_consuntivo_tree(self):
        # create consuntivo root
        subtree_node = Voce(denominazione='Consuntivo', slug='consuntivo')
        subtree_node.insert_at(None, save=True, position='last-child')

        subtrees = OrderedDict([
            ('consuntivo-entrate', {
                'denominazione': u'Consuntivo entrate',
                'sections': [u'Accertamenti', u'Riscossioni in conto competenza', u'Riscossioni in conto residui', u'Cassa']
            }),
            ('consuntivo-spese', {
                'denominazione': u'Consuntivo spese',
                'sections': [u'Impegni', u'Pagamenti in conto competenza', u'Pagamenti in conto residui', u'Cassa']
            }),
        ])

        for subtree_slug, subtree_structure in subtrees.items():

            for section_name in subtree_structure['sections']:
                for leaf_bc in self.simplified_subtrees_leaves[subtree_slug]:
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
                slug = u"{0}-{1}".format(prefix_slug, u"-".join(slugify(i) for i in bc[0:bc.index(item)+1]))
                node = Voce(denominazione=item, slug=slug)
                node.insert_at(current_node, save=True, position='last-child')
                if bc[-1] == item:
                    return
            else:
                node = current_node.get_children().get(denominazione__iexact=item)

            current_node = node


