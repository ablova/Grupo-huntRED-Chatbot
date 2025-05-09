from abc import ABC, abstractmethod
from typing import List, Dict

class BaseRecipient(ABC):
    """Clase base para todos los destinatarios de notificaciones."""
    
    @abstractmethod
    def get_contact_info(self) -> Dict[str, str]:
        """Obtiene la información de contacto del destinatario."""
        pass
        
    @abstractmethod
    def get_preferred_channels(self) -> List[str]:
        """Obtiene los canales preferidos de comunicación."""
        pass
        
    @abstractmethod
    def get_notification_context(self) -> Dict:
        """Obtiene el contexto para las notificaciones."""
        pass
