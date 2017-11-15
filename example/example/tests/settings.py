import os

# use normal settings as basis
from example.settings import *  # noqa: F403, F401


POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD', '')
"""
try:
    POSTGRES_PASSWORD = os.environ['POSTGRES_PASSWORD']
except KeyError:
    raise Exception(
        '"POSTGRES_PASSWORD" is not in evniron. '
        'Please set your postgres password into '
        'environment variable "POSTGRES_PASSWORD". '
    )
"""
# Postgres is needed for testing.
# Cannot connect to the in memory db.
# (There are some workarounds.
# One of them upgrading to celery 4.
# But using it on Windows is still difficult.)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'example_test_postgres',
        'USER': 'postgres',
        'PASSWORD': POSTGRES_PASSWORD,
        'HOST': 'localhost',
        'PORT': '5432',
    },
}

# ------ #
# CELERY #
# ------ #

# ---------------------- #
# CELERY RESULTS BACKEND #
_CELERY_RESULTS_BACKEND = 'DATABASE'
if _CELERY_RESULTS_BACKEND == 'DATABASE':
    CELERY_RESULT_BACKEND = 'djcelery.backends.database:DatabaseBackend'
    import djcelery  # noqa
    djcelery.setup_loader()
elif _CELERY_RESULTS_BACKEND == 'MEMCACHED':
    CELERY_RESULT_BACKEND = "cache"
    CELERY_CACHE_BACKEND = 'memcached://127.0.0.1:11211/'

CELERY_SEND_EVENTS = True
CELERYD_POOL = 'threads'
CELERYD_CONCURRENCY = 1
CELERYD_HIJACK_ROOT_LOGGER = False
CELERYD_LOG_FORMAT = "%(message)s"

# ------------- #
# CELERY BROKER #

BROKER_URL = 'memory://'
BROKER_TRANSPORT_OPTIONS = {'polling_interval': .01}
