# /home/pablo/app/com/feedback/views.py
"""
Vistas para el sistema integrado de retroalimentación de Grupo huntRED®.

Proporciona un panel unificado para gestionar y analizar la retroalimentación 
en todas las etapas del ciclo de vida del servicio: propuestas, durante la 
prestación del servicio, y evaluación final.
"""

import logging
import json
import asyncio
from datetime import datetime, timedelta, date
import secrets
import uuid
import csv # Added for interview_feedback_export

from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse, Http404
from django.views.decorators.http import require_POST, require_GET, require_http_methods
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.urls import reverse
from django.db.models import Q, Count, Avg, F, Value, Sum, Case, When, IntegerField
from django.views.generic import TemplateView, ListView, DetailView

from app.models import Proposal, Opportunity, Contract, Company, Contact
from app.ats.feedback.feedback_models import (
    ServiceFeedback, OngoingServiceFeedback, CompletedServiceFeedback, 
    ServiceImprovementSuggestion
)
from app.ats.feedback import get_feedback_tracker, FEEDBACK_STAGES, SERVICE_TYPES

from app.models import Interview, InterviewFeedback, CompetencyEvaluation, CandidateFeedback, RecruitmentProcess, ProcessFeedback # Added for new feedback types
from app.ats.pricing.models.feedback import MeetingRequest, ProposalFeedback # Use existing models

logger = logging.getLogger(__name__)

