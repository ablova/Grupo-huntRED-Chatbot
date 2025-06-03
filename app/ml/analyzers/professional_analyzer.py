# /home/pablo/app/ml/analyzers/professional_analyzer.py
"""
Analizador profesional para Grupo huntRED®.

Este módulo implementa el análisis de competencias y habilidades profesionales.
"""
import logging
from typing import Dict, Any, List
import numpy as np
from django.core.cache import cache
from pathlib import Path

from ai_huntred import settings
from app.ml.analyzers.base_analyzer import BaseAnalyzer
from app.ml.core.models.base import MatchmakingLearningSystem

logger = logging.getLogger(__name__)

class ProfessionalAnalyzer(BaseAnalyzer):
    """
    Analizador de perfil profesional basado en habilidades y experiencia.
    """
    
    def __init__(self):
        super().__init__()
        self.model = MatchmakingLearningSystem()
        
    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analiza los datos profesionales y retorna un perfil.
        
        Args:
            data: Diccionario con los datos profesionales
            
        Returns:
            Dict con el perfil profesional
        """
        try:
            # Extraer habilidades y experiencia
            skills = self._extract_skills(data)
            experience = self._extract_experience(data)
            
            # Calcular nivel profesional
            professional_level = self._calculate_professional_level(skills, experience)
            
            # Generar recomendaciones
            recommendations = self._generate_recommendations(skills, experience)
            
            return {
                'skills': skills,
                'experience': experience,
                'professional_level': professional_level,
                'recommendations': recommendations,
                'score': self._calculate_score(skills, experience)
            }
            
        except Exception as e:
            logger.error(f"Error analizando perfil profesional: {str(e)}")
            return {
                'error': str(e),
                'status': 'error'
            }
            
    def _extract_skills(self, data: Dict[str, Any]) -> Dict[str, float]:
        """
        Extrae las habilidades del perfil.
        """
        skills = {}
        
        # Extraer habilidades técnicas
        technical_skills = data.get('technical_skills', {})
        for skill, level in technical_skills.items():
            skills[f'technical_{skill}'] = float(level)
            
        # Extraer habilidades blandas
        soft_skills = data.get('soft_skills', {})
        for skill, level in soft_skills.items():
            skills[f'soft_{skill}'] = float(level)
            
        return skills
        
    def _extract_experience(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extrae la experiencia profesional.
        """
        experience = {
            'years': data.get('years_experience', 0),
            'roles': data.get('previous_roles', []),
            'industries': data.get('industries', []),
            'projects': data.get('projects', [])
        }
        
        return experience
        
    def _calculate_professional_level(self, skills: Dict[str, float], 
                                   experience: Dict[str, Any]) -> str:
        """
        Calcula el nivel profesional basado en habilidades y experiencia.
        """
        try:
            # Calcular score promedio de habilidades
            skill_scores = list(skills.values())
            avg_skill_score = sum(skill_scores) / len(skill_scores) if skill_scores else 0
            
            # Determinar nivel basado en experiencia y habilidades
            years = experience.get('years', 0)
            
            if years >= 10 and avg_skill_score >= 0.8:
                return 'Senior'
            elif years >= 5 and avg_skill_score >= 0.6:
                return 'Mid-Level'
            elif years >= 2 and avg_skill_score >= 0.4:
                return 'Junior'
            else:
                return 'Entry-Level'
                
        except Exception as e:
            logger.error(f"Error calculando nivel profesional: {str(e)}")
            return 'Entry-Level'
            
    def _generate_recommendations(self, skills: Dict[str, float], 
                                experience: Dict[str, Any]) -> List[str]:
        """
        Genera recomendaciones basadas en el perfil profesional.
        """
        try:
            return self.model.generate_professional_recommendations(skills, experience)
        except Exception as e:
            logger.error(f"Error generando recomendaciones profesionales: {str(e)}")
            return []
            
    def _calculate_score(self, skills: Dict[str, float], 
                        experience: Dict[str, Any]) -> float:
        """
        Calcula un score general del perfil profesional.
        """
        try:
            return self.model.calculate_professional_score(skills, experience)
        except Exception as e:
            logger.error(f"Error calculando score profesional: {str(e)}")
            return 0.0
