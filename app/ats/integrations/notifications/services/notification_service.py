"""
Servicio centralizado de notificaciones para Grupo huntRED®.

Este módulo proporciona una interfaz unificada para enviar notificaciones
a través de múltiples canales (email, WhatsApp, etc.) con soporte para
templates y personalización por unidad de negocio.

Por defecto, las notificaciones se envían por todos los canales disponibles,
con opción de restringir a canales específicos cuando sea necesario.
"""
from typing import Dict, Optional, List, Union, Type, Any, Set, Tuple
from functools import lru_cache
import re
from django.conf import settings
from django.template.loader import render_to_string
from django.core.cache import cache
from django.db.models import Prefetch
from django.utils.module_loading import import_string
from django.utils import timezone
from app.models import (
    Notification, NotificationChannel, Person, Feedback, BusinessUnit,
    ChatMessage, MessageLog
)
from app.ats.utils import logger_utils
from app.ats.integrations.notifications.channels.base import BaseNotificationChannel
import logging
import asyncio
import uuid
from datetime import timedelta
from asgiref.sync import sync_to_async
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configuración de caché
CACHE_TIMEOUT = 3600  # 1 hora
CHANNEL_CACHE_PREFIX = "notification_channels_"
TEMPLATE_CACHE_PREFIX = "notification_template_"
LAST_INTERACTION_CACHE_PREFIX = "last_interaction_"

# Ventana de tiempo para mensajes gratis de Meta
META_MESSAGE_WINDOW = 24 * 60 * 60  # 24 horas en segundos

# Patrones para clasificación automática de mensajes
SERVICE_PATTERNS = [
    r'perfil', r'assessment', r'evaluación', r'vacante', r'aplicación', r'postulación',
    r'proceso', r'entrevista', r'soporte', r'ayuda', r'consulta', r'pregunta', r'duda',
    r'status', r'estado', r'progreso', r'feedback', r'resultado'
]

UTILITY_PATTERNS = [
    r'recordatorio', r'notificación', r'aviso', r'alerta', r'actualización',
    r'credencial', r'confirmación', r'verificación', r'código', r'cambio', r'actualizar'
]

MARKETING_PATTERNS = [
    r'promoción', r'oferta', r'descuento', r'evento', r'invitación',
    r'webinar', r'seminario', r'curso', r'workshop', r'taller', r'nueva función'
]

logger = logging.getLogger(__name__)

# Mapa de canales disponibles con sus pesos de prioridad (mayor = más prioridad)
CHANNEL_MAP = {
    'whatsapp': {
        'class': 'app.ats.integrations.notifications.channels.whatsapp.WhatsAppNotificationChannel',
        'priority': 40,
        'fallback': 'email'
    },
    'email': {
        'class': 'app.ats.integrations.notifications.channels.email.EmailNotificationChannel',
        'priority': 35,
        'fallback': None  # Email es el canal de último recurso
    },
    'telegram': {
        'class': 'app.ats.integrations.notifications.channels.telegram.TelegramNotificationChannel',
        'priority': 30,
        'fallback': 'whatsapp'
    },
    'sms': {
        'class': 'app.ats.integrations.notifications.channels.sms.SMSNotificationChannel',
        'priority': 20,
        'fallback': 'whatsapp'
    },
    'messenger': {
        'class': 'app.ats.integrations.notifications.channels.messenger.MessengerNotificationChannel',
        'priority': 15,
        'fallback': 'whatsapp'
    },
    'instagram': {
        'class': 'app.ats.integrations.notifications.channels.instagram.InstagramNotificationChannel',
        'priority': 12,
        'fallback': 'whatsapp'
    },
    'slack': {
        'class': 'app.ats.integrations.notifications.channels.slack.SlackNotificationChannel',
        'priority': 10,
        'fallback': 'whatsapp'
    },
    'x': {
        'class': 'app.ats.integrations.notifications.channels.x.XNotificationChannel',
        'priority': 5,
        'fallback': 'whatsapp'
    }
}

