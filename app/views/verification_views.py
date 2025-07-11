# /home/pablo/app/views/verification_views.py
#
# Vista para el módulo. Implementa la lógica de presentación y manejo de peticiones HTTP.

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.views.decorators import staff_member_required
from django.db import transaction
from django.core.paginator import Paginator
from django.db.models import Q
import json
import logging
from datetime import datetime

from app.models import (
    Person, BackgroundCheck, INCODEVerification,
    VerificationStatus, RiskLevel, VerificationType
)
from app.ats.chatbot.components.risk_analysis import RiskAnalysis
from app.ats.verification.tasks import process_verification
from app.ats.verification.utils import (
    get_verification_processor, analyze_risk, verify_incode
)

logger = logging.getLogger(__name__)

@staff_member_required
@login_required
def verification_list(request):
    """
    Lista de verificaciones y análisis
    """
    verifications = BackgroundCheck.objects.all().order_by('-created_at')
    paginator = Paginator(verifications, 20)
    page = request.GET.get('page', 1)
    
    context = {
        'verifications': paginator.get_page(page),
        'status_choices': VerificationStatus.choices,
        'risk_levels': RiskLevel.choices,
        'verification_types': VerificationType.choices
    }
    return render(request, 'verification/verification_list.html', context)

@staff_member_required
@login_required
def initiate_verification(request, candidate_id):
    """
    Iniciar proceso de verificación para un candidato
    """
    candidate = get_object_or_404(Person, id=candidate_id)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Crear verificación
            verification = BackgroundCheck.objects.create(
                candidate=candidate,
                status=VerificationStatus.PENDING,
                verification_type=data.get('verification_type', VerificationType.STANDARD)
            )
            
            # Procesar verificación en segundo plano
            process_verification.delay(verification.id)
            
            return JsonResponse({
                'status': 'success',
                'message': 'Verificación iniciada exitosamente',
                'verification_id': verification.id
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Error en el formato JSON'
            }, status=400)
        except Exception as e:
            logger.error(f"Error iniciando verificación: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': 'Error interno del servidor'
            }, status=500)
    
    # GET request
    context = {
        'candidate': candidate,
        'verification_types': VerificationType.choices
    }
    return render(request, 'verification/initiate_verification.html', context)

@staff_member_required
@login_required
def analyze_risk(request, verification_id):
    """
    Realizar análisis de riesgo para una verificación
    """
    verification = get_object_or_404(BackgroundCheck, id=verification_id)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Realizar análisis de riesgo
            risk_analysis = analyze_risk(
                verification,
                data.get('risk_factors', []),
                data.get('custom_risk_data', {})
            )
            
            return JsonResponse({
                'status': 'success',
                'message': 'Análisis de riesgo completado',
                'risk_analysis': risk_analysis
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Error en el formato JSON'
            }, status=400)
        except Exception as e:
            logger.error(f"Error en análisis de riesgo: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': 'Error interno del servidor'
            }, status=500)
    
    # GET request
    context = {
        'verification': verification
    }
    return render(request, 'verification/analyze_risk.html', context)

@staff_member_required
@login_required
def verify_incode(request, verification_id):
    """
    Realizar verificación con INCODE
    """
    verification = get_object_or_404(BackgroundCheck, id=verification_id)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Realizar verificación con INCODE
            incode_result = verify_incode(
                verification,
                data.get('document_type'),
                data.get('document_number'),
                data.get('document_front'),
                data.get('document_back'),
                data.get('selfie')
            )
            
            return JsonResponse({
                'status': 'success',
                'message': 'Verificación INCODE completada',
                'result': incode_result
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Error en el formato JSON'
            }, status=400)
        except Exception as e:
            logger.error(f"Error en verificación INCODE: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': 'Error interno del servidor'
            }, status=500)
    
    # GET request
    context = {
        'verification': verification
    }
    return render(request, 'verification/verify_incode.html', context)

@csrf_exempt
@login_required
def webhook_verification(request):
    """
    Webhook para recibir resultados de verificaciones
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            verification_id = data.get('verification_id')
            verification = get_object_or_404(BackgroundCheck, id=verification_id)
            
            # Actualizar estado y resultados
            verification.status = data.get('status', VerificationStatus.FAILED)
            verification.results = data.get('results', {})
            verification.completed_at = datetime.now()
            verification.save()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Webhook procesado exitosamente'
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Error en el formato JSON'
            }, status=400)
        except Exception as e:
            logger.error(f"Error en webhook: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': 'Error interno del servidor'
            }, status=500)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Método no permitido'
    }, status=405)
