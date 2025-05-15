"""
Módulo para generar propuestas de verificación y calcular precios.

Este módulo proporciona funciones para:
1. Generar propuestas de verificación para oportunidades
2. Calcular precios para paquetes de verificación
3. Manejar la selección de addons y servicios
"""

import json
from decimal import Decimal, ROUND_HALF_UP
from django.utils import timezone
from django.db import transaction
from django.contrib.auth.models import User
from asgiref.sync import sync_to_async

from app.models import (
    Opportunity, Person, VerificationService, VerificationAddon,
    OpportunityVerificationPackage, PackageAddonDetail, CandidateVerification
)
from app.pricing.utils import calculate_pricing_opportunity

async def generate_verification_proposal(opportunity_id, selected_addons=None):
    """
    Genera una propuesta de verificación para una oportunidad.
    
    Args:
        opportunity_id: ID de la oportunidad
        selected_addons: Lista de IDs de addons seleccionados
        
    Returns:
        dict: Detalles de la propuesta de verificación
    """
    # Si no se especifican addons, usar los recomendados por defecto
    if not selected_addons:
        selected_addons = await get_recommended_addons(opportunity_id)
    
    # Calcular precios
    pricing = await calculate_verification_pricing(opportunity_id, selected_addons)
    
    # Obtener oportunidad
    opportunity = await sync_to_async(Opportunity.objects.get)(id=opportunity_id)
    
    # Construir propuesta
    proposal = {
        'opportunity': {
            'id': opportunity.id,
            'name': opportunity.name,
            'business_unit': opportunity.business_unit.name
        },
        'verification_services': await get_verification_services(),
        'selected_addons': await get_addons_details(selected_addons),
        'pricing': pricing,
        'generated_at': timezone.now().isoformat(),
        'expiration_date': (timezone.now() + timezone.timedelta(days=30)).isoformat()
    }
    
    return proposal

