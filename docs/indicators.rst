Indicators
==========

Indicators are financial indexes that give a quick glance on the financial status of the Comune.

Each indicator is calculated with a mathematical formula inserted by an administrator in a specific back-end using
 the following standard:

  - each Voce of Bilancio that is inserted in the formula must be inserted using its slug between quotes and separated
  by other factors by spaces

  - when specifying a Voce to be used in the formula the absolute value of the voce is used by default
    when calculating the indicator value.
    If is needed to use the per-capita value the slug of the voice must be followed by the string "-PC"

Example with absolute value:

.. code-block::

   ("voce-slug-a" + "voce-slug--b") / ("voce-slug--c" - "voce-slug--d")



Example with per-capita value:

.. code-block::

   ("voce-slug-a-PC" + "voce-slug--b-PC") / ("voce-slug--c" - "voce-slug--d")



Once the indicator is inserted in the db the value must be calculated. This operation is done using a management
task in the following way

.. code-block:: bash

    python manage.py indicators -i [ALL | INDICATOR_NAME | INDICATOR_1,INDICATOR_2] --cities= [ALL | MILANO | MILANO,ROMA] --year=2001-2012 -v 3


Giving that an indicator is calculated on values of Voce of Bilancio, if at least one value is not available
for a Comune in a specified year then the indicator cannot be calculated and that year is skipped.
