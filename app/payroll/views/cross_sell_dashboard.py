"""
Dashboard de Venta Cruzada - huntRED® Payroll
Muestra oportunidades de ATS y AURA para clientes de Payroll
"""

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import json
from ..models import Company, Employee
from ..services.cross_sell_service import CrossSellService
from ..services.pricing_service import PricingService


@login_required
def cross_sell_dashboard(request):
    """
    Dashboard principal de venta cruzada
    """
    companies = Company.objects.all()
    
    # Obtener estadísticas generales
    total_companies = companies.count()
    payroll_only_companies = sum(1 for c in companies if not c.has_ats and not c.has_aura)
    ats_companies = sum(1 for c in companies if c.has_ats)
    aura_companies = sum(1 for c in companies if c.has_aura)
    bundle_companies = sum(1 for c in companies if c.has_ats and c.has_aura)
    
    # Calcular oportunidades totales
    cross_sell_service = CrossSellService()
    total_opportunities = 0
    total_potential_value = 0
    
    for company in companies:
        opportunities = cross_sell_service.get_cross_sell_opportunities(company)
        total_opportunities += len(opportunities.get('recommendations', []))
        total_potential_value += cross_sell_service._calculate_total_potential_value(opportunities)
    
    context = {
        'page_title': 'Dashboard de Venta Cruzada - huntRED® Payroll',
        'active_tab': 'cross_sell',
        'stats': {
            'total_companies': total_companies,
            'payroll_only': payroll_only_companies,
            'ats_companies': ats_companies,
            'aura_companies': aura_companies,
            'bundle_companies': bundle_companies,
            'total_opportunities': total_opportunities,
            'total_potential_value': total_potential_value
        },
        'companies': companies[:10]  # Mostrar solo las primeras 10 para el dashboard
    }
    
    return render(request, 'payroll/cross_sell_dashboard.html', context)


@login_required
def company_cross_sell_analysis(request, company_id):
    """
    Análisis detallado de venta cruzada para una empresa específica
    """
    company = get_object_or_404(Company, id=company_id)
    cross_sell_service = CrossSellService(company)
    
    # Obtener oportunidades de venta cruzada
    opportunities = cross_sell_service.get_cross_sell_opportunities(company)
    
    # Crear propuesta de venta cruzada
    proposal = cross_sell_service.create_cross_sell_proposal(company, opportunities)
    
    # Obtener datos de pricing actual
    pricing_service = PricingService(company)
    current_pricing = pricing_service.calculate_company_pricing(
        employees=company.employees.count(),
        plan=company.payroll_plan or 'professional'
    )
    
    context = {
        'page_title': f'Análisis de Venta Cruzada - {company.name}',
        'active_tab': 'cross_sell',
        'company': company,
        'opportunities': opportunities,
        'proposal': proposal,
        'current_pricing': current_pricing,
        'employee_count': company.employees.count()
    }
    
    return render(request, 'payroll/company_cross_sell_analysis.html', context)


@login_required
def cross_sell_opportunities_list(request):
    """
    Lista de todas las oportunidades de venta cruzada
    """
    companies = Company.objects.all()
    cross_sell_service = CrossSellService()
    
    opportunities_list = []
    
    for company in companies:
        opportunities = cross_sell_service.get_cross_sell_opportunities(company)
        recommendations = opportunities.get('recommendations', [])
        
        for recommendation in recommendations:
            opportunities_list.append({
                'company': company,
                'recommendation': recommendation,
                'priority': recommendation.get('priority', 'medium'),
                'estimated_value': recommendation.get('estimated_roi', 0) * 100
            })
    
    # Ordenar por prioridad y valor estimado
    opportunities_list.sort(key=lambda x: (
        {'high': 3, 'medium': 2, 'low': 1}[x['priority']], 
        x['estimated_value']
    ), reverse=True)
    
    context = {
        'page_title': 'Oportunidades de Venta Cruzada',
        'active_tab': 'cross_sell',
        'opportunities': opportunities_list,
        'total_opportunities': len(opportunities_list)
    }
    
    return render(request, 'payroll/cross_sell_opportunities_list.html', context)


@login_required
def bundle_proposals(request):
    """
    Propuestas de bundles integrados
    """
    companies = Company.objects.all()
    cross_sell_service = CrossSellService()
    
    bundle_proposals_list = []
    
    for company in companies:
        opportunities = cross_sell_service.get_cross_sell_opportunities(company)
        bundles = opportunities.get('bundle_opportunities', {})
        
        for bundle_key, bundle_data in bundles.items():
            if bundle_data.get('priority') == 'high':
                bundle_proposals_list.append({
                    'company': company,
                    'bundle': bundle_data,
                    'employee_count': company.employees.count(),
                    'current_plan': company.payroll_plan
                })
    
    # Ordenar por valor del bundle
    bundle_proposals_list.sort(key=lambda x: x['bundle']['bundle_price'], reverse=True)
    
    context = {
        'page_title': 'Propuestas de Bundles',
        'active_tab': 'cross_sell',
        'bundles': bundle_proposals_list,
        'total_bundles': len(bundle_proposals_list)
    }
    
    return render(request, 'payroll/bundle_proposals.html', context)


