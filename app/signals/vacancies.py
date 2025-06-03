"""
Señales relacionadas con vacantes en Grupo huntRED®.
Gestiona las señales para eventos de creación, actualización y
procesamiento de vacantes.
"""

import logging
from django.db.models.signals import post_save, m2m_changed, pre_save
from django.dispatch import receiver, Signal
from django.utils import timezone
from app.models import Vacante, BusinessUnit, WorkflowStage, Person, Application
from app.ats.tasks.ml import train_matchmaking_model_task, predict_top_candidates_task

logger = logging.getLogger(__name__)

# Señales personalizadas
vacancy_published = Signal()
vacancy_matched = Signal()

@receiver(post_save, sender=Vacante)
def update_vacancy_timestamps(sender, instance, created, **kwargs):
    """
    Actualiza los timestamps de una vacante y realiza acciones adicionales
    cuando se crea o actualiza una vacante.
    """
    if created:
        logger.info(f"Nueva vacante creada: {instance.title} (ID: {instance.id})")
        
        # Si es una vacante nueva, actualizar último timestamp
        instance.last_updated = timezone.now()
        instance.save(update_fields=['last_updated'])
        
        # Lanzar tarea para buscar candidatos coincidentes
        try:
            predict_top_candidates_task.delay(vacancy_id=instance.id)
        except Exception as e:
            logger.error(f"Error al iniciar predicción de candidatos: {str(e)}")
    else:
        # Actualización: comprobar si campos relevantes cambiaron
        if instance.tracker.has_changed('title') or instance.tracker.has_changed('description'):
            logger.info(f"Vacante actualizada: {instance.title} (ID: {instance.id})")
            
            # Actualizar último timestamp
            instance.last_updated = timezone.now()
            instance.save(update_fields=['last_updated'])
            
            # Reentrenar modelo ML si es necesario
            if instance.business_unit and instance.business_unit.use_ml:
                try:
                    train_matchmaking_model_task.delay(business_unit_id=instance.business_unit.id)
                except Exception as e:
                    logger.error(f"Error al iniciar reentrenamiento del modelo: {str(e)}")


@receiver(m2m_changed, sender=Vacante.tags.through)
def vacancy_tags_changed(sender, instance, action, pk_set, **kwargs):
    """
    Responde a cambios en las etiquetas de una vacante.
    """
    if action in ['post_add', 'post_remove']:
        logger.info(f"Etiquetas de vacante modificadas: {instance.title} (ID: {instance.id})")
        
        # Actualizar último timestamp
        instance.last_updated = timezone.now()
        instance.save(update_fields=['last_updated'])
        
        # Actualizar coincidencias de candidatos
        if instance.business_unit and instance.business_unit.use_ml:
            try:
                predict_top_candidates_task.delay(vacancy_id=instance.id)
            except Exception as e:
                logger.error(f"Error al iniciar actualización de coincidencias: {str(e)}")


@receiver(post_save, sender=Application)
def application_created(sender, instance, created, **kwargs):
    """
    Procesa una nueva aplicación a una vacante.
    """
    if created:
        logger.info(f"Nueva aplicación: {instance.person.email} para vacante {instance.vacancy.title}")
        
        # Notificar al reclutador si es necesario
        from app.ats.tasks.notifications import send_notification
        
        try:
            # Actualizar estadísticas de la vacante
            instance.vacancy.application_count = (
                Application.objects.filter(vacancy=instance.vacancy).count()
            )
            instance.vacancy.save(update_fields=['application_count'])
            
            # Emitir señal personalizada
            vacancy_matched.send(
                sender=sender,
                vacancy=instance.vacancy,
                person=instance.person,
                application=instance
            )
        except Exception as e:
            logger.error(f"Error procesando aplicación: {str(e)}")
