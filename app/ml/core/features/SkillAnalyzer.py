"""
Análisis avanzado de habilidades usando transformers y análisis semántico.
"""

import logging
from typing import Dict, List, Tuple
import numpy as np
import tensorflow as tf
import tensorflow_hub as hub
from sklearn.preprocessing import MultiLabelBinarizer
from app.models import Person, Vacante

logger = logging.getLogger(__name__)

class SkillAnalyzer:
    def __init__(self):
        """Inicializa el analizador de habilidades."""
        self.embed = hub.load("https://tfhub.dev/google/universal-sentence-encoder/4")
        self.mlb = MultiLabelBinarizer()
        self.skill_categories = [
            'technical', 'soft', 'management', 'communication',
            'analytical', 'creative', 'leadership', 'strategic'
        ]
        self._initialize_model()

    def _initialize_model(self):
        """Inicializa el modelo de análisis de habilidades."""
        self.model = tf.keras.Sequential([
            tf.keras.layers.Input(shape=(512,)),  # Dimensión de USE
            tf.keras.layers.Dense(256, activation='relu'),
            tf.keras.layers.Dropout(0.3),
            tf.keras.layers.Dense(128, activation='relu'),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.Dense(len(self.skill_categories), activation='sigmoid')
        ])
        self.model.compile(
            optimizer='adam',
            loss='binary_crossentropy',
            metrics=['accuracy']
        )

    def analyze_skills(self, text: str) -> Dict[str, float]:
        """
        Analiza el texto para extraer y categorizar habilidades.
        
        Args:
            text: Texto a analizar
            
        Returns:
            Dict: Diccionario con categorías de habilidades y sus puntajes
        """
        try:
            # Obtener embedding
            embedding = self.embed([text])[0].numpy()
            
            # Predecir categorías de habilidades
            predictions = self.model.predict(np.array([embedding]))[0]
            
            # Convertir a diccionario
            skill_scores = dict(zip(self.skill_categories, predictions))
            
            return skill_scores
            
        except Exception as e:
            logger.error(f"Error analizando habilidades: {e}")
            return {cat: 0.0 for cat in self.skill_categories}

    def get_skill_overlap(self, person: Person, vacancy: Vacante) -> float:
        """
        Calcula el nivel de coincidencia de habilidades entre un candidato y una vacante.
        
        Args:
            person: Objeto Person
            vacancy: Objeto Vacante
            
        Returns:
            float: Puntaje de coincidencia (0-1)
        """
        try:
            # Analizar habilidades del candidato
            person_skills = self.analyze_skills(person.skills_text)
            
            # Analizar habilidades requeridas en la vacante
            vacancy_skills = self.analyze_skills(vacancy.skills_text)
            
            # Calcular coincidencia
            overlap = sum(
                min(person_skills[cat], vacancy_skills[cat])
                for cat in self.skill_categories
            ) / len(self.skill_categories)
            
            return max(0.0, min(1.0, overlap))
            
        except Exception as e:
            logger.error(f"Error calculando coincidencia de habilidades: {e}")
            return 0.0
