# /home/pablo/app/chatbot/integrations/services.py
import logging
import smtplib
import asyncio
import ssl
import itertools
import time
from asgiref.sync import sync_to_async
from typing import Optional, List, Dict, Union, Any, Tuple
from django.core.cache import cache
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from pathlib import Path
from tenacity import retry, stop_after_attempt
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from abc import ABC, abstractmethod
from datetime import datetime

from app.models import (
    BusinessUnit, ConfiguracionBU, WhatsAppAPI, TelegramAPI, SlackAPI,
    InstagramAPI, MessengerAPI, ChatState, Person,
    EnhancedNetworkGamificationProfile
)
import tracemalloc
tracemalloc.start()
logger = logging.getLogger('chatbot')

# Constantes globales
MAX_RETRIES = 3
REQUEST_TIMEOUT = 10.0
CACHE_TIMEOUT = 600  # 10 minutos
whatsapp_semaphore = asyncio.Semaphore(10)

# Menús dinámicos por unidad de negocio
MENU_OPTIONS_BY_BU = {
    "amigro": [
        {"title": "📝 Crear Perfil", "payload": "crear_perfil", "description": "Crea tu perfil con datos personales y profesionales."},
        {"title": "📝 Actualizar Perfil", "payload": "actualizar_perfil", "description": "Gestiona y actualiza tu perfil."},
        {"title": "💰 Calcular Salario", "payload": "calcular_salario", "description": "Calcula salario neto o bruto."},
        {"title": "📄 Cargar CV", "payload": "cargar_cv", "description": "Sube tu currículum."},
        {"title": "🧠 Prueba de Personalidad", "payload": "prueba_personalidad", "description": "Descubre tu perfil profesional."},
        {"title": "🤝 Invitar Grupo", "payload": "travel_in_group", "description": "Invita a amigos o familia."},
        {"title": "🔍 Ver Vacantes", "payload": "ver_vacantes", "description": "Explora oportunidades laborales disponibles."},
        {"title": "📊 Consultar Estatus", "payload": "consultar_estatus", "description": "Revisa el estado de tus aplicaciones."},
        {"title": "📞 Contacto", "payload": "contacto", "description": "Habla con un asesor."},
        {"title": "❓ Ayuda", "payload": "ayuda", "description": "Resuelve dudas generales."},
        {"title": "📜 Ver TOS", "payload": "tos_accept", "description": "Consulta los términos de servicio."},
    ],
    "huntred": [
        {"title": "📝 Creación  Perfil", "payload": "crear_perfil", "description": "Modifica tus datos personales o profesionales."},
        {"title": "🔍 Buscar Empleo", "payload": "buscar_empleo", "description": "Encuentra trabajos específicos."},
        {"title": "📝 Mi Perfil", "payload": "mi_perfil", "description": "Gestiona tu perfil."},
        {"title": "📊 Ver Vacantes", "payload": "ver_vacantes", "description": "Lista de empleos disponibles."},
        {"title": "📄 Cargar CV", "payload": "cargar_cv", "description": "Sube tu currículum."},
        {"title": "📅 Agendar Entrevista", "payload": "agendar_entrevista", "description": "Programa una entrevista."},
        {"title": "🧠 Prueba de Personalidad", "payload": "prueba_personalidad", "description": "Descubre tu perfil profesional."},
        {"title": "💰 Calcular Salario", "payload": "calcular_salario", "description": "Calcula salario neto o bruto."},
        {"title": "🤝 Recomendar a huntRED®", "payload": "travel_in_group", "description": "Invita a amigos o familia."},
        {"title": "❓ Ayuda", "payload": "ayuda", "description": "Soporte general."},
        {"title": "💡 Tips Entrevista", "payload": "preparacion_entrevista", "description": "Consejos para entrevistas."},
    ],
    "huntu": [
        {"title": "📝 Creación  Perfil", "payload": "crear_perfil", "description": "Modifica tus datos personales o profesionales."},
        {"title": "🔍 Explorar Vacantes", "payload": "explorar_vacantes", "description": "Descubre oportunidades únicas."},
        {"title": "📝 Mi Perfil", "payload": "mi_perfil", "description": "Actualiza tu información."},
        {"title": "📄 Cargar CV", "payload": "cargar_cv", "description": "Sube tu currículum."},
        {"title": "🧠 Prueba de Personalidad", "payload": "prueba_personalidad", "description": "Descubre tu perfil profesional."},
        {"title": "🧑‍🏫 Asesoría Profesional", "payload": "asesoria_profesional", "description": "Recibe orientación."},
        {"title": "🤝 Programa de Mentores", "payload": "mentores", "description": "Conéctate con mentores."},
        {"title": "🤝 Invitar a huntU®", "payload": "travel_in_group", "description": "Invita a amigos o familia."},
        {"title": "💰 Calcular Salario", "payload": "calcular_salario", "description": "Calcula salario neto o bruto."},
        {"title": "❓ Ayuda", "payload": "ayuda", "description": "Asistencia general."},
        {"title": "💰 Consultar Sueldo", "payload": "consultar_sueldo_mercado", "description": "Rangos salariales."},
    ],
    "default": [
        {"title": "🔍 Ver Vacantes", "payload": "ver_vacantes", "description": "Oportunidades disponibles."},
        {"title": "📝 Mi Perfil", "payload": "mi_perfil", "description": "Gestiona tu perfil."},
        {"title": "⚙️ Configuración", "payload": "configuracion", "description": "Ajustes personales."},
        {"title": "📄 Cargar CV", "payload": "cargar_cv", "description": "Sube tu currículum."},
        {"title": "💰 Calcular Salario", "payload": "calcular_salario", "description": "Calcula salario neto o bruto."},
        {"title": "📞 Contacto", "payload": "contacto", "description": "Habla con soporte."},
        {"title": "❓ Ayuda", "payload": "ayuda", "description": "Resuelve dudas."},
    ]
}

