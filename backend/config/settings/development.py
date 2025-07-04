"""
🚀 GhuntRED-v2 Development Settings
Optimized for development with debugging and performance monitoring
"""

from .base import *

# =============================================================================
# DEBUG CONFIGURATION
# =============================================================================

DEBUG = True
TEMPLATE_DEBUG = DEBUG

# Additional debug settings
DEBUG_TOOLBAR_ENABLED = env.bool('DEBUG_TOOLBAR_ENABLED', default=True)

if DEBUG_TOOLBAR_ENABLED:
    INSTALLED_APPS += [
        'debug_toolbar',
        'django_querycount',
    ]
    
    MIDDLEWARE = [
        'debug_toolbar.middleware.DebugToolbarMiddleware',
    ] + MIDDLEWARE
    
    DEBUG_TOOLBAR_CONFIG = {
        'SHOW_TEMPLATE_CONTEXT': True,
        'SHOW_TOOLBAR_CALLBACK': lambda request: True,
    }

# =============================================================================
# SILK PROFILER CONFIGURATION
# =============================================================================

SILK_ENABLED = env.bool('SILK_ENABLED', default=True)

if SILK_ENABLED:
    SILKY_PYTHON_PROFILER = True
    SILKY_PYTHON_PROFILER_BINARY = True
    SILKY_ANALYZE_QUERIES = True
    SILKY_META = True
    SILKY_INTERCEPT_PERCENT = 50
    SILKY_MAX_REQUEST_BODY_SIZE = 1024 * 1024  # 1MB
    SILKY_MAX_RESPONSE_BODY_SIZE = 1024 * 1024  # 1MB

# =============================================================================
# CORS CONFIGURATION (Permissive for development)
# =============================================================================

CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

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
    'x-debug',
]

# =============================================================================
# EMAIL CONFIGURATION (Console backend for development)
# =============================================================================

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

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
        'json': {
            'format': '{"level": "%(levelname)s", "time": "%(asctime)s", "module": "%(module)s", "message": "%(message)s"}',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'ghuntred_v2.log',
            'maxBytes': 1024*1024*100,  # 100MB
            'backupCount': 5,
            'formatter': 'json',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': env('LOG_LEVEL', default='INFO'),
            'propagate': True,
        },
        'backend': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'backend.ml': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'backend.tasks': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'celery': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}

# Create logs directory if it doesn't exist
import os
logs_dir = BASE_DIR / 'logs'
os.makedirs(logs_dir, exist_ok=True)

# =============================================================================
# SECURITY (Relaxed for development)
# =============================================================================

SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# =============================================================================
# PERFORMANCE MONITORING
# =============================================================================

# Query debugging
QUERY_DEBUG = env.bool('QUERY_DEBUG', default=True)
SQL_DEBUG = env.bool('SQL_DEBUG', default=False)

if QUERY_DEBUG:
    INSTALLED_APPS += ['django_querycount']
    MIDDLEWARE += ['django_querycount.middleware.QueryCountMiddleware']

# =============================================================================
# DEVELOPMENT TOOLS
# =============================================================================

# Django Extensions
DJANGO_EXTENSIONS_ENABLED = env.bool('DJANGO_EXTENSIONS_ENABLED', default=True)

if DJANGO_EXTENSIONS_ENABLED:
    SHELL_PLUS_PRINT_SQL = True
    SHELL_PLUS_PRINT_SQL_TRUNCATE = 1000
    SHELL_PLUS_PRE_IMPORTS = [
        ('backend.apps.core.utils', '*'),
        ('backend.ml.core.factory', 'MLFactory'),
        ('backend.ml.genia.analyzer', 'GenIAAnalyzer'),
        ('backend.ml.aura.engine', 'AURAEngine'),
    ]

# =============================================================================
# CACHE SETTINGS (Optimized for development)
# =============================================================================

# Shorter cache timeouts for development
CACHES['default']['TIMEOUT'] = 300  # 5 minutes
CACHE_TTL = 300

# =============================================================================
# ML AND AI DEVELOPMENT SETTINGS
# =============================================================================

# Enable verbose ML logging
ML_DEBUG = True
ML_CACHE_ENABLED = False  # Disable cache for development testing

