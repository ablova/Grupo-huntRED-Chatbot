# /home/pablo/ai_huntred/settings.py

import os
import logging
import environ
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from pathlib import Path
import tensorflow as tf
import sys
from ai_huntred.config.security import SecurityConfig
from ai_huntred.config.logging import setup_logging
from ai_huntred.config.optimization import OptimizationConfig
from ai_huntred.config.monitoring import MonitoringConfig


# --- Configuración de NLP ---
# Switch para controlar el uso de Spacy vs Tabiya
NLP_USE_TABIYA = env.bool('NLP_USE_TABIYA', default=True)  # Habilitar/deshabilitar Tabiya
NLP_MIN_TEXT_LENGTH = env.int('NLP_MIN_TEXT_LENGTH', default=100)  # Longitud mínima para usar Tabiya
NLP_MAX_REQUESTS_PER_MINUTE = env.int('NLP_MAX_REQUESTS_PER_MINUTE', default=100)  # Limite de requests a Tabiya

# --- Configuración de Tabiya Technologies ---
TABIYA_API_KEY = env('TABIYA_API_KEY', default='')  # Solo necesario si NLP_USE_TABIYA=True
TABIYA_API_URL = env('TABIYA_API_URL', default='https://api.tabiya.ai')
TABIYA_TIMEOUT = env.int('TABIYA_TIMEOUT', default=30)  # Timeout en segundos
TABIYA_RETRY_ATTEMPTS = env.int('TABIYA_RETRY_ATTEMPTS', default=3)
TABIYA_CACHE_TTL = env.int('TABIYA_CACHE_TTL', default=3600)  # TTL del cache en segundos

# Configuración específica por unidad de negocio
# Solo se usa si NLP_USE_TABIYA=True
TABIYA_CONFIG = {
    'amigro': {
        'model_version': 'v1.0',
        'skills_threshold': 0.7,
        'experience_threshold': 0.6,
        'culture_threshold': 0.8
    },
    'huntu': {
        'model_version': 'v1.1',
        'skills_threshold': 0.75,
        'experience_threshold': 0.65,
        'culture_threshold': 0.85
    },
    'huntred': {
        'model_version': 'v2.0',
        'skills_threshold': 0.8,
        'experience_threshold': 0.7,
        'culture_threshold': 0.9
    },
    'huntred_executive': {
        'model_version': 'v2.1',
        'skills_threshold': 0.85,
        'experience_threshold': 0.75,
        'culture_threshold': 0.95
    },
    'sexsi': {
        'model_version': 'v1.5',
        'skills_threshold': 0.7,
        'experience_threshold': 0.6,
        'culture_threshold': 0.8
    },
    'milkyleak': {
        'model_version': 'v1.2',
        'skills_threshold': 0.7,
        'experience_threshold': 0.6,
        'culture_threshold': 0.8
    }
}

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


# --- Funciones para obtener configuración de la base de datos
# Funciones de configuración de API

def get_api_config(api_type, business_unit):
    """
    Obtiene la configuración de API para una unidad de negocio
    """
    try:
        if api_type == 'whatsapp':
            from app.models import WhatsAppAPI as APIModel
        elif api_type == 'telegram':
            from app.models import TelegramAPI as APIModel
        else:
            raise ValueError(f"API type {api_type} not supported")
            
        return APIModel.objects.get(
            business_unit=business_unit,
            is_active=True
        )
    except Exception as e:
        logger.error(f"Error getting {api_type} API config: {str(e)}")
        return None

# Configuración de publicación
PUBLISH_DEFAULT_CHANNEL = env('PUBLISH_DEFAULT_CHANNEL', default='TELEGRAM_CHANNEL')
PUBLISH_AUTO_PUBLISH = env.bool('PUBLISH_AUTO_PUBLISH', default=True)

# Configuración dinámica por unidad de negocio
def get_channel_config(business_unit, channel_type):
    """
    Obtiene la configuración de un canal específico para una unidad de negocio
    """
    if channel_type == 'WHATSAPP':
        return get_whatsapp_api_config(business_unit)
    elif channel_type == 'TELEGRAM':
        return get_telegram_api_config(business_unit)
    return None

# Configuración de Pagos ---
def get_paypal_config(business_unit):
    """
    Obtiene la configuración de PayPal para una unidad de negocio
    """
    from app.models import ApiConfig
    try:
        return ApiConfig.objects.get(
            business_unit=business_unit,
            api_type='paypal',
            enabled=True
        )
    except ApiConfig.DoesNotExist:
        return None

# Configuración dinámica por unidad de negocio
def get_channel_config(business_unit, channel_type):
    """
    Obtiene la configuración de un canal específico para una unidad de negocio
    """
    if channel_type == 'WHATSAPP':
        return get_whatsapp_api_config(business_unit)
