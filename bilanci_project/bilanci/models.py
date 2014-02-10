import abc

class SubtreeIsEmpty(Exception):
    pass

class SubtreeDoesNotExist(Exception):
    pass

class BudgetTreeDict(dict):

    """
    An Abstract Base Class, representing the simplified BudgetTree.

    Extends the standard dict and can be serialized as json and exported to couchdb.

    It MUST be subclassed by dedicated classes:
    - PreventivoBudgetTreeDict,
    - ConsuntivoEntrateBudgetTreeDict,
    - ConsuntivoUsciteBudgetTreeDict

    Every sub-tree is built according to a slightly different logic.
    """

    __metaclass__  = abc.ABCMeta

    def __init__(self, *args, **kwargs):
        """
        Build and return a BudgetTreeDict object, out of a list of items.
        Each item is a sequence of paths.

        Leaf values are computed using the mapping tuple (voci_map, source_doc), if specified.
        The default value (0) is assigned to leaf if the mapping tuple is not specified.
        """
        super(BudgetTreeDict, self).__init__(*args, **kwargs)


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
    def build_tree(self, leaves, mapping=None, logger=None):
        """
        Builds a BudgetTreeDict, out of the leaves.
        Can be passed an optional mapping argument, to map the leaves to an original tree,
        where values can be computed.

        :
        * :leaves:  - the list of leaves, each expressed as a breadcrumbs sequence
        * :mapping: - a tuple, containing the map to the original values
          * :mapping[0]: - the mapping between old and new couchdb tree
          * :mapping[1]: - the old couchdb document (where to read values)

        """


    def _compute_sum(self, simplified_bc, voci_map, normalized_doc, col_idx=None, logger=None):
        """
        Compute the sum of all voices in the normalized budget doc (source)
        that corresponds to the simplified voice (destination)
        according to the voci_map mapping.

        :simplified_bc:  - the simplified destination tree, as breadcrumbs
        :voci_map:       - the mapping between source and destination voices
        :normalized_doc: - the couchdb source document,
        :col_idx:        - integer, representing the column index to fetch (optional)
        :logger:         - the logging.Logger instance used for logging purposes (optional)

        the method always returns a scalar value
        """
        ret = 0

        # get all voices in mormalized tree, matching the voce in simplified tree
        voci_matches = self._get_matching_voci(simplified_bc, voci_map)
        if not voci_matches:
            self._emit_warning(u"No matching voci found for: {0}.".format(
                simplified_bc
            ), logger)


        # compute the sum of the matching voices
        for voce_match in voci_matches:

            tipo = voce_match[0]
            if normalized_doc[tipo] == {}:
                raise SubtreeIsEmpty(u"[{0}] has no content (missing from source)".format(
                    tipo
                ))

            quadro = "{:02d}".format(int(voce_match[1]))


            if quadro not in normalized_doc[tipo]:
                raise SubtreeDoesNotExist(u"Missing quadro [{0}] for [{1}]".format(
                    quadro, tipo
                ))
            normalized_quadro = normalized_doc[tipo][quadro]

            titolo = voce_match[2]
            if titolo not in normalized_quadro:
                self._emit_debug(u"Titolo [{0}] not found for [{1}], quadro [{2}].".format(
                    titolo, tipo, quadro
                ), logger)
                continue
            normalized_titolo = normalized_quadro[titolo]

            voce = voce_match[3]
            if voce not in normalized_titolo['data']:
                self._emit_debug(u"Voce [{0}] not found for [{1}], quadro [{2}], titolo [{3}].".format(
                    voce, tipo, quadro, titolo
                ), logger)
                continue
            normalized_voce = normalized_titolo['data'][voce]

            if len(normalized_voce) == 1:
                val = normalized_voce[0]
                ret += int(val.replace(',00', '').replace('.',''))
            else:
                if col_idx is None:
                    self._emit_warning(u"More than one value found for tipo: [{0}], quadro [{1}], titolo [{2}], voce [{3}].".format(
                        tipo, quadro, titolo, voce
                    ), logger)
                else:
                    val = normalized_voce[col_idx]
                    ret += int(val.replace(',00', '').replace('.',''))

        return ret


    def _get_matching_voci(self, simplified_bc, voci_map, logger=None):
        """
        Return the voci of the original normalized tree,
        matching the voce identified by the simplified breadcrumbs
        """

        # reverse and lowercase breadcrumbs
        bc = [i.lower() for i in simplified_bc][::-1]

        # fetch matches in the mapping
        voci_matches = []
        for voce_map in voci_map:
            if [i.lower() for i in voce_map[-4:]] == bc:
                voci_matches.append(voce_map[:4])

        return voci_matches

    def _emit_warning(self, message, logger=None):
        if logger:
            logger.warning(message)

    def _emit_debug(self, message, logger=None):
        if logger:
            logger.debug(message)



class PreventivoBudgetTreeDict(BudgetTreeDict):

    def build_tree(self, leaves, mapping=None, logger=None):
        """
        Builds a BudgetTreeDict for the consuntivo/entrate section.
        """
        for source_bc in leaves:
            value = None
            if mapping:
                (voci_map, source_doc) = mapping
                value = self._compute_sum(source_bc, voci_map, source_doc, logger)

            # add this leaf to the tree, with the computed value
            self.add_leaf(source_bc, value)

        # allows constructs such as
        # tree = BudgetDictTree().build_tree(leaves, mapping)
        return self




class ConsuntivoEntrateBudgetTreeDict(BudgetTreeDict):

    def build_tree(self, leaves, mapping=None, logger=None):
        """
        Builds a BudgetTreeDict for the consuntivo/entrate section.

        It splits the section into 4 different sub-sections.
        """
        sections = {
            'Accertamenti': 0,
            'Riscossioni in conto competenza': 1,
            'Riscossioni in conto residui': 2,
#            'Cassa': '1+2'
        }

        for section_name, section_idx in sections.iteritems():
            for source_bc in leaves:
                value = None
                if mapping:
                    (voci_map, source_doc) = mapping
                    value = self._compute_sum(source_bc, voci_map, source_doc, logger=logger, col_idx=section_idx)

                # massage source_bc, before adding the leaf,
                # since the structure of the tree needs to consider
                # the sections
                bc = source_bc[:]
                bc.insert(1, section_name)
                # add the leaf to the tree, with the computed value
                self.add_leaf(bc, value)

        # allows constructs such as
        # tree = BudgetDictTree().build_tree(leaves, mapping)
        return self
