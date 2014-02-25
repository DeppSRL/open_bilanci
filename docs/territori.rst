Territori
====

Territori are a set of locations read from openpolis API.


Initialization
----

To initialize the db value use the following command


.. code-block:: bash

    python manage.py importlocations


Set Finanza Locale code
----

Second step is to add to basic location data the Finanza Locale code for each Comune.
The said code is a unique string used to identify a single Comune on Finanza Locale website.


.. code-block:: bash

   python manage.py setfinloc

