import logging
import backoff
from openai import OpenAI, OpenAIError, RateLimitError
from typing import Optional, Dict, Any, List, Union, Type
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
from cachetools import TTLCache
from concurrent.futures import ThreadPoolExecutor

# Configuración del logger avanzado
logger = logging.getLogger('gpt_v2')

# Constantes de configuración
MAX_RETRIES = 3
CIRCUIT_BREAKER_THRESHOLD = 5
CIRCUIT_BREAKER_TIMEOUT = 60  # segundos
PROMPT_CACHE_SIZE = 1000
TOKEN_USAGE_ALERT_THRESHOLD = 0.8  # 80% del límite
MAX_CONCURRENT_REQUESTS = 5

# Cache para prompts y respuestas
global_prompt_cache = TTLCache(maxsize=PROMPT_CACHE_SIZE, ttl=3600)
response_cache = TTLCache(maxsize=1000, ttl=3600)

# Estado del circuit breaker
circuit_breakers = {}

# ThreadPool para operaciones bloqueantes
thread_pool = ThreadPoolExecutor(max_workers=5)

class PromptManager:
    """Manejador de prompts con cache y optimización."""
    
    def __init__(self, business_unit: BusinessUnit):
        self.business_unit = business_unit
        self.cache = TTLCache(maxsize=100, ttl=3600)
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
                Habilidades: {skills}
                Experiencia: {experience}
                Responde con oportunidades relevantes en formato JSON."""
            }
        }
        return templates.get(self.business_unit.name.lower(), {})
        
    def get_prompt(self, template_name: str, context: Dict) -> str:
        """Obtiene un prompt específico con contexto."""
        if template_name in self.cache:
            return self.cache[template_name]
            
        template = self.templates.get(template_name)
        if not template:
            raise ValueError(f"Template {template_name} no encontrado para {self.business_unit.name}")
            
        prompt = template.format(**context)
        self.cache[template_name] = prompt
        return prompt
        
    def get_system_prompt(self) -> str:
        """Obtiene el prompt del sistema para el BU."""
        return f"""Eres un asistente de {self.business_unit.name} especializado en:
        - Análisis de posiciones laborales
        - Evaluación de candidatos
        - Asistencia a migrantes
        - Búsqueda de oportunidades
        Responde siempre en formato JSON y considera el contexto de {self.business_unit.name}.
        """

class BaseGPTHandler:
    """Handler base para todas las implementaciones GPT."""
    
    def __init__(self, config: GptApi, business_unit: BusinessUnit):
        self.config = config
        self.business_unit = business_unit
        self.prompt_manager = PromptManager(business_unit)
        self.client = None
        self.failures = 0
        self.is_circuit_open = False
        self.circuit_open_time = 0
        self.token_usage = 0
        self.token_limit = getattr(config, 'token_limit', 100000)
        self.semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
        
    async def initialize(self) -> None:
        """Inicializa el handler y sus recursos."""
        raise NotImplementedError("Método 'initialize' debe ser implementado.")
        
    async def generate_response(self, prompt: Union[str, Dict], context: Optional[Dict] = None) -> Dict:
        """Genera una respuesta usando el modelo GPT."""
        if self._check_circuit_breaker():
            raise Exception("Circuit breaker abierto. Intenta más tarde.")
            
        try:
            async with self.semaphore:
                # Convertir prompt a string si es un diccionario
                if isinstance(prompt, dict):
                    prompt = self.prompt_manager.get_prompt(prompt['template'], prompt.get('context', {}))
                    
                # Verificar cache
                cache_key = f"{self.config.model}:{prompt}:{str(context)}"
                if cache_key in response_cache:
                    return response_cache[cache_key]
                    
                # Generar respuesta
                response = await self._generate_response(prompt, context)
                
                # Almacenar en cache
                response_cache[cache_key] = response
                
                return response
                
        except Exception as e:
            self._increment_failure()
            raise
            
    async def _generate_response(self, prompt: str, context: Optional[Dict]) -> Dict:
        """Método a implementar por las subclases."""
        raise NotImplementedError("Método '_generate_response' debe ser implementado.")
        
    def _check_circuit_breaker(self) -> bool:
        """Verifica el estado del circuit breaker."""
        if self.is_circuit_open:
            if time.time() - self.circuit_open_time > CIRCUIT_BREAKER_TIMEOUT:
                logger.info(f"Reseteando circuit breaker para {self.config.model}")
                self.is_circuit_open = False
                self.failures = 0
                return False
            return True
        return False
        
    def _increment_failure(self) -> None:
        """Incrementa el contador de fallos."""
        self.failures += 1
        if self.failures >= CIRCUIT_BREAKER_THRESHOLD:
            logger.warning(f"Circuit breaker abierto para {self.config.model}")
            self.is_circuit_open = True
            self.circuit_open_time = time.time()
            
    def _update_token_usage(self, tokens: int) -> None:
        """Actualiza el uso de tokens."""
        self.token_usage += tokens
        if self.token_usage >= self.token_limit * TOKEN_USAGE_ALERT_THRESHOLD:
            logger.warning(f"Uso de tokens ({self.token_usage}/{self.token_limit}) cerca del límite")
            
    async def close(self) -> None:
        """Limpia recursos."""
        if hasattr(self, 'client'):
            await self._close_client()
            
    async def _close_client(self) -> None:
        """Cierra el cliente."""
        raise NotImplementedError("Método '_close_client' debe ser implementado.")

class OpenAIHandler(BaseGPTHandler):
    """Handler para OpenAI API."""
    
    async def initialize(self) -> None:
        """Inicializa el cliente OpenAI."""
        self.client = OpenAI(
            api_key=self.config.api_key,
            base_url=self.config.api_base or "https://api.openai.com/v1"
        )
        logger.info(f"OpenAIHandler inicializado para {self.config.model}")
        
    async def _generate_response(self, prompt: str, context: Optional[Dict]) -> Dict:
        """Genera respuesta usando OpenAI."""
        try:
            response = await self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": self.prompt_manager.get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.config.max_tokens or 150,
                temperature=self.config.temperature or 0.2,
                top_p=self.config.top_p or 0.9,
                timeout=self.config.timeout or 60
            )
            
            # Actualizar uso de tokens
            total_tokens = response.usage.total_tokens
            self._update_token_usage(total_tokens)
            
            return {
                'response': response.choices[0].message.content,
                'tokens': total_tokens,
                'model': self.config.model
            }
            
        except RateLimitError:
            logger.warning("Rate limit alcanzado. Esperando...")
            await asyncio.sleep(60)
            raise
            
        except Exception as e:
            logger.error(f"Error en OpenAIHandler: {str(e)}")
            raise
            
    async def _close_client(self) -> None:
        """Cierra el cliente OpenAI."""
        if hasattr(self.client, 'close'):
            await self.client.close()

class GoogleGeminiHandler(BaseGPTHandler):
    """Handler para Google Gemini API."""
    
    async def initialize(self) -> None:
        """Inicializa el cliente Gemini."""
        genai.configure(api_key=self.config.api_key)
        self.client = genai.GenerativeModel(model=self.config.model)
        logger.info(f"GoogleGeminiHandler inicializado para {self.config.model}")
        
    async def _generate_response(self, prompt: str, context: Optional[Dict]) -> Dict:
        """Genera respuesta usando Gemini."""
        try:
            response = await self.client.generate_content(
                prompt,
                generation_config=types.GenerationConfig(
                    temperature=self.config.temperature or 0.2,
                    top_p=self.config.top_p or 0.9,
                    max_output_tokens=self.config.max_tokens or 1024
                )
            )
            
            # Estimar tokens
            total_tokens = len(prompt.split()) + len(response.text.split())
            self._update_token_usage(total_tokens)
            
            return {
                'response': response.text,
                'tokens': total_tokens,
                'model': self.config.model
            }
            
        except Exception as e:
            logger.error(f"Error en GoogleGeminiHandler: {str(e)}")
            raise
            
    async def _close_client(self) -> None:
        """Cierra el cliente Gemini."""
        pass  # No necesita cierre explícito

class HandlerFactory:
    """Factoría para crear handlers GPT."""
    
    handlers = {
        'openai': OpenAIHandler,
        'google_gemini': GoogleGeminiHandler,
        # Agregar otros handlers aquí
    }
    
    @classmethod
    async def create_handler(cls, config: GptApi, business_unit: BusinessUnit) -> BaseGPTHandler:
        """Crea un handler específico."""
        handler_class = cls.handlers.get(config.provider.lower())
        if not handler_class:
            raise ValueError(f"Handler no encontrado para proveedor {config.provider}")
            
        handler = handler_class(config, business_unit)
        await handler.initialize()
        return handler

class GPTManager:
    """Manejador principal para todas las operaciones GPT."""
    
    def __init__(self):
        self.handlers = {}
        self.active_handler = None
        self._load_handlers()
        
    def _load_handlers(self) -> None:
        """Carga todos los handlers configurados."""
        configs = GptApi.objects.all()
        for config in configs:
            try:
                handler = HandlerFactory.create_handler(config, config.business_unit)
                self.handlers[config.provider] = handler
                logger.info(f"Handler {config.provider} cargado exitosamente")
            except Exception as e:
                logger.error(f"Error cargando handler {config.provider}: {str(e)}")
                
    async def get_handler(self, provider: str) -> BaseGPTHandler:
        """Obtiene un handler específico."""
        handler = self.handlers.get(provider.lower())
        if not handler:
            raise ValueError(f"Handler no encontrado para {provider}")
            
        return handler
        
    async def generate_response(self, provider: str, prompt: Union[str, Dict], context: Optional[Dict] = None) -> Dict:
        """Genera una respuesta usando el handler especificado."""
        handler = await self.get_handler(provider)
        return await handler.generate_response(prompt, context)
        
    async def close_all(self) -> None:
        """Cierra todos los handlers."""
        for handler in self.handlers.values():
            await handler.close()
            
# Instancia global del manager
gpt_manager = GPTManager()

async def generate_response(provider: str, prompt: Union[str, Dict], context: Optional[Dict] = None) -> Dict:
    """Función de utilidad para generar respuestas."""
    return await gpt_manager.generate_response(provider, prompt, context)

async def close_all_handlers() -> None:
    """Cierra todos los handlers."""
    await gpt_manager.close_all()
