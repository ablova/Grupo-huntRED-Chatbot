"""
Sistema de Triggers Automáticos para Evaluaciones y Gamificación
Dispara emails, notificaciones y acciones automáticas basadas en eventos del sistema.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from django.utils import timezone
from asgiref.sync import sync_to_async

from app.models import Person, BusinessUnit, Company
from app.ats.chatbot.workflow.assessments.nom35.models import AssessmentNOM35
from app.ats.integrations.services.email_campaigns import EmailCampaignService
from app.ats.gamification.models import Badge, UserBadge
from app.ats.pricing.models import DiscountCoupon
from app.ats.integrations.notifications.core.service import NotificationService

logger = logging.getLogger(__name__)

class AssessmentTriggerManager:
    """Gestor de triggers automáticos para evaluaciones."""
    
    def __init__(self, business_unit: BusinessUnit):
        self.business_unit = business_unit
        self.email_service = EmailCampaignService(business_unit)
        self.notification_service = NotificationService()
    
    async def trigger_nom35_completion(self, assessment: AssessmentNOM35):
        """
        Trigger cuando se completa una evaluación NOM 35.
        
        Args:
            assessment: Instancia de AssessmentNOM35 completada
        """
        try:
            # Obtener datos de la evaluación
            assessment_data = {
                'score': assessment.score,
                'risk_level': assessment.risk_level,
                'date_taken': assessment.date_taken,
                'responses': assessment.responses
            }
            
            # Enviar email de completación
            email_result = await self.email_service.send_nom35_completion_email(
                recipient=assessment.person,
                assessment_data=assessment_data,
                client_email=self._get_client_email(assessment.person)
            )
            
            # Disparar badge de completación
            await self._trigger_completion_badge(assessment.person, "nom35")
            
            # Programar evaluación de seguimiento (3 meses)
            await self._schedule_followup_assessment(assessment.person, 90)
            
            # Generar reporte automático
            await self._generate_automated_report(assessment)
            
            logger.info(f"NOM35 completion triggered for person {assessment.person.id}")
            
        except Exception as e:
            logger.error(f"Error triggering NOM35 completion: {str(e)}", exc_info=True)
    
    async def trigger_assessment_upsell(self, person: Person, completed_assessment: str):
        """
        Trigger para upsell de evaluaciones adicionales.
        
        Args:
            person: Persona que completó la evaluación
            completed_assessment: Tipo de evaluación completada
        """
        try:
            # Determinar evaluación recomendada
            recommended_assessment = self._get_recommended_assessment(completed_assessment)
            
            if recommended_assessment:
                # Enviar email de upsell
                await self.email_service.send_assessment_upsell_email(
                    recipient=person,
                    assessment_type=recommended_assessment,
                    trigger_event=f"{completed_assessment}_completion"
                )
                
                # Disparar badge de explorador
                await self._trigger_explorer_badge(person)
            
            logger.info(f"Assessment upsell triggered for person {person.id}")
            
        except Exception as e:
            logger.error(f"Error triggering assessment upsell: {str(e)}", exc_info=True)
    
    async def trigger_badge_achievement(self, person: Person, badge: Badge, achievement_type: str):
        """
        Trigger cuando se gana un badge.
        
        Args:
            person: Persona que ganó el badge
            badge: Badge ganado
            achievement_type: Tipo de logro
        """
        try:
            # Enviar email de gamificación
            await self.email_service.send_gamification_email(
                recipient=person,
                badge=badge,
                achievement_type=achievement_type
            )
            
            # Disparar notificación push
            await self._send_badge_notification(person, badge)
            
            # Verificar si desbloquea algún logro especial
            await self._check_special_achievements(person, badge)
            
            logger.info(f"Badge achievement triggered for person {person.id}")
            
        except Exception as e:
            logger.error(f"Error triggering badge achievement: {str(e)}", exc_info=True)
    
    async def trigger_onboarding_sequence(self, person: Person, step: int, total_steps: int):
        """
        Trigger para secuencia de onboarding.
        
        Args:
            person: Persona en onboarding
            step: Paso actual
            total_steps: Total de pasos
        """
        try:
            # Enviar email de onboarding
            await self.email_service.send_onboarding_sequence_email(
                recipient=person,
                onboarding_step=step,
                total_steps=total_steps
            )
            
            # Disparar badge de progreso
            if step == 1:
                await self._trigger_onboarding_badge(person, "started")
            elif step == total_steps:
                await self._trigger_onboarding_badge(person, "completed")
            
            logger.info(f"Onboarding sequence triggered for person {person.id}")
            
        except Exception as e:
            logger.error(f"Error triggering onboarding sequence: {str(e)}", exc_info=True)
    
    async def trigger_engagement_reminder(self, person: Person, days_inactive: int):
        """
        Trigger para recordatorios de engagement.
        
        Args:
            person: Persona inactiva
            days_inactive: Días de inactividad
        """
        try:
            # Determinar tipo de recordatorio
            reminder_type = self._get_reminder_type(days_inactive)
            
            # Generar cupón de re-engagement
            reengagement_coupon = await self._generate_reengagement_coupon(person, days_inactive)
            
            # Enviar notificación
            context = {
                'recipient_name': person.nombre,
                'days_inactive': days_inactive,
                'coupon_code': reengagement_coupon.code if reengagement_coupon else None,
                'coupon_discount': reengagement_coupon.discount_percentage if reengagement_coupon else 15,
                'reminder_type': reminder_type,
                'business_unit': self.business_unit.name
            }
            
            await self.notification_service.send_notification(
                recipient=person,
                template_name='emails/engagement_reminder.html',
                context=context,
                notification_type='engagement_reminder',
                business_unit=self.business_unit,
                channels=['email', 'whatsapp']
            )
            
            logger.info(f"Engagement reminder triggered for person {person.id}")
            
        except Exception as e:
            logger.error(f"Error triggering engagement reminder: {str(e)}", exc_info=True)
    
    # Métodos auxiliares
    
    async def _trigger_completion_badge(self, person: Person, assessment_type: str):
        """Dispara badge de completación de evaluación."""
        try:
            badge_name = f"{assessment_type.upper()}_COMPLETION"
            badge = await sync_to_async(Badge.objects.filter(
                name=badge_name,
                business_unit=self.business_unit,
                is_active=True
            ).first)()
            
            if badge:
                user_badge, created = await sync_to_async(UserBadge.objects.get_or_create)(
                    user=person,
                    badge=badge,
                    defaults={'earned_date': timezone.now()}
                )
                
                if created:
                    await self.trigger_badge_achievement(person, badge, "assessment_completion")
                    
        except Exception as e:
            logger.error(f"Error triggering completion badge: {str(e)}")
    
    async def _trigger_explorer_badge(self, person: Person):
        """Dispara badge de explorador de evaluaciones."""
        try:
            # Contar evaluaciones completadas
            completed_assessments = await sync_to_async(AssessmentNOM35.objects.filter(
                person=person,
                business_unit=self.business_unit
            ).count)()
            
            # Determinar badge basado en cantidad
            if completed_assessments >= 3:
                badge_name = "ASSESSMENT_EXPLORER"
            elif completed_assessments >= 2:
                badge_name = "ASSESSMENT_LEARNER"
            else:
                return
            
            badge = await sync_to_async(Badge.objects.filter(
                name=badge_name,
                business_unit=self.business_unit,
                is_active=True
            ).first)()
            
            if badge:
                user_badge, created = await sync_to_async(UserBadge.objects.get_or_create)(
                    user=person,
                    badge=badge,
                    defaults={'earned_date': timezone.now()}
                )
                
                if created:
                    await self.trigger_badge_achievement(person, badge, "exploration")
                    
        except Exception as e:
            logger.error(f"Error triggering explorer badge: {str(e)}")
    
    async def _trigger_onboarding_badge(self, person: Person, status: str):
        """Dispara badge de onboarding."""
        try:
            badge_name = f"ONBOARDING_{status.upper()}"
            badge = await sync_to_async(Badge.objects.filter(
                name=badge_name,
                business_unit=self.business_unit,
                is_active=True
            ).first)()
            
            if badge:
                user_badge, created = await sync_to_async(UserBadge.objects.get_or_create)(
                    user=person,
                    badge=badge,
                    defaults={'earned_date': timezone.now()}
                )
                
                if created:
                    await self.trigger_badge_achievement(person, badge, "onboarding")
                    
        except Exception as e:
            logger.error(f"Error triggering onboarding badge: {str(e)}")
    
    async def _schedule_followup_assessment(self, person: Person, days_delay: int):
        """Programa evaluación de seguimiento."""
        try:
            followup_date = timezone.now() + timedelta(days=days_delay)
            
            # Crear evaluación programada
            scheduled_assessment = AssessmentNOM35(
                person=person,
                business_unit=self.business_unit,
                scheduled_by_onboarding=True,
                scheduled_date=followup_date,
                score=0,
                risk_level='pendiente'
            )
            await sync_to_async(scheduled_assessment.save)()
            
            # Programar tarea de envío
            await self._schedule_assessment_reminder(person, followup_date)
            
        except Exception as e:
            logger.error(f"Error scheduling followup assessment: {str(e)}")
    
    async def _generate_automated_report(self, assessment: AssessmentNOM35):
        """Genera reporte automático de la evaluación."""
        try:
            # Aquí implementarías la lógica de generación de reporte
            # Por ejemplo, crear un PDF con los resultados
            report_data = {
                'assessment_id': assessment.id,
                'person_name': assessment.person.nombre,
                'score': assessment.score,
                'risk_level': assessment.risk_level,
                'date_taken': assessment.date_taken,
                'recommendations': self._get_nom35_recommendations(assessment)
            }
            
            # Generar PDF y enviar por email
            # await self._generate_and_send_report(report_data)
            
        except Exception as e:
            logger.error(f"Error generating automated report: {str(e)}")
    
    async def _send_badge_notification(self, person: Person, badge: Badge):
        """Envía notificación push de badge."""
        try:
            context = {
                'badge_name': badge.name,
                'badge_description': badge.description,
                'badge_icon': badge.icon_url
            }
            
            await self.notification_service.send_notification(
                recipient=person,
                template_name='notifications/badge_achievement.html',
                context=context,
                notification_type='badge_push',
                business_unit=self.business_unit,
                channels=['push']
            )
            
        except Exception as e:
            logger.error(f"Error sending badge notification: {str(e)}")
    
    async def _check_special_achievements(self, person: Person, badge: Badge):
        """Verifica si el badge desbloquea logros especiales."""
        try:
            # Contar badges totales
            total_badges = await sync_to_async(UserBadge.objects.filter(
                user=person,
                is_active=True
            ).count)()
            
            # Verificar logros especiales
            special_achievements = {
                5: "BADGE_COLLECTOR",
                10: "BADGE_MASTER",
                20: "BADGE_LEGEND"
            }
            
            if total_badges in special_achievements:
                special_badge_name = special_achievements[total_badges]
                special_badge = await sync_to_async(Badge.objects.filter(
                    name=special_badge_name,
                    business_unit=self.business_unit,
                    is_active=True
                ).first)()
                
                if special_badge:
                    user_badge, created = await sync_to_async(UserBadge.objects.get_or_create)(
                        user=person,
                        badge=special_badge,
                        defaults={'earned_date': timezone.now()}
                    )
                    
                    if created:
                        await self.trigger_badge_achievement(person, special_badge, "special_achievement")
                        
        except Exception as e:
            logger.error(f"Error checking special achievements: {str(e)}")
    
    async def _generate_reengagement_coupon(self, person: Person, days_inactive: int) -> Optional[DiscountCoupon]:
        """Genera cupón de re-engagement."""
        try:
            # Determinar descuento basado en días inactivo
            if days_inactive >= 30:
                discount = 25
            elif days_inactive >= 15:
                discount = 20
            else:
                discount = 15
            
            coupon = DiscountCoupon(
                code=f"REENGAGE_{person.id}_{int(timezone.now().timestamp())}",
                discount_percentage=discount,
                valid_from=timezone.now(),
                valid_until=timezone.now() + timedelta(days=15),
                max_uses=1,
                business_unit=self.business_unit,
                description=f"Cupón de re-engagement ({days_inactive} días inactivo)"
            )
            await sync_to_async(coupon.save)()
            
            return coupon
            
        except Exception as e:
            logger.error(f"Error generating reengagement coupon: {str(e)}")
            return None
    
    def _get_client_email(self, person: Person) -> Optional[str]:
        """Obtiene email del cliente asociado."""
        try:
            # Lógica para obtener email del cliente
            # Esto dependerá de tu modelo de datos
            return None
        except Exception as e:
            logger.error(f"Error getting client email: {str(e)}")
            return None
    
    def _get_recommended_assessment(self, completed_assessment: str) -> Optional[str]:
        """Obtiene la evaluación recomendada basada en la completada."""
        recommendations = {
            'nom35': 'cultural_fit',
            'cultural_fit': 'professional_dna',
            'professional_dna': 'personality',
            'personality': 'leadership'
        }
        
        return recommendations.get(completed_assessment)
    
    def _get_reminder_type(self, days_inactive: int) -> str:
        """Determina el tipo de recordatorio basado en días inactivo."""
        if days_inactive >= 30:
            return "urgent"
        elif days_inactive >= 15:
            return "moderate"
        else:
            return "gentle"
    
    def _get_nom35_recommendations(self, assessment: AssessmentNOM35) -> List[str]:
        """Obtiene recomendaciones basadas en resultados NOM 35."""
        risk_level = assessment.risk_level
        
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
    
    async def _schedule_assessment_reminder(self, person: Person, reminder_date: datetime):
        """Programa recordatorio de evaluación."""
        try:
            # Aquí implementarías la lógica para programar el recordatorio
            # Por ejemplo, usando Celery o un sistema de tareas
            pass
        except Exception as e:
            logger.error(f"Error scheduling assessment reminder: {str(e)}") 