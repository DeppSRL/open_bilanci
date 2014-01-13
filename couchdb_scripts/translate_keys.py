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
    server_name = None
    check_function= None


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


    accepted_functions = {
        'titoli':{
            'gdoc_url':'',

        }
    }


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
        # destination_db = server[accepted_servers[server_name]['destination_db_name']]
        print "Db connection ok!"


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
        list_worksheet = list_sheet.get_worksheet(0)
        list_values = list_worksheet.get_all_values()


    else:
        print "no op:"+server_name+","+str(check_function)


# launches main function
if __name__ == "__main__":
   main(sys.argv[1:])
