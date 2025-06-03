# /home/pablo/app/com/chatbot/workflow/analysis.py
#
# Módulo de análisis para el chatbot.
# Incluye funcionalidades para manejo de evaluaciones, análisis y más.
# Optimizado para bajo uso de CPU, escalabilidad, y robustez frente a fallos.

from typing import Dict, Any, List
from .evaluaciones.personality_evaluation import PersonalityEvaluation
from .evaluaciones.talent_evaluation import TalentEvaluation
from .evaluaciones.cultural_evaluation import CulturalEvaluation

class EvaluationAnalysis:
    def __init__(self):
        self.personality_eval = PersonalityEvaluation()
        self.talent_eval = TalentEvaluation()
        self.cultural_eval = CulturalEvaluation()
    
    async def analyze_responses(self, responses: Dict[str, Any], evaluation_type: str, business_unit: str) -> Dict[str, Any]:
        """
        Analiza las respuestas según el tipo de evaluación y unidad de negocio
        
        Args:
            responses: Diccionario con las respuestas del usuario
            evaluation_type: Tipo de evaluación (personality, talent, cultural)
            business_unit: Unidad de negocio (huntred, huntu, amigro)
            
        Returns:
            Dict con los resultados del análisis
        """
        if evaluation_type == "personality":
            return await self.personality_eval.evaluate(responses, business_unit)
        elif evaluation_type == "talent":
            return await self.talent_eval.evaluate(responses, business_unit)
        elif evaluation_type == "cultural":
            return await self.cultural_eval.evaluate(responses, business_unit)
        else:
            raise ValueError(f"Tipo de evaluación no válido: {evaluation_type}")
    
    async def generate_insights(self, results: Dict[str, Any], business_unit: str) -> Dict[str, Any]:
        """
        Genera insights basados en los resultados del análisis
        
        Args:
            results: Resultados del análisis
            business_unit: Unidad de negocio
            
        Returns:
            Dict con los insights generados
        """
        insights = {
            "fortalezas": [],
            "areas_mejora": [],
            "recomendaciones": []
        }
        
        # Análisis específico por unidad de negocio
        if business_unit == "huntred":
            insights.update(self._analyze_huntred_insights(results))
        elif business_unit in ["huntu", "amigro"]:
            insights.update(self._analyze_huntu_insights(results))
            
        return insights
    
    def _analyze_huntred_insights(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Análisis específico para huntRED"""
        return {
            "liderazgo": self._analyze_leadership(results),
            "adaptabilidad": self._analyze_adaptability(results),
            "gestion": self._analyze_management(results)
        }
    
    def _analyze_huntu_insights(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Análisis específico para huntU y amigro"""
        return {
            "ventas": self._analyze_sales(results),
            "operaciones": self._analyze_operations(results)
        }
    
    def _analyze_leadership(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Análisis de liderazgo"""
        return {
            "score": results.get("liderazgo_score", 0),
            "fortalezas": self._identify_leadership_strengths(results),
            "areas_mejora": self._identify_leadership_improvements(results)
        }
    
    def _analyze_adaptability(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Análisis de adaptabilidad"""
        return {
            "score": results.get("adaptabilidad_score", 0),
            "capacidad_cambio": self._assess_change_capacity(results),
            "recomendaciones": self._generate_adaptability_recommendations(results)
        }
    
    def _analyze_management(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Análisis de gestión"""
        return {
            "score": results.get("gestion_score", 0),
            "eficiencia": self._assess_management_efficiency(results),
            "recomendaciones": self._generate_management_recommendations(results)
        }
    
    def _analyze_sales(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Análisis de ventas"""
        return {
            "score": results.get("ventas_score", 0),
            "fortalezas": self._identify_sales_strengths(results),
            "areas_mejora": self._identify_sales_improvements(results)
        }
    
    def _analyze_operations(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Análisis de operaciones"""
        return {
            "score": results.get("operaciones_score", 0),
            "eficiencia": self._assess_operations_efficiency(results),
            "recomendaciones": self._generate_operations_recommendations(results)
        } 