from abc import ABC, abstractmethod
from typing import Dict
import logging

logger = logging.getLogger('app.notifications.channels')

class BaseChannel(ABC):
    """Clase base para todos los canales de comunicación."""
    
    @abstractmethod
    def send(self, recipient: Dict, message: str, context: Dict) -> bool:
        """Envía un mensaje a través del canal."""
        pass
        
    def _log_message(self, recipient: Dict, message: str, success: bool):
        """Registra el envío del mensaje."""
        log_level = logging.INFO if success else logging.ERROR
        logger.log(
            log_level,
            f"Message sent via {self.__class__.__name__}: {message}"
            f"Recipient: {recipient}"
            f"Success: {success}"
        )
