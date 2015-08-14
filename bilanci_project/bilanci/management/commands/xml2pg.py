from collections import OrderedDict
from itertools import groupby
import logging
import os
import shutil
import pprint
from optparse import make_option
from django.conf import settings
from django.core.management import BaseCommand, call_command
from bs4 import BeautifulSoup
from bilanci.utils import gdocs
from bilanci.utils.comuni import FLMapper
from bilanci.models import CodiceVoce, ValoreBilancio, Voce, ImportXmlBilancio
from territori.models import Territorio, Contesto, ObjectDoesNotExist


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--dry-run',
                    dest='dryrun',
                    action='store_true',
                    default=False,
                    help='Set the dry-run command mode: nothing is written on the db'),
        make_option('--file',
                    dest='input_file',
                    default='',
                    help='Input Xml file to parse'),
        make_option('--append',
                    dest='append',
                    action='store_true',
                    default=False,
                    help='Use the log file appending instead of overwriting (used when launching shell scripts)'),
    )

    help = 'Import xml bilancio files into pg db'
    dryrun = None
    logger = logging.getLogger('management')
    comuni_dicts = {}
    composition_errors = []
    territorio = None
    tipo_certificato = None
    rootnode_slug = None
    anno = None
    colonne_regroup = None
    codici_regroup = OrderedDict()
    unmapped_slugs = None
    popolazione_residente = None

    def import_context(self, ):
        sep = "."
        popolazione_str = self.colonne_regroup[('01', '001', '1')]['valore']
        popolazione_residente = int(popolazione_str.split(sep, 1)[0])

        try:
            contesto_db = Contesto.objects.get(anno=self.anno, territorio=self.territorio)

        except ObjectDoesNotExist:
            new_contesto = Contesto()
            new_contesto.anno = self.anno
            new_contesto.territorio = self.territorio
            new_contesto.bil_popolazione_residente = popolazione_residente

            if not self.dryrun:
                new_contesto.save()
        else:

            if contesto_db.bil_popolazione_residente != popolazione_residente:
                self.logger.error(
                    "Popolazione residente year:{0} in xml file ({1}) != pop.residente stored in db ({2})". \
                        format(self.anno, contesto_db.bil_popolazione_residente, popolazione_residente))

        return popolazione_residente

    def set_popolazione_residente(self, ):

        if self.tipo_certificato == 'consuntivo':
            # import territorio context data from xml file and set self.popolazione_residente
            self.popolazione_residente = self.import_context()

        else:
            valid_pop_tuple = self.territorio.nearest_valid_population(year=self.anno)

            if valid_pop_tuple is None:
                self.logger.error("Nearest valid population not found for {}, try launching 'context' mng task".format(self.territorio))
                exit()

            self.popolazione_residente =  valid_pop_tuple[1]

    def log_errors(self,):
        # output composition errors, if any
        if len(self.composition_errors) > 0:

            # create a list of lists to be written with unicodewriter
            errors_to_write = [[nms] for nms in self.composition_errors]
            bilancio_type_year = u"{0}_{1}".format(self.tipo_certificato[:4], self.anno)
            composition_filename = "{0}_{1}_comp_err".format(self.territorio.slug, bilancio_type_year, )
            log_base_dir = "{0}/".format(settings.REPO_ROOT)
            gdocs.write_to_csv(path_name='log', contents={composition_filename: errors_to_write},
                               csv_base_dir=log_base_dir)
            self.logger.warning(
                "{0} VOCE SLUG FROM BILANCIO TREE GAVE COMPOSITION ERRORS ".format(len(self.composition_errors)))
            self.logger.warning("{0}log/{1}.csv file written for check".format(log_base_dir, composition_filename))
        else:
            self.logger.info("All Codes from bilancio file were inserted correctly")

    def create_mapping(self, bilancio):
        ##
        # create mapping creates a mapping for colonne: the Values of the bilancio file
        # and the CodiceVoce objects: which are the associations between codici bilancio and slug of Voce tree
        ##

        # creates a colonne mapping from the data contained in the xml file
        colonne_xml = bilancio.find_all('colonne')
        colonne_list = []
        for colonne_element in colonne_xml:

            for colonna_element in colonne_element.contents:
                if colonna_element != u'\n':
                    colonne_list.append({
                        'voce': colonna_element.parent['voce'],
                        'quadro': colonna_element.parent['quadro'],
                        'colonna': colonna_element['num'],
                        'valore': colonna_element.contents[0]
                    })

        colonne_list_keygen = lambda x: (x['quadro'], x['voce'], x['colonna'])
        self.colonne_regroup = dict((k, list(v)[0]) for k, v in groupby(colonne_list, key=colonne_list_keygen))

        ##
        # creates a mapping (codici_regroup) on CodiceVoce:
        # get all elements for anno, tipo_certificato and regroup by voce__slug
        ##

        codici = CodiceVoce.get_bilancio_codes(anno=self.anno, tipo_certificato=self.tipo_certificato)
        codici_keygen = lambda x: x.voce.slug
        self.codici_regroup = dict((k, list(v)) for k, v in groupby(codici, key=codici_keygen))

        # checks difference between mapped slugs and total tree size
        # if there are voce of the bilancio tree which are not mapped with CodiceVoce then:
        # they will be computed as sums of their direct natural children
        # NOTE: natural children are the first level children of a Voce, excluding Voce which are in computed branches
        # as CASSA branch or SOMMA-FUNZIONI branch

        natural_desc = set(
            Voce.objects.get(slug=self.tipo_certificato).get_natural_descendants().values_list('slug', flat=True))

        self.logger.debug("Codici regroup count:{0}, natural_descent_count:{1}".format(len(self.codici_regroup.keys()),
                                                                                       len(natural_desc)))
        self.unmapped_slugs = natural_desc - set(self.codici_regroup.keys())
        if len(self.unmapped_slugs) > 0:
            self.add_unmapped_voci()

        if self.tipo_certificato == 'consuntivo':
            # add cassa branch
            entrate_cassa = list(Voce.objects.get(slug='consuntivo-entrate-cassa').get_descendants(include_self=True))
            spese_cassa = list(
                Voce.objects.get(slug='consuntivo-spese-cassa').get_descendants(include_self=True).exclude(
                    slug__startswith='consuntivo-spese-cassa-spese-somma-funzioni'))
            entrate_cassa.extend(spese_cassa)

            self.add_computed_branch(node_set=entrate_cassa, is_cassa=True)

            # set somma_funzioni_ set for consuntivo
            funzioni_cassa = list(
                Voce.objects.get(slug='consuntivo-spese-cassa-spese-somma-funzioni').get_descendants(include_self=True))
            funzioni_impegni = list(
                Voce.objects.get(slug='consuntivo-spese-impegni-spese-somma-funzioni').get_descendants(
                    include_self=True))
            funzioni_cassa.extend(funzioni_impegni)
            somma_funzioni_set = funzioni_cassa
        else:
            # set somma_funzioni_ set for preventivo
            funzioni_preventivo = list(
                Voce.objects.get(slug='preventivo-spese-spese-somma-funzioni').get_descendants(include_self=True))
            somma_funzioni_set = funzioni_preventivo

        # add somma_funzioni branch
        self.add_computed_branch(node_set=somma_funzioni_set, is_cassa=False)

    def add_unmapped_voci(self):
        # add_unmapped_voci adds to self.codici_regroup the mapping for the natural Voce which dont have
        # an explicit mapping in the CodiceVoce table. Those Voce will be mapped as a sum of the values of their
        # first level natural children

        # get unmapped nodes from the slugs. Order the nodes from the leaf to the root so the script
        # adds the leaf to the mapping before the root: in this way KeyErrors are minimized
        unmapped_nodes = Voce.objects.filter(slug__in=self.unmapped_slugs).order_by('-level')

        for unmapped_node in unmapped_nodes:
            # skip riassuntivo branch, sums in that branch are not needed
            if 'consuntivo-riassuntivo' in unmapped_node.slug:
                continue

            # debug
            self.logger.debug(u"Add summed voci for:{0}".format(unmapped_node.slug))
            natural_children_slugs = unmapped_node.get_natural_children().values_list('slug', flat=True)

            children_codes = []
            for child_slug in natural_children_slugs:

                self.logger.debug(u"Natural child:{0}".format(child_slug))
                try:
                    children_codes.extend(self.codici_regroup[child_slug])
                except KeyError:
                    self.logger.warning(
                        u"Mapping missing slug:{0} could not find child key:{1}".format(unmapped_node.slug, child_slug))
                    continue

            self.codici_regroup[unmapped_node.slug] = children_codes

        return

    def add_computed_branch(self, node_set, is_cassa=False):
        # add_computed_branch (somma funzioni, cassa) to the codici regroup dict
        # to do so asks the model which are the slugs of each Voce which is a component of such node
        # EXAMPLE:
        # for Voce with slug 'consuntivo-spese-cassa-spese-correnti'
        # and is_cassa=True
        # components will be
        # 'consuntivo-spese-pagamenti-in-conto-competenza-spese-correnti' and
        # 'consuntivo-spese-pagamenti-in-conto-residui-spese-correnti'
        # so in codici_regroup for the key 'consuntivo-spese-cassa-spese-correnti'
        # the corresponding value will be
        # codici_regroup['consuntivo-spese-pagamenti-in-conto-competenza-spese-correnti'] added to
        # codici_regroup['consuntivo-spese-pagamenti-in-conto-residui-spese-correnti']

        for node in node_set:
            if is_cassa:
                composition = node.get_components_cassa()
            else:
                composition = node.get_components_somma_funzioni()

            if composition is None or len(composition) == 0:
                self.logger.error("{0} returned None for composition with is_cassa:{1}".format(node.slug, is_cassa))
                self.composition_errors.append(node.slug)
                return

            try:
                code_set = self.codici_regroup[composition[0].slug][:]
                code_set.extend(self.codici_regroup[composition[1].slug][:])
                self.codici_regroup[node.slug] = code_set

                self.logger.debug("Codeset for:{0}".format(node.slug))
                for c in code_set:
                    self.logger.debug(c)

            except KeyError:
                self.logger.error(
                    "Cannot compute {0}: slug missing in codici_regroup with is_cassa:{1}".format(node.slug, is_cassa))
                self.composition_errors.append(node.slug)
            except IndexError:
                self.logger.error(
                    "Cannot compute {0}: composition incomplete with is_cassa:{1}".format(node.slug, is_cassa))
                self.composition_errors.append(node.slug)

    def import_bilancio(self, bilancio):

        if not self.dryrun:
            # before importing new data, deletes old data, if present
            self.logger.info(u"Deleting previous values for Comune: {0}, year: {1}, tipo_bilancio: {2}...".format(
                self.territorio.denominazione, self.anno, self.tipo_certificato))
            ValoreBilancio.objects.filter(
                territorio=self.territorio,
                anno=self.anno,
                voce=Voce.objects.get(slug=self.rootnode_slug).get_descendants(include_self=True)
            ).delete()

            # delete Importxml data
            ImportXmlBilancio.objects.filter(
                territorio=self.territorio,
                anno=self.anno,
                tipologia=self.tipo_certificato
            ).delete()

        # create mapping between codici bilancio (in Google document) and voce_slug of simplified tree
        self.create_mapping(bilancio)

        self.set_popolazione_residente()

        self.logger.info("Inserting XML values into Postgres db...")
        for voce_slug, codice_list in self.codici_regroup.iteritems():
            xml_code_found = True

            # debug
            self.logger.debug(u"Getting data for {0}".format(voce_slug))

            valore_totale = 0
            # adds up all the xml codice needed to calculate a single voce
            for codice in codice_list:
                if (codice.quadro_cod, codice.voce_cod, codice.colonna_cod) not in self.colonne_regroup.keys():
                    self.logger.error(u"Code {0}-{1}-{2} not found in XML file! Cannot compute {3} Voce". \
                        format(codice.quadro_cod, codice.voce_cod, codice.colonna_cod, voce_slug))
                    xml_code_found = False
                    break

                valore_string = unicode(
                    self.colonne_regroup[(codice.quadro_cod, codice.voce_cod, codice.colonna_cod)]['valore'])
                if valore_string.lower() != 's' and valore_string.lower() != 'n':

                    # debug
                    self.logger.debug(
                        "{0}-{1}-{2}:{3}".format(codice.quadro_cod, codice.voce_cod, codice.colonna_cod,
                                                 valore_string))

                    valore_totale += float(valore_string)
                else:
                    # expecting a string representing a number, got "S" or "N" instead
                    raise Exception

            if xml_code_found:

                vb = ValoreBilancio()
                vb.voce = Voce.objects.get(slug=voce_slug)
                vb.anno = self.anno
                vb.territorio = self.territorio
                vb.valore = valore_totale

                if self.popolazione_residente is not None:
                    vb.valore_procapite = valore_totale / float(self.popolazione_residente)

                if not self.dryrun:
                    # debug
                    self.logger.debug(u"Write {0} = {1}".format(voce_slug, valore_totale))

                    vb.save()

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
        input_file_path = options['input_file']

        if options['append'] is True:
            self.logger = logging.getLogger('management_append')

        # open input file
        try:
            bilancio = BeautifulSoup(open(input_file_path), "xml")
        except IOError:
            self.logger.error("File {0} not found".format(input_file_path))
            return

        # get finloc, year, tipo bilancio
        certificato = bilancio.certificato
        self.anno = int(certificato['anno'])
        tipo_certificato_code = certificato['tipoCertificato']

        valuta = certificato['tipoValuta']
        if valuta.lower() != 'e':
            self.logger.error("Valuta is not EURO")
            return

        if tipo_certificato_code == "C":
            self.tipo_certificato = 'consuntivo'

        else:
            self.tipo_certificato = 'preventivo'

        self.rootnode_slug = self.tipo_certificato
        # identifies the Comune from the finloc code
        codiceente = certificato['codiceEnte']
        mapper = FLMapper()
        codfinloc = mapper.get_cities(codiceente)[0]

        try:
            self.territorio = Territorio.objects.get(cod_finloc=codfinloc)
            self.logger.info(u"Comune: {0}".format(self.territorio.cod_finloc))
        except ObjectDoesNotExist:
            self.logger.error(u"Comune with codfinloc:{0} is not present on DB. Quitting".format(codfinloc))
            return

        # from finloc extracts only the numeric part, removing the eventual name
        numeric_finloc = self.territorio.cod_finloc
        if "--" in numeric_finloc:
            split_finloc = numeric_finloc.split("--")
            numeric_finloc = split_finloc[1]

        # checks if Codice Voce (xml2slug mapping) is present in the DB for the current bilancio type
        if CodiceVoce.get_bilancio_codes(anno=self.anno, tipo_certificato=self.tipo_certificato).count() == 0:
            self.logger.error("Xml mapping is not present for current bilancio type. Run xml2slug command first")
            exit()
        # import bilancio data into Postgres db, calculate per capita values
        self.import_bilancio(bilancio)
        # log errors in a file, if any
        self.log_errors()
        ##
        # adds bilancio to the source table to mark this bilancio as coming from Comune xml source
        ##
        import_data = {'territorio': self.territorio, 'anno': self.anno, 'tipologia': self.tipo_certificato}
        if not self.dryrun:
            try:
                ImportXmlBilancio.objects.get(**import_data).delete()
            except ObjectDoesNotExist:
                pass

        import_bilancio = ImportXmlBilancio(**import_data)
        if not self.dryrun:
            import_bilancio.save()

        ##
        # Compute Indicators if bilancio is Consuntivo
        ##

        if self.tipo_certificato == 'consuntivo':
            self.logger.info(u"Compute indicators for Comune: {0}, year: {1}, tipo_bilancio: {2}...".format(
                self.territorio.denominazione, self.anno, self.tipo_certificato))

            if not self.dryrun:
                call_command('indicators', verbosity=2, years=str(self.anno), cities=numeric_finloc, indicators='all',
                             interactive=False)

        ##
        # Updates open data
        ##

        # copy xml file to open data folder
        xml_path = os.path.join(settings.OPENDATA_XML_ROOT, self.territorio.cod_finloc, certificato['anno'])
        destination_file = xml_path+'/'+self.tipo_certificato + ".xml"
        
        if not self.dryrun:
            if not os.path.exists(xml_path):
                os.makedirs(xml_path)

            shutil.copyfile(src=input_file_path, dst=destination_file)
        self.logger.info("Copied Xml file to {}".format(destination_file))

        self.logger.info("** Update open data zip file for {} **".format(self.territorio.denominazione))

        # updates open data zip file for considered Comune
        if not self.dryrun:
            years = "{0}-{1}".format(settings.APP_START_YEAR, settings.APP_END_YEAR)
            call_command('update_opendata', verbosity=2, years=years, cities=numeric_finloc, compress=True,
                         interactive=False)