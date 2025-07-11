# app/ats/sexsi/views.py
"""
Vistas del módulo SEXSI (Sistema de Acuerdos Íntimos Consensuados).
Sistema para firma de acuerdos íntimos consensuados usando tecnología 
de firma electrónica y blockchain, alineado con las leyes sexuales de cada país.
"""

from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from typing import Dict, Any
import logging
import json
from datetime import datetime, timedelta
import hashlib

logger = logging.getLogger(__name__)


@login_required
def sexsi_dashboard(request):
    """
    Dashboard principal del sistema SEXSI para acuerdos íntimos consensuados.
    """
    try:
        context = {
            'title': 'SEXSI - Acuerdos Íntimos Consensuados',
            'module': 'sexsi',
            'page': 'dashboard',
            'description': 'Sistema de firma electrónica y blockchain para acuerdos íntimos'
        }
        return render(request, 'sexsi/dashboard.html', context)
    except Exception as e:
        logger.error(f"Error en sexsi_dashboard: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET", "POST"])
def create_agreement(request):
    """
    Crear un nuevo acuerdo íntimo consensuado.
    """
    try:
        if request.method == "POST":
            # Procesar creación del acuerdo
            agreement_data = request.POST.dict()
            
            # Validar datos del acuerdo
            required_fields = ['agreement_type', 'parties', 'terms', 'country']
            for field in required_fields:
                if field not in agreement_data:
                    return JsonResponse({'error': f'Campo requerido: {field}'}, status=400)
            
            # Generar hash único para el acuerdo
            agreement_hash = hashlib.sha256(
                f"{agreement_data['agreement_type']}{agreement_data['parties']}{datetime.now().isoformat()}".encode()
            ).hexdigest()
            
            # Simular almacenamiento en blockchain
            blockchain_data = {
                'agreement_id': agreement_hash,
                'timestamp': datetime.now().isoformat(),
                'status': 'pending_signature',
                'parties': agreement_data['parties'].split(','),
                'agreement_type': agreement_data['agreement_type'],
                'country': agreement_data['country']
            }
            
            logger.info(f"Nuevo acuerdo creado: {agreement_hash}")
            
            return JsonResponse({
                'status': 'success',
                'agreement_id': agreement_hash,
                'message': 'Acuerdo creado exitosamente. Pendiente de firma.'
            })
        
        # GET: Mostrar formulario de creación
        context = {
            'title': 'Crear Acuerdo Íntimo Consensuado',
            'module': 'sexsi',
            'page': 'create_agreement',
            'agreement_types': [
                'Consentimiento Sexual',
                'Acuerdo de Límites',
                'Acuerdo de Confidencialidad',
                'Acuerdo de Seguridad'
            ],
            'countries': [
                'España', 'México', 'Colombia', 'Argentina', 'Chile', 'Perú'
            ]
        }
        return render(request, 'sexsi/create_agreement.html', context)
        
    except Exception as e:
        logger.error(f"Error en create_agreement: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET", "POST"])
