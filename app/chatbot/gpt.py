# /home/pablo/app/chatbot/gpt.py

import logging
import backoff
from openai import OpenAI, OpenAIError, RateLimitError
from typing import Dict, Optional
from app.models import GptApi, BusinessUnit
from app.chatbot.integrations.services import send_email
from django.conf import settings
from asgiref.sync import sync_to_async
import asyncio
import json
import requests  # Para las APIs de Grok y Gemini

# Configuración del logger
logger = logging.getLogger(__name__)

# Valores por defecto
GPT_DEFAULTS = {
    "model": "gpt-4",
    "max_tokens": 150,
    "temperature": 0.2,
    "top_p": 0.9,
    "timeout": 60,
}

# Clase base para handlers
class BaseHandler:
    def __init__(self, config: GptApi):
        self.config = config
        self.client = None

    async def initialize(self):
        raise NotImplementedError("Método 'initialize' debe ser implementado.")

    async def generate_response(self, prompt: str, business_unit=None) -> str:
        raise NotImplementedError("Método 'generate_response' debe ser implementado.")

# Handler para OpenAI
class OpenAIHandler(BaseHandler):
    async def initialize(self):
        self.client = OpenAI(api_key=self.config.api_token, organization=self.config.organization)
        logger.info(f"OpenAIHandler configurado con modelo: {self.config.model}")

    @backoff.on_exception(backoff.expo, OpenAIError, max_tries=3)
    async def generate_response(self, prompt: str, business_unit=None) -> str:
        if not self.client:
            return "⚠ OpenAI no inicializado."

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
                        {"role": "system", "content": self.config.get_prompt("system", "Eres experto en empleabilidad y reclutamiento.")},
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
            return "Cuota excedida."
        except asyncio.TimeoutError:
            logger.warning("Timeout en OpenAI.")
            return "Solicitud tardó demasiado."

# Handler para Llama (Vertex AI)
class LlamaHandler(BaseHandler):
    async def initialize(self):
        # Nota: Esto asume que usas la API de Vertex AI para Llama
        from google.cloud import aiplatform
        aiplatform.init(project=self.config.project, credentials=self.config.api_token)
        logger.info(f"LlamaHandler configurado con modelo: {self.config.model}")

    async def generate_response(self, prompt: str, business_unit=None) -> str:
        bu_name = business_unit.name if business_unit else "General"
        full_prompt = (
            f"Unidad de Negocio: {bu_name}\n"
            f"{prompt}\n\n"
            "Devuelve únicamente una lista JSON de habilidades (ej: ['Python', 'Django'])."
        )
        # Placeholder: ajustar según la API real de Vertex AI
        return f"Respuesta desde Llama: {full_prompt}"  # Implementar la llamada real

# Handler para Grok (X AI)
class GrokHandler(BaseHandler):
    async def initialize(self):
        self.api_url = "https://api.x.ai/v1/chat/completions"  # URL ficticia, reemplazar con la real
        self.headers = {"Authorization": f"Bearer {self.config.api_token}"}
        logger.info(f"GrokHandler configurado con modelo: {self.config.model}")

    async def generate_response(self, prompt: str, business_unit=None) -> str:
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
            response = await asyncio.to_thread(
                requests.post, self.api_url, headers=self.headers, json=payload
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"].strip()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error en Grok: {e}")
            return "Error al comunicarse con Grok."

# Handler para Gemini (Google)
class GeminiHandler(BaseHandler):
    async def initialize(self):
        self.api_url = "https://api.google.com/gemini/v1/generate"  # URL ficticia, reemplazar con la real
        self.headers = {"Authorization": f"Bearer {self.config.api_token}"}
        logger.info(f"GeminiHandler configurado con modelo: {self.config.model}")

    async def generate_response(self, prompt: str, business_unit=None) -> str:
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
            "temperature": self.config.temperature,
            "top_p": self.config.top_p
        }

        try:
            response = await asyncio.to_thread(
                requests.post, self.api_url, headers=self.headers, json=payload
            )
            response.raise_for_status()
            return response.json()["text"].strip()  # Ajustar según la estructura real de la respuesta
        except requests.exceptions.RequestException as e:
            logger.error(f"Error en Gemini: {e}")
            return "Error al comunicarse con Gemini."

