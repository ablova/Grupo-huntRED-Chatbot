# /home/pablo/app/com/feedback/signals.py
"""
Conecta el sistema de feedback con eventos del ciclo de vida del servicio.

Este módulo contiene señales de Django que detectan automáticamente eventos 
importantes como el envío de propuestas, hitos durante el servicio, y 
finalización de servicios, para disparar las encuestas de retroalimentación 
en el momento adecuado de acuerdo con las reglas de negocio de Grupo huntRED®.
"""

import logging
import asyncio
from django.db.models.signals import post_save, post_init
from django.dispatch import receiver

from app.com.pricing.models import Proposal
from app.models import Opportunity, ServiceContract, ServiceMilestone
from .feedback_models import ServiceFeedback, OngoingServiceFeedback, CompletedServiceFeedback
from .ongoing_tracker import get_ongoing_service_tracker
from .completion_tracker import get_service_completion_tracker
from app.com.pricing.proposal_tracker import get_proposal_tracker
from app.utilidades.logging_utils import get_logger

logger = get_logger(__name__)

# Configuración
PROPOSAL_FEEDBACK_DELAY = 3  # días después de enviar la propuesta
MILESTONE_FEEDBACK_DELAY = 1  # día después de alcanzar un hito
COMPLETION_FEEDBACK_DELAY = 5  # días después de completar el servicio

# Función auxiliar para ejecutar corrutinas asíncronas desde señales síncronas
def run_async(coroutine):
    """Ejecuta una corrutina asíncrona desde un contexto síncrono."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        # Si no hay un event loop en el contexto actual, crear uno nuevo
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(coroutine)

# SEÑALES PARA PROPUESTAS

@receiver(post_save, sender=Proposal)
def track_proposal_feedback(sender, instance, created, **kwargs):
    """
    Detecta cuando se envía una nueva propuesta y programa
    la solicitud de retroalimentación.
    """
    # Solo para nuevas propuestas o cuando cambia el estado a 'sent'
    if not created and not instance._status_changed:
        return
    
    # Verificar que sea una propuesta enviada
    if instance.status != 'sent':
        return
    
    logger.info(f"Propuesta {instance.id} enviada, programando feedback en {PROPOSAL_FEEDBACK_DELAY} días")
    
    # Programar solicitud de feedback
    tracker = get_proposal_tracker()
    run_async(tracker.schedule_feedback_request(
        proposal=instance, 
        delay_days=PROPOSAL_FEEDBACK_DELAY
    ))

# Rastrear cambios de estado en propuestas
@receiver(post_init, sender=Proposal)
def store_initial_proposal_status(sender, instance, **kwargs):
    """Almacena el estado inicial de la propuesta para detectar cambios."""
    instance._initial_status = instance.status if hasattr(instance, 'status') else None

@receiver(post_save, sender=Proposal)
def check_proposal_status_change(sender, instance, **kwargs):
    """Detecta cambios en el estado de la propuesta."""
    if not hasattr(instance, '_initial_status'):
        return
    
    instance._status_changed = instance.status != instance._initial_status
    instance._initial_status = instance.status

# SEÑALES PARA SERVICIOS EN CURSO

@receiver(post_save, sender=ServiceMilestone)
def track_milestone_feedback(sender, instance, created, **kwargs):
    """
    Detecta cuando se alcanza un hito en un servicio y programa
    la solicitud de retroalimentación durante el servicio.
    """
    # Solo para hitos completados
    if not instance.completed:
        return
    
    logger.info(f"Hito {instance.id} completado para oportunidad {instance.opportunity_id}, programando feedback")
    
    # Programar solicitud de feedback para servicio en curso
    tracker = get_ongoing_service_tracker()
    run_async(tracker.trigger_milestone_feedback(
        opportunity_id=instance.opportunity_id,
        milestone=instance.milestone_number,
        delay_days=MILESTONE_FEEDBACK_DELAY,
        progress_percentage=instance.progress_percentage
    ))

# Enviar feedback a intervalos regulares para servicios largos
@receiver(post_save, sender=ServiceContract)
def schedule_periodic_feedback(sender, instance, created, **kwargs):
    """
    Para servicios de larga duración, programa retroalimentación
    en intervalos regulares aunque no haya hitos específicos.
    """
    # Solo para contratos activos
    if instance.status != 'active':
        return
    
    # Verificar si es un servicio de larga duración (> 60 días)
    if not instance.end_date or (instance.end_date - instance.start_date).days <= 60:
        return
    
    # Solo programar en la creación o activación del contrato
    if not created and not instance._status_changed:
        return
    
    # Calcular puntos intermedios para feedback (25%, 50%, 75%)
    opportunity_id = instance.opportunity_id
    start_date = instance.start_date
    end_date = instance.end_date
    total_days = (end_date - start_date).days
    
    # Programar para 25% del servicio
    days_to_25_percent = int(total_days * 0.25)
    tracker = get_ongoing_service_tracker()
    run_async(tracker.schedule_feedback_request(
        opportunity_id=opportunity_id,
        milestone=1,
        delay_days=days_to_25_percent,
        progress_percentage=25
    ))
    
    # Programar para 50% del servicio
    days_to_50_percent = int(total_days * 0.5)
    run_async(tracker.schedule_feedback_request(
        opportunity_id=opportunity_id,
        milestone=2,
        delay_days=days_to_50_percent,
        progress_percentage=50
    ))
    
    # Programar para 75% del servicio
    days_to_75_percent = int(total_days * 0.75)
    run_async(tracker.schedule_feedback_request(
        opportunity_id=opportunity_id,
        milestone=3,
        delay_days=days_to_75_percent,
        progress_percentage=75
    ))
    
    logger.info(f"Programados 3 puntos de feedback periódico para servicio de larga duración {opportunity_id}")

# Rastrear cambios de estado en contratos
@receiver(post_init, sender=ServiceContract)
def store_initial_contract_status(sender, instance, **kwargs):
    """Almacena el estado inicial del contrato para detectar cambios."""
    instance._initial_status = instance.status if hasattr(instance, 'status') else None

@receiver(post_save, sender=ServiceContract)
def check_contract_status_change(sender, instance, **kwargs):
    """Detecta cambios en el estado del contrato."""
    if not hasattr(instance, '_initial_status'):
        return
    
    instance._status_changed = instance.status != instance._initial_status
    instance._initial_status = instance.status

# SEÑALES PARA FINALIZACIÓN DE SERVICIOS

@receiver(post_save, sender=ServiceContract)
def track_service_completion(sender, instance, created, **kwargs):
    """
    Detecta cuando se completa un servicio y programa la evaluación final.
    """
    # Solo cuando el estado cambia a 'completed'
    if instance.status != 'completed' or not instance._status_changed:
        return
    
    logger.info(f"Servicio {instance.id} completado, programando evaluación final en {COMPLETION_FEEDBACK_DELAY} días")
    
    # Programar solicitud de evaluación final
    tracker = get_service_completion_tracker()
    run_async(tracker.trigger_completion_feedback(
        opportunity_id=instance.opportunity_id,
        delay_days=COMPLETION_FEEDBACK_DELAY
    ))

def connect_feedback_signals():
    """
    Función auxiliar para asegurar que todas las señales están conectadas.
    Esta función se llama desde el inicializador del módulo de feedback.
    """
    logger.info("Conectando señales del sistema de feedback")
    # Las señales se conectan automáticamente al importar este módulo,
    # esta función existe principalmente para confirmación y claridad
