# /home/pablo/app/com/pricing/feedback_views.py
"""
Vistas para gestionar el sistema de retroalimentación de propuestas de Grupo huntRED®.

Este módulo contiene las vistas necesarias para:
1. Mostrar y procesar el formulario de retroalimentación de propuestas
2. Gestionar las solicitudes de reunión con el Managing Director
3. Generar reportes y estadísticas sobre la retroalimentación recibida
"""

import logging
import json
import asyncio
from datetime import datetime, timedelta
import secrets
import uuid

from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse, Http404
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.html import strip_tags
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Count, Avg, F, Value, Sum, Case, When, IntegerField

from app.models import Proposal, TalentAnalysisRequest, Company, Contact, Opportunity
from app.com.pricing.feedback_models import ProposalFeedback, MeetingRequest
from app.com.pricing.feedback_forms import ProposalFeedbackForm, MeetingRequestForm
from app.com.pricing.proposal_tracker import ProposalTracker, get_proposal_tracker

logger = logging.getLogger(__name__)


def proposal_feedback(request, token):
    """
    Vista para mostrar y procesar el formulario de retroalimentación de propuestas.
    
    Esta vista se accede desde un link enviado por email, con un token único
    que identifica la propuesta específica.
    """
    # Inicializar el tracker
    tracker = get_proposal_tracker()
    token_key = f"{tracker.redis_prefix}token:{token}"
    proposal_id = tracker.redis.get(token_key)
    
    if not proposal_id:
        # Token inválido o expirado
        return render(request, 'pricing/feedback_error.html', {
            'error': 'El enlace ha expirado o no es válido. Por favor solicite un nuevo enlace.'
        })
    
    # Si es POST, procesar el formulario
    if request.method == 'POST':
        form = ProposalFeedbackForm(request.POST)
        
        if form.is_valid():
            # Obtener datos del formulario
            feedback_data = {
                'interest_level': form.cleaned_data.get('response_type'),
                'rejection_reason': form.cleaned_data.get('rejection_reason'),
                'price_perception': form.cleaned_data.get('price_perception'),
                'improvement': form.cleaned_data.get('improvement_suggestions'),
                'meeting_requested': form.cleaned_data.get('meeting_requested', False),
                'meeting_type': request.POST.get('meeting_type'),
                'meeting_notes': request.POST.get('meeting_notes'),
                'contact_phone': request.POST.get('contact_phone')
            }
            
            # Procesar feedback de forma asíncrona
            feedback = asyncio.run(tracker.process_feedback(token, feedback_data))
            
            # Redirigir a página de agradecimiento
            calendar_url = getattr(settings, "MANAGING_DIRECTOR_CALENDAR_URL", 
                                 "https://huntred.com/agenda-pllh/")
            
            return render(request, 'pricing/proposal_feedback.html', {
                'submitted': True,
                'meeting_requested': feedback and feedback.meeting_requested,
                'calendar_url': calendar_url
            })
    else:
        # GET: mostrar formulario
        form = ProposalFeedbackForm(initial={'token': token})
    
    # Preparar el contexto
    calendar_url = getattr(settings, "MANAGING_DIRECTOR_CALENDAR_URL", 
                         "https://huntred.com/agenda-pllh/")
    
    return render(request, 'pricing/proposal_feedback.html', {
        'form': form,
        'token': token,
        'calendar_url': calendar_url,
        'submitted': False
    })


@login_required
def schedule_meeting(request, feedback_id):
    """
    Vista para programar una reunión con el cliente a partir de una retroalimentación.
    
    Esta vista es solo para administradores/consultores y permite programar
    manualmente una reunión solicitada por un cliente.
    """
    feedback = get_object_or_404(ProposalFeedback, id=feedback_id)
    
    if request.method == 'POST':
        form = MeetingRequestForm(request.POST)
        
        if form.is_valid():
            meeting = form.save(commit=False)
            
            # Asignar datos del feedback
            meeting.proposal_feedback = feedback
            meeting.contact_name = feedback.contact_name
            meeting.contact_email = feedback.contact_email
            meeting.company_name = feedback.company_name
            
            # Si se programó la reunión
            if 'scheduled_for' in request.POST and request.POST['scheduled_for']:
                meeting.is_scheduled = True
                meeting.scheduled_for = request.POST['scheduled_for']
                meeting.meeting_link = request.POST.get('meeting_link', '')
                
                # Actualizar también el feedback
                feedback.meeting_scheduled_for = meeting.scheduled_for
                feedback.meeting_link = meeting.meeting_link
                feedback.save()
                
                # Enviar confirmación al cliente
                send_meeting_confirmation(meeting)
            
            meeting.save()
            messages.success(request, "Reunión programada correctamente")
            return redirect('pricing:feedback_detail', pk=feedback_id)
            
    else:
        # Preparar formulario con datos pre-poblados
        client_data = {
            'contact_phone': ''  # Buscar en modelos relacionados si está disponible
        }
        form = MeetingRequestForm(client_data=client_data)
    
    return render(request, 'pricing/schedule_meeting.html', {
        'form': form,
        'feedback': feedback
    })


