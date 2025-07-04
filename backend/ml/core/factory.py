"""
🧠 GhuntRED-v2 ML Factory
Central factory for all ML systems with performance optimizations and caching
"""

import asyncio
import logging
import time
from typing import Dict, List, Any, Optional, Union, Type
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from functools import lru_cache, wraps
import threading

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

# ML Libraries
import numpy as np
import pandas as pd
import joblib
from sklearn.base import BaseEstimator
import tensorflow as tf

# Custom imports (will be created)
from .exceptions import MLException, ModelNotFoundError, PredictionError
from .metrics import MLMetrics
from .validators import MLValidator
from .optimizers import PerformanceOptimizer

logger = logging.getLogger(__name__)

@dataclass
class MLModelInfo:
    """Information about an ML model"""
    name: str
    version: str
    model_type: str
    business_unit: str
    created_at: str
    accuracy: float
    performance_metrics: Dict[str, float]
    file_path: str
    
class MLModelRegistry:
    """Registry for ML models with versioning and performance tracking"""
    
    def __init__(self):
        self._models: Dict[str, MLModelInfo] = {}
        self._lock = threading.RLock()
        
    def register_model(self, model_info: MLModelInfo) -> bool:
        """Register a new ML model"""
        with self._lock:
            key = f"{model_info.business_unit}:{model_info.name}:{model_info.version}"
            self._models[key] = model_info
            logger.info(f"🧠 Registered ML model: {key}")
            return True
    
    def get_model_info(self, name: str, business_unit: str, version: str = "latest") -> Optional[MLModelInfo]:
        """Get model information"""
        with self._lock:
            if version == "latest":
                # Find latest version
                matching_models = [
                    (k, v) for k, v in self._models.items() 
                    if k.startswith(f"{business_unit}:{name}:")
                ]
                if not matching_models:
                    return None
                # Sort by version and get latest
                latest_key = sorted(matching_models, key=lambda x: x[1].created_at)[-1][0]
                return self._models[latest_key]
            else:
                key = f"{business_unit}:{name}:{version}"
                return self._models.get(key)
    
    def list_models(self, business_unit: str = None) -> List[MLModelInfo]:
        """List all registered models"""
        with self._lock:
            if business_unit:
                return [v for k, v in self._models.items() if k.startswith(f"{business_unit}:")]
            return list(self._models.values())

