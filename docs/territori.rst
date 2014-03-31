Territori
=========

Territori are a set of locations read from openpolis API.


Initialization
--------------

To initialize the db value use the following command


.. code-block:: bash

    python manage.py importlocations


Set Finanza Locale code
-----------------------

The following step is to add to basic location data the Finanza Locale code for each Comune.
The said code is a unique string used to identify a single Comune on Finanza Locale website.


.. code-block:: bash

   python manage.py setfinloc
   

Set Openpolis Id
----------------

Open Bilanci needs to use Openpolis API3 to get data about Politicians in charge along the years in the Comune. 
To do that every Territorio needs to have an Openpolis id, which is set as follows.

.. code-block:: bash

    python manage.py set_opid [--auth=USER:PASS]



Context
=======

Each Territorio for each year has demographic context data read from Bilanci and from Istat.

Apart from that each Territorio has political context data read from Openpolis Api.


Istat data
----------

Istat data are: inhabitants, male inhabitants and female inhabitants for each year, and are set as follows:



.. code-block:: bash

    python manage.py set_istat --years=YEARS_START-YEAR_END
    
    
Bilanci data
------------

Bilanci data are 

- number of families (nuclei familiari)
- urban area (superficie urbana)
- total area (superficie totale)
- external streets length (strade esterne)
- internal streets length (strade interne)
- mountain streets length (strade montane)

These fields are set as follows:

.. code-block:: bash

    python manage.py data_completion -f contesto --years=YEARS_START-YEAR_END --cities=CITIES_LIST
    

Political charges
-----------------

Political charges are modeled with a specific class: Incarico.

Incarico objects are read from Openpolis Api, merging the charges for 'Sindaco' and 'Commissario straordinario' charge type.
The charges are then validated checking that no charges overlap for the same Territorio.

Incarico model is imported from API as follows:


.. code-block:: bash

    python manage.py import_incarichi -v 2 [--type=all|capoluoghi|others] [--delete] [--dry-run]
    
