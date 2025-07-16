# /home/pablo/ai_huntred/settings/base.py
"""
Configuración base de Django para Grupo huntRED®.

Este archivo contiene la configuración común a todos los entornos (desarrollo, pruebas, producción).
Las configuraciones específicas de cada entorno deben ir en sus respectivos archivos.
"""

# Importaciones estándar
import os
import sys
import logging
import platform
from pathlib import Path
from datetime import timedelta

# Terceros
import environ
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

# Configuración de logging
logger = logging.getLogger(__name__)

# Configuración de entorno
env = environ.Env()

# Configuración de rutas
BASE_DIR = Path(__file__).resolve().parent.parent  # /home/pablo/ai_huntred/
PROJECT_ROOT = BASE_DIR.parent  # /home/pablo/

# Asegurar que el directorio base esté en el path
sys.path.append(str(PROJECT_ROOT))

# Configuración básica
SECRET_KEY = env('DJANGO_SECRET_KEY', default='django-insecure-development-key-change-in-production')
ROOT_URLCONF = 'ai_huntred.urls'
WSGI_APPLICATION = 'ai_huntred.wsgi.application'
ASGI_APPLICATION = 'ai_huntred.asgi.application'

# Configuración de entorno
ENVIRONMENT = env('DJANGO_ENVIRONMENT', default='development')

# Configuración del modelo de usuario personalizado
AUTH_USER_MODEL = 'accounts.CustomUser'

INSTALLED_APPS = [
    # Django apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party apps
    'rest_framework',
    'corsheaders',
    'django_filters',
    'silk',
    
    'drf_yasg',
    # 'channels',  # No lo incluyas aquí directamente
    
    # Aplicaciones locales
    'app.ats.accounts.apps.AccountsConfig',
    'app.apps.AppConfig',  # Incluye todos los modelos incluyendo sexsi
    'app.ats.pricing.apps.PricingConfig',  # Módulo de precios y propuestas
    'app.ats.publish.apps.PublishConfig',  # Módulo de publicación estratégica
    'app.payroll.apps.PayrollConfig',  # Sistema de nómina huntRED®
    
    # Celery apps (deben ir al final)
    'django_celery_results',
    'django_celery_beat',
]

# Opcional: agregar Channels solo si está instalado
try:
    import channels  # noqa: F401
    INSTALLED_APPS.append('channels')
except ImportError:
    import warnings
    warnings.warn('Django Channels no está instalado; funcionalidades en tiempo real deshabilitadas.', ImportWarning)

# Configuración de usuario personalizado

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'app.middleware.security.SecurityHeadersMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'app.middleware.database_adapter.DatabaseAdapterMiddleware',
    'ai_huntred.middleware.PermissionMiddleware',
    'ai_huntred.middleware.RoleMiddleware',
    'ai_huntred.middleware.BusinessUnitMiddleware',
    'ai_huntred.middleware.DivisionMiddleware',
    'silk.middleware.SilkyMiddleware',
    'ai_huntred.error_handling.ErrorHandlerMiddleware',
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# Configuración de autenticación
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Configuración de internacionalización
LANGUAGE_CODE = 'es'
TIME_ZONE = 'America/Santiago'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Archivos estáticos y multimedia
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Configuración de REST Framework
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
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
}

# Configuración CORS
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[]) if not CORS_ALLOW_ALL_ORIGINS else []

# Configuración de Celery
CELERY_BROKER_URL = env('CELERY_BROKER_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND', default='redis://localhost:6379/1')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_ENABLE_UTC = False
CELERY_TASK_ROUTES = {
    'app.ats.tasks.process_media.*': {'queue': 'media'},
    'app.ats.tasks.send_message.*': {'queue': 'messages'},
    'app.ats.tasks.analyze_content.*': {'queue': 'analysis'},
}
CELERY_TASK_QUEUES = {
    'default': {
        'exchange': 'default',
        'routing_key': 'default',
    },
    'media': {
        'exchange': 'media',
        'routing_key': 'media',
    },
    'messages': {
        'exchange': 'messages',
        'routing_key': 'messages',
    },
    'analysis': {
        'exchange': 'analysis',
        'routing_key': 'analysis',
    },
}

