"""
Vistas para el dashboard de prospección inteligente y gestión del Gantt chart.
"""
import logging
from typing import Dict, Any
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg, Sum
from django.template.response import TemplateResponse

from app.ats.publish.models import (
    DomainAnalysis, UsageFrequencyAnalysis, IntelligentProspecting,
    CrossSellingOpportunity, MarketingCampaign, CampaignExecutionPhase,
    CampaignTask, CampaignMilestone, CampaignGanttView
)
from app.ats.publish.services.intelligent_prospecting_service import IntelligentProspectingService
from app.ats.publish.services.gantt_chart_service import GanttChartService

logger = logging.getLogger(__name__)

@staff_member_required
def intelligent_prospecting_dashboard(request):
    """
    Dashboard principal de prospección inteligente.
    """
    try:
        prospecting_service = IntelligentProspectingService()
        
        # Obtener datos del dashboard
        dashboard_data = prospecting_service.get_prospecting_dashboard_data()
        
        # Obtener prospectos de alto potencial
        high_potential_prospects = DomainAnalysis.objects.filter(
            prospect_score__gte=70
        ).order_by('-prospect_score')[:10]
        
        # Obtener oportunidades de cross-selling
        cross_sell_opportunities = CrossSellingOpportunity.objects.filter(
            status='identified'
        ).order_by('-priority', '-estimated_value')[:10]
        
        # Obtener campañas activas
        active_campaigns = MarketingCampaign.objects.filter(
            status='active'
        ).order_by('-created_at')[:5]
        
        # Métricas rápidas
        quick_metrics = {
            'total_domains': DomainAnalysis.objects.count(),
            'high_potential_count': DomainAnalysis.objects.filter(prospect_score__gte=70).count(),
            'active_prospecting': IntelligentProspecting.objects.filter(
                status__in=['research', 'qualified', 'contacted']
            ).count(),
            'cross_sell_opportunities': CrossSellingOpportunity.objects.filter(
                status='identified'
            ).count()
        }
        
        context = {
            'title': 'Dashboard de Prospección Inteligente',
            'dashboard_data': dashboard_data,
            'high_potential_prospects': high_potential_prospects,
            'cross_sell_opportunities': cross_sell_opportunities,
            'active_campaigns': active_campaigns,
            'quick_metrics': quick_metrics
        }
        
        return TemplateResponse(request, 'admin/intelligent_prospecting_dashboard.html', context)
        
    except Exception as e:
        logger.error(f"Error en dashboard de prospección: {str(e)}")
        context = {
            'title': 'Dashboard de Prospección Inteligente',
            'error': str(e)
        }
        return TemplateResponse(request, 'admin/intelligent_prospecting_dashboard.html', context)

@staff_member_required
def domain_analysis_list(request):
    """
    Lista de análisis de dominios con filtros y búsqueda.
    """
    try:
        # Filtros
        industry_filter = request.GET.get('industry', '')
        status_filter = request.GET.get('status', '')
        score_filter = request.GET.get('score', '')
        search_query = request.GET.get('search', '')
        
        # Query base
        domains = DomainAnalysis.objects.all()
        
        # Aplicar filtros
        if industry_filter:
            domains = domains.filter(industry=industry_filter)
        
        if status_filter:
            domains = domains.filter(status=status_filter)
        
        if score_filter:
            if score_filter == 'high':
                domains = domains.filter(prospect_score__gte=70)
            elif score_filter == 'medium':
                domains = domains.filter(prospect_score__gte=40, prospect_score__lt=70)
            elif score_filter == 'low':
                domains = domains.filter(prospect_score__lt=40)
        
        if search_query:
            domains = domains.filter(
                Q(company_name__icontains=search_query) |
                Q(domain__icontains=search_query)
            )
        
        # Ordenar
        domains = domains.order_by('-prospect_score', '-last_contact_date')
        
        # Paginación
        paginator = Paginator(domains, 25)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        # Estadísticas
        stats = {
            'total': domains.count(),
            'high_potential': domains.filter(prospect_score__gte=70).count(),
            'medium_potential': domains.filter(prospect_score__gte=40, prospect_score__lt=70).count(),
            'low_potential': domains.filter(prospect_score__lt=40).count(),
        }
        
        context = {
            'title': 'Análisis de Dominios',
            'page_obj': page_obj,
            'stats': stats,
            'filters': {
                'industry': industry_filter,
                'status': status_filter,
                'score': score_filter,
                'search': search_query
            }
        }
        
        return TemplateResponse(request, 'admin/domain_analysis_list.html', context)
        
    except Exception as e:
        logger.error(f"Error en lista de análisis de dominios: {str(e)}")
        context = {
            'title': 'Análisis de Dominios',
            'error': str(e)
        }
        return TemplateResponse(request, 'admin/domain_analysis_list.html', context)

