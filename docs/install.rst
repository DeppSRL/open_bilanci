Install
=========
Instructions on how to create a development environment on your workstation.

Prepare the virtualenv environment::

    WORK_PATH = ~/Workspace # change accordingly
    cd $WORK_PATH
    mkvirtualenv open-bilanci
    mkdir $WORK_PATH/open_bilanci
    cd open_bilanci
    setvirtualenvproject

Clone the repository from github::

    git clone git@github.com:DeppSRL/open_bilanci.git
    cp .env.sample .env

Modify the ``.env`` file, adding these password and keys:

* the ``SECRET_KEY``
* the ``DB_DEFAULT_URL`` (a connection string to the RDBMD)
* the ``COUCHDB`` parameters - user and pass needed only for writing to the DB
* the ``OP_API`` parameters - user and pass needed to avoid throttling
* the ``GOOGLE`` parameters - used only when refining the simple map tree


Install the requirements::

    pip install -r requirements/local.txt

Create the DB::

    python manage syncdb

Import the territori from the OP_API (takes some time), then add cluster information::

    python manage importlocations --api-domain=api3.staging.deppsviluppo.org -v2
    python manage cluster_comuni -v2

Run the server::

    python manage runserver_plus

