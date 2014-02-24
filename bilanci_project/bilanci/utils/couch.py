import couchdb
from django.conf import settings
from django.core.cache import cache


def get(key):
    """
    Read all city budgets from the cache, and if not found,
    get that from couch (connecting if needed).

    :key: - the city slug (as for couchdb)
    """
    ret = cache.get(key)
    if ret is None:
        couch_db = connect()
        ret = couch_db.get(key)
        cache.set(key, ret)

    return ret


def get_connection_address(couchdb_server_settings=None):
    if couchdb_server_settings is None:
        couchdb_server_settings = settings.COUCHDB_SERVERS[settings.COUCHDB_DEFAULT_SERVER]

    server_connection_address = "http://"
    if 'user' in couchdb_server_settings and 'password' in couchdb_server_settings:
        server_connection_address += "{0}:{1}@".format(
            couchdb_server_settings['user'],
            couchdb_server_settings['password']
        )
    server_connection_address += "{0}:{1}".format(
        couchdb_server_settings['host'],
        couchdb_server_settings['port']
    )
    return server_connection_address

def get_server(couchdb_server_settings=None):
    server_connection_address = get_connection_address(couchdb_server_settings=couchdb_server_settings)
    couch_server = couchdb.Server(server_connection_address)
    return couch_server

def connect(couchdb_dbname=settings.COUCHDB_SIMPLIFIED_NAME, couchdb_server_settings=None):
    """
    Connect to the couchdb server and hook to the DB.
    Server and dbname are defined in the settings.

    Returns the pointer to the database or raise appropriate exceptions.
    """

    # open connection to couchdb server and hook to db
    couch_server = get_server(couchdb_server_settings=couchdb_server_settings)
    couch_db = couch_server[couchdb_dbname]

    return couch_db