# Menús dinámicos por estado (para amigro)
MENU_OPTIONS_BY_STATE = {
    "amigro": {
        "initial": [
            {"title": "📝 Crear Perfil", "payload": "crear_perfil", "description": "Crea tu perfil con datos personales y profesionales."},
            {"title": "📜 Ver TOS", "payload": "tos_accept", "description": "Consulta los términos de servicio."},
            {"title": "💰 Calcular Salario", "payload": "calcular_salario", "description": "Calcula salario neto o bruto."},
            {"title": "🤝 Invitar a Amigro", "payload": "travel_in_group", "description": "Invita a amigos o familia."},
            {"title": "📞 Contacto", "payload": "contacto", "description": "Habla con un asesor."},
            {"title": "❓ Ayuda", "payload": "ayuda", "description": "Resuelve dudas generales."},
        ],
        "waiting_for_tos": [
            {"title": "📜 Ver TOS", "payload": "tos_accept", "description": "Consulta los términos de servicio."},
            {"title": "✅ Aceptar TOS", "payload": "accept_tos", "description": "Acepta los términos de servicio."},
            {"title": "❌ Rechazar TOS", "payload": "reject_tos", "description": "Rechaza los términos de servicio."},
            {"title": "💰 Calcular Salario", "payload": "calcular_salario", "description": "Calcula salario neto o bruto."},
            {"title": "🤝 Invitar a Amigro", "payload": "travel_in_group", "description": "Invita a amigos o familia."},
        ],
        "profile_in_progress": [
            {"title": "📝 Crear Perfil", "payload": "crear_perfil", "description": "Sigue completando tu perfil."},
            {"title": "📄 Cargar CV", "payload": "cargar_cv", "description": "Sube tu currículum."},
            {"title": "💰 Calcular Salario", "payload": "calcular_salario", "description": "Calcula salario neto o bruto."},
            {"title": "🤝 Invitar a Amigro", "payload": "travel_in_group", "description": "Invita a amigos o familia."},
            {"title": "📞 Contacto", "payload": "contacto", "description": "Habla con un asesor."},
            {"title": "❓ Ayuda / FAQ", "payload": "ayuda", "description": "Resuelve dudas generales."},
        ],
        "profile_complete": [
            {"title": "📝 Actualizar Perfil", "payload": "mi_perfil", "description": "Gestiona y actualiza tu perfil."},
            {"title": "🔍 Ver Vacantes", "payload": "ver_vacantes", "description": "Explora oportunidades laborales disponibles."},
            {"title": "🧠 Prueba de Personalidad", "payload": "prueba_personalidad", "description": "Descubre tu perfil profesional."},
            {"title": "💰 Calcular Salario", "payload": "calcular_salario", "description": "Calcula salario neto o bruto."},
            {"title": "🤝 Invitar a Amigro", "payload": "travel_in_group", "description": "Invita a amigos o familia."},
            {"title": "📞 Contacto", "payload": "contacto", "description": "Habla con un asesor."},
            {"title": "❓ Ayuda", "payload": "ayuda", "description": "Resuelve dudas generales."},
        ],
        "applied": [
            {"title": "📝 Actualizar Perfil", "payload": "mi_perfil", "description": "Gestiona y actualiza tu perfil."},
            {"title": "🔍 Ver Vacantes", "payload": "ver_vacantes", "description": "Explora oportunidades laborales disponibles."},
            {"title": "📊 Consultar Estatus", "payload": "consultar_estatus", "description": "Revisa el estado de tus aplicaciones."},
            {"title": "🧠 Prueba de Personalidad", "payload": "prueba_personalidad", "description": "Descubre tu perfil profesional."},
            {"title": "💰 Calcular Salario", "payload": "calcular_salario", "description": "Calcula salario neto o bruto."},
            {"title": "🤝 Recomendar", "payload": "travel_in_group", "description": "Invita a amigos o familia."},
            {"title": "📞 Contacto", "payload": "contacto", "description": "Habla con un asesor."},
            {"title": "❓ Ayuda", "payload": "ayuda", "description": "Resuelve dudas generales."},
        ],
        "scheduled": [
            {"title": "📝 Actualizar Perfil", "payload": "mi_perfil", "description": "Gestiona y actualiza tu perfil."},
            {"title": "🔍 Ver Vacantes", "payload": "ver_vacantes", "description": "Explora oportunidades laborales disponibles."},
            {"title": "📊 Consultar Estatus", "payload": "consultar_estatus", "description": "Revisa el estado de tus aplicaciones."},
            {"title": "🧠 Prueba de Personalidad", "payload": "prueba_personalidad", "description": "Descubre tu perfil profesional."},
            {"title": "📅 Reagendar Entrevista", "payload": "reagendar_entrevista", "description": "Modifica tu cita de entrevista."},
            {"title": "📩 Enviar Recordatorio", "payload": "recordatorio_entrevista", "description": "Solicita un recordatorio."},
            {"title": "💰 Calcular Salario", "payload": "calcular_salario", "description": "Calcula salario neto o bruto."},
            {"title": "🤝 Recomendar", "payload": "travel_in_group", "description": "Invita a amigos o familia."},
            {"title": "📞 Contacto", "payload": "contacto", "description": "Habla con un asesor."},
            {"title": "❓ Ayuda", "payload": "ayuda", "description": "Resuelve dudas generales."},
        ],
        "interviewed": [
            {"title": "📝 Actualizar Perfil", "payload": "mi_perfil", "description": "Gestiona y actualiza tu perfil."},
            {"title": "🔍 Ver Vacantes", "payload": "ver_vacantes", "description": "Explora oportunidades laborales disponibles."},
            {"title": "📊 Consultar Estatus", "payload": "consultar_estatus", "description": "Revisa el estado de tus aplicaciones."},
            {"title": "🧠 Prueba de Personalidad", "payload": "prueba_personalidad", "description": "Descubre tu perfil profesional."},
            {"title": "📝 Enviar Feedback", "payload": "enviar_feedback", "description": "Comparte tu experiencia de la entrevista."},
            {"title": "💰 Calcular Salario", "payload": "calcular_salario", "description": "Calcula salario neto o bruto."},
            {"title": "🤝 Recomendar", "payload": "travel_in_group", "description": "Invita a amigos o familia."},
            {"title": "📞 Contacto", "payload": "contacto", "description": "Habla con un asesor."},
            {"title": "❓ Ayuda", "payload": "ayuda", "description": "Resuelve dudas generales."},
        ],
        "offered": [
            {"title": "📝 Actualizar Perfil", "payload": "mi_perfil", "description": "Gestiona y actualiza tu perfil."},
            {"title": "🔍 Ver Vacantes", "payload": "ver_vacantes", "description": "Explora oportunidades laborales disponibles."},
            {"title": "📊 Consultar Estatus", "payload": "consultar_estatus", "description": "Revisa el estado de tus aplicaciones."},
            {"title": "🧠 Prueba de Personalidad", "payload": "prueba_personalidad", "description": "Descubre tu perfil profesional."},
            {"title": "📜 Ver Oferta", "payload": "ver_oferta", "description": "Consulta los detalles de tu oferta."},
            {"title": "💰 Calcular Salario", "payload": "calcular_salario", "description": "Calcula salario neto o bruto."},
            {"title": "🤝 Recomendar", "payload": "travel_in_group", "description": "Invita a amigos o familia."},
            {"title": "📞 Contacto", "payload": "contacto", "description": "Habla con un asesor."},
            {"title": "❓ Ayuda", "payload": "ayuda", "description": "Resuelve dudas generales."},
        ],
        "signed": [
            {"title": "📝 Actualizar Perfil", "payload": "mi_perfil", "description": "Gestiona y actualiza tu perfil."},
            {"title": "🔍 Ver Vacantes", "payload": "ver_vacantes", "description": "Explora oportunidades laborales disponibles."},
            {"title": "📊 Consultar Estatus", "payload": "consultar_estatus", "description": "Revisa el estado de tus aplicaciones."},
            {"title": "📜 Descargar Oferta", "payload": "descargar_oferta", "description": "Descarga tu oferta firmada."},
            {"title": "💰 Calcular Salario", "payload": "calcular_salario", "description": "Calcula salario neto o bruto."},
            {"title": "🤝 Recomendar", "payload": "travel_in_group", "description": "Invita a amigos o familia."},
            {"title": "📞 Contacto", "payload": "contacto", "description": "Habla con un asesor."},
            {"title": "❓ Ayuda", "payload": "ayuda", "description": "Resuelve dudas generales."},
        ],
        "hired": [
            {"title": "📝 Actualizar Perfil", "payload": "mi_perfil", "description": "Gestiona y actualiza tu perfil."},
            {"title": "🔍 Ver Vacantes", "payload": "ver_vacantes", "description": "Explora nuevas oportunidades tras 6 meses."},
            {"title": "💰 Calcular Salario", "payload": "calcular_salario", "description": "Calcula salario neto o bruto."},
            {"title": "🤝 Recomendar", "payload": "travel_in_group", "description": "Invita a amigos o familia."},
            {"title": "📞 Contacto", "payload": "contacto", "description": "Habla con un asesor."},
            {"title": "❓ Ayuda", "payload": "ayuda", "description": "Resuelve dudas generales."},
        ],
        "idle": [
            {"title": "📝 Actualizar Perfil", "payload": "mi_perfil", "description": "Gestiona y actualiza tu perfil."},
            {"title": "🔍 Ver Vacantes", "payload": "ver_vacantes", "description": "Explora oportunidades laborales disponibles."},
            {"title": "🧠 Prueba de Personalidad", "payload": "prueba_personalidad", "description": "Descubre tu perfil profesional."},
            {"title": "💰 Calcular Salario", "payload": "calcular_salario", "description": "Calcula salario neto o bruto."},
            {"title": "🤝 Recomendar", "payload": "travel_in_group", "description": "Invita a amigos o familia."},
            {"title": "📞 Contacto", "payload": "contacto", "description": "Habla con un asesor."},
            {"title": "❓ Ayuda", "payload": "ayuda", "description": "Resuelve dudas generales."},
        ],
    },
    "default": MENU_OPTIONS_BY_BU["default"]  # Fallback para otras unidades
}

