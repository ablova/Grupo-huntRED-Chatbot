"""
Núcleo del sistema de notificaciones para el ciclo de reclutamiento.
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
from enum import Enum

from app.ats.models import Person, Job, Match, BusinessUnit

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

class NotificationService:
    """Servicio de notificaciones para el ciclo de reclutamiento."""
    
    def __init__(self):
        self.channels = {
            'email': self._send_email,
            'whatsapp': self._send_whatsapp,
            'telegram': self._send_telegram,
            'sms': self._send_sms
        }
        
    async def notify_process_update(
        self,
        stage: ProcessStage,
        candidate: Person,
        job: Job,
        business_unit: BusinessUnit,
        metadata: Optional[Dict] = None
    ):
        """
        Notifica actualizaciones del proceso a todos los actores relevantes.
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
            await self._notify_error(stage, candidate, job, str(e))
            
    async def _notify_candidate(
        self,
        stage: ProcessStage,
        candidate: Person,
        job: Job,
        metadata: Optional[Dict]
    ):
        """Notifica al candidato según la etapa del proceso."""
        channels = self._get_candidate_channels(stage)
        for channel in channels:
            await self.channels[channel](
                recipient=candidate,
                subject=self._get_candidate_subject(stage),
                template=self._get_candidate_template(stage),
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
        job: Job,
        business_unit: BusinessUnit,
        metadata: Optional[Dict]
    ):
        """Notifica al consultor asignado."""
        consultant = job.assigned_consultant
        if not consultant:
            return
            
        await self.channels['email'](
            recipient=consultant,
            subject=self._get_consultant_subject(stage),
            template=self._get_consultant_template(stage),
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
        job: Job,
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
        
        for role, stakeholder in stakeholders.items():
            if not stakeholder:
                continue
                
            template = self._get_stakeholder_template(stage, role)
            if template:
                await self.channels['email'](
                    recipient=stakeholder,
                    subject=self._get_stakeholder_subject(stage, role),
                    template=template,
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
        job: Job,
        metadata: Optional[Dict]
    ):
        """Notifica a las referencias del candidato."""
        references = candidate.references_received.all()
        for reference in references:
            await self.channels['email'](
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
        job: Job,
        business_unit: BusinessUnit,
        metadata: Optional[Dict]
    ):
        """Notifica al equipo interno sobre actualizaciones importantes."""
        if stage in [ProcessStage.OFFER, ProcessStage.CONTRACTING]:
            await self.channels['telegram'](
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
        job: Job,
        error_message: str
    ):
        """Notifica errores al equipo interno."""
        await self.channels['telegram'](
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
        
    def _get_candidate_channels(self, stage: ProcessStage) -> List[str]:
        """Obtiene los canales de notificación para el candidato según la etapa."""
        channels = {
            ProcessStage.INITIAL_CONTACT: ['email', 'whatsapp'],
            ProcessStage.SCREENING: ['email', 'whatsapp'],
            ProcessStage.INTERVIEW: ['email', 'whatsapp', 'sms'],
            ProcessStage.ASSESSMENT: ['email', 'whatsapp'],
            ProcessStage.REFERENCE_CHECK: ['email'],
            ProcessStage.OFFER: ['email', 'whatsapp', 'sms'],
            ProcessStage.CONTRACTING: ['email', 'whatsapp'],
            ProcessStage.ONBOARDING: ['email', 'whatsapp'],
            ProcessStage.REJECTION: ['email']
        }
        return channels.get(stage, ['email'])
        
    def _get_candidate_subject(self, stage: ProcessStage) -> str:
        """Obtiene el asunto del correo para el candidato según la etapa."""
        subjects = {
            ProcessStage.INITIAL_CONTACT: 'Inicio de proceso de selección',
            ProcessStage.SCREENING: 'Evaluación inicial',
            ProcessStage.INTERVIEW: 'Confirmación de entrevista',
            ProcessStage.ASSESSMENT: 'Evaluación de competencias',
            ProcessStage.REFERENCE_CHECK: 'Verificación de referencias',
            ProcessStage.OFFER: 'Oferta de trabajo',
            ProcessStage.CONTRACTING: 'Proceso de contratación',
            ProcessStage.ONBOARDING: 'Bienvenida a la empresa',
            ProcessStage.REJECTION: 'Actualización del proceso'
        }
        return subjects.get(stage, 'Actualización del proceso')
        
    def _get_candidate_template(self, stage: ProcessStage) -> str:
        """Obtiene la plantilla para el candidato según la etapa."""
        templates = {
            ProcessStage.INITIAL_CONTACT: 'candidate/initial_contact.html',
            ProcessStage.SCREENING: 'candidate/screening.html',
            ProcessStage.INTERVIEW: 'candidate/interview.html',
            ProcessStage.ASSESSMENT: 'candidate/assessment.html',
            ProcessStage.REFERENCE_CHECK: 'candidate/reference_check.html',
            ProcessStage.OFFER: 'candidate/offer.html',
            ProcessStage.CONTRACTING: 'candidate/contracting.html',
            ProcessStage.ONBOARDING: 'candidate/onboarding.html',
            ProcessStage.REJECTION: 'candidate/rejection.html'
        }
        return templates.get(stage, 'candidate/generic.html')
        
    def _get_consultant_subject(self, stage: ProcessStage) -> str:
        """Obtiene el asunto del correo para el consultor según la etapa."""
        subjects = {
            ProcessStage.INITIAL_CONTACT: 'Nuevo candidato en proceso',
            ProcessStage.SCREENING: 'Resultado de screening',
            ProcessStage.INTERVIEW: 'Programación de entrevista',
            ProcessStage.ASSESSMENT: 'Resultado de evaluación',
            ProcessStage.REFERENCE_CHECK: 'Verificación de referencias pendiente',
            ProcessStage.OFFER: 'Preparación de oferta',
            ProcessStage.CONTRACTING: 'Inicio de contratación',
            ProcessStage.ONBOARDING: 'Candidato contratado',
            ProcessStage.REJECTION: 'Candidato descartado'
        }
        return subjects.get(stage, 'Actualización de proceso')
        
    def _get_consultant_template(self, stage: ProcessStage) -> str:
        """Obtiene la plantilla para el consultor según la etapa."""
        templates = {
            ProcessStage.INITIAL_CONTACT: 'consultant/new_candidate.html',
            ProcessStage.SCREENING: 'consultant/screening_result.html',
            ProcessStage.INTERVIEW: 'consultant/interview_scheduled.html',
            ProcessStage.ASSESSMENT: 'consultant/assessment_result.html',
            ProcessStage.REFERENCE_CHECK: 'consultant/reference_check_pending.html',
            ProcessStage.OFFER: 'consultant/offer_preparation.html',
            ProcessStage.CONTRACTING: 'consultant/contracting_start.html',
            ProcessStage.ONBOARDING: 'consultant/candidate_hired.html',
            ProcessStage.REJECTION: 'consultant/candidate_rejected.html'
        }
        return templates.get(stage, 'consultant/generic.html')
        
    def _get_stakeholder_subject(self, stage: ProcessStage, role: str) -> str:
        """Obtiene el asunto del correo para el stakeholder según la etapa y rol."""
        subjects = {
            ProcessStage.SCREENING: {
                'executive': 'Candidato en evaluación inicial'
            },
            ProcessStage.INTERVIEW: {
                'executive': 'Entrevista programada',
                'process_owner': 'Preparación de entrevista'
            },
            ProcessStage.OFFER: {
                'executive': 'Aprobación de oferta',
                'payment_contact': 'Información de compensación'
            },
            ProcessStage.CONTRACTING: {
                'fiscal_contact': 'Información fiscal requerida'
            }
        }
        return subjects.get(stage, {}).get(role, 'Actualización de proceso')
        
    def _get_stakeholder_template(self, stage: ProcessStage, role: str) -> Optional[str]:
        """Obtiene la plantilla para el stakeholder según la etapa y rol."""
        templates = {
            ProcessStage.SCREENING: {
                'executive': 'client/executive/screening.html'
            },
            ProcessStage.INTERVIEW: {
                'executive': 'client/executive/interview.html',
                'process_owner': 'client/process_owner/interview.html'
            },
            ProcessStage.OFFER: {
                'executive': 'client/executive/offer_approval.html',
                'payment_contact': 'client/payment/compensation_info.html'
            },
            ProcessStage.CONTRACTING: {
                'fiscal_contact': 'client/fiscal/tax_info.html'
            }
        }
        return templates.get(stage, {}).get(role)
        
    async def _send_email(
        self,
        recipient: Person,
        subject: str,
        template: str,
        context: Dict
    ):
        """Envía notificación por correo electrónico."""
        # Implementar lógica de envío de email
        pass
        
    async def _send_whatsapp(
        self,
        recipient: Person,
        subject: str,
        template: str,
        context: Dict
    ):
        """Envía notificación por WhatsApp."""
        # Implementar lógica de envío de WhatsApp
        pass
        
    async def _send_telegram(
        self,
        recipient: Person,
        subject: str,
        template: str,
        context: Dict
    ):
        """Envía notificación por Telegram."""
        # Implementar lógica de envío de Telegram
        pass
        
    async def _send_sms(
        self,
        recipient: Person,
        subject: str,
        template: str,
        context: Dict
    ):
        """Envía notificación por SMS."""
        # Implementar lógica de envío de SMS
        pass 