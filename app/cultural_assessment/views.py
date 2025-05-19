"""
Vistas para el Sistema de Análisis Cultural de Grupo huntRED®.

Implementa las vistas, APIs y endpoints necesarios para gestionar
las evaluaciones culturales y reportes, optimizado para bajo uso
de CPU y siguiendo reglas globales.
"""

import logging
import json
from datetime import datetime, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, Http404, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Count, Avg, F, Q
from django.conf import settings
from django.urls import reverse
from django.core.cache import cache

from app.models_cultural import (
    CulturalAssessment, OrganizationalCulture, CulturalDimension, 
    CulturalValue, CulturalProfile, CulturalReport
)
from app.models import Person, BusinessUnit, Organization, Application
from app.utils.cache import cache_result
from app.utils.rbac import check_permission, has_organization_access

logger = logging.getLogger(__name__)

# Vistas públicas para participantes

def assessment_view(request, token):
    """Vista principal para realizar evaluación cultural"""
    # Obtener la evaluación utilizando el token
    assessment = get_object_or_404(
        CulturalAssessment.objects.select_related(
            'person', 'organization', 'organizational_culture', 'business_unit'
        ),
        invitation_token=token
    )
    
    # Verificar si la evaluación ya fue completada
    if assessment.status == 'completed':
        return redirect('cultural_assessment_complete', token=token)
    
    # Verificar si la evaluación expiró
    if assessment.status == 'expired' or (
        assessment.expiration_date and assessment.expiration_date < timezone.now()
    ):
        assessment.status = 'expired'
        assessment.save(update_fields=['status'])
        return render(request, 'cultural_assessment/expired.html', {
            'assessment': assessment
        })
    
    # Actualizar estado si es la primera vez que accede
    if assessment.status == 'invited' or assessment.status == 'pending':
        assessment.status = 'in_progress'
        assessment.started_at = timezone.now()
        assessment.save(update_fields=['status', 'started_at'])
    
    # Actualizar timestamp de última interacción
    assessment.last_interaction = timezone.now()
    assessment.save(update_fields=['last_interaction'])
    
    # Obtener las dimensiones culturales a evaluar
    dimensions = CulturalDimension.objects.filter(
        business_unit=assessment.business_unit,
        active=True
    ).order_by('category', 'name')
    
    # Obtener las dimensiones ya respondidas
    answered_dimensions = []
    if assessment.assessment_data and 'responses' in assessment.assessment_data:
        answered_dimensions = list(map(int, assessment.assessment_data['responses'].keys()))
    
    # Organizar las dimensiones por estado (respondidas y pendientes)
    dimensions_data = {
        'answered': [],
        'pending': []
    }
    
    for dimension in dimensions:
        values = CulturalValue.objects.filter(
            dimension=dimension,
            active=True
        ).order_by('?')[:3]  # Muestra algunos valores aleatorios como ejemplo
        
        dimension_data = {
            'id': dimension.id,
            'name': dimension.name,
            'category': dimension.category,
            'description': dimension.description,
            'sample_values': [
                {
                    'id': value.id,
                    'name': value.name,
                    'statement': value.positive_statement
                } for value in values
            ]
        }
        
        if dimension.id in answered_dimensions:
            response = assessment.assessment_data['responses'][str(dimension.id)]
            dimension_data['response'] = response.get('value')
            dimensions_data['answered'].append(dimension_data)
        else:
            dimensions_data['pending'].append(dimension_data)
    
    # Calcular progreso
    total_dimensions = len(dimensions)
    answered_count = len(dimensions_data['answered'])
    
    if total_dimensions > 0:
        progress_percentage = (answered_count / total_dimensions) * 100
    else:
        progress_percentage = 0
    
    context = {
        'assessment': assessment,
        'dimensions': dimensions_data,
        'progress': {
            'total': total_dimensions,
            'answered': answered_count,
            'percentage': progress_percentage
        },
        'person': assessment.person,
        'organization': assessment.organization
    }
    
    return render(request, 'cultural_assessment/assessment.html', context)


def assessment_complete_view(request, token):
    """Vista de finalización de evaluación cultural"""
    # Obtener la evaluación utilizando el token
    assessment = get_object_or_404(
        CulturalAssessment.objects.select_related(
            'person', 'organization', 'organizational_culture'
        ),
        invitation_token=token
    )
    
    # Si no está completa, redirigir a la evaluación
    if assessment.status != 'completed':
        return redirect('cultural_assessment', token=token)
    
    # Actualizar perfil cultural si no se ha hecho ya
    profile = assessment.update_profile()
    
    context = {
        'assessment': assessment,
        'profile': profile,
        'person': assessment.person,
        'organization': assessment.organization,
        'completion_date': assessment.completed_at
    }
    
    return render(request, 'cultural_assessment/complete.html', context)


