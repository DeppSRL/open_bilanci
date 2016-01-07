Data import: html -> Couch -> Pg
================================

Data are fetched from the source site and recorded as documents in a CouchDB Database. 
All tables are transformed into json structures.

Budget titles and labels are normalized, by finding the MCD, defining a mapping and replicating the
raw couchdb. This is a 2 steps process.

The final product of the normalization process is a normalized database on couchdb that
can be now reduced to a simplified form using a dedicated script (simplify.py).

Due to application needs and operational functionalities the non-relational database is transferred to a
relational Postgres db using the couch2pg.py script. The Postgres instance is the application db on which
the application relies to build HTML pages, compute indicators and cluster averages.

Data source
-----------
The source is http://finanzalocale.interno.it/ (response times are good).

The complete list of municipalities, with slugs and codes may be
extracted at: http://finanzalocale.interno.it/apps/floc.php/ajax/searchComune/


Fetch
-----
HTML documents are parsed with the ``scrapy`` parser called "finanzalocale" in the "scrapy" project.
The script ec2.py contains the code that deploys a number of AWS EC2 instances, deploy the scraper on them and launch
them with the correct parameters.

After cloning the repo, simply edit scrapy.cfg file and set the correct parameters, then run

.. code-block:: bash

    python ec2.py

Possible parameters for the scraper are the following

.. code-block:: bash

   cities=CITY_NAME 
   years=YEAR 
   type=BILANCIO_TYPE


Bilancio type parameter can have the following values:

- c | C for Consuntivo
- p | P for Preventivo


The ``finanzalocale/settings.py`` and ``finanzalocale/local_settings.py`` files contains configuration informations
about couchdb instances, Api keys and such.

The scraper ``bilancio_comune`` gets the bilancio pages and writes directly to Couchdb database called ``bilanci`` which 
is the raw database.

After the scraping activity is complete each scraper logs out the complete list of missing bilanci and missing Comune
for the selected year(s).

CouchDB compaction
------------------

After the scraping cycle is completed is strongly suggested to launch db compaction to reduce DB size and
computational time. 
To do that simply login into futon and select ``Compact & Cleanup`` from the menu.
A pop-window will be shown: choose ``Compact Database``.
This should reduce DB size from 20 GB to ~3 GB .

Missing bilanci
---------------

To identify the missing bilanci in the Couch database there is a specific management task called missing_bilanci.

.. code-block:: bash

    python manage.py missing_bilanci -cities=CITIES --years=YEARS --output-script=FILENAME


The management task generates a script file listing all the missing bilanci of all the Comuni for the specified years.

The output script file contains:

- the scrapy call to get the city bilancio from base_url
- the management task html2couch call to insert the city data into bilanci db

After missin_bilanci script has finished simply execute the script with

.. code-block:: bash

    ./FILENAME


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

    # load one of the view in view in couchdb_scripts/views in a given couchdb instance
    python getkeys.py -f [<view>] -db [raw|titoli|voci|simple] -s [localhost| staging]
    python getkeys.py -f [<view>] -db [raw|titoli|voci|simple] -s [localhost | staging]
    # browse to the view and wait for view generation to finish (status)
    

+ when the process is finished the couchdb view results have to be merged with the existing
  google drive documents on titoli / voci normalization.
  To perform the task simply run
  
  .. code-block:: bash
  
    python merge_keys.py -s [localhost | staging] -t [titoli | voci] -tb [preventivo |consuntivo] -o OUTPUT_CSV_FILE
    
+ The script generates a csv file that merges the existing google drive normalization spreadsheet and the couchdb view results.

+ The csv file is uploaded to **Google Drive**, creating a new sheet in the before mentioned spreadsheet
  and not-so-skilled operators can copy-paste the results into the original sheet following the procedure:

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


+ the mapping is read and used by the normalization management task,
  to create a new normalized couchdb database:

  .. code-block:: bash

    python manage.py couch_translate_keys --type=[titoli|voci] --cities=all --years=2003-2013 --force-google


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


Patching Consuntivo 2013
------------------------

After normalizing titoli and voci, before going on with simplification a patch is needed for Consuntivo 2013, which is contained in a management task.

Execute with

  .. code-block:: bash

    python manage.py consuntivo_13_patch --couchdb-server=staging
    

The script does the following:

