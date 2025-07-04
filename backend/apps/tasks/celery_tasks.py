"""
Celery Tasks - Sistema huntRED® v2
Tasks para procesamiento ML, workflows, notificaciones y análisis en background.
"""

from celery import shared_task, current_task
from celery.exceptions import MaxRetriesExceededError
from django.utils import timezone
from django.conf import settings
from typing import Dict, List, Any, Optional, Union
import logging
import traceback
import json
import time
from datetime import timedelta

# Configurar logging
logger = logging.getLogger(__name__)


# ============================================================================
# TASKS ML - GENIA
# ============================================================================

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def analyze_candidate_skills(self, person_id: str, job_position_id: str = None) -> Dict[str, Any]:
    """
    Analiza las habilidades de un candidato usando GenIA.
    """
    try:
        from apps.ml.genia.skill_analyzer import SkillAnalyzer
        from apps.core.models import Person, JobPosition
        
        logger.info(f"Starting skill analysis for person {person_id}")
        
        # Obtener candidato
        try:
            person = Person.objects.get(id=person_id)
        except Person.DoesNotExist:
            logger.error(f"Person {person_id} not found")
            return {'error': 'Person not found', 'success': False}
        
        # Obtener posición si está especificada
        job_position = None
        if job_position_id:
            try:
                job_position = JobPosition.objects.get(id=job_position_id)
            except JobPosition.DoesNotExist:
                logger.warning(f"Job position {job_position_id} not found")
        
        # Inicializar analizador
        analyzer = SkillAnalyzer()
        
        # Realizar análisis
        start_time = time.time()
        analysis_result = analyzer.analyze_candidate(person, job_position)
        processing_time = time.time() - start_time
        
        # Guardar resultados
        analysis_result.update({
            'task_id': self.request.id,
            'processing_time_seconds': processing_time,
            'timestamp': timezone.now().isoformat(),
            'success': True
        })
        
        logger.info(f"Skill analysis completed for person {person_id} in {processing_time:.2f}s")
        return analysis_result
        
    except Exception as exc:
        logger.error(f"Error in skill analysis for person {person_id}: {str(exc)}")
        logger.error(traceback.format_exc())
        
        try:
            self.retry(countdown=60 * (self.request.retries + 1))
        except MaxRetriesExceededError:
            return {
                'error': str(exc),
                'success': False,
                'max_retries_exceeded': True,
                'task_id': self.request.id
            }


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def analyze_candidate_experience(self, person_id: str) -> Dict[str, Any]:
    """
    Analiza la experiencia profesional de un candidato.
    """
    try:
        from apps.ml.genia.experience_analyzer import ExperienceAnalyzer
        from apps.core.models import Person
        
        logger.info(f"Starting experience analysis for person {person_id}")
        
        person = Person.objects.get(id=person_id)
        analyzer = ExperienceAnalyzer()
        
        start_time = time.time()
        analysis_result = analyzer.analyze_experience(person)
        processing_time = time.time() - start_time
        
        analysis_result.update({
            'task_id': self.request.id,
            'processing_time_seconds': processing_time,
            'timestamp': timezone.now().isoformat(),
            'success': True
        })
        
        logger.info(f"Experience analysis completed for person {person_id}")
        return analysis_result
        
    except Exception as exc:
        logger.error(f"Error in experience analysis: {str(exc)}")
        
        try:
            self.retry(countdown=60 * (self.request.retries + 1))
        except MaxRetriesExceededError:
            return {'error': str(exc), 'success': False, 'max_retries_exceeded': True}


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def analyze_resume_content(self, person_id: str, resume_text: str = None) -> Dict[str, Any]:
    """
    Analiza el contenido del CV usando NLP avanzado.
    """
    try:
        from apps.ml.genia.resume_analyzer import ResumeAnalyzer
        from apps.core.models import Person
        
        logger.info(f"Starting resume analysis for person {person_id}")
        
        person = Person.objects.get(id=person_id)
        analyzer = ResumeAnalyzer()
        
        # Usar texto proporcionado o extraer del CV del candidato
        if not resume_text and hasattr(person, 'resume_file') and person.resume_file:
            # Extraer texto del archivo CV
            resume_text = analyzer.extract_text_from_file(person.resume_file.path)
        
        start_time = time.time()
        analysis_result = analyzer.analyze_resume(resume_text, person)
        processing_time = time.time() - start_time
        
        analysis_result.update({
            'task_id': self.request.id,
            'processing_time_seconds': processing_time,
            'timestamp': timezone.now().isoformat(),
            'success': True
        })
        
        logger.info(f"Resume analysis completed for person {person_id}")
        return analysis_result
        
    except Exception as exc:
        logger.error(f"Error in resume analysis: {str(exc)}")
        
        try:
            self.retry(countdown=60 * (self.request.retries + 1))
        except MaxRetriesExceededError:
            return {'error': str(exc), 'success': False, 'max_retries_exceeded': True}


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def match_candidate_to_jobs(self, person_id: str, job_ids: List[str] = None) -> Dict[str, Any]:
    """
    Realiza matching inteligente entre candidato y posiciones.
    """
    try:
        from apps.ml.genia.matching_engine import MatchingEngine
        from apps.core.models import Person, JobPosition
        
        logger.info(f"Starting job matching for person {person_id}")
        
        person = Person.objects.get(id=person_id)
        matcher = MatchingEngine()
        
        # Obtener trabajos a evaluar
        if job_ids:
            jobs = JobPosition.objects.filter(id__in=job_ids, is_active=True)
        else:
            # Obtener trabajos activos de la misma business unit
            jobs = JobPosition.objects.filter(
                business_unit=person.business_unit,
                is_active=True,
                status='open'
            )[:50]  # Limitar a 50 trabajos para evitar sobrecarga
        
        start_time = time.time()
        matching_results = []
        
        for job in jobs:
            match_result = matcher.calculate_match_score(person, job)
            matching_results.append({
                'job_id': str(job.id),
                'job_title': job.title,
                'match_score': match_result['score'],
                'match_details': match_result['details'],
                'recommendations': match_result.get('recommendations', [])
            })
        
        # Ordenar por puntuación
        matching_results.sort(key=lambda x: x['match_score'], reverse=True)
        
        processing_time = time.time() - start_time
        
        result = {
            'person_id': person_id,
            'total_jobs_analyzed': len(matching_results),
            'top_matches': matching_results[:10],  # Top 10 matches
            'all_matches': matching_results,
            'task_id': self.request.id,
            'processing_time_seconds': processing_time,
            'timestamp': timezone.now().isoformat(),
            'success': True
        }
        
        logger.info(f"Job matching completed for person {person_id} - {len(matching_results)} jobs analyzed")
        return result
        
    except Exception as exc:
        logger.error(f"Error in job matching: {str(exc)}")
        
        try:
            self.retry(countdown=60 * (self.request.retries + 1))
        except MaxRetriesExceededError:
            return {'error': str(exc), 'success': False, 'max_retries_exceeded': True}


