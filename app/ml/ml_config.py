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
        },
        'ASYNC': {
            'MAX_CONCURRENT_TASKS': 5,
            'TASK_TIMEOUT': 60,
            'RETRY_DELAY': 5,
            'MAX_RETRIES': 3
        }
    },
    'PREDICTION': {
        'CONFIDENCE_THRESHOLD': 0.7,
        'MIN_MATCH_SCORE': 0.5,
        'MAX_RECOMMENDATIONS': 10,
        'CACHE_TTL': 3600,  # 1 hora
        'DATA_VALIDATION': {
            'MIN_EXPERIENCE': 0,
            'MAX_EXPERIENCE': 50,
            'MIN_SALARY': 0,
            'MAX_SALARY': 500000,
            'MIN_EDUCATION': 0,
            'MAX_EDUCATION': 6
        }
    },
    'BUSINESS': {
        'UNITS': {
            'AMIGRO': {
                'WEIGHT': 1.0,
                'PRIORITY': 1,
                'MATCHING_WEIGHTS': {
                    'SKILLS': {
                        'HARD_SKILLS': 0.25,
                        'SOFT_SKILLS': 0.15,
                        'TECHNICAL_EXPERTISE': 0.20
                    },
                    'CULTURAL_FIT': {
                        'VALUES_ALIGNMENT': 0.15,
                        'TEAM_DYNAMICS': 0.10,
                        'COMMUNICATION_STYLE': 0.05
                    },
                    'EXPERIENCE': {
                        'YEARS': 0.10,
                        'INDUSTRY': 0.05,
                        'ROLE_SPECIFIC': 0.15
                    },
                    'LOCATION': {
                        'GEOGRAPHIC': 0.05,
                        'REMOTE_COMPATIBILITY': 0.05
                    }
                }
            },
            'HUNTU': {
                'WEIGHT': 1.2,
                'PRIORITY': 2,
                'MATCHING_WEIGHTS': {
                    'SKILLS': {
                        'HARD_SKILLS': 0.30,
                        'SOFT_SKILLS': 0.15,
                        'TECHNICAL_EXPERTISE': 0.20
                    },
                    'CULTURAL_FIT': {
                        'VALUES_ALIGNMENT': 0.15,
                        'TEAM_DYNAMICS': 0.10,
                        'COMMUNICATION_STYLE': 0.05
                    },
                    'EXPERIENCE': {
                        'YEARS': 0.10,
                        'INDUSTRY': 0.05,
                        'ROLE_SPECIFIC': 0.15
                    },
                    'LOCATION': {
                        'GEOGRAPHIC': 0.05,
                        'REMOTE_COMPATIBILITY': 0.05
                    }
                }
            },
            'HUNTRED': {
                'WEIGHT': 1.5,
                'PRIORITY': 3,
                'MATCHING_WEIGHTS': {
                    'SKILLS': {
                        'HARD_SKILLS': 0.35,
                        'SOFT_SKILLS': 0.15,
                        'TECHNICAL_EXPERTISE': 0.20
                    },
                    'CULTURAL_FIT': {
                        'VALUES_ALIGNMENT': 0.15,
                        'TEAM_DYNAMICS': 0.10,
                        'COMMUNICATION_STYLE': 0.05
                    },
                    'EXPERIENCE': {
                        'YEARS': 0.10,
                        'INDUSTRY': 0.05,
                        'ROLE_SPECIFIC': 0.15
                    },
                    'LOCATION': {
                        'GEOGRAPHIC': 0.05,
                        'REMOTE_COMPATIBILITY': 0.05
                    }
                }
            },
            'HUNTRED_EXECUTIVE': {
                'WEIGHT': 2.0,
                'PRIORITY': 4,
                'MATCHING_WEIGHTS': {
                    'SKILLS': {
                        'HARD_SKILLS': 0.40,
                        'SOFT_SKILLS': 0.20,
                        'TECHNICAL_EXPERTISE': 0.20
                    },
                    'CULTURAL_FIT': {
                        'VALUES_ALIGNMENT': 0.20,
                        'TEAM_DYNAMICS': 0.15,
                        'COMMUNICATION_STYLE': 0.10
                    },
                    'EXPERIENCE': {
                        'YEARS': 0.15,
                        'INDUSTRY': 0.10,
                        'ROLE_SPECIFIC': 0.20
                    },
                    'LOCATION': {
                        'GEOGRAPHIC': 0.05,
                        'REMOTE_COMPATIBILITY': 0.10
                    }
                }
            }
        },
        'MATCHING': {
            'DEFAULT_WEIGHTS': {
                'SKILLS': {
                    'HARD_SKILLS': 0.30,
                    'SOFT_SKILLS': 0.15,
                    'TECHNICAL_EXPERTISE': 0.20
                },
                'CULTURAL_FIT': {
                    'VALUES_ALIGNMENT': 0.15,
                    'TEAM_DYNAMICS': 0.10,
                    'COMMUNICATION_STYLE': 0.05
                },
                'EXPERIENCE': {
                    'YEARS': 0.10,
                    'INDUSTRY': 0.05,
                    'ROLE_SPECIFIC': 0.15
                },
                'LOCATION': {
                    'GEOGRAPHIC': 0.05,
                    'REMOTE_COMPATIBILITY': 0.05
                }
            },
            'MIN_SCORE': 0.7,
            'MAX_RECOMMENDATIONS': 10,
            'DYNAMIC_WEIGHT_ADJUSTMENT': {
                'ENABLED': True,
                'LEARNING_RATE': 0.01,
                'UPDATE_FREQUENCY': 'WEEKLY',
                'MIN_SAMPLES': 100,
                'CONFIDENCE_THRESHOLD': 0.8
            },
            'FEATURE_IMPORTANCE': {
                'ENABLED': True,
                'UPDATE_FREQUENCY': 'MONTHLY',
                'MIN_SAMPLES': 500
            }
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