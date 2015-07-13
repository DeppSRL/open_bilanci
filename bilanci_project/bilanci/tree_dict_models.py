# -*- coding: utf-8 -*-
from collections import OrderedDict
from bilanci.utils import nearly_equal

__author__ = 'guglielmo'

import abc

###
# functions
###

def subtree_sum(a, b):
    """
    Recursive function to generate a dictionary,
    that contains the same keys of the addends,
    where each value is the sum of the corrsponding addeds' values

    Non-matching keys are skipped.

    :retv: dictionary or integer
    """
    if isinstance(a, int) or isinstance(a, long):
        return a + b
    else:
        c = {}
        for k, av in a.items():
            if k in b:
                bv = b[k]
                c[k] = subtree_sum(av, bv)
        return c


def deep_sum(node, exclude='totale', logger=None, level=0):
    """
    Recursive function to generate the sum of all descending leaves of a node

    Node with key equal to the *excluded* argument are skipped

    :retv: int
    """
    if isinstance(node, int) or isinstance(node, long):
        return node
    else:
        s = 0
        level += 1
        for k, v in node.items():
            if logger:
                if (isinstance(v, int) or isinstance(v, long)):
                    logger.info(u"{0}node: {1} => {2}".format(level * "-", k, v))
                else:
                    logger.info(u"{0}node: {1} => *".format(level * "-", k))

            if k.lower() == exclude.lower():
                continue
            s += deep_sum(v, exclude=exclude, logger=logger, level=level)

        if logger:
            logger.info(u"{0}::::{1}:::::".format(level * "-", s))

        return s



###
#  TreeDict model, to be used along couchdb to model the budget trees,
#  access them and build them
###

# exceptions
class SubtreeWrongMapping(Exception):
    pass

class SubtreeIsEmpty(Exception):
    pass

class SubtreeDoesNotExist(Exception):
    pass

class MultipleValueFoundException(Exception):
    pass

class TitoloNotFound(Exception):
    pass

class VoceNotFound(Exception):
    pass





class EntrateBudgetMixin(object):
    """
    Defines the _compute_sum method for the entrate BudgetTrees

    MUST be subclassed along with a subclass of BudgetTreeDict
    """

    def _compute_sum(self, simplified_bc, mapping, col_idx=None, bilancio_type=None):
        """
        Compute the sum of all voices in the normalized budget doc (source)
        that corresponds to the simplified voice (destination)
        according to the voci_map mapping.

        :simplified_bc:  - the simplified destination tree, as breadcrumbs
        :mapping:        - the mapping parameters, grouped
          :voci_map:       - the mapping between source and destination voices
          :normalized_doc: - the couchdb source document,
        :col_idx:        - if integer, representing the column index to fetch (optional)
        :bilancio_type:        - guess what

        the method always returns a scalar value
        """
        ret = 0

        (voci_map, normalized_doc) = mapping


        # get all voices in normalized tree, matching the voce in simplified tree
        voci_matches = self._get_matching_voci(simplified_bc, voci_map)
        if not voci_matches:
            self._emit_debug(u"No matching voci found for: {},{}.".format(
                bilancio_type,simplified_bc
            ))


        # compute the sum of the matching voices
        for voce_match in voci_matches:
            try:
                val = self._get_value(voce_match, normalized_doc, col_idx=col_idx)
            except (MultipleValueFoundException, SubtreeDoesNotExist, SubtreeIsEmpty) as e:
                self._emit_warning(unicode(e))
                continue
            except (TitoloNotFound, VoceNotFound) as e:
                self._emit_debug(unicode(e))
                continue

            ret += val

        return ret


