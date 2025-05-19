# /home/pablo/app/com/tasks.py
#
# Tareas programadas para el módulo de comunicaciones.
#
from celery import shared_task
from app.models import Conversation, Message, Notification, Metric
from app.com.config import ComConfig
import logging

logger = logging.getLogger('app.com.tasks')

@shared_task
def process_message(conversation_id: int, content: str, channel: str) -> bool:
    """Procesa un mensaje recibido."""
    try:
        # Obtener configuración del canal
        channel_config = ComConfig.get_channel_config(channel)
        
        # Actualizar conversación
        conversation = Conversation.objects.get(id=conversation_id)
        conversation.last_message = content
        conversation.save()
        
        # Crear mensaje
        Message.objects.create(
            conversation=conversation,
            content=content,
            direction='in',
            status='received'
        )
        
        # Actualizar métricas
        Metric.objects.create(
            name='messages_received',
            value=1,
            timestamp=conversation.timestamp
        )
        
        logger.info(f"Message processed successfully for conversation {conversation_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        return False

@shared_task
def send_notification(
    recipient_id: int,
    notification_type: str,
    channel: str,
    content: str
) -> bool:
    """Envía una notificación."""
    try:
        # Obtener configuración del canal
        channel_config = ComConfig.get_channel_config(channel)
        
        # Crear notificación
        notification = Notification.objects.create(
            recipient_id=recipient_id,
            type=notification_type,
            channel=channel,
            content=content,
            status='pending'
        )
        
        # Intentar enviar
        success = True  # Aquí iría la lógica de envío real
        if success:
            notification.status = 'sent'
        else:
            notification.status = 'failed'
        notification.save()
        
        # Actualizar métricas
        Metric.objects.create(
            name='notifications_sent' if success else 'notifications_failed',
            value=1,
            timestamp=notification.timestamp
        )
        
        logger.info(f"Notification {notification.id} processed with status: {notification.status}")
        return success
        
    except Exception as e:
        logger.error(f"Error sending notification: {str(e)}")
        return False

@shared_task
def update_workflow_state(conversation_id: int, new_state: str) -> bool:
    """Actualiza el estado del flujo de trabajo."""
    try:
        # Obtener configuración del flujo
        workflow_config = ComConfig.get_workflow_config()
        
        # Validar transición
        current_state = WorkflowState.objects.filter(
            conversation_id=conversation_id
        ).order_by('-timestamp').first()
        
        if current_state:
            if new_state not in workflow_config['transitions'].get(current_state.state, []):
                logger.warning(f"Invalid state transition: {current_state.state} -> {new_state}")
                return False
        
        # Crear nuevo estado
        WorkflowState.objects.create(
            conversation_id=conversation_id,
            state=new_state
        )
        
        # Actualizar métricas
        Metric.objects.create(
            name='workflow_transitions',
            value=1,
            timestamp=WorkflowState.objects.latest('timestamp').timestamp
        )
        
        logger.info(f"Workflow state updated to {new_state} for conversation {conversation_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error updating workflow state: {str(e)}")
        return False
