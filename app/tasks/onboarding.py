# app/tasks/onboarding.py
from celery import shared_task
from django.utils import timezone
import logging
import asyncio

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def send_satisfaction_survey_task(self, onboarding_id, period):
    """
    Envía una encuesta de satisfacción a un candidato para un período específico.
    
    Args:
        onboarding_id (int): ID del proceso de onboarding
        period (int): Período de días desde contratación (3, 7, 15, 30, 60, 90, 180, 365)
    """
    from app.models import OnboardingProcess
    from app.ats.onboarding.onboarding_controller import OnboardingController
    from app.ats.integrations.notifications.process.onboarding_notifications import OnboardingNotificationService
    
    try:
        # Obtener proceso de onboarding
        process = OnboardingProcess.objects.get(id=onboarding_id)
        
        # Verificar si ya se ha enviado para este período
        if str(period) in process.survey_responses:
            logger.info(f"Encuesta para período {period} ya fue respondida en proceso {onboarding_id}")
            return f"Encuesta ya respondida para período {period}"
        
        # Generar enlace seguro
        survey_url = asyncio.run(OnboardingController.generate_secure_survey_link(onboarding_id, period))
        if not survey_url:
            raise ValueError(f"No se pudo generar el enlace para la encuesta ID: {onboarding_id}, período: {period}")
        
        # Preparar mensaje
        person = process.person
        vacancy = process.vacancy
        company_name = vacancy.empresa.name if hasattr(vacancy, 'empresa') and vacancy.empresa else "la empresa"
        
        message = f"👋 Hola {person.first_name},\n\n"
        message += f"Han pasado {period} días desde tu incorporación a {company_name} y nos gustaría conocer tu experiencia.\n\n"
        message += f"📝 Por favor, completa esta breve encuesta de satisfacción: {survey_url}\n\n"
        message += "Tu opinión es muy importante para nosotros.\n\n"
        
        # Enviar notificación usando el servicio específico
        notification_service = OnboardingNotificationService()
        result = asyncio.run(notification_service.notify_satisfaction_survey(
            onboarding_id=onboarding_id,
            period=period
        ))
        
        if not result.get('success'):
            raise ValueError(f"Error enviando notificación: {result.get('error')}")
        
        return f"Encuesta enviada correctamente para período {period}"
        
    except Exception as e:
        logger.error(f"Error enviando encuesta de satisfacción: {str(e)}")
        if self.request.retries < self.max_retries:
            countdown = 5 * 60 * (5 ** self.request.retries)
            raise self.retry(exc=e, countdown=countdown)
        return f"Error: {str(e)}" 