# ============================================================================
# TASKS ML - AURA
# ============================================================================

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def analyze_personality_profile(self, person_id: str, assessment_data: Dict = None) -> Dict[str, Any]:
    """
    Analiza el perfil de personalidad usando AURA.
    """
    try:
        from apps.ml.aura.personality_analyzer import PersonalityAnalyzer
        from apps.core.models import Person
        
        logger.info(f"Starting personality analysis for person {person_id}")
        
        person = Person.objects.get(id=person_id)
        analyzer = PersonalityAnalyzer()
        
        start_time = time.time()
        personality_result = analyzer.analyze_personality(person, assessment_data)
        processing_time = time.time() - start_time
        
        personality_result.update({
            'task_id': self.request.id,
            'processing_time_seconds': processing_time,
            'timestamp': timezone.now().isoformat(),
            'success': True
        })
        
        logger.info(f"Personality analysis completed for person {person_id}")
        return personality_result
        
    except Exception as exc:
        logger.error(f"Error in personality analysis: {str(exc)}")
        
        try:
            self.retry(countdown=60 * (self.request.retries + 1))
        except MaxRetriesExceededError:
            return {'error': str(exc), 'success': False, 'max_retries_exceeded': True}


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def analyze_cultural_compatibility(self, person_id: str, company_id: str) -> Dict[str, Any]:
    """
    Analiza la compatibilidad cultural entre candidato y empresa.
    """
    try:
        from apps.ml.aura.compatibility_analyzer import CompatibilityAnalyzer
        from apps.core.models import Person, Company
        
        logger.info(f"Starting cultural compatibility analysis: person {person_id} <-> company {company_id}")
        
        person = Person.objects.get(id=person_id)
        company = Company.objects.get(id=company_id)
        analyzer = CompatibilityAnalyzer()
        
        start_time = time.time()
        compatibility_result = analyzer.analyze_cultural_fit(person, company)
        processing_time = time.time() - start_time
        
        compatibility_result.update({
            'task_id': self.request.id,
            'processing_time_seconds': processing_time,
            'timestamp': timezone.now().isoformat(),
            'success': True
        })
        
        logger.info(f"Cultural compatibility analysis completed")
        return compatibility_result
        
    except Exception as exc:
        logger.error(f"Error in cultural compatibility analysis: {str(exc)}")
        
        try:
            self.retry(countdown=60 * (self.request.retries + 1))
        except MaxRetriesExceededError:
            return {'error': str(exc), 'success': False, 'max_retries_exceeded': True}


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def perform_vibrational_matching(self, person_id: str, target_profiles: List[Dict] = None) -> Dict[str, Any]:
    """
    Realiza matching vibracional avanzado usando AURA.
    """
    try:
        from apps.ml.aura.vibrational_matcher import VibrationalMatcher
        from apps.core.models import Person
        
        logger.info(f"Starting vibrational matching for person {person_id}")
        
        person = Person.objects.get(id=person_id)
        matcher = VibrationalMatcher()
        
        start_time = time.time()
        matching_result = matcher.perform_vibrational_analysis(person, target_profiles)
        processing_time = time.time() - start_time
        
        matching_result.update({
            'task_id': self.request.id,
            'processing_time_seconds': processing_time,
            'timestamp': timezone.now().isoformat(),
            'success': True
        })
        
        logger.info(f"Vibrational matching completed for person {person_id}")
        return matching_result
        
    except Exception as exc:
        logger.error(f"Error in vibrational matching: {str(exc)}")
        
        try:
            self.retry(countdown=60 * (self.request.retries + 1))
        except MaxRetriesExceededError:
            return {'error': str(exc), 'success': False, 'max_retries_exceeded': True}


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def generate_holistic_assessment(self, person_id: str, context: Dict = None) -> Dict[str, Any]:
    """
    Genera una evaluación holística completa usando AURA.
    """
    try:
        from apps.ml.aura.holistic_assessor import HolisticAssessor
        from apps.core.models import Person
        
        logger.info(f"Starting holistic assessment for person {person_id}")
        
        person = Person.objects.get(id=person_id)
        assessor = HolisticAssessor()
        
        start_time = time.time()
        assessment_result = assessor.generate_holistic_profile(person, context)
        processing_time = time.time() - start_time
        
        assessment_result.update({
            'task_id': self.request.id,
            'processing_time_seconds': processing_time,
            'timestamp': timezone.now().isoformat(),
            'success': True
        })
        
        logger.info(f"Holistic assessment completed for person {person_id}")
        return assessment_result
        
    except Exception as exc:
        logger.error(f"Error in holistic assessment: {str(exc)}")
        
        try:
            self.retry(countdown=60 * (self.request.retries + 1))
        except MaxRetriesExceededError:
            return {'error': str(exc), 'success': False, 'max_retries_exceeded': True}