def send_meeting_confirmation(meeting):
    """Envía un email de confirmación para una reunión programada."""
    try:
        context = {
            'meeting': meeting,
            'company_name': meeting.company_name,
            'contact_name': meeting.contact_name,
            'meeting_date': meeting.scheduled_for.strftime("%d/%m/%Y"),
            'meeting_time': meeting.scheduled_for.strftime("%H:%M"),
            'meeting_link': meeting.meeting_link or "#",
            'meeting_type': meeting.get_meeting_type_display()
        }
        
        subject = f"Confirmación de reunión con Pablo Lelo de Larrea H. - Grupo huntRED®"
        html_message = render_to_string("emails/meeting_confirmation.html", context)
        text_message = strip_tags(html_message)
        
        send_mail(
            subject=subject,
            message=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[meeting.contact_email],
            html_message=html_message,
            fail_silently=False
        )
        
        return True
    except Exception as e:
        logger.error(f"Error al enviar confirmación de reunión: {str(e)}")
        return False


@login_required
class FeedbackListView(LoginRequiredMixin, ListView):
    """Lista de retroalimentación de propuestas para administradores."""
    
    model = ProposalFeedback
    template_name = 'pricing/feedback_list.html'
    context_object_name = 'feedbacks'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset().order_by('-created_at')
        
        # Filtrar por búsqueda
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(company_name__icontains=search) |
                Q(contact_name__icontains=search) |
                Q(contact_email__icontains=search)
            )
        
        # Filtrar por tipo de respuesta
        response_type = self.request.GET.get('response_type', '')
        if response_type:
            queryset = queryset.filter(response_type=response_type)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['response_type'] = self.request.GET.get('response_type', '')
        context['response_choices'] = ProposalFeedback.RESPONSE_CHOICES
        
        # Estadísticas básicas
        context['total_feedback'] = ProposalFeedback.objects.count()
        context['interested_count'] = ProposalFeedback.objects.filter(
            response_type__in=['interested', 'considering']
        ).count()
        
        return context


@login_required
class FeedbackDetailView(LoginRequiredMixin, DetailView):
    """Detalle de una retroalimentación específica."""
    
    model = ProposalFeedback
    template_name = 'pricing/feedback_detail.html'
    context_object_name = 'feedback'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtener propuesta relacionada
        feedback = self.get_object()
        context['proposal'] = feedback.proposal
        context['opportunity'] = feedback.opportunity
        
        # Verificar si hay una solicitud de reunión
        try:
            context['meeting_request'] = feedback.meeting_request
        except:
            context['meeting_request'] = None
        
        return context