@csrf_exempt
def generate_cross_sell_proposal(request, company_id):
    """
    Genera una propuesta de venta cruzada en PDF
    """
    if request.method == 'POST':
        company = get_object_or_404(Company, id=company_id)
        cross_sell_service = CrossSellService(company)
        
        # Obtener datos del formulario
        data = json.loads(request.body)
        selected_services = data.get('selected_services', [])
        custom_discount = data.get('custom_discount', 0)
        
        # Obtener oportunidades
        opportunities = cross_sell_service.get_cross_sell_opportunities(company)
        
        # Crear propuesta personalizada
        proposal = cross_sell_service.create_cross_sell_proposal(company, opportunities)
        
        # Aplicar descuento personalizado si se especifica
        if custom_discount > 0:
            for service_type in selected_services:
                if service_type in proposal['opportunities']:
                    for opportunity in proposal['opportunities'][service_type].values():
                        if 'estimated_value' in opportunity:
                            opportunity['estimated_value'] *= (1 - custom_discount / 100)
        
        # Aquí se generaría el PDF (implementación futura)
        # pdf_url = generate_pdf_proposal(proposal)
        
        result = {
            'success': True,
            'proposal': proposal,
            'selected_services': selected_services,
            'custom_discount': custom_discount,
            'pdf_url': '/media/proposals/cross_sell_proposal.pdf'  # Placeholder
        }
        
        return JsonResponse(result)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)


@login_required
def cross_sell_analytics(request):
    """
    Analytics de venta cruzada
    """
    companies = Company.objects.all()
    cross_sell_service = CrossSellService()
    
    # Estadísticas por industria
    industry_stats = {}
    service_adoption = {
        'payroll_only': 0,
        'payroll_ats': 0,
        'payroll_aura': 0,
        'complete_bundle': 0
    }
    
    total_potential_value = 0
    conversion_rates = {
        'ats': 0,
        'aura': 0,
        'bundles': 0
    }
    
    for company in companies:
        # Estadísticas por industria
        industry = company.industry or 'Sin especificar'
        if industry not in industry_stats:
            industry_stats[industry] = {
                'companies': 0,
                'total_employees': 0,
                'potential_value': 0
            }
        
        industry_stats[industry]['companies'] += 1
        industry_stats[industry]['total_employees'] += company.employees.count()
        
        # Oportunidades por empresa
        opportunities = cross_sell_service.get_cross_sell_opportunities(company)
        potential_value = cross_sell_service._calculate_total_potential_value(opportunities)
        industry_stats[industry]['potential_value'] += potential_value
        total_potential_value += potential_value
        
        # Adopción de servicios
        if company.has_ats and company.has_aura:
            service_adoption['complete_bundle'] += 1
        elif company.has_ats:
            service_adoption['payroll_ats'] += 1
        elif company.has_aura:
            service_adoption['payroll_aura'] += 1
        else:
            service_adoption['payroll_only'] += 1
    
    # Calcular tasas de conversión
    total_companies = companies.count()
    if total_companies > 0:
        conversion_rates['ats'] = (service_adoption['payroll_ats'] + service_adoption['complete_bundle']) / total_companies
        conversion_rates['aura'] = (service_adoption['payroll_aura'] + service_adoption['complete_bundle']) / total_companies
        conversion_rates['bundles'] = service_adoption['complete_bundle'] / total_companies
    
    context = {
        'page_title': 'Analytics de Venta Cruzada',
        'active_tab': 'cross_sell',
        'industry_stats': industry_stats,
        'service_adoption': service_adoption,
        'total_potential_value': total_potential_value,
        'conversion_rates': conversion_rates,
        'total_companies': total_companies
    }
    
    return render(request, 'payroll/cross_sell_analytics.html', context)


@login_required
def cross_sell_recommendations(request):
    """
    Recomendaciones personalizadas de venta cruzada
    """
    companies = Company.objects.all()
    cross_sell_service = CrossSellService()
    
    recommendations_by_priority = {
        'high': [],
        'medium': [],
        'low': []
    }
    
    for company in companies:
        opportunities = cross_sell_service.get_cross_sell_opportunities(company)
        recommendations = opportunities.get('recommendations', [])
        
        for recommendation in recommendations:
            priority = recommendation.get('priority', 'medium')
            recommendations_by_priority[priority].append({
                'company': company,
                'recommendation': recommendation
            })
    
    context = {
        'page_title': 'Recomendaciones de Venta Cruzada',
        'active_tab': 'cross_sell',
        'recommendations': recommendations_by_priority,
        'total_high_priority': len(recommendations_by_priority['high']),
        'total_medium_priority': len(recommendations_by_priority['medium']),
        'total_low_priority': len(recommendations_by_priority['low'])
    }
    
    return render(request, 'payroll/cross_sell_recommendations.html', context) 