# Configuración de correo electrónico
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env('EMAIL_HOST', default='mail.huntred.com')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='hola@huntred.com')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='Grupo huntRED® <hola@huntred.com>')

# Configuración de chatbot
CHATBOT_CONFIG = {
    'ENABLED': True,
    'MAX_CONCURRENT_SESSIONS': 100,
    'MESSAGE_TIMEOUT': 30,
    'MAX_MESSAGE_RETRIES': 3,
    'FALLBACK_CHANNEL': 'email',
}

# Configuración de directorios
ML_MODELS_DIR = BASE_DIR / 'app' / 'models' / 'ml_models'
CARTAS_OFERTA_DIR = BASE_DIR / 'media' / 'cartas_oferta'
LOG_DIR = BASE_DIR / 'logs'

# Configuración de Sentry
SENTRY_DSN = env('SENTRY_DSN', default=None)
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],
        traces_sample_rate=1.0,
        send_default_pii=True
    )

# Configuración de Redis
REDIS_CONFIG = {
    'host': env('REDIS_HOST', default='localhost'),
    'port': env.int('REDIS_PORT', default=6379),
    'db': env.int('REDIS_DB', default=0),
    'password': env('REDIS_PASSWORD', default=None),
    'socket_timeout': 5,
    'socket_connect_timeout': 5,
    'retry_on_timeout': True,
    'max_connections': 100,
}

# Configuración de caché
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f"redis://{REDIS_CONFIG['host']}:{REDIS_CONFIG['port']}/{REDIS_CONFIG['db']}",
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'PASSWORD': REDIS_CONFIG['password'],
            'SOCKET_TIMEOUT': REDIS_CONFIG['socket_timeout'],
            'SOCKET_CONNECT_TIMEOUT': REDIS_CONFIG['socket_connect_timeout'],
            'RETRY_ON_TIMEOUT': REDIS_CONFIG['retry_on_timeout'],
            'CONNECTION_POOL_KWARGS': {
                'max_connections': REDIS_CONFIG['max_connections'],
            },
        },
        'KEY_PREFIX': 'ai_huntred_',
    }
}

# Configuración de canales de mensajería
# Las configuraciones de los canales se obtienen de sus respectivos modelos API:
# - WhatsApp: WhatsAppAPI
# - Telegram: TelegramAPI
# - Messenger: MessengerAPI
# - Instagram: InstagramAPI
# - Slack: SlackAPI
# - LinkedIn: LinkedInAPI
# - X (Twitter): XAPI

# Configuración de PayPal
PAYPAL_CONFIG = {
    'mode': env('PAYPAL_MODE', default='sandbox'),
    'client_id': env('PAYPAL_CLIENT_ID', default=None),
    'client_secret': env('PAYPAL_CLIENT_SECRET', default=None),
    'return_url': env('PAYPAL_RETURN_URL', default=None),
    'cancel_url': env('PAYPAL_CANCEL_URL', default=None)
}

# Configuración de WordPress
WORDPRESS_CONFIG = {
    'api_url': env('WORDPRESS_API_URL', default=None),
    'username': env('WORDPRESS_USERNAME', default=None),
    'password': env('WORDPRESS_PASSWORD', default=None)
}

# Configuración de Stripe
STRIPE_CONFIG = {
    'api_key': env('STRIPE_API_KEY', default=''),
    'webhook_secret': env('STRIPE_WEBHOOK_SECRET', default=''),
    'currency': env('STRIPE_CURRENCY', default='mxn'),
    'success_url': env('STRIPE_SUCCESS_URL', default='/payments/success/'),
    'cancel_url': env('STRIPE_CANCEL_URL', default='/payments/cancel/')
}

# Configuración de X (Twitter)
X_CONFIG = {
    'api_key': env('X_API_KEY', default=''),
    'api_secret': env('X_API_SECRET', default=''),
    'access_token': env('X_ACCESS_TOKEN', default=''),
    'access_token_secret': env('X_ACCESS_TOKEN_SECRET', default='')
}

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

# Crear directorios necesarios
for directory in [LOG_DIR, STATIC_ROOT, MEDIA_ROOT, ML_MODELS_DIR]:
    directory.mkdir(parents=True, exist_ok=True) 