def get_greeting_by_time() -> str:
    """Devuelve un saludo basado en la hora actual."""
    hour = datetime.now().hour
    if 5 <= hour < 12:
        return "🌅 Buenos días"
    elif 12 <= hour < 19:
        return "🌇 Buenas tardes"
    else:
        return "🌙 Buenas noches"

class RateLimiter:
    def __init__(self, max_requests=10, time_window=60):
        self.max_requests = max_requests  # Máximo de mensajes por usuario
        self.time_window = time_window    # Ventana de tiempo en segundos

    async def check_rate_limit(self, user_id: str) -> bool:
        cache_key = f"rate_limit:{user_id}"
        current_time = time.time()
        
        # Obtener historial de mensajes
        request_history = cache.get(cache_key, [])
        
        # Filtrar mensajes dentro de la ventana de tiempo
        request_history = [t for t in request_history if current_time - t < self.time_window]
        
        if len(request_history) >= self.max_requests:
            logger.warning(f"Rate limit excedido para user_id={user_id}")
            return False
        
        # Añadir nuevo timestamp
        request_history.append(current_time)
        cache.set(cache_key, request_history, timeout=self.time_window)
        return True

async def apply_rate_limit(platform: str, user_id: str, message: dict) -> bool:
    limiter = RateLimiter(max_requests=10, time_window=60)
    if not await limiter.check_rate_limit(user_id):
        await send_message(platform, user_id, "Por favor, espera un momento antes de enviar más mensajes.", "default")
        return False
    return True

class Button:
    """Clase para representar botones interactivos."""
    def __init__(self, title: str, payload: Optional[str] = None, url: Optional[str] = None):
        self.title = title
        self.payload = payload
        self.url = url

    @classmethod
    def from_dict(cls, button_dict: Dict) -> 'Button':
        return cls(
            title=button_dict.get('title', ''),
            payload=button_dict.get('payload'),
            url=button_dict.get('url')
        )

# Clase abstracta para estandarizar la obtención de datos de usuario
class UserDataFetcher(ABC):
    """Clase base abstracta para estandarizar la obtención de datos de usuario."""
    @abstractmethod
    async def fetch(self, user_id: str, api_instance: Any, payload: Dict[str, Any] = None) -> Dict[str, Any]:
        pass

class WhatsAppUserDataFetcher(UserDataFetcher):
    async def fetch(self, user_id: str, api_instance: WhatsAppAPI, payload: Dict[str, Any] = None) -> Dict[str, Any]:
        from app.chatbot.integrations.whatsapp import fetch_whatsapp_user_data
        return await fetch_whatsapp_user_data(user_id, api_instance, payload)

class TelegramUserDataFetcher(UserDataFetcher):
    async def fetch(self, user_id: str, api_instance: TelegramAPI, payload: Dict[str, Any] = None) -> Dict[str, Any]:
        from app.chatbot.integrations.telegram import fetch_telegram_user_data
        return await fetch_telegram_user_data(user_id, api_instance, payload)

class MessengerUserDataFetcher(UserDataFetcher):
    async def fetch(self, user_id: str, api_instance: MessengerAPI, payload: Dict[str, Any] = None) -> Dict[str, Any]:
        from app.chatbot.integrations.messenger import fetch_messenger_user_data
        return await fetch_messenger_user_data(user_id, api_instance, payload)

class InstagramUserDataFetcher(UserDataFetcher):
    async def fetch(self, user_id: str, api_instance: InstagramAPI, payload: Dict[str, Any] = None) -> Dict[str, Any]:
        from app.chatbot.integrations.instagram import fetch_instagram_user_data
        return await fetch_instagram_user_data(user_id, api_instance, payload)

class SlackUserDataFetcher(UserDataFetcher):
    async def fetch(self, user_id: str, api_instance: SlackAPI, payload: Dict[str, Any] = None) -> Dict[str, Any]:
        from app.chatbot.integrations.slack import fetch_slack_user_data
        return await fetch_slack_user_data(user_id, api_instance, payload)

