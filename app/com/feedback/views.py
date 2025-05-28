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

from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse, Http404
from django.views.decorators.http import require_POST, require_GET
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.urls import reverse
from django.db.models import Q, Count, Avg, F, Value, Sum, Case, When, IntegerField
from django.views.generic import TemplateView, ListView, DetailView

from app.models import Proposal, Opportunity, ServiceContract, Company, Contact
from app.com.feedback.feedback_models import (
    ServiceFeedback, OngoingServiceFeedback, CompletedServiceFeedback, 
    ServiceImprovementSuggestion
)
from app.com.feedback import get_feedback_tracker, FEEDBACK_STAGES, SERVICE_TYPES

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
    from app.com.pricing.feedback_views import proposal_feedback as pricing_proposal_feedback
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