# AURA Development Settings
AURA_DEBUG = True
AURA_CACHE_PREDICTIONS = False
AURA_SIMILARITY_THRESHOLD = 0.75  # Lower threshold for testing

# GenIA Development Settings
GENIA_DEBUG = True
GENIA_CACHE_ANALYSIS = False
GENIA_VERBOSE_LOGGING = True

# =============================================================================
# API DEVELOPMENT SETTINGS
# =============================================================================

# More permissive API settings for development
REST_FRAMEWORK.update({
    'DEFAULT_THROTTLE_RATES': {
        'anon': '10000/hour',
        'user': '10000/hour',
    },
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
})

# Enable API documentation in development
SPECTACULAR_SETTINGS.update({
    'SERVE_INCLUDE_SCHEMA': True,
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,
        'displayOperationId': True,
        'defaultModelsExpandDepth': 2,
        'defaultModelExpandDepth': 2,
        'displayRequestDuration': True,
    },
})

# =============================================================================
# CELERY DEVELOPMENT SETTINGS
# =============================================================================

# More aggressive task monitoring in development
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_SEND_SENT_EVENT = True
CELERY_SEND_EVENTS = True
CELERY_SEND_TASK_EVENTS = True

# Lower concurrency for development
CELERY_WORKER_CONCURRENCY = 2

# =============================================================================
# DATABASE DEVELOPMENT SETTINGS
# =============================================================================

# Enable query logging
DATABASES['default']['OPTIONS'].update({
    'options': '-c log_statement=all -c log_min_duration_statement=0'
})

# =============================================================================
# FILE STORAGE (Local for development)
# =============================================================================

# Use local file storage instead of S3 for development
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

# =============================================================================
# FEATURE FLAGS (All enabled for development)
# =============================================================================

FEATURE_FLAGS.update({
    'NEW_DASHBOARD': True,
    'ADVANCED_ML': True,
    'REAL_TIME_CHAT': True,
    'ENHANCED_AURA': True,
    'GENIA_V2': True,
    'MULTI_TENANT': True,
    'DEBUG_FEATURES': True,
    'ML_EXPERIMENTS': True,
    'PERFORMANCE_TESTING': True,
})

# =============================================================================
# DEVELOPMENT UTILITIES
# =============================================================================

# Allow all hosts in development
ALLOWED_HOSTS = ['*']

# Disable template caching
for template in TEMPLATES:
    template['OPTIONS']['debug'] = True

# =============================================================================
# TESTING CONFIGURATION
# =============================================================================

# Test database settings
if 'test' in sys.argv:
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
    
    # Disable migrations for faster testing
    class DisableMigrations:
        def __contains__(self, item):
            return True
        
        def __getitem__(self, item):
            return None
    
    MIGRATION_MODULES = DisableMigrations()
    
    # Use dummy cache for testing
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        }
    }
    
    # Disable Celery for testing
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_EAGER_PROPAGATES = True

# =============================================================================
# JUPYTER NOTEBOOK CONFIGURATION
# =============================================================================

# Jupyter configuration for development
NOTEBOOK_ARGUMENTS = [
    '--ip=0.0.0.0',
    '--port=8888',
    '--allow-root',
    '--no-browser',
]

# =============================================================================
# HOT RELOAD CONFIGURATION
# =============================================================================

# Enable hot reloading for development
USE_TZ = True
USE_I18N = True

# Live reload for templates and static files
if DEBUG:
    INSTALLED_APPS += ['livereload']
    MIDDLEWARE += ['livereload.middleware.LiveReloadScript']

print("🚀 GhuntRED-v2 Development Environment Loaded!")
print(f"🔧 Debug Mode: {DEBUG}")
print(f"🧠 ML Debug: {ML_DEBUG}")
print(f"⚡ AURA Enhanced: {FEATURE_FLAGS['ENHANCED_AURA']}")
print(f"🤖 GenIA v2: {FEATURE_FLAGS['GENIA_V2']}")
print(f"📊 Advanced ML: {FEATURE_FLAGS['ADVANCED_ML']}")
print(f"🎯 All integrations enabled and ready for development!")