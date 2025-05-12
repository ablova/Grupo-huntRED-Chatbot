# /home/pablo/app/com/chatbot/gpt.py
import logging
import backoff
from openai import OpenAI, OpenAIError, RateLimitError
from typing import Optional
from app.models import GptApi, BusinessUnit
from app.com.chatbot.integrations.services import send_email
from django.conf import settings
from asgiref.sync import sync_to_async
import asyncio
import json
import requests
from aiohttp import ClientSession, ClientConnectorSSLError  # For efficient HTTP requests
import os
import google.generativeai as genai
from google.generativeai import types

# Suppress TensorFlow warnings and configure CPU-only mode
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"  # Suppress TensorFlow logs (0=All, 3=Errors only)
os.environ["CUDA_VISIBLE_DEVICES"] = ""  # Disable GPU
import tensorflow as tf
tf.config.set_soft_device_placement(True)
tf.config.threading.set_inter_op_parallelism_threads(1)
tf.config.threading.set_intra_op_parallelism_threads(1)

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

    async def close(self):
        pass  # Optional cleanup method for handlers

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
        # Use aiohttp for connection pooling and SSL error handling
        self.api_url = "https://api.x.ai/v1/chat/completions"
        self.headers = {"Authorization": f"Bearer {self.config.api_token}"}
        self.client = ClientSession()
        logger.info(f"GrokHandler configurado con modelo: {self.config.model}")

    @backoff.on_exception(
        backoff.expo,
        (ClientConnectorSSLError, asyncio.TimeoutError, requests.exceptions.RequestException),
        max_tries=3
    )
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
            logger.debug(f"Enviando solicitud a Grok - URL: {self.api_url}, Payload: {payload}")
            async with self.client.post(self.api_url, headers=self.headers, json=payload) as response:
                response.raise_for_status()
                data = await response.json()
                logger.debug(f"Respuesta de Grok: {data}")
                return data["choices"][0]["message"]["content"].strip()
        except (ClientConnectorSSLError, requests.exceptions.RequestException) as e:
            error_detail = f"Error en Grok: {str(e)}, Status: {getattr(e.response, 'status_code', 'N/A')}"
            logger.error(error_detail)
            return f"Error al comunicarse con Grok: {error_detail}"
        except asyncio.TimeoutError:
            logger.warning("Timeout en Grok.")
            return "Solicitud tardó demasiado."
        except Exception as e:
            logger.error(f"Error inesperado en Grok: {e}")
            return f"Error inesperado: {e}"

    async def close(self):
        if self.client:
            await self.client.close()

class GeminiHandler(BaseHandler):
    async def initialize(self):
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.config.model}:generateContent"
        self.headers = {"Authorization": f"Bearer {self.config.api_token}"}
        self.client = ClientSession()
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
            async with self.client.post(self.api_url, headers=self.headers, json=payload) as response:
                response.raise_for_status()
                data = await response.json()
                return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except asyncio.TimeoutError:
            logger.warning("Timeout en Gemini.")
            return "Solicitud tardó demasiado."
        except requests.exceptions.RequestException as e:
            logger.error(f"Error en Gemini: {e}")
            return "Error al comunicarse con Gemini."

    async def close(self):
        if self.client:
            await self.client.close()

class LlamaHandler(BaseHandler):
    async def initialize(self):
        self.client = True  # Placeholder
        logger.info(f"LlamaHandler configurado con modelo: {self.config.model}")

    async def generate_response(self, prompt: str, business_unit=None) -> str:
        if not self.client:
            return "⚠ GPT no inicializado."
        return "Respuesta desde Llama (placeholder)"

