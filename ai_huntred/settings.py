# /home/pablo/ai_huntred/settings.py

import os
import logging
import environ
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from pathlib import Path
import tensorflow as tf

# --- Configuración temprana de TensorFlow ---
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"  # Desactiva GPU
tf.config.threading.set_intra_op_parallelism_threads(1)
tf.config.threading.set_inter_op_parallelism_threads(1)
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

# --- Configuración de entorno ---
env = environ.Env()
BASE_DIR = Path(__file__).resolve().parent.parent
env_file = os.path.join(BASE_DIR, '.env')

# Validar existencia del archivo .env (sin usar logger aún)
if not os.path.exists(env_file):
    raise FileNotFoundError(f"Environment file not found: {env_file}")
if not os.access(env_file, os.R_OK):
    raise PermissionError(f"Environment file not readable: {env_file}")

# Cargar variables de entorno
environ.Env.read_env(env_file)

# --- Seguridad y entorno ---
SECRET_KEY = env('DJANGO_SECRET_KEY', default='hfmrpTNRwmQ1F7gZI1DNKaQ9gNw3cgayKFB0HK_gt9BKJEnLy60v1v0PnkZtX3OkY48')
DEBUG = env.bool('DJANGO_DEBUG', default=False)
ALLOWED_HOSTS = env.list('DJANGO_ALLOWED_HOSTS', default=['ai.huntred.com', '127.0.0.1', 'localhost', '34.57.227.244'])

# Configuración de base de datos
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME', default='g_huntred_ai_db'),
        'USER': env('DB_USER', default='g_huntred_pablo'),
        'PASSWORD': env('DB_PASSWORD', default='Natalia&Patricio1113!'),
        'HOST': env('DB_HOST', default='localhost'),
        'PORT': env('DB_PORT', default='5432'),
        'CONN_MAX_AGE': env.int('DB_CONN_MAX_AGE', default=60),
        'OPTIONS': {
            'connect_timeout': env.int('DB_CONNECT_TIMEOUT', default=10),
        },
    }
}
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
WAIT_FOR_DB = {
    'RETRIES': 30,
    'DELAY': 1,
}

# Aplicaciones instaladas
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_celery_beat',
    'django_celery_results',
    'corsheaders',
    'rest_framework',
    'django_filters',
    'drf_yasg',
    'app',
    'app.chatbot',
    'app.ml',
    'app.utilidades',
    'app.sexsi',
    'app.milkyleak',
    'silk',
#    'django_wait_for_db',  # Debe estar aquí
]

# Middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Silk Configuration
SILKY_PYTHON_PROFILER = True
SILKY_AUTHENTICATION = True
SILKY_AUTHORISATION = True
SILKY_PERMISSIONS = lambda user: user.is_superuser
SILKY_META = True
SILKY_INTERCEPT_PERCENT = 100  # Profile all requests
SILKY_MAX_RECORDED_REQUESTS = 10000

# Seguridad para HTTPS
SECURE_SSL_REDIRECT = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
X_FRAME_OPTIONS = 'DENY'

# Configuración de URLs y plantillas
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
ASGI_APPLICATION = 'ai_huntred.asgi.application'

# Internacionalización
LANGUAGE_CODE = env('LANGUAGE_CODE', default='es-mx')
TIME_ZONE = env('TIMEZONE', default='America/Mexico_City')
USE_I18N = True
USE_TZ = True

# Archivos estáticos y multimedia
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Directorios
ML_MODELS_DIR = os.path.join(BASE_DIR, 'app', 'models', 'ml_models')
LOG_DIR = os.path.join(BASE_DIR, 'logs')
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Create directories (permissions set manually)
for directory in [LOG_DIR, STATIC_ROOT, MEDIA_ROOT, ML_MODELS_DIR]:
    os.makedirs(directory, exist_ok=True)
    #logger.debug(f"Ensured directory exists: {directory}")

# Ubicación del archivo: /home/pablo/ai_huntred/settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
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
            'level': 'INFO',
            'formatter': 'simple',
        },
        'app_file': {
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'app.log'),
            'level': 'DEBUG',  # Más detalle para depuración
            'formatter': 'verbose',
        },
        'chatbot_file': {
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'chatbot.log'),
            'level': 'DEBUG',
            'formatter': 'verbose',
        },
        'celery_file': {
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'celery.log'),
            'level': 'DEBUG',
            'formatter': 'verbose',
        },
        'gunicorn_file': {
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'gunicorn.log'),
            'level': 'INFO',
            'formatter': 'verbose',
        },
        'nlp_file': {
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'nlp.log'),
            'level': 'DEBUG',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'app_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'app': {
            'handlers': ['console', 'app_file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'chatbot': {
            'handlers': ['console', 'chatbot_file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'celery': {
            'handlers': ['console', 'celery_file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'gunicorn': {
            'handlers': ['console', 'gunicorn_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'nlp': {
            'handlers': ['console', 'nlp_file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# Configuración de Celery
CELERY_BROKER_URL = env('CELERY_BROKER_URL', default='redis://127.0.0.1:6379/0')
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND', default='redis://127.0.0.1:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'America/Mexico_City'
CELERY_WORKER_CONCURRENCY = env.int('CELERY_WORKER_CONCURRENCY', default=2)

# Sentry
if env('SENTRY_DSN', default=None):
    sentry_sdk.init(
        dsn=env('SENTRY_DSN'),
        integrations=[DjangoIntegration()],
        traces_sample_rate=env.float('SENTRY_SAMPLE_RATE', default=0.2),
        send_default_pii=env.bool('SENTRY_SEND_PII', default=False),
    )

# Email
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env('EMAIL_HOST', default='mail.huntred.com')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='hola@huntred.com')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='Natalia&Patricio1113!')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='Grupo huntRED® <hola@huntred.com>')

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.IsAuthenticated'],
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend'],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': env('THROTTLE_ANON', default='100/day'),
        'user': env('THROTTLE_USER', default='1000/day'),
    },
}

# CORS
CORS_ALLOW_ALL_ORIGINS = env.bool('CORS_ALLOW_ALL_ORIGINS', default=False)
CORS_ALLOW_CREDENTIALS = env.bool('CORS_ALLOW_CREDENTIALS', default=False)
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[]) if not CORS_ALLOW_ALL_ORIGINS else []


# Dynamic Email Backend
def get_email_backend(business_unit):
    from django.apps import apps
    BusinessUnit = apps.get_model('app', 'BusinessUnit')
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
    except BusinessUnit.DoesNotExist:
        raise ValueError(f"Email configuration not found for Business Unit: {business_unit}")

class DynamicEmailBackend:
    def __init__(self, business_unit):
        from django.apps import apps
        ConfiguracionBU = apps.get_model('app', 'ConfiguracionBU')
        try:
            self.config = ConfiguracionBU.objects.get(business_unit=business_unit)
        except ConfiguracionBU.DoesNotExist:
            raise ValueError(f"No se encontró configuración para la unidad de negocio: {business_unit}")

    def send_email(self, subject, message, recipient_list, from_email=None):
        from django.core.mail import get_connection, send_mail
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