# ============================================================================
# TASKS DE WORKFLOW
# ============================================================================

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_workflow_transition(self, workflow_instance_id: str, target_stage_id: str, user_id: str = None) -> Dict[str, Any]:
    """
    Procesa la transición de un workflow a la siguiente etapa.
    """
    try:
        from apps.core.models import WorkflowInstance, WorkflowStage
        from django.contrib.auth.models import User
        
        logger.info(f"Processing workflow transition: {workflow_instance_id} -> {target_stage_id}")
        
        workflow_instance = WorkflowInstance.objects.get(id=workflow_instance_id)
        target_stage = WorkflowStage.objects.get(id=target_stage_id)
        user = User.objects.get(id=user_id) if user_id else None
        
        start_time = time.time()
        
        # Verificar si puede avanzar
        can_advance, reason = workflow_instance.current_stage.can_advance_to_next(workflow_instance)
        if not can_advance:
            return {
                'success': False,
                'error': f"Cannot advance workflow: {reason}",
                'task_id': self.request.id
            }
        
        # Ejecutar transición
        old_stage = workflow_instance.current_stage
        workflow_instance.current_stage = target_stage
        workflow_instance.save()
        
        # Ejecutar acciones de salida de la etapa anterior
        if old_stage:
            old_stage.execute_exit_actions(workflow_instance)
        
        # Ejecutar acciones de entrada de la nueva etapa
        target_stage.execute_entry_actions(workflow_instance)
        
        # Crear logs
        workflow_instance.create_stage_log(target_stage, 'entered', user)
        
        processing_time = time.time() - start_time
        
        result = {
            'workflow_instance_id': workflow_instance_id,
            'old_stage': old_stage.name if old_stage else None,
            'new_stage': target_stage.name,
            'user_id': user_id,
            'processing_time_seconds': processing_time,
            'timestamp': timezone.now().isoformat(),
            'success': True,
            'task_id': self.request.id
        }
        
        logger.info(f"Workflow transition completed: {old_stage.name if old_stage else 'None'} -> {target_stage.name}")
        return result
        
    except Exception as exc:
        logger.error(f"Error in workflow transition: {str(exc)}")
        
        try:
            self.retry(countdown=60 * (self.request.retries + 1))
        except MaxRetriesExceededError:
            return {'error': str(exc), 'success': False, 'max_retries_exceeded': True}


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def auto_advance_workflows(self) -> Dict[str, Any]:
    """
    Avanza automáticamente workflows que cumplan condiciones.
    """
    try:
        from apps.core.models import WorkflowInstance
        
        logger.info("Starting automatic workflow advancement")
        
        # Buscar workflows en estado activo con auto-advance habilitado
        workflows = WorkflowInstance.objects.filter(
            status='active',
            current_stage__isnull=False
        ).select_related('current_stage', 'template')
        
        processed_count = 0
        advanced_count = 0
        errors = []
        
        for workflow in workflows:
            try:
                # Verificar si la etapa actual tiene auto-advance habilitado
                stage_config = workflow.current_stage.config
                if not stage_config.get('auto_advance', False):
                    continue
                
                processed_count += 1
                
                # Verificar condiciones de salida
                can_advance, reason = workflow.current_stage.can_advance_to_next(workflow)
                if can_advance:
                    next_stage = workflow.current_stage.get_next_stage()
                    if next_stage:
                        workflow.advance_to_next_stage()
                        advanced_count += 1
                        logger.info(f"Auto-advanced workflow {workflow.id} to stage {next_stage.name}")
                    else:
                        # Workflow completado
                        workflow.complete()
                        advanced_count += 1
                        logger.info(f"Auto-completed workflow {workflow.id}")
                        
            except Exception as exc:
                error_msg = f"Error processing workflow {workflow.id}: {str(exc)}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        result = {
            'total_workflows_checked': workflows.count(),
            'workflows_processed': processed_count,
            'workflows_advanced': advanced_count,
            'errors': errors,
            'timestamp': timezone.now().isoformat(),
            'success': True,
            'task_id': self.request.id
        }
        
        logger.info(f"Automatic workflow advancement completed: {advanced_count}/{processed_count} workflows advanced")
        return result
        
    except Exception as exc:
        logger.error(f"Error in automatic workflow advancement: {str(exc)}")
        return {'error': str(exc), 'success': False, 'task_id': self.request.id}