class NotificationService:
    """
    Servicio centralizado para el envío de notificaciones a través de múltiples canales.
    
    Utiliza el sistema de canales existente en app/ats/integrations/notifications/channels/
    para garantizar consistencia y evitar duplicación de lógica.
    
    Por defecto, las notificaciones se envían por todos los canales disponibles,
    a menos que se especifique lo contrario.
    """
    _instance = None
    _lock = asyncio.Lock()
    _executor = ThreadPoolExecutor(max_workers=5)
    
    def __new__(cls, business_unit: Optional[BusinessUnit] = None):
        """Implementa patrón Singleton para reutilizar instancias de canales."""
        if cls._instance is None:
            cls._instance = super(NotificationService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, business_unit: Optional[BusinessUnit] = None):
        """
        Inicializa el servicio de notificaciones.
        
        Args:
            business_unit: Unidad de negocio para la configuración de canales
        """
        if self._initialized:
            return
            
        self.logger = logger_utils.get_logger("notifications")
        self.business_unit = business_unit
        self._channels: Dict[str, BaseNotificationChannel] = {}
        self._initialized = True
        self._available_channels = list(CHANNEL_MAP.keys())  # Todos los canales disponibles
        self._channel_cache: Dict[str, BaseNotificationChannel] = {}
        self._template_cache: Dict[str, str] = {}
        self._rate_limits: Dict[str, float] = {}  # Control de tasa por canal
        
    @property
    async def default_channels(self) -> List[str]:
        """Obtiene los canales por defecto (todos los disponibles)."""
        return self._available_channels.copy()
    
    @lru_cache(maxsize=128)
    async def _get_channel(self, channel_name: str) -> Optional[BaseNotificationChannel]:
        """
        Obtiene o crea una instancia del canal especificado con caché.
        
        Args:
            channel_name: Nombre del canal (email, whatsapp, etc.)
            
        Returns:
            Instancia del canal o None si no se pudo cargar
        """
        # Verificar caché primero
        if channel_name in self._channel_cache:
            return self._channel_cache[channel_name]
            
        channel_config = CHANNEL_MAP.get(channel_name, {})
        channel_class_path = channel_config.get('class')
        
        if not channel_class_path:
            self.logger.warning(f"Canal no soportado: {channel_name}")
            return None
            
        try:
            # Cargar la clase del canal de forma asíncrona
            channel_class = await asyncio.get_event_loop().run_in_executor(
                None, import_string, channel_class_path
            )
            
            # Crear instancia del canal
            channel_instance = channel_class(self.business_unit)
            
            # Almacenar en caché
            self._channel_cache[channel_name] = channel_instance
            return channel_instance
            
        except ImportError as e:
            self.logger.error(f"Error cargando el canal {channel_name}: {str(e)}")
            return None
    
    async def _get_template(self, template_name: str, channel: str) -> str:
        """
        Obtiene el contenido de una plantilla desde caché o del sistema de plantillas.
        
        Args:
            template_name: Nombre de la plantilla
            channel: Canal para el que se necesita la plantilla
            
        Returns:
            Contenido de la plantilla
        """
        cache_key = f"{TEMPLATE_CACHE_PREFIX}{template_name}_{channel}"
        
        # Intentar obtener de la caché
        if cache_key in self._template_cache:
            return self._template_cache[cache_key]
            
        # Intentar obtener de la caché de Django
        cached_content = cache.get(cache_key)
        if cached_content:
            self._template_cache[cache_key] = cached_content
            return cached_content
            
        # Cargar la plantilla
        try:
            template_path = f"notifications/{channel}/{template_name}.{channel}"
            template_content = await asyncio.get_event_loop().run_in_executor(
                None, render_to_string, template_path, {}
            )
            
            # Almacenar en caché
            self._template_cache[cache_key] = template_content
            cache.set(cache_key, template_content, timeout=CACHE_TIMEOUT)
            return template_content
            
        except Exception as e:
            self.logger.error(f"Error cargando plantilla {template_name} para {channel}: {str(e)}")
            return ""
    
    async def _rate_limit_channel(self, channel_name: str) -> bool:
        """
        Verifica y aplica límites de tasa para un canal.
        
        Args:
            channel_name: Nombre del canal
            
        Returns:
            bool: True si se permite el envío, False si se debe esperar
        """
        now = asyncio.get_event_loop().time()
        last_sent = self._rate_limits.get(channel_name, 0)
        
        # Verificar si ha pasado el tiempo mínimo entre envíos (ej. 1 segundo)
        if now - last_sent < 1.0:  # 1 segundo entre envíos por canal
            return False
            
        # Actualizar el último tiempo de envío
        self._rate_limits[channel_name] = now
        return True
    
    async def _send_single_channel(
        self,
        channel_name: str,
        recipient: Person,
        template_name: str,
        context: Dict,
        notification_id: uuid.UUID
    ) -> Tuple[str, bool]:
        """
        Envía una notificación a través de un único canal.
        
        Args:
            channel_name: Nombre del canal
            recipient: Destinatario
            template_name: Nombre de la plantilla
            context: Contexto para la plantilla
            notification_id: ID de la notificación
            
        Returns:
            Tupla con (nombre_canal, éxito)
        """
        try:
            # Verificar límite de tasa
            if not await self._rate_limit_channel(channel_name):
                self.logger.warning(f"Límite de tasa alcanzado para {channel_name}")
                return channel_name, False
                
            # Obtener el canal
            channel = await self._get_channel(channel_name)
            if not channel:
                self.logger.warning(f"Canal no disponible: {channel_name}")
                return channel_name, False
                
            # Obtener plantilla
            template_content = await self._get_template(template_name, channel_name)
            if not template_content:
                self.logger.warning(f"No se pudo cargar la plantilla {template_name} para {channel_name}")
                return channel_name, False
                
            # Enviar notificación
            success = await channel.send(
                recipient=recipient,
                template_content=template_content,
                context=context,
                notification_id=notification_id
            )
            
            return channel_name, success
            
        except Exception as e:
            self.logger.error(f"Error enviando notificación por {channel_name}: {str(e)}", exc_info=True)
            return channel_name, False
    
    async def send_notification(
        self,
        recipient: Person,
        template_name: str,
        context: Optional[Dict] = None,
        channels: Optional[List[str]] = None,
        business_unit: Optional[Union[str, BusinessUnit]] = None,
        flow_type: str = None
    ) -> bool:
        """
        Envía una notificación usando una plantilla predefinida.
        
        Args:
            recipient: Persona que recibirá la notificación
            template_name: Nombre de la plantilla a utilizar
            context: Contexto para la plantilla
            channels: Canales a utilizar (email, whatsapp, etc.)
            business_unit: Unidad de negocio (opcional)
            flow_type: Tipo de flujo para clasificación automática
            
        Returns:
            bool: True si la notificación se envió correctamente
        """
        context = context or {}
        channels = channels or ['email']
        
        # Añadir datos del destinatario al contexto
        context.update({
            'recipient_name': recipient.get_full_name() or 'Estimado/a',
            'recipient_email': recipient.email,
            'recipient_phone': recipient.phone
        })
        
        return await self.send_notification(
            recipient=recipient,
            template_name=template_name,
            context=context,
            channels=channels,
            business_unit=business_unit,
            flow_type=flow_type
        )
    
    async def send_template_notification(
        self,
        recipient: Person,
        template_name: str,
        context: Optional[Dict] = None,
        channels: Optional[List[str]] = None,
        business_unit: Optional[Union[str, BusinessUnit]] = None,
        flow_type: str = None
    ) -> bool:
        """
        Alias avanzado de send_notification para compatibilidad y claridad semántica.
        Permite enviar notificaciones usando plantillas, compatible con código legado y nuevas integraciones.
        Args:
            recipient: Persona que recibirá la notificación
            template_name: Nombre de la plantilla a utilizar
            context: Contexto para la plantilla
            channels: Canales a utilizar (email, whatsapp, etc.)
            business_unit: Unidad de negocio (opcional)
            flow_type: Tipo de flujo para clasificación automática
        Returns:
            bool: True si la notificación se envió correctamente
        """
        return await self.send_notification(
            recipient=recipient,
            template_name=template_name,
            context=context,
            channels=channels,
            business_unit=business_unit,
            flow_type=flow_type
        )
    
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
                self.logger.error(f"Error verificando ventana de 24h: {str(e)}")
                return False
        
        # Verificar si estamos dentro de la ventana de 24 horas
        current_time = timezone.now().timestamp()
        time_diff = current_time - last_interaction
        
        return time_diff < META_MESSAGE_WINDOW
            
    async def _log_notification(
        self,
        recipient: Person,
        template: str,
        channels: List[str],
        business_unit: Optional[str] = None,
        context: Optional[Dict] = None
    ) -> None:
        """
        Registra la notificación en la base de datos con clasificación automática 
        para optimización de costos de Meta.
        
        Args:
            recipient: Destinatario de la notificación
            template: Nombre de la plantilla utilizada
            channels: Canales por los que se envió
            business_unit: Unidad de negocio (opcional)
            context: Contexto adicional para clasificación
        """
        try:
            # Crear notificación básica
            notification = Notification(
                recipient=recipient,
                template=template,
                channels=channels,
                business_unit=business_unit,
                status='sent',
                sent_at=timezone.now()
            )
            await sync_to_async(notification.save)()
            
            # Para canales de Meta (WhatsApp, Instagram, Messenger), optimizar y clasificar
            meta_channels = [ch for ch in channels if ch in ['whatsapp', 'instagram', 'messenger']]
            if meta_channels and hasattr(recipient, 'phone'):
                # Clasificar automáticamente
                content = template  # Usar nombre de template como base para clasificación
                model, msg_type, category = self.classify_message_content(content, context)
                
                # Verificar ventana de 24h solo para canales Meta
                is_in_window = False
                if recipient.phone:
                    is_in_window = await self.is_within_24h_window(recipient.phone)
                    
                # Determinar costo
                if is_in_window and model in ['service', 'utility']:
                    cost = 0.0
                else:
                    cost = None  # Se determinará por Meta
                
                # Registrar en MessageLog para cada canal Meta
                for channel in meta_channels:
                    await sync_to_async(lambda: MessageLog.objects.create(
                        business_unit=business_unit,
                        channel=channel,
                        template_name=template,
                        meta_pricing_model=model,
                        meta_pricing_type=msg_type,
                        meta_pricing_category=category,
                        meta_cost=cost,
                        message_type=channel.upper(),
                        phone=recipient.phone,
                        meta_within_24h_window=is_in_window,
                        flow_context=context.get('flow_type', '') if context else '',
                        sent_at=timezone.now(),
                        status='SENT'
                    ))()
                    
        except Exception as e:
            self.logger.error(f"Error registrando notificación: {str(e)}", exc_info=True)

# Instancia global para uso sencillo
notification_service = NotificationService()
