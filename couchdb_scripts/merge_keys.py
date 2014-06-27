__author__ = 'stefano'

#!/usr/local/bin/python
# coding: utf-8

import sys
import couchdb
import gspread
import argparse
from pprint import pprint
import requests
import settings_local


def main(argv):
    parser = argparse.ArgumentParser(description='Merge keys for titoli / voci comparing couch db views and gdoc')

    settings_local.accepted_servers_help = "Server name: "
    for settings_local.accepted_servers_name in settings_local.accepted_servers.keys():
        settings_local.accepted_servers_help+= settings_local.accepted_servers_name+" | "


    parser.add_argument('--server','-s', dest='server_name', action='store',
               default='localhost',
               help=settings_local.accepted_servers_help
        )

    parser.add_argument('--type','-t', dest='type', action='store',
           default='titoli',
           help='Type to translate: titoli | voci')

    parser.add_argument('--output','-o', dest='output', action='store',
           default='output.csv',
           help="Output filename"
        )

    args = parser.parse_args()

    server_name= args.server_name
    translation_type = args.type

    if translation_type in settings_local.accepted_types.keys():

        if server_name in settings_local.accepted_servers.keys():
            # Login with the script Google account
            gc = gspread.login(g_user, g_password)

            # open the list worksheet
            list_sheet = None
            try:
                list_sheet = gc.open_by_key(settings_local.gdoc_keys[translation_type])
            except gspread.exceptions.SpreadsheetNotFound:
                print "Error: gdoc url not found"
                return


            # connessione a couchdb
            # costruisce la stringa per la connessione al server aggiungendo user/passw se necessario
            server_connection_address ='http://'
            if settings_local.accepted_servers[server_name]['user']:
                server_connection_address+=settings_local.accepted_servers[server_name]['user']+":"
                if settings_local.accepted_servers[server_name]['password']:
                    server_connection_address+=settings_local.accepted_servers[server_name]['password']+"@"

            server_connection_address+=settings_local.accepted_servers[server_name]['host']+":"+settings_local.accepted_servers[server_name]['port']

            print "Connecting to: "+server_connection_address+" ..."
            # open db connection
            server = couchdb.Server(server_connection_address)

            # set source db name / destination db name
            if translation_type == 'voci':
                source_db_name = settings_local.accepted_servers[server_name]['normalized_titoli_db_name']
            else:
                source_db_name = settings_local.accepted_servers[server_name]['raw_db_name']

            source_db = server[source_db_name]
            print "Source DB connection ok: db name: "+source_db_name+"!"


            #get json file from couchdb view
            #transform json view into csv
            #get csv file from google drive spreadsheet
            #merge the two csv files
            #output csv file



        else:
            print "server not accepted:"+server_name
    else:
        print "Type not accepted: " + translation_type


# launches main function
if __name__ == "__main__":
   main(sys.argv[1:])