class SpeseBudgetMixin(object):
    """
    Defines the _compute_sum method for the spese BudgetTrees

    MUST be subclassed along with a subclass of BudgetTreeDict
    """
    def _compute_sum(self, simplified_bc, mapping, section_name=None, col_idx=None, bilancio_type=None):
        """
        Compute the sum of all voices in the normalized budget doc (source)
        that corresponds to the simplified voice (destination)
        according to the voci_map mapping.

        :simplified_bc:  - the simplified destination tree, as breadcrumbs
        :mapping:        - the mapping parameters, grouped
          :voci_map:       - the mapping between source and destination voices
          :interventi_map: - the mapping of the interventi
          :normalized_doc: - the couchdb source document,
        :section_name:  - string, the extended name of the section (Impegni, Spese in conto competenza, ...)
        :col_idx:        - integer, representing the column index to fetch (optional)
        :bilancio_type:        -

        the method always returns a scalar value
        """
        ret = 0

        (voci_map, interventi_map, normalized_doc) = mapping

        # get all voices in mormalized tree, matching the voce in simplified tree
        bc = simplified_bc[:]
        if section_name:
            bc.insert(2, section_name)


        voci_matches = self._get_matching_voci(bc, voci_map)
        if not voci_matches:
            self._emit_debug(u"No matching voci found for: {},{}.".format(
                bilancio_type,bc
            ))

        # compute the sum of the matching voices
        for voce_match in voci_matches:

            interventi_matches = ()

            if bc[2] == 'interventi':
                # handle mapping and sum
                interventi_matches = self._get_matching_interventi(bc[3], interventi_map)
                if not interventi_matches:
                    self._emit_warning(u"Could not find proper mapping for [{}]".format(
                        bc[3]
                    ))

            if bc[3] == 'interventi':
                # handle mapping and sum
                interventi_matches = self._get_matching_interventi(bc[4], interventi_map)
                if not interventi_matches:
                    self._emit_warning(u"Could not find proper mapping for [{}]".format(
                        bc[4]
                    ))

            try:
                val = self._get_value(voce_match, normalized_doc, col_idx=col_idx, interventi_matches=tuple(interventi_matches))
            except (MultipleValueFoundException, SubtreeDoesNotExist, SubtreeIsEmpty) as e:
                self._emit_warning(unicode(e))
                continue
            except (TitoloNotFound, VoceNotFound) as e:
                self._emit_debug(unicode(e))
                continue



            ret += val

        return ret