async def calculate_verification_pricing(opportunity_id, selected_addons=None):
    """
    Calcula el pricing para servicios de verificación.
    
    Args:
        opportunity_id: ID de la oportunidad
        selected_addons: Lista de IDs de addons seleccionados
        
    Returns:
        dict: Detalles del pricing
    """
    # Obtener oportunidad y candidatos
    opportunity = await sync_to_async(Opportunity.objects.get)(id=opportunity_id)
    candidates = await sync_to_async(list)(Person.objects.filter(vacante__opportunity=opportunity))
    
    # Inicializar pricing
    pricing = {
        'subtotal': Decimal('0.00'),
        'iva': Decimal('0.00'),
        'total': Decimal('0.00'),
        'per_candidate': [],
        'addons': []
    }
    
    # Si no hay addons seleccionados, devolver precio en cero
    if not selected_addons or len(selected_addons) == 0:
        return pricing
        
    # Obtener addons
    addons = await sync_to_async(list)(VerificationAddon.objects.filter(id__in=selected_addons))
    
    # Calcular precio por addon
    for addon in addons:
        addon_total = addon.price * len(candidates)
        pricing['addons'].append({
            'id': addon.id,
            'name': addon.name,
            'code': addon.code,
            'price': str(addon.price),
            'tier': addon.tier,
            'candidates': len(candidates),
            'total': str(addon_total)
        })
        pricing['subtotal'] += addon_total
    
    # Calcular por candidato
    for candidate in candidates:
        candidate_addons = []
        candidate_total = Decimal('0.00')
        
        for addon in addons:
            candidate_addons.append({
                'id': addon.id,
                'name': addon.name,
                'price': str(addon.price)
            })
            candidate_total += addon.price
        
        pricing['per_candidate'].append({
            'candidate_id': candidate.id,
            'candidate_name': candidate.nombre + ' ' + candidate.apellido,
            'addons': candidate_addons,
            'total': str(candidate_total)
        })
    
    # Calcular impuestos y total
    pricing['iva'] = pricing['subtotal'] * Decimal('0.16')
    pricing['total'] = pricing['subtotal'] + pricing['iva']
    
    # Redondear valores
    pricing['subtotal'] = str(pricing['subtotal'].quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
    pricing['iva'] = str(pricing['iva'].quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
    pricing['total'] = str(pricing['total'].quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
    
    return pricing

async def get_recommended_addons(opportunity_id):
    """
    Obtiene los addons recomendados para una oportunidad según su BU.
    
    Args:
        opportunity_id: ID de la oportunidad
        
    Returns:
        list: Lista de IDs de addons recomendados
    """
    # Obtener oportunidad
    opportunity = await sync_to_async(Opportunity.objects.get)(id=opportunity_id)
    bu_name = opportunity.business_unit.name
    
    # Addons recomendados por BU
    recommendations = {
        'huntU': await sync_to_async(list)(VerificationAddon.objects.filter(tier='basic').values_list('id', flat=True)),
        'Amigro': await sync_to_async(list)(VerificationAddon.objects.filter(tier='basic').values_list('id', flat=True)),
        'huntRED': await sync_to_async(list)(VerificationAddon.objects.filter(tier__in=['basic', 'freemium']).values_list('id', flat=True)),
        'huntRED Executive': await sync_to_async(list)(VerificationAddon.objects.filter(tier__in=['basic', 'freemium', 'premium']).values_list('id', flat=True))
    }
    
    # Devolver recomendaciones según BU, o básico si no hay específicas
    return recommendations.get(bu_name, await sync_to_async(list)(VerificationAddon.objects.filter(tier='basic').values_list('id', flat=True)))

@sync_to_async
def get_verification_services():
    """
    Obtiene todos los servicios de verificación disponibles.
    
    Returns:
        list: Lista de servicios de verificación
    """
    services = []
    for service in VerificationService.objects.filter(is_active=True):
        services.append({
            'id': service.id,
            'name': service.name,
            'code': service.code,
            'category': service.category,
            'description': service.description
        })
    return services

@sync_to_async
def get_addons_details(addon_ids):
    """
    Obtiene los detalles de los addons seleccionados.
    
    Args:
        addon_ids: Lista de IDs de addons
        
    Returns:
        list: Detalles de los addons
    """
    addons = []
    for addon in VerificationAddon.objects.filter(id__in=addon_ids):
        addons.append({
            'id': addon.id,
            'name': addon.name,
            'code': addon.code,
            'price': str(addon.price),
            'tier': addon.tier,
            'description': addon.description,
            'services': list(addon.services.values('id', 'name', 'category'))
        })
    return addons

@transaction.atomic
async def create_verification_package(opportunity_id, name, selected_addons, created_by_id):
    """
    Crea un paquete de verificación para una oportunidad.
    
    Args:
        opportunity_id: ID de la oportunidad
        name: Nombre del paquete
        selected_addons: Lista de IDs de addons seleccionados
        created_by_id: ID del usuario que crea el paquete
        
    Returns:
        dict: Detalles del paquete creado
    """
    # Verificar que la oportunidad existe
    opportunity = await sync_to_async(Opportunity.objects.get)(id=opportunity_id)
    created_by = await sync_to_async(User.objects.get)(id=created_by_id)
    
    # Calcular pricing
    pricing = await calculate_verification_pricing(opportunity_id, selected_addons)
    total_price = Decimal(pricing['total'])
    
    # Crear paquete
    package = await sync_to_async(OpportunityVerificationPackage.objects.create)(
        opportunity=opportunity,
        name=name,
        description=f"Paquete de verificación para {opportunity.name}",
        total_price=total_price,
        created_by=created_by,
        status='draft'
    )
    
    # Agregar detalles de addons
    addons = await sync_to_async(list)(VerificationAddon.objects.filter(id__in=selected_addons))
    for addon in addons:
        await sync_to_async(PackageAddonDetail.objects.create)(
            package=package,
            addon=addon,
            quantity=1,
            unit_price=addon.price,
            subtotal=addon.price
        )
    
    return {
        'id': package.id,
        'name': package.name,
        'opportunity': {
            'id': opportunity.id,
            'name': opportunity.name
        },
        'total_price': str(package.total_price),
        'status': package.status,
        'created_at': package.created_at.isoformat()
    }

@transaction.atomic
async def assign_verification_to_candidates(package_id, candidate_ids, assigned_by_id):
    """
    Asigna verificaciones a candidatos dentro de un paquete.
    
    Args:
        package_id: ID del paquete de verificación
        candidate_ids: Lista de IDs de candidatos
        assigned_by_id: ID del usuario que asigna
        
    Returns:
        list: Lista de verificaciones creadas
    """
    # Obtener package y usuario
    package = await sync_to_async(OpportunityVerificationPackage.objects.get)(id=package_id)
    assigned_by = await sync_to_async(User.objects.get)(id=assigned_by_id)
    
    # Verificar que el paquete está activo
    if package.status != 'active':
        package.status = 'active'
        await sync_to_async(package.save)()
    
    # Crear verificaciones
    verification_ids = []
    for candidate_id in candidate_ids:
        candidate = await sync_to_async(Person.objects.get)(id=candidate_id)
        
        # Verificar si ya existe verificación para este candidato
        existing = await sync_to_async(CandidateVerification.objects.filter(
            package=package,
            candidate=candidate
        ).exists)()
        
        if not existing:
            verification = await sync_to_async(CandidateVerification.objects.create)(
                package=package,
                candidate=candidate,
                status='pending',
                assigned_by=assigned_by
            )
            verification_ids.append(verification.id)
    
    return verification_ids

async def get_verification_status(package_id=None, candidate_id=None):
    """
    Obtiene el estado de verificación para un paquete o candidato.
    
    Args:
        package_id: ID del paquete (opcional)
        candidate_id: ID del candidato (opcional)
        
    Returns:
        dict: Estado de verificación
    """
    # Construir query
    query = {}
    if package_id:
        query['package_id'] = package_id
    if candidate_id:
        query['candidate_id'] = candidate_id
    
    # Obtener verificaciones
    verifications = await sync_to_async(list)(CandidateVerification.objects.filter(**query))
    
    # Construir respuesta
    status = {
        'total': len(verifications),
        'by_status': {
            'pending': 0,
            'in_progress': 0,
            'completed': 0,
            'failed': 0
        },
        'candidates': []
    }
    
    for verification in verifications:
        # Contar por estado
        status['by_status'][verification.status] += 1
        
        # Agregar detalle de candidato
        candidate = {
            'verification_id': verification.id,
            'candidate_id': verification.candidate.id,
            'candidate_name': verification.candidate.nombre + ' ' + verification.candidate.apellido,
            'status': verification.status,
            'overall_score': verification.overall_score,
            'assigned_at': verification.assigned_at.isoformat(),
            'completed_at': verification.completed_at.isoformat() if verification.completed_at else None
        }
        
        # Obtener resultados de servicios
        service_results = await sync_to_async(list)(verification.service_results.all())
        services = []
        for result in service_results:
            services.append({
                'id': result.id,
                'service_name': result.service.name,
                'status': result.status,
                'score': result.score,
                'completed_at': result.completed_at.isoformat() if result.completed_at else None
            })
        
        candidate['services'] = services
        status['candidates'].append(candidate)
    
    return status
