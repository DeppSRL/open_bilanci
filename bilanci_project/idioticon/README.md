Rationale
=========
*Idioticon* (see http://en.wiktionary.org/wiki/idioticon for the meaning),
is a module that allows to disseminate html templates with clickable question marks (idioticons).

Whenever a user clicks on an idioticon, a popover appears, showing some content.
The content can be easily managed by administrators in the backend.

Prerequisites
=============
django-idioticon is based on bootstrap,
so Bootstrap's CSS and Javascript need to be correctly loaded in the html pages
where the popovers appear.

Installation
============
Install django-tinymce, if not already installed with::

    pip install django-tinymce

Install this module, by downloading it and copying it as a django app, within your project.

Add both ``tinymce`` and ``idioticon`` to the installed apps.

Execute ``syncdb`` or ``python manage.py migrate idioticon`` to generate the table in the db,
where the idioticons' content will be stored.


Usage
=====
Go to the admin interface, in the *Idioticon* section and add some content (name, title, definition).
Idioticons are referenced in the HTMl template by their slugs, which therefore cannot be null or blank.

Choose an HTML template where you want to add an idioticon.
Add this snippet of code::

    {% popover_info 'home' %}

Right where you want the question mark to appear.

The popover_info templatetags library (one template tag, actually), needs to be included
in all the templates where you want idioticons to appear. This can be done with::

    {% load popover_info %}


Enable the popovers, by adding a javascript line in the ``$(document).ready`` section
of your (possibly global) template javascript::

    !function($){
        $(document).ready(function(){

            ...

            // enable popovers
            $('a[rel=info-popover]').popover();
        });
    }(jQuery);


