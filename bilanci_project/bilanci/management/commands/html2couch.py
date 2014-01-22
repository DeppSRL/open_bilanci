import logging
from optparse import make_option
from pprint import pprint
import re
from bs4 import BeautifulSoup
import couchdb
from django.core.management import BaseCommand
from django.conf import settings
from django.utils.text import slugify
import requests
import time
from bilanci.utils import UnicodeDictReader
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

        cities = self.get_cities(cities_codes)
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


    def get_comuni_dicts(self):
        """
        read list of comuni from CSV into a single dictionary
        having the code as key and the slug as value
        """
        lista_comuni_csv = settings.LISTA_COMUNI_PATH
        try:
            udr = UnicodeDictReader(f=open(lista_comuni_csv, mode='r'), dialect="excel_quote_all",)
        except IOError:
            raise Exception("Impossible to open file:%s" % lista_comuni_csv)

        comuni_by_codes = {}
        comuni_by_slugs = {}
        for row in udr:
            complete = "{0}--{1}".format(row['NOME_COMUNE'].upper(), row['CODICE_COMUNE'])
            comuni_by_codes[row['CODICE_COMUNE']] = complete
            comuni_by_slugs[row['NOME_COMUNE']] = complete

        return {'codes': comuni_by_codes, 'slugs': comuni_by_slugs}


    _digits = re.compile('\d')
    def contains_digits(self, d):
        return bool(self._digits.search(d))

    def get_cities(self, codes):
        """
        Returns the list of complete names of the cities, used in the html files
        starting from codes or slugs.

        The type of strings passed is automatically guessed.

        Return the complete list, if the All shortcut is used.
        """
        if not self.comuni_dicts:
            self.comuni_dicts = self.get_comuni_dicts()

        if codes.lower() == 'all':
            return self.comuni_dicts['codes'].values()

        codes = [c.strip().upper() for c in codes.split(",")]

        ret = []
        for code in codes:
            try:
                if self.contains_digits(code):
                    # it's a code
                    ret.append(self.comuni_dicts['codes'][code])
                else:
                    # it's a slug
                    ret.append(self.comuni_dicts['slugs'][code])
            except KeyError:
                continue

        return ret


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
                ).text
            )
            # non considera la prima tabella (con i dati riassuntivi del comune)
            # e le ultima: l'indice delle pagine
            considered_tables = soup.findAll("table")[1:-1]
            for table in considered_tables:
                ret = self.scrape_table(table=table)
                # ret == none se la tabella non conteneva dati
                if ret is not None:
                    data[quadro][ret['slug']] = ret['data']

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
                dummy_title = "Tabella-senza-titolo-"
                timestamp = str(time.time()).replace('.','')
                table_data['meta']['titolo'] = dummy_title+timestamp


            # cerca il sottotitolo
            caption = table_html.find("caption")
            if caption:
                table_data['meta']['sottotitolo'] = caption.text.strip(' \t\n\r')

            # prende la prima riga della tabella, che descrive le colonne
            for th in table_html.findAll("th"):
                if th.text.lower() != "voci":
                    table_data['meta']['columns'].append(th.text.strip(' \t\n\r'))

            if len(table_html.findAll("th")) == 0:
                self.logger.warning(u"No columns found in table: {0}".format(table_data['meta']['titolo']))

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


            slug = ''
            if table_data['meta']['titolo']:
                slug = slug + table_data['meta']['titolo']
            if table_data['meta']['sottotitolo']:
                slug += table_data['meta']['sottotitolo']
            else:
                slug += str(table_counter)

            if table_is_empty:
                return None
            else:
                return {'slug': slugify(unicode(slug)), 'data': table_data}
