from typing import Dict, Optional
from app.models import Feedback, Person, Vacante, Entrevista
from app.com.utils.notification_service import NotificationService
from app.com.utils import logger_utils
import logging
import asyncio

class FeedbackService:
    def __init__(self, business_unit: str):
        """
        Inicializa el servicio de feedback.
        
        Args:
            business_unit: Unidad de negocio (huntRED, huntU, Amigro, etc.)
        """
        self.business_unit = business_unit
        self.logger = logger_utils.get_logger(f"{business_unit}_feedback")
        self.notification_service = NotificationService(business_unit)
        
    async def send_feedback_notification(self, interview: Entrevista) -> bool:
        """
        Envía notificación de feedback al entrevistador.
        
        Args:
            interview: Entrevista realizada
            
        Returns:
            bool: True si la notificación se envió correctamente
        """
        try:
            # Crear feedback pendiente
            feedback = await self._create_pending_feedback(interview)
            
            # Preparar contenido de la notificación
            content = f"Se ha solicitado su feedback para la entrevista con {interview.candidato.nombre}"
            metadata = {
                'template': 'feedback_notification',
                'interview_date': interview.fecha.strftime('%Y-%m-%d %H:%M'),
                'candidate_name': interview.candidato.nombre,
                'vacancy_title': interview.vacante.titulo,
                'feedback_id': feedback.id
            }
            
            # Enviar notificación
            await self.notification_service.send_notification(
                recipient=interview.tipo,
                notification_type='FEEDBACK',
                content=content,
                metadata=metadata
            )
            
            self.logger.info(f"Notificación de feedback enviada para entrevista {interview.id}")
            return True
            
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
            
            # Actualizar el ML con el feedback
            await self._update_ml_with_feedback(feedback)
            
            # Guardar cambios
            await feedback.asave()
            
            self.logger.info(f"Feedback procesado exitosamente para {feedback.candidate.nombre}")
            return feedback
            
        except Exception as e:
            self.logger.error(f"Error procesando feedback: {str(e)}")
            return None
            
    async def _create_pending_feedback(self, interview: Entrevista) -> Feedback:
        """Crea un nuevo feedback pendiente."""
        return await Feedback.objects.acreate(
            candidate=interview.candidato,
            interviewer=interview.tipo,
            feedback_type='INTERVIEW',
            status='PENDING'
        )
        
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