def sign_agreement(request):
    """
    Firmar un acuerdo íntimo consensuado.
    """
    try:
        if request.method == "POST":
            # Procesar firma del acuerdo
            signature_data = request.POST.dict()
            
            if 'agreement_id' not in signature_data:
                return JsonResponse({'error': 'ID de acuerdo requerido'}, status=400)
            
            agreement_id = signature_data['agreement_id']
            
            # Simular proceso de firma electrónica
            signature_hash = hashlib.sha256(
                f"{agreement_id}{request.user.id}{datetime.now().isoformat()}".encode()
            ).hexdigest()
            
            # Simular verificación de identidad
            identity_verified = True  # En producción, aquí iría la verificación real
            
            if not identity_verified:
                return JsonResponse({'error': 'Verificación de identidad fallida'}, status=400)
            
            # Simular registro en blockchain
            signature_record = {
                'agreement_id': agreement_id,
                'signer_id': request.user.id,
                'signature_hash': signature_hash,
                'timestamp': datetime.now().isoformat(),
                'ip_address': request.META.get('REMOTE_ADDR'),
                'user_agent': request.META.get('HTTP_USER_AGENT')
            }
            
            logger.info(f"Acuerdo firmado: {agreement_id} por usuario {request.user.id}")
            
            return JsonResponse({
                'status': 'success',
                'signature_hash': signature_hash,
                'message': 'Acuerdo firmado exitosamente'
            })
        
        # GET: Mostrar formulario de firma
        agreement_id = request.GET.get('agreement_id')
        context = {
            'title': 'Firmar Acuerdo Íntimo Consensuado',
            'module': 'sexsi',
            'page': 'sign_agreement',
            'agreement_id': agreement_id
        }
        return render(request, 'sexsi/sign_agreement.html', context)
        
    except Exception as e:
        logger.error(f"Error en sign_agreement: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def agreement_status(request):
    """
    Verificar el estado de un acuerdo íntimo consensuado.
    """
    try:
        agreement_id = request.GET.get('agreement_id')
        
        if not agreement_id:
            return JsonResponse({'error': 'ID de acuerdo requerido'}, status=400)
        
        # Simular consulta a blockchain
        agreement_status_data = {
            'agreement_id': agreement_id,
            'status': 'signed',  # pending_signature, signed, expired, revoked
            'created_at': (datetime.now() - timedelta(days=1)).isoformat(),
            'signed_at': datetime.now().isoformat(),
            'parties': ['usuario1@email.com', 'usuario2@email.com'],
            'signatures': [
                {
                    'signer': 'usuario1@email.com',
                    'signature_hash': 'abc123...',
                    'timestamp': datetime.now().isoformat()
                },
                {
                    'signer': 'usuario2@email.com', 
                    'signature_hash': 'def456...',
                    'timestamp': datetime.now().isoformat()
                }
            ],
            'legal_validity': True,
            'expires_at': (datetime.now() + timedelta(days=365)).isoformat()
        }
        
        return JsonResponse(agreement_status_data)
        
    except Exception as e:
        logger.error(f"Error en agreement_status: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def legal_compliance(request):
    """
    Verificar cumplimiento legal según las leyes del país.
    """
    try:
        country = request.GET.get('country', 'España')
        
        # Simular verificación de cumplimiento legal
        compliance_data = {
            'country': country,
            'compliance_status': 'compliant',
            'legal_framework': {
                'consent_age': 16,
                'documentation_required': True,
                'witness_required': False,
                'notarization_required': False,
                'electronic_signature_valid': True
            },
            'legal_requirements': [
                'Consentimiento libre y voluntario',
                'Mayoría de edad legal',
                'Capacidad mental',
                'Información clara y comprensible'
            ],
            'legal_risks': [
                'Coacción o presión',
                'Información falsa',
                'Incapacidad mental',
                'Menor de edad'
            ],
            'recommendations': [
                'Verificar identidad de ambas partes',
                'Documentar consentimiento explícito',
                'Mantener copias seguras del acuerdo',
                'Consultar con abogado especializado'
            ]
        }
        
        return JsonResponse(compliance_data)
        
    except Exception as e:
        logger.error(f"Error en legal_compliance: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["POST"])
def process_payment(request):
    """
    Procesar pago rápido y ágil para el acuerdo.
    """
    try:
        payment_data = request.POST.dict()
        
        # Simular procesamiento de pago
        payment_id = hashlib.sha256(
            f"payment{datetime.now().isoformat()}{payment_data.get('amount', '0')}".encode()
        ).hexdigest()
        
        # Simular validación de pago
        payment_status = 'completed'
        
        return JsonResponse({
            'status': 'success',
            'payment_id': payment_id,
            'payment_status': payment_status,
            'amount': payment_data.get('amount', '0'),
            'message': 'Pago procesado exitosamente'
        })
        
    except Exception as e:
        logger.error(f"Error en process_payment: {e}")
        return JsonResponse({'error': str(e)}, status=500)


# Funciones adicionales para compatibilidad con el sistema existente
def consent_form(request):
    """
    Formulario de consentimiento existente.
    """
    try:
        context = {
            'title': 'Formulario de Consentimiento - SEXSI',
            'module': 'sexsi',
            'page': 'consent_form'
        }
        return render(request, 'sexsi/consent_form.html', context)
    except Exception as e:
        logger.error(f"Error en consent_form: {e}")
        return JsonResponse({'error': str(e)}, status=500)


def mutual_agreement(request):
    """
    Acuerdo mutuo existente.
    """
    try:
        context = {
            'title': 'Acuerdo Mutuo - SEXSI',
            'module': 'sexsi',
            'page': 'mutual_agreement'
        }
        return render(request, 'sexsi/mutual_agreement.html', context)
    except Exception as e:
        logger.error(f"Error en mutual_agreement: {e}")
        return JsonResponse({'error': str(e)}, status=500)


def agreement_detail(request):
    """
    Detalle del acuerdo existente.
    """
    try:
        agreement_id = request.GET.get('id')
        context = {
            'title': 'Detalle del Acuerdo - SEXSI',
            'module': 'sexsi',
            'page': 'agreement_detail',
            'agreement_id': agreement_id
        }
        return render(request, 'sexsi/agreement_detail.html', context)
    except Exception as e:
        logger.error(f"Error en agreement_detail: {e}")
        return JsonResponse({'error': str(e)}, status=500)


def preference_selection(request):
    """
    Selección de preferencias existente.
    """
    try:
        context = {
            'title': 'Selección de Preferencias - SEXSI',
            'module': 'sexsi',
            'page': 'preference_selection'
        }
        return render(request, 'sexsi/preference_selection.html', context)
    except Exception as e:
        logger.error(f"Error en preference_selection: {e}")
        return JsonResponse({'error': str(e)}, status=500) 