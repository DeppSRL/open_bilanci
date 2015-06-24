Data XML -> Pg
==============

Data is fetched directly from specific xml files provided by the Comune.

The procedure that imports bilanci data from xml files to simplified Postgres database requires 
preparatory steps before the real import is performed.


Download Finanza locale official document
-----------------------------------------

The Xml file is based on alpahnumerical codes that identify *quadro*, *voce* and *colonna* for each bilancio value.

To create a map that associates that triple of codes to a slug the operator has to download the document that describes the bilancio that
has to be imported using this search engine:
http://finanzalocale.interno.it/apps/floc.php/circ

Select the year and search the result list for a document called

*Certificazioni del bilancio di previsione YEAR delle province, dei comuni, delle comunita' montane e delle unioni di comuni*

for preventivo 

or

*Decreto di approvazione dei modelli del certificato di conto di bilancio YEAR di Province, Comuni, Comunità Montane e Unioni di comuni*

for consuntivo

Click on the desired link and at the bottom of the page click and download the document called *Scarica il modello relativo ai Comuni e Unioni di comuni*.

That is the file that associates the official voce codes to bilanci voci.

Creating a dedicated Google Drive document
-------------------------------------------

Create a new Google drive spreadsheet **using the old format of Gdocs** so the document will have a url similar to 

.. code-block:: bash

    https://docs.google.com/spreadsheet/ccc?key=GOOGLE_DOCUMENT_KEY#gid=0

and not like

.. code-block:: bash

    https://docs.google.com/spreadsheets/d/GOOGLE_DOCUMENT_KEY/edit?usp=drive_web

**Note: if the document has the new tyep of url the following steps will NOT work at all**


Share the Gdoc with openpolis.script@gmail.com with "edit" permits and the users working on the doc.

The spreadsheet has to have 3 sheets called *Voci*, *Colonne*, *slug*.

The *Voci* sheet will have the following columns:


====================  ====================  =======  ==================  ==========  ========  =========
Voci
--------------------------------------------------------------------------------------------------------
 
quadro_denominazione  titolo_denominazione  cat_cod  voce_denominazione  quadro_cod  voce_cod  voce_slug

====================  ====================  =======  ==================  ==========  ========  ========= 


The *Colonne* sheet will have the following columns:

====================  ==========  =======  =================  ====
Colonne
------------------------------------------------------------------
 
quadro_denominazione  quadro_cod  col_cod  col_denominazione  slug

====================  ==========  =======  =================  ==== 



The *slug* sheet will have the following columns:

+------+ 
| slug | 
+======+ 
| slug | 
+------+ 


Copying the values to the Google Drive document
-----------------------------------------------

Open the pdf file and copy-paste the 

**quadro_denominazione, titolo_denominazione, cat_cod, voce_denominazione, quadro_cod, voce_cod**

values in the right cells for *Voci* and for colonne

**quadro_denominazione, quadro_cod, col_cod, col_denominazione**

for *Colonne* sheets.

About the **slugs** sheet:  get the normalized slugs contained in the Voce table relative to the bilancio type considered.
For the voce that have more than one column keep only the slugs relative to the first column.

**Example:**
Insert


.. code-block:: bash

    consuntivo-entrate-accertamenti-contributi-pubblici

But skip


.. code-block:: bash

    consuntivo-entrate-riscossioni-in-conto-competenza-contributi-pubblici
    consuntivo-entrate-riscossioni-in-conto-residui-contributi-pubblici

The association script will make automagically the association.


Bilancio Codes - simplified slugs association for Voci
------------------------------------------------------

This step requires that a skilled operator associates the normalized slugs with the voci in the *Voci* sheet 
keeping in mind the rule aforementioned: **the slug used in the Voci sheet must be only the ones relative to the first column of the table, 
association for other columns will happen automatically**.

For example:

QUADRO 9 - QUADRO RIASSUNTIVO DELLA GESTIONE FINANZIARIA has 3 columns: 

.. code-block:: bash

    Gestione Residui

    Gestione Competenza

    Gestione Totale


The voci in the Voci sheet must be associated only with gestione residui branch slugs.
In the colonne sheet just report the part of slug that must be replaced.

