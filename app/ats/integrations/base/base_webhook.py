from typing import Dict, Any, Optional, Callable
from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import logging
import hmac
import hashlib
from functools import wraps

logger = logging.getLogger('integrations')

class BaseWebhook:
    """
    Clase base para manejar webhooks de diferentes canales.
    Proporciona funcionalidad común para validación y procesamiento de webhooks.
    """
    
    def __init__(self, secret_key: Optional[str] = None):
        self.secret_key = secret_key
        
    def verify_signature(self, request: HttpRequest) -> bool:
        """
        Verifica la firma del webhook
        """
        if not self.secret_key:
            return True
            
        signature = request.headers.get('X-Hub-Signature')
        if not signature:
            return False
            
        try:
            # Obtener el cuerpo del request
            body = request.body
            
            # Calcular HMAC
            expected = hmac.new(
                self.secret_key.encode(),
                body,
                hashlib.sha1
            ).hexdigest()
            
            # Comparar firmas
            return hmac.compare_digest(f"sha1={expected}", signature)
            
        except Exception as e:
            logger.error(f"Error verificando firma: {str(e)}")
            return False
            
    def extract_payload(self, request: HttpRequest) -> Dict[str, Any]:
        """
        Extrae el payload del webhook
        """
        try:
            return json.loads(request.body.decode('utf-8'))
        except Exception as e:
            logger.error(f"Error extrayendo payload: {str(e)}")
            return {}
            
    def create_webhook_view(self, handler: Callable) -> Callable:
        """
        Crea una vista de webhook con validación y manejo de errores
        """
        @csrf_exempt
        @require_http_methods(["POST"])
        async def webhook_view(request: HttpRequest) -> JsonResponse:
            try:
                # Verificar método
                if request.method != "POST":
                    return JsonResponse({
                        "status": "error",
                        "message": "Método no permitido"
                    }, status=405)
                    
                # Verificar firma si hay secret key
                if self.secret_key and not self.verify_signature(request):
                    return JsonResponse({
                        "status": "error",
                        "message": "Firma inválida"
                    }, status=401)
                    
                # Extraer payload
                payload = self.extract_payload(request)
                if not payload:
                    return JsonResponse({
                        "status": "error",
                        "message": "Payload inválido"
                    }, status=400)
                    
                # Procesar webhook
                response = await handler(payload)
                
                return JsonResponse({
                    "status": "success",
                    "response": response
                })
                
            except Exception as e:
                logger.error(f"Error en webhook: {str(e)}")
                return JsonResponse({
                    "status": "error",
                    "message": str(e)
                }, status=500)
                
        return webhook_view
        
    def register_webhook(self, url_pattern: str, handler: Callable) -> None:
        """
        Registra un webhook en las URLs de Django
        """
        from django.urls import path
        from django.urls import include
        
        # Crear la vista del webhook
        webhook_view = self.create_webhook_view(handler)
        
        # Registrar en las URLs
        urlpatterns = [
            path(url_pattern, webhook_view, name=f"{self.__class__.__name__}_webhook")
        ]
        
        return include(urlpatterns) 