from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from datetime import datetime, timedelta
import asyncio
from django.urls import reverse

from app.ml.feedback.feedback_system import FeedbackEntry
from app.ml.feedback.feedback_system import FeedbackAggregator, ModelRetrainer
import json
from app.models import Person, BusinessUnit, Vacante, User
from app.ats.feedback.feedback_models import SkillFeedback
from app.ats.notifications.notification_manager import SkillFeedbackNotificationManager
from app.models import SkillAssessment

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_feedback(request):
    """Vista para enviar feedback sobre predicciones de skills"""
    try:
        data = json.loads(request.body)
        feedback = FeedbackEntry.objects.create(
            user=request.user,
            candidate_id=data['candidate_id'],
            skill_id=data['skill_id'],
            feedback_type=data['feedback_type'],
            confidence_score=data['confidence_score'],
            original_prediction=data['original_prediction'],
            feedback_notes=data.get('feedback_notes', '')
        )
        
        return Response({
            'status': 'success',
            'feedback_id': feedback.id
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'status': 'error',
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_feedback_stats(request, skill_id):
    """Vista para obtener estadísticas de feedback de un skill"""
    aggregator = FeedbackAggregator()
    stats = aggregator.get_skill_feedback_stats(skill_id)
    
    return Response(stats)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_feedback(request):
    """Vista para listar feedback con paginación"""
    page = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', 10)
    
    feedback_list = FeedbackEntry.objects.all().order_by('-created_at')
    paginator = Paginator(feedback_list, per_page)
    
    try:
        feedback_page = paginator.page(page)
        return Response({
            'status': 'success',
            'data': {
                'items': [
                    {
                        'id': item.id,
                        'user': item.user.username,
                        'candidate_id': item.candidate_id,
                        'skill_id': item.skill_id,
                        'feedback_type': item.feedback_type,
                        'confidence_score': item.confidence_score,
                        'created_at': item.created_at.isoformat()
                    }
                    for item in feedback_page
                ],
                'total_pages': paginator.num_pages,
                'current_page': int(page),
                'total_items': paginator.count
            }
        })
    except Exception as e:
        return Response({
            'status': 'error',
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def trigger_retraining(request, skill_id):
    """Vista para iniciar re-entrenamiento de un modelo"""
    retrainer = ModelRetrainer()
    
    if not retrainer.should_retrain(skill_id):
        return Response({
            'status': 'skipped',
            'reason': 'No cumple criterios de re-entrenamiento'
        }, status=status.HTTP_200_OK)
    
    try:
        result = retrainer.retrain_model(skill_id)
        return Response(result)
    except Exception as e:
        return Response({
            'status': 'error',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_feedback_details(request, feedback_id):
    """Vista para obtener detalles de un feedback específico"""
    feedback = get_object_or_404(FeedbackEntry, id=feedback_id)
    
    return Response({
        'status': 'success',
        'data': {
            'id': feedback.id,
            'user': feedback.user.username,
            'candidate_id': feedback.candidate_id,
            'skill_id': feedback.skill_id,
            'feedback_type': feedback.feedback_type,
            'confidence_score': feedback.confidence_score,
            'original_prediction': feedback.original_prediction,
            'feedback_notes': feedback.feedback_notes,
            'created_at': feedback.created_at.isoformat(),
            'updated_at': feedback.updated_at.isoformat()
        }
    })

@login_required
def get_feedback_form(request, vacante_id, candidate_id):
    """
    Muestra el formulario de feedback de habilidades.
    """
    try:
        vacante = Vacante.objects.get(id=vacante_id)
        candidate = Person.objects.get(id=candidate_id)
        
        # Verificamos que el usuario tenga permiso para ver este feedback
        if not request.user.has_perm('view_skill_feedback', vacante):
            return JsonResponse({'error': 'No tienes permiso para ver este feedback'}, status=403)
        
        # Obtenemos el feedback existente o creamos uno nuevo
        feedback, created = SkillFeedback.objects.get_or_create(
            vacante=vacante,
            candidate=candidate,
            defaults={
                'created_by': request.user,
                'business_unit': vacante.business_unit
            }
        )
        
        # Si es un nuevo feedback, enviamos notificación al responsable
        if created:
            notification_manager = SkillFeedbackNotificationManager(vacante.business_unit)
            asyncio.create_task(notification_manager.notify_feedback_required(
                recipient=vacante.responsible,
                vacante=vacante,
                candidate=candidate,
                skills=feedback.detected_skills,
                deadline=timezone.now() + timedelta(days=2)
            ))
        
        return render(request, 'feedback/skill_feedback_form.html', {
            'feedback': feedback,
            'vacante': vacante,
            'candidate': candidate
        })
        
    except (Vacante.DoesNotExist, Person.DoesNotExist):
        return JsonResponse({'error': 'Vacante o candidato no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def submit_structured_feedback(request, vacante_id, candidate_id):
    """
    Procesa el envío del formulario de feedback de habilidades.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
        
    try:
        vacante = Vacante.objects.get(id=vacante_id)
        candidate = Person.objects.get(id=candidate_id)
        
        # Verificamos que el usuario tenga permiso para enviar feedback
        if not request.user.has_perm('submit_skill_feedback', vacante):
            return JsonResponse({'error': 'No tienes permiso para enviar feedback'}, status=403)
        
        # Obtenemos o creamos el feedback
        feedback, created = SkillFeedback.objects.get_or_create(
            vacante=vacante,
            candidate=candidate,
            defaults={
                'created_by': request.user,
                'business_unit': vacante.business_unit
            }
        )
        
        # Actualizamos el feedback con los datos del formulario
        feedback.skill_accuracy = request.POST.get('skill_accuracy')
        feedback.missing_skills = request.POST.getlist('missing_skills')
        feedback.extra_skills = request.POST.getlist('extra_skills')
        feedback.was_hired = request.POST.get('was_hired') == 'true'
        feedback.technical_fit = int(request.POST.get('technical_fit', 0))
        feedback.cultural_fit = int(request.POST.get('cultural_fit', 0))
        feedback.strengths = request.POST.get('strengths')
        feedback.areas_for_improvement = request.POST.get('areas_for_improvement')
        feedback.potential_roles = request.POST.getlist('potential_roles')
        feedback.growth_potential = int(request.POST.get('growth_potential', 0))
        feedback.development_path = request.POST.get('development_path')
        feedback.market_demand = request.POST.get('market_demand')
        feedback.salary_range = request.POST.get('salary_range')
        feedback.market_notes = request.POST.get('market_notes')
        feedback.updated_by = request.user
        feedback.updated_at = timezone.now()
        
        # Guardamos el feedback
        feedback.save()
        
        # Enviamos notificación de feedback completado
        notification_manager = SkillFeedbackNotificationManager(vacante.business_unit)
        asyncio.create_task(notification_manager.notify_feedback_completed(
            recipient=vacante.responsible,
            vacante=vacante,
            candidate=candidate,
            feedback_data={
                'skill_accuracy': feedback.skill_accuracy,
                'missing_skills': feedback.missing_skills,
                'extra_skills': feedback.extra_skills,
                'development_time': feedback.development_time,
                'critical_skills': feedback.critical_skills
            }
        ))
        
        # Si hay habilidades críticas, enviamos una alerta
        if feedback.critical_skills:
            asyncio.create_task(notification_manager.notify_critical_skills_alert(
                recipient=vacante.responsible,
                vacante=vacante,
                candidate=candidate,
                critical_skills=feedback.critical_skills,
                development_time=feedback.development_time
            ))
        
        return JsonResponse({
            'success': True,
            'message': 'Feedback guardado exitosamente',
            'redirect_url': reverse('feedback_thanks')
        })
        
    except (Vacante.DoesNotExist, Person.DoesNotExist):
        return JsonResponse({'error': 'Vacante o candidato no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_http_methods(["POST"])
def validate_skill_assessment(request, assessment_id):
    """
    Vista para validar una evaluación de skill.
    Permite a los usuarios con permisos apropiados validar o rechazar
    una evaluación de skill, con la opción de agregar notas.
    """
    try:
        assessment = SkillAssessment.objects.get(id=assessment_id)
        
        # Verificar permisos
        if not request.user.has_perm('validate_skill_assessment'):
            return JsonResponse({
                'error': 'No tienes permiso para validar evaluaciones de skills'
            }, status=403)
        
        data = json.loads(request.body)
        status = data.get('status')
        notes = data.get('notes')
        
        if status not in dict(SkillAssessment.VALIDATION_STATUS).keys():
            return JsonResponse({
                'error': 'Estado de validación inválido'
            }, status=400)
        
        # Validar la evaluación
        assessment.validate(
            validator=request.user,
            status=status,
            notes=notes
        )
        
        # Si la evaluación es validada, actualizar el skill del candidato
        if status == 'VALIDATED':
            assessment.update_person_skill()
        
        return JsonResponse({
            'status': 'success',
            'assessment': {
                'id': assessment.id,
                'validation_status': assessment.validation_status,
                'validation_date': assessment.validation_date,
                'validator': assessment.validator.get_full_name() if assessment.validator else None,
                'validation_notes': assessment.validation_notes
            }
        })
        
    except SkillAssessment.DoesNotExist:
        return JsonResponse({
            'error': 'Evaluación no encontrada'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)

@login_required
@require_http_methods(["GET"])
def get_skill_assessment_details(request, assessment_id):
    """
    Vista para obtener detalles de una evaluación de skill,
    incluyendo su estado de validación y notas.
    """
    try:
        assessment = SkillAssessment.objects.get(id=assessment_id)
        
        return JsonResponse({
            'status': 'success',
            'assessment': {
                'id': assessment.id,
                'person': {
                    'id': assessment.person.id,
                    'name': assessment.person.nombre
                },
                'skill': {
                    'id': assessment.skill.id,
                    'name': assessment.skill.name
                },
                'expertise_level': assessment.expertise_level,
                'score': assessment.score,
                'assessment_type': assessment.assessment_type,
                'assessment_date': assessment.assessment_date,
                'evaluator': assessment.evaluator.nombre if assessment.evaluator else None,
                'evidence': assessment.evidence,
                'context': assessment.context,
                'validation_status': assessment.validation_status,
                'validation_date': assessment.validation_date,
                'validator': assessment.validator.get_full_name() if assessment.validator else None,
                'validation_notes': assessment.validation_notes
            }
        })
        
    except SkillAssessment.DoesNotExist:
        return JsonResponse({
            'error': 'Evaluación no encontrada'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500) 