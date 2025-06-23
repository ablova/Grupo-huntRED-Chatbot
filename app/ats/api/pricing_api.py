# app/ats/api/pricing_api.py
"""
API de Pricing y Servicios de Grupo huntRED®

Este módulo expone endpoints REST para:
- Listar planes base y características
- Listar addons y detalles
- Listar unidades de negocio y su pricing
- Listar assessments (ej. Talent 360) y lógica de precios
- Calcular precios combinados (plan, addons, assessments, unidad de negocio, headcount, etc.)
- Consultar estrategias de pricing, descuentos y referidos
- Consultar propuestas completas

Incluye autenticación y control de permisos.
"""

import json
from decimal import Decimal
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from app.ats.pricing.models import (
    PricingStrategy, PricePoint, DiscountRule, ReferralFee,
    BusinessUnitAddon, PricingProposal, ProposalSection, ProposalTemplate
)
from app.ats.pricing.talent_360_pricing import Talent360Pricing
from app.ats.pricing.utils import calculate_pricing_opportunity, get_business_unit_pricing
from app.ats.models.business_unit import BusinessUnit
from app.ats.pricing.services.pricing_service import PricingService
from django.views.decorators.cache import cache_page

# --- Endpoints principales ---

@csrf_exempt
@require_http_methods(["GET"])
@login_required
@cache_page(60 * 60 * 24 * 30)  # 30 días
def get_pricing_plans(request):
    """Lista todos los planes base y sus características."""
    strategies = PricingStrategy.objects.filter(status='active')
    data = [
        {
            'id': s.id,
            'name': s.name,
            'type': s.get_type_display(),
            'description': s.description,
            'base_price': str(s.base_price),
            'currency': s.currency,
            'pricing_model': s.pricing_model,
            'conditions': s.conditions,
            'success_rate': str(s.success_rate),
            'conversion_rate': str(s.conversion_rate),
            'revenue_impact': str(s.revenue_impact)
        }
        for s in strategies
    ]
    return JsonResponse({'plans': data})

@csrf_exempt
@require_http_methods(["GET"])
@login_required
@cache_page(60 * 60 * 24 * 30)
def get_pricing_addons(request):
    """Lista todos los addons activos, con detalles y precios."""
    addons = BusinessUnitAddon.objects.filter(is_active=True)
    data = [
        {
            'id': a.id,
            'business_unit': a.business_unit.name,
            'addon': str(a.addon),
            'activated_at': a.activated_at,
            'metadata': a.metadata
        }
        for a in addons
    ]
    return JsonResponse({'addons': data})

@csrf_exempt
@require_http_methods(["GET"])
@login_required
@cache_page(60 * 60 * 24 * 30)
def get_pricing_business_units(request):
    """Lista unidades de negocio y su configuración de pricing."""
    business_units = BusinessUnit.objects.all()
    data = [
        {
            'id': bu.id,
            'name': bu.name,
            'pricing_config': get_business_unit_pricing(bu)
        }
        for bu in business_units
    ]
    return JsonResponse({'business_units': data})

@csrf_exempt
@require_http_methods(["GET"])
@login_required
@cache_page(60 * 60 * 24 * 30)
def get_pricing_assessments(request):
    """Lista los assessments disponibles (ej. Talent 360) y su lógica de precios."""
    # Solo Talent 360 por ahora, pero se puede extender
    tiers = Talent360Pricing.DISCOUNT_TIERS
    base_price = str(Talent360Pricing.BASE_PRICE)
    iva = str(Talent360Pricing.IVA_RATE)
    example = Talent360Pricing.calculate_total(user_count=50)
    return JsonResponse({
        'assessments': [
            {
                'id': 'talent_360',
                'name': 'Análisis de Talento 360°',
                'base_price': base_price,
                'iva': iva,
                'discount_tiers': tiers,
                'example_pricing': example
            }
        ]
    })

@csrf_exempt
@require_http_methods(["POST"])
@login_required
def calculate_pricing_api(request):
    """Calcula el precio total de una combinación (plan, addons, assessments, unidad de negocio, headcount, etc.)."""
    try:
        data = json.loads(request.body)
        opportunity_id = data.get('opportunity_id')
        include_addons = data.get('include_addons', [])
        include_bundles = data.get('include_bundles', [])
        include_assessments = data.get('include_assessments', [])
        custom_milestones = data.get('custom_milestones', None)
        payment_schedule = data.get('payment_schedule', True)
        # Usar PricingManager para lógica profunda
        from app.ats.pricing.pricing_interface import PricingManager
        proposal = PricingManager.generate_proposal(
            opportunity_id=opportunity_id,
            include_addons=include_addons,
            include_bundles=include_bundles,
            payment_schedule=payment_schedule,
            custom_milestones=custom_milestones,
            include_assessments=include_assessments
        )
        return JsonResponse({'proposal': proposal})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
@login_required
@cache_page(60 * 60 * 24 * 30)
def get_pricing_strategies(request):
    """Devuelve estrategias de pricing avanzadas, descuentos y referidos."""
    strategies = PricingStrategy.objects.filter(status='active')
    data = [
        {
            'id': s.id,
            'name': s.name,
            'discount_rules': [
                {
                    'id': d.id,
                    'type': d.get_type_display(),
                    'value': str(d.value),
                    'conditions': d.conditions
                } for d in s.discount_rules.all()
            ],
            'referral_fees': [
                {
                    'id': r.id,
                    'type': r.get_type_display(),
                    'value': str(r.value),
                    'conditions': r.conditions
                } for r in s.referral_fees.all()
            ]
        }
        for s in strategies
    ]
    return JsonResponse({'strategies': data})

@csrf_exempt
@require_http_methods(["GET"])
@login_required
def get_pricing_proposal(request, proposal_id):
    """Devuelve una propuesta completa (para SolutionCalculator, etc.)."""
    proposal = get_object_or_404(PricingProposal, id=proposal_id)
    sections = [
        {
            'id': s.id,
            'type': s.get_tipo_display(),
            'title': s.titulo,
            'content': s.contenido,
            'order': s.orden,
            'metadata': s.metadata
        }
        for s in proposal.secciones.all()
    ]
    return JsonResponse({
        'proposal': {
            'id': proposal.id,
            'title': proposal.titulo,
            'description': proposal.descripcion,
            'total_amount': str(proposal.monto_total),
            'currency': proposal.moneda,
            'status': proposal.estado,
            'created_at': proposal.fecha_creacion,
            'sections': sections,
            'metadata': proposal.metadata
        }
    })

# --- URLS sugeridas para incluir en ats/api/urls.py ---
# path('pricing/plans/', get_pricing_plans),
# path('pricing/addons/', get_pricing_addons),
# path('pricing/business-units/', get_pricing_business_units),
# path('pricing/assessments/', get_pricing_assessments),
# path('pricing/calculate/', calculate_pricing_api),
# path('pricing/strategies/', get_pricing_strategies),
# path('pricing/proposals/<int:proposal_id>/', get_pricing_proposal), 