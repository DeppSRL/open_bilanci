
Bilancio Voce tree structure
============================

The Bilancio is defined by a Mptt model: **Voce**.

The updated structure of the bilancio tree is defined in the csv file found in the following file

.. code-block:: bash

    /data/bilancio_voce_structure.csv
    
    
So when deploying the app from scratch the complete bilancio voce tree can be restored with the following steps

.. code-block:: bash
    
    psql -U postgres DATABASE_NAME
    COPY TABLE_NAME FROM '/path/to/csv/file.csv' DELIMITER ',' CSV;


Updating Voce tree structure
============================

When changing or updating the structure of the Bilancio Voce tree the following steps are required to have a smooth transition
from the old tree to the new one.

1. Update the AlberoSemplificato Google document. Open the following link and add the voices in the right sheet of the Gdoc (entrate, spese, riassuntivo).

.. code-block:: bash

    https://docs.google.com/spreadsheet/ccc?key=0ApDnbg0qraKMdHVDUEtlLWVzYWJkNUhWVE5lei1lTVE#gid=0


2. Associate the normalized Voci with the new leaves in the simplified tree in the Semplificazione bilancio depp Google doc

.. code-block:: bash

    https://docs.google.com/spreadsheet/ccc?key=0An-5r4iUtWq7dFBoM2prSkZWcEc5Vmd5aU9iSXNOdHc&usp=drive_web#gid=30


3. Create a CSV file describing the new Voce objects to be created in the Postgres db. The file must have the following columns: slug,denominazione,slug_parent

4. Update the Voce table in the Postgres db using the following script

.. code-block:: bash

    python manage.py update_bilancio_tree -v2 --file=PATH/TO/FILE.CSV
