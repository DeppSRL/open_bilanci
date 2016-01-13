Data testing
============

To check that the mapping for Titoli/Voci is correctly set on the GDOC a couple of test have been implemented.

These tests run before translate keys script is called and compare the current GDOC mapping with the reference CSV files in data/reference folder.

If in the GDOC there are titoli/voci not present in the reference CSV file an error is issued and the trasfer stopped.
If in the reference CSV there are titoli/voci not present in the GDOC map an error is issued and the trasfer stopped.

Verify normalization maps for titoli/voci
-----------------------------------------

Matches the reference CSV map (stored in /data/reference_test/...) with the actual Gdocs mapping.
Verify that all the rows in the CSV are present in the GDOC and that all rows in the GDOCS are present in the CSV.

Verify mapping with 

.. code-block:: bash

    python manage.py test_titoli_voci -v2 --type=[t|v] --force-google


*NOTE:* normally there is no need to launch this test because it is launched automatically when the task "translation" is launched, before the whole process starts. If the test fails the translation is aborted.




Verify simple
-------------
Verify sums between voci-normalized bilanci and simplified bilanci with 


.. code-block:: bash

    python manage.py verify_simple -v2 --cities=CITY_NAME --years=STARTYEAR-ENDYEAR


