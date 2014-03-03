from collections import OrderedDict
import logging
from optparse import make_option
from django.conf import settings
from django.core.management import BaseCommand
from django.utils.text import slugify
from bilanci.models import Voce, ValoreBilancio
from bilanci.utils import couch, gdocs
from bilanci.utils.comuni import FLMapper
from territori.models import Territorio


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
        make_option('--create-tree',
                    dest='create_tree',
                    action='store_true',
                    default=False,
                    help='Force recreating simplified tree leaves from csv file or gdocs (remove all values)'),
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
        self.voci_map = dict([(v.slug, v) for v in Voce.objects.all()])

        for city in cities:

            territorio = Territorio.objects.get(cod_finloc=city)

            # get all budgets for the city
            city_budget = couchdb.get(city)

            if city_budget is None:
               self.logger.warning(u"City {} not found in couchdb instance. Skipping.".format(city))
               continue

            self.logger.info(u"Processing city of {0}".format(city))

            for year in years:
                if str(year) not in city_budget:
                    self.logger.warning(u"- Year {} not found. Skipping.".format(year))
                    continue

                self.logger.info(u"- Processing year: {}".format(year))
                self.get_values_from_couch(territorio, year, city_budget[str(year)])


    def get_values_from_couch(self, territorio, anno, node, path=None):
        """
        The values from the couch db (in self.city_budget) are copied into the ValoreBilancio model
        """
        if path is None:
            path = []
        if isinstance(node, dict):
            for key, child_node in node.items():
                local_path = path[:]
                local_path.append(key)
                self.get_values_from_couch(territorio, anno, child_node, local_path)
        else:
            local_path = path[:]

            # build slug out of the local_path
            if len(local_path) == 1:
                slug = u"{}".format(slugify(local_path[0]))
            else:
                slug = u"{0}-{1}".format(local_path[0], "-".join(slugify(i) for i in local_path[1:]))

            # insert into the DB
            if slug not in self.voci_map:
                self.logger.warning("Slug:{0} not present in voci_map, skipping".format(slug))
            else:
                params = {
                    'anno': anno,
                    'territorio': territorio,
                    'valore': node,
                    'voce': self.voci_map[slug]
                }
                self.logger.debug(
                    u"Inserting val: {0[valore]}, anno: {0[anno]}, territorio:{0[territorio]}, voce: {0[voce]}".format(
                        params
                    )
                )
                ValoreBilancio.objects.create(**params)



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
                self.logger.debug(u"adding leaf {}".format(",".join(leaf_bc)))


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
                    self.logger.debug(u"adding leaf {}".format(",".join(leaf_bc)))


    def add_leaf(self, breadcrumbs, subtree_node, section_slug=''):
        """
        Add a leaf to the subtree, given the breadcrumbs list.
        Creates the needed nodes in the process.
        """

        # copy breadcrumbs and remove last elements if empty
        bc = breadcrumbs[:]
        while not bc[-1]:
            bc.pop()

        prefix_slug = subtree_node.slug

        current_node = subtree_node
        for item in bc:
            if current_node.get_children().filter(denominazione__iexact=item).count() == 0:
                slug = u"{0}-{1}".format(prefix_slug, "-".join(slugify(i) for i in bc[0:bc.index(item)+1]))
                node = Voce(denominazione=item, slug=slug)
                node.insert_at(current_node, save=True, position='last-child')
                if bc[-1] == item:
                    return
            else:
                node = current_node.get_children().get(denominazione__iexact=item)

            current_node = node

