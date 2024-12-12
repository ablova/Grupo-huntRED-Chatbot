# /home/amigro/chatbot_django/settings/production.py
from .base import *

DEBUG = False
ALLOWED_HOSTS = ['chatbot.amigro.org']

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

