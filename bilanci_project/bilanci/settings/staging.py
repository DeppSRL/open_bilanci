"""Production settings and globals."""
from base import *


########## HOST CONFIGURATION
# See: https://docs.djangoproject.com/en/1.5/releases/1.5/#allowed-hosts-required-in-production
MAIN_HOST = ['storico.staging.openbilanci.it', 'staging.openbilanci.it']

# Allowed hosts expansion: needed for servizi ai Comuni
HOSTS_COMUNI = [
'novara.comuni.storico.staging.openbilanci.it',
'rapallo.storico.staging.comuni.openbilanci.it',
'castiglionedellestiviere.comuni.storico.staging.openbilanci.it',
'firenze.comuni.storico.staging.openbilanci.it',
'roma.comuni.storico.staging.openbilanci.it',
'terni.comuni.storico.staging.openbilanci.it',
]

ALLOWED_HOSTS += MAIN_HOST + HOSTS_COMUNI
########## END HOST CONFIGURATION

########## EMAIL CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
########## END EMAIL CONFIGURATION


########## TOOLBAR CONFIGURATION
# See: https://github.com/django-debug-toolbar/django-debug-toolbar#installation
INSTALLED_APPS += (
#    'debug_toolbar',
)

# See: https://github.com/django-debug-toolbar/django-debug-toolbar#installation
INTERNAL_IPS = ('176.31.74.29',)

# See: https://github.com/django-debug-toolbar/django-debug-toolbar#installation
MIDDLEWARE_CLASSES = (
#    'debug_toolbar.middleware.DebugToolbarMiddleware',
) + MIDDLEWARE_CLASSES

# See: https://github.com/django-debug-toolbar/django-debug-toolbar#installation
DEBUG_TOOLBAR_CONFIG = {
    'INTERCEPT_REDIRECTS': False,
    'SHOW_TEMPLATE_CONTEXT': True,
}
def show_toolbar(request):
    print("IP Address for debug-toolbar: " + request.META['REMOTE_ADDR'])
    return True
SHOW_TOOLBAR_CALLBACK = show_toolbar
DEBUG_TOOLBAR_PATCH_SETTINGS=False

########## END TOOLBAR CONFIGURATION


BILANCI_PATH = "/home/open_bilanci/dati/bilanci_subset"
OUTPUT_FOLDER = '../scraper_project/scraper/output/'
LISTA_COMUNI = 'listacomuni.csv'
LISTA_COMUNI_PATH = OUTPUT_FOLDER + LISTA_COMUNI

PATH_PREVENTIVI = BILANCI_PATH+"/%s/%s/Preventivo/%s.html"
PATH_CONSUNTIVI = BILANCI_PATH+"/%s/%s/Consuntivo/%s.html"

BILANCI_RAW_DB = 'bilanci_raw'

# add this definitions to see what happens through loggers
#LOGGING['handlers']['logfile'] = {
#            'level': 'DEBUG',
#            'class': 'logging.FileHandler',
#            'filename': REPO_ROOT + "/log/logfile",
#            'mode': 'w',
#            'formatter': 'standard',
#}
#LOGGING['loggers']['bilanci_project'] = {
#            'handlers': ['logfile'],
#            'level': 'DEBUG',
#            'propagate': False,
#}
