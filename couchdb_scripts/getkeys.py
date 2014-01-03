__author__ = 'stefano'
import couchdb
import json
from couchdb.design import ViewDefinition
from pprint import pprint


server = couchdb.Server('http://localhost:5984')
db = server['bilanci_raw']


def quadro4_getkeys(doc):
    all_keys = []
    possible_values =['quadro-4-a-impegni','quadro-4-a-impegni-1']
    for value in possible_values:
        if value in doc['consuntivo']['04'].keys():
            for key in doc['consuntivo']['04'][value]['data'].keys():
                clean_key = key.lower().strip()
                # se presente toglie il carattere - iniziale
                try:
                    if clean_key.index('- ') == 0:
                        clean_key = clean_key[2:]
                except ValueError:
                    pass

                all_keys.append(clean_key)


    if len(all_keys) < 1:
        if 'consuntivo' in doc.keys():
            all_keys.append('CONSUNTIVO NOT AVAILABLE')
        else:
            all_keys.append('QUADRO IMPEGNI NOT AVAILABLE')

    yield ('x', all_keys)


def quadro4_reduce(keys,values,rereduce):
    total= []

    for value in values:
        for key in value:
            if key not in total:
                total.append(key)
    return sorted(total)


def map_keys(doc):
    if len(doc['value']['preventivo']['04'].keys())>0:
        yield (doc['value']['preventivo']['04'].keys()[0],1)
    else:
        yield ('*',1)

def summingReducer(keys, values, rereduce):
    return sum(values)



# sync the view
view = ViewDefinition('tree_getkeys', 'quadro4_getkeys', map_fun=quadro4_getkeys, reduce_fun=quadro4_reduce, language='python')
pprint(view.sync(db))




# get view values
docs = []
c = 0

for row in db.view('tree_getkeys/quadro4_getkeys'):
    docs.append(row)
    c += 1
    if c > 100:
        break

print json.dumps(docs, indent=4)