# trees
class BudgetTreeDict(OrderedDict):

    """
    An Abstract Base Class, representing the simplified BudgetTree.

    Extends the standard dict and can be serialized as json and exported to couchdb.

    It MUST be subclassed by dedicated classes:
    - PreventivoEntrateBudgetTreeDict,
    - ConsuntivoEntrateBudgetTreeDict,
    - ConsuntivoSpeseBudgetTreeDict

    Every sub-tree is built according to a slightly different logic.
    """

    __metaclass__  = abc.ABCMeta
    logger = None

    def __init__(self, *args, **kwargs):
        """
        Build and return a BudgetTreeDict object, out of a list of items.
        Each item is a sequence of paths.

        Leaf values are computed using the mapping tuple (voci_map, source_doc), if specified.
        The default value (0) is assigned to leaf if the mapping tuple is not specified.
        """
        super(BudgetTreeDict, self).__init__(*args, **kwargs)

        self.logger = kwargs.get('logger', None)


    def add_leaf(self, breadcrumbs, default_val = 0):
        """
        Add a leaf to the tree, starting from the breadcrumbs list.
        Creates the needed nodes in the process.

        The default value of the list can be specified in the arguments.
        """

        # copy breadcrumbs and remove last elements if empty
        bc = breadcrumbs[:]
        while not bc[-1]:
            bc.pop()

        current_node = self
        for item in bc:
            if item not in current_node:
                if bc[-1] == item:
                    current_node[item] = default_val
                    return
                else:
                    current_node[item] = OrderedDict()
            current_node = current_node[item]


    @abc.abstractmethod
    def build_tree(self, leaves, mapping=None):
        """
        Builds a BudgetTreeDict, out of the leaves.
        Can be passed an optional mapping argument, to map the leaves to an original tree,
        where values can be computed.

        :
        * :leaves:  - the list of leaves, each expressed as a breadcrumbs sequence
        * :mapping: - a tuple, containing the map to the original values
        """

    def _get_value(self, voce_match, normalized_doc, col_idx=None, interventi_matches=()):
        """
        given the matching voce as a list of breadcrumbs,
        and the normalized couch doc,
        return a single value, from the couchdb voce subtree
        :voce_match:
        :normalized_doc:
        :col_idx:            - integer, representing the column index to fetch (optional)
        :interventi_matches: - tuple of interventi to lookup to build the returning value (optional)

        this method returns an integer
        """
        tipo = voce_match[0]
        if normalized_doc[tipo] == {}:
            raise SubtreeIsEmpty(u"Could not find [{}] in source doc [{}]".format(
                tipo, normalized_doc.get('_id')
            ))

        quadro = "{:02d}".format(int(voce_match[1]))


        if quadro not in normalized_doc[tipo]:
            raise SubtreeDoesNotExist(u"Missing quadro [{0}] for [{1}]".format(
                quadro, tipo
            ))
        normalized_quadro = normalized_doc[tipo][quadro]

        titolo = voce_match[2]
        if titolo not in normalized_quadro:
            raise TitoloNotFound(u"'{}','{}'- titolo:'{}' not found".format(
                tipo, quadro,titolo
            ))
        normalized_titolo = normalized_quadro[titolo]

        voce = voce_match[3]
        if voce not in normalized_titolo['data']:
            # if voce is not found in the normalized data dict then tries to get the data using a
            # dict with lowercase keys and using a lower case voce name.
            # this way is the voce is "TEST" and the key in normalized_titolo['data'] is "test"
            # the match will be found

            import string
            normalized_titolo_lowercase = dict(zip(map(string.lower,normalized_titolo['data'].keys()),normalized_titolo['data'].values()))
            voce_lowercase = voce.lower()
            if voce_lowercase not in normalized_titolo_lowercase:
                raise VoceNotFound(u"'{}','{}','{}'- voce:'{}' not found ".format(
                    tipo, quadro, titolo, voce
                ))
            else:
                normalized_voce = normalized_titolo_lowercase[voce_lowercase]
                normalized_voce_columns = normalized_titolo['meta']['columns']
        else:
            normalized_voce = normalized_titolo['data'][voce]
            normalized_voce_columns = normalized_titolo['meta']['columns']


        # value extraction (or computation)
        if interventi_matches:
            # interventi_matches being not null signals
            # that the value must be computed for an interventi node
            ret = 0
            if len(normalized_voce_columns) == 1 and 'Dati' in normalized_voce_columns:
                # 2003-2007: budgets have a simple data structure
                col_idx = -1

                if normalized_voce[col_idx] != '':
                    ret = int(round(float(normalized_voce[col_idx].replace('.', '').replace(',','.'))))
            else:
                # 2008-*: budgets
                # value is the sum of the matching interventi
                for interventi_match in interventi_matches:
                    try:
                        col_idx = normalized_voce_columns.index(interventi_match)
                    except ValueError:
                        continue
                    if normalized_voce[col_idx] != '':
                        ret += int(round(float(normalized_voce[col_idx].replace('.', '').replace(',','.'))))
        else:
            # value computed for a function or other sections
            #
            # if the column index is not specified, fetch the last value
            # - when there is more than one column, the last value is usually the total
            # - when there is only one value, that's the last one, too
            if col_idx is None:
                col_idx = -1
            try:
                ret = int(round(float(normalized_voce[col_idx].replace('.', '').replace(',','.'))))
            except (IndexError, ValueError):
                ret = 0

        return ret


    def _get_matching_voci(self, simplified_bc, voci_map):
        """
        Return the voci of the original normalized tree,
        matching the voce identified by the simplified breadcrumbs
        """

        # remove empty item, reverse and lowercase breadcrumbs
        bc = [i.lower() for i in simplified_bc if i][::-1]

        # fetch matches in the mapping
        voci_matches = []
        for voce_map in voci_map:
            if [i.lower() for i in voce_map[4:] if i] == bc:
                voci_matches.append(voce_map[:4])

        return voci_matches


    def _get_matching_interventi(self, simplified, map):
        """
        Return the interventi of the original normalized tree,
        matching the interventi identified by the simplified breadcrumbs
        """
        # fetch matches in the mapping
        matches = []
        for intervento_map in map:
            if intervento_map[-1].lower() == simplified.lower():
                matches.append(intervento_map[0])

        return matches

    def _emit_warning(self, message):
        if self.logger:
            self.logger.warning(message)

    def _emit_debug(self, message):
        if self.logger:
            self.logger.debug(message)




