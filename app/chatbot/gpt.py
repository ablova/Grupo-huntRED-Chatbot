# /home/pablo/app/chatbot/gpt.py

import logging
import backoff
from openai import OpenAI, OpenAIError, RateLimitError
from typing import Optional
from app.models import GptApi, BusinessUnit
from app.chatbot.integrations.services import send_email
from django.conf import settings
from asgiref.sync import sync_to_async
import asyncio
import json
import requests
import google.generativeai as genai

logger = logging.getLogger('chatbot')

GPT_DEFAULTS = {
    "max_tokens": 150,
    "temperature": 0.2,
    "top_p": 0.9,
    "timeout": 60,
}

class BaseHandler:
    def __init__(self, config: GptApi):
        self.config = config
        self.client = None

    async def initialize(self):
        raise NotImplementedError("Método 'initialize' debe ser implementado.")

    async def generate_response(self, prompt: str, business_unit=None) -> str:
        raise NotImplementedError("Método 'generate_response' debe ser implementado.")

class OpenAIHandler(BaseHandler):
    async def initialize(self):
        self.client = OpenAI(api_key=self.config.api_token, organization=self.config.organization)
        logger.info(f"OpenAIHandler configurado con modelo: {self.config.model}")

    @backoff.on_exception(backoff.expo, OpenAIError, max_tries=3)
    async def generate_response(self, prompt: str, business_unit=None) -> str:
        if not self.client:
            return "⚠ GPT no inicializado."
        bu_name = business_unit.name if business_unit else "General"
        full_prompt = (
            f"Unidad de Negocio: {bu_name}\n"
            f"{prompt}\n\n"
            "Devuelve únicamente una lista JSON de habilidades (ej: ['Python', 'Django'])."
        )
        try:
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    self.client.chat.completions.create,
                    model=self.config.model,
                    messages=[
                        {"role": "system", "content": "Eres experto en empleabilidad y reclutamiento."},
                        {"role": "user", "content": full_prompt}
                    ],
                    max_tokens=self.config.max_tokens,
                    temperature=self.config.temperature,
                    top_p=self.config.top_p
                ),
                timeout=GPT_DEFAULTS["timeout"]
            )
            return response.choices[0].message.content.strip()
        except RateLimitError:
            logger.warning("Cuota de OpenAI excedida.")
            self._notify_quota_exceeded()
            return "Cuota excedida."
        except asyncio.TimeoutError:
            logger.warning("Timeout en OpenAI.")
            return "Solicitud tardó demasiado."

class GrokHandler(BaseHandler):
    async def initialize(self):
        self.api_url = "https://api.x.ai/v1/chat/completions"  # Verificar si este es el endpoint correcto
        self.headers = {"Authorization": f"Bearer {self.config.api_token}"}
        self.client = True
        logger.info(f"GrokHandler configurado con modelo: {self.config.model}, Token: {self.config.api_token}")

    async def generate_response(self, prompt: str, business_unit=None) -> str:
        if not self.client:
            return "⚠ GPT no inicializado."
        bu_name = business_unit.name if business_unit else "General"
        full_prompt = (
            f"Unidad de Negocio: {bu_name}\n"
            f"{prompt}\n\n"
            "Devuelve únicamente una lista JSON de habilidades (ej: ['Python', 'Django'])."
        )
        payload = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": self.config.get_prompt("system", "Eres experto en empleabilidad y reclutamiento.")},
                {"role": "user", "content": full_prompt}
            ],
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "top_p": self.config.top_p
        }
        try:
            logger.debug(f"Enviando solicitud a Grok - URL: {self.api_url}, Headers: {self.headers}, Payload: {payload}")
            response = await asyncio.to_thread(
                requests.post, self.api_url, headers=self.headers, json=payload
            )
            response.raise_for_status()
            logger.debug(f"Respuesta de Grok: {response.text}")
            return response.json()["choices"][0]["message"]["content"].strip()
        except requests.exceptions.RequestException as e:
            error_detail = f"Error en Grok: {str(e)}, Status: {getattr(e.response, 'status_code', 'N/A')}, Response: {getattr(e.response, 'text', 'No response')}"
            logger.error(error_detail)
            return f"Error al comunicarse con Grok: {error_detail}"

