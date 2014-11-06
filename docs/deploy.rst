Deploy
========

Create Bilancio Voce table from scratch
---------------------------------------


.. code-block:: bash

    python manage.py couch2pg -v2 --create-tree --force-google --cities=roma --years=2003
    
.. code-block:: bash

    python manage.py update_bilancio_tree -v2 --file=data/20140717_nuove_voci_riassuntivo.csv
    python manage.py update_bilancio_tree -v2 --file=data/20140910_nuove_voci_debiti.csv
    

.. code-block:: bash

    python manage.py couch2pg -v2 --create-tree --force-google --cities=roma --years=2003
    
    
    
