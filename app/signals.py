# /home/pablo/app/signals.py
"""
Archivo de compatibilidad para señales de Django.
Este archivo importa todas las señales desde los módulos específicos 
en app/signals/ para mantener compatibilidad con el código existente.

NOTA: Este archivo será eliminado eventualmente. Todo el código nuevo debe
usar directamente los módulos específicos.
"""

import logging
import warnings
from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from django.utils.deprecation import RemovedInNextVersionWarning

# Advertencia de deprecación
warnings.warn(
    "El archivo app/signals.py está obsoleto. Usa los módulos específicos en app/signals/",
    RemovedInNextVersionWarning, stacklevel=2
)

# Configuración de logging
logger = logging.getLogger(__name__)

# Notificar la carga del archivo deprecado
logger.warning(
    "El archivo app/signals.py está obsoleto. Se recomienda usar los módulos específicos en app/signals/"
)

# Importar desde cada módulo específico
from app.signals.core import (
    initialize_signals, register_signal_handler,
    business_unit_changed, candidate_state_changed,
    document_processed, notification_sent, payment_processed,
    whatsapp_message_received
)

from app.signals.chatbot import process_chat_message, initialize_chat_session
from app.signals.vacancies import (
    vacancy_published, vacancy_matched,
    update_vacancy_timestamps, vacancy_tags_changed, application_created
)
from app.signals.payments import (
    payment_processed, payment_failed, invoice_generated,
    handle_payment_update, handle_invoice_creation
)
from app.signals.user import (
    profile_completed, cv_analyzed,
    analyze_cv, create_person_profile
)

from app.models import SuccessionReadinessAssessment, SuccessionCandidate
from django.utils import timezone

@receiver(post_save, sender=SuccessionReadinessAssessment)
def update_candidate_readiness(sender, instance, created, **kwargs):
    """
    Actualiza automáticamente el estado del candidato cuando se crea una nueva evaluación.
    """
    if created:
        candidate = instance.candidate
        candidate.readiness_level = instance.readiness_level
        candidate.readiness_score = instance.readiness_score
        candidate.last_assessed = timezone.now()
        
        # Actualizar las brechas clave desde las áreas de desarrollo
        if instance.development_areas:
            candidate.key_gaps = [area['name'] for area in instance.development_areas]
        
        candidate.save(update_fields=[
            'readiness_level', 
            'readiness_score', 
            'last_assessed',
            'key_gaps'
        ])

@receiver(pre_save, sender=SuccessionCandidate)
def set_initial_development_plan(sender, instance, **kwargs):
    """
    Establece un plan de desarrollo inicial si no existe uno.
    """
    if not instance.pk and not instance.development_plan:
        instance.development_plan = {
            'goals': [],
            'timeline': {},
            'resources': [],
            'milestones': []
        }
from app.signals.publish import (
    publication_created, publication_updated, publication_failed,
    auto_publish_vacancy, handle_publication_result
)
from app.signals.notifications import (
    notification_created, notification_sent, notification_failed,
    handle_notification_created, process_notification_queue
)


@receiver(post_save, sender=Person)
def analyze_cv(sender, instance, created, **kwargs):
    """
    Analiza el CV del candidato y actualiza su perfil.
    """
    if instance.cv_file and not instance.cv_parsed:
        try:
            parser = CVParser(instance.business_unit)
            analysis_result = parser.parse_cv(instance.cv_file.path)
            
            # Actualizar perfil con análisis
            instance.cv_analysis = analysis_result
            instance.skills = analysis_result.get('skills', [])
            instance.experience_years = analysis_result.get('experience_years', 0)
            instance.education = analysis_result.get('education', '')
            instance.languages = analysis_result.get('languages', [])
            instance.cv_parsed = True
            
            # Actualizar perfil de gamificación
            gamification_profile = instance.enhancednetworkgamificationprofile
            gamification_profile.update_profile(
                skills=instance.skills,
                experience=instance.experience_years,
                education=instance.education
            )
            gamification_profile.save()
            
            instance.save(update_fields=['cv_analysis', 'cv_parsed',
                                       'skills', 'experience_years',
                                       'education', 'languages'])
            
            # Notificar análisis completado
            Notification.objects.create(
                user=instance,
                message="Tu CV ha sido analizado exitosamente",
                type="success"
            )
            
        except Exception as e:
            logger.error(f"Error analizando el CV: {e}")
            Notification.objects.create(
                user=instance,
                message="Hubo un error al analizar tu CV",
                type="error"
            )

@receiver(post_save, sender=Application)
def trigger_model_retraining(sender, instance, created, **kwargs):
    """
    Retraina el modelo de matchmaking y actualiza puntuaciones.
    """
    if created:
        bu = instance.vacancy.business_unit
        total_applications = Application.objects.filter(
            vacancy__business_unit=bu
        ).count()
        
        # Retrenar modelo cada 100 aplicaciones
        if total_applications % 100 == 0:
            train_matchmaking_model_task.delay(bu.id)
            
        # Actualizar puntuaciones de matchmaking
        update_matchmaking_scores_task.delay(
            candidate_id=instance.user_id,
            vacancy_id=instance.vacancy_id
        )