@staff_member_required
def domain_analysis_detail(request, domain_id):
    """
    Vista detallada de un análisis de dominio específico.
    """
    try:
        domain_analysis = get_object_or_404(DomainAnalysis, id=domain_id)
        
        # Obtener análisis de uso
        usage_analyses = UsageFrequencyAnalysis.objects.filter(
            domain_analysis=domain_analysis
        ).order_by('-analysis_date')
        
        # Obtener esfuerzos de prospección
        prospecting_efforts = IntelligentProspecting.objects.filter(
            domain_analysis=domain_analysis
        ).order_by('-created_at')
        
        # Obtener oportunidades de cross-selling
        cross_sell_opportunities = CrossSellingOpportunity.objects.filter(
            usage_analysis__domain_analysis=domain_analysis
        ).order_by('-priority', '-estimated_value')
        
        # Calcular métricas adicionales
        metrics = {
            'total_scraping_sessions': domain_analysis.scraping_frequency,
            'avg_vacancies_per_session': domain_analysis.total_vacancies_found / max(domain_analysis.scraping_frequency, 1),
            'engagement_score': (float(domain_analysis.email_open_rate) + float(domain_analysis.click_through_rate)) / 2,
            'days_since_last_contact': (timezone.now() - domain_analysis.last_contact_date).days if domain_analysis.last_contact_date else None
        }
        
        context = {
            'title': f'Análisis de {domain_analysis.company_name}',
            'domain_analysis': domain_analysis,
            'usage_analyses': usage_analyses,
            'prospecting_efforts': prospecting_efforts,
            'cross_sell_opportunities': cross_sell_opportunities,
            'metrics': metrics
        }
        
        return TemplateResponse(request, 'admin/domain_analysis_detail.html', context)
        
    except Exception as e:
        logger.error(f"Error en detalle de análisis de dominio: {str(e)}")
        context = {
            'title': 'Análisis de Dominio',
            'error': str(e)
        }
        return TemplateResponse(request, 'admin/domain_analysis_detail.html', context)

