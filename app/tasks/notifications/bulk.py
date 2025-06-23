# app/tasks/notifications/bulk.py
from celery import shared_task
import logging
from typing import List, Dict, Union, Any

logger = logging.getLogger(__name__)

@shared_task(bind=True, name='app.tasks.send_bulk_notifications_task', max_retries=3)
def send_bulk_notifications_task(self,
                                 recipients: List[Union[str, Dict]],
                                 subject: str,
                                 message: str,
                                 channel: str = None,
                                 template: str = None,
                                 context: Dict = None,
                                 priority: str = None,
                                 bu_name: str = None,
                                 sender: Union[str, Dict] = None,
                                 metadata: Dict = None) -> Dict[str, Any]:
    """
    Celery task to send notifications to a large number of recipients.

    This task iterates through a list of recipients and sends a notification
    to each one using the NotificationService.
    """
    # Importar servicios y modelos aquí para evitar dependencias circulares a nivel de módulo
    from app.ats.utils.notification_service import NotificationService
    from django.apps import apps
    
    success_count = 0
    failure_count = 0
    errors = []

    for i, recipient_data in enumerate(recipients):
        try:
            recipient: Union[str, Dict, Any] = recipient_data
            
            # Rehidratar modelos de Django si es necesario
            if isinstance(recipient_data, dict) and 'type' in recipient_data and 'id' in recipient_data:
                model_class = apps.get_model(app_label='app', model_name=recipient_data['type'])
                recipient = model_class.objects.get(id=recipient_data['id'])

            NotificationService.send_notification(
                recipient=recipient,
                subject=subject,
                message=message,
                channel=channel,
                template=template,
                context=context,
                priority=priority,
                bu_name=bu_name,
                sender=sender,
                metadata={'bulk_task_id': self.request.id, **(metadata or {})}
            )
            success_count += 1
            
        except Exception as e:
            failure_count += 1
            error_msg = f"Failed to send notification to recipient {i} ({recipient_data}): {str(e)}"
            logger.error(error_msg, exc_info=False) # exc_info a False para no llenar logs
            errors.append(error_msg)

    result = {
        'total_recipients': len(recipients),
        'success_count': success_count,
        'failure_count': failure_count,
        'errors': errors
    }
    
    if failure_count > 0 and self.request.retries < self.max_retries:
        countdown = 60 * (2 ** self.request.retries)  # Backoff exponencial
        logger.warning(f"Retrying bulk notification task {self.request.id} due to {failure_count} failures. Retrying in {countdown}s.")
        raise self.retry(exc=Exception(f"{failure_count} failures"), countdown=countdown)

    return result 