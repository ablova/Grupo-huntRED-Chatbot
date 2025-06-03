from celery import shared_task
from app.ats.notifications.notifications_managernotifications_manager import NotificationsManager
from app.ats.notifications.notifications_managerconfig import NotificationsConfig
import logging

logger = logging.getLogger('app.ats.notifications.tasks')

@shared_task
def send_notification_task(
    recipient_type: str,
    recipient_id: int,
    notification_type: str,
    context: Dict
) -> bool:
    """Tarea asíncrona para enviar una notificación."""
    try:
        # Inicializar gestor de notificaciones
        manager = NotificationsManager()
        
        # Obtener clase de destinatario
        recipient_class = get_recipient_class(recipient_type)
        
        # Obtener destinatario
        recipient = recipient_class.objects.get(id=recipient_id)
        
        # Enviar notificación
        success = manager.send_notification(
            recipient,
            notification_type,
            context
        )
        
        if success:
            logger.info(
                f"Successfully sent {notification_type} notification to {recipient_type} {recipient_id}"
            )
        else:
            logger.error(
                f"Failed to send {notification_type} notification to {recipient_type} {recipient_id}"
            )
            
        return success
        
    except Exception as e:
        logger.error(f"Error in send_notification_task: {str(e)}")
        return False

@shared_task
def send_bulk_notifications_task(
    recipient_type: str,
    recipient_ids: List[int],
    notification_type: str,
    context: Dict
) -> Dict[str, bool]:
    """Tarea asíncrona para enviar notificaciones en masa."""
    try:
        # Inicializar gestor de notificaciones
        manager = NotificationsManager()
        
        # Obtener clase de destinatario
        recipient_class = get_recipient_class(recipient_type)
        
        # Obtener destinatarios
        recipients = recipient_class.objects.filter(id__in=recipient_ids)
        
        # Enviar notificaciones
        results = manager.send_bulk_notifications(
            list(recipients),
            notification_type,
            context
        )
        
        logger.info(
            f"Bulk notification task completed for {len(recipients)} {recipient_type}s"
        )
        
        return results
        
    except Exception as e:
        logger.error(f"Error in send_bulk_notifications_task: {str(e)}")
        return {str(id): False for id in recipient_ids}

def get_recipient_class(recipient_type: str):
    """Obtiene la clase de destinatario correspondiente."""
    from app.models import Person
    
    recipient_classes = {
        'candidate': Person,
        'consultant': Person,
        'client': Person
    }
    
    return recipient_classes.get(recipient_type, Person)
