from collections import OrderedDict
from datetime import time
import os
from bs4 import BeautifulSoup
from django.utils.text import slugify
import requests
from bilanci.utils import unicode_csv

__author__ = 'guglielmo'


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
                row = [table_content['meta']['row_type']]
                row.extend(table_content['meta']['columns'])
                csv_writer.writerow(row)

                # emit table content
                rows = []
                for label, data in table_content['data'].items():
                    row = [label]
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

