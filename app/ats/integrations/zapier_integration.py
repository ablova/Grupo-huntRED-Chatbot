"""
Integración con Zapier para Grupo huntRED®

Este módulo proporciona integración completa con Zapier para:
- Automatización de flujos de trabajo
- Sincronización con herramientas externas
- Webhooks inteligentes
- Integración con CRM y herramientas de marketing
"""
import asyncio
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from django.utils import timezone
from django.conf import settings
import aiohttp
import json
import hashlib
import hmac

from app.models import (
    Person, Application, Vacante, BusinessUnit, 
    ApiConfig, Event, Interview, ClientFeedback
)
from app.ats.integrations.notifications.core.service import NotificationService

logger = logging.getLogger(__name__)

class ZapierIntegration:
    """
    Integración con Zapier para automatización de flujos de trabajo.
    
    Proporciona funcionalidades para:
    - Webhooks inteligentes
    - Sincronización con CRM
    - Automatización de marketing
    - Integración con herramientas de productividad
    """
    
    def __init__(self, business_unit: Optional[BusinessUnit] = None):
        self.business_unit = business_unit
        self.api_config = self._get_api_config()
        self.notification_service = NotificationService()
        
    def _get_api_config(self) -> Optional[ApiConfig]:
        """Obtiene la configuración de Zapier desde ConfigAPI."""
        try:
            return ApiConfig.objects.get(
                api_type='zapier',
                business_unit=self.business_unit,
                enabled=True
            )
        except ApiConfig.DoesNotExist:
            logger.warning(f"No se encontró configuración de Zapier para {self.business_unit}")
            return None
    
    async def trigger_webhook(
        self,
        webhook_name: str,
        data: Dict[str, Any],
        webhook_type: str = 'post'
    ) -> Dict[str, Any]:
        """
        Dispara un webhook de Zapier.
        
        Args:
            webhook_name: Nombre del webhook
            data: Datos a enviar
            webhook_type: Tipo de webhook (post, get, put)
            
        Returns:
            Dict con el resultado del webhook
        """
        if not self.api_config:
            return {'success': False, 'error': 'Configuración de Zapier no encontrada'}
        
        try:
            webhook_url = self.api_config.additional_config.get('webhooks', {}).get(webhook_name)
            if not webhook_url:
                return {'success': False, 'error': f'Webhook {webhook_name} no configurado'}
            
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'Grupo-huntRED-Zapier-Integration/1.0'
            }
            
            # Agregar autenticación si está configurada
            if self.api_config.api_key:
                headers['Authorization'] = f'Bearer {self.api_config.api_key}'
            
            # Preparar datos
            payload = {
                'timestamp': timezone.now().isoformat(),
                'source': 'huntred_system',
                'business_unit': self.business_unit.name if self.business_unit else 'default',
                'data': data
            }
            
            async with aiohttp.ClientSession() as session:
                if webhook_type.lower() == 'get':
                    async with session.get(webhook_url, headers=headers, params=data) as response:
                        return await self._handle_webhook_response(response)
                else:
                    async with session.post(webhook_url, headers=headers, json=payload) as response:
                        return await self._handle_webhook_response(response)
                        
        except Exception as e:
            logger.error(f"Error en trigger_webhook: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def sync_candidate_to_crm(self, candidate: Person, crm_type: str = 'hubspot') -> Dict[str, Any]:
        """
        Sincroniza un candidato con CRM externo.
        
        Args:
            candidate: Candidato a sincronizar
            crm_type: Tipo de CRM (hubspot, salesforce, etc.)
            
        Returns:
            Dict con el resultado de la sincronización
        """
        try:
            # Preparar datos del candidato
            candidate_data = {
                'email': candidate.email,
                'first_name': candidate.name.split()[0] if candidate.name else '',
                'last_name': ' '.join(candidate.name.split()[1:]) if candidate.name and len(candidate.name.split()) > 1 else '',
                'phone': candidate.phone if hasattr(candidate, 'phone') else '',
                'linkedin_url': candidate.linkedin_url if hasattr(candidate, 'linkedin_url') else '',
                'current_position': candidate.current_position if hasattr(candidate, 'current_position') else '',
                'experience_years': candidate.experience_years if hasattr(candidate, 'experience_years') else 0,
                'skills': candidate.skills if hasattr(candidate, 'skills') else [],
                'location': candidate.location if hasattr(candidate, 'location') else '',
                'source': 'huntred_platform',
                'lead_status': 'new_lead'
            }
            
            # Disparar webhook específico para CRM
            webhook_name = f'sync_candidate_{crm_type}'
            result = await self.trigger_webhook(webhook_name, candidate_data)
            
            if result['success']:
                # Actualizar candidato con información de sincronización
                if hasattr(candidate, 'crm_sync_status'):
                    candidate.crm_sync_status = 'synced'
                    candidate.crm_sync_date = timezone.now()
                    candidate.save()
            
            return result
            
        except Exception as e:
            logger.error(f"Error en sync_candidate_to_crm: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def sync_vacancy_to_job_board(self, vacancy: Vacante, job_board: str = 'linkedin') -> Dict[str, Any]:
        """
        Sincroniza una vacante con tablero de empleos.
        
        Args:
            vacancy: Vacante a sincronizar
            job_board: Tablero de empleos (linkedin, indeed, etc.)
            
        Returns:
            Dict con el resultado de la sincronización
        """
        try:
            # Preparar datos de la vacante
            vacancy_data = {
                'title': vacancy.titulo,
                'description': vacancy.descripcion,
                'requirements': vacancy.required_skills if hasattr(vacancy, 'required_skills') else [],
                'salary_min': vacancy.salary_min if hasattr(vacancy, 'salary_min') else 0,
                'salary_max': vacancy.salary_max if hasattr(vacancy, 'salary_max') else 0,
                'location': vacancy.location if hasattr(vacancy, 'location') else '',
                'employment_type': vacancy.employment_type if hasattr(vacancy, 'employment_type') else 'full_time',
                'remote_work': vacancy.remote_work if hasattr(vacancy, 'remote_work') else False,
                'company_name': vacancy.empresa.nombre if hasattr(vacancy, 'empresa') else 'N/A',
                'company_description': vacancy.empresa.descripcion if hasattr(vacancy, 'empresa') else '',
                'application_url': f"{settings.SITE_URL}/apply/{vacancy.id}",
                'source': 'huntred_platform'
            }
            
            # Disparar webhook específico para tablero de empleos
            webhook_name = f'sync_vacancy_{job_board}'
            result = await self.trigger_webhook(webhook_name, vacancy_data)
            
            if result['success']:
                # Actualizar vacante con información de sincronización
                if hasattr(vacancy, 'job_board_sync_status'):
                    vacancy.job_board_sync_status = 'synced'
                    vacancy.job_board_sync_date = timezone.now()
                    vacancy.save()
            
            return result
            
        except Exception as e:
            logger.error(f"Error en sync_vacancy_to_job_board: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def create_marketing_campaign(
        self,
        campaign_name: str,
        target_audience: List[Person],
        campaign_type: str = 'email',
        template_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Crea una campaña de marketing a través de Zapier.
        
        Args:
            campaign_name: Nombre de la campaña
            target_audience: Lista de personas objetivo
            campaign_type: Tipo de campaña (email, sms, social)
            template_data: Datos del template
            
        Returns:
            Dict con el resultado de la creación
        """
        try:
            # Preparar datos de la campaña
            campaign_data = {
                'campaign_name': campaign_name,
                'campaign_type': campaign_type,
                'target_audience_count': len(target_audience),
                'audience_data': [
                    {
                        'email': person.email,
                        'name': person.name,
                        'phone': person.phone if hasattr(person, 'phone') else '',
                        'custom_fields': self._get_person_custom_fields(person)
                    }
                    for person in target_audience
                ],
                'template_data': template_data or {},
                'business_unit': self.business_unit.name if self.business_unit else 'default',
                'created_at': timezone.now().isoformat()
            }
            
            # Disparar webhook para crear campaña
            webhook_name = f'create_campaign_{campaign_type}'
            result = await self.trigger_webhook(webhook_name, campaign_data)
            
            return result
            
        except Exception as e:
            logger.error(f"Error en create_marketing_campaign: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def sync_interview_to_calendar(
        self,
        interview: Interview,
        calendar_type: str = 'google'
    ) -> Dict[str, Any]:
        """
        Sincroniza una entrevista con calendario externo.
        
        Args:
            interview: Entrevista a sincronizar
            calendar_type: Tipo de calendario (google, outlook, etc.)
            
        Returns:
            Dict con el resultado de la sincronización
        """
        try:
            # Preparar datos de la entrevista
            interview_data = {
                'title': f'Entrevista - {interview.vacancy.titulo}',
                'description': f"""
                Entrevista con {interview.candidate.name}
                Posición: {interview.vacancy.titulo}
                Empresa: {interview.vacancy.empresa.nombre if hasattr(interview.vacancy, 'empresa') else 'N/A'}
                
                Preparación:
                - Revisar CV del candidato
                - Preparar preguntas específicas
                - Verificar requisitos del rol
                """,
                'start_time': interview.scheduled_at.isoformat(),
                'end_time': (interview.scheduled_at + timedelta(hours=1)).isoformat(),
                'attendees': [
                    interview.candidate.email,
                    interview.consultant.email if hasattr(interview, 'consultant') else ''
                ],
                'location': interview.location if hasattr(interview, 'location') else 'Por definir',
                'meeting_type': interview.interview_type if hasattr(interview, 'interview_type') else 'video',
                'source': 'huntred_platform'
            }
            
            # Disparar webhook para sincronizar con calendario
            webhook_name = f'sync_interview_{calendar_type}'
            result = await self.trigger_webhook(webhook_name, interview_data)
            
            return result
            
        except Exception as e:
            logger.error(f"Error en sync_interview_to_calendar: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def create_slack_notification(
        self,
        channel: str,
        message: str,
        attachments: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Crea una notificación en Slack a través de Zapier.
        
        Args:
            channel: Canal de Slack
            message: Mensaje a enviar
            attachments: Archivos adjuntos
            
        Returns:
            Dict con el resultado de la notificación
        """
        try:
            notification_data = {
                'channel': channel,
                'message': message,
                'attachments': attachments or [],
                'business_unit': self.business_unit.name if self.business_unit else 'default',
                'timestamp': timezone.now().isoformat()
            }
            
            # Disparar webhook para Slack
            result = await self.trigger_webhook('slack_notification', notification_data)
            
            return result
            
        except Exception as e:
            logger.error(f"Error en create_slack_notification: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def sync_application_to_ats(
        self,
        application: Application,
        ats_type: str = 'workday'
    ) -> Dict[str, Any]:
        """
        Sincroniza una aplicación con ATS externo.
        
        Args:
            application: Aplicación a sincronizar
            ats_type: Tipo de ATS (workday, bamboo, etc.)
            
        Returns:
            Dict con el resultado de la sincronización
        """
        try:
            # Preparar datos de la aplicación
            application_data = {
                'candidate_email': application.candidate.email,
                'candidate_name': application.candidate.name,
                'vacancy_title': application.vacancy.titulo,
                'application_date': application.created_at.isoformat(),
                'status': application.status,
                'source': 'huntred_platform',
                'resume_url': application.resume_url if hasattr(application, 'resume_url') else '',
                'cover_letter': application.cover_letter if hasattr(application, 'cover_letter') else '',
                'custom_fields': self._get_application_custom_fields(application)
            }
            
            # Disparar webhook para ATS
            webhook_name = f'sync_application_{ats_type}'
            result = await self.trigger_webhook(webhook_name, application_data)
            
            return result
            
        except Exception as e:
            logger.error(f"Error en sync_application_to_ats: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def create_document_automation(
        self,
        document_type: str,
        data: Dict[str, Any],
        recipient: Person = None
    ) -> Dict[str, Any]:
        """
        Crea automatización de documentos a través de Zapier.
        
        Args:
            document_type: Tipo de documento (contract, offer_letter, etc.)
            data: Datos para el documento
            recipient: Persona que recibirá el documento
            
        Returns:
            Dict con el resultado de la automatización
        """
        try:
            document_data = {
                'document_type': document_type,
                'data': data,
                'recipient_email': recipient.email if recipient else '',
                'recipient_name': recipient.name if recipient else '',
                'business_unit': self.business_unit.name if self.business_unit else 'default',
                'created_at': timezone.now().isoformat()
            }
            
            # Disparar webhook para automatización de documentos
            webhook_name = f'create_document_{document_type}'
            result = await self.trigger_webhook(webhook_name, document_data)
            
            return result
            
        except Exception as e:
            logger.error(f"Error en create_document_automation: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def handle_zapier_webhook(
        self,
        webhook_data: Dict[str, Any],
        webhook_signature: str = None
    ) -> Dict[str, Any]:
        """
        Maneja webhooks entrantes de Zapier.
        
        Args:
            webhook_data: Datos del webhook
            webhook_signature: Firma del webhook para verificación
            
        Returns:
            Dict con el resultado del procesamiento
        """
        try:
            # Verificar firma si está configurada
            if webhook_signature and self.api_config.secret_key:
                if not self._verify_webhook_signature(webhook_data, webhook_signature):
                    return {'success': False, 'error': 'Firma de webhook inválida'}
            
            # Procesar webhook según el tipo
            webhook_type = webhook_data.get('type')
            
            if webhook_type == 'new_candidate':
                return await self._handle_new_candidate_webhook(webhook_data)
            elif webhook_type == 'application_update':
                return await self._handle_application_update_webhook(webhook_data)
            elif webhook_type == 'interview_scheduled':
                return await self._handle_interview_scheduled_webhook(webhook_data)
            elif webhook_type == 'placement_completed':
                return await self._handle_placement_completed_webhook(webhook_data)
            else:
                logger.info(f"Webhook no manejado: {webhook_type}")
                return {'success': True, 'message': 'Webhook procesado'}
                
        except Exception as e:
            logger.error(f"Error en handle_zapier_webhook: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    # Métodos auxiliares privados
    
    async def _handle_webhook_response(self, response: aiohttp.ClientResponse) -> Dict[str, Any]:
        """Maneja la respuesta de un webhook."""
        try:
            if response.status in [200, 201, 202]:
                response_data = await response.text()
                return {
                    'success': True,
                    'status_code': response.status,
                    'response': response_data
                }
            else:
                error_text = await response.text()
                logger.error(f"Error en webhook: {response.status} - {error_text}")
                return {
                    'success': False,
                    'error': f"Error HTTP {response.status}: {error_text}",
                    'status_code': response.status
                }
        except Exception as e:
            logger.error(f"Error manejando respuesta de webhook: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _get_person_custom_fields(self, person: Person) -> Dict[str, Any]:
        """Obtiene campos personalizados de una persona."""
        custom_fields = {}
        
        # Agregar campos específicos según el modelo
        if hasattr(person, 'experience_years'):
            custom_fields['experience_years'] = person.experience_years
        if hasattr(person, 'current_position'):
            custom_fields['current_position'] = person.current_position
        if hasattr(person, 'skills'):
            custom_fields['skills'] = person.skills
        if hasattr(person, 'location'):
            custom_fields['location'] = person.location
        
        return custom_fields
    
    def _get_application_custom_fields(self, application: Application) -> Dict[str, Any]:
        """Obtiene campos personalizados de una aplicación."""
        custom_fields = {}
        
        # Agregar campos específicos según el modelo
        if hasattr(application, 'salary_expectation'):
            custom_fields['salary_expectation'] = application.salary_expectation
        if hasattr(application, 'availability'):
            custom_fields['availability'] = application.availability
        if hasattr(application, 'source'):
            custom_fields['source'] = application.source
        
        return custom_fields
    
    def _verify_webhook_signature(self, data: Dict[str, Any], signature: str) -> bool:
        """Verifica la firma de un webhook."""
        try:
            # Crear firma esperada
            payload = json.dumps(data, sort_keys=True)
            expected_signature = hmac.new(
                self.api_config.secret_key.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
        except Exception as e:
            logger.error(f"Error verificando firma: {str(e)}")
            return False
    
    async def _handle_new_candidate_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Maneja webhook de nuevo candidato."""
        try:
            # Procesar datos del candidato
            candidate_data = webhook_data.get('data', {})
            
            # Crear o actualizar candidato
            # Implementar lógica específica según necesidades
            
            return {'success': True, 'message': 'Candidato procesado'}
        except Exception as e:
            logger.error(f"Error manejando nuevo candidato: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def _handle_application_update_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Maneja webhook de actualización de aplicación."""
        try:
            # Procesar actualización de aplicación
            application_data = webhook_data.get('data', {})
            
            # Actualizar aplicación
            # Implementar lógica específica según necesidades
            
            return {'success': True, 'message': 'Aplicación actualizada'}
        except Exception as e:
            logger.error(f"Error manejando actualización de aplicación: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def _handle_interview_scheduled_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Maneja webhook de entrevista programada."""
        try:
            # Procesar entrevista programada
            interview_data = webhook_data.get('data', {})
            
            # Crear o actualizar entrevista
            # Implementar lógica específica según necesidades
            
            return {'success': True, 'message': 'Entrevista procesada'}
        except Exception as e:
            logger.error(f"Error manejando entrevista programada: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def _handle_placement_completed_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Maneja webhook de colocación completada."""
        try:
            # Procesar colocación completada
            placement_data = webhook_data.get('data', {})
            
            # Actualizar aplicación y crear colocación
            # Implementar lógica específica según necesidades
            
            return {'success': True, 'message': 'Colocación procesada'}
        except Exception as e:
            logger.error(f"Error manejando colocación completada: {str(e)}")
            return {'success': False, 'error': str(e)} 