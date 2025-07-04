"""
🚀 GhuntRED-v2 Base Settings
Django 5.0 with latest optimizations and security features
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Any

import environ
from django.utils.translation import gettext_lazy as _

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ROOT_DIR = BASE_DIR.parent

# Environment variables
env = environ.Env(
    DEBUG=(bool, False),
    USE_TZ=(bool, True),
    LANGUAGE_CODE=(str, 'es-mx'),
    TIME_ZONE=(str, 'America/Mexico_City'),
)

# Read environment file
environ.Env.read_env(os.path.join(ROOT_DIR, '.env'))

# =============================================================================
# CORE DJANGO SETTINGS
# =============================================================================

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG')

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[])

# Application definition
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions', 
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.humanize',
    'django.contrib.sitemaps',
]

THIRD_PARTY_APPS = [
    # API Framework
    'rest_framework',
    'rest_framework.authtoken',
    'rest_framework_simplejwt',
    'drf_spectacular',
    'knox',
    'ninja',
    
    # Async Support
    'channels',
    
    # Task Queue
    'django_celery_beat',
    'django_celery_results',
    
    # CORS and Security
    'corsheaders',
    'guardian',
    'django_otp',
    'django_otp.plugins.otp_totp',
    'django_otp.plugins.otp_static',
    
    # Caching and Performance
    'cachalot',
    'compressor',
    
    # Extensions and Utilities
    'django_extensions',
    'crispy_forms',
    'crispy_bootstrap5',
    'django_filters',
    
    # Storage
    'storages',
    
    # Email
    'anymail',
    'mjml',
    
    # Monitoring
    'silk',
    'django_prometheus',
]

LOCAL_APPS = [
    # Core Apps
    'backend.apps.core',
    'backend.apps.business_units',
    'backend.apps.candidates',
    'backend.apps.companies',
    'backend.apps.workflows',
    'backend.apps.notifications',
    
    # ML Apps
    'backend.ml.core',
    'backend.ml.genia',
    'backend.ml.aura',
    
    # Task Apps
    'backend.tasks.core',
    'backend.tasks.notifications',
    'backend.tasks.ml',
    'backend.tasks.scraping',
    'backend.tasks.maintenance',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    # Security Middleware
    'django.middleware.security.SecurityMiddleware',
    
    # Performance Middleware
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
    
    # Session and User Middleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    
    # CORS Middleware
    'corsheaders.middleware.CorsMiddleware',
    
    # Common Middleware
    'django.middleware.common.CommonMiddleware',
    
    # CSRF Middleware
    'django.middleware.csrf.CsrfViewMiddleware',
    
    # Authentication Middleware
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django_otp.middleware.OTPMiddleware',
    
    # Messages Middleware
    'django.contrib.messages.middleware.MessageMiddleware',
    
    # Security Middleware
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
    # Custom Middleware
    'backend.apps.core.middleware.BusinessUnitMiddleware',
    'backend.apps.core.middleware.TimezoneMiddleware',
    'backend.apps.core.middleware.APIVersionMiddleware',
    
    # Performance Monitoring
    'django_prometheus.middleware.PrometheusAfterMiddleware',
]

ROOT_URLCONF = 'backend.config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates',
            ROOT_DIR / 'frontend' / 'packages' / 'email-templates' / 'templates',
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'backend.apps.core.context_processors.business_unit',
                'backend.apps.core.context_processors.feature_flags',
            ],
        },
    },
]

WSGI_APPLICATION = 'backend.config.wsgi.application'
ASGI_APPLICATION = 'backend.config.asgi.application'

# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME'),
        'USER': env('DB_USER'), 
        'PASSWORD': env('DB_PASSWORD'),
        'HOST': env('DB_HOST'),
        'PORT': env('DB_PORT'),
        'CONN_MAX_AGE': env.int('DB_CONN_MAX_AGE', default=600),
        'CONN_HEALTH_CHECKS': env.bool('DB_CONN_HEALTH_CHECKS', default=True),
        'OPTIONS': {
            'sslmode': 'prefer',
        },
        'TEST': {
            'NAME': 'test_ghuntred_v2',
        },
    }
}

# Database routing for read replicas (if needed)
DATABASE_ROUTERS = ['backend.apps.core.routers.DatabaseRouter']

# =============================================================================
# CACHING CONFIGURATION
# =============================================================================

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': env('REDIS_URL'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'PARSER_CLASS': 'redis.connection.HiredisParser',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            },
        },
        'KEY_PREFIX': env('CACHE_KEY_PREFIX', default='ghuntred_v2'),
        'VERSION': env.int('CACHE_VERSION', default=1),
        'TIMEOUT': env.int('CACHE_TTL', default=3600),
    },
    'sessions': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f"{env('REDIS_URL')}/3",
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'sessions',
        'TIMEOUT': 86400,  # 24 hours
    },
}

# Session configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'sessions'
SESSION_COOKIE_AGE = env.int('SESSION_COOKIE_AGE', default=86400)
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = env.bool('SESSION_COOKIE_SECURE', default=False)
SESSION_COOKIE_SAMESITE = 'Lax'

# =============================================================================
# INTERNATIONALIZATION
# =============================================================================

LANGUAGE_CODE = env('LANGUAGE_CODE')
TIME_ZONE = env('TIME_ZONE')
USE_I18N = True
USE_TZ = True

LANGUAGES = [
    ('es', _('Spanish')),
    ('en', _('English')),
]

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

# =============================================================================
# STATIC AND MEDIA FILES
# =============================================================================

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
    ROOT_DIR / 'frontend' / 'dist',
]

STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
]

STATICFILES_STORAGE = env(
    'STATICFILES_STORAGE',
    default='whitenoise.storage.CompressedManifestStaticFilesStorage'
)

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# =============================================================================
# SECURITY SETTINGS
# =============================================================================

# HTTPS and Security Headers
SECURE_SSL_REDIRECT = env.bool('SECURE_SSL_REDIRECT', default=False)
SECURE_HSTS_SECONDS = env.int('SECURE_HSTS_SECONDS', default=31536000)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

# CSRF Protection
CSRF_COOKIE_SECURE = env.bool('CSRF_COOKIE_SECURE', default=False)
CSRF_COOKIE_HTTPONLY = True
CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=[])

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 12,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Password hashing
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
]

# =============================================================================
# REST FRAMEWORK CONFIGURATION
# =============================================================================

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'knox.auth.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'backend.apps.core.pagination.StandardResultsSetPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': env('API_RATE_LIMIT', default='1000/hour'),
        'user': env('API_BURST_LIMIT', default='100/minute'),
    }
}

# =============================================================================
# JWT CONFIGURATION
# =============================================================================

from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(seconds=env.int('JWT_ACCESS_TOKEN_LIFETIME', default=3600)),
    'REFRESH_TOKEN_LIFETIME': timedelta(seconds=env.int('JWT_REFRESH_TOKEN_LIFETIME', default=86400)),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': env('JWT_ALGORITHM', default='HS256'),
    'SIGNING_KEY': env('JWT_SECRET_KEY', default=SECRET_KEY),
    'VERIFYING_KEY': None,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
}

# =============================================================================
# CORS CONFIGURATION
# =============================================================================

CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[])
CORS_ALLOW_CREDENTIALS = env.bool('CORS_ALLOW_CREDENTIALS', default=True)
CORS_ALLOWED_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'x-business-unit',
    'x-api-version',
]

# =============================================================================
# CELERY CONFIGURATION
# =============================================================================

CELERY_BROKER_URL = env('CELERY_BROKER_URL')
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_ENABLE_UTC = True
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = env.int('CELERY_TASK_TIME_LIMIT', default=3600)
CELERY_WORKER_PREFETCH_MULTIPLIER = env.int('CELERY_WORKER_PREFETCH_MULTIPLIER', default=1)

# Celery Beat Schedule
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# =============================================================================
# CHANNELS CONFIGURATION (WebSockets)
# =============================================================================

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [env('CHANNELS_REDIS_URL', default='redis://redis:6379/4')],
            'capacity': 1500,
            'expiry': 10,
        },
    },
}

# =============================================================================
# ML AND AI CONFIGURATION
# =============================================================================

# OpenAI Configuration
OPENAI_API_KEY = env('OPENAI_API_KEY', default='')
OPENAI_MODEL = env('OPENAI_MODEL', default='gpt-4-turbo-preview')
OPENAI_MAX_TOKENS = env.int('OPENAI_MAX_TOKENS', default=4096)
OPENAI_TEMPERATURE = env.float('OPENAI_TEMPERATURE', default=0.7)

# Anthropic Configuration
ANTHROPIC_API_KEY = env('ANTHROPIC_API_KEY', default='')
ANTHROPIC_MODEL = env('ANTHROPIC_MODEL', default='claude-3-sonnet-20240229')

# Google Gemini Configuration
GOOGLE_API_KEY = env('GOOGLE_API_KEY', default='')
GEMINI_MODEL = env('GEMINI_MODEL', default='gemini-pro')

# TensorFlow Serving
TF_SERVING_URL = env('TF_SERVING_URL', default='http://ml-server:8501')
TF_SERVING_GRPC_URL = env('TF_SERVING_GRPC_URL', default='ml-server:8500')

# ML Model Storage
ML_MODELS_BUCKET = env('ML_MODELS_BUCKET', default='ml-models')
ML_MODELS_PREFIX = env('ML_MODELS_PREFIX', default='ghuntred-v2/models/')

# AURA Configuration
AURA_ENABLED = env.bool('AURA_ENABLED', default=True)
AURA_HOLISTIC_MODEL = env('AURA_HOLISTIC_MODEL', default='aura_holistic_v2')
AURA_VIBRATIONAL_MODEL = env('AURA_VIBRATIONAL_MODEL', default='aura_vibrational_v2')
AURA_COMPATIBILITY_MODEL = env('AURA_COMPATIBILITY_MODEL', default='aura_compatibility_v2')
AURA_MAX_CANDIDATES = env.int('AURA_MAX_CANDIDATES', default=100)
AURA_SIMILARITY_THRESHOLD = env.float('AURA_SIMILARITY_THRESHOLD', default=0.85)

# GenIA Configuration
GENIA_ENABLED = env.bool('GENIA_ENABLED', default=True)
GENIA_SENTIMENT_MODEL = env('GENIA_SENTIMENT_MODEL', default='genia_sentiment_v2')
GENIA_PERSONALITY_MODEL = env('GENIA_PERSONALITY_MODEL', default='genia_personality_v2')
GENIA_SKILLS_MODEL = env('GENIA_SKILLS_MODEL', default='genia_skills_v2')
GENIA_MATCHING_MODEL = env('GENIA_MATCHING_MODEL', default='genia_matching_v2')

# =============================================================================
# INTEGRATION SETTINGS
# =============================================================================

# WhatsApp Integration
WHATSAPP_ENABLED = env.bool('WHATSAPP_ENABLED', default=True)
WHATSAPP_API_URL = env('WHATSAPP_API_URL', default='https://graph.facebook.com/v18.0')
WHATSAPP_ACCESS_TOKEN = env('WHATSAPP_ACCESS_TOKEN', default='')
WHATSAPP_PHONE_NUMBER_ID = env('WHATSAPP_PHONE_NUMBER_ID', default='')
WHATSAPP_BUSINESS_ACCOUNT_ID = env('WHATSAPP_BUSINESS_ACCOUNT_ID', default='')
WHATSAPP_WEBHOOK_VERIFY_TOKEN = env('WHATSAPP_WEBHOOK_VERIFY_TOKEN', default='')
WHATSAPP_APP_SECRET = env('WHATSAPP_APP_SECRET', default='')

# Telegram Integration
TELEGRAM_ENABLED = env.bool('TELEGRAM_ENABLED', default=True)
TELEGRAM_BOT_TOKEN = env('TELEGRAM_BOT_TOKEN', default='')
TELEGRAM_API_URL = env('TELEGRAM_API_URL', default='https://api.telegram.org/bot')
TELEGRAM_WEBHOOK_URL = env('TELEGRAM_WEBHOOK_URL', default='')
TELEGRAM_WEBHOOK_SECRET_TOKEN = env('TELEGRAM_WEBHOOK_SECRET_TOKEN', default='')

# LinkedIn Integration
LINKEDIN_ENABLED = env.bool('LINKEDIN_ENABLED', default=True)
LINKEDIN_CLIENT_ID = env('LINKEDIN_CLIENT_ID', default='')
LINKEDIN_CLIENT_SECRET = env('LINKEDIN_CLIENT_SECRET', default='')
LINKEDIN_REDIRECT_URI = env('LINKEDIN_REDIRECT_URI', default='')
LINKEDIN_SCOPE = env('LINKEDIN_SCOPE', default='r_liteprofile,r_emailaddress,w_member_social')

# =============================================================================
# EMAIL CONFIGURATION
# =============================================================================

EMAIL_BACKEND = env('EMAIL_BACKEND', default='anymail.backends.sendgrid.EmailBackend')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='noreply@huntred.com')
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# Anymail configuration for SendGrid
ANYMAIL = {
    'SENDGRID_API_KEY': env('EMAIL_HOST_PASSWORD', default=''),
    'SENDGRID_GENERATE_MESSAGE_ID': True,
    'SENDGRID_MERGE_FIELD_FORMAT': '-{}-',
    'SENDGRID_API_URL': 'https://api.sendgrid.com/v3/',
}

# MJML for email templates
MJML_BACKEND_MODE = 'httpserver'
MJML_HTTPSERVER_URL = 'https://api.mjml.io/v1/render'

# =============================================================================
# ELASTICSEARCH CONFIGURATION
# =============================================================================

ELASTICSEARCH_DSL = {
    'default': {
        'hosts': env('ELASTICSEARCH_URL', default='http://elasticsearch:9200'),
        'timeout': env.int('ELASTICSEARCH_TIMEOUT', default=30),
        'max_retries': env.int('ELASTICSEARCH_MAX_RETRIES', default=3),
    },
}

# =============================================================================
# FILE STORAGE CONFIGURATION
# =============================================================================

# MinIO/S3 Configuration
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
AWS_ACCESS_KEY_ID = env('MINIO_ACCESS_KEY', default='')
AWS_SECRET_ACCESS_KEY = env('MINIO_SECRET_KEY', default='')
AWS_STORAGE_BUCKET_NAME = env('MINIO_BUCKET_NAME', default='ghuntred-v2')
AWS_S3_ENDPOINT_URL = f"http://{env('MINIO_ENDPOINT', default='minio:9000')}"
AWS_S3_USE_SSL = env.bool('MINIO_USE_SSL', default=False)
AWS_DEFAULT_ACL = None
AWS_S3_FILE_OVERWRITE = False
AWS_S3_REGION_NAME = env('AWS_S3_REGION_NAME', default='us-east-1')

# =============================================================================
# MONITORING AND LOGGING
# =============================================================================

# Sentry Error Tracking
SENTRY_DSN = env('SENTRY_DSN', default='')
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.celery import CeleryIntegration
    from sentry_sdk.integrations.redis import RedisIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            DjangoIntegration(auto_enabling=True),
            CeleryIntegration(monitor_beat_tasks=True),
            RedisIntegration(),
        ],
        traces_sample_rate=env.float('SENTRY_TRACES_SAMPLE_RATE', default=0.1),
        send_default_pii=True,
        environment=env('SENTRY_ENVIRONMENT', default='development'),
    )

# Prometheus Metrics
PROMETHEUS_METRICS_EXPORT_PORT = 8001
PROMETHEUS_METRICS_EXPORT_ADDRESS = ''

# =============================================================================
# FEATURE FLAGS
# =============================================================================

FEATURE_FLAGS = {
    'NEW_DASHBOARD': env.bool('FEATURE_NEW_DASHBOARD', default=True),
    'ADVANCED_ML': env.bool('FEATURE_ADVANCED_ML', default=True),
    'REAL_TIME_CHAT': env.bool('FEATURE_REAL_TIME_CHAT', default=True),
    'ENHANCED_AURA': env.bool('FEATURE_ENHANCED_AURA', default=True),
    'GENIA_V2': env.bool('FEATURE_GENIA_V2', default=True),
    'MULTI_TENANT': env.bool('FEATURE_MULTI_TENANT', default=True),
}

# =============================================================================
# BUSINESS UNITS CONFIGURATION
# =============================================================================

BUSINESS_UNITS = {
    'huntRED': {
        'enabled': env.bool('HUNTRED_ENABLED', default=True),
        'brand_color': env('HUNTRED_BRAND_COLOR', default='#ef4444'),
        'logo_url': env('HUNTRED_LOGO_URL', default=''),
        'domain': env('HUNTRED_DOMAIN', default='huntred.com'),
    },
    'amigro': {
        'enabled': env.bool('AMIGRO_ENABLED', default=True),
        'brand_color': env('AMIGRO_BRAND_COLOR', default='#10b981'),
        'logo_url': env('AMIGRO_LOGO_URL', default=''),
        'domain': env('AMIGRO_DOMAIN', default='amigro.com'),
    },
    'sexsi': {
        'enabled': env.bool('SEXSI_ENABLED', default=True),
        'brand_color': env('SEXSI_BRAND_COLOR', default='#8b5cf6'),
        'logo_url': env('SEXSI_LOGO_URL', default=''),
        'domain': env('SEXSI_DOMAIN', default='sexsi.com'),
    },
    'huntu': {
        'enabled': env.bool('HUNTU_ENABLED', default=True),
        'brand_color': env('HUNTU_BRAND_COLOR', default='#f59e0b'),
        'logo_url': env('HUNTU_LOGO_URL', default=''),
        'domain': env('HUNTU_DOMAIN', default='huntu.com'),
    },
    'huntred_executive': {
        'enabled': env.bool('HUNTRED_EXECUTIVE_ENABLED', default=True),
        'brand_color': env('HUNTRED_EXECUTIVE_BRAND_COLOR', default='#1e40af'),
        'logo_url': env('HUNTRED_EXECUTIVE_LOGO_URL', default=''),
        'domain': env('HUNTRED_EXECUTIVE_DOMAIN', default='executive.huntred.com'),
    },
}

# =============================================================================
# API CONFIGURATION
# =============================================================================

API_VERSION = env('API_VERSION', default='v2')
API_BASE_URL = env('API_BASE_URL', default='/api/v2/')

# API Documentation
SPECTACULAR_SETTINGS = {
    'TITLE': 'GhuntRED v2 API',
    'DESCRIPTION': 'Next Generation huntRED Platform API',
    'VERSION': '2.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,
        'displayOperationId': True,
    },
    'COMPONENT_SPLIT_REQUEST': True,
    'SORT_OPERATIONS': False,
}

# =============================================================================
# CRISPY FORMS CONFIGURATION
# =============================================================================

CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'
CRISPY_TEMPLATE_PACK = 'bootstrap5'

# =============================================================================
# DJANGO EXTENSIONS CONFIGURATION
# =============================================================================

GRAPH_MODELS = {
    'all_applications': True,
    'group_models': True,
}

# =============================================================================
# ADDITIONAL SETTINGS
# =============================================================================

# Site framework
SITE_ID = 1

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Internal IPs for debug toolbar
INTERNAL_IPS = env.list('INTERNAL_IPS', default=['127.0.0.1', 'localhost'])

# Append slash URL configuration
APPEND_SLASH = True

# Admins
ADMINS = [
    ('GhuntRED Admin', 'admin@huntred.com'),
]

MANAGERS = ADMINS