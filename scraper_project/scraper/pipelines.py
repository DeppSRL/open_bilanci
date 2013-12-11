# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
from pprint import pprint

class ScraperProjectPipeline(object):
    def process_item(self, item, spider):
        return item

class BilanciPagesPipeline(object):
    def process_item(self,item,spider):
        # scrive il file contenente la pagina nella directory assegnata.
        # se non esiste la directory la crea
        pprint(item)


        return