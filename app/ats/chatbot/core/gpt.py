# app/com/chatbot/gpt.py - Extensión para integrar GROK como default en GenIA y AURA, con async para bajo CPU y respuestas rápidas.
# Optimización: Uso de aiohttp para llamadas API no bloqueantes, balanceando CPU (bajo overhead) y tiempo (respuestas <1s).
# Mejora: Diseño dinámico vía clases, permitiendo herencia por BU sin alterar funcionalidades existentes.
# Manteniendo nombres existentes como 'generate_response' para compatibilidad.
"""
Manejador de GPT para Grupo huntRED®.
Proporciona una interfaz unificada para diferentes proveedores de IA.
"""

# Importaciones estándar de Python
import logging
import json
import os
import time
import asyncio
import aiohttp  # Tecnología de última generación para async HTTP, eficiente en CPU.
from contextlib import asynccontextmanager  # Context managers para manejo de sesiones seguras y liberadas.
from functools import lru_cache  # Caching para optimizar CPU en prompts repetidos, sin aumentar latencia inicial.
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Dict, Any, List, Union  # Type hints para mejores prácticas y detección de errores.

# Importaciones de Django
from django.conf import settings
from django.core.cache import cache
from asgiref.sync import sync_to_async

# Importaciones de terceros
import backoff
import requests
from openai import OpenAI, OpenAIError, RateLimitError
from aiohttp import ClientSession, ClientConnectorSSLError, TCPConnector
import google.generativeai as genai
from google.generativeai import types

# Importaciones de modelos
from app.models import GptApi, BusinessUnit

# Importaciones de servicios
from app.ats.integrations.services import EmailService

# Importaciones de utilidades
from app.ats.utils.logger_utils import get_module_logger, log_async_function_call, ResourceMonitor

# Configuración de TensorFlow (opcional)
try:
    os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"  # Suprimir logs de TensorFlow (0=Todos, 3=Solo errores)
    os.environ["CUDA_VISIBLE_DEVICES"] = ""  # Deshabilitar GPU
    import tensorflow as tf
    tf.config.set_soft_device_placement(True)
    tf.config.threading.set_inter_op_parallelism_threads(1)
    tf.config.threading.set_intra_op_parallelism_threads(1)
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    logger = get_module_logger('gpt')
    logger.warning("TensorFlow no está disponible. Algunas funcionalidades pueden estar limitadas.")

# Configuración del logger
if not 'logger' in locals():
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

# Cache mediante el sistema de caché de Django (en lugar de memoria local)
# Funciones para gestionar cache de respuestas
def get_cached_response(model, prompt, business_unit=None):
    """Obtiene respuesta cacheada con soporte para BU"""
    bu_id = getattr(business_unit, 'id', None) or getattr(business_unit, 'name', '')
    cache_key = f"gpt:{model}:{bu_id}:{hash(prompt[:200])}"
    return cache.get(cache_key)

def cache_response(model, prompt, response, business_unit=None, ttl=3600):
    """Almacena respuesta en caché con TTL y soporte para BU"""
    bu_id = getattr(business_unit, 'id', None) or getattr(business_unit, 'name', '')
    cache_key = f"gpt:{model}:{bu_id}:{hash(prompt[:200])}"
    cache.set(cache_key, response, ttl)
    
# Caché en memoria TTL para respuestas frecuentes (más rápida que Django cache)
PROMPT_CACHE_SIZE = 1000
try:
    from cachetools import TTLCache
    TTLCACHE_AVAILABLE = True
except ImportError:
    TTLCACHE_AVAILABLE = False

if TTLCACHE_AVAILABLE:
    # TTLCache es más eficiente para respuestas frecuentes (1 hora de TTL)
    memory_cache = TTLCache(maxsize=PROMPT_CACHE_SIZE, ttl=3600)
else:
    # Fallback a diccionario simple si TTLCache no está disponible
    memory_cache = {}
    
