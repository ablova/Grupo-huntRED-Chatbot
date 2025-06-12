"""
Clase base para canales que requieren iniciación de conversación.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from django.conf import settings
from django.core.cache import cache

from app.models import BusinessUnit, User, MessageLog
from app.ats.integrations.notifications.core.base import BaseNotificationChannel

class RequireInitiationChannel(BaseNotificationChannel):
    """Canal base para plataformas que requieren iniciación de conversación."""
    
    def __init__(self, business_unit: BusinessUnit):
        super().__init__(business_unit)
        self.initiation_window = timedelta(hours=24)  # Ventana de tiempo para iniciar conversación
        self.max_retries = 3  # Número máximo de reintentos
    
    async def can_send_notification(self, user_id: str) -> bool:
        """
        Verifica si se puede enviar una notificación al usuario.
        
        Args:
            user_id: ID del usuario
        
        Returns:
            True si se puede enviar, False en caso contrario
        """
        # Verificar si el usuario ha iniciado conversación
        cache_key = f"{self.get_channel_name()}_initiated_{user_id}"
        is_initiated = cache.get(cache_key)
        
        if not is_initiated:
            # Verificar en la base de datos
            last_message = await sync_to_async(MessageLog.objects.filter)(
                platform=self.get_channel_name(),
                user_id=user_id,
                direction='incoming'
            ).order_by('-created_at').first()
            
            if last_message:
                # Si hay un mensaje reciente, actualizar cache
                is_initiated = True
                cache.set(cache_key, True, timeout=self.initiation_window.total_seconds())
            else:
                # Si no hay mensaje, verificar si podemos enviar mensaje de iniciación
                return await self._can_send_initiation(user_id)
        
        return is_initiated
    
    async def _can_send_initiation(self, user_id: str) -> bool:
        """
        Verifica si se puede enviar un mensaje de iniciación.
        
        Args:
            user_id: ID del usuario
        
        Returns:
            True si se puede enviar, False en caso contrario
        """
        # Verificar número de intentos
        cache_key = f"{self.get_channel_name()}_initiation_attempts_{user_id}"
        attempts = cache.get(cache_key, 0)
        
        if attempts >= self.max_retries:
            return False
        
        # Verificar último intento
        last_attempt_key = f"{self.get_channel_name()}_last_initiation_{user_id}"
        last_attempt = cache.get(last_attempt_key)
        
        if last_attempt:
            # Si el último intento fue hace menos de 24 horas, no permitir nuevo intento
            if datetime.now() - last_attempt < self.initiation_window:
                return False
        
        return True
    
    async def send_initiation_message(self, user_id: str) -> Dict[str, Any]:
        """
        Envía un mensaje de iniciación al usuario.
        
        Args:
            user_id: ID del usuario
        
        Returns:
            Dict con el resultado de la operación
        """
        try:
            # Incrementar contador de intentos
            cache_key = f"{self.get_channel_name()}_initiation_attempts_{user_id}"
            attempts = cache.get(cache_key, 0) + 1
            cache.set(cache_key, attempts, timeout=self.initiation_window.total_seconds())
            
            # Registrar último intento
            last_attempt_key = f"{self.get_channel_name()}_last_initiation_{user_id}"
            cache.set(last_attempt_key, datetime.now(), timeout=self.initiation_window.total_seconds())
            
            # Enviar mensaje de iniciación
            message = self._get_initiation_message()
            result = await self._send_initiation(user_id, message)
            
            if result.get('success'):
                # Registrar el mensaje
                await sync_to_async(MessageLog.objects.create)(
                    platform=self.get_channel_name(),
                    user_id=user_id,
                    message=message,
                    direction='outgoing',
                    status='sent',
                    business_unit=self.business_unit
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Error enviando mensaje de iniciación: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @abstractmethod
    def _get_initiation_message(self) -> str:
        """
        Obtiene el mensaje de iniciación.
        
        Returns:
            Mensaje de iniciación
        """
        pass
    
    @abstractmethod
    async def _send_initiation(self, user_id: str, message: str) -> Dict[str, Any]:
        """
        Envía el mensaje de iniciación.
        
        Args:
            user_id: ID del usuario
            message: Mensaje a enviar
        
        Returns:
            Dict con el resultado de la operación
        """
        pass
    
    async def send_notification(
        self,
        message: str,
        options: Optional[Dict[str, Any]] = None,
        priority: int = 0
    ) -> Dict[str, Any]:
        """
        Envía una notificación, verificando primero si se puede enviar.
        
        Args:
            message: Mensaje a enviar
            options: Opciones adicionales
            priority: Prioridad de la notificación
        
        Returns:
            Dict con el resultado de la operación
        """
        user_id = options.get('user_id') if options else None
        
        if not user_id:
            return {
                'success': False,
                'error': 'Se requiere user_id para enviar la notificación'
            }
        
        if not await self.can_send_notification(user_id):
            # Intentar enviar mensaje de iniciación
            initiation_result = await self.send_initiation_message(user_id)
            
            if not initiation_result.get('success'):
                return {
                    'success': False,
                    'error': 'No se puede enviar la notificación y falló el mensaje de iniciación',
                    'initiation_error': initiation_result.get('error')
                }
            
            return {
                'success': False,
                'error': 'Se requiere iniciar conversación',
                'initiation_sent': True
            }
        
        # Si se puede enviar, proceder con el envío normal
        return await super().send_notification(message, options, priority) 