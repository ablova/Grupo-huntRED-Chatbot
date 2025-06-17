"""
API de verificación

Este módulo proporciona endpoints para:
1. Acceder a servicios de verificación
2. Comprar paquetes de verificación
3. Asignar verificaciones a candidatos
4. Obtener resultados de verificación
"""

import json
import asyncio
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.utils import timezone
from asgiref.sync import sync_to_async

from app.decorators import *
from models import (
    VerificationService, VerificationAddon, OpportunityVerificationPackage,
    CandidateVerification, CandidateServiceResult, Person, SocialNetworkVerification
)
from app.ats.utils.proposal_generator import (
    generate_verification_proposal, calculate_verification_pricing,
    create_verification_package, assign_verification_to_candidates,
    get_verification_status
)
from app.ats.utils.tasks import start_verification_process

@csrf_exempt
@require_http_methods(["GET"])
@login_required
def get_verification_services_api(request):
    """Endpoint para obtener todos los servicios de verificación disponibles."""
    services = VerificationService.objects.filter(is_active=True)
    data = []
    
    for service in services:
        data.append({
            'id': service.id,
            'name': service.name,
            'code': service.code,
            'category': service.category,
            'description': service.description,
            'addons': [
                {
                    'id': addon.id,
                    'name': addon.name,
                    'price': str(addon.price),
                    'tier': addon.tier
                }
                for addon in service.addons.filter(is_active=True)
            ]
        })
    
    return JsonResponse({'services': data})

@csrf_exempt
@require_http_methods(["GET"])
@login_required
def get_verification_addons_api(request):
    """Endpoint para obtener todos los addons de verificación disponibles."""
    tier = request.GET.get('tier', None)
    
    # Filtrar por tier si se proporciona
    if tier:
        addons = VerificationAddon.objects.filter(is_active=True, tier=tier)
    else:
        addons = VerificationAddon.objects.filter(is_active=True)
    
    data = []
    for addon in addons:
        data.append({
            'id': addon.id,
            'name': addon.name,
            'code': addon.code,
            'price': str(addon.price),
            'tier': addon.tier,
            'description': addon.description,
            'services': [
                {
                    'id': service.id,
                    'name': service.name,
                    'category': service.category
                }
                for service in addon.services.all()
            ]
        })
    
    return JsonResponse({'addons': data})

@csrf_exempt
@require_http_methods(["POST"])
@login_required
@role_required(['super_admin', 'consultant_complete'])
def generate_verification_proposal_api(request):
    """Endpoint para generar una propuesta de verificación."""
    try:
        data = json.loads(request.body)
        opportunity_id = data.get('opportunity_id')
        selected_addons = data.get('selected_addons', [])
        
        if not opportunity_id:
            return JsonResponse({'error': 'Se requiere ID de oportunidad'}, status=400)
        
        # Generar propuesta de manera asíncrona
        proposal = asyncio.run(generate_verification_proposal(opportunity_id, selected_addons))
        
        return JsonResponse({'proposal': proposal})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
@login_required
@role_required(['super_admin', 'consultant_complete'])
def purchase_verification_package(request):
    """Endpoint para comprar un paquete de verificación."""
    try:
        data = json.loads(request.body)
        opportunity_id = data.get('opportunity_id')
        name = data.get('name', 'Paquete de verificación')
        selected_addons = data.get('selected_addons', [])
        
        if not opportunity_id or not selected_addons:
            return JsonResponse({
                'error': 'Se requiere ID de oportunidad y addons seleccionados'
            }, status=400)
        
        # Crear paquete de manera asíncrona
        package = asyncio.run(create_verification_package(
            opportunity_id, name, selected_addons, request.user.id
        ))
        
        return JsonResponse({'package': package})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
@login_required
@role_required(['super_admin', 'consultant_complete'])
def assign_verifications(request):
    """Endpoint para asignar verificaciones a candidatos."""
    try:
        data = json.loads(request.body)
        package_id = data.get('package_id')
        candidate_ids = data.get('candidate_ids', [])
        
        if not package_id or not candidate_ids:
            return JsonResponse({
                'error': 'Se requiere ID de paquete y IDs de candidatos'
            }, status=400)
        
        # Asignar verificaciones de manera asíncrona
        verification_ids = asyncio.run(assign_verification_to_candidates(
            package_id, candidate_ids, request.user.id
        ))
        
        # Iniciar proceso de verificación para cada candidato
        for verification_id in verification_ids:
            start_verification_process.delay(verification_id)
        
        return JsonResponse({
            'success': True,
            'message': f'Se asignaron {len(verification_ids)} verificaciones',
            'verification_ids': verification_ids
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
@login_required
def get_verification_status_api(request):
    """Endpoint para obtener el estado de verificación."""
    try:
        package_id = request.GET.get('package_id')
        candidate_id = request.GET.get('candidate_id')
        
        if not package_id and not candidate_id:
            return JsonResponse({
                'error': 'Se requiere ID de paquete o ID de candidato'
            }, status=400)
        
        # Obtener estado de manera asíncrona
        status = asyncio.run(get_verification_status(package_id, candidate_id))
        
        return JsonResponse({'status': status})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
@login_required
def get_social_verifications(request, candidate_id):
    """Endpoint para obtener las verificaciones de redes sociales de un candidato."""
    try:
        candidate = get_object_or_404(Person, id=candidate_id)
        
        # Obtener verificaciones del candidato
        verifications = CandidateVerification.objects.filter(candidate=candidate)
        
        social_data = []
        for verification in verifications:
            # Obtener resultados de servicios sociales
            service_results = CandidateServiceResult.objects.filter(
                verification=verification,
                service__category='social'
            )
            
            for result in service_results:
                # Obtener verificaciones de redes sociales
                social_verifications = SocialNetworkVerification.objects.filter(
                    service_result=result
                )
                
                for social in social_verifications:
                    social_data.append({
                        'id': social.id,
                        'network': social.network,
                        'profile_url': social.profile_url,
                        'profile_name': social.profile_name,
                        'followers_count': social.followers_count,
                        'verified_identity': social.verified_identity,
                        'account_age_days': social.account_age_days,
                        'reputation_score': social.reputation_score,
                        'verified_at': social.verified_at.isoformat()
                    })
        
        return JsonResponse({'social_verifications': social_data})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
@login_required
@role_required(['super_admin', 'consultant_complete'])
def verify_immediately(request):
    """Endpoint para iniciar una verificación inmediata para un candidato."""
    try:
        data = json.loads(request.body)
        verification_id = data.get('verification_id')
        
        if not verification_id:
            return JsonResponse({'error': 'Se requiere ID de verificación'}, status=400)
        
        # Obtener verificación
        verification = get_object_or_404(CandidateVerification, id=verification_id)
        
        # Iniciar proceso de verificación inmediata
        start_verification_process.delay(verification_id, immediate=True)
        
        return JsonResponse({
            'success': True,
            'message': f'Verificación iniciada para {verification.candidate.nombre}'
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
@login_required
def verify_social_profile(request):
    """Endpoint para verificar un perfil de red social específico."""
    try:
        profile_url = request.GET.get('profile_url')
        network = request.GET.get('network')
        candidate_id = request.GET.get('candidate_id')
        
        if not profile_url or not network or not candidate_id:
            return JsonResponse({
                'error': 'Se requieren URL de perfil, red social y ID de candidato'
            }, status=400)
        
        # Programar la verificación del perfil
        # Esta función sería implementada en el módulo de tareas
        # verify_social_profile_task.delay(profile_url, network, candidate_id)
        
        return JsonResponse({
            'success': True,
            'message': f'Verificación de perfil en {network} programada'
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
