# Ubicación del archivo: /home/pablollh/ai_huntred/settings.py
# Archivo Base de Configuración de Django


import os
from pathlib import Path
# Configuration for dynamic email settings per Business Unit (BU)

# Import the required libraries
from django.core.mail import get_connection, send_mail
from django.conf import settings
#from app.models import ConfiguracionBU  # Assuming we have a model defined for email configurations


# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
ML_MODELS_DIR = os.path.join(BASE_DIR, 'app', 'models', 'ml_models')

# Seguridad
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'reemplazar_esta_clave')
DEBUG = os.getenv('DJANGO_DEBUG', 'True') == 'True'
#ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', '*').split(',')
ALLOWED_HOSTS = ['ai.huntred.com', '34.57.227.244', 'localhost']

#Entorno General
# Administrador General (si aplica)
GENERAL_ADMIN_EMAIL = 'pablo@huntred.com'
GENERAL_ADMIN_PHONE = '+525518490291'  # Número de WhatsApp del administrador general
# Aplicaciones Instaladas
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
    # Librerías externas
    'rest_framework',
    'django_filters',
    'corsheaders',
    'drf_yasg',
]

# Middleware
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

# URL Configuration
ROOT_URLCONF = 'ai_huntred.urls'

# Templates
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

# WSGI Application
WSGI_APPLICATION = 'ai_huntred.wsgi.application'

# Base de Datos
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'grupo_huntred_ai_db',
        'USER': 'grupo_huntred_user',
        'PASSWORD': 'Natalia&Patricio1113!',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Configuración de Idioma
LANGUAGE_CODE = 'es-mx'
TIME_ZONE = 'America/Mexico_City'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Archivos Estáticos
STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Media
MEDIA_URL = '/media/'
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
}

# Configuración de Celery
CELERY_BROKER_URL = 'redis://127.0.0.1:6379/0'
CELERY_RESULT_BACKEND = 'redis://127.0.0.1:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'America/Mexico_City'
CELERY_ENABLE_UTC = True
CELERY_WORKER_CONCURRENCY = 2  # Ajusta según tu CPU

# CORS Configuración
cors_origins = os.getenv('CORS_ALLOWED_ORIGINS', '*')

if cors_origins == '*':
    CORS_ALLOW_ALL_ORIGINS = True
else:
    CORS_ALLOWED_ORIGINS = cors_origins.split(',')

# Logging
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
        'debug_file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/debug.log'),
            'formatter': 'verbose',
        },
        'messenger_file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/messenger.log'),
            'formatter': 'verbose',
        },
        'whatsapp_file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/whatsapp.log'),
            'formatter': 'verbose',
        },
        'instagram_file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/instagram.log'),
            'formatter': 'verbose',
        },
        'telegram_file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/telegram.log'),
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'messenger': {
            'handlers': ['messenger_file', 'debug_file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'whatsapp': {
            'handlers': ['whatsapp_file', 'debug_file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'instagram': {
            'handlers': ['instagram_file', 'debug_file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'telegram': {
            'handlers': ['telegram_file', 'debug_file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['debug_file'],
        'level': 'DEBUG',
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
        """
        Inicializa el backend de correo para una unidad de negocio específica.

        :param business_unit: Instancia de BusinessUnit asociada a ConfiguracionBU.
        """
        try:
            self.config = ConfiguracionBU.objects.get(business_unit=business_unit)
        except ConfiguracionBU.DoesNotExist:
            raise ValueError(f"No se encontró configuración para la unidad de negocio: {business_unit}")

    def send_email(self, subject, message, recipient_list, from_email=None):
        """
        Envía un correo utilizando las configuraciones dinámicas de ConfiguracionBU.

        :param subject: str - Asunto del correo.
        :param message: str - Cuerpo del correo.
        :param recipient_list: list - Lista de destinatarios.
        :param from_email: str - Dirección de correo del remitente (opcional).
        """
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