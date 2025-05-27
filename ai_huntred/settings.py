# /home/pablo/ai_huntred/settings.py

import os
import logging
import environ
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from pathlib import Path
import sys
from ai_huntred.config.security import SecurityConfig
from ai_huntred.config.logging import setup_logging
from ai_huntred.config.optimization import OptimizationConfig
from ai_huntred.config.monitoring import MonitoringConfig
import platform

# --- Configuración de entorno ---
env = environ.Env()
BASE_DIR = Path(__file__).resolve().parent.parent
env_file = os.path.join(BASE_DIR, '.env')

# Validar existencia del archivo .env
if not os.path.exists(env_file):
    raise FileNotFoundError(f"Environment file not found: {env_file}")
if not os.access(env_file, os.R_OK):
    raise PermissionError(f"Environment file not readable: {env_file}")

# Cargar variables de entorno
environ.Env.read_env(env_file)

# --- Configuración de NLP ---
NLP_USE_TABIYA = env.bool('NLP_USE_TABIYA', default=True)
NLP_FALLBACK_TO_SPACY = env.bool('NLP_FALLBACK_TO_SPACY', default=True)

# --- Configuración temprana de TensorFlow ---
if not any(arg in sys.argv for arg in ['migrate', 'makemigrations', 'collectstatic']):
    try:
        import tensorflow as tf
        os.environ["CUDA_VISIBLE_DEVICES"] = "-1"  # Desactiva GPU
        tf.config.threading.set_intra_op_parallelism_threads(1)
        tf.config.threading.set_inter_op_parallelism_threads(1)
        os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
        os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
    except ImportError:
        pass

# --- Configuración de Django ---
SECRET_KEY = 'django-insecure-development-key-change-in-production'
DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Aplicaciones instaladas
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'app',
    'rest_framework',
    'corsheaders',
    'django_celery_results',
    'django_celery_beat',
    'django_filters',  # Added for REST Framework filtering
]

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
    'app.middleware.database_adapter.DatabaseAdapterMiddleware',
    'app.middleware.PermissionMiddleware',
    'app.middleware.RoleMiddleware',
    'app.middleware.BusinessUnitMiddleware',
    'app.middleware.DivisionMiddleware',
    'silk.middleware.SilkyMiddleware',
    'ai_huntred.error_handling.ErrorHandlerMiddleware',
]

ROOT_URLCONF = 'ai_huntred.urls'

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

WSGI_APPLICATION = 'ai_huntred.wsgi.application'
ASGI_APPLICATION = 'ai_huntred.asgi.application'

# --- Database Configuration ---
IS_MAC = platform.system() == 'Darwin'
IS_LOCAL = env.bool('LOCAL_DEV', default=IS_MAC)
PRODUCTION = env.bool('PRODUCTION', default=False)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
FORCE_SQLITE = IS_LOCAL and not PRODUCTION
logging.info(f"Using {'SQLite' if FORCE_SQLITE else 'PostgreSQL'} for {'local' if IS_LOCAL else 'production'} environment")

# Debug print to confirm DATABASES
print("DEBUG: DATABASES configuration:", DATABASES)

# Configuración del modelo de usuario personalizado
AUTH_USER_MODEL = 'app.CustomUser'

# Validadores de contraseña
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

# Archivos estáticos y multimedia
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Campo de clave primaria por defecto
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

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
}

# Configuración CORS
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[]) if not CORS_ALLOW_ALL_ORIGINS else []

# --- Funciones para configuración ---
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
        return APIModel.objects.get(business_unit=business_unit, is_active=True)
    except Exception as e:
        logging.error(f"Error getting {api_type} API config: {str(e)}")
        return None

def get_paypal_config(business_unit):
    """
    Obtiene la configuración de PayPal para una unidad de negocio
    """
    from app.models import ApiConfig
    try:
        return ApiConfig.objects.get(business_unit=business_unit, api_type='paypal', enabled=True)
    except ApiConfig.DoesNotExist:
        return None

def get_channel_config(business_unit, channel_type):
    """
    Obtiene la configuración de un canal específico para una unidad de negocio
    """
    if channel_type == 'WHATSAPP':
        return get_whatsapp_api_config(business_unit)
    elif channel_type == 'TELEGRAM':
        return get_telegram_api_config(business_unit)
    return None

PAYPAL_CONFIG = {
    'mode': env('PAYPAL_MODE', default='sandbox'),
    'client_id': env('PAYPAL_CLIENT_ID', default=None),
    'client_secret': env('PAYPAL_CLIENT_SECRET', default=None),
    'return_url': env('PAYPAL_RETURN_URL', default=None),
    'cancel_url': env('PAYPAL_CANCEL_URL', default=None)
}

