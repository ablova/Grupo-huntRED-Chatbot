# /home/pablo/app/chatbot/integrations/services.py

import logging
import smtplib
import asyncio
import ssl
from typing import Optional, List, Dict, Union, Any
from asgiref.sync import sync_to_async
from django.core.cache import cache
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.models import (
    BusinessUnit, ConfiguracionBU, WhatsAppAPI, TelegramAPI, 
    InstagramAPI, MessengerAPI, ChatState, Person,
    EnhancedNetworkGamificationProfile
)

logger = logging.getLogger("app.chatbot.services")

# Constantes globales
MAX_RETRIES = 3
REQUEST_TIMEOUT = 10.0
CACHE_TIMEOUT = 600  # 10 minutos
whatsapp_semaphore = asyncio.Semaphore(10)

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
                    'instagram': InstagramAPI
                }
                model_class = model_mapping.get(platform)
                if not model_class:
                    raise ValueError(f"Plataforma no soportada: {platform}")

                self._api_instances[platform] = await sync_to_async(model_class.objects.filter(
                    business_unit=self.business_unit,
                    is_active=True
                ).select_related('business_unit').first)()
                
                if self._api_instances[platform]:
                    cache.set(cache_key, self._api_instances[platform], timeout=CACHE_TIMEOUT)

        return self._api_instances[platform]

    async def send_message(
        self,
        platform: str,
        user_id: str,
        message: str,
        options: Optional[List[Dict]] = None
    ) -> bool:
        """Envía un mensaje al usuario en la plataforma especificada"""
        try:
            logger.info(f"[send_message] Plataforma: {platform}, User: {user_id}, BU: {self.business_unit.name}")
            
            api_instance = await self.get_api_instance(platform)
            if not api_instance:
                logger.error(f"[send_message] No se encontró configuración API para {platform}")
                return False

            if platform == 'whatsapp':
                return await self._send_whatsapp_message(user_id, message, options, api_instance)
            elif platform == 'telegram':
                return await self._send_telegram_message(user_id, message, api_instance)
            elif platform in ['messenger', 'instagram']:
                return await self._send_meta_message(platform, user_id, message, options, api_instance)
            else:
                logger.error(f"[send_message] Plataforma no soportada: {platform}")
                return False

        except Exception as e:
            logger.error(f"[send_message] Error: {e}", exc_info=True)
            return False

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
                'instagram': self._send_instagram_options
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

    async def _send_whatsapp_message(
        self,
        user_id: str,
        message: str,
        options: Optional[List[Dict]],
        api_instance: WhatsAppAPI
    ) -> bool:
        """Envía mensaje por WhatsApp"""
        from app.chatbot.integrations.whatsapp import send_whatsapp_message
        
        try:
            async with whatsapp_semaphore:
                # Manejar URLs primero si hay opciones con URLs
                if options:
                    url_options = [opt for opt in options if 'url' in opt]
                    for opt in url_options:
                        await send_whatsapp_message(
                            user_id=user_id,
                            message=f"Más información: {opt['url']}",
                            phone_id=api_instance.phoneID,
                            business_unit=self.business_unit
                        )
                        await asyncio.sleep(0.5)

                # Enviar mensaje principal
                await send_whatsapp_message(
                    user_id=user_id,
                    message=message,
                    phone_id=api_instance.phoneID,
                    buttons=[opt for opt in (options or []) if 'url' not in opt],
                    business_unit=self.business_unit
                )
                return True

        except Exception as e:
            logger.error(f"Error enviando mensaje WhatsApp: {e}", exc_info=True)
            return False

    async def _send_telegram_message(
        self,
        user_id: str,
        message: str,
        api_instance: TelegramAPI
    ) -> bool:
        """Envía mensaje por Telegram"""
        from app.chatbot.integrations.telegram import send_telegram_message
        
        try:
            chat_id = int(user_id.split(":")[-1]) if ":" in user_id else int(user_id)
            await send_telegram_message(
                chat_id=chat_id,
                message=message,
                telegram_api=api_instance,
                business_unit_name=self.business_unit.name
            )
            return True

        except Exception as e:
            logger.error(f"Error enviando mensaje Telegram: {e}", exc_info=True)
            return False

    async def _send_meta_message(
        self,
        platform: str,
        user_id: str,
        message: str,
        options: Optional[List[Dict]],
        api_instance: Union[MessengerAPI, InstagramAPI]
    ) -> bool:
        """Envía mensaje por plataformas Meta (Messenger/Instagram)"""
        try:
            if platform == 'messenger':
                from app.chatbot.integrations.messenger import send_messenger_message
                send_func = send_messenger_message
            else:
                from app.chatbot.integrations.instagram import send_instagram_message
                send_func = send_instagram_message

            await send_func(
                user_id=user_id,
                message=message,
                buttons=options,
                access_token=api_instance.page_access_token or api_instance.api_key
            )
            return True

        except Exception as e:
            logger.error(f"Error enviando mensaje {platform}: {e}", exc_info=True)
            return False

    # Implementaciones específicas de send_options para cada plataforma
    async def _send_whatsapp_options(self, user_id, message, buttons, api_instance):
        from app.chatbot.integrations.whatsapp import send_whatsapp_decision_buttons
        
        url_buttons = [btn for btn in buttons if btn.url]
        option_buttons = [btn for btn in buttons if btn.payload][:3]
        
        try:
            for btn in url_buttons:
                await self.send_message(
                    'whatsapp',
                    user_id,
                    f"Más información: {btn.url}",
                    None
                )

            if option_buttons:
                formatted_buttons = [
                    {
                        "type": "reply",
                        "reply": {
                            "id": btn.payload,
                            "title": btn.title[:20]
                        }
                    }
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
                {
                    "text": btn.title,
                    "callback_data": btn.payload if btn.payload else "no_payload"
                }
                for btn in buttons
            ]

            await send_telegram_buttons(
                chat_id=chat_id,
                message=message,
                buttons=telegram_buttons,
                access_token=api_instance.api_key
            )
            return True

        except Exception as e:
            logger.error(f"Error enviando opciones Telegram: {e}", exc_info=True)
            return False

    async def _send_messenger_options(self, user_id, message, buttons, api_instance):
        from app.chatbot.integrations.messenger import send_messenger_buttons
        
        try:
            quick_replies = [
                {
                    'content_type': 'text',
                    'title': btn.title,
                    'payload': btn.payload or 'no_payload'
                }
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
                {
                    'title': btn.title,
                    'payload': btn.payload or 'no_payload'
                }
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
            
            logger.info(f"[send_email] Correo enviado exitosamente a {to_email}")
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