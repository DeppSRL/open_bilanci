import csv
import glob
import json
import logging
from urllib2 import URLError
from django.conf import settings
from gspread import exceptions
from oauth2client.client import SignedJwtAssertionCredentials
import gspread
from bilanci import utils
import os

logger = logging.getLogger('management')


def get_connection():
    from oauth2client.client import SignedJwtAssertionCredentials

    json_key = json.load(open(settings.OAUTH2_KEY_PATH))
    scope = ['https://spreadsheets.google.com/feeds']

    credentials = SignedJwtAssertionCredentials(json_key['client_email'], json_key['private_key'], scope)
    gc = gspread.authorize(credentials)
    return gc


def read_from_csv(path_name, csv_base_dir='data/gdocs_csv_cache/', n_header_lines=0):
    """
    Read all .csv files under a path and return a tuple

    skip the first n_header_lines rows
    """

    ret = {}

    path = "{0}{1}".format(csv_base_dir, path_name)
    csv_files = glob.glob("{0}/*.csv".format(path))
    for csv_file in csv_files:
        # read csv file
        try:
            unicode_reader = utils.UnicodeReader(open(csv_file, 'r'), dialect=utils.excel_semicolon)
        except IOError:
            raise Exception("It was impossible to open file %s" % csv_file)
        except csv.Error, e:
            raise Exception("CSV error while reading %s: %s" % (csv_file, e.message))

        content = []
        c = 0
        for row in unicode_reader:
            c += 1
            if c < n_header_lines:
                continue

            content.append(list(row))

        ret[os.path.basename(os.path.splitext(csv_file)[0])] = content
        logger.info("{} file read".format(csv_file))

    return ret



def write_to_csv(path_name, contents, csv_base_dir='data/gdocs_csv_cache/'):
    """
    write contents dict into as many csv files as contents' keys

    create the csv file according to the keys (adding the .csv extension)

    check if the csv_base_dir/path_name path exists, and create it if it doesn't
    """
    path = "{0}{1}".format(csv_base_dir, path_name)
    if not os.path.exists(path):
        os.makedirs(path)
    for name, content in contents.iteritems():
        csv_filename = "{0}/{1}.csv".format(path, name)
        csv_f = open(csv_filename, mode='wb')
        writer = utils.UnicodeWriter(csv_f, dialect=utils.excel_semicolon)
        for row in content:
            writer.writerow(row)

        logger.info("{} file written".format(csv_filename))


def get_normalized_map(normalization_type, connection=None, force_google=False, n_header_lines=0):
    """
    :param: normalization_type (t|v)
    :param: connection - (optional) a connection to the google account (singleton)
    :param: n_header_lines - (optional) n. of lines to ignore

    :ret: a dict, containing the consuntivo and preventivo sheets

    Try a local CSV version of the documents, or retrieve them from google

    Always retrieve from google, if instructed to do so.

    Skip header lines when reading from google (csv do not contain header lines).

    Return a dict of the sheets.
    """
    ret = None

    if normalization_type == 't':
        map_name = 'titoli_map'
    elif normalization_type == 'v':
        map_name = 'voci_map'
    else:
        raise Exception("normalization_type arg accepts 't' or 'v' as possible values")

    if force_google == False:
        ret = read_from_csv(map_name)

    if not ret:
        ret = get_normalized_map_from_google(normalization_type, n_header_lines=n_header_lines)
        write_to_csv(map_name, ret)

    return ret


def get_simple_map(connection=None, force_google=False, n_header_lines=0):
    """
    Try a local CSV version of the documents, or retrieve them from google

    Always retrieve from google, if instructed to do so.

    Skip header lines when reading from google (csv do not contain header lines).

    Return a dict of the sheets.
    """
    ret = None
    if force_google == False:
        ret = read_from_csv('simple_map')

    if not ret:
        ret = get_simple_map_from_google(n_header_lines=n_header_lines)
        write_to_csv('simple_map', ret)

    return ret



def get_simplified_leaves(force_google=False, n_header_lines=0):
    """
    Try a local CSV version of the documents, or retrieve them from google

    Always retrieve from google, if instructed to do so.

    Skip header lines when reading from google (csv do not contain header lines).

    Return a dict of the sheets
    """
    ret = None
    if force_google == False:
        ret = read_from_csv('simplified_leaves')

    if not ret:
        ret = get_simplified_leaves_from_google(n_header_lines=n_header_lines)
        write_to_csv('simplified_leaves', ret)


    return ret


def get_normalized_map_from_google(normalization_type, connection=None, n_header_lines=0):
    """
    get normalized voci or titoli mapping from gdoc spreadsheets

    :param: normalization_type (t|v)
    :param: connection - (optional) a connection to the google account (singleton)
    :param: n_header_lines - (optional) n. of lines to ignore

    :ret: a dict, containing the consuntivo and preventivo sheets
    """

    # get all gdocs keys
    gdoc_keys = settings.GDOC_KEYS

    if normalization_type == 't':
        gdoc_key = gdoc_keys['titoli_map']
    elif normalization_type == 'v':
        gdoc_key = gdoc_keys['voci_map']
    else:
        raise Exception("normalization_type arg accepts 't' or 'v' as possible values")

    if connection is None:
        connection = get_connection()

    # open the list worksheet
    list_sheet = None
    try:
        list_sheet = connection.open_by_key(gdoc_key)
    except exceptions.SpreadsheetNotFound:
        raise Exception("Error: gdoc url not found: {0}".format(
            gdoc_key
        ))

    logger.info("normalized mapping gdoc read. key: {0}".format(
        gdoc_key
    ))

    # put the mapping into the voci_map dict
    # preventivo and consuntivo sheets are appended in a single list
    # the first two rows are removed (labels)
    try:
        logger.info("reading preventivo ...")
        voci_map_preventivo = list_sheet.worksheet("preventivo").get_all_values()[n_header_lines:]
        logger.info("reading consuntivo ...")
        voci_map_consuntivo = list_sheet.worksheet("consuntivo").get_all_values()[n_header_lines:]
    except URLError:
        raise Exception("Connection error to Gdrive")

    logger.info("done with reading the mapping list.")

    return {
        'preventivo': voci_map_preventivo,
        'consuntivo': voci_map_consuntivo,
    }



