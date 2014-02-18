Architecture Information
========================



Main sections
-------------

The web application has 4 main sections and a series of static pages::


                                  +------------+
                                  |            |
                                  |    HOME    |
                                  |            |
                                  +------------+
                                         |
                                         |
           +-------------------+---------+----------+--------------------+--------------------+
           |                   |                    |                    |                    |
    +------------+      +-------------+      +-------------+      +-------------+      +------------+
    |            |      |             |+     |             |      |             |      |            |+
    |    BLOG    |      |   BILANCI   ||+    | CLASSIFICHE |      |  CONFRONTI  |      |  STATICHE  ||+
    |            |      |             |||    |             |      |             |      |            |||
    +------------+      +-------------+||    +-------------+      +-------------+      +------------+||
                          +-----------+||                                                +-----------+|
                            +----------++                                                  +----------+


**Blog**
    The editorial section. A series of posts, authored by editors, with news around OpenBilanci.

**Bilanci**
    The section where the cities' budgets can be seen. There is no subhome, you get straight to
    the :ref:`single-city-budget-section`.

**Classifiche**
    Section with indicators charts.

**Confronti**
    Section where budgets and indicators of two different cities can be compared. See the :ref:`comparison-section`.

**Statiche**
    Static pages, containing FAQ, Licence Terms, API description, ...


.. _single-city-budget-section:

Single city budgets section
---------------------------

A single city budgets section is organized as such::



                                          +----------------+
                                          |                |
                                          |    (COMUNE)    |
                                          |                |
                                          +--------+-------+
                                                   |
                                                   |
                                                   |
             +-------------------------+-----------+------------+------------------------+
             |                         |                        |                        |
     +-------+--------+       +--------+-------+       +--------+-------+       +--------+-------+
     |                |       |                |       |                |       |                |
     |    BILANCIO    |       |    (ENTRATE)   |       |     (SPESE)    |       |   INDICATORI   |
     |                |       |                |       |                |       |                |
     +----------------+       +--------+-------+       +----------------+       +----------------+
                                       |
                                       |
                                       |
                                       |    +----------------+
                                       |    |                |
                                       +----+  COMPOSIZIONE  |
                                       |    |                |
                                       |    +----------------+
                                       |
                                       |
                                       |
                                       |    +----------------+
                                       |    |                |
                                       +----|    DETTAGLIO   |
                                            |                |
                                            +----------------+


**Bilancio**
    This is the starting point for the section.
    An overview visualization of the composition of the budget, with trends with respect
    to the previous budget (be it a *consuntivo* or a *preventivo*). Context and summarized data
    related to the city budget.

**Entrate** and **Spese**
    The two sections are almost identical and we'll only describe the entries.
    The sections start with the **Composizione** view.

**Composizione**
    A browseable visualization of the budget composition and
    some contextual information related to the entries (or the expenses).

**Dettaglio**
    The detailed view of the entries (or expenses). Composed of:

    + a linear graph showing the global values over the years,
      compared to average for the cluster;
    + an accordion with all the voices exploded and the possibility
      of showing a dedicated line graph for each single voice (click)

**Indicatori**
    The charts of all indicators for the budgets of the given city.
    All charts are over the years. More than one charts can be selected from a menu.

    The position of the city in the ranking, for each chart is rendered as a table,
    with the trend w.r. to the previous week.

    If indicated, the comparison with another city is shown.


.. _comparison-section:

Comparison section
------------------

The confronti section is where budgets and indicators for two different cities can be compared.
Year and date are not selected, since all the information here regards the whole temporal span.

The confronti section has a subhome and tree subsections::

                                +----------------+
                                |                |
                                |    CONFRONTO   |
                                |                |
                                +--------+-------+
                                         |
                                         |
                                         |
                +------------------------+------------------------+
                |                        |                        |
       +--------+-------+       +--------+-------+       +--------+-------+
       |                |       |                |       |                |
       |     ENTRATE    |       |      SPESE     |       |   INDICATORI   |
       |                |       |                |       |                |
       +--------+-------+       +----------------+       +----------------+

**Confronto**
    This is where the user can select the two cities. It's done through 2 auto-completer selectors.
    Once both the cities are selected and the button is pressed, the user is redirected to the Entrate section.

**Entrate**
    The sub-section showing the entries comparisons between the two cities.
    A lines chart for the comparison of the total entries over the years is shown on top.
    The accordion with the details of the entries budget trees shows a line charts for every voice.

**Spese**
    The sub-section showing the expenses comparisons between the two cities.
    The components in the page mirrors those shown in the Entrate section.
    Expenses are only shown by functions and not by investments (simplification).

**Indicatori**
    The sub-section showing the comparison between a single indicator.
    A random indicator is chosen at the beginning. The user can select the indicator through
    a slide away menu. Only one indicator can be chosen at a time.
    A lines chart shows how the indicator compares over the years.
    The position in the charts is shown for the selected indicator, with the trend over the last year.


Rankings section
----------------

::

                                +----------------+
                                |                |
                                |  (CLASSIFICHE) |
                                |                |
                                +--------+-------+
                                         |
                                         |
                                         |
                +------------------------+------------------------+
                |                        |                        |
       +--------+-------+       +--------+-------+       +--------+-------+
       |                |       |                |       |                |
       |     ENTRATE    |       |      SPESE     |       |   INDICATORI   |
       |                |       |                |       |                |
       +--------+-------+       +----------------+       +----------------+

The classifiche section starts from the Entrate subsection, by default.

Each subsection shows the timeline to select the year and type of budget to visualize charts for.

A slide-away menu allows the selection of a single voice of the budget (or indicator).

The rankings for the given voice or indicator are shown. Since there are more than 8 thousands cities,
it must be possible to filter them out, and that's done through a facet menu, on the left.

Cities are paged. A city search engine on top of the chart helps locate the page where the city
can be found in the filtered or unfiltered chart list.

Along with the voice or indicator value, each city shows these context information:

- name,
- province acronym,
- region
- the mayor, or mayors (for the given year).