# ============================================================================
# TASKS DE NOTIFICACIONES
# ============================================================================

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_notification(self, notification_id: str) -> Dict[str, Any]:
    """
    Envía una notificación específica.
    """
    try:
        from apps.core.models import Notification
        from apps.services.notification_service import NotificationService
        
        logger.info(f"Sending notification {notification_id}")
        
        notification = Notification.objects.get(id=notification_id)
        service = NotificationService()
        
        start_time = time.time()
        
        # Verificar si se puede enviar
        if not notification.can_send_now():
            return {
                'success': False,
                'error': 'Notification cannot be sent now',
                'notification_id': notification_id,
                'task_id': self.request.id
            }
        
        # Enviar notificación
        success = service.send_notification(notification)
        processing_time = time.time() - start_time
        
        result = {
            'notification_id': notification_id,
            'channel_type': notification.channel.channel_type,
            'recipient': str(notification.recipient.id),
            'success': success,
            'processing_time_seconds': processing_time,
            'timestamp': timezone.now().isoformat(),
            'task_id': self.request.id
        }
        
        if success:
            logger.info(f"Notification {notification_id} sent successfully")
        else:
            logger.warning(f"Failed to send notification {notification_id}")
        
        return result
        
    except Exception as exc:
        logger.error(f"Error sending notification {notification_id}: {str(exc)}")
        
        try:
            self.retry(countdown=60 * (self.request.retries + 1))
        except MaxRetriesExceededError:
            return {'error': str(exc), 'success': False, 'max_retries_exceeded': True}


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_notification_queue(self, queue_id: str = None) -> Dict[str, Any]:
    """
    Procesa una cola de notificaciones.
    """
    try:
        from apps.core.models import NotificationQueue, Notification
        from apps.services.notification_service import NotificationService
        
        logger.info(f"Processing notification queue {queue_id or 'default'}")
        
        if queue_id:
            queues = NotificationQueue.objects.filter(id=queue_id, is_active=True, is_paused=False)
        else:
            queues = NotificationQueue.objects.filter(is_active=True, is_paused=False)
        
        service = NotificationService()
        total_processed = 0
        total_success = 0
        total_failed = 0
        
        for queue in queues:
            logger.info(f"Processing queue: {queue.name}")
            
            # Obtener siguiente lote
            notifications = queue.get_next_batch()
            
            for notification in notifications:
                try:
                    success = service.send_notification(notification)
                    queue.mark_processed(notification, success)
                    
                    if success:
                        total_success += 1
                    else:
                        total_failed += 1
                    
                    total_processed += 1
                    
                except Exception as exc:
                    logger.error(f"Error processing notification {notification.id}: {str(exc)}")
                    queue.mark_processed(notification, False)
                    total_failed += 1
                    total_processed += 1
        
        result = {
            'queues_processed': queues.count(),
            'total_notifications_processed': total_processed,
            'successful_sends': total_success,
            'failed_sends': total_failed,
            'timestamp': timezone.now().isoformat(),
            'success': True,
            'task_id': self.request.id
        }
        
        logger.info(f"Notification queue processing completed: {total_success}/{total_processed} successful")
        return result
        
    except Exception as exc:
        logger.error(f"Error processing notification queue: {str(exc)}")
        return {'error': str(exc), 'success': False, 'task_id': self.request.id}