def report_view(request, token):
    """Vista de reporte cultural"""
    # Obtener el reporte utilizando el token
    report = get_object_or_404(
        CulturalReport.objects.select_related(
            'organization', 'organizational_culture', 'business_unit'
        ),
        access_token=token,
        is_public=True
    )
    
    # Verificar si el reporte está completo
    if report.status != 'completed':
        return render(request, 'cultural_assessment/report_pending.html', {
            'report': report
        })
    
    context = {
        'report': report,
        'organization': report.organization,
        'dimensions': report.report_data.get('dimensions', {}),
        'strengths': report.strengths,
        'areas_of_improvement': report.areas_of_improvement,
        'recommendations': report.recommendations,
        'participants': report.participant_count
    }
    
    return render(request, 'cultural_assessment/report.html', context)


# APIs para AJAX y Chatbot

@csrf_exempt
@require_POST
def api_save_dimension_response(request, dimension_id):
    """API para guardar respuesta a una dimensión cultural"""
    try:
        # Validar parámetros
        data = json.loads(request.body)
        token = data.get('token')
        response_value = data.get('value')
        
        if not token or response_value is None:
            return JsonResponse({
                'success': False,
                'error': 'Parámetros faltantes'
            }, status=400)
        
        # Validar valor de respuesta
        try:
            response_value = float(response_value)
            if response_value < 1 or response_value > 5:
                raise ValueError()
        except (ValueError, TypeError):
            return JsonResponse({
                'success': False,
                'error': 'Valor de respuesta inválido, debe ser un número entre 1 y 5'
            }, status=400)
        
        # Obtener la evaluación utilizando el token
        assessment = get_object_or_404(
            CulturalAssessment,
            invitation_token=token,
            status__in=['in_progress', 'pending']
        )
        
        # Obtener la dimensión cultural
        dimension = get_object_or_404(
            CulturalDimension,
            id=dimension_id,
            business_unit=assessment.business_unit,
            active=True
        )
        
        # Inicializar datos de evaluación si es necesario
        assessment_data = assessment.assessment_data or {}
        dimensions_scores = assessment.dimensions_scores or {}
        
        if 'responses' not in assessment_data:
            assessment_data['responses'] = {}
        
        # Guardar respuesta
        assessment_data['responses'][str(dimension_id)] = {
            'value': response_value,
            'timestamp': timezone.now().isoformat(),
            'dimension_name': dimension.name,
            'dimension_category': dimension.category
        }
        
        # Actualizar puntuación de dimensión
        dimensions_scores[str(dimension_id)] = response_value
        
        # Calcular porcentaje de completitud
        total_dimensions = CulturalDimension.objects.filter(
            business_unit=assessment.business_unit, 
            active=True
        ).count()
        
        if total_dimensions > 0:
            completion_percentage = (len(dimensions_scores) / total_dimensions) * 100
            # Limitar al 100%
            completion_percentage = min(completion_percentage, 100)
        else:
            completion_percentage = 0
        
        # Actualizar la evaluación
        assessment.assessment_data = assessment_data
        assessment.dimensions_scores = dimensions_scores
        assessment.completion_percentage = completion_percentage
        assessment.last_interaction = timezone.now()
        
        # Si se completó la evaluación
        if completion_percentage >= 100:
            assessment.status = 'completed'
            assessment.completed_at = timezone.now()
            
            # Calcular factor de riesgo (simplificado)
            risk_scores = []
            for dim_id, score in dimensions_scores.items():
                deviation = abs(score - 3.0)
                risk = (deviation / 2.0) * 100
                risk_scores.append(risk)
            
            if risk_scores:
                assessment.risk_factor = sum(risk_scores) / len(risk_scores)
            
            # Actualizar perfil cultural
            profile = assessment.update_profile()
        
        assessment.save()
        
        # Verificar si quedan dimensiones pendientes
        pending_dimensions = CulturalDimension.objects.filter(
            business_unit=assessment.business_unit,
            active=True
        ).exclude(
            id__in=[int(d) for d in dimensions_scores.keys()]
        ).values('id', 'name', 'category', 'description').order_by('category', 'name')
        
        # Preparar respuesta
        result = {
            'success': True,
            'dimension_id': dimension_id,
            'value': response_value,
            'completion': {
                'percentage': completion_percentage,
                'is_complete': completion_percentage >= 100
            },
            'pending_dimensions': list(pending_dimensions)
        }
        
        return JsonResponse(result)
    
    except Exception as e:
        logger.exception(f"Error guardando respuesta cultural: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f"Error procesando solicitud: {str(e)}"
        }, status=500)


