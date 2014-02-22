This directory contains csv files to see whether the google docs
and the normalized voci are well aligned.

To extract the 4c quadro from the cached consuntivo.csv, and list only the voci,
removing the quotes, and sorting alphabetically ::

    cat ../gdocs_csv_cache/simple_map/consuntivo.csv | \
      grep "quadro-4-c-pagamenti-in-conto-residui" | \
      gawk -vFPAT='[^;]*|"[^"]*"' '{print $4}' | \
      sed -e 's/"//g' | sort > voci_consuntivo_q4c.csv

The comprehensive list of normalized voci is taken from couchdb with::

    curl -o voci_consuntivo.json \
      "http://staging.depp.it:5984/bilanci/_design/voci_consuntivo/_view/voci_consuntivo?group_level=2"

The it can be put into csv with::

    python json2csv.py -f=voci_consuntivo.json -t=voci


And the list of voci for the given quadro (q4c), can be extracted and massaged with::

    cat voci_consuntivo.csv | \
        grep "quadro-4-c-pagamenti-in-conto-residui" | \
        gawk -vFPAT='[^,]*|"[^"]*"' '{$4}' | \
        sed -e 's/"//g' | sort > voci_norm_q4c.csv


Other tree's sections can be extracted by specifying the quadro slug.


The same actions can be taken to fetch csv files for the preventivo subtree.


The two files can be compared by any **diff** application.
The diff application provided with pyCharm is particularly handy.


The script to generate the files to compare::

for Q in quadro-4-a-impegni quadro-4-b-pagamenti-in-conto-competenza quadro-4-c-pagamenti-in-conto-residui
do
    echo $Q
    cat ../gdocs_csv_cache/simple_map/consuntivo.csv | grep "$Q" | gawk -vFPAT='[^;]*|"[^"]*"' '{print $4}' | sed -e 's/"//g' | sort > voci-consuntivo-$Q.csv
    cat voci_consuntivo.csv | grep "$Q" | gawk -vFPAT='[^,]*|"[^"]*"' '{print $4}' | sed -e 's/"//g' | sort > voci-consuntivo-$Q.normalized.csv
done

for Q in quadro-5-a-impegni quadro-5-b-pagamenti-in-conto-competenza quadro-5-c-pagamenti-in-conto-residui
do
    echo $Q
    cat ../gdocs_csv_cache/simple_map/consuntivo.csv | grep "$Q" | gawk -vFPAT='[^;]*|"[^"]*"' '{print $4}' | sed -e 's/"//g' | sort > voci-consuntivo-$Q.csv
    cat voci_consuntivo.csv | grep "$Q" | gawk -vFPAT='[^,]*|"[^"]*"' '{print $4}' | sed -e 's/"//g' | sort > voci-consuntivo-$Q.normalized.csv
done
