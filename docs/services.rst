

Services for Comuni
===============

The web platform offers services to Comuni.
If activated a Comune can get

-  a third / fourth level domain linked to its bilancio page
-  a different template is shown with customizable text in header / footer
-  Comune logo can be uploaded via backend and it appears on the Comune header
-  Comune back link to official website

Activating services for a Comune
--------------------------------

To activate services for a Comune follow the steps

-  enter the backend of the app
-  go to Services app
-  add a paginacomune object
-  add the host address. Example: www.comune.bilancio.EXAMPLE.it
-  add header, footer text, logo
-  open application settings (production, staging depending on the deploying server)
-  add the same host address in the list HOSTS_COMUNI
-  restart uwsgi

After the domain name is correctly set with the DNS pointing to the application server then browsing

.. code-block:: bash

    http://www.comune.bilancio.EXAMPLE.it
    
will show the page

.. code-block:: bash

    http://www.openbilanci.it/bilanci/slug-comune-pr/
    
with Comune template
    

