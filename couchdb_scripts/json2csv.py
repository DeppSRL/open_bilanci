__author__ = 'stefano'

import csv
import json


# questo script prende i risultati del design document titoli getkeys e genera un file CSV
json_filename = 'output/staging_cons_titoli_getkeys.json'

with open(json_filename, 'r') as content_file:
    json_file_content = content_file.read()

json_data = json.loads(json_file_content)

f = csv.writer(open("output/bilanci_quadri_titoli_map.csv", "wb+"))

# Write CSV Header, If you dont need that, remove this line
f.writerow(["tipo_bilancio", "quadro", "titolo",])

for row in json_data['rows']:
    f.writerow([row["key"][0],
                row["key"][1],
                row["key"][2],
                ])