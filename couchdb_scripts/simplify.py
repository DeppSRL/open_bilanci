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
    return



def main(argv):
    parser = argparse.ArgumentParser(description='Simplify DB structure, copying elements from a db to a new one')

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
