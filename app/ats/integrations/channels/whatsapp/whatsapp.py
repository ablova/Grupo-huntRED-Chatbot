# app/ats/integrations/channels/whatsapp/whatsapp.py
#
# Módulo para manejar la integración con WhatsApp Business API.
# Procesa mensajes entrantes, envía respuestas, y gestiona interacciones como botones y listas.
# Optimizado para bajo uso de CPU, escalabilidad, y robustez frente a fallos.
# Incluye soporte para carruseles de vacantes y manejo de documentos (CV).

import json
import logging
import asyncio
import httpx
import time
import os
import re
import datetime
from typing import Optional, Dict, Any, List, Tuple
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone
from asgiref.sync import sync_to_async
from tenacity import retry, stop_after_attempt, wait_exponential
from app.models import (
    Person, BusinessUnit, WhatsAppAPI, ChatState,
    Chat, ChatMessage, Notification, MessageLog
)
# Importaciones directas siguiendo estándares de Django

# Import at runtime to avoid circular imports
def get_intent_processor():
    from app.ats.chatbot.intents_handler import IntentProcessor
    return IntentProcessor

from app.ats.integrations.services.document import EnhancedDocumentProcessor
from app.ats.chatbot.middleware.message_retry import MessageRetry
from app.ats.integrations.services import MessageService

# Stub temporal para registro_amigro - utilizado durante la migración
def registro_amigro(phone_number=None, business_unit_id=None, flow_type='registro', **kwargs):
    """
    Stub temporal para el template de registro de WhatsApp.
    Este es un placeholder hasta que la base de datos esté inicializada y los flujos de WhatsApp estén disponibles.
    
    Args:
        phone_number: Número de teléfono del usuario
        business_unit_id: ID de la unidad de negocio
        flow_type: Tipo de flujo ('registro' por defecto)
        kwargs: Argumentos adicionales
        
    Returns:
        Dict: Respuesta simulada del registro
    """
    logger.warning("Usando stub temporal para registro_amigro - Este método debe ser reemplazado después de la inicialización de la base de datos")
    return {
        'success': True,
        'message': 'Stub temporal de registro_amigro',
        'flow_type': flow_type,
        'phone_number': phone_number,
        'business_unit_id': business_unit_id,
        'is_stub': True
    }

logger = logging.getLogger('chatbot')

# Configuraciones globales
REQUEST_TIMEOUT = 10.0
MAX_RETRIES = 3
CACHE_TIMEOUT = 600  # 10 minutos
whatsapp_semaphore = asyncio.Semaphore(10)

# Configuraciones para ventana de mensajes y clasificación
META_MESSAGE_WINDOW = 24 * 60 * 60  # 24 horas en segundos
LAST_INTERACTION_CACHE_PREFIX = "last_interaction_"

# Patrones para clasificación automática
SERVICE_PATTERNS = [
    r'perfil', r'assessment', r'evaluación', r'vacante', r'aplicación', r'postulación',
    r'proceso', r'entrevista', r'soporte', r'ayuda', r'consulta', r'pregunta', r'duda',
    r'status', r'estado', r'progreso', r'feedback', r'resultado', r'oferta', r'salario', 
    r'beneficios', r'vacaciones', r'horario', r'jornada', r'aplicación', r'carta'
]

UTILITY_PATTERNS = [
    r'recordatorio', r'notificación', r'aviso', r'alerta', r'actualización',
    r'credencial', r'confirmación', r'verificación', r'código', r'cambio', r'actualizar', r'menu', r'iniciar', 
]

MARKETING_PATTERNS = [
    r'promoción', r'oferta', r'descuento', r'evento', r'invitación',
    r'webinar', r'seminario', r'curso', r'workshop', r'taller', r'nueva función'
]

