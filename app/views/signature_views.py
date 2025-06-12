"""
Vistas para el sistema de firmas electrónicas.
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q
from datetime import datetime, timedelta
import json
import logging

from ..ats.utils.signature.blockchain import BlockchainSignature
from ..ats.utils.signature.biometric import AdvancedBiometricValidation
from ..ats.utils.signature.config import (
    DOCUMENT_TYPES,
    BIOMETRIC_CONFIG,
    BLOCKCHAIN_CONFIG,
    STORAGE_CONFIG,
    NOTIFICATION_CONFIG,
    SECURITY_CONFIG,
    LOGGING_CONFIG,
    CACHE_CONFIG,
    API_CONFIG,
    UI_CONFIG
)
from ..models import (
    Document,
    Signature,
    SignatureRequest,
    SignatureStatus
)

logger = logging.getLogger(__name__)

@login_required
def signature_dashboard(request):
    """
    Vista principal del dashboard de firmas.
    """
    try:
        # Obtener estadísticas
        stats = {
            'pending': SignatureRequest.objects.filter(status='pending').count(),
            'signed_today': SignatureRequest.objects.filter(
                status='signed',
                signed_at__date=datetime.now().date()
            ).count(),
            'signed_week': SignatureRequest.objects.filter(
                status='signed',
                signed_at__date__gte=datetime.now().date() - timedelta(days=7)
            ).count(),
            'avg_response_time': _calculate_avg_response_time()
        }
        
        # Obtener documentos pendientes
        pending_documents = SignatureRequest.objects.filter(
            status='pending'
        ).order_by('-created_at')[:10]
        
        # Obtener actividad reciente
        recent_activity = SignatureRequest.objects.filter(
            status__in=['signed', 'rejected']
        ).order_by('-updated_at')[:10]
        
        # Obtener estado de sistemas
        systems_status = {
            'blockchain': _check_blockchain_status(),
            'biometric': _check_biometric_status()
        }
        
        context = {
            'stats': stats,
            'pending_documents': pending_documents,
            'recent_activity': recent_activity,
            'systems_status': systems_status,
            'document_types': DOCUMENT_TYPES,
            'ui_config': UI_CONFIG
        }
        
        return render(request, 'dashboard/signature_dashboard.html', context)
        
    except Exception as e:
        logger.error(f"Error en dashboard de firmas: {str(e)}")
        return JsonResponse({
            'error': 'Error al cargar el dashboard'
        }, status=500)

@login_required
@require_http_methods(['GET'])
def get_pending_documents(request):
    """
    Obtiene la lista de documentos pendientes.
    """
    try:
        page = request.GET.get('page', 1)
        per_page = request.GET.get('per_page', 10)
        search = request.GET.get('search', '')
        document_type = request.GET.get('type', '')
        
        # Construir query
        query = Q(status='pending')
        if search:
            query &= Q(document__name__icontains=search)
        if document_type:
            query &= Q(document__type=document_type)
            
        # Obtener documentos
        documents = SignatureRequest.objects.filter(query).order_by('-created_at')
        
        # Paginar resultados
        paginator = Paginator(documents, per_page)
        page_obj = paginator.get_page(page)
        
        # Preparar respuesta
        data = {
            'documents': [{
                'id': doc.id,
                'name': doc.document.name,
                'type': doc.document.type,
                'status': doc.status,
                'created_at': doc.created_at.isoformat(),
                'deadline': doc.deadline.isoformat() if doc.deadline else None,
                'signers': [{
                    'id': signer.id,
                    'name': signer.get_full_name(),
                    'email': signer.email,
                    'status': signer.status
                } for signer in doc.signers.all()]
            } for doc in page_obj],
            'total': paginator.count,
            'pages': paginator.num_pages,
            'current_page': page_obj.number
        }
        
        return JsonResponse(data)
        
    except Exception as e:
        logger.error(f"Error al obtener documentos pendientes: {str(e)}")
        return JsonResponse({
            'error': 'Error al obtener documentos pendientes'
        }, status=500)

@login_required
@require_http_methods(['POST'])
def create_signature_request(request):
    """
    Crea una nueva solicitud de firma.
    """
    try:
        data = json.loads(request.body)
        
        # Validar datos requeridos
        required_fields = ['document_type', 'document_name', 'signers']
        for field in required_fields:
            if field not in data:
                return JsonResponse({
                    'error': f'Campo requerido: {field}'
                }, status=400)
        
        # Crear documento
        document = Document.objects.create(
            type=data['document_type'],
            name=data['document_name'],
            file=request.FILES.get('file')
        )
        
        # Crear solicitud de firma
        signature_request = SignatureRequest.objects.create(
            document=document,
            created_by=request.user,
            deadline=data.get('deadline')
        )
        
        # Agregar firmantes
        for signer_data in data['signers']:
            signature_request.signers.add(signer_data['id'])
        
        # Enviar notificaciones
        _send_signature_notifications(signature_request)
        
        return JsonResponse({
            'id': signature_request.id,
            'message': 'Solicitud de firma creada exitosamente'
        })
        
    except Exception as e:
        logger.error(f"Error al crear solicitud de firma: {str(e)}")
        return JsonResponse({
            'error': 'Error al crear solicitud de firma'
        }, status=500)

@login_required
@require_http_methods(['POST'])
def sign_document(request, request_id):
    """
    Firma un documento.
    """
    try:
        signature_request = SignatureRequest.objects.get(id=request_id)
        
        # Validar que el usuario es firmante
        if not signature_request.signers.filter(id=request.user.id).exists():
            return JsonResponse({
                'error': 'No eres firmante de este documento'
            }, status=403)
        
        # Validar que el documento está pendiente
        if signature_request.status != 'pending':
            return JsonResponse({
                'error': 'El documento ya no está pendiente de firma'
            }, status=400)
        
        # Obtener datos de firma
        signature_data = {
            'selfie_image': request.FILES.get('selfie'),
            'document_image': request.FILES.get('document'),
            'signature_image': request.FILES.get('signature')
        }
        
        # Validar biométricamente
        if is_biometric_required(signature_request.document.type):
            biometric = AdvancedBiometricValidation()
            validation_result = biometric.validate_signature(signature_data)
            
            if not validation_result['success']:
                return JsonResponse({
                    'error': 'Validación biométrica fallida',
                    'details': validation_result
                }, status=400)
        
        # Registrar firma en blockchain
        if is_blockchain_required(signature_request.document.type):
            blockchain = BlockchainSignature()
            blockchain_result = blockchain.add_signature_transaction(
                signature_request.id,
                request.user.id,
                signature_data
            )
            
            if not blockchain_result['success']:
                return JsonResponse({
                    'error': 'Error al registrar firma en blockchain',
                    'details': blockchain_result
                }, status=500)
        
        # Crear firma
        signature = Signature.objects.create(
            request=signature_request,
            user=request.user,
            signature_file=signature_data['signature_image'],
            selfie_file=signature_data['selfie_image'],
            document_file=signature_data['document_image']
        )
        
        # Actualizar estado de la solicitud
        signature_request.status = 'signed'
        signature_request.signed_at = datetime.now()
        signature_request.save()
        
        # Enviar notificaciones
        _send_signature_notifications(signature_request)
        
        return JsonResponse({
            'message': 'Documento firmado exitosamente'
        })
        
    except SignatureRequest.DoesNotExist:
        return JsonResponse({
            'error': 'Solicitud de firma no encontrada'
        }, status=404)
        
    except Exception as e:
        logger.error(f"Error al firmar documento: {str(e)}")
        return JsonResponse({
            'error': 'Error al firmar documento'
        }, status=500)

def _calculate_avg_response_time():
    """
    Calcula el tiempo promedio de respuesta para firmas.
    """
    try:
        signed_requests = SignatureRequest.objects.filter(
            status='signed',
            created_at__gte=datetime.now() - timedelta(days=30)
        )
        
        if not signed_requests:
            return 0
            
        total_time = sum(
            (req.signed_at - req.created_at).total_seconds()
            for req in signed_requests
        )
        
        return total_time / signed_requests.count()
        
    except Exception as e:
        logger.error(f"Error al calcular tiempo promedio: {str(e)}")
        return 0

def _check_blockchain_status():
    """
    Verifica el estado del sistema blockchain.
    """
    try:
        blockchain = BlockchainSignature()
        return {
            'active': blockchain.is_active(),
            'transactions': blockchain.get_total_transactions(),
            'last_block': blockchain.get_last_block()
        }
    except Exception as e:
        logger.error(f"Error al verificar estado de blockchain: {str(e)}")
        return {
            'active': False,
            'error': str(e)
        }

def _check_biometric_status():
    """
    Verifica el estado del sistema biométrico.
    """
    try:
        biometric = AdvancedBiometricValidation()
        return {
            'active': biometric.is_active(),
            'methods': biometric.get_available_methods(),
            'success_rate': biometric.get_success_rate()
        }
    except Exception as e:
        logger.error(f"Error al verificar estado biométrico: {str(e)}")
        return {
            'active': False,
            'error': str(e)
        }

def _send_signature_notifications(signature_request):
    """
    Envía notificaciones relacionadas con la firma.
    """
    try:
        if NOTIFICATION_CONFIG['email']['enabled']:
            # Enviar email
            pass
            
        if NOTIFICATION_CONFIG['sms']['enabled']:
            # Enviar SMS
            pass
            
    except Exception as e:
        logger.error(f"Error al enviar notificaciones: {str(e)}") 