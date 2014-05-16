"""Common settings and globals."""
import os
from os.path import abspath, basename, dirname, join, normpath
from sys import path
from datetime import datetime
import environ

root = environ.Path(__file__) - 4  # (/open_bilanci/bilanci_project/bilanci/settings/ - 4 = /)

# set default values and casting
env = environ.Env(
    DEBUG=(bool, True),
)
env.read_env(root('.env'))


########## PATH CONFIGURATION
REPO_ROOT = root()
PROJECT_ROOT = root('bilanci_project')

# Add our project to our pythonpath, this way we don't need to type our project
# name in our dotted import paths:
path.append(PROJECT_ROOT)

# Site name:
SITE_ROOT = root('bilanci_project/bilanci')
SITE_NAME = basename(SITE_ROOT)
########## END PATH CONFIGURATION


########## DEBUG CONFIGURATION
DEBUG = env('DEBUG')
TEMPLATE_DEBUG = DEBUG
########## END DEBUG CONFIGURATION


########## MANAGER CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#admins
ADMINS = (
    ('Your Name', 'your_email@example.com'),
)

# See: https://docs.djangoproject.com/en/dev/ref/settings/#managers
MANAGERS = ADMINS
########## END MANAGER CONFIGURATION


########## DATABASE CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#databases
DATABASES = {
    'default': env.db('DB_DEFAULT_URL'),
}
########## END DATABASE CONFIGURATION


########## GENERAL CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#time-zone
TIME_ZONE = 'Europe/Rome'

# See: https://docs.djangoproject.com/en/dev/ref/settings/#language-code
LANGUAGE_CODE = 'it-IT'

# See: https://docs.djangoproject.com/en/dev/ref/settings/#site-id
SITE_ID = 1

# See: https://docs.djangoproject.com/en/dev/ref/settings/#use-i18n
USE_I18N = True

# See: https://docs.djangoproject.com/en/dev/ref/settings/#use-l10n
USE_L10N = True

# See: https://docs.djangoproject.com/en/dev/ref/settings/#use-tz
USE_TZ = True
########## END GENERAL CONFIGURATION


########## MEDIA CONFIGURATION
MEDIA_ROOT = root('assets')
MEDIA_URL = '/media/'
########## END MEDIA CONFIGURATION


########## STATIC FILE CONFIGURATION
STATIC_ROOT = root('static')
STATIC_URL = '/static/'

# See: https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#std:setting-STATICFILES_DIRS
STATICFILES_DIRS = (
    normpath(join(PROJECT_ROOT, 'static')),
)

# See: https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#staticfiles-finders
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)
########## END STATIC FILE CONFIGURATION


OPENDATA_ROOT = os.path.join(root('open_data'), 'zip')
OPENDATA_URL = '/opendata/'


########## SECRET CONFIGURATION
SECRET_KEY = env('SECRET_KEY')  # Raises ImproperlyConfigured exception if SECRET_KEY not in os.environ
########## END SECRET CONFIGURATION


########## SITE CONFIGURATION
# Hosts/domain names that are valid for this site
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = []
########## END SITE CONFIGURATION


########## FIXTURE CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-FIXTURE_DIRS
FIXTURE_DIRS = (
    normpath(join(PROJECT_ROOT, 'fixtures')),
)
########## END FIXTURE CONFIGURATION


########## TEMPLATE CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#template-context-processors
TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.core.context_processors.tz',
    'django.contrib.messages.context_processors.messages',
    'django.core.context_processors.request',

    # bilanci project context processor
    'bilanci.context_processor.main_settings',
)

# See: https://docs.djangoproject.com/en/dev/ref/settings/#template-loaders
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

# See: https://docs.djangoproject.com/en/dev/ref/settings/#template-dirs
TEMPLATE_DIRS = (
    normpath(join(PROJECT_ROOT, 'templates')),
)
########## END TEMPLATE CONFIGURATION


########## MIDDLEWARE CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#middleware-classes
MIDDLEWARE_CLASSES = (
    # Default Django middleware.
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)
########## END MIDDLEWARE CONFIGURATION


