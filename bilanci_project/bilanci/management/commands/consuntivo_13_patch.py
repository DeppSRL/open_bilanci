import logging
from optparse import make_option
from pprint import pprint
from django.conf import settings
from django.core.management import BaseCommand
from bilanci.utils import couch, gdocs
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

    help = 'Patches bilanci_voci for Consuntivo 2013 documents applying ' \
           '"Residui passivi" patch and "Totale a pareggio" patch'
    dryrun = False
    logger = logging.getLogger('management')
    couchdb = None

    def couch_connect(self, couchdb_server):
        # connect to couch database
        couchdb_server_alias = couchdb_server
        couchdb_dbname = settings.COUCHDB_NORMALIZED_VOCI_NAME

        if couchdb_server_alias not in settings.COUCHDB_SERVERS:
            raise Exception("Unknown couchdb server alias.")

        self.couchdb = couch.connect(
            couchdb_dbname,
            couchdb_server_settings=settings.COUCHDB_SERVERS[couchdb_server_alias]
        )

    def overwrite_row(self, data_dict, key_to_overwrite, key_to_delete, comune_slug, quadro):
        # overwrites a key in a dict with another, then deletes the key to be deleted
        try:
            data_dict[key_to_overwrite] = data_dict[key_to_delete]
        except KeyError:
            self.logger.error("{}: {} Cannot find '{}'".format(comune_slug, quadro, key_to_delete))
        data_dict.pop(key_to_delete, None)


    def patch_totale_pareggio(self, consuntivo, comune_slug):

        # overwrites the 'totale' row (which is a sub-total, actually) with "totale a pareggio" values and
        # removes the voce relative to "totale a pareggio" from the the object

        #             Q2
        try:
            data_dict = consuntivo['02']['quadro-2-entrate-titolo-i-entrate-tributarie']['data']
        except KeyError:
            self.logger.error("Cannot find consuntivo['02']['quadro-2-entrate-titolo-i-entrate-tributarie']['data'] for {}".format(comune_slug))
        else:
            self.overwrite_row(
                data_dict,
                key_to_overwrite='totale entrate tributarie',
                key_to_delete='totale entrate tributarie a pareggio',
                comune_slug=comune_slug,
                quadro="cons['02']['quadro-2-entrate-titolo-i-entrate-tributarie']")

        #             Q4 Impegni
        try:
            data_dict = consuntivo['04']['quadro-4-a-impegni']['data']
        except KeyError:
            self.logger.error("Cannot find consuntivo['04']['quadro-4-a-impegni']['data'] for {}".format(comune_slug))
        else:
            self.overwrite_row(
                data_dict,
                key_to_overwrite='totale',
                key_to_delete='totale a pareggio (entrate tributarie + quota imu)',
                comune_slug=comune_slug,
                quadro="cons['04']['quadro-4-a-impegni']")

        #             Q4 Pagamenti Conto competenza
        try:
            data_dict = consuntivo['04']['quadro-4-b-pagamenti-in-conto-competenza']['data']
        except KeyError:
            self.logger.error("Cannot find consuntivo['04']['quadro-4-b-pagamenti-in-conto-competenza']['data'] for {}".format(comune_slug))
        else:
            self.overwrite_row(
                data_dict,
                key_to_overwrite='totale',
                key_to_delete='totale a pareggio (entrate tributarie + quota imu)',
                comune_slug=comune_slug,
                quadro="cons['04']['quadro-4-b-pagamenti-in-conto-competenza']")
        return

    def patch_residui_passivi(self, consuntivo, comune_slug):
        # gets the value of residui passivi from Q12 because in Q9 the table is malformed and the row was overwritten or removed
        try:
            residui_passivi = consuntivo['12']['quadro-12-gestione-dei-residui-passivi']['data']['Totale'][4:]
        except KeyError:
            self.logger.error("Cannot find consuntivo['12']['quadro-12-gestione-dei-residui-passivi']['data']['Totale'] for {}".format(comune_slug))
        else:
            try:
                consuntivo['09']['quadro-9-quadro-riassuntivo-della-gestione-finanziaria']['data'][
                    'residui passivi'] = residui_passivi
            except KeyError:
                self.logger.error("Cannot find consuntivo['09']['quadro-9-quadro-riassuntivo-della-gestione-finanziaria']['data']['residui passivi'] for {}".format(comune_slug))
        return

    def patch_residui_attivi(self, consuntivo, comune_slug):
        # gets the value of residui attivi from Q11 because in Q9 the table is malformed and the row was overwritten or removed
        try:
            residui_attivi = consuntivo['11']['quadro-11-gestione-dei-residui-attivi']['data']['Totale'][5:]
        except KeyError:
            self.logger.error("Cannot find consuntivo['11']['quadro-11-gestione-dei-residui-attivi']['data']['Totale'] for {}".format(comune_slug))
        else:
            try:
                consuntivo['09']['quadro-9-quadro-riassuntivo-della-gestione-finanziaria']['data'][
                'residui attivi'] = residui_attivi
            except KeyError:
                self.logger.error("Cannot find consuntivo['09']['quadro-9-quadro-riassuntivo-della-gestione-finanziaria']['data']['residui attivi'] for {}".format(comune_slug))

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

        ###
        # connect to couchdb
        ###
        self.couch_connect(options['couchdb_server'])
        mapper = FLMapper()
        all_cities = mapper.get_cities('all', logger=self.logger)
        counter = 0
        for comune_slug in all_cities:
            doc_key = "2013_{}".format(comune_slug)
            bilancio_2013 = self.couchdb.get(doc_key)
            if bilancio_2013 is None:
                self.logger.error("Cannot find bilancio 2013 for {}".format(comune_slug))
                continue
            consuntivo = bilancio_2013.get('consuntivo', None)
            if consuntivo is None:
                self.logger.error("Cannot find consuntivo 2013 for {}".format(comune_slug))
                continue

            self.patch_totale_pareggio(consuntivo,comune_slug)
            self.patch_residui_passivi(consuntivo,comune_slug)
            self.patch_residui_attivi(consuntivo,comune_slug)
            # writes back in couchdb
            bilancio_2013['_id'] = doc_key
            bilancio_2013.pop('_rev')
            self.couchdb.delete(self.couchdb[doc_key])
            self.couchdb[doc_key] = bilancio_2013
            counter +=1
            if counter == 100:
                self.logger.info(u"Document {} updated".format(doc_key))
                counter =0
                
        self.logger.info(u"Done")
        return