@receiver(post_save, sender=Application)
def update_engagement_metrics(sender, instance, created, **kwargs):
    """
    Actualiza métricas de engagement cuando se crea una aplicación.
    """
    if created:
        update_engagement_scores_task.delay(
            business_unit_id=instance.vacancy.business_unit_id,
            user_id=instance.user_id
        )

@receiver(post_save, sender=Person)
def create_gamification_profile(sender, instance, created, **kwargs):
    """
    Crea y configura el perfil de gamificación para nuevos usuarios.
    """
    if created:
        try:
            profile = EnhancedNetworkGamificationProfile.objects.create(
                user=instance,
                initial_points=100,  # Puntos iniciales
                level=1,
                badges=['new_user'],
                achievements=['registered']
            )
            logger.info(f"EnhancedNetworkGamificationProfile creado para {instance}")
            
            # Enviar notificación de bienvenida
            send_message(
                'whatsapp',
                instance.phone,
                "¡Bienvenido a huntRED®! Has iniciado tu perfil. "
                "Completa tu información para comenzar a buscar oportunidades.",
                instance.business_unit
            )
            
            # Programar actualización de perfil
            update_profile_task.delay(instance.id)
            
        except Exception as e:
            logger.error(f"Error creando perfil de gamificación: {e}")

@receiver(post_save, sender=Person)
def save_gamification_profile(sender, instance, **kwargs):
    """
    Actualiza el perfil de gamificación cuando se actualiza el usuario.
    """
    try:
        profile = instance.enhancednetworkgamificationprofile
        profile.update_profile(
            skills=instance.skills,
            experience=instance.experience_years,
            education=instance.education
        )
        profile.save()
        
        # Actualizar ranking
        profile.update_ranking()
        
        # Notificar actualización
        Notification.objects.create(
            user=instance,
            message="Tu perfil de gamificación ha sido actualizado",
            type="info"
        )
        
    except Exception as e:
        logger.error(f"Error actualizando perfil de gamificación: {e}")

@receiver(post_save, sender=Person)
def award_points_on_profile_update(sender, instance, created, **kwargs):
    """
    Otorga puntos de gamificación y logra logros al actualizar el perfil.
    """
    if not created:
        try:
            profile = instance.enhancednetworkgamificationprofile
            
            # Calcular puntos basados en cambios
            points = 0
            if instance.cv_parsed:
                points += 100
            if instance.skills:
                points += 50
            if instance.experience_years:
                points += 20 * instance.experience_years
            
            profile.award_points(
                points=points,
                reason='profile_update',
                metadata={
                    'skills': len(instance.skills),
                    'experience': instance.experience_years
                }
            )
            
            # Verificar logros
            achievements = profile.check_achievements()
            if achievements:
                profile.award_achievements(achievements)
                
            profile.save()
            
        except Exception as e:
            logger.error(f"Error otorgando puntos: {e}")

@receiver(post_save, sender=Application)
def notify_candidate_status_update(sender, instance, created, **kwargs):
    """
    Notifica al candidato sobre cambios en su estatus y actualiza métricas.
    """
    if not created:  # Solo para actualizaciones
        try:
            candidate = instance.user
            status = instance.status
            business_unit = instance.vacancy.business_unit
            
            # Construir mensaje basado en el nuevo estatus
            messages = {
                'applied': "Tu solicitud ha sido recibida. Estamos revisando tu perfil.",
                'in_review': "Tu perfil está siendo evaluado. ¡Gracias por tu paciencia!",
                'interview': "¡Felicidades! Has sido seleccionado para una entrevista. Te contactaremos pronto.",
                'hired': "¡Enhorabuena! Has sido contratado. Te enviaremos más detalles pronto.",
                'rejected': "Gracias por postularte. Desafortunadamente, no hemos podido avanzar con tu solicitud en esta ocasión."
            }
            message = messages.get(status, "Se ha actualizado tu estatus en el proceso. Revisa tu perfil.")
            
            # Enviar notificación por WhatsApp
            send_message(
                'whatsapp',
                candidate.phone,
                message,
                business_unit
            )
            
            # Crear notificación en sistema
            Notification.objects.create(
                user=candidate,
                message=message,
                type="info",
                related_object=instance
            )
            
            # Actualizar métricas de éxito
            if status == 'hired':
                update_success_metrics.delay(
                    business_unit_id=business_unit.id,
                    vacancy_id=instance.vacancy_id
                )
                
                # Enviar email de felicitación
                send_mass_email_task.delay([
                    candidate.email
                ], "¡Felicidades! Has sido seleccionado", 
                "hired_template", 
                context={
                    "candidate": candidate,
                    "vacancy": instance.vacancy
                })
                
        except Exception as e:
            logger.error(f"Error notificando cambio de estatus: {e}")