# ThreadPool para operaciones bloqueantes
thread_pool = ThreadPoolExecutor(max_workers=5)

# Estado del circuit breaker para cada API (se mantiene en memoria para velocidad)
service_circuit_breakers = {}

# Constantes de configuración del circuit breaker
CIRCUIT_BREAKER_THRESHOLD = 5  # Número de fallos consecutivos para abrir el circuito
CIRCUIT_BREAKER_TIMEOUT = 60    # Segundos que el circuito permanece abierto
MAX_CONCURRENT_REQUESTS = 5     # Máximo de solicitudes simultáneas

# HTTP Session compartida para mejorar rendimiento de conexiones
_http_session = None

async def get_http_session():
    """Obtiene una sesión HTTP compartida para todas las peticiones"""
    global _http_session
    if _http_session is None or _http_session.closed:
        _http_session = ClientSession(
            connector=TCPConnector(
                ssl=False,
                limit=MAX_CONCURRENT_REQUESTS,  # Máximo de conexiones simultáneas
                keepalive_timeout=30
            )
        )
    return _http_session


class PromptManager:
    """Manejador de prompts con cache y optimización para cada BU."""
    
    def __init__(self, business_unit=None):
        self.business_unit = business_unit
        self.templates = self._load_templates()
        
    def _load_templates(self) -> Dict:
        """Cargar templates de prompts específicos por BU."""
        templates = {
            'huntred': {
                'job_analysis': """Analiza la posición laboral y genera una descripción detallada.
                Contexto: {context}
                Requisitos: {requirements}
                Salario: {salary}
                Responde en formato JSON con: nombre, descripción, requisitos, salario, beneficios.""",
                'candidate_evaluation': """Evalúa al candidato basado en su perfil y la posición.
                Candidato: {candidate_profile}
                Posición: {job_description}
                Responde con una evaluación detallada en formato JSON."""
            },
            'amigro': {
                'migration_assistance': """Proporciona asistencia para migrantes.
                Documentos: {documents}
                Proceso: {process}
                Responde con pasos detallados en formato JSON.""",
                'job_search': """Busca oportunidades laborales para migrantes.
                Perfil: {profile}
                Ubicación: {location}
                Responde con lista de trabajos en formato JSON."""
            },
            'huntrex': {
                'executive_search': """Busca candidatos ejecutivos según los criterios.
                Posición: {position}
                Empresa: {company}
                Requisitos: {requirements}
                Responde con estrategia de búsqueda en formato JSON."""
            }
        }
        
        # Intentar cargar templates desde la base de datos si está disponible
        try:
            from app.models import ConfiguracionBU
            if self.business_unit:
                config = ConfiguracionBU.objects.filter(business_unit=self.business_unit).first()
                if config and hasattr(config, 'config'):
                    config_data = json.loads(config.config)
                    if 'prompt_templates' in config_data:
                        # Fusionar con los templates existentes
                        bu_name = self.business_unit.name.lower()
                        if bu_name not in templates:
                            templates[bu_name] = {}
                        templates[bu_name].update(config_data['prompt_templates'])
        except Exception as e:
            logger.warning(f"No se pudieron cargar templates desde la BD: {e}")
            
        return templates
    
    def get_template(self, template_name, bu_name=None):
        """Obtiene un template por nombre y BU."""
        if not bu_name and self.business_unit:
            bu_name = self.business_unit.name.lower()
            
        bu_name = bu_name.lower() if bu_name else 'huntred'  # Default
        
        if bu_name in self.templates and template_name in self.templates[bu_name]:
            return self.templates[bu_name][template_name]
        else:
            # Buscar en templates genéricos
            return self.templates.get('huntred', {}).get(
                template_name, 
                "Por favor responde a la siguiente consulta: {prompt}"
            )
    
    def format_prompt(self, template_name, **kwargs):
        """Formatea un template con los datos proporcionados."""
        template = self.get_template(template_name)
        try:
            return template.format(**kwargs)
        except KeyError as e:
            logger.warning(f"Falta parámetro {e} para template {template_name}")
            # Devolver template con datos parciales o mensaje de error
            return f"Error en template {template_name}: {e}"

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
        """Generate a response from the OpenAI API."""
        # Verificar circuit breaker
        if self._check_circuit_breaker():
            return "⚠️ Servicio temporalmente no disponible. Intente más tarde."
        
        # Verificar caché con sistema de caché de Django
        model = self.config.model
        cached_response = get_cached_response(model, prompt, business_unit)
        if cached_response:
            logger.info(f"Respuesta obtenida de caché para modelo {model} y BU {getattr(business_unit, 'name', '...')}")
            return cached_response
        
        # Implementación específica del handler
        raise NotImplementedError("Método 'generate_response' debe ser implementado.")
        
    def _check_circuit_breaker(self):
        """Verifica si el circuit breaker está abierto para esta API."""
        if not self.circuit_breaker_key:
            return False
            
        breaker = service_circuit_breakers.get(self.circuit_breaker_key, {})
        # Verificar si el circuito está abierto
        if breaker.get('is_open', False):
            open_time = breaker.get('open_time', 0)
            # Si han pasado más de CIRCUIT_BREAKER_TIMEOUT segundos, intentar cerrar el circuit breaker
            if time.time() - open_time > CIRCUIT_BREAKER_TIMEOUT:
                service_circuit_breakers[self.circuit_breaker_key]['is_open'] = False
                service_circuit_breakers[self.circuit_breaker_key]['failures'] = 0
                logger.info(f"Circuit breaker cerrado para {self.circuit_breaker_key} después de {CIRCUIT_BREAKER_TIMEOUT}s")
                return False
            # El circuito sigue abierto
            logger.warning(f"Circuit breaker abierto para {self.circuit_breaker_key}, evitando llamada")
            return True
        return False
        
    def _increment_failure(self):
        """Incrementa el contador de fallos y abre el circuit breaker si es necesario."""
        if not self.circuit_breaker_key:
            return
            
        if self.circuit_breaker_key not in service_circuit_breakers:
            service_circuit_breakers[self.circuit_breaker_key] = {'failures': 0, 'is_open': False}
            
        service_circuit_breakers[self.circuit_breaker_key]['failures'] += 1
        failures = service_circuit_breakers[self.circuit_breaker_key]['failures']
        
        # Si supera el umbral, abrir el circuit breaker
        if failures >= CIRCUIT_BREAKER_THRESHOLD:
            service_circuit_breakers[self.circuit_breaker_key]['is_open'] = True
            service_circuit_breakers[self.circuit_breaker_key]['open_time'] = time.time()
            logger.warning(f"Circuit breaker abierto para {self.circuit_breaker_key} por {failures} fallos")
            
    def _reset_failures(self):
        """Resetea el contador de fallos tras una llamada exitosa."""
        if not self.circuit_breaker_key:
            return
            
        if self.circuit_breaker_key in service_circuit_breakers:
            service_circuit_breakers[self.circuit_breaker_key]['failures'] = 0
    
    def _update_token_usage(self, tokens: int, business_unit=None):
        """Actualiza contador de tokens por BU y total"""
        self.token_usage += tokens
        
        # Contador global del modelo
        usage_percent = self.token_usage / self.token_limit
        if usage_percent >= TOKEN_USAGE_ALERT_THRESHOLD:
            logger.warning(f"Uso de tokens al {usage_percent*100:.1f}% del límite para {self.config.model}")
        
        # Contador específico por BU
        if business_unit:
            bu_id = getattr(business_unit, 'id', None) or getattr(business_unit, 'name', '')
            if bu_id:
                bu_key = f"token_usage:{self.config.model}:{bu_id}"
                current_usage = cache.get(bu_key) or 0
                new_usage = current_usage + tokens
                
                # Obtener límite por BU (configuración o default)
                bu_limit = self.token_limit  # Default
                try:
                    from app.models import ConfiguracionBU
                    config = ConfiguracionBU.objects.filter(business_unit=business_unit).first()
                    if config and hasattr(config, 'config'):
                        bu_config = json.loads(config.config)
                        bu_limit = bu_config.get('token_limit', self.token_limit)
                except Exception:
                    pass
                    
                cache.set(bu_key, new_usage, 86400)  # 24 horas
                
                # Alertar si está cerca del límite
                bu_usage_percent = new_usage / bu_limit
                if bu_usage_percent >= TOKEN_USAGE_ALERT_THRESHOLD:
                    logger.warning(f"BU {bu_id}: Uso de tokens al {bu_usage_percent*100:.1f}%")

    async def close(self):
        """Limpia recursos"""
        logger.debug(f"Cerrando handler para {self.config.model}")

