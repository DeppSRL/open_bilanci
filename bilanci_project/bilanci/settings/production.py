"""Production settings and globals."""
from base import *


########## HOST CONFIGURATION
# See: https://docs.djangoproject.com/en/1.5/releases/1.5/#allowed-hosts-required-in-production
MAIN_HOST = ['www.openbilanci.it',]

# Allowed hosts expansion: needed for servizi ai Comuni
HOSTS_COMUNI = [
'openbilanci.comune.fi.it',
'openbilanci.comune.castiglione.mn.it',
]

ALLOWED_HOSTS += MAIN_HOST + HOSTS_COMUNI

########## END HOST CONFIGURATION

########## EMAIL CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

########## MANAGER CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#admins
ADMINS = (
    ('Developers', 'developers@openbilanci.it'),
)

# See: https://docs.djangoproject.com/en/dev/ref/settings/#managers
MANAGERS = ADMINS
########## END MANAGER CONFIGURATION

# See: https://docs.djangoproject.com/en/dev/ref/settings/#email-host
#EMAIL_HOST = environ.get('EMAIL_HOST', 'smtp.gmail.com')

# See: https://docs.djangoproject.com/en/dev/ref/settings/#email-host-password
#EMAIL_HOST_PASSWORD = environ.get('EMAIL_HOST_PASSWORD', '')

# See: https://docs.djangoproject.com/en/dev/ref/settings/#email-host-user
#EMAIL_HOST_USER = environ.get('EMAIL_HOST_USER', 'your_email@example.com')

# See: https://docs.djangoproject.com/en/dev/ref/settings/#email-port
#EMAIL_PORT = environ.get('EMAIL_PORT', 587)

# See: https://docs.djangoproject.com/en/dev/ref/settings/#email-subject-prefix
#EMAIL_SUBJECT_PREFIX = '[%s] ' % SITE_NAME

# See: https://docs.djangoproject.com/en/dev/ref/settings/#email-use-tls
#EMAIL_USE_TLS = True

# See: https://docs.djangoproject.com/en/dev/ref/settings/#server-email
#SERVER_EMAIL = EMAIL_HOST_USER
########## END EMAIL CONFIGURATION

########## EMAIL CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
#EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
########## END EMAIL CONFIGURATION


BILANCI_PATH = "/home/open_bilanci/dati/bilanci_subset"
OUTPUT_FOLDER = '../scraper_project/scraper/output/'
LISTA_COMUNI = 'listacomuni.csv'
LISTA_COMUNI_PATH = OUTPUT_FOLDER + LISTA_COMUNI

PATH_PREVENTIVI = BILANCI_PATH+"/%s/%s/Preventivo/%s.html"
PATH_CONSUNTIVI = BILANCI_PATH+"/%s/%s/Consuntivo/%s.html"

BILANCI_RAW_DB = 'bilanci_raw'

ADMINS = (
    ('Guglielmo Celata', 'guglielmo.celata@depp.it'),
    ('Stefano Vergani', 'stefano.vergani.it@gmail.com'),
)


