#!/usr/local/bin/python
# coding: utf-8

"""
DEPRECATED. Superseeded by the couch_translate_keys management task.
"""

import sys
import couchdb
from couchdb.http import ResourceConflict
import gspread
import argparse
from pprint import pprint
import requests
from settings_local import *


def translate_titoli(source_db, destination_db, id_list_response, list_sheet, overwrite_flag=False):

    translation_map = {}
    #prende entrambi i fogli di calcolo e li inserisce nella stessa lista, saltando le prime due righe di instestazione
    ws_values = list_sheet.worksheet("preventivo").get_all_values()[2:]
    ws_values.extend(list_sheet.worksheet("consuntivo").get_all_values()[2:])

    for row in ws_values:
        # considero valide solo le righe che hanno l'ultimo valore (titolo di destinazione) non nullo
        if row[3]:
            
            tipo_bilancio = row[0]
            # zero padding per n_quadro: '2' -> '02'
            n_quadro=row[1].zfill(2)
            titolo_raw = row[2]
            titolo_normalizzato = row[3]
            
            if tipo_bilancio not in translation_map:
                translation_map[tipo_bilancio] = {}
            if n_quadro not in translation_map[tipo_bilancio]:
                translation_map[tipo_bilancio][n_quadro] = {}
            if titolo_raw not in translation_map[tipo_bilancio][n_quadro]:
                translation_map[tipo_bilancio][n_quadro][titolo_raw] = {}

            #  crea la mappa di conversione dei titoli
            # la chiave e' tipo_bilancio, numero_quadro , nome_titolo_raw
            translation_map[tipo_bilancio][n_quadro][titolo_raw]=titolo_normalizzato


    if 'rows' in id_list_response.keys():
        id_list=id_list_response['rows']

        for id_object in id_list:

            # skip existing documents, if overwrite_flag is set to false
            if id_object['id'] in destination_db and not overwrite_flag:
                continue

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
                                    # per ogni titolo presente, se il titolo e' nella translation map
                                    # applica la trasformazione, poi copia il contenuto nell'oggetto di destinazione

                                    if quadro_name in translation_map[bilancio_name].keys():
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
                        if quadro_name in destination_document[bilancio_name]:
                            if len(destination_document[bilancio_name][quadro_name].keys()) != len(source_document[bilancio_name][quadro_name].keys()):
                                print "Error: Different number of keys for doc_id:"+id_object['id']

                    if overwrite_flag:
                        destination_document['_rev'] = source_document['_rev']
                else:
                    # se il documennto e' un design doc, lo copia nella sua interezza
                    print "Copying design document id:"+id_object['id']
                    destination_document['language']=''
                    destination_document['language'] = source_document['language']
                    destination_document['views']={}
                    destination_document['views']=source_document['views']


                # scrive il nuovo oggetto nel db di destinazione
                try:
                    destination_db.save(destination_document)
                except ResourceConflict:
                    destination_db.update(documents = [destination_document])

    else:
        print "Error: document list is empty"
    return




