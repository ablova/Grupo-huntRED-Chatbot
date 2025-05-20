# /home/pablo/app/ml/import_config.py
#
# NOTA: Este archivo está obsoleto y se mantiene temporalmente para compatibilidad.
# El registro de módulos ahora es gestionado automáticamente por ModuleRegistry en app/module_registry.py
# siguiendo la regla global de Grupo huntRED® "No Redundancies".
# 
# De acuerdo con las reglas globales de Grupo huntRED®:
# - Code Consistency: Se siguen estándares de Django (DRY, referencias string para dependencias)
# - Modularity: Escribir código modular, reutilizable; evitar duplicar funcionalidad
# - No Redundancies: Verificar antes de añadir funciones que no existan en el código fuente

# Los módulos de ML deben ser importados directamente con importaciones estándar de Python:  
# from app.ml.ml_model import MLModel
# from app.ml.data_loader import DataLoader
# etc.


def get_ml_model():
    """Get MLModel instance."""
    from app.ml.ml_model import MLModel
    return MLModel

def get_data_loader():
    """Get DataLoader instance."""
    from app.ml.data_loader import DataLoader
    return DataLoader

def get_feature_extractor():
    """Get FeatureExtractor instance."""
    from app.ml.feature_extractor import FeatureExtractor
    return FeatureExtractor

def get_model_trainer():
    """Get ModelTrainer instance."""
    from app.ml.model_trainer import ModelTrainer
    return ModelTrainer

def get_prediction_service():
    """Get PredictionService instance."""
    from app.ml.prediction_service import PredictionService
    return PredictionService

def get_skill_classifier():
    """Get SkillClassifier instance."""
    from app.ml.skill_classifier import SkillClassifier
    return SkillClassifier

def get_cv_analyzer():
    """Get CVAnalyzer instance."""
    from app.ml.cv_analyzer import CVAnalyzer
    return CVAnalyzer

def get_nlp_processor():
    """Get NLPProcessor instance."""
    from app.ml.nlp_processor import NLPProcessor
    return NLPProcessor

def get_sentiment_analyzer():
    """Get SentimentAnalyzer instance."""
    from app.ml.sentiment_analyzer import SentimentAnalyzer
    return SentimentAnalyzer
