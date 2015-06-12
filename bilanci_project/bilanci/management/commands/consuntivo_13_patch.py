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

    def patch_totale_pareggio(self, consuntivo):

        # overwrites the 'totale' row (which is a sub-total, actually) with "totale a pareggio" values and
        # removes the voce relative to "totale a pareggio" from the the object

        def overwrite_row(data_dict, key_to_overwrite, key_to_delete):
            data_dict[key_to_overwrite] = data_dict[key_to_delete]
            data_dict.pop(key_to_delete, None)

        #             Q2
        data_dict = consuntivo['02']['quadro-2-entrate-titolo-i-entrate-tributarie']['data']
        overwrite_row(data_dict, key_to_overwrite='totale entrate tributarie',
                      key_to_delete='totale entrate tributarie a pareggio')

        #             Q4 Impegni
        data_dict = consuntivo['04']['quadro-4-a-impegni']['data']
        overwrite_row(data_dict, key_to_overwrite='totale',
                      key_to_delete='totale a pareggio (entrate tributarie + quota imu)')

        #             Q4 Pagamenti Conto competenza
        data_dict = consuntivo['04']['quadro-4-b-pagamenti-in-conto-competenza']['data']
        overwrite_row(data_dict, key_to_overwrite='totale',
                      key_to_delete='totale a pareggio (entrate tributarie + quota imu)')
        return

    def patch_residui_passivi(self, consuntivo):
        # gets the value of residui passivi from Q12 because in Q9 the table is malformed and the row was overwritten or removed

        residui_passivi = consuntivo['12']['quadro-12-gestione-dei-residui-passivi']['data']['Totale'][4:]
        consuntivo['09']['quadro-9-quadro-riassuntivo-della-gestione-finanziaria']['data'][
            'residui passivi'] = residui_passivi
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

        for comune_slug in all_cities:
            doc_key = "2013_{}".format(comune_slug)
            bilanci_2013 = self.couchdb.get(doc_key)
            consuntivo = bilanci_2013.get('consuntivo', None)
            if consuntivo is None:
                self.logger.error("Cannot find consuntivo 2013 for {}".format(comune_slug))
                continue

            self.patch_totale_pareggio(consuntivo)
            self.patch_residui_passivi(consuntivo)
            # writes back in couchdb
            self.couchdb.delete(doc_key)
            self.couchdb[doc_key] = bilanci_2013
            self.logger.info(u"Document {} updated".format(doc_key))

        return