class MessageService:
    """Servicio para enviar mensajes y obtener datos de usuario en múltiples plataformas."""
    def __init__(self, business_unit: BusinessUnit):
        self.business_unit = business_unit
        self._api_instances = {}

    async def get_api_instance(self, platform: str):
        """Obtiene o cachea la instancia de API para la plataforma especificada."""
        if not platform or not isinstance(platform, str):
            logger.error(f"Plataforma inválida: {platform}")
            return None
            
        cache_key = f"api_instance:{platform}:{self.business_unit.id}"
        
        # Verificar si ya está en memoria
        if platform in self._api_instances:
            if self._api_instances[platform] is not None and not isinstance(self._api_instances[platform], str):
                return self._api_instances[platform]
        
        # Intentar obtener del caché
        try:
            cached_api = cache.get(cache_key)
            if cached_api is not None:
                if isinstance(cached_api, str):
                    logger.warning(f"Caché corrupto para {platform}: se encontró string en lugar de objeto")
                    cache.delete(cache_key)
                else:
                    required_attrs = {
                        'whatsapp': ['phoneID', 'api_token', 'v_api'],
                        'telegram': ['api_key'],
                        'messenger': ['page_access_token'],
                        'instagram': ['access_token'],
                        'slack': ['bot_token']
                    }
                    
                    is_valid = True
                    for attr in required_attrs.get(platform, []):
                        if not hasattr(cached_api, attr) or not getattr(cached_api, attr):
                            logger.warning(f"Objeto en caché para {platform} no tiene atributo válido: {attr}")
                            is_valid = False
                            break
                    
                    if is_valid:
                        self._api_instances[platform] = cached_api
                        logger.debug(f"API para {platform} recuperada del caché correctamente")
                        return cached_api
                    else:
                        cache.delete(cache_key)
        except Exception as e:
            logger.warning(f"Error al recuperar del caché para {platform}: {e}")
        
        # Cargar desde la base de datos
        model_mapping = {
            'whatsapp': WhatsAppAPI,
            'telegram': TelegramAPI,
            'messenger': MessengerAPI,
            'instagram': InstagramAPI,
            'slack': SlackAPI
        }
        
        model_class = model_mapping.get(platform)
        if not model_class:
            logger.error(f"Plataforma no soportada: {platform}")
            self._api_instances[platform] = None
            return None

        try:
            api_instance = await model_class.objects.filter(
                business_unit=self.business_unit, is_active=True
            ).afirst()

            if not api_instance:
                logger.warning(f"No se encontró configuración activa para {platform} en BU {self.business_unit.name}")
                self._api_instances[platform] = None
                return None
            
            # Validar atributos requeridos según la plataforma
            required_attrs = {
                'whatsapp': ['phoneID', 'api_token', 'v_api'],
                'telegram': ['api_key'],
                'messenger': ['page_access_token'],
                'instagram': ['access_token'],
                'slack': ['bot_token']
            }
            
            missing_attrs = []
            for attr in required_attrs.get(platform, []):
                if not hasattr(api_instance, attr):
                    missing_attrs.append(f"{attr} (atributo no existe)")
                elif not getattr(api_instance, attr):
                    missing_attrs.append(f"{attr} (valor vacío)")
            
            if missing_attrs:
                logger.error(f"Configuración incompleta para {platform} en BU {self.business_unit.name}: {', '.join(missing_attrs)}")
                self._api_instances[platform] = None
                return None
            
            self._api_instances[platform] = api_instance
            try:
                cache.set(cache_key, api_instance, timeout=CACHE_TIMEOUT)
                logger.debug(f"API para {platform} almacenada en caché correctamente")
            except Exception as e:
                logger.warning(f"Error al guardar en caché para {platform}: {e}")
            
            return api_instance
            
        except Exception as e:
            logger.error(f"Error al obtener instancia de API para {platform}: {e}", exc_info=True)
            self._api_instances[platform] = None
            return None

    async def send_platform_message(
        self,
        platform: str,
        user_id: str,
        message: str,
        api_instance: Optional[object] = None,
        options: Optional[List[Dict]] = None
    ) -> bool:
        """Envía mensajes a cualquier plataforma de manera dinámica."""
        if api_instance is None:
            api_instance = await self.get_api_instance(platform)
            if not api_instance:
                logger.error(f"No se encontró configuración para {platform}")
                return False

        send_funcs = {
            'whatsapp': self._send_whatsapp,
            'telegram': self._send_telegram,
            'messenger': self._send_messenger,
            'instagram': self._send_instagram,
            'slack': self._send_slack
        }

        send_func = send_funcs.get(platform)
        if not send_func:
            logger.error(f"Plataforma no soportada: {platform}")
            return False

        return await send_func(user_id, message, api_instance, options)

    @retry(stop=stop_after_attempt(MAX_RETRIES))
    async def send_message(
        self,
        platform: str,
        user_id: str,
        message: str,
        options: Optional[List[Dict]] = None
    ) -> bool:
        """Envía un mensaje al usuario en la plataforma especificada."""
        try:
            logger.info(f"[send_message] Enviando a {user_id} en {platform}, BU: {self.business_unit.name}")
            return await self.send_platform_message(platform, user_id, message, options=options)
        except Exception as e:
            logger.error(f"[send_message] Error: {e}", exc_info=True)
            return False

    @retry(stop=stop_after_attempt(MAX_RETRIES))
    async def send_image(
        self,
        platform: str,
        user_id: str,
        message: str,
        image_url: str
    ) -> bool:
        """Envía una imagen al usuario."""
        try:
            api_instance = await self.get_api_instance(platform)
            if not api_instance:
                logger.error(f"[send_image] No se encontró configuración API para {platform}")
                return False

            if platform == "whatsapp":
                from app.chatbot.integrations.whatsapp import send_whatsapp_image
                await send_whatsapp_image(
                    user_id=user_id,
                    message=message,
                    image_url=image_url,
                    phone_id=api_instance.phoneID,
                    business_unit=self.business_unit
                )
            elif platform == "telegram":
                from app.chatbot.integrations.telegram import send_telegram_image
                await send_telegram_image(
                    chat_id=user_id,
                    image_url=image_url,
                    caption=message,
                    api_key=api_instance.api_key
                )
            elif platform in ["messenger", "instagram"]:
                from app.chatbot.integrations.messenger import send_messenger_image
                await send_messenger_image(
                    user_id=user_id,
                    image_url=image_url,
                    caption=message,
                    access_token=api_instance.page_access_token if platform == "messenger" else api_instance.access_token
                )
            elif platform == "slack":
                from app.chatbot.integrations.slack import send_slack_message
                await send_slack_message(
                    channel_id=user_id,
                    message=f"{message}\n{image_url}",
                    bot_token=api_instance.bot_token
                )
            else:
                logger.error(f"[send_image] Plataforma no soportada: {platform}")
                return False

            logger.info(f"✅ Imagen enviada a {user_id} en {platform}.")
            return True
        except Exception as e:
            logger.error(f"[send_image] Error enviando imagen en {platform}: {e}", exc_info=True)
            return False

    @retry(stop=stop_after_attempt(MAX_RETRIES))
    async def send_menu(self, platform: str, user_id: str):
        """Envía el menú principal dinámico basado en el estado del ChatState."""
        try:
            logger.info(f"[send_menu] 📩 Enviando menú a {user_id} en {platform} para {self.business_unit.name}")
            
            chat_state = await ChatState.objects.filter(
                user_id=user_id, business_unit=self.business_unit
            ).afirst()
            
            if not chat_state:
                logger.warning(f"[send_menu] No se encontró ChatState para {user_id}, usando 'initial'")
                state = "initial"
            else:
                state = chat_state.state

            cache_key = f"menu_options:{self.business_unit.name.lower()}:{state}:{user_id}"
            cached_options = cache.get(cache_key)
            if cached_options:
                message, simplified_options = cached_options
            else:
                bu_name = self.business_unit.name.lower()
                options_by_state = MENU_OPTIONS_BY_STATE.get(bu_name, MENU_OPTIONS_BY_STATE["default"])
                options = options_by_state.get(state, options_by_state["initial"])
                
                message = f"📱📋  *Menú de {bu_name}*\nSelecciona una opción:"
                simplified_options = [{"title": opt["title"], "payload": opt["payload"]} for opt in options]
                cache.set(cache_key, (message, simplified_options), timeout=CACHE_TIMEOUT)

            if platform == "slack":
                success = await self.send_options(platform, user_id, message, simplified_options)
                return success
            else:
                success, msg_id = await send_smart_options(platform, user_id, message, simplified_options, self.business_unit.name)
                if success:
                    logger.info(f"[send_menu] ✅ Menú enviado correctamente. Message ID: {msg_id}")
                    return True
                else:
                    logger.error(f"[send_menu] ❌ Falló el envío del menú.")
                    return False
        except Exception as e:
            logger.error(f"[send_menu] ❌ Error enviando menú: {e}", exc_info=True)
            return False

    @retry(stop=stop_after_attempt(MAX_RETRIES))
    async def send_url(self, platform: str, user_id: str, url: str) -> bool:
        """Envía un enlace al usuario."""
        return await self.send_message(platform, user_id, f"Aquí tienes el enlace: {url}")

    @retry(stop=stop_after_attempt(MAX_RETRIES))
    async def send_options(
        self,
        platform: str,
        user_id: str,
        message: str,
        buttons: Optional[List[Dict]] = None
    ) -> bool:
        """Envía mensaje con opciones al usuario."""
        try:
            if not buttons:
                buttons = [{"title": "Continuar", "payload": "continue"}]

            button_objects = [Button.from_dict(btn) for btn in buttons]
            
            api_instance = await self.get_api_instance(platform)
            if not api_instance:
                logger.error(f"No se encontró configuración para {platform}")
                return False

            platform_handlers = {
                'whatsapp': self._send_whatsapp_options,
                'telegram': self._send_telegram_options,
                'messenger': self._send_messenger_options,
                'instagram': self._send_instagram_options,
                'slack': self._send_slack_options
            }

            handler = platform_handlers.get(platform)
            if handler:
                return await handler(user_id, message, button_objects, api_instance)
            else:
                logger.error(f"Plataforma no soportada: {platform}")
                return False
        except Exception as e:
            logger.error(f"Error enviando opciones en {platform}: {e}", exc_info=True)
            return False

    async def _send_whatsapp(self, user_id: str, message: str, api_instance: WhatsAppAPI, options: Optional[List[Dict]]) -> bool:
        from app.chatbot.integrations.whatsapp import send_whatsapp_message
        async with whatsapp_semaphore:
            if options:
                await self._send_whatsapp_options(user_id, message, [Button.from_dict(opt) for opt in options], api_instance)
            else:
                await send_whatsapp_message(
                    user_id=user_id,
                    message=message,
                    phone_id=api_instance.phoneID,
                    business_unit=self.business_unit
                )
            return True

    async def _send_telegram(self, user_id: str, message: str, api_instance: TelegramAPI, options: Optional[List[Dict]]) -> bool:
        from app.chatbot.integrations.telegram import send_telegram_message
        chat_id = int(user_id.split(":")[-1]) if ":" in user_id else int(user_id)
        if options:
            await self._send_telegram_options(chat_id, message, [Button.from_dict(opt) for opt in options], api_instance)
        else:
            await send_telegram_message(chat_id, message, api_instance, self.business_unit.name)
        return True

    async def _send_messenger(self, user_id: str, message: str, api_instance: MessengerAPI, options: Optional[List[Dict]]) -> bool:
        from app.chatbot.integrations.messenger import send_messenger_message
        if options:
            await self._send_messenger_options(user_id, message, [Button.from_dict(opt) for opt in options], api_instance)
        else:
            await send_messenger_message(user_id, message, None, api_instance.page_access_token)
        return True

    async def _send_instagram(self, user_id: str, message: str, api_instance: InstagramAPI, options: Optional[List[Dict]]) -> bool:
        from app.chatbot.integrations.instagram import send_instagram_message
        if options:
            await self._send_instagram_options(user_id, message, [Button.from_dict(opt) for opt in options], api_instance)
        else:
            await send_instagram_message(user_id, message, None, api_instance.access_token)
        return True

    async def _send_slack(self, user_id: str, message: str, api_instance: SlackAPI, options: Optional[List[Dict]]) -> bool:
        from app.chatbot.integrations.slack import send_slack_message
        if options:
            await self._send_slack_options(user_id, message, [Button.from_dict(opt) for opt in options], api_instance)
        else:
            await send_slack_message(user_id, message, api_instance.bot_token)
        return True

    async def _send_whatsapp_options(self, user_id, message, buttons, api_instance):
        from app.chatbot.integrations.whatsapp import send_whatsapp_decision_buttons
        url_buttons = [btn for btn in buttons if btn.url]
        option_buttons = [btn for btn in buttons if btn.payload][:3]
        
        try:
            for btn in url_buttons:
                await self.send_message('whatsapp', user_id, f"Más información: {btn.url}")
            if option_buttons:
                formatted_buttons = [
                    {"type": "reply", "reply": {"id": btn.payload, "title": btn.title[:20]}}
                    for btn in option_buttons
                ]
                await send_whatsapp_decision_buttons(
                    user_id=user_id,
                    message=message,
                    buttons=formatted_buttons,
                    business_unit=self.business_unit
                )
            return True
        except Exception as e:
            logger.error(f"Error enviando opciones WhatsApp: {e}", exc_info=True)
            return False

    async def _send_telegram_options(self, user_id, message, buttons, api_instance):
        from app.chatbot.integrations.telegram import send_telegram_buttons
        try:
            chat_id = int(user_id.split(":")[-1]) if ":" in user_id else int(user_id)
            telegram_buttons = [
                {"text": btn.title, "callback_data": btn.payload or "default"} if btn.payload
                else {"text": btn.title, "url": btn.url} if btn.url
                else {"text": btn.title, "callback_data": "no_action"}
                for btn in buttons
            ]
            success = await send_telegram_buttons(
                chat_id=chat_id,
                message=message,
                buttons=telegram_buttons,
                telegram_api=api_instance,
                business_unit_name=self.business_unit.name
            )
            return success is not None
        except Exception as e:
            logger.error(f"Error enviando opciones Telegram: {e}", exc_info=True)
            return False

    async def _send_messenger_options(self, user_id, message, buttons, api_instance):
        from app.chatbot.integrations.messenger import send_messenger_buttons
        try:
            quick_replies = [
                {"content_type": "text", "title": btn.title, "payload": btn.payload or "no_payload"}
                for btn in buttons
            ]
            await send_messenger_buttons(
                user_id=user_id,
                message=message,
                quick_replies=quick_replies,
                access_token=api_instance.page_access_token
            )
            return True
        except Exception as e:
            logger.error(f"Error enviando opciones Messenger: {e}", exc_info=True)
            return False

    async def _send_instagram_options(self, user_id, message, buttons, api_instance):
        from app.chatbot.integrations.instagram import send_instagram_buttons
        try:
            instagram_buttons = [
                {"title": btn.title, "payload": btn.payload or "no_payload"}
                for btn in buttons
            ]
            await send_instagram_buttons(
                user_id=user_id,
                message=message,
                buttons=instagram_buttons,
                access_token=api_instance.access_token
            )
            return True
        except Exception as e:
            logger.error(f"Error enviando opciones Instagram: {e}", exc_info=True)
            return False

    async def _send_slack_options(self, user_id, message, buttons, api_instance):
        from app.chatbot.integrations.slack import send_slack_message_with_buttons
        try:
            slack_buttons = [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": btn.title},
                    "value": btn.payload or "default"
                }
                for btn in buttons
            ]
            await send_slack_message_with_buttons(
                channel_id=user_id,
                message=message,
                buttons=slack_buttons,
                bot_token=api_instance.bot_token
            )
            return True
        except Exception as e:
            logger.error(f"Error enviando opciones Slack: {e}", exc_info=True)
            return False

    async def fetch_user_data(self, platform: str, user_id: str, payload: Dict[str, Any] = None) -> Dict[str, Any]:
        """Obtiene datos de usuario de manera estandarizada."""
        cache_key = f"user_data:{platform}:{user_id}"
        cached_data = cache.get(cache_key)
        if cached_data:
            logger.debug(f"Datos de usuario para {platform}:{user_id} obtenidos del caché")
            return cached_data

        api_instance = await self.get_api_instance(platform)
        if not api_instance:
            logger.error(f"No se encontró instancia de API para {platform}")
            return {}

        fetcher_mapping = {
            'whatsapp': WhatsAppUserDataFetcher(),
            'telegram': TelegramUserDataFetcher(),
            'messenger': MessengerUserDataFetcher(),
            'instagram': InstagramUserDataFetcher(),
            'slack': SlackUserDataFetcher(),
        }

        fetcher = fetcher_mapping.get(platform)
        if not fetcher:
            logger.error(f"No hay fetcher definido para {platform}")
            return {}

        try:
            data = await fetcher.fetch(user_id, api_instance, payload)
            cache.set(cache_key, data, timeout=3600)
            return data
        except Exception as e:
            logger.error(f"Error al obtener datos de usuario para {platform}:{user_id}: {e}", exc_info=True)
            return {}

    async def invalidate_cache(self, platform: str):
        """Invalida el caché para una plataforma específica."""
        cache_key = f"api_instance:{platform}:{self.business_unit.id}"
        cache.delete(cache_key)
        if platform in self._api_instances:
            del self._api_instances[platform]
        logger.info(f"Caché invalidado para {platform}")

