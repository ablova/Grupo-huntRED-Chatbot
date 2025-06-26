"""
Evaluación de personalidad para el sistema de workflow.
"""

from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class PersonalityEvaluation:
    """
    Clase para manejar evaluaciones de personalidad.
    """
    
    def __init__(self):
        self.logger = logger
    
    async def evaluate(self, responses: Dict[str, Any], business_unit: str) -> Dict[str, Any]:
        """
        Evalúa las respuestas de personalidad del usuario.
        
        Args:
            responses: Diccionario con las respuestas del usuario
            business_unit: Unidad de negocio (huntred, huntu, amigro)
            
        Returns:
            Dict con los resultados de la evaluación
        """
        try:
            self.logger.info(f"Iniciando evaluación de personalidad para {business_unit}")
            
            # Análisis básico de respuestas
            analysis = self._analyze_responses(responses)
            
            # Aplicar lógica específica por unidad de negocio
            if business_unit == "huntred":
                results = self._analyze_huntred_personality(analysis)
            elif business_unit == "huntu":
                results = self._analyze_huntu_personality(analysis)
            elif business_unit == "amigro":
                results = self._analyze_amigro_personality(analysis)
            else:
                results = self._analyze_generic_personality(analysis)
            
            self.logger.info(f"Evaluación de personalidad completada para {business_unit}")
            return results
            
        except Exception as e:
            self.logger.error(f"Error en evaluación de personalidad: {str(e)}", exc_info=True)
            return {
                "error": str(e),
                "status": "failed"
            }
    
    def _analyze_responses(self, responses: Dict[str, Any]) -> Dict[str, Any]:
        """Analiza las respuestas básicas del usuario."""
        analysis = {
            "total_responses": len(responses),
            "completion_rate": self._calculate_completion_rate(responses),
            "response_consistency": self._analyze_consistency(responses)
        }
        return analysis
    
    def _calculate_completion_rate(self, responses: Dict[str, Any]) -> float:
        """Calcula la tasa de completitud de las respuestas."""
        if not responses:
            return 0.0
        
        completed = sum(1 for response in responses.values() if response is not None and response != "")
        return completed / len(responses)
    
    def _analyze_consistency(self, responses: Dict[str, Any]) -> Dict[str, Any]:
        """Analiza la consistencia de las respuestas."""
        return {
            "score": 0.8,  # Placeholder
            "notes": "Análisis de consistencia básico"
        }
    
    def _analyze_huntred_personality(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Análisis específico para huntRED."""
        return {
            "business_unit": "huntred",
            "personality_score": 85,
            "leadership_potential": 90,
            "adaptability": 88,
            "team_work": 92,
            "analysis": analysis,
            "recommendations": [
                "Excelente potencial de liderazgo",
                "Alta adaptabilidad al cambio",
                "Fuerte capacidad de trabajo en equipo"
            ]
        }
    
    def _analyze_huntu_personality(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Análisis específico para huntU."""
        return {
            "business_unit": "huntu",
            "personality_score": 82,
            "sales_potential": 88,
            "communication": 85,
            "persistence": 90,
            "analysis": analysis,
            "recommendations": [
                "Alto potencial en ventas",
                "Excelente comunicación",
                "Gran persistencia y determinación"
            ]
        }
    
    def _analyze_amigro_personality(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Análisis específico para amigro."""
        return {
            "business_unit": "amigro",
            "personality_score": 80,
            "operational_efficiency": 85,
            "attention_to_detail": 88,
            "reliability": 92,
            "analysis": analysis,
            "recommendations": [
                "Alta eficiencia operacional",
                "Excelente atención al detalle",
                "Gran confiabilidad"
            ]
        }
    
    def _analyze_generic_personality(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Análisis genérico para unidades de negocio no específicas."""
        return {
            "business_unit": "generic",
            "personality_score": 75,
            "analysis": analysis,
            "recommendations": [
                "Evaluación estándar completada",
                "Se recomienda análisis específico por unidad de negocio"
            ]
        } 