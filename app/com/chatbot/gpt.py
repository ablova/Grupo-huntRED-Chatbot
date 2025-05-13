# /home/pablo/app/com/chatbot/gpt.py
import logging
import backoff
from openai import OpenAI, OpenAIError, RateLimitError
from typing import Optional, Dict, Any, List, Union
from app.models import GptApi, BusinessUnit
from app.com.chatbot.integrations.services import send_email
from django.conf import settings
from asgiref.sync import sync_to_async
import asyncio
import json
import requests
from aiohttp import ClientSession, ClientConnectorSSLError, TCPConnector
import os
import time
from functools import lru_cache
import google.generativeai as genai
from google.generativeai import types

# Importar el sistema de logging avanzado
from app.com.utils.logger_utils import get_module_logger, log_async_function_call, ResourceMonitor

# Suppress TensorFlow warnings and configure CPU-only mode
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"  # Suppress TensorFlow logs (0=All, 3=Errors only)
os.environ["CUDA_VISIBLE_DEVICES"] = ""  # Disable GPU
import tensorflow as tf
tf.config.set_soft_device_placement(True)
tf.config.threading.set_inter_op_parallelism_threads(1)
tf.config.threading.set_intra_op_parallelism_threads(1)

# Configuración del logger con el nuevo sistema
logger = get_module_logger('gpt')

GPT_DEFAULTS = {
    "max_tokens": 150,
    "temperature": 0.2,
    "top_p": 0.9,
    "timeout": 60,
}

# Constantes de configuración
MAX_RETRIES = 3
CIRCUIT_BREAKER_THRESHOLD = 5
CIRCUIT_BREAKER_TIMEOUT = 60  # segundos
PROMPT_CACHE_SIZE = 100
TOKEN_USAGE_ALERT_THRESHOLD = 0.8  # 80% del límite

# Cache para evitar llamadas repetidas a la API
response_cache = {}

# Estado del circuit breaker para cada API
service_circuit_breakers = {}

class BaseHandler:
    def __init__(self, config: GptApi):
        self.config = config
        self.client = None
        self.failures = 0
        self.is_circuit_open = False
        self.circuit_open_time = 0
        self.token_usage = 0
        self.token_limit = getattr(config, 'token_limit', 100000)
        # Inicializar cache
        if config.model not in response_cache:
            response_cache[config.model] = {}
        
        # Log de inicialización
        logger.info(f"Iniciando handler para modelo {config.model}", 
                   extra={"data": {"model": config.model}})

    @log_async_function_call(logger)
    async def initialize(self):
        raise NotImplementedError("Método 'initialize' debe ser implementado.")

    @log_async_function_call(logger)
    async def generate_response(self, prompt: str, business_unit=None) -> str:
        raise NotImplementedError("Método 'generate_response' debe ser implementado.")
        
    def _check_circuit_breaker(self):
        """Verifica si el circuit breaker está abierto"""
        if self.is_circuit_open:
            # Verifica si ha pasado suficiente tiempo para reintentar
            if time.time() - self.circuit_open_time > CIRCUIT_BREAKER_TIMEOUT:
                logger.info(f"Reseteando circuit breaker para {self.config.model}")
                self.is_circuit_open = False
                self.failures = 0
                return False
            return True
        return False
    
    def _increment_failure(self):
        """Incrementa el contador de fallos y abre el circuit breaker si es necesario"""
        self.failures += 1
        if self.failures >= CIRCUIT_BREAKER_THRESHOLD:
            logger.warning(f"Circuit breaker abierto para {self.config.model} después de {self.failures} fallos")
            self.is_circuit_open = True
            self.circuit_open_time = time.time()
    
    def _update_token_usage(self, tokens: int):
        """Actualiza el contador de uso de tokens y alerta si se acerca al límite"""
        self.token_usage += tokens
        usage_percent = self.token_usage / self.token_limit
        if usage_percent >= TOKEN_USAGE_ALERT_THRESHOLD:
            logger.warning(f"Uso de tokens al {usage_percent*100:.1f}% del límite para {self.config.model}")

    async def close(self):
        """Limpia recursos"""
        logger.debug(f"Cerrando handler para {self.config.model}")

