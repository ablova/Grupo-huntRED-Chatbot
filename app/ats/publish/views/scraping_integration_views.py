"""
Vistas para integración de scraping con ML y sistema de publicación.
"""
import json
import logging
from typing import Dict, Any
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Q

from app.ats.publish.services.scraping_integration_service import ScrapingIntegrationService
from app.ats.publish.services.intelligent_prospecting_service import IntelligentProspectingService
from app.ats.publish.models import (
    DomainAnalysis, UsageFrequencyAnalysis, IntelligentProspecting,
    CrossSellingOpportunity, MarketingCampaign
)

logger = logging.getLogger(__name__)

@staff_member_required
def scraping_integration_dashboard(request):
    """
    Dashboard principal de integración de scraping con ML.
    """
    try:
        business_unit = request.GET.get('business_unit')
        
        # Obtener estadísticas generales
        stats = {
            'total_domains': DomainAnalysis.objects.count(),
            'active_campaigns': MarketingCampaign.objects.filter(status='active').count(),
            'pending_opportunities': CrossSellingOpportunity.objects.filter(status='pending').count(),
            'high_value_domains': DomainAnalysis.objects.filter(potential_score__gte=0.8).count()
        }
        
        # Obtener dominios de alto valor
        high_value_domains = DomainAnalysis.objects.filter(
            potential_score__gte=0.7
        ).order_by('-potential_score')[:10]
        
        # Obtener campañas activas
        active_campaigns = MarketingCampaign.objects.filter(
            status='active'
        ).order_by('-created_at')[:5]
        
        # Obtener oportunidades de cross-selling
        cross_selling_opportunities = CrossSellingOpportunity.objects.filter(
            status='pending'
        ).order_by('-potential_value')[:5]
        
        context = {
            'stats': stats,
            'high_value_domains': high_value_domains,
            'active_campaigns': active_campaigns,
            'cross_selling_opportunities': cross_selling_opportunities,
            'business_unit': business_unit
        }
        
        return render(request, 'admin/scraping_integration_dashboard.html', context)
        
    except Exception as e:
        logger.error(f"Error en dashboard de integración: {str(e)}")
        return render(request, 'admin/error.html', {'error': str(e)})

