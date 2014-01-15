
import sys
import argparse
import csv
import json
import utils


def main(argv):
    parser = argparse.ArgumentParser(description='Convert json file to csv for titoli and voci')


    parser.add_argument('--filename','-f', dest='filename', action='store',
               default='',
               help='Insert json file name')

    parser.add_argument('--type','-t', dest='type', action='store',
               default='voci',
               help='Type to convert: titoli | voci')


    accepted_types={
        'voci':{
            'keys':["tipo_quadro_titolo", "voce",]
        },
        'titoli':{
            'keys':["tipo_quadro", "titolo",]
        }
    }

    args = parser.parse_args()
    json_filename= args.filename
    # todo fare anche la versione per i titoli
    type= args.type


    if type in accepted_types.keys():

        # apre il file json
        with open(json_filename, 'r') as content_file:
            json_file_content = content_file.read()

        json_data = json.loads(json_file_content)
        csv_file = open(json_filename.replace('json', 'csv'), "wb+")

        udw = utils.UnicodeDictWriter(csv_file, ["tipo_quadro_titolo", "voce",], dialect=csv.excel, encoding="utf-8")

        for row in json_data['rows']:

            mydict = { "tipo_quadro_titolo": row['key'][0], "voce": row['key'][1] }
            udw.writerow(mydict)
    else:
        print "Error: Type "+type+" not accepted"





# launches main function
if __name__ == "__main__":
   main(sys.argv[1:])
