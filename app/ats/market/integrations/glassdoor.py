"""
Integración con Glassdoor para análisis de mercado.
"""
from typing import Dict, Any, List
import logging
from datetime import datetime

from app.ats.integrations.base import BaseIntegration
from app.ml.analyzers.market.salary_analyzer import SalaryAnalyzer

logger = logging.getLogger('market')

class GlassdoorIntegration(BaseIntegration):
    """Integración con Glassdoor."""
    
    def __init__(self):
        super().__init__()
        self.salary_analyzer = SalaryAnalyzer()
    
    async def get_salary_insights(self, skill: str, location: str = None) -> Dict[str, Any]:
        """
        Obtiene insights de salarios desde Glassdoor.
        
        Args:
            skill: Skill a analizar
            location: Ubicación (opcional)
            
        Returns:
            Dict con insights de salarios
        """
        try:
            # Analizar salarios
            salary_analysis = await self.salary_analyzer.analyze_salary(skill, location)
            
            # Formatear insights
            insights = await self._format_insights(salary_analysis)
            
            return insights
            
        except Exception as e:
            logger.error(f"Error obteniendo insights de Glassdoor: {str(e)}")
            return {
                'error': str(e)
            }
    
    async def _format_insights(self, salary_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Formatea los insights de salarios.
        
        Args:
            salary_analysis: Análisis de salarios
            
        Returns:
            Dict con insights formateados
        """
        return {
            'skill': salary_analysis['skill'],
            'location': salary_analysis['location'],
            'ranges': salary_analysis['ranges'],
            'statistics': salary_analysis['statistics'],
            'timestamp': datetime.now().isoformat()
        }
    
    async def get_company_insights(self, company: str) -> Dict[str, Any]:
        """
        Obtiene insights de una empresa específica.
        
        Args:
            company: Nombre de la empresa
            
        Returns:
            Dict con insights de la empresa
        """
        try:
            # Aquí iría la lógica para obtener insights de la empresa
            return {
                'company': company,
                'rating': 4.2,
                'reviews_count': 5000,
                'salary_satisfaction': 0.75,
                'benefits_rating': 4.0,
                'work_life_balance': 3.8,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo insights de empresa: {str(e)}")
            return {
                'error': str(e)
            }
    
    async def get_interview_insights(self, company: str, position: str) -> Dict[str, Any]:
        """
        Obtiene insights de entrevistas para una posición.
        
        Args:
            company: Nombre de la empresa
            position: Posición
            
        Returns:
            Dict con insights de entrevistas
        """
        try:
            # Aquí iría la lógica para obtener insights de entrevistas
            return {
                'company': company,
                'position': position,
                'difficulty': 3.5,
                'experience': 'positive',
                'process_duration': '2 weeks',
                'interview_types': ['technical', 'behavioral'],
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo insights de entrevistas: {str(e)}")
            return {
                'error': str(e)
            } 