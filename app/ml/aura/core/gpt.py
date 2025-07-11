# app/ml/aura/core/gpt.py
"""
Módulo GPT para integración con modelos de lenguaje.
Proporciona clases y funciones para interactuar con modelos GPT.
"""

import logging
from typing import Dict, List, Any, Optional, Union
from app.models import BusinessUnit, GptApi

logger = logging.getLogger(__name__)

class BaseModularGPT:
    """Clase base para interacción con modelos GPT."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.model = "gpt-3.5-turbo"
        self.temperature = 0.7
        self.max_tokens = 1000
        self.initialized = False
        
    def initialize(self) -> bool:
        """Inicializa el cliente GPT."""
        try:
            if not self.api_key:
                logger.warning("No se proporcionó API key para GPT")
                return False
            self.initialized = True
            return True
        except Exception as e:
            logger.error(f"Error al inicializar GPT: {e}")
            return False
    
    def generate(self, prompt: str, **kwargs) -> Optional[str]:
        """Genera texto a partir de un prompt."""
        if not self.initialized:
            logger.warning("GPT no inicializado. Llamar a initialize() primero.")
            return None
        
        try:
            # Implementación básica - en producción usar cliente real
            logger.info(f"Generando respuesta para prompt: {prompt[:50]}...")
            return f"Respuesta simulada para: {prompt[:20]}..."
        except Exception as e:
            logger.error(f"Error en generación GPT: {e}")
            return None


class BUModularGPT(BaseModularGPT):
    """GPT específico para una Business Unit."""
    
    def __init__(self, business_unit: BusinessUnit):
        super().__init__()
        self.business_unit = business_unit
        self.config = None
        
    def initialize(self) -> bool:
        """Inicializa con configuración de la BU."""
        try:
            # Intentar obtener configuración de GPT de la BU
            gpt_config = GptApi.objects.filter(business_unit=self.business_unit).first()
            if gpt_config and gpt_config.api_key:
                self.api_key = gpt_config.api_key
                self.model = gpt_config.model or self.model
                self.config = gpt_config
                return super().initialize()
            else:
                logger.warning(f"No se encontró configuración GPT para BU: {self.business_unit.name}")
                return False
        except Exception as e:
            logger.error(f"Error al inicializar BU GPT: {e}")
            return False
    
    def generate_with_context(self, prompt: str, context: Dict[str, Any], **kwargs) -> Optional[str]:
        """Genera texto con contexto específico de la BU."""
        if not self.initialized:
            if not self.initialize():
                return None
        
        # Enriquecer el prompt con contexto de la BU
        enriched_prompt = f"[BU: {self.business_unit.name}]\n{prompt}"
        
        # Añadir contexto si está disponible
        if context:
            context_str = "\n".join([f"{k}: {v}" for k, v in context.items()])
            enriched_prompt = f"{enriched_prompt}\n\nContexto:\n{context_str}"
        
        return self.generate(enriched_prompt, **kwargs)
