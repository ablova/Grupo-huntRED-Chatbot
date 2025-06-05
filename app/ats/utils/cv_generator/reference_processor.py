# /home/pablo/app/ats/utils/cv_generator/reference_processor.py
"""
Procesador de referencias para CVs.
"""

from typing import Dict, List, Optional
from datetime import datetime
from app.models import Reference, Person
from app.ats.chatbot.references.gamification import ReferenceGamification

class ReferenceProcessor:
    """Procesa y formatea referencias para diferentes tipos de CVs."""
    
    def __init__(self, business_unit):
        self.business_unit = business_unit
        self.gamification = ReferenceGamification(business_unit)
    
    async def process_references_for_cv(self, person: Person, audience_type: str = 'client') -> Dict:
        """
        Procesa las referencias para incluirlas en el CV según el tipo de audiencia.
        
        Args:
            person: Person - Persona cuyas referencias procesar
            audience_type: str - Tipo de audiencia ('client', 'candidate', 'consultant')
            
        Returns:
            Dict con referencias procesadas
        """
        try:
            # Obtener referencias completadas
            references = Reference.objects.filter(
                candidate=person,
                status='completed'
            ).order_by('-created_at')
            
            if not references:
                return {}
            
            # Procesar según audiencia
            if audience_type == 'client':
                return await self._process_for_client(references)
            elif audience_type == 'candidate':
                return await self._process_for_candidate(references)
            else:  # consultant
                return await self._process_for_consultant(references)
                
        except Exception as e:
            print(f"Error procesando referencias para CV: {e}")
            return {}
    
    async def _process_for_client(self, references: List[Reference]) -> Dict:
        """Procesa referencias para CV de cliente."""
        processed = {
            'references': [],
            'summary': {
                'total': len(references),
                'average_score': 0,
                'top_skills': [],
                'key_achievements': []
            }
        }
        
        total_score = 0
        skills_count = {}
        achievements = []
        
        for ref in references:
            # Obtener estadísticas de gamificación
            stats = await self.gamification.get_reference_stats(ref)
            
            # Procesar feedback
            feedback = ref.metadata.get('feedback', {})
            analysis = ref.metadata.get('analysis', {})
            
            # Calcular score
            score = analysis.get('metrics', {}).get('score', 0)
            total_score += score
            
            # Extraer habilidades mencionadas
            skills = analysis.get('competencies', {}).get('skills', [])
            for skill in skills:
                skills_count[skill] = skills_count.get(skill, 0) + 1
            
            # Extraer logros
            achievements.extend(analysis.get('insights', {}).get('achievements', []))
            
            # Formatear referencia para cliente
            processed['references'].append({
                'name': ref.reference.get_full_name(),
                'position': ref.reference.current_position if hasattr(ref.reference, 'current_position') else '',
                'company': ref.reference.current_company if hasattr(ref.reference, 'current_company') else '',
                'relationship': ref.relationship,
                'score': score,
                'key_points': analysis.get('insights', {}).get('key_points', []),
                'gamification': {
                    'points': stats.get('points', 0),
                    'achievements': stats.get('achievements', [])
                }
            })
        
        # Calcular promedios y top skills
        if references:
            processed['summary']['average_score'] = total_score / len(references)
            processed['summary']['top_skills'] = sorted(
                skills_count.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
            processed['summary']['key_achievements'] = list(set(achievements))[:3]
        
        return processed
    
    async def _process_for_candidate(self, references: List[Reference]) -> Dict:
        """Procesa referencias para CV de candidato."""
        processed = {
            'references': [],
            'growth_insights': {
                'strengths': [],
                'areas_for_improvement': [],
                'career_recommendations': []
            }
        }
        
        for ref in references:
            analysis = ref.metadata.get('analysis', {})
            insights = analysis.get('insights', {})
            
            # Formatear referencia para candidato
            processed['references'].append({
                'name': ref.reference.get_full_name(),
                'position': ref.reference.current_position if hasattr(ref.reference, 'current_position') else '',
                'company': ref.reference.current_company if hasattr(ref.reference, 'current_company') else '',
                'relationship': ref.relationship,
                'feedback_summary': insights.get('summary', ''),
                'strengths': insights.get('strengths', []),
                'areas_for_improvement': insights.get('areas_for_improvement', [])
            })
            
            # Acumular insights para crecimiento
            processed['growth_insights']['strengths'].extend(insights.get('strengths', []))
            processed['growth_insights']['areas_for_improvement'].extend(
                insights.get('areas_for_improvement', [])
            )
            processed['growth_insights']['career_recommendations'].extend(
                insights.get('career_recommendations', [])
            )
        
        # Eliminar duplicados y limitar cantidad
        for key in processed['growth_insights']:
            processed['growth_insights'][key] = list(set(processed['growth_insights'][key]))[:5]
        
        return processed
    
    async def _process_for_consultant(self, references: List[Reference]) -> Dict:
        """Procesa referencias para CV de consultor."""
        processed = {
            'references': [],
            'analysis': {
                'quality_metrics': {},
                'market_fit': {},
                'risk_factors': []
            }
        }
        
        for ref in references:
            analysis = ref.metadata.get('analysis', {})
            metrics = analysis.get('metrics', {})
            
            # Formatear referencia para consultor
            processed['references'].append({
                'name': ref.reference.get_full_name(),
                'position': ref.reference.current_position if hasattr(ref.reference, 'current_position') else '',
                'company': ref.reference.current_company if hasattr(ref.reference, 'current_company') else '',
                'relationship': ref.relationship,
                'quality_metrics': {
                    'completeness': metrics.get('completeness', 0),
                    'detail_level': metrics.get('detail_level', 0),
                    'sentiment': metrics.get('sentiment', 0)
                },
                'key_insights': analysis.get('insights', {}).get('key_points', []),
                'risk_factors': analysis.get('insights', {}).get('risk_factors', [])
            })
            
            # Acumular métricas
            for metric, value in metrics.items():
                if metric not in processed['analysis']['quality_metrics']:
                    processed['analysis']['quality_metrics'][metric] = []
                processed['analysis']['quality_metrics'][metric].append(value)
            
            # Acumular factores de riesgo
            processed['analysis']['risk_factors'].extend(
                analysis.get('insights', {}).get('risk_factors', [])
            )
        
        # Calcular promedios de métricas
        for metric, values in processed['analysis']['quality_metrics'].items():
            processed['analysis']['quality_metrics'][metric] = sum(values) / len(values)
        
        # Eliminar duplicados en factores de riesgo
        processed['analysis']['risk_factors'] = list(set(processed['analysis']['risk_factors']))
        
        return processed 