# Ubicación del archivo: /home/pablollh/ai_huntred/settings.py
import os
from pathlib import Path
from django.core.mail import get_connection, send_mail
from django.conf import settings
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
import environ
import logging

# Inicializar environ
env = environ.Env()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Asegurar que existe el directorio de logs
os.makedirs(os.path.join(BASE_DIR, 'logs'), exist_ok=True)

# Lee el archivo .env
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# Sentry configuration
sentry_sdk.init(
    dsn=env('SENTRY_DSN'),
    integrations=[DjangoIntegration()],
    traces_sample_rate=env.float('SENTRY_SAMPLE_RATE', default=1.0),
    _experiments={
        "continuous_profiling_auto_start": True,
    },
    send_default_pii=env.bool('SENTRY_SEND_PII', default=True),
    debug=env.bool('SENTRY_DEBUG', default=False),
)

# Paths
ML_MODELS_DIR = os.path.join(BASE_DIR, 'app', 'models', 'ml_models')

# Security Settings
SECRET_KEY = env('DJANGO_SECRET_KEY')
DEBUG = env.bool('DJANGO_DEBUG', default=False)
ALLOWED_HOSTS = env.list('DJANGO_ALLOWED_HOSTS', default=['127.0.0.1', 'localhost', 'ai.huntred.com'])

# General Environment
GENERAL_ADMIN_EMAIL = env('ADMIN_EMAIL')
GENERAL_ADMIN_PHONE = env('ADMIN_PHONE')

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME'),
        'USER': env('DB_USER'),
        'PASSWORD': env('DB_PASSWORD'),
        'HOST': env('DB_HOST'),
        'PORT': env('DB_PORT'),
        'CONN_MAX_AGE': env.int('DB_CONN_MAX_AGE', default=60),
        'OPTIONS': {
            'connect_timeout': env.int('DB_CONNECT_TIMEOUT', default=10),
        }
    }
}

# Celery Configuration
CELERY_BROKER_URL = env('CELERY_BROKER_URL')
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = env('TIMEZONE', default='America/Mexico_City')
CELERY_ENABLE_UTC = True
CELERY_WORKER_CONCURRENCY = env.int('CELERY_WORKER_CONCURRENCY', default=2)

# CORS Configuration
CORS_ALLOW_ALL_ORIGINS = env.bool('CORS_ALLOW_ALL_ORIGINS', default=False)
CORS_ALLOW_CREDENTIALS = env.bool('CORS_ALLOW_CREDENTIALS', default=False)

# Las aplicaciones se mantienen igual...
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_celery_beat',
    # Apps internas
    'app',
    'app.chatbot',
    'app.ml',
    'app.utilidades',
    # Librerías externas
    'rest_framework',
    'django_filters',
    'corsheaders',
    'drf_yasg',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'ai_huntred.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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

WSGI_APPLICATION = 'ai_huntred.wsgi.application'

# Configuración de Idioma
LANGUAGE_CODE = env('LANGUAGE_CODE', default='es-mx')
TIME_ZONE = env('TIMEZONE', default='America/Mexico_City')
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Archivos Estáticos
STATIC_URL = env('STATIC_URL', default='/static/')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Media
MEDIA_URL = env('MEDIA_URL', default='/media/')
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': env('THROTTLE_ANON', default='100/day'),
        'user': env('THROTTLE_USER', default='1000/day')
    }
}

