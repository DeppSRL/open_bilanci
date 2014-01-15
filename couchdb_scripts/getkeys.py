import sys
import couchdb
import json
import argparse
from couchdb.design import ViewDefinition
from pprint import pprint

def titoli_getkeys(doc):
    # funzione che raccoglie per tutti i bilanci tutti i nomi
    # dei titoli, quadro per quadro
    considered_keys =["consuntivo", "preventivo"]
    if doc:
        for doc_keys in doc.keys():
            if doc_keys in considered_keys:
                tipo_bilancio = doc_keys
                for quadro_n, quadro_v  in doc[tipo_bilancio].iteritems():

                    # genera una chiave che contiene tipo di bilancio, quadro e la voce
                    # il valore 1 ci permette di fare somme con la reduce function _sum()
                    for nome_titolo in quadro_v.keys():
                        yield ([tipo_bilancio,quadro_n,nome_titolo,doc['_id'][:4]],1)


def voci_getkeys(doc):
    # funzione che raccoglie per tutti i bilanci tutti i nomi
    # delle voci, titolo per titolo, quadro per quadro
    considered_keys =["consuntivo", "preventivo"]
    if doc:
        for document_keys in doc.keys():
            if document_keys in considered_keys:
                tipo_bilancio = document_keys
                for quadro_n, quadro_v  in doc[tipo_bilancio].iteritems():

                    # genera una chiave che contiene tipo di bilancio, quadro e la voce
                    # il valore 1 ci permette di fare somme con la reduce function _sum()
                    for nome_titolo, contenuto in quadro_v.iteritems():

                        if 'data' in contenuto.keys():
                            if len(contenuto['data'])>0:
                                for voce in contenuto['data']:
                                    anno = doc['_id'][:4]
                                    yield ([tipo_bilancio,quadro_n,nome_titolo,voce,anno],1)



def main(argv):
    parser = argparse.ArgumentParser(description='Get Titolo names and voce labels from bilanci')
    server_name = None
    check_function= None

    voci_consuntivo_getkeys_js = '''
       function (doc) {
        var considered_keys= [ "consuntivo", "preventivo" ];
        var considered_quadro=['01','02','03','04','05','06'];
        var tipo_bilancio = considered_keys[0];
            if(doc!==null){
                	  if(tipo_bilancio in doc){
                	  	if(doc[tipo_bilancio]!==null){

                        for (var j = 0; j < considered_quadro.length; j++) {
			    				  quadro_n = considered_quadro[j];
			    				  if( quadro_n in doc[tipo_bilancio] ){
			    				  	for( var nome_titolo in doc[tipo_bilancio][quadro_n]){

                             if('data' in doc[tipo_bilancio][quadro_n][nome_titolo]){
                                 for(voce in doc[tipo_bilancio][quadro_n][nome_titolo]['data']){
                                     emit([tipo_bilancio+"_"+quadro_n+"_"+nome_titolo,voce],1);
                                 }

                             }
                            }
			    				  }
                        }
                    }
                	}

           }
        }
    '''

    voci_preventivo_getkeys_js = '''
       function (doc) {
        var considered_keys= [ "consuntivo", "preventivo" ];
        var considered_quadro=['01','02','03','04','05','06'];
        var tipo_bilancio = considered_keys[1];
            if(doc!==null){
                	  if(tipo_bilancio in doc){
                	  	if(doc[tipo_bilancio]!==null){

                        for (var j = 0; j < considered_quadro.length; j++) {
			    				  quadro_n = considered_quadro[j];
			    				  if( quadro_n in doc[tipo_bilancio] ){
			    				  	for( var nome_titolo in doc[tipo_bilancio][quadro_n]){

                             if('data' in doc[tipo_bilancio][quadro_n][nome_titolo]){
                                 for(voce in doc[tipo_bilancio][quadro_n][nome_titolo]['data']){
                                     emit([tipo_bilancio+"_"+quadro_n+"_"+nome_titolo,voce],1);
                                 }

                             }
                            }
			    				  }
                        }
                    }
                	}

           }
        }
    '''

    accepted_servers = {
        'localhost': {
            'host': 'localhost',
            'port': '5984',
            'user': '',
            'password':'',
            'db_name':'bilanci_raw'

        },
        'staging': {
            'host': 'staging.depp.it',
            'port': '5984',
            'user': 'op',
            'password':'op42',
            'db_name':'bilanci_titoli'
        },
    }

    accepted_views = {
        'voci':{
            'design_document': 'tree_getkeys',
            'mapping_function':voci_getkeys,
            'language': 'python'
        },
        'voci_consuntivo_js':{
            'design_document': 'consuntivo_getkeys_js',
            'mapping_function': voci_consuntivo_getkeys_js,
            'language': 'javascript'
        },
        'voci_preventivo_js':{
            'design_document': 'preventivo_getkeys_js',
            'mapping_function': voci_preventivo_getkeys_js,
            'language': 'javascript'
        },
        'titoli':{
            'design_document': 'tree_getkeys',
            'mapping_function': titoli_getkeys,
            'language': 'python'
        },
    }

    accepted_language = ['python','javascript']


    parser.add_argument('--server','-s', dest='server_name', action='store',
               default='localhost',
               help='Server name: localhost | staging')

    parser.add_argument('--function','-f', dest='function', action='store',
               default='voci',
               help='Function to sync: titoli | voci| voci_preventivo_js | voci_consuntivo_js')

    parser.add_argument("--check-function","-ck", help="check function after synch",
                    action="store_true")

    args = parser.parse_args()
    server_name= args.server_name
    check_function= args.check_function
    function_to_sync = args.function
    

    if server_name in accepted_servers.keys():
        # costruisce la stringa per la connessione al server aggiungendo user/passw se necessario
        server_string ='http://'
        if accepted_servers[server_name]['user']:
            server_string+=accepted_servers[server_name]['user']+":"
            if accepted_servers[server_name]['password']:
                server_string+=accepted_servers[server_name]['password']+"@"

        server_string+=accepted_servers[server_name]['host']+":"+accepted_servers[server_name]['port']

        print "Connecting to: "+server_string+" ..."
        # open db connection
        server = couchdb.Server(server_string)
        db = server[accepted_servers[server_name]['db_name']]
        print "Db connection ok!"

        if function_to_sync in accepted_views.keys():
            view_name = function_to_sync
            reduce_function = accepted_views[view_name]['mapping_function']

            # sync the view
            view = ViewDefinition(accepted_views[view_name]['design_document'],
                                  view_name,
                                  map_fun=reduce_function,
                                  reduce_fun='_sum()',
                                  language=accepted_views[view_name]['language']
            )

            view.sync(db)
            print "Sync done!"

            if check_function:
                # get view values
                check = db.view(accepted_views[view_name]['design_document']+'/'+view_name)
                # dummy code just to test the function
                for row in check:
                    print "Test output:"
                    pprint(row)
                    break

        else:
            print "Function "+function_to_sync+" not accepted"
    else:
        print "no op:"+server_name+","+str(check_function)


# launches main function
if __name__ == "__main__":
   main(sys.argv[1:])
