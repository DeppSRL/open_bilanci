from collections import OrderedDict
from itertools import groupby
import logging
from optparse import make_option
from django.conf import settings
from django.core.management import BaseCommand
from bs4 import BeautifulSoup
from bilanci.utils.comuni import FLMapper
from bilanci.models import CodiceVoce, ValoreBilancio, Voce
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

    logger = logging.getLogger('management')
    comuni_dicts = {}
    territorio = None
    tipo_certificato = None
    anno = None
    xml_colonne_regroup = None
    popolazione_residente = None

    def import_bilancio(self, soup, popolazione_residente, dryrun):

        ##
        # CodiceVoce: get all elements for anno, tipo_certificato
        ##
        codici = CodiceVoce.get_bilancio_codes(anno=int(self.anno), tipo_certificato=self.tipo_certificato)
        codici_keygen = lambda x: (x.voce.slug)
        codici_regroup = dict((k,list(v)) for k,v in groupby(codici, key=codici_keygen))

        for voce_slug, codice_list in codici_regroup.iteritems():
            xml_code_found = True
            self.logger.info("Getting data for {0}".format(voce_slug))

            valore_totale = 0
            # adds up all the xml codice needed to calculate a single voce
            for codice in codice_list:
                if (codice.quadro_cod, codice.voce_cod, codice.colonna_cod) not in self.xml_colonne_regroup.keys():
                    self.logger.error("Code {0}-{1}-{2} not found in XML file! Cannot compute {3} Voce".\
                        format(codice.quadro_cod, codice.voce_cod, codice.colonna_cod, voce_slug))
                    xml_code_found = False
                    break

                valore_string = unicode(self.xml_colonne_regroup[(codice.quadro_cod, codice.voce_cod, codice.colonna_cod)]['valore'])
                if valore_string.lower() != 's' and valore_string.lower() != 'n':
                    valore_totale += float(valore_string)


            if xml_code_found:
                self.logger.info("Write {0}:{1} on db".format(voce_slug, valore_totale))
                vb = ValoreBilancio()
                vb.voce = Voce.objects.get(slug = voce_slug)
                vb.anno = int(self.anno)
                vb.territorio = self.territorio
                vb.valore = valore_totale

                if popolazione_residente is not None:
                    vb.valore_procapite = valore_totale/float(popolazione_residente)

                if not dryrun:
                    vb.save()



        return

    def import_context(self, soup, dryrun):

        popolazione_residente = self.xml_colonne_regroup[('01','001','1')]['valore']

        try:
            contesto_db = Contesto.objects.get(anno = self.anno, territorio = self.territorio)

        except ObjectDoesNotExist:
            new_contesto = Contesto()
            new_contesto.anno = self.anno
            new_contesto.territorio = self.territorio
            new_contesto.bil_popolazione_residente = popolazione_residente

            if not dryrun:
                new_contesto.save()
        else:

            if contesto_db.bil_popolazione_residente != popolazione_residente:
                self.logger.error("Popolazione residente in xml file ({0}) != pop.residente stored in db ({1})".\
                    format(contesto_db.bil_popolazione_residente, popolazione_residente))

        return popolazione_residente


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
        input_file = options['input_file']
        popolazione_residente = None

        if options['append'] is True:
            self.logger = logging.getLogger('management_append')

        # open input file
        try:
            soup = BeautifulSoup(open(input_file),"xml")
        except IOError:
            self.logger.error("File {0} not found".format(input_file))
            return

        # get finloc, year, tipo bilancio
        certificato = soup.certificato
        self.anno = certificato['anno']
        tipo_certificato_code = certificato['tipoCertificato']

        valuta = certificato['tipoValuta']
        if valuta.lower() != 'e':
            self.logger.error("Valuta is not EURO")
            return

        if tipo_certificato_code == "C":
            self.tipo_certificato = 'consuntivo'
        else:
            self.tipo_certificato = 'preventivo'

        # identifies the Comune from the finloc code
        codiceente = certificato['codiceEnte']
        mapper = FLMapper(settings.LISTA_COMUNI_PATH)
        codfinloc = mapper.get_cities(codiceente)[0]
        self.territorio = Territorio.objects.get(cod_finloc = codfinloc)
        self.logger.info(u"Comune: {0}".format(self.territorio.cod_finloc))

        ##
        # XML file: get all colonna elements and creates a xml codes map
        ##

        colonne_xml = soup.find_all('colonne')
        colonne_list = []
        for colonne_element in colonne_xml:

            for colonna_element in colonne_element.contents:
                if colonna_element != u'\n':

                    colonne_list.append({
                        'voce':colonna_element.parent['voce'],
                        'quadro':colonna_element.parent['quadro'],
                        'colonna': colonna_element['num'],
                        'valore': colonna_element.contents[0]
                        })

        colonne_list_keygen = lambda x: (x['quadro'], x['voce'], x['colonna'])
        self.xml_colonne_regroup = dict((k,list(v)[0]) for k,v in groupby(colonne_list, key=colonne_list_keygen))


        if self.tipo_certificato == 'consuntivo':
            # import territorio context data from xml file and set self.popolazione_residente
            popolazione_residente = self.import_context(soup, dryrun)
        else:
            try:
                contesto_db = Contesto.objects.get(anno = self.anno, territorio = self.territorio)
            except ObjectDoesNotExist:
                self.logger.warning(u"Context not present for territorio {0} year {1}, cannot compute per capita values!".format(
                    self.territorio.denominazione, self.anno
                ))
            else:
                popolazione_residente = contesto_db.bil_popolazione_residente

        # import bilancio data into Postgres db, calculate per capita values
        self.import_bilancio(soup, popolazione_residente, dryrun)