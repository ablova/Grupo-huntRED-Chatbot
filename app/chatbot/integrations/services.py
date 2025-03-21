# /home/pablo/app/chatbot/integrations/services.py

import logging
import smtplib
import asyncio
import ssl
import itertools
from asgiref.sync import sync_to_async
from typing import Optional, List, Dict, Union, Any, Tuple
from asgiref.sync import sync_to_async
from django.core.cache import cache
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.models import (
    BusinessUnit, ConfiguracionBU, WhatsAppAPI, TelegramAPI, SlackAPI,
    InstagramAPI, MessengerAPI, ChatState, Person,
    EnhancedNetworkGamificationProfile
)
logger = logging.getLogger(__name__)


# Constantes globales
MAX_RETRIES = 3
REQUEST_TIMEOUT = 10.0
CACHE_TIMEOUT = 600  # 10 minutos
whatsapp_semaphore = asyncio.Semaphore(10)

# Constantes globales
MAX_RETRIES = 3
REQUEST_TIMEOUT = 10.0
CACHE_TIMEOUT = 600  # 10 minutos
whatsapp_semaphore = asyncio.Semaphore(10)

# En services.py No pueden ser más de 10, por envio.
MENU_OPTIONS_BY_BU = {
    "amigro": [
        {"title": "📝 Crear Perfil", "payload": "actualizar_perfil", "description": "Crea tu perfil con datos personales y profesionales."},
        {"title": "📝 Actualizar Perfil", "payload": "mi_perfil", "description": "Gestiona y actualiza tu perfil."},
        {"title": "💰 Calcular Salario", "payload": "calcular_salario", "description": "Calcula salario neto o bruto."},
        {"title": "📄 Cargar CV", "payload": "cargar_cv", "description": "Sube tu currículum."},
        {"title": "🤝 Invitar Grupo", "payload": "travel_in_group", "description": "Invita a amigos o familia."},
        {"title": "🔍 Ver Vacantes", "payload": "ver_vacantes", "description": "Explora oportunidades laborales disponibles."},
        {"title": "📊 Consultar Estatus", "payload": "consultar_estatus", "description": "Revisa el estado de tus aplicaciones."},
        {"title": "📞 Contacto", "payload": "contacto", "description": "Habla con un asesor."},
        {"title": "❓ Ayuda", "payload": "ayuda", "description": "Resuelve dudas generales."},
        {"title": "📜 Ver TOS", "payload": "tos_accept", "description": "Consulta los términos de servicio."},
    ],
    "huntred": [
        {"title": "📝 Creación / Actualizar Perfil", "payload": "actualizar_perfil", "description": "Modifica tus datos personales o profesionales."},
        {"title": "🔍 Buscar Empleo", "payload": "buscar_empleo", "description": "Encuentra trabajos específicos."},
        {"title": "📝 Mi Perfil", "payload": "mi_perfil", "description": "Gestiona tu perfil."},
        {"title": "📊 Ver Vacantes", "payload": "ver_vacantes", "description": "Lista de empleos disponibles."},
        {"title": "📄 Cargar CV", "payload": "cargar_cv", "description": "Sube tu currículum."},
        {"title": "📅 Agendar Entrevista", "payload": "agendar_entrevista", "description": "Programa una entrevista."},
        {"title": "💰 Calcular Salario", "payload": "calcular_salario", "description": "Calcula salario neto o bruto."},
        {"title": "🤝 Recomendar a huntRED®", "payload": "travel_in_group", "description": "Invita a amigos o familia."},
        {"title": "❓ Ayuda", "payload": "ayuda", "description": "Soporte general."},
        {"title": "💡 Tips Entrevista", "payload": "preparacion_entrevista", "description": "Consejos para entrevistas."},
    ],
    "huntu": [
        {"title": "📝 Creación / Actualizar Perfil", "payload": "actualizar_perfil", "description": "Modifica tus datos personales o profesionales."},
        {"title": "🔍 Explorar Vacantes", "payload": "explorar_vacantes", "description": "Descubre oportunidades únicas."},
        {"title": "📝 Mi Perfil", "payload": "mi_perfil", "description": "Actualiza tu información."},
        {"title": "📄 Cargar CV", "payload": "cargar_cv", "description": "Sube tu currículum."},
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
MENU_OPTIONS_BY_STATE = {
    "amigro": {
        "initial": [
            {"title": "📝 Crear Perfil", "payload": "actualizar_perfil", "description": "Crea tu perfil con datos personales y profesionales."},
            {"title": "📜 Ver TOS", "payload": "tos_accept", "description": "Consulta los términos de servicio."},
            {"title": "💰 Calcular Salario", "payload": "calcular_salario", "description": "Calcula salario neto o bruto."},
            {"title": "🤝 Invitar a Amigro", "payload": "travel_in_group", "description": "Invita a amigos o familia."},
            {"title": "📞 Contacto", "payload": "contacto", "description": "Habla con un asesor."},
            {"title": "❓ Ayuda", "payload": "ayuda", "description": "Resuelve dudas generales."},
        ],
        "waiting_for_tos": [
            {"title": "📜 Ver TOS", "payload": "tos_accept", "description": "Consulta los términos de servicio."},
            {"title": "💰 Calcular Salario", "payload": "calcular_salario", "description": "Calcula salario neto o bruto."},
            {"title": "🤝 Invitar a Amigro", "payload": "travel_in_group", "description": "Invita a amigos o familia."},
            {"title": "📞 Contacto", "payload": "contacto", "description": "Habla con un asesor."},
            {"title": "❓ Ayuda", "payload": "ayuda", "description": "Resuelve dudas generales."},
        ],
        "profile_in_progress": [
            {"title": "📝 Continuar Perfil", "payload": "actualizar_perfil", "description": "Sigue completando tu perfil."},
            {"title": "📄 Cargar CV", "payload": "cargar_cv", "description": "Sube tu currículum."},
            {"title": "💰 Calcular Salario", "payload": "calcular_salario", "description": "Calcula salario neto o bruto."},
            {"title": "🤝 Invitar a Amigro", "payload": "travel_in_group", "description": "Invita a amigos o familia."},
            {"title": "📞 Contacto", "payload": "contacto", "description": "Habla con un asesor."},
            {"title": "❓ Ayuda", "payload": "ayuda", "description": "Resuelve dudas generales."},
        ],
        "profile_complete": [
            {"title": "📝 Actualizar Perfil", "payload": "mi_perfil", "description": "Gestiona y actualiza tu perfil."},
            {"title": "🔍 Ver Vacantes", "payload": "ver_vacantes", "description": "Explora oportunidades laborales disponibles."},
            {"title": "💰 Calcular Salario", "payload": "calcular_salario", "description": "Calcula salario neto o bruto."},
            {"title": "🤝 Invitar a Amigro", "payload": "travel_in_group", "description": "Invita a amigos o familia."},
            {"title": "📞 Contacto", "payload": "contacto", "description": "Habla con un asesor."},
            {"title": "❓ Ayuda", "payload": "ayuda", "description": "Resuelve dudas generales."},
        ],
        "applied": [
            {"title": "📝 Actualizar Perfil", "payload": "mi_perfil", "description": "Gestiona y actualiza tu perfil."},
            {"title": "🔍 Ver Vacantes", "payload": "ver_vacantes", "description": "Explora oportunidades laborales disponibles."},
            {"title": "📊 Consultar Estatus", "payload": "consultar_estatus", "description": "Revisa el estado de tus aplicaciones."},
            {"title": "💰 Calcular Salario", "payload": "calcular_salario", "description": "Calcula salario neto o bruto."},
            {"title": "🤝 Recomendar", "payload": "travel_in_group", "description": "Invita a amigos o familia."},
            {"title": "📞 Contacto", "payload": "contacto", "description": "Habla con un asesor."},
            {"title": "❓ Ayuda", "payload": "ayuda", "description": "Resuelve dudas generales."},
        ],
        "scheduled": [
            {"title": "📝 Actualizar Perfil", "payload": "mi_perfil", "description": "Gestiona y actualiza tu perfil."},
            {"title": "🔍 Ver Vacantes", "payload": "ver_vacantes", "description": "Explora oportunidades laborales disponibles."},
            {"title": "📊 Consultar Estatus", "payload": "consultar_estatus", "description": "Revisa el estado de tus aplicaciones."},
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
            {"title": "💰 Calcular Salario", "payload": "calcular_salario", "description": "Calcula salario neto o bruto."},
            {"title": "🤝 Recomendar", "payload": "travel_in_group", "description": "Invita a amigos o familia."},
            {"title": "📞 Contacto", "payload": "contacto", "description": "Habla con un asesor."},
            {"title": "❓ Ayuda", "payload": "ayuda", "description": "Resuelve dudas generales."},
        ],
    },
    "default": MENU_OPTIONS_BY_BU["default"]  # Fallback para otras unidades
}

class Button:
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

class MessageService:
    def __init__(self, business_unit: BusinessUnit):
        self.business_unit = business_unit
        self._api_instances = {}

    async def get_api_instance(self, platform: str):
        """Obtiene o cachea la instancia de API para la plataforma especificada"""
        cache_key = f"api_instance:{platform}:{self.business_unit.id}"
        
        if platform not in self._api_instances:
            self._api_instances[platform] = cache.get(cache_key)
            
            if not self._api_instances[platform]:
                model_mapping = {
                    'whatsapp': WhatsAppAPI,
                    'telegram': TelegramAPI,
                    'messenger': MessengerAPI,
                    'instagram': InstagramAPI,
                    'slack': SlackAPI  # Corregido: '=' por ':'
                }
                model_class = model_mapping.get(platform)
                if not model_class:
                    logger.error(f"Plataforma no soportada: {platform}")
                    return None

                self._api_instances[platform] = await sync_to_async(model_class.objects.filter(
                    business_unit=self.business_unit,
                    is_active=True
                ).select_related('business_unit').first)()
                
                if self._api_instances[platform]:
                    api = self._api_instances[platform]
                    required_attrs = {
                        'whatsapp': ['phoneID', 'api_token'],
                        'telegram': ['api_key'],
                        'messenger': ['page_access_token'],
                        'instagram': ['access_token'],
                        'slack': ['bot_token']
                    }
                    for attr in required_attrs.get(platform, []):
                        if not hasattr(api, attr) or not getattr(api, attr):
                            logger.error(f"Configuración incompleta para {platform} en BU {self.business_unit.name}: {attr} faltante")
                            self._api_instances[platform] = None
                            break
                    else:
                        cache.set(cache_key, api, timeout=CACHE_TIMEOUT)
                else:
                    logger.warning(f"No se encontró configuración activa para {platform} en BU {self.business_unit.name}")

        return self._api_instances[platform]

    async def send_platform_message(
        self,
        platform: str,
        user_id: str,
        message: str,
        api_instance: Optional[object] = None,
        options: Optional[List[Dict]] = None
    ) -> bool:
        """Envía mensajes a cualquier plataforma de manera dinámica"""
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
            'slack': self._send_slack  # Corregido: Añadido Slack
        }

        send_func = send_funcs.get(platform)
        if not send_func:
            logger.error(f"Plataforma no soportada: {platform}")
            return False

        return await send_func(user_id, message, api_instance, options)

    from tenacity import retry, stop_after_attempt
    @retry(stop=stop_after_attempt(MAX_RETRIES))
    async def send_message(
        self,
        platform: str,
        user_id: str,
        message: str,
        options: Optional[List[Dict]] = None
    ) -> bool:
        """Envía un mensaje al usuario en la plataforma especificada"""
        try:
            logger.info(f"[send_message] Enviando a {user_id} en {platform}, BU: {self.business_unit.name}")
            return await self.send_platform_message(platform, user_id, message, options=options)
        except Exception as e:
            logger.error(f"[send_message] Error: {e}", exc_info=True)
            return False

    from tenacity import retry, stop_after_attempt
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
                    api_key=api_instance.api_key  # Cambiar access_token por api_key
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

    # Actualizar send_menu para usar el diccionario
    from tenacity import retry, stop_after_attempt
    @retry(stop=stop_after_attempt(MAX_RETRIES))
    async def send_menu(self, platform: str, user_id: str):
        """Envía el menú principal dinámico basado en el estado del ChatState"""
        try:
            logger.info(f"[send_menu] 📩 Enviando menú a {user_id} en {platform} para {self.business_unit.name}")
            
            # Obtener el ChatState del usuario
            chat_state = await sync_to_async(ChatState.objects.filter)(
                user_id=user_id, business_unit=self.business_unit
            ).afirst()
            
            if not chat_state:
                logger.warning(f"[send_menu] No se encontró ChatState para {user_id}, usando 'initial'")
                state = "initial"
            else:
                state = chat_state.state

            # Determinar las opciones según el estado y la unidad de negocio
            bu_name = self.business_unit.name.lower()
            options_by_state = MENU_OPTIONS_BY_STATE.get(bu_name, MENU_OPTIONS_BY_STATE["default"])
            options = options_by_state.get(state, options_by_state["initial"])
            
            message = "📍 *Menú Principal*\nSelecciona una opción:"
            simplified_options = [{"title": opt["title"], "payload": opt["payload"]} for opt in options]

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

    from tenacity import retry, stop_after_attempt
    @retry(stop=stop_after_attempt(MAX_RETRIES))
    async def send_url(self, platform: str, user_id: str, url: str) -> bool:
        return await self.send_message(platform, user_id, f"Aquí tienes el enlace: {url}")

    from tenacity import retry, stop_after_attempt
    @retry(stop=stop_after_attempt(MAX_RETRIES))
    async def send_options(
        self,
        platform: str,
        user_id: str,
        message: str,
        buttons: Optional[List[Dict]] = None
    ) -> bool:
        """Envía mensaje con opciones al usuario"""
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
                'slack': self._send_slack_options  # Añadido soporte para Slack
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

    # Funciones específicas por canal
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
                    #access_token=api_instance.api_token,
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

    # Implementaciones específicas de send_options
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
        
class EmailService:
    def __init__(self, business_unit: BusinessUnit):
        self.business_unit = business_unit
        self._config = None

    async def get_config(self) -> ConfiguracionBU:
        """Obtiene la configuración de correo de la unidad de negocio"""
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
        """Envía un correo electrónico"""
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
    def __init__(self):
        pass

    async def award_points(self, user: Person, activity_type: str, points: int = 10):
        """Otorga puntos al usuario por una actividad"""
        try:
            profile, created = await sync_to_async(EnhancedNetworkGamificationProfile.objects.get_or_create)(
                user=user,
                defaults={'points': 0, 'level': 1}
            )
            
            # Asumiendo que award_points es un método sincrónico
            await sync_to_async(profile.award_points)(activity_type, points)
            await sync_to_async(profile.save)()
            
            logger.info(f"[GamificationService] Otorgados {points} puntos a {user.nombre}")
            
            # Notificar al usuario
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


# ================================
# FUNCIONES PARA OBTENER BUSINESS UNIT DINÁMICO
# ================================
async def get_business_unit(name: Optional[str] = None) -> Optional[BusinessUnit]:
    """
    Obtiene la Business Unit de forma segura.

    Args:
        name (Optional[str]): Nombre de la unidad de negocio (opcional).

    Returns:
        Optional[BusinessUnit]: Objeto BusinessUnit si se encuentra, None si no.
    """
    try:
        if name:
            logger.debug(f"[get_business_unit] Buscando BusinessUnit con nombre: {name}")
            business_unit = await sync_to_async(lambda: BusinessUnit.objects.filter(name__iexact=name).first())()
        else:
            logger.debug("[get_business_unit] Buscando primera BusinessUnit disponible")
            business_unit = await sync_to_async(lambda: BusinessUnit.objects.first())()

        if business_unit:
            logger.info(f"[get_business_unit] BusinessUnit encontrada: {business_unit.name}")
            return business_unit
        else:
            logger.warning(f"[get_business_unit] No se encontró BusinessUnit para nombre: {name}")
            return None

    except Exception as e:
        logger.error(f"[get_business_unit] Error obteniendo BusinessUnit ({name}): {e}", exc_info=True)
        return None

def run_async(func, *args, **kwargs):
    """ Ejecuta la función en modo síncrono o asíncrono según el contexto. """
    try:
        loop = asyncio.get_running_loop()
        return func(*args, **kwargs)
    except RuntimeError:
        return asyncio.run(func(*args, **kwargs))

async def reset_chat_state(user_id: str, business_unit: BusinessUnit, platform: Optional[str] = None):
        """
        Reinicia el estado de la conversación (ChatState) para un usuario en una unidad de negocio específica.
        
        Args:
            user_id (str): Identificador del usuario.
            business_unit (BusinessUnit): Unidad de negocio asociada al chat.
            platform (Optional[str]): Nombre del canal (e.g., 'whatsapp', 'telegram') para enviar mensaje de confirmación.
        """
        try:
            # Busca y elimina el ChatState existente
            chat_state = await sync_to_async(ChatState.objects.get)(user_id=user_id, business_unit=business_unit)
            await sync_to_async(chat_state.delete)()
            logger.info(f"🧹 ChatState reiniciado para {user_id} en {business_unit.name}")
            
            # Si se especifica una plataforma, envía un mensaje de confirmación
            if platform:
                await send_message(platform, user_id, "🧹 Conversación reiniciada. Envía un mensaje para comenzar de nuevo.", business_unit)
        except ChatState.DoesNotExist:
            # Si no existe un ChatState, no hay nada que reiniciar
            logger.info(f"🧹 No se encontró ChatState para {user_id} en {business_unit.name}, no hay nada que reiniciar.")
            if platform:
                await send_message(platform, user_id, "🧹 No había conversación activa, pero estás listo para comenzar de nuevo.", business_unit)
# ================================
# WRAPPERS PARA FUNCIONES ASÍNCRONAS Y SINCRÓNICAS -----  NO MODIFICAR POR FAVOR
# ================================
async def send_message_async(platform: str, user_id: str, message: str, business_unit_name: Optional[str] = None):
    """
    Envío de mensaje asíncrono con validación de Business Unit.

    Args:
        platform (str): Plataforma donde se enviará el mensaje (WhatsApp, Telegram, Messenger, Instagram).
        user_id (str): ID del usuario al que se enviará el mensaje.
        message (str): Contenido del mensaje a enviar.
        business_unit_name (Optional[str]): Nombre de la unidad de negocio (opcional).

    Returns:
        bool: True si el mensaje se envió correctamente, False en caso contrario.
    """
    try:
        business_unit = await get_business_unit(business_unit_name)
        if not business_unit:
            logger.error(f"[send_message_async] ❌ No se encontró BusinessUnit para {business_unit}")
            return False

        service = MessageService(business_unit)
        success = await service.send_message(platform, user_id, message)

        if success:
            logger.info(f"[send_message_async] ✅ Mensaje enviado a {user_id} en {platform}: {message}")
        else:
            logger.warning(f"[send_message_async] ⚠️ Fallo en el envío de mensaje a {user_id} en {platform}")

        return success

    except Exception as e:
        logger.error(f"[send_message_async] ❌ Error enviando mensaje a {user_id} en {platform}: {e}", exc_info=True)
        return False

def send_message(platform: str, user_id: str, message: str, business_unit: str = None):
    """ Envío de mensaje de forma segura en entornos síncronos y asíncronos. """
    return run_async(send_message_async, platform, user_id, message, business_unit)

async def send_email_async(subject: str, to_email: str, body: str, business_unit_name: str = None, from_email=None):
    """ Versión asíncrona de `send_email`. """
    business_unit = await get_business_unit(business_unit_name)
    if business_unit:
        service = EmailService(business_unit)
        return await service.send_email(subject, to_email, body, from_email)
    logger.error(f"❌ No se encontró la unidad de negocio")
    return False

def send_email(subject: str, to_email: str, body: str, business_unit_name: str = None, from_email=None):
    """ Wrapper de `send_email`, compatible con entornos síncronos y asíncronos. """
    return run_async(send_email_async, subject, to_email, body, business_unit, from_email)

async def send_list_options(platform: str, user_id: str, message: str, buttons: List[Dict], business_unit_name: str):
    """
    Envía una lista interactiva en WhatsApp si hay más de 3 opciones.
    """
    from app.chatbot.integrations.whatsapp import send_whatsapp_list

    if platform != "whatsapp":
        success = await send_options(platform, user_id, message, buttons, business_unit_name)
        return success, None
    sections = [{"title": "Opciones", "rows": [{"id": btn["payload"], "title": btn["title"]} for btn in buttons]}]
    success = await send_whatsapp_list(user_id, message, sections, business_unit_name)
    msg_id = "msg_id_placeholder" if success else None  # Reemplaza con el ID real si la API lo devuelve
    return success, msg_id
#Envio de Lista Interactiva para cuando hay más de 3 botones

async def send_smart_options(platform, user_id, message, options, business_unit_name):
    """
    Envía opciones interactivas de manera optimizada:
    - Si hay solo botones con URL, los envía como mensajes separados.
    - Si hay 1 botón con URL y otros sin URL, primero envía la URL, luego los botones tras 2 segundos.
    - Si hay más de 3 opciones en WhatsApp, usa listas interactivas.
    - Si la lista interactiva falla, divide en lotes de 3 botones.
    - Si hay 3 o menos opciones, usa botones directamente.
    """
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
                last_msg_id = "msg_id_placeholder"  # Reemplaza con el ID real si está disponible
                await asyncio.sleep(0.5)

            return True, last_msg_id

        else:
            success = await service.send_options(platform, user_id, message, options)
            return success, "msg_id_placeholder" if success else None

    except Exception as e:
        logger.error(f"[send_smart_options] ❌ Error enviando opciones a {user_id}: {e}", exc_info=True)
        return False, None
           
async def send_options_async(platform: str, user_id: str, message: str, buttons=None, business_unit_name: str = None):
    """
    Envío de mensaje con botones interactivos de forma asíncrona.

    Args:
        platform (str): Plataforma donde se enviará el mensaje (WhatsApp, Telegram, Messenger, Instagram).
        user_id (str): ID del usuario al que se enviará el mensaje.
        message (str): Contenido del mensaje.
        buttons (Optional[List[Dict]]): Lista de botones interactivos.
        business_unit_name (Optional[str]): Nombre de la unidad de negocio.

    Returns:
        bool: True si se envió correctamente, False en caso contrario.
    """
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
            
            # ✅ Asegurar que los títulos no se corten arbitrariamente
            formatted_buttons = []
            for i, btn in enumerate(buttons[:3]):  # WhatsApp permite máximo 3 botones
                if "title" in btn and "payload" in btn:
                    formatted_buttons.append({
                        "type": "reply",
                        "reply": {
                            "id": btn["payload"],  # ID debe ser el payload correcto
                            "title": btn["title"][:20]  # Máximo 20 caracteres
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
    """ Wrapper de `send_options_async`, compatible con entornos síncronos y asíncronos. """
    return run_async(send_options_async, platform, user_id, message, buttons, business_unit_name)

async def send_menu_async(platform: str, user_id: str, business_unit: Optional[str] = None):
    """ Envía el menú principal al usuario en la plataforma especificada. """
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
    """ Envía una imagen con un mensaje al usuario en la plataforma especificada. """
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
    """ Envía un enlace al usuario en la plataforma especificada. """
    business_unit = await get_business_unit(business_unit)
    
    if not business_unit:
        logger.error(f"❌ No se encontró la unidad de negocio para {platform} - Usuario: {user_id}")
        return False
    
    logger.info(f"🔗 Enviando enlace a {user_id} en {platform} - URL: {url}")
    service = MessageService(business_unit)
    return await service.send_url(platform, user_id, url)

def send_url(platform: str, user_id: str, url: str, business_unit_name: str = None):
    return run_async(send_url_async, platform, user_id, url, business_unit_name)