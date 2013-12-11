from pprint import pprint
from string import split
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.selector import Selector
from scrapy.spider import BaseSpider
from scrapy.contrib.spiders import CrawlSpider, Rule
from utils import UnicodeWriter, UnicodeDictReader
from slugify import slugify
from scrapy import log
from ..settings import LISTA_COMUNI_PATH, URL_CONSUNTIVI_PRINCIPALE,URL_PREVENTIVI_PRINCIPALE, \
    START_YEAR_SPIDER,END_YEAR_SPIDER
from scraper.items import BilanciPageItem


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



class BilanciPagesSpider(CrawlSpider):
    name = "bilanci_pages"
    allowed_domains = ["http://finanzalocale.interno.it",'finanzalocale.interno.it']
    start_urls = []
    lista_comuni = []
    anni_considerati = range(START_YEAR_SPIDER, END_YEAR_SPIDER)
    quadri_considerati = []


    rules = [
        Rule(
            SgmlLinkExtractor(
                deny=[
                ],
                allow=[
                    # preventivi url
                    r"http://finanzalocale.interno.it/apps/floc.php/certificati/index/codice_ente/\d+/cod/3/anno/\d+/md/0/cod_modello/PCOU/tipo_modello/U/cod_quadro/\d+",
                    # consuntivi url
                    r"http://finanzalocale.interno.it/apps/floc.php/certificati/index/codice_ente/\d+/cod/4/anno/\d+/md/0/cod_modello/CCOU/tipo_modello/U/cod_quadro/\d+",
                ]
            ),

            callback='parse_page',
            follow=True
        ),
        ]
    encoding = 'utf8'



    def __init__(self,**kwargs):

        super(BilanciPagesSpider, self).__init__(self.name, **kwargs)

        # initialize start_urls with all comune codes, years and type of bilancio
        udr = None
        try:
            udr = UnicodeDictReader(f=open(LISTA_COMUNI_PATH,mode='r'), dialect="excel_quote_all",)
        except IOError:
            log.msg(message='Cannot open comuni lista file, quitting...',level=log.ERROR)
            print "File error:"+LISTA_COMUNI_PATH
            return

        # get comuni name and code from lista comuni
        for row in udr:
            self.lista_comuni.append(row)

        # creates the start urls list
        # per ogni comune, per ogni anno considerato, i quadri considerati di prev. e cons.
        for anno in self.anni_considerati:
            for comune in self.lista_comuni:
                url_prev =URL_PREVENTIVI_PRINCIPALE % (comune['CODICE_COMUNE'],anno)
                url_cons =URL_CONSUNTIVI_PRINCIPALE % (comune['CODICE_COMUNE'],anno)
                self.start_urls.append(url_prev)
                self.start_urls.append(url_cons)

        return


    def parse_page(self, response):

        # get comune, anno, quadro and tipologia from scraped url
        # da
        # http://finanzalocale.interno.it/apps/floc.php/certificati/index/codice_ente/4150721100/cod/4/anno/2010/md/0/cod_modello/CCOU/tipo_modello/U/cod_quadro/01
        # passa a
        # 4150721100/cod/4/anno/2010/md/0/cod_modello/CCOU/tipo_modello/U/cod_quadro/01
        preventivo_consuntivo ={
            '3':'Preventivo',
            '4':'Consuntivo',
        }

        splitted_url=split(response.url[76:],'/')
        bilancio = BilanciPageItem()
        bilancio['comune'] = splitted_url[0]
        bilancio['tipologia'] = preventivo_consuntivo[splitted_url[2]]
        bilancio['anno'] = splitted_url[4]
        bilancio['quadro'] = splitted_url[12]
        bilancio['body'] = response.body
        return bilancio