"""
Analizador de skills para el sistema de aprendizaje.
"""
from typing import Dict, Any, List
import logging
from datetime import datetime

from app.ml.core.base_analyzer import BaseAnalyzer
from app.ml.analyzers.notification_analyzer import NotificationAnalyzer

logger = logging.getLogger('ml')

class SkillAnalyzer(BaseAnalyzer):
    """Analizador de skills y brechas de aprendizaje."""
    
    def __init__(self):
        super().__init__()
        self.notification_analyzer = NotificationAnalyzer()
    
    async def analyze_skill_gaps(self, user_id: str) -> Dict[str, Any]:
        """
        Analiza las brechas de skills basado en:
        - Perfil actual
        - Requisitos del puesto
        - Tendencias del mercado
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Dict con análisis de brechas y recomendaciones
        """
        try:
            # Obtener patrones del usuario
            user_patterns = await self.notification_analyzer.get_user_patterns(user_id)
            
            # Analizar brechas
            skill_gaps = await self._analyze_gaps(user_patterns)
            
            # Generar recomendaciones
            recommendations = await self._generate_recommendations(skill_gaps)
            
            return {
                'gaps': skill_gaps,
                'recommendations': recommendations,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analizando brechas de skills: {str(e)}")
            return {
                'gaps': [],
                'recommendations': [],
                'error': str(e)
            }
    
    async def _analyze_gaps(self, user_patterns: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Analiza las brechas de skills basado en patrones del usuario.
        
        Args:
            user_patterns: Patrones del usuario
            
        Returns:
            Lista de brechas identificadas
        """
        gaps = []
        
        # Analizar skills actuales vs requeridos
        current_skills = user_patterns.get('skills', [])
        required_skills = user_patterns.get('required_skills', [])
        
        for skill in required_skills:
            if skill not in current_skills:
                gaps.append({
                    'skill': skill,
                    'level': 'missing',
                    'priority': 'high'
                })
            else:
                # Analizar nivel de competencia
                current_level = current_skills[skill]
                required_level = required_skills[skill]
                
                if current_level < required_level:
                    gaps.append({
                        'skill': skill,
                        'level': 'incomplete',
                        'current': current_level,
                        'required': required_level,
                        'priority': 'medium'
                    })
        
        return gaps
    
    async def _generate_recommendations(self, gaps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Genera recomendaciones basadas en las brechas identificadas.
        
        Args:
            gaps: Lista de brechas identificadas
            
        Returns:
            Lista de recomendaciones
        """
        recommendations = []
        
        for gap in gaps:
            # Generar recomendación específica para cada brecha
            recommendation = {
                'skill': gap['skill'],
                'type': 'course' if gap['level'] == 'missing' else 'practice',
                'priority': gap['priority'],
                'resources': await self._get_resources(gap)
            }
            
            recommendations.append(recommendation)
        
        return recommendations
    
    async def _get_resources(self, gap: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Obtiene recursos recomendados para una brecha específica.
        
        Args:
            gap: Brecha identificada
            
        Returns:
            Lista de recursos recomendados
        """
        # Aquí iría la lógica para obtener recursos específicos
        # Por ahora retornamos una lista vacía
        return [] 