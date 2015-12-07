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

########## INSTANCE TYPE: production | staging | development | test
INSTANCE_TYPE = env.str('INSTANCE_TYPE')

########## PATH CONFIGURATION
REPO_ROOT = root()
PROJECT_ROOT = root('bilanci_project')

# Add our project to our pythonpath, this way we don't need to type our project
# name in our dotted import paths:
path.append(PROJECT_ROOT)

# Site name:
SITE_ROOT = root('bilanci_project/bilanci')
SITE_NAME = basename(SITE_ROOT)
SITE_VERSION = 'beta'
########## END PATH CONFIGURATION


########## DEBUG CONFIGURATION
DEBUG = env.bool('DEBUG', False)
TEMPLATE_DEBUG = env.bool('TEMPLATE_DEBUG', False)
########## END DEBUG CONFIGURATION


########## MANAGER CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#admins
ADMINS = (
    ('Your Name', 'your_email@example.com'),
)

# See: https://docs.djangoproject.com/en/dev/ref/settings/#managers
MANAGERS = ADMINS

########## END MANAGER CONFIGURATION


########## PROJECT_OWNERS CONFIGURATION
# PROJECT_OWNERS WILL GET AN EMAIL WHEN IMPORT MNG TASK ARE COMPLETED

PROJECT_OWNERS = (
    # ('Guglielmo Celata', 'guglielmo.celata@depp.it'),
    ('Stefano Vergani', 'stefano.vergani.it@gmail.com'),
)


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

OPENDATA_ROOT = root('open_data')
OPENDATA_ZIP_ROOT = os.path.join(root(OPENDATA_ROOT), 'zip')
OPENDATA_CSV_ROOT = os.path.join(root(OPENDATA_ROOT), 'csv')
OPENDATA_XML_ROOT = os.path.join(root(OPENDATA_ROOT), 'xml')
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
    'bilanci.middlewares.PrivateBetaMiddleware',
    'bilanci.middlewares.ComuniServicesMiddleware',
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
    'django.contrib.sitemaps',

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
    'robots',
)

# Apps specific for this project go here.
LOCAL_APPS = (
    'bilanci',
    'territori',
    'services',
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
            'format': "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
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
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'standard'
        },
        'test_console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
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
        'bilanci_project': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
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

OUTPUT_PATH = '../scraper_project/scraper/output/'
LISTA_COMUNI = 'listacomuni.csv'
LISTA_COMUNI_PATH = OUTPUT_PATH + LISTA_COMUNI

S3_LISTA_COMUNI_URL = env('S3_LISTA_COMUNI_URL')

# preventivi url
URL_PREVENTIVI_QUADRI = "http://finanzalocale.interno.it/apps/floc.php/certificati/index/codice_ente/%s/cod/3/anno/%s/md/0/cod_modello/PCOU/tipo_modello/U/cod_quadro/%s"
# consuntivi url
URL_CONSUNTIVI_QUADRI = "http://finanzalocale.interno.it/apps/floc.php/certificati/index/codice_ente/%s/cod/4/anno/%s/md/0/cod_modello/CCOU/tipo_modello/U/cod_quadro/%s"

# Google Account Oauth key
OAUTH2_KEY_PATH=env('OAUTH2_KEY_PATH')

# Google Docs keys
GDOC_KEYS = {
    'titoli_map': env('GDOC_TITOLI_MAP_KEY'),
    'voci_map': env('GDOC_VOCI_MAP_KEY'),
    'simple_map': env('GDOC_VOCI_SIMPLE_MAP_KEY'),
    'simple_tree': env('GDOC_VOCI_SIMPLE_TREE_KEY'),
    'bilancio_consuntivo_2013': env('GDOC_BILANCIO_CONSUNTIVO_2013'),
    'bilancio_preventivo_2014': env('GDOC_BILANCIO_PREVENTIVO_2014'),
    'bilancio_consuntivo_2014': env('GDOC_BILANCIO_CONSUNTIVO_2014'),
    'bilancio_preventivo_2015': env('GDOC_BILANCIO_PREVENTIVO_2015')
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
        'password': env('COUCHDB_LOCALHOST_PASSWORD'),
    },
    'staging': {
        'host': env('COUCHDB_STAGING_HOST'),
        'port': env('COUCHDB_STAGING_PORT'),
        'user': env('COUCHDB_STAGING_USER'),
        'password': env('COUCHDB_STAGING_PASSWORD'),
    },
}
COUCHDB_DEFAULT_SERVER = 'staging'