@receiver(m2m_changed, sender=Vacante.skills_required.through)
def update_skills_matching(sender, instance, action, **kwargs):
    """
    Actualiza el matching de habilidades cuando se modifican las habilidades requeridas.
    """
    if action in ['post_add', 'post_remove']:
        try:
            # Actualizar puntuaciones de matching
            update_matchmaking_scores_task.delay(
                vacancy_id=instance.id
            )
            
            # Notificar cambios a candidatos afectados
            candidates = Application.objects.filter(
                vacancy=instance,
                status__in=['applied', 'in_review']
            ).values_list('user_id', flat=True)
            
            for candidate_id in candidates:
                send_message(
                    'whatsapp',
                    Person.objects.get(id=candidate_id).phone,
                    "Se han actualizado los requisitos de la vacante. "
                    "Revisa tu perfil para ver cómo te afecta.",
                    instance.business_unit
                )
                
        except Exception as e:
            logger.error(f"Error actualizando matching de habilidades: {e}")

@receiver(post_save, sender=Vacante)
def analyze_vacancy_requirements(sender, instance, created, **kwargs):
    """
    Analiza los requisitos de la vacante usando NLP y actualiza el matching.
    """
    if created:
        try:
            nlp_processor = get_nlp_processor()
            if nlp_processor:
                analysis = nlp_processor.analyze_vacancy(
                    instance.description,
                    instance.requirements
                )
                
                instance.skills_required = analysis.get('skills', [])
                instance.experience_required = analysis.get('experience', 0)
                instance.education_required = analysis.get('education', '')
                instance.save()
                
                # Actualizar matching con candidatos existentes
                update_matchmaking_scores_task.delay(
                    vacancy_id=instance.id
                )
                
        except Exception as e:
            logger.error(f"Error analizando requisitos de vacante: {e}")

@receiver(post_save, sender=WorkflowStage)
def update_workflow_metrics(sender, instance, created, **kwargs):
    """
    Actualiza métricas de flujo de trabajo cuando se modifican las etapas.
    """
    if not created:  # Solo para actualizaciones
        try:
            # Actualizar duración promedio
            avg_duration = Application.objects.filter(
                workflow_stage=instance,
                status__in=['hired', 'rejected']
            ).annotate(
                duration=timezone.now() - F('created_at')
            ).aggregate(avg=Avg('duration'))['avg']
            
            instance.avg_duration = avg_duration
            instance.save()
            
            # Notificar cambios a administradores
            admins = Person.objects.filter(is_admin=True)
            for admin in admins:
                send_message(
                    'whatsapp',
                    admin.phone,
                    f"Se han actualizado las métricas de la etapa '{instance.name}'",
                    instance.business_unit
                )
                
        except Exception as e:
            logger.error(f"Error actualizando métricas de workflow: {e}")

# Funciones auxiliares

def get_current_user():
    """Obtiene el usuario actual de la request."""
    from threading import local
    _thread_locals = local()
    
    def get_current_request():
        return getattr(_thread_locals, 'request', None)
    
    def get_current_user():
        request = get_current_request()
        if request:
            return request.user
        return None
    
    return get_current_user()

@receiver(post_save, sender=WeightingModel)
def log_weighting_change(sender, instance, created, **kwargs):
    """Registra cambios en ponderaciones."""
    if not created:
        # Obtener valores anteriores
        old_instance = WeightingModel.objects.get(pk=instance.pk)
        
        # Comparar y registrar cambios
        changes = {}
        for field in ['weight_skills', 'weight_experience', 'weight_culture', 'weight_location',
                     'culture_importance', 'experience_requirement']:
            old_value = getattr(old_instance, field)
            new_value = getattr(instance, field)
            if old_value != new_value:
                changes[field] = {
                    'old': float(old_value),
                    'new': float(new_value)
                }
        
        if changes:
            WeightingHistory.objects.create(
                weighting=instance,
                changed_by=get_current_user(),
                changes=changes
            )

# Funciones auxiliares

def update_profile_task(person_id):
    """Tarea asíncrona para actualizar el perfil."""
    try:
        person = Person.objects.get(id=person_id)
        person.update_profile()
        person.save()
    except Exception as e:
        logger.error(f"Error en update_profile_task: {e}")

def update_success_metrics(business_unit_id, vacancy_id):
    """Actualiza métricas de éxito para la unidad de negocio."""
    try:
        bu = BusinessUnit.objects.get(id=business_unit_id)
        vacancy = Vacante.objects.get(id=vacancy_id)
        
        # Actualizar métricas
        bu.update_success_metrics(vacancy)
        bu.save()
        
    except Exception as e:
        logger.error(f"Error actualizando métricas de éxito: {e}")