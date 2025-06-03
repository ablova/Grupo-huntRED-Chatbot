from typing import Dict, Optional, List
from django.conf import settings
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.utils import timezone
from app.models import Feedback, Person, Vacante, Entrevista, Notification, NotificationConfig
from app.ats.utils.notification_service import NotificationService
from app.ats.utils.whatsapp import WhatsAppApi
from app.ats.utils import logger_utils
import logging
import asyncio
import uuid

logger = logging.getLogger(__name__)

class FeedbackService:
    def __init__(self, business_unit: str):
        """
        Inicializa el servicio de feedback.
        
        Args:
            business_unit: Unidad de negocio (huntRED, huntU, Amigro, etc.)
        """
        self.business_unit = business_unit
        self.logger = logger_utils.get_logger(f"{business_unit}_feedback")
        self.notification_service = NotificationService()
        self.whatsapp_api = WhatsAppApi()
        
    async def _get_whatsapp_activation_link(self, token: str) -> str:
        """Genera el enlace de activación de WhatsApp."""
        # Obtener el enlace desde la API de WhatsApp
        return self.whatsapp_api.get_activation_link(token)
        
    async def send_activation_email(self, person: Person) -> bool:
        """
        Envía correo de activación para WhatsApp.
        
        Args:
            person: Usuario a activar
            
        Returns:
            bool: True si el correo se envió correctamente
        """
        try:
            # Generar token de activación
            activation_token = str(uuid.uuid4())
            activation_link = await self._get_whatsapp_activation_link(activation_token)
            
            # Guardar token en el modelo
            person.whatsapp_activation_token = activation_token
            person.whatsapp_activation_expires = timezone.now() + timezone.timedelta(hours=24)
            await person.asave(update_fields=['whatsapp_activation_token', 'whatsapp_activation_expires'])
            
            # Crear notificación
            notification = await self.notification_service.send_notification(
                recipient=person,
                notification_type='ACTIVATION',
                content="Por favor, active WhatsApp para recibir notificaciones de Grupo huntRED®",
                metadata={'activation_link': activation_link}
            )
            
            if notification:
                self.logger.info(f"Notificación de activación creada para {person.email}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error enviando correo de activación: {str(e)}")
            return False
            
    async def activate_whatsapp(self, person: Person, token: str) -> bool:
        """
        Activa WhatsApp para un usuario.
        
        Args:
            person: Usuario a activar
            token: Token de activación
            
        Returns:
            bool: True si la activación fue exitosa
        """
        try:
            if person.whatsapp_activation_token != token:
                raise ValueError("Token de activación inválido")
                
            if person.whatsapp_activation_expires < timezone.now():
                raise ValueError("Token de activación expirado")
                
            # Activar WhatsApp
            person.whatsapp_enabled = True
            person.whatsapp_activation_token = None
            person.whatsapp_activation_expires = None
            await person.asave(update_fields=['whatsapp_enabled', 'whatsapp_activation_token', 'whatsapp_activation_expires'])
            
            # Enviar mensaje de bienvenida
            welcome_message = "¡Hola! WhatsApp está activado. Ahora recibirá notificaciones de Grupo huntRED®."
            await self.whatsapp_api.send_message(person.phone, welcome_message)
            
            self.logger.info(f"WhatsApp activado para {person.email}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error activando WhatsApp: {str(e)}")
            return False
            
    async def send_feedback_notification(self, interview: Entrevista) -> bool:
        """
        Envía notificación de feedback.
        
        Args:
            interview: Entrevista realizada
            
        Returns:
            bool: True si la notificación se envió correctamente
        """
        try:
            # Verificar si el entrevistador tiene WhatsApp activado
            interviewer = interview.tipo
            if not interviewer.whatsapp_enabled:
                # Si no está activado, enviar correo de activación
                await self.send_activation_email(interviewer)
                return False
                
            # Crear feedback pendiente
            feedback = await self._create_pending_feedback(interview)
            
            # Preparar contenido
            content = f"Feedback solicitado para entrevista con {interview.candidato.nombre}\n"
            content += f"Vacante: {interview.vacante.titulo}\n"
            content += f"Fecha: {interview.fecha.strftime('%Y-%m-%d %H:%M')}\n"
            content += "\nPor favor, responda las siguientes preguntas:\n"
            content += "1. ¿El candidato/a le gustó? (Sí/No/Parcialmente)\n"
            content += "2. ¿Cumple con los requerimientos? (Sí/No/Parcialmente)\n"
            content += "3. ¿Qué requisitos faltan?\n"
            content += "4. Comentarios adicionales\n"
            
            # Crear notificación
            notification = await self.notification_service.send_notification(
                recipient=interviewer,
                notification_type='FEEDBACK',
                content=content,
                metadata={'interview_id': interview.id, 'feedback_id': feedback.id}
            )
            
            if notification:
                self.logger.info(f"Notificación de feedback creada para entrevista {interview.id}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error enviando notificación de feedback: {str(e)}")
            return False
            
    async def process_feedback(self, feedback_data: Dict) -> Optional[Feedback]:
        """
        Procesa el feedback recibido y actualiza el ML.
        
        Args:
            feedback_data: Datos del feedback
            
        Returns:
            Feedback: Objeto Feedback actualizado o None si hay error
        """
        try:
            # Validar datos
            required_fields = ['feedback_id', 'is_candidate_liked', 'meets_requirements']
            if not all(field in feedback_data for field in required_fields):
                raise ValueError("Faltan campos requeridos en el feedback")
                
            # Obtener feedback
            feedback = await Feedback.objects.aget(id=feedback_data['feedback_id'])
            
            # Actualizar campos
            feedback.is_candidate_liked = feedback_data['is_candidate_liked']
            feedback.meets_requirements = feedback_data['meets_requirements']
            
            if feedback_data.get('missing_requirements'):
                feedback.missing_requirements = feedback_data['missing_requirements']
                
            if feedback_data.get('additional_comments'):
                feedback.additional_comments = feedback_data['additional_comments']
                
            # Marcar como completado
            feedback.mark_as_completed()
            
            # Actualizar ML con el feedback
            await self._update_ml_with_feedback(feedback)
            
            # Guardar cambios
            await feedback.asave()
            
            # Marcar notificación como leída
            if feedback.notification:
                await feedback.notification.mark_as_read()
            
            self.logger.info(f"Feedback procesado exitosamente para {feedback.candidate.nombre}")
            return feedback
            
        except Exception as e:
            self.logger.error(f"Error procesando feedback: {str(e)}")
            return None
            
    async def _update_ml_with_feedback(self, feedback: Feedback):
        """Actualiza el modelo ML con el feedback recibido."""
        try:
            # Obtener perfil del candidato
            candidate_profile = await self._get_candidate_profile(feedback.candidate)
            
            # Obtener requisitos de la vacante
            vacancy_requirements = await self._get_vacancy_requirements(feedback.candidate.vacantes.first())
            
            # Actualizar pesos del modelo ML
            if feedback.is_candidate_liked == 'NO':
                await self._adjust_weights(candidate_profile, vacancy_requirements, -0.1)
            elif feedback.is_candidate_liked == 'PARTIAL':
                await self._adjust_weights(candidate_profile, vacancy_requirements, -0.05)
            elif feedback.is_candidate_liked == 'YES':
                await self._adjust_weights(candidate_profile, vacancy_requirements, 0.1)
                
            # Si hay requisitos faltantes, ajustar pesos específicos
            if feedback.missing_requirements:
                await self._adjust_missing_requirements(feedback.missing_requirements, vacancy_requirements)
                
            self.logger.info(f"Modelo ML actualizado con feedback de {feedback.candidate.nombre}")
            
        except Exception as e:
            self.logger.error(f"Error actualizando ML con feedback: {str(e)}")
            
    async def _get_candidate_profile(self, candidate: Person) -> Dict:
        """Obtiene el perfil completo del candidato."""
        return {
            'skills': candidate.skills,
            'experience': candidate.experience_years,
            'education': candidate.education,
            'location': candidate.location,
            'personality': candidate.personality_data
        }
        
    async def _get_vacancy_requirements(self, vacancy: Vacante) -> Dict:
        """Obtiene los requisitos completos de la vacante."""
        return {
            'skills_required': vacancy.skills_required,
            'experience_required': vacancy.experience_required,
            'location': vacancy.ubicacion,
            'modality': vacancy.modalidad,
            'required_skills': vacancy.required_skills
        }
        
    async def _adjust_weights(self, candidate_profile: Dict, vacancy_requirements: Dict, adjustment: float):
        """Ajusta los pesos del modelo ML según el feedback."""
        # Ajustar pesos generales
        for skill in candidate_profile['skills']:
            if skill in vacancy_requirements['skills_required']:
                await self._update_skill_weight(skill, adjustment)
                
        # Ajustar pesos por experiencia
        experience_diff = abs(candidate_profile['experience'] - vacancy_requirements['experience_required'])
        if experience_diff > 1:
            await self._update_experience_weight(vacancy_requirements['experience_required'], -0.05)
            
        # Ajustar pesos por ubicación
        if candidate_profile['location'] != vacancy_requirements['location']:
            await self._update_location_weight(vacancy_requirements['location'], -0.1)
            
    async def _adjust_missing_requirements(self, missing_requirements: str, vacancy_requirements: Dict):
        """Ajusta los pesos específicos de los requisitos faltantes."""
        # Procesar requisitos faltantes
        requirements = missing_requirements.split(',')
        for req in requirements:
            req = req.strip()
            if req in vacancy_requirements['skills_required']:
                await self._update_skill_weight(req, -0.2)
            elif req in vacancy_requirements['required_skills']:
                await self._update_skill_weight(req, -0.15)
                
    async def _update_skill_weight(self, skill: str, adjustment: float):
        """Actualiza el peso de una habilidad específica."""
        # TODO: Implementar actualización de pesos en el modelo ML
        pass
        
    async def _update_experience_weight(self, years: int, adjustment: float):
        """Actualiza el peso de la experiencia."""
        # TODO: Implementar actualización de pesos en el modelo ML
        pass
        
    async def _update_location_weight(self, location: str, adjustment: float):
        """Actualiza el peso de la ubicación."""
        # TODO: Implementar actualización de pesos en el modelo ML
        pass
        
    async def _create_pending_feedback(self, interview: Entrevista) -> Feedback:
        """Crea un nuevo feedback pendiente."""
        feedback = await Feedback.objects.acreate(
            candidate=interview.candidato,
            interviewer=interview.tipo,
            feedback_type='INTERVIEW',
            status='PENDING'
        )
        
        # Crear notificación asociada
        notification = await Notification.objects.acreate(
            recipient=interview.tipo,
            notification_type='FEEDBACK',
            content="Feedback pendiente de entrevista",
            metadata={'interview_id': interview.id, 'feedback_id': feedback.id}
        )
        
        feedback.notification = notification
        await feedback.asave()
        
        return feedback
        
    async def get_pending_feedback(self, interviewer: Person) -> List[Feedback]:
        """Obtiene feedback pendiente para un entrevistador."""
        return await Feedback.objects.filter(
            interviewer=interviewer,
            status='PENDING'
        ).order_by('created_at').all()
        
    async def skip_feedback(self, feedback_id: int) -> bool:
        """Omite un feedback."""
        try:
            feedback = await Feedback.objects.aget(id=feedback_id)
            feedback.skip_feedback()
            if feedback.notification:
                await feedback.notification.skip_notification()
            return True
        except Feedback.DoesNotExist:
            return False
