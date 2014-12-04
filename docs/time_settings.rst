Application time settings
=========================

Open Bilanci needs various time settings with different functions.
They are declared in settings/base.py

APP_START_DATE / APP_END_DATE
-----------------------------

Sets the timespan for:

- composition widget data
- bilancio overview: to flag the bilancio as "recent"
- composition widget internal linechart in the widget boxes
- timeline in the context processor
- IncarichiGetterMixin: that is used for ConfrontiDataJson, IncarichiIndicatorJson, IncarichiVoceJson
- import_incarichi
- the sitemap
- the medians


