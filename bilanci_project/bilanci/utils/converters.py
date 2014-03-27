from collections import OrderedDict
from datetime import time
import os
from bs4 import BeautifulSoup
from django.utils.text import slugify
import requests
from bilanci.utils import unicode_csv

__author__ = 'guglielmo'



class FLScraper(object):
    """
    Finanza Locale Scraper

    has one public method to scrape finanzalocale budget pages

    * scrape       - scrape pages, identifies tables, call scrape_table

    The scrape method uses the internal _scrape_table method, to scrape single tables.
    """

    def __init__(self, logger):
        self.logger = logger

    def scrape(self, path, pages=None):
        """
        Create and return data out of HTML code, for each page in pages.
        Every page contains one quadro.

        The structure returned is a dictionary:
        {
          <quadro_num>:
          {
            <quadro_slug>: <quadro_data_list>
          }
        }

        :ret: - dict
        """
        data = OrderedDict()
        for quadro in pages:
            data[quadro] = OrderedDict()
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
                ret = self._scrape_table(table=table)
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


    def _scrape_table(self,table):
        """
        Scrape a given table and return a data structure.
        The data structure is used in the raw bilanci couchdb instance.

        ret = {
            <table_title_slug>: {
               'meta': { 'titolo': <table_title>, 'sottotitolo': <table_subtitle>, 'columns': <columns_labels_list> },
               'data': OrderedDict([
                  (<row_label>, <values_list>)
               ])
            }
        }
        :retv: dict
        """
        if table is not None:
            #scraped table
            table_html = table
            # data struct to return
            table_data = OrderedDict([
                ('meta', OrderedDict([
                        ('title', None),
                        ('subtitle', None),
                        ('row_type', 'ND'),
                        ('columns', [])
                    ])),
                ('data', OrderedDict()),
            ])

            # cerca il titolo negli elementi precedenti la tabella
            table_counter = 0
            for previous_element in table_html.previous_elements:
                if previous_element.name == "div" and previous_element.get('class'):
                    if previous_element.get('class')[0]=='acentro':
                        contents=previous_element.contents
                        if len(contents)==2:
                            table_data['meta']['title'] = previous_element.contents[1].text.\
                                replace("(gli importi sono espressi in euro)",'').strip(' \t\n\r')
                            break
                elif previous_element.name == "table":
                    table_counter+=1


            if table_data['meta']['title'] is None:
                # creates dummy title with timestamp to avoid overwriting other tables
                dummy_title = u"Tabella-senza-titolo-"
                timestamp = unicode(time.time()).replace('.','')
                table_data['meta']['title'] = dummy_title+timestamp


            # cerca il sottotitolo
            caption = table_html.find("caption")
            if caption:
                table_data['meta']['subtitle'] = caption.text.strip(' \t\n\r')

            # prende la prima riga della tabella, che descrive le colonne
            ths = table_html.findAll("th")

            ## HEADERS


            if ths:
                # label of the 0-th column (identifies the type of rows) [Voci, Funzioni/Interventi, ...]
                th0 = ths[0]
                table_data['meta']['row_type'] = th0.text.strip(' \t\n\r')

                # the labels of all other columns
                for th in ths[1:]:
                    table_data['meta']['columns'].append(th.text.strip(' \t\n\r'))


            ## DATA

            # prende i dati dalla tabella
            # table_is_empty e' un controllo che ci permette di non salvare tabelle che non hanno nemmeno
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
            if table_data['meta']['title']:
                slug += table_data['meta']['title']
            if table_data['meta']['subtitle']:
                slug += '-' + table_data['meta']['subtitle']
            elif table_counter > 0:
                slug += "-count-" +str(table_counter)

            slug = slugify(unicode(slug))

            if table_is_empty:
                return None
            else:
                if len(table_data['meta']['columns']) == 0:
                    self.logger.warning(u"No columns found in table: {0}".format(slug))
                return OrderedDict([
                    ('slug', slug),
                    ('data', table_data)
                ])




class FLEmitter(object):
    """
    An abstract class that has one public method to emit a
    finanzalocale budget in a variety of formats

    * emit - emit data

    The emit method must be implemented in subclasses.
    """
    def __init__(self, logger):
        self.logger = logger

    def emit(self, **kwargs):
        raise Exception("To be implemented")


class FLCSVEmitter(FLEmitter):
    """
    Finanza Locale CSV Emitter

    has one public method to emit the HTML-scraped data into a set of csv files.
    """

    def emit(self, **kwargs):
        """
        Files are organized in nested folders, under base_path.

        Non-existing directories are created.

        Data are passed in the q_data structure.

        kwargs:

        * q_data - the data structure to emit
        * base_path - the path where to start the directory tree
        """

        q_data = kwargs['q_data']
        base_path = kwargs['base_path']

        for q_num, q_tables in q_data.items():

            # check or create directory
            q_path = os.path.join(base_path, q_num)
            if not os.path.exists(q_path):
                os.mkdir(q_path)

            for table_slug, table_content in q_tables.items():

                # open csv file
                csv_filename = os.path.join(q_path, "{}.csv".format(table_slug))
                csv_file = open(csv_filename, 'w')
                csv_writer = unicode_csv.UnicodeWriter(csv_file, dialect=unicode_csv.excel_semicolon)
                self.logger.debug("\t{}".format(table_slug))

                # build and emit header
                row = [ table_content['meta']['row_type'] ]
                row.extend(table_content['meta']['columns'])
                csv_writer.writerow(row)

                # emit table content
                rows = []
                for label, data in table_content['data'].items():
                    row = [ label ]
                    row.extend(data)
                    rows.append(row)
                csv_writer.writerows(rows)


class FLCouchEmitter(FLEmitter):
    """
    Finanza Locale Couch Emitter

    has one public method to emit the data as a couchdb document

    the couchdb instance is defined when initializing the Emitter class
    """

    def __init__(self, logger, couchdb):
        super(FLCouchEmitter, self).__init__(logger)
        self.couchdb = couchdb

    def emit(self, **kwargs):
        """
        send data to couchdb, into the document identified by id

        kwargs:

        * data - the data structure to emit
        * id - the id of the couch document to add the document to

        the data is overwritten
        """
        id = kwargs['id']
        data = kwargs['data']

        # create or update budget data on couchdb
        if id in self.couchdb:
            data['_rev'] = self.couchdb[id].rev

        self.couchdb[id] = data

