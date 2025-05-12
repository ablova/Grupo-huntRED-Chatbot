from typing import Any, Callable
from app.import_config import register_module

# Register ML modules at startup
register_module('ml_model', 'app.ml.ml_model.MLModel')
register_module('data_loader', 'app.ml.data_loader.DataLoader')
register_module('feature_extractor', 'app.ml.feature_extractor.FeatureExtractor')
register_module('model_trainer', 'app.ml.model_trainer.ModelTrainer')
register_module('prediction_service', 'app.ml.prediction_service.PredictionService')
register_module('skill_classifier', 'app.ml.skill_classifier.SkillClassifier')
register_module('cv_analyzer', 'app.ml.cv_analyzer.CVAnalyzer')
register_module('nlp_processor', 'app.ml.nlp_processor.NLPProcessor')
register_module('sentiment_analyzer', 'app.ml.sentiment_analyzer.SentimentAnalyzer')

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
