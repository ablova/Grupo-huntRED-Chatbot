import logging
from telegram import Bot as TelegramBot
from telegram.error import TelegramError
from typing import Dict, Any
from django.conf import settings
from django.db import models
from app.publish.processors.base_processor import BaseProcessor
from app.publish.utils.content_adapters import TelegramAdapter

class TelegramProcessor(BaseProcessor):
    """
    Procesador para publicación en Telegram
    """
    def __init__(self, channel: Dict[str, Any]):
        super().__init__(channel)
        
    async def publish(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Publica contenido en Telegram
        """
        # Adaptar contenido para Telegram
        adapter = TelegramAdapter(content)
        adapted_content = adapter.adapt()
        
        # Obtener configuración específica para esta unidad de negocio
        config = self._get_telegram_config()
        self.bot = TelegramBot(token=config['api_key'])
        
        # Determinar el tipo de envío
        if self.channel['type'] == 'TELEGRAM_CHANNEL':
            return await self._send_to_channel(adapted_content)
        elif self.channel['type'] == 'TELEGRAM_BOT':
            return await self._send_to_bot(adapted_content)
        else:
            raise ValueError(f"Tipo de canal no soportado: {self.channel['type']}")
            
    async def get_analytics(self) -> Dict[str, Any]:
        """
        Obtiene métricas del canal
        """
        config = self._get_telegram_config()
        self.bot = TelegramBot(token=config['api_key'])
        try:
            # Telegram no proporciona métricas directas, se simulan
            return {
                'member_count': await self.bot.get_chat_member_count(self.channel['identifier']),
                'last_post_date': datetime.now().isoformat()
            }
        except TelegramError as e:
            self.logger.error(f"Error getting Telegram analytics: {str(e)}")
            raise
            
    def _get_telegram_config(self) -> Dict[str, Any]:
        """
        Obtiene la configuración de Telegram para esta unidad de negocio
        """
        from app.models import TelegramAPI
        
        try:
            config = TelegramAPI.objects.get(
                business_unit=self.business_unit,
                is_active=True
            )
            return {
                'api_key': config.api_key,
                'bot_name': config.bot_name
            }
        except TelegramAPI.DoesNotExist:
            self.logger.error(f"No se encontró configuración de Telegram para la unidad de negocio {self.business_unit.name}")
            raise
            
    async def _send_to_channel(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Envía contenido a un canal de Telegram
        """
        try:
            message = await self.bot.send_message(
                chat_id=self.channel['identifier'],
                text=content['text'],
                parse_mode='Markdown'
            )
            return {'message_id': message.message_id}
        except TelegramError as e:
            self.logger.error(f"Error sending to Telegram channel: {str(e)}")
            raise
            
    async def _send_to_bot(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Envía contenido a través de un bot
        """
        try:
            message = await self.bot.send_message(
                chat_id=self.channel['identifier'],
                text=content['text'],
                parse_mode='Markdown',
                reply_markup=content.get('reply_markup')
            )
            return {'message_id': message.message_id}
        except TelegramError as e:
            self.logger.error(f"Error sending through Telegram bot: {str(e)}")
            raise
            
    async def handle_callback(self, update: Any, context: Any) -> None:
        """
        Maneja callbacks de botones interactivos
        """
        try:
            # Obtener datos del callback
            callback_data = update.callback_query.data
            
            # Manejar diferentes tipos de callbacks
            if callback_data.startswith('apply_'):
                await self.handle_apply(update, context)
            elif callback_data.startswith('refer_'):
                await self.handle_refer(update, context)
            
        except Exception as e:
            self.logger.error(f"Error handling callback: {str(e)}")
            await update.callback_query.answer("Error al procesar la solicitud")
            
    async def handle_apply(self, update: Any, context: Any) -> None:
        """
        Maneja la aplicación de un usuario
        """
        try:
            # Extraer ID de la oportunidad
            opportunity_id = update.callback_query.data.split('_')[1]
            user_id = update.effective_user.id
            
            # Crear registro de aplicación
            from app.models import JobApplication
            application = await JobApplication.objects.acreate(
                opportunity_id=opportunity_id,
                user_id=user_id,
                status='pending'
            )
            
            # Responder al usuario
            await update.callback_query.answer("¡Solicitud enviada!")
            
        except Exception as e:
            self.logger.error(f"Error handling application: {str(e)}")
            await update.callback_query.answer("Error al procesar la solicitud")
            
    async def handle_refer(self, update: Any, context: Any) -> None:
        """
        Maneja la referencia de un usuario
        """
        try:
            # Extraer ID de la oportunidad
            opportunity_id = update.callback_query.data.split('_')[1]
            user_id = update.effective_user.id
            
            # Crear registro de referencia
            from app.models import JobReferral
            referral = await JobReferral.objects.acreate(
                opportunity_id=opportunity_id,
                referrer_id=user_id,
                status='pending'
            )
            
            # Responder al usuario
            await update.callback_query.answer("¡Referencia registrada!")
            
            # Enviar mensaje de referencia
            await update.callback_query.message.reply_text(
                "¡Perfecto! Ahora puedes compartir esta oportunidad con tus contactos."
                "Cada persona que se una a través de tu referencia, ganarás una bonificación."
            )
            
        except Exception as e:
            self.logger.error(f"Error handling referral: {str(e)}")
            await update.callback_query.answer("Error al procesar la referencia")
            
    async def create_reply_markup(self, opportunity_id: str) -> Any:
        """
        Crea el teclado interactivo para una oportunidad
        """
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        keyboard = [
            [
                InlineKeyboardButton("Aplicar", callback_data=f"apply_{opportunity_id}"),
                InlineKeyboardButton("Referir", callback_data=f"refer_{opportunity_id}")
            ]
        ]
        
        return InlineKeyboardMarkup(keyboard)
            
    async def format_job_post(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Formatea una oportunidad laboral para Telegram
        """
        return {
            'text': f"🌟 *Nueva Oportunidad: {opportunity['title']}*\n\n"
                   f"{opportunity['description']}\n\n"
                   f"📍 *Ubicación:* {opportunity['location']}\n"
                   f"💰 *Salario:* {opportunity['salary_range']}\n\n"
                   f"¿Te interesa? ¡Aplica ahora!",
            'parse_mode': 'Markdown',
            'reply_markup': await self.create_reply_markup(opportunity['id'])
        }
        
        # Determinar el tipo de envío
        if self.channel['type'] == 'TELEGRAM_CHANNEL':
            return await self.send_to_channel(adapted_content)
        elif self.channel['type'] == 'TELEGRAM_BOT':
            return await self.send_to_bot(adapted_content)
        else:
            raise ValueError(f"Tipo de canal no soportado: {self.channel['type']}")
            
    async def get_analytics(self) -> Dict[str, Any]:
        """
        Obtiene métricas del canal
        """
        try:
            # Telegram no proporciona métricas directas, se simulan
            return {
                'member_count': await self.bot.get_chat_member_count(self.channel['identifier']),
                'last_post_date': datetime.now().isoformat()
            }
        except TelegramError as e:
            self.logger.error(f"Error getting Telegram analytics: {str(e)}")
            raise
