# -*- coding: utf-8 -*-
from pprint import pprint
from django.core.management.base import BaseCommand, CommandError
import logging
from bs4 import BeautifulSoup
import requests
from slugify import slugify
from bilanci.utils import UnicodeDictReader
from bilanci.settings.base import LISTA_COMUNI_PATH,START_YEAR, END_YEAR, URL_CONSUNTIVI_QUADRI,URL_PREVENTIVI_QUADRI
import couchdb

class Command(BaseCommand):

    help = 'Scrape bilanci data and store them into DB'

    encoding = 'utf8'
    #    encoding='latin1'
    logger = logging.getLogger('management')
    unicode_reader = None


    def handle(self, *args, **options):
        self.handle_scrape(*args, **options)


    def scrape_table(self,*args,**options):
        if options['table'] is not None:
            #scraped table
            table_html = options['table']
            # data struct to return
            table_data={'meta':{'titolo':None,'sottotitolo':None,'columns':[]},'data':{}}

            # cerca il titolo
            for previous_element in table_html.previous_elements:
                if previous_element.name == "div" and previous_element.get('class'):
                    if previous_element.get('class')[0]=='acentro':
                        contents=previous_element.contents
                        if len(contents)==2:
                            table_data['meta']['titolo'] = previous_element.contents[1].text.replace("(gli importi sono espressi in euro)",'').strip(' \t\n\r')
                            break

            # cerca il sottotitolo
            caption = table_html.find("caption")
            if caption:
                table_data['meta']['sottotitolo'] = caption.text.strip(' \t\n\r')

            # prende la prima riga della tabella, che descrive le colonne
            for th in table_html.findAll("th"):
                if th.text.lower() != "voci":
                    table_data['meta']['columns'].append(th.text.strip(' \t\n\r'))

            # prende i dati dalla tabella
            for tr in table_html.findAll("tr"):
                row_key=None
                for (col_counter,td) in enumerate(tr.findAll("td")):
                    if col_counter == 0 :
                        row_key = td.text.strip(' \t\n\r')
                        table_data['data'][row_key]=[]

                    else:
                        table_data['data'][row_key].append(td.text.strip(' \t\n\r'))


            slug = ''
            if table_data['meta']['titolo']:
                slug = slug + table_data['meta']['titolo']
            if table_data['meta']['sottotitolo']:
                slug = slug + table_data['meta']['sottotitolo']


            return {'slug':slugify(slug),'data':table_data}


    def scrape_bilancio(self, *args, **options):
        # crea la struttura dati e fa lo scraping di ogni quadro
        data = {}
        if options['url'] is not None:
            url_list = options['url']
            for quadro,url in url_list.items():
                data[quadro]={}
                self.logger.info(msg="Scraping quadro:%s"%(quadro,))
                soup = BeautifulSoup(requests.get(url).text)
                # non considera la prima tabella (con i dati riassuntivi del comune)
                # e le ultima: l'indice delle pagine
                considered_tables = soup.findAll("table")[1:-1]
                for table in considered_tables:
                    return_value = self.scrape_table(table=table)
                    data[quadro][return_value['slug']]=return_value['data']


        return data


    def handle_scrape(self, *args, **options):
        # scrapes bilanci data and stores them in the DB
        # initialize start_urls with all comune codes, years and type of bilancio
        udr = None
        lista_comuni = []
        scrape_list = {}
        anni_considerati = range(START_YEAR, END_YEAR)
        quadri_considerati = ['01','02','03','04','05']
        couch_server = couchdb.Server()
        bilanci_db = couch_server['bilanci']
        try:
            udr = UnicodeDictReader(f=open(LISTA_COMUNI_PATH,mode='r'), dialect="excel_quote_all",)
        except IOError:
            self.logger.error(msg="Impossible to open the file:%s"%LISTA_COMUNI_PATH)
            return

        # get comuni name and code from lista comuni
        for row in udr:
            lista_comuni.append(row)

        # creates the start urls list
        # per ogni comune, per ogni anno considerato, i quadri considerati di prev. e cons.
        for anno in anni_considerati:
            scrape_list[anno] = {}
            for comune in lista_comuni:
                url_prev={}
                url_cons={}
                scrape_list[anno][comune["NOME_COMUNE"]+"--"+comune['CODICE_COMUNE']]={}
                scrape_list[anno][comune["NOME_COMUNE"]+"--"+comune['CODICE_COMUNE']]['P']={}
                scrape_list[anno][comune["NOME_COMUNE"]+"--"+comune['CODICE_COMUNE']]['C']={}

                for quadro in quadri_considerati:
                    url_prev[quadro]=URL_PREVENTIVI_QUADRI % (comune['CODICE_COMUNE'],anno, quadro)
                    url_cons[quadro]=URL_CONSUNTIVI_QUADRI % (comune['CODICE_COMUNE'],anno, quadro)

                scrape_list[anno][comune["NOME_COMUNE"]+"--"+comune['CODICE_COMUNE']]['P']['url'] = url_prev
                scrape_list[anno][comune["NOME_COMUNE"]+"--"+comune['CODICE_COMUNE']]['C']['url'] = url_cons

                scrape_list[anno][comune["NOME_COMUNE"]+"--"+comune['CODICE_COMUNE']]['P']['data'] = {}
                scrape_list[anno][comune["NOME_COMUNE"]+"--"+comune['CODICE_COMUNE']]['C']['data'] = {}


        self.logger.info("Start scraping")

        for anno_key, anno_obj in scrape_list.items():

            self.logger.info("Scraping year: "+str(anno_key))
            for comune_key, comune_obj in anno_obj.items():
                self.logger.info("Scraping Comune: "+str(comune_key))

                self.logger.info("Scraping preventivo")
                preventivo=self.scrape_bilancio(url=comune_obj['P']['url'])

                self.logger.info("Scraping consuntivo: "+comune_obj['C']['url']['03'])
                consuntivo=self.scrape_bilancio(url=comune_obj['C']['url'])

                bilancio_id = "{0}_{1}".format(anno_key,comune_key)
                bilancio_data = {'preventivo':preventivo,'consuntivo':consuntivo}
                # se esiste l'oggetto lo aggiorna, se no lo aggiunge
                if bilanci_db[bilancio_id]:
                    bilancio_data['_rev']=bilanci_db[bilancio_id].rev

                bilanci_db[bilancio_id]=bilancio_data




