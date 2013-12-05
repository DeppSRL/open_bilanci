import pprint
from scrapy.selector import Selector
from scrapy.spider import BaseSpider
from utils import UnicodeWriter, UnicodeDictReader
from slugify import slugify
from scrapy import log
from ..settings import LISTA_COMUNI_PATH,LOGFILE_PATH


class ListaComuniSpider(BaseSpider):
    name = "listacomuni"
    allowed_domains = ["http://finanzalocale.interno.it"]
    start_urls = [
        "http://finanzalocale.interno.it/apps/floc.php/ajax/searchComune/",
    ]


    def parse(self, response):

        uw = UnicodeWriter(f=open(LISTA_COMUNI_PATH,mode='w'), dialect="excel_quote_all")
        hxs = Selector(response)

        comuni = hxs.xpath("//li/@onclick")
        # gets a set of strings like these
        # fillEnte('ZUGLIO','2060851360');

        # writes the header
        header = ["NOME_COMUNE","CODICE_COMUNE"]
        uw.writerow(header)
        for comune in comuni:

            comune_string = comune.extract()
            # transforms to => ZUGLIO','2060851360
            comune_string = comune_string[10:len(comune_string)-3]
            nome_comune = comune_string.split(u"','")[0]
            codice_comune = comune_string.split(u"','")[1]
            row_comune = [slugify(nome_comune).upper(),codice_comune]
            uw.writerow(row_comune)

            # ZUGLIO:2060851360



        return

class BilancioSpider(BaseSpider):
    name = "bilancio"
    allowed_domains = ["http://finanzalocale.interno.it"]
    start_urls = ["http://finanzalocale.interno.it",]
    lista_comuni = []



    def __init__(self,**kwargs):

        super(BilancioSpider, self).__init__(self.name, **kwargs)

        # initialize start_urls with all comune codes, years and type of bilancio
        udr = None
        try:
            udr = UnicodeDictReader(f=open(LISTA_COMUNI_PATH,mode='r'), dialect="excel_quote_all",)
        except IOError:

            print "Impossible to open the file: %s.Closing the spider..." % LISTA_COMUNI_PATH
            return


        # get comuni name and code from lista comuni
        # for row in udr:
        #     self.lista_comuni.append(row)

        # get list of considered years
        anni_considerati = range(2002, 2012)
        return



    def parse(self, response):






        return None