class WhatsAppHandler:
    """
    Manejador de integración con WhatsApp.
    
    Proporciona métodos para:
    - Enviar mensajes
    - Recibir mensajes
    - Procesar respuestas
    - Clasificar automáticamente mensajes según políticas de Meta
    - Optimizar costos identificando ventanas gratuitas
    """
    
    def __init__(self):
        self.service = MessageService()
        self.retry = MessageRetry()
        self.base_url = settings.WHATSAPP_API_BASE_URL
        self.access_token = settings.WHATSAPP_ACCESS_TOKEN
        self.phone_number_id = settings.WHATSAPP_PHONE_NUMBER_ID
        
    async def send_message(self, message: Dict) -> bool:
        """
        Envía un mensaje a través de WhatsApp.
        
        Args:
            message: Mensaje a enviar
            
        Returns:
            bool indicando éxito
        """
        return await self.retry.process_message(message, self.service)
        
    async def receive_message(self, message: Dict) -> Dict:
        """
        Procesa un mensaje recibido de WhatsApp.
        
        Args:
            message: Mensaje recibido
            
        Returns:
            Dict con respuesta procesada
        """
        try:
            # Procesar mensaje
            response = await self.service.process_message(message)
            
            # Enviar respuesta
            await self.send_message(response)
            
            return response
            
        except Exception as e:
            logger.error(f"Error procesando mensaje: {str(e)}")
            return {
                'error': str(e),
                'status': 'error'
            }

    async def is_within_24h_window(self, phone_number: str, business_unit_id: int = None) -> bool:
        """
        Verifica si estamos dentro de la ventana de 24 horas desde la última interacción del usuario.
        
        Args:
            phone_number: Número de teléfono del usuario
            business_unit_id: ID opcional de la unidad de negocio
            
        Returns:
            bool: True si estamos dentro de la ventana, False si no
        """
        cache_key = f"{LAST_INTERACTION_CACHE_PREFIX}{phone_number}"
        last_interaction = cache.get(cache_key)
        
        if not last_interaction:
            # Si no está en caché, buscar en la base de datos
            try:
                # Buscar último mensaje recibido (del usuario hacia nosotros)
                latest_message = await sync_to_async(lambda: ChatMessage.objects.filter(
                    chat__phone=phone_number,
                    direction='INBOUND',
                    business_unit_id=business_unit_id
                ).order_by('-created_at').first())()  # noqa
                
                if latest_message:
                    last_interaction = latest_message.created_at.timestamp()
                    # Actualizar caché
                    cache.set(cache_key, last_interaction, CACHE_TIMEOUT)
                else:
                    return False  # No hay mensajes previos del usuario
            except Exception as e:
                logger.error(f"Error verificando ventana de 24h: {str(e)}")
                return False
        
        # Verificar si estamos dentro de la ventana de 24 horas
        current_time = timezone.now().timestamp()
        time_diff = current_time - last_interaction
        
        return time_diff < META_MESSAGE_WINDOW
    
    def classify_message_content(self, content: str, context: Dict = None) -> Tuple[str, str, str]:
        """
        Clasifica automáticamente un mensaje según su contenido y contexto.
        
        Args:
            content: Contenido del mensaje
            context: Contexto adicional (flujo, tipo de usuario, etc.)
            
        Returns:
            Tuple[str, str, str]: (modelo_precio, tipo, categoría)
        """
        content_lower = content.lower()
        context = context or {}
        flow_type = context.get('flow_type', '')
        
        # Clasificación basada en el flujo (tiene precedencia)
        if flow_type in ['onboarding', 'profile_creation', 'assessment', 'feedback', 'support']:
            return 'service', 'service_msg', 'service'
            
        # Clasificación basada en patrones de contenido
        for pattern in SERVICE_PATTERNS:
            if re.search(pattern, content_lower):
                return 'service', 'service_msg', 'service'
                
        for pattern in UTILITY_PATTERNS:
            if re.search(pattern, content_lower):
                return 'utility', 'utility_msg', 'utility'
                
        for pattern in MARKETING_PATTERNS:
            if re.search(pattern, content_lower):
                return 'marketing', 'marketing_msg', 'marketing'
        
        # Por defecto, clasificar como servicio (más conservador para costos)
        return 'service', 'service_msg', 'service'
        
    async def send_template_message(self, phone_number: str, template_name: str, parameters: List[str], language: str = 'es_MX', meta_pricing: Optional[Dict[str, Any]] = None, context: Dict = None) -> Dict:
        """
        Envía mensaje usando template pre-aprobado y registra en MessageLog con los nuevos campos.
        Optimizado para Meta Conversations 2025 con clasificación automática.
        
        Args:
            phone_number: Número de teléfono del destinatario
            template_name: Nombre de la plantilla
            parameters: Parámetros para la plantilla
            language: Código de idioma
            meta_pricing: Configuración manual de pricing (opcional)
            context: Contexto adicional para clasificación (flujo, tipo de usuario)
        """
        try:
            url = f"{self.base_url}/{self.phone_number_id}/messages"
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            components = []
            if parameters:
                components.append({
                    'type': 'body',
                    'parameters': [
                        {'type': 'text', 'text': param} for param in parameters
                    ]
                })
            payload = {
                'messaging_product': 'whatsapp',
                'to': phone_number,
                'type': 'template',
                'template': {
                    'name': template_name,
                    'language': {'code': language},
                    'components': components
                }
            }
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            # Determinar si estamos en ventana de 24 horas
            is_in_window = await self.is_within_24h_window(phone_number)
            
            # Extraer info de pricing de Meta si está disponible en resultado
            meta_info = meta_pricing or {}
            if 'pricing' in result:
                meta_info['model'] = result['pricing'].get('pricing_model')
                meta_info['type'] = result['pricing'].get('type')
                meta_info['category'] = result['pricing'].get('category')
                meta_info['cost'] = result['pricing'].get('cost')
            else:
                # Clasificar automáticamente si no hay info explícita de pricing
                content = ' '.join(parameters) if parameters else template_name
                model, msg_type, category = self.classify_message_content(content, context)
                
                # Si estamos dentro de la ventana de 24h y es servicio/utility, será gratis
                if is_in_window and model in ['service', 'utility']:
                    cost = 0.0
                else:
                    # Fuera de ventana o marketing, puede tener costo
                    cost = None  # Se determinará por Meta
                    
                meta_info['model'] = model
                meta_info['type'] = msg_type
                meta_info['category'] = category
                meta_info['cost'] = cost
                meta_info['within_24h_window'] = is_in_window
            # Registrar en MessageLog con datos ampliados para análisis de costos
            bu = BusinessUnit.objects.filter(whatsappapi__phone_number=phone_number).first()
            message_log = MessageLog.objects.create(
                business_unit=bu,
                channel='whatsapp',
                template_name=template_name,
                meta_pricing_model=meta_info.get('model'),
                meta_pricing_type=meta_info.get('type'),
                meta_pricing_category=meta_info.get('category'),
                meta_cost=meta_info.get('cost'),
                message_type='WHATSAPP',
                phone=phone_number,
                message=str(payload),
                status='SENT',
                response_data=result,
                # Campos adicionales para optimización y análisis
                meta_within_24h_window=meta_info.get('within_24h_window', False),
                flow_context=context.get('flow_type', '') if context else '',
                sent_at=timezone.now()
            )
            return {
                'success': True,
                'message_id': result.get('messages', [{}])[0].get('id'),
                'response': result
            }
        except Exception as e:
            logger.error(f"Error enviando template message: {str(e)}")
            return {'error': str(e)}

