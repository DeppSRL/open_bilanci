# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

from scrapy.item import Item, Field

class ScraperProjectItem(Item):
    # define the fields for your item here like:
    # name = Field()
    pass

class BilanciPageItem(Item):
    body = Field()
    # codice ente
    comune = Field()
    # anno
    anno = Field()
    # preventivo o consuntivo
    tipologia = Field()
    # numero quadro
    quadro = Field()

