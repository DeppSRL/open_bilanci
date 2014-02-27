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


The script to generate the complete set of files::

    for Q in \
     quadro-2-bis \
     quadro-2-entrate-entrate-derivanti-da-accensioni-di-prestiti \
     quadro-2-entrate-entrate-derivanti-da-alienazione-da-trasferimenti-di-capitali-e-da-riscossioni-di-crediti \
     quadro-2-entrate-entrate-derivanti-da-contributi-e-trasferimenti-correnti-dello-stato-della-regione-e-di-altri-enti-pubblici-anche-in-rapporto-funzioni-delegate-dalla-regione \
     quadro-2-entrate-entrate-extratributarie \
     quadro-2-entrate-entrate-tributarie \
     quadro-3-spese-spese-correnti \
     quadro-3-spese-spese-in-conto-capitale \
     quadro-3-spese-spese-per-rimborso-prestiti \
     quadro-4-riepilogo-spese-correnti \
     quadro-4-riepilogo-spese-correnti-totale \
     quadro-4-riepilogo-spese-correnti-trasferimenti \
     quadro-4-riepilogo-spese-correnti-utilizzo-di-beni-terzi \
     quadro-5-riepilogo-spese-in-conto-capitale \
     quadro-5-riepilogo-spese-in-conto-capitale-totale \
     quadro-5-riepilogo-spese-in-conto-capitale-trasferimenti-di-capitali \
     quadro-5-riepilogo-spese-in-conto-capitale \
     quadro-6-generale-riassuntivo-entrate \
     quadro-6-generale-riassuntivo
    do
        echo $Q
        cat voci_preventivo_gdoc.csv | grep "$Q" | gawk -vFPAT='[^,]*|"[^"]*"' '{print $4}' | sed -e 's/"//g' | sort | uniq > voci-preventivo-$Q-gdoc.csv
        cat voci_preventivo.csv | grep "$Q" | gawk -vFPAT='[^,]*|"[^"]*"' '{print $4}' | sed -e 's/"//g' | sort | uniq > voci-preventivo-$Q.csv
    done


    for Q in \
     quadro-1-dati-generali \
     quadro-2-entrate-titolo-i-entrate-tributarie \
     quadro-2-entrate-titolo-ii-entrate \
     quadro-2-entrate-titolo-iii-entrate \
     quadro-2-entrate-titolo-iv-entrate \
     quadro-2-entrate-titolo-v-entrate \
     quadro-3 \
     quadro-4-a- \
     quadro-4-b- \
     quadro-4-c- \
     quadro-5-a- \
     quadro-5-b- \
     quadro-5-c- \
     quadro-6-an-
    do
        echo $Q
        cat voci_consuntivo_gdoc.csv | grep "$Q" | gawk -vFPAT='[^,]*|"[^"]*"' '{print $4}' | sed -e 's/"//g' | sort | uniq > voci-consuntivo-$Q-gdoc.csv
        cat voci_consuntivo.csv | grep "$Q" | gawk -vFPAT='[^,]*|"[^"]*"' '{print $4}' | sed -e 's/"//g' | sort | uniq > voci-consuntivo-$Q.csv
    done
