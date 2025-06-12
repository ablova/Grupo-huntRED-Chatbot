"""
Generador de rutas de aprendizaje personalizadas.
"""
from typing import Dict, Any, List
import logging
from datetime import datetime

from app.ml.core.base_analyzer import BaseAnalyzer
from app.ml.analyzers.learning.skill_analyzer import SkillAnalyzer

logger = logging.getLogger('ml')

class LearningPathGenerator(BaseAnalyzer):
    """Generador de rutas de aprendizaje personalizadas."""
    
    def __init__(self):
        super().__init__()
        self.skill_analyzer = SkillAnalyzer()
    
    async def generate_learning_path(self, user_id: str) -> Dict[str, Any]:
        """
        Genera una ruta de aprendizaje personalizada.
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Dict con la ruta de aprendizaje generada
        """
        try:
            # Analizar brechas de skills
            skill_analysis = await self.skill_analyzer.analyze_skill_gaps(user_id)
            
            # Generar ruta de aprendizaje
            learning_path = await self._generate_path(skill_analysis)
            
            # Calcular estimaciones
            estimates = await self._calculate_estimates(learning_path)
            
            return {
                'path': learning_path,
                'estimates': estimates,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generando ruta de aprendizaje: {str(e)}")
            return {
                'path': [],
                'estimates': {},
                'error': str(e)
            }
    
    async def _generate_path(self, skill_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Genera la ruta de aprendizaje basada en el análisis de skills.
        
        Args:
            skill_analysis: Análisis de skills
            
        Returns:
            Lista de pasos en la ruta de aprendizaje
        """
        path = []
        
        # Ordenar brechas por prioridad
        gaps = sorted(
            skill_analysis['gaps'],
            key=lambda x: {'high': 0, 'medium': 1, 'low': 2}[x['priority']]
        )
        
        for gap in gaps:
            # Generar pasos para cada brecha
            steps = await self._generate_steps(gap)
            path.extend(steps)
        
        return path
    
    async def _generate_steps(self, gap: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Genera pasos específicos para una brecha.
        
        Args:
            gap: Brecha identificada
            
        Returns:
            Lista de pasos para la brecha
        """
        steps = []
        
        if gap['level'] == 'missing':
            # Pasos para skills faltantes
            steps.append({
                'type': 'course',
                'skill': gap['skill'],
                'description': f"Completar curso de {gap['skill']}",
                'estimated_time': '4 weeks'
            })
        else:
            # Pasos para skills incompletas
            steps.append({
                'type': 'practice',
                'skill': gap['skill'],
                'description': f"Practicar {gap['skill']} hasta nivel {gap['required']}",
                'current_level': gap['current'],
                'target_level': gap['required'],
                'estimated_time': '2 weeks'
            })
        
        return steps
    
    async def _calculate_estimates(self, learning_path: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calcula estimaciones para la ruta de aprendizaje.
        
        Args:
            learning_path: Ruta de aprendizaje
            
        Returns:
            Dict con estimaciones
        """
        total_time = 0
        total_steps = len(learning_path)
        
        for step in learning_path:
            # Extraer tiempo estimado
            time_str = step['estimated_time']
            weeks = int(time_str.split()[0])
            total_time += weeks
        
        return {
            'total_steps': total_steps,
            'total_weeks': total_time,
            'estimated_completion': (datetime.now() + timedelta(weeks=total_time)).isoformat()
        } 