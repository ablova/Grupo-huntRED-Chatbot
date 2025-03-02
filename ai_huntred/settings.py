# Ubicación del archivo: /home/pablo/ai_huntred/settings.py
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
ML_MODELS_DIR = os.path.join(BASE_DIR, 'ml_models')

# Asegurar que existe el directorio de logs
os.makedirs(os.path.join(BASE_DIR, 'logs'), exist_ok=True)

# Lee el archivo .env
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# Sentry configuration
sentry_sdk.init(
    dsn=env('SENTRY_DSN'),
    integrations=[DjangoIntegration()],
    traces_sample_rate=env.float('SENTRY_SAMPLE_RATE', default=0.2),
    _experiments={
        "continuous_profiling_auto_start": True,
    },
    send_default_pii=env.bool('SENTRY_SEND_PII', default=True),
    debug=env.bool('SENTRY_DEBUG', default=False),
)

# Paths
ML_MODELS_DIR = os.path.join(BASE_DIR, 'app', 'models', 'ml_models')
# utils.py
import tensorflow as tf
def load_tensorflow():
    tf.config.threading.set_intra_op_parallelism_threads(1)
    tf.config.threading.set_inter_op_parallelism_threads(1)
    return tf

# Donde lo necesites
from .utils import load_tensorflow
tf = load_tensorflow()
# Security Settings
SECRET_KEY = env('DJANGO_SECRET_KEY')
DEBUG = env.bool('DJANGO_DEBUG', default=False)
ALLOWED_HOSTS = env.list('DJANGO_ALLOWED_HOSTS', default=['127.0.0.1', 'localhost', 'ai.huntred.com', '34.57.227.244'])

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
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Celery Configuration
CELERY_BROKER_URL = env('CELERY_BROKER_URL')
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = env('TIMEZONE', default='America/Mexico_City')
CELERY_ENABLE_UTC = True
CELERY_WORKER_CONCURRENCY = env.int('CELERY_WORKER_CONCURRENCY', default=1)
CELERYD_PREFETCH_MULTIPLIER = 1  # Para evitar que un worker tome demasiadas tareas
CELERY_TASK_ACKS_LATE = True
CELERY_WORKER_MAX_MEMORY_PER_CHILD = 100000  # 100MB por proceso
CELERYD_MAX_TASKS_PER_CHILD = 10  # 🔹 Reinicia workers después de X tareas
CELERYD_MAX_MEMORY_PER_CHILD = 150000  # 🔹 Evita uso excesivo de memoria
# Habilitar reintentos de conexión en startup
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True

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
    #'django_ratelimit',  eliminado para no generar problemas
    'django_celery_beat',
    'django_celery_results',
    # Apps internas
    'app',
    'app.chatbot',
    'app.ml',
    'app.utilidades',
    'app.sexsi',
    'app.milkyleak',
    # Manejo de Diseño - WoWDash
    #'app.wowdash',
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
        'DIRS': [
            os.path.join(BASE_DIR, 'templates'),  # 🔹 Plantillas generales
            os.path.join(BASE_DIR, 'app', 'templates', 'admin'),  # 📌 Templates Admin
            os.path.join(BASE_DIR, 'app', 'sexsi', 'templates'), # 🔥 Plantillas de SEXSI
        ],
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


# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'  # Por ahora, usa el predeterminado
EMAIL_HOST = env('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')

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


# Define el directorio de logs y créalo si no existe
LOG_DIR = os.path.join(BASE_DIR, 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{asctime} {levelname} {name} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
            'level': 'INFO',
        },
        'app_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'app.log'),
            'formatter': 'verbose',
            'maxBytes': 10 * 1024 * 1024,  # 10 MB
            'backupCount': 3,  # Hasta 3 archivos de respaldo
            'level': 'INFO',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'app_file'],
            'level': 'INFO',
            'propagate': True,
        },
        '': {  # Logger raíz
            'handlers': ['app_file'],
            'level': 'INFO',
            'propagate': True,
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