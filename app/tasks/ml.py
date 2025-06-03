"""
Tareas asíncronas relacionadas con procesamiento de Machine Learning.
Este módulo centraliza todas las tareas de análisis, procesamiento de datos y predicciones.
"""
from celery import shared_task
import logging
from django.conf import settings
import time
from asgiref.sync import async_to_sync
import os
import json

logger = logging.getLogger(__name__)

@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={'max_retries': 3},
    queue='ml'
)
def update_embeddings(self, model_name="default", force_update=False):
    """
    Actualiza los embeddings del modelo ML para mejorar las coincidencias.
    
    Args:
        model_name (str): Nombre del modelo a actualizar
        force_update (bool): Si True, regenera todos los embeddings aunque estén actualizados
        
    Returns:
        dict: Estadísticas de la actualización
    """
    from app.ats.ml.core.models.base import ModelManager
    
    logger.info(f"Updating embeddings for model {model_name}, force={force_update}")
    start_time = time.time()
    
    try:
        model_manager = ModelManager()
        stats = async_to_sync(model_manager.update_embeddings)(model_name, force_update)
        
        processing_time = time.time() - start_time
        logger.info(f"Embeddings updated in {processing_time:.2f}s. Stats: {stats}")
        
        return {
            "success": True,
            "model_name": model_name,
            "processing_time": processing_time,
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Error updating embeddings: {str(e)}", exc_info=True)
        self.retry(exc=e)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={'max_retries': 2},
    queue='ml'
)
def process_matching(self, vacancy_id=None, candidate_ids=None, limit=50, threshold=0.65):
    """
    Procesa coincidencias entre vacantes y candidatos utilizando los modelos ML.
    
    Args:
        vacancy_id (int): ID de la vacante a evaluar (None = todas las vacantes activas)
        candidate_ids (list): Lista de IDs de candidatos a evaluar (None = todos los candidatos activos)
        limit (int): Número máximo de coincidencias a retornar
        threshold (float): Umbral mínimo de confianza para considerar una coincidencia
        
    Returns:
        dict: Resultados de las coincidencias
    """
    from app.ats.ml.core.models.matchmaking.matchmaking import MatchMakingEngine
    
    logger.info(f"Processing matching for vacancy_id={vacancy_id}, candidates={len(candidate_ids) if candidate_ids else 'all'}")
    start_time = time.time()
    
    try:
        engine = MatchMakingEngine()
        matches = async_to_sync(engine.process_matching)(
            vacancy_id=vacancy_id,
            candidate_ids=candidate_ids,
            limit=limit,
            threshold=threshold
        )
        
        processing_time = time.time() - start_time
        logger.info(f"Matching completed in {processing_time:.2f}s. Found {len(matches)} matches.")
        
        return {
            "success": True,
            "vacancy_id": vacancy_id,
            "matches_count": len(matches),
            "processing_time": processing_time,
            "matches": matches
        }
    except Exception as e:
        logger.error(f"Error processing matching: {str(e)}", exc_info=True)
        self.retry(exc=e)


@shared_task(
    bind=True,
    time_limit=3600,  # 1 hora máximo
    soft_time_limit=3300,  # 55 minutos
    queue='ml_training'
)
def train_model(self, model_name, parameters=None, dataset_ids=None):
    """
    Entrena o reentrenar un modelo ML con nuevos datos.
    
    Args:
        model_name (str): Nombre del modelo a entrenar
        parameters (dict): Parámetros específicos para el entrenamiento
        dataset_ids (list): IDs de conjuntos de datos a utilizar (None = usar todos)
        
    Returns:
        dict: Métricas y estado del entrenamiento
    """
    from app.ats.ml.core.models.base import ModelManager
    
    logger.info(f"Starting training for model {model_name}")
    start_time = time.time()
    
    parameters = parameters or {}
    checkpoint_dir = os.path.join(settings.ML_CHECKPOINTS_DIR, model_name)
    os.makedirs(checkpoint_dir, exist_ok=True)
    
    try:
        # Iniciar entrenamiento con puntos de control
        model_manager = ModelManager()
        training_result = async_to_sync(model_manager.train_model)(
            model_name=model_name,
            parameters=parameters,
            dataset_ids=dataset_ids,
            checkpoint_dir=checkpoint_dir
        )
        
        processing_time = time.time() - start_time
        logger.info(f"Training completed in {processing_time:.2f}s. Metrics: {training_result.get('metrics')}")
        
        # Almacenar resultados del entrenamiento
        result_path = os.path.join(checkpoint_dir, f"training_result_{int(time.time())}.json")
        with open(result_path, 'w') as f:
            json.dump(training_result, f, indent=2)
        
        return {
            "success": True,
            "model_name": model_name,
            "processing_time": processing_time,
            "metrics": training_result.get('metrics'),
            "model_path": training_result.get('model_path')
        }
    except Exception as e:
        logger.error(f"Error training model: {str(e)}", exc_info=True)
        
        # Guardar estado del error para diagnóstico posterior
        error_path = os.path.join(checkpoint_dir, f"training_error_{int(time.time())}.json")
        with open(error_path, 'w') as f:
            json.dump({
                "error": str(e),
                "model_name": model_name,
                "parameters": parameters,
                "timestamp": int(time.time())
            }, f, indent=2)
        
        self.retry(exc=e)


@shared_task(queue='ml')
def optimize_model_performance(model_name, target_metric="accuracy", target_threshold=0.85):
    """
    Optimiza el rendimiento de un modelo existente sin reentrenamiento completo.
    
    Args:
        model_name (str): Nombre del modelo a optimizar
        target_metric (str): Métrica objetivo para optimización
        target_threshold (float): Umbral objetivo para la métrica
        
    Returns:
        dict: Resultados de la optimización
    """
    from app.ats.ml.core.optimizers.PerformanceOptimizer import PerformanceOptimizer
    
    logger.info(f"Optimizing model {model_name} for {target_metric}")
    start_time = time.time()
    
    try:
        optimizer = PerformanceOptimizer()
        result = async_to_sync(optimizer.optimize)(
            model_name=model_name,
            target_metric=target_metric,
            target_threshold=target_threshold
        )
        
        processing_time = time.time() - start_time
        improvement = result.get('improvement', 0)
        
        logger.info(f"Optimization completed in {processing_time:.2f}s. "
                   f"Improvement: {improvement:.2%} on {target_metric}")
        
        return {
            "success": True,
            "model_name": model_name,
            "processing_time": processing_time,
            "target_metric": target_metric,
            "initial_value": result.get('initial_value'),
            "final_value": result.get('final_value'),
            "improvement": improvement
        }
    except Exception as e:
        logger.error(f"Error optimizing model: {str(e)}", exc_info=True)
        raise
