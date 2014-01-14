import sys
import couchdb
import gspread
import argparse
from pprint import pprint
import requests
from settings_local import *


def main(argv):
    parser = argparse.ArgumentParser(description='Translate bilanci keys, copying elements from a db to a new one')

    translation_map = {}

    accepted_servers_help = "Server name: "
    for accepted_servers_name in accepted_servers.keys():
        accepted_servers_help+= accepted_servers_name+" | "


    parser.add_argument('--server','-s', dest='server_name', action='store',
               default='localhost',
               help=accepted_servers_help
        )

    args = parser.parse_args()
    
    server_name= args.server_name


    if server_name in accepted_servers.keys():
        # Login with the script Google account
        gc = gspread.login(g_user, g_password)

        # open the list worksheet
        list_sheet = None
        try:
            list_sheet = gc.open_by_key(gdoc_keys['voci'])
        except gspread.exceptions.SpreadsheetNotFound:
            print "gdoc url not found"
            return


        # Select worksheet by index. Worksheet indexes start from zero
        titoli_ws_values = list_sheet.get_worksheet(0).get_all_values()


        for row in titoli_ws_values[1:]:
            # considero valide solo le righe che hanno l'ultimo valore (titolo di destinazione) non nullo
            if row[3]:
                # zero padding per n_quadro: '2' -> '02'
                n_quadro=row[1].zfill(2)

                if row[0] not in translation_map:
                    translation_map[row[0]] = {}
                if n_quadro not in translation_map[row[0]]:
                    translation_map[row[0]][n_quadro] = {}
                if row[2] not in translation_map[row[0]][n_quadro]:
                    translation_map[row[0]][n_quadro][row[2]] = {}

                #  crea la mappa di conversione dei titoli
                # la chiave e' tipo_bilancio, numero_quadro , nome_titolo
                translation_map[row[0]][n_quadro][row[2]]=row[3]


        # connessione a couchdb
        # costruisce la stringa per la connessione al server aggiungendo user/passw se necessario
        server_connection_address ='http://'
        if accepted_servers[server_name]['user']:
            server_connection_address+=accepted_servers[server_name]['user']+":"
            if accepted_servers[server_name]['password']:
                server_connection_address+=accepted_servers[server_name]['password']+"@"

        server_connection_address+=accepted_servers[server_name]['host']+":"+accepted_servers[server_name]['port']

        print "Connecting to: "+server_connection_address+" ..."
        # open db connection
        server = couchdb.Server(server_connection_address)
        source_db = server[accepted_servers[server_name]['source_db_name']]
        print "Source DB connection ok!"


        # se esiste il db lo cancella
        if accepted_servers[server_name]['destination_db_name'] in server:
            del server[accepted_servers[server_name]['destination_db_name']]
            print  "Destination db: "+  accepted_servers[server_name]['destination_db_name'] +" deleted"
        # crea il db
        destination_db = server.create(accepted_servers[server_name]['destination_db_name'])
        print  "Destination db: "+  accepted_servers[server_name]['destination_db_name'] +" created"


        # legge la lista di id per recuperare tutti gli oggetti del db
        get_all_docs_url = server_connection_address+'/'+accepted_servers[server_name]['source_db_name']+'/_all_docs?include_docs=false'

        id_list_response = requests.get(get_all_docs_url ).json()

        if 'rows' in id_list_response.keys():
            id_list=id_list_response['rows']

            for row in id_list:
                source_document = source_db.get(row['id'])
                print "Analyzing doc_id:"+row['id']

                if source_document is not None:
                    destination_document = {'_id': row['id']}

                    #  per ogni tipo di bilancio
                    for bilancio_name in ['preventivo','consuntivo']:
                        if bilancio_name in source_document.keys():
                            bilancio_object = source_document[bilancio_name]
                            destination_document[bilancio_name]={}

                            for quadro_name, quadro_object in bilancio_object.iteritems():
                                destination_document[bilancio_name][quadro_name]={}
                                for titolo_name, titolo_object in quadro_object.iteritems():
                                    # per ogni titolo presente, se il titolo e' nella translation map
                                    # applica la trasformazione, poi copia il contenuto nell'oggetto di destinazione

                                    if titolo_name in translation_map[bilancio_name][quadro_name].keys():
                                        titolo_name_translated = translation_map[bilancio_name][quadro_name][titolo_name]
                                    else:
                                        titolo_name_translated = titolo_name

                                    # crea il dizionario con il nome tradotto
                                    destination_document[bilancio_name][quadro_name][titolo_name_translated]={}
                                    # crea i meta
                                    if 'meta' in titolo_object.keys():
                                        destination_document[bilancio_name][quadro_name][titolo_name_translated]['meta']={}
                                        destination_document[bilancio_name][quadro_name][titolo_name_translated]['meta']=titolo_object['meta']

                                    # passa i dati sul nuovo oggetto
                                    if 'data' in titolo_object.keys():
                                        destination_document[bilancio_name][quadro_name][titolo_name_translated]['data']={}
                                        destination_document[bilancio_name][quadro_name][titolo_name_translated]['data'] =\
                                                    titolo_object['data']


                    # controlla che alcune voci di titoli non siano andate perse nella traduzione
                    if bilancio_name in source_document:
                        if len(destination_document[bilancio_name][quadro_name].keys()) != len(source_document[bilancio_name][quadro_name].keys()):
                            print "Error: Different number of keys for doc_id:"+row['id']

                    # scrive il nuovo oggetto nel db di destinazione
                    destination_db.save(destination_document)

    else:
        print "server not accepted:"+server_name


# launches main function
if __name__ == "__main__":
   main(sys.argv[1:])
