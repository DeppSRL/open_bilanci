# -*- coding: utf-8 -*-
__author__ = 'guglielmo'

import abc


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

    def _compute_sum(self, simplified_bc, mapping, col_idx=None):
        """
        Compute the sum of all voices in the normalized budget doc (source)
        that corresponds to the simplified voice (destination)
        according to the voci_map mapping.

        :simplified_bc:  - the simplified destination tree, as breadcrumbs
        :mapping:        - the mapping parameters, grouped
          :voci_map:       - the mapping between source and destination voices
          :normalized_doc: - the couchdb source document,
        :col_idx:        - if integer, representing the column index to fetch (optional)
                           if a string, the sum of the indexes

        the method always returns a scalar value
        """
        ret = 0

        (voci_map, normalized_doc) = mapping


        # get all voices in mormalized tree, matching the voce in simplified tree
        voci_matches = self._get_matching_voci(simplified_bc, voci_map)
        if not voci_matches:
            self._emit_warning(u"No matching voci found for: {0}.".format(
                simplified_bc
            ))


        # compute the sum of the matching voices
        for voce_match in voci_matches:
            try:
                if isinstance(col_idx, str):
                    idxs = col_idx.split('+')
                    val = 0
                    for idx in idxs:
                        val += self._get_value(voce_match, normalized_doc, col_idx=int(idx))
                else:
                    val = self._get_value(voce_match, normalized_doc, col_idx=col_idx)
            except (MultipleValueFoundException, SubtreeDoesNotExist, SubtreeIsEmpty) as e:
                self._emit_warning(e.message)
                continue
            except (TitoloNotFound, VoceNotFound) as e:
                self._emit_debug(e.message)
                continue

            ret += val

        return ret


class SpeseBudgetMixin(object):
    """
    Defines the _compute_sum method for the spese BudgetTrees

    MUST be subclassed along with a subclass of BudgetTreeDict
    """
    def _compute_sum(self, simplified_bc, mapping, section_name=None, col_idx=None):
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
            self._emit_warning(u"No matching voci found for: {0}.".format(
                bc
            ))

        # compute the sum of the matching voices
        for voce_match in voci_matches:

            interventi_matches = ()
            if bc[3] == 'interventi':
                # handle mapping and sum
                interventi_matches = self._get_matching_interventi(bc[4], interventi_map)
                if not interventi_matches:
                    self._emit_warning("Could not find proper mapping for [{}]".format(
                        bc[4]
                    ))

            try:
                if isinstance(col_idx, str):
                    idxs = col_idx.split('+')
                    val = 0
                    for idx in idxs:
                        val += self._get_value(voce_match, normalized_doc, col_idx=int(idx), interventi_matches=tuple(interventi_matches))
                else:
                    val = self._get_value(voce_match, normalized_doc, col_idx=col_idx, interventi_matches=tuple(interventi_matches))
            except (MultipleValueFoundException, SubtreeDoesNotExist, SubtreeIsEmpty) as e:
                self._emit_warning(e.message)
                continue
            except (TitoloNotFound, VoceNotFound) as e:
                self._emit_debug(e.message)
                continue



            ret += val

        return ret



# trees
class BudgetTreeDict(dict):

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
                    current_node[item] = {}
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
            raise TitoloNotFound(u"Titolo [{0}] not found for [{1}], quadro [{2}].".format(
                titolo, tipo, quadro
            ))
        normalized_titolo = normalized_quadro[titolo]

        voce = voce_match[3]
        if voce not in normalized_titolo['data']:
            raise VoceNotFound(u"Voce [{0}] not found for [{1}], quadro [{2}], titolo [{3}].".format(
                voce, tipo, quadro, titolo
            ))
        normalized_voce = normalized_titolo['data'][voce]
        normalized_voce_columns = normalized_titolo['meta']['columns']


        # value extraction (or computation)
        if interventi_matches:
            # value is the sum of the matching interventi's
            ret = 0
            for interventi_match in interventi_matches:
                # shift 1 position to the left, to handle the header mismatch
                try:
                    col_idx = normalized_voce_columns.index(interventi_match) - 1
                    ret += int(normalized_voce[col_idx].replace(',00', '').replace('.',''))
                except ValueError:
                    continue
        else:
            # if the column index is not specified, fetch the last value
            # - when there is more than one column, the last value is usually the total
            # - when there is only one value, that's the last one, too
            if col_idx is None:
                col_idx = -1
            ret = int(normalized_voce[col_idx].replace(',00', '').replace('.',''))

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
                value = self._compute_sum(source_bc, mapping)

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
            'Cassa': '1+2',
        }

        for section_name, section_idx in sections.iteritems():
            for source_bc in leaves:
                value = None
                if mapping:
                    value = self._compute_sum(source_bc, mapping, col_idx=section_idx)

                # massage source_bc, before adding the leaf,
                # since the structure of the tree needs to consider
                # the sections
                bc = source_bc[:]
                bc.insert(1, section_name)
                # add the leaf to the tree, with the computed value
                self.add_leaf(bc, value)

        # allows constructs such as
        # tree = BudgetDictTree().build_tree(leaves, mapping)

        self.pop('logger')
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
                value = self._compute_sum(source_bc, mapping)

            # add this leaf to the tree, with the computed value
            self.add_leaf(source_bc, value)

        # allows constructs such as
        # tree = BudgetDictTree().build_tree(leaves, mapping)

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
            'Cassa': '1+2',
        }

        for section_name, section_idx in sections.iteritems():
            for source_bc in leaves:
                value = None
                if mapping:
                    # value computation depend on the branch of the simplified tree
                    if ({'spese correnti', 'spese per investimenti'}.intersection(set([v.lower() for v in source_bc])) and
                        'TOTALE' not in [v.lower() for v in source_bc]):
                        # q1 or q2
                        value = self._compute_sum(source_bc, mapping, section_name=section_name)
                    else:
                        # q3 (or titles 3 and 4 and general title)
                        value = self._compute_sum(source_bc, mapping, col_idx=section_idx)

                # massage source_bc, before adding the leaf,
                # since the structure of the tree needs to consider
                # the sections
                bc = source_bc[:]
                bc.insert(1, section_name)
                # add the leaf to the tree, with the computed value
                self.add_leaf(bc, value)

        # allows constructs such as
        # tree = BudgetDictTree().build_tree(leaves, mapping)

        self.pop('logger')
        return self
