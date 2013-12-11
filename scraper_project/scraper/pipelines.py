# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
from pprint import pprint
from os import path, makedirs
from items import BilanciPageItem
from settings import BILANCI_PAGES_FOLDER


class BilanciPagesPipeline(object):
    def process_item(self,item,spider):
        if isinstance(item, BilanciPageItem):
            # scrive il file contenente la pagina nella directory assegnata.
            # se non esiste la directory la crea
            folder_path = BILANCI_PAGES_FOLDER+"/"+str(item['anno'])+"/"+str(item['comune'])+"/"+str(item['tipologia'])
            if not path.isdir(folder_path):
                makedirs(folder_path)


            f=open(folder_path+"/"+str(item['quadro'])+".html", 'w')
            f.write(str(item['body']))
            f.close()


        return item['comune']