class GeminiHandler(BaseHandler):
    async def initialize(self):
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.config.model}:generateContent"
        self.headers = {"Authorization": f"Bearer {self.config.api_token}"}
        self.client = True
        logger.info(f"GeminiHandler configurado con modelo: {self.config.model}")

    async def generate_response(self, prompt: str, business_unit=None) -> str:
        if not self.client:
            return "⚠ GPT no inicializado."
        bu_name = business_unit.name if business_unit else "General"
        full_prompt = (
            f"Unidad de Negocio: {bu_name}\n"
            f"{prompt}\n\n"
            "Devuelve únicamente una lista JSON de habilidades (ej: ['Python', 'Django'])."
        )
        payload = {
            "contents": [{"parts": [{"text": full_prompt}]}],
            "generationConfig": {
                "maxOutputTokens": self.config.max_tokens,
                "temperature": self.config.temperature,
                "topP": self.config.top_p
            }
        }
        try:
            response = await asyncio.wait_for(
                asyncio.to_thread(requests.post, self.api_url, headers=self.headers, json=payload),
                timeout=GPT_DEFAULTS["timeout"]
            )
            response.raise_for_status()
            return response.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        except asyncio.TimeoutError:
            logger.warning("Timeout en Gemini.")
            return "Solicitud tardó demasiado."
        except requests.exceptions.RequestException as e:
            logger.error(f"Error en Gemini: {e}")
            return "Error al comunicarse con Gemini."

class LlamaHandler(BaseHandler):
    async def initialize(self):
        self.client = True  # Placeholder, ajustar según la API real
        logger.info(f"LlamaHandler configurado con modelo: {self.config.model}")

    async def generate_response(self, prompt: str, business_unit=None) -> str:
        if not self.client:
            return "⚠ GPT no inicializado."
        return "Respuesta desde Llama (placeholder)"

class ClaudeHandler(BaseHandler):
    async def initialize(self):
        self.api_url = "https://api.anthropic.com/v1/complete"
        self.headers = {"Authorization": f"Bearer {self.config.api_token}"}
        self.client = True
        logger.info(f"ClaudeHandler configurado con modelo: {self.config.model}")

    async def generate_response(self, prompt: str, business_unit=None) -> str:
        if not self.client:
            return "⚠ GPT no inicializado."
        bu_name = business_unit.name if business_unit else "General"
        full_prompt = (
            f"Unidad de Negocio: {bu_name}\n"
            f"{prompt}\n\n"
            "Devuelve únicamente una lista JSON de habilidades (ej: ['Python', 'Django'])."
        )
        payload = {
            "model": self.config.model,
            "prompt": full_prompt,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature
        }
        try:
            response = await asyncio.to_thread(
                requests.post, self.api_url, headers=self.headers, json=payload
            )
            response.raise_for_status()
            return response.json()["completion"].strip()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error en Claude: {e}")
            return "Error al comunicarse con Claude."
       
class VertexAIHandler(BaseHandler):
    async def initialize(self):
        self.client = genai.Client(
            vertexai=True,
            project="grupo-huntred",
            location="us-central1",
        )
        self.model = self.config.model or "gemini-2.0-flash-001"
        logger.info(f"VertexAIHandler configurado con modelo: {self.model}")

    async def generate_response(self, prompt: str, business_unit=None) -> str:
        if not self.client:
            return "⚠ Vertex AI no inicializado."
        bu_name = business_unit.name if business_unit else "General"
        full_prompt = f"Unidad de Negocio: {bu_name}\n{prompt}"
        document = types.Part.from_text(text=full_prompt)
        contents = [types.Content(role="user", parts=[document])]
        config = types.GenerateContentConfig(
            temperature=self.config.temperature,
            top_p=self.config.top_p,
            max_output_tokens=self.config.max_tokens,
            response_mime_type="application/json",
        )
        try:
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=self.model,
                contents=contents,
                config=config,
            )
            return response.text.strip()
        except Exception as e:
            logger.error(f"Error en Vertex AI: {e}")
            return "Error al comunicarse con Vertex AI."