For example:
voce_slug is

.. code-block:: bash

    consuntivo-riassuntivo-gestione-finanziaria-gestione-competenza-riscossioni

colonne_slugs should be

.. code-block:: bash

    gestione-residui

    gestione-competenza

    gestione-totale


**Special cases: Q4/ Q5**

If the voci are the same in Q4/Q5 then fill in just the voci for Q4 Impegni.
The other voci will be filled automatically by xml2slug management task.


For the columns: interventi are different for spese correnti / spese per investimenti so fill in columns for Q4 Impegni and Q5 Impegni.
The other columns will be filled automatically by xml2slug management task.

**IMPORTANT NOTE**

The method of filling the column sheet is different for Q4/Q5: 
fill in the exact slug of the intervento for the impegni table.

Example for Q4 Impegni:

.. code-block:: bash

    consuntivo-spese-impegni-spese-correnti-interventi-personale

    consuntivo-spese-impegni-spese-correnti-interventi-altre-spese-per-interventi-correnti

and for TOTALE (in Colonne sheet)

.. code-block:: bash

    consuntivo-spese-impegni-spese-correnti-interventi

Example for Q5 Impegni:

.. code-block:: bash

    consuntivo-spese-impegni-spese-per-investimenti-interventi-acquisizione-di-beni-immobili

    consuntivo-spese-impegni-spese-per-investimenti-interventi-altri-investimenti-per-interventi

and for TOTALE (in Colonne sheet)

.. code-block:: bash

    consuntivo-spese-impegni-spese-per-investimenti-interventi


Bilancio Codes - simplified slugs association for Colonne
---------------------------------------------------------


The sheet *Colonne* requires the association of column names with partial slugs.

Example:


+-------------------------------------------+------------+---------+---------------------------+-------------------------------------+ 
| quadro_denominazione                      | quadro_cod | col_cod | col_denominazione         | slug                                | 
+===========================================+============+=========+===========================+=====================================+
| QUADRO 4 - SPESE CORRENTI - (A) - IMPEGNI | 04         | 4       | Utilizzo di beni di terzi | altre-spese-per-interventi-correnti |
+-------------------------------------------+------------+---------+---------------------------+-------------------------------------+ 



Integrating the Document with Django app
----------------------------------------

Copy the document key and create a new constant value in the **.env** file

.. code-block:: bash

    GDOC_BILANCIO_BILANCIOTYPE_YEAR=GOOGLE_DOCUMENT_KEY
    
    example:
    
    GDOC_BILANCIO_CONSUNTIVO_2013=GOOGLE_DOCUMENT_KEY


Update the .env.sample file.

Adds the constant in the **settings/base.py** file using the same name but lowercase

.. code-block:: bash

    # Google Docs keys
    GDOC_KEYS= {
        'titoli_map': env('GDOC_TITOLI_MAP_KEY'),
        'voci_map': env('GDOC_VOCI_MAP_KEY'),
        'simple_map':env('GDOC_VOCI_SIMPLE_MAP_KEY'),
        'simple_tree':env('GDOC_VOCI_SIMPLE_TREE_KEY'),
        'bilancio_consuntivo_2013':env('GDOC_BILANCIO_CONSUNTIVO_2013'),
        ## INSERT NEW VALUE HERE ##
        'bilancio_bilanciotype_year':env('GDOC_BILANCIO_BILANCIOTYPE_YEAR'),
    }

In this way the Google doc is now accessible by management tasks.


Generate the code-slug map
--------------------------

When the association is over and checked then run the following script to generate the association between official 
codes and normalized slugs.

.. code-block:: bash

    python manage.py xml2slug --type=[C|P] --year=YEAR  -v3 --force-google
    
This management task will access the google document, download the map in a simple csv file and creates the associations that were implicit:
for example those regarding funzioni / interventi.

The values created will be stored in the CodiceValore table in Postgres DB.

Xml import
----------

After the association map has been created launch the xml import with

.. code-block:: bash

    python manage.py xml2pg --file=FILEPATH.XML -v2
    
There is no need to specify territorio, year or bilancio type because those info are stored in the xml file.



				
