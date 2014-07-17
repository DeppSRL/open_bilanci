
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
