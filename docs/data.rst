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

Bilanci data normalization is necessary because data from different objects varies in structure and labelling of data along
different years and different Comune.

Data normalization process consist of two steps:

+ on the source couch Db instance a view document is inserted to map all the possible values of keys and count keys
  occurrences with a _sum function as a reduce function.

+ the results of the view documents are converted from json to csv with the script json2csv.py

+ the csv file is uploaded to Google Drive, creating a new spreadsheet
+ skilled operators perform the many-to-one key mapping based on typhography of keys
+ the map is read and used by the normalization script, translate_keys, to create a new couchdb database based on the
  existing database and the key map stored in Google Drive document
  

Data normalization is applied twice in this project in the following order

+ titoli labels normalization
 
+ voci labels normalization
    


Simplification
-------------

After normalizing titoli and voci the result is a normalized but comprehensive bilanci couchdb database.
The web application relies on a database which contains only a fraction of the data contained in the normalized database, moreover the application db requires a simplificated structure in which some keys get summed up to a single key in the application db. 

The process converts the last normalized db, the one with voci and titoli normalized, to a simplified db and it is executed through a script which 

+ reads Google Drive document contained the mapping info
+ reads all the documents in the normalized db
+ transforms the documents following the mapping algorithm
+ writes the transformed docs in the simplified db







