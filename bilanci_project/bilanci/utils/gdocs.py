import logging
from urllib2 import URLError
from django.conf import settings
from gspread import exceptions
import gspread

logger = logging.getLogger('management')

def get_connection():
    """
    login into Google Account with credentials in the settings
    """
    # log into Google account
    gc = gspread.login(settings.GOOGLE_USER, settings.GOOGLE_PASSWORD)

    return gc


def get_simple_map(connection=None):
    """
    get mapping data from gdoc spreadsheet
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

    logger.info("Spreadsheet gdoc read: {0}".format(
        gdoc_keys['simple_map']
    ))

    # put the mapping into the voci_map dict
    # preventivo and consuntivo sheets are appended in a single list
    # the first two rows are removed (labels)
    try:
        logger.info("reading preventivo ...")
        voci_map_preventivo = list_sheet.worksheet("preventivo").get_all_values()[2:]
        logger.info("reading consuntivo ...")
        voci_map_consuntivo = list_sheet.worksheet("consuntivo").get_all_values()[2:]
    except URLError:
        raise Exception("Connection error to Gdrive")

    logger.info("done with reading the mapping list.")

    return (voci_map_preventivo, voci_map_consuntivo)


def get_simplified_leaves(connection=None):
    """
    get the simplified tree structure from gDoc
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

    logger.info("Spreadsheet gdoc read: {0}".format(
        gdoc_keys['simple_tree']
    ))

    # get the tree voices from gDoc spreadsheet
    try:
        logger.info("reading preventivo entrate ...")
        preventivo_entrate = list_sheet.worksheet("Entrate prev").get_all_values()
        logger.info("reading consuntivo entrate ...")
        consuntivo_entrate = list_sheet.worksheet("Entrate cons").get_all_values()
        logger.info("reading preventivo uscite ...")
        preventivo_uscite = list_sheet.worksheet("Spese prev").get_all_values()
        logger.info("reading consuntivo uscite ...")
        consuntivo_uscite = list_sheet.worksheet("Spese cons").get_all_values()
    except URLError:
        raise Exception("Connection error to Gdrive")

    logger.info("done with reading the tree list.")

    return (preventivo_entrate, consuntivo_entrate, preventivo_uscite, consuntivo_uscite)
