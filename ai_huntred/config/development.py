# /Users/pablollh/MEGA/GitHub/Grupo-huntRED-Chatbot/ai_huntred/config/development.py
#
# Configuración de desarrollo para AI HuntRED.
# Configura la base de datos, permisos y modo de desarrollo.
# Optimizado para bajo uso de CPU, escalabilidad, y robustez frente a fallos.

from ai_huntred.settings import *
from ai_huntred.settings.base import BASE_DIR, INSTALLED_APPS, MIDDLEWARE
import os
import environ

env = environ.Env()

# Development settings
DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Database configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Email configuration
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'noreply@huntred.com'

# Configuración de WhatsApp
WHATSAPP_CONFIG = {
    # Los valores de API y webhooks se obtienen desde ConfigAPI y modelos dinámicos
    'api_key': '',  # Obtenido desde ConfigAPI
    'api_url': '',  # Obtenido desde ConfigAPI
    'webhook_url': '',  # Obtenido dinámicamente
    'webhook_token': '',  # Obtenido dinámicamente
}

# Configuración de Telegram
TELEGRAM_CONFIG = {
    # Los valores de API y webhooks se obtienen desde ConfigAPI y modelos dinámicos
    'BOT_TOKEN': '',  # Obtenido desde ConfigAPI
    'WEBHOOK_URL': '',  # Obtenido dinámicamente
    'WEBHOOK_TOKEN': '',  # Obtenido dinámicamente
}

# Configuración de Messenger
MESSENGER_CONFIG = {
    # Los valores de API y webhooks se obtienen desde ConfigAPI y modelos dinámicos
    'APP_SECRET': '',  # Obtenido desde ConfigAPI
    'WEBHOOK_URL': '',  # Obtenido dinámicamente
    'WEBHOOK_TOKEN': '',  # Obtenido dinámicamente
}

# Configuración de Instagram
INSTAGRAM_CONFIG = {
    # Los valores de API y webhooks se obtienen desde ConfigAPI y modelos dinámicos
    'APP_SECRET': '',  # Obtenido desde ConfigAPI
    'WEBHOOK_URL': '',  # Obtenido dinámicamente
    'WEBHOOK_TOKEN': '',  # Obtenido dinámicamente
}

# Cache configuration
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# Celery configuration
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

# CDN configuration
CDN_ENABLED = False
CDN_DOMAIN = None

# Monitoring configuration
ENABLE_METRICS = True
ENABLE_PROMETHEUS = True
METRICS_ENDPOINT = '/metrics'

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
}

# Debug toolbar configuration
INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
INTERNAL_IPS = ['127.0.0.1']