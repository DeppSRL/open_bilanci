from collections import OrderedDict
from itertools import groupby
import logging
from optparse import make_option
from django.conf import settings
from django.core.management import BaseCommand
from bs4 import BeautifulSoup
from bilanci.utils.comuni import FLMapper
from bilanci.models import CodiceVoce, ValoreBilancio, Voce
from territori.models import Territorio, ObjectDoesNotExist


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
        anno = certificato['anno']
        tipo_certificato_code = certificato['tipoCertificato']
        if tipo_certificato_code == "C":
            tipo_certificato = 'consuntivo'
        else:
            tipo_certificato = 'preventivo'

        # identifies the Comune from the finloc code
        codiceente = certificato['codiceEnte']
        mapper = FLMapper(settings.LISTA_COMUNI_PATH)
        codfinloc = mapper.get_cities(codiceente)[0]
        territorio = Territorio.objects.get(cod_finloc = codfinloc)
        self.logger.info(u"Comune: {0}".format(territorio.cod_finloc))

        ##
        # XML: get all colonna elements
        ##

        colonne_xml = soup.find_all('colonne')
        colonne_list = []
        for colonne_element in colonne_xml:
            # print "Quadro:{0} voce:{1}".format(colonne_element['quadro'], colonne_element['voce'])

            for colonna_element in colonne_element.contents:
                if colonna_element != u'\n':
                    # print "colonna n:{0} value:{1}".format(colonna_element['num'], colonna_element.string)

                    colonne_list.append({
                        'voce':colonna_element.parent['voce'],
                        'quadro':colonna_element.parent['quadro'],
                        'colonna': colonna_element['num'],
                        'valore': colonna_element.contents[0]
                        })

        colonne_list_keygen = lambda x: (x['quadro'], x['voce'], x['colonna'])
        colonne_regroup = dict((k,list(v)[0]) for k,v in groupby(colonne_list, key=colonne_list_keygen))

        ##
        # CodiceVoce: get all elements for anno, tipo_certificato
        ##
        codici = CodiceVoce.get_bilancio_codes(anno=int(anno), tipo_certificato=tipo_certificato)
        codici_keygen = lambda x: (x.voce.slug)
        codici_regroup = dict((k,list(v)) for k,v in groupby(codici, key=codici_keygen))

        for voce_slug, codice_list in codici_regroup.iteritems():
            xml_code_not_found = False
            self.logger.info("Getting data for {0}".format(voce_slug))

            valore_totale = 0
            # adds up all the xml codice needed to calculate a single voce
            for codice in codice_list:
                if (codice.quadro_cod, codice.voce_cod, codice.colonna_cod) not in colonne_regroup.keys():
                    self.logger.error("Code {0}-{1}-{2} not found in XML file! Cannot compute {3} Voce".\
                        format(codice.quadro_cod, codice.voce_cod, codice.colonna_cod, voce_slug))
                    xml_code_not_found = True
                    break
                valore_string = unicode(colonne_regroup[(codice.quadro_cod, codice.voce_cod, codice.colonna_cod)]['valore'])
                if valore_string.lower() != 's' and valore_string.lower() != 'n':
                    valore_totale += float(valore_string)


            if not xml_code_not_found and not dryrun:
                self.logger.info("Write {0}:{1} on db".format(voce_slug, valore_totale))
                vb = ValoreBilancio()
                vb.voce = Voce.objects.get(slug = voce_slug)
                vb.anno = int(anno)
                vb.territorio = territorio
                vb.valore = valore_totale
                # vb.save()

            pass




