# /home/pablo/app/ml/analyzers/cultural_analyzer.py
"""
Analizador de compatibilidad cultural.

Este módulo implementa el análisis de compatibilidad cultural entre
candidatos y empresas basado en dimensiones culturales.
"""
import logging
from typing import Dict, List, Any, Optional
import numpy as np
from pathlib import Path

from app.ml.core.models.assessments.cultural_fit_model import CulturalFitModel
from sklearn.preprocessing import MinMaxScaler

logger = logging.getLogger(__name__)

class CulturalAnalyzer:
    """
    Analizador de compatibilidad cultural que utiliza modelos de ML
    para evaluar y generar recomendaciones.
    """
    
    def __init__(self):
        self.model = CulturalFitModel()
        self.scaler = MinMaxScaler()
        
    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analiza las respuestas culturales y genera insights.
        
        Args:
            data: Diccionario con respuestas y preguntas
            
        Returns:
            Diccionario con resultados del análisis
        """
        try:
            # Extraer dimensiones y respuestas
            dimensions = self._extract_dimensions(data['questions'])
            responses = data['responses']
            
            # Calcular puntuaciones por dimensión
            dimension_scores = self._calculate_dimension_scores(dimensions, responses)
            
            # Generar predicción de compatibilidad
            compatibility_score = self._predict_compatibility(dimension_scores)
            
            # Generar insights
            insights = self._generate_insights(dimension_scores)
            
            # Generar recomendaciones
            recommendations = self._generate_recommendations(dimension_scores, compatibility_score)
            
            return {
                'dimension_scores': dimension_scores,
                'compatibility_score': compatibility_score,
                'insights': insights,
                'recommendations': recommendations
            }
            
        except Exception as e:
            logger.error(f"Error en análisis cultural: {str(e)}")
            return {
                'error': True,
                'message': f"Error en análisis: {str(e)}"
            }
    
    def _extract_dimensions(self, questions: List[Dict]) -> Dict[str, List[str]]:
        """
        Extrae las dimensiones y sus preguntas asociadas.
        
        Args:
            questions: Lista de preguntas con sus dimensiones
            
        Returns:
            Diccionario con dimensiones y sus preguntas
        """
        dimensions = {}
        for question in questions:
            dimension = question['dimension']
            if dimension not in dimensions:
                dimensions[dimension] = []
            dimensions[dimension].append(question['id'])
        return dimensions
    
    def _calculate_dimension_scores(self, 
                                  dimensions: Dict[str, List[str]], 
                                  responses: Dict[str, int]) -> Dict[str, float]:
        """
        Calcula las puntuaciones por dimensión.
        
        Args:
            dimensions: Dimensiones y sus preguntas
            responses: Respuestas del usuario
            
        Returns:
            Diccionario con puntuaciones por dimensión
        """
        scores = {}
        for dimension, question_ids in dimensions.items():
            # Obtener respuestas para esta dimensión
            dimension_responses = [
                responses[q_id] for q_id in question_ids 
                if q_id in responses
            ]
            
            if dimension_responses:
                # Calcular promedio normalizado (0-100)
                avg_score = np.mean(dimension_responses)
                normalized_score = (avg_score - 1) * 25  # Convertir de 1-5 a 0-100
                scores[dimension] = round(normalized_score, 1)
            else:
                scores[dimension] = 0.0
                
        return scores
    
    def _predict_compatibility(self, dimension_scores: Dict[str, float]) -> float:
        """
        Predice la compatibilidad cultural general.
        
        Args:
            dimension_scores: Puntuaciones por dimensión
            
        Returns:
            Puntuación de compatibilidad (0-100)
        """
        try:
            # Preparar datos para el modelo
            features = np.array([list(dimension_scores.values())])
            features_scaled = self.scaler.fit_transform(features)
            
            # Obtener predicción
            prediction = self.model.predict(features_scaled)
            
            # Convertir a escala 0-100
            compatibility = float(prediction[0] * 100)
            return round(compatibility, 1)
            
        except Exception as e:
            logger.error(f"Error en predicción de compatibilidad: {str(e)}")
            # Si hay error, calcular promedio simple
            return round(np.mean(list(dimension_scores.values())), 1)
    
    def _generate_insights(self, dimension_scores: Dict[str, float]) -> List[str]:
        """
        Genera insights basados en las puntuaciones.
        
        Args:
            dimension_scores: Puntuaciones por dimensión
            
        Returns:
            Lista de insights
        """
        insights = []
        
        # Analizar fortalezas (puntuaciones altas)
        strengths = [
            (dim, score) for dim, score in dimension_scores.items()
            if score >= 75
        ]
        if strengths:
            strength_text = ", ".join(
                f"{dim.replace('_', ' ').title()}" 
                for dim, _ in sorted(strengths, key=lambda x: x[1], reverse=True)
            )
            insights.append(f"Tus fortalezas culturales incluyen: {strength_text}")
        
        # Analizar áreas de desarrollo (puntuaciones bajas)
        areas = [
            (dim, score) for dim, score in dimension_scores.items()
            if score < 50
        ]
        if areas:
            area_text = ", ".join(
                f"{dim.replace('_', ' ').title()}" 
                for dim, _ in sorted(areas, key=lambda x: x[1])
            )
            insights.append(f"Áreas de desarrollo cultural: {area_text}")
        
        # Analizar balance
        if len(strengths) > len(areas):
            insights.append("Tienes un perfil cultural bien balanceado con más fortalezas que áreas de desarrollo")
        elif len(areas) > len(strengths):
            insights.append("Tu perfil cultural muestra más áreas de desarrollo que fortalezas")
        else:
            insights.append("Tu perfil cultural muestra un balance entre fortalezas y áreas de desarrollo")
        
        return insights
    
    def _generate_recommendations(self, 
                                dimension_scores: Dict[str, float],
                                compatibility_score: float) -> List[str]:
        """
        Genera recomendaciones personalizadas.
        
        Args:
            dimension_scores: Puntuaciones por dimensión
            compatibility_score: Puntuación de compatibilidad general
            
        Returns:
            Lista de recomendaciones
        """
        recommendations = []
        
        # Recomendaciones basadas en compatibilidad general
        if compatibility_score >= 80:
            recommendations.append(
                "Tu perfil cultural muestra una alta compatibilidad con nuestra organización. "
                "Te recomendamos explorar roles que te permitan maximizar tus fortalezas culturales."
            )
        elif compatibility_score >= 60:
            recommendations.append(
                "Tu perfil cultural muestra una compatibilidad moderada. "
                "Considera desarrollar las áreas identificadas para mejorar tu adaptación cultural."
            )
        else:
            recommendations.append(
                "Tu perfil cultural muestra áreas de mejora significativas. "
                "Te recomendamos trabajar en el desarrollo de las competencias culturales clave."
            )
        
        # Recomendaciones específicas por dimensión
        for dimension, score in dimension_scores.items():
            if score < 50:
                recommendations.append(
                    self._get_dimension_recommendation(dimension, score)
                )
        
        return recommendations
    
    def _get_dimension_recommendation(self, dimension: str, score: float) -> str:
        """
        Obtiene una recomendación específica para una dimensión.
        
        Args:
            dimension: Dimensión cultural
            score: Puntuación de la dimensión
            
        Returns:
            Recomendación personalizada
        """
        recommendations = {
            'innovation': {
                'low': "Considera participar en proyectos de innovación o proponer mejoras en procesos existentes.",
                'medium': "Busca oportunidades para contribuir con nuevas ideas en tu área."
            },
            'collaboration': {
                'low': "Participa activamente en proyectos de equipo y busca oportunidades de colaboración.",
                'medium': "Desarrolla habilidades de trabajo en equipo y comunicación efectiva."
            },
            'adaptability': {
                'low': "Practica la adaptación a cambios pequeños y gradualmente aumenta el nivel de desafío.",
                'medium': "Busca experiencias que te saquen de tu zona de confort."
            },
            'results_orientation': {
                'low': "Establece objetivos claros y medibles para tus tareas diarias.",
                'medium': "Enfócate en la entrega de resultados de calidad y el cumplimiento de objetivos."
            },
            'customer_focus': {
                'low': "Desarrolla una mejor comprensión de las necesidades de los clientes.",
                'medium': "Busca formas de mejorar la experiencia del cliente en tu área."
            },
            'integrity': {
                'low': "Familiarízate con los valores y políticas éticas de la organización.",
                'medium': "Refuerza tu compromiso con la integridad en todas tus interacciones."
            },
            'diversity': {
                'low': "Participa en iniciativas de diversidad e inclusión.",
                'medium': "Busca oportunidades para trabajar con equipos diversos."
            },
            'learning': {
                'low': "Establece un plan de desarrollo profesional con objetivos claros.",
                'medium': "Busca oportunidades de aprendizaje continuo en tu área."
            }
        }
        
        if dimension in recommendations:
            if score < 30:
                return recommendations[dimension]['low']
            else:
                return recommendations[dimension]['medium']
        
        return f"Considera desarrollar tus habilidades en {dimension.replace('_', ' ')}."
