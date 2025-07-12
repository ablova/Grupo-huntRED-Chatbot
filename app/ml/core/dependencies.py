"""
Configuración de dependencias opcionales para el módulo de ML.
Maneja la disponibilidad de diferentes librerías de ML.
"""

import logging

logger = logging.getLogger(__name__)

# PyTorch
try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
    logger.info("✅ PyTorch disponible")
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("⚠️ PyTorch no disponible. Algunas funcionalidades pueden estar limitadas.")

# TensorFlow
try:
    import tensorflow as tf
    TENSORFLOW_AVAILABLE = True
    logger.info("✅ TensorFlow disponible")
except ImportError:
    TENSORFLOW_AVAILABLE = False
    logger.warning("⚠️ TensorFlow no disponible. Algunas funcionalidades pueden estar limitadas.")

# Scikit-learn
try:
    import sklearn
    SKLEARN_AVAILABLE = True
    logger.info("✅ Scikit-learn disponible")
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("⚠️ Scikit-learn no disponible. Algunas funcionalidades pueden estar limitadas.")

# Transformers (Hugging Face)
try:
    import transformers
    TRANSFORMERS_AVAILABLE = True
    logger.info("✅ Transformers disponible")
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.warning("⚠️ Transformers no disponible. Algunas funcionalidades pueden estar limitadas.")

# Pandas
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
    logger.info("✅ Pandas disponible")
except ImportError:
    PANDAS_AVAILABLE = False
    logger.warning("⚠️ Pandas no disponible. Algunas funcionalidades pueden estar limitadas.")

# Matplotlib
try:
    import matplotlib
    MATPLOTLIB_AVAILABLE = True
    logger.info("✅ Matplotlib disponible")
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    logger.warning("⚠️ Matplotlib no disponible. Algunas funcionalidades pueden estar limitadas.")

# Seaborn
try:
    import seaborn as sns
    SEABORN_AVAILABLE = True
    logger.info("✅ Seaborn disponible")
except ImportError:
    SEABORN_AVAILABLE = False
    logger.warning("⚠️ Seaborn no disponible. Algunas funcionalidades pueden estar limitadas.")

# Plotly
try:
    import plotly
    PLOTLY_AVAILABLE = True
    logger.info("✅ Plotly disponible")
except ImportError:
    PLOTLY_AVAILABLE = False
    logger.warning("⚠️ Plotly no disponible. Algunas funcionalidades pueden estar limitadas.")

# NLTK
try:
    import nltk
    NLTK_AVAILABLE = True
    logger.info("✅ NLTK disponible")
except ImportError:
    NLTK_AVAILABLE = False
    logger.warning("⚠️ NLTK no disponible. Algunas funcionalidades pueden estar limitadas.")

# SpaCy
try:
    import spacy
    SPACY_AVAILABLE = True
    logger.info("✅ SpaCy disponible")
except ImportError:
    SPACY_AVAILABLE = False
    logger.warning("⚠️ SpaCy no disponible. Algunas funcionalidades pueden estar limitadas.")

# Redis
try:
    import redis
    REDIS_AVAILABLE = True
    logger.info("✅ Redis disponible")
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("⚠️ Redis no disponible. Algunas funcionalidades pueden estar limitadas.")

# Celery
try:
    import celery
    CELERY_AVAILABLE = True
    logger.info("✅ Celery disponible")
except ImportError:
    CELERY_AVAILABLE = False
    logger.warning("⚠️ Celery no disponible. Algunas funcionalidades pueden estar limitadas.")

def get_ml_status():
    """Obtiene el estado de todas las dependencias de ML."""
    return {
        'torch': TORCH_AVAILABLE,
        'tensorflow': TENSORFLOW_AVAILABLE,
        'sklearn': SKLEARN_AVAILABLE,
        'transformers': TRANSFORMERS_AVAILABLE,
        'pandas': PANDAS_AVAILABLE,
        'matplotlib': MATPLOTLIB_AVAILABLE,
        'seaborn': SEABORN_AVAILABLE,
        'plotly': PLOTLY_AVAILABLE,
        'nltk': NLTK_AVAILABLE,
        'spacy': SPACY_AVAILABLE,
        'redis': REDIS_AVAILABLE,
        'celery': CELERY_AVAILABLE
    }

def check_ml_requirements(required_deps: list) -> bool:
    """Verifica si las dependencias requeridas están disponibles."""
    status = get_ml_status()
    missing = [dep for dep in required_deps if not status.get(dep, False)]
    
    if missing:
        logger.warning(f"⚠️ Dependencias faltantes: {missing}")
        return False
    
    return True 