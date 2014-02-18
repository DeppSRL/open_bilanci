Data
====
Data are fetched from the source as HTML files (no images, styles, or js scripts).
This is done in order to prevent damage whenever tehy should disappear from the source.

HTML files are then parsed into couchdb documents. All tables are transformed into json structures.

Budget titles and labels are normalized, by finding the MCD, defining a mapping and replicating the
raw couchdb. This is a 2 steps process.

The final product is a normalized set of budget documents, available on couchdb (through a RESTFUL API),
that can be used both as source to build HTML page and to compute indicators and averages (through map-reduce).


Data source
-----------
The source is http://finanzalocale.interno.it/ (response times are good).

The complete list of municipalities, with slugs and codes may be
extracted at: http://finanzalocale.interno.it/apps/floc.php/ajax/searchComune/


Fetch
-----
HTML documents are parsed with the ``scrapy`` parser:

.. code-block:: bash

    cd /home/open_bilanci/scraper_project
    scrapy crawl bilanci_pages

The ``scraper/settings.py`` file contains instruction on the source URIs,
what to scrape (years and cities) and where to put the results:

.. code-block:: bash

    OUTPUT_FOLDER = 'scraper/output/'
    LISTA_COMUNI = 'listacomuni.csv'
    BILANCI_PAGES_FOLDER = '/home/open_bilanci/dati/finanzalocale'

    # preventivi url
    URL_PREVENTIVI_PRINCIPALE = "http://finanzalocale.interno.it/apps/floc.php/certificati/index/codice_ente/%s/anno/%s/cod/3/md/0/tipo_modello/U"
    # consuntivi url
    URL_CONSUNTIVI_PRINCIPALE ="http://finanzalocale.interno.it/apps/floc.php/certificati/index/codice_ente/%s/anno/%s/cod/4/md/0/tipo_modello/U"

    START_YEAR_SPIDER = 2002
    END_YEAR_SPIDER = 2003
    
The settings can be overridden and selected cities and years can be fetched::

.. code-block:: bash

    cd /home/open_bilanci/scraper_project
    scrapy crawl bilanci_pages -a cities=1020040140 -a years=2004
    scrapy crawl bilanci_pages -a cities=roma,milano,napoli -a years=2004,2005
    scrapy crawl bilanci_pages -a cities=roma -a years=2004-2009
 
    

Mirror
------
Fetched HTML files are published at http://finanzalocale.mirror.openpolis.it/, through an Nginx server
on the ``staging.depp.it`` machine. The config file is ``/etc/nginx/sites-enabled/finanzalocale``.
The documents path is specified in ``BILANCI_PAGES_FOLDER``.

The estimated size of the HTML files is ~100GB (9Gb per year).


Missing bilanci
---------------

To identify the missing bilanci in the Couch database there is a specific management task called missing_bilanci.

.. code-block:: bash

    python manage.py missing_bilanci -cities=CITIES --years=YEARS


The management task generates a text file listing all the missing bilanci of all the Comuni for the specified years.

Then to scrape selectively all the missing bilanci with Scrapy we have to execute the following command:


..  code-block:: bash

    cat missing_bilanci | awk '{print $8, $9}' | \
      sed "s/Comune://" | sed "s/, yr:/ /" | \
      awk -F"--" '{print $2}' | \
      awk '{print "scrapy crawl bilanci_pages -a cities=" $1 "-a years=" $2}' >\
      fetch_missing_bilanci.sh


Parse into couchdb
------------------
Data are parsed from HTML into the couchdb local server with the html2couch management task:

.. code-block:: bash

    cd /home/open_bilanci/bilanci_project
    python manage.py html2couch --cities=all --years=2003-2011 -v3 --base-url=http://finanzalocale.mirror.openpolis.it
    python manage.py html2couch --cities=Roma --years=2003,2004 -v2
    
The default value for the ``base_url`` parameter is http://finanzalocale.mirror.openpolis.it.
The couchdb server is always localhost.

Overall couchDB size for the parsed documents is around 3GB.


Normalization
-------------

Bilanci data *normalization* is required because data from different cities and years vary in structure and labelling.
The raw data, as parsed from HTML, are normalized twice in this project, once for **titoli** and, successively,
another time for **voci** labels.

A single normalization process consists of these steps (the procedure descriptions are valid both for
titoli and for voci):