@login_required
def feedback_dashboard(request):
    """
    Dashboard con estadísticas sobre la retroalimentación de propuestas.
    
    Muestra gráficos y métricas sobre las respuestas recibidas, razones de rechazo,
    percepción de precios, etc.
    """
    # Período de análisis (por defecto el último mes)
    end_date = timezone.now().date()
    start_date = request.GET.get('start_date', '')
    if not start_date:
        start_date = end_date - timedelta(days=30)
    else:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        except:
            start_date = end_date - timedelta(days=30)
    
    # Obtener datos para el período
    feedbacks = ProposalFeedback.objects.filter(
        created_at__gte=start_date,
        created_at__lte=end_date + timedelta(days=1)  # Incluir el día final completo
    )
    
    # Calcular estadísticas
    total = feedbacks.count()
    
    if total > 0:
        # Distribución por tipo de respuesta
        response_distribution = (
            feedbacks.values('response_type')
            .annotate(count=Count('id'))
            .annotate(percentage=100 * F('count') / Value(total))
        )
        
        # Razones de rechazo
        rejection_reasons = (
            feedbacks.exclude(rejection_reason__isnull=True)
            .values('rejection_reason')
            .annotate(count=Count('id'))
        )
        
        # Percepción de precios
        price_perception_avg = feedbacks.exclude(price_perception__isnull=True).aggregate(
            avg=Avg('price_perception')
        )['avg'] or 0
        
        # Solicitudes de reunión
        meeting_requests = feedbacks.filter(meeting_requested=True).count()
        meeting_conversion = (meeting_requests / total) * 100 if total > 0 else 0
        
        # Conversión a oportunidades reales
        # Verificar cuántas propuestas con respuesta "interested" se convirtieron en ventas
        interested_count = feedbacks.filter(response_type='interested').count()
        
        # Tendencias a lo largo del tiempo (agregación por semana)
        time_series = []
        
        # Generar insights y recomendaciones
        insights = []
        
        if price_perception_avg > 4:
            insights.append("Los clientes perciben los precios como altos. Considerar revisar la estructura de precios o mejorar la comunicación de valor.")
        
        rejection_clarity = feedbacks.filter(rejection_reason='clarity').count()
        if rejection_clarity / total > 0.2:
            insights.append("Muchos clientes indican falta de claridad. Revisar cómo se presenta la información en las propuestas.")
    
    else:
        # Sin datos para el período
        response_distribution = []
        rejection_reasons = []
        price_perception_avg = 0
        meeting_requests = 0
        meeting_conversion = 0
        time_series = []
        insights = ["No hay suficientes datos para generar insights en el período seleccionado."]
    
    return render(request, 'pricing/feedback_dashboard.html', {
        'total_feedbacks': total,
        'start_date': start_date,
        'end_date': end_date,
        'response_distribution': response_distribution,
        'rejection_reasons': rejection_reasons,
        'price_perception_avg': price_perception_avg,
        'meeting_requests': meeting_requests,
        'meeting_conversion': meeting_conversion,
        'time_series': time_series,
        'insights': insights
    })


@login_required
def meeting_requests_list(request):
    """Lista de solicitudes de reunión pendientes y programadas."""
    
    # Filtrar por estado
    status = request.GET.get('status', 'pending')
    
    if status == 'scheduled':
        meetings = MeetingRequest.objects.filter(is_scheduled=True).order_by('scheduled_for')
    elif status == 'completed':
        meetings = MeetingRequest.objects.filter(meeting_completed=True).order_by('-updated_at')
    else:  # pending
        meetings = MeetingRequest.objects.filter(is_scheduled=False, meeting_completed=False).order_by('-created_at')
    
    return render(request, 'pricing/meeting_requests_list.html', {
        'meetings': meetings,
        'status': status
    })


@login_required
@require_POST
def mark_meeting_completed(request, meeting_id):
    """Marca una reunión como completada."""
    meeting = get_object_or_404(MeetingRequest, id=meeting_id)
    meeting.meeting_completed = True
    meeting.save()
    
    messages.success(request, "Reunión marcada como completada")
    return redirect('pricing:meeting_requests_list')


# Utilidades para el front-end
@login_required
@require_GET
def get_feedback_stats_json(request):
    """
    API interna para obtener estadísticas de retroalimentación en formato JSON.
    Para uso en dashboards y reportes.
    """
    # Período de análisis (por defecto el último mes)
    end_date = timezone.now().date()
    start_date = request.GET.get('start_date', '')
    if not start_date:
        start_date = end_date - timedelta(days=30)
    else:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        except:
            start_date = end_date - timedelta(days=30)
    
    # Obtener estadísticas
    tracker = get_proposal_tracker()
    stats = asyncio.run(tracker.generate_insights_report(
        start_date=timezone.make_aware(datetime.combine(start_date, datetime.min.time())),
        end_date=timezone.make_aware(datetime.combine(end_date, datetime.max.time()))
    ))
    
    return JsonResponse(stats)


@csrf_exempt
@require_POST
def webhook_feedback(request):
    """
    Webhook para recibir retroalimentación desde fuentes externas.
    
    Este endpoint permite integrar el sistema de retroalimentación con otras
    plataformas, como herramientas de encuestas o CRM.
    """
    # Verificar token de seguridad
    token = request.headers.get('X-Api-Token')
    if not token or token != settings.FEEDBACK_API_TOKEN:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    try:
        data = json.loads(request.body)
        
        # Validar datos mínimos
        required_fields = ['token', 'response_type']
        for field in required_fields:
            if field not in data:
                return JsonResponse({'error': f'Missing required field: {field}'}, status=400)
        
        # Procesar feedback
        tracker = get_proposal_tracker()
        feedback = asyncio.run(tracker.process_feedback(data['token'], data))
        
        if not feedback:
            return JsonResponse({'error': 'Invalid token or proposal not found'}, status=400)
        
        return JsonResponse({'success': True, 'feedback_id': feedback.id})
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Error en webhook de retroalimentación: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)
