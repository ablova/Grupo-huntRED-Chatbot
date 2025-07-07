"""
Dashboard de Pricing - huntRED® Payroll
Muestra precios base, costos, márgenes y calculadora de precios
"""

from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import json
from decimal import Decimal
from ..models import Company, Employee, PayrollPlan
from ..services.pricing_service import PricingService
from ..services.compliance_automation_service import ComplianceAutomationService
from ..services.predictive_analytics_service import PredictiveAnalyticsService
from ..services.workflow_automation_service import WorkflowAutomationService


@login_required
def pricing_dashboard(request):
    """
    Dashboard principal de pricing con calculadora y análisis de costos
    """
    context = {
        'page_title': 'Dashboard de Pricing - huntRED® Payroll',
        'active_tab': 'pricing',
        'pricing_data': get_pricing_overview(),
        'cost_breakdown': get_cost_breakdown(),
        'competitive_analysis': get_competitive_analysis(),
        'profitability_analysis': get_profitability_analysis(),
        'revenue_projection': get_revenue_projection()
    }
    
    return render(request, 'payroll/pricing_dashboard.html', context)


def get_pricing_overview():
    """
    Obtiene el resumen de precios por plan
    """
    from .. import PAYROLL_PRICING, PREMIUM_SERVICES, AI_SERVICES
    
    pricing_overview = {
        'plans': {},
        'premium_services': {},
        'ai_services': {},
        'implementation': {}
    }
    
    # Planes principales
    for plan_name, plan_data in PAYROLL_PRICING.items():
        pricing_overview['plans'][plan_name] = {
            'price_per_employee': plan_data['price_per_employee'],
            'setup_fee': plan_data['setup_fee'],
            'monthly_base_fee': plan_data['monthly_base_fee'],
            'min_employees': plan_data['min_employees'],
            'max_employees': plan_data['max_employees'],
            'profit_margin': plan_data['profit_margin'],
            'break_even_employees': plan_data['break_even_employees'],
            'features_count': len(plan_data['features']),
            'target_market': plan_data['target_market']
        }
    
    # Servicios premium
    for service_name, service_data in PREMIUM_SERVICES.items():
        pricing_overview['premium_services'][service_name] = {
            'price': service_data.get('price_per_employee', service_data.get('fee_percentage', service_data.get('fee_per_receipt', service_data.get('fee_per_transaction')))),
            'profit_margin': service_data.get('profit_margin', 0.80),
            'target_market': service_data.get('target_market', 'General')
        }
    
    # Servicios de IA
    for service_name, service_data in AI_SERVICES.items():
        pricing_overview['ai_services'][service_name] = {
            'price_per_employee': service_data['price_per_employee'],
            'profit_margin': service_data['profit_margin'],
            'features_count': len(service_data['features'])
        }
    
    return pricing_overview


def get_cost_breakdown():
    """
    Obtiene el desglose de costos por empresa
    """
    from .. import COST_BREAKDOWN
    
    return {
        'infrastructure': COST_BREAKDOWN['infrastructure_per_company'],
        'setup_costs': COST_BREAKDOWN['setup_costs'],
        'profit_margins': COST_BREAKDOWN['profit_margins'],
        'monthly_breakdown': {
            'whatsapp_bot': 300.00,
            'ai_servers': 400.00,
            'compliance_automation': 200.00,
            'support': 150.00,
            'backup_storage': 100.00,
            'total': 1150.00
        }
    }


def get_competitive_analysis():
    """
    Análisis competitivo vs otros proveedores
    """
    competitors = {
        'runa': {
            'price_per_employee': 45.00,  # USD
            'setup_fee': 0,
            'features': ['basic_payroll', 'basic_reports'],
            'our_advantage': 'WhatsApp + IA + Compliance automático'
        },
        'worky': {
            'price_per_employee': 38.00,  # USD
            'setup_fee': 1000,
            'features': ['payroll', 'hr_management'],
            'our_advantage': 'Analytics predictivo + Workflow automation'
        },
        'contpaqi': {
            'price_per_employee': 25.00,  # USD
            'setup_fee': 5000,
            'features': ['accounting', 'payroll'],
            'our_advantage': 'IA avanzada + Multi-país + WhatsApp'
        },
        'aspel_noi': {
            'price_per_employee': 20.00,  # USD
            'setup_fee': 3000,
            'features': ['payroll', 'basic_reports'],
            'our_advantage': 'Compliance automático + Analytics + Workflows'
        }
    }
    
    return competitors


def get_profitability_analysis():
    """
    Análisis de rentabilidad por plan
    """
    from .. import PAYROLL_PRICING, COST_BREAKDOWN
    
    profitability = {}
    
    for plan_name, plan_data in PAYROLL_PRICING.items():
        # Costos mensuales base
        monthly_costs = COST_BREAKDOWN['infrastructure_per_company']['total_monthly']
        
        # Ingresos por empleado
        revenue_per_employee = plan_data['price_per_employee']
        
        # Break even point
        break_even = plan_data['break_even_employees']
        
        # Margen de contribución
        contribution_margin = revenue_per_employee * 0.75  # Estimado
        
        profitability[plan_name] = {
            'monthly_costs': monthly_costs,
            'revenue_per_employee': revenue_per_employee,
            'break_even_employees': break_even,
            'contribution_margin': contribution_margin,
            'profit_margin': plan_data['profit_margin'],
            'monthly_profit_at_break_even': (revenue_per_employee * break_even) - monthly_costs
        }
    
    return profitability


