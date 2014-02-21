from pprint import pprint
import sys
import argparse
import logging
import csv
from settings_local import *

# compares two csv files and find different rows
# couchdb file comes from the couchdb view
# gdrive file comes from google drive doc

def main(argv):
    parser = argparse.ArgumentParser(description='Compare couchdb-generated csv and google drive csv')


    parser.add_argument('--couch','-c', dest='couch_filename', action='store',
               default='',
               help='Insert couchdb file name')

    parser.add_argument('--drive','-d', dest='drive_filename', action='store',
               default='',
               help='Insert google drive file name')

    parser.add_argument('--quadri','-q', dest='quadri', action='store',
               default='',
               help='Quadri to consider. From 1 to 99. Use one of this formats: 1 or 1-6 or 1,2,6')


    args = parser.parse_args()


    input_files = {
        'couch':{
            'filename':args.couch_filename,
            'content':[],
            'rows_to_skip': 1,

        },
        'drive':{
            'filename':args.drive_filename,
            'content':[],
            'rows_to_skip': 2,
        },
    }


    quadri = range(1,100)
    if args.quadri:
        if "-" in args.quadri:
            (start_quadro, end_quadro) = args.quadri.split("-")
            quadri = range(int(start_quadro), int(end_quadro)+1)
        else:
            quadri = [int(q.strip()) for q in args.quadri.split(",") if 0 < int(q.strip()) < 100]



    # sets the numbers of columns based on the number of fields of the couch file
    columns_n = 0
    try:
        couch_file = open(input_files['couch']['filename'])
        couch_reader = csv.reader(couch_file, dialect=csv.excel)
        for row in couch_reader:
            columns_n = len(row)
            break

    except IOError:
        logging.error("Error: File does not exist: {0}".format(input_files['couch']['filename']))
        return



    for considered_input in input_files.keys():
        try:
            # reads the files and put in the content structure the string containing the relevant fields of the files
            # the couch file will be put entirely
            # the drive file will be stripped of unnecessary cols and rows

            with open(input_files[considered_input]['filename'], 'r') as content_file:
                csv_reader = csv.reader(content_file, dialect=csv.excel)
                c = 0
                for row in csv_reader:
                    if c >= input_files[considered_input]['rows_to_skip']:
                        light_row = row[:columns_n]
                        if int(light_row[1]) in quadri:
                            light_row[1] = light_row[1].zfill(2)
                            input_files[considered_input]['content'].append('_'.join(light_row))
                    c+=1

        except IOError:
            logging.error("Error: File does not exist: {0}".format(input_files[considered_input]['filename']))
            return


    # once the structures are constructed, it goes looking for missing row
    c= 0
    for couch_row in input_files['couch']['content']:
        trovato = False
        for drive_row in input_files['drive']['content']:
            if couch_row == drive_row:
                trovato = True

        if not trovato:
            logging.warning("Missing from drive: {0}".format(couch_row))
            c+=1

    logging.warning("Missing {0} lines from drive".format(c))

    c = 0
    for drive_row in input_files['drive']['content']:
        trovato = False
        for couch_row in input_files['couch']['content']:
            if couch_row == drive_row:
                trovato = True

        if not trovato:
            logging.warning("Missing from couch: {0}".format(drive_row))
            c +=1

    logging.warning("Missing {0} lines from couch".format(c))


















# launches main function
if __name__ == "__main__":
   main(sys.argv[1:])