# ============================================================================
# TASKS DE ASSESSMENT
# ============================================================================

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def grade_assessment_instance(self, assessment_instance_id: str) -> Dict[str, Any]:
    """
    Califica automáticamente un assessment completado.
    """
    try:
        from apps.core.models import AssessmentInstance
        from apps.services.assessment_service import AssessmentService
        
        logger.info(f"Grading assessment instance {assessment_instance_id}")
        
        instance = AssessmentInstance.objects.get(id=assessment_instance_id)
        service = AssessmentService()
        
        start_time = time.time()
        grading_result = service.auto_grade_assessment(instance)
        processing_time = time.time() - start_time
        
        result = {
            'assessment_instance_id': assessment_instance_id,
            'template_name': instance.template.name,
            'person_id': str(instance.person.id),
            'final_score': grading_result.get('final_score'),
            'passed': grading_result.get('passed'),
            'auto_feedback': grading_result.get('feedback'),
            'processing_time_seconds': processing_time,
            'timestamp': timezone.now().isoformat(),
            'success': True,
            'task_id': self.request.id
        }
        
        logger.info(f"Assessment grading completed for instance {assessment_instance_id}")
        return result
        
    except Exception as exc:
        logger.error(f"Error grading assessment: {str(exc)}")
        
        try:
            self.retry(countdown=60 * (self.request.retries + 1))
        except MaxRetriesExceededError:
            return {'error': str(exc), 'success': False, 'max_retries_exceeded': True}


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def generate_assessment_report(self, assessment_instance_id: str, report_type: str = 'full') -> Dict[str, Any]:
    """
    Genera un reporte detallado de un assessment.
    """
    try:
        from apps.core.models import AssessmentInstance
        from apps.services.report_service import ReportService
        
        logger.info(f"Generating assessment report for instance {assessment_instance_id}")
        
        instance = AssessmentInstance.objects.get(id=assessment_instance_id)
        service = ReportService()
        
        start_time = time.time()
        report = service.generate_assessment_report(instance, report_type)
        processing_time = time.time() - start_time
        
        result = {
            'assessment_instance_id': assessment_instance_id,
            'report_type': report_type,
            'report_data': report,
            'processing_time_seconds': processing_time,
            'timestamp': timezone.now().isoformat(),
            'success': True,
            'task_id': self.request.id
        }
        
        logger.info(f"Assessment report generated for instance {assessment_instance_id}")
        return result
        
    except Exception as exc:
        logger.error(f"Error generating assessment report: {str(exc)}")
        
        try:
            self.retry(countdown=60 * (self.request.retries + 1))
        except MaxRetriesExceededError:
            return {'error': str(exc), 'success': False, 'max_retries_exceeded': True}


