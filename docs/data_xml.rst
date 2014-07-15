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

Copying the values to Google Drive document
-------------------------------------------

Create a new Google drive spreadsheet **using the old format of Gdocs** so the document will have a url similar to 

.. code-block:: bash

    https://docs.google.com/spreadsheet/ccc?key=GOOGLE_DOCUMENT_KEY#gid=0

and not like

.. code-block:: bash

    https://docs.google.com/spreadsheets/d/GOOGLE_DOCUMENT_KEY/edit?usp=drive_web

**Note: if the document has the new tyep of url the following steps will NOT work at all**


The spreadsheet has to have 3 sheets called *Voci*, *Colonne*, *slug*.

The *Voci* sheet will have the following columns:


====================  ====================  =======  ==================  ==========  ========  =========
Voci
--------------------------------------------------------------------------------------------------------
 
quadro_denominazione  titolo_denominazione  cad_cod  voce_denominazione  quadro_cod  voce_cod  voce_slug

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

