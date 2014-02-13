Templates
---------
The way templates are handled in ``django`` suggests a hierarchy of templates, extending from base.

The templates are listed, along with the components they include.

Blocks are within square brackets, with the default components shown after the column (i.e. [content: composizione]).


**base.html**
    - :ref:`main-menu`
    - [content]: -
    - :ref:`footer`


**home.html** (base.html) [url: /]
    - [content]: home_content


**bilanci/bilancio.html** (base.html) [url: /bilanci/comune-slug]
    - [content]:
        - :ref:`city-data`
        - [bilanci_navigation_menu]: :ref:`bilanci-menu` (composizione selected)
        - [sidebar_rollaway_menu]: :ref:`rollaway-menu-for-value-types`
        - [timeline]: :ref:`timeline`
        - [bilanci_content]:
            - :ref:`budget-composition-widget` (total)

**bilanci/entrate.html** (bilanci/bilancio.html) [url: /bilanci/comune-slug/entrate]
    - [bilanci_navigation_menu]: :ref:`bilanci-menu` (entrate selected)
    - [bilanci_content]:
        - :ref:`budget-composition-widget` (entrate)
        - :ref:`trend-and-analysis-charts` (entrate)

**bilanci/spese.html** (bilanci/bilancio.html) [url: /bilanci/comune-slug/spese]
    - [bilanci_navigation_menu]: :ref:`bilanci-menu` (spese selected)
    - [bilanci_content]:
        - :ref:`budget-composition-widget` (spese)
        - :ref:`trend-and-analysis-charts` (spese)

**bilanci/entrate_dettaglio.html** (bilanci/entrate.html) [url: /bilanci/comune-slug/entrate_dettaglio]
    - [bilanci_content]:
        - :ref:`lines-chart-over-the-years` (entrate, average)
        - :ref:`accordion` (entrate)

**bilanci/spese_dettaglio.html** (bilanci/spese.html) [url: /bilanci/comune-slug/spese_dettaglio]
    - [bilanci_content]:
        - :ref:`lines-chart-over-the-years` (spese, average)
        - :ref:`accordion` (spese)

**bilanci/indicatori.html** (bilanci/bilancio.html) [url: /bilanci/comune-slug/indicatori]
    - [bilanci_navigation_menu]: :ref:`bilanci-menu` (indicatori selected)
    - [timeline]: -
    - [sidebar_rollaway_menu]: :ref:`rollaway-menu-with-for-indicators`
    - [bilanci_content]:
        - :ref:`lines-chart-over-the-years` (spese, average)
        - linear_charts (all selected indicators)
        - city_positions_charts

**bilanci/confronto.html** (base.html) [url: /confronti]
    - [sidebar_rollaway_menu]: -
    - [content]:
        - [cities_selector]: fully visible
        - [confronto_nav_menu]: -
        - [confronto_content]: -

**bilanci/confronto_entrate.html** (confronto.html) [url: /confronti/<slugA>/<slugB>/entrate]
    - [cities_selector]: clickable handle (js)
    - [confronto_nav_menu]: menu_with_entrate_selected
    - [confronto_content]:
        - lines_chart_over_the_years (entrateA, entrateB)
        - accordion_entrate_with_lines_charts (entrateA, entrateB)
        
        
**bilanci/confronto_spese.html** (confronto.html) [url: /confronti/<slugA>/<slugB>/spese]
    - [cities_selector]: clickable handle (js)
    - [confronto_nav_menu]: menu_with_spese_selected
    - [confronto_content]:
        - lines_chart_over_the_years (speseA, speseB)
        - accordion_spese_with_lines_charts (speseA, speseB)

**bilanci/confronto_indicatori.html** (confronto.html) [url: /confronti/<slugA>/<slugB>/indicatori/<indicator>]
    - [cities_selector]: clickable handle (js)
    - [confronto_nav_menu]: menu_with_indicatori_selected
    - [confronto_content]:
        - lines_chart_over_the_years (indicatorA, indicatorB)
        - position_in_charts (indicatorA, indicatorB)
