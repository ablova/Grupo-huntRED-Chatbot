"""
Vistas Administrativas Avanzadas para el Sistema de Publicación.
"""
import json
from typing import Dict, Any, List
from datetime import datetime, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, Count, Sum, Avg, F
from django.utils import timezone
from django.core.paginator import Paginator
from django.template.loader import render_to_string

from app.ats.publish.models import (
    MarketingCampaign, CampaignApproval, CampaignMetrics, 
    CampaignAuditLog, AudienceSegment, ContentTemplate
)
from app.models import BusinessUnit

@login_required
@permission_required('app.view_marketingcampaign')
def campaign_dashboard(request):
    """
    Dashboard principal de campañas con métricas en tiempo real.
    """
    # Obtener estadísticas generales
    total_campaigns = MarketingCampaign.objects.count()
    active_campaigns = MarketingCampaign.objects.filter(status='active').count()
    pending_approvals = CampaignApproval.objects.filter(status='pending').count()
    
    # Métricas de rendimiento
    recent_campaigns = MarketingCampaign.objects.filter(
        created_at__gte=timezone.now() - timedelta(days=30)
    )
    
    total_revenue = sum(campaign.metrics.aggregate(Sum('total_revenue'))['total_revenue__sum'] or 0 
                       for campaign in recent_campaigns)
    total_spent = sum(campaign.metrics.aggregate(Sum('total_spent'))['total_spent__sum'] or 0 
                     for campaign in recent_campaigns)
    
    avg_engagement = CampaignMetrics.objects.aggregate(Avg('engagement_score'))['engagement_score__avg'] or 0
    
    # Campañas que requieren atención
    campaigns_needing_attention = MarketingCampaign.objects.filter(
        Q(status='pending') | 
        Q(approvals__status='pending') |
        Q(scheduled_date__lte=timezone.now() + timedelta(days=1))
    ).distinct()[:5]
    
    # Gráficos de rendimiento
    performance_data = _get_performance_chart_data()
    
    context = {
        'total_campaigns': total_campaigns,
        'active_campaigns': active_campaigns,
        'pending_approvals': pending_approvals,
        'total_revenue': total_revenue,
        'total_spent': total_spent,
        'roi': ((total_revenue - total_spent) / total_spent * 100) if total_spent > 0 else 0,
        'avg_engagement': avg_engagement,
        'campaigns_needing_attention': campaigns_needing_attention,
        'performance_data': performance_data,
        'page_title': 'Dashboard de Campañas',
        'active_tab': 'dashboard'
    }
    
    return render(request, 'ats/publish/admin/dashboard.html', context)

@login_required
@permission_required('app.view_campaignapproval')
def approval_workflow(request):
    """
    Vista del workflow de aprobación de campañas.
    """
    # Obtener aprobaciones según el rol del usuario
    if request.user.is_superuser:
        approvals = CampaignApproval.objects.all()
    elif request.user.groups.filter(name='Administradores').exists():
        approvals = CampaignApproval.objects.filter(
            Q(required_level='admin') | Q(required_level='supervisor') | Q(required_level='consultant')
        )
    elif request.user.groups.filter(name='Supervisores').exists():
        approvals = CampaignApproval.objects.filter(
            Q(required_level='supervisor') | Q(required_level='consultant')
        )
    else:
        approvals = CampaignApproval.objects.filter(created_by=request.user)
    
    # Filtrar por estado
    status_filter = request.GET.get('status', '')
    if status_filter:
        approvals = approvals.filter(status=status_filter)
    
    # Ordenar
    approvals = approvals.order_by('-created_at')
    
    # Paginación
    paginator = Paginator(approvals, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_choices': CampaignApproval.APPROVAL_STATUS_CHOICES,
        'current_status': status_filter,
        'page_title': 'Workflow de Aprobación',
        'active_tab': 'approvals'
    }
    
    return render(request, 'ats/publish/admin/approval_workflow.html', context)

