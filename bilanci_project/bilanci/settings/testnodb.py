from base import *

########## TEST SETTINGS
TEST_RUNNER = 'testrunner.NoDbTestRunner'

TEST_DISCOVER_TOP_LEVEL = SITE_ROOT
TEST_DISCOVER_ROOT = SITE_ROOT
TEST_DISCOVER_PATTERN = "test_*.py"

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

########## LIVE TEST DATABASE ACCESS !!! (Warning)
### this may only be used with a NoDbTestRunner TEST_RUNNER,
### to allow deletion of the complete database
### invoke with python manage.py test --settings=bilanci.settings.testnodb
DATABASES = {
    'default': env.db('DB_DEFAULT_URL'),
}
