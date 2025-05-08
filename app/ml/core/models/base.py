from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod
import numpy as np
from app.models import Person, Vacante

class BaseModel(ABC):
    """
    Clase base para todos los modelos del sistema ATS AI.
    
    Esta clase proporciona una interfaz común para todos los modelos,
    asegurando consistencia y facilitando la extensibilidad.
    """
    
    @abstractmethod
    def train(self, X: np.ndarray, y: np.ndarray, **kwargs) -> None:
        """
        Entrena el modelo con los datos proporcionados.
        
        Args:
            X: Características de entrada
            y: Etiquetas objetivo
            **kwargs: Parámetros adicionales para el entrenamiento
        """
        pass

    @abstractmethod
    def predict(self, *args, **kwargs) -> Any:
        """
        Realiza predicciones usando el modelo entrenado.
        
        Args:
            *args: Argumentos posicionales
            **kwargs: Argumentos de palabra clave
            
        Returns:
            Any: Resultados de la predicción
        """
        pass

    def evaluate(self, X: np.ndarray, y: np.ndarray) -> Dict[str, float]:
        """
        Evalúa el rendimiento del modelo.
        
        Args:
            X: Características de entrada
            y: Etiquetas objetivo
            
        Returns:
            Dict[str, float]: Métricas de evaluación
        """
        raise NotImplementedError("Este método debe ser implementado por las subclases")

    def save(self, filepath: str) -> None:
        """
        Guarda el modelo en el archivo especificado.
        
        Args:
            filepath: Ruta donde guardar el modelo
        """
        raise NotImplementedError("Este método debe ser implementado por las subclases")

    def load(self, filepath: str) -> None:
        """
        Carga el modelo desde el archivo especificado.
        
        Args:
            filepath: Ruta del archivo del modelo
        """
        raise NotImplementedError("Este método debe ser implementado por las subclases")

    def get_feature_importance(self) -> Dict[str, float]:
        """
        Obtiene la importancia de las características.
        
        Returns:
            Dict[str, float]: Importancia de cada característica
        """
        raise NotImplementedError("Este método debe ser implementado por las subclases")
