# /home/pablo/app/com/feedback/process_views.py
"""
Vistas para gestionar y visualizar feedback específico de procesos y enviar recordatorios.

Este módulo contiene vistas específicas para:
1. Visualizar todo el feedback relacionado con un proceso/oportunidad específica
2. Gestionar recordatorios manualmente para solicitudes pendientes
3. Enviar solicitudes de feedback ad-hoc para procesos específicos
"""

import logging
import json
import asyncio
from datetime import datetime, timedelta
import secrets

from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse, Http404
from django.views.decorators.http import require_POST, require_GET
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.urls import reverse
from django.db.models import Q, Count, Avg, F, Value, Sum, Case, When, IntegerField

from app.models import Opportunity, Proposal, ServiceContract, Company, Contact, BusinessUnit
from app.ats.feedback.feedback_models import ServiceFeedback, OngoingServiceFeedback, CompletedServiceFeedback
from app.ats.feedback.reminder_system import get_reminder_system, ReminderChannel
from app.ats.feedback import get_feedback_tracker

logger = logging.getLogger(__name__)

# Función auxiliar para ejecutar corrutinas asíncronas
def run_async(coroutine):
    """Ejecuta una corrutina asíncrona desde un contexto síncrono."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(coroutine)

@login_required
def process_feedback_summary(request, opportunity_id):
    """
    Vista que muestra un resumen de toda la retroalimentación relacionada 
    con un proceso (oportunidad) específico.
    
    Incluye feedback de propuestas, durante el servicio y evaluación final.
    """
    # Obtener la oportunidad
    opportunity = get_object_or_404(Opportunity, id=opportunity_id)
    
    # Obtener todo el feedback relacionado
    feedbacks = ServiceFeedback.objects.filter(opportunity=opportunity).order_by('-created_at')
    
    # Agrupar por etapa
    proposal_feedback = feedbacks.filter(stage='proposal')
    ongoing_feedback = feedbacks.filter(stage='ongoing')
    completed_feedback = feedbacks.filter(stage='completed')
    
    # Verificar si hay solicitudes pendientes
    reminder_system = get_reminder_system()
    pending_requests = []
    
    # Buscar en Redis solicitudes pendientes para esta oportunidad
    pattern = f"{reminder_system.redis_prefix}request:*"
    for key in reminder_system.redis.scan_iter(match=pattern):
        try:
            request_data = json.loads(reminder_system.redis.get(key))
            
            # Si es para esta oportunidad y no se ha respondido
            if request_data.get("opportunity_id") == opportunity_id and not request_data.get("responded", False):
                # Calcular días pendientes
                sent_at = datetime.fromisoformat(request_data["sent_at"])
                days_pending = (timezone.now() - sent_at).days
                
                pending_requests.append({
                    "token": request_data.get("token"),
                    "stage": request_data.get("stage"),
                    "sent_at": sent_at,
                    "days_pending": days_pending,
                    "reminders_sent": request_data.get("reminders_sent", 0)
                })
        except:
            pass
    
    # Determinar si hay una solicitud activa pendiente
    has_pending_request = len(pending_requests) > 0
    
    # Verificar etapa actual del proceso para saber qué tipo de feedback se puede solicitar
    can_request_proposal = False
    can_request_ongoing = False
    can_request_completion = False
    
    # Lógica para determinar qué tipos de feedback se pueden solicitar
    if hasattr(opportunity, 'proposals') and opportunity.proposals.exists():
        can_request_proposal = True
    
    if hasattr(opportunity, 'service_contract') and opportunity.service_contract.status == 'active':
        can_request_ongoing = True
    
    if hasattr(opportunity, 'service_contract') and opportunity.service_contract.status == 'completed':
        can_request_completion = True
    
    return render(request, 'feedback/process_summary.html', {
        'opportunity': opportunity,
        'proposal_feedback': proposal_feedback,
        'ongoing_feedback': ongoing_feedback,
        'completed_feedback': completed_feedback,
        'pending_requests': pending_requests,
        'has_pending_request': has_pending_request,
        'can_request_proposal': can_request_proposal,
        'can_request_ongoing': can_request_ongoing,
        'can_request_completion': can_request_completion
    })

@login_required
@require_POST
def send_feedback_request(request, opportunity_id):
    """
    Envía una nueva solicitud de feedback para una oportunidad específica.
    
    Permite enviar solicitudes ad-hoc en cualquier etapa del proceso.
    """
    opportunity = get_object_or_404(Opportunity, id=opportunity_id)
    
    # Obtener parámetros
    stage = request.POST.get('stage', 'proposal')
    contact_email = request.POST.get('contact_email', '')
    notes = request.POST.get('notes', '')
    
    # Validar email
    if not contact_email:
        messages.error(request, "Se requiere una dirección de email para enviar la solicitud")
        return redirect('feedback:process_summary', opportunity_id=opportunity_id)
    
    # Generar token único
    token = secrets.token_urlsafe(32)
    
    # Obtener el tracker adecuado según la etapa
    try:
        tracker = get_feedback_tracker(stage)
        
        # Preparar datos según la etapa
        if stage == 'proposal':
            # Buscar la propuesta más reciente
            proposal = opportunity.proposals.order_by('-created_at').first()
            if not proposal:
                messages.error(request, "No se encontró ninguna propuesta asociada a esta oportunidad")
                return redirect('feedback:process_summary', opportunity_id=opportunity_id)
            
            # Registrar solicitud
            reminder_system = get_reminder_system()
            run_async(reminder_system.register_feedback_request(
                token=token,
                opportunity_id=opportunity_id,
                proposal_id=proposal.id,
                stage=stage,
                contact_email=contact_email,
                company_id=opportunity.company_id if opportunity.company else None,
                business_unit_id=opportunity.business_unit_id if opportunity.business_unit else None
            ))
            
            # Enviar solicitud inmediatamente
            success = run_async(tracker._send_feedback_email({
                "token": token,
                "proposal_id": proposal.id,
                "company_name": opportunity.company.name if opportunity.company else "su empresa",
                "contact_name": opportunity.contact.name if opportunity.contact else "Estimado cliente",
                "contact_email": contact_email
            }))
            
        elif stage == 'ongoing':
            # Verificar que hay un contrato activo
            if not hasattr(opportunity, 'service_contract') or opportunity.service_contract.status != 'active':
                messages.error(request, "No hay un servicio activo para esta oportunidad")
                return redirect('feedback:process_summary', opportunity_id=opportunity_id)
            
            # Registrar solicitud
            reminder_system = get_reminder_system()
            run_async(reminder_system.register_feedback_request(
                token=token,
                opportunity_id=opportunity_id,
                stage=stage,
                contact_email=contact_email,
                company_id=opportunity.company_id if opportunity.company else None,
                business_unit_id=opportunity.business_unit_id if opportunity.business_unit else None
            ))
            
            # Calcular progreso estimado
            contract = opportunity.service_contract
            start_date = contract.start_date
            end_date = contract.end_date or (start_date + timedelta(days=90))
            total_days = (end_date - start_date).days
            days_elapsed = (timezone.now().date() - start_date).days
            progress_percentage = min(int((days_elapsed / total_days) * 100), 99) if total_days > 0 else 50
            
            # Enviar solicitud inmediatamente
            success = run_async(tracker._send_feedback_email({
                "token": token,
                "opportunity_id": opportunity_id,
                "company_name": opportunity.company.name if opportunity.company else "su empresa",
                "contact_email": contact_email,
                "progress_percentage": progress_percentage,
                "milestone": 1
            }))
            
        elif stage == 'completed':
            # Verificar que el servicio está marcado como completado
            if not hasattr(opportunity, 'service_contract') or opportunity.service_contract.status != 'completed':
                messages.error(request, "El servicio no está marcado como completado")
                return redirect('feedback:process_summary', opportunity_id=opportunity_id)
            
            # Registrar solicitud
            reminder_system = get_reminder_system()
            run_async(reminder_system.register_feedback_request(
                token=token,
                opportunity_id=opportunity_id,
                stage=stage,
                contact_email=contact_email,
                company_id=opportunity.company_id if opportunity.company else None,
                business_unit_id=opportunity.business_unit_id if opportunity.business_unit else None
            ))
            
            # Enviar solicitud inmediatamente
            success = run_async(tracker._send_feedback_email({
                "token": token,
                "opportunity_id": opportunity_id,
                "company_name": opportunity.company.name if opportunity.company else "su empresa",
                "contact_email": contact_email
            }))
        
        # Mostrar mensaje según resultado
        if success:
            messages.success(request, f"Solicitud de retroalimentación enviada correctamente a {contact_email}")
        else:
            messages.error(request, "Error al enviar la solicitud. Por favor, inténtelo nuevamente.")
            
    except Exception as e:
        logger.error(f"Error al enviar solicitud de feedback: {str(e)}")
        messages.error(request, f"Error al procesar la solicitud: {str(e)}")
    
    return redirect('feedback:process_summary', opportunity_id=opportunity_id)

@login_required
@require_POST
def send_reminder(request, opportunity_id):
    """
    Envía un recordatorio manual para una solicitud de feedback pendiente.
    """
    # Obtener token de la solicitud pendiente
    token = request.POST.get('token', '')
    if not token:
        messages.error(request, "Token de solicitud no válido")
        return redirect('feedback:process_summary', opportunity_id=opportunity_id)
    
    # Obtener canales seleccionados
    channels = []
    if request.POST.get('email_channel') == 'on':
        channels.append(ReminderChannel.EMAIL)
    if request.POST.get('whatsapp_channel') == 'on':
        channels.append(ReminderChannel.WHATSAPP)
    
    # Si no se seleccionó ningún canal, usar email por defecto
    if not channels:
        channels = [ReminderChannel.EMAIL]
    
    try:
        # Programar recordatorio inmediato
        reminder_system = get_reminder_system()
        reminder_id = run_async(reminder_system.schedule_reminder(
            token=token,
            days_delay=0,  # Inmediato
            channels=channels
        ))
        
        if reminder_id:
            # Procesar recordatorios pendientes inmediatamente
            run_async(reminder_system.process_pending_reminders())
            messages.success(request, "Recordatorio enviado correctamente")
        else:
            messages.error(request, "No se pudo programar el recordatorio")
    
    except Exception as e:
        logger.error(f"Error al enviar recordatorio manual: {str(e)}")
        messages.error(request, f"Error al enviar recordatorio: {str(e)}")
    
    return redirect('feedback:process_summary', opportunity_id=opportunity_id)

@login_required
def pending_reminders_dashboard(request):
    """
    Dashboard para gestionar todas las solicitudes de feedback pendientes.
    """
    # Obtener filtros
    stage = request.GET.get('stage', '')
    business_unit_id = request.GET.get('business_unit', '')
    days_pending = request.GET.get('days_pending', '')
    
    # Obtener estadísticas generales
    reminder_system = get_reminder_system()
    stats = run_async(reminder_system.get_pending_requests_stats())
    
    # Obtener solicitudes pendientes
    pending_requests = []
    pattern = f"{reminder_system.redis_prefix}request:*"
    
    for key in reminder_system.redis.scan_iter(match=pattern):
        try:
            request_data = json.loads(reminder_system.redis.get(key))
            
            # Si ya se respondió, continuar
            if request_data.get("responded", False):
                continue
            
            # Aplicar filtros
            if stage and request_data.get("stage") != stage:
                continue
                
            if business_unit_id and str(request_data.get("business_unit_id")) != business_unit_id:
                continue
            
            # Calcular días pendientes
            sent_at = datetime.fromisoformat(request_data["sent_at"])
            days_pending_value = (timezone.now() - sent_at).days
            
            # Filtrar por días pendientes
            if days_pending:
                if days_pending == 'low' and days_pending_value > 7:
                    continue
                elif days_pending == 'normal' and (days_pending_value <= 7 or days_pending_value > 14):
                    continue
                elif days_pending == 'high' and (days_pending_value <= 14 or days_pending_value > 30):
                    continue
                elif days_pending == 'critical' and days_pending_value <= 30:
                    continue
            
            # Añadir a la lista
            pending_requests.append({
                "token": request_data.get("token"),
                "opportunity_id": request_data.get("opportunity_id"),
                "proposal_id": request_data.get("proposal_id"),
                "stage": request_data.get("stage"),
                "contact_email": request_data.get("contact_email"),
                "contact_name": request_data.get("contact_name"),
                "company_name": request_data.get("company_name"),
                "business_unit": request_data.get("business_unit"),
                "sent_at": sent_at,
                "days_pending": days_pending_value,
                "reminders_sent": request_data.get("reminders_sent", 0),
                "priority": "critical" if days_pending_value > 30 else 
                            "high" if days_pending_value > 14 else 
                            "normal" if days_pending_value > 7 else "low"
            })
        except Exception as e:
            logger.error(f"Error al procesar solicitud pendiente {key}: {str(e)}")
    
    # Ordenar por antigüedad (más antiguas primero)
    pending_requests.sort(key=lambda x: x["days_pending"], reverse=True)
    
    # Obtener unidades de negocio para filtros
    business_units = BusinessUnit.objects.all()
    
    return render(request, 'feedback/pending_reminders.html', {
        'pending_requests': pending_requests,
        'stats': stats,
        'stage_filter': stage,
        'business_unit_filter': business_unit_id,
        'days_pending_filter': days_pending,
        'business_units': business_units,
        'stage_options': [
            ('proposal', 'Propuestas'),
            ('ongoing', 'Servicios en Curso'),
            ('completed', 'Servicios Concluidos')
        ],
        'days_pending_options': [
            ('low', 'Recientes (0-7 días)'),
            ('normal', 'Normal (8-14 días)'),
            ('high', 'Alta (15-30 días)'),
            ('critical', 'Crítica (>30 días)')
        ]
    })

@login_required
@require_POST
def bulk_send_reminders(request):
    """
    Envía recordatorios en lote para múltiples solicitudes pendientes.
    """
    # Obtener tokens seleccionados
    tokens = request.POST.getlist('selected_tokens', [])
    
    if not tokens:
        messages.error(request, "No se seleccionó ninguna solicitud")
        return redirect('feedback:pending_reminders')
    
    # Canales seleccionados
    channels = []
    if request.POST.get('email_channel') == 'on':
        channels.append(ReminderChannel.EMAIL)
    if request.POST.get('whatsapp_channel') == 'on':
        channels.append(ReminderChannel.WHATSAPP)
    
    # Si no se seleccionó ningún canal, usar email por defecto
    if not channels:
        channels = [ReminderChannel.EMAIL]
    
    # Programar recordatorios
    reminder_system = get_reminder_system()
    success_count = 0
    error_count = 0
    
    for token in tokens:
        try:
            reminder_id = run_async(reminder_system.schedule_reminder(
                token=token,
                days_delay=0,  # Inmediato
                channels=channels
            ))
            
            if reminder_id:
                success_count += 1
            else:
                error_count += 1
                
        except Exception as e:
            logger.error(f"Error al programar recordatorio para {token}: {str(e)}")
            error_count += 1
    
    # Procesar recordatorios inmediatamente
    run_async(reminder_system.process_pending_reminders())
    
    # Mostrar mensaje según resultados
    if success_count > 0:
        messages.success(request, f"Se programaron correctamente {success_count} recordatorios")
    
    if error_count > 0:
        messages.warning(request, f"No se pudieron programar {error_count} recordatorios")
    
    return redirect('feedback:pending_reminders')

@login_required
@require_POST
def manually_mark_responded(request):
    """
    Marca manualmente una solicitud como respondida.
    
    Útil cuando la retroalimentación se recibió por otro canal (ej. llamada telefónica).
    """
    token = request.POST.get('token', '')
    notes = request.POST.get('notes', '')
    
    if not token:
        messages.error(request, "Token de solicitud no válido")
        return redirect('feedback:pending_reminders')
    
    # Marcar como respondida en el sistema de recordatorios
    reminder_system = get_reminder_system()
    request_key = f"{reminder_system.redis_prefix}request:{token}"
    request_data_json = reminder_system.redis.get(request_key)
    
    if not request_data_json:
        messages.error(request, "No se encontró la solicitud de feedback")
        return redirect('feedback:pending_reminders')
    
    try:
        request_data = json.loads(request_data_json)
        
        # Actualizar estado
        now = timezone.now()
        request_data["responded"] = True
        request_data["responded_at"] = now.isoformat()
        request_data["status"] = "responded"
        request_data["manual_notes"] = notes
        
        # Guardar en Redis
        reminder_system.redis.set(request_key, json.dumps(request_data), ex=60*60*24*90)
        
        messages.success(request, "Solicitud marcada como respondida correctamente")
        
    except Exception as e:
        logger.error(f"Error al marcar solicitud como respondida: {str(e)}")
        messages.error(request, "Error al procesar la solicitud")
    
    return redirect('feedback:pending_reminders')
