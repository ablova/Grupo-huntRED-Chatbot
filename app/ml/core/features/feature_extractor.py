from typing import Dict, List, Optional, Tuple
from app.models import Person, Vacante
from app.ml.core.analyzers import BaseAnalyzer
from app.ml.core.models.base import BaseModel
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
        try:
            from app.ml.core.analyzers import SkillAnalyzer, CulturalFitAnalyzer
            
            # Inicializar analizadores
            self.skill_analyzer = SkillAnalyzer()
            self.cultural_fit_analyzer = CulturalFitAnalyzer()
            
            # Registrar analizadores
            self.register_analyzer('skills', self.skill_analyzer)
            self.register_analyzer('cultural_fit', self.cultural_fit_analyzer)
            
            logger.info("Analizadores inicializados correctamente")
            
        except Exception as e:
            logger.error(f"Error inicializando analizadores: {e}")
            raise

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
            # Extraer resultados por analizador
            skill_results = results[0]  # Resultados del SkillAnalyzer
            cultural_fit = results[1]  # Resultados del CulturalFitAnalyzer
            
            # Construir vector de características
            features = []
            
            # 1. Características de habilidades (512 dimensiones)
            features.extend(skill_results['embedding'])
            
            # 2. Métricas de ajuste cultural (8 dimensiones)
            features.append(cultural_fit['cultural_alignment'])
            features.append(cultural_fit['values_alignment'])
            features.append(cultural_fit['behavior_alignment'])
            features.append(cultural_fit['communication_alignment'])
            features.append(cultural_fit['team_alignment'])
            features.append(cultural_fit['leadership_alignment'])
            features.append(cultural_fit['workstyle_alignment'])
            features.append(cultural_fit['growth_alignment'])
            
            # 3. Características adicionales (6 dimensiones)
            features.append(person.years_of_experience / 50)  # Normalizado 0-1
            features.append(person.education_level / 5)  # Normalizado 0-1
            features.append(person.certifications_count / 10)  # Normalizado 0-1
            features.append(vacancy.required_experience / 10)  # Normalizado 0-1
            features.append(vacancy.required_education_level / 5)  # Normalizado 0-1
            features.append(vacancy.required_certifications_count / 10)  # Normalizado 0-1
            
            # Convertir a numpy array y normalizar
            features_array = np.array(features)
            features_array = (features_array - features_array.min()) / (features_array.max() - features_array.min())
            
            return features_array
            
        except Exception as e:
            logger.error(f"Error construyendo vector de características: {e}")
            return np.zeros(526)  # 512 + 8 + 6

    def _normalize_score(self, score: float) -> float:
        """
        Normaliza un puntaje a un rango de 0-1.
        
        Args:
            score: Puntaje a normalizar
            
        Returns:
            float: Puntaje normalizado
        """
        try:
            # Asegurar que el score esté en un rango válido
            score = max(0, min(1, score))
            return float(score)
            
        except Exception as e:
            logger.error(f"Error normalizando puntaje: {e}")
            return 0.0