PAYPAL_ENABLED = all(value is not None for value in [PAYPAL_CONFIG['client_id'], PAYPAL_CONFIG['client_secret']])

WORDPRESS_CONFIG = {
    'api_url': env('WORDPRESS_API_URL', default=None),
    'username': env('WORDPRESS_USERNAME', default=None),
    'password': env('WORDPRESS_PASSWORD', default=None)
}

WORDPRESS_ENABLED = all(value is not None for value in [WORDPRESS_CONFIG['api_url'], WORDPRESS_CONFIG['username'], WORDPRESS_CONFIG['password']])

# --- Configuraciones avanzadas ---
STRIPE_CONFIG = {
    'api_key': env('STRIPE_API_KEY', default=''),
    'webhook_secret': env('STRIPE_WEBHOOK_SECRET', default=''),
    'currency': env('STRIPE_CURRENCY', default='mxn'),
    'success_url': env('STRIPE_SUCCESS_URL', default='/payments/success/'),
    'cancel_url': env('STRIPE_CANCEL_URL', default='/payments/cancel/')
}

STRIPE_ENABLED = all([STRIPE_CONFIG['api_key'], STRIPE_CONFIG['webhook_secret']])

X_CONFIG = {
    'api_key': env('X_API_KEY', default=''),
    'api_secret': env('X_API_SECRET', default=''),
    'access_token': env('X_ACCESS_TOKEN', default=''),
    'access_token_secret': env('X_ACCESS_TOKEN_SECRET', default='')
}

REDIS_CONFIG = {
    'host': env('REDIS_HOST', default='localhost'),
    'port': env.int('REDIS_PORT', default=6379),
    'db': env.int('REDIS_DB', default=0),
    'ttl': env.int('REDIS_TTL', default=3600)
}

QR_CONFIG = {
    'version': env.int('QR_VERSION', default=1),
    'error_correction': env('QR_ERROR_CORRECTION', default='L'),
    'box_size': env.int('QR_BOX_SIZE', default=10),
    'border': env.int('QR_BORDER', default=4),
    'upload_path': env('QR_UPLOAD_PATH', default='proposals/qr/')
}

ANALYTICS_CONFIG = {
    'time_window': env.int('ANALYTICS_TIME_WINDOW', default=30),
    'open_threshold': env.float('ANALYTICS_OPEN_THRESHOLD', default=0.7),
    'response_threshold': env.int('ANALYTICS_RESPONSE_THRESHOLD', default=24),
    'max_discount': env.float('ANALYTICS_MAX_DISCOUNT', default=0.10)
}

# Configuración de localización
TIME_ZONE = 'America/Santiago'
LANGUAGE_CODE = 'es'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Configuración de correo electrónico
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env('EMAIL_HOST', default='mail.huntred.com')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='hola@huntred.com')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='Natalia&Patricio1113!')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='Grupo huntRED® <hola@huntred.com>')

# Configuración de Celery
CELERY_BROKER_URL = env('CELERY_BROKER_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND', default='redis://localhost:6379/1')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_ENABLE_UTC = False
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_TASK_ACKS_LATE = True
CELERY_TASK_REJECT_ON_WORKER_LOST = True
CELERY_TASK_TRACK_STARTED = True
CELERY_WORKER_CONCURRENCY = env.int('CELERY_WORKER_CONCURRENCY', default=2)
CELERY_TASK_TIME_LIMIT = 3600
CELERY_TASK_SOFT_TIME_LIMIT = 3300
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# Configuración de formato de fecha y hora
DATE_FORMAT = 'd/m/Y'
DATETIME_FORMAT = 'd/m/Y H:i'
SHORT_DATE_FORMAT = 'd/m/Y'
SHORT_DATETIME_FORMAT = 'd/m/Y H:i'
TIME_FORMAT = 'H:i'

# Seguridad
SECURE_BROWSER_XSS_FILTER = True
SESSION_COOKIE_SECURE = env.bool('SESSION_COOKIE_SECURE', default=not DEBUG)
CSRF_COOKIE_SECURE = env.bool('CSRF_COOKIE_SECURE', default=not DEBUG)
SECURE_SSL_REDIRECT = env.bool('SECURE_SSL_REDIRECT', default=not DEBUG)
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
X_FRAME_OPTIONS = 'DENY'

# Configuración de autenticación
AUTHENTICATION_BACKENDS = ['django.contrib.auth.backends.ModelBackend']

# Directorios
ML_MODELS_DIR = os.path.join(BASE_DIR, 'app', 'models', 'ml_models')
CARTAS_OFERTA_DIR = os.path.join(BASE_DIR, 'media', 'cartas_oferta')
LOG_DIR = os.path.join(BASE_DIR, 'logs')

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

