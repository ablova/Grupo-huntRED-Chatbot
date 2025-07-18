# /home/pablo/ai_huntred/config/logging.py
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
                'format': ('%(asctime)s [%(levelname)s] %(name)s %(filename)s:%(lineno)d - %(message)s'),
                'datefmt': DATE_FORMAT
            },
            'debug': {
                'format': ('%(asctime)s [%(levelname)s] %(name)s %(filename)s:%(lineno)d '
                          'PID:%(process)d TID:%(thread)d - %(message)s'),
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
            },
            'whatsapp_file': {
                'level': 'INFO',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': os.path.join(LOG_DIR, f'whatsapp_{datetime.now().strftime("%Y%m%d")}.log'),
                'maxBytes': 1024*1024*10,  # 10MB
                'backupCount': 7,
                'formatter': 'debug',
            },
            'telegram_file': {
                'level': 'INFO',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': os.path.join(LOG_DIR, f'telegram_{datetime.now().strftime("%Y%m%d")}.log'),
                'maxBytes': 1024*1024*10,  # 10MB
                'backupCount': 7,
                'formatter': 'debug',
            },
            'messenger_file': {
                'level': 'INFO',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': os.path.join(LOG_DIR, f'messenger_{datetime.now().strftime("%Y%m%d")}.log'),
                'maxBytes': 1024*1024*10,  # 10MB
                'backupCount': 7,
                'formatter': 'debug',
            },
            'instagram_file': {
                'level': 'INFO',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': os.path.join(LOG_DIR, f'instagram_{datetime.now().strftime("%Y%m%d")}.log'),
                'maxBytes': 1024*1024*10,  # 10MB
                'backupCount': 7,
                'formatter': 'debug',
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
            },
            'whatsapp': {
                'handlers': ['file', 'console', 'error_file', 'whatsapp_file'],
                'level': 'DEBUG',
                'propagate': False,
            },
            'telegram': {
                'handlers': ['file', 'console', 'error_file', 'telegram_file'],
                'level': 'DEBUG',
                'propagate': False,
            },
            'messenger': {
                'handlers': ['file', 'console', 'error_file', 'messenger_file'],
                'level': 'DEBUG',
                'propagate': False,
            },
            'instagram': {
                'handlers': ['file', 'console', 'error_file', 'instagram_file'],
                'level': 'DEBUG',
                'propagate': False,
            }
        },
    }

    return log_config
