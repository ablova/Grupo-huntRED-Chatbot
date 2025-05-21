import logging
from typing import Dict, List, Any

from app.com.chatbot.core.values import ValuesPrinciples

logger = logging.getLogger(__name__)

class ValuesProcessor:
    def __init__(self):
        self.values_principles = ValuesPrinciples()
    
    async def get_person_values(self, person_id: int) -> Dict[str, Any]:
        """Obtiene los valores de una persona."""
        try:
            # Obtener valores de soporte
            support_values = await self._get_support_values(person_id)
            
            # Obtener valores de sinergia
            synergy_values = await self._get_synergy_values(person_id)
            
            # Obtener principios
            principles = await self._get_principles(person_id)
            
            return {
                "support": support_values,
                "synergy": synergy_values,
                "principles": principles,
                "overall_score": self._calculate_overall_score(support_values, synergy_values, principles)
            }
        except Exception as e:
            logger.error(f"Error obteniendo valores de la persona: {str(e)}")
            return {}
    
    async def _get_support_values(self, person_id: int) -> Dict[str, float]:
        """Obtiene los valores de soporte de una persona."""
        try:
            # Implementar lógica para obtener valores de soporte
            return {
                "empathy": 0.8,
                "collaboration": 0.7,
                "communication": 0.9,
                "adaptability": 0.6
            }
        except Exception as e:
            logger.error(f"Error obteniendo valores de soporte: {str(e)}")
            return {}
    
    async def _get_synergy_values(self, person_id: int) -> Dict[str, float]:
        """Obtiene los valores de sinergia de una persona."""
        try:
            # Implementar lógica para obtener valores de sinergia
            return {
                "innovation": 0.8,
                "efficiency": 0.7,
                "quality": 0.9,
                "sustainability": 0.6
            }
        except Exception as e:
            logger.error(f"Error obteniendo valores de sinergia: {str(e)}")
            return {}
    
    async def _get_principles(self, person_id: int) -> List[Dict[str, Any]]:
        """Obtiene los principios de una persona."""
        try:
            # Implementar lógica para obtener principios
            return [
                {
                    "name": "Integridad",
                    "description": "Actuar con honestidad y ética en todas las situaciones",
                    "score": 0.9
                },
                {
                    "name": "Excelencia",
                    "description": "Buscar la mejora continua y la calidad en todo lo que hacemos",
                    "score": 0.8
                },
                {
                    "name": "Respeto",
                    "description": "Valorar y respetar la diversidad y las diferencias",
                    "score": 0.9
                }
            ]
        except Exception as e:
            logger.error(f"Error obteniendo principios: {str(e)}")
            return []
    
    def _calculate_overall_score(self, support_values: Dict[str, float], 
                               synergy_values: Dict[str, float], 
                               principles: List[Dict[str, Any]]) -> float:
        """Calcula el score general de valores."""
        try:
            # Calcular promedio de valores de soporte
            support_score = sum(support_values.values()) / len(support_values) if support_values else 0
            
            # Calcular promedio de valores de sinergia
            synergy_score = sum(synergy_values.values()) / len(synergy_values) if synergy_values else 0
            
            # Calcular promedio de principios
            principles_score = sum(p["score"] for p in principles) / len(principles) if principles else 0
            
            # Pesos para cada componente
            weights = {
                "support": 0.4,
                "synergy": 0.3,
                "principles": 0.3
            }
            
            # Calcular score ponderado
            overall_score = (
                support_score * weights["support"] +
                synergy_score * weights["synergy"] +
                principles_score * weights["principles"]
            )
            
            return round(overall_score * 100)  # Convertir a porcentaje
        except Exception as e:
            logger.error(f"Error calculando score general: {str(e)}")
            return 0
    
    def get_value_recommendations(self, values: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Genera recomendaciones basadas en los valores."""
        try:
            recommendations = []
            
            # Analizar valores de soporte
            support_values = values.get("support", {})
            for value, score in support_values.items():
                if score < 0.7:
                    recommendations.append({
                        "type": "support",
                        "value": value,
                        "current_score": score,
                        "recommendation": self._get_support_recommendation(value)
                    })
            
            # Analizar valores de sinergia
            synergy_values = values.get("synergy", {})
            for value, score in synergy_values.items():
                if score < 0.7:
                    recommendations.append({
                        "type": "synergy",
                        "value": value,
                        "current_score": score,
                        "recommendation": self._get_synergy_recommendation(value)
                    })
            
            # Analizar principios
            principles = values.get("principles", [])
            for principle in principles:
                if principle["score"] < 0.7:
                    recommendations.append({
                        "type": "principle",
                        "value": principle["name"],
                        "current_score": principle["score"],
                        "recommendation": self._get_principle_recommendation(principle["name"])
                    })
            
            return recommendations
        except Exception as e:
            logger.error(f"Error generando recomendaciones de valores: {str(e)}")
            return []
    
    def _get_support_recommendation(self, value: str) -> str:
        """Obtiene recomendación para un valor de soporte."""
        recommendations = {
            "empathy": "Participar en actividades de voluntariado o mentoring",
            "collaboration": "Buscar proyectos colaborativos y actividades de team building",
            "communication": "Tomar cursos de comunicación efectiva y presentaciones",
            "adaptability": "Exponerse a diferentes roles y responsabilidades"
        }
        return recommendations.get(value, "Desarrollar habilidades de soporte en general")
    
    def _get_synergy_recommendation(self, value: str) -> str:
        """Obtiene recomendación para un valor de sinergia."""
        recommendations = {
            "innovation": "Participar en hackathons o proyectos de innovación",
            "efficiency": "Aprender metodologías ágiles y herramientas de productividad",
            "quality": "Obtener certificaciones de calidad y mejores prácticas",
            "sustainability": "Involucrarse en proyectos de sostenibilidad"
        }
        return recommendations.get(value, "Desarrollar habilidades de sinergia en general")
    
    def _get_principle_recommendation(self, principle: str) -> str:
        """Obtiene recomendación para un principio."""
        recommendations = {
            "Integridad": "Participar en talleres de ética y compliance",
            "Excelencia": "Establecer metas de mejora continua y seguimiento",
            "Respeto": "Participar en programas de diversidad e inclusión"
        }
        return recommendations.get(principle, "Fortalecer principios y valores fundamentales") 