# Create directories
for directory in [LOG_DIR, STATIC_ROOT, MEDIA_ROOT, ML_MODELS_DIR]:
    os.makedirs(directory, exist_ok=True)

# Configuración de logging
LOGGING = setup_logging()

# Initialize module registry
try:
    from app.module_registry import auto_register_modules
    auto_register_modules()
    logging.info("Module registry initialized successfully")
except Exception as e:
    logging.error(f"Failed to initialize module registry: {e}")

# Import Celery app
try:
    from celery_config import app as celery_app
except ImportError:
    try:
        from ai_huntred.celery_config import app as celery_app
    except ImportError:
        pass

__all__ = ('celery_app',)

# Configuración de optimización
optimization_config = OptimizationConfig.get_config()
CACHES = {
    'default': optimization_config['CACHE_CONFIG'] if not (IS_LOCAL or DEBUG) else {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Configuración de seguridad
security_config = SecurityConfig.get_config()
SIMPLE_JWT = security_config['JWT_CONFIG']
RATELIMIT_RATE = security_config['RATE_LIMITING']['DEFAULT_RATE']
RATELIMIT_LOGIN_RATE = security_config['RATE_LIMITING']['LOGIN_RATE']
RATELIMIT_API_RATE = security_config['RATE_LIMITING']['API_RATE']

# Configuración de chatbot
CHATBOT_CONFIG = {
    'ENABLED': env.bool('CHATBOT_ENABLED', default=True),
    'MAX_CONCURRENT_SESSIONS': env.int('CHATBOT_MAX_SESSIONS', default=100),
    'MESSAGE_TIMEOUT': env.int('CHATBOT_MESSAGE_TIMEOUT', default=30),
    'MAX_MESSAGE_RETRIES': env.int('CHATBOT_MAX_RETRIES', default=3),
    'METRICS_COLLECTION_INTERVAL': env.int('CHATBOT_METRICS_INTERVAL', default=60),
    'FALLBACK_CHANNEL': env('CHATBOT_FALLBACK_CHANNEL', default='email'),
    'CHANNEL_CONFIG': {
        'whatsapp': {
            'enabled': env.bool('CHANNEL_WHATSAPP_ENABLED', default=True),
            'rate_limit': env.int('CHANNEL_WHATSAPP_RATE', default=20),
            'max_retries': env.int('CHANNEL_WHATSAPP_RETRIES', default=3)
        },
        'telegram': {
            'enabled': env.bool('CHANNEL_TELEGRAM_ENABLED', default=True),
            'rate_limit': env.int('CHANNEL_TELEGRAM_RATE', default=30),
            'max_retries': env.int('CHANNEL_TELEGRAM_RETRIES', default=3)
        },
        'email': {
            'enabled': env.bool('CHANNEL_EMAIL_ENABLED', default=True),
            'rate_limit': env.int('CHANNEL_EMAIL_RATE', default=50),
            'max_retries': env.int('CHANNEL_EMAIL_RETRIES', default=3)
        }
    },
    'OPTIMIZATION': {
        'INTENT_PROCESSING': {
            'MAX_CONCURRENT_INTENTS': env.int('CHATBOT_MAX_INTENTS', default=10),
            'CACHE_DURATION': env.int('CHATBOT_CACHE_DURATION', default=300),
            'PATTERN_OPTIMIZATION_ENABLED': env.bool('CHATBOT_PATTERN_OPTIMIZATION', default=True),
            'BATCH_SIZE': env.int('CHATBOT_BATCH_SIZE', default=1000)
        }
    }
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

# Configuración de producción
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'
    sentry_sdk.init(
        dsn=env('SENTRY_DSN', default=''),
        integrations=[DjangoIntegration()],
        traces_sample_rate=0.1,
        send_default_pii=True,
        environment=env('ENVIRONMENT', default='production')
    )

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

# Silenciar advertencia de Django 6.0
FORMS_URLFIELD_ASSUME_HTTPS = True

# Inicialización del sistema de importaciones
try:
    # Asegurar que el directorio raíz esté en el PYTHONPATH
    import sys
    from pathlib import Path
    
    app_root = str(Path(__file__).parent.parent.absolute())
    if app_root not in sys.path:
        sys.path.insert(0, app_root)
    
    # Importar e inicializar el sistema de importaciones
    from app.imports import imports
    imports.add_application_imports()
    
    print("Sistema de importaciones inicializado correctamente")
    
except Exception as e:
    print(f"Error al inicializar el sistema de importaciones: {e}")
    raise

# Configuración de aplicaciones instaladas
try:
    from app.module_registry import init_project
    if not any(arg in sys.argv for arg in ['migrate', 'makemigrations', 'collectstatic', 'test']):
        init_project()
        logging.info("Module registry initialized successfully")
except ImportError as e:
    logging.warning(f"Could not initialize module registry: {e}")
