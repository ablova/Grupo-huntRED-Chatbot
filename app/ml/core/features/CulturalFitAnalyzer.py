"""
Análisis avanzado de ajuste cultural usando NLP y análisis de comportamiento.
"""

import logging
from typing import Dict, List, Tuple
import numpy as np
import tensorflow as tf
import tensorflow_hub as hub
from app.models import Person, Vacante, BusinessUnit

logger = logging.getLogger(__name__)

class CulturalFitAnalyzer:
    def __init__(self):
        """Inicializa el analizador de ajuste cultural."""
        self.embed = hub.load("https://tfhub.dev/google/universal-sentence-encoder/4")
        self.cultural_factors = [
            'communication_style', 'work_ethic', 'teamwork',
            'adaptability', 'values_alignment', 'leadership_style'
        ]
        self._initialize_model()

    def _initialize_model(self):
        """Inicializa el modelo de análisis cultural."""
        self.model = tf.keras.Sequential([
            tf.keras.layers.Input(shape=(512,)),  # Dimensión de USE
            tf.keras.layers.Dense(256, activation='relu'),
            tf.keras.layers.Dropout(0.3),
            tf.keras.layers.Dense(128, activation='relu'),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.Dense(len(self.cultural_factors), activation='sigmoid')
        ])
        self.model.compile(
            optimizer='adam',
            loss='binary_crossentropy',
            metrics=['accuracy']
        )

    def analyze_cultural_fit(self, person: Person, vacancy: Vacante) -> Dict[str, float]:
        """
        Analiza el ajuste cultural entre un candidato y una vacante.
        
        Args:
            person: Objeto Person
            vacancy: Objeto Vacante
            
        Returns:
            Dict: Diccionario con factores culturales y sus puntajes
        """
        try:
            # Crear texto combinado para análisis
            text = f"{person.personality_text} {vacancy.culture_text}"
            
            # Obtener embedding
            embedding = self.embed([text])[0].numpy()
            
            # Predecir factores culturales
            predictions = self.model.predict(np.array([embedding]))[0]
            
            # Convertir a diccionario
            cultural_scores = dict(zip(self.cultural_factors, predictions))
            
            return cultural_scores
            
        except Exception as e:
            logger.error(f"Error analizando ajuste cultural: {e}")
            return {factor: 0.5 for factor in self.cultural_factors}

    def calculate_cultural_score(self, person: Person, vacancy: Vacante) -> float:
        """
        Calcula un puntaje global de ajuste cultural.
        
        Args:
            person: Objeto Person
            vacancy: Objeto Vacante
            
        Returns:
            float: Puntaje de ajuste cultural (0-1)
        """
        try:
            # Obtener análisis detallado
            cultural_scores = self.analyze_cultural_fit(person, vacancy)
            
            # Calcular puntaje promedio ponderado
            weights = {
                'communication_style': 0.2,
                'work_ethic': 0.2,
                'teamwork': 0.2,
                'adaptability': 0.15,
                'values_alignment': 0.15,
                'leadership_style': 0.1
            }
            
            total_score = sum(
                cultural_scores[factor] * weights[factor]
                for factor in self.cultural_factors
            )
            
            return max(0.0, min(1.0, total_score))
            
        except Exception as e:
            logger.error(f"Error calculando puntaje cultural: {e}")
            return 0.5