CACHES = {
    "default": {
        "BACKEND": "redis_cache.cache.RedisCache",
        "LOCATION": "127.0.0.1:6379:1", # db 1
        "TIMEOUT": 0,
        "OPTIONS": {
            "CLIENT_CLASS": "redis_cache.client.DefaultClient",
        }
    }
}

CACHE_PAGE_DURATION_SECS = 3600

SOUTH_TESTS_MIGRATE = False

##
# Application variables
##

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
    # TODO: update with real deflator value
    2014: 1.014412693,
}

CAPOLUOGHI_PROVINCIA = [u'agrigento-comune-ag', u'alessandria-comune-al', u'ancona-comune-an', u'andria-comune-bt',
                        u'aosta-comune-ao', u'arezzo-comune-ar', u'ascoli-piceno-comune-ap',
                        u'asti-comune-at', u'avellino-comune-av', u'bari-comune-ba', u'barletta-comune-bt',
                        u'belluno-comune-bl', u'benevento-comune-bn', u'bergamo-comune-bg', u'biella-comune-bi',
                        u'bologna-comune-bo',
                        u'bolzano-bozen-comune-bz', u'brescia-comune-bs', u'brindisi-comune-br', u'cagliari-comune-ca',
                        u'caltanissetta-comune-cl', u'campobasso-comune-cb', u'carbonia-comune-ci',
                        u'caserta-comune-ce',
                        u'catania-comune-ct', u'catanzaro-comune-cz', u'chieti-comune-ch', u'como-comune-co',
                        u'cosenza-comune-cs', u'cremona-comune-cr', u'crotone-comune-kr', u'cuneo-comune-cn',
                        u'enna-comune-en',
                        u'fermo-comune-fm', u'ferrara-comune-fe', u'firenze-comune-fi', u'foggia-comune-fg',
                        u'forli-comune-fc', u'frosinone-comune-fr', u'genova-comune-ge', u'gorizia-comune-go',
                        u'grosseto-comune-gr',
                        u'iglesias-comune-ci', u'imperia-comune-im', u'isernia-comune-is', u'lanusei-comune-og',
                        u'laquila-comune-aq', u'la-spezia-comune-sp', u'latina-comune-lt', u'lecce-comune-le',
                        u'lecco-comune-lc',
                        u'livorno-comune-li', u'lodi-comune-lo', u'lucca-comune-lu', u'macerata-comune-mc',
                        u'mantova-comune-mn', u'massa-comune-ms', u'matera-comune-mt', u'messina-comune-me',
                        u'milano-comune-mi',
                        u'modena-comune-mo', u'monza-comune-mb', u'napoli-comune-na', u'novara-comune-no',
                        u'nuoro-comune-nu', u'olbia-comune-ot', u'oristano-comune-or', u'padova-comune-pd',
                        u'palermo-comune-pa', u'parma-comune-pr',
                        u'pavia-comune-pv', u'perugia-comune-pg', u'pesaro-comune-pu', u'pescara-comune-pe',
                        u'piacenza-comune-pc', u'pisa-comune-pi', u'pistoia-comune-pt', u'pordenone-comune-pn',
                        u'potenza-comune-pz',
                        u'prato-comune-po', u'ragusa-comune-rg', u'ravenna-comune-ra', u'reggio-di-calabria-comune-rc',
                        u'reggio-nellemilia-comune-re', u'rieti-comune-ri', u'rimini-comune-rn', u'roma-comune-rm',
                        u'rovigo-comune-ro', u'salerno-comune-sa', u'sanluri-comune-vs', u'sassari-comune-ss',
                        u'savona-comune-sv', u'siena-comune-si', u'siracusa-comune-sr', u'sondrio-comune-so',
                        u'taranto-comune-ta',
                        u'tempio-pausania-comune-ot', u'teramo-comune-te', u'terni-comune-tr', u'torino-comune-to',
                        u'tortoli-comune-og', u'trani-comune-bt', u'trapani-comune-tp', u'trento-comune-tn',
                        u'treviso-comune-tv',
                        u'trieste-comune-ts', u'udine-comune-ud', u'urbino-comune-pu', u'varese-comune-va',
                        u'venezia-comune-ve', u'verbania-comune-vb', u'vercelli-comune-vc', u'verona-comune-vr',
                        u'vibo-valentia-comune-vv', u'vicenza-comune-vi', u'villacidro-comune-vs', u'viterbo-comune-vt']

