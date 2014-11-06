Deploy
========

Create Bilancio Voce table from scratch
---------------------------------------

When deploying Open bilanci on an empty database follow these steps:

- Get Voce structure from google documents, use this just for one city to the process is quick. **The Voce tables must be updated before the whole import takes place.**


.. code-block:: bash

    python manage.py couch2pg -v2 --create-tree --force-google --cities=roma --years=2003
    
    
- Updates Voce tables with new Voce, follow the order of the scripts. After these steps the Voce in the table must count 878 Voce objects.

.. code-block:: bash

    python manage.py update_bilancio_tree -v2 --file=data/20140717_nuove_voci_riassuntivo.csv
    python manage.py update_bilancio_tree -v2 --file=data/20140910_nuove_voci_debiti.csv
    

- Enter the backend and go to the Bilanci -> Voce admin panel.

- Move Preventivo - Spese up to be the first child of Preventivo

- Move Consuntivo - Spese up to be the first child of Consuntivo

- Check that Consuntivo - Riassuntivo is present

- Check that Voce tree is showing Voce correctly

- Disable DEBUG on .env file
- Restart uwsgi
- check DEBUG value in python shell

.. code-block:: bash

    python manage.py shell_plus

- Launch the import on all cities, all years
.. code-block:: bash

    python manage.py couch2pg -v2 --create-tree --force-google --cities=all --years=2003-2013
    
    

Create new branches of Bilancio Voce and import data
----------------------------------------------------


    