class EmailService:
    """Servicio para enviar correos electrónicos."""
    def __init__(self, business_unit: BusinessUnit):
        self.business_unit = business_unit
        self._config = None

    async def get_config(self) -> ConfiguracionBU:
        """Obtiene la configuración de correo de la unidad de negocio."""
        if not self._config:
            self._config = await sync_to_async(ConfiguracionBU.objects.select_related('business_unit').get)(
                business_unit=self.business_unit
            )
        return self._config

    async def send_email(
        self,
        subject: str,
        to_email: str,
        body: str,
        from_email: Optional[str] = None
    ) -> Dict[str, str]:
        """Envía un correo electrónico."""
        server = None
        try:
            config = await self.get_config()
            
            smtp_host = config.smtp_host or "mail.huntred.com"
            smtp_port = config.smtp_port or 465
            smtp_username = config.smtp_username or config.correo_bu
            smtp_password = config.smtp_password
            from_email = from_email or smtp_username

            msg = MIMEMultipart()
            msg['From'] = from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'html'))

            server = smtplib.SMTP_SSL(smtp_host, smtp_port)
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
            
            logger.info(f"Correo enviado a {to_email} con asunto: {subject}")
            return {"status": "success", "message": "Correo enviado correctamente."}
        except Exception as e:
            logger.error(f"[send_email] Error: {e}", exc_info=True)
            return {"status": "error", "message": str(e)}
        finally:
            if server:
                server.quit()

