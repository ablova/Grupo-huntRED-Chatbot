"""
Sistema de Campañas de Email con CTAs Dinámicos para huntRED
Integra cupones, bundles y gamificación para maximizar conversiones.
"""

import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from django.template.loader import render_to_string
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.utils import timezone
from asgiref.sync import sync_to_async

from app.models import Person, BusinessUnit, Company
from app.ats.pricing.models import DiscountCoupon
from app.ats.gamification.models import Badge, UserBadge
from app.ats.integrations.notifications.core.service import NotificationService

logger = logging.getLogger(__name__)

class EmailCampaignService:
    """Servicio para gestión de campañas de email con CTAs dinámicos."""
    
    def __init__(self, business_unit: BusinessUnit):
        self.business_unit = business_unit
        self.notification_service = NotificationService()
    
    async def send_nom35_completion_email(
        self, 
        recipient: Person, 
        assessment_data: Dict[str, Any],
        client_email: Optional[str] = None
    ) -> Dict[str, bool]:
        """
        Envía email de completación NOM 35 con CTA para upsell.
        
        Args:
            recipient: Persona que completó la evaluación
            assessment_data: Datos de la evaluación completada
            client_email: Email del cliente para notificación adicional
        """
        try:
            # Generar cupón de descuento para upsell
            coupon = await self._generate_upsell_coupon(recipient, "nom35_completion")
            
            # Preparar contexto con CTA dinámico
            context = {
                'recipient_name': recipient.nombre,
                'assessment_date': timezone.now().strftime('%d/%m/%Y'),
                'risk_level': assessment_data.get('risk_level', 'bajo'),
                'score': assessment_data.get('score', 0),
                'coupon_code': coupon.code if coupon else None,
                'coupon_discount': coupon.discount_percentage if coupon else 20,
                'upsell_url': f"{settings.SITE_URL}/assessments/team?coupon={coupon.code}" if coupon else f"{settings.SITE_URL}/assessments/team",
                'business_unit': self.business_unit.name,
                'cta_text': self._get_personalized_cta(recipient, "nom35_completion"),
                'badges': await self._get_user_badges(recipient),
                'recommendations': self._get_nom35_recommendations(assessment_data)
            }
            
            # Enviar email al empleado
            employee_result = await self.notification_service.send_notification(
                recipient=recipient,
                template_name='emails/nom35_completion.html',
                context=context,
                notification_type='nom35_completion',
                business_unit=self.business_unit,
                channels=['email']
            )
            
            # Enviar notificación al cliente si se proporciona
            client_result = {}
            if client_email:
                client_context = {
                    'client_name': 'Cliente',
                    'employee_name': recipient.nombre,
                    'assessment_date': timezone.now().strftime('%d/%m/%Y'),
                    'risk_level': assessment_data.get('risk_level', 'bajo'),
                    'upsell_url': f"{settings.SITE_URL}/assessments/enterprise?coupon={coupon.code}" if coupon else f"{settings.SITE_URL}/assessments/enterprise",
                    'cta_text': 'Activa NOM 35 para todo tu equipo',
                    'business_unit': self.business_unit.name
                }
                
                client_result = await self._send_client_notification(
                    client_email, 
                    'emails/nom35_client_notification.html',
                    client_context
                )
            
            return {
                'employee_email': employee_result.get('email', False),
                'client_email': client_result.get('email', False) if client_result else False
            }
            
        except Exception as e:
            logger.error(f"Error sending NOM35 completion email: {str(e)}", exc_info=True)
            return {'employee_email': False, 'client_email': False}
    
    async def send_assessment_upsell_email(
        self, 
        recipient: Person, 
        assessment_type: str,
        trigger_event: str
    ) -> Dict[str, bool]:
        """
        Envía email de upsell para evaluaciones adicionales.
        
        Args:
            recipient: Destinatario del email
            assessment_type: Tipo de evaluación (cultural_fit, professional_dna, etc.)
            trigger_event: Evento que disparó el email
        """
        try:
            # Generar cupón específico para el tipo de evaluación
            coupon = await self._generate_upsell_coupon(recipient, f"{assessment_type}_upsell")
            
            # Obtener bundle recomendado
            recommended_bundle = await self._get_recommended_bundle(assessment_type)
            
            context = {
                'recipient_name': recipient.nombre,
                'assessment_type': assessment_type,
                'assessment_name': self._get_assessment_display_name(assessment_type),
                'coupon_code': coupon.code if coupon else None,
                'coupon_discount': coupon.discount_percentage if coupon else 15,
                'bundle_name': recommended_bundle.name if recommended_bundle else None,
                'bundle_price': recommended_bundle.price if recommended_bundle else None,
                'upsell_url': f"{settings.SITE_URL}/assessments/{assessment_type}?coupon={coupon.code}" if coupon else f"{settings.SITE_URL}/assessments/{assessment_type}",
                'business_unit': self.business_unit.name,
                'cta_text': self._get_personalized_cta(recipient, f"{assessment_type}_upsell"),
                'badges': await self._get_user_badges(recipient),
                'benefits': self._get_assessment_benefits(assessment_type)
            }
            
            return await self.notification_service.send_notification(
                recipient=recipient,
                template_name='emails/assessment_upsell.html',
                context=context,
                notification_type=f'{assessment_type}_upsell',
                business_unit=self.business_unit,
                channels=['email']
            )
            
        except Exception as e:
            logger.error(f"Error sending assessment upsell email: {str(e)}", exc_info=True)
            return {'email': False}
    
    async def send_gamification_email(
        self, 
        recipient: Person, 
        badge: Badge,
        achievement_type: str
    ) -> Dict[str, bool]:
        """
        Envía email de gamificación con badge y CTA para siguiente nivel.
        
        Args:
            recipient: Persona que ganó el badge
            badge: Badge ganado
            achievement_type: Tipo de logro
        """
        try:
            # Obtener siguiente badge disponible
            next_badge = await self._get_next_badge(recipient, badge)
            
            # Generar cupón de celebración
            celebration_coupon = await self._generate_upsell_coupon(recipient, "badge_achievement")
            
            context = {
                'recipient_name': recipient.nombre,
                'badge_name': badge.name,
                'badge_description': badge.description,
                'badge_icon': badge.icon_url,
                'achievement_type': achievement_type,
                'next_badge': next_badge.name if next_badge else None,
                'next_badge_description': next_badge.description if next_badge else None,
                'celebration_coupon': celebration_coupon.code if celebration_coupon else None,
                'celebration_discount': celebration_coupon.discount_percentage if celebration_coupon else 10,
                'cta_text': self._get_personalized_cta(recipient, "badge_achievement"),
                'business_unit': self.business_unit.name,
                'total_badges': await self._get_user_badge_count(recipient)
            }
            
            return await self.notification_service.send_notification(
                recipient=recipient,
                template_name='emails/badge_achievement.html',
                context=context,
                notification_type='badge_achievement',
                business_unit=self.business_unit,
                channels=['email']
            )
            
        except Exception as e:
            logger.error(f"Error sending gamification email: {str(e)}", exc_info=True)
            return {'email': False}
    
    async def send_onboarding_sequence_email(
        self, 
        recipient: Person, 
        onboarding_step: int,
        total_steps: int
    ) -> Dict[str, bool]:
        """
        Envía email de secuencia de onboarding con CTA para siguiente paso.
        
        Args:
            recipient: Persona en onboarding
            onboarding_step: Paso actual del onboarding
            total_steps: Total de pasos en el onboarding
        """
        try:
            # Determinar siguiente paso y CTA apropiado
            next_step_info = self._get_onboarding_step_info(onboarding_step + 1)
            
            # Generar cupón de bienvenida si es el primer paso
            welcome_coupon = None
            if onboarding_step == 1:
                welcome_coupon = await self._generate_upsell_coupon(recipient, "onboarding_welcome")
            
            context = {
                'recipient_name': recipient.nombre,
                'current_step': onboarding_step,
                'total_steps': total_steps,
                'progress_percentage': int((onboarding_step / total_steps) * 100),
                'next_step_title': next_step_info.get('title', 'Siguiente paso'),
                'next_step_description': next_step_info.get('description', ''),
                'welcome_coupon': welcome_coupon.code if welcome_coupon else None,
                'welcome_discount': welcome_coupon.discount_percentage if welcome_coupon else 25,
                'cta_text': self._get_personalized_cta(recipient, "onboarding_step"),
                'business_unit': self.business_unit.name,
                'next_step_url': next_step_info.get('url', f"{settings.SITE_URL}/onboarding/step/{onboarding_step + 1}")
            }
            
            return await self.notification_service.send_notification(
                recipient=recipient,
                template_name='emails/onboarding_step.html',
                context=context,
                notification_type='onboarding_step',
                business_unit=self.business_unit,
                channels=['email']
            )
            
        except Exception as e:
            logger.error(f"Error sending onboarding email: {str(e)}", exc_info=True)
            return {'email': False}
    
    # Métodos auxiliares
    
    async def _generate_upsell_coupon(self, recipient: Person, trigger_type: str) -> Optional[DiscountCoupon]:
        """Genera un cupón de descuento para upsell."""
        try:
            # Determinar descuento basado en el tipo de trigger
            discount_mapping = {
                'nom35_completion': 20,
                'cultural_fit_upsell': 15,
                'professional_dna_upsell': 15,
                'personality_upsell': 10,
                'badge_achievement': 10,
                'onboarding_welcome': 25
            }
            
            discount = discount_mapping.get(trigger_type, 10)
            
            # Crear cupón
            coupon = DiscountCoupon(
                code=f"UPSELL_{trigger_type.upper()}_{recipient.id}_{int(timezone.now().timestamp())}",
                discount_percentage=discount,
                valid_from=timezone.now(),
                valid_until=timezone.now() + timedelta(days=30),
                max_uses=1,
                business_unit=self.business_unit,
                description=f"Cupón de {trigger_type.replace('_', ' ').title()}"
            )
            await sync_to_async(coupon.save)()
            
            return coupon
            
        except Exception as e:
            logger.error(f"Error generating upsell coupon: {str(e)}")
            return None
    
    async def _get_recommended_bundle(self, assessment_type: str) -> Optional[Bundle]:
        """Obtiene el bundle recomendado para el tipo de evaluación."""
        try:
            # Lógica para recomendar bundle basado en assessment_type
            bundle_mapping = {
                'cultural_fit': 'Cultural Excellence Bundle',
                'professional_dna': 'Professional Development Bundle',
                'personality': 'Personality Insights Bundle'
            }
            
            bundle_name = bundle_mapping.get(assessment_type)
            if bundle_name:
                return await sync_to_async(Bundle.objects.filter(
                    name=bundle_name,
                    business_unit=self.business_unit,
                    is_active=True
                ).first)()
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting recommended bundle: {str(e)}")
            return None
    
    async def _get_user_badges(self, recipient: Person) -> List[Dict[str, Any]]:
        """Obtiene los badges del usuario."""
        try:
            user_badges = await sync_to_async(list)(
                UserBadge.objects.filter(
                    user=recipient,
                    is_active=True
                ).select_related('badge')
            )
            
            return [
                {
                    'name': ub.badge.name,
                    'description': ub.badge.description,
                    'icon': ub.badge.icon_url,
                    'earned_date': ub.earned_date.strftime('%d/%m/%Y')
                }
                for ub in user_badges
            ]
            
        except Exception as e:
            logger.error(f"Error getting user badges: {str(e)}")
            return []
    
    async def _get_next_badge(self, recipient: Person, current_badge: Badge) -> Optional[Badge]:
        """Obtiene el siguiente badge disponible para el usuario."""
        try:
            # Lógica para determinar siguiente badge
            earned_badges = await sync_to_async(list)(
                UserBadge.objects.filter(user=recipient).values_list('badge_id', flat=True)
            )
            
            next_badge = await sync_to_async(Badge.objects.filter(
                business_unit=self.business_unit,
                is_active=True,
                order__gt=current_badge.order
            ).exclude(id__in=earned_badges).first)()
            
            return next_badge
            
        except Exception as e:
            logger.error(f"Error getting next badge: {str(e)}")
            return None
    
    async def _get_user_badge_count(self, recipient: Person) -> int:
        """Obtiene el número total de badges del usuario."""
        try:
            return await sync_to_async(UserBadge.objects.filter(
                user=recipient,
                is_active=True
            ).count)()
        except Exception as e:
            logger.error(f"Error getting badge count: {str(e)}")
            return 0
    
    def _get_personalized_cta(self, recipient: Person, context: str) -> str:
        """Genera un CTA personalizado basado en el contexto."""
        cta_mapping = {
            'nom35_completion': 'Activa evaluaciones para tu equipo',
            'cultural_fit_upsell': 'Descubre tu fit cultural',
            'professional_dna_upsell': 'Revela tu ADN profesional',
            'personality_upsell': 'Conoce tu personalidad laboral',
            'badge_achievement': 'Continúa tu crecimiento',
            'onboarding_step': 'Completa tu onboarding'
        }
        
        return cta_mapping.get(context, 'Ver más')
    
    def _get_assessment_display_name(self, assessment_type: str) -> str:
        """Obtiene el nombre de display para el tipo de evaluación."""
        display_names = {
            'cultural_fit': 'Cultural Fit',
            'professional_dna': 'Professional DNA',
            'personality': 'Personality Assessment',
            'nom35': 'NOM 35'
        }
        
        return display_names.get(assessment_type, assessment_type.title())
    
    def _get_assessment_benefits(self, assessment_type: str) -> List[str]:
        """Obtiene los beneficios del tipo de evaluación."""
        benefits_mapping = {
            'cultural_fit': [
                'Mejora la retención de empleados',
                'Reduce conflictos organizacionales',
                'Aumenta la productividad del equipo'
            ],
            'professional_dna': [
                'Identifica líderes potenciales',
                'Optimiza la asignación de roles',
                'Mejora el desarrollo profesional'
            ],
            'personality': [
                'Mejora la comunicación del equipo',
                'Optimiza la dinámica grupal',
                'Aumenta la satisfacción laboral'
            ]
        }
        
        return benefits_mapping.get(assessment_type, ['Beneficios personalizados'])
    
    def _get_nom35_recommendations(self, assessment_data: Dict[str, Any]) -> List[str]:
        """Obtiene recomendaciones basadas en los resultados NOM 35."""
        risk_level = assessment_data.get('risk_level', 'bajo')
        
        recommendations = {
            'bajo': [
                'Mantén las buenas prácticas actuales',
                'Considera evaluaciones de desarrollo',
                'Implementa programas de reconocimiento'
            ],
            'medio': [
                'Revisa las políticas de carga de trabajo',
                'Implementa programas de bienestar',
                'Mejora la comunicación organizacional'
            ],
            'alto': [
                'Prioriza intervenciones inmediatas',
                'Implementa programas de apoyo psicológico',
                'Revisa la estructura organizacional'
            ]
        }
        
        return recommendations.get(risk_level, ['Consulta con un especialista'])
    
    def _get_onboarding_step_info(self, step: int) -> Dict[str, str]:
        """Obtiene información del paso de onboarding."""
        steps_info = {
            2: {
                'title': 'Completa tu perfil',
                'description': 'Agrega información adicional para personalizar tu experiencia',
                'url': f"{settings.SITE_URL}/onboarding/profile"
            },
            3: {
                'title': 'Configura notificaciones',
                'description': 'Elige cómo quieres recibir actualizaciones importantes',
                'url': f"{settings.SITE_URL}/onboarding/notifications"
            },
            4: {
                'title': 'Explora evaluaciones',
                'description': 'Conoce las evaluaciones disponibles para tu desarrollo',
                'url': f"{settings.SITE_URL}/onboarding/assessments"
            }
        }
        
        return steps_info.get(step, {
            'title': 'Siguiente paso',
            'description': 'Continúa con tu onboarding',
            'url': f"{settings.SITE_URL}/onboarding"
        })
    
    async def _send_client_notification(
        self, 
        client_email: str, 
        template_name: str, 
        context: Dict[str, Any]
    ) -> Dict[str, bool]:
        """Envía notificación al cliente."""
        try:
            # Crear persona temporal para el cliente
            temp_recipient = Person(
                email=client_email,
                nombre=context.get('client_name', 'Cliente')
            )
            
            return await self.notification_service.send_notification(
                recipient=temp_recipient,
                template_name=template_name,
                context=context,
                notification_type='client_notification',
                business_unit=self.business_unit,
                channels=['email']
            )
            
        except Exception as e:
            logger.error(f"Error sending client notification: {str(e)}")
            return {'email': False} 