##
# OP API VARIABLES:
##

OP_BLOG_CATEGORY = 'neibilanci'
OP_API_DOMAIN = env('OP_API_DOMAIN')
OP_API_USERNAME = env('OP_API_USERNAME')
OP_API_PASSWORD = env('OP_API_PASSWORD')

##
# COOKIES
# expiration time for a data in a session (seconds)
##

SESSION_COOKIE_AGE = 7200
SESSION_SAVE_EVERY_REQUEST = True

##
# TIMELINE VARIABLES:
# set the start / end of the time span considered
##

APP_DATE_FMT = '%Y-%m-%d'

APP_START_YEAR = 2004
APP_END_YEAR = 2014
APP_START_DATE = datetime.strptime("{0}-01-01".format(APP_START_YEAR), APP_DATE_FMT)
APP_END_DATE = datetime.strptime("{0}-12-31".format(APP_END_YEAR), APP_DATE_FMT)

LAST_VALID_CONSUNTIVO_YEAR = 2013
CLASSIFICHE_START_YEAR = APP_START_DATE.year
CLASSIFICHE_END_YEAR = LAST_VALID_CONSUNTIVO_YEAR

TERRITORI_CONTEXT_REFERENCE_YEAR = CLASSIFICHE_END_YEAR

##
# BILANCIO GRAPHS VARIABLES:
# set the start / end of the Sindaci timeline and line graphs in the Bilancio Pages
##


# define lines color of the SINDACO marker on the timeline
INCARICO_MARKER_INACTIVE = '#b9c6c4'
INCARICO_MARKER_DUMMY = '/static/img/incarico_dummy.png'
INCARICO_MARKER_COMMISSARIO = '/static/img/commissario.png'

# defines the color of the line graph
TERRITORIO_1_COLOR = '#cc6633'
TERRITORIO_2_COLOR = '#a51206'

CLUSTER_LINE_COLOR = '#f7b5a1'

DEFAULT_INDICATOR_SLUG = 'autonomia-finanziaria'
DEFAULT_VOCE_SLUG_CONFRONTI = 'consuntivo-entrate-cassa-imposte-e-tasse'
DEFAULT_VOCE_SLUG_CLASSIFICHE = DEFAULT_VOCE_SLUG_CONFRONTI

INDICATOR_COLORS = ['#cc6633',
                    '#f7da94',
                    '#913d6a',
                    '#999924',
                    '#993527',
                    '#c3a150',
                    '#666c14',
                    '#5f6b78',
                    '#e2a8b0',
                    '#c6d041']

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

# voce bilancio slugs of funzioni sum branches
PREVENTIVO_SOMMA_SPESE_FUNZIONI_SLUG = 'preventivo-spese-spese-somma-funzioni'
CONSUNTIVO_SOMMA_SPESE_FUNZIONI_SLUG = 'consuntivo-spese-cassa-spese-somma-funzioni'
CONSUNTIVO_SPESE_INVESTIMENTI_INTERVENTI_SLUG = 'consuntivo-spese-cassa-spese-per-investimenti-interventi'
CONSUNTIVO_SPESE_CORRENTI_INTERVENTI_SLUG = 'consuntivo-spese-cassa-spese-correnti-interventi'

HOSTS_COMUNI=[]

CLASSIFICHE_PAGINATE_BY = 15
EARLYBIRD_ENABLE = env.bool('EARLYBIRD_ENABLE')

ENABLED_STATIC_PAGES = [
    'faq',
    'indicatori',
    'bilancio_comune',
    'mappa',
    'confronti',
    'classifiche',
    'software',
    'licenze',
    'informativa',
    'credits',
]
