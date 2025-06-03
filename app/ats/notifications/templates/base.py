from abc import ABC, abstractmethod
from typing import Dict
import logging

logger = logging.getLogger('app.ats.notifications.templates')

class BaseTemplate(ABC):
    """Clase base para todos los templates de notificaciones."""
    
    @abstractmethod
    def render(self, context: Dict) -> str:
        """Renderiza el template con el contexto proporcionado."""
        pass
        
    def _log_render(self, context: Dict, success: bool):
        """Registra el renderizado del template."""
        log_level = logging.INFO if success else logging.ERROR
        logger.log(
            log_level,
            f"Template rendered: {self.__class__.__name__}"
            f"Context: {context}"
            f"Success: {success}"
        )
