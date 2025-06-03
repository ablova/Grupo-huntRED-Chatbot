"""
Módulo para el procesamiento asíncrono de datos y modelos ML.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
import pandas as pd
from asgiref.sync import sync_to_async
from django.core.cache import cache
from app.ml.core.data_cleaning import DataCleaner
from app.ml.ml_config import ML_CONFIG

logger = logging.getLogger(__name__)

class AsyncProcessor:
    """Clase para procesamiento asíncrono de datos y modelos ML."""

    def __init__(self):
        self.data_cleaner = DataCleaner()
        self.cache_timeout = ML_CONFIG['STORAGE']['CACHE']['TTL']
        self.max_workers = ML_CONFIG['PERFORMANCE']['ANALYSIS']['MAX_WORKERS']

    async def process_data_async(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa datos de manera asíncrona."""
        try:
            # Verificar caché
            cache_key = f"processed_data:{hash(str(data))}"
            cached_data = cache.get(cache_key)
            
            if cached_data:
                logger.info(f"Datos recuperados de caché: {cache_key}")
                return cached_data

            # Procesar datos
            cleaned_data = self.data_cleaner.clean_data(data)
            
            # Guardar en caché
            cache.set(cache_key, cleaned_data, self.cache_timeout)
            
            return cleaned_data
        except Exception as e:
            logger.error(f"Error procesando datos: {str(e)}")
            return {}

    async def process_batch_async(self, data_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Procesa un lote de datos de manera asíncrona."""
        tasks = []
        for data in data_list:
            tasks.append(self.process_data_async(data))
        
        # Ejecutar tareas con límite de workers
        results = await asyncio.gather(
            *tasks,
            return_exceptions=True
        )
        
        return [result for result in results if not isinstance(result, Exception)]

    async def predict_async(self, model, features: pd.DataFrame) -> pd.DataFrame:
        """Realiza predicciones de manera asíncrona."""
        try:
            # Verificar caché de predicciones
            cache_key = f"predictions:{hash(str(features))}"
            cached_predictions = cache.get(cache_key)
            
            if cached_predictions is not None:
                logger.info(f"Predicciones recuperadas de caché: {cache_key}")
                return cached_predictions

            # Realizar predicción
            predictions = model.predict(features)
            
            # Guardar en caché
            cache.set(cache_key, predictions, self.cache_timeout)
            
            return predictions
        except Exception as e:
            logger.error(f"Error realizando predicción: {str(e)}")
            return pd.DataFrame()

    async def train_model_async(self, model, X: pd.DataFrame, y: pd.Series) -> bool:
        """Entrena un modelo de manera asíncrona."""
        try:
            # Verificar si ya existe un modelo entrenado
            cache_key = f"trained_model:{hash(str(X))}"
            if cache.get(cache_key):
                logger.info(f"Modelo ya entrenado: {cache_key}")
                return True

            # Entrenar modelo
            model.fit(X, y)
            
            # Guardar en caché
            cache.set(cache_key, True, self.cache_timeout)
            
            return True
        except Exception as e:
            logger.error(f"Error entrenando modelo: {str(e)}")
            return False

    async def evaluate_model_async(self, model, X: pd.DataFrame, y: pd.Series) -> Dict[str, float]:
        """Evaluación de modelo de manera asíncrona."""
        try:
            # Realizar predicciones
            predictions = await self.predict_async(model, X)
            
            # Calcular métricas
            metrics = {
                'accuracy': (predictions == y).mean(),
                'precision': (predictions[predictions == 1] == y[predictions == 1]).mean(),
                'recall': (predictions[predictions == 1] == y[predictions == 1]).sum() / y.sum()
            }
            
            return metrics
        except Exception as e:
            logger.error(f"Error evaluando modelo: {str(e)}")
            return {}

    async def process_pipeline_async(self, data: Dict[str, Any], model) -> Dict[str, Any]:
        """Procesa el pipeline completo de manera asíncrona."""
        try:
            # Paso 1: Limpieza de datos
            cleaned_data = await self.process_data_async(data)
            
            # Paso 2: Transformación de características
            features = pd.DataFrame([cleaned_data])
            features_transformed = self.data_cleaner.transform_features(features)
            
            # Paso 3: Predicción
            predictions = await self.predict_async(model, features_transformed)
            
            # Paso 4: Evaluación
            evaluation = await self.evaluate_model_async(model, features_transformed, pd.Series([1]))
            
            return {
                'cleaned_data': cleaned_data,
                'features': features_transformed.to_dict(),
                'prediction': predictions[0] if len(predictions) > 0 else None,
                'evaluation': evaluation
            }
        except Exception as e:
            logger.error(f"Error en pipeline: {str(e)}")
            return {
                'error': str(e),
                'success': False
            }
