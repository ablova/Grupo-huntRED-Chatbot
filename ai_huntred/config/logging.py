import logging
import os
from datetime import datetime

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

def setup_logging():
    # Configuración de directorio de logs
    LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

    # Formato de fecha para México
    DATE_FORMAT = '%d/%m/%Y %H:%M:%S'

    log_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'verbose': {
                'format': ('%(asctime)s [%(levelname)s] %(name)s '
                         '%(filename)s:%(lineno)d - %(message)s'),
                'datefmt': DATE_FORMAT
            },
            'simple': {
                'format': '%(asctime)s [%(levelname)s] %(message)s',
                'datefmt': DATE_FORMAT
            },
            'mexico': {
                'format': ('%(asctime)s [%(levelname)s] %(name)s '
                         '[%(hostname)s] %(filename)s:%(lineno)d - %(message)s'),
                'datefmt': DATE_FORMAT
            }
        },
        'handlers': {
            'file': {
                'level': 'DEBUG',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': os.path.join(LOG_DIR, f'application_{datetime.now().strftime("%Y%m%d")}.log'),
                'maxBytes': 1024*1024*10,  # 10MB
                'backupCount': 7,
                'formatter': 'mexico',
            },
            'console': {
                'level': 'INFO',
                'class': 'logging.StreamHandler',
                'formatter': 'simple',
            },
            'error_file': {
                'level': 'ERROR',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': os.path.join(LOG_DIR, f'error_{datetime.now().strftime("%Y%m%d")}.log'),
                'maxBytes': 1024*1024*10,  # 10MB
                'backupCount': 7,
                'formatter': 'mexico',
            },
            'celery_file': {
                'level': 'INFO',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': os.path.join(LOG_DIR, f'celery_{datetime.now().strftime("%Y%m%d")}.log'),
                'maxBytes': 1024*1024*10,  # 10MB
                'backupCount': 7,
                'formatter': 'mexico',
            },
            'security_file': {
                'level': 'INFO',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': os.path.join(LOG_DIR, f'security_{datetime.now().strftime("%Y%m%d")}.log'),
                'maxBytes': 1024*1024*10,  # 10MB
                'backupCount': 7,
                'formatter': 'mexico',
            }
        },
        'loggers': {
            'django': {
                'handlers': ['file', 'console', 'error_file'],
                'level': 'INFO',
                'propagate': True,
            },
            'app': {
                'handlers': ['file', 'console', 'error_file', 'security_file'],
                'level': 'DEBUG',
                'propagate': False,
            },
            'celery': {
                'handlers': ['file', 'console', 'error_file', 'celery_file'],
                'level': 'INFO',
                'propagate': False,
            },
            'security': {
                'handlers': ['file', 'console', 'error_file', 'security_file'],
                'level': 'INFO',
                'propagate': False,
            },
            'performance': {
                'handlers': ['file', 'console', 'error_file'],
                'level': 'INFO',
                'propagate': False,
            }
        },
    }

    return log_config
