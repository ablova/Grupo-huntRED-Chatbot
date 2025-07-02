# app/ats/integrations/notifications/channels/sms.py
"""
Canal de notificación SMS utilizando MessageBird

Este módulo implementa un canal de notificación SMS utilizando MessageBird,
una API confiable con buen soporte para México y Latinoamérica.

Ofreciendo mejores tasas de entrega y reportes detallados comparado con
alternativas gratuitas como TextBelt.
"""

import logging
import requests
import json
import time
from typing import Dict, Any, Optional
from datetime import datetime
from django.conf import settings

from app.models import BusinessUnit
from app.ats.integrations.notifications.channels.base import RequireInitiationChannel

logger = logging.getLogger('chatbot')

class SMSNotificationChannel(RequireInitiationChannel):
    """
    Canal de notificaciones para SMS utilizando MessageBird.

    MessageBird proporciona una API confiable con excelente soporte
    para México y Latinoamérica, permitiendo enviar SMS de manera
    segura y eficiente.
    """

    # URL del API de MessageBird
    API_URL = "https://rest.messagebird.com/messages"

    def __init__(self, business_unit: BusinessUnit):
        """Inicializar el canal de SMS."""
        super().__init__(business_unit)
        self.business_unit = business_unit
        
        # Obtener configuración de MessageBird desde la integración centralizada
        config = business_unit.get_integration_config('messagebird') or {}
        
        # Obtener API key y otras configuraciones con valores por defecto
        self.api_key = config.get('api_key', getattr(settings, 'MESSAGEBIRD_API_KEY', ''))
        self.from_number = config.get('from_number', getattr(settings, 'SMS_FROM_NUMBER', 'huntRED'))
        self.dlr_enabled = config.get('dlr_enabled', True)
        self.dlr_url = config.get('dlr_url', getattr(settings, 'MESSAGEBIRD_WEBHOOK_URL', None))
        self.sandbox_mode = config.get('sandbox_mode', False)
        
        # Si no hay API key configurada, mostrar advertencia
        if not self.api_key:
            logger.warning(f"No se encontró API key de MessageBird para la BU {business_unit.name}. SMS no funcionará correctamente.")

    def _get_initiation_message(self) -> str:
        """
        Obtiene el mensaje de iniciación para SMS.

        Returns:
            Mensaje de iniciación
        """
        return (
            f"¡Hola! Soy el asistente de {self.business_unit.name}. "
            "Para recibir notificaciones importantes, por favor responde a este mensaje. "
            "También puedes recibir notificaciones por WhatsApp o Telegram."
        )

    async def _send_initiation(self, user_id: str, message: str) -> Dict[str, Any]:
        """
        Envía el mensaje de iniciación por SMS.
        
        Args:
            user_id: Número telefónico del destinatario
            message: Mensaje a enviar
        
        Returns:
            Dict con el resultado de la operación
        """
        try:
            # Formato internacional para el número
            phone = self._format_phone_number(user_id)
            
            # Enviar SMS a través de MessageBird
            headers = {
                'Authorization': f'AccessKey {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'originator': self.from_number,
                'recipients': [phone],
                'body': message,
                'reference': f'init-{int(datetime.now().timestamp())}',  # Referencia única
                'type': 'sms'
            }
            
            response = requests.post(
                self.API_URL, 
                headers=headers,
                json=payload
            )
            
            result = response.json()
            
            if response.status_code == 201 and 'id' in result:
                return {
                    'success': True,
                    'message_id': result.get('id'),
                    'timestamp': datetime.now().isoformat(),
                    'recipients': len(result.get('recipients', []))
                }
            else:
                error = result.get('errors', [{'description': 'Unknown error'}])[0]['description']
                logger.error(f"Error enviando SMS de iniciación: {error}")
                return {
                    'success': False,
                    'error': error,
                }
            
        except Exception as e:
            logger.error(f"Error enviando SMS de iniciación: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    async def send_notification(
        self,
        message: str,
        options: Optional[Dict[str, Any]] = None,
        priority: int = 0
    ) -> Dict[str, Any]:
        """
        Envía una notificación por SMS.
        
        Args:
            message: Mensaje a enviar
            options: Opciones adicionales
            priority: Prioridad de la notificación (0-5)
        
        Returns:
            Dict con el resultado de la operación
        """
        try:
            user_id = options.get('user_id') if options else None
            
            if not user_id:
                return {
                    'success': False,
                    'error': 'Se requiere user_id (número telefónico) para enviar la notificación'
                }
            
            # Verificar si se puede enviar
            if not await self.can_send_notification(user_id):
                return await self.send_initiation_message(user_id)
            
            # Formatear el mensaje según la prioridad
            formatted_message = self._format_message(message, priority)
            
            # Formato internacional para el número
            phone = self._format_phone_number(user_id)
            
            # Enviar SMS a través de MessageBird
            headers = {
                'Authorization': f'AccessKey {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            # Generar referencia única para este mensaje
            reference = f'msg-{int(datetime.now().timestamp())}-{priority}'
            
            payload = {
                'originator': self.from_number,
                'recipients': [phone],
                'body': formatted_message,
                'reference': reference,
                'type': 'sms',
                # Agregar parametrización DLR (Delivery Receipt)
                'dlr': self.dlr_enabled,
                'dlr_url': self.dlr_url
            }
            
            # Eliminar valores None del payload
            payload = {k: v for k, v in payload.items() if v is not None}
            
            response = requests.post(
                self.API_URL, 
                headers=headers,
                json=payload
            )
            
            result = response.json()
            
            if response.status_code == 201 and 'id' in result:
                # Extraer información del envío
                message_id = result.get('id')
                recipient_status = result.get('recipients', {}).get('items', [{}])[0].get('status', 'sent')
                
                # Registrar en MessageLog para seguimiento y reportes
                from app.models import MessageLog
                
                # Clasificar mensaje para Meta 2025 (más para consistencia que por necesidad para SMS)
                meta_pricing = options.get('meta_pricing', {}) if options else {}
                model = meta_pricing.get('model', 'service')
                msg_type = meta_pricing.get('type', 'standard')
                category = meta_pricing.get('category', 'general')
                
                try:
                    MessageLog.objects.create(
                        business_unit=self.business_unit,
                        channel='sms',
                        message_type='SMS',
                        phone=phone,
                        message=formatted_message,
                        status=recipient_status.upper(),
                        response_data=result,
                        meta_pricing_model=model,
                        meta_pricing_type=msg_type,
                        meta_pricing_category=category,
                        external_id=message_id,
                        reference=reference,
                        sent_at=datetime.now()
                    )
                except Exception as log_error:
                    logger.warning(f"No se pudo registrar SMS en MessageLog: {str(log_error)}")
                
                return {
                    'success': True,
                    'channel': 'SMS',
                    'message_id': message_id,
                    'recipient_phone': phone,
                    'status': recipient_status,
                    'reference': reference,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                # Extraer mensaje de error
                error = result.get('errors', [{'description': 'Unknown error'}])[0]['description']
                logger.error(f"Error enviando SMS: {error}")
                return {
                    'success': False,
                    'error': error
                }
            
        except Exception as e:
            logger.error(f"Error enviando SMS: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def _format_message(self, message: str, priority: int) -> str:
        """
        Formatea el mensaje según la prioridad.

        Args:
            message: Mensaje original
            priority: Nivel de prioridad (0-5)

        Returns:
            Mensaje formateado
        """
        if priority >= 4:
            return f"URGENTE: {message}"
        elif priority >= 2:
            return f"IMPORTANTE: {message}"
        else:
            return message

    def _format_phone_number(self, phone_number: str) -> str:
        """
        Formatea el número de teléfono para asegurar formato internacional.

        Args:
            phone_number: Número telefónico a formatear

        Returns:
            Número telefónico en formato internacional
        """
        # Eliminar espacios y caracteres no numéricos
        clean_number = ''.join(filter(str.isdigit, phone_number))

        # Si ya tiene prefijo internacional (+), lo dejamos como está
        if phone_number.startswith('+'):
            return clean_number

        # Si no tiene prefijo, asumimos que es un número local y añadimos prefijo de México
        # (ajustar según país predeterminado de la plataforma)
        if not clean_number.startswith('52') and len(clean_number) == 10:
            clean_number = '52' + clean_number

        return clean_number