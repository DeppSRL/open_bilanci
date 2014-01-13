__author__ = 'guglielmo'
from pprint import pprint
from couchdb.design import ViewDefinition
import couchdb
import json

server = couchdb.Server('http://localhost:5984')
db = server['bilanci']

def get_inhabitants(doc):
    k = 'quadro-1-dati-generali-al-31-dicembrenotizie-varie'
    if k in doc['consuntivo']['01'].keys():
        kpop = 'Popolazione residente (ab.)'
        if kpop in doc['consuntivo']['01'][k]['data'].keys():
            i = doc['consuntivo']['01'][k]['data'][kpop][0]
            yield ((doc['city_name'], doc['anno']), i)


# sync the view
view = ViewDefinition('city_info', 'get_inhabitants', map_fun=get_inhabitants, language='python')
pprint(view.sync(db))

docs = []
for c, row in enumerate(db.view('city_info/get_inhabitants'), start=1):
    docs.append(row)
    if c > 10:
        break

print json.dumps(docs, indent=4)