class OpenAIHandler(BaseHandler):
    @log_async_function_call(logger)
    async def initialize(self):
        try:
            self.client = OpenAI(api_key=self.config.api_token, organization=self.config.organization)
            logger.info(f"OpenAIHandler configurado con modelo: {self.config.model}")
            # Registrar estado de memoria al inicializar
            ResourceMonitor.log_memory_usage(logger, f"OpenAIHandler-{self.config.model}")
            return True
        except Exception as e:
            logger.error(f"Error inicializando OpenAIHandler: {str(e)}", exc_info=True)
            return False

    @log_async_function_call(logger)
    @backoff.on_exception(backoff.expo, OpenAIError, max_tries=MAX_RETRIES)
    async def generate_response(self, prompt: str, business_unit=None) -> str:
        # Verificar circuit breaker
        if self._check_circuit_breaker():
            logger.warning(f"Circuit breaker abierto para {self.config.model}, evitando llamada")
            return "⚠ Servicio temporalmente no disponible. Intente más tarde."
            
        if not self.client:
            logger.error("Cliente OpenAI no inicializado")
            return "⚠ GPT no inicializado."
            
        # Verificar cache
        cache_key = f"{prompt[:100]}_{business_unit.id if business_unit else 'general'}"
        if cache_key in response_cache[self.config.model]:
            logger.info(f"Respuesta encontrada en caché para {self.config.model}")
            return response_cache[self.config.model][cache_key]
            
        bu_name = business_unit.name if business_unit else "General"
        full_prompt = (
            f"Unidad de Negocio: {bu_name}\n"
            f"{prompt}\n\n"
            "Devuelve únicamente una lista JSON de habilidades (ej: ['Python', 'Django'])."
        )
        
        # Tiempo de inicio para métricas
        start_time = time.time()
        
        try:
            # Log de la solicitud
            logger.info(f"Enviando solicitud a OpenAI ({self.config.model})", 
                       extra={"data": {"prompt_length": len(full_prompt), "business_unit": bu_name}})
                       
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
            
            # Actualizar contadores de tokens
            tokens_used = response.usage.total_tokens
            self._update_token_usage(tokens_used)
            
            # Registrar métricas
            elapsed_time = time.time() - start_time
            logger.info(f"Respuesta OpenAI recibida en {elapsed_time:.2f}s, {tokens_used} tokens", 
                       extra={"data": {"elapsed_time": elapsed_time, "tokens": tokens_used}})
            
            # Guardar en caché
            result = response.choices[0].message.content.strip()
            if len(response_cache[self.config.model]) < PROMPT_CACHE_SIZE:
                response_cache[self.config.model][cache_key] = result
                
            # Resetear contador de fallos
            self.failures = 0
            return result
            
        except RateLimitError as e:
            self._increment_failure()
            logger.warning(f"Cuota de OpenAI excedida: {str(e)}")
            await self._notify_quota_exceeded()
            return "Cuota excedida. Por favor, intente más tarde."
            
        except asyncio.TimeoutError:
            self._increment_failure()
            logger.warning(f"Timeout en OpenAI después de {GPT_DEFAULTS['timeout']}s")
            return "La solicitud tardó demasiado en completarse."
            
        except OpenAIError as e:
            self._increment_failure()
            logger.error(f"Error de OpenAI: {str(e)}", exc_info=True)
            return f"Error al procesar la solicitud: {str(e)}"
            
        except Exception as e:
            self._increment_failure()
            logger.error(f"Error inesperado: {str(e)}", exc_info=True)
            return "Error procesando la solicitud."
            
    async def _notify_quota_exceeded(self):
        """Notifica a los administradores sobre cuota excedida"""
        try:
            admin_email = self.config.notify_email or "admin@huntred.com"
            await send_email(
                business_unit_name="Sistema",
                subject=f"⚠ ALERTA: Cuota de API excedida para {self.config.model}",
                to_email=admin_email,
                body=f"La cuota de la API de {self.config.model} ha sido excedida. "
                     f"Por favor, revise el uso y considere aumentar el límite. "
                     f"Uso actual: {self.token_usage} tokens.",
                from_email="noreply@huntred.com"
            )
            logger.info(f"Notificación de cuota excedida enviada a {admin_email}")
        except Exception as e:
            logger.error(f"Error enviando notificación de cuota excedida: {str(e)}", exc_info=True)

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