import couchdb
from django.conf import settings
from django.core.cache import cache
from bilanci.utils import email_utils


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

# def read_bulk(couchdb, couchdb_name, keys_list, logger):
#         # reads bulk of docs and returns True if everything went fine else False
#         logger.info("Reading bulk of {} docs to db".format(len(keys_list)))
#         # curl -d '{"keys":["bar","baz"]}' -X POST http://127.0.0.1:5984/foo/_all_docs?include_docs=true
#
#         data = {'keys': keys_list}
#         if couchdb_name == 'bilanci_simple':
#             return_values = couchdb.bilanci_simple._all_docs.post(data=data)
#         elif couchdb_name == 'bilanci_voci':
#             return_values = couchdb.bilanci_voci._all_docs.post(data=data)
#         elif couchdb_name == 'bilanci_titoli':
#             return_values = couchdb.bilanci_titoli._all_docs.post(data=data)
#         else:
#             logger.critical("Couchdb name not accepted:{}".format(couchdb_name))
#             return False
#
#         return_values = return_values['rows']
#
#         for r in return_values:
#             doc_id = r['id']
#             deleted = r.get('deleted',None)
#             error = r.get('error',None)
#             if error and error == 'not_found' or deleted:
#                 logger.warning("Document not found id:'{}' in db:'{}'".format(doc_id,couchdb_name))
#                 return False
#
#         return return_values


def write_bulk(couchdb_dest, couchdb_name, docs_bulk, logger):
        # writes bulk of bilanci to destination db and returns True if everything went fine else False
        logger.info("Writing bulk of {} docs to db".format(len(docs_bulk)))

        data = {'docs': docs_bulk}
        if couchdb_name == 'bilanci_simple':
            return_values = couchdb_dest.bilanci_simple._bulk_docs.post(data=data)
        elif couchdb_name == 'bilanci_voci':
            return_values = couchdb_dest.bilanci_voci._bulk_docs.post(data=data)
        elif couchdb_name == 'bilanci_titoli':
            return_values = couchdb_dest.bilanci_titoli._bulk_docs.post(data=data)
        else:
            logger.critical("Couchdb name not accepted:{}".format(couchdb_name))
            return False

        for r in return_values:
            success = r['ok']
            doc_id = r['id']
            rev = r['rev']
            logger.debug("Write return values:{},{},{}".format(success,doc_id,rev))
            if success is False:
                logger.critical("Document write failure! id:{} Rev:'{}'".format(doc_id,rev))
                return False

        return True