+ for Q2 Entrate tributarie: gets the row "Totale a pareggio" and copies the values to the row "Totale", then removes the row "Totale a pareggio" which was inconvenient for the default simplification
+ for Q4 Impegni and Q4 Pag. Conto competenza: does the same thing as for Q2
+ for Q9 Quadro riasssuntivo gestione finanziaria: gets the row "Residui attivi" from the last three columns of Q11 "Totale" row because the Q9 table is malformed
+ for Q9 Quadro riasssuntivo gestione finanziaria: gets the row "Residui passivi" from the last three columns of Q12 "Totale" row because the Q9 table is malformed

Then saves the modified object back to couchdb.










Simplification
--------------

After normalizing titoli and voci labels, the result is a normalized but
comprehensive bilanci couchdb database (named ``bilanci_voci``).

The web application relies on a database which contains only a fraction of
the data contained in the normalized database, moreover the application db requires
a simplified structure in which some keys get summed up to a single key in the application db.

This last process converts the *normalized* ``bilanci_voci`` db,
the one with both voci and titoli normalized, to a *simplified* ``bilanci_simple`` db.

+ If the voci views were not copied to ``bilanci_voci`` db, push them to the db using

.. code-block:: bash
  
  python getkeys.py --server staging -f voci_preventivo -db voci
  python getkeys.py --server staging -f voci_consuntivo -db voci
    
+ To merge the actual normalized Voce slug with the simplified tree slug and update the simplification Gdoc spreadsheet simply run
  
  .. code-block:: bash
  
    python merge_keys.py -s [localhost | staging] -t simplify -tb [preventivo |consuntivo] -o OUTPUT_CSV_FILE
    
+ The script generates a csv file that merges the existing google drive simplification spreadsheet and the couchdb view results.

+ The csv file is uploaded to **Google Drive**, creating a new sheet in the before mentioned spreadsheet
  and not-so-skilled operators can copy-paste the results into the original sheet following the procedure:

  .. code-block:: bash

    # open gDrive spreadsheet
    # https://docs.google.com/spreadsheet/ccc?key=0An-5r4iUtWq7dFBoM2prSkZWcEc5Vmd5aU9iSXNOdHc&usp=drive_web#gid=9

    # import csv *consuntivo* to a new, blank sheet
    # select all and paste to *consuntivo* sheet

    # import csv *preventivo* to a new sheet
    # select all and paste to *preventivo* sheet

    # remove temporary sheets


+ the skilled operator proceeds to do the semplification mapping

+ the simplification mapping is read from google and used by the simplification script (``simplify.py``),
  to create the simplified couchdb instance:

  .. code-block:: bash

    python manage.py simplify --couchdb-server=staging --cities=roma --years=2004-2012 --verbosity=2

The simplification process logs every single import task in ``log/import_log`` and it is possible to extract
the unique warnings with the help of awk:

.. code-block:: bash

    grep WARNING ../log/import_logfile | grep "No matching" | awk '{for (i=5; i<NF; i++) printf $i " "; print $NF}' | sort | uniq


See details of the inner workings in the ``simplify`` task :ref:`here <simplify>`.

Conversion to relational database
---------------------------------

The database should now be converted one last time to fit in a relational database, in this case, Postgres.

The task is performed with the following command

.. code-block:: bash

    python manage.py couch2pg --cities=all --years=2003-2011 -v3


All the data contained in the couch db is then copied to Postgres database.

Development dataset
-------------------

Schema and data (bar Valori, which contains millions of records), can be restored from 2 dump files,
available under ``s3://open_bilanci``:

* ``ob_schema.sql`` and
* ``ob_data_novalori.sql``

A random set of cities codes can be extracted from the python shell_plus, with a single command line::

    import numpy as np
    cities = ",".join(
        np.hstack(
            [
                [t.split('--')[1] for t in
                    Territorio.objects.filter(cluster=c, territorio='C').order_by('?').values_list('cod_finloc', flat=True)[:10]
                ] for c in range(1, 10)
            ]
        )
    )

Then, assuming that the ``cities`` string has been **copied** in the clipboard,
the following management tasks will import all values from the couchdb instance; compute the median values
and the indicators::

    CITIES=<PASTE>
    python manage.py couch2pg --cities=$CITIES --years=2003-2013 -v2
    python manage.py median --years=2003-2013 -v2
    python manage.py indicators --cities=$CITIES --years=2003-2013 -v2

