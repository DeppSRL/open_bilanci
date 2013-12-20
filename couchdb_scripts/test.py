__author__ = 'stefano'
import couchdb
import json
from couchdb.design import ViewDefinition
from pprint import pprint

server = couchdb.Server('http://localhost:5984')
db = server['bilanci']


def quadro4_getkeys(doc):
    all_keys = []
    possible_values =['quadro-4-a-impegni','quadro-4-a-impegni-1']
    for value in possible_values:
        if value in doc['value']['preventivo']['04'].keys():
            for key in doc['value']['preventivo']['04'][value]['data'].keys():
                clean_key = key.lower().strip()
                try:
                    if clean_key.index('- ') == 0:
                        clean_key = clean_key[2:]
                except ValueError:
                    pass

                all_keys.append(clean_key)


    if len(all_keys) < 1:
        all_keys.append('DATA NOT AVAILABLE')
    # all_keys.append(doc['value']['consuntivo']['04']['quadro-4-a-impegni']['data'].keys())

    yield (doc['key'], all_keys)


def quadro_4_reduce(keys,values,rereduce):
    total= []
    array_list = values
    for array in array_list:
        for value in array:
            if value not in total:
                total.append(value)

    return total

def map_keys(doc):
    if len(doc['value']['preventivo']['04'].keys())>0:
        yield (doc['value']['preventivo']['04'].keys()[0],1)
    else:
        yield ('*',1)

def summingReducer(keys, values, rereduce):
    return sum(values)


# sync the view
view = ViewDefinition('tree_getkeys', 'quadro4_getkeys', quadro4_getkeys, reduce_fun=quadro_4_reduce, language='python')
view.sync(db)

# sync the view
# view = ViewDefinition('tree_getkeys', 'map_keys', map_keys, reduce_fun=summingReducer, language='python')
# view.sync(db)


# get view values
docs = []
c = 0
#
# for row in db.view('tree_getkeys/quadro4_getkeys'):
#     docs.append(row)
#     c += 1
#     if c > 100:
#         break
#
# print json.dumps(docs, indent=4)
