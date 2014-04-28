.. _indicators:

Indicators
==========

Indicators are financial indexes that give a quick glance on the financial status of the Comune.

Insertion
---------

Each indicator's value is calculated with mathematical formulas inserted in the ``get_formula_result`` values
of the ``Indicator`` classes in the ``bilanci.indicators`` module.

All Indicator classes extend a common ``BaseIndicator`` class, that contains methods to compute the values for
each city and year.

To add a new indicator, just create a new class, and specify the ``slug`` and ``label`` attributes.
They will be used both in the frontend and in the backend of the web app.

The ``get_formula_result`` method can contain all the logic to compute the value, of an indicator,
given a city and a year. Thr ``data_dict`` structure contains all the values for the slugs
used in the formula, the must be listed in the ``used_slugs`` dictionay.

.. code-block:: python

    class AutonomiaFinanziariaIndicator(BaseIndicator):
        """
        (
         consuntivo-entrate-accertamenti-imposte-e-tasse +
         consuntivo-entrate-accertamenti-entrate-extratributarie
        )
        /
        (consuntivo-entrate-accertamenti-imposte-e-tasse +
         consuntivo-entrate-accertamenti-entrate-extratributarie +
         consuntivo-entrate-accertamenti-contributi-pubblici
        ) * 100
        """
        slug = 'autonomia-finanziaria'
        label = 'Autonomia finanziaria'
        used_voci_slugs = {
            'it': 'consuntivo-entrate-accertamenti-imposte-e-tasse',
            'ex': 'consuntivo-entrate-accertamenti-entrate-extratributarie',
            'pb': 'consuntivo-entrate-accertamenti-contributi-pubblici'
        }

        def get_formula_result(self, data_dict, city, year):
            it = self.get_val(data_dict, city,  year, 'it')
            ex = self.get_val(data_dict, city, year, 'ex')
            pb = self.get_val(data_dict, city, year, 'pb')
            return 100.0 / ( 1.0 + pb / ( it + ex ) )


Calculation
-----------

Once the indicator is added to the code, the values must be calculated.
This operation is done using a management task in the following way:

.. code-block:: bash

    python manage.py indicators -i[ALL | INDICATOR_NAME | INDICATOR_1,INDICATOR_2] --cities=all --years=2003-2013 -v2

Giving that an indicator is calculated on values of Voce of Bilancio, if at least one value is not available
for a Comune in a specified year then the indicator cannot be calculated and that year is skipped.
