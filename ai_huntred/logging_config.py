import os
from pathlib import Path
from django.conf import settings

# Directorio base para logs
LOGS_DIR = Path(__file__).resolve().parent.parent / 'logs'

# Asegurar que el directorio de logs existe
LOGS_DIR.mkdir(exist_ok=True)

# Configuración de logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} {message}',
            'style': '{',
        },
        'json': {
            'format': '{"time": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s", "module": "%(module)s", "process": "%(process)d", "thread": "%(thread)d"}',
            'style': '%',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'django.log',
            'maxBytes': 1024*1024*10,  # 10MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'error.log',
            'maxBytes': 1024*1024*10,
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'json_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'json.log',
            'maxBytes': 1024*1024*10,
            'backupCount': 10,
            'formatter': 'json',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file', 'error_file'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['error_file', 'json_file'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.server': {
            'handlers': ['error_file'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['error_file'],
            'level': 'ERROR',
            'propagate': False,
        },
        'app': {
            'handlers': ['console', 'file', 'error_file', 'json_file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# En producción, ajustar niveles de logging
if not settings.DEBUG:
    LOGGING['handlers']['console']['level'] = 'WARNING'
    LOGGING['handlers']['file']['level'] = 'WARNING'
    LOGGING['loggers']['django']['level'] = 'WARNING'
    LOGGING['loggers']['app']['level'] = 'WARNING'
