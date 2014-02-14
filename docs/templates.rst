Templates
=========
The way templates are handled in ``django`` suggests a hierarchy of templates, extending from base.

The extension point is indicated right after the template complete name, between round brackets.

The urls where the template is used are shown among square brackets, after the title.

The templates are listed, along with the UI elements they include. A link to the corresponding UI element
detailed description is present, when available.

Blocks are within square brackets, with the default components shown after the column (i.e. [content: composizione]).

Generic Templates
-----------------

**base.html**
    - :ref:`main-menu`
    - [content]: -
    - :ref:`footer`


**home.html** (base.html) [url: ``/``]
    - [content]: home_content


Bilanci templates
-----------------

**bilanci/bilancio.html** (base.html) [url: ``/bilanci/<comune-slug>``]
    - [content]:
        - :ref:`city-data`
        - [bilanci_navigation_menu]: :ref:`bilanci-menu` (bilancio selected)
        - [sidebar_rollaway_menu]: :ref:`rollaway-menu-for-value-types`
        - [timeline]: :ref:`timeline`
        - [bilanci_content]:
            - :ref:`budget-composition-widget` (total)

**bilanci/entrate.html** (bilanci/bilancio.html) [url: ``/bilanci/<comune-slug>/entrate``]
    - [bilanci_navigation_menu]: :ref:`bilanci-menu` (entrate selected)
    - [bilanci_content]:
        - :ref:`budget-composition-widget` (entrate)
        - :ref:`trend-and-analysis-charts` (entrate)

**bilanci/spese.html** (bilanci/bilancio.html) [url: ``/bilanci/<comune-slug>/spese``]
    - [bilanci_navigation_menu]: :ref:`bilanci-menu` (spese selected)
    - [bilanci_content]:
        - :ref:`budget-composition-widget` (spese)
        - :ref:`trend-and-analysis-charts` (spese)

**bilanci/entrate_dettaglio.html** (bilanci/entrate.html) [url: ``/bilanci/<comune-slug>/entrate_dettaglio``]
    - [bilanci_content]:
        - :ref:`lines-chart-over-the-years` (entrate, average)
        - :ref:`accordion` (entrate)

**bilanci/spese_dettaglio.html** (bilanci/spese.html) [url: ``/bilanci/<comune-slug>/spese_dettaglio``]
    - [bilanci_content]:
        - :ref:`lines-chart-over-the-years` (spese, average)
        - :ref:`accordion` (spese)

**bilanci/indicatori.html** (bilanci/bilancio.html) [url: ``/bilanci/<comune-slug>/indicatori``]
    - [bilanci_navigation_menu]: :ref:`bilanci-menu` (indicatori selected)
    - [timeline]: -
    - [sidebar_rollaway_menu]: :ref:`rollaway-menu-with-for-indicators` (multiple)
    - [bilanci_content]:
        - :ref:`lines-chart-over-the-years` (all selected indicators)
        - :ref:`city-positions-charts` (city, all selected indicators)

Confronti templates
-------------------

**bilanci/confronto.html** (base.html) [url: ``/confronti``]
    - [sidebar_rollaway_menu]: -
    - [content]:
        - [cities_selector]: :ref:`cities-selector` (fully visible)
        - [confronto_nav_menu]: -
        - [confronto_content]: -

**bilanci/confronto_entrate.html** (confronto.html) [url: ``/confronti/<slugA>/<slugB>/entrate``]
    - [cities_selector]: :ref:`cities-selector` (need to click on a handle to make it visible)
    - [confronto_nav_menu]: :ref:`confronti-menu` (entrate selected)
    - [confronto_content]:
        - :ref:`lines-chart-over-the-years` (entrateA, entrateB)
        - :ref:`accordion` (entrateA, entrateB)

        
**bilanci/confronto_spese.html** (confronto.html) [url: ``/confronti/<slugA>/<slugB>/spese``]
    - [cities_selector]: :ref:`cities-selector` (need to click on a handle to make it visible)
    - [confronto_nav_menu]: :ref:`confronti-menu` (spese selected)
    - [confronto_content]:
        - :ref:`lines-chart-over-the-years` (speseA, speseB)
        - :ref:`accordion` (speseA, speseB)

**bilanci/confronto_indicatori.html** (confronto.html) [url: ``/confronti/<slugA>/<slugB>/indicatori/<indicator>``]
    - [cities_selector]: clickable handle (js)
    - [confronto_nav_menu]: :ref:`confronti-menu` (indicatori selected)
    - [confronto_content]:
        - :ref:`lines-chart-over-the-years` (indicator for city A, indicator for city B)
        - :ref:`city-positions-charts` (cityA, cityB, indicator)