class GamificationService:
    """Servicio para gestionar gamificación."""
    def __init__(self):
        pass

    async def award_points(self, user: Person, activity_type: str, points: int = 10):
        """Otorga puntos al usuario por una actividad."""
        try:
            profile, created = await sync_to_async(EnhancedNetworkGamificationProfile.objects.get_or_create)(
                user=user,
                defaults={'points': 0, 'level': 1}
            )
            
            await sync_to_async(profile.award_points)(activity_type, points)
            await sync_to_async(profile.save)()
            
            logger.info(f"[GamificationService] Otorgados {points} puntos a {user.nombre}")
            await self.notify_user_gamification_update(user, activity_type)
        except Exception as e:
            logger.error(f"[GamificationService] Error otorgando puntos a {user.nombre}: {e}", exc_info=True)

    async def notify_user_gamification_update(self, user: Person, activity_type: str):
        """Notifica al usuario sobre la actualización de puntos de gamificación."""
        try:
            profile = await sync_to_async(EnhancedNetworkGamificationProfile.objects.get)(user=user)
            message = f"¡Has ganado puntos por {activity_type}! Ahora tienes {profile.points} puntos."
            platform = user.chat_state.platform if hasattr(user, 'chat_state') else 'whatsapp'
            business_unit = user.chat_state.business_unit if hasattr(user, 'chat_state') else user.business_unit
            if platform and business_unit:
                await send_message(
                    platform=platform,
                    user_id=user.phone,
                    message=message,
                    business_unit=business_unit
                )
        except EnhancedNetworkGamificationProfile.DoesNotExist:
            logger.warning(f"[GamificationService] No se encontró perfil de gamificación para {user.nombre}")
        except Exception as e:
            logger.error(f"[GamificationService] Error notificando gamificación a {user.nombre}: {e}", exc_info=True)

    async def generate_challenges(self, user: Person):
        """Genera desafíos personalizados para el usuario."""
        try:
            profile = await sync_to_async(EnhancedNetworkGamificationProfile.objects.get)(user=user)
            return profile.generate_networking_challenges()
        except EnhancedNetworkGamificationProfile.DoesNotExist:
            return []

    async def notify_user_challenges(self, user: Person):
        """Notifica al usuario sobre nuevos desafíos."""
        challenges = await self.generate_challenges(user)
        if challenges:
            message = f"Tienes nuevos desafíos: {', '.join(challenges)}"
            await send_message(
                platform=user.chat_state.platform if hasattr(user, 'chat_state') else 'whatsapp',
                user_id=user.phone,
                message=message,
                business_unit=user.chat_state.business_unit if hasattr(user, 'chat_state') else user.business_unit
            )

