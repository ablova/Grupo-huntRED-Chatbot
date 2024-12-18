# /home/pablollh/ai_huntred/settings/production.py
from ..settings import *

DEBUG = False
ALLOWED_HOSTS = ['ai.huntred.com']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'amigro_db',
        'USER': 'amigro_user',
        'PASSWORD': 'securepassword',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