########## URL CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#root-urlconf
ROOT_URLCONF = '%s.urls' % SITE_NAME
########## END URL CONFIGURATION


########## APP CONFIGURATION
DJANGO_APPS = (
    # Default Django apps:
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Useful template tags:
    'django.contrib.humanize',

    # Admin panel and documentation:
    'django.contrib.admin',
    'django.contrib.admindocs',
    
    # Django add-ons
    'django_extensions',

    'django.contrib.gis',
)

THIRD_PARTY_APPS = (
    # Database migration helpers:
    'south',
    'django_select2',
    'treeadmin',
    'mptt',
    'front',
    'tinymce',
)

# Apps specific for this project go here.
LOCAL_APPS = (
    'bilanci',
    'territori',
    'idioticon',
    'shorturls',
)

# See: https://docs.djangoproject.com/en/dev/ref/settings/#installed-apps
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS
########## END APP CONFIGURATION

POSTGIS_VERSION = (2, 0, 0)


########## LOGGING CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#logging
# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format' : "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            'datefmt' : "%d/%b/%Y %H:%M:%S"
        },
        'reduced': {
            'format': "%(levelname)s %(message)s"
        }
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'console':{
            'level':'DEBUG',
            'class':'logging.StreamHandler',
            'formatter': 'standard'
        },
        'test_console':{
            'level':'DEBUG',
            'class':'logging.StreamHandler',
            'formatter': 'reduced'
        },
        'import_logfile': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': REPO_ROOT + "/log/import_logfile",
            'mode': 'w',
            'formatter': 'standard',
        },
        'import_logfile_append': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': REPO_ROOT + "/log/import_logfile",
            'formatter': 'standard',
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'management': {
            'handlers': ['console', 'import_logfile'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'management_append': {
            'handlers': ['console', 'import_logfile_append'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'test': {
            'handlers': ['test_console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    }
}
########## END LOGGING CONFIGURATION


########## WSGI CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#wsgi-application
WSGI_APPLICATION = 'wsgi.application'
########## END WSGI CONFIGURATION

# scrapers settings
START_YEAR = 2002
END_YEAR = 2012

OUTPUT_PATH = '../scraper_project/scraper/output/'
LISTA_COMUNI = 'listacomuni.csv'
LISTA_COMUNI_PATH = OUTPUT_PATH + LISTA_COMUNI

# preventivi url
URL_PREVENTIVI_QUADRI = "http://finanzalocale.interno.it/apps/floc.php/certificati/index/codice_ente/%s/cod/3/anno/%s/md/0/cod_modello/PCOU/tipo_modello/U/cod_quadro/%s"
# consuntivi url
URL_CONSUNTIVI_QUADRI = "http://finanzalocale.interno.it/apps/floc.php/certificati/index/codice_ente/%s/cod/4/anno/%s/md/0/cod_modello/CCOU/tipo_modello/U/cod_quadro/%s"



# Google Account credentials
GOOGLE_USER = env('GOOGLE_USER')
GOOGLE_PASSWORD = env('GOOGLE_PASSWORD')

# Google Docs keys
GDOC_KEYS= {
    'titoli_map': env('GDOC_TITOLI_MAP_KEY'),
    'voci_map': env('GDOC_VOCI_MAP_KEY'),
    'simple_map':env('GDOC_VOCI_SIMPLE_MAP_KEY'),
    'simple_tree':env('GDOC_VOCI_SIMPLE_TREE_KEY')
}

COUCHDB_RAW_NAME = 'bilanci'
COUCHDB_NORMALIZED_TITOLI_NAME = 'bilanci_titoli'
COUCHDB_NORMALIZED_VOCI_NAME = 'bilanci_voci'
COUCHDB_SIMPLIFIED_NAME = 'bilanci_simple'

COUCHDB_SERVERS = {
    'localhost': {
        'host': '127.0.0.1',
        'port': '5984',
        'user': env('COUCHDB_LOCALHOST_USER'),
        'password':env('COUCHDB_LOCALHOST_PASSWORD'),
    },
    'staging': {
        'host': 'staging.depp.it',
        'port': '5984',
        'user': env('COUCHDB_STAGING_USER'),
        'password':env('COUCHDB_STAGING_PASSWORD'),
    },
}
COUCHDB_DEFAULT_SERVER = 'staging'

CACHES = {
    "default": {
        "BACKEND": "redis_cache.cache.RedisCache",
        "LOCATION": "127.0.0.1:6379:1",  # db 1
        "TIMEOUT": 0,
        "OPTIONS": {
            "CLIENT_CLASS": "redis_cache.client.DefaultClient",
        }
    }
}

CACHE_PAGE_DURATION_SECS = 3600

SOUTH_TESTS_MIGRATE = False

GDP_DEFLATORS = {
    2000: 0.777728432,
    2001: 0.800109527,
    2002: 0.825777358,
    2003: 0.851531437,
    2004: 0.871901728,
    2005: 0.887745029,
    2006: 0.902904158,
    2007: 0.924337811,
    2008: 0.947752751,
    2009: 0.967550814,
    2010: 0.971307248,
    2011: 0.984445032,
    2012: 1,
    2013: 1.014412693,
}

##
# OP API VARIABLES:
##

OP_API_HOST = "http://api3.openpolis.it"

##
# APPLICATION VARIABLES:
# set the start / end of the time span considered for incarichi related to Territori
##


APP_DATE_FMT = '%Y-%m-%d'
APP_START_DATE_STR = "2003-01-01"
APP_END_DATE_STR = "2013-12-31"
APP_START_DATE = datetime.strptime(APP_START_DATE_STR, APP_DATE_FMT)
APP_END_DATE = datetime.strptime(APP_END_DATE_STR, APP_DATE_FMT)

##
# BILANCIO GRAPHS VARIABLES:
# set the start / end of the Sindaci timeline and line graphs in the Bilancio Pages
##

TERRITORI_CONTEXT_REFERENCE_YEAR = 2012

TIMELINE_START_DATE = APP_START_DATE
TIMELINE_END_DATE = APP_END_DATE

CLASSIFICHE_START_YEAR = APP_START_DATE.year
CLASSIFICHE_END_YEAR = 2012

SELECTOR_DEFAULT_YEAR = 2013
SELECTOR_DEFAULT_BILANCIO_TYPE = 'preventivo'

# expiration time for a data in a session (seconds)
SESSION_COOKIE_AGE = 7200
SESSION_SAVE_EVERY_REQUEST = True

# define lines color of the SINDACO marker on the timeline
INCARICO_MARKER_INACTIVE = '#b9c6c4'
INCARICO_MARKER_DUMMY = '/static/img/incarico_dummy.png'

# defines the color of the line graph
TERRITORIO_1_COLOR = '#cc6633'
TERRITORIO_2_COLOR = '#a51206'

CLUSTER_LINE_COLOR = '#f7b5a1'

DEFAULT_INDICATOR_SLUG = 'autonomia-finanziaria'
INDICATOR_COLORS = ['#cc6633',
                    '#f7da94',
                    '#913d6a',
                    '#999924',
                    '#993527',
                    '#c3a150',
                    '#666c14']

# euros range to define two sums equal
# due to round of floats to integers,
# can be as large as 10
NEARLY_EQUAL_THRESHOLD = 10

# LOGIN_URL defines the name of the view to be called
# when an unauthorized user tries to access a passw-protected view
LOGIN_URL = 'login'

# defines Mailbin server address to push temporary home page form user data
MAILBIN_SERVER_HOST = 'mailbin.openpolis.it'
MAILBIN_QUEUE_ADDR = "tcp://{0}:5558".format(MAILBIN_SERVER_HOST)
GOOGLE_SHORTENER_API_KEY = 'AIzaSyAzTAcojoJMKV3eh8XAsE3CP7hpgmms17M'
GOOGLE_SHORTENER_URL = "https://www.googleapis.com/urlshortener/v1/url"

TINYMCE_DEFAULT_CONFIG = {'theme': "advanced", 'relative_urls': False}
