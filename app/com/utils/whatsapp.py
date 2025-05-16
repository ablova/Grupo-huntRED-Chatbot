from typing import Dict, Optional
from django.conf import settings
from django.db import transaction
from app.models import NotificationChannel, NotificationConfig, MetaAPI, WhatsAppConfig
import logging
import asyncio
import json
import httpx

class WhatsAppApi:
    def __init__(self):
        """Inicializa la API de WhatsApp con la configuración de Meta API."""
        self.logger = logging.getLogger("whatsapp_api")
        self.config = self._load_config()
        self.meta_api = self._load_meta_api()
        self.phone_id = None
        self.api_version = "v19.0"
        
        if self.meta_api:
            self.phone_id = self.meta_api.phone_number_id
        
    def _load_config(self) -> Optional[NotificationConfig]:
        """Carga la configuración de notificaciones."""
        try:
            config = NotificationConfig.objects.get(name="Canal de Notificaciones General")
            return config
        except NotificationConfig.DoesNotExist:
            self.logger.error("Configuración de notificaciones no encontrada")
            return None
            
    def _load_meta_api(self) -> Optional[MetaAPI]:
        """Carga la configuración de Meta API."""
        try:
            # Obtener la configuración activa
            meta_api = MetaAPI.objects.filter(active=True).first()
            
            if not meta_api:
                self.logger.error("No hay configuración activa de Meta API")
                return None
                
            return meta_api
            
        except Exception as e:
            self.logger.error(f"Error cargando Meta API: {str(e)}")
            return None
            
    def _get_whatsapp_config(self) -> Optional[WhatsAppConfig]:
        """Obtiene la configuración de WhatsApp."""
        try:
            return WhatsAppConfig.objects.filter(active=True).first()
        except Exception:
            return None
            
    def get_activation_link(self, token: str) -> str:
        """Obtiene el enlace de activación de WhatsApp."""
        whatsapp_config = self._get_whatsapp_config()
        if not whatsapp_config or not whatsapp_config.use_custom_activation_page:
            # Usar enlace directo si no hay configuración o no se usa página personalizada
            return f"https://wa.me/{self.meta_api.phone_id_formatted}?text=Activar%20servicio%20de%20notificaciones%20{token}"
        else:
            # Usar página personalizada
            return f"{whatsapp_config.activation_url}?token={token}"
            
    async def send_message(self, phone: str, message: str) -> bool:
        """
        Envía un mensaje por WhatsApp usando Meta API.
        
        Args:
            phone: Número de teléfono (formato internacional sin +)
            message: Mensaje a enviar
            
        Returns:
            bool: True si el mensaje se envió correctamente
        """
        try:
            if not self.meta_api or not self.phone_id:
                self.logger.error("Meta API no está configurada")
                return False
                
            # Asegurar formato correcto del teléfono (remover + si existe)
            if phone.startswith("+"):
                phone = phone[1:]
                
            # Construir el endpoint
            endpoint = f"https://graph.facebook.com/{self.api_version}/{self.phone_id}/messages"
            
            # Construir el payload
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": phone,
                "type": "text",
                "text": {"body": message}
            }
            
            # Construir los headers
            headers = {
                "Authorization": f"Bearer {self.meta_api.access_token}",
                "Content-Type": "application/json"
            }
            
            # Enviar la solicitud
            async with httpx.AsyncClient() as client:
                response = await client.post(endpoint, json=payload, headers=headers)
                
                if response.status_code in [200, 201]:
                    # Registrar el envío exitoso
                    response_data = response.json()
                    await self._log_message(phone, message, response_data)
                    self.logger.info(f"Mensaje enviado exitosamente: {response_data}")
                    return True
                else:
                    self.logger.error(f"Error enviando mensaje: {response.text}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Error enviando mensaje: {str(e)}")
            return False
            
    async def _log_message(self, phone: str, message: str, response: Dict = None):
        """Registra el mensaje enviado en la base de datos."""
        try:
            # Implementar registro de mensajes para auditoría
            from app.models import MessageLog
            
            await MessageLog.objects.acreate(
                phone=phone,
                message=message[:255],  # Limitar longitud
                status="SENT",
                message_type="WHATSAPP",
                response_data=response or {}
            )
            
        except Exception as e:
            self.logger.error(f"Error registrando mensaje: {str(e)}")
            
    async def update_config(self, config_data: Dict) -> bool:
        """
        Actualiza la configuración de WhatsApp.
        
        Args:
            config_data: Datos de configuración a actualizar
            
        Returns:
            bool: True si la configuración se actualizó correctamente
        """
        try:
            if not self.config:
                return False
                
            with transaction.atomic():
                # Actualizar configuración general
                for field, value in config_data.items():
                    if hasattr(self.config, field):
                        setattr(self.config, field, value)
                self.config.save()
                
                # Actualizar configuración específica de WhatsApp
                if 'whatsapp' in config_data:
                    self.config.update_channel_config('WHATSAPP', config_data['whatsapp'])
                
                # Recargar configuración
                self.config = self._load_config()
                self.meta_api = self._load_meta_api()
                
                if self.meta_api:
                    self.phone_id = self.meta_api.phone_number_id
                
            return True
            
        except Exception as e:
            self.logger.error(f"Error actualizando configuración: {str(e)}")
            return False

class WhatsAppHandler:
    """Handler para WhatsApp (compatible con versiones anteriores)."""
    def __init__(self):
        self.api = WhatsAppApi()
        
    async def send_message(self, phone: str, message: str) -> bool:
        """Envía un mensaje por WhatsApp."""
        return await self.api.send_message(phone, message)