class OpenAIHandler(BaseHandler):
    @log_async_function_call(logger)
    async def initialize(self):
        """Inicializa el cliente con configuración optimizada."""
        try:
            # Establecer API key de la configuración
            self.api_key = self.config.api_key
            self.organization = getattr(self.config, 'organization', None)
            
            # Obtener timeout adaptativo según carga del sistema
            timeout = self.config.timeout or GPT_DEFAULTS["timeout"]
            
            # Verificar carga del sistema para timeout adaptativo
            try:
                import psutil
                cpu_load = psutil.cpu_percent(interval=None) / 100.0
                if cpu_load > 0.8:  # Más del 80% de CPU
                    timeout *= 1.5  # Aumentar 50%
                    logger.info(f"Timeout aumentado por alta carga de CPU ({cpu_load:.1%})")
            except ImportError:
                pass
                
            # Crear cliente con configuración optimizada
            self.client = OpenAI(
                api_key=self.api_key,
                organization=self.organization,
                max_retries=MAX_RETRIES,
                timeout=timeout
            )
            logger.info(f"Cliente OpenAI inicializado para {self.config.model} con timeout {timeout}s")
        except Exception as e:
            logger.error(f"Error inicializando OpenAI: {str(e)}")
            self._increment_failure()
            self.client = None

    @log_async_function_call(logger)
    @backoff.on_exception(backoff.expo, OpenAIError, max_tries=MAX_RETRIES)
    async def generate_response(self, prompt: str, business_unit=None) -> str:
        # Verificar circuit breaker
        if self._check_circuit_breaker():
            return "⚠️ Servicio temporalmente no disponible. Intente más tarde."
        
        # Verificar caché con sistema de caché de Django
        model = self.config.model
        cached_response = get_cached_response(model, prompt, business_unit)
        if cached_response:
            logger.info(f"Respuesta obtenida de caché para modelo {model} y BU {getattr(business_unit, 'name', '...')}")
            return cached_response
        
        # Implementación específica del handler
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
            
            # Actualizar contador de tokens
            completion_tokens = response.usage.completion_tokens
            prompt_tokens = response.usage.prompt_tokens
            total_tokens = completion_tokens + prompt_tokens
            self._update_token_usage(total_tokens, business_unit)
            
            # Guardar en caché Django (persistente y compartida)
            response_text = response.choices[0].message.content.strip()
            cache_response(model, prompt, response_text, business_unit)
            
            # Log de finalización con identificador de BU
            bu_name = getattr(business_unit, 'name', 'ninguna') if business_unit else 'ninguna'
            logger.debug(f"Respuesta generada para BU '{bu_name}': {len(response_text)} caracteres")
            return response_text
            
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
            await EmailService.send_email(
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

class MistralAIHandler(BaseHandler):
    """Manejador para la API de Mistral AI."""
    
    async def initialize(self):
        """Inicializa el cliente de Mistral AI."""
        try:
            self.client = None
            self.api_key = self.config.api_key
            self.model = self.config.model
            self.base_url = "https://api.mistral.ai/v1"
            
            # Configurar headers comunes
            self.headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Verificar disponibilidad del modelo
            async with await get_http_session() as session:
                async with session.get(
                    f"{self.base_url}/models",
                    headers=self.headers
                ) as response:
                    if response.status == 200:
                        models = await response.json()
                        available_models = [m["id"] for m in models.get("data", [])]
                        if self.model not in available_models:
                            logger.warning(f"Modelo {self.model} no disponible. Modelos disponibles: {available_models}")
                            # Usar el modelo más potente disponible
                            self.model = next((m for m in available_models if "large" in m.lower()), available_models[0])
                    else:
                        logger.error(f"Error verificando modelos de Mistral AI: {response.status}")
            
            logger.info(f"MistralAIHandler inicializado con modelo {self.model}")
            self._reset_failures()
            
        except Exception as e:
            logger.error(f"Error inicializando MistralAIHandler: {str(e)}")
            self._increment_failure()
            raise

    @log_async_function_call(logger)
    @backoff.on_exception(
        backoff.expo,
        (ClientConnectorSSLError, asyncio.TimeoutError, requests.exceptions.RequestException),
        max_tries=MAX_RETRIES
    )
    async def generate_response(self, prompt: str, business_unit=None) -> str:
        """Genera una respuesta usando la API de Mistral AI."""
        if self._check_circuit_breaker():
            raise Exception("Circuit breaker abierto para Mistral AI")
            
        try:
            # Verificar caché
            cached_response = get_cached_response(self.model, prompt, business_unit)
            if cached_response:
                logger.info("Respuesta obtenida de caché")
                return cached_response
                
            # Preparar payload
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": self.config.max_tokens,
                "temperature": self.config.temperature,
                "top_p": self.config.top_p,
                "frequency_penalty": self.config.frequency_penalty,
                "presence_penalty": self.config.presence_penalty
            }
            
            if self.config.stop_sequences:
                payload["stop"] = self.config.stop_sequences
                
            # Realizar petición
            async with await get_http_session() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload,
                    timeout=self.config.timeout
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        response_text = result["choices"][0]["message"]["content"]
                        
                        # Actualizar métricas
                        tokens_used = result.get("usage", {}).get("total_tokens", 0)
                        self._update_token_usage(tokens_used, business_unit)
                        
                        # Guardar en caché
                        cache_response(self.model, prompt, response_text, business_unit)
                        
                        self._reset_failures()
                        return response_text
                    else:
                        error_text = await response.text()
                        logger.error(f"Error en Mistral AI: {response.status} - {error_text}")
                        self._increment_failure()
                        raise Exception(f"Error en Mistral AI: {response.status}")
                        
        except Exception as e:
            logger.error(f"Error generando respuesta con Mistral AI: {str(e)}")
            self._increment_failure()
            raise

    async def close(self):
        """Cierra la conexión con Mistral AI."""
        # No es necesario cerrar nada ya que usamos aiohttp
        pass

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
            gpt_api = await sync_to_async(lambda: GptApi.objects.filter(is_active=True, provider__name__iexact='Mistral AI').select_related('provider').first())()
            if not gpt_api:
                logger.info("No se encontró configuración activa para Mistral AI, intentando con Grok.")
                gpt_api = await sync_to_async(lambda: GptApi.objects.filter(is_active=True, provider__name__iexact='Xai (Grok)').select_related('provider').first())()
            if not gpt_api:
                logger.info("No se encontró configuración activa para Grok, intentando con OpenAI.")
                gpt_api = await sync_to_async(lambda: GptApi.objects.filter(is_active=True, provider__name__iexact='OpenAI (ChatGPT)').select_related('provider').first())()
            if not gpt_api:
                logger.info("No se encontró configuración activa, intentando proveedores inactivos.")
                gpt_api = await sync_to_async(lambda: GptApi.objects.filter(provider__name__iexact='Mistral AI').select_related('provider').first())()
                if not gpt_api:
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
                logger.error("Sin configuración de GPT API en BD para Mistral AI, Grok o OpenAI.")
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
                EmailService.send_email(
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
class MetaAIHandler(BaseHandler):
    """Handler para Meta AI (Llama 3) y otros modelos de Meta.
    Optimizado para Meta Conversations 2025."""
    
    async def initialize(self):
        """Inicializa el cliente con configuración optimizada para Meta AI."""
        try:
            import httpx
            self.client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.config.timeout or GPT_DEFAULTS["timeout"]),
                limits=httpx.Limits(
                    max_keepalive_connections=10,
                    max_connections=20,
                    keepalive_expiry=30
                ),
                http2=True
            )
            self.api_key = self.config.api_key
            self.api_base = self.config.endpoint or "https://api.meta.ai/v1"
            self.model = self.config.model or "meta-llama-3-70b-instruct"
            self.initialized = True
            logger.info(f"MetaAIHandler inicializado con modelo {self.model}")
        except Exception as e:
            logger.error(f"Error inicializando MetaAIHandler: {str(e)}")
            self._increment_failure()
            raise
            
    async def generate_response(self, prompt: str, business_unit=None, channel_api=None):
        """Genera una respuesta utilizando Meta AI (Llama 3)."""
        if not self.initialized:
            await self.initialize()
            
        # Verificar circuit breaker
        if self._check_circuit_breaker():
            logger.warning("Circuit breaker abierto para Meta AI")
            return "⚠️ Servicio no disponible temporalmente. Intente más tarde."
            
        # Verificar caché
        cached = get_cached_response(self.model, prompt, business_unit)
        if cached:
            logger.debug("Respuesta recuperada de caché para Meta AI")
            return cached
            
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": self.config.max_tokens or GPT_DEFAULTS["max_tokens"],
                "temperature": self.config.temperature or GPT_DEFAULTS["temperature"],
                "top_p": self.config.top_p or GPT_DEFAULTS["top_p"]
            }
            # Buscar verificación Meta en el canal correspondiente
            if channel_api and hasattr(channel_api, 'meta_verified') and channel_api.meta_verified:
                payload["meta_verified"] = True
                if getattr(channel_api, 'meta_verified_badge_url', None):
                    payload["badge_url"] = channel_api.meta_verified_badge_url
            # Hooks para futuras capacidades (voz, foto, video)
            # if hasattr(self, 'voice_config'):
            #     payload['voice'] = self.voice_config
            # if hasattr(self, 'image_config'):
            #     payload['image'] = self.image_config
            # if hasattr(self, 'video_config'):
            #     payload['video'] = self.video_config
            start_time = time.time()
            response = await self.client.post(
                f"{self.api_base}/completions",
                headers=headers,
                json=payload
            )
            elapsed = time.time() - start_time
            response.raise_for_status()
            response_data = response.json()
            # Extraer respuesta y metadata
            result = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")
            tokens_used = response_data.get("usage", {}).get("total_tokens", 0)
            self._reset_failures()
            self._update_token_usage(tokens_used, business_unit)
            cache_response(self.model, prompt, result, business_unit)
            logger.info(f"Meta AI response generated in {elapsed:.2f}s using {tokens_used} tokens")
            return result
        except Exception as e:
            self._increment_failure()
            error_msg = str(e)
            logger.error(f"Error generando respuesta con Meta AI: {error_msg}")
            if "quota exceeded" in error_msg.lower() or "rate limit" in error_msg.lower():
                await self._notify_quota_exceeded()
                return "⚠️ Límite de cuota excedido. Se ha notificado al administrador."
            return f"Error: {error_msg}"
            
    async def _notify_quota_exceeded(self):
        """Notifica a los administradores sobre cuota excedida."""
        try:
            from app.ats.integrations.services import EmailService
            
            # Determinar destinatarios según BusinessUnit
            if hasattr(self, 'current_business_unit') and self.current_business_unit:
                bu_name = self.current_business_unit.name
                recipients = [self.current_business_unit.admin_email] if hasattr(self.current_business_unit, 'admin_email') else []
            else:
                bu_name = "Meta AI Service"
                recipients = ["admin@grupohuntred.com"]
                
            if not recipients:
                recipients = ["admin@grupohuntred.com"]
                
            # Enviar notificación
            for recipient in recipients:
                await EmailService.send_email_async(
                    subject=f"Alerta: Cuota de Meta AI excedida para {bu_name}",
                    to_email=recipient,
                    body=f"La cuota de Meta AI (Llama 3) ha sido excedida para {bu_name}. "  
                         f"Por favor, revise su suscripción o contacte con Meta Business Support.",
                    from_email="no-reply@grupohuntred.com"
                )
                
            logger.info(f"Notificación de cuota excedida enviada a {', '.join(recipients)}")
            
        except Exception as e:
            logger.error(f"Error enviando notificación de cuota excedida: {str(e)}")
            
    async def close(self):
        """Cierra recursos."""
        if hasattr(self, 'client') and self.client:
            await self.client.aclose()
            self.client = None
            
        self.initialized = False
        logger.debug("MetaAIHandler cerrado correctamente")