@csrf_exempt
async def whatsapp_webhook(request):
    """Webhook para procesar mensajes entrantes de WhatsApp."""
    try:
        if request.method != "POST":
            return JsonResponse({"status": "error", "message": "Método no permitido"}, status=405)

        payload = json.loads(request.body.decode("utf-8"))
        entry = payload.get('entry', [])[0]
        changes = entry.get('changes', [])[0]
        value = changes.get('value', {})
        messages = value.get('messages', [])
        if not messages:
            return JsonResponse({"status": "success", "message": "No messages to process"}, status=200)

        message = messages[0]
        user_id = message.get('from')
        phone_number_id = value.get('metadata', {}).get('phone_number_id')
        business_unit = await sync_to_async(lambda: WhatsAppAPI.objects.filter(
            phoneID=phone_number_id, is_active=True
        ).first().business_unit)()
        
        # Actualizar caché de última interacción para mantener ventana de 24h
        cache_key = f"{LAST_INTERACTION_CACHE_PREFIX}{user_id}"
        cache.set(cache_key, timezone.now().timestamp(), CACHE_TIMEOUT)

        handler = WhatsAppHandler()
        response = await handler.receive_message(message)
        return JsonResponse({"status": "success", "response": response}, status=200)
    except Exception as e:
        logger.error(f"Error en whatsapp_webhook: {str(e)}")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)