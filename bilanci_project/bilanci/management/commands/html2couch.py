import logging
from optparse import make_option
import re
from bs4 import BeautifulSoup
import couchdb
from django.core.management import BaseCommand
from django.conf import settings
from django.utils.text import slugify
import requests
import time
from bilanci.utils import UnicodeDictReader
from bilanci.utils.comuni import FLMapper

__author__ = 'guglielmo'

class Command(BaseCommand):


    option_list = BaseCommand.option_list + (
        make_option('--dry-run',
                    dest='dryrun',
                    action='store_true',
                    default=False,
                    help='Set the dry-run command mode: nothing is written in the couchdb'),
        make_option('--years',
                    dest='years',
                    default='',
                    help='Years to fetch. From 2002 to 2012. Use one of this formats: 2012 or 2003-2006 or 2002,2004,2006'),
        make_option('--cities',
                    dest='cities',
                    default='',
                    help='Cities codes or slugs. Use comma to separate values: Roma,Napoli,Torino or  "All"'),
        make_option('--base-url',
                    dest='base_url',
                    default='http://finanzalocale.mirror.openpolis.it',
                    help='Base URL for HTML files (mirror)')

    )

    help = 'Import the data for given cities and years, from HTML code into Couchdb'

    logger = logging.getLogger('management')
    comuni_dicts = {}


    def handle(self, *args, **options):
        verbosity = options['verbosity']
        if verbosity == '0':
            self.logger.setLevel(logging.ERROR)
        elif verbosity == '1':
            self.logger.setLevel(logging.WARNING)
        elif verbosity == '2':
            self.logger.setLevel(logging.INFO)
        elif verbosity == '3':
            self.logger.setLevel(logging.DEBUG)

        dryrun = options['dryrun']

        cities_codes = options['cities']
        if not cities_codes:
            raise Exception("Missing city parameter")

        mapper = FLMapper(settings.LISTA_COMUNI_PATH)
        cities = mapper.get_cities(cities_codes)
        if cities_codes.lower() != 'all':
            self.logger.info("Scraping cities: {0}".format(cities))


        years = options['years']
        if not years:
            raise Exception("Missing years parameter")

        if "-" in years:
            (start_year, end_year) = years.split("-")
            years = range(int(start_year), int(end_year)+1)
        else:
            years = [int(y.strip()) for y in years.split(",") if 2001 < int(y.strip()) < 2013]

        if not years:
            raise Exception("No suitable year found in {0}".format(years))

        self.logger.info("Scraping years: {0}".format(years))

        base_url = options['base_url']

        # setup couchdb connection
        couch_server = couchdb.Server()

        for city in cities:
            for year in years:

                # Preventivo
                q_list = ["%02d" % (i,) for i in range(1, 10)]
                url = "{0}/{1}/{2}/Preventivo".format(
                        base_url, year, city
                )
                self.logger.info("Scraping Preventivo: {0}".format(url))
                preventivo = self.scrape(
                    url,
                    pages=q_list
                )

                # Consuntivo
                q_list = ["%02d" % (i,) for i in range(1, 20)]
                q_list.append("50")
                url = "{0}/{1}/{2}/Consuntivo".format(
                    base_url, year, city
                )
                self.logger.info("Scraping Consuntivo: {0}".format(url))
                consuntivo = self.scrape(
                    url,
                    pages=q_list
                )

                # prepare global data
                bilancio_id = "{0}_{1}".format(year, city)
                bilancio_data = {
                    'anno': year,
                    'city_name': city.split("--")[0],
                    'preventivo': preventivo,
                    'consuntivo': consuntivo
                }

                if not dryrun:
                    # se non trova il db lo crea
                    if 'bilanci' not in couch_server:
                        destination_db = couch_server.create('bilanci')

                    bilanci_db = couch_server['bilanci']

                    # create or update budget data on couchdb
                    if bilancio_id in bilanci_db:
                        bilancio_data['_rev'] = bilanci_db[bilancio_id].rev

                    bilanci_db[bilancio_id] = bilancio_data
                    self.logger.info("Data written to couchdb")
                else:
                    self.logger.info("Couchdb writing skipped because of --dry-run")


    def scrape(self, path, pages=None):
        """
        Create and return data out of HTML code, for each page in pages list
        """
        data = {}
        for quadro in pages:
            data[quadro]={}
            self.logger.debug("Scraping quadro:{0}.html".format(quadro))

            soup = BeautifulSoup(
                requests.get(
                    "{0}/{1}.html".format(path, quadro)
                ).content
            )
            # non considera la prima tabella (con i dati riassuntivi del comune)
            # e le ultima: l'indice delle pagine
            considered_tables = soup.findAll("table")[1:-1]
            for table in considered_tables:
                ret = self.scrape_table(table=table)
                # ret == none se la tabella non conteneva dati
                if ret is not None:
                    data[quadro][ret['slug']] = ret['data']

            # se il quadro considerato non esiste per il bilancio in questione
            # elimina la chiave relativa al quadro dalla struttura dati
            # in questo modo evitiamo di avere dizionari vuoti nella struttura quando
            # il quadro non esiste
            if any(data[quadro]) is False:
                data.pop(quadro, None)


        return data


    def scrape_table(self,*args,**options):
        if options['table'] is not None:
            #scraped table
            table_html = options['table']
            # data struct to return
            table_data={'meta':{'titolo':None,'sottotitolo':None,'columns':[]},'data':{}}

            # cerca il titolo negli elementi precedenti la tabella

            table_counter = 0
            for previous_element in table_html.previous_elements:
                if previous_element.name == "div" and previous_element.get('class'):
                    if previous_element.get('class')[0]=='acentro':
                        contents=previous_element.contents
                        if len(contents)==2:
                            table_data['meta']['titolo'] = previous_element.contents[1].text.\
                                replace("(gli importi sono espressi in euro)",'').strip(' \t\n\r')
                            break
                elif previous_element.name == "table":
                    table_counter+=1


            if table_data['meta']['titolo'] is None:
                # creates dummy title with timestamp to avoid overwriting other tables
                dummy_title = u"Tabella-senza-titolo-"
                timestamp = unicode(time.time()).replace('.','')
                table_data['meta']['titolo'] = dummy_title+timestamp


            # cerca il sottotitolo
            caption = table_html.find("caption")
            if caption:
                table_data['meta']['sottotitolo'] = caption.text.strip(' \t\n\r')

            # prende la prima riga della tabella, che descrive le colonne
            for th in table_html.findAll("th"):
                if th.text.lower() != "voci":
                    table_data['meta']['columns'].append(th.text.strip(' \t\n\r'))

            # prende i dati dalla tabella
            # table_is_empy e' un controllo che ci permette di non salvare tabelle che non hanno nemmeno
            # un valore, solitamente si tratta di tabelle di note
            table_is_empty = True
            for tr in table_html.findAll("tr"):
                row_key=None
                for (col_counter,td) in enumerate(tr.findAll("td")):

                    if col_counter == 0 :
                        row_key = td.text.strip(' \t\n\r')
                        table_data['data'][row_key]=[]

                    else:
                        table_data['data'][row_key].append(td.text.strip(' \t\n\r'))
                        table_is_empty=False


            # crea lo slug della tabella che servira' come chiave nel dizionario dei dati
            # in questo caso lo slug e' il titolo di bilancio e viene costruito usando
            # titolo e sottotitolo della tabella. nel caso il sottotitolo non sia presente
            # si aggiunge il table_counter, che conta il n. di tabelle che hanno un unico titolo

            slug = ''
            if table_data['meta']['titolo']:
                slug = slug + table_data['meta']['titolo']
            if table_data['meta']['sottotitolo']:
                slug += table_data['meta']['sottotitolo']
            elif table_counter > 0:
                slug += "-count-" +str(table_counter)

            slug = slugify(unicode(slug))

            if table_is_empty:
                return None
            else:
                if len(table_data['meta']['columns']) == 0:
                    self.logger.warning(u"No columns found in table: {0}".format(slug))
                return {'slug': slug, 'data': table_data}
