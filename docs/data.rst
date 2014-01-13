Overview
============
Data are fetched from the source as HTML files (no images, styles, or js scripts).
This is done in order to prevent damage whenever tehy should disappear from the source.

HTML files are then parsed into couchdb documents. All tables are transformed into json structures.

Budget titles and labels are normalized, by finding the MCD, defining a mapping and replicating the
raw couchdb. This is a 2 steps process.

The final product is a normalized set of budget documents, available on couchdb (through a RESTFUL API),
that can be used both as source to build HTML page and to compute indicators and averages (through map-reduce).


Data source
-----------
The source is http://finanzalocale.interno.it/. Response times are good. 
The list of municipalities, with slugs and code may be 
extracted at: http://finanzalocale.interno.it/apps/floc.php/ajax/searchComune/
The estimated size of the HTML files is ~100GB.


Fetch
-----
HTML documents are parsed with the ``scrapy`` parser.
**TODO**.



Parse into couchdb
------------------
Data are parsed from HTML into the couchdb local server with the html2couch management task::

    html2couch --cities=all --years=2003-2011 --base-url=http://finanzalocale.mirror.openpolis.it
    html2couch --cities=Roma --years=2003,2004
    
The default value for the ``base_url`` parameter is http://finanzalocale.mirror.openpolis.it.
The couchdb server is always localhost.

Overall couchDB size for the parsed documents is around 3GB.


Normalization
-------------
**TODO**

Titles
++++++

Keys
++++



