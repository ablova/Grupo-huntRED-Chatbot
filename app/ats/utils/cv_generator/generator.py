"""
Módulo principal del CV Generator.
Integra la personalidad con la generación de CV.
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging
import json
from datetime import datetime

from app.ats.utils.cv_generator.personality_integration import (
    PersonalityCVIntegrator,
    CVOptimization
)
from app.ats.integrations.services.gamification import (
    ActivityType,
    gamification_service
)

logger = logging.getLogger(__name__)

@dataclass
class CVSection:
    """Sección de un CV."""
    title: str
    content: List[str]
    order: int
    style: Dict[str, Any] = None

@dataclass
class CVTemplate:
    """Plantilla de CV."""
    name: str
    sections: List[CVSection]
    style: Dict[str, Any]
    metadata: Dict[str, Any] = None

class CVGenerator:
    """Generador de CV con integración de personalidad."""
    
    def __init__(self):
        self.personality_integrator = PersonalityCVIntegrator()
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, CVTemplate]:
        """Carga las plantillas de CV disponibles."""
        return {
            'professional': CVTemplate(
                name='Professional',
                sections=[
                    CVSection('summary', [], 1, {'font_size': '1.2em', 'spacing': '1.5'}),
                    CVSection('experience', [], 2, {'font_size': '1em', 'spacing': '1.2'}),
                    CVSection('education', [], 3, {'font_size': '1em', 'spacing': '1.2'}),
                    CVSection('skills', [], 4, {'font_size': '1em', 'spacing': '1.2'})
                ],
                style={
                    'font': 'Arial',
                    'colors': ['#2c3e50', '#34495e'],
                    'spacing': '1.5',
                    'layout': 'traditional',
                    'header_style': 'centered',
                    'section_headers': 'bold'
                },
                metadata={
                    'best_for': ['corporate', 'finance', 'legal'],
                    'personality_fit': ['prudence', 'adjustment'],
                    'experience_level': ['mid', 'senior']
                }
            ),
            'modern': CVTemplate(
                name='Modern',
                sections=[
                    CVSection('summary', [], 1, {'font_size': '1.3em', 'spacing': '1.8'}),
                    CVSection('skills', [], 2, {'font_size': '1.1em', 'spacing': '1.5'}),
                    CVSection('experience', [], 3, {'font_size': '1.1em', 'spacing': '1.5'}),
                    CVSection('education', [], 4, {'font_size': '1.1em', 'spacing': '1.5'})
                ],
                style={
                    'font': 'Roboto',
                    'colors': ['#1a237e', '#283593'],
                    'spacing': '2.0',
                    'layout': 'asymmetric',
                    'header_style': 'left-aligned',
                    'section_headers': 'uppercase'
                },
                metadata={
                    'best_for': ['tech', 'creative', 'startup'],
                    'personality_fit': ['inquisitive', 'learning_approach'],
                    'experience_level': ['junior', 'mid']
                }
            ),
            'creative': CVTemplate(
                name='Creative',
                sections=[
                    CVSection('summary', [], 1, {'font_size': '1.4em', 'spacing': '2.0'}),
                    CVSection('experience', [], 2, {'font_size': '1.2em', 'spacing': '1.8'}),
                    CVSection('skills', [], 3, {'font_size': '1.2em', 'spacing': '1.8'}),
                    CVSection('education', [], 4, {'font_size': '1.2em', 'spacing': '1.8'})
                ],
                style={
                    'font': 'Montserrat',
                    'colors': ['#311b92', '#4527a0'],
                    'spacing': '1.8',
                    'layout': 'dynamic',
                    'header_style': 'stylized',
                    'section_headers': 'gradient'
                },
                metadata={
                    'best_for': ['design', 'marketing', 'arts'],
                    'personality_fit': ['sociability', 'interpersonal_sensitivity'],
                    'experience_level': ['all']
                }
            )
        }
    
    async def generate_cv(
        self,
        cv_data: Dict,
        personality_insights: List[Any],
        derailer_insights: List[Any],
        value_insights: List[Any],
        template_name: str = 'professional',
        user_id: Optional[str] = None
    ) -> Dict:
        """
        Genera un CV optimizado basado en la personalidad.
        
        Args:
            cv_data: Datos del CV
            personality_insights: Insights de personalidad
            derailer_insights: Insights de derailers
            value_insights: Insights de valores
            template_name: Nombre de la plantilla a usar
            user_id: ID del usuario para gamificación
            
        Returns:
            Dict con el CV generado
        """
        try:
            # 1. Obtener plantilla
            template = self.templates.get(template_name, self.templates['professional'])
            
            # 2. Optimizar CV con personalidad
            optimization = self.personality_integrator.optimize_cv(
                cv_data,
                personality_insights,
                derailer_insights,
                value_insights
            )
            
            # 3. Aplicar optimizaciones
            optimized_cv = self._apply_optimizations(
                cv_data,
                template,
                optimization
            )
            
            # 4. Generar formato final
            final_cv = self._generate_final_format(
                optimized_cv,
                template,
                optimization
            )
            
            # 5. Agregar metadata
            final_cv['metadata'] = {
                'generated_at': datetime.now().isoformat(),
                'template': template_name,
                'optimization_score': self._calculate_optimization_score(optimization),
                'personality_match': self._calculate_personality_match(
                    template,
                    personality_insights
                )
            }
            
            # 6. Registrar actividades de gamificación si hay user_id
            if user_id:
                await self._record_gamification_activities(
                    user_id,
                    template_name,
                    final_cv['metadata']
                )
            
            return final_cv
            
        except Exception as e:
            logger.error(f"Error generando CV: {str(e)}", exc_info=True)
            return {
                'error': f"Error generando CV: {str(e)}",
                'cv_data': cv_data
            }
    
    def _apply_optimizations(
        self,
        cv_data: Dict,
        template: CVTemplate,
        optimization: CVOptimization
    ) -> Dict:
        """Aplica las optimizaciones al CV."""
        optimized_cv = cv_data.copy()
        
        # Aplicar fortalezas
        if 'summary' in optimized_cv:
            optimized_cv['summary'] = self._enhance_summary(
                optimized_cv['summary'],
                optimization.strengths,
                template.style
            )
        
        # Aplicar keywords
        if 'skills' in optimized_cv:
            optimized_cv['skills'] = self._enhance_skills(
                optimized_cv['skills'],
                optimization.keywords,
                template.style
            )
        
        # Aplicar optimizaciones de secciones
        for section, content in optimization.sections.items():
            if section in optimized_cv:
                optimized_cv[section] = self._apply_section_style(
                    content,
                    template.sections[section].style if section in template.sections else None,
                    optimization.style
                )
        
        return optimized_cv
    
    def _enhance_summary(
        self,
        summary: str,
        strengths: List[str],
        style: Dict[str, Any]
    ) -> str:
        """Mejora el resumen con las fortalezas identificadas."""
        if not strengths:
            return summary
        
        enhanced_summary = summary
        for strength in strengths[:3]:  # Usar máximo 3 fortalezas
            if strength.lower() not in enhanced_summary.lower():
                enhanced_summary += f" {strength}."
        
        # Aplicar estilo
        if style.get('font_size'):
            enhanced_summary = f"<span style='font-size: {style['font_size']}'>{enhanced_summary}</span>"
        
        return enhanced_summary
    
    def _enhance_skills(
        self,
        skills: List[str],
        keywords: List[str],
        style: Dict[str, Any]
    ) -> List[str]:
        """Mejora las habilidades con keywords relevantes."""
        enhanced_skills = skills.copy()
        
        for keyword in keywords:
            if keyword.lower() not in [s.lower() for s in enhanced_skills]:
                enhanced_skills.append(keyword)
        
        # Aplicar estilo
        if style.get('font_size'):
            enhanced_skills = [
                f"<span style='font-size: {style['font_size']}'>{skill}</span>"
                for skill in enhanced_skills
            ]
        
        return enhanced_skills
    
    def _apply_section_style(
        self,
        content: List[str],
        section_style: Optional[Dict[str, Any]],
        optimization_style: Dict[str, Any]
    ) -> List[str]:
        """Aplica estilos a una sección del CV."""
        styled_content = []
        
        for item in content:
            # Aplicar estilo de sección
            if section_style and section_style.get('font_size'):
                item = f"<span style='font-size: {section_style['font_size']}'>{item}</span>"
            
            # Aplicar estilo de optimización
            if optimization_style.get('tone'):
                item = self._apply_tone(item, optimization_style['tone'])
            
            styled_content.append(item)
        
        return styled_content
    
    def _generate_final_format(
        self,
        optimized_cv: Dict,
        template: CVTemplate,
        optimization: CVOptimization
    ) -> Dict:
        """Genera el formato final del CV."""
        final_cv = {
            'template': template.name,
            'style': {
                **template.style,
                **optimization.style
            },
            'sections': []
        }
        
        # Ordenar secciones según la plantilla
        for section in sorted(template.sections, key=lambda x: x.order):
            if section.title in optimized_cv:
                final_cv['sections'].append({
                    'title': section.title,
                    'content': optimized_cv[section.title],
                    'style': section.style
                })
        
        # Agregar recomendaciones
        if optimization.recommendations:
            final_cv['recommendations'] = optimization.recommendations
        
        return final_cv
    
    def _calculate_optimization_score(self, optimization: CVOptimization) -> float:
        """Calcula un score de optimización basado en las mejoras aplicadas."""
        score = 0.0
        
        # Ponderar fortalezas
        score += len(optimization.strengths) * 0.2
        
        # Ponderar keywords
        score += len(optimization.keywords) * 0.15
        
        # Ponderar recomendaciones
        score += len(optimization.recommendations) * 0.1
        
        return min(score, 1.0)  # Normalizar a 1.0
    
    def _calculate_personality_match(
        self,
        template: CVTemplate,
        personality_insights: List[Any]
    ) -> Dict[str, float]:
        """Calcula qué tan bien se ajusta la plantilla al perfil de personalidad."""
        matches = {}
        
        if template.metadata and 'personality_fit' in template.metadata:
            for dimension in template.metadata['personality_fit']:
                for insight in personality_insights:
                    if insight.dimension.value == dimension:
                        matches[dimension] = insight.score
        
        return matches 

    async def _record_gamification_activities(
        self,
        user_id: str,
        template_name: str,
        metadata: Dict[str, Any]
    ) -> None:
        """Registra actividades de gamificación relacionadas con el CV."""
        try:
            # Registrar generación de CV
            await gamification_service.record_activity(
                user_id,
                ActivityType.CV_GENERATED,
                {'template': template_name}
            )
            
            # Registrar optimización
            await gamification_service.record_activity(
                user_id,
                ActivityType.CV_OPTIMIZED,
                {'optimization_score': metadata['optimization_score']}
            )
            
            # Registrar uso de plantilla
            await gamification_service.record_activity(
                user_id,
                ActivityType.CV_TEMPLATE_USED,
                {'template': template_name}
            )
            
            # Registrar match de personalidad
            if metadata['personality_match']:
                max_match = max(metadata['personality_match'].values())
                await gamification_service.record_activity(
                    user_id,
                    ActivityType.CV_PERSONALITY_MATCH,
                    {'match_score': max_match}
                )
            
            # Registrar score de optimización
            if metadata['optimization_score'] >= 0.9:
                await gamification_service.record_activity(
                    user_id,
                    ActivityType.CV_OPTIMIZATION_SCORE,
                    {'score': metadata['optimization_score']}
                )
                
        except Exception as e:
            logger.error(f"Error registrando actividades de gamificación: {str(e)}") 