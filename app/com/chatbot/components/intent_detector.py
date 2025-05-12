from typing import Optional
from app.models import Person, BusinessUnit, IntentPattern
import logging

logger = logging.getLogger(__name__)

class IntentDetector:
    """
    Detector de intents para el chatbot.
    
    Características:
    - Detección de intents basada en patrones
    - Priorización de intents
    - Manejo de sinónimos y variaciones
    """

    def __init__(self, business_unit: BusinessUnit):
        """
        Inicializa el detector de intents.
        
        Args:
            business_unit (BusinessUnit): Unidad de negocio asociada
        """
        self.business_unit = business_unit
        self._patterns = None

    async def detect_intent(self, message: str) -> Optional[str]:
        """
        Detecta el intent del mensaje.
        
        Args:
            message (str): Mensaje del usuario
            
        Returns:
            Optional[str]: Intent detectado o None si no se encuentra
        """
        try:
            if not self._patterns:
                await self._load_patterns()

            # Procesar el mensaje (limpieza, normalización)
            processed_message = self._process_message(message)

            # Buscar el intent con mayor prioridad que coincida
            for pattern in sorted(self._patterns, key=lambda x: x.priority, reverse=True):
                if pattern.matches(processed_message):
                    return pattern.intent

            # Si no se encuentra ningún intent, usar fallback
            return self._get_fallback_intent(processed_message)

        except Exception as e:
            logger.error(f"Error detecting intent: {str(e)}", exc_info=True)
            return None

    async def _load_patterns(self):
        """Carga los patrones de intents desde la base de datos."""
        self._patterns = await IntentPattern.objects.filter(
            business_unit=self.business_unit,
            is_active=True
        ).aall()

    def _process_message(self, message: str) -> str:
        """Procesa el mensaje para la detección de intents."""
        # Implementar lógica de procesamiento (limpieza, normalización)
        return message.lower().strip()

    def _get_fallback_intent(self, message: str) -> Optional[str]:
        """Obtiene el intent de fallback."""
        # Implementar lógica de fallback
        return "default_intent"
