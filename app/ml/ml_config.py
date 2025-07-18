"""
Configuración centralizada para los modelos de Machine Learning.
"""

import os
from pathlib import Path
from django.conf import settings

# Directorios
ML_MODELS_DIR = os.path.join(settings.BASE_DIR, 'ml_models')
ML_DATA_DIR = os.path.join(settings.BASE_DIR, 'ml_data')
ML_LOGS_DIR = os.path.join(settings.BASE_DIR, 'ml_logs')

# Crear directorios si no existen
for directory in [ML_MODELS_DIR, ML_DATA_DIR, ML_LOGS_DIR]:
    Path(directory).mkdir(parents=True, exist_ok=True)

# Configuración de modelos
MODEL_CONFIG = {
    'matchmaking': {
        'type': 'random_forest',
        'n_estimators': 100,
        'max_depth': 10,
        'random_state': 42
    },
    'transition': {
        'type': 'random_forest',
        'n_estimators': 100,
        'max_depth': 10,
        'random_state': 42
    },
    'market': {
        'type': 'random_forest',
        'n_estimators': 100,
        'max_depth': 10,
        'random_state': 42
    }
}

# Configuración de unidades de negocio
BUSINESS_UNIT_CONFIG = {
    'huntRED®': {
        'matchmaking_threshold': 0.7,
        'transition_threshold': 0.8,
        'market_update_frequency': 'daily'
    },
    'huntU': {
        'matchmaking_threshold': 0.6,
        'transition_threshold': 0.7,
        'market_update_frequency': 'weekly'
    },
    'Amigro': {
        'matchmaking_threshold': 0.6,
        'transition_threshold': 0.7,
        'market_update_frequency': 'weekly'
    }
}

# Configuración de características
FEATURE_CONFIG = {
    'matchmaking': [
        'hard_skills_score',
        'soft_skills_score',
        'salary_alignment',
        'age',
        'experience_years'
    ],
    'transition': [
        'experience_years',
        'skills_count',
        'certifications_count',
        'education_level',
        'personality_traits'
    ],
    'market': [
        'skill_demand',
        'salary_trends',
        'experience_requirements',
        'education_requirements'
    ]
}

# Configuración de evaluación
EVALUATION_CONFIG = {
    'test_size': 0.2,
    'random_state': 42,
    'metrics': ['accuracy', 'precision', 'recall', 'f1']
}

# Configuración de caché
CACHE_CONFIG = {
    'enabled': True,
    'ttl': 3600,  # 1 hora
    'max_size': 1000
}

# Configuración de logging
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file': os.path.join(ML_LOGS_DIR, 'ml.log')
}