# Mapeo actualizado para incluir Meta AI
HANDLER_MAPPING = {
    'openai': OpenAIHandler,
    'xai': GrokHandler,
    'xai (grok)': GrokHandler,
    'grok': GrokHandler,
    'gemini': GeminiHandler,
    'llama': LlamaHandler,
    'claude': ClaudeHandler,
    'vertex': VertexAIHandler,
    'mistral': MistralAIHandler,
    'mistral ai': MistralAIHandler,
    'mistralai': MistralAIHandler,
    'meta': MetaAIHandler,
    'meta ai': MetaAIHandler,
    'meta-llama': MetaAIHandler,
    'llama-3': MetaAIHandler
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


class GPTProvider:
    """Clase base dinámica para proveedores IA, extensible por BU vía herencia."""
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.grok.x.ai/v1/"  # GROK como default, configurable.

    @lru_cache(maxsize=500)  # Caché dinámico para prompts comunes, reduce CPU sin latencia extra.
    def prepare_prompt(self, input_text: str, bu_context: Dict[str, Any]) -> str:
        # Optimización: Preparación simple y cacheada para balance CPU/respuesta.
        return f"Genera contenido para BU {bu_context.get('bu_id')}: {input_text}"

    async def generate_response(self, prompt: str, bu_context: Optional[Dict[str, Any]] = None) -> str:
        """Función existente mantenida, ahora async para dinamismo y bajo CPU en I/O."""
        prepared = self.prepare_prompt(prompt, bu_context or {})
        async with aiohttp.ClientSession() as session:  # Context manager para eficiencia.
            async with session.post(
                self.base_url + "chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"model": "grok-4", "messages": [{"role": "user", "content": prepared}]}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data["choices"][0]["message"]["content"]
                raise ValueError("Error en API GROK")

class BUModularGPT(GPTProvider):
    """Extensión dinámica para modularidad por BU, hereda de GPTProvider para escalabilidad sin perder funcionalidad."""
    def __init__(self, api_key: str, bu_specifics: Dict[str, Any]):
        super().__init__(api_key)
        self.bu_specifics = bu_specifics  # Contexto dinámico por BU (e.g., idioma, preferencias).

    async def generate_response(self, prompt: str, bu_context: Optional[Dict[str, Any]] = None) -> str:
        # Dinamismo: Ajuste por BU sin eventos aislados, usando herencia.
        combined_context = {**self.bu_specifics, **(bu_context or {})}
        return await super().generate_response(prompt, combined_context)