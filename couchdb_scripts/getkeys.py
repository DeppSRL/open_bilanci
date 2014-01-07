__author__ = 'stefano'
import couchdb
import json
from couchdb.design import ViewDefinition
from pprint import pprint


server = couchdb.Server('http://localhost:5984')
db = server['bilanci_raw']

def cons_titoli_getkeys(doc):
    # funzione che raccoglie per tutti i bilanci consuntivi tutti i nomi
    # dei titoli, quadro per quadro
    all_keys={}
    if 'consuntivo' in doc.keys():
        for quadro_n, quadro_v  in doc['consuntivo'].iteritems():

            if quadro_n not in all_keys.keys():
                all_keys[quadro_n]=[]

            all_keys[quadro_n]=quadro_v.keys()

    yield ('key', all_keys)



def quadro4_getkeys(doc):
    all_keys = {
        'a':[],
        'b':[],
        'c':[]
    }

    possible_values = {
        'a':['quadro-4-a-impegni','quadro-4-a-impegni-1'],
        'b':['quadro-4-b-pagamenti-in-conto-competenza','quadro-4-b-pagamenti-in-conto-competenza-1'],
        'c':['quadro-4-c-pagamenti-in-conto-residui','quadro-4-c-pagamenti-in-conto-residui-1']
    }

    for titolo_key,titolo_values in possible_values.iteritems():
        for titolo_name in titolo_values:
            if titolo_name in doc['consuntivo']['04'].keys():
                for sottovoce in doc['consuntivo']['04'][titolo_name]['data'].keys():
                    clean_sottovoce = sottovoce.lower().strip()
                    # se presente toglie il carattere - iniziale
                    try:
                        if clean_sottovoce.index('- ') == 0:
                            clean_sottovoce = clean_sottovoce[2:]
                    except ValueError:
                        pass

                    all_keys[titolo_key].append(clean_sottovoce)

    all_keys['a']=sorted(all_keys['a'])
    all_keys['b']=sorted(all_keys['b'])
    all_keys['c']=sorted(all_keys['c'])
    yield ('key', all_keys)


def keys_reduce(keys,values,rereduce):
    total={}

    all_keys_list = values
    for all_key in all_keys_list:
        for titolo_name in all_key.keys():
            # se total[titolo_name] non esiste, lo crea
            if titolo_name not in total.keys():
                total[titolo_name]=[]

            for voce in all_key[titolo_name]:
                if voce not in total[titolo_name]:
                    total[titolo_name].append(voce)

    # ordina alfabeticamente i risultati
    # for titolo_name in total.keys():
    #     total[titolo_name]=sorted(total[titolo_name])

    return total


# sync the view
# view = ViewDefinition('tree_getkeys', 'quadro4_getkeys', map_fun=quadro4_getkeys, reduce_fun=keys_reduce, language='python')
view = ViewDefinition('tree_getkeys', 'cons_titoli_getkeys', map_fun=cons_titoli_getkeys, reduce_fun=keys_reduce, language='python')
view.sync(db)




# get view values
docs = []
c = 0

for row in db.view('tree_getkeys/cons_titoli_getkeys'):
    docs.append(row)


print json.dumps(docs, indent=4)
