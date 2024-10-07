# /home/amigro/chatbot_django/settings.py
import os
import sentry_sdk
from pathlib import Path
from django.conf import settings
from sentry_sdk.integrations.django import DjangoIntegration


BASE_DIR = Path(__file__).resolve().parent.parent

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    integrations=[DjangoIntegration()],
    traces_sample_rate=1.0,
    send_default_pii=True
)

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-rxkhgtlsk84*0)-ivntl4&cnt8sp9ahu0aib$709q^crthve&u')

DEBUG = os.getenv('DJANGO_DEBUG', 'True') == 'True'

ALLOWED_HOSTS = [
    "35.209.109.141",
    "chatbot.amigro.org",
    "www.chat.amigro.org",
    "localhost",
    "127.0.0.1"
]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'app',
    'corsheaders',  # Correcto
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # CORS middleware
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Para archivos estáticos en producción
]

ROOT_URLCONF = 'chatbot_django.urls'

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

WSGI_APPLICATION = 'chatbot_django.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
#DATABASES = {
#    'default': {
#        'ENGINE': 'django.db.backends.postgresql',
#        'NAME': os.getenv('DB_NAME'),
#        'USER': os.getenv('DB_USER'),
#        'PASSWORD': os.getenv('DB_PASSWORD'),
#        'HOST': os.getenv('DB_HOST'),
#        'PORT': os.getenv('DB_PORT', '5432'),
#    }
#}
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'America/Mexico_City'
USE_TZ = True

USE_I18N = True

USE_L10N = True


STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CORS configuration
# CORS_ORIGIN_ALLOW_ALL = True  # Cambia a False en producción y define los dominios permitidos
CORS_ORIGIN_ALLOW_ALL = False
CORS_ORIGIN_WHITELIST = [
     'https://chatbot.amigro.org',
     'https://amigro.org',
]


# Celery configuration
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
CELERY_TASK_RETRY_DELAY = 300  # Reintentar cada 5 minutos
CELERY_TASK_MAX_RETRIES = 5  # Máximo 5 reintentos

CELERY_WORKER_LOG_FILE = '/home/amigro/logs/worker.log'
CELERY_WORKER_LOG_LEVEL = 'INFO'
CELERY_WORKER_LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'


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
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/error.log'),
            'formatter': 'verbose',
        },
        'telegram_file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/telegram.log'),
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'whatsapp_file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/whatsapp.log'),
            'formatter': 'verbose',
        },
        'messenger_file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/messenger.log'),
            'formatter': 'verbose',
        },
        'instagram_file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/instagram.log'),
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'ERROR',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': False,
        },
        'telegram': {
            'handlers': ['telegram_file', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'whatsapp': {
            'handlers': ['whatsapp_file', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'messenger': {
            'handlers': ['messenger_file', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'instagram': {
            'handlers': ['instagram_file', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}