def get_revenue_projection():
    """
    Proyección de ingresos por diferentes escenarios
    """
    scenarios = {
        'conservative': {
            'companies_month_1': 5,
            'companies_month_6': 25,
            'companies_month_12': 50,
            'avg_employees_per_company': 75,
            'avg_plan': 'professional',
            'avg_monthly_revenue_per_company': 2100,  # USD
            'projected_annual_revenue': 1260000  # USD
        },
        'moderate': {
            'companies_month_1': 10,
            'companies_month_6': 50,
            'companies_month_12': 100,
            'avg_employees_per_company': 100,
            'avg_plan': 'professional',
            'avg_monthly_revenue_per_company': 2800,  # USD
            'projected_annual_revenue': 3360000  # USD
        },
        'aggressive': {
            'companies_month_1': 20,
            'companies_month_6': 100,
            'companies_month_12': 200,
            'avg_employees_per_company': 125,
            'avg_plan': 'professional',
            'avg_monthly_revenue_per_company': 3500,  # USD
            'projected_annual_revenue': 8400000  # USD
        }
    }
    
    return scenarios


@csrf_exempt
def calculate_pricing(request):
    """
    Calcula el precio para una empresa específica
    """
    if request.method == 'POST':
        data = json.loads(request.body)
        
        employees = int(data.get('employees', 0))
        plan = data.get('plan', 'professional')
        country = data.get('country', 'MX')
        addons = data.get('addons', [])
        setup_type = data.get('setup_type', 'standard_setup')
        
        # Cálculo base
        from .. import PAYROLL_PRICING, PREMIUM_SERVICES, AI_SERVICES, IMPLEMENTATION_SERVICES, VOLUME_DISCOUNTS
        
        plan_data = PAYROLL_PRICING[plan]
        base_price = plan_data['price_per_employee'] * employees
        setup_fee = plan_data['setup_fee']
        monthly_base_fee = plan_data['monthly_base_fee']
        
        # Descuentos por volumen
        volume_discount = 0
        for threshold, discount in VOLUME_DISCOUNTS['employee_discounts'].items():
            threshold_employees = int(threshold.replace('+', ''))
            if employees >= threshold_employees:
                volume_discount = discount
                break
        
        # Precio con descuento
        discounted_price = base_price * (1 - volume_discount)
        
        # Add-ons
        addon_total = 0
        for addon in addons:
            if addon in PREMIUM_SERVICES:
                addon_price = PREMIUM_SERVICES[addon].get('price_per_employee', 0) * employees
                addon_total += addon_price
            elif addon in AI_SERVICES:
                addon_price = AI_SERVICES[addon]['price_per_employee'] * employees
                addon_total += addon_price
        
        # Descuento por múltiples add-ons
        if len(addons) >= 3:
            addon_discount = VOLUME_DISCOUNTS['addon_discounts']['3_addons']
            addon_total *= (1 - addon_discount)
        
        # Setup fee
        implementation_fee = IMPLEMENTATION_SERVICES[setup_type]['price']
        
        # Totales
        monthly_total = discounted_price + monthly_base_fee + addon_total
        annual_total = monthly_total * 12
        setup_total = setup_fee + implementation_fee
        
        # ROI calculation
        cost_savings = employees * 50  # Estimado de ahorro por empleado
        annual_savings = cost_savings * 12
        roi_percentage = ((annual_savings - annual_total) / annual_total) * 100
        
        result = {
            'pricing_breakdown': {
                'base_price': float(base_price),
                'volume_discount': float(volume_discount * 100),
                'discounted_price': float(discounted_price),
                'monthly_base_fee': float(monthly_base_fee),
                'addon_total': float(addon_total),
                'monthly_total': float(monthly_total),
                'annual_total': float(annual_total)
            },
            'setup_costs': {
                'plan_setup_fee': float(setup_fee),
                'implementation_fee': float(implementation_fee),
                'total_setup': float(setup_total)
            },
            'roi_analysis': {
                'annual_savings': float(annual_savings),
                'annual_cost': float(annual_total),
                'net_savings': float(annual_savings - annual_total),
                'roi_percentage': float(roi_percentage),
                'payback_months': float(setup_total / (annual_savings - annual_total) * 12)
            },
            'plan_details': {
                'plan_name': plan,
                'employees': employees,
                'country': country,
                'addons': addons,
                'setup_type': setup_type
            }
        }
        
        return JsonResponse(result)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)


@login_required
def pricing_comparison(request):
    """
    Comparación de precios con competidores
    """
    context = {
        'page_title': 'Comparación de Precios - huntRED® Payroll',
        'active_tab': 'pricing',
        'competitors': get_competitive_analysis(),
        'our_advantages': [
            'WhatsApp integrado con IA conversacional',
            'Compliance automático multi-país',
            'Analytics predictivo y sentiment analysis',
            'Workflow automation inteligente',
            'Dashboard avanzado con insights',
            'Soporte dedicado 24/7'
        ]
    }
    
    return render(request, 'payroll/pricing_comparison.html', context)


@login_required
def profitability_analysis(request):
    """
    Análisis detallado de rentabilidad
    """
    context = {
        'page_title': 'Análisis de Rentabilidad - huntRED® Payroll',
        'active_tab': 'pricing',
        'profitability': get_profitability_analysis(),
        'revenue_projection': get_revenue_projection(),
        'cost_breakdown': get_cost_breakdown()
    }
    
    return render(request, 'payroll/profitability_analysis.html', context) 