async def notify_employer(worker, message):
    """Notifica al empleador que un evento ha ocurrido."""
    try:
        if worker.whatsapp:
            whatsapp_api = await sync_to_async(lambda: WhatsAppAPI.objects.filter(
                business_unit=worker.business_unit, is_active=True
            ).select_related('business_unit').first())()
            if whatsapp_api:
                from app.chatbot.integrations.whatsapp import send_whatsapp_message
                await send_whatsapp_message(
                    user_id=worker.whatsapp,
                    message=message,
                    phone_id=whatsapp_api.phoneID,
                    business_unit=whatsapp_api.business_unit
                )
                logger.info(f"[notify_employer] Notificación enviada al empleador {worker.name} vía WhatsApp.")
            else:
                logger.error("[notify_employer] No se encontró configuración de WhatsAppAPI.")
        else:
            logger.warning(f"[notify_employer] El empleador {worker.name} no tiene número de WhatsApp configurado.")
    except Exception as e:
        logger.error(f"[notify_employer] Error enviando notificación al empleador {worker.name}: {e}", exc_info=True)

async def get_business_unit(name: Optional[str] = None) -> Optional[BusinessUnit]:
    """Obtiene una instancia de BusinessUnit por nombre."""
    try:
        if not name:
            return None
        
        normalized_name = str(name).lower().replace('®', '').strip() if isinstance(name, str) else name
        
        if isinstance(name, BusinessUnit):
            return name
            
        business_unit = await sync_to_async(BusinessUnit.objects.filter)(
            name__iexact=normalized_name
        )
        return await sync_to_async(business_unit.first)()
    except Exception as e:
        logger.error(f"[get_business_unit] Error obteniendo BusinessUnit ({name}): {e}")
        return None

def run_async(func, *args, **kwargs):
    """Ejecuta la función en modo síncrono o asíncrono según el contexto."""
    try:
        loop = asyncio.get_running_loop()
        return func(*args, **kwargs)
    except RuntimeError:
        return asyncio.run(func(*args, **kwargs))

async def reset_chat_state(user_id: str, business_unit: BusinessUnit, platform: Optional[str] = None):
    """Reinicia el estado de la conversación (ChatState) para un usuario."""
    try:
        chat_state = await sync_to_async(ChatState.objects.get)(user_id=user_id, business_unit=business_unit)
        await sync_to_async(chat_state.delete)()
        logger.info(f"🧹 ChatState reiniciado para {user_id} en {business_unit.name}")
        
        if platform:
            await send_message(platform, user_id, "🧹 Conversación reiniciada. Envía un mensaje para comenzar de nuevo.", business_unit)
    except ChatState.DoesNotExist:
        logger.info(f"🧹 No se encontró ChatState para {user_id} en {business_unit.name}, no hay nada que reiniciar.")
        if platform:
            await send_message(platform, user_id, "🧹 No había conversación activa, pero estás listo para comenzar de nuevo.", business_unit)

async def send_message_async(platform: str, user_id: str, message: str, business_unit_name: str = None):
    """Envía un mensaje de forma asíncrona."""
    try:
        if not business_unit_name:
            business_unit_name = 'default'
        
        business_unit_name = business_unit_name.lower().replace('®', '').strip()
        # Log antes de buscar la unidad de negocio
        logger.debug(f"[send_message_async] Iniciando proceso para {user_id} en {platform} con unidad de negocio: {business_unit_name}")
        
        business_unit = await get_business_unit(business_unit_name)
        if not business_unit:
            logger.error(f"Business unit no encontrado: {business_unit_name}")
            return False
        
        message_service = MessageService(business_unit)
        # Log antes de enviar el mensaje
        logger.info(f"[send_message_async] Preparando envío a {user_id} en {platform} para {business_unit_name}: {message}")
        
        # Ejecutar el envío y registrar el resultado
        success = await message_service.send_message(platform, user_id, message)
        if success:
            logger.info(f"[send_message_async] Mensaje enviado exitosamente a {user_id} en {platform} para {business_unit_name}")
        else:
            logger.warning(f"[send_message_async] Fallo al enviar mensaje a {user_id} en {platform} para {business_unit_name}")
        return success
    except Exception as e:
        # Log detallado del error
        logger.error(f"[send_message_async] Error al enviar mensaje a {user_id} en {platform} para {business_unit_name}: {str(e)}", exc_info=True)
        return False
    
def send_message(platform: str, user_id: str, message: str, business_unit: str = None):
    """Envío de mensaje de forma segura en entornos síncronos y asíncronos."""
    logger.debug(f"[send_message] Llamada a send_message para {user_id} en {platform}")
    return run_async(send_message_async, platform, user_id, message, business_unit)

async def send_email_async(subject: str, to_email: str, body: str, business_unit_name: str = None, from_email=None):
    """Versión asíncrona de `send_email`."""
    business_unit = await get_business_unit(business_unit_name)
    if business_unit:
        service = EmailService(business_unit)
        return await service.send_email(subject, to_email, body, from_email)
    logger.error(f"❌ No se encontró la unidad de negocio")
    return False

def send_email(subject: str, to_email: str, body: str, business_unit_name: str = None, from_email=None):
    """Wrapper de `send_email`, compatible con entornos síncronos y asíncronos."""
    return run_async(send_email_async, subject, to_email, body, business_unit_name, from_email)

