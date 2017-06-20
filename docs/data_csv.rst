Data CSV -> Pg
==============

Data are taken from a provided url: https://servizisie.dait.interno.gov.it/finanzalocale/
which is not free to access, but which we've been granted access to.


.. warning:: This procedure is still *alpha* and is not part of the official
    releases. Use with the utmost attention!

Certificates types
------------------
We are interested in 2 kinds of certificates: **CCOU** (Consuntivi) and **PCOU** (Preventivi).
The structure of the file is the same.

Data structure
--------------
Data come in the form of compressed files, subdivided into Consuntivi and Preventivi, for each year.
Each compressed file is organized by regions and provinces. Each txt file contains all values for all quadri, voices and columns,
for all the municipalities of the given province.

2017_01_27_estrazioneCCOU2015
|- TRENTINO_ALTO_ADIGE
|- UMBRIA
|- ...
|- LAZIO
|  |- ROMA
|  |  |- ROMA_dati.txt
|  |  |- ROMA_riepilogo.txt
|  |- RIETI
|  |  |- RIETI_dati.txt
|  |  |- RIETI_riepilogo.txt
|  |- VITERBO
|  |  |- VITERBO_dati.txt
|  |  |- VITERBO_riepilogo.txt
|  |- ...
|- TOSCANA


Each *dati* file is a CSV file using the `#` character as separator.
There is no header int the txt file, but if it was there, then it would have been like this:

```
nd#year#city_code#cert_type#quadro#voice#column#value#date
```

`nd` - an empty column, due to the row starting with the separator character
`year` - the year the budget relates to
`city_code` - the code of the location, accotding to the MinInt institutional classification
`cert_type` - the certification code (CCOU/PCOU)
`quadro, voice, column` - the triplet identifying the budget voice (see Mapping)
`value` - the value, expressed in euro
`date` - a date, which has currently no meaning to us

Mapping
-------
`city_code` can be mapped to known locations by using the internal `utils.comuni.FBMapper` class.

1010020010 maps to Acqui Terme (AL).

Each of the triplets containing values, must be mapped to one of the simplified voices in the  `Voce` model.
All values belonging to triplets associated to one simplified voice, should be summed.

The mapping is created for a single year in an external management task (TODO), and
stored into the `CodiceVoce` model.



Import management task
----------------------

The task is launched by specifying the compressed file, and it imports all of the locations' budgets
into the simplified couchdb instance.

It can be limited and import only one cities of one or more given provinces,
through the `--cities` option.

It should be possible todebug, by invoking a single `quadro`, by numbers.


Data are imported finally into the DB following the standard procedure
through the `couch2pg` management task.
