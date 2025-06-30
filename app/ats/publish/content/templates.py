"""
Sistema de Plantillas de Contenido con integración AURA y Analyzers.
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from django.utils import timezone
import json

from app.ats.publish.models import ContentTemplate, AudienceSegment
from app.models import BusinessUnit

# Importaciones de AURA
from app.ml.aura.integration_layer import AuraIntegrationLayer
from app.ml.aura.core import AuraEngine

# Importaciones de Analyzers
from app.ml.analyzers.personality_analyzer import PersonalityAnalyzer
from app.ml.analyzers.professional_analyzer import ProfessionalAnalyzer
from app.ml.analyzers.cultural_analyzer import CulturalAnalyzer
from app.ml.analyzers.generational_analyzer import GenerationalAnalyzer

logger = logging.getLogger(__name__)

class ContentTemplateEngine:
    """
    Motor de plantillas de contenido que integra AURA y analyzers.
    """
    
    def __init__(self, business_unit: BusinessUnit):
        """
        Inicializa el motor de plantillas.
        
        Args:
            business_unit: Unidad de negocio para las plantillas.
        """
        self.business_unit = business_unit
        self.logger = logging.getLogger('content_template_engine')
        
        # Inicializar AURA
        self.aura_integration = AuraIntegrationLayer()
        self.aura_engine = AuraEngine()
        
        # Inicializar Analyzers
        self.personality_analyzer = PersonalityAnalyzer()
        self.professional_analyzer = ProfessionalAnalyzer()
        self.cultural_analyzer = CulturalAnalyzer()
        self.generational_analyzer = GenerationalAnalyzer()
    
    async def create_intelligent_template(self,
                                        name: str,
                                        template_type: str,
                                        content_structure: Dict[str, Any],
                                        target_segments: List[AudienceSegment] = None) -> ContentTemplate:
        """
        Crea una plantilla inteligente con integración AURA.
        
        Args:
            name: Nombre de la plantilla.
            template_type: Tipo de plantilla (email, social, landing, etc.).
            content_structure: Estructura del contenido.
            target_segments: Segmentos objetivo.
            
        Returns:
            Plantilla de contenido creada.
        """
        try:
            # Análisis de segmentos objetivo
            segment_analysis = {}
            if target_segments:
                segment_analysis = await self._analyze_target_segments(target_segments)
            
            # Crear plantilla
            template = await ContentTemplate.objects.acreate(
                name=name,
                template_type=template_type,
                content_structure=content_structure,
                active=True
            )
            
            # Asociar segmentos si se proporcionan
            if target_segments:
                for segment in target_segments:
                    template.target_segments.add(segment)
            
            # Guardar análisis en metadata
            template.metadata = {
                'segment_analysis': segment_analysis,
                'aura_integration': True,
                'personalization_variables': await self._get_personalization_variables(target_segments),
                'created_at': timezone.now().isoformat()
            }
            await template.asave()
            
            return template
            
        except Exception as e:
            self.logger.error(f"Error creando plantilla inteligente: {str(e)}")
            raise
    
    async def _analyze_target_segments(self, segments: List[AudienceSegment]) -> Dict[str, Any]:
        """
        Analiza segmentos objetivo para personalización.
        """
        try:
            analysis = {
                'personality_profiles': [],
                'professional_profiles': [],
                'cultural_preferences': [],
                'generational_insights': [],
                'aura_recommendations': []
            }
            
            for segment in segments:
                # Análisis de personalidad
                personality_analysis = await self.personality_analyzer.analyze_segment_personality(
                    segment.criteria, self.business_unit
                )
                analysis['personality_profiles'].append(personality_analysis)
                
                # Análisis profesional
                professional_analysis = await self.professional_analyzer.analyze_segment_professional(
                    segment.criteria, self.business_unit
                )
                analysis['professional_profiles'].append(professional_analysis)
                
                # Análisis cultural
                cultural_analysis = await self.cultural_analyzer.analyze_segment_cultural_fit(
                    segment.criteria, self.business_unit
                )
                analysis['cultural_preferences'].append(cultural_analysis)
                
                # Análisis generacional
                generational_analysis = await self.generational_analyzer.analyze_segment_generational(
                    segment.criteria, self.business_unit
                )
                analysis['generational_insights'].append(generational_analysis)
                
                # Recomendaciones de AURA
                aura_recommendations = await self.aura_engine.get_template_recommendations(
                    segment_id=segment.id,
                    template_type='content',
                    business_unit=self.business_unit
                )
                analysis['aura_recommendations'].append(aura_recommendations)
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analizando segmentos objetivo: {str(e)}")
            return {}
    
    async def _get_personalization_variables(self, segments: List[AudienceSegment]) -> List[str]:
        """
        Obtiene variables de personalización basadas en segmentos.
        """
        try:
            variables = [
                'nombre',
                'empresa',
                'cargo',
                'industria',
                'ubicación',
                'tamaño_empresa'
            ]
            
            if segments:
                for segment in segments:
                    # Variables basadas en personalidad
                    personality_vars = await self.personality_analyzer.get_personalization_variables(
                        segment.criteria, self.business_unit
                    )
                    variables.extend(personality_vars)
                    
                    # Variables basadas en análisis profesional
                    professional_vars = await self.professional_analyzer.get_personalization_variables(
                        segment.criteria, self.business_unit
                    )
                    variables.extend(professional_vars)
                    
                    # Variables basadas en análisis cultural
                    cultural_vars = await self.cultural_analyzer.get_personalization_variables(
                        segment.criteria, self.business_unit
                    )
                    variables.extend(cultural_vars)
                    
                    # Variables basadas en análisis generacional
                    generational_vars = await self.generational_analyzer.get_personalization_variables(
                        segment.criteria, self.business_unit
                    )
                    variables.extend(generational_vars)
            
            # Eliminar duplicados
            return list(set(variables))
            
        except Exception as e:
            self.logger.error(f"Error obteniendo variables de personalización: {str(e)}")
            return ['nombre', 'empresa', 'cargo']
    
    async def render_template(self, template: ContentTemplate, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Renderiza una plantilla con contexto personalizado.
        
        Args:
            template: Plantilla a renderizar.
            context: Contexto con variables de personalización.
            
        Returns:
            Contenido renderizado.
        """
        try:
            rendered_content = {
                'subject': '',
                'content': '',
                'personalization': {},
                'recommendations': []
            }
            
            # Obtener estructura de contenido
            content_structure = template.content_structure
            
            # Renderizar subject
            if 'subject' in content_structure:
                rendered_content['subject'] = await self._render_text(
                    content_structure['subject'], context
                )
            
            # Renderizar contenido principal
            if 'content' in content_structure:
                rendered_content['content'] = await self._render_content(
                    content_structure['content'], context
                )
            
            # Aplicar personalización basada en AURA
            if template.metadata.get('aura_integration'):
                personalization = await self._apply_aura_personalization(template, context)
                rendered_content['personalization'] = personalization
            
            # Obtener recomendaciones
            recommendations = await self._get_template_recommendations(template, context)
            rendered_content['recommendations'] = recommendations
            
            return rendered_content
            
        except Exception as e:
            self.logger.error(f"Error renderizando plantilla: {str(e)}")
            return {}
    
    async def _render_text(self, text_template: str, context: Dict[str, Any]) -> str:
        """
        Renderiza texto con variables de contexto.
        """
        try:
            rendered_text = text_template
            
            # Reemplazar variables de contexto
            for key, value in context.items():
                placeholder = f'{{{key}}}'
                if placeholder in rendered_text:
                    rendered_text = rendered_text.replace(placeholder, str(value))
            
            return rendered_text
            
        except Exception as e:
            self.logger.error(f"Error renderizando texto: {str(e)}")
            return text_template
    
    async def _render_content(self, content_structure: Dict[str, Any], context: Dict[str, Any]) -> str:
        """
        Renderiza estructura de contenido compleja.
        """
        try:
            if isinstance(content_structure, str):
                return await self._render_text(content_structure, context)
            
            elif isinstance(content_structure, dict):
                rendered_content = {}
                
                for key, value in content_structure.items():
                    if isinstance(value, str):
                        rendered_content[key] = await self._render_text(value, context)
                    elif isinstance(value, dict):
                        rendered_content[key] = await self._render_content(value, context)
                    elif isinstance(value, list):
                        rendered_content[key] = []
                        for item in value:
                            if isinstance(item, str):
                                rendered_content[key].append(await self._render_text(item, context))
                            elif isinstance(item, dict):
                                rendered_content[key].append(await self._render_content(item, context))
                            else:
                                rendered_content[key].append(item)
                    else:
                        rendered_content[key] = value
                
                return rendered_content
            
            else:
                return content_structure
            
        except Exception as e:
            self.logger.error(f"Error renderizando contenido: {str(e)}")
            return content_structure
    
    async def _apply_aura_personalization(self, template: ContentTemplate, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Aplica personalización basada en AURA.
        """
        try:
            personalization = {
                'tone': 'professional',
                'style': 'formal',
                'urgency_level': 'medium',
                'personalization_level': 'basic',
                'recommended_timing': 'morning',
                'channel_preference': 'email'
            }
            
            # Obtener recomendaciones de AURA
            aura_recommendations = await self.aura_engine.get_content_personalization(
                template_id=template.id,
                context=context,
                business_unit=self.business_unit
            )
            
            if aura_recommendations:
                personalization.update(aura_recommendations)
            
            return personalization
            
        except Exception as e:
            self.logger.error(f"Error aplicando personalización AURA: {str(e)}")
            return {}
    
    async def _get_template_recommendations(self, template: ContentTemplate, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Obtiene recomendaciones para la plantilla.
        """
        try:
            recommendations = []
            
            # Recomendaciones de timing
            timing_recommendation = await self._get_timing_recommendation(template, context)
            if timing_recommendation:
                recommendations.append(timing_recommendation)
            
            # Recomendaciones de canal
            channel_recommendation = await self._get_channel_recommendation(template, context)
            if channel_recommendation:
                recommendations.append(channel_recommendation)
            
            # Recomendaciones de personalización
            personalization_recommendation = await self._get_personalization_recommendation(template, context)
            if personalization_recommendation:
                recommendations.append(personalization_recommendation)
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error obteniendo recomendaciones: {str(e)}")
            return []
    
    async def _get_timing_recommendation(self, template: ContentTemplate, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Obtiene recomendación de timing.
        """
        try:
            # Análisis basado en comportamiento
            timing_analysis = await self.aura_engine.get_optimal_timing(
                template_id=template.id,
                context=context,
                business_unit=self.business_unit
            )
            
            if timing_analysis:
                return {
                    'type': 'timing',
                    'recommendation': timing_analysis.get('optimal_time', 'Tuesday 10:00 AM'),
                    'reason': timing_analysis.get('reason', 'Basado en análisis de engagement'),
                    'confidence': timing_analysis.get('confidence', 0.8)
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error obteniendo recomendación de timing: {str(e)}")
            return None
    
    async def _get_channel_recommendation(self, template: ContentTemplate, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Obtiene recomendación de canal.
        """
        try:
            # Análisis basado en preferencias culturales
            channel_analysis = await self.cultural_analyzer.get_channel_preference(
                context.get('segment_criteria', {}),
                self.business_unit
            )
            
            if channel_analysis:
                return {
                    'type': 'channel',
                    'recommendation': channel_analysis.get('preferred_channel', 'email'),
                    'reason': channel_analysis.get('reason', 'Basado en preferencias culturales'),
                    'confidence': channel_analysis.get('confidence', 0.7)
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error obteniendo recomendación de canal: {str(e)}")
            return None
    
    async def _get_personalization_recommendation(self, template: ContentTemplate, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Obtiene recomendación de personalización.
        """
        try:
            # Análisis basado en personalidad
            personalization_analysis = await self.personality_analyzer.get_personalization_recommendation(
                context.get('segment_criteria', {}),
                self.business_unit
            )
            
            if personalization_analysis:
                return {
                    'type': 'personalization',
                    'recommendation': personalization_analysis.get('recommendation', 'basic'),
                    'reason': personalization_analysis.get('reason', 'Basado en perfil de personalidad'),
                    'confidence': personalization_analysis.get('confidence', 0.75)
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error obteniendo recomendación de personalización: {str(e)}")
            return None

# Plantillas predefinidas
class PredefinedTemplates:
    """
    Plantillas predefinidas para diferentes tipos de contenido.
    """
    
    @staticmethod
    def get_launch_email_template() -> Dict[str, Any]:
        """Plantilla de email de lanzamiento."""
        return {
            'name': 'Email de Lanzamiento AURA',
            'template_type': 'email',
            'content_structure': {
                'subject': '🚀 {campaign_name}: El Futuro del Reclutamiento ha Llegado',
                'content': {
                    'header': {
                        'title': '¡Bienvenido al Futuro del Reclutamiento!',
                        'subtitle': 'Hemos lanzado {campaign_name} con tecnología AURA avanzada.'
                    },
                    'body': [
                        {
                            'type': 'paragraph',
                            'content': 'Descubre cómo podemos transformar tu proceso de contratación con un 70% de mejora en eficiencia.'
                        },
                        {
                            'type': 'features',
                            'items': [
                                '🤖 IA Predictiva para candidatos',
                                '🎯 Matchmaking inteligente',
                                '⚡ Automatización completa',
                                '📊 Análisis en tiempo real'
                            ]
                        },
                        {
                            'type': 'cta',
                            'text': 'Explorar Ahora',
                            'url': '{landing_url}'
                        }
                    ],
                    'footer': {
                        'text': '¿Preguntas? Contacta con nuestro equipo de soporte.',
                        'contact': '{support_email}'
                    }
                }
            },
            'personalization_variables': [
                'nombre', 'empresa', 'cargo', 'industria', 'campaign_name', 
                'landing_url', 'support_email'
            ]
        }
    
    @staticmethod
    def get_webinar_invitation_template() -> Dict[str, Any]:
        """Plantilla de invitación a webinar."""
        return {
            'name': 'Invitación a Webinar AURA',
            'template_type': 'email',
            'content_structure': {
                'subject': '🎥 Invitación Exclusiva: Webinar {webinar_name}',
                'content': {
                    'header': {
                        'title': 'Te Invitamos a Ver AURA en Acción',
                        'subtitle': 'Únete a nuestro webinar exclusivo donde verás {webinar_name} funcionando en tiempo real.'
                    },
                    'body': [
                        {
                            'type': 'webinar_details',
                            'date': '{webinar_date}',
                            'time': '{webinar_time}',
                            'duration': '60 minutos',
                            'format': 'Online (Zoom)'
                        },
                        {
                            'type': 'agenda',
                            'items': [
                                '🎯 Demo en vivo de AURA',
                                '📊 Casos de éxito reales',
                                '💡 Mejores prácticas',
                                '❓ Preguntas y respuestas',
                                '🎁 Ofertas especiales'
                            ]
                        },
                        {
                            'type': 'cta',
                            'text': 'Registrarse Gratis',
                            'url': '{registration_url}'
                        }
                    ],
                    'footer': {
                        'text': '¡No te pierdas esta oportunidad única!',
                        'reminder': 'Te enviaremos un recordatorio 1 hora antes.'
                    }
                }
            },
            'personalization_variables': [
                'nombre', 'empresa', 'webinar_name', 'webinar_date', 
                'webinar_time', 'registration_url'
            ]
        }
    
    @staticmethod
    def get_social_post_template() -> Dict[str, Any]:
        """Plantilla de post para redes sociales."""
        return {
            'name': 'Post Social AURA',
            'template_type': 'social',
            'content_structure': {
                'platform': '{platform}',
                'content': {
                    'text': '{post_text}',
                    'hashtags': ['{primary_hashtag}', '{secondary_hashtag}', '#huntRED'],
                    'call_to_action': '{cta_text}',
                    'link': '{post_link}'
                },
                'media': {
                    'type': '{media_type}',
                    'url': '{media_url}',
                    'alt_text': '{media_alt_text}'
                }
            },
            'personalization_variables': [
                'platform', 'post_text', 'primary_hashtag', 'secondary_hashtag',
                'cta_text', 'post_link', 'media_type', 'media_url', 'media_alt_text'
            ]
        }
    
    @staticmethod
    def get_landing_page_template() -> Dict[str, Any]:
        """Plantilla de landing page."""
        return {
            'name': 'Landing Page AURA',
            'template_type': 'landing',
            'content_structure': {
                'hero_section': {
                    'headline': '{hero_headline}',
                    'subheadline': '{hero_subheadline}',
                    'cta_text': '{hero_cta_text}',
                    'cta_url': '{hero_cta_url}'
                },
                'features_section': {
                    'title': 'Características Principales',
                    'features': [
                        {
                            'title': 'IA Predictiva',
                            'description': 'AURA analiza patrones y predice el éxito de candidatos',
                            'icon': '🤖'
                        },
                        {
                            'title': 'Matchmaking Inteligente',
                            'description': 'Encuentra el candidato perfecto con 9 factores de análisis',
                            'icon': '🎯'
                        },
                        {
                            'title': 'Automatización Completa',
                            'description': 'Desde screening hasta onboarding con firma digital',
                            'icon': '⚡'
                        }
                    ]
                },
                'testimonials_section': {
                    'title': 'Lo que Dicen Nuestros Clientes',
                    'testimonials': [
                        {
                            'quote': '{testimonial_quote}',
                            'author': '{testimonial_author}',
                            'company': '{testimonial_company}'
                        }
                    ]
                },
                'cta_section': {
                    'title': '¿Listo para Transformar tu Reclutamiento?',
                    'subtitle': 'Únete a cientos de empresas que ya confían en AURA',
                    'cta_text': '{final_cta_text}',
                    'cta_url': '{final_cta_url}'
                }
            },
            'personalization_variables': [
                'hero_headline', 'hero_subheadline', 'hero_cta_text', 'hero_cta_url',
                'testimonial_quote', 'testimonial_author', 'testimonial_company',
                'final_cta_text', 'final_cta_url'
            ]
        }
    
    @staticmethod
    def get_retargeting_ad_template() -> Dict[str, Any]:
        """Plantilla de anuncio de retargeting."""
        return {
            'name': 'Anuncio Retargeting AURA',
            'template_type': 'ad',
            'content_structure': {
                'platform': '{ad_platform}',
                'headline': '{ad_headline}',
                'description': '{ad_description}',
                'cta': '{ad_cta}',
                'target_audience': '{target_audience}',
                'budget_recommendation': '{budget_amount}',
                'creative_elements': {
                    'image_url': '{ad_image_url}',
                    'video_url': '{ad_video_url}',
                    'logo_url': '{ad_logo_url}'
                }
            },
            'personalization_variables': [
                'ad_platform', 'ad_headline', 'ad_description', 'ad_cta',
                'target_audience', 'budget_amount', 'ad_image_url', 
                'ad_video_url', 'ad_logo_url'
            ]
        } 