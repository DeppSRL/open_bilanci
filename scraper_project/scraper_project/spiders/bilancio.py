from scrapy.selector import Selector
from scrapy.spider import BaseSpider
from utils import UnicodeWriter

class ListaComuniSpider(BaseSpider):
    name = "listacomuni"
    allowed_domains = ["http://finanzalocale.interno.it"]
    start_urls = [
        "http://finanzalocale.interno.it/apps/floc.php/ajax/searchComune/",
    ]


    def parse(self, response):

        uw = UnicodeWriter(f=open('output/listacomuni',mode='w'))
        hxs = Selector(response)

        comuni = hxs.xpath("//li/@onclick")
        # gets a set of strings like these
        # fillEnte('ZUGLIO','2060851360');
        for comune in comuni:

            comune_string = comune.extract()
            # transforms to => ZUGLIO','2060851360
            comune_string = comune_string[10:len(comune_string)-3]
            nome_comune = comune_string.split(u"','")[0]
            codice_comune = comune_string.split(u"','")[1]
            row_comune = [nome_comune,codice_comune]
            uw.writerow(row_comune)

            # ZUGLIO:2060851360



        return

class BilancioSpider(BaseSpider):
    name = "bilancio"
    allowed_domains = ["http://finanzalocale.interno.it"]
    # start_urls = [
    #     "http://finanzalocale.interno.it/apps/floc.php/certificati/index/codice_ente/4150721100/anno/2010/cod/4/md/0/tipo_modello/U"
    #         % i for i in xrange(18),
    # ]


    def parse(self, response):
        filename = response.url.split("/")[-2]
        open(filename, 'wb').write(response.body)



        return