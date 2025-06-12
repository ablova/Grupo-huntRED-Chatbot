# /home/pablo/ai_huntred/settings/production.py
"""
Configuración de producción para Grupo huntRED®.

Este archivo contiene toda la configuración específica para entornos de producción.
Incluye configuraciones de seguridad, base de datos, caché, y servicios externos.
"""

# Importaciones estándar
import os
import sys
import logging
import environ
import sentry_sdk
from pathlib import Path
from datetime import timedelta
from django.core.exceptions import ImproperlyConfigured
from sentry_sdk.integrations.django import DjangoIntegration

# Importar configuración base
from .base import *

# Configuración de logging
logger = logging.getLogger(__name__)

# Configuración de entorno
env = environ.Env()

# Configuración de rutas
BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent  # /home/pablo/ai_huntred/

# Asegurar que el directorio base esté en el path
sys.path.append(str(PROJECT_ROOT))

# Load .env file
env_file = os.path.join(BASE_DIR.parent, '.env')  # Changed to /home/pablo/.env
if not os.path.exists(env_file):
    raise FileNotFoundError(f"Environment file not found: {env_file}")
if not os.access(env_file, os.R_OK):
    raise PermissionError(f"Environment file not readable: {env_file}")
environ.Env.read_env(env_file)

# Validación de variables de entorno requeridas
required_env_vars = [
    'DJANGO_SECRET_KEY',
    'DB_NAME',
    'DB_USER',
    'DB_PASSWORD',
    'DB_HOST',
    'REDIS_HOST',
    'REDIS_PASSWORD',
    'EMAIL_HOST',
    'EMAIL_HOST_USER',
    'EMAIL_HOST_PASSWORD',
    'WHATSAPP_API_TOKEN',
    'TELEGRAM_BOT_TOKEN',
    'MESSENGER_APP_SECRET',
    'INSTAGRAM_APP_SECRET',
]

for var in required_env_vars:
    if not env(var, default=None):
        raise ImproperlyConfigured(f"Environment variable {var} is required in production")

# Configuración de producción
DEBUG = False
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['huntred.com', 'www.huntred.com'])

# Configuración de base de datos
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME'),
        'USER': env('DB_USER'),
        'PASSWORD': env('DB_PASSWORD'),
        'HOST': env('DB_HOST'),
        'PORT': env('DB_PORT', default='5432'),
        'CONN_MAX_AGE': 60,
        'OPTIONS': {
            'connect_timeout': 10,
            'keepalives': 1,
            'keepalives_idle': 30,
            'keepalives_interval': 10,
            'keepalives_count': 5,
            'application_name': 'ai_huntred',
            'options': '-c statement_timeout=30000 -c idle_in_transaction_session_timeout=30000',
        }
    }
}

# Configuración de seguridad
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000  # 1 año
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_HTTPONLY = True
SECURE_REFERRER_POLICY = 'same-origin'

# Configuración de caché
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': f"redis://{REDIS_CONFIG['host']}:{REDIS_CONFIG['port']}/{REDIS_CONFIG['db']}",
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'PASSWORD': REDIS_CONFIG['password'],
            'SOCKET_TIMEOUT': 5,
            'SOCKET_CONNECT_TIMEOUT': 5,
            'RETRY_ON_TIMEOUT': True,
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 100,
            },
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
            'PARSER_CLASS': 'redis.connection.HiredisParser',
        }
    }
}

# Configuración de sesiones
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
SESSION_COOKIE_AGE = 86400  # 24 horas
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# Configuración de CORS
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[])
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS']
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# Configuración de Celery
CELERY_BROKER_USE_SSL = True
CELERY_REDIS_BACKEND_USE_SSL = True
CELERY_TASK_ALWAYS_EAGER = False
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000
CELERY_WORKER_PREFETCH_MULTIPLIER = 4
CELERY_TASK_TIME_LIMIT = 3600  # 1 hora
CELERY_TASK_SOFT_TIME_LIMIT = 3000  # 50 minutos
CELERY_TASK_ACKS_LATE = True
CELERY_TASK_REJECT_ON_WORKER_LOST = True
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 3600
CELERY_TASK_SOFT_TIME_LIMIT = 3000

