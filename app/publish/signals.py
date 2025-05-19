from django.db.models.signals import post_save
from django.dispatch import receiver
from app.models import JobOpportunity
from app.publish.tasks import process_new_opportunity

@receiver(post_save, sender=JobOpportunity)
def handle_job_opportunity_creation(sender, instance, created, **kwargs):
    """
    Maneja la creación de una nueva oportunidad laboral
    """
    if created and instance.publish_on_create:
        # Programar procesamiento de la oportunidad
        process_new_opportunity.delay(instance.id)