@staff_member_required
def cross_selling_opportunities(request):
    """
    Lista de oportunidades de cross-selling.
    """
    try:
        # Filtros
        priority_filter = request.GET.get('priority', '')
        status_filter = request.GET.get('status', '')
        opportunity_type = request.GET.get('type', '')
        search_query = request.GET.get('search', '')
        
        # Query base
        opportunities = CrossSellingOpportunity.objects.select_related(
            'usage_analysis__domain_analysis'
        ).all()
        
        # Aplicar filtros
        if priority_filter:
            opportunities = opportunities.filter(priority=priority_filter)
        
        if status_filter:
            opportunities = opportunities.filter(status=status_filter)
        
        if opportunity_type:
            opportunities = opportunities.filter(opportunity_type=opportunity_type)
        
        if search_query:
            opportunities = opportunities.filter(
                Q(title__icontains=search_query) |
                Q(usage_analysis__domain_analysis__company_name__icontains=search_query)
            )
        
        # Ordenar
        opportunities = opportunities.order_by('-priority', '-estimated_value')
        
        # Paginación
        paginator = Paginator(opportunities, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        # Estadísticas
        stats = {
            'total': opportunities.count(),
            'critical': opportunities.filter(priority='critical').count(),
            'high': opportunities.filter(priority='high').count(),
            'identified': opportunities.filter(status='identified').count(),
            'total_value': opportunities.aggregate(total=Sum('estimated_value'))['total'] or 0
        }
        
        context = {
            'title': 'Oportunidades de Cross-Selling',
            'page_obj': page_obj,
            'stats': stats,
            'filters': {
                'priority': priority_filter,
                'status': status_filter,
                'type': opportunity_type,
                'search': search_query
            }
        }
        
        return TemplateResponse(request, 'admin/cross_selling_opportunities.html', context)
        
    except Exception as e:
        logger.error(f"Error en oportunidades de cross-selling: {str(e)}")
        context = {
            'title': 'Oportunidades de Cross-Selling',
            'error': str(e)
        }
        return TemplateResponse(request, 'admin/cross_selling_opportunities.html', context)

@staff_member_required
def campaign_gantt_view(request, campaign_id):
    """
    Vista del Gantt chart para una campaña específica.
    """
    try:
        campaign = get_object_or_404(MarketingCampaign, id=campaign_id)
        gantt_service = GanttChartService()
        
        # Obtener datos del Gantt
        gantt_data = gantt_service.create_campaign_gantt(campaign_id)
        
        # Obtener timeline
        timeline_data = gantt_service.get_campaign_timeline(campaign_id)
        
        # Obtener fases y tareas
        phases = CampaignExecutionPhase.objects.filter(campaign=campaign).order_by('execution_order')
        tasks = CampaignTask.objects.filter(phase__campaign=campaign).order_by('phase__execution_order', 'task_order')
        milestones = CampaignMilestone.objects.filter(campaign=campaign).order_by('target_date')
        
        context = {
            'title': f'Gantt Chart - {campaign.name}',
            'campaign': campaign,
            'gantt_data': gantt_data.get('gantt_data', {}),
            'timeline_data': timeline_data.get('timeline', {}),
            'phases': phases,
            'tasks': tasks,
            'milestones': milestones,
            'summary': gantt_data.get('summary', {})
        }
        
        return TemplateResponse(request, 'admin/campaign_gantt_view.html', context)
        
    except Exception as e:
        logger.error(f"Error en vista Gantt de campaña: {str(e)}")
        context = {
            'title': 'Gantt Chart de Campaña',
            'error': str(e)
        }
        return TemplateResponse(request, 'admin/campaign_gantt_view.html', context)

@staff_member_required
def gantt_dashboard(request):
    """
    Dashboard general de Gantt charts para todas las campañas.
    """
    try:
        # Obtener campañas activas
        active_campaigns = MarketingCampaign.objects.filter(
            status='active'
        ).order_by('-created_at')
        
        # Obtener vistas Gantt guardadas
        saved_views = CampaignGanttView.objects.filter(
            created_by=request.user
        ).order_by('-created_at')
        
        # Estadísticas generales
        total_campaigns = MarketingCampaign.objects.count()
        active_campaigns_count = active_campaigns.count()
        completed_campaigns = MarketingCampaign.objects.filter(status='completed').count()
        
        # Campañas con retrasos
        delayed_campaigns = []
        for campaign in active_campaigns:
            phases = CampaignExecutionPhase.objects.filter(campaign=campaign)
            delayed_phases = [p for p in phases if p.is_delayed()]
            if delayed_phases:
                delayed_campaigns.append({
                    'campaign': campaign,
                    'delayed_phases': len(delayed_phases)
                })
        
        context = {
            'title': 'Dashboard de Gantt Charts',
            'active_campaigns': active_campaigns,
            'saved_views': saved_views,
            'stats': {
                'total_campaigns': total_campaigns,
                'active_campaigns': active_campaigns_count,
                'completed_campaigns': completed_campaigns,
                'delayed_campaigns': len(delayed_campaigns)
            },
            'delayed_campaigns': delayed_campaigns
        }
        
        return TemplateResponse(request, 'admin/gantt_dashboard.html', context)
        
    except Exception as e:
        logger.error(f"Error en dashboard de Gantt: {str(e)}")
        context = {
            'title': 'Dashboard de Gantt Charts',
            'error': str(e)
        }
        return TemplateResponse(request, 'admin/gantt_dashboard.html', context)

# ===== VISTAS AJAX =====

@staff_member_required
def update_task_progress_ajax(request):
    """
    Actualiza el progreso de una tarea vía AJAX.
    """
    try:
        if request.method == 'POST':
            task_id = request.POST.get('task_id')
            progress = float(request.POST.get('progress', 0))
            status = request.POST.get('status')
            
            gantt_service = GanttChartService()
            result = gantt_service.update_task_progress(task_id, progress, status)
            
            return JsonResponse(result)
        
        return JsonResponse({'success': False, 'error': 'Método no permitido'})
        
    except Exception as e:
        logger.error(f"Error actualizando progreso de tarea: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})

@staff_member_required
def get_campaign_timeline_ajax(request):
    """
    Obtiene timeline de campaña vía AJAX.
    """
    try:
        campaign_id = request.GET.get('campaign_id')
        
        if not campaign_id:
            return JsonResponse({'success': False, 'error': 'ID de campaña requerido'})
        
        gantt_service = GanttChartService()
        result = gantt_service.get_campaign_timeline(campaign_id)
        
        return JsonResponse(result)
        
    except Exception as e:
        logger.error(f"Error obteniendo timeline: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})

@staff_member_required
def analyze_domains_ajax(request):
    """
    Ejecuta análisis de dominios vía AJAX.
    """
    try:
        business_unit = request.POST.get('business_unit')
        
        prospecting_service = IntelligentProspectingService()
        result = prospecting_service.analyze_domains_for_prospecting(business_unit)
        
        return JsonResponse(result)
        
    except Exception as e:
        logger.error(f"Error analizando dominios: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})

@staff_member_required
def analyze_usage_ajax(request):
    """
    Ejecuta análisis de uso vía AJAX.
    """
    try:
        business_unit = request.POST.get('business_unit')
        
        prospecting_service = IntelligentProspectingService()
        result = prospecting_service.analyze_usage_for_cross_selling(business_unit)
        
        return JsonResponse(result)
        
    except Exception as e:
        logger.error(f"Error analizando uso: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})

@staff_member_required
def generate_campaigns_ajax(request):
    """
    Genera campañas inteligentes vía AJAX.
    """
    try:
        target_type = request.POST.get('target_type', 'mixed')
        
        prospecting_service = IntelligentProspectingService()
        result = prospecting_service.generate_intelligent_campaigns(target_type)
        
        return JsonResponse(result)
        
    except Exception as e:
        logger.error(f"Error generando campañas: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})

@staff_member_required
def get_dashboard_data_ajax(request):
    """
    Obtiene datos del dashboard vía AJAX.
    """
    try:
        prospecting_service = IntelligentProspectingService()
        result = prospecting_service.get_prospecting_dashboard_data()
        
        return JsonResponse(result)
        
    except Exception as e:
        logger.error(f"Error obteniendo datos del dashboard: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})

# ===== VISTAS DE ACCIONES =====

@staff_member_required
def create_prospecting_opportunity(request, domain_id):
    """
    Crea una oportunidad de prospección para un dominio.
    """
    try:
        domain_analysis = get_object_or_404(DomainAnalysis, id=domain_id)
        
        if request.method == 'POST':
            # Crear oportunidad de prospección
            prospecting = IntelligentProspecting.objects.create(
                domain_analysis=domain_analysis,
                assigned_to=request.user,
                status='research',
                priority=request.POST.get('priority', 'medium'),
                estimated_value=request.POST.get('estimated_value', 0)
            )
            
            return redirect('admin:domain_analysis_detail', domain_id=domain_id)
        
        context = {
            'title': f'Crear Oportunidad de Prospección - {domain_analysis.company_name}',
            'domain_analysis': domain_analysis
        }
        
        return TemplateResponse(request, 'admin/create_prospecting_opportunity.html', context)
        
    except Exception as e:
        logger.error(f"Error creando oportunidad de prospección: {str(e)}")
        return redirect('admin:domain_analysis_list')

@staff_member_required
def create_cross_sell_opportunity(request, usage_analysis_id):
    """
    Crea una oportunidad de cross-selling para un análisis de uso.
    """
    try:
        usage_analysis = get_object_or_404(UsageFrequencyAnalysis, id=usage_analysis_id)
        
        if request.method == 'POST':
            # Crear oportunidad de cross-selling
            cross_sell = CrossSellingOpportunity.objects.create(
                usage_analysis=usage_analysis,
                opportunity_type=request.POST.get('opportunity_type'),
                title=request.POST.get('title'),
                description=request.POST.get('description'),
                priority=request.POST.get('priority', 'medium'),
                estimated_value=request.POST.get('estimated_value', 0)
            )
            
            return redirect('admin:cross_selling_opportunities')
        
        context = {
            'title': f'Crear Oportunidad de Cross-Selling - {usage_analysis.domain_analysis.company_name}',
            'usage_analysis': usage_analysis
        }
        
        return TemplateResponse(request, 'admin/create_cross_sell_opportunity.html', context)
        
    except Exception as e:
        logger.error(f"Error creando oportunidad de cross-selling: {str(e)}")
        return redirect('admin:cross_selling_opportunities')

@staff_member_required
def export_gantt_data(request, campaign_id):
    """
    Exporta datos del Gantt chart en formato JSON.
    """
    try:
        campaign = get_object_or_404(MarketingCampaign, id=campaign_id)
        gantt_service = GanttChartService()
        
        gantt_data = gantt_service.create_campaign_gantt(campaign_id)
        
        response = JsonResponse(gantt_data, safe=False)
        response['Content-Disposition'] = f'attachment; filename="gantt_{campaign.name}_{timezone.now().date()}.json"'
        
        return response
        
    except Exception as e:
        logger.error(f"Error exportando datos Gantt: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}) 