PAYPAL_CONFIG = {
    'mode': env('PAYPAL_MODE', default='sandbox'),
    'client_id': env('PAYPAL_CLIENT_ID', default=None),
    'client_secret': env('PAYPAL_CLIENT_SECRET', default=None),
    'return_url': env('PAYPAL_RETURN_URL', default=None),
    'cancel_url': env('PAYPAL_CANCEL_URL', default=None)
}

# Verifica si PayPal está configurado
PAYPAL_ENABLED = all(
    value is not None 
    for value in [PAYPAL_CONFIG['client_id'], PAYPAL_CONFIG['client_secret']]
)

# Configuración de WordPress (opcional)
WORDPRESS_CONFIG = {
    'api_url': env('WORDPRESS_API_URL', default=None),
    'username': env('WORDPRESS_USERNAME', default=None),
    'password': env('WORDPRESS_PASSWORD', default=None)
}

# Verifica si WordPress está configurado
WORDPRESS_ENABLED = all(
    value is not None 
    for value in [WORDPRESS_CONFIG['api_url'], WORDPRESS_CONFIG['username'], WORDPRESS_CONFIG['password']]
)

# --- Configuración de entorno ---

# Configuración de localización para Ciudad de México
TIME_ZONE = 'America/Mexico_City'
LANGUAGE_CODE = 'es-mx'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Validar existencia del archivo .env (sin usar logger aún)
if not os.path.exists(env_file):
    raise FileNotFoundError(f"Environment file not found: {env_file}")

# Configuración de Celery
CELERY_BROKER_URL = env('CELERY_BROKER_URL', default='redis://127.0.0.1:6379/0')
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND', default='redis://127.0.0.1:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'America/Mexico_City'
CELERY_ENABLE_UTC = False
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_TASK_ACKS_LATE = True
CELERY_TASK_REJECT_ON_WORKER_LOST = True
CELERY_TASK_TRACK_STARTED = True
CELERY_WORKER_CONCURRENCY = env.int('CELERY_WORKER_CONCURRENCY', default=2)
if not os.access(env_file, os.R_OK):
    raise PermissionError(f"Environment file not readable: {env_file}")

# Cargar variables de entorno
environ.Env.read_env(env_file)

# Configuración de formato de fecha y hora para México
DATE_FORMAT = 'd/m/Y'
DATETIME_FORMAT = 'd/m/Y H:i'
SHORT_DATE_FORMAT = 'd/m/Y'
SHORT_DATETIME_FORMAT = 'd/m/Y H:i'
TIME_FORMAT = 'H:i'

# --- Seguridad y entorno ---
# Asegurar que no se use la clave por defecto en producción
SECRET_KEY = env('DJANGO_SECRET_KEY')
DEBUG = env.bool('DJANGO_DEBUG', default=False)

# Configurar hosts permitidos para Ciudad de México
ALLOWED_HOSTS = env.list('DJANGO_ALLOWED_HOSTS', default=['ai.huntred.com', '127.0.0.1', 'localhost'])

# Configuración de CORS para Ciudad de México
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=['http://localhost:3000', 'http://127.0.0.1:3000'])
CORS_ALLOW_CREDENTIALS = True

# Configuración de seguridad adicional
SECURE_BROWSER_XSS_FILTER = True
SESSION_COOKIE_SECURE = env.bool('SESSION_COOKIE_SECURE', default=not DEBUG)
CSRF_COOKIE_SECURE = env.bool('CSRF_COOKIE_SECURE', default=not DEBUG)
SECURE_SSL_REDIRECT = env.bool('SECURE_SSL_REDIRECT', default=not DEBUG)
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Configuración de correo para Ciudad de México
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='noreply@huntred.com')
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env('EMAIL_HOST')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_USE_TLS = True
EMAIL_HOST_USER = env('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')

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
        'TEST': {
            'NAME': 'test_g_huntred_ai_db',
        },
    }
}

# Silenciar advertencia de Django 6.0
FORMS_URLFIELD_ASSUME_HTTPS = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

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
    'silk',
    'django_extensions',
    'app',  # Incluye todos los módulos de app
    'app.sexsi', # Recordemos que este tiene unos contratos separados.
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
    'app.middleware.PermissionMiddleware',
    'app.middleware.RoleMiddleware',
    'app.middleware.BusinessUnitMiddleware',
    'app.middleware.DivisionMiddleware',
    'silk.middleware.SilkyMiddleware',
    'ai_huntred.error_handling.ErrorHandlerMiddleware',
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

