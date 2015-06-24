# coding: utf-8

import logging
import tortilla
from optparse import make_option
from couchdb.http import ResourceNotFound
from django.core.management import BaseCommand, call_command
from django.conf import settings
from bilanci.utils import couch
from bilanci.utils import gdocs, email_utils
from bilanci.utils.comuni import FLMapper

__author__ = 'guglielmo'


class Command(BaseCommand):
    """
    Reads data from a source couchdb instance and produces (upgrades) couchdb destination documents,
    by translating the document keys, according to the content of gdoc mappings.

    Substitutes and supersedes the couchdb_scripts/translate_keys script.
    """

    option_list = BaseCommand.option_list + (
        make_option('--dry-run',
                    dest='dryrun',
                    action='store_true',
                    default=False,
                    help='Set the dry-run command mode: nothing is written in the couchdb'),
        make_option('--type',
                    dest='type',
                    help='Select translation type: [(v)oce | (t)itolo]'),
        make_option('--years',
                    dest='years',
                    default='',
                    help='Years to fetch. From 2002 to 2012. Use one of this formats: 2012 or 2003-2006 or 2002,2004,2006'),
        make_option('--cities',
                    dest='cities',
                    default='',
                    help='Cities codes or slugs. Use comma to separate values: Roma,Napoli,Torino or  "All"'),
        make_option('--couchdb-server',
                    dest='couchdb_server',
                    default=settings.COUCHDB_DEFAULT_SERVER,
                    help='CouchDB server to connect to (defaults to staging).'),
        make_option('--skip-existing',
                    dest='skip_existing',
                    action='store_true',
                    default=False,
                    help='Skip existing documents. Use to speed up long import of many cities, when errors occur'),
        make_option('--force-google',
                    dest='force_google',
                    action='store_true',
                    default=False,
                    help='Force reloading mapping files from gdocs (invalidate the csv cache)'),
        make_option('--design-documents',
                    dest='design_documents',
                    action='store_true',
                    default=False,
                    help='Copy design documents into destination db'),
        make_option('--append',
                    dest='append',
                    action='store_true',
                    default=False,
                    help='Use the log file appending instead of overwriting (used when launching shell scripts)'),
        make_option('--no-patch',
                    dest='no_patch',
                    action='store_true',
                    default=False,
                    help='When translating Voci excludes Patch 2013 Consuntivo mng task (development only)'),
    )

    help = 'Translate the keys of couchdb documents, normalizing them.'

    logger = logging.getLogger('management')
    comuni_dicts = {}
    docs_bulk = []
    bulk_size = 80
    couchdb_source = None
    couchdb_dest = None
    couchdb_dest_tortilla = None

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
        no_patch = options['no_patch']

        if options['append'] is True:
            self.logger = logging.getLogger('management_append')

        # type option, different values are accepted:
        #  v, V, voce, Voce, VOCE or
        #  t, T, titolo, Titolo, TITOLO, Title
        if 'type' not in options:
            raise Exception("Missing type parameter")
        if options['type'].lower()[0] not in ('v', 't'):
            raise Exception("Wrong type parameter value (voce|titolo)")
        translation_type = options['type'][0].lower()

        force_google = options['force_google']
        skip_existing = options['skip_existing']
        design_documents = options['design_documents']

        cities_codes = options['cities']
        if not cities_codes:
            raise Exception("Missing city parameter")

        self.logger.info("Opening Lista Comuni")
        mapper = FLMapper()
        cities = mapper.get_cities(cities_codes)
        if cities_codes.lower() != 'all':
            self.logger.info("Processing cities: {0}".format(cities))

        years = options['years']
        if not years:
            raise Exception("Missing years parameter")

        if "-" in years:
            (start_year, end_year) = years.split("-")
            years = range(int(start_year), int(end_year) + 1)
        else:
            years = [int(y.strip()) for y in years.split(",") if
                     settings.APP_START_YEAR <= int(y.strip()) <= settings.APP_END_YEAR]

        if not years:
            raise Exception("No suitable year found in {0}".format(years))

        self.logger.info("Processing years: {0}".format(years))

        ###
        # couchdb connections
        ###

        couchdb_server_alias = options['couchdb_server']

        # set couch source and destination names
        if translation_type == 't':
            couchdb_source_name = settings.COUCHDB_RAW_NAME
            couchdb_dest_name = settings.COUCHDB_NORMALIZED_TITOLI_NAME
        elif translation_type == 'v':
            couchdb_source_name = settings.COUCHDB_NORMALIZED_TITOLI_NAME
            couchdb_dest_name = settings.COUCHDB_NORMALIZED_VOCI_NAME
        else:
            self.logger.critical(u"Translation type not accepted:{}".format(translation_type))
            exit()

        if couchdb_server_alias not in settings.COUCHDB_SERVERS:
            raise Exception("Unknown couchdb server alias.")

        self.logger.info("Connecting to server: {}".format(couchdb_server_alias, ))
        self.logger.info("Connecting source db: {}".format(couchdb_source_name))
        try:
            self.couchdb_source = couch.connect(
                couchdb_source_name,
                couchdb_server_settings=settings.COUCHDB_SERVERS[couchdb_server_alias]
            )
        except ResourceNotFound:
            self.logger.error("Could not find source db. Quitting")
            return

        self.logger.info("Connecting to destination db: {0}".format(couchdb_dest_name))
        couchdb_dest_settings = settings.COUCHDB_SERVERS[couchdb_server_alias]

        try:
            self.couchdb_dest = couch.connect(
                couchdb_dest_name,
                couchdb_server_settings=couchdb_dest_settings
            )
        except ResourceNotFound:
            self.logger.error("Could not find destination db. Quitting")
            return

        server_connection_string = "http://{}:{}".format(couchdb_dest_settings['host'], couchdb_dest_settings['port'])
        self.couchdb_dest_tortilla = tortilla.wrap(server_connection_string)

        self.logger.info("Compact destination db...")
        self.couchdb_dest.compact()
        self.logger.info("Done")

        ###
        #   Mapping files from gdoc
        ###
        # connect to google account and fetch tree mapping and simple tree structure
        normalized_map = gdocs.get_normalized_map(translation_type, n_header_lines=2, force_google=force_google)

        normalized_titoli_sheet = {'preventivo': [row[2] for row in normalized_map['preventivo']],
                                   'consuntivo': [row[2] for row in normalized_map['consuntivo']],
                                   }
        normalized_voci_sheet = {'preventivo': [(row[2], row[3]) for row in normalized_map['preventivo']],
                                 'consuntivo': [(row[2], row[3]) for row in normalized_map['consuntivo']],
                                 }

        # copying design documents
        if design_documents:
            self.logger.info(u"Copying design documents")
            source_design_docs = self.couchdb_source.view("_all_docs",
                                                          startkey="_design/", endkey="_design0",
                                                          include_docs=True
            )
            for row in source_design_docs.rows:
                source_design_doc = row.doc
                self.logger.info(u"  document id: ".format(source_design_doc.id))
                destination_document = {'_id': source_design_doc.id}
                destination_document['language'] = source_design_doc['language']
                destination_document['views'] = source_design_doc['views']
                if not dryrun:
                    self.couchdb_dest.save(destination_document)

        if cities and years:

            for city in cities:
                self.logger.info(u"Updating {}".format(city))

                for year in years:

                    doc_id = u"{0}_{1}".format(year, city)
                    if doc_id in self.couchdb_dest and skip_existing:
                        self.logger.info("Skipping city of {}, as already existing".format(city))
                        continue

                    # identify source document or skip
                    source_document = self.couchdb_source.get(doc_id)
                    if source_document is None:
                        self.logger.warning("{0} doc_id not found in source db. skipping.".format(doc_id))
                        continue

                    # create destination document, to REPLACE old one
                    destination_document = {'_id': doc_id, }

                    # if a doc with that id already exists on the destination document, gets the _rev value
                    # and insert it in the dest. document.
                    # this avoids document conflict on writing
                    # otherwise you should delete the old doc before writing the new one

                    old_destination_doc = self.couchdb_dest.get(doc_id, None)
                    if old_destination_doc:
                        revision = old_destination_doc.get('_rev', None)
                        if revision:
                            destination_document['_rev'] = revision
                            self.logger.debug("Adds rev value to doc")

                    for bilancio_type in ['preventivo', 'consuntivo']:
                        if bilancio_type in source_document.keys():
                            bilancio_object = source_document[bilancio_type]
                            destination_document[bilancio_type] = {}

                            for quadro_name, quadro_object in bilancio_object.iteritems():
                                destination_document[bilancio_type][quadro_name] = {}

                                for titolo_name, titolo_object in quadro_object.iteritems():

                                    if translation_type == 't':
                                        # for each titolo, apply translation_map, if valid
                                        try:
                                            idx = normalized_titoli_sheet[bilancio_type].index(titolo_name)
                                            titolo_name = normalized_map[bilancio_type][idx][3]
                                        except ValueError:
                                            pass

                                    # create dest doc titolo dictionary
                                    destination_document[bilancio_type][quadro_name][titolo_name] = {}

                                    # copy meta
                                    if 'meta' in titolo_object.keys():
                                        destination_document[bilancio_type][quadro_name][titolo_name]['meta'] = {}
                                        destination_document[bilancio_type][quadro_name][titolo_name]['meta'] = \
                                            titolo_object['meta']

                                    # copy data (normalize voci if needed)
                                    if 'data' in titolo_object.keys():
                                        destination_document[bilancio_type][quadro_name][titolo_name]['data'] = {}

                                        if translation_type == 'v':
                                            # voci translation
                                            for voce_name, voce_obj in titolo_object['data'].iteritems():
                                                # voci are always translated into lowercase, unicode strings
                                                # trailing dash is removed, if present
                                                voce_name = unicode(voce_name.lower())
                                                if voce_name.find("- ") == 0:
                                                    voce_name = voce_name.replace("- ", "")

                                                # for each voce, apply translation_map, if valid
                                                try:
                                                    idx = normalized_voci_sheet[bilancio_type].index(
                                                        (titolo_name, voce_name))
                                                    voce_name = normalized_map[bilancio_type][idx][4]
                                                except ValueError:
                                                    pass

                                                # create voice dictionary with normalized name
                                                destination_document[bilancio_type][quadro_name][titolo_name]['data'][
                                                    voce_name] = {}
                                                destination_document[bilancio_type][quadro_name][titolo_name]['data'][
                                                    voce_name] = voce_obj

                                        else:
                                            # copy all voci in data, with no normalization
                                            destination_document[bilancio_type][quadro_name][titolo_name]['data'] = \
                                                titolo_object['data']

                    # add the document to the list that will be written to couchdb in bulks
                    self.docs_bulk.append(destination_document)

                    if len(self.docs_bulk) == self.bulk_size:
                        if not dryrun:
                            ret_value = couch.write_bulk(
                                couchdb_dest=self.couchdb_dest_tortilla,
                                couchdb_name=couchdb_dest_name,
                                docs_bulk=self.docs_bulk,
                                logger=self.logger)

                            if ret_value is False:
                                email_utils.send_notification_email(msg_string='Couch translate key has encountered problems')
                            self.docs_bulk = []

        # if the last set was < bulk_size write the last documents
        if len(self.docs_bulk) > 0:
            if not dryrun:
                ret_value = couch.write_bulk(
                                couchdb_dest=self.couchdb_dest_tortilla,
                                couchdb_name=couchdb_dest_name,
                                docs_bulk=self.docs_bulk,
                                logger=self.logger)

                if ret_value is False:
                    email_utils.send_notification_email(msg_string='Couch translate key has encountered problems')
                self.docs_bulk = []

        self.logger.info("Compact destination db...")
        self.couchdb_dest.compact()
        self.logger.info("Done compacting")

        if not dryrun and couchdb_dest_name == settings.COUCHDB_NORMALIZED_VOCI_NAME and settings.INSTANCE_TYPE == 'production' or settings.INSTANCE_TYPE == 'staging' and no_patch is False:
            self.logger.info(u"============Run patch 2013 for consuntivo======================")
            call_command('consuntivo_13_patch', verbosity=2, interactive=False)

        email_utils.send_notification_email(msg_string="Couch translate key has finished")
        self.logger.info("finish couch translate keys")
