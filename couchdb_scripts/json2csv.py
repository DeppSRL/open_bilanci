from pprint import pprint
import sys
import argparse
import csv
import json
import utils
from settings_local import *


def main(argv):
    parser = argparse.ArgumentParser(description='Convert json file to csv for titoli and voci')


    parser.add_argument('--filename','-f', dest='filename', action='store',
               default='',
               help='Insert json file name')

    parser.add_argument('--type','-t', dest='type', action='store',
               default='voci',
               help='Type to convert: titoli | voci')


    args = parser.parse_args()
    json_filename= args.filename
    translation_type= args.type


    if translation_type in accepted_types.keys():

        print "Open json file: "+json_filename
        try:
            # apre il file json
            with open(json_filename, 'r') as content_file:
                json_file_content = content_file.read()
        except IOError:
            print "Error: File does not exist: "+json_filename
            return

        json_data = json.loads(json_file_content)
        csv_filename = json_filename.replace('json', 'csv')
        csv_file = open(csv_filename, "wb+")
        udw = utils.UnicodeDictWriter(csv_file, accepted_types[translation_type]['csv_keys'], dialect=csv.excel, encoding="utf-8")

        # scrive l'intestazione
        udw.writeheader()
        print "Write CSV file: "+csv_filename
        for json_row in json_data['rows']:

            # fa lo split del valore sull'underscore
            row_keys = json_row['key'][0].split('_')
            # aggiunge al vettore la colonna con il valore
            # in questo modo il vettore row_keys ha tutti i valori splittati che ci servono
            # per i titoli
            # tipo, quadro, titolo, titolo normalizzato
            # per le voci
            # tipo, quadro, titolo, voce, voce normalizzata
            row_keys.append(json_row['key'][1])
            csv_dict = {}

            if len(row_keys) == len(accepted_types[translation_type]['csv_keys']):
                
                for (counter, key) in enumerate(accepted_types[translation_type]['csv_keys']):
                    csv_dict[key]=''
                    csv_dict[key]=row_keys[counter]

                udw.writerow(csv_dict)
            else:
                print "Error: number of keys in settings != number of keys in Json file, exiting..."
                return

        print "Finished writing file: "+csv_filename
    else:
        print "Error: Type "+translation_type+" not accepted"





# launches main function
if __name__ == "__main__":
   main(sys.argv[1:])
