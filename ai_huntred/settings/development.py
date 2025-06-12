"""
Configuración de desarrollo para Grupo huntRED®.
"""
import os
import logging
from pathlib import Path
import environ
from .base import *

# Initialize environment variables
env = environ.Env()
# Buscar el archivo .env en el directorio raíz del proyecto (donde está manage.py)
project_root = Path(__file__).resolve().parent.parent.parent
env_path = project_root / '.env'
logger = logging.getLogger(__name__)
logger.info(f"Buscando archivo .env en: {env_path}")
if env_path.exists():
    logger.info(f"Archivo .env encontrado en: {env_path}")
    environ.Env.read_env(env_path)
else:
    logger.warning(f"No se encontró el archivo .env en: {env_path}")

# Configuración de desarrollo
DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Configuración de base de datos PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME', default='g_huntred_ai_db'),
        'USER': env('DB_USER', default='g_huntred_pablo'),
        'PASSWORD': env('DB_PASSWORD', default='Natalia&Patricio1113!'),
        'HOST': env('DB_HOST', default='localhost'),
        'PORT': env('DB_PORT', default='5432'),
        'OPTIONS': {
            'client_encoding': 'UTF8',
            'options': '-c search_path=public,pg_catalog',
        },
    }
}

# Configuración de correo electrónico
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Configuración de CORS
CORS_ALLOW_ALL_ORIGINS = True

# Configuración de Celery
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Configuración de Debug Toolbar
INSTALLED_APPS += [
    'debug_toolbar',
    'django_extensions',
]
MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
INTERNAL_IPS = ['127.0.0.1']

# Configuración de Silk
SILKY_PYTHON_PROFILER = True
SILKY_PYTHON_PROFILER_BINARY = True
SILKY_AUTHENTICATION = True
SILKY_AUTHORISATION = True
SILKY_MAX_RECORDED_REQUESTS = 1000
SILKY_MAX_RECORDED_REQUESTS_CHECK_PERCENT = 10

# Configuración de logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
        'debug': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {pathname}:{lineno} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'development.log',
            'formatter': 'verbose',
        },
        'debug_file': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'debug.log',
            'formatter': 'debug',
        },
    },
    'root': {
        'handlers': ['console', 'file', 'debug_file'],
        'level': 'DEBUG',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file', 'debug_file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'app': {
            'handlers': ['console', 'file', 'debug_file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'whatsapp': {
            'handlers': ['console', 'file', 'debug_file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'telegram': {
            'handlers': ['console', 'file', 'debug_file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'messenger': {
            'handlers': ['console', 'file', 'debug_file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'instagram': {
            'handlers': ['console', 'file', 'debug_file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

# Configuración de entorno
ENVIRONMENT = 'development'

# Configuración de APIs para desarrollo
MESSAGING_APIS['whatsapp'].update({
    'ENABLED': True,
    'API_URL': 'http://localhost:8000/api/whatsapp',
    'API_TOKEN': 'dev_whatsapp_token',
    'WEBHOOK_SECRET': 'dev_webhook_secret',
    'VERIFY_TOKEN': 'dev_verify_token',
})

MESSAGING_APIS['telegram'].update({
    'ENABLED': True,
    'BOT_TOKEN': 'dev_telegram_token',
    'WEBHOOK_SECRET': 'dev_webhook_secret',
})

MESSAGING_APIS['messenger'].update({
    'ENABLED': True,
    'APP_SECRET': 'dev_messenger_secret',
    'VERIFY_TOKEN': 'dev_verify_token',
})

MESSAGING_APIS['instagram'].update({
    'ENABLED': True,
    'APP_SECRET': 'dev_instagram_secret',
    'ACCESS_TOKEN': 'dev_access_token',
})

# Configuración de Django Extensions
SHELL_PLUS = "ipython"
SHELL_PLUS_PRINT_SQL = True
IPYTHON_ARGUMENTS = [
    '--ext', 'django_extensions.management.notebook_extension',
    '--debug',
]

# Debug print
logger = logging.getLogger(__name__)
logger.info("DEBUG: DATABASES configuration (development.py): %s", DATABASES)