# ============================================================================
# TASKS DE MANTENIMIENTO Y LIMPIEZA
# ============================================================================

@shared_task(bind=True)
def cleanup_expired_sessions(self) -> Dict[str, Any]:
    """
    Limpia sesiones expiradas y datos temporales.
    """
    try:
        from django.contrib.sessions.models import Session
        from apps.core.models import Notification, AssessmentInstance
        
        logger.info("Starting cleanup of expired sessions and data")
        
        # Limpiar sesiones expiradas
        expired_sessions = Session.objects.filter(expire_date__lt=timezone.now())
        sessions_deleted = expired_sessions.count()
        expired_sessions.delete()
        
        # Limpiar notificaciones expiradas
        expired_notifications = Notification.objects.filter(
            expires_at__lt=timezone.now(),
            status__in=['pending', 'queued']
        )
        notifications_expired = expired_notifications.count()
        expired_notifications.update(status='expired')
        
        # Limpiar assessments abandonados (iniciados hace más de 24 horas sin completar)
        cutoff_time = timezone.now() - timedelta(hours=24)
        abandoned_assessments = AssessmentInstance.objects.filter(
            status__in=['started', 'in_progress'],
            started_at__lt=cutoff_time
        )
        assessments_expired = abandoned_assessments.count()
        abandoned_assessments.update(status='expired')
        
        result = {
            'sessions_deleted': sessions_deleted,
            'notifications_expired': notifications_expired,
            'assessments_expired': assessments_expired,
            'timestamp': timezone.now().isoformat(),
            'success': True,
            'task_id': self.request.id
        }
        
        logger.info(f"Cleanup completed: {sessions_deleted} sessions, {notifications_expired} notifications, {assessments_expired} assessments")
        return result
        
    except Exception as exc:
        logger.error(f"Error in cleanup task: {str(exc)}")
        return {'error': str(exc), 'success': False, 'task_id': self.request.id}


@shared_task(bind=True)
def update_ml_model_metrics(self) -> Dict[str, Any]:
    """
    Actualiza métricas de los modelos ML.
    """
    try:
        from apps.ml.core.metrics import MLMetricsCollector
        
        logger.info("Starting ML model metrics update")
        
        collector = MLMetricsCollector()
        start_time = time.time()
        
        # Actualizar métricas de todos los modelos
        metrics_result = collector.update_all_model_metrics()
        processing_time = time.time() - start_time
        
        result = {
            'models_updated': metrics_result.get('models_updated', 0),
            'metrics_collected': metrics_result.get('metrics_collected', 0),
            'errors': metrics_result.get('errors', []),
            'processing_time_seconds': processing_time,
            'timestamp': timezone.now().isoformat(),
            'success': True,
            'task_id': self.request.id
        }
        
        logger.info(f"ML metrics update completed: {result['models_updated']} models updated")
        return result
        
    except Exception as exc:
        logger.error(f"Error updating ML metrics: {str(exc)}")
        return {'error': str(exc), 'success': False, 'task_id': self.request.id}


# ============================================================================
# TASKS COMPUESTOS/WORKFLOWS
# ============================================================================

