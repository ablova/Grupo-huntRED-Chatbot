# Ubicación del archivo: /home/amigro/chatbot_django/settings/base.py
# Archivo Base de Configuración de Django


import os
from pathlib import Path
# Configuration for dynamic email settings per Business Unit (BU)

# Import the required libraries
from django.core.mail import get_connection
from django.conf import settings
from .models import EmailConfig  # Assuming we have a model defined for email configurations


# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
ML_MODELS_DIR = os.path.join(BASE_DIR, 'app', 'models', 'ml_models')

# Seguridad
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'reemplazar_esta_clave')
DEBUG = os.getenv('DJANGO_DEBUG', 'True') == 'True'
ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', '*').split(',')

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
    # Apps internas
    'chatbot',
    'app'
    # Librerías externas
    'rest_framework',
    'django_filters',
    'corsheaders',
    'drf_yasg',
    'encrypted_fields',
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
ROOT_URLCONF = 'chatbot_django.urls'

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
            'loaders': [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
            ],
        },
    },
]

# WSGI Application
WSGI_APPLICATION = 'chatbot_django.wsgi.application'

# Base de Datos
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'chatbot_db'),
        'USER': os.getenv('DB_USER', 'amigro_user'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'password'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
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

# CORS Configuración
CORS_ALLOWED_ORIGINS = os.getenv('CORS_ALLOWED_ORIGINS', '*').split(',')

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
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/debug.log'),
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['file'],
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
        config = EmailConfig.objects.get(business_unit=business_unit)
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
    def __init__(self, business_unit):
        self.business_unit = business_unit
        self.email_settings = get_email_backend(business_unit)

    def send_email(self, subject, message, recipient_list, from_email=None):
        """
        Send an email using the dynamic settings for the specified business unit.

        :param subject: str - Subject of the email.
        :param message: str - Body of the email.
        :param recipient_list: list - List of recipients.
        :param from_email: str - Custom from email (optional).
        """
        email_backend = get_connection(
            backend='django.core.mail.backends.smtp.EmailBackend',
            host=self.email_settings['EMAIL_HOST'],
            port=self.email_settings['EMAIL_PORT'],
            username=self.email_settings['EMAIL_HOST_USER'],
            password=self.email_settings['EMAIL_HOST_PASSWORD'],
            use_tls=self.email_settings['EMAIL_USE_TLS'],
            use_ssl=self.email_settings['EMAIL_USE_SSL'],
        )

        send_mail(
            subject=subject,
            message=message,
            from_email=from_email or self.email_settings['DEFAULT_FROM_EMAIL'],
            recipient_list=recipient_list,
            connection=email_backend,
        )
