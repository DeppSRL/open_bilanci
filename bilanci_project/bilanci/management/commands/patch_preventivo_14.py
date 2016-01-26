import logging
import locale
from optparse import make_option
from pprint import pprint
from decimal import Decimal
from django.conf import settings
from django.core.management import BaseCommand
import time
from bilanci.utils.moneydate import moneyfmt
from bilanci.utils import couch
from bilanci.utils.comuni import FLMapper


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--dry-run',
                    dest='dryrun',
                    action='store_true',
                    default=False,
                    help='Set the dry-run command mode: nothing is written in the couchdb'),
        make_option('--couchdb-server',
                    dest='couchdb_server',
                    default=settings.COUCHDB_DEFAULT_SERVER,
                    help='CouchDB server alias to connect to (staging | localhost). Defaults to staging.'),

    )

    help = 'Patches bilanci_voci for preventivo 2014 documents applying ' \
           'ICI voce patch'
    dryrun = False
    cbw = None
    logger = logging.getLogger('management')
    couchdb_dest = None

    def couch_connect(self, couchdb_server):
        # connect to couch database
        couchdb_server_alias = couchdb_server
        couchdb_dbname = settings.COUCHDB_NORMALIZED_VOCI_NAME

        if couchdb_server_alias not in settings.COUCHDB_SERVERS:
            raise Exception("Unknown couchdb server alias.")

        return couch.connect(
            couchdb_dbname,
            couchdb_server_settings=settings.COUCHDB_SERVERS[couchdb_server_alias]
            )

    def patch(self, preventivo,comune_slug):
        # gets the value of residui attivi from Q11 because in Q9 the table is malformed and the row was overwritten or removed
        try:
            altre_imposte_di_cui = preventivo['02']['quadro-2-entrate-entrate-tributarie']['data']['altre imposte di cui :'][0]

        except KeyError:
            self.logger.error("Cannot find consuntivo['02']['quadro-2-entrate-entrate-tributarie']['data']['altre imposte di cui :'] for {}".format(comune_slug))
            return

        try:
            ici_pep = preventivo['02']['quadro-2-entrate-entrate-tributarie']['data']['i.c.i. per poste esercizi precedenti (recupero evasione e altre fattispecie particolari)'][0]
        except KeyError:
            self.logger.error("Cannot find preventivo['02']['quadro-2-entrate-entrate-tributarie']['data']['i.c.i. per poste esercizi precedenti (recupero evasione e altre fattispecie particolari)'] for {}".format(comune_slug))
            return

        try:
            altre_imposte_di_cui = float(altre_imposte_di_cui.replace(".","").replace(",","."))
            ici_pep = float(ici_pep.replace(".","").replace(",","."))
            altre_imposte_di_cui -= ici_pep
        except ValueError:
            self.logger.error("Number conversion errors for {}, could not patch!".format(comune_slug))
            return

        # transform altre imposte di cui back to string with the correct format:
        # from: 123456.00 to: 123,456.00
        altre_imposte_di_cui= Decimal(altre_imposte_di_cui)
        preventivo['02']['quadro-2-entrate-entrate-tributarie']['data']['altre imposte di cui :'][0] = moneyfmt(altre_imposte_di_cui,2,curr='',sep='.', dp=',')

        return


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

        self.dryrun = options['dryrun']
        # get the timestamp to ensure the document will be written in couchdb, this is a workaround for a bug,
        # see later comment
        timestamp = time.time()
        ###
        # connect to couchdb
        ###
        self.couchdb_dest = self.couch_connect(options['couchdb_server'])

        # create couch bulk writer
        self.cbw = couch.CouchBulkWriter(logger=self.logger, couchdb_dest=self.couchdb_dest)

        mapper = FLMapper()
        all_cities = mapper.get_cities('all', logger=self.logger)
        counter=0
        for comune_slug in all_cities:
            doc_key = "2014_{}".format(comune_slug)
            if counter%50==0:
                self.logger.info(u"Reached {}".format(comune_slug))
            counter+=1
            
            bilancio_2014 = self.couchdb_dest.get(doc_key)

            old_destination_doc = self.couchdb_dest.get(doc_key, None)
            if old_destination_doc:
                revision = old_destination_doc.get('_rev', None)
                if revision:
                    bilancio_2014['_rev'] = revision
                    self.logger.debug("Adds rev value to doc:{}".format(doc_key))

            if bilancio_2014 is None:
                self.logger.error("Cannot find bilancio 2014 for {}".format(comune_slug))
                continue

            preventivo = bilancio_2014.get('preventivo', None)
            if preventivo is None:
                self.logger.error("Cannot find preventivo 2014 for {}".format(comune_slug))
                continue

            self.patch(preventivo,comune_slug)
            # writes back in couchdb
            bilancio_2014['_id'] = doc_key
            bilancio_2014['useless_timestamp'] = timestamp

            if not self.dryrun:
                # write doc to couchdb dest
                ret = self.cbw.write(bilancio_2014)
                if ret is False:
                    self.logger.critical("Write critical problem. Quit")
                    exit()


        if not self.dryrun:
            # if the buffer in CBW is non-empty, flushes the docs to the db
            ret = self.cbw.close()

            if ret is False:
                self.logger.critical("Write critical problem. Quit")

        self.logger.info(u"Done patch preventivo 14")
        return