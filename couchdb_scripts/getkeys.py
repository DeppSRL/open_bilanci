from os import listdir
from os.path import isfile, join
import socket
import sys
import couchdb
import argparse
from couchdb.design import ViewDefinition
from pprint import pprint
from settings_local import *



def main(argv):
    parser = argparse.ArgumentParser(description='Get Titolo names and voce labels from bilanci')
    server_name = None
    check_function= None

    views_folder = 'views'

    # crea un vettore con le accepted views sulla base dei file contenuti in views ed escludendo i file temporanei
    accepted_views = [ f.replace('.js','') for f in listdir(views_folder) if isfile(join(views_folder,f)) and f.find('~') == -1 ]



    accepted_language = ['python','javascript']


    parser.add_argument('--server','-s', dest='server_name', action='store',
               default='localhost',
               help='Server name: localhost | staging')

    parser.add_argument('--function','-f', dest='function', action='store',
               default='voci_preventivo',
               help='Function to sync: '+  ' | '.join(accepted_views) )

    parser.add_argument('--database','-db', dest='database', action='store',
               default='voci',
               help='Db to use: raw | titoli | voci | simple')

    parser.add_argument("--check-function","-ck", help="check function after synch",
                    action="store_true")

    args = parser.parse_args()
    server_name= args.server_name
    check_function= args.check_function
    function_to_sync = args.function
    database_type = args.database
    

    if server_name in accepted_servers.keys():
        # costruisce la stringa per la connessione al server aggiungendo user/passw se necessario
        server_string ='http://'
        if accepted_servers[server_name]['user']:
            server_string+=accepted_servers[server_name]['user']+":"
            if accepted_servers[server_name]['password']:
                server_string+=accepted_servers[server_name]['password']+"@"

        server_string+=accepted_servers[server_name]['host']+":"+accepted_servers[server_name]['port']

        if function_to_sync in accepted_views:
            view_name = function_to_sync

            with file(views_folder+"/"+view_name+".js") as f: s = f.read()
            map_function = s

            print "Connecting to: "+server_string+" ..."
            # open db connection
            server = couchdb.Server(server_string)

            db_name = ''
            if database_type == 'raw':
                db_name = accepted_servers[server_name]['raw_db_name']
            if database_type == 'titoli':
                db_name = accepted_servers[server_name]['normalized_titoli_db_name']
            elif database_type == 'voci':
                db_name = accepted_servers[server_name]['normalized_voci_db_name']
            elif database_type == 'simple':
                db_name = accepted_servers[server_name]['simplified_db_name']

            if db_name == '':
                print "Db name not found. Quitting..."
                return
            else:
                try:
                    db = server[db_name]
                except socket.gaierror:
                    print "Connection ERROR. Quitting..."
                print "Db connection ok!"

            reduce_fun = '_count()'

            # sync the view
            view = ViewDefinition(view_name,
                                  view_name,
                                  map_fun=map_function,
                                  reduce_fun=reduce_fun,
                                  language='javascript',
            )

            view.sync(db)
            print "Sync done!"

            if check_function:
                # get view values
                check = db.view(view_name+'/'+view_name)
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
