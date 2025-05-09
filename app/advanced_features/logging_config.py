import os
from pathlib import Path

# Directorio base para logs
LOGS_DIR = Path(__file__).resolve().parent.parent / 'logs'

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
    },
    'handlers': {
        'advanced_features_file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'advanced_features.log',
            'maxBytes': 1024*1024*5,  # 5MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'forms_file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'forms.log',
            'maxBytes': 1024*1024*5,
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'analytics_file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'analytics.log',
            'maxBytes': 1024*1024*5,
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'payments_file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'payments.log',
            'maxBytes': 1024*1024*5,
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'social_file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'social.log',
            'maxBytes': 1024*1024*5,
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'proposals_file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'proposals.log',
            'maxBytes': 1024*1024*5,
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'communications_file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'communications.log',
            'maxBytes': 1024*1024*5,
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'app.advanced_features': {
            'handlers': ['advanced_features_file', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'app.forms': {
            'handlers': ['forms_file', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'app.analytics': {
            'handlers': ['analytics_file', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'app.payments': {
            'handlers': ['payments_file', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'app.social': {
            'handlers': ['social_file', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'app.proposals': {
            'handlers': ['proposals_file', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'app.communications': {
            'handlers': ['communications_file', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
