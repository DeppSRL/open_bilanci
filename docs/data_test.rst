Data testing
============

To check that the mapping for Titoli/Voci is correctly set on the GDOC a couple of test have been implemented.

These tests run before translate keys script is called and compare the current GDOC mapping with the reference CSV files in data/reference folder.

If in the GDOC there are titoli/voci not present in the reference CSV file an error is issued and the trasfer stopped.
If in the reference CSV there are titoli/voci not present in the GDOC map an error is issued and the trasfer stopped.