class GPTHandler:
    def __init__(self):
        logger.debug("Instancia GPTHandler creada.")
        self.handler = None
        self.config = GPT_DEFAULTS.copy()
        self.current_business_unit = None

    async def initialize(self):
        try:
            gpt_api = await sync_to_async(lambda: GptApi.objects.filter(is_active=True).select_related('provider').first())()
            if gpt_api:
                self.handler = await get_handler(gpt_api)
                await self.handler.initialize()
                self.config.update({
                    "model": gpt_api.model,
                    "max_tokens": gpt_api.max_tokens or GPT_DEFAULTS["max_tokens"],
                    "temperature": gpt_api.temperature or GPT_DEFAULTS["temperature"],
                    "top_p": gpt_api.top_p or GPT_DEFAULTS["top_p"],
                })
                logger.info(f"GPTHandler configurado con modelo: {self.config['model']}")
            else:
                logger.error("Sin configuración de GPT API en BD.")
                raise ValueError("Configuración GPT no encontrada.")
        except Exception as e:
            logger.exception(f"Error inicializando GPTHandler: {e}")
            raise e

    async def generate_response(self, prompt: str, business_unit: Optional[BusinessUnit] = None) -> str:
        self.current_business_unit = business_unit
        
        if not self.handler:
            return "⚠ GPT no inicializado."
        return await self.handler.generate_response(prompt, business_unit)

    def _notify_quota_exceeded(self):
        if self.current_business_unit and hasattr(self.current_business_unit, 'admin_email') and self.current_business_unit.admin_email:
            remitente = self.current_business_unit.name
            emails = [self.current_business_unit.admin_email]
        else:
            remitente = "Grupo huntRED®"
            emails = ["hola@huntRED.com", "finanzas@huntRED.com"]
        subject = "Cuota de API agotada"
        body = (
            f"Hola,\n\nLa cuota de la API para '{remitente}' se ha agotado. "
            f"Por favor revisa tu cuenta.\n\nSaludos."
        )
        for email in emails:
            try:
                send_email(
                    subject=subject,
                    to_email=email,
                    body=body,
                    business_unit_name=remitente,
                    from_email=f"no-reply@{remitente.lower().replace(' ', '')}.com"
                )
                logger.info(f"Notificación cuota enviada a {email} desde {remitente}.")
            except Exception as e:
                logger.error(f"Error enviando correo a {email}: {e}")

    def generate_response_sync(self, prompt: str, business_unit=None) -> str:
        try:
            return asyncio.run(self.generate_response(prompt, business_unit))
        except Exception as e:
            logger.error(f"Error generando respuesta síncrona GPT: {e}")
            return "Error inesperado en la solicitud."
         
# Actualizar HANDLER_MAPPING
HANDLER_MAPPING = {
    'openai': OpenAIHandler,
    'grok': GrokHandler,
    'google(gemini)': GeminiHandler,
    'vertexai': VertexAIHandler,  # Nuevo handler para Vertex AI
    'meta(llama)': LlamaHandler,
    'anthropic(claude)': ClaudeHandler,
}
async def get_handler(config: GptApi) -> BaseHandler:
    provider = await sync_to_async(lambda: config.provider)()
    provider_key = provider.name.lower().replace(' ', '').replace('(xai)', '')
    handler_class = HANDLER_MAPPING.get(provider_key)
    if handler_class:
        return handler_class(config)
    raise ValueError(f"Proveedor no soportado: {provider_key}")        

async def test_provider(self, provider_name: str, prompt: str = "Test prompt") -> str:
        """Prueba un proveedor específico."""
        gpt_api = await sync_to_async(lambda: GptApi.objects.filter(provider__name__iexact=provider_name).first())()
        if not gpt_api:
            return f"Proveedor {provider_name} no encontrado."
        temp_handler = await get_handler(gpt_api)
        await temp_handler.initialize()
        return await temp_handler.generate_response(prompt)