@shared_task(bind=True, max_retries=2, default_retry_delay=120)
def complete_candidate_analysis(self, person_id: str, job_position_id: str = None) -> Dict[str, Any]:
    """
    Realiza un análisis completo de candidato (GenIA + AURA).
    """
    try:
        logger.info(f"Starting complete candidate analysis for person {person_id}")
        
        start_time = time.time()
        results = {}
        
        # Ejecutar análisis GenIA en paralelo
        genia_tasks = [
            analyze_candidate_skills.delay(person_id, job_position_id),
            analyze_candidate_experience.delay(person_id),
            analyze_resume_content.delay(person_id)
        ]
        
        # Ejecutar análisis AURA en paralelo
        aura_tasks = [
            analyze_personality_profile.delay(person_id),
            generate_holistic_assessment.delay(person_id)
        ]
        
        # Esperar resultados GenIA
        for i, task in enumerate(genia_tasks):
            task_name = ['skills', 'experience', 'resume'][i]
            try:
                result = task.get(timeout=300)  # 5 minutos timeout
                results[f'genia_{task_name}'] = result
            except Exception as exc:
                logger.error(f"Error in GenIA {task_name} analysis: {str(exc)}")
                results[f'genia_{task_name}'] = {'error': str(exc), 'success': False}
        
        # Esperar resultados AURA
        for i, task in enumerate(aura_tasks):
            task_name = ['personality', 'holistic'][i]
            try:
                result = task.get(timeout=300)  # 5 minutos timeout
                results[f'aura_{task_name}'] = result
            except Exception as exc:
                logger.error(f"Error in AURA {task_name} analysis: {str(exc)}")
                results[f'aura_{task_name}'] = {'error': str(exc), 'success': False}
        
        # Si tenemos job_position_id, realizar matching
        if job_position_id:
            try:
                matching_result = match_candidate_to_jobs.delay(person_id, [job_position_id])
                results['job_matching'] = matching_result.get(timeout=180)
            except Exception as exc:
                logger.error(f"Error in job matching: {str(exc)}")
                results['job_matching'] = {'error': str(exc), 'success': False}
        
        processing_time = time.time() - start_time
        
        # Consolidar resultados
        final_result = {
            'person_id': person_id,
            'job_position_id': job_position_id,
            'analysis_results': results,
            'total_processing_time_seconds': processing_time,
            'timestamp': timezone.now().isoformat(),
            'success': True,
            'task_id': self.request.id
        }
        
        logger.info(f"Complete candidate analysis finished for person {person_id} in {processing_time:.2f}s")
        return final_result
        
    except Exception as exc:
        logger.error(f"Error in complete candidate analysis: {str(exc)}")
        
        try:
            self.retry(countdown=120 * (self.request.retries + 1))
        except MaxRetriesExceededError:
            return {'error': str(exc), 'success': False, 'max_retries_exceeded': True}


# ============================================================================
# TASKS PERIÓDICOS
# ============================================================================

@shared_task(bind=True)
def daily_system_maintenance(self) -> Dict[str, Any]:
    """
    Mantenimiento diario del sistema.
    """
    try:
        logger.info("Starting daily system maintenance")
        
        start_time = time.time()
        maintenance_results = {}
        
        # Ejecutar tareas de mantenimiento
        cleanup_task = cleanup_expired_sessions.delay()
        metrics_task = update_ml_model_metrics.delay()
        workflow_task = auto_advance_workflows.delay()
        
        # Esperar resultados
        try:
            maintenance_results['cleanup'] = cleanup_task.get(timeout=300)
        except Exception as exc:
            maintenance_results['cleanup'] = {'error': str(exc)}
        
        try:
            maintenance_results['metrics'] = metrics_task.get(timeout=600)
        except Exception as exc:
            maintenance_results['metrics'] = {'error': str(exc)}
        
        try:
            maintenance_results['workflows'] = workflow_task.get(timeout=300)
        except Exception as exc:
            maintenance_results['workflows'] = {'error': str(exc)}
        
        processing_time = time.time() - start_time
        
        result = {
            'maintenance_results': maintenance_results,
            'total_processing_time_seconds': processing_time,
            'timestamp': timezone.now().isoformat(),
            'success': True,
            'task_id': self.request.id
        }
        
        logger.info(f"Daily system maintenance completed in {processing_time:.2f}s")
        return result
        
    except Exception as exc:
        logger.error(f"Error in daily system maintenance: {str(exc)}")
        return {'error': str(exc), 'success': False, 'task_id': self.request.id}