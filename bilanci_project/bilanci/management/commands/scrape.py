# -*- coding: utf-8 -*-
from pprint import pprint
from django.core.management.base import BaseCommand, CommandError
import logging
from bs4 import BeautifulSoup
import requests
from slugify import slugify
from bilanci.utils import UnicodeDictReader
from bilanci.settings.base import LISTA_COMUNI_PATH,START_YEAR, END_YEAR, URL_CONSUNTIVI,URL_PREVENTIVI

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
            #scrape table
            table = options['table']
            titolo = None
            sottotitolo=None

            # cerca il titolo
            for previous_element in table.previous_elements:
                if previous_element.name == "div" and previous_element.get('class'):
                    if previous_element.get('class')[0]=='acentro':
                        contents=previous_element.contents
                        if len(contents)==2:
                            titolo = previous_element.contents[1].text.replace("(gli importi sono espressi in euro)",'')
                            break

            # cerca il sottotitolo
            caption = table.find("caption")
            if caption:
                sottotitolo = caption.text.strip()


            # print "titolo:"+titolo
            # print "sottotitolo:"+sottotitolo
            slug = slugify(titolo+"-"+sottotitolo)
            print slug

        return

    def scrape_bilancio(self, *args, **options):
        # crea la struttura dati e fa lo scraping di ogni quadro
        data = {}
        if options['url'] is not None:
            url_list = options['url']
            for quadro,url in url_list.items():
                self.logger.info(msg="Scrape quadro:%s"%(quadro,))
                soup = BeautifulSoup(requests.get(url).text)
                # non considera la prima tabella (con i dati riassuntivi del comune)
                # e le ultime due: l'indice delle pagine e una tabella vuota
                considered_tables = soup.findAll("table")[1:-2]

                for table in considered_tables:
                    data[quadro]=self.scrape_table(table=table)
                pass

        return data


    def handle_scrape(self, *args, **options):
        # scrapes bilanci data and stores them in the DB
        # initialize start_urls with all comune codes, years and type of bilancio
        udr = None
        lista_comuni = []
        scrape_list = {}
        anni_considerati = range(START_YEAR, END_YEAR)
        quadri_considerati = ['02','03','04','05']
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
                    url_prev[quadro]=URL_PREVENTIVI % (comune['CODICE_COMUNE'],anno, quadro)
                    url_cons[quadro]=URL_CONSUNTIVI % (comune['CODICE_COMUNE'],anno, quadro)

                scrape_list[anno][comune["NOME_COMUNE"]+"--"+comune['CODICE_COMUNE']]['P']['url'] = url_prev
                scrape_list[anno][comune["NOME_COMUNE"]+"--"+comune['CODICE_COMUNE']]['C']['url'] = url_cons

                scrape_list[anno][comune["NOME_COMUNE"]+"--"+comune['CODICE_COMUNE']]['P']['data'] = {}
                scrape_list[anno][comune["NOME_COMUNE"]+"--"+comune['CODICE_COMUNE']]['C']['data'] = {}


        self.logger.info("Start scraping")

        for anno_key, anno_obj in scrape_list.items():

            self.logger.info("Scraping year: "+str(anno_key))
            for comune_key, comune_obj in anno_obj.items():
                self.logger.info("Scraping Comune: "+str(comune_key))
                #scrape consuntivo
                comune_obj['P']['data']=self.scrape_bilancio(url=comune_obj['P']['url'])
                #scrape preventivo
                comune_obj['C']['data']=self.scrape_bilancio(url=comune_obj['C']['url'])






