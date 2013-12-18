__author__ = 'stefano'
import couchdb
import json
from couchdb.design import ViewDefinition
from pprint import pprint

server = couchdb.Server('http://localhost:5984')
db = server['bilanci']


def quadro4_getkeys(doc):

    yield ('key', doc['value'])


# {
#    "getkeys": {
#        "map": "
# function(doc) {
# function walk(obj){
#    var keys = new Object();
#    for(var key in obj){
#       keys[key]=obj[key];
#     }
#      return keys\n
#    }
#    emit(doc.key, walk(doc.value));
#   }
#    }
# }


view = ViewDefinition('tree_getkeys', 'quadro4_getkeys', quadro4_getkeys, language='python')
view.sync(db)
