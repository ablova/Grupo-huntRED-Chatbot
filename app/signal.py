# /home/amigro/app/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from app.models import Person, Application, EnhancedNetworkGamificationProfile
from app.parser import CVParser
from app.tasks import train_matchmaking_model
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Person)
def analyze_cv(sender, instance, created, **kwargs):
    if instance.cv_file and not instance.cv_parsed:
        parser = CVParser("Amigro")  # O la unidad de negocio correspondiente
        try:
            analysis_result = parser.parse_cv(instance.cv_file.path)
            instance.cv_analysis = analysis_result
            instance.cv_parsed = True
            instance.save()
        except Exception as e:
            logger.error(f"Error analizando el CV: {e}")

@receiver(post_save, sender=Application)
def trigger_model_retraining(sender, instance, created, **kwargs):
    if created:
        total_applications = Application.objects.filter(
            business_unit=instance.business_unit
        ).count()
        if total_applications % 100 == 0:
            train_matchmaking_model.delay(instance.business_unit.id)

@receiver(post_save, sender=Person)
def create_gamification_profile(sender, instance, created, **kwargs):
    if created:
        EnhancedNetworkGamificationProfile.objects.create(user=instance)
        logger.info(f"EnhancedNetworkGamificationProfile creado para {instance}")

@receiver(post_save, sender=Person)
def save_gamification_profile(sender, instance, **kwargs):
    instance.enhancednetworkgamificationprofile.save()

@receiver(post_save, sender=Person)
def award_points_on_profile_update(sender, instance, created, **kwargs):
    if not created:
        # Aquí puedes agregar lógica para determinar si se actualizó el perfil
        # Por simplicidad, asumiremos que cualquier actualización del perfil otorga puntos
        gamification_profile = instance.enhancednetworkgamificationprofile
        gamification_profile.award_points('profile_update')