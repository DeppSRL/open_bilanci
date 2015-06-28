"""
Module containing a BilancioItem class and some factory methods.
"""
import sys
import itertools
from django.conf import settings
from django.utils.formats import number_format
from django.utils.text import slugify
from bilanci.models import Voce, ValoreBilancio

__author__ = 'guglielmo'


def make_item(**kwargs):
    """
    Return an instance of BilancioItem, starting from the parameters
    specified in the kwargs dictionary.

    :param kwargs:
        needed keys: slug, denominazione
        optional keys (default): descrizione (''), valore (0.0), valore_procapite (0.0)

    :return: BilanciItem instance
    """
    return BilancioItem(**kwargs)

def make_composite(*items, **kwargs):
    """
    Return an instance of BilancioItem, containing other items (composite pattern)
    The container instance's attributes are fetched from the parameters
    specified in the kwargs dictionary.

    :param items: list of BilanciItem to be added as children of the returned instance
    :param kwargs:
        needed keys: slug, denominazione
        optional keys (default): descrizione (''), valore (0.0), valore_procapite (0.0)

    :return: BilanciItem instance
    """
    return BilancioItem(*items, **kwargs)


def make_tree_from_dict(budget_node, voci_dict, path=None, logger=None, population=None):
    """
    Generate a composite BilancioItem tree, starting from a budget_node python dict

    :param budget_node: Contains the budget (usually extracted from couchdb)
    :param voci_dict:   Contains the mapping of the Voce MPTT tree (slug to instance)
    :param path:        A list of path, within the budget_node, where to start
    :param logger:      If specified, used to log warning messages
    """
    if not isinstance(voci_dict, dict):
        raise Exception("Wrong type {} for voci_dict. dict expected.".format(type(voci_dict)))

    if path is None:
        path = []


    # build slug out of the local_path
    local_path = path[:]
    if len(local_path) == 0:
        raise Exception("At least one element is needed in the local path")
    elif len(local_path) == 1:
        slug = u"{}".format(slugify(local_path[0]))
    else:
        slug = u"{0}-{1}".format(local_path[0], "-".join(slugify(i) for i in local_path[1:]))

    # get corresponding Voce instance
    voce_node_params = {}
    if slug not in voci_dict:
        # this should not happen, skipping
        if logger:
            logger.warning("Slug:{0} not present in voci_dict, skipping".format(slug))
        return None
    else:
        voce_node = voci_dict[slug]

        voce_node_params = {
            'denominazione':     voce_node.denominazione,
            'descrizione':       voce_node.descrizione,
            'slug':              voce_node.slug,
        }


    if isinstance(budget_node, dict):
        treeitem_children = []

        for key, child_node in budget_node.items():
            if key == 'TOTALE':
                continue
            local_path = path[:]
            local_path.append(key)
            child_tree = make_tree_from_dict(child_node, voci_dict, local_path, logger, population)
            if child_tree is not None:
                treeitem_children.append(child_tree)

        # return the composition of children
        ret = make_composite(*treeitem_children, **voce_node_params)

        # compute valore associated with this node, using a TOTALE child
        # or computing the sum
        if 'TOTALE' in budget_node.keys():
            ret.valore = budget_node['TOTALE']
            if population:
                ret.valore_procapite = ret.valore / float(population)
        else:
            ret.valore = ret.somma_valori()
            if population:
                ret.valore_procapite = ret.valore / float(population)
        return ret

    else:
        voce_node_params['valore'] = budget_node
        if population:
            voce_node_params['valore_procapite'] = budget_node / float(population)
        return make_item(**voce_node_params)

def make_tree_from_db(voce_node, valori_bilancio):
    """
    Return a BilancioItem object, starting from a Voce MPTT model node
    and a dictionary of unique values extracted from VoceBilancio.

    The function is recursive.

    :param voce_node: The Voce node
    :param voci_bilancio: A dictionary of values, one for every descendant of the Voce node
    :return: a BilancioItem object

    """
    if not isinstance(voce_node, Voce):
        raise Exception("Wrong type {} for voce_node. Voce expected.".format(type(voce_node)))

    if not isinstance(valori_bilancio, dict):
        raise Exception("Wrong type {} for valori_bilancio. dict expected.".format(type(valori_bilancio)))

    voce_node_params = {
        'denominazione':     voce_node.denominazione,
        'descrizione':       voce_node.descrizione,
        'slug':              voce_node.slug,
    }
    if voce_node.pk in valori_bilancio:
        voce_node_params['valore'] = valori_bilancio[voce_node.pk]['valore'],
        voce_node_params['valore_procapite'] = valori_bilancio[voce_node.pk]['valore_procapite']

    if voce_node.is_leaf_node():
        return make_item(**voce_node_params)
    else:
        treeitem_children = []
        for voce_node_child in voce_node.get_children():
            treeitem_children.append(make_tree_from_db(voce_node_child, valori_bilancio))
        return make_composite(*treeitem_children, **voce_node_params)

