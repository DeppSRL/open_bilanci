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

#from bilanci_project.bilanci.utils.comuni import FLMapper


class ListaComuniSpider(BaseSpider):
    name = "listacomuni"
    allowed_domains = ["http://finanzalocale.interno.it"]
    start_urls = [
        "http://finanzalocale.interno.it/apps/floc.php/ajax/searchComune/",
    ]


    def parse(self, response):

        uw = UnicodeWriter(f=open(LISTA_COMUNI_PATH,mode='w'), dialect="excel_quote_all")
        hxs = Selector(response)

        list_elements = hxs.xpath("//li")

        # writes the header
        header = ["NOME_COMUNE", "SIGLA_PROV", "CODICE_COMUNE"]
        uw.writerow(header)
        for list_element in list_elements:

            nome_provincia = list_element.xpath("text()").extract()[0]
            # nome provincia: ABANO TERME (PD)
            # sigla_provincia takes the provincia_sigla between parentesis
            sigla_provincia = nome_provincia[nome_provincia.find("(")+1:nome_provincia.find(")")]

            cod_finloc = list_element.xpath("./@onclick")
            nome_finloc = cod_finloc.extract()[0]
            # nome_finloc = fillEnte('ZUGLIO','2060851360');
            # transforms to => ZUGLIO','2060851360
            nome_finloc = nome_finloc[10:len(nome_finloc)-3]
            (nome_comune, codice_comune) = nome_finloc.split(u"','")
            row_comune = [slugify(nome_comune).upper(),sigla_provincia,codice_comune]
            uw.writerow(row_comune)

            # ZUGLIO:2060851360

        return



class BilanciPagesSpider(CrawlSpider):
    name = "bilanci_pages"
    allowed_domains = ["http://finanzalocale.interno.it",'finanzalocale.interno.it']
    start_urls = []
    lista_comuni = {}
    anni_considerati = range(START_YEAR_SPIDER, END_YEAR_SPIDER+1)
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

        # the type of bilancio can be specified in command line
        bilancio_type = ''
        if 'type' in kwargs:
            bilancio_type = kwargs.get('type').upper()

        if 'cities' in kwargs:
            # trim spaces
            cities = ",".join(map(lambda c: c.strip(), kwargs.get('cities').split(',')))

            import sys, os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__name__))))
            from bilanci_project.bilanci.utils.comuni import FLMapper

            mapper = FLMapper(LISTA_COMUNI_PATH)
            cities = mapper.get_cities(cities)
            self.lista_comuni = dict([tuple(c.split('--')[::-1]) for c in cities])
        else:
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
                self.lista_comuni[row['CODICE_COMUNE']]=row['NOME_COMUNE']


        if 'years' in kwargs:
            years = kwargs.get('years')
            if "-" in years:
                (start_year, end_year) = years.split("-")
                years = range(int(start_year), int(end_year)+1)
            else:
                years = [int(y.strip()) for y in years.split(",") if 2001 < int(y.strip()) < 2014]
            self.anni_considerati = years

        pprint(self.lista_comuni)
        pprint(self.anni_considerati)

        # creates the start urls list
        # per ogni comune, per ogni anno considerato, i quadri considerati di prev. e cons.
        # se il parametro bilancio_type non e' caratterizzato prende prev e cons
        # viceversa prende solo consuntivo o preventivo
        for anno in self.anni_considerati:
            for comune in self.lista_comuni.keys():
                if bilancio_type == 'C' or bilancio_type == '':
                    url_cons =URL_CONSUNTIVI_PRINCIPALE % (comune,anno)
                    self.start_urls.append(url_cons)
                if bilancio_type == 'P' or bilancio_type == '':
                    url_prev =URL_PREVENTIVI_PRINCIPALE % (comune,anno)
                    self.start_urls.append(url_prev)

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
        bilancio['comune'] = self.lista_comuni[splitted_url[0]]+"--"+splitted_url[0]
        bilancio['tipologia'] = preventivo_consuntivo[splitted_url[2]]
        bilancio['anno'] = splitted_url[4]
        bilancio['quadro'] = splitted_url[12]
        bilancio['body'] = response.body
        return bilancio
