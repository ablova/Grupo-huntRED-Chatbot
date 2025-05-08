import os
from django.conf import settings

ML_CONFIG = {
    'SYSTEM': {
        'ENABLED_ON_MIGRATE': False,  # Deshabilitar durante migraciones
        'TENSORFLOW_THREADS': {
            'INTRA_OP': 1,
            'INTER_OP': 1
        },
        'LOG_LEVEL': 'INFO',
        'MONITORING_INTERVAL': 60  # 60 segundos
    },
    'STORAGE': {
        'MODEL_PATHS': {
            'BASE_DIR': settings.ML_MODELS_DIR,
            'SKILLS': os.path.join(settings.ML_MODELS_DIR, 'skills'),
            'NER': os.path.join(settings.ML_MODELS_DIR, 'ner'),
            'SENTIMENT': os.path.join(settings.ML_MODELS_DIR, 'sentiment'),
            'MATCHMAKING': os.path.join(settings.ML_MODELS_DIR, 'matchmaking'),
            'TRANSITION': os.path.join(settings.ML_MODELS_DIR, 'transition')
        },
        'CACHE': {
            'MAX_SIZE': 10000,
            'TTL': 86400,  # 24 horas
            'DISTRIBUTED': True,
            'BACKEND': 'redis'
        }
    },
    'PERFORMANCE': {
        'OPTIMIZATION': {
            'BATCH_SIZE': 1000,
            'GPU_ENABLED': False,
            'QUANTIZATION': True,
            'MODEL_COMPRESSION': True,
            'DATA_COMPRESSION': True
        },
        'ANALYSIS': {
            'MAX_WORKERS': os.cpu_count(),
            'TIMEOUT': 30,
            'RETRY_ATTEMPTS': 3,
            'QUEUE_SIZE': 1000
        }
    },
    'PREDICTION': {
        'CONFIDENCE_THRESHOLD': 0.7,
        'MIN_MATCH_SCORE': 0.5,
        'MAX_RECOMMENDATIONS': 10,
        'CACHE_TTL': 3600  # 1 hora
    },
    'BUSINESS': {
        'UNITS': {
            'AMIGRO': {
                'WEIGHT': 1.0,
                'PRIORITY': 1,
                'MATCHING_WEIGHTS': {
                    'SKILLS': 0.4,
                    'CULTURAL_FIT': 0.3,
                    'EXPERIENCE': 0.2,
                    'LOCATION': 0.1
                }
            },
            'HUNTU': {
                'WEIGHT': 1.2,
                'PRIORITY': 2,
                'MATCHING_WEIGHTS': {
                    'SKILLS': 0.45,
                    'CULTURAL_FIT': 0.3,
                    'EXPERIENCE': 0.15,
                    'LOCATION': 0.1
                }
            },
            'HUNTRED': {
                'WEIGHT': 1.5,
                'PRIORITY': 3,
                'MATCHING_WEIGHTS': {
                    'SKILLS': 0.5,
                    'CULTURAL_FIT': 0.3,
                    'EXPERIENCE': 0.15,
                    'LOCATION': 0.05
                }
            },
            'HUNTRED_EXECUTIVE': {
                'WEIGHT': 2.0,
                'PRIORITY': 4,
                'MATCHING_WEIGHTS': {
                    'SKILLS': 0.6,
                    'CULTURAL_FIT': 0.2,
                    'EXPERIENCE': 0.15,
                    'LOCATION': 0.05
                }
            }
        },
        'MATCHING': {
            'DEFAULT_WEIGHTS': {
                'SKILLS': 0.4,
                'CULTURAL_FIT': 0.3,
                'EXPERIENCE': 0.2,
                'LOCATION': 0.1
            },
            'MIN_SCORE': 0.5,
            'MAX_RECOMMENDATIONS': 10
        }
    },
    'ANALYTICS': {
        'PREDICTIVE': {
            'TIME_WINDOW': 30,  # 30 días
            'TREND_THRESHOLD': 0.1,
            'ANOMALY_THRESHOLD': 3.0
        },
        'METRICS': {
            'UPDATE_INTERVAL': 300,  # 5 minutos
            'HISTORY_WINDOW': 7,  # 7 días
            'ALERT_THRESHOLDS': {
                'MATCHING': 0.9,
                'TRANSITION': 0.85,
                'PREDICTION': 0.7
            }
        }
    }
}
} 