def translate_voci(source_db, destination_db, id_list_response, list_sheet, overwrite_flag=False):

    translation_map = {}
    #prende entrambi i fogli di calcolo e li inserisce nella stessa lista, saltando le prime due righe di instestazione
    ws_values = list_sheet.worksheet("preventivo").get_all_values()[2:]
    ws_values.extend(list_sheet.worksheet("consuntivo").get_all_values()[2:])

    for row in ws_values:

        # considero valide solo le righe che hanno l'ultimo valore (voce normalizzata) non nullo
        if row[4]:

            tipo_bilancio = unicode(row[0]).lower()
            # zero padding per n_quadro: '2' -> '02'
            n_quadro=row[1].zfill(2)
            titolo = unicode(row[2]).lower()
            voce_raw = unicode(row[3]).lower()
            voce_normalizzata = unicode(row[4]).lower()
            
            if tipo_bilancio not in translation_map:
                translation_map[tipo_bilancio] = {}
            if n_quadro not in translation_map[tipo_bilancio]:
                translation_map[tipo_bilancio][n_quadro] = {}
            if titolo not in translation_map[tipo_bilancio][n_quadro]:
                translation_map[tipo_bilancio][n_quadro][titolo] = {}
            
            if voce_raw not in translation_map[tipo_bilancio][n_quadro][titolo]:
                translation_map[tipo_bilancio][n_quadro][titolo][voce_raw] = {}


            #  crea la mappa di conversione delle voci
            # la chiave e' tipo_bilancio, numero_quadro , nome_titolo, voce_raw
            translation_map[tipo_bilancio][n_quadro][titolo][voce_raw]=voce_normalizzata


    if 'rows' in id_list_response.keys():
        id_list = id_list_response['rows']

        for id_object in id_list:

            # skip existing documents, if overwrite_flag is set to false
            if id_object['id'] in destination_db and not overwrite_flag:
                continue

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
                                    # per ogni titolo presente analizza tutte le voci
                                    destination_document[bilancio_name][quadro_name][titolo_name]={}
                                    # crea i meta
                                    if 'meta' in titolo_object.keys():
                                        destination_document[bilancio_name][quadro_name][titolo_name]['meta']={}
                                        destination_document[bilancio_name][quadro_name][titolo_name]['meta']=\
                                            titolo_object['meta']

                                    # passa i dati sul nuovo oggetto
                                    if 'data' in titolo_object.keys():
                                        destination_document[bilancio_name][quadro_name][titolo_name]['data']={}

                                        for voce_name, voce_obj in titolo_object['data'].iteritems():
                                            # se c'e' una traduzione da effettuare per la voce, la effettua
                                            u_voce_name = unicode(voce_name).lower()
                                            # se la voce inizia con "- " lo elimina, cosi come abbiamo fatto
                                            # nella view
                                            if u_voce_name.find("- ") == 0:
                                                u_voce_name = u_voce_name.replace("- ","")
                                            voce_name_translated = u_voce_name
                                            if quadro_name in translation_map[bilancio_name].keys():
                                                if titolo_name in translation_map[bilancio_name][quadro_name].keys():
                                                    if u_voce_name in translation_map[bilancio_name][quadro_name][titolo_name].keys():

                                                        voce_name_translated = translation_map[bilancio_name][quadro_name][titolo_name][u_voce_name]


                                            # crea il dizionario con il nome tradotto
                                            destination_document[bilancio_name][quadro_name]\
                                                [titolo_name]['data'][voce_name_translated]={}
                                            destination_document[bilancio_name][quadro_name]\
                                                [titolo_name]['data'][voce_name_translated]=voce_obj


                                        # controlla che alcune voci non siano andate perse nella traduzione
                                        if len(destination_document[bilancio_name][quadro_name]\
                                                    [titolo_name].keys()) != \
                                                len(source_document[bilancio_name][quadro_name][titolo_name].keys()):
                                            print "Error: Different number of keys for doc_id:"+id_object['id']


                else:
                    # se il documento e' un design doc, lo copia nella sua interezza
                    print "Copying design document id:"+id_object['id']
                    destination_document['language']=''
                    destination_document['language'] = source_document['language']
                    destination_document['views']={}
                    destination_document['views']=source_document['views']

                
                # scrive il nuovo oggetto nel db di destinazione
                destination_db.save(destination_document)

    else:
        print "Error: document list is empty"
    return



def main(argv):
    parser = argparse.ArgumentParser(description='Translate bilanci keys, copying elements from a db to a new one')

    accepted_servers_help = "Server name: "
    for accepted_servers_name in accepted_servers.keys():
        accepted_servers_help+= accepted_servers_name+" | "


    parser.add_argument('--server','-s', dest='server_name', action='store',
               default='localhost',
               help=accepted_servers_help
        )

    parser.add_argument('--type','-t', dest='type', action='store',
           default='titoli',
           help='Type to translate: titoli | voci')

    parser.add_argument('--delete','-d', dest='delete', action='store_true',
           default=False,
           help='Delete DB before translation. Use only while developing. Defaults to false.')

    parser.add_argument('--overwrite','-o', dest='overwrite', action='store_true',
           default=False,
           help='Overwrite all values. Defaults to false.')




    args = parser.parse_args()
    
    server_name= args.server_name
    translation_type = args.type
    delete_db_flag = args.delete
    overwrite_flag = args.overwrite

    if translation_type in accepted_types.keys():

        if server_name in accepted_servers.keys():
            # Login with the script Google account
            gc = gspread.login(g_user, g_password)

            # open the list worksheet
            list_sheet = None
            try:
                list_sheet = gc.open_by_key(gdoc_keys[translation_type])
            except gspread.exceptions.SpreadsheetNotFound:
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
            if translation_type == 'voci':
                source_db_name = accepted_servers[server_name]['normalized_titoli_db_name']
                destination_db_name = accepted_servers[server_name]['normalized_voci_db_name']
            else:
                source_db_name = accepted_servers[server_name]['raw_db_name']
                destination_db_name = accepted_servers[server_name]['normalized_titoli_db_name']

            source_db = server[source_db_name]
            print "Source DB connection ok: db name: "+source_db_name+"!"

            if destination_db_name not in server:
                # create db afresh, if not found
                destination_db = server.create(destination_db_name)
                print  "Destination db: "+  destination_db_name +" newly created"
            else:
                # remove existing db if asked to do so
                if delete_db_flag:
                    del server[destination_db_name]
                    destination_db = server.create(destination_db_name)
                    print  "Destination db: "+  destination_db_name +" deleted and re-created"
                else:
                    destination_db = server[destination_db_name]

            # legge la lista di id per recuperare tutti gli oggetti del db
            get_all_docs_url = server_connection_address+'/'+source_db_name+'/_all_docs?include_docs=false'

            id_list_response = requests.get(get_all_docs_url ).json()

            if translation_type == 'voci':
                translate_voci(source_db, destination_db, id_list_response, list_sheet, overwrite_flag=overwrite_flag)
            elif translation_type == 'titoli':
                translate_titoli(source_db, destination_db, id_list_response, list_sheet, overwrite_flag=overwrite_flag)


        else:
            print "server not accepted:"+server_name
    else:
        print "Type not accepted: " + translation_type


# launches main function
if __name__ == "__main__":
   main(sys.argv[1:])