async def send_list_options(platform: str, user_id: str, message: str, buttons: List[Dict], business_unit_name: str):
    """Envía una lista interactiva en WhatsApp si hay más de 3 opciones."""
    from app.chatbot.integrations.whatsapp import send_whatsapp_list
    if platform != "whatsapp":
        success = await send_options(platform, user_id, message, buttons, business_unit_name)
        return success, None
    sections = [{"title": "Opciones", "rows": [{"id": btn["payload"], "title": btn["title"]} for btn in buttons]}]
    success = await send_whatsapp_list(user_id, message, sections, business_unit_name)
    msg_id = "msg_id_placeholder" if success else None
    return success, msg_id

async def send_smart_options(platform, user_id, message, options, business_unit_name):
    """Envía opciones interactivas de manera optimizada."""
    try:
        business_unit = await get_business_unit(business_unit_name)
        if not business_unit:
            logger.error(f"[send_smart_options] No se encontró BusinessUnit para {business_unit_name}")
            return False, None

        service = MessageService(business_unit)

        if platform == "whatsapp":
            url_buttons = [opt for opt in options if "url" in opt]
            normal_buttons = [opt for opt in options if "url" not in opt]

            if url_buttons and not normal_buttons:
                logger.info("[send_smart_options] 📤 Enviando botones URL como mensajes separados.")
                for opt in url_buttons:
                    await service.send_message(platform, user_id, f"🔗 {opt['title']}: {opt['url']}")
                return True, None

            if len(url_buttons) == 1 and normal_buttons:
                logger.info(f"[send_smart_options] 📤 Enviando primero el enlace: {url_buttons[0]['url']}")
                await service.send_message(platform, user_id, f"🔗 {url_buttons[0]['title']}: {url_buttons[0]['url']}")
                await asyncio.sleep(2)

            if len(normal_buttons) > 3:
                success, msg_id = await send_list_options(platform, user_id, message, normal_buttons, business_unit_name)
                if success:
                    return True, msg_id
                logger.warning("[send_smart_options] ❌ Listas interactivas fallaron, usando fallback.")

            last_msg_id = None
            option_batches = [normal_buttons[i:i+3] for i in range(0, len(normal_buttons), 3)]
            for batch in option_batches:
                success = await service.send_options(platform, user_id, message, batch)
                if not success:
                    logger.error("[send_smart_options] ❌ Falló el envío de opciones.")
                    return False, None
                last_msg_id = "msg_id_placeholder"
                await asyncio.sleep(0.5)

            return True, last_msg_id

        else:
            success = await service.send_options(platform, user_id, message, options)
            return success, "msg_id_placeholder" if success else None

    except Exception as e:
        logger.error(f"[send_smart_options] ❌ Error enviando opciones a {user_id}: {e}", exc_info=True)
        return False, None

async def send_options_async(platform: str, user_id: str, message: str, buttons=None, business_unit_name: str = None):
    """Envío de mensaje con botones interactivos de forma asíncrona."""
    try:
        business_unit = await get_business_unit(business_unit_name)
        if not business_unit:
            logger.error(f"[send_options_async] ❌ No se encontró BusinessUnit para {business_unit_name}")
            return False

        service = MessageService(business_unit)

        if platform == "whatsapp":
            if not buttons:
                logger.error(f"[send_options_async] ⚠️ No hay botones válidos para enviar a WhatsApp.")
                return False
            
            formatted_buttons = []
            for i, btn in enumerate(buttons[:3]):
                if "title" in btn and "payload" in btn:
                    formatted_buttons.append({
                        "type": "reply",
                        "reply": {
                            "id": btn["payload"],
                            "title": btn["title"][:20]
                        }
                    })
                else:
                    logger.warning(f"[send_options_async] ⚠️ Botón inválido: {btn}")

            logger.info(f"[send_options_async] 🚀 Botones generados para WhatsApp: {formatted_buttons}")

            if not formatted_buttons:
                logger.error(f"[send_options_async] ⚠️ No se generaron botones válidos para WhatsApp.")
                return False

            from app.chatbot.integrations.whatsapp import send_whatsapp_decision_buttons
            success = await send_whatsapp_decision_buttons(
                user_id=user_id,
                message=message,
                buttons=formatted_buttons,
                business_unit=business_unit
            )
        else:
            success = await service.send_options(platform, user_id, message, buttons)

        if success:
            logger.info(f"[send_options_async] ✅ Opciones enviadas a {user_id} en {platform}")
        else:
            logger.warning(f"[send_options_async] ⚠️ Fallo en el envío de opciones a {user_id} en {platform}")

        return success

    except Exception as e:
        logger.error(f"[send_options_async] ❌ Error enviando opciones a {user_id} en {platform}: {e}", exc_info=True)
        return False

def send_options(platform: str, user_id: str, message: str, buttons=None, business_unit_name: str = None):
    """Wrapper de `send_options_async`, compatible con entornos síncronos y asíncronos."""
    return run_async(send_options_async, platform, user_id, message, buttons, business_unit_name)

async def send_menu_async(platform: str, user_id: str, business_unit: Optional[str] = None):
    """Envía el menú principal al usuario en la plataforma especificada."""
    business_unit = await get_business_unit(business_unit)
    
    if not business_unit:
        logger.error(f"❌ No se encontró la unidad de negocio para {platform} - Usuario: {user_id}")
        return False
    
    logger.info(f"📩 Enviando menú a {user_id} en {platform} para {business_unit.name}")
    service = MessageService(business_unit)
    return await service.send_menu(platform, user_id)

def send_menu(platform: str, user_id: str, business_unit_name: str = None):
    return run_async(send_menu_async, platform, user_id, business_unit_name)

async def send_image_async(platform: str, user_id: str, message: str, image_url: str, business_unit: Optional[str] = None):
    """Envía una imagen con un mensaje al usuario en la plataforma especificada."""
    business_unit = await get_business_unit(business_unit)
    
    if not business_unit:
        logger.error(f"❌ No se encontró la unidad de negocio para {platform} - Usuario: {user_id}")
        return False
    
    logger.info(f"📷 Enviando imagen a {user_id} en {platform} - Mensaje: {message} - URL: {image_url}")
    service = MessageService(business_unit)
    return await service.send_image(platform, user_id, message, image_url)

def send_image(platform: str, user_id: str, message: str, image_url: str, business_unit_name: str = None):
    return run_async(send_image_async, platform, user_id, message, image_url, business_unit_name)

async def send_url_async(platform: str, user_id: str, url: str, business_unit: Optional[str] = None):
    """Envía un enlace al usuario en la plataforma especificada."""
    business_unit = await get_business_unit(business_unit)
    
    if not business_unit:
        logger.error(f"❌ No se encontró la unidad de negocio para {platform} - Usuario: {user_id}")
        return False
    
    logger.info(f"🔗 Enviando enlace a {user_id} en {platform} - URL: {url}")
    service = MessageService(business_unit)
    return await service.send_url(platform, user_id, url)

def send_url(platform: str, user_id: str, url: str, business_unit_name: str = None):
    return run_async(send_url_async, platform, user_id, url, business_unit_name)