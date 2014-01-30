#!/usr/local/bin/python
# coding: utf-8
import sys
import couchdb
from  gspread.exceptions import SpreadsheetNotFound
import gspread
import argparse
from pprint import pprint
import requests
from settings_local import *


def simplify(source_db, destination_db, id_list_response, list_sheet):
    voci_map = {}
    #prende entrambi i fogli di calcolo e li inserisce nella stessa lista, saltando le prime due righe di intestazione
    voci_ws = list_sheet.worksheet("preventivo").get_all_values()[2:]
    voci_ws.extend(list_sheet.worksheet("consuntivo").get_all_values()[2:])

    # crea la mappa per voci e funzioni
    for row in voci_ws:
        # considero valide solo le righe che hanno i valori di entrata/uscita e di titolo non nulli
        if row[6] and row[7]:

            tipo_bilancio = unicode(row[0]).lower()
            # zero padding per n_quadro: '2' -> '02'
            quadro_norm=row[1].zfill(2)
            titolo_norm = unicode(row[2]).lower()
            voce_norm = unicode(row[3]).lower()


            if tipo_bilancio not in voci_map:
                voci_map[tipo_bilancio] = {}
            if quadro_norm not in voci_map[tipo_bilancio]:
                voci_map[tipo_bilancio][quadro_norm] = {}
            if titolo_norm not in voci_map[tipo_bilancio][quadro_norm]:
                voci_map[tipo_bilancio][quadro_norm][titolo_norm] = {}

            if voce_norm not in voci_map[tipo_bilancio][quadro_norm][titolo_norm]:
                voci_map[tipo_bilancio][quadro_norm][titolo_norm][voce_norm] = {}


            #  crea la mappa di conversione delle voci
            # la chiave e' tipo_bilancio, numero_quadro , nome_titolo, voce_raw

            voci_map[tipo_bilancio][quadro_norm][titolo_norm][voce_norm]=\
                {
                'tipo_bilancio': tipo_bilancio,
                'entrata_uscita': unicode(row[7]).lower(),
                'titolo': unicode(row[6]).lower(),
                'categoria': unicode(row[5]).lower(),
                'voce': unicode(row[4]).lower(),

            }

    # todo: creare la mappa per gli interventi


    # per ogni documento nel db applica la conversione
    if 'rows' in id_list_response.keys():
        id_list=id_list_response['rows']

        for id_object in id_list:
            source_document = source_db.get(id_object['id'])


            if source_document is not None:
                destination_document = {'_id': id_object['id']}

                if "_design/" not in id_object['id']:

                    print "Copying document id:"+id_object['id']
                    #  per ogni tipo di bilancio
                    for bilancio_name in ['preventivo','consuntivo']:
                        if bilancio_name in source_document.keys():
                            bilancio_object = source_document[bilancio_name]
                            destination_document[bilancio_name]={}

                            for quadro_name, quadro_object in bilancio_object.iteritems():
                                destination_document[bilancio_name][quadro_name]={}
                                for titolo_name, titolo_object in quadro_object.iteritems():
                                    # analizza i titoli e traduce titoli e voci
                                    pass

                        else:
                            # se il documento e' un design doc, non lo copia
                            pass


                        # scrive il nuovo oggetto nel db di destinazione
                        # destination_db.save(destination_document)

    return



def main(argv):
    description = 'Simplify DB structure, copying elements from voci normalized db to the simplified db'
    parser = argparse.ArgumentParser(description=description)

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
            list_sheet = gc.open_by_key(gdoc_keys['simplify'])
        except SpreadsheetNotFound:
            print "Error: gdoc url not found"
            return


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

        # set source db name / destination db name
        source_db_name = accepted_servers[server_name]['normalized_voci_db_name']
        destination_db_name = accepted_servers[server_name]['simplified_db_name']


        source_db = server[source_db_name]
        print "Source DB connection OK! Db name: "+source_db_name

        # se esiste il db lo cancella

        if destination_db_name in server:
            del server[destination_db_name]
            print  "Destination db: "+  destination_db_name +" deleted"

        # crea il db
        destination_db = server.create(destination_db_name)
        print  "Destination db: "+  destination_db_name +" created"


        # legge la lista di id per recuperare tutti gli oggetti del db
        get_all_docs_url = server_connection_address+'/'+source_db_name+'/_all_docs?include_docs=false'

        id_list_response = requests.get(get_all_docs_url ).json()
        simplify(source_db, destination_db, id_list_response, list_sheet)

    else:
        print "server not accepted:"+server_name



# launches main function
if __name__ == "__main__":
   main(sys.argv[1:])