@login_required
@permission_required('app.change_campaignapproval')
def review_campaign(request, approval_id):
    """
    Vista para revisar y aprobar/rechazar una campaña.
    """
    approval = get_object_or_404(CampaignApproval, id=approval_id)
    campaign = approval.campaign
    
    # Verificar permisos
    if not approval.can_be_approved_by(request.user):
        messages.error(request, 'No tienes permisos para revisar esta campaña.')
        return redirect('approval_workflow')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        notes = request.POST.get('notes', '')
        
        try:
            if action == 'approve':
                approval.approve(
                    user=request.user,
                    notes=notes,
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                messages.success(request, 'Campaña aprobada exitosamente.')
                
                # Log de auditoría
                CampaignAuditLog.log_action(
                    campaign=campaign,
                    user=request.user,
                    action='approved',
                    notes=f'Aprobada por {request.user.username}',
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                
            elif action == 'reject':
                approval.reject(
                    user=request.user,
                    reason=notes,
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                messages.warning(request, 'Campaña rechazada.')
                
                # Log de auditoría
                CampaignAuditLog.log_action(
                    campaign=campaign,
                    user=request.user,
                    action='rejected',
                    notes=f'Rechazada por {request.user.username}: {notes}',
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
            
            return redirect('approval_workflow')
            
        except Exception as e:
            messages.error(request, f'Error al procesar la acción: {str(e)}')
    
    # Obtener datos de la campaña para preview
    campaign_data = _get_campaign_preview_data(campaign)
    
    context = {
        'approval': approval,
        'campaign': campaign,
        'campaign_data': campaign_data,
        'can_approve': approval.can_be_approved_by(request.user),
        'page_title': f'Revisar Campaña: {campaign.name}',
        'active_tab': 'approvals'
    }
    
    return render(request, 'ats/publish/admin/review_campaign.html', context)

@login_required
@permission_required('app.view_campaignmetrics')
def campaign_metrics(request, campaign_id=None):
    """
    Vista de métricas detalladas de campañas.
    """
    if campaign_id:
        campaign = get_object_or_404(MarketingCampaign, id=campaign_id)
        metrics = campaign.metrics.all().order_by('-measurement_date')
        
        # Métricas específicas de la campaña
        campaign_metrics = _get_campaign_specific_metrics(campaign)
        
        context = {
            'campaign': campaign,
            'metrics': metrics,
            'campaign_metrics': campaign_metrics,
            'page_title': f'Métricas: {campaign.name}',
            'active_tab': 'metrics'
        }
        
        return render(request, 'ats/publish/admin/campaign_metrics_detail.html', context)
    
    else:
        # Vista general de métricas
        campaigns = MarketingCampaign.objects.filter(status='active')
        
        # Métricas agregadas
        overall_metrics = _get_overall_metrics()
        
        # Top campañas por rendimiento
        top_campaigns = _get_top_performing_campaigns()
        
        # Gráficos de tendencias
        trend_data = _get_metrics_trend_data()
        
        context = {
            'overall_metrics': overall_metrics,
            'top_campaigns': top_campaigns,
            'trend_data': trend_data,
            'page_title': 'Métricas de Campañas',
            'active_tab': 'metrics'
        }
        
        return render(request, 'ats/publish/admin/campaign_metrics_overview.html', context)

@login_required
@permission_required('app.view_campaignauditlog')
def audit_log(request):
    """
    Vista del log de auditoría de campañas.
    """
    # Obtener logs con filtros
    logs = CampaignAuditLog.objects.all()
    
    # Filtros
    campaign_filter = request.GET.get('campaign', '')
    user_filter = request.GET.get('user', '')
    action_filter = request.GET.get('action', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    if campaign_filter:
        logs = logs.filter(campaign__name__icontains=campaign_filter)
    if user_filter:
        logs = logs.filter(user__username__icontains=user_filter)
    if action_filter:
        logs = logs.filter(action=action_filter)
    if date_from:
        logs = logs.filter(action_timestamp__date__gte=date_from)
    if date_to:
        logs = logs.filter(action_timestamp__date__lte=date_to)
    
    # Ordenar
    logs = logs.order_by('-action_timestamp')
    
    # Paginación
    paginator = Paginator(logs, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'action_choices': CampaignAuditLog.ACTION_CHOICES,
        'filters': {
            'campaign': campaign_filter,
            'user': user_filter,
            'action': action_filter,
            'date_from': date_from,
            'date_to': date_to
        },
        'page_title': 'Log de Auditoría',
        'active_tab': 'audit'
    }
    
    return render(request, 'ats/publish/admin/audit_log.html', context)

@login_required
@permission_required('app.view_campaignauditlog')
def audit_log_detail(request, log_id):
    """
    Vista detallada de un log de auditoría.
    """
    log = get_object_or_404(CampaignAuditLog, id=log_id)
    
    # Formatear cambios para visualización
    changes = _format_audit_changes(log.previous_state, log.new_state)
    
    context = {
        'log': log,
        'changes': changes,
        'page_title': f'Detalle de Auditoría: {log.campaign.name}',
        'active_tab': 'audit'
    }
    
    return render(request, 'ats/publish/admin/audit_log_detail.html', context)

# APIs para AJAX
@login_required
@permission_required('app.view_marketingcampaign')
def api_campaign_stats(request):
    """
    API para obtener estadísticas de campañas en tiempo real.
    """
    try:
        # Estadísticas generales
        stats = {
            'total_campaigns': MarketingCampaign.objects.count(),
            'active_campaigns': MarketingCampaign.objects.filter(status='active').count(),
            'pending_approvals': CampaignApproval.objects.filter(status='pending').count(),
            'total_revenue': CampaignMetrics.objects.aggregate(Sum('total_revenue'))['total_revenue__sum'] or 0,
            'avg_engagement': CampaignMetrics.objects.aggregate(Avg('engagement_score'))['engagement_score__avg'] or 0
        }
        
        return JsonResponse({'success': True, 'data': stats})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@permission_required('app.view_campaignmetrics')
def api_metrics_chart(request):
    """
    API para obtener datos de gráficos de métricas.
    """
    try:
        chart_type = request.GET.get('type', 'performance')
        
        if chart_type == 'performance':
            data = _get_performance_chart_data()
        elif chart_type == 'engagement':
            data = _get_engagement_chart_data()
        elif chart_type == 'revenue':
            data = _get_revenue_chart_data()
        else:
            data = {}
        
        return JsonResponse({'success': True, 'data': data})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
@require_http_methods(["POST"])
def api_update_metrics(request):
    """
    API para actualizar métricas de campañas (usado por tareas automáticas).
    """
    try:
        data = json.loads(request.body)
        campaign_id = data.get('campaign_id')
        metrics_data = data.get('metrics', {})
        
        campaign = get_object_or_404(MarketingCampaign, id=campaign_id)
        
        # Actualizar o crear métricas
        metrics, created = CampaignMetrics.objects.get_or_create(
            campaign=campaign,
            measurement_date=timezone.now().date(),
            defaults=metrics_data
        )
        
        if not created:
            metrics.update_metrics(metrics_data)
        
        return JsonResponse({'success': True, 'message': 'Métricas actualizadas'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

# Funciones auxiliares
def _get_performance_chart_data():
    """
    Obtiene datos para gráfico de rendimiento.
    """
    # Últimos 30 días
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    
    metrics = CampaignMetrics.objects.filter(
        measurement_date__range=[start_date, end_date]
    ).values('measurement_date').annotate(
        avg_engagement=Avg('engagement_score'),
        total_revenue=Sum('total_revenue'),
        total_conversions=Sum('total_converted')
    ).order_by('measurement_date')
    
    return {
        'labels': [m['measurement_date'].strftime('%d/%m') for m in metrics],
        'engagement': [float(m['avg_engagement'] or 0) for m in metrics],
        'revenue': [float(m['total_revenue'] or 0) for m in metrics],
        'conversions': [int(m['total_conversions'] or 0) for m in metrics]
    }

def _get_engagement_chart_data():
    """
    Obtiene datos para gráfico de engagement.
    """
    campaigns = MarketingCampaign.objects.filter(status='active')[:10]
    
    return {
        'labels': [c.name for c in campaigns],
        'engagement': [float(c.metrics.aggregate(Avg('engagement_score'))['engagement_score__avg'] or 0) for c in campaigns]
    }

def _get_revenue_chart_data():
    """
    Obtiene datos para gráfico de ingresos.
    """
    campaigns = MarketingCampaign.objects.filter(status='active').order_by('-created_at')[:10]
    
    return {
        'labels': [c.name for c in campaigns],
        'revenue': [float(c.metrics.aggregate(Sum('total_revenue'))['total_revenue__sum'] or 0) for c in campaigns],
        'spent': [float(c.metrics.aggregate(Sum('total_spent'))['total_spent__sum'] or 0) for c in campaigns]
    }

def _get_campaign_preview_data(campaign):
    """
    Obtiene datos para preview de campaña.
    """
    return {
        'basic_info': {
            'name': campaign.name,
            'description': campaign.description,
            'type': campaign.get_campaign_type_display(),
            'status': campaign.get_status_display(),
            'scheduled_date': campaign.scheduled_date,
            'budget': campaign.budget
        },
        'segments': list(campaign.target_segments.values('name', 'segment_type')),
        'templates': list(campaign.content_templates.values('name', 'template_type')),
        'approval_history': list(campaign.approvals.values('status', 'created_at', 'created_by__username')),
        'recent_metrics': campaign.metrics.first()
    }

def _get_campaign_specific_metrics(campaign):
    """
    Obtiene métricas específicas de una campaña.
    """
    latest_metrics = campaign.metrics.first()
    
    if not latest_metrics:
        return {}
    
    return {
        'engagement_score': latest_metrics.engagement_score,
        'open_rate': latest_metrics.open_rate,
        'click_rate': latest_metrics.click_rate,
        'conversion_rate': latest_metrics.conversion_rate,
        'roi': latest_metrics.roi,
        'cost_per_conversion': latest_metrics.cost_per_conversion,
        'total_revenue': latest_metrics.total_revenue,
        'total_spent': latest_metrics.total_spent,
        'aura_accuracy': latest_metrics.aura_prediction_accuracy
    }

def _get_overall_metrics():
    """
    Obtiene métricas generales de todas las campañas.
    """
    return {
        'total_campaigns': MarketingCampaign.objects.count(),
        'active_campaigns': MarketingCampaign.objects.filter(status='active').count(),
        'total_revenue': CampaignMetrics.objects.aggregate(Sum('total_revenue'))['total_revenue__sum'] or 0,
        'total_spent': CampaignMetrics.objects.aggregate(Sum('total_spent'))['total_spent__sum'] or 0,
        'avg_engagement': CampaignMetrics.objects.aggregate(Avg('engagement_score'))['engagement_score__avg'] or 0,
        'avg_open_rate': CampaignMetrics.objects.aggregate(Avg('open_rate'))['open_rate__avg'] or 0,
        'avg_click_rate': CampaignMetrics.objects.aggregate(Avg('click_rate'))['click_rate__avg'] or 0
    }

def _get_top_performing_campaigns():
    """
    Obtiene las mejores campañas por rendimiento.
    """
    return MarketingCampaign.objects.filter(
        status='active'
    ).annotate(
        avg_engagement=Avg('metrics__engagement_score'),
        total_revenue=Sum('metrics__total_revenue'),
        total_conversions=Sum('metrics__total_converted')
    ).order_by('-avg_engagement')[:10]

def _get_metrics_trend_data():
    """
    Obtiene datos de tendencias de métricas.
    """
    # Últimos 7 días
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=7)
    
    return CampaignMetrics.objects.filter(
        measurement_date__range=[start_date, end_date]
    ).values('measurement_date').annotate(
        avg_engagement=Avg('engagement_score'),
        total_revenue=Sum('total_revenue'),
        total_conversions=Sum('total_converted')
    ).order_by('measurement_date')

def _format_audit_changes(previous_state, new_state):
    """
    Formatea los cambios para visualización en el log de auditoría.
    """
    changes = []
    
    for key in set(previous_state.keys()) | set(new_state.keys()):
        old_value = previous_state.get(key, 'N/A')
        new_value = new_state.get(key, 'N/A')
        
        if old_value != new_value:
            changes.append({
                'field': key,
                'old_value': old_value,
                'new_value': new_value,
                'type': 'changed'
            })
    
    return changes 