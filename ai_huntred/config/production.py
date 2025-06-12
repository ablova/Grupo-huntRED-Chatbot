# /home/pablo/ai_huntred/settings/production.py
from ai_huntred.settings import *
import os
import environ

env = environ.Env()

# Production-specific settings
DEBUG = False

# Allowed hosts for production
ALLOWED_HOSTS = env.list('DJANGO_ALLOWED_HOSTS', default=['huntred.com', 'www.huntred.com'])

# Secure settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Static and media files for production
STATIC_ROOT = BASE_DIR / 'static'
MEDIA_ROOT = BASE_DIR / 'media'

# Email backend for production
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_USE_TLS = True
EMAIL_HOST_USER = env('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default=EMAIL_HOST_USER)

# API Keys and Secrets
WHATSAPP_API_KEY = env('WHATSAPP_API_KEY')
TELEGRAM_BOT_TOKEN = env('TELEGRAM_BOT_TOKEN')
MESSENGER_APP_SECRET = env('MESSENGER_APP_SECRET')
INSTAGRAM_APP_SECRET = env('INSTAGRAM_APP_SECRET')

# Database configuration
DATABASES = {
    'default': env.db('DATABASE_URL')
}

# Cache configuration
CACHES = {
    'default': env.cache('REDIS_URL')
}

# Celery configuration
CELERY_BROKER_URL = env('CELERY_BROKER_URL')
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND')

# CDN configuration
CDN_ENABLED = env.bool('CDN_ENABLED', default=True)
CDN_DOMAIN = env('CDN_DOMAIN', default='cdn.huntred.com')

# Monitoring configuration
ENABLE_METRICS = True
ENABLE_PROMETHEUS = True
METRICS_ENDPOINT = '/metrics'

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}
