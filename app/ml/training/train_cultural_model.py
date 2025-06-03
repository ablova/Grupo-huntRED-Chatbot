"""
Script para entrenar y evaluar el modelo de compatibilidad cultural.

Este script carga datos históricos, entrena el modelo y evalúa su rendimiento.
"""
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from pathlib import Path
import logging
import sys
import os

# Añadir el directorio raíz al path
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.ml.models.cultural_fit_model import CulturalFitModel
from app.ml.data.data_loader import DataLoader

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def prepare_data(data: pd.DataFrame) -> tuple:
    """
    Prepara los datos para el entrenamiento.
    
    Args:
        data: DataFrame con los datos históricos
        
    Returns:
        Tupla con características y etiquetas
    """
    # Definir columnas de características
    feature_columns = [
        'innovation',
        'collaboration',
        'adaptability',
        'results_orientation',
        'customer_focus',
        'integrity',
        'diversity',
        'learning'
    ]
    
    # Extraer características y etiquetas
    X = data[feature_columns].values
    y = data['compatibility_score'].values
    
    return X, y

def train_and_evaluate():
    """
    Entrena y evalúa el modelo de compatibilidad cultural.
    """
    try:
        # Cargar datos
        logger.info("Cargando datos...")
        data_loader = DataLoader()
        data = data_loader.load_cultural_data()
        
        if data is None or data.empty:
            logger.error("No se pudieron cargar los datos")
            return
            
        # Preparar datos
        X, y = prepare_data(data)
        
        # Dividir en conjuntos de entrenamiento y prueba
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Crear y entrenar modelo
        logger.info("Entrenando modelo...")
        model = CulturalFitModel()
        model.train(X_train, y_train)
        
        # Evaluar modelo
        logger.info("Evaluando modelo...")
        metrics = model.evaluate(X_test, y_test)
        
        # Mostrar resultados
        logger.info("Resultados de la evaluación:")
        for metric, value in metrics.items():
            logger.info(f"{metric}: {value:.4f}")
            
        # Obtener importancia de características
        feature_importance = model.get_feature_importance()
        logger.info("\nImportancia de características:")
        for feature, importance in sorted(
            feature_importance.items(),
            key=lambda x: x[1],
            reverse=True
        ):
            logger.info(f"{feature}: {importance:.4f}")
            
        # Guardar modelo
        model_path = Path(__file__).parent.parent / "models" / "cultural_fit_model.joblib"
        logger.info(f"Guardando modelo en {model_path}")
        model.save(str(model_path))
        
        logger.info("¡Entrenamiento completado exitosamente!")
        
    except Exception as e:
        logger.error(f"Error durante el entrenamiento: {str(e)}")
        raise

if __name__ == "__main__":
    train_and_evaluate() 