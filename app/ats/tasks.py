# /home/pablo/app/com/tasks.py
#
# Tareas programadas para el módulo de comunicaciones.
#
from celery import shared_task
from django.core.cache import cache
from django.conf import settings
from app.models import (
    Conversation, 
    ChatMessage, 
    Notification, 
    Metric,
    WorkflowState
)
from app.ats.config import ATS_CONFIG
import logging
from django.utils import timezone

logger = logging.getLogger('app.ats.tasks')

@shared_task(
    name='ats.process_message',
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def process_message(self, conversation_id: int, content: str, channel: str) -> bool:
    """
    Procesa un mensaje recibido a través de cualquier canal.
    
    Args:
        conversation_id: ID de la conversación
        content: Contenido del mensaje
        channel: Canal de comunicación
        
    Returns:
        bool: True si el procesamiento fue exitoso
    """
    try:
        # Verificar configuración del canal
        channel_config = ATS_CONFIG['COMMUNICATION']['CHANNELS'].get(channel)
        if not channel_config or not channel_config['enabled']:
            logger.warning(f"Canal {channel} no configurado o deshabilitado")
            return False
        
        # Obtener conversación
        conversation = Conversation.objects.get(id=conversation_id)
        
        # Crear mensaje
        message = ChatMessage.objects.create(
            conversation=conversation,
            content=content,
            direction='in',
            status='received',
            channel=channel
        )
        
        # Actualizar estado de la conversación
        conversation.last_message = content
        conversation.last_message_at = message.created_at
        conversation.save()
        
        # Registrar métrica
        Metric.objects.create(
            name=f'messages_received_{channel}',
            value=1,
            metadata={
                'conversation_id': conversation_id,
                'channel': channel
            }
        )
        
        logger.info(f"Mensaje procesado exitosamente para conversación {conversation_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error procesando mensaje: {str(e)}")
        self.retry(exc=e)

@shared_task(
    name='ats.send_notification',
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def send_notification(
    self,
    recipient_id: int,
    notification_type: str,
    channel: str,
    content: str,
    metadata: dict = None
) -> bool:
    """
    Envía una notificación a través del canal especificado.
    
    Args:
        recipient_id: ID del destinatario
        notification_type: Tipo de notificación
        channel: Canal de comunicación
        content: Contenido de la notificación
        metadata: Metadatos adicionales
        
    Returns:
        bool: True si el envío fue exitoso
    """
    try:
        # Verificar configuración del canal
        channel_config = ATS_CONFIG['COMMUNICATION']['CHANNELS'].get(channel)
        if not channel_config or not channel_config['enabled']:
            logger.warning(f"Canal {channel} no configurado o deshabilitado")
            return False
        
        # Crear notificación
        notification = Notification.objects.create(
            recipient_id=recipient_id,
            type=notification_type,
            channel=channel,
            content=content,
            metadata=metadata or {},
            status='pending'
        )
        
        # Intentar envío
        success = True  # Aquí iría la lógica de envío real
        if success:
            notification.status = 'sent'
        else:
            notification.status = 'failed'
        notification.save()
        
        # Registrar métrica
        Metric.objects.create(
            name=f'notifications_{notification.status}',
            value=1,
            metadata={
                'type': notification_type,
                'channel': channel
            }
        )
        
        logger.info(f"Notificación {notification.id} procesada con estado: {notification.status}")
        return success
        
    except Exception as e:
        logger.error(f"Error enviando notificación: {str(e)}")
        self.retry(exc=e)

@shared_task(
    name='ats.update_workflow_state',
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def update_workflow_state(
    self,
    conversation_id: int,
    new_state: str,
    workflow_type: str = 'candidate'
) -> bool:
    """
    Actualiza el estado del flujo de trabajo.
    
    Args:
        conversation_id: ID de la conversación
        new_state: Nuevo estado
        workflow_type: Tipo de flujo de trabajo ('candidate' o 'client')
        
    Returns:
        bool: True si la actualización fue exitosa
    """
    try:
        # Obtener configuración del flujo
        workflow_config = ATS_CONFIG['WORKFLOW'].get(workflow_type)
        if not workflow_config:
            logger.error(f"Tipo de flujo de trabajo no válido: {workflow_type}")
            return False
        
        # Validar estado
        if new_state not in workflow_config['states']:
            logger.error(f"Estado no válido para {workflow_type}: {new_state}")
            return False
        
        # Obtener estado actual
        current_state = WorkflowState.objects.filter(
            conversation_id=conversation_id
        ).order_by('-timestamp').first()
        
        # Validar transición
        if current_state:
            valid_transitions = workflow_config['transitions'].get(current_state.state, [])
            if new_state not in valid_transitions:
                logger.warning(
                    f"Transición no válida: {current_state.state} -> {new_state}"
                )
                return False
        
        # Crear nuevo estado
        WorkflowState.objects.create(
            conversation_id=conversation_id,
            state=new_state,
            workflow_type=workflow_type
        )
        
        # Registrar métrica
        Metric.objects.create(
            name='workflow_transitions',
            value=1,
            metadata={
                'workflow_type': workflow_type,
                'from_state': current_state.state if current_state else None,
                'to_state': new_state
            }
        )
        
        logger.info(
            f"Estado de flujo actualizado a {new_state} para conversación {conversation_id}"
        )
        return True
        
    except Exception as e:
        logger.error(f"Error actualizando estado de flujo: {str(e)}")
        self.retry(exc=e)

@shared_task(name='ats.cleanup_old_data')
def cleanup_old_data():
    """Limpia datos antiguos según la configuración de retención."""
    try:
        retention_config = ATS_CONFIG['SECURITY']['data_retention']
        
        # Limpiar conversaciones antiguas
        Conversation.objects.filter(
            created_at__lt=timezone.now() - timezone.timedelta(
                days=retention_config['conversations']
            )
        ).delete()
        
        # Limpiar métricas antiguas
        Metric.objects.filter(
            timestamp__lt=timezone.now() - timezone.timedelta(
                days=retention_config['metrics']
            )
        ).delete()
        
        logger.info("Limpieza de datos antiguos completada")
        
    except Exception as e:
        logger.error(f"Error en limpieza de datos: {str(e)}")
