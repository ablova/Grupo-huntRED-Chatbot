from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from app.models import Proposal, Opportunity
from app.ats.proposals.tasks import send_proposal_email
from app.ats.utils.notification_handler import NotificationHandler

@receiver(post_save, sender=Proposal)
def proposal_saved(sender, instance, created, **kwargs):
    """
    Maneja el evento de creación o actualización de una propuesta.
    
    Args:
        sender: Modelo que envía la señal
        instance: Instancia del modelo
        created: Booleano que indica si es una nueva instancia
    """
    if created:
        # Enviar email con la propuesta
        send_proposal_email.delay(instance.id)
        
        # Notificar al equipo
        notification_handler = NotificationHandler()
        message = f"Nueva propuesta generada para {instance.company.name}"
        notification_handler.send_notification(
            recipient='pablo@huntred.com',
            message=message,
            subject='Nueva Propuesta'
        )

@receiver(post_delete, sender=Proposal)
def proposal_deleted(sender, instance, **kwargs):
    """
    Maneja el evento de eliminación de una propuesta.
    
    Args:
        sender: Modelo que envía la señal
        instance: Instancia del modelo
    """
    # Notificar al equipo
    notification_handler = NotificationHandler()
    message = f"Propuesta eliminada para {instance.company.name}"
    notification_handler.send_notification(
        recipient='pablo@huntred.com',
        message=message,
        subject='Propuesta Eliminada'
    )
