"""
Clase base para manejar webhooks

Esta clase proporciona una interfaz común para la implementación de webhooks
en diferentes plataformas de integración.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union, Callable
import logging
import hmac
import hashlib
import json
import time
from datetime import datetime
import asyncio
from django.core.cache import cache
from django.conf import settings
from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.urls import path, include
from app.models import BusinessUnit

logger = logging.getLogger(__name__)

class WebhookQueue:
    """Clase para manejar colas de webhooks"""
    
    def __init__(self, queue_name: str):
        """
        Inicializa la cola de webhooks
        
        Args:
            queue_name: Nombre de la cola
        """
        self.queue_name = queue_name
        self.retry_config = {
            'max_retries': getattr(settings, 'WEBHOOK_MAX_RETRIES', 3),
            'retry_delay': getattr(settings, 'WEBHOOK_RETRY_DELAY', 60),  # 1 minuto
            'backoff_factor': getattr(settings, 'WEBHOOK_BACKOFF_FACTOR', 2)
        }
        
    async def enqueue(self, payload: Dict[str, Any], headers: Dict[str, str] = None):
        """
        Añade un webhook a la cola
        
        Args:
            payload: Datos del webhook
            headers: Cabeceras del webhook
        """
        webhook_data = {
            'payload': payload,
            'headers': headers or {},
            'retry_count': 0,
            'last_retry': None,
            'created_at': datetime.now().isoformat()
        }
        
        # Almacenar en caché
        cache_key = f"{self.queue_name}:{int(time.time())}"
        cache.set(cache_key, webhook_data, timeout=self.retry_config['retry_delay'] * 10)
        
    async def process_queue(self, processor: Callable):
        """
        Procesa la cola de webhooks
        
        Args:
            processor: Función para procesar cada webhook
        """
        while True:
            try:
                # Obtener webhooks pendientes
                pending_webhooks = self._get_pending_webhooks()
                
                for webhook_id, webhook_data in pending_webhooks.items():
                    try:
                        # Procesar webhook
                        await processor(webhook_data['payload'], webhook_data['headers'])
                        
                        # Eliminar de la cola
                        self._remove_webhook(webhook_id)
                        
                    except Exception as e:
                        logger.error(f"Error procesando webhook {webhook_id}: {str(e)}")
                        
                        # Manejar reintentos
                        if webhook_data['retry_count'] < self.retry_config['max_retries']:
                            # Calcular delay exponencial
                            delay = self.retry_config['retry_delay'] * (
                                self.retry_config['backoff_factor'] ** webhook_data['retry_count']
                            )
                            
                            # Actualizar webhook
                            webhook_data['retry_count'] += 1
                            webhook_data['last_retry'] = datetime.now().isoformat()
                            self._update_webhook(webhook_id, webhook_data, delay)
                            
                        else:
                            # Eliminar después de máximo de reintentos
                            self._remove_webhook(webhook_id)
                            
                # Esperar antes de siguiente iteración
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error en procesamiento de cola: {str(e)}")
                await asyncio.sleep(5)  # Esperar más tiempo en caso de error
                
    def _get_pending_webhooks(self) -> Dict[str, Dict[str, Any]]:
        """
        Obtiene webhooks pendientes de la caché
        
        Returns:
            Dict con webhooks pendientes
        """
        pending = {}
        pattern = f"{self.queue_name}:*"
        
        # Obtener todas las claves que coinciden con el patrón
        keys = cache.keys(pattern)
        
        for key in keys:
            webhook_data = cache.get(key)
            if webhook_data:
                pending[key] = webhook_data
                
        return pending
        
    def _remove_webhook(self, webhook_id: str):
        """
        Elimina un webhook de la cola
        
        Args:
            webhook_id: ID del webhook
        """
        cache.delete(webhook_id)
        
    def _update_webhook(self, webhook_id: str, webhook_data: Dict[str, Any], delay: int):
        """
        Actualiza un webhook en la cola
        
        Args:
            webhook_id: ID del webhook
            webhook_data: Datos actualizados
            delay: Tiempo de espera en segundos
        """
        cache.set(webhook_id, webhook_data, timeout=delay)

class BaseWebhook(ABC):
    """
    Clase base para manejar webhooks de diferentes canales.
    Proporciona funcionalidad común para validación y procesamiento de webhooks.
    """
    
    def __init__(self, secret_key: Optional[str] = None):
        """
        Inicializa el manejador de webhooks
        
        Args:
            secret_key: Clave secreta para validar firmas
        """
        self.secret_key = secret_key
        self.queue = WebhookQueue(self.__class__.__name__)
        
    def verify_signature(self, request: HttpRequest) -> bool:
        """
        Verifica la firma del webhook
        
        Args:
            request: Request HTTP
            
        Returns:
            bool: True si la firma es válida
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
        
        Args:
            request: Request HTTP
            
        Returns:
            Dict con el payload
        """
        try:
            return json.loads(request.body.decode('utf-8'))
        except Exception as e:
            logger.error(f"Error extrayendo payload: {str(e)}")
            return {}
            
    def create_webhook_view(self, handler: Callable):
        """
        Crea una vista para el webhook
        
        Args:
            handler: Función manejadora del webhook
            
        Returns:
            Vista del webhook
        """
        @csrf_exempt
        @require_http_methods(["POST"])
        def webhook_view(request: HttpRequest) -> JsonResponse:
            try:
                # Verificar firma
                if not self.verify_signature(request):
                    return JsonResponse({'error': 'Invalid signature'}, status=401)
                    
                # Extraer payload
                payload = self.extract_payload(request)
                if not payload:
                    return JsonResponse({'error': 'Invalid payload'}, status=400)
                    
                # Procesar webhook
                result = handler(payload)
                
                return JsonResponse(result)
                
            except Exception as e:
                logger.error(f"Error en webhook: {str(e)}")
                return JsonResponse({'error': str(e)}, status=500)
                
        return webhook_view
        
    def register_webhook(self, url_pattern: str, handler: Callable) -> None:
        """
        Registra un webhook en las URLs de Django
        
        Args:
            url_pattern: Patrón de URL
            handler: Función manejadora del webhook
        """
        # Crear la vista del webhook
        webhook_view = self.create_webhook_view(handler)
        
        # Registrar en las URLs
        urlpatterns = [
            path(url_pattern, webhook_view, name=f"{self.__class__.__name__}_webhook")
        ]
        
        return include(urlpatterns)
        
    async def handle_webhook(self, payload: Dict[str, Any], headers: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Maneja un webhook entrante
        
        Args:
            payload: Datos del webhook
            headers: Cabeceras del webhook
            
        Returns:
            Dict con la respuesta al webhook
        """
        try:
            # Validar firma si está presente
            if headers and 'X-Webhook-Signature' in headers:
                if not self.validate_signature(payload, headers['X-Webhook-Signature']):
                    raise ValueError("Invalid webhook signature")
                    
            # Añadir a la cola
            await self.queue.enqueue(payload, headers)
            
            return {
                'status': 'queued',
                'message': 'Webhook queued for processing'
            }
            
        except Exception as e:
            logger.error(f"Error handling webhook: {str(e)}")
            raise
            
    async def process_webhook(self, payload: Dict[str, Any], headers: Dict[str, str] = None):
        """
        Procesa un webhook de la cola
        
        Args:
            payload: Datos del webhook
            headers: Cabeceras del webhook
        """
        try:
            # Implementación específica del procesamiento
            await self._process_webhook(payload, headers)
            
        except Exception as e:
            logger.error(f"Error processing webhook: {str(e)}")
            raise
            
    @abstractmethod
    async def _process_webhook(self, payload: Dict[str, Any], headers: Dict[str, str] = None):
        """
        Implementación específica del procesamiento del webhook
        
        Args:
            payload: Datos del webhook
            headers: Cabeceras del webhook
        """
        pass
        
    async def start_processing(self):
        """Inicia el procesamiento de la cola de webhooks"""
        await self.queue.process_queue(self.process_webhook)

    async def verify_webhook(self, request: Any) -> bool:
        """
        Verifica la autenticidad del webhook
        """
        pass

    async def process_webhook_data(self, data: Dict[str, Any]) -> bool:
        """
        Procesa los datos del webhook
        """
        pass

    async def log_webhook_event(self, event_type: str, payload: Dict[str, Any], error: Optional[str] = None) -> None:
        """
        Registra un evento de webhook
        """
        from app.ats.integrations.utils import log_integration_event
        await log_integration_event(
            integration=self.business_unit,
            event_type='WEBHOOK',
            payload={
                'type': event_type,
                'data': payload
            },
            error=error
        ) 