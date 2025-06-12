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
from django.conf import settings
from django.template.loader import render_to_string
from django.core.cache import cache
from django.db.models import Prefetch
from django.utils.module_loading import import_string
from app.models import (
    Notification, NotificationChannel, Person, Feedback, BusinessUnit
)
from app.ats.utils import logger_utils
from app.ats.integrations.notifications.channels.base import BaseNotificationChannel
import logging
import asyncio
import uuid
from datetime import timezone, timedelta
from asgiref.sync import sync_to_async
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configuración de caché
CACHE_TIMEOUT = 3600  # 1 hora
CHANNEL_CACHE_PREFIX = "notification_channels_"
TEMPLATE_CACHE_PREFIX = "notification_template_"

logger = logging.getLogger(__name__)

# Mapa de canales disponibles con sus pesos de prioridad (mayor = más prioridad)
CHANNEL_MAP = {
    'whatsapp': {
        'class': 'app.ats.integrations.notifications.channels.whatsapp.WhatsAppNotificationChannel',
        'priority': 40,
        'fallback': 'email'
    },
    'telegram': {
        'class': 'app.ats.integrations.notifications.channels.telegram.TelegramNotificationChannel',
        'priority': 30,
        'fallback': 'whatsapp'
    },
    'email': {
        'class': 'app.ats.integrations.notifications.channels.email.EmailNotificationChannel',
        'priority': 20,
        'fallback': None
    },
    'sms': {
        'class': 'app.ats.integrations.notifications.channels.sms.SMSNotificationChannel',
        'priority': 10,
        'fallback': 'email'
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
        restrict_channels: Optional[List[str]] = None,
        fallback_channels: Optional[Dict[str, List[str]]] = None,
        fallback_timeout: int = 0,
        priority: str = "normal"
    ) -> Dict[str, bool]:
        """
        Envía una notificación al destinatario usando la plantilla especificada.
        
        Por defecto, la notificación se envía por todos los canales disponibles.
        
        Args:
            recipient: Persona que recibirá la notificación
            template_name: Nombre de la plantilla a utilizar
            context: Contexto para la plantilla (opcional)
            channels: Canales específicos a utilizar (opcional, por defecto todos)
            business_unit: Unidad de negocio (opcional)
            restrict_channels: Lista de canales a los que restringir (opuesto a channels)
            fallback_channels: Mapa de canales de respaldo si falla el canal principal
            fallback_timeout: Tiempo en segundos para esperar antes de usar canales de respaldo
            priority: Prioridad de la notificación (low, normal, high)
            
        Returns:
            Dict[str, bool]: Diccionario con el estado de envío por canal
            
        Ejemplos:
            # Enviar por todos los canales disponibles
            await notification_service.send_notification(
                recipient=user,
                template_name="welcome"
            )
            
            # Restringir a canales específicos
            await notification_service.send_notification(
                recipient=user,
                template_name="important_update",
                channels=["email", "whatsapp"]
            )
            
            # Usar canales de respaldo
            await notification_service.send_notification(
                recipient=user,
                template_name="urgent",
                channels=["telegram"],
                fallback_channels={"telegram": ["email", "whatsapp"]},
                fallback_timeout=3600,  # 1 hora
                priority="high"
            )
        """
        context = context or {}
        notification_id = uuid.uuid4()
        results = {}
        
        # Determinar canales a utilizar
        if channels is None and restrict_channels is None:
            # Por defecto, usar todos los canales disponibles
            channels_to_use = await self.default_channels
        elif channels is not None:
            # Usar canales específicos si se proporcionan
            channels_to_use = [c for c in channels if c in self._available_channels]
        else:
            # Usar todos los canales excepto los restringidos
            channels_to_use = [c for c in await self.default_channels if c not in (restrict_channels or [])]
        
        # Obtener la instancia de BusinessUnit si se proporciona un nombre
        if isinstance(business_unit, str):
            try:
                business_unit = await sync_to_async(BusinessUnit.objects.get)(name=business_unit)
            except BusinessUnit.DoesNotExist:
                self.logger.warning(f"Unidad de negocio no encontrada: {business_unit}")
                business_unit = None
        
        # Usar la unidad de negocio del servicio si no se proporciona una
        business_unit = business_unit or self.business_unit
        
        try:
            # Renderizar plantilla
            template_path = f"notifications/{template_name}.txt"
            message = render_to_string(template_path, context)
            
            # Enviar por cada canal solicitado
            results = []
            for channel_name in channels:
                channel = await self._get_channel(channel_name)
                if not channel:
                    self.logger.warning(f"Canal no disponible: {channel_name}")
                    results.append(False)
                    continue
                
                try:
                    # Usar el método apropiado según el canal
                    if channel_name == 'email':
                        result = await channel.send(
                            to=recipient.email,
                            subject=context.get('subject', 'Notificación'),
                            message=message,
                            template_name=template_name,
                            context=context
                        )
                    elif channel_name == 'whatsapp':
                        result = await channel.send(
                            to=recipient.phone,
                            message=message,
                            template_name=template_name,
                            template_params=context
                        )
                    else:
                        # Método genérico para otros canales
                        result = await channel.send(
                            to=getattr(recipient, channel_name, None) or recipient.phone,
                            message=message,
                            **context
                        )
                    
                    results.append(bool(result))
                    
                except Exception as e:
                    self.logger.error(f"Error enviando notificación por {channel_name}: {str(e)}", exc_info=True)
                    results.append(False)
            
            # Registrar la notificación
            await self._log_notification(
                recipient=recipient,
                template=template_name,
                channels=channels,
                business_unit=business_unit.name if business_unit else None
            )
            
            return all(results)
            
        except Exception as e:
            self.logger.error(f"Error enviando notificación: {str(e)}", exc_info=True)
            return False
    
    async def send_template_notification(
        self,
        recipient: Person,
        template_name: str,
        context: Optional[Dict] = None,
        channels: Optional[List[str]] = None,
        business_unit: Optional[Union[str, BusinessUnit]] = None
    ) -> bool:
        """
        Envía una notificación usando una plantilla predefinida.
        
        Args:
            recipient: Persona que recibirá la notificación
            template_name: Nombre de la plantilla a utilizar
            context: Contexto para la plantilla
            channels: Canales a utilizar (email, whatsapp, etc.)
            business_unit: Unidad de negocio (opcional)
            
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
            business_unit=business_unit
        )
    
    async def _log_notification(
        self,
        recipient: Person,
        template: str,
        channels: List[str],
        business_unit: Optional[str] = None
    ) -> None:
        """
        Registra la notificación en la base de datos.
        
        Args:
            recipient: Destinatario de la notificación
            template: Nombre de la plantilla utilizada
            channels: Canales por los que se envió
            business_unit: Unidad de negocio (opcional)
        """
        try:
            notification = Notification(
                recipient=recipient,
                template=template,
                channels=channels,
                business_unit=business_unit,
                status='sent',
                sent_at=timezone.now()
            )
            await sync_to_async(notification.save)()
        except Exception as e:
            self.logger.error(f"Error registrando notificación: {str(e)}", exc_info=True)

# Instancia global para uso sencillo
notification_service = NotificationService()
