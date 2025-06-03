from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from .models import Integration, IntegrationConfig, IntegrationLog

@receiver(post_save, sender=Integration)
def integration_post_save(sender, instance, created, **kwargs):
    """
    Señal que se dispara después de guardar una integración
    """
    if created:
        # Crear log de creación
        IntegrationLog.objects.create(
            integration=instance,
            event_type='OTHER',
            payload={'action': 'created'}
        )

@receiver(pre_delete, sender=Integration)
def integration_pre_delete(sender, instance, **kwargs):
    """
    Señal que se dispara antes de eliminar una integración
    """
    # Crear log de eliminación
    IntegrationLog.objects.create(
        integration=instance,
        event_type='OTHER',
        payload={'action': 'deleted'}
    )

@receiver(post_save, sender=IntegrationConfig)
def integration_config_post_save(sender, instance, created, **kwargs):
    """
    Señal que se dispara después de guardar una configuración
    """
    if created:
        # Crear log de creación de configuración
        IntegrationLog.objects.create(
            integration=instance.integration,
            event_type='OTHER',
            payload={
                'action': 'config_created',
                'key': instance.key
            }
        ) 