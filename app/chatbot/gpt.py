# /home/pablo/app/chatbot/gpt.py

import logging
import backoff
from openai import OpenAI, OpenAIError, RateLimitError
from typing import Dict, Optional
from app.models import GptApi
from app.chatbot.integrations.services import send_email
from django.conf import settings
from asgiref.sync import sync_to_async
import asyncio
import json

# Configuración del logger
logger = logging.getLogger(__name__)

# Valores por defecto para futura configuración dinámica
GPT_DEFAULTS = {
    "model": "gpt-4",
    "max_tokens": 150,
    "temperature": 0.2,
    "top_p": 0.9,
    "timeout": 60,
}

class GPTHandler:
    def __init__(self):
        logger.debug("Instancia GPTHandler creada.")
        self.gpt_api = None
        self.client = None
        self.config = GPT_DEFAULTS.copy()

    async def initialize(self):
        try:
            gpt_api = await sync_to_async(lambda: GptApi.objects.first())()
            if gpt_api:
                self.gpt_api = gpt_api
                self.client = OpenAI(api_key=gpt_api.api_token, organization=gpt_api.organization)
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
    async def generate_response(self, prompt: str, business_unit=None) -> str:
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

        except asyncio.TimeoutError:
            logger.warning("Timeout en la solicitud GPT.")
            return "Solicitud tardó demasiado. Intenta nuevamente."

        except OpenAIError as e:
            logger.error(f"Error OpenAI: {e}")
            return "Problema al comunicarse con GPT."

    def _notify_quota_exceeded(self):
        subject = "Cuota de OpenAI agotada"
        body = (
            "Hola,\n\nLa cuota de OpenAI se ha agotado. Por favor revisa tu cuenta.\n\nSaludos."
        )
        emails = ["pablo@huntred.com", "finanzas@huntred.com"]
        for email in emails:
            try:
                send_email("Amigro", subject, email, body)
                logger.info(f"Notificación cuota enviada a {email}.")
            except Exception as e:
                logger.error(f"Error enviando correo a {email}: {e}")

    @staticmethod
    async def gpt_message(api_token: str, text: str, model: str = "gpt-4") -> Optional[str]:
        try:
            client = OpenAI(api_key=api_token)
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    client.chat.completions.create,
                    model=model,
                    messages=[{"role": "user", "content": text}],
                    max_tokens=150,
                    temperature=0.2,
                    top_p=0.9
                ),
                timeout=10
            )
            return response.choices[0].message.content.strip()

        except asyncio.TimeoutError:
            logger.warning("Timeout en gpt_message.")
            return None
        except OpenAIError as oe:
            logger.error(f"Error OpenAI en gpt_message: {oe}")
            return None

    def generate_response_sync(self, prompt: str, business_unit=None) -> str:
        try:
            return asyncio.run(self.generate_response(prompt, business_unit))
        except Exception as e:
            logger.error(f"Error generando respuesta síncrona GPT: {e}")
            return "Error inesperado en la solicitud."

class LLMChatGenerator:
    def __init__(self, model_name="huggyllama/llama-2-7b-chat-hf"):
        from transformers import pipeline
        self.generator = pipeline("text-generation", model=model_name)

    def generate_response(self, prompt, max_length=100, temperature=0.7):
        response = self.generator(prompt, max_length=max_length, temperature=temperature)
        return response[0]["generated_text"]

    def generate_personalized_message(self, candidate, vacancy):
        candidate_skills = candidate.skills.split(',') if candidate.skills else []
        job_skills = vacancy.skills_required or []
        prompt = (
            f"Candidato con habilidades: {candidate_skills}. "
            f"Vacante requiere: {job_skills}. Genera un mensaje personalizado invitando al candidato."
        )
        return self.generate_response(prompt)
    