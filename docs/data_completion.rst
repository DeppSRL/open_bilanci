

Additional data
===============

Once all the data resides in the application Postgres db there is few data which is needed to be imported to make the db
functional to Bilanci app:


-  Territorio context data taken from Comune bilancio consuntivo

.. code-block:: bash

  python manage.py context --cities=all --year=2001-2012 -v2

-  Territorio Openpolis id, necessary to get political data from Openpolis API

.. code-block:: bash

    python manage.py set_opid -v2


Then there are data which need to be computed on the data already present in the db

-  median values of bilanci for territori clusters

.. code-block:: bash

    python manage.py median --type=voci --years=2003-2013 -v2

- indicators, and indicators median values (see a description of the indicators computation internals on :ref:`here <indicators>`

.. code-block:: bash

    python manage.py indicators --cities=all --years=2003-2013 -v2
    python manage.py median --type=indicatori --indicators=all --years=2003-2013 -v2


- generating downloadable packages of CSV files

.. code-block:: bash

    python manage.py couch2csv --cities=all --years=2003-2013 --compress -v2

