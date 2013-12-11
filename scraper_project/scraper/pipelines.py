# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
from pprint import pprint
from items import BilanciPageItem



class BilanciPagesPipeline(object):
    def process_item(self,item,spider):
        if isinstance(item, BilanciPageItem):
            # scrive il file contenente la pagina nella directory assegnata.
            # se non esiste la directory la crea
            pprint(item)


        return item