@staff_member_required
@csrf_exempt
@require_http_methods(["POST"])
def analyze_and_generate_campaigns(request):
    """
    Analiza datos de scraping y genera campañas inteligentes.
    """
    try:
        data = json.loads(request.body)
        business_unit = data.get('business_unit')
        
        service = ScrapingIntegrationService()
        result = await service.analyze_and_generate_campaigns(business_unit)
        
        if result['success']:
            # Guardar campañas generadas
            campaigns_created = []
            for campaign_data in result['generated_campaigns']:
                campaign = MarketingCampaign.objects.create(
                    name=campaign_data['name'],
                    campaign_type=campaign_data['type'],
                    business_unit=campaign_data.get('business_unit', 'general'),
                    priority=campaign_data['priority'],
                    budget=campaign_data['budget'],
                    duration_days=campaign_data['duration_days'],
                    channels=campaign_data['channels'],
                    objectives=campaign_data['objectives'],
                    ml_recommendations=campaign_data['ml_recommendations'],
                    status='planning'
                )
                campaigns_created.append(campaign.id)
            
            return JsonResponse({
                'success': True,
                'message': f'Se generaron {len(campaigns_created)} campañas inteligentes',
                'campaigns_created': campaigns_created,
                'analysis': result
            })
        else:
            return JsonResponse({
                'success': False,
                'error': result['error']
            })
            
    except Exception as e:
        logger.error(f"Error analizando y generando campañas: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@staff_member_required
@csrf_exempt
@require_http_methods(["POST"])
def predict_domain_opportunities(request):
    """
    Predice oportunidades para un dominio específico.
    """
    try:
        data = json.loads(request.body)
        domain = data.get('domain')
        
        if not domain:
            return JsonResponse({
                'success': False,
                'error': 'Dominio requerido'
            })
        
        service = ScrapingIntegrationService()
        result = await service.predict_domain_opportunities(domain)
        
        return JsonResponse(result)
        
    except Exception as e:
        logger.error(f"Error prediciendo oportunidades: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@staff_member_required
@csrf_exempt
@require_http_methods(["POST"])
def optimize_publishing_strategy(request):
    """
    Optimiza la estrategia de publicación basada en datos de scraping.
    """
    try:
        data = json.loads(request.body)
        business_unit = data.get('business_unit')
        
        service = ScrapingIntegrationService()
        result = await service.optimize_publishing_strategy(business_unit)
        
        return JsonResponse(result)
        
    except Exception as e:
        logger.error(f"Error optimizando estrategia: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@staff_member_required
@csrf_exempt
@require_http_methods(["POST"])
def generate_ml_insights(request):
    """
    Genera insights de ML basados en datos de scraping.
    """
    try:
        data = json.loads(request.body)
        business_unit = data.get('business_unit')
        
        service = ScrapingIntegrationService()
        result = await service.generate_ml_insights(business_unit)
        
        return JsonResponse(result)
        
    except Exception as e:
        logger.error(f"Error generando insights de ML: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@staff_member_required
def domain_analysis_list(request):
    """
    Lista de análisis de dominios con filtros.
    """
    try:
        # Filtros
        business_unit = request.GET.get('business_unit')
        min_potential = request.GET.get('min_potential')
        max_potential = request.GET.get('max_potential')
        search = request.GET.get('search')
        
        # Query base
        queryset = DomainAnalysis.objects.all()
        
        # Aplicar filtros
        if business_unit:
            queryset = queryset.filter(business_unit=business_unit)
        
        if min_potential:
            queryset = queryset.filter(potential_score__gte=float(min_potential))
        
        if max_potential:
            queryset = queryset.filter(potential_score__lte=float(max_potential))
        
        if search:
            queryset = queryset.filter(
                Q(domain__icontains=search) |
                Q(company__icontains=search) |
                Q(industry__icontains=search)
            )
        
        # Ordenar
        queryset = queryset.order_by('-potential_score', '-last_updated')
        
        # Paginación
        paginator = Paginator(queryset, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {
            'page_obj': page_obj,
            'business_unit': business_unit,
            'min_potential': min_potential,
            'max_potential': max_potential,
            'search': search
        }
        
        return render(request, 'admin/domain_analysis_list.html', context)
        
    except Exception as e:
        logger.error(f"Error en lista de análisis de dominios: {str(e)}")
        return render(request, 'admin/error.html', {'error': str(e)})

@staff_member_required
def usage_frequency_analysis(request):
    """
    Análisis de frecuencia de uso.
    """
    try:
        # Filtros
        business_unit = request.GET.get('business_unit')
        frequency_type = request.GET.get('frequency_type')  # high, medium, low
        
        # Query base
        queryset = UsageFrequencyAnalysis.objects.all()
        
        # Aplicar filtros
        if business_unit:
            queryset = queryset.filter(business_unit=business_unit)
        
        if frequency_type:
            if frequency_type == 'high':
                queryset = queryset.filter(usage_frequency__gte=0.7)
            elif frequency_type == 'medium':
                queryset = queryset.filter(
                    usage_frequency__gte=0.3,
                    usage_frequency__lt=0.7
                )
            elif frequency_type == 'low':
                queryset = queryset.filter(usage_frequency__lt=0.3)
        
        # Ordenar
        queryset = queryset.order_by('-usage_frequency', '-last_updated')
        
        # Paginación
        paginator = Paginator(queryset, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {
            'page_obj': page_obj,
            'business_unit': business_unit,
            'frequency_type': frequency_type
        }
        
        return render(request, 'admin/usage_frequency_analysis.html', context)
        
    except Exception as e:
        logger.error(f"Error en análisis de frecuencia: {str(e)}")
        return render(request, 'admin/error.html', {'error': str(e)})

@staff_member_required
def cross_selling_opportunities(request):
    """
    Oportunidades de cross-selling.
    """
    try:
        # Filtros
        business_unit = request.GET.get('business_unit')
        status = request.GET.get('status')
        min_value = request.GET.get('min_value')
        
        # Query base
        queryset = CrossSellingOpportunity.objects.all()
        
        # Aplicar filtros
        if business_unit:
            queryset = queryset.filter(business_unit=business_unit)
        
        if status:
            queryset = queryset.filter(status=status)
        
        if min_value:
            queryset = queryset.filter(potential_value__gte=float(min_value))
        
        # Ordenar
        queryset = queryset.order_by('-potential_value', '-created_at')
        
        # Paginación
        paginator = Paginator(queryset, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {
            'page_obj': page_obj,
            'business_unit': business_unit,
            'status': status,
            'min_value': min_value
        }
        
        return render(request, 'admin/cross_selling_opportunities.html', context)
        
    except Exception as e:
        logger.error(f"Error en oportunidades de cross-selling: {str(e)}")
        return render(request, 'admin/error.html', {'error': str(e)})

@staff_member_required
@csrf_exempt
@require_http_methods(["POST"])
def update_opportunity_status(request):
    """
    Actualiza el estado de una oportunidad de cross-selling.
    """
    try:
        data = json.loads(request.body)
        opportunity_id = data.get('opportunity_id')
        new_status = data.get('status')
        notes = data.get('notes', '')
        
        if not opportunity_id or not new_status:
            return JsonResponse({
                'success': False,
                'error': 'ID de oportunidad y estado requeridos'
            })
        
        opportunity = CrossSellingOpportunity.objects.get(id=opportunity_id)
        opportunity.status = new_status
        if notes:
            opportunity.notes = notes
        opportunity.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Estado actualizado exitosamente'
        })
        
    except CrossSellingOpportunity.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Oportunidad no encontrada'
        })
    except Exception as e:
        logger.error(f"Error actualizando estado de oportunidad: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@staff_member_required
def ml_insights_dashboard(request):
    """
    Dashboard de insights de ML.
    """
    try:
        business_unit = request.GET.get('business_unit')
        
        # Obtener insights recientes
        recent_insights = {
            'aura_insights': [],
            'predictive_insights': [],
            'segmentation_insights': [],
            'trend_insights': []
        }
        
        # Simular datos de insights (en producción vendrían del servicio)
        service = ScrapingIntegrationService()
        ml_insights = await service.generate_ml_insights(business_unit)
        
        if ml_insights['success']:
            recent_insights = ml_insights
        
        context = {
            'recent_insights': recent_insights,
            'business_unit': business_unit
        }
        
        return render(request, 'admin/ml_insights_dashboard.html', context)
        
    except Exception as e:
        logger.error(f"Error en dashboard de insights de ML: {str(e)}")
        return render(request, 'admin/error.html', {'error': str(e)})

@staff_member_required
@csrf_exempt
@require_http_methods(["POST"])
def export_analysis_data(request):
    """
    Exporta datos de análisis en formato JSON.
    """
    try:
        data = json.loads(request.body)
        analysis_type = data.get('analysis_type')  # domain, usage, cross_selling
        business_unit = data.get('business_unit')
        date_from = data.get('date_from')
        date_to = data.get('date_to')
        
        # Construir query según tipo de análisis
        if analysis_type == 'domain':
            queryset = DomainAnalysis.objects.all()
        elif analysis_type == 'usage':
            queryset = UsageFrequencyAnalysis.objects.all()
        elif analysis_type == 'cross_selling':
            queryset = CrossSellingOpportunity.objects.all()
        else:
            return JsonResponse({
                'success': False,
                'error': 'Tipo de análisis no válido'
            })
        
        # Aplicar filtros
        if business_unit:
            queryset = queryset.filter(business_unit=business_unit)
        
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)
        
        # Serializar datos
        export_data = []
        for obj in queryset:
            export_data.append({
                'id': obj.id,
                'created_at': obj.created_at.isoformat(),
                'updated_at': obj.updated_at.isoformat(),
                **{field.name: getattr(obj, field.name) 
                   for field in obj._meta.fields 
                   if field.name not in ['id', 'created_at', 'updated_at']}
            })
        
        return JsonResponse({
            'success': True,
            'data': export_data,
            'total_records': len(export_data)
        })
        
    except Exception as e:
        logger.error(f"Error exportando datos: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@staff_member_required
def real_time_analytics(request):
    """
    Analytics en tiempo real del sistema de scraping.
    """
    try:
        # Obtener métricas en tiempo real
        real_time_stats = {
            'active_scraping_sessions': 0,  # Esto vendría de un sistema de monitoreo
            'domains_scraped_today': 0,
            'vacancies_found_today': 0,
            'success_rate_today': 0.0,
            'ml_predictions_accuracy': 0.0
        }
        
        # Obtener actividad reciente
        recent_activity = []
        
        # Obtener alertas
        alerts = []
        
        context = {
            'real_time_stats': real_time_stats,
            'recent_activity': recent_activity,
            'alerts': alerts
        }
        
        return render(request, 'admin/real_time_analytics.html', context)
        
    except Exception as e:
        logger.error(f"Error en analytics en tiempo real: {str(e)}")
        return render(request, 'admin/error.html', {'error': str(e)})

@staff_member_required
@csrf_exempt
@require_http_methods(["POST"])
def generate_campaign_from_insights(request):
    """
    Genera una campaña específica basada en insights de ML.
    """
    try:
        data = json.loads(request.body)
        insight_type = data.get('insight_type')  # aura, predictive, segmentation, trend
        target_domains = data.get('target_domains', [])
        campaign_name = data.get('campaign_name')
        business_unit = data.get('business_unit')
        
        if not insight_type or not campaign_name:
            return JsonResponse({
                'success': False,
                'error': 'Tipo de insight y nombre de campaña requeridos'
            })
        
        # Generar campaña basada en insight
        service = ScrapingIntegrationService()
        
        # Obtener insights específicos
        ml_insights = await service.generate_ml_insights(business_unit)
        
        if not ml_insights['success']:
            return JsonResponse({
                'success': False,
                'error': 'Error obteniendo insights de ML'
            })
        
        # Crear campaña basada en insight
        campaign_data = {
            'name': campaign_name,
            'campaign_type': f'ml_{insight_type}',
            'business_unit': business_unit or 'general',
            'priority': 'medium',
            'budget': 10000,  # Presupuesto base
            'duration_days': 30,
            'channels': ['email', 'linkedin'],
            'objectives': [f'Leverage {insight_type} insights'],
            'ml_recommendations': ml_insights.get(f'{insight_type}_insights', []),
            'target_domains': target_domains
        }
        
        # Crear campaña
        campaign = MarketingCampaign.objects.create(
            name=campaign_data['name'],
            campaign_type=campaign_data['campaign_type'],
            business_unit=campaign_data['business_unit'],
            priority=campaign_data['priority'],
            budget=campaign_data['budget'],
            duration_days=campaign_data['duration_days'],
            channels=campaign_data['channels'],
            objectives=campaign_data['objectives'],
            ml_recommendations=campaign_data['ml_recommendations'],
            status='planning'
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Campaña generada exitosamente',
            'campaign_id': campaign.id
        })
        
    except Exception as e:
        logger.error(f"Error generando campaña desde insights: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }) 