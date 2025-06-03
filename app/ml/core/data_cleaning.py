"""
Módulo para la limpieza y preprocesamiento de datos en el sistema ML.
"""

import re
import string
from typing import List, Dict, Any
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from app.ml.ml_config import ML_CONFIG


class DataCleaner:
    """Clase para limpiar y preprocesar datos."""

    def __init__(self):
        self.scaler = StandardScaler()
        self.imputer = SimpleImputer(strategy='mean')
        self.stopwords = set()
        self.load_stopwords()

    def load_stopwords(self):
        """Carga palabras stopwords para procesamiento de texto."""
        try:
            # Cargar stopwords desde archivo o configuración
            self.stopwords.update([
                'y', 'o', 'en', 'de', 'la', 'el', 'los', 'las', 'un', 'una',
                'con', 'para', 'por', 'que', 'se', 'su', 'sus', 'al', 'del'
            ])
        except Exception as e:
            logger.warning(f"Error cargando stopwords: {str(e)}")

    def clean_text(self, text: str) -> str:
        """Limpia texto eliminando caracteres especiales y stopwords."""
        if not text:
            return ""

        # Convertir a minúsculas
        text = text.lower()

        # Eliminar puntuación
        text = text.translate(str.maketrans('', '', string.punctuation))

        # Eliminar números
        text = re.sub(r'\d+', '', text)

        # Eliminar espacios extra
        text = re.sub(r'\s+', ' ', text).strip()

        # Eliminar stopwords
        words = [word for word in text.split() if word not in self.stopwords]
        
        return ' '.join(words)

    def clean_skills(self, skills_text: str) -> List[str]:
        """Limpia y normaliza texto de habilidades."""
        if not skills_text:
            return []

        # Separar por comas, puntos y espacios
        skills = re.split(r'[\s,;]+', skills_text)
        
        # Limpiar cada skill
        cleaned_skills = []
        for skill in skills:
            cleaned = self.clean_text(skill)
            if cleaned:
                cleaned_skills.append(cleaned)

        return cleaned_skills

    def clean_experience(self, experience: float) -> float:
        """Limpia y normaliza años de experiencia."""
        if pd.isna(experience) or experience < 0:
            return ML_CONFIG['PREDICTION']['MIN_EXPERIENCE']
        return min(experience, ML_CONFIG['PREDICTION']['MAX_EXPERIENCE'])

    def clean_salary(self, salary: float) -> float:
        """Limpia y normaliza rangos de salario."""
        if pd.isna(salary) or salary < 0:
            return ML_CONFIG['PREDICTION']['MIN_SALARY']
        return min(salary, ML_CONFIG['PREDICTION']['MAX_SALARY'])

    def clean_location_score(self, score: float) -> float:
        """Normaliza puntaje de ubicación."""
        return min(max(score, 0.0), 1.0)

    def clean_education_level(self, level: int) -> int:
        """Normaliza nivel educativo."""
        if pd.isna(level) or level < 0:
            return ML_CONFIG['PREDICTION']['MIN_EDUCATION']
        return min(level, ML_CONFIG['PREDICTION']['MAX_EDUCATION'])

    def clean_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Limpia un conjunto de datos completo."""
        cleaned = data.copy()
        
        # Limpiar texto
        cleaned['skills_text'] = self.clean_text(cleaned.get('skills_text', ''))
        cleaned['description'] = self.clean_text(cleaned.get('description', ''))
        
        # Limpiar habilidades
        cleaned['skills'] = self.clean_skills(cleaned.get('skills_text', ''))
        
        # Limpiar valores numéricos
        cleaned['years_of_experience'] = self.clean_experience(cleaned.get('years_of_experience', 0))
        cleaned['salary_range'] = self.clean_salary(cleaned.get('salary_range', 0))
        cleaned['location_score'] = self.clean_location_score(cleaned.get('location_score', 0))
        cleaned['education_level'] = self.clean_education_level(cleaned.get('education_level', 0))
        
        return cleaned

    def transform_features(self, features: pd.DataFrame) -> pd.DataFrame:
        """Transforma características numéricas usando escalado y imputación."""
        # Imputar valores faltantes
        features_imputed = pd.DataFrame(
            self.imputer.fit_transform(features),
            columns=features.columns
        )
        
        # Escalar características
        features_scaled = pd.DataFrame(
            self.scaler.fit_transform(features_imputed),
            columns=features.columns
        )
        
        return features_scaled

    def get_feature_importance(self, model, feature_names: List[str]) -> Dict[str, float]:
        """Obtiene importancia de características desde el modelo."""
        try:
            importance = model.feature_importances_
            return dict(zip(feature_names, importance))
        except AttributeError:
            logger.warning("El modelo no tiene atributo feature_importances_")
            return {}

    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Valida la integridad de los datos."""
        required_fields = [
            'skills_text', 'years_of_experience', 'education_level',
            'salary_range', 'location_score', 'description'
        ]
        
        return all(field in data for field in required_fields)
