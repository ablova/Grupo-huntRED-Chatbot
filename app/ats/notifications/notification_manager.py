"""
Gestor de notificaciones para el ciclo de reclutamiento.
Coordina el envío de notificaciones a los diferentes actores en cada etapa del proceso.
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
from enum import Enum

from app.models import Person, BusinessUnit, Vacante
from app.ats.integrations.notifications.channels import get_channel_class

logger = logging.getLogger(__name__)

class ProcessStage(Enum):
    """Etapas del proceso de reclutamiento."""
    INITIAL_CONTACT = "initial_contact"
    SCREENING = "screening"
    INTERVIEW = "interview"
    ASSESSMENT = "assessment"
    REFERENCE_CHECK = "reference_check"
    OFFER = "offer"
    CONTRACTING = "contracting"
    ONBOARDING = "onboarding"
    REJECTION = "rejection"

class NotificationManager:
    """Gestor de notificaciones para el ciclo de reclutamiento."""
    
    def __init__(self):
        self.channels = {}
        # Inicializar canales disponibles dinámicamente
        channel_names = ['whatsapp', 'telegram', 'sms', 'slack']
        for channel_name in channel_names:
            channel_class = get_channel_class(channel_name)
            if channel_class:
                self.channels[channel_name] = channel_class()
        
    async def notify_process_update(
        self,
        stage: ProcessStage,
        candidate: Person,
        job: Vacante,
        business_unit: BusinessUnit,
        metadata: Optional[Dict] = None
    ):
        """
        Notifica actualizaciones del proceso a todos los actores relevantes.
        
        Args:
            stage: Etapa actual del proceso
            candidate: Candidato involucrado
            job: Vacante relacionada
            business_unit: Unidad de negocio
            metadata: Datos adicionales específicos de la etapa
        """
        try:
            # 1. Notificar al candidato
            await self._notify_candidate(stage, candidate, job, metadata)
            
            # 2. Notificar al consultor
            await self._notify_consultant(stage, candidate, job, business_unit, metadata)
            
            # 3. Notificar a los stakeholders del cliente
            await self._notify_client_stakeholders(stage, candidate, job, business_unit, metadata)
            
            # 4. Notificar referencias si es necesario
            if stage == ProcessStage.REFERENCE_CHECK:
                await self._notify_references(candidate, job, metadata)
                
            # 5. Notificar al equipo interno si es necesario
            await self._notify_internal_team(stage, candidate, job, business_unit, metadata)
            
        except Exception as e:
            logger.error(f"Error en notificación de proceso: {str(e)}")
            # Notificar error al equipo interno
            await self._notify_error(stage, candidate, job, str(e))
            
    async def _notify_candidate(
        self,
        stage: ProcessStage,
        candidate: Person,
        job: Vacante,
        metadata: Optional[Dict]
    ):
        """Notifica al candidato según la etapa del proceso."""
        templates = {
            ProcessStage.INITIAL_CONTACT: {
                'subject': 'Inicio de proceso de selección',
                'template': 'candidate/initial_contact.html',
                'channels': ['email', 'whatsapp']
            },
            ProcessStage.SCREENING: {
                'subject': 'Evaluación inicial',
                'template': 'candidate/screening.html',
                'channels': ['email', 'whatsapp']
            },
            ProcessStage.INTERVIEW: {
                'subject': 'Confirmación de entrevista',
                'template': 'candidate/interview.html',
                'channels': ['email', 'whatsapp', 'sms']
            },
            ProcessStage.ASSESSMENT: {
                'subject': 'Evaluación de competencias',
                'template': 'candidate/assessment.html',
                'channels': ['email', 'whatsapp']
            },
            ProcessStage.REFERENCE_CHECK: {
                'subject': 'Verificación de referencias',
                'template': 'candidate/reference_check.html',
                'channels': ['email']
            },
            ProcessStage.OFFER: {
                'subject': 'Oferta de trabajo',
                'template': 'candidate/offer.html',
                'channels': ['email', 'whatsapp', 'sms']
            },
            ProcessStage.CONTRACTING: {
                'subject': 'Proceso de contratación',
                'template': 'candidate/contracting.html',
                'channels': ['email', 'whatsapp']
            },
            ProcessStage.ONBOARDING: {
                'subject': 'Bienvenida a la empresa',
                'template': 'candidate/onboarding.html',
                'channels': ['email', 'whatsapp']
            },
            ProcessStage.REJECTION: {
                'subject': 'Actualización del proceso',
                'template': 'candidate/rejection.html',
                'channels': ['email']
            }
        }
        
        template_data = templates.get(stage)
        if template_data:
            for channel in template_data['channels']:
                if channel in self.channels:
                    await self.channels[channel].send(
                        recipient=candidate,
                        subject=template_data['subject'],
                        template=template_data['template'],
                        context={
                            'candidate': candidate,
                            'job': job,
                            'metadata': metadata
                        }
                    )
                
    async def _notify_consultant(
        self,
        stage: ProcessStage,
        candidate: Person,
        job: Vacante,
        business_unit: BusinessUnit,
        metadata: Optional[Dict]
    ):
        """Notifica al consultor asignado."""
        # Para Vacante, usamos el responsable de la vacante
        consultant = getattr(job, 'responsible', None)
        if not consultant:
            return
            
        templates = {
            ProcessStage.INITIAL_CONTACT: {
                'subject': 'Nuevo candidato en proceso',
                'template': 'consultant/new_candidate.html'
            },
            ProcessStage.SCREENING: {
                'subject': 'Resultado de screening',
                'template': 'consultant/screening_result.html'
            },
            ProcessStage.INTERVIEW: {
                'subject': 'Programación de entrevista',
                'template': 'consultant/interview_scheduled.html'
            },
            ProcessStage.ASSESSMENT: {
                'subject': 'Resultado de evaluación',
                'template': 'consultant/assessment_result.html'
            },
            ProcessStage.REFERENCE_CHECK: {
                'subject': 'Verificación de referencias pendiente',
                'template': 'consultant/reference_check_pending.html'
            },
            ProcessStage.OFFER: {
                'subject': 'Preparación de oferta',
                'template': 'consultant/offer_preparation.html'
            },
            ProcessStage.CONTRACTING: {
                'subject': 'Inicio de contratación',
                'template': 'consultant/contracting_start.html'
            },
            ProcessStage.ONBOARDING: {
                'subject': 'Candidato contratado',
                'template': 'consultant/candidate_hired.html'
            },
            ProcessStage.REJECTION: {
                'subject': 'Candidato descartado',
                'template': 'consultant/candidate_rejected.html'
            }
        }
        
        template_data = templates.get(stage)
        if template_data and 'whatsapp' in self.channels:
            await self.channels['whatsapp'].send(
                recipient=consultant,
                subject=template_data['subject'],
                template=template_data['template'],
                context={
                    'candidate': candidate,
                    'job': job,
                    'business_unit': business_unit,
                    'metadata': metadata
                }
            )
            
    async def _notify_client_stakeholders(
        self,
        stage: ProcessStage,
        candidate: Person,
        job: Vacante,
        business_unit: BusinessUnit,
        metadata: Optional[Dict]
    ):
        """Notifica a los stakeholders del cliente."""
        stakeholders = {
            'executive': job.executive_sponsor,
            'process_owner': job.process_owner,
            'payment_contact': job.payment_contact,
            'fiscal_contact': job.fiscal_contact
        }
        
        templates = {
            ProcessStage.SCREENING: {
                'executive': {
                    'subject': 'Candidato en evaluación inicial',
                    'template': 'client/executive/screening.html'
                }
            },
            ProcessStage.INTERVIEW: {
                'executive': {
                    'subject': 'Entrevista programada',
                    'template': 'client/executive/interview.html'
                },
                'process_owner': {
                    'subject': 'Preparación de entrevista',
                    'template': 'client/process_owner/interview.html'
                }
            },
            ProcessStage.OFFER: {
                'executive': {
                    'subject': 'Aprobación de oferta',
                    'template': 'client/executive/offer_approval.html'
                },
                'payment_contact': {
                    'subject': 'Información de compensación',
                    'template': 'client/payment/compensation_info.html'
                }
            },
            ProcessStage.CONTRACTING: {
                'fiscal_contact': {
                    'subject': 'Información fiscal requerida',
                    'template': 'client/fiscal/tax_info.html'
                }
            }
        }
        
        stage_templates = templates.get(stage, {})
        for role, stakeholder in stakeholders.items():
            if not stakeholder:
                continue
                
            role_templates = stage_templates.get(role)
            if role_templates:
                await self.channels['email'].send(
                    recipient=stakeholder,
                    subject=role_templates['subject'],
                    template=role_templates['template'],
                    context={
                        'candidate': candidate,
                        'job': job,
                        'business_unit': business_unit,
                        'metadata': metadata
                    }
                )
                
    async def _notify_references(
        self,
        candidate: Person,
        job: Vacante,
        metadata: Optional[Dict]
    ):
        """Notifica a las referencias del candidato."""
        references = candidate.references_received.all()
        for reference in references:
            await self.channels['email'].send(
                recipient=reference.reference,
                subject='Solicitud de referencia',
                template='reference/request.html',
                context={
                    'candidate': candidate,
                    'job': job,
                    'reference': reference,
                    'metadata': metadata
                }
            )
            
    async def _notify_internal_team(
        self,
        stage: ProcessStage,
        candidate: Person,
        job: Vacante,
        business_unit: BusinessUnit,
        metadata: Optional[Dict]
    ):
        """Notifica al equipo interno sobre actualizaciones importantes."""
        if stage in [ProcessStage.OFFER, ProcessStage.CONTRACTING]:
            await self.channels['telegram'].send(
                recipient=business_unit.admin,
                subject=f'Actualización de proceso - {stage.value}',
                template='internal/process_update.html',
                context={
                    'candidate': candidate,
                    'job': job,
                    'business_unit': business_unit,
                    'metadata': metadata
                }
            )
            
    async def _notify_error(
        self,
        stage: ProcessStage,
        candidate: Person,
        job: Vacante,
        error_message: str
    ):
        """Notifica errores al equipo interno."""
        await self.channels['telegram'].send(
            recipient='admin',
            subject='Error en proceso de notificación',
            template='internal/error.html',
            context={
                'stage': stage.value,
                'candidate': candidate,
                'job': job,
                'error': error_message
            }
        )

class SkillFeedbackNotificationManager:
    """Gestor especializado para notificaciones de feedback de habilidades."""
    
    def __init__(self, business_unit: BusinessUnit):
        self.business_unit = business_unit
        self.channels = {}
        # Inicializar canales disponibles dinámicamente
        channel_names = ['whatsapp', 'telegram', 'sms', 'slack']
        for channel_name in channel_names:
            channel_class = get_channel_class(channel_name)
            if channel_class:
                self.channels[channel_name] = channel_class()
        
    async def notify_feedback_required(
        self,
        recipient: Person,
        vacante: Vacante,
        candidate: Person,
        skills: list,
        deadline: datetime
    ):
        """
        Notifica que se requiere feedback de habilidades.
        """
        try:
            context = {
                'recipient': recipient,
                'vacante': vacante,
                'candidate': candidate,
                'skills': skills,
                'deadline': deadline,
                'business_unit': self.business_unit
            }
            
            # Notificar por WhatsApp (reemplazando email temporalmente)
            if 'whatsapp' in self.channels:
                await self.channels['whatsapp'].send(
                    recipient=recipient,
                    subject=f'Feedback requerido: {candidate.nombre} - {vacante.titulo}',
                    template='feedback/feedback_required.html',
                    context=context
                )
            
            # Notificar por WhatsApp si está disponible
            if recipient.telefono:
                await self.channels['whatsapp'].send(
                    recipient=recipient,
                    subject='Feedback de habilidades requerido',
                    template='feedback/feedback_required_whatsapp.html',
                    context=context
                )
                
        except Exception as e:
            logger.error(f"Error notificando feedback requerido: {str(e)}")
            
    async def notify_feedback_completed(
        self,
        recipient: Person,
        vacante: Vacante,
        candidate: Person,
        feedback_data: dict
    ):
        """
        Notifica que se completó el feedback de habilidades.
        """
        try:
            context = {
                'recipient': recipient,
                'vacante': vacante,
                'candidate': candidate,
                'feedback_data': feedback_data,
                'business_unit': self.business_unit
            }
            
            # Notificar por WhatsApp (reemplazando email temporalmente)
            if 'whatsapp' in self.channels:
                await self.channels['whatsapp'].send(
                    recipient=recipient,
                    subject=f'Feedback completado: {candidate.nombre} - {vacante.titulo}',
                    template='feedback/feedback_completed.html',
                    context=context
                )
            
        except Exception as e:
            logger.error(f"Error notificando feedback completado: {str(e)}")
            
    async def notify_critical_skills_alert(
        self,
        recipient: Person,
        vacante: Vacante,
        candidate: Person,
        critical_skills: list,
        development_time: str
    ):
        """
        Notifica alerta de habilidades críticas detectadas.
        """
        try:
            context = {
                'recipient': recipient,
                'vacante': vacante,
                'candidate': candidate,
                'critical_skills': critical_skills,
                'development_time': development_time,
                'business_unit': self.business_unit
            }
            
            # Notificar por WhatsApp con alta prioridad (reemplazando email temporalmente)
            if 'whatsapp' in self.channels:
                await self.channels['whatsapp'].send(
                    recipient=recipient,
                    subject=f'🚨 Habilidades críticas detectadas: {candidate.nombre}',
                    template='feedback/critical_skills_alert.html',
                    context=context
                )
            
            # Notificar por WhatsApp si está disponible
            if recipient.telefono:
                await self.channels['whatsapp'].send(
                    recipient=recipient,
                    subject='🚨 Habilidades críticas detectadas',
                    template='feedback/critical_skills_alert_whatsapp.html',
                    context=context
                )
                
        except Exception as e:
            logger.error(f"Error notificando alerta de habilidades críticas: {str(e)}")
            
    async def schedule_notification(
        self,
        notification_type: str,
        recipient: Person,
        scheduled_time: datetime,
        vacante: Vacante = None,
        context: dict = None
    ):
        """
        Programa una notificación para un momento específico.
        """
        try:
            # Aquí se integraría con un sistema de tareas programadas
            # Por ahora, solo registramos la programación
            logger.info(f"Notification scheduled for {scheduled_time}: {notification_type} to {recipient.nombre}")
            
        except Exception as e:
            logger.error(f"Error scheduling notification: {str(e)}") 