class PreventivoEntrateBudgetTreeDict(BudgetTreeDict, EntrateBudgetMixin):

    def build_tree(self, leaves, mapping=None):
        """
        Builds a BudgetTreeDict for the preventivo entrate section.

        When mapping is not passed, an empty tree (default value = 0) is built.
        """
        for source_bc in leaves:
            value = None
            if mapping:
                value = self._compute_sum(source_bc, mapping,bilancio_type='preventivo')

            # add this leaf to the tree, with the computed value
            self.add_leaf(source_bc, value)

        # allows constructs such as
        # tree = BudgetDictTree().build_tree(leaves, mapping)

        self.pop('logger')
        return self


class ConsuntivoEntrateBudgetTreeDict(BudgetTreeDict, EntrateBudgetMixin):

    def build_tree(self, leaves, mapping=None):
        """
        Builds a BudgetTreeDict for the consuntivo/entrate section.

        When mapping is not passed, an empty tree (default value = 0) is built.

        It splits the section into 4 different sub-sections.
        """
        sections = {
            'Accertamenti': 0,
            'Riscossioni in conto competenza': 1,
            'Riscossioni in conto residui': 2,
        }

        for section_name, section_idx in sections.iteritems():
            for source_bc in leaves:
                value = None
                if mapping:
                    value = self._compute_sum(source_bc, mapping, col_idx=section_idx, bilancio_type='consuntivo')

                # massage source_bc, before adding the leaf,
                # since the structure of the tree needs to consider
                # the sections
                bc = source_bc[:]
                bc.insert(1, section_name)
                # add the leaf to the tree, with the computed value
                self.add_leaf(bc, value)

            # HACK
            # compute the 'Altri proventi' value as a difference
            # between the total and the sum of the children
            # this is due to the label altri proventi being
            # repeated in the Entrate extratributarie section
            # TODO: it should be corrected at the parsing level (html2couch)
            self['ENTRATE'][section_name]['Entrate extratributarie']['Servizi pubblici']['Altri proventi'] = \
             self['ENTRATE'][section_name]['Entrate extratributarie']['Servizi pubblici']['TOTALE'] - \
             deep_sum(self['ENTRATE'][section_name]['Entrate extratributarie']['Servizi pubblici'])

        # create the Cassa section of the tree,
        # by recursively adding two other branches
        self['ENTRATE']['Cassa'] = subtree_sum(
            self['ENTRATE']['Riscossioni in conto competenza'],
            self['ENTRATE']['Riscossioni in conto residui'],
        )

        # remove logger attribute,
        # in order to avoid problems when serializing
        self.pop('logger')

        # returns self, allowing constructs such as
        # tree = BudgetDictTree().build_tree(leaves, mapping)
        return self



class PreventivoSpeseBudgetTreeDict(BudgetTreeDict, SpeseBudgetMixin):

    def build_tree(self, leaves, mapping=None):
        """
        Builds a BudgetTreeDict for the preventivo uscite section.

        When mapping is not passed, an empty tree (default value = 0) is built.
        """
        for source_bc in leaves:
            value = None
            if mapping:
                value = self._compute_sum(source_bc, mapping, bilancio_type='preventivo')

            # add this leaf to the tree, with the computed value
            self.add_leaf(source_bc, value)

        # allows constructs such as
        # tree = BudgetDictTree().build_tree(leaves, mapping)


        self.pop('logger')
        return self

