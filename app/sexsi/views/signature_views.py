# /home/pablo/app/sexsi/views/signature_views.py
#
# Vista para el módulo. Implementa la lógica de presentación y manejo de peticiones HTTP.

"""
Vistas para manejo de firma digital en SEXSI.
"""
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from app.com.utils.signature.digital_signature_providers import get_signature_provider
from app.sexsi.config import get_document_config, validate_document_fields

@method_decorator(csrf_exempt, name='dispatch')
class SignatureRequestView(View):
    """
    Vista para manejar solicitudes de firma digital.
    """
    def post(self, request):
        """
        Maneja la solicitud de firma de un documento.
        """
        try:
            # Obtener datos del formulario
            data = json.loads(request.body)
            document_type = data.get('document_type')
            
            # Validar campos requeridos
            if not validate_document_fields(document_type, data):
                return JsonResponse({
                    'success': False,
                    'error': 'Faltan campos requeridos'
                }, status=400)
            
            # Obtener configuración del documento
            doc_config = get_document_config(document_type)
            
            # Preparar destinatarios
            recipients = [{
                'email': data['email'],
                'name': data['full_name']
            }]
            
            # Obtener proveedor de firma digital
            signature_provider = get_signature_provider('sexsi')
            
            # Crear solicitud de firma
            signature_request = signature_provider.create_signature_request(
                document_path=self._generate_document(data, doc_config),
                recipients=recipients
            )
            
            return JsonResponse({
                'success': True,
                'signature_request': signature_request
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    def _generate_document(self, data: Dict, config: Dict) -> str:
        """
        Genera el documento a partir de la plantilla y los datos proporcionados.
        """
        # Implementar la generación del documento
        # Esto dependerá del tipo de documento y su configuración
        pass

@method_decorator(csrf_exempt, name='dispatch')
class SignatureStatusView(View):
    """
    Vista para obtener el estado de una solicitud de firma.
    """
    def get(self, request, request_id):
        """
        Obtiene el estado de una solicitud de firma.
        """
        try:
            # Obtener proveedor de firma digital
            signature_provider = get_signature_provider('sexsi')
            
            # Obtener estado de la firma
            status = signature_provider.get_signature_status(request_id)
            
            return JsonResponse({
                'success': True,
                'status': status
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