+ a **view** on the source couchdb builds the set of all possible values of the keys,
  counting keys occurrences in the process, with a ``_sum`` reduce function:

  .. code-block:: bash


    # start in the right directory
    cd couchdb_scripts

    # load views in couchdb bilanci
    python getkeys.py -f [titoli_preventivo|vista_preventivo]
    python getkeys.py -f [titoli_consuntivo|vista_consuntivo]
    # browse to the view and wait for view generation to finisc (status)

    # save views to json files (may take time, if launched for the first time)
    curl -o output/[titoli|voci]_consuntivo.json http://staging.depp.it:5984/bilanci/_design/[titoli|voci]_consuntivo/_view/[titoli|voci]_consuntivo?group_level=4
    curl -o output/[titoli|voci]_preventivo.json http://staging.depp.it:5984/bilanci/_design/[titoli|voci]_preventivo/_view/[titoli|voci]_preventivo?group_level=4

+ the results of the view documents are converted from json to csv with the script ``json2csv.py``:

  .. code-block:: bash


    # convert json file to csv (the name is unchanged)
    python json2csv.py -f=output/[titoli|voci]_consuntivo.json -t=[titoli|voci]
    python json2csv.py -f=output/[titoli|voci]_preventivo.json -t=[titoli|voci]

+ the csv file is uploaded to **Google Drive**, creating a new spreadsheet
  and skilled operators perform the many-to-one key mapping, based on keys typography:

  .. code-block:: bash

    # open gDrive spreadsheet
    # titoli
    # https://docs.google.com/spreadsheet/ccc?key=0An-5r4iUtWq7dEJ4LVRpRGpQcjdRTE40Vkh5UElmYUE&usp=drive_web#gid=0
    # voci
    # https://docs.google.com/spreadsheet/ccc?key=0An-5r4iUtWq7dFRYTTJyakhULWpZTFBjS3RYZFduLUE&usp=drive_web#gid=10

    # import csv *consuntivo* to a new, blank sheet
    # select all and paste to *consuntivo* sheet

    # import csv *preventivo* to a new sheet
    # select all and paste to *preventivo* sheet

    # remove temporary sheets

    # let the skilled operators operate (skillfully)

+ the mapping is read and used by the normalization script (``translate_keys.py``),
  to create a new normalized couchdb database:

  .. code-block:: bash

    python translate_keys.py -t [titoli|voci]


The Google Document mapping spreadsheet must have a fixed structure for the algorithm to work.

Titoli and Voci structures are different.

Titoli's columns:

+ Tipo bilancio ( preventivo / consuntivo)
+ Quadro, zero-filled ( es. '04')
+ Titolo name
+ normalized Titolo name


Voci's columns:

+ Tipo bilancio ( preventivo / consuntivo)
+ Quadro, zero-filled ( es. '04')
+ normalized Titolo name
+ Voce name
+ normalized Voce name


Simplification
--------------

After normalizing titoli and voci labels, the result is a normalized but
comprehensive bilanci couchdb database (named ``bilanci_voci``).

The web application relies on a database which contains only a fraction of
the data contained in the normalized database, moreover the application db requires
a simplified structure in which some keys get summed up to a single key in the application db.

This last process converts the *normalized* ``bilanci_voci`` db,
the one with both voci and titoli normalized, to a *simplified* ``bilanci_simpl`` db.

+ the ``voci_preventivo`` and ``voci_consuntivo`` views are *copied* automatically from the ``bilanci_titoli`` couchdb
  when the ``translate_key`` script is invoked.
+ the views are generated, by browsing and the json documents are downloaded:

  .. code-block:: bash


    # browse to the view and wait for view generation to finisc (status)

    # save views to json files (may take time, if launched for the first time)
    curl -o output/voci_consuntivo_norm.json http://staging.depp.it:5984/bilanci_voci/_design/voci_consuntivo/_view/voci_consuntivo?group_level=4
    curl -o output/voci_preventivo_norm.json http://staging.depp.it:5984/bilanci_voci/_design/voci_preventivo/_view/voci_preventivo?group_level=4

+ the resulting documents are converted from json to csv:

  .. code-block:: bash

    # convert json file to csv (the name is unchanged)
    python json2csv.py -f=output/voci_consuntivo_norm.json -t=voci
    python json2csv.py -f=output/voci_preventivo_norm.json -t=voci

+ the CSV is uploaded to the gDoc spreadsheet:

  .. code-block:: bash

    https://docs.google.com/spreadsheet/ccc?key=0An-5r4iUtWq7dFBoM2prSkZWcEc5Vmd5aU9iSXNOdHc&usp=drive_web#gid=9

+ the skilled operator proceeds to do the semplification mapping

+ the simplification mapping is read from google and used by the simplification script (``simplify.py``),
  to create the simplified couchdb instance:

  .. code-block:: bash

    python manage.py simplify --couchdb-server=staging --cities=roma --years=2004-2012 --verbosity=2

The simplification process logs every single import task in ``log/import_log`` and it is possible to extract
the unique warnings with the help of awk:

.. code-block:: bash

    grep WARNING ../log/import_logfile | grep "No matching" | awk '{for (i=5; i<NF; i++) printf $i " "; print $NF}' | sort | uniq