class ConsuntivoRiassuntivoBudgetTreeDict(BudgetTreeDict, EntrateBudgetMixin):

    def build_tree(self, leaves, mapping=None):
        """
        Builds a BudgetTreeDict for the consuntivo riassuntivo section.

        The leaves of Riassuntivo branch are divided in two sets:
        * leaves of Gestione finanziaria
        * other leaves

        The leaves of Gestione finanziaria sub-branch are divided in three sub-sub-branches:
        * gestione totale
        * gestione residui
        * gestione competenza

        The data of each Gestione is stored in the same table but in different columns, for that
        reason the section dictionary here is used slightly differently compared to the Consuntivo Spese Budget treedict

        When mapping is not passed, an empty tree (default value = 0) is built.
        """

        self.logger.debug("Build tree for leaves:{0}".format(leaves))


        residui_mapping = {
            'iniziali': 0,
            'iniziali a': 0,
            'riscossi': 1,
            'riscossi b': 1,
            'pagati': 1,
            'pagati b': 1,
        }


        columns_mapping = {
            u'Gestione finanziaria':
                {
                'gestione residui': 0,
                'gestione competenza': 1,
                'gestione totale': 2,
                },
            u'Debito':{
                'consistenza iniziale': 0,
                'consistenza iniziale (a)': 0,
                'consistenza finale': 6,
                'consistenza finale (a+b-d-f)': 6,
                },
            u'Residui attivi':  residui_mapping,
            u'Residui passivi': residui_mapping,

        }


        ##
        #  translate tree leaves
        ##

        for source_bc in leaves:

            section_idx = None
            if source_bc[1] in columns_mapping.keys():
                section_idx = columns_mapping[source_bc[1]][source_bc[2].lower()]

            value = None
            if mapping:
                value = self._compute_sum(source_bc, mapping, col_idx=section_idx, bilancio_type='consuntivo')

            # massage source_bc, before adding the leaf,
            # since the structure of the tree needs to consider
            # the sections
            bc = source_bc[:]
            # add the leaf to the tree, with the computed value
            self.add_leaf(bc, value)


        self.pop('logger')
        return self



class ConsuntivoSpeseBudgetTreeDict(BudgetTreeDict, SpeseBudgetMixin):

    def build_tree(self, leaves, mapping=None):
        """
        Builds a BudgetTreeDict for the consuntivo/entrate section.

        When mapping is not passed, an empty tree (default value = 0) is built.

        It splits the section into 4 different sub-sections.
        """
        sections = {
            'Impegni': 0,
            'Pagamenti in conto competenza': 1,
            'Pagamenti in conto residui': 2,
        }

        for section_name, section_idx in sections.iteritems():
            for source_bc in leaves:
                value = None
                if mapping:
                    # value computation depends on the branch of the simplified tree
                    if len([i for i in source_bc if i]) > 3:
                        # q1 or q2
                        value = self._compute_sum(source_bc, mapping, section_name=section_name, bilancio_type='consuntivo')
                    else:
                        # q3 (or titles 3 and 4 and general title)
                        value = self._compute_sum(source_bc, mapping, col_idx=section_idx, bilancio_type='consuntivo')

                # massage source_bc, before adding the leaf,
                # since the structure of the tree needs to consider
                # the sections
                bc = source_bc[:]
                bc.insert(1, section_name)
                # add the leaf to the tree, with the computed value
                self.add_leaf(bc, value)


            # HACK
            # compute and add the 'Altro' leaf in the funzioni subtotals
            # when there is a substantial difference between the total and the sum
            for tipo_spese in ('Spese correnti', 'Spese per investimenti'):
                funzioni = self['SPESE'][section_name][tipo_spese]['funzioni']
                for funzione, subtotals in funzioni.items():
                    if isinstance(subtotals, OrderedDict) and 'TOTALE' in subtotals:
                        remainder = subtotals['TOTALE'] - sum(v for k,v in subtotals.items() if k != 'TOTALE')
                        if remainder > 0:
                            altro_bc = ('SPESE', section_name, tipo_spese, 'funzioni', funzione, 'Altro')
                            self.add_leaf(altro_bc, remainder)

                            # warn if remainder is greater than 50% of the total
                            if remainder/float(subtotals['TOTALE']) > 0.5:
                                self.logger.debug(
                                    "/".join(altro_bc) +
                                    ": altro {0:.0f}% of {1}".format(
                                        (100.*remainder/float(subtotals['TOTALE'])), subtotals['TOTALE']
                                    )
                                )



        # create the Cassa section of the tree,
        # by recursively adding two other branches
        self['SPESE']['Cassa'] = subtree_sum(
            self['SPESE']['Pagamenti in conto competenza'],
            self['SPESE']['Pagamenti in conto residui'],
        )

        # remove logger attribute,
        # in order to avoid problems when serializing
        self.pop('logger')

        # returns self, allowing constructs such as
        # tree = BudgetDictTree().build_tree(leaves, mapping)
        return self
