from typing import Dict, List, Optional, Tuple
from app.models import Person, Vacante
from app.ml.core.analyzers import BaseAnalyzer
from app.ml.core.models import BaseModel
from app.ml.core.utils import DistributedCache
from app.ml.core.scheduling import AsyncProcessor
import numpy as np
import logging

logger = logging.getLogger(__name__)

class FeatureExtractor:
    """
    Sistema de extracción de características para el ATS AI.
    
    Este sistema coordina múltiples analizadores para extraer características
    relevantes para el matchmaking y análisis predictivo.
    """
    
    def __init__(self, cache: DistributedCache, async_processor: AsyncProcessor):
        """
        Inicializa el sistema de extracción de características.
        
        Args:
            cache: Sistema de caché distribuido
            async_processor: Procesador asíncrono para análisis paralelo
        """
        self.cache = cache
        self.async_processor = async_processor
        self.analyzers = {}
        self._initialize_analyzers()

    def _initialize_analyzers(self) -> None:
        """
        Inicializa los analizadores disponibles.
        """
        # Implementar inicialización de analizadores
        pass

    def register_analyzer(self, name: str, analyzer: BaseAnalyzer) -> None:
        """
        Registra un nuevo analizador.
        
        Args:
            name: Nombre del analizador
            analyzer: Instancia del analizador
        """
        self.analyzers[name] = analyzer

    def extract_features(self, person: Person, vacancy: Vacante) -> np.ndarray:
        """
        Extrae características para el modelo usando múltiples fuentes de análisis.
        
        Args:
            person: Objeto Person
            vacancy: Objeto Vacante
            
        Returns:
            np.ndarray: Vector de características
        """
        try:
            # Verificar cache distribuido
            cache_key = f"features_{person.id}_{vacancy.id}"
            cached_features = self.cache.get(cache_key)
            if cached_features is not None:
                return cached_features
                
            # Preparar tareas de análisis
            tasks = []
            for analyzer_name, analyzer in self.analyzers.items():
                if hasattr(analyzer, 'analyze_skills'):
                    tasks.append((analyzer.analyze_skills, person.skills_text))
                elif hasattr(analyzer, 'analyze_cultural_fit'):
                    tasks.append((analyzer.analyze_cultural_fit, person, vacancy))
                elif hasattr(analyzer, 'predict'):
                    tasks.append((analyzer.predict, vacancy))
                elif hasattr(analyzer, 'get_current_trends'):
                    tasks.append((analyzer.get_current_trends,))
            
            # Ejecutar análisis en paralelo
            results = self.async_processor.process(tasks)
            
            # Construir vector de características
            features_vector = self._build_feature_vector(results, person, vacancy)
            
            # Almacenar en caché
            self.cache.set(cache_key, features_vector)
            
            return features_vector
            
        except Exception as e:
            logger.error(f"Error extrayendo características: {e}")
            return np.zeros(14)

    def _build_feature_vector(self, results: List, person: Person, vacancy: Vacante) -> np.ndarray:
        """
        Construye el vector de características final a partir de los resultados de análisis.
        
        Args:
            results: Lista de resultados de los analizadores
            person: Objeto Person
            vacancy: Objeto Vacante
            
        Returns:
            np.ndarray: Vector de características completo
        """
        try:
            # Extraer características numéricas
            features = [
                self._normalize_score(sum(results[0].values()) / len(results[0])),  # Puntaje de habilidades
                self._normalize_score(sum(results[1].values()) / len(results[1])),  # Puntaje cultural
                results[2],  # Predicción de tiempo de contratación
                results[3],  # Riesgo de rotación
                self._normalize_score(person.years_of_experience),  # Años de experiencia
                self._normalize_score(person.education_level),  # Nivel educativo
                self._normalize_score(vacancy.salary_range),  # Rango salarial
                self._normalize_score(vacancy.required_experience),  # Experiencia requerida
                self._normalize_score(vacancy.required_education),  # Educación requerida
                self._normalize_score(vacancy.location_score),  # Puntaje de ubicación
                self._normalize_score(results[4]['demand'].get(vacancy.industry, 1.0)),  # Demanda del sector
                self._normalize_score(results[4]['salary'].get(vacancy.level, 1.0)),  # Tendencia salarial
                self._normalize_score(results[4]['skills'].get(vacancy.main_skill, 1.0)),  # Tendencia de habilidades
                self._normalize_score(results[4]['locations'].get(vacancy.location, 1.0))  # Tendencia geográfica
            ]
            
            return np.array(features)
            
        except Exception as e:
            logger.error(f"Error construyendo vector de características: {e}")
            return np.zeros(14)

    def _normalize_score(self, score: float) -> float:
        """
        Normaliza un puntaje a un rango de 0-1.
        
        Args:
            score: Puntaje a normalizar
            
        Returns:
            float: Puntaje normalizado
        """
        return max(0, min(1, score))
