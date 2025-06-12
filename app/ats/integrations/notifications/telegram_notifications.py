from typing import Dict, Any, Optional
import logging
import aiohttp
from django.conf import settings
from app.ats.chatbot.models.business_unit import BusinessUnit

logger = logging.getLogger(__name__)

class TelegramNotifier:
    """
    Manejador de notificaciones vía Telegram por Business Unit.
    """
    
    def __init__(self, business_unit_id: int):
        self.business_unit_id = business_unit_id
        self.business_unit = BusinessUnit.objects.get(id=business_unit_id)
        self.api_token = self.business_unit.telegram_bot_token
        self.channel_id = self.business_unit.telegram_channel_id
        self.base_url = f"https://api.telegram.org/bot{self.api_token}"
        
    async def send_message(self, message: str, parse_mode: str = "Markdown") -> Dict[str, Any]:
        """
        Envía un mensaje al canal de Telegram de la Business Unit.
        
        Args:
            message: Mensaje a enviar
            parse_mode: Modo de parseo del mensaje (Markdown o HTML)
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/sendMessage",
                    json={
                        "chat_id": self.channel_id,
                        "text": message,
                        "parse_mode": parse_mode
                    }
                ) as response:
                    result = await response.json()
                    
                    if not result.get("ok"):
                        logger.error(f"Error enviando mensaje a Telegram para BU {self.business_unit.name}: {result.get('description')}")
                        return {
                            'success': False,
                            'error': result.get('description')
                        }
                    
                    return {
                        'success': True,
                        'message_id': result['result']['message_id']
                    }
                    
        except Exception as e:
            logger.error(f"Error en comunicación con Telegram para BU {self.business_unit.name}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def send_preselection_notification(self, preselection_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Envía una notificación sobre una pre-selección.
        """
        try:
            # Preparar mensaje
            message = (
                f"*Nueva Pre-selección Pendiente* 🎯\n\n"
                f"*Vacante:* {preselection_data['vacancy']}\n"
                f"*Candidatos:* {preselection_data['total_candidates']}\n"
                f"*Creada:* {preselection_data['created_at']}\n\n"
                f"Por favor, revisa los candidatos en el sistema.\n"
                f"ID de Pre-selección: `{preselection_data['id']}`"
            )
            
            return await self.send_message(message)
            
        except Exception as e:
            logger.error(f"Error enviando notificación de pre-selección para BU {self.business_unit.name}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def send_review_reminder(self, preselection_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Envía un recordatorio de revisión.
        """
        try:
            # Preparar mensaje
            message = (
                f"*Recordatorio de Revisión* ⏰\n\n"
                f"*Vacante:* {preselection_data['vacancy']}\n"
                f"*Tiempo pendiente:* {preselection_data['hours_pending']:.1f} horas\n"
                f"*Candidatos:* {preselection_data['total_candidates']}\n\n"
                f"Por favor, completa la revisión lo antes posible.\n"
                f"ID de Pre-selección: `{preselection_data['id']}`"
            )
            
            return await self.send_message(message)
            
        except Exception as e:
            logger.error(f"Error enviando recordatorio para BU {self.business_unit.name}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def send_review_completed(self, preselection_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Notifica la finalización de una revisión.
        """
        try:
            # Preparar mensaje
            message = (
                f"*Revisión Completada* ✅\n\n"
                f"*Vacante:* {preselection_data['vacancy']}\n"
                f"*Candidatos seleccionados:* {preselection_data['selected_candidates']}\n"
                f"*Tiempo de revisión:* {preselection_data['review_time']}\n\n"
                f"Los candidatos seleccionados serán notificados automáticamente."
            )
            
            return await self.send_message(message)
            
        except Exception as e:
            logger.error(f"Error enviando notificación de completado para BU {self.business_unit.name}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def send_error_notification(self, error_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Envía una notificación de error.
        """
        try:
            # Preparar mensaje
            message = (
                f"*Error en el Sistema* ⚠️\n\n"
                f"*Tipo:* {error_data['type']}\n"
                f"*Descripción:* {error_data['description']}\n"
                f"*Timestamp:* {error_data['timestamp']}\n\n"
                f"Por favor, revisa los logs para más detalles."
            )
            
            return await self.send_message(message)
            
        except Exception as e:
            logger.error(f"Error enviando notificación de error para BU {self.business_unit.name}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            } 