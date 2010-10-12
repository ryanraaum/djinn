import os 

ROOT_PATH = '/Users/ryan/development/djinn'
DEBUG = True
TEMPLATE_DEBUG = DEBUG

DATABASE_ENGINE = 'sqlite3'
DATABASE_NAME = 'db/development.db'
DATABASE_USER = ''
DATABASE_PASSWORD = ''

SECRET_KEY = 'monumificisnteisy'

# Celery Settings
BROKER_HOST = "localhost"
BROKER_PORT = 5672
BROKER_USER = "guest"
BROKER_PASSWORD = "guest"
BROKER_VHOST = "/"

ROOT_URLCONF = 'djinn.urls'

STATIC_ROOT = os.path.join(ROOT_PATH, 'static')
MEDIA_ROOT = ''
MEDIA_URL = ''
ADMIN_MEDIA_PREFIX = '/media/'