# Configuración de autenticación
AUTH_USER_MODEL = 'app.CustomUser'
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

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
CARTAS_OFERTA_DIR = os.path.join(BASE_DIR, 'media', 'cartas_oferta')

# Configuración de PDFKit
WKHTMLTOPDF_PATH = env('WKHTMLTOPDF_PATH', default='/usr/local/bin/wkhtmltopdf')

# Configuración de cartas de oferta
CARTA_OFERTA_TEMPLATES = {
    'default': 'carta_oferta_template.html',
    'amigro': 'carta_oferta_amigro.html',
    'huntu': 'carta_oferta_huntu.html',
    'huntred': 'carta_oferta_huntred.html',
    'huntred_executive': 'carta_oferta_huntred_executive.html'
}
LOG_DIR = os.path.join(BASE_DIR, 'logs')
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Create directories (permissions set manually)
for directory in [LOG_DIR, STATIC_ROOT, MEDIA_ROOT, ML_MODELS_DIR]:
    os.makedirs(directory, exist_ok=True)

# Configuración de logging
LOGGING = setup_logging()

# Initialize module registry for lazy loading
try:
    from app.module_registry import auto_register_modules
    auto_register_modules()
    logging.info("Module registry initialized successfully")
except Exception as e:
    logging.error(f"Failed to initialize module registry: {e}")

# Celery Configuration Options
CELERY_BROKER_URL = 'redis://localhost:6379/0'  # Use Redis as the broker
CELERY_RESULT_BACKEND = 'redis://localhost:6379/1'  # Store task results
CELERY_ACCEPT_CONTENT = ['json']  # Allow JSON content
CELERY_TASK_SERIALIZER = 'json'  # Use JSON serializer for tasks
CELERY_RESULT_SERIALIZER = 'json'  # Use JSON serializer for results
CELERY_TIMEZONE = TIME_ZONE  # Set Celery timezone to match Django
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 3600  # Set a time limit for tasks (in seconds)
CELERY_TASK_SOFT_TIME_LIMIT = 3300  # Soft time limit for tasks
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# Import Celery app
# Using celery_config.py to avoid circular import
try:
    from celery_config import app as celery_app
except ImportError:
    # Fallback in case the file is in a different location
    try:
        from ai_huntred.celery_config import app as celery_app
    except ImportError:
        pass

# Configuración de emails
FINANCE_EMAIL = 'finanzas@huntred.com'  # Email para notificaciones de finanzas
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='noreply@huntred.com')

__all__ = ('celery_app',)

# Configuración de optimización
optimization_config = OptimizationConfig.get_config()
CACHES = {
    'default': optimization_config['CACHE_CONFIG']
}

# Configuración de seguridad
security_config = SecurityConfig.get_config()
SIMPLE_JWT = security_config['JWT_CONFIG']
RATELIMIT_RATE = security_config['RATE_LIMITING']['DEFAULT_RATE']
RATELIMIT_LOGIN_RATE = security_config['RATE_LIMITING']['LOGIN_RATE']
RATELIMIT_API_RATE = security_config['RATE_LIMITING']['API_RATE']

# Configuración de chatbot
from app.com.chatbot.optimization_config import OptimizationConfig

CHATBOT_CONFIG = {
    'ENABLED': env.bool('CHATBOT_ENABLED', default=True),
    'MAX_CONCURRENT_SESSIONS': env.int('CHATBOT_MAX_SESSIONS', default=100),
    'MESSAGE_TIMEOUT': env.int('CHATBOT_MESSAGE_TIMEOUT', default=30),  # segundos
    'MAX_MESSAGE_RETRIES': env.int('CHATBOT_MAX_RETRIES', default=3),
    'METRICS_COLLECTION_INTERVAL': env.int('CHATBOT_METRICS_INTERVAL', default=60),  # segundos
    'FALLBACK_CHANNEL': env('CHATBOT_FALLBACK_CHANNEL', default='email'),
    'CHANNEL_CONFIG': ChannelConfig.get_config(),
    'OPTIMIZATION': OptimizationConfig.get_config()
}

# Configuración de monitoreo
monitoring_config = MonitoringConfig.get_config()
ENABLE_METRICS = monitoring_config['METRICS_CONFIG']['ENABLED']
METRICS_ENDPOINT = monitoring_config['METRICS_CONFIG']['METRICS_ENDPOINT']

# Configuración de alertas
ALERT_EMAILS = monitoring_config['ALERT_CONFIG']['ALERT_EMAILS']
CRITICAL_THRESHOLD = monitoring_config['ALERT_CONFIG']['CRITICAL_THRESHOLD']
WARNING_THRESHOLD = monitoring_config['ALERT_CONFIG']['WARNING_THRESHOLD']

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