list_to_create = []
def write_values_to_vb(territorio, anno, voce, valori, get_or_create=False):
    """
    Write a record in the VoceBilancio model

    :param territorio:    A Territorio object, identifying the city
    :param anno:          The year, as an integer
    :param voce:          The Voce node
    :para valori:         a dict, with valore and valore_procapito values, to be persisted
    :param get_or_create: A flag, signaling whether to use the get_or_create method (slower)
    """
    if get_or_create:
        vb, created = ValoreBilancio.objects.get_or_create(
            territorio=territorio,
            anno=anno,
            voce=voce,
            defaults={
                'valore': valori['valore'],
                'valore_procapite': valori['valore_procapite']
            }
        )
        if not created:
            vb.valore = valori['valore']
            vb.valore_procapite = valori['valore_procapite']
            vb.save()
    else:
        global list_to_create
        list_to_create.append(
            ValoreBilancio(
                territorio=territorio,
                anno=anno,
                voce=voce,
                valore=valori['valore'],
                valore_procapite=valori['valore_procapite'])
        )

def db_flush():
    global list_to_create
    ValoreBilancio.objects.bulk_create(list_to_create)
    list_to_create=[]

def write_record_to_vb_db(territorio, anno, tree_node, voci_dict, get_or_create=False):
    """
    Save a single node in the VoceBilancio model

    :param territorio:    A Territorio object, identifying the city
    :param anno:          The year, as an integer
    :param tree_node:     The BilancioItem object to persist
    :param get_or_create: A flag, signaling whether to use the get_or_create method (slower)
    """

    tree_node_slug = tree_node.slug
    voce = voci_dict[tree_node_slug]
    valori = {
        'valore': tree_node.valore,
        'valore_procapite': tree_node.valore_procapite,
    }

    write_values_to_vb(territorio, anno, voce, valori, get_or_create)


def write_tree_to_vb_db(territorio, anno, tree_node, voci_dict, get_or_create=False):
    """
    Recursively save records in the VoceBilancio model, persisting a BilancioItem tree

    :param territorio:    A Territorio object, identifying the city
    :param anno:          The year, as an integer
    :param tree_node:     The BilancioItem object to persist
    :param get_or_create: A flag, signaling whether to use the get_or_create method (slower)
    """
    write_record_to_vb_db(territorio, anno, tree_node, voci_dict, get_or_create)
    for child_node in tree_node.children:
        write_tree_to_vb_db(territorio, anno, child_node, voci_dict, get_or_create)


class BilancioItem():
    """
    Model representing the budget tree, as a composite pattern.

    The BilancioItem class is used to merge the tree structure and the values in the DB,
    in a single instance, as to minimize the number of queries in management tasks or views context.
    """

    def __init__(self, *items, **kwargs):
        # slug and denominazione are needed
        self.slug = kwargs['slug']
        self.denominazione = kwargs['denominazione']

        # descrizione and valori are not needed
        self.descrizione = kwargs.get('descrizione', '')
        self.valore = kwargs.get('valore', 0.00)
        self.valore_procapite = kwargs.get('valore_procapite', 0.00)

        self.children = []
        self.parent = None

        if items:
            self.add(*items)

    @property
    def composite(self):
        return bool(self.children)

    def get_ancestors(self):
        ret = []
        node = self
        while node.parent is not None:
            ret.append(node.denominazione)
            node = node.parent
        return ret

    def valore_reale(self, year):
        return self.valore * settings.GDP_DEFLATORS[year]

    def valore_procapite_reale(self, year):
        return self.valore_procapite * settings.GDP_DEFLATORS[year]

    def add(self, first, *items):
        self.children.extend(itertools.chain((first,), items))
        for child in self.children:
            child.parent = self

    def remove(self, item):
        self.children.remove(item)

    def __iter__(self):
        return iter(self.children)

    def somma_valori(self):
        """
        Return the computed sum of valore for the children of the current node
        """
        return (sum(item.valore for item in self) if self.composite else self.valore)

    def somma_valori_veriifed(self):
        """
        Return a boolean that states if the computed sum equals the stored one
        """
        return self.somma_valori() == self.valore

    def somma_valori_procapite(self):
        """
        Return the computed sum of valore_procapite for the children of the current node
        """
        return (sum(item.valore_procapite for item in self) if self.composite else self.valore_procapite)

    def somma_valori_procapite_veriifed(self):
        """
        Return a boolean that states if the computed sum equals the stored one
        """
        return self.somma_valori_procapite() == self.valore_procapite

    def emit(self, indent=u"", file=sys.stdout):
        """
        Emit the Bilancio tree item in readable format.
        Useful for debugging and development purposes.
        """
        print(u"{} {} {:.2f} (procapite: {:.2f})".format(
            indent, self.denominazione, self.valore, self.valore_procapite
        ))
        for child in self:
            child.emit(indent + u"  ")

    def emit_as_list(self, list_of_leaves=None, ancestors_separator="|"):
        list_of_leaves = [] if list_of_leaves is None else list_of_leaves

        ancestors = ancestors_separator.join(self.get_ancestors()[::-1])
        list_of_leaves.append([ancestors,
                               str(self.valore),
                               str(self.valore_procapite).replace(".", ",")])
        for child in self:
            child.emit_as_list(list_of_leaves, ancestors_separator=ancestors_separator)


