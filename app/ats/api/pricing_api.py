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
import logging
from decimal import Decimal
from typing import Dict, Any, List
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.views.decorators.cache import cache_page
from django.core.exceptions import ValidationError
from app.ats.pricing.models import (
    PricingStrategy, PricePoint, DiscountRule, ReferralFee,
    BusinessUnitAddon, PricingProposal, ProposalSection, ProposalTemplate
)
from app.ats.pricing.talent_360_pricing import Talent360Pricing
from app.ats.pricing.utils import calculate_pricing_opportunity, get_business_unit_pricing
from app.ats.models.business_unit import BusinessUnit
from app.ats.pricing.services.pricing_service import PricingService

logger = logging.getLogger(__name__)

# --- Endpoints principales ---

@csrf_exempt
@require_http_methods(["GET"])
@login_required
@cache_page(60 * 60 * 24 * 30)  # 30 días
def get_pricing_plans(request):
    """Lista todos los planes base y sus características."""
    try:
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
        return JsonResponse({'plans': data, 'status': 'success'})
    except Exception as e:
        logger.error(f"Error en get_pricing_plans: {str(e)}")
        return JsonResponse({'error': 'Error interno del servidor', 'status': 'error'}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
@login_required
@cache_page(60 * 60 * 24 * 30)
def get_pricing_addons(request):
    """Lista todos los addons activos, con detalles y precios."""
    try:
        addons = BusinessUnitAddon.objects.filter(is_active=True)
        data = [
            {
                'id': a.id,
                'business_unit': a.business_unit.name,
                'addon': str(a.addon),
                'activated_at': a.activated_at.isoformat() if a.activated_at else None,
                'metadata': a.metadata or {}
            }
            for a in addons
        ]
        return JsonResponse({'addons': data, 'status': 'success'})
    except Exception as e:
        logger.error(f"Error en get_pricing_addons: {str(e)}")
        return JsonResponse({'error': 'Error interno del servidor', 'status': 'error'}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
@login_required
@cache_page(60 * 60 * 24 * 30)
def get_pricing_business_units(request):
    """Lista unidades de negocio y su configuración de pricing."""
    try:
        business_units = BusinessUnit.objects.all()
        data = [
            {
                'id': bu.id,
                'name': bu.name,
                'pricing_config': get_business_unit_pricing(bu)
            }
            for bu in business_units
        ]
        return JsonResponse({'business_units': data, 'status': 'success'})
    except Exception as e:
        logger.error(f"Error en get_pricing_business_units: {str(e)}")
        return JsonResponse({'error': 'Error interno del servidor', 'status': 'error'}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
@login_required
@cache_page(60 * 60 * 24 * 30)
def get_pricing_assessments(request):
    """Lista los assessments disponibles (ej. Talent 360) y su lógica de precios."""
    try:
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
            ],
            'status': 'success'
        })
    except Exception as e:
        logger.error(f"Error en get_pricing_assessments: {str(e)}")
        return JsonResponse({'error': 'Error interno del servidor', 'status': 'error'}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
@login_required
def calculate_pricing_api(request):
    """Calcula el precio total de una combinación (plan, addons, assessments, unidad de negocio, headcount, etc.)."""
    try:
        data = json.loads(request.body)
        
        # Validar datos de entrada
        if not data:
            return JsonResponse({'error': 'Datos requeridos', 'status': 'error'}, status=400)
        
        opportunity_id = data.get('opportunity_id')
        include_addons = data.get('include_addons', [])
        include_bundles = data.get('include_bundles', [])
        include_assessments = data.get('include_assessments', [])
        custom_milestones = data.get('custom_milestones', None)
        payment_schedule = data.get('payment_schedule', True)
        
        # Validar bundles
        if not include_bundles:
            return JsonResponse({'error': 'Se requiere al menos un bundle', 'status': 'error'}, status=400)
        
        # Usar PricingManager para lógica profunda
        from app.ats.pricing.pricing_interface import PricingManager
        
        # Si no hay opportunity_id, crear una propuesta simulada
        if not opportunity_id:
            proposal = create_simulated_proposal(
                include_bundles=include_bundles,
                include_addons=include_addons,
                include_assessments=include_assessments,
                payment_schedule=payment_schedule,
                custom_milestones=custom_milestones
            )
        else:
            proposal = PricingManager.generate_proposal(
                opportunity_id=opportunity_id,
                include_addons=include_addons,
                include_bundles=include_bundles,
                payment_schedule=payment_schedule,
                custom_milestones=custom_milestones,
                include_assessments=include_assessments
            )
        
        return JsonResponse({'proposal': proposal, 'status': 'success'})
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido', 'status': 'error'}, status=400)
    except ValidationError as e:
        return JsonResponse({'error': str(e), 'status': 'error'}, status=400)
    except Exception as e:
        logger.error(f"Error en calculate_pricing_api: {str(e)}")
        return JsonResponse({'error': 'Error interno del servidor', 'status': 'error'}, status=500)

def create_simulated_proposal(include_bundles, include_addons, include_assessments, payment_schedule, custom_milestones):
    """
    Crea una propuesta simulada para la calculadora cuando no hay opportunity_id.
    """
    total_amount = 0
    modalities = []
    
    # Procesar bundles
    for bundle in include_bundles:
        business_unit = bundle.get('business_unit', '')
        base_salary = bundle.get('base_salary', 0)
        retainer_scheme = bundle.get('retainer_scheme', 'single')
        
        # Obtener precios por modalidad
        for mode in ['ai', 'hybrid', 'human']:
            count = bundle.get(mode, 0)
            if count == 0:
                continue
                
            cost = 0
            milestones = []
            
            # Calcular costo según modalidad y unidad de negocio
            if mode == 'ai':
                if business_unit in ['huntRED Executive', 'huntRED Standard']:
                    cost = 95000 * count
                elif business_unit == 'huntU':
                    cost = 45000 * count
                elif business_unit == 'amigro':
                    cost = 25000 * count
                milestones = [{'label': 'Pago único', 'amount': cost, 'detail': '100% al inicio'}]
                
            elif mode in ['hybrid', 'human'] and business_unit in ['huntRED Executive', 'huntRED Standard']:
                base_calc = base_salary * 13
                rate = 0.13 if count >= 2 else 0.14  # Descuento por volumen
                if mode == 'human':
                    rate = 0.18 if count >= 2 else 0.20
                    
                cost = base_calc * rate * count
                
                if retainer_scheme == 'single':
                    retainer = cost * 0.25
                    remainder = cost * 0.75
                    milestones = [
                        {'label': 'Retainer', 'amount': retainer, 'detail': '1 pago de 25%'},
                        {'label': 'Al éxito 1', 'amount': remainder / 2, 'detail': '37.5% en colocación'},
                        {'label': 'Al éxito 2', 'amount': remainder / 2, 'detail': '37.5% en colocación final'}
                    ]
                else:  # double
                    retainer = cost * 0.175
                    remainder = cost * 0.65
                    milestones = [
                        {'label': 'Retainer 1', 'amount': retainer, 'detail': '17.5%'},
                        {'label': 'Retainer 2', 'amount': retainer, 'detail': '17.5%'},
                        {'label': 'Al éxito', 'amount': remainder, 'detail': '65% en colocación'}
                    ]
            else:  # huntU, amigro
                if mode == 'hybrid':
                    cost = 70000 * count if business_unit == 'huntU' else 40000 * count
                milestones = [{'label': 'Pago único', 'amount': cost, 'detail': '100% al inicio'}]
            
            modalities.append({
                'type': mode,
                'count': count,
                'cost': cost,
                'billing_milestones': milestones
            })
            total_amount += cost
    
    # Procesar addons
    addons_total = 0
    for addon_id in include_addons:
        try:
            addon = BusinessUnitAddon.objects.get(id=addon_id, is_active=True)
            addon_price = Decimal(addon.metadata.get('price', '0'))
            addons_total += addon_price
        except BusinessUnitAddon.DoesNotExist:
            continue
    
    # Procesar assessments
    assessments_total = 0
    for assessment in include_assessments:
        if assessment.get('id') == 'talent_360':
            user_count = assessment.get('users', 1)
            assessment_pricing = Talent360Pricing.calculate_total(user_count=user_count)
            assessments_total += assessment_pricing['total']
    
    total_amount += addons_total + assessments_total
    
    return {
        'total_amount': float(total_amount),
        'currency': 'MXN',
        'modalities': modalities,
        'addons_total': float(addons_total),
        'assessments_total': float(assessments_total),
        'totals': {
            'subtotal': float(total_amount / 1.16),  # Sin IVA
            'iva': float(total_amount - (total_amount / 1.16)),
            'total': float(total_amount),
            'currency': 'MXN',
            'date': '2024-01-01',
            'valid_until': '2024-02-01'
        }
    }

@csrf_exempt
@require_http_methods(["GET"])
@login_required
@cache_page(60 * 60 * 24 * 30)
def get_pricing_strategies(request):
    """Devuelve estrategias de pricing avanzadas, descuentos y referidos."""
    try:
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
        return JsonResponse({'strategies': data, 'status': 'success'})
    except Exception as e:
        logger.error(f"Error en get_pricing_strategies: {str(e)}")
        return JsonResponse({'error': 'Error interno del servidor', 'status': 'error'}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
@login_required
def get_pricing_proposal(request, proposal_id):
    """Devuelve una propuesta completa (para SolutionCalculator, etc.)."""
    try:
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
                'created_at': proposal.fecha_creacion.isoformat() if proposal.fecha_creacion else None,
                'sections': sections,
                'metadata': proposal.metadata
            },
            'status': 'success'
        })
    except Exception as e:
        logger.error(f"Error en get_pricing_proposal: {str(e)}")
        return JsonResponse({'error': 'Error interno del servidor', 'status': 'error'}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
@login_required
def send_proposal_email(request):
    """Envía una propuesta por email."""
    try:
        data = json.loads(request.body)
        email = data.get('email')
        proposal = data.get('proposal')
        
        if not email or not proposal:
            return JsonResponse({'error': 'Email y propuesta son requeridos', 'status': 'error'}, status=400)
        
        # Aquí iría la lógica de envío de email
        # Por ahora simulamos el envío
        logger.info(f"Enviando propuesta a {email}")
        
        return JsonResponse({
            'message': 'Propuesta enviada correctamente',
            'status': 'success'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido', 'status': 'error'}, status=400)
    except Exception as e:
        logger.error(f"Error en send_proposal_email: {str(e)}")
        return JsonResponse({'error': 'Error interno del servidor', 'status': 'error'}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
@login_required
def track_share(request):
    """Registra el compartir de una propuesta."""
    try:
        data = json.loads(request.body)
        email = data.get('email', 'Anónimo')
        proposal = data.get('proposal')
        platform = data.get('platform')
        business_unit = data.get('business_unit')
        timestamp = data.get('timestamp')
        
        # Aquí iría la lógica de tracking
        logger.info(f"Tracking share: {platform} - {business_unit} - {email}")
        
        return JsonResponse({
            'message': 'Share registrado correctamente',
            'status': 'success'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido', 'status': 'error'}, status=400)
    except Exception as e:
        logger.error(f"Error en track_share: {str(e)}")
        return JsonResponse({'error': 'Error interno del servidor', 'status': 'error'}, status=500)

# --- URLS sugeridas para incluir en ats/api/urls.py ---
# path('pricing/plans/', get_pricing_plans),
# path('pricing/addons/', get_pricing_addons),
# path('pricing/business-units/', get_pricing_business_units),
# path('pricing/assessments/', get_pricing_assessments),
# path('pricing/calculate/', calculate_pricing_api),
# path('pricing/strategies/', get_pricing_strategies),
# path('pricing/proposals/<int:proposal_id>/', get_pricing_proposal),
# path('pricing/send-proposal/', send_proposal_email),
# path('pricing/track-share/', track_share), 