class ClaudeHandler(BaseHandler):
    async def initialize(self):
        self.api_url = "https://api.anthropic.com/v1/complete"
        self.headers = {"Authorization": f"Bearer {self.config.api_token}"}
        self.client = ClientSession()
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
            async with self.client.post(self.api_url, headers=self.headers, json=payload) as response:
                response.raise_for_status()
                data = await response.json()
                return data["completion"].strip()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error en Claude: {e}")
            return "Error al comunicarse con Claude."

    async def close(self):
        if self.client:
            await self.client.close()

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
        self._handler_cache = {}  # Cache for handler instances

    async def initialize(self):
        try:
            # Try active providers first
            gpt_api = await sync_to_async(lambda: GptApi.objects.filter(is_active=True, provider__name__iexact='Xai (Grok)').select_related('provider').first())()
            if not gpt_api:
                logger.info("No se encontró configuración activa para Grok, intentando con OpenAI.")
                gpt_api = await sync_to_async(lambda: GptApi.objects.filter(is_active=True, provider__name__iexact='OpenAI (ChatGPT)').select_related('provider').first())()
            if not gpt_api:
                logger.info("No se encontró configuración activa, intentando proveedores inactivos.")
                gpt_api = await sync_to_async(lambda: GptApi.objects.filter(provider__name__iexact='OpenAI (ChatGPT)').select_related('provider').first())()
                if not gpt_api:
                    gpt_api = await sync_to_async(lambda: GptApi.objects.filter(provider__name__iexact='Xai (Grok)').select_related('provider').first())()
            if gpt_api:
                provider_key = (await sync_to_async(lambda: gpt_api.provider.name)())
                # Check cache for existing handler
                if provider_key in self._handler_cache:
                    self.handler = self._handler_cache[provider_key]
                else:
                    self.handler = await get_handler(gpt_api)
                    self._handler_cache[provider_key] = self.handler
                await self.handler.initialize()
                self.config.update({
                    "model": gpt_api.model,
                    "max_tokens": gpt_api.max_tokens or GPT_DEFAULTS["max_tokens"],
                    "temperature": gpt_api.temperature or GPT_DEFAULTS["temperature"],
                    "top_p": gpt_api.top_p or GPT_DEFAULTS["top_p"],
                })
                logger.info(f"GPTHandler configurado con modelo: {self.config['model']}, proveedor: {provider_key}")
            else:
                logger.error("Sin configuración de GPT API en BD para Grok o OpenAI.")
                raise ValueError("Configuración GPT no encontrada.")
        except Exception as e:
            logger.exception(f"Error inicializando GPTHandler: {e}")
            raise

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

    async def close(self):
        if self.handler:
            await self.handler.close()
            self.handler = None
            self._handler_cache.clear()

# Updated HANDLER_MAPPING to support xai(grok) and xai (grok)
HANDLER_MAPPING = {
    'openai': OpenAIHandler,
    'OpenAI (ChatGPT)': OpenAIHandler,
    'xai(grok)': GrokHandler,
    'xai (grok)': GrokHandler,
    'Xai (Grok)': GrokHandler,
    'google(gemini)': GeminiHandler,
    'Google (Gemini)': GeminiHandler,
    'vertexai': VertexAIHandler,
    'Vertex API': VertexAIHandler,
    'meta(llama)': LlamaHandler,
    'anthropic(claude)': ClaudeHandler,
    'Anthropic (Claude)': ClaudeHandler,
}

async def get_handler(config: GptApi) -> BaseHandler:
    provider = await sync_to_async(lambda: config.provider)()
    provider_key = provider.name  # Keep original case for exact match
    logger.debug(f"Buscando handler para proveedor: {provider_key}")
    handler_class = HANDLER_MAPPING.get(provider_key)
    if handler_class:
        return handler_class(config)
    raise ValueError(f"Proveedor no soportado: {provider_key}")

async def test_provider(provider_name: str, prompt: str = "Test prompt") -> str:
    """Prueba un proveedor específico."""
    gpt_api = await sync_to_async(lambda: GptApi.objects.filter(provider__name__iexact=provider_name).first())()
    if not gpt_api:
        return f"Proveedor {provider_name} no encontrado."
    temp_handler = await get_handler(gpt_api)
    await temp_handler.initialize()
    try:
        return await temp_handler.generate_response(prompt)
    finally:
        await temp_handler.close()  # Correctly await the async method