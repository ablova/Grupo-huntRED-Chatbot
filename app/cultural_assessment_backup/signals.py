"""
Señales del sistema de Análisis Cultural para Grupo huntRED®.

Gestiona las operaciones automáticas y sincronizaciones cuando ocurren
eventos relevantes relacionados con evaluaciones culturales.
Optimizado para bajo uso de CPU siguiendo reglas globales.
"""

import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from app.models import (
    CulturalAssessment, OrganizationalCulture, CulturalProfile, CulturalReport,
    PersonCulturalProfile, CulturalFitReport, Application
)

logger = logging.getLogger(__name__)

@receiver(post_save, sender=CulturalAssessment)
def update_organizational_culture_stats(sender, instance, created, **kwargs):
    """
    Actualiza las estadísticas de cultura organizacional cuando se modifica una evaluación.
    Solo se ejecuta si el estado de la evaluación ha cambiado a 'completed'.
    """
    # Solo actualizar si la evaluación fue completada
    if instance.status == 'completed' and instance.organizational_culture:
        try:
            org_culture = instance.organizational_culture
            
            # Contar evaluaciones completadas
            completed_count = CulturalAssessment.objects.filter(
                organizational_culture=org_culture,
                status='completed'
            ).count()
            
            # Contar total de evaluaciones (no expiradas o canceladas)
            total_count = CulturalAssessment.objects.filter(
                organizational_culture=org_culture
            ).exclude(
                status__in=['expired', 'cancelled']
            ).count()
            
            # Calcular porcentaje de completitud
            if total_count > 0:
                completion_percentage = (completed_count / total_count) * 100
            else:
                completion_percentage = 0
                
            # Actualizar cultura organizacional
            org_culture.completion_percentage = completion_percentage
            
            # Actualizar estado basado en porcentaje
            if completion_percentage >= 100:
                org_culture.status = 'complete'
            elif completion_percentage >= 80:
                org_culture.status = 'partial'
            elif completion_percentage > 0:
                org_culture.status = 'in_progress'
            else:
                org_culture.status = 'not_started'
                
            org_culture.save(update_fields=['completion_percentage', 'status'])
            logger.info(
                f"Actualizada cultura organizacional {org_culture.id}: "
                f"{completion_percentage:.1f}% completado"
            )
        except Exception as e:
            logger.error(f"Error actualizando estadísticas de cultura organizacional: {str(e)}")


@receiver(post_save, sender=CulturalReport)
def notify_report_completion(sender, instance, created, **kwargs):
    """
    Envía notificaciones cuando un reporte cultural es completado.
    """
    # Solo enviar notificación si el reporte acaba de completarse
    if instance.status == 'completed' and instance.is_public:
        try:
            from app.ats.tasks.notifications import send_report_notification_task
            
            # Programar tarea para enviar notificación
            send_report_notification_task.delay(report_id=instance.id)
            
            logger.info(f"Programada notificación para reporte cultural {instance.id}")
        except Exception as e:
            logger.error(f"Error programando notificación de reporte: {str(e)}")


@receiver(post_save, sender=PersonCulturalProfile)
def update_application_compatibility(sender, instance, created, **kwargs):
    """
    Actualiza la compatibilidad cultural en aplicaciones activas 
    cuando se modifica un perfil cultural.
    """
    try:
        # Buscar aplicaciones activas para esta persona
        applications = Application.objects.filter(
            person=instance.person,
            status__in=['active', 'in_process', 'interview']
        ).select_related('vacante', 'vacante__organization')
        
        # Si no hay aplicaciones, no hay nada que hacer
        if not applications:
            return
            
        # Para cada aplicación, actualizar compatibilidad cultural
        for application in applications:
            if not application.vacante or not application.vacante.organization:
                continue
                
            org_id = application.vacante.organization.id
            
            # Verificar si ya existe información de compatibilidad
            if instance.compatibility_data and str(org_id) in instance.compatibility_data:
                compatibility = instance.compatibility_data[str(org_id)]
                
                # Actualizar el campo de compatibilidad cultural si existe
                if hasattr(application, 'cultural_compatibility'):
                    application.cultural_compatibility = compatibility
                    application.save(update_fields=['cultural_compatibility'])
                    
                    logger.info(
                        f"Actualizada compatibilidad cultural para aplicación {application.id}: "
                        f"{compatibility:.1f}%"
                    )
    except Exception as e:
        logger.error(f"Error actualizando compatibilidad en aplicaciones: {str(e)}")


@receiver(post_delete, sender=CulturalAssessment)
def cleanup_after_assessment_deletion(sender, instance, **kwargs):
    """
    Actualiza estadísticas de cultura organizacional cuando se elimina una evaluación.
    """
    if instance.organizational_culture:
        try:
            # Actualizar estadísticas después de eliminar una evaluación
            org_culture = instance.organizational_culture
            
            # Contar evaluaciones completadas
            completed_count = CulturalAssessment.objects.filter(
                organizational_culture=org_culture,
                status='completed'
            ).count()
            
            # Contar total de evaluaciones (no expiradas o canceladas)
            total_count = CulturalAssessment.objects.filter(
                organizational_culture=org_culture
            ).exclude(
                status__in=['expired', 'cancelled']
            ).count()
            
            # Calcular porcentaje de completitud
            if total_count > 0:
                completion_percentage = (completed_count / total_count) * 100
            else:
                completion_percentage = 0
                
            # Actualizar cultura organizacional
            org_culture.completion_percentage = completion_percentage
            
            # Actualizar estado basado en porcentaje
            if completion_percentage >= 100:
                org_culture.status = 'complete'
            elif completion_percentage >= 80:
                org_culture.status = 'partial'
            elif completion_percentage > 0:
                org_culture.status = 'in_progress'
            else:
                org_culture.status = 'not_started'
                
            org_culture.save(update_fields=['completion_percentage', 'status'])
            logger.info(f"Actualizada cultura organizacional después de eliminar evaluación")
        except Exception as e:
            logger.error(f"Error actualizando estadísticas después de eliminar evaluación: {str(e)}")


@receiver(post_save, sender=OrganizationalCulture)
def create_cultural_report(sender, instance, created, **kwargs):
    """
    Crea un reporte cultural cuando se completa un perfil organizacional.
    """
    try:
        if instance.status == 'complete' and instance.completion_percentage >= 100:
            # Verificar si ya existe un reporte para esta fecha
            existing_report = CulturalReport.objects.filter(
                organization=instance.organization,
                report_date=instance.last_assessment_date
            ).first()
            
            if not existing_report:
                CulturalReport.objects.create(
                    title=f"Reporte Cultural {instance.organization.name} - {instance.last_assessment_date}",
                    organization=instance.organization,
                    report_type='complete',
                    report_date=instance.last_assessment_date,
                    participant_count=instance.participant_count if hasattr(instance, 'participant_count') else 0,
                    completion_percentage=100
                )
                logger.info(f"Creado nuevo reporte cultural para {instance.organization.name}")
    except Exception as e:
        logger.error(f"Error creando reporte cultural: {str(e)}")
