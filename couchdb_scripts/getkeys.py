__author__ = 'stefano'
import couchdb
import json
from couchdb.design import ViewDefinition
from pprint import pprint


# db_name = 'bilanci'
db_name = 'bilanci_raw'
# server = couchdb.Server('http://op:op42@staging.depp.it:5984/')
server = couchdb.Server('http://localhost:5984/')
db = server[db_name]


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



def titoli_getkeys(doc):
    # funzione che raccoglie per tutti i bilanci consuntivi tutti i nomi
    # dei titoli, quadro per quadro
    all_keys={'preventivo':{},'consuntivo':{}}

    for tipo_bilancio in all_keys.keys():
        if tipo_bilancio in doc.keys():
            for quadro_n, quadro_v  in doc[tipo_bilancio].iteritems():

                if quadro_n not in all_keys[tipo_bilancio].keys():
                    all_keys[tipo_bilancio][quadro_n]=[]
                # genera una chiave che contiene tipo di bilancio, quadro e la voce
                # il valore 1 ci permette di fare somme con la reduce function _sum()
                for voce in quadro_v.keys():
                    yield ([tipo_bilancio,quadro_n,voce,doc['_id'][:4]],1)



def keys_reduce(keys,values,rereduce):
    total={'preventivo':{},'consuntivo':{}}

    all_keys_list = values
    for all_key in all_keys_list:
        for tipo_bilancio in all_key:
            for titolo_name in all_key[tipo_bilancio].keys():
                # se total[titolo_name] non esiste, lo crea
                if titolo_name not in total[tipo_bilancio].keys():
                    total[tipo_bilancio][titolo_name]=[]

                for voce in all_key[tipo_bilancio][titolo_name]:
                    if voce not in total[tipo_bilancio][titolo_name]:
                        total[tipo_bilancio][titolo_name].append(voce)

    # ordina alfabeticamente i risultati
    for tipo_bilancio in total.keys():
        for titolo_name in total[tipo_bilancio].keys():
            total[tipo_bilancio][titolo_name]=sorted(total[tipo_bilancio][titolo_name])

    return total

# sync the view
view = ViewDefinition('tree_getkeys', 'cons_titoli_getkeys', map_fun=titoli_getkeys,  language='python')
view.sync(db)




# get view values
docs = []
c = 0
#
# for row in db.view('tree_getkeys/cons_titoli_getkeys'):
#     docs.append(row)
#
#
# print json.dumps(docs, indent=4)