# Función auxiliar para ejecutar corrutinas asíncronas
def run_async(coroutine):
    """Ejecuta una corrutina asíncrona desde un contexto síncrono."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        # Si no hay un event loop en el contexto actual, crear uno nuevo
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(coroutine)

# VISTAS PÚBLICAS PARA CLIENTES (FORMULARIOS DE RETROALIMENTACIÓN)

def proposal_feedback(request, token):
    """
    Vista para mostrar y procesar el formulario de retroalimentación de propuestas.
    
    Esta vista se accede desde un link enviado por email, con un token único
    que identifica la propuesta específica.
    """
    # Redirigir al módulo de pricing que maneja el feedback de propuestas
    from app.ats.pricing.feedback_views import proposal_feedback as pricing_proposal_feedback
    return pricing_proposal_feedback(request, token)

def ongoing_feedback(request, token):
    """
    Vista para mostrar y procesar el formulario de retroalimentación de servicios en curso.
    
    Esta vista se accede desde un link enviado por email durante la prestación del servicio,
    con un token único que identifica la oportunidad y el hito específico.
    """
    # Inicializar el tracker
    tracker = get_feedback_tracker('ongoing')
    token_key = f"{tracker.redis_prefix}token:{token}"
    token_data_json = tracker.redis.get(token_key)
    
    if not token_data_json:
        # Token inválido o expirado
        return render(request, 'feedback/feedback_error.html', {
            'error': 'El enlace ha expirado o no es válido. Por favor solicite un nuevo enlace.'
        })
    
    try:
        token_data = json.loads(token_data_json)
        opportunity_id = token_data.get("opportunity_id")
        milestone = token_data.get("milestone", 1)
    except:
        return render(request, 'feedback/feedback_error.html', {
            'error': 'Error al procesar el token. Por favor solicite un nuevo enlace.'
        })
    
    # Si es POST, procesar el formulario
    if request.method == 'POST':
        # Recopilar datos del formulario
        feedback_data = {
            'rating': int(request.POST.get('rating', 0)) or None,
            'progress_satisfaction': int(request.POST.get('progress_satisfaction', 0)) or None,
            'communication_rating': int(request.POST.get('communication_rating', 0)) or None,
            'consultant_rating': int(request.POST.get('consultant_rating', 0)) or None,
            'urgent_issues': request.POST.get('urgent_issues', ''),
            'improvement_suggestions': request.POST.get('improvement_suggestions', ''),
            'new_services': request.POST.get('new_services', ''),
            'comments': request.POST.get('comments', ''),
            'meeting_requested': 'meeting_requested' in request.POST,
            'progress_percentage': int(token_data.get('progress_percentage', 50))
        }
        
        # Procesar feedback de forma asíncrona
        feedback = run_async(tracker.process_feedback(token, feedback_data))
        
        # Redirigir a página de agradecimiento
        calendar_url = getattr(settings, "MANAGING_DIRECTOR_CALENDAR_URL", 
                             "https://huntred.com/agenda-pllh/")
        
        return render(request, 'feedback/ongoing_feedback_thanks.html', {
            'meeting_requested': feedback and feedback.meeting_requested,
            'calendar_url': calendar_url,
            'urgent_issue_reported': feedback_data.get('urgent_issues') and len(feedback_data.get('urgent_issues', '').strip()) > 10
        })
    
    # GET: mostrar formulario
    # Obtener datos de la oportunidad si es posible
    company_name = "su empresa"
    service_name = "nuestro servicio"
    progress = token_data.get('progress_percentage', 50)
    
    try:
        opportunity = Opportunity.objects.get(id=opportunity_id)
        company_name = opportunity.company.name
        service_name = dict(SERVICE_TYPES).get(opportunity.service_type, "nuestro servicio")
    except:
        pass
    
    # Preparar el contexto
    calendar_url = getattr(settings, "MANAGING_DIRECTOR_CALENDAR_URL", 
                         "https://huntred.com/agenda-pllh/")
    
    return render(request, 'feedback/ongoing_feedback.html', {
        'token': token,
        'questions': tracker.ongoing_questions,
        'company_name': company_name,
        'service_name': service_name,
        'progress': progress,
        'milestone': milestone,
        'calendar_url': calendar_url
    })

def completion_feedback(request, token):
    """
    Vista para mostrar y procesar el formulario de evaluación final de servicios.
    
    Esta vista se accede desde un link enviado por email al concluir el servicio,
    con un token único que identifica la oportunidad específica.
    """
    # Inicializar el tracker
    tracker = get_feedback_tracker('completed')
    token_key = f"{tracker.redis_prefix}token:{token}"
    opportunity_id = tracker.redis.get(token_key)
    
    if not opportunity_id:
        # Token inválido o expirado
        return render(request, 'feedback/feedback_error.html', {
            'error': 'El enlace ha expirado o no es válido. Por favor solicite un nuevo enlace.'
        })
    
    # Si es POST, procesar el formulario
    if request.method == 'POST':
        # Recopilar datos del formulario
        feedback_data = {
            'objectives_met': int(request.POST.get('objectives_met', 0)) or None,
            'value_perception': request.POST.get('value_perception', ''),
            'recommendation_likelihood': int(request.POST.get('recommendation_likelihood', 0)) or None,
            'consultant_evaluation': int(request.POST.get('consultant_evaluation', 0)) or None,
            'best_aspects': request.POST.get('best_aspects', ''),
            'areas_for_improvement': request.POST.get('areas_for_improvement', ''),
            'interested_in_other_services': request.POST.get('interested_in_other_services', 'No'),
            'services_of_interest': request.POST.getlist('services_of_interest', []),
            'new_services_suggestion': request.POST.get('new_services_suggestion', ''),
            'testimonial': request.POST.get('testimonial', ''),
            'allow_public_testimonial': request.POST.get('allow_public_testimonial', 'No'),
            'meeting_requested': 'meeting_requested' in request.POST
        }
        
        # Procesar feedback de forma asíncrona
        feedback = run_async(tracker.process_feedback(token, feedback_data))
        
        # Redirigir a página de agradecimiento
        testimonial_provided = feedback_data.get('testimonial') and len(feedback_data.get('testimonial', '').strip()) > 10
        return render(request, 'feedback/completion_feedback_thanks.html', {
            'meeting_requested': feedback and feedback.meeting_requested,
            'testimonial_provided': testimonial_provided,
            'interested_in_other_services': feedback_data.get('interested_in_other_services') == 'Sí',
            'calendar_url': getattr(settings, "MANAGING_DIRECTOR_CALENDAR_URL", "https://huntred.com/agenda-pllh/")
        })
    
    # GET: mostrar formulario
    # Obtener datos de la oportunidad si es posible
    company_name = "su empresa"
    service_name = "nuestro servicio"
    
    try:
        opportunity = Opportunity.objects.get(id=int(opportunity_id))
        company_name = opportunity.company.name
        service_name = dict(SERVICE_TYPES).get(opportunity.service_type, "nuestro servicio")
    except:
        pass
    
    return render(request, 'feedback/completion_feedback.html', {
        'token': token,
        'questions': tracker.completion_questions,
        'company_name': company_name,
        'service_name': service_name,
        'calendar_url': getattr(settings, "MANAGING_DIRECTOR_CALENDAR_URL", "https://huntred.com/agenda-pllh/")
    })

@login_required
def skill_feedback(request, token):
    """
    Vista para mostrar y procesar el formulario de feedback de skills.
    
    Esta vista se accede desde un link enviado por email al completar el análisis
    de skills de un candidato, con un token único que identifica la oportunidad.
    """
    # Inicializar el tracker
    tracker = get_feedback_tracker('skills')
    token_key = f"{tracker.redis_prefix}token:{token}"
    opportunity_id = tracker.redis.get(token_key)
    
    if not opportunity_id:
        # Token inválido o expirado
        return render(request, 'feedback/feedback_error.html', {
            'error': 'El enlace ha expirado o no es válido. Por favor solicite un nuevo enlace.'
        })
    
    # Si es POST, procesar el formulario
    if request.method == 'POST':
        # Recopilar datos del formulario
        feedback_data = {
            'skill_validation': {
                'skill_accuracy': request.POST.get('skill_accuracy'),
                'missing_skills': request.POST.getlist('missing_skills'),
                'extra_skills': request.POST.getlist('extra_skills')
            },
            'candidate_assessment': {
                'was_hired': request.POST.get('was_hired') == 'on',
                'technical_fit': int(request.POST.get('technical_fit', 0)) or None,
                'cultural_fit': int(request.POST.get('cultural_fit', 0)) or None,
                'strengths': request.POST.get('strengths'),
                'areas_for_improvement': request.POST.get('areas_for_improvement')
            },
            'potential_analysis': {
                'potential_roles': request.POST.getlist('potential_roles'),
                'growth_potential': int(request.POST.get('growth_potential', 0)) or None,
                'development_path': request.POST.get('development_path')
            },
            'market_context': {
                'market_demand': int(request.POST.get('market_demand', 0)) or None,
                'salary_range': request.POST.get('salary_range'),
                'market_notes': request.POST.get('market_notes')
            }
        }
        
        # Procesar feedback de forma asíncrona
        feedback = run_async(tracker.process_feedback(token, feedback_data))
        
        # Redirigir a página de agradecimiento
        return render(request, 'feedback/skill_feedback_thanks.html', {
            'feedback': feedback
        })
    
    # GET: mostrar formulario
    # Obtener datos de la oportunidad si es posible
    company_name = "su empresa"
    service_name = "análisis de skills"
    
    return render(request, 'feedback/skill_feedback_form.html', {
        'company_name': company_name,
        'service_name': service_name,
        'token': token
    })

# VISTAS PARA EL PANEL DE ADMINISTRACIÓN

@login_required
def feedback_dashboard(request):
    """
    Dashboard principal del sistema integrado de retroalimentación.
    
    Muestra métricas y tendencias consolidadas de todas las etapas de feedback,
    permitiendo filtrar por fecha, tipo de servicio y etapa.
    """
    # Obtener parámetros de filtrado
    end_date = timezone.now().date()
    start_date_str = request.GET.get('start_date', '')
    stage = request.GET.get('stage', '')
    service_type = request.GET.get('service_type', '')
    
    # Procesar fecha de inicio
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        except:
            start_date = end_date - timedelta(days=90)
    else:
        start_date = end_date - timedelta(days=90)
    
    # Obtener datos para cada etapa
    stages_data = {}
    overall_rating = 0
    total_feedbacks = 0
    
    for stage_key, stage_info in FEEDBACK_STAGES.items():
        # Si se ha filtrado por etapa y no es esta, saltar
        if stage and stage != stage_key:
            continue
        
        # Obtener datos de la etapa
        try:
            tracker = get_feedback_tracker(stage_key)
            stage_insights = run_async(tracker.generate_insights_report(
                start_date=timezone.make_aware(datetime.combine(start_date, datetime.min.time())),
                end_date=timezone.make_aware(datetime.combine(end_date, datetime.max.time())),
                service_type=service_type
            ))
            
            # Si no hay datos, pasar a la siguiente etapa
            if 'error' in stage_insights:
                continue
                
            stages_data[stage_key] = {
                'name': stage_info['name'],
                'description': stage_info['description'],
                'insights': stage_insights,
                'feedbacks_count': stage_insights.get('total_feedbacks', 0)
            }
            
            # Acumular totales
            total_feedbacks += stage_insights.get('total_feedbacks', 0)
            
            # Acumular calificaciones (distintas estructuras según la etapa)
            if stage_key == 'proposal':
                interest_rate = stage_insights.get('interest_rate', 0)
                overall_rating += interest_rate * stage_insights.get('total_feedbacks', 0)
            elif stage_key == 'ongoing':
                avg_general = stage_insights.get('average_ratings', {}).get('general', 0)
                if avg_general:
                    # Convertir a porcentaje (5->100%)
                    avg_percent = (avg_general / 5) * 100
                    overall_rating += avg_percent * stage_insights.get('total_feedbacks', 0)
            elif stage_key == 'completed':
                objectives_met = stage_insights.get('average_ratings', {}).get('objectives_met', 0)
                if objectives_met:
                    # Convertir a porcentaje (5->100%)
                    obj_percent = (objectives_met / 5) * 100
                    overall_rating += obj_percent * stage_insights.get('total_feedbacks', 0)
                    
        except Exception as e:
            logger.error(f"Error al obtener insights para etapa {stage_key}: {str(e)}")
            stages_data[stage_key] = {
                'name': stage_info['name'],
                'description': stage_info['description'],
                'error': str(e),
                'feedbacks_count': 0
            }
    
    # Calcular calificación general ponderada
    if total_feedbacks > 0:
        overall_rating = round(overall_rating / total_feedbacks, 1)
    else:
        overall_rating = 0
    
    # Obtener tendencias comparando con período anterior
    previous_start = start_date - (end_date - start_date)
    previous_end = start_date - timedelta(days=1)
    
    previous_total = ServiceFeedback.objects.filter(
        created_at__gte=timezone.make_aware(datetime.combine(previous_start, datetime.min.time())),
        created_at__lte=timezone.make_aware(datetime.combine(previous_end, datetime.max.time()))
    ).count()
    
    trend_percentage = 0
    if previous_total > 0:
        trend_percentage = ((total_feedbacks - previous_total) / previous_total) * 100
    
    # Obtener sugerencias de mejora recientes
    recent_suggestions = ServiceImprovementSuggestion.objects.filter(
        status='new',
        created_at__gte=timezone.now() - timedelta(days=30)
    ).order_by('-created_at')[:5]
    
    # Preparar datos para gráficos
    # (En implementación real se procesarían datos para charts.js o similar)
    
    return render(request, 'feedback/dashboard.html', {
        'stages_data': stages_data,
        'start_date': start_date,
        'end_date': end_date,
        'stage_filter': stage,
        'service_type_filter': service_type,
        'total_feedbacks': total_feedbacks,
        'overall_rating': overall_rating,
        'trend_percentage': trend_percentage,
        'recent_suggestions': recent_suggestions,
        'stage_options': FEEDBACK_STAGES,
        'service_options': SERVICE_TYPES,
        # Datos para gráficos
        'has_chart_data': total_feedbacks > 0
    })

@login_required
class FeedbackListView(ListView):
    """
    Lista todas las retroalimentaciones con filtros por etapa y tipo de servicio.
    """
    model = ServiceFeedback
    template_name = 'feedback/feedback_list.html'
    context_object_name = 'feedbacks'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = ServiceFeedback.objects.all().order_by('-created_at')
        
        # Aplicar filtros
        stage = self.request.GET.get('stage', '')
        if stage:
            queryset = queryset.filter(stage=stage)
            
        service_type = self.request.GET.get('service_type', '')
        if service_type:
            queryset = queryset.filter(service_type=service_type)
            
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(company_name__icontains=search) |
                Q(contact_name__icontains=search) |
                Q(contact_email__icontains=search)
            )
            
        date_from = self.request.GET.get('date_from', '')
        if date_from:
            try:
                date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
                queryset = queryset.filter(created_at__gte=timezone.make_aware(
                    datetime.combine(date_from, datetime.min.time())
                ))
            except:
                pass
                
        date_to = self.request.GET.get('date_to', '')
        if date_to:
            try:
                date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
                queryset = queryset.filter(created_at__lte=timezone.make_aware(
                    datetime.combine(date_to, datetime.max.time())
                ))
            except:
                pass
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Añadir filtros actuales al contexto
        context['stage_filter'] = self.request.GET.get('stage', '')
        context['service_type_filter'] = self.request.GET.get('service_type', '')
        context['search'] = self.request.GET.get('search', '')
        context['date_from'] = self.request.GET.get('date_from', '')
        context['date_to'] = self.request.GET.get('date_to', '')
        
        # Opciones para los filtros
        context['stage_options'] = FEEDBACK_STAGES
        context['service_options'] = SERVICE_TYPES
        
        return context

@login_required
class FeedbackDetailView(DetailView):
    """
    Muestra los detalles de una retroalimentación específica.
    """
    model = ServiceFeedback
    template_name = 'feedback/feedback_detail.html'
    context_object_name = 'feedback'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        feedback = self.get_object()
        
        # Añadir datos específicos según la etapa
        if feedback.stage == 'ongoing':
            try:
                context['ongoing_data'] = feedback.ongoing_feedback
            except:
                pass
                
        elif feedback.stage == 'completed':
            try:
                context['completed_data'] = feedback.completed_feedback
            except:
                pass
        
        # Añadir información relacionada
        context['improvement_suggestions'] = feedback.improvement_suggestions.all()
        
        # Obtener otras retroalimentaciones del mismo cliente
        context['related_feedbacks'] = ServiceFeedback.objects.filter(
            company=feedback.company
        ).exclude(id=feedback.id).order_by('-created_at')[:5]
        
        return context

@login_required
def suggestions_list(request):
    """
    Lista todas las sugerencias de mejora con filtros y opciones de gestión.
    """
    # Filtrar sugerencias
    status = request.GET.get('status', '')
    suggestions_query = ServiceImprovementSuggestion.objects.all()
    
    if status:
        suggestions_query = suggestions_query.filter(status=status)
    
    # Ordenar
    order_by = request.GET.get('order_by', '-created_at')
    suggestions = suggestions_query.order_by(order_by)
    
    return render(request, 'feedback/suggestions_list.html', {
        'suggestions': suggestions,
        'status_filter': status,
        'order_by': order_by,
        'status_options': [
            ('new', 'Nuevas'),
            ('under_review', 'En revisión'),
            ('planned', 'Planificadas'),
            ('implemented', 'Implementadas'),
            ('declined', 'Descartadas'),
        ]
    })

@login_required
@require_POST
def update_suggestion_status(request, suggestion_id):
    """
    Actualiza el estado de una sugerencia de mejora.
    """
    suggestion = get_object_or_404(ServiceImprovementSuggestion, id=suggestion_id)
    new_status = request.POST.get('status', '')
    notes = request.POST.get('notes', '')
    
    if new_status in ['new', 'under_review', 'planned', 'implemented', 'declined']:
        suggestion.status = new_status
        if notes:
            suggestion.internal_notes = notes
        suggestion.save()
        messages.success(request, f"Sugerencia actualizada correctamente a estado: {new_status}")
    else:
        messages.error(request, "Estado inválido")
    
    return redirect('feedback:suggestions_list')

@login_required
def testimonials_list(request):
    """
    Lista todos los testimoniales recibidos con opciones para usarlos en marketing.
    """
    # Filtrar por permiso de uso
    public_only = request.GET.get('public_only', '') == 'yes'
    
    testimonials_query = CompletedServiceFeedback.objects.filter(
        testimonial_provided=True
    ).select_related('base_feedback')
    
    if public_only:
        testimonials_query = testimonials_query.filter(allow_public_testimonial=True)
    
    # Ordenar por calificación (NPS) para destacar los mejores primero
    testimonials = testimonials_query.order_by('-recommendation_likelihood', '-base_feedback__created_at')
    
    return render(request, 'feedback/testimonials_list.html', {
        'testimonials': testimonials,
        'public_only': public_only
    })

@login_required
def export_insights(request):
    """
    Exporta un informe detallado de insights para un período específico.
    """
    # Obtener parámetros
    end_date = timezone.now().date()
    start_date_str = request.GET.get('start_date', '')
    export_format = request.GET.get('format', 'json')
    
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        except:
            start_date = end_date - timedelta(days=90)
    else:
        start_date = end_date - timedelta(days=90)
    
    # Recopilar datos de todas las etapas
    all_data = {
        'period': {
            'start': start_date.strftime('%Y-%m-%d'),
            'end': end_date.strftime('%Y-%m-%d')
        },
        'stages': {}
    }
    
    for stage_key, stage_info in FEEDBACK_STAGES.items():
        try:
            tracker = get_feedback_tracker(stage_key)
            stage_insights = run_async(tracker.generate_insights_report(
                start_date=timezone.make_aware(datetime.combine(start_date, datetime.min.time())),
                end_date=timezone.make_aware(datetime.combine(end_date, datetime.max.time()))
            ))
            
            all_data['stages'][stage_key] = {
                'name': stage_info['name'],
                'insights': stage_insights
            }
        except Exception as e:
            logger.error(f"Error al exportar insights para etapa {stage_key}: {str(e)}")
            all_data['stages'][stage_key] = {
                'name': stage_info['name'],
                'error': str(e)
            }
    
    # Exportar según formato solicitado
    if export_format == 'json':
        return JsonResponse(all_data)
    else:
        # Para otros formatos como CSV o Excel, se procesaría aquí
        return HttpResponse("Formato no soportado", content_type="text/plain", status=400)

# Redirecciones para compatibilidad
def redirect_to_feedback_dashboard(request):
    """Redirección para mantener compatibilidad con URLs antiguas."""
    return redirect('feedback:dashboard')

# URLs para integraciones externas
@require_POST
def webhook_feedback(request):
    """
    Webhook para recibir retroalimentación desde fuentes externas.
    """
    # Verificar token de seguridad
    token = request.headers.get('X-Api-Token')
    if not token or token != settings.FEEDBACK_API_TOKEN:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    try:
        data = json.loads(request.body)
        
        # Validar datos mínimos
        required_fields = ['token', 'stage']
        for field in required_fields:
            if field not in data:
                return JsonResponse({'error': f'Missing required field: {field}'}, status=400)
        
        # Obtener el tracker adecuado según la etapa
        stage = data.get('stage')
        if stage not in FEEDBACK_STAGES:
            return JsonResponse({'error': f'Invalid stage: {stage}'}, status=400)
        
        tracker = get_feedback_tracker(stage)
        feedback = run_async(tracker.process_feedback(data['token'], data))
        
        if not feedback:
            return JsonResponse({'error': 'Invalid token or opportunity/proposal not found'}, status=400)
        
        return JsonResponse({'success': True, 'feedback_id': feedback.id})
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Error en webhook de retroalimentación: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)

# ============================================================================
# FEEDBACK DE PROPUESTAS Y REUNIONES (RESTAURADAS)
# ============================================================================

def schedule_meeting(request, proposal_id):
    """Programa una reunión para discutir una propuesta."""
    if request.method == 'POST':
        from app.ats.pricing.models import PricingProposal
        proposal = get_object_or_404(PricingProposal, id=proposal_id)
        
        # Crear solicitud de reunión usando el modelo existente
        meeting_request = MeetingRequest.objects.create(
            propuesta=proposal,
            estado='PENDIENTE',
            fecha_solicitud=timezone.now(),
            fecha_reunion=request.POST.get('meeting_date'),
            duracion_minutos=request.POST.get('duration', 30),
            tipo_reunion=request.POST.get('meeting_type', 'consultation'),
            participantes={'requested_by': request.user.id},
            notas=request.POST.get('notes', ''),
            meeting_type=request.POST.get('meeting_type', 'consultation'),
            preferred_date=request.POST.get('meeting_date'),
            preferred_time_range=request.POST.get('time_range', 'morning'),
            contact_phone=request.POST.get('contact_phone', '')
        )
        
        messages.success(request, 'Solicitud de reunión enviada exitosamente.')
        return redirect('pricing:proposal_feedback', token=proposal.feedback_token)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)

def meeting_requests_list(request):
    """Lista todas las solicitudes de reunión."""
    if request.user.is_staff:
        meeting_requests = MeetingRequest.objects.all().order_by('-created_at')
    else:
        meeting_requests = MeetingRequest.objects.filter(
            requested_by=request.user
        ).order_by('-created_at')
    
    return render(request, 'ats/feedback/meeting_requests_list.html', {
        'meeting_requests': meeting_requests
    })

def mark_meeting_completed(request, meeting_id):
    """Marca una reunión como completada."""
    if request.method == 'POST':
        meeting = get_object_or_404(MeetingRequest, id=meeting_id)
        meeting.estado = 'COMPLETADA'
        meeting.fecha_reunion = timezone.now()
        meeting.save()
        
        # Crear feedback de la reunión usando ProposalFeedback
        meeting_feedback = ProposalFeedback.objects.create(
            propuesta=meeting.propuesta,
            estado='APROBADO',
            comentarios=request.POST.get('comments', ''),
            calificacion=request.POST.get('rating'),
            metadata={
                'meeting_id': meeting.id,
                'follow_up_required': request.POST.get('follow_up_required') == 'on',
                'meeting_feedback': True
            }
        )
        
        messages.success(request, 'Reunión marcada como completada.')
        return redirect('pricing:meeting_requests_list')
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)

# ============================================================================
# SISTEMA COMPLETO DE FEEDBACK DE ENTREVISTAS
# ============================================================================

def interview_feedback_dashboard(request):
    """Dashboard principal de feedback de entrevistas."""
    if not request.user.is_authenticated:
        return redirect('login')
    
    # Estadísticas generales
    total_interviews = Interview.objects.count()
    interviews_with_feedback = Interview.objects.filter(feedback__isnull=False).count()
    avg_rating = InterviewFeedback.objects.aggregate(
        avg_rating=Avg('overall_rating')
    )['avg_rating'] or 0
    
    # Feedback por tipo de entrevista
    feedback_by_type = InterviewFeedback.objects.values('interview__interview_type').annotate(
        count=Count('id'),
        avg_rating=Avg('overall_rating')
    )
    
    # Feedback reciente
    recent_feedback = InterviewFeedback.objects.select_related(
        'interview', 'interview__candidate', 'interview__job'
    ).order_by('-created_at')[:10]
    
    context = {
        'total_interviews': total_interviews,
        'interviews_with_feedback': interviews_with_feedback,
        'avg_rating': round(avg_rating, 2),
        'feedback_by_type': feedback_by_type,
        'recent_feedback': recent_feedback,
    }
    
    return render(request, 'ats/feedback/interview_feedback_dashboard.html', context)

def interview_feedback_form(request, interview_id):
    """Formulario para crear/editar feedback de entrevista."""
    interview = get_object_or_404(Interview, id=interview_id)
    
    if request.method == 'POST':
        # Crear o actualizar feedback
        feedback, created = InterviewFeedback.objects.get_or_create(
            interview=interview,
            defaults={
                'interviewer': request.user,
                'overall_rating': request.POST.get('overall_rating'),
                'technical_skills_rating': request.POST.get('technical_skills_rating'),
                'communication_rating': request.POST.get('communication_rating'),
                'cultural_fit_rating': request.POST.get('cultural_fit_rating'),
                'problem_solving_rating': request.POST.get('problem_solving_rating'),
                'strengths': request.POST.get('strengths', ''),
                'weaknesses': request.POST.get('weaknesses', ''),
                'recommendations': request.POST.get('recommendations', ''),
                'hiring_decision': request.POST.get('hiring_decision'),
                'next_steps': request.POST.get('next_steps', ''),
                'additional_notes': request.POST.get('additional_notes', ''),
            }
        )
        
        if not created:
            # Actualizar feedback existente
            feedback.overall_rating = request.POST.get('overall_rating')
            feedback.technical_skills_rating = request.POST.get('technical_skills_rating')
            feedback.communication_rating = request.POST.get('communication_rating')
            feedback.cultural_fit_rating = request.POST.get('cultural_fit_rating')
            feedback.problem_solving_rating = request.POST.get('problem_solving_rating')
            feedback.strengths = request.POST.get('strengths', '')
            feedback.weaknesses = request.POST.get('weaknesses', '')
            feedback.recommendations = request.POST.get('recommendations', '')
            feedback.hiring_decision = request.POST.get('hiring_decision')
            feedback.next_steps = request.POST.get('next_steps', '')
            feedback.additional_notes = request.POST.get('additional_notes', '')
            feedback.save()
        
        # Crear evaluación de competencias específicas
        competencies = request.POST.getlist('competency_name')
        ratings = request.POST.getlist('competency_rating')
        comments = request.POST.getlist('competency_comment')
        
        # Eliminar evaluaciones anteriores
        feedback.competency_evaluations.all().delete()
        
        # Crear nuevas evaluaciones
        for i, competency in enumerate(competencies):
            if competency and ratings[i]:
                CompetencyEvaluation.objects.create(
                    feedback=feedback,
                    competency_name=competency,
                    rating=int(ratings[i]),
                    comments=comments[i] if i < len(comments) else ''
                )
        
        messages.success(request, 'Feedback de entrevista guardado exitosamente.')
        return redirect('feedback:interview_feedback_detail', feedback_id=feedback.id)
    
    # Obtener feedback existente si existe
    try:
        existing_feedback = InterviewFeedback.objects.get(interview=interview)
    except InterviewFeedback.DoesNotExist:
        existing_feedback = None
    
    context = {
        'interview': interview,
        'feedback': existing_feedback,
        'rating_choices': [(i, str(i)) for i in range(1, 6)],
        'hiring_decisions': InterviewFeedback.HIRING_DECISIONS,
    }
    
    return render(request, 'ats/feedback/interview_feedback_form.html', context)

def interview_feedback_detail(request, feedback_id):
    """Vista detallada de un feedback de entrevista."""
    feedback = get_object_or_404(InterviewFeedback, id=feedback_id)
    
    # Verificar permisos
    if not (request.user.is_staff or 
            request.user == feedback.interviewer or 
            request.user == feedback.interview.interviewer):
        messages.error(request, 'No tienes permisos para ver este feedback.')
        return redirect('feedback:interview_feedback_dashboard')
    
    context = {
        'feedback': feedback,
        'competency_evaluations': feedback.competency_evaluations.all(),
    }
    
    return render(request, 'ats/feedback/interview_feedback_detail.html', context)

def interview_feedback_list(request):
    """Lista todos los feedbacks de entrevistas."""
    if request.user.is_staff:
        feedbacks = InterviewFeedback.objects.select_related(
            'interview', 'interview__candidate', 'interview__job', 'interviewer'
        ).order_by('-created_at')
    else:
        feedbacks = InterviewFeedback.objects.filter(
            interviewer=request.user
        ).select_related(
            'interview', 'interview__candidate', 'interview__job'
        ).order_by('-created_at')
    
    # Filtros
    interview_type = request.GET.get('interview_type')
    if interview_type:
        feedbacks = feedbacks.filter(interview__interview_type=interview_type)
    
    hiring_decision = request.GET.get('hiring_decision')
    if hiring_decision:
        feedbacks = feedbacks.filter(hiring_decision=hiring_decision)
    
    min_rating = request.GET.get('min_rating')
    if min_rating:
        feedbacks = feedbacks.filter(overall_rating__gte=min_rating)
    
    context = {
        'feedbacks': feedbacks,
        'interview_types': Interview.INTERVIEW_TYPES,
        'hiring_decisions': InterviewFeedback.HIRING_DECISIONS,
    }
    
    return render(request, 'ats/feedback/interview_feedback_list.html', context)

def interview_feedback_analytics(request):
    """Análisis y reportes de feedback de entrevistas."""
    if not request.user.is_staff:
        messages.error(request, 'Acceso restringido.')
        return redirect('feedback:interview_feedback_dashboard')
    
    # Estadísticas por período
    period = request.GET.get('period', '30')  # días
    end_date = timezone.now()
    start_date = end_date - timedelta(days=int(period))
    
    feedbacks_in_period = InterviewFeedback.objects.filter(
        created_at__range=[start_date, end_date]
    )
    
    # Análisis de ratings
    rating_distribution = feedbacks_in_period.values('overall_rating').annotate(
        count=Count('id')
    ).order_by('overall_rating')
    
    # Análisis por competencia
    competency_analysis = CompetencyEvaluation.objects.filter(
        feedback__in=feedbacks_in_period
    ).values('competency_name').annotate(
        avg_rating=Avg('rating'),
        count=Count('id')
    ).order_by('-avg_rating')
    
    # Análisis de decisiones de contratación
    hiring_analysis = feedbacks_in_period.values('hiring_decision').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Tendencias temporales
    daily_feedback = feedbacks_in_period.extra(
        select={'day': 'date(created_at)'}
    ).values('day').annotate(
        count=Count('id'),
        avg_rating=Avg('overall_rating')
    ).order_by('day')
    
    context = {
        'period': period,
        'rating_distribution': rating_distribution,
        'competency_analysis': competency_analysis,
        'hiring_analysis': hiring_analysis,
        'daily_feedback': daily_feedback,
        'total_feedbacks': feedbacks_in_period.count(),
        'avg_rating': feedbacks_in_period.aggregate(
            avg=Avg('overall_rating')
        )['avg'] or 0,
    }
    
    return render(request, 'ats/feedback/interview_feedback_analytics.html', context)

def interview_feedback_export(request):
    """Exporta feedbacks de entrevistas a CSV/Excel."""
    if not request.user.is_staff:
        messages.error(request, 'Acceso restringido.')
        return redirect('feedback:interview_feedback_dashboard')
    
    format_type = request.GET.get('format', 'csv')
    period = request.GET.get('period', 'all')
    
    # Filtrar por período
    if period != 'all':
        end_date = timezone.now()
        start_date = end_date - timedelta(days=int(period))
        feedbacks = InterviewFeedback.objects.filter(
            created_at__range=[start_date, end_date]
        )
    else:
        feedbacks = InterviewFeedback.objects.all()
    
    feedbacks = feedbacks.select_related(
        'interview', 'interview__candidate', 'interview__job', 'interviewer'
    ).prefetch_related('competency_evaluations')
    
    if format_type == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="interview_feedback_{period}.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Fecha', 'Candidato', 'Puesto', 'Entrevistador', 'Tipo Entrevista',
            'Rating General', 'Habilidades Técnicas', 'Comunicación', 
            'Fit Cultural', 'Resolución Problemas', 'Fortalezas', 'Debilidades',
            'Recomendaciones', 'Decisión', 'Próximos Pasos'
        ])
        
        for feedback in feedbacks:
            writer.writerow([
                feedback.created_at.strftime('%Y-%m-%d %H:%M'),
                feedback.interview.candidate.name,
                feedback.interview.job.title,
                feedback.interviewer.get_full_name(),
                feedback.interview.get_interview_type_display(),
                feedback.overall_rating,
                feedback.technical_skills_rating,
                feedback.communication_rating,
                feedback.cultural_fit_rating,
                feedback.problem_solving_rating,
                feedback.strengths,
                feedback.weaknesses,
                feedback.recommendations,
                feedback.get_hiring_decision_display(),
                feedback.next_steps,
            ])
        
        return response
    
    # Para Excel necesitarías openpyxl
    messages.error(request, 'Formato no soportado.')
    return redirect('feedback:interview_feedback_analytics')

# ============================================================================
# FEEDBACK DE CANDIDATOS (NUEVO)
# ============================================================================

def candidate_feedback_form(request, candidate_id):
    """Formulario para feedback general de candidatos."""
    candidate = get_object_or_404(Candidate, id=candidate_id)
    
    if request.method == 'POST':
        feedback = CandidateFeedback.objects.create(
            candidate=candidate,
            evaluator=request.user,
            evaluation_date=timezone.now(),
            overall_impression=request.POST.get('overall_impression'),
            technical_competence=request.POST.get('technical_competence'),
            communication_skills=request.POST.get('communication_skills'),
            teamwork_ability=request.POST.get('teamwork_ability'),
            problem_solving=request.POST.get('problem_solving'),
            learning_ability=request.POST.get('learning_ability'),
            cultural_fit=request.POST.get('cultural_fit'),
            strengths=request.POST.get('strengths', ''),
            areas_for_improvement=request.POST.get('areas_for_improvement', ''),
            recommendations=request.POST.get('recommendations', ''),
            would_recommend=request.POST.get('would_recommend') == 'on',
            notes=request.POST.get('notes', ''),
        )
        
        messages.success(request, 'Feedback del candidato guardado exitosamente.')
        return redirect('feedback:candidate_feedback_detail', feedback_id=feedback.id)
    
    context = {
        'candidate': candidate,
        'rating_choices': [(i, str(i)) for i in range(1, 6)],
    }
    
    return render(request, 'ats/feedback/candidate_feedback_form.html', context)

def candidate_feedback_detail(request, feedback_id):
    """Vista detallada de feedback de candidato."""
    feedback = get_object_or_404(CandidateFeedback, id=feedback_id)
    
    context = {
        'feedback': feedback,
    }
    
    return render(request, 'ats/feedback/candidate_feedback_detail.html', context)

# ============================================================================
# FEEDBACK DE PROCESOS DE RECLUTAMIENTO (NUEVO)
# ============================================================================

def recruitment_process_feedback(request, process_id):
    """Feedback sobre el proceso de reclutamiento completo."""
    process = get_object_or_404(RecruitmentProcess, id=process_id)
    
    if request.method == 'POST':
        feedback = ProcessFeedback.objects.create(
            process=process,
            evaluator=request.user,
            overall_satisfaction=request.POST.get('overall_satisfaction'),
            communication_quality=request.POST.get('communication_quality'),
            process_efficiency=request.POST.get('process_efficiency'),
            candidate_experience=request.POST.get('candidate_experience'),
            transparency=request.POST.get('transparency'),
            speed_of_process=request.POST.get('speed_of_process'),
            what_went_well=request.POST.get('what_went_well', ''),
            what_could_improve=request.POST.get('what_could_improve', ''),
            suggestions=request.POST.get('suggestions', ''),
            would_recommend=request.POST.get('would_recommend') == 'on',
            additional_comments=request.POST.get('additional_comments', ''),
        )
        
        messages.success(request, 'Feedback del proceso guardado exitosamente.')
        return redirect('feedback:process_feedback_detail', feedback_id=feedback.id)
    
    context = {
        'process': process,
        'rating_choices': [(i, str(i)) for i in range(1, 6)],
    }
    
    return render(request, 'ats/feedback/process_feedback_form.html', context)

def process_feedback_detail(request, feedback_id):
    """Vista detallada de feedback de proceso."""
    feedback = get_object_or_404(ProcessFeedback, id=feedback_id)
    
    context = {
        'feedback': feedback,
    }
    
    return render(request, 'ats/feedback/process_feedback_detail.html', context)

# ============================================================================
# API ENDPOINTS PARA FEEDBACK
# ============================================================================

@require_http_methods(["POST"])
def api_interview_feedback(request):
    """API endpoint para crear feedback de entrevista."""
    try:
        data = json.loads(request.body)
        interview_id = data.get('interview_id')
        interview = get_object_or_404(Interview, id=interview_id)
        
        feedback = InterviewFeedback.objects.create(
            interview=interview,
            interviewer=request.user,
            overall_rating=data.get('overall_rating'),
            technical_skills_rating=data.get('technical_skills_rating'),
            communication_rating=data.get('communication_rating'),
            cultural_fit_rating=data.get('cultural_fit_rating'),
            problem_solving_rating=data.get('problem_solving_rating'),
            strengths=data.get('strengths', ''),
            weaknesses=data.get('weaknesses', ''),
            recommendations=data.get('recommendations', ''),
            hiring_decision=data.get('hiring_decision'),
            next_steps=data.get('next_steps', ''),
            additional_notes=data.get('additional_notes', ''),
        )
        
        return JsonResponse({
            'success': True,
            'feedback_id': feedback.id,
            'message': 'Feedback creado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

@require_http_methods(["GET"])
def api_feedback_stats(request):
    """API endpoint para estadísticas de feedback."""
    period = request.GET.get('period', '30')
    end_date = timezone.now()
    start_date = end_date - timedelta(days=int(period))
    
    feedbacks = InterviewFeedback.objects.filter(
        created_at__range=[start_date, end_date]
    )
    
    stats = {
        'total_feedbacks': feedbacks.count(),
        'avg_rating': feedbacks.aggregate(avg=Avg('overall_rating'))['avg'] or 0,
        'rating_distribution': list(feedbacks.values('overall_rating').annotate(
            count=Count('id')
        ).order_by('overall_rating')),
        'hiring_decisions': list(feedbacks.values('hiring_decision').annotate(
            count=Count('id')
        ).order_by('-count')),
    }
    
    return JsonResponse(stats)
