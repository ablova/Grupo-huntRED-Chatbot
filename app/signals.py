# /home/pablollh/app/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from app.models import Person, Application, EnhancedNetworkGamificationProfile
from app.parser import CVParser
from app.tasks import train_matchmaking_model_task
import logging
from app.integrations.services import send_message

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Person)
def analyze_cv(sender, instance, created, **kwargs):
    """
    Analiza el CV del candidato después de guardarlo.
    """
    if instance.cv_file and not instance.cv_parsed:
        parser = CVParser(instance.business_unit)
        try:
            analysis_result = parser.parse_cv(instance.cv_file.path)
            instance.cv_analysis = analysis_result
            instance.cv_parsed = True
            instance.save(update_fields=['cv_analysis', 'cv_parsed'])
        except Exception as e:
            logger.error(f"Error analizando el CV: {e}")

@receiver(post_save, sender=Application)
def trigger_model_retraining(sender, instance, created, **kwargs):
    """
    Retraina el modelo de matchmaking cada 100 nuevas aplicaciones.
    """
    if created:
        bu = instance.vacancy.business_unit
        total_applications = Application.objects.filter(vacancy__business_unit=bu).count()
        if total_applications % 100 == 0:
            train_matchmaking_model_task.delay(bu.id)

@receiver(post_save, sender=Person)
def create_gamification_profile(sender, instance, created, **kwargs):
    """
    Crea un perfil de gamificación para cada nuevo usuario.
    """
    if created:
        EnhancedNetworkGamificationProfile.objects.create(user=instance)
        logger.info(f"EnhancedNetworkGamificationProfile creado para {instance}")

@receiver(post_save, sender=Person)
def save_gamification_profile(sender, instance, **kwargs):
    """
    Guarda el perfil de gamificación al actualizar el usuario.
    """
    instance.enhancednetworkgamificationprofile.save()

@receiver(post_save, sender=Person)
def award_points_on_profile_update(sender, instance, created, **kwargs):
    """
    Otorga puntos de gamificación al actualizar el perfil del usuario.
    """
    if not created:
        gamification_profile = instance.enhancednetworkgamificationprofile
        gamification_profile.award_points('profile_update')

@receiver(post_save, sender=Application)
def notify_candidate_status_update(sender, instance, created, **kwargs):
    """
    Notifica al candidato cuando su estatus en el proceso de reclutamiento cambia.
    """
    if not created:  # Solo para actualizaciones, no para nuevas aplicaciones
        candidate = instance.user
        status = instance.status
        business_unit = instance.vacancy.business_unit

        # Construir el mensaje basado en el nuevo estatus
        messages = {
            'applied': "Tu solicitud ha sido recibida. Estamos revisando tu perfil.",
            'in_review': "Tu perfil está siendo evaluado. ¡Gracias por tu paciencia!",
            'interview': "¡Felicidades! Has sido seleccionado para una entrevista. Te contactaremos pronto.",
            'hired': "¡Enhorabuena! Has sido contratado. Te enviaremos más detalles pronto.",
            'rejected': "Gracias por postularte. Desafortunadamente, no hemos podido avanzar con tu solicitud en esta ocasión."
        }
        message = messages.get(status, "Se ha actualizado tu estatus en el proceso. Revisa tu perfil.")

        # Enviar notificación por WhatsApp o la plataforma correspondiente
        send_message('whatsapp', candidate.phone, message, business_unit)