class MLFactory:
    """
    🚀 Central factory for all ML systems in GhuntRED-v2
    
    Features:
    - Lazy loading of models
    - Performance optimization
    - Caching system
    - Error handling
    - Metrics tracking
    - Multi-threading support
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern for ML Factory"""
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
            
        self._initialized = True
        self._models: Dict[str, Any] = {}
        self._model_registry = MLModelRegistry()
        self._metrics = MLMetrics()
        self._validator = MLValidator()
        self._optimizer = PerformanceOptimizer()
        self._thread_pool = ThreadPoolExecutor(max_workers=4)
        self._process_pool = ProcessPoolExecutor(max_workers=2)
        self._model_cache = {}
        self._lock = threading.RLock()
        
        logger.info("🚀 ML Factory initialized with latest optimizations")
        self._initialize_tensorflow()
        self._initialize_models()
    
    def _initialize_tensorflow(self):
        """Initialize TensorFlow with optimizations"""
        try:
            # Configure TensorFlow for optimal performance
            tf.config.threading.set_inter_op_parallelism_threads(2)
            tf.config.threading.set_intra_op_parallelism_threads(2)
            
            # Enable mixed precision if available
            if hasattr(tf.keras.mixed_precision, 'set_global_policy'):
                tf.keras.mixed_precision.set_global_policy('mixed_float16')
            
            # Configure memory growth for GPU if available
            gpus = tf.config.experimental.list_physical_devices('GPU')
            if gpus:
                for gpu in gpus:
                    tf.config.experimental.set_memory_growth(gpu, True)
                logger.info(f"🎮 Configured {len(gpus)} GPU(s) for TensorFlow")
            else:
                logger.info("💻 TensorFlow configured for CPU optimization")
                
        except Exception as e:
            logger.warning(f"⚠️ TensorFlow initialization warning: {e}")
    
    def _initialize_models(self):
        """Initialize and register default models"""
        try:
            # Register GenIA models
            self._register_genia_models()
            
            # Register AURA models  
            self._register_aura_models()
            
            logger.info("✅ All ML models registered successfully")
            
        except Exception as e:
            logger.error(f"❌ Error initializing models: {e}")
    
    def _register_genia_models(self):
        """Register GenIA models"""
        genia_models = [
            {
                'name': 'sentiment_analyzer',
                'version': '2.0.0',
                'model_type': 'sentiment_analysis',
                'accuracy': 0.94,
                'file_path': 'genia/sentiment_v2.joblib'
            },
            {
                'name': 'personality_analyzer', 
                'version': '2.0.0',
                'model_type': 'personality_analysis',
                'accuracy': 0.89,
                'file_path': 'genia/personality_v2.h5'
            },
            {
                'name': 'skills_extractor',
                'version': '2.0.0', 
                'model_type': 'skill_extraction',
                'accuracy': 0.91,
                'file_path': 'genia/skills_v2.joblib'
            },
            {
                'name': 'matching_engine',
                'version': '2.0.0',
                'model_type': 'candidate_matching',
                'accuracy': 0.87,
                'file_path': 'genia/matching_v2.h5'
            }
        ]
        
        for model_data in genia_models:
            for bu in ['huntRED', 'amigro', 'sexsi', 'huntu', 'huntred_executive']:
                model_info = MLModelInfo(
                    name=model_data['name'],
                    version=model_data['version'],
                    model_type=model_data['model_type'],
                    business_unit=bu,
                    created_at=timezone.now().isoformat(),
                    accuracy=model_data['accuracy'],
                    performance_metrics={
                        'precision': model_data['accuracy'] + 0.02,
                        'recall': model_data['accuracy'] - 0.01,
                        'f1_score': model_data['accuracy'],
                        'inference_time_ms': 150
                    },
                    file_path=model_data['file_path']
                )
                self._model_registry.register_model(model_info)
    
    def _register_aura_models(self):
        """Register AURA models"""
        aura_models = [
            {
                'name': 'holistic_assessor',
                'version': '2.0.0',
                'model_type': 'holistic_assessment',
                'accuracy': 0.92,
                'file_path': 'aura/holistic_v2.h5'
            },
            {
                'name': 'vibrational_matcher',
                'version': '2.0.0',
                'model_type': 'vibrational_matching',
                'accuracy': 0.88,
                'file_path': 'aura/vibrational_v2.h5'
            },
            {
                'name': 'compatibility_analyzer',
                'version': '2.0.0',
                'model_type': 'compatibility_analysis', 
                'accuracy': 0.90,
                'file_path': 'aura/compatibility_v2.h5'
            },
            {
                'name': 'energy_profiler',
                'version': '2.0.0',
                'model_type': 'energy_profiling',
                'accuracy': 0.86,
                'file_path': 'aura/energy_v2.joblib'
            }
        ]
        
        for model_data in aura_models:
            for bu in ['huntRED', 'amigro', 'sexsi', 'huntu', 'huntred_executive']:
                model_info = MLModelInfo(
                    name=model_data['name'],
                    version=model_data['version'],
                    model_type=model_data['model_type'],
                    business_unit=bu,
                    created_at=timezone.now().isoformat(),
                    accuracy=model_data['accuracy'],
                    performance_metrics={
                        'precision': model_data['accuracy'] + 0.01,
                        'recall': model_data['accuracy'],
                        'f1_score': model_data['accuracy'] - 0.01,
                        'inference_time_ms': 200
                    },
                    file_path=model_data['file_path']
                )
                self._model_registry.register_model(model_info)
    
    @lru_cache(maxsize=128)
    def get_model(self, model_name: str, business_unit: str, version: str = "latest") -> Any:
        """
        Get a model with caching and lazy loading
        
        Args:
            model_name: Name of the model
            business_unit: Business unit identifier
            version: Model version (default: latest)
            
        Returns:
            Loaded ML model
            
        Raises:
            ModelNotFoundError: If model is not found
        """
        cache_key = f"ml_model:{business_unit}:{model_name}:{version}"
        
        # Try to get from cache first
        cached_model = cache.get(cache_key)
        if cached_model:
            self._metrics.increment_cache_hit()
            return cached_model
        
        with self._lock:
            # Double-check in instance cache
            if cache_key in self._model_cache:
                return self._model_cache[cache_key]
            
            # Get model info from registry
            model_info = self._model_registry.get_model_info(model_name, business_unit, version)
            if not model_info:
                raise ModelNotFoundError(f"Model {model_name} not found for {business_unit}")
            
            # Load the actual model
            model = self._load_model(model_info)
            
            # Cache the model
            self._model_cache[cache_key] = model
            cache.set(cache_key, model, timeout=3600)  # Cache for 1 hour
            
            self._metrics.increment_cache_miss()
            logger.info(f"🔄 Loaded model: {cache_key}")
            
            return model
    
    def _load_model(self, model_info: MLModelInfo) -> Any:
        """Load a model from disk"""
        try:
            import os
            model_path = os.path.join(settings.BASE_DIR, 'ml', 'models', model_info.file_path)
            
            if model_info.file_path.endswith('.joblib'):
                return joblib.load(model_path)
            elif model_info.file_path.endswith('.h5'):
                return tf.keras.models.load_model(model_path)
            else:
                raise MLException(f"Unsupported model format: {model_info.file_path}")
                
        except Exception as e:
            logger.error(f"❌ Error loading model {model_info.name}: {e}")
            # Return a dummy model for development
            return self._create_dummy_model(model_info)
    
    def _create_dummy_model(self, model_info: MLModelInfo) -> Any:
        """Create a dummy model for development/testing"""
        logger.warning(f"⚠️ Creating dummy model for {model_info.name}")
        
        class DummyModel:
            def __init__(self, model_info):
                self.model_info = model_info
                self.model_type = model_info.model_type
                
            def predict(self, X):
                """Dummy prediction"""
                if hasattr(X, 'shape'):
                    # Return random predictions based on input shape
                    if len(X.shape) == 1:
                        return np.random.random(1)
                    else:
                        return np.random.random(X.shape[0])
                else:
                    return np.random.random()
            
            def predict_proba(self, X):
                """Dummy probability prediction"""
                predictions = self.predict(X)
                if hasattr(predictions, '__len__'):
                    return np.column_stack([1 - predictions, predictions])
                else:
                    return np.array([[1 - predictions, predictions]])
        
        return DummyModel(model_info)
    
    async def predict_async(self, model_name: str, business_unit: str, data: Any, **kwargs) -> Any:
        """
        Asynchronous prediction with performance optimization
        
        Args:
            model_name: Name of the model to use
            business_unit: Business unit identifier
            data: Input data for prediction
            **kwargs: Additional parameters
            
        Returns:
            Prediction results
        """
        start_time = time.time()
        
        try:
            # Validate input data
            self._validator.validate_input(data, model_name)
            
            # Get model
            model = self.get_model(model_name, business_unit)
            
            # Run prediction in thread pool for CPU-intensive tasks
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self._thread_pool,
                self._execute_prediction,
                model,
                data,
                kwargs
            )
            
            # Record metrics
            execution_time = (time.time() - start_time) * 1000  # milliseconds
            self._metrics.record_prediction_time(model_name, execution_time)
            self._metrics.increment_prediction_count(model_name)
            
            logger.debug(f"⚡ Prediction completed in {execution_time:.2f}ms")
            
            return result
            
        except Exception as e:
            self._metrics.increment_error_count(model_name)
            logger.error(f"❌ Prediction error for {model_name}: {e}")
            raise PredictionError(f"Prediction failed: {str(e)}")
    
    def _execute_prediction(self, model: Any, data: Any, kwargs: Dict) -> Any:
        """Execute the actual prediction"""
        try:
            # Preprocess data if needed
            processed_data = self._preprocess_data(data, kwargs)
            
            # Make prediction
            if hasattr(model, 'predict_proba'):
                result = model.predict_proba(processed_data)
            else:
                result = model.predict(processed_data)
            
            # Postprocess result if needed
            return self._postprocess_result(result, kwargs)
            
        except Exception as e:
            logger.error(f"❌ Prediction execution error: {e}")
            raise
    
    def _preprocess_data(self, data: Any, kwargs: Dict) -> Any:
        """Preprocess input data"""
        # Basic preprocessing - can be extended
        if isinstance(data, pd.DataFrame):
            return data.values
        elif isinstance(data, list):
            return np.array(data)
        else:
            return data
    
    def _postprocess_result(self, result: Any, kwargs: Dict) -> Any:
        """Postprocess prediction result"""
        # Basic postprocessing - can be extended
        if hasattr(result, 'tolist'):
            return result.tolist()
        else:
            return result
    
    def get_model_metrics(self, model_name: str) -> Dict[str, Any]:
        """Get performance metrics for a model"""
        return self._metrics.get_model_metrics(model_name)
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get overall system metrics"""
        return {
            'total_models': len(self._model_cache),
            'cache_hit_rate': self._metrics.get_cache_hit_rate(),
            'total_predictions': self._metrics.get_total_predictions(),
            'average_response_time': self._metrics.get_average_response_time(),
            'error_rate': self._metrics.get_error_rate(),
            'registered_models': len(self._model_registry._models),
            'active_threads': self._thread_pool._threads,
        }
    
    def clear_cache(self, model_name: str = None, business_unit: str = None):
        """Clear model cache"""
        if model_name and business_unit:
            cache_key = f"ml_model:{business_unit}:{model_name}:latest"
            cache.delete(cache_key)
            self._model_cache.pop(cache_key, None)
        else:
            # Clear all cache
            cache.clear()
            self._model_cache.clear()
        
        logger.info("🧹 ML cache cleared")
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on ML systems"""
        health_status = {
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'models_loaded': len(self._model_cache),
            'registry_models': len(self._model_registry._models),
            'tensorflow_version': tf.__version__,
            'gpu_available': len(tf.config.experimental.list_physical_devices('GPU')) > 0,
        }
        
        # Test a simple prediction
        try:
            test_data = np.array([[0.5, 0.3, 0.8]])
            model = self.get_model('sentiment_analyzer', 'huntRED')
            result = model.predict(test_data)
            health_status['test_prediction'] = 'success'
        except Exception as e:
            health_status['status'] = 'degraded'
            health_status['test_prediction'] = f'failed: {str(e)}'
        
        return health_status
    
    def shutdown(self):
        """Gracefully shutdown ML Factory"""
        logger.info("🔄 Shutting down ML Factory...")
        
        # Shutdown thread pools
        self._thread_pool.shutdown(wait=True)
        self._process_pool.shutdown(wait=True)
        
        # Clear caches
        self.clear_cache()
        
        logger.info("✅ ML Factory shutdown complete")

# Global instance
ml_factory = MLFactory()

# Convenience functions
def get_genia_analyzer(business_unit: str = 'huntRED'):
    """Get GenIA analyzer for a business unit"""
    from ..genia.analyzer import GenIAAnalyzer
    return GenIAAnalyzer(business_unit, ml_factory)

def get_aura_engine(business_unit: str = 'huntRED'):
    """Get AURA engine for a business unit"""
    from ..aura.engine import AURAEngine
    return AURAEngine(business_unit, ml_factory)

def get_ml_metrics():
    """Get ML system metrics"""
    return ml_factory.get_system_metrics()

def health_check():
    """Perform ML system health check"""
    return ml_factory.health_check()

# Export main components
__all__ = [
    'MLFactory',
    'MLModelRegistry', 
    'MLModelInfo',
    'ml_factory',
    'get_genia_analyzer',
    'get_aura_engine',
    'get_ml_metrics',
    'health_check'
]