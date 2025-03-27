import os
from django.conf import settings

ML_CONFIG = {
    'ENABLED_ON_MIGRATE': False,  # Deshabilitar durante migraciones
    'TENSORFLOW_THREADS': {
        'INTRA_OP': 1,
        'INTER_OP': 1
    },
    'MODEL_PATHS': {
        'BASE_DIR': settings.ML_MODELS_DIR,
        'SKILLS': os.path.join(settings.ML_MODELS_DIR, 'skills'),
        'NER': os.path.join(settings.ML_MODELS_DIR, 'ner'),
        'SENTIMENT': os.path.join(settings.ML_MODELS_DIR, 'sentiment')
    }
} 