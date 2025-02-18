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
CELERY_WORKER_CONCURRENCY = env.int('CELERY_WORKER_CONCURRENCY', default=2)
CELERYD_PREFETCH_MULTIPLIER = 1  # Para evitar que un worker tome demasiadas tareas
CELERY_TASK_ACKS_LATE = True
CELERY_WORKER_MAX_MEMORY_PER_CHILD = 100000  # 100MB por proceso
CELERYD_MAX_TASKS_PER_CHILD = 10  # 🔹 Reinicia workers después de X tareas
CELERYD_MAX_MEMORY_PER_CHILD = 150000  # 🔹 Evita uso excesivo de memoria

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
    'app.sexsi',
    'app.milkyleak',
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
        # en el debug file, quisiera los errores más criticos, hay alguna manera de implementar eso?
        'debug_file': {
            'level': 'CRITICAL',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'debug.log'),
            'formatter': 'verbose',
            'maxBytes': env.int('LOG_MAX_BYTES', default=10485760),  # 10 MB
            'backupCount': env.int('LOG_BACKUP_COUNT', default=3),
        },
        # Handler global (opcional)
        'global_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'app.log'),
            'formatter': 'verbose',
            'maxBytes': 10485760,  # 10 MB
            'backupCount': 3,
            'level': 'DEBUG',
        },
        # Handlers específicos por categoría
        'chatbot_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'chatbot.log'),
            'formatter': 'verbose',
            'maxBytes': 10485760,
            'backupCount': 2,
            'level': 'DEBUG',
        },
        'nlp_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'nlp.log'),
            'formatter': 'verbose',
            'maxBytes': 10485760,
            'backupCount': 2,
            'level': 'DEBUG',
        },
        'gpt_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'gpt.log'),
            'formatter': 'verbose',
            'maxBytes': 10485760,
            'backupCount': 2,
            'level': 'INFO',
        },
        'vacantes_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'vacantes.log'),
            'formatter': 'verbose',
            'maxBytes': 10485760,
            'backupCount': 2,
            'level': 'INFO',
        },
        'scraping_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'scraping.log'),
            'formatter': 'verbose',
            'maxBytes': 10485760,
            'backupCount': 2,
            'level': 'DEBUG',
        },
        'parse_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'parse.log'),
            'formatter': 'verbose',
            'maxBytes': 10485760,
            'backupCount': 2,
            'level': 'DEBUG',
        },
        'ml_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'ml.log'),
            'formatter': 'verbose',
            'maxBytes': 10485760,
            'backupCount': 2,
            'level': 'INFO',
        },
        'signature_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'signature.log'),
            'formatter': 'verbose',
            'maxBytes': 10485760,
            'backupCount': 2,
            'level': 'DEBUG',
        },
        'config_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'config.log'),
            'formatter': 'verbose',
            'maxBytes': 10485760,
            'backupCount': 2,
            'level': 'INFO',
        },
        'dashboard_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'dashboard.log'),
            'formatter': 'verbose',
            'maxBytes': 10485760,
            'backupCount': 2,
            'level': 'INFO',
        },
        'tasks_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'tasks.log'),
            'formatter': 'verbose',
            'maxBytes': 10485760,
            'backupCount': 2,
            'level': 'INFO',
        },
        'tests_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'tests.log'),
            'formatter': 'verbose',
            'maxBytes': 10485760,
            'backupCount': 2,
            'level': 'DEBUG',
        },
        'views_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'views.log'),
            'formatter': 'verbose',
            'maxBytes': 10485760,
            'backupCount': 2,
            'level': 'DEBUG',
        },
                'messenger_file': {
            'level': env('MESSENGER_LOG_LEVEL', default='ERROR'),
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'messenger.log'),
            'formatter': 'verbose',
            'maxBytes': env.int('LOG_MAX_BYTES', default=10485760),
            'backupCount': env.int('LOG_BACKUP_COUNT', default=3),
        },
        'whatsapp_file': {
            'level': env('WHATSAPP_LOG_LEVEL', default='ERROR'),
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'whatsapp.log'),
            'formatter': 'verbose',
            'maxBytes': env.int('LOG_MAX_BYTES', default=10485760),
            'backupCount': env.int('LOG_BACKUP_COUNT', default=3),
        },
        'instagram_file': {
            'level': env('INSTAGRAM_LOG_LEVEL', default='ERROR'),
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'instagram.log'),
            'formatter': 'verbose',
            'maxBytes': env.int('LOG_MAX_BYTES', default=10485760),
            'backupCount': env.int('LOG_BACKUP_COUNT', default=3),
        },
        'telegram_file': {
            'level': env('TELEGRAM_LOG_LEVEL', default='ERROR'),
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'telegram.log'),
            'formatter': 'verbose',
            'maxBytes': env.int('LOG_MAX_BYTES', default=10485760),
            'backupCount': env.int('LOG_BACKUP_COUNT', default=3),
        },
        'celery': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOG_DIR, 'celery.log'),
            'formatter': 'verbose',
        },
        # Handlers para workflows de cada unidad de negocio
        'amigro_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'amigro.log'),
            'formatter': 'verbose',
            'maxBytes': 10485760,
            'backupCount': 2,
            'level': 'INFO',
        },
        'executive_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'executive.log'),
            'formatter': 'verbose',
            'maxBytes': 10485760,
            'backupCount': 2,
            'level': 'INFO',
        },
        'huntred_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'huntred.log'),
            'formatter': 'verbose',
            'maxBytes': 10485760,
            'backupCount': 2,
            'level': 'INFO',
        },
        'huntu_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'huntu.log'),
            'formatter': 'verbose',
            'maxBytes': 10485760,
            'backupCount': 2,
            'level': 'INFO',
        },
        'sexsi_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'sexsi.log'),
            'formatter': 'verbose',
            'maxBytes': 10485760,
            'backupCount': 2,
            'level': 'INFO',
        },
        'milkyleak_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'milkyleak.log'),
            'formatter': 'verbose',
            'maxBytes': 10485760,
            'backupCount': 2,
            'level': 'DEBUG',
        },
        'utilidades_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'utilidades.log'),
            'formatter': 'verbose',
            'maxBytes': 10485760,
            'backupCount': 2,
            'level': 'DEBUG',
        },
    },
    'loggers': {
        # Logger raíz (todos los módulos que no tienen configuración específica usarán el global)
        '': {
            'handlers': ['global_file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        # EN el de DEBUG, habiamos comentado que los más criticos, si esto choca con lo expresado, solo informar y vemos como procedemos.
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
        # Categorías específicas
        'app.chatbot': {
            'handlers': ['chatbot_file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'app.chatbot.nlp': {
            'handlers': ['nlp_file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'app.chatbot.gpt': {
            'handlers': ['gpt_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'app.utilidades.vacantes': {
            'handlers': ['vacantes_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'app.utilidades.scraping': {
            'handlers': ['scraping_file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'app.utilidades.parse': {
            'handlers': ['parse_file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'app.ml': {
            'handlers': ['ml_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'app.utilidades.signature': {
            'handlers': ['signature_file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'app': {  # Para configuración (admin, apps, models, signals, etc.)
            'handlers': ['config_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'app.dashboard': {
            'handlers': ['dashboard_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'app.tasks': {
            'handlers': ['tasks_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'app.tests': {
            'handlers': ['tests_file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'app.views': {
            'handlers': ['views_file'],
            'level': 'DEBUG',
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
        'celery': {
            'handlers': ['celery'],
            'level':  env('DJANGO_LOG_LEVEL', default='INFO'),
            'propagate': False,
        },
        # Workflows por unidad
        'app.chatbot.workflows.amigro': {
            'handlers': ['amigro_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'app.chatbot.workflows.executive': {
            'handlers': ['executive_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'app.chatbot.workflows.huntred': {
            'handlers': ['huntred_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'app.chatbot.workflows.huntu': {
            'handlers': ['huntu_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'app.chatbot.workflows.sexsi': {
            'handlers': ['sexsi_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'app.milkyleak': {
            'handlers': ['milkyleak_file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'app.utilidades': {
            'handlers': ['utilidades_file'],
            'level': 'DEBUG',
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