# Configuración de logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'production.log',
            'maxBytes': 1024 * 1024 * 5,  # 5 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'error.log',
            'maxBytes': 1024 * 1024 * 5,  # 5 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console', 'error_file'],
            'level': 'INFO',
            'propagate': True,
        },
        'app': {
            'handlers': ['file', 'console', 'error_file'],
            'level': 'INFO',
            'propagate': True,
        },
        'whatsapp': {
            'handlers': ['file', 'console', 'error_file'],
            'level': 'INFO',
            'propagate': True,
        },
        'telegram': {
            'handlers': ['file', 'console', 'error_file'],
            'level': 'INFO',
            'propagate': True,
        },
        'messenger': {
            'handlers': ['file', 'console', 'error_file'],
            'level': 'INFO',
            'propagate': True,
        },
        'instagram': {
            'handlers': ['file', 'console', 'error_file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# Configuración de archivos estáticos
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
WHITENOISE_MAX_AGE = 31536000  # 1 año
WHITENOISE_USE_FINDERS = True
WHITENOISE_MANIFEST_STRICT = True
WHITENOISE_ALLOW_ALL_ORIGINS = False

# Configuración de Silk
SILKY_PYTHON_PROFILER = False
SILKY_AUTHENTICATION = True
SILKY_AUTHORISATION = True
SILKY_MAX_RECORDED_REQUESTS = 100
SILKY_MAX_RECORDED_REQUESTS_CHECK_PERCENT = 10

# Configuración de Sentry
if env('SENTRY_DSN', default=None):
    sentry_sdk.init(
        dsn=env('SENTRY_DSN'),
        integrations=[DjangoIntegration()],
        traces_sample_rate=env.float('SENTRY_SAMPLE_RATE', default=0.1),
        send_default_pii=True,
        environment='production',
        release=env('APP_VERSION', default='1.0.0'),
        before_send=lambda event, hint: {
            **event,
            'tags': {
                **event.get('tags', {}),
                'environment': 'production',
            }
        }
    )

# Email backend
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env('EMAIL_HOST')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)
EMAIL_HOST_USER = env('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='Grupo huntRED® <hola@huntred.com>')

# API configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend'],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': env('THROTTLE_ANON', default='100/day'),
        'user': env('THROTTLE_USER', default='1000/day'),
    },
    'DEFAULT_RENDERER_CLASSES': ['rest_framework.renderers.JSONRenderer'],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
    'EXCEPTION_HANDLER': 'ai_huntred.error_handling.custom_exception_handler',
}

# WhatsApp configuration
WHATSAPP_API_URL = env('WHATSAPP_API_URL', default='')
WHATSAPP_API_TOKEN = env('WHATSAPP_API_TOKEN', default='')

# PayPal configuration
PAYPAL_CONFIG = {
    'mode': env('PAYPAL_MODE', default='sandbox'),
    'client_id': env('PAYPAL_CLIENT_ID', default=''),
    'client_secret': env('PAYPAL_CLIENT_SECRET', default=''),
    'return_url': env('PAYPAL_RETURN_URL', default=''),
    'cancel_url': env('PAYPAL_CANCEL_URL', default=''),
}

# Stripe configuration
STRIPE_CONFIG = {
    'api_key': env('STRIPE_API_KEY', default=''),
    'webhook_secret': env('STRIPE_WEBHOOK_SECRET', default=''),
}

# Configuración de entorno
ENVIRONMENT = 'production'

# Startup checks
try:
    logger.info('Production configuration loaded successfully')
    from django.db import connections
    connections['default'].ensure_connection()
    logger.info('Database connection established successfully')
    import redis
    redis_client = redis.Redis.from_url(CELERY_BROKER_URL)
    redis_client.ping()
    logger.info('Redis connection established successfully')
except Exception as e:
    logger.error(f'Error during production configuration initialization: {e}')
    raise

# Debug print
logger.info("DEBUG: DATABASES configuration (production.py): %s", DATABASES)