# Fábrica de handlers
def get_handler(config: GptApi) -> BaseHandler:
    model_type = config.model_type
    if model_type == 'gpt-4':
        return OpenAIHandler(config)
    elif model_type == 'llama-2':
        return LlamaHandler(config)
    elif model_type == 'grok-2':
        return GrokHandler(config)
    elif model_type == 'gemini':
        return GeminiHandler(config)
    else:
        raise ValueError(f"Tipo de modelo no soportado: {model_type}")

# Clase principal ajustada
class GPTHandler:
    def __init__(self):
        logger.debug("Instancia GPTHandler creada.")
        self.gpt_api = None
        self.client = None
        self.config = GPT_DEFAULTS.copy()
        self.current_business_unit = None  # Atributo para almacenar la unidad de negocio actual

    async def initialize(self):
        try:
            gpt_api = await sync_to_async(lambda: GptApi.objects.filter(is_active=True).first())()
            if gpt_api:
                self.handler = get_handler(gpt_api)
                await self.handler.initialize()
                self.config.update({
                    "model": gpt_api.model or GPT_DEFAULTS["model"],
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

    async def detectar_intencion(self, mensaje: str) -> str:
        from app.chatbot.nlp import NLPProcessor
        nlp = NLPProcessor()
        analisis = await sync_to_async(nlp.analyze)(mensaje)

        entidades = [ent[0].lower() for ent in analisis.get("entities", [])]
        intenciones = analisis.get("intents", [])

        unidades_negocio = ["huntred", "huntred executive", "huntu", "amigro"]
        for unidad in unidades_negocio:
            if unidad.lower() in mensaje.lower() or unidad in entidades:
                return unidad

        intent_map = {
            "perfil": ["perfil", "experiencia"],
            "habilidades": ["habilidades"],
            "migracion": ["migracion"],
            "recomendaciones": ["recomendaciones"],
            "idiomas": ["idiomas"],
            "soft_skills": ["soft_skills"],
            "hard_skills": ["hard_skills"],
            "negociacion": ["negociacion"],
            "gestion_proyectos": ["gestion_proyectos"],
        }

        for key, keywords in intent_map.items():
            if any(intent in intenciones for intent in keywords):
                return key

        return "general"

    @backoff.on_exception(backoff.expo, OpenAIError, max_tries=3)
    async def generate_response(self, prompt: str, business_unit: Optional[BusinessUnit] = None) -> str:
        self.current_business_unit = business_unit  # Almacenar la unidad de negocio
        if not self.client:
            return "⚠ GPT no inicializado."

        prompt_type = await self.detectar_intencion(prompt)
        bu_name = business_unit.name if business_unit else "General"

        full_prompt = (
            f"Unidad de Negocio: {bu_name}\n"
            f"Tipo de consulta: {prompt_type}\n"
            f"{prompt}\n\n"
            "Devuelve únicamente una lista JSON de habilidades (ej: ['Python', 'Django'])."
        )

        try:
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    self.client.chat.completions.create,
                    model=self.config["model"],
                    messages=[
                        {"role": "system", "content": "Eres experto en empleabilidad y reclutamiento."},
                        {"role": "user", "content": full_prompt}
                    ],
                    max_tokens=self.config["max_tokens"],
                    temperature=self.config["temperature"],
                    top_p=self.config["top_p"]
                ),
                timeout=self.config["timeout"]
            )
            return response.choices[0].message.content.strip()

        except RateLimitError:
            logger.warning("Cuota de OpenAI excedida.")
            self._notify_quota_exceeded()
            return "Cuota excedida. Intenta más tarde."

    def _notify_quota_exceeded(self):
        # Determinar dinámicamente el remitente y los destinatarios
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
                # Usar la función send_email de services.py
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

# Eliminamos LLMChatGenerator si no lo usas activamente