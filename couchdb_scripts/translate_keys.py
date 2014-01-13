import sys
import couchdb
import json
import gspread
import argparse
from couchdb.design import ViewDefinition
from pprint import pprint
from settings_local import *


def main(argv):
    parser = argparse.ArgumentParser(description='Translate bilanci keys, copying elements from a db to a new one')

    accepted_servers = {
        'localhost': {
            'host': 'localhost',
            'port': '5984',
            'user': '',
            'password':'',
            'source_db_name':'bilanci_raw',
            'destination_db_name':'bilanci_raw_titoli'

        },
        'staging': {
            'host': 'staging.depp.it',
            'port': '5984',
            'user': 'op',
            'password':'op42',
            'source_db_name':'bilanci',
            'destination_db_name':'bilanci_titoli'
        },
    }

    translation_map = {}

    parser.add_argument('--server','-s', dest='server_name', action='store',
               default='localhost',
               help='Server name: localhost | staging')

    parser.add_argument("--create-db","-create", help="create new destination db",
                    action="store_true")

    parser.add_argument("--copy-design","-cpdd", help="include design documents in the copy process",
                    action="store_true")

    args = parser.parse_args()
    
    server_name= args.server_name
    create_db= args.create_db
    copy_design_docs = args.copy_design

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

                if row[0] not in translation_map:
                    translation_map[row[0]] = {}
                if row[1] not in translation_map[row[0]]:
                    translation_map[row[0]][row[1]] = {}
                if row[2] not in translation_map[row[0]][row[1]]:
                    translation_map[row[0]][row[1]][row[2]] = {}

                #  crea la mappa di conversione dei titoli
                translation_map[row[0]][row[1]][row[2]]=row[3]


        # connessione a couchdb
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
        source_db = server[accepted_servers[server_name]['source_db_name']]
        print "Source DB connection ok!"

        if create_db:
            # se esiste il db lo cancella
            if accepted_servers[server_name]['destination_db_name'] in server:
                del server[accepted_servers[server_name]['destination_db_name']]
                print  "Destination db: "+  accepted_servers[server_name]['destination_db_name'] +" deleted"
            # crea il db
            destination_db = server.create(accepted_servers[server_name]['destination_db_name'])
            print  "Destination db: "+  accepted_servers[server_name]['destination_db_name'] +" created"
        else:
            #     apre una connessione con destination db
            try:
                destination_db = server[accepted_servers[server_name]['destination_db_name']]
            except couchdb.http.ResourceNotFound:
                print "Destination db: "+  accepted_servers[server_name]['destination_db_name'] +" not found"
                return

    else:
        print "server not accepted:"+server_name


# launches main function
if __name__ == "__main__":
   main(sys.argv[1:])