# Configuración de modelos de educación
EDUCATION_CONFIG = {
    'university': {
        'base_scores': {
            # Top 10 Universidades Nacionales
            'UNAM': {
                'score': 0.95,
                'ranking': 1,
                'cost': '$',
                'specialties': ['Medicina', 'Arquitectura', 'Política'],
                'is_public': True
            },
            'ITESM': {
                'score': 0.95,
                'ranking': 2,
                'cost': '$$$',
                'specialties': ['Ingeniería', 'TIC\'s', 'Economía'],
                'is_public': False
            },
            'UDG': {
                'score': 0.90,
                'ranking': 3,
                'cost': '$',
                'specialties': ['Ciencias sociales', 'Medicina'],
                'is_public': True
            },
            'UANL': {
                'score': 0.90,
                'ranking': 4,
                'cost': '$',
                'specialties': ['Ingeniería', 'Derecho', 'Administración'],
                'is_public': True
            },
            'IPN': {
                'score': 0.90,
                'ranking': 5,
                'cost': '$',
                'specialties': ['Administración', 'Ingeniería'],
                'is_public': True
            },
            'UIA': {
                'score': 0.85,
                'ranking': 13,
                'cost': '$$$',
                'specialties': ['Arquitectura', 'Comunicación', 'Contaduría'],
                'is_public': False
            },
            'ITAM': {
                'score': 0.85,
                'ranking': 19,
                'cost': '$$$',
                'specialties': ['Administración', 'Contaduría', 'Derecho'],
                'is_public': False
            },
            'Anáhuac': {
                'score': 0.80,
                'ranking': 17,
                'cost': '$$$',
                'specialties': ['Mercadotecnia', 'Medicina', 'Negocios'],
                'is_public': False
            },
            'La Salle': {
                'score': 0.80,
                'ranking': 46,
                'cost': '$$$',
                'specialties': ['Diseño Gráfico', 'Ingeniería Cibernética'],
                'is_public': False
            },
            'UVM': {
                'score': 0.75,
                'ranking': 38,
                'cost': '$$$',
                'specialties': ['Administración', 'Arquitectura', 'Derecho'],
                'is_public': False
            },
            # Universidades internacionales (top 10 QS)
            'MIT': {
                'score': 1.0,
                'ranking': 1,
                'cost': '$$$$',
                'specialties': ['Ingeniería', 'Ciencias', 'Tecnología'],
                'is_public': False,
                'is_international': True
            },
            'Cambridge': {
                'score': 1.0,
                'ranking': 2,
                'cost': '$$$$',
                'specialties': ['Ciencias', 'Humanidades', 'Ingeniería'],
                'is_public': False,
                'is_international': True
            },
            'Oxford': {
                'score': 1.0,
                'ranking': 3,
                'cost': '$$$$',
                'specialties': ['Humanidades', 'Ciencias', 'Medicina'],
                'is_public': False,
                'is_international': True
            },
            'Harvard': {
                'score': 1.0,
                'ranking': 4,
                'cost': '$$$$',
                'specialties': ['Negocios', 'Derecho', 'Medicina'],
                'is_public': False,
                'is_international': True
            },
            'Stanford': {
                'score': 1.0,
                'ranking': 5,
                'cost': '$$$$',
                'specialties': ['Tecnología', 'Negocios', 'Ingeniería'],
                'is_public': False,
                'is_international': True
            }
        },
        'ml_weights': {},  # Se llenará dinámicamente
        'cost_multipliers': {
            '$': 1.0,      # Públicas
            '$$': 1.1,     # Privadas económicas
            '$$$': 1.2,    # Privadas medias
            '$$$$': 1.3    # Privadas premium/internacionales
        }
    },
    'program': {
        'base_scores': {
            # Derecho
            'Derecho': {
                'Escuela Libre de Derecho': 1.0,
                'UNAM': 0.9,
                'ITAM': 0.9,
                'UIA': 0.85,
                'UANL': 0.85,
                'CIDE': 0.9,
            },
            # Medicina
            'Medicina': {
                'UNAM': 1.0,
                'IPN': 0.9,
                'ITESM': 0.85,
                'UDG': 0.85,
                'UANL': 0.85,
            },
            # Ingeniería
            'Ingeniería en Sistemas': {
                'ITESM': 1.0,
                'UNAM': 0.9,
                'IPN': 0.9,
                'UIA': 0.85,
            },
            'Ingeniería Industrial': {
                'ITESM': 1.0,
                'UNAM': 0.9,
                'IPN': 0.9,
                'UANL': 0.85,
            },
            # Negocios
            'Administración': {
                'ITAM': 1.0,
                'ITESM': 0.95,
                'UIA': 0.9,
                'IPN': 0.85,
            },
            'Finanzas': {
                'ITAM': 1.0,
                'ITESM': 0.95,
                'UIA': 0.9,
                'EBC': 0.85,
            },
            # Comunicación
            'Comunicación': {
                'UIA': 1.0,
                'ITESM': 0.95,
                'UNAM': 0.9,
                'UAM': 0.85,
            },
            # Arquitectura
            'Arquitectura': {
                'UNAM': 1.0,
                'UIA': 0.95,
                'ITESM': 0.9,
                'La Salle': 0.85,
            }
        },
        'ml_weights': {},  # Se llenará dinámicamente
        'specialty_bonus': 0.1  # Bonus por estudiar en una universidad especializada
    },
    'weights': {
        'undergraduate': 0.4,
        'graduate': 0.4,
        'phd': 0.2,
    },
    'confidence_threshold': 0.7,
    'update_frequency': 'weekly',
    'ranking_weights': {
        'top_10': 1.0,
        'top_25': 0.9,
        'top_50': 0.8,
        'top_100': 0.7,
        'others': 0.6
    }
}

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

class MLConfig:
    """
    Clase de configuración para el sistema de Machine Learning.
    """
    
    def __init__(self):
        self.model_config = MODEL_CONFIG
        self.business_unit_config = BUSINESS_UNIT_CONFIG
        self.feature_config = FEATURE_CONFIG
        self.evaluation_config = EVALUATION_CONFIG
        self.cache_config = CACHE_CONFIG
        self.logging_config = LOGGING_CONFIG
        self.education_config = EDUCATION_CONFIG
    
    def get_model_config(self, model_type: str) -> dict:
        """Obtiene la configuración de un modelo específico."""
        return self.model_config.get(model_type, {})
    
    def get_business_unit_config(self, bu_name: str) -> dict:
        """Obtiene la configuración de una unidad de negocio específica."""
        return self.business_unit_config.get(bu_name, {})
    
    def get_feature_config(self, model_type: str) -> list:
        """Obtiene la configuración de características para un modelo."""
        return self.feature_config.get(model_type, [])
    
    def is_cache_enabled(self) -> bool:
        """Verifica si el caché está habilitado."""
        return self.cache_config.get('enabled', False)
    
    def get_cache_ttl(self) -> int:
        """Obtiene el TTL del caché."""
        return self.cache_config.get('ttl', 3600) 