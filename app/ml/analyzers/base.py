from typing import Dict, Any
from abc import ABC, abstractmethod
from app.models import Person, Vacante

class BaseAnalyzer(ABC):
    """
    Interfaz base para todos los analizadores del sistema ATS AI.
    
    Este analizador proporciona una interfaz común para todos los analizadores
    del sistema, asegurando consistencia y facilitando la extensibilidad.
    """
    
    @abstractmethod
    def analyze(self, *args, **kwargs) -> Dict[str, float]:
        """
        Analiza los datos de entrada y devuelve un diccionario de resultados.
        
        Args:
            *args: Argumentos posicionales
            **kwargs: Argumentos de palabra clave
            
        Returns:
            Dict[str, float]: Diccionario con los resultados del análisis
        """
        pass

    def _normalize_score(self, score: float) -> float:
        """
        Normaliza un puntaje a un rango de 0-1.
        
        Args:
            score: Puntaje a normalizar
            
        Returns:
            float: Puntaje normalizado
        """
        return max(0, min(1, score))

    def _calculate_weighted_average(self, scores: Dict[str, float], weights: Dict[str, float]) -> float:
        """
        Calcula el promedio ponderado de un conjunto de puntajes.
        
        Args:
            scores: Diccionario de puntajes
            weights: Diccionario de pesos
            
        Returns:
            float: Promedio ponderado
        """
        total = sum(weights.values())
        weighted_sum = sum(score * weights[key] for key, score in scores.items())
        return weighted_sum / total if total > 0 else 0.0
