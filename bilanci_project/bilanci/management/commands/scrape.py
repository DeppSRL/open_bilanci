# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
import logging
from bs4 import BeautifulSoup
import requests
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



    def handle_scrape(self, *args, **options):
        # scrapes bilanci data and stores them in the DB
        # initialize start_urls with all comune codes, years and type of bilancio
        udr = None
        lista_comuni = []
        scrape_urls = []
        anni_considerati = range(START_YEAR, END_YEAR)
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
            for comune in lista_comuni:
                url_prev =URL_PREVENTIVI % (comune['CODICE_COMUNE'],anno)
                url_cons =URL_CONSUNTIVI % (comune['CODICE_COMUNE'],anno)
                scrape_urls.append(url_prev)
                scrape_urls.append(url_cons)

        print "here"

        for url in scrape_urls:
            r  = requests.get(url)
            data = r.text

            soup = BeautifulSoup(data)

            for link in soup.find_all('a'):
                print(link.get('href'))

        self.logger.info("Inizio scraping")


