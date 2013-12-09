import pprint
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.selector import Selector
from scrapy.spider import BaseSpider
from scrapy.contrib.spiders import CrawlSpider, Rule
from utils import UnicodeWriter, UnicodeDictReader
from slugify import slugify
from scrapy import log
from ..settings import LISTA_COMUNI_PATH,START_YEAR, END_YEAR, URL_CONSUNTIVI,URL_PREVENTIVI


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
    start_urls = []
    lista_comuni = []
    anni_considerati = range(START_YEAR, END_YEAR)
    quadri_considerati = [2,3,4,5,]



    def __init__(self,**kwargs):

        super(BilancioSpider, self).__init__(self.name, **kwargs)

        # initialize start_urls with all comune codes, years and type of bilancio
        udr = None
        try:
            udr = UnicodeDictReader(f=open(LISTA_COMUNI_PATH,mode='r'), dialect="excel_quote_all",)
        except IOError:
            log.msg(message='test',level=log.ERROR)
            # print "Impossible to open the file: %s.Closing the spider..." % LISTA_COMUNI_PATH
            return

        # get comuni name and code from lista comuni
        for row in udr:
            self.lista_comuni.append(row)

        # creates the start urls list
        # per ogni comune, per ogni anno considerato, i quadri considerati di prev. e cons.
        for anno in self.anni_considerati:
            for comune in self.lista_comuni:
                url_prev =URL_PREVENTIVI % (comune['CODICE_COMUNE'],anno)
                url_cons =URL_CONSUNTIVI % (comune['CODICE_COMUNE'],anno)
                self.start_urls.append(url_prev)
                self.start_urls.append(url_cons)
        return


    def parse(self, response):


        return None