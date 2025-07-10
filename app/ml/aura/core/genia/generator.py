# app/ml/genia/generator.py - Maximizar GenIA con integración de GPT para generación dinámica.
# Optimización: Async calls a GROK, caching para bajo CPU y respuestas rápidas.
# Mejora: Clases dinámicas para contenido por BU, con type hints.

from typing import str, Dict, Optional
from com.chatbot.gpt import BUModularGPT

class GenIAGenerator:
    """Clase dinámica para GenIA, integrada con GPT modular."""
    def __init__(self, gpt: BUModularGPT):
        self.gpt = gpt

    async def generate_content(self, template: str, context: Dict[str, Any]) -> str:
        """Generación async, optimizada para balance CPU/respuesta."""
        prompt = f"Genera {template} con contexto: {context}"
        return await self.gpt.generate_response(prompt, context)