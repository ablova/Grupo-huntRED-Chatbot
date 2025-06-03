# /home/pablo/app/com/chatbot/rate_limiter.py
#
# Módulo para gestionar límites de tasa en canales de comunicación.
# Previene sobrecargas de APIs externas y cumple con términos de servicio.
# Optimizado para bajo uso de CPU, escalabilidad, y robustez frente a fallos.

from collections import defaultdict
from datetime import datetime, timedelta
import asyncio
import logging

logger = logging.getLogger('chatbot')

class RateLimiter:
    """Limitador de tasa para canales de comunicación con prevención de ráfagas y recuperación."""

    def __init__(self, requests_per_minute=None):
        """
        Inicializa el limitador de tasa.
        
        Args:
            requests_per_minute (dict, optional): Límites por canal. Anula configuración predeterminada.
        """
        self.limits = defaultdict(int)
        self.last_reset = defaultdict(lambda: datetime.now())
        
        # Límites predeterminados por canal (mensajes por minuto)
        self.channel_limits = {
            'whatsapp': 20,
            'telegram': 30,
            'messenger': 30,
            'slack': 50,
            'instagram': 20
        }
        
        # Actualizar con límites personalizados si se proporcionan
        if requests_per_minute:
            if isinstance(requests_per_minute, dict):
                self.channel_limits.update(requests_per_minute)
            elif isinstance(requests_per_minute, int):
                for channel in self.channel_limits:
                    self.channel_limits[channel] = requests_per_minute
    
    async def check_limit(self, channel: str) -> bool:
        """
        Verifica si podemos enviar otro mensaje en este canal.
        
        Args:
            channel (str): El canal a verificar (whatsapp, telegram, etc.)
            
        Returns:
            bool: True si está dentro del límite, False si excede
        """
        if channel not in self.channel_limits:
            return True

        limit = self.channel_limits[channel]
        now = datetime.now()
        
        # Resetear contadores después de un minuto
        if (now - self.last_reset[channel]).total_seconds() > 60:
            self.limits[channel] = 0
            self.last_reset[channel] = now
        
        # Verificar si estamos dentro del límite
        if self.limits[channel] < limit:
            self.limits[channel] += 1
            return True
        
        # Si excedemos el límite, registrarlo y devolver False
        logger.warning(f"Rate limit exceeded for {channel}: {self.limits[channel]}/{limit}")
        return False
    
    async def wait_if_needed(self, channel: str) -> None:
        """
        Espera si es necesario para cumplir con los límites de tasa.
        
        Args:
            channel (str): El canal a verificar
        """
        while not await self.check_limit(channel):
            await asyncio.sleep(1)
