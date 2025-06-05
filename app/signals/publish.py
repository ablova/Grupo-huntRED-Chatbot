"""
Señales relacionadas con el módulo de publicación en Grupo huntRED®.
Gestiona las señales para eventos de publicación en canales externos.
"""

import logging
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver, Signal
from django.utils import timezone
from app.models import Vacante, PublicationChannel, PublicationRecord
from app.tasks import (
    publish_to_channel_task,
    retry_publication_task
)

logger = logging.getLogger(__name__)

# Señales personalizadas
publication_created = Signal()
publication_updated = Signal()
publication_failed = Signal()

@receiver(post_save, sender=Vacante)
def auto_publish_vacancy(sender, instance, created, **kwargs):
    """
    Publica automáticamente una vacante en los canales configurados
    cuando se marca como publicable.
    """
    # Solo procesar si la vacante está activa y publicable
    if instance.active and instance.status == 'approved':
        # Verificar si es nueva o actualizada
        if created:
            logger.info(f"Nueva vacante aprobada para publicación: {instance.title}")
        elif instance.tracker.has_changed('status') and instance.tracker.previous('status') != 'approved':
            logger.info(f"Vacante actualizada y aprobada para publicación: {instance.title}")
        else:
            # No es una vacante nueva ni recién aprobada
            return
            
        # Obtener canales de publicación configurados para la BU
        if instance.business_unit:
            channels = PublicationChannel.objects.filter(
                business_unit=instance.business_unit,
                auto_publish=True,
                active=True
            )
            
            if channels.exists():
                # Programar tarea de publicación en canales
                
                for channel in channels:
                    try:
                        publish_to_channel_task.delay(
                            vacancy_id=instance.id,
                            channel_id=channel.id
                        )
                        logger.info(f"Programada publicación de vacante {instance.id} en canal {channel.name}")
                    except Exception as e:
                        logger.error(f"Error programando publicación en canal {channel.name}: {str(e)}")
            else:
                logger.info(f"No hay canales automáticos configurados para BU {instance.business_unit.name}")


@receiver(post_save, sender=PublicationRecord)
def handle_publication_result(sender, instance, created, **kwargs):
    """
    Maneja el resultado de una publicación y emite señales correspondientes.
    """
    if created:
        logger.info(f"Registro de publicación creado: {instance.vacancy.title} en {instance.channel.name}")
        
        # Emitir señal de publicación creada
        publication_created.send(
            sender=sender,
            publication=instance,
            vacancy=instance.vacancy,
            channel=instance.channel
        )
    
    elif instance.tracker.has_changed('status'):
        previous_status = instance.tracker.previous('status')
        current_status = instance.status
        
        logger.info(f"Estado de publicación actualizado: {instance.vacancy.title} - {previous_status} → {current_status}")
        
        # Emitir señal correspondiente según el cambio de estado
        if current_status == 'published':
            publication_updated.send(
                sender=sender,
                publication=instance,
                previous_status=previous_status
            )
        elif current_status == 'failed':
            publication_failed.send(
                sender=sender,
                publication=instance,
                previous_status=previous_status,
                error=instance.error_message
            )
            
            # Programar reintento si es necesario
            if instance.retry_count < instance.channel.max_retries:
                try:
                    retry_publication_task.delay(publication_id=instance.id)
                    logger.info(f"Programado reintento #{instance.retry_count+1} para publicación {instance.id}")
                except Exception as e:
                    logger.error(f"Error programando reintento de publicación: {str(e)}")