def get_simple_map_from_google(connection=None, n_header_lines=0):
    """
    get mapping data from gdoc spreadsheet

    return a dict, containing the consuntivo and preventivo sheet
    """

    # get all gdocs keys
    gdoc_keys = settings.GDOC_KEYS

    if connection is None:
        connection = get_connection()

    # open the list worksheet
    list_sheet = None
    try:
        list_sheet = connection.open_by_key(gdoc_keys['simple_map'])
    except exceptions.SpreadsheetNotFound:
        raise Exception("Error: gdoc url not found: {0}".format(
            gdoc_keys['simple_map']
        ))

    logger.info("norm_2_simple mapping gdoc read. key: {0}".format(
        gdoc_keys['simple_map']
    ))

    # put the mapping into the voci_map dict
    # preventivo and consuntivo sheets are appended in a single list
    # the first two rows are removed (labels)
    try:
        logger.info("reading preventivo ...")
        voci_map_preventivo = list_sheet.worksheet("preventivo").get_all_values()[n_header_lines:]
        logger.info("reading consuntivo ...")
        voci_map_consuntivo = list_sheet.worksheet("consuntivo").get_all_values()[n_header_lines:]
        logger.info("reading interventi ...")
        voci_map_interventi = list_sheet.worksheet("interventi").get_all_values()[n_header_lines:]
    except URLError:
        raise Exception("Connection error to Gdrive")

    logger.info("done with reading the mapping list.")

    return {
        'preventivo': voci_map_preventivo,
        'consuntivo': voci_map_consuntivo,
        'interventi': voci_map_interventi,
    }


def get_simplified_leaves_from_google(connection=None, n_header_lines=0):
    """
    get the simplified tree structure from gDoc

    return a dict, containing the leaves for
     - preventivo_entrate
    """

    # get all gdocs keys
    gdoc_keys = settings.GDOC_KEYS

    if connection is None:
        connection = get_connection()


    # open the list worksheet
    list_sheet = None
    try:
        list_sheet = connection.open_by_key(gdoc_keys['simple_tree'])
    except exceptions.SpreadsheetNotFound:
        raise Exception("Error: gdoc url not found: {0}".format(
            gdoc_keys['simple_tree']
        ))

    logger.info("simplified_subtrees_leaves gdoc read. key: {0}".format(
        gdoc_keys['simple_tree']
    ))

    # get the voices subtrees from gDoc spreadsheet
    # skip the first n_headers lines
    try:
        logger.info("reading preventivo entrate ...")
        preventivo_entrate = list_sheet.worksheet("Entrate prev").get_all_values()[n_header_lines:]
        logger.info("reading consuntivo entrate ...")
        consuntivo_entrate = list_sheet.worksheet("Entrate cons").get_all_values()[n_header_lines:]
        logger.info("reading preventivo uscite ...")
        preventivo_spese = list_sheet.worksheet("Spese prev").get_all_values()[n_header_lines:]
        logger.info("reading consuntivo uscite ...")
        consuntivo_spese = list_sheet.worksheet("Spese cons").get_all_values()[n_header_lines:]
        logger.info("reading consuntivo riassuntivo ...")
        consuntivo_riassuntivo = list_sheet.worksheet("Riassuntivo cons").get_all_values()[n_header_lines:]

    except URLError:
        raise Exception("Connection error to Gdrive")

    logger.info("done with reading the tree list.")

    return {
        'preventivo-entrate': preventivo_entrate,
        'consuntivo-entrate': consuntivo_entrate,
        'preventivo-spese': preventivo_spese,
        'consuntivo-spese': consuntivo_spese,
        'consuntivo-riassuntivo': consuntivo_riassuntivo,
    }


def get_bilancio_codes_from_google(connection = None, n_header_lines = 0, bilancio_type_year = None ):

    """
    IMPORT BILANCIO XML

    get the bilancio xml codes from Google doc
    return a dict
    """

    # get all gdocs keys
    gdoc_keys = settings.GDOC_KEYS

    if connection is None:
        connection = get_connection()


    # open the list worksheet
    list_sheet = None
    try:
        list_sheet = connection.open_by_key(gdoc_keys[bilancio_type_year])
    except exceptions.SpreadsheetNotFound:
        raise Exception("Error: gdoc url not found: '{0}'".format(
            gdoc_keys[bilancio_type_year]
        ))

    logger.info("Bilancio xml code gdoc read. key: {0}".format(
        gdoc_keys[bilancio_type_year]
    ))

    # get the voices subtrees from gDoc spreadsheet
    # skip the first n_headers lines
    try:
        logger.info("Reading {} from drive".format(bilancio_type_year))
        voci = list_sheet.worksheet("Voci").get_all_values()[n_header_lines:]
        colonne = list_sheet.worksheet("Colonne").get_all_values()[n_header_lines:]


    except URLError:
        raise Exception("Connection error to Gdrive")

    logger.info("done with reading the list.")

    return {
        'voci': voci,
        'colonne': colonne,
    }
