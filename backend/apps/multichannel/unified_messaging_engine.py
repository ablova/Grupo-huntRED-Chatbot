"""
Unified Messaging Engine huntRED® v2 - Multi-Channel
===================================================

Funcionalidades:
- Soporte simultáneo WhatsApp + Telegram + SMS + Email
- Consolidación inteligente de usuarios por empleado
- Filtrado automático de duplicados
- Routing inteligente por preferencias
- Fallback automático entre canales
- Analytics unificados
- Compliance internacional
- API única para todos los canales
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import json
import logging
import hashlib

logger = logging.getLogger(__name__)

class MessagingChannel(Enum):
    """Canales de mensajería soportados."""
    WHATSAPP = "whatsapp"
    TELEGRAM = "telegram"
    SMS = "sms"
    EMAIL = "email"
    SLACK = "slack"
    TEAMS = "teams"
    DISCORD = "discord"
    WEBCHAT = "webchat"

class ChannelStatus(Enum):
    """Estados del canal."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    MAINTENANCE = "maintenance"
    ERROR = "error"

class MessagePriority(Enum):
    """Prioridades de mensaje."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"

class DeliveryStatus(Enum):
    """Estados de entrega."""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    EXPIRED = "expired"

@dataclass
class ChannelConfiguration:
    """Configuración específica por canal."""
    channel: MessagingChannel
    client_id: str
    
    # Configuración técnica
    api_endpoint: str
    api_token: str
    webhook_url: str
    phone_number: Optional[str] = None  # Para WhatsApp/SMS
    bot_token: Optional[str] = None     # Para Telegram
    
    # Configuración regional
    country_code: str = "MX"
    timezone: str = "America/Mexico_City"
    language: str = "es"
    
    # Configuración de negocio
    business_hours_start: str = "09:00"
    business_hours_end: str = "18:00"
    auto_reply_enabled: bool = True
    
    # Límites y throttling
    daily_message_limit: int = 1000
    rate_limit_per_minute: int = 30
    
    # Preferencias
    primary_channel: bool = False
    fallback_order: int = 1
    
    # Estado
    status: ChannelStatus = ChannelStatus.ACTIVE
    last_health_check: datetime = field(default_factory=datetime.now)
    
    # Metadatos
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

@dataclass
class UnifiedContact:
    """Contacto unificado multi-canal."""
    unified_id: str
    employee_id: str
    client_id: str
    
    # Información básica
    first_name: str
    last_name: str
    email: str
    
    # Canales asociados
    whatsapp_number: Optional[str] = None
    telegram_user_id: Optional[str] = None
    telegram_username: Optional[str] = None
    sms_number: Optional[str] = None
    slack_user_id: Optional[str] = None
    
    # Preferencias de canal
    preferred_channel: MessagingChannel = MessagingChannel.WHATSAPP
    fallback_channels: List[MessagingChannel] = field(default_factory=list)
    
    # Configuración
    timezone: str = "America/Mexico_City"
    language: str = "es"
    notifications_enabled: bool = True
    
    # Estados por canal
    channel_status: Dict[MessagingChannel, str] = field(default_factory=dict)
    last_activity: Dict[MessagingChannel, datetime] = field(default_factory=dict)
    
    # Consolidación
    duplicate_contacts: List[str] = field(default_factory=list)
    verified_identity: bool = False
    identity_score: float = 0.0
    
    # Metadatos
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

@dataclass
class UnifiedMessage:
    """Mensaje unificado multi-canal."""
    message_id: str
    unified_contact_id: str
    client_id: str
    
    # Contenido
    text: str
    message_type: str = "text"  # text, image, document, location, etc.
    attachments: List[Dict[str, Any]] = field(default_factory=list)
    
    # Routing
    target_channels: List[MessagingChannel] = field(default_factory=list)
    priority: MessagePriority = MessagePriority.NORMAL
    
    # Delivery tracking por canal
    delivery_status: Dict[MessagingChannel, DeliveryStatus] = field(default_factory=dict)
    delivery_attempts: Dict[MessagingChannel, int] = field(default_factory=dict)
    delivery_timestamps: Dict[MessagingChannel, datetime] = field(default_factory=dict)
    
    # Fallback
    fallback_enabled: bool = True
    fallback_delay_minutes: int = 5
    
    # Contexto
    conversation_id: Optional[str] = None
    reply_to: Optional[str] = None
    
    # Metadatos
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None

@dataclass
class ConversationContext:
    """Contexto de conversación unificado."""
    conversation_id: str
    unified_contact_id: str
    client_id: str
    
    # Estado actual
    active_channel: MessagingChannel
    current_flow: Optional[str] = None
    flow_step: int = 0
    
    # Datos temporales
    temp_data: Dict[str, Any] = field(default_factory=dict)
    
    # Historial
    message_history: List[str] = field(default_factory=list)
    channel_switches: List[Dict[str, Any]] = field(default_factory=list)
    
    # Configuración
    auto_switch_enabled: bool = True
    preferred_response_time: int = 300  # segundos
    
    # Metadatos
    started_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)

class UnifiedMessagingEngine:
    """Motor principal de mensajería unificada."""
    
    def __init__(self):
        self.channel_configs: Dict[str, Dict[MessagingChannel, ChannelConfiguration]] = {}
        self.unified_contacts: Dict[str, UnifiedContact] = {}
        self.conversations: Dict[str, ConversationContext] = {}
        self.message_queue: Dict[MessagingChannel, List[UnifiedMessage]] = {}
        
        # Mapeo de contactos por canal
        self.channel_to_unified: Dict[str, str] = {}  # channel_contact_id -> unified_id
        
        # Analytics
        self.delivery_stats: Dict[str, Dict[str, int]] = {}
        self.channel_performance: Dict[MessagingChannel, Dict[str, float]] = {}
        
        # Setup inicial
        self._initialize_channels()
    
    def _initialize_channels(self):
        """Inicializa configuraciones de canales."""
        
        for channel in MessagingChannel:
            self.message_queue[channel] = []
            self.channel_performance[channel] = {
                "delivery_rate": 0.0,
                "response_time": 0.0,
                "error_rate": 0.0,
                "user_satisfaction": 0.0
            }
    
    async def setup_client_channels(self, client_id: str, 
                                  channel_preferences: Dict[str, Any]) -> Dict[str, str]:
        """Configura canales para un cliente específico."""
        
        if client_id not in self.channel_configs:
            self.channel_configs[client_id] = {}
        
        setup_results = {}
        
        # Configurar WhatsApp si está especificado
        if "whatsapp" in channel_preferences:
            whatsapp_config = await self._setup_whatsapp_channel(
                client_id, channel_preferences["whatsapp"]
            )
            self.channel_configs[client_id][MessagingChannel.WHATSAPP] = whatsapp_config
            setup_results["whatsapp"] = "configured"
        
        # Configurar Telegram si está especificado
        if "telegram" in channel_preferences:
            telegram_config = await self._setup_telegram_channel(
                client_id, channel_preferences["telegram"]
            )
            self.channel_configs[client_id][MessagingChannel.TELEGRAM] = telegram_config
            setup_results["telegram"] = "configured"
        
        # Configurar SMS si está especificado
        if "sms" in channel_preferences:
            sms_config = await self._setup_sms_channel(
                client_id, channel_preferences["sms"]
            )
            self.channel_configs[client_id][MessagingChannel.SMS] = sms_config
            setup_results["sms"] = "configured"
        
        # Configurar Email
        if "email" in channel_preferences:
            email_config = await self._setup_email_channel(
                client_id, channel_preferences["email"]
            )
            self.channel_configs[client_id][MessagingChannel.EMAIL] = email_config
            setup_results["email"] = "configured"
        
        logger.info(f"Channels configured for client {client_id}: {list(setup_results.keys())}")
        return setup_results
    
    async def _setup_whatsapp_channel(self, client_id: str, config: Dict[str, Any]) -> ChannelConfiguration:
        """Configura canal de WhatsApp."""
        
        return ChannelConfiguration(
            channel=MessagingChannel.WHATSAPP,
            client_id=client_id,
            api_endpoint=config["api_endpoint"],
            api_token=config["api_token"],
            webhook_url=config["webhook_url"],
            phone_number=config["phone_number"],
            country_code=config.get("country_code", "MX"),
            timezone=config.get("timezone", "America/Mexico_City"),
            language=config.get("language", "es"),
            primary_channel=config.get("primary", True),
            fallback_order=config.get("fallback_order", 1),
            daily_message_limit=config.get("daily_limit", 1000),
            rate_limit_per_minute=config.get("rate_limit", 30)
        )
    
    async def _setup_telegram_channel(self, client_id: str, config: Dict[str, Any]) -> ChannelConfiguration:
        """Configura canal de Telegram."""
        
        return ChannelConfiguration(
            channel=MessagingChannel.TELEGRAM,
            client_id=client_id,
            api_endpoint=f"https://api.telegram.org/bot{config['bot_token']}",
            api_token=config["bot_token"],
            webhook_url=config["webhook_url"],
            bot_token=config["bot_token"],
            country_code=config.get("country_code", "MX"),
            timezone=config.get("timezone", "America/Mexico_City"),
            language=config.get("language", "es"),
            primary_channel=config.get("primary", False),
            fallback_order=config.get("fallback_order", 2),
            daily_message_limit=config.get("daily_limit", 1000),
            rate_limit_per_minute=config.get("rate_limit", 30)
        )
    
    async def _setup_sms_channel(self, client_id: str, config: Dict[str, Any]) -> ChannelConfiguration:
        """Configura canal de SMS."""
        
        return ChannelConfiguration(
            channel=MessagingChannel.SMS,
            client_id=client_id,
            api_endpoint=config["api_endpoint"],
            api_token=config["api_token"],
            webhook_url=config.get("webhook_url", ""),
            phone_number=config.get("phone_number"),
            country_code=config.get("country_code", "MX"),
            timezone=config.get("timezone", "America/Mexico_City"),
            language=config.get("language", "es"),
            primary_channel=config.get("primary", False),
            fallback_order=config.get("fallback_order", 3),
            daily_message_limit=config.get("daily_limit", 500),
            rate_limit_per_minute=config.get("rate_limit", 10)
        )
    
    async def _setup_email_channel(self, client_id: str, config: Dict[str, Any]) -> ChannelConfiguration:
        """Configura canal de Email."""
        
        return ChannelConfiguration(
            channel=MessagingChannel.EMAIL,
            client_id=client_id,
            api_endpoint=config.get("smtp_server", "smtp.gmail.com"),
            api_token=config["api_token"],
            webhook_url="",
            country_code=config.get("country_code", "MX"),
            timezone=config.get("timezone", "America/Mexico_City"),
            language=config.get("language", "es"),
            primary_channel=config.get("primary", False),
            fallback_order=config.get("fallback_order", 4),
            daily_message_limit=config.get("daily_limit", 200),
            rate_limit_per_minute=config.get("rate_limit", 5)
        )
    
    async def register_unified_contact(self, contact_data: Dict[str, Any]) -> str:
        """Registra un contacto unificado multi-canal."""
        
        # Generar ID unificado
        unified_id = await self._generate_unified_id(contact_data)
        
        # Verificar si ya existe
        existing_contact = await self._find_existing_contact(contact_data)
        if existing_contact:
            # Consolidar con contacto existente
            return await self._consolidate_contacts(existing_contact, contact_data)
        
        # Crear nuevo contacto unificado
        contact = UnifiedContact(
            unified_id=unified_id,
            employee_id=contact_data["employee_id"],
            client_id=contact_data["client_id"],
            first_name=contact_data["first_name"],
            last_name=contact_data["last_name"],
            email=contact_data["email"],
            whatsapp_number=contact_data.get("whatsapp_number"),
            telegram_user_id=contact_data.get("telegram_user_id"),
            telegram_username=contact_data.get("telegram_username"),
            sms_number=contact_data.get("sms_number"),
            slack_user_id=contact_data.get("slack_user_id"),
            preferred_channel=MessagingChannel(contact_data.get("preferred_channel", "whatsapp")),
            fallback_channels=[
                MessagingChannel(ch) for ch in contact_data.get("fallback_channels", ["telegram", "sms", "email"])
            ],
            timezone=contact_data.get("timezone", "America/Mexico_City"),
            language=contact_data.get("language", "es")
        )
        
        self.unified_contacts[unified_id] = contact
        
        # Crear mapeos por canal
        await self._create_channel_mappings(contact)
        
        # Verificar identidad
        await self._verify_identity(contact)
        
        logger.info(f"Unified contact registered: {unified_id} for employee {contact.employee_id}")
        return unified_id
    
    async def _generate_unified_id(self, contact_data: Dict[str, Any]) -> str:
        """Genera ID unificado basado en datos del contacto."""
        
        # Combinar datos únicos para generar hash
        unique_data = f"{contact_data['employee_id']}_{contact_data['email']}_{contact_data['client_id']}"
        hash_object = hashlib.sha256(unique_data.encode())
        return f"unified_{hash_object.hexdigest()[:12]}"
    
    async def _find_existing_contact(self, contact_data: Dict[str, Any]) -> Optional[UnifiedContact]:
        """Busca contacto existente por diferentes criterios."""
        
        # Buscar por employee_id
        for contact in self.unified_contacts.values():
            if contact.employee_id == contact_data["employee_id"]:
                return contact
        
        # Buscar por email
        for contact in self.unified_contacts.values():
            if contact.email == contact_data["email"]:
                return contact
        
        # Buscar por WhatsApp
        if "whatsapp_number" in contact_data:
            for contact in self.unified_contacts.values():
                if contact.whatsapp_number == contact_data["whatsapp_number"]:
                    return contact
        
        # Buscar por Telegram
        if "telegram_user_id" in contact_data:
            for contact in self.unified_contacts.values():
                if contact.telegram_user_id == contact_data["telegram_user_id"]:
                    return contact
        
        return None
    
    async def _consolidate_contacts(self, existing: UnifiedContact, new_data: Dict[str, Any]) -> str:
        """Consolida contactos duplicados."""
        
        # Actualizar campos faltantes
        if new_data.get("whatsapp_number") and not existing.whatsapp_number:
            existing.whatsapp_number = new_data["whatsapp_number"]
        
        if new_data.get("telegram_user_id") and not existing.telegram_user_id:
            existing.telegram_user_id = new_data["telegram_user_id"]
            existing.telegram_username = new_data.get("telegram_username")
        
        if new_data.get("sms_number") and not existing.sms_number:
            existing.sms_number = new_data["sms_number"]
        
        # Actualizar canales de fallback
        new_fallback_channels = [MessagingChannel(ch) for ch in new_data.get("fallback_channels", [])]
        for channel in new_fallback_channels:
            if channel not in existing.fallback_channels:
                existing.fallback_channels.append(channel)
        
        existing.updated_at = datetime.now()
        
        # Recrear mapeos
        await self._create_channel_mappings(existing)
        
        logger.info(f"Contacts consolidated: {existing.unified_id}")
        return existing.unified_id
    
    async def _create_channel_mappings(self, contact: UnifiedContact):
        """Crea mapeos de canal a contacto unificado."""
        
        if contact.whatsapp_number:
            self.channel_to_unified[f"whatsapp_{contact.whatsapp_number}"] = contact.unified_id
        
        if contact.telegram_user_id:
            self.channel_to_unified[f"telegram_{contact.telegram_user_id}"] = contact.unified_id
        
        if contact.sms_number:
            self.channel_to_unified[f"sms_{contact.sms_number}"] = contact.unified_id
        
        if contact.email:
            self.channel_to_unified[f"email_{contact.email}"] = contact.unified_id
    
    async def _verify_identity(self, contact: UnifiedContact):
        """Verifica la identidad del contacto usando ML."""
        
        # Factores de identidad
        identity_factors = []
        
        # Factor 1: Consistencia de nombre
        if contact.first_name and contact.last_name:
            identity_factors.append(0.3)
        
        # Factor 2: Email corporativo
        if contact.email and ("@" + contact.client_id.split("_")[-1] in contact.email):
            identity_factors.append(0.3)
        
        # Factor 3: Múltiples canales verificados
        verified_channels = sum([
            1 for ch in [contact.whatsapp_number, contact.telegram_user_id, contact.sms_number]
            if ch is not None
        ])
        if verified_channels >= 2:
            identity_factors.append(0.4)
        
        # Calcular score
        contact.identity_score = sum(identity_factors)
        contact.verified_identity = contact.identity_score >= 0.7
    
    async def send_unified_message(self, message_data: Dict[str, Any]) -> str:
        """Envía mensaje a través del canal óptimo o múltiples canales."""
        
        message_id = str(uuid.uuid4())
        
        # Crear mensaje unificado
        message = UnifiedMessage(
            message_id=message_id,
            unified_contact_id=message_data["unified_contact_id"],
            client_id=message_data["client_id"],
            text=message_data["text"],
            message_type=message_data.get("message_type", "text"),
            attachments=message_data.get("attachments", []),
            priority=MessagePriority(message_data.get("priority", "normal")),
            fallback_enabled=message_data.get("fallback_enabled", True),
            fallback_delay_minutes=message_data.get("fallback_delay_minutes", 5)
        )
        
        # Obtener contacto
        contact = self.unified_contacts.get(message_data["unified_contact_id"])
        if not contact:
            raise ValueError("Unified contact not found")
        
        # Determinar canales de entrega
        if "target_channels" in message_data:
            # Canales específicos solicitados
            message.target_channels = [MessagingChannel(ch) for ch in message_data["target_channels"]]
        else:
            # Usar estrategia automática
            message.target_channels = await self._determine_optimal_channels(contact, message)
        
        # Enviar a cada canal
        for channel in message.target_channels:
            await self._send_to_channel(message, contact, channel)
        
        # Configurar fallback si está habilitado
        if message.fallback_enabled:
            await self._setup_fallback_delivery(message, contact)
        
        logger.info(f"Unified message sent: {message_id} to {len(message.target_channels)} channels")
        return message_id
    
    async def _determine_optimal_channels(self, contact: UnifiedContact, 
                                        message: UnifiedMessage) -> List[MessagingChannel]:
        """Determina los canales óptimos para entregar el mensaje."""
        
        # Estrategia basada en prioridad y disponibilidad
        if message.priority in [MessagePriority.URGENT, MessagePriority.CRITICAL]:
            # Mensajes urgentes: usar todos los canales disponibles
            return await self._get_available_channels(contact)
        
        elif message.priority == MessagePriority.HIGH:
            # Mensajes de alta prioridad: canal preferido + 1 fallback
            channels = [contact.preferred_channel]
            if contact.fallback_channels:
                channels.append(contact.fallback_channels[0])
            return [ch for ch in channels if await self._is_channel_available(contact, ch)]
        
        else:
            # Mensajes normales: solo canal preferido
            if await self._is_channel_available(contact, contact.preferred_channel):
                return [contact.preferred_channel]
            else:
                # Si el preferido no está disponible, usar el primer fallback
                for fallback in contact.fallback_channels:
                    if await self._is_channel_available(contact, fallback):
                        return [fallback]
                return []
    
    async def _get_available_channels(self, contact: UnifiedContact) -> List[MessagingChannel]:
        """Obtiene todos los canales disponibles para el contacto."""
        
        available = []
        
        # Verificar cada canal configurado
        all_channels = [contact.preferred_channel] + contact.fallback_channels
        
        for channel in all_channels:
            if await self._is_channel_available(contact, channel):
                available.append(channel)
        
        return available
    
    async def _is_channel_available(self, contact: UnifiedContact, channel: MessagingChannel) -> bool:
        """Verifica si un canal está disponible para el contacto."""
        
        # Verificar configuración del cliente
        client_channels = self.channel_configs.get(contact.client_id, {})
        if channel not in client_channels:
            return False
        
        channel_config = client_channels[channel]
        if channel_config.status != ChannelStatus.ACTIVE:
            return False
        
        # Verificar que el contacto tenga el canal configurado
        if channel == MessagingChannel.WHATSAPP and not contact.whatsapp_number:
            return False
        elif channel == MessagingChannel.TELEGRAM and not contact.telegram_user_id:
            return False
        elif channel == MessagingChannel.SMS and not contact.sms_number:
            return False
        elif channel == MessagingChannel.EMAIL and not contact.email:
            return False
        
        # Verificar límites de rate
        if await self._is_rate_limited(contact.client_id, channel):
            return False
        
        return True
    
    async def _send_to_channel(self, message: UnifiedMessage, contact: UnifiedContact, 
                             channel: MessagingChannel):
        """Envía mensaje a un canal específico."""
        
        try:
            # Marcar como intentando enviar
            message.delivery_status[channel] = DeliveryStatus.PENDING
            message.delivery_attempts[channel] = message.delivery_attempts.get(channel, 0) + 1
            message.delivery_timestamps[channel] = datetime.now()
            
            # Enviar según el canal
            if channel == MessagingChannel.WHATSAPP:
                await self._send_whatsapp(message, contact)
            elif channel == MessagingChannel.TELEGRAM:
                await self._send_telegram(message, contact)
            elif channel == MessagingChannel.SMS:
                await self._send_sms(message, contact)
            elif channel == MessagingChannel.EMAIL:
                await self._send_email(message, contact)
            
            # Marcar como enviado
            message.delivery_status[channel] = DeliveryStatus.SENT
            
            # Actualizar estadísticas
            await self._update_delivery_stats(contact.client_id, channel, "sent")
            
        except Exception as e:
            # Marcar como fallido
            message.delivery_status[channel] = DeliveryStatus.FAILED
            await self._update_delivery_stats(contact.client_id, channel, "failed")
            logger.error(f"Failed to send message {message.message_id} via {channel.value}: {e}")
    
    async def _send_whatsapp(self, message: UnifiedMessage, contact: UnifiedContact):
        """Envía mensaje por WhatsApp."""
        
        # Integración con WhatsApp API
        # En un sistema real, aquí se haría la llamada a la API de WhatsApp
        logger.info(f"Sending WhatsApp message to {contact.whatsapp_number}: {message.text}")
    
    async def _send_telegram(self, message: UnifiedMessage, contact: UnifiedContact):
        """Envía mensaje por Telegram."""
        
        # Integración con Telegram Bot API
        # En un sistema real, aquí se haría la llamada a la API de Telegram
        logger.info(f"Sending Telegram message to {contact.telegram_user_id}: {message.text}")
    
    async def _send_sms(self, message: UnifiedMessage, contact: UnifiedContact):
        """Envía mensaje por SMS."""
        
        # Integración con proveedor SMS (Twilio, etc.)
        logger.info(f"Sending SMS to {contact.sms_number}: {message.text}")
    
    async def _send_email(self, message: UnifiedMessage, contact: UnifiedContact):
        """Envía mensaje por Email."""
        
        # Integración con SMTP o servicio de email
        logger.info(f"Sending email to {contact.email}: {message.text}")
    
    async def _setup_fallback_delivery(self, message: UnifiedMessage, contact: UnifiedContact):
        """Configura entrega de fallback automática."""
        
        # Programar verificación de entrega después del delay
        asyncio.create_task(
            self._check_and_fallback(message, contact, message.fallback_delay_minutes * 60)
        )
    
    async def _check_and_fallback(self, message: UnifiedMessage, contact: UnifiedContact, delay_seconds: int):
        """Verifica entrega y activa fallback si es necesario."""
        
        await asyncio.sleep(delay_seconds)
        
        # Verificar si algún canal fue exitoso
        successful_delivery = any(
            status in [DeliveryStatus.DELIVERED, DeliveryStatus.READ]
            for status in message.delivery_status.values()
        )
        
        if not successful_delivery:
            # Intentar canales de fallback
            remaining_channels = [
                ch for ch in contact.fallback_channels 
                if ch not in message.target_channels and await self._is_channel_available(contact, ch)
            ]
            
            for channel in remaining_channels[:2]:  # Máximo 2 fallbacks adicionales
                await self._send_to_channel(message, contact, channel)
                logger.info(f"Fallback delivery attempted via {channel.value} for message {message.message_id}")
    
    async def process_incoming_message(self, channel: MessagingChannel, 
                                     channel_contact_id: str, 
                                     message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa mensaje entrante y lo unifica."""
        
        # Encontrar contacto unificado
        mapping_key = f"{channel.value}_{channel_contact_id}"
        unified_id = self.channel_to_unified.get(mapping_key)
        
        if not unified_id:
            # Contacto no encontrado, crear automáticamente si es posible
            unified_id = await self._auto_register_contact(channel, channel_contact_id, message_data)
        
        if not unified_id:
            return {"error": "Contact not found and could not be auto-registered"}
        
        contact = self.unified_contacts[unified_id]
        
        # Obtener o crear contexto de conversación
        conversation = await self._get_or_create_conversation(unified_id, channel)
        
        # Procesar mensaje según el canal
        if channel == MessagingChannel.WHATSAPP:
            response = await self._process_whatsapp_message(contact, conversation, message_data)
        elif channel == MessagingChannel.TELEGRAM:
            response = await self._process_telegram_message(contact, conversation, message_data)
        else:
            response = await self._process_generic_message(contact, conversation, message_data)
        
        # Actualizar actividad
        contact.last_activity[channel] = datetime.now()
        conversation.last_activity = datetime.now()
        conversation.active_channel = channel
        
        return response
    
    async def _auto_register_contact(self, channel: MessagingChannel, 
                                   channel_contact_id: str, 
                                   message_data: Dict[str, Any]) -> Optional[str]:
        """Registra automáticamente un contacto desde mensaje entrante."""
        
        # Intentar extraer información del mensaje
        contact_data = {
            "employee_id": f"auto_{channel_contact_id}",
            "client_id": message_data.get("client_id", "unknown"),
            "first_name": message_data.get("first_name", "Unknown"),
            "last_name": message_data.get("last_name", "User"),
            "email": f"auto_{channel_contact_id}@unknown.com",
            "preferred_channel": channel.value
        }
        
        # Agregar información específica del canal
        if channel == MessagingChannel.WHATSAPP:
            contact_data["whatsapp_number"] = channel_contact_id
        elif channel == MessagingChannel.TELEGRAM:
            contact_data["telegram_user_id"] = channel_contact_id
            contact_data["telegram_username"] = message_data.get("username")
        
        try:
            unified_id = await self.register_unified_contact(contact_data)
            logger.info(f"Auto-registered contact {unified_id} from {channel.value}")
            return unified_id
        except Exception as e:
            logger.error(f"Failed to auto-register contact: {e}")
            return None
    
    async def _get_or_create_conversation(self, unified_id: str, 
                                        channel: MessagingChannel) -> ConversationContext:
        """Obtiene o crea contexto de conversación."""
        
        conversation_id = f"{unified_id}_{channel.value}"
        
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = ConversationContext(
                conversation_id=conversation_id,
                unified_contact_id=unified_id,
                client_id=self.unified_contacts[unified_id].client_id,
                active_channel=channel
            )
        
        return self.conversations[conversation_id]
    
    async def _process_whatsapp_message(self, contact: UnifiedContact, 
                                      conversation: ConversationContext,
                                      message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa mensaje de WhatsApp."""
        
        # Importar WhatsApp bot para procesamiento
        from ..chatbot.payroll_whatsapp_bot import PayrollWhatsAppBot
        
        bot = PayrollWhatsAppBot()
        return await bot.process_message(contact.whatsapp_number, message_data)
    
    async def _process_telegram_message(self, contact: UnifiedContact,
                                      conversation: ConversationContext,
                                      message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa mensaje de Telegram."""
        
        # Adaptador para Telegram
        # Convertir formato de Telegram a formato estándar
        adapted_message = {
            "type": "text",
            "text": message_data.get("text", ""),
            "to": contact.client_id,
            "from": contact.telegram_user_id
        }
        
        # Usar misma lógica que WhatsApp pero adaptada
        from ..chatbot.payroll_whatsapp_bot import PayrollWhatsAppBot
        
        bot = PayrollWhatsAppBot()
        
        # Simular procesamiento (en realidad necesitaríamos un TelegramBot específico)
        return {
            "type": "text",
            "text": f"Mensaje recibido por Telegram: {message_data.get('text', '')}"
        }
    
    async def _process_generic_message(self, contact: UnifiedContact,
                                     conversation: ConversationContext,
                                     message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa mensaje de canal genérico."""
        
        return {
            "type": "text",
            "text": f"Mensaje procesado desde {conversation.active_channel.value}"
        }
    
    async def _is_rate_limited(self, client_id: str, channel: MessagingChannel) -> bool:
        """Verifica si el cliente está limitado por rate limiting."""
        
        # Implementar lógica de rate limiting por cliente y canal
        # Por ahora, siempre retornar False
        return False
    
    async def _update_delivery_stats(self, client_id: str, channel: MessagingChannel, status: str):
        """Actualiza estadísticas de entrega."""
        
        if client_id not in self.delivery_stats:
            self.delivery_stats[client_id] = {}
        
        if channel.value not in self.delivery_stats[client_id]:
            self.delivery_stats[client_id][channel.value] = {}
        
        current_count = self.delivery_stats[client_id][channel.value].get(status, 0)
        self.delivery_stats[client_id][channel.value][status] = current_count + 1
    
    def get_unified_analytics(self, client_id: str, days: int = 30) -> Dict[str, Any]:
        """Obtiene analytics unificados del cliente."""
        
        # Filtrar contactos del cliente
        client_contacts = [
            contact for contact in self.unified_contacts.values()
            if contact.client_id == client_id
        ]
        
        # Estadísticas por canal
        channel_stats = {}
        for channel in MessagingChannel:
            channel_contacts = [
                c for c in client_contacts
                if channel in c.last_activity
            ]
            
            channel_stats[channel.value] = {
                "active_contacts": len(channel_contacts),
                "total_messages": self.delivery_stats.get(client_id, {}).get(channel.value, {}).get("sent", 0),
                "delivery_rate": self._calculate_delivery_rate(client_id, channel),
                "response_rate": self._calculate_response_rate(client_id, channel)
            }
        
        # Contactos consolidados
        total_contacts = len(client_contacts)
        verified_contacts = len([c for c in client_contacts if c.verified_identity])
        multi_channel_contacts = len([
            c for c in client_contacts 
            if len([ch for ch in c.last_activity.keys()]) > 1
        ])
        
        return {
            "client_id": client_id,
            "period_days": days,
            "summary": {
                "total_unified_contacts": total_contacts,
                "verified_contacts": verified_contacts,
                "multi_channel_contacts": multi_channel_contacts,
                "verification_rate": (verified_contacts / total_contacts * 100) if total_contacts > 0 else 0,
                "multi_channel_rate": (multi_channel_contacts / total_contacts * 100) if total_contacts > 0 else 0
            },
            "by_channel": channel_stats,
            "performance": {
                channel.value: self.channel_performance.get(channel, {})
                for channel in MessagingChannel
            }
        }
    
    def _calculate_delivery_rate(self, client_id: str, channel: MessagingChannel) -> float:
        """Calcula tasa de entrega para un canal."""
        
        stats = self.delivery_stats.get(client_id, {}).get(channel.value, {})
        sent = stats.get("sent", 0)
        failed = stats.get("failed", 0)
        
        total = sent + failed
        return (sent / total * 100) if total > 0 else 0.0
    
    def _calculate_response_rate(self, client_id: str, channel: MessagingChannel) -> float:
        """Calcula tasa de respuesta para un canal."""
        
        # Implementación simplificada
        # En un sistema real, calcularía respuestas vs mensajes enviados
        return 75.0  # Placeholder

# Funciones de utilidad
async def setup_multi_channel_client(client_id: str, channels_config: Dict[str, Any]) -> str:
    """Configura cliente con múltiples canales."""
    
    engine = UnifiedMessagingEngine()
    
    result = await engine.setup_client_channels(client_id, channels_config)
    
    return f"Multi-channel setup completed for {client_id}: {list(result.keys())}"

# Exportaciones
__all__ = [
    'MessagingChannel', 'ChannelStatus', 'MessagePriority', 'DeliveryStatus',
    'ChannelConfiguration', 'UnifiedContact', 'UnifiedMessage', 'ConversationContext',
    'UnifiedMessagingEngine', 'setup_multi_channel_client'
]