# Logging Configuration
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
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
            'level': env('CONSOLE_LOG_LEVEL', default='INFO'),
        },
        'debug_file': {
            'level': env('DEBUG_LOG_LEVEL', default='ERROR'),
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/debug.log'),
            'formatter': 'verbose',
            'maxBytes': env.int('LOG_MAX_BYTES', default=10485760),  # 10 MB
            'backupCount': env.int('LOG_BACKUP_COUNT', default=3),
        },
        'messenger_file': {
            'level': env('MESSENGER_LOG_LEVEL', default='ERROR'),
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/messenger.log'),
            'formatter': 'verbose',
            'maxBytes': env.int('LOG_MAX_BYTES', default=10485760),
            'backupCount': env.int('LOG_BACKUP_COUNT', default=3),
        },
        'whatsapp_file': {
            'level': env('WHATSAPP_LOG_LEVEL', default='ERROR'),
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/whatsapp.log'),
            'formatter': 'verbose',
            'maxBytes': env.int('LOG_MAX_BYTES', default=10485760),
            'backupCount': env.int('LOG_BACKUP_COUNT', default=3),
        },
        'instagram_file': {
            'level': env('INSTAGRAM_LOG_LEVEL', default='ERROR'),
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/instagram.log'),
            'formatter': 'verbose',
            'maxBytes': env.int('LOG_MAX_BYTES', default=10485760),
            'backupCount': env.int('LOG_BACKUP_COUNT', default=3),
        },
        'telegram_file': {
            'level': env('TELEGRAM_LOG_LEVEL', default='ERROR'),
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/telegram.log'),
            'formatter': 'verbose',
            'maxBytes': env.int('LOG_MAX_BYTES', default=10485760),
            'backupCount': env.int('LOG_BACKUP_COUNT', default=3),
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'debug_file'],
            'level': env('DJANGO_LOG_LEVEL', default='INFO'),
            'propagate': True,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': env('DB_LOG_LEVEL', default='INFO'),
            'propagate': False,
        },
        'messenger': {
            'handlers': ['messenger_file', 'console'],
            'level': env('MESSENGER_LOG_LEVEL', default='ERROR'),
            'propagate': False,
        },
        'whatsapp': {
            'handlers': ['whatsapp_file', 'console'],
            'level': env('WHATSAPP_LOG_LEVEL', default='ERROR'),
            'propagate': False,
        },
        'instagram': {
            'handlers': ['instagram_file', 'console'],
            'level': env('INSTAGRAM_LOG_LEVEL', default='ERROR'),
            'propagate': False,
        },
        'telegram': {
            'handlers': ['telegram_file', 'console'],
            'level': env('TELEGRAM_LOG_LEVEL', default='ERROR'),
            'propagate': False,
        },
    },
}

# Para tener las configuraciones basadas en la unidad de negocio.
def get_email_backend(business_unit):
    """
    Fetch email settings dynamically based on the business unit and return
    the appropriate email backend configuration.

    :param business_unit: str - The business unit identifier (e.g., 'amigro', 'huntu', 'huntred').
    :return: dict - Email backend configuration.
    """
    try:
        config = BusinessUnit.objects.get(business_unit=business_unit)
        return {
            'EMAIL_HOST': config.email_host,
            'EMAIL_PORT': config.email_port,
            'EMAIL_HOST_USER': config.email_user,
            'EMAIL_HOST_PASSWORD': config.email_password,
            'EMAIL_USE_TLS': config.use_tls,
            'EMAIL_USE_SSL': config.use_ssl,
            'DEFAULT_FROM_EMAIL': config.email_from,
        }
    except EmailConfig.DoesNotExist:
        raise ValueError(f"Email configuration not found for Business Unit: {business_unit}")

# Function to dynamically set email backend
class DynamicEmailBackend:
    """
    Clase para enviar correos utilizando configuraciones SMTP dinámicas
    obtenidas del modelo ConfiguracionBU.
    """
    def __init__(self, business_unit):
        try:
            self.config = ConfiguracionBU.objects.get(business_unit=business_unit)
        except ConfiguracionBU.DoesNotExist:
            raise ValueError(f"No se encontró configuración para la unidad de negocio: {business_unit}")

    def send_email(self, subject, message, recipient_list, from_email=None):
        smtp_config = self.config.get_smtp_config()

        email_backend = get_connection(
            backend='django.core.mail.backends.smtp.EmailBackend',
            host=smtp_config['host'],
            port=smtp_config['port'],
            username=smtp_config['username'],
            password=smtp_config['password'],
            use_tls=smtp_config['use_tls'],
            use_ssl=smtp_config['use_ssl'],
        )

        send_mail(
            subject=subject,
            message=message,
            from_email=from_email or self.config.correo_bu,
            recipient_list=recipient_list,
            connection=email_backend,
        )