@require_GET
def api_assessment_status(request, assessment_id):
    """API para consultar estado de evaluación cultural"""
    try:
        # Validar acceso mediante token o sesión autenticada
        token = request.GET.get('token')
        
        if token:
            # Acceso público con token
            assessment = get_object_or_404(
                CulturalAssessment,
                id=assessment_id,
                invitation_token=token
            )
        elif request.user.is_authenticated:
            # Acceso autenticado, verificar permisos
            assessment = get_object_or_404(CulturalAssessment, id=assessment_id)
            
            # Verificar si tiene acceso a la organización
            if not has_organization_access(request.user, assessment.organization):
                return JsonResponse({
                    'success': False,
                    'error': 'No tiene permisos para acceder a esta evaluación'
                }, status=403)
        else:
            return JsonResponse({
                'success': False,
                'error': 'Acceso no autorizado'
            }, status=401)
        
        # Construir respuesta
        result = {
            'success': True,
            'assessment': {
                'id': assessment.id,
                'status': assessment.status,
                'completion_percentage': assessment.completion_percentage,
                'person': {
                    'name': f"{assessment.person.first_name} {assessment.person.last_name}",
                    'email': assessment.person.email
                },
                'organization': {
                    'name': assessment.organization.name,
                    'id': assessment.organization.id
                },
                'started_at': assessment.started_at.isoformat() if assessment.started_at else None,
                'completed_at': assessment.completed_at.isoformat() if assessment.completed_at else None,
                'last_interaction': assessment.last_interaction.isoformat() if assessment.last_interaction else None
            }
        }
        
        # Si está completada, incluir datos adicionales
        if assessment.status == 'completed':
            result['assessment']['risk_factor'] = assessment.risk_factor
            
            # Buscar perfil cultural
            try:
                profile = CulturalProfile.objects.get(person=assessment.person)
                result['cultural_profile'] = {
                    'id': profile.id,
                    'strengths': profile.strengths[:3] if hasattr(profile, 'strengths') else [],
                    'improvement_areas': profile.areas_of_improvement[:3] if hasattr(profile, 'areas_of_improvement') else []
                }
            except CulturalProfile.DoesNotExist:
                pass
        
        return JsonResponse(result)
    
    except Exception as e:
        logger.exception(f"Error consultando estado de evaluación: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f"Error procesando solicitud: {str(e)}"
        }, status=500)


# Vistas de dashboard (acceso autenticado)

@login_required
@cache_result(prefix="cultural_dashboard", timeout=300)
def dashboard_view(request):
    """Vista principal del dashboard de análisis cultural"""
    # Verificar permisos
    if not check_permission(request.user, 'cultural_assessment.view_dashboard'):
        return HttpResponseForbidden("No tiene permisos para acceder a esta sección")
    
    # Obtener organizaciones a las que tiene acceso
    if request.user.is_superuser:
        organizations = Organization.objects.all()
    else:
        organizations = Organization.objects.filter(
            Q(consultant=request.user) | 
            Q(businessunit__consultant=request.user)
        ).distinct()
    
    # Obtener perfiles culturales organizacionales
    org_cultures = OrganizationalCulture.objects.filter(
        organization__in=organizations,
        is_current=True
    ).select_related('organization', 'business_unit')
    
    # Obtener estadísticas generales
    total_assessments = CulturalAssessment.objects.filter(
        organization__in=organizations
    ).count()
    
    completed_assessments = CulturalAssessment.objects.filter(
        organization__in=organizations,
        status='completed'
    ).count()
    
    completion_rate = (completed_assessments / total_assessments * 100) if total_assessments > 0 else 0
    
    # Obtener reportes recientes
    recent_reports = CulturalReport.objects.filter(
        organization__in=organizations,
        status='completed'
    ).select_related('organization').order_by('-completed_at')[:5]
    
    context = {
        'organizations': organizations,
        'org_cultures': org_cultures,
        'stats': {
            'total_assessments': total_assessments,
            'completed_assessments': completed_assessments,
            'completion_rate': completion_rate
        },
        'recent_reports': recent_reports
    }
    
    return render(request, 'cultural_assessment/dashboard.html', context)


@login_required
def organization_dashboard_view(request, organization_id):
    """Vista de dashboard cultural para una organización específica"""
    # Obtener la organización
    organization = get_object_or_404(Organization, id=organization_id)
    
    # Verificar acceso a la organización
    if not has_organization_access(request.user, organization):
        return HttpResponseForbidden("No tiene permisos para acceder a esta organización")
    
    # Obtener cultura organizacional actual
    org_culture = get_object_or_404(
        OrganizationalCulture,
        organization=organization,
        is_current=True
    )
    
    # Obtener evaluaciones
    assessments = CulturalAssessment.objects.filter(
        organization=organization,
        organizational_culture=org_culture
    ).select_related('person', 'department', 'team')
    
    # Calcular estadísticas
    total = assessments.count()
    completed = assessments.filter(status='completed').count()
    pending = assessments.filter(status__in=['invited', 'pending', 'in_progress']).count()
    expired = assessments.filter(status='expired').count()
    
    completion_rate = (completed / total * 100) if total > 0 else 0
    
    # Obtener reportes
    reports = CulturalReport.objects.filter(
        organization=organization,
        organizational_culture=org_culture
    ).order_by('-created_at')
    
    # Obtener estadísticas por departamento
    dept_stats = assessments.values('department__name').annotate(
        total=Count('id'),
        completed=Count('id', filter=Q(status='completed')),
        completion_rate=Count('id', filter=Q(status='completed')) * 100.0 / Count('id')
    ).order_by('-completion_rate')
    
    context = {
        'organization': organization,
        'org_culture': org_culture,
        'stats': {
            'total': total,
            'completed': completed,
            'pending': pending,
            'expired': expired,
            'completion_rate': completion_rate
        },
        'reports': reports,
        'department_stats': dept_stats,
        'assessments': assessments
    }
    
    return render(request, 'cultural_assessment/organization_dashboard.html', context)
