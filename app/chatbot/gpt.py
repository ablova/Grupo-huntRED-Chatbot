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

# Configuración del logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

REQUEST_TIMEOUT = 10.0  # ya definido en services.py; se puede importar si se centraliza

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_formatter = logging.Formatter('[%(asctime)s] %(levelname)s %(name)s: %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

file_handler = logging.FileHandler('logs/gpt_handler.log')
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter('[%(asctime)s] %(levelname)s %(name)s: %(message)s')
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

from app.chatbot.nlp import nlp_processor  # Importamos el NLP

from app.chatbot.nlp import nlp_processor  # Importamos el NLP

class GPTHandler:
    def __init__(self):
        logger.debug("Creando instancia de GPTHandler...")
        self.gpt_api = None
        self.client = None
        self.model = None
        self.max_tokens = None
        self.temperature = None
        self.top_p = None

    async def initialize(self):
        """
        Carga la configuración de GPT desde la base de datos.
        """
        try:
            gpt_api = await sync_to_async(lambda: GptApi.objects.first())()
            if gpt_api:
                self.gpt_api = gpt_api
                self.client = OpenAI(api_key=gpt_api.api_token, organization=gpt_api.organization)
                self.model = gpt_api.model or "gpt-4"
                self.max_tokens = gpt_api.max_tokens or 150
                self.temperature = gpt_api.temperature or 0.7
                self.top_p = gpt_api.top_p or 1.0
                logger.debug(f"GPTHandler configurado para usar el modelo: {self.model}")
            else:
                logger.error("No se encontró una instancia de GptApi en la base de datos.")
                raise ValueError("No hay GPT API configurada en la base de datos.")
        except Exception as e:
            logger.exception("Error al inicializar GPTHandler:", exc_info=True)
            raise e

    def detectar_intencion(self, mensaje: str) -> str:
        """
        Analiza la intención del usuario usando NLP y devuelve un tipo de prompt.
        """
        analisis = nlp_processor.analyze(mensaje)
        entidades_detectadas = [entidad[0].lower() for entidad in analisis.get("entities", [])]
        intenciones = analisis.get("intents", [])

        # 🔹 Identificar si el mensaje menciona una unidad de negocio
        unidades_negocio = ["huntred", "huntred executive", "huntu", "amigro"]
        for unidad in unidades_negocio:
            if unidad.lower() in mensaje.lower() or unidad in entidades_detectadas:
                return unidad

        # 🔹 Identificar preguntas comunes según la intención detectada
        if "perfil" in intenciones or "experiencia" in intenciones:
            return "perfil"
        if "habilidades" in intenciones:
            return "habilidades"
        if "migracion" in intenciones:
            return "migracion"
        if "recomendaciones" in intenciones:
            return "recomendaciones"
        if "idiomas" in intenciones:
            return "idiomas"
        if "soft_skills" in intenciones:
            return "soft_skills"
        if "hard_skills" in intenciones:
            return "hard_skills"
        if "negociacion" in intenciones:
            return "negociacion"
        if "gestion_proyectos" in intenciones:
            return "gestion_proyectos"

        return "general"  # Si no detectamos nada específico, usamos un prompt genérico

    async def generate_response(self, prompt: str, business_unit: str = "General") -> str:
        """
        Genera una respuesta usando GPT, incluyendo la unidad de negocio como contexto en formato optimizado.
        """
        if not self.client:
            return "⚠ GPT no está inicializado."

        prompt_type = self.detectar_intencion(prompt)  # 🔹 Identifica si es "ventas", "finanzas", etc.
        context = self.gpt_api.get_prompt(prompt_type, default="Responde de forma clara y precisa.")

        business_unit_name = getattr(business_unit, "name", "Grupo huntRED")  # Si no tiene nombre, usa "General"

        full_prompt = f"[{business_unit_name} | {prompt_type}] {context}\n\nUsuario: {prompt}"

        # 🔹 Optimización del prompt
        full_prompt = f"[{business_unit}] {context}\nPregunta: {prompt}"

        logger.debug(f"Generando respuesta para unidad '{business_unit}': {full_prompt[:100]}...")  # 🔹 Evitamos logs extensos

        try:
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=self.model,
                messages=[
                    {"role": "system", "content": f"Responde con base en la unidad '{business_unit}'."},
                    {"role": "user", "content": full_prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                top_p=self.top_p
            )
            return response.choices[0].message.content.strip()

        except RateLimitError:
            logger.error("⚠ Se ha excedido la cuota de OpenAI.")
            return "Lo siento, hemos excedido la cuota de OpenAI."
        except OpenAIError as oe:
            logger.error(f"❌ Error de OpenAI: {oe}", exc_info=True)
            return "Hubo un problema con GPT."
        except Exception as e:
            logger.error(f"❌ Error inesperado: {e}", exc_info=True)
            return "Ocurrió un error inesperado."

    def generate_response_sync(self, prompt: str, context: Optional[Dict] = None) -> str:
        """
        Versión síncrona de generate_response.
        Se recomienda llamar a la versión asíncrona desde un entorno asíncrono.
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                logger.warning("Se está ejecutando en un loop asíncrono; se recomienda usar generate_response directamente.")
                return asyncio.run(self.generate_response(prompt, context))
            else:
                return asyncio.run(self.generate_response(prompt, context))
        except Exception as e:
            logger.error(f"Error generando respuesta sincronizada con GPT: {e}", exc_info=True)
            return "Error inesperado al procesar la solicitud."

    def _notify_quota_exceeded(self):
        logger.debug("Enviando notificación de cuota excedida.")
        subject = "Se acabó la cuota de OpenAI"
        body = (
            "Hola,\n\n"
            "El sistema ha detectado que se ha excedido la cuota de OpenAI.\n\n"
            "Por favor, revisa el plan y detalles de facturación de OpenAI para continuar con el servicio.\n\n"
            "Saludos."
        )
        emails = ["pablo@huntred.com", "finanzas@huntred.com"]
        for email in emails:
            try:
                send_email(
                    business_unit_name="Amigro", 
                    subject=subject, 
                    to_email=email, 
                    body=body
                )
                logger.debug(f"Correo de notificación enviado a {email}.")
            except Exception as e:
                logger.error(f"No se pudo enviar el correo de notificación de cuota excedida a {email}: {e}", exc_info=True)

    @staticmethod
    async def gpt_message(api_token: str, text: str, model: str = "gpt-4") -> Optional[str]:
        logger.debug(f"Generando respuesta con gpt_message para el texto: {text}")
        try:
            client = OpenAI(api_key=api_token)
            response = await asyncio.to_thread(
                client.chat.completions.create,
                model=model,
                messages=[{"role": "user", "content": text}],
                max_tokens=150,
                temperature=0.7,
                top_p=1.0
            )
            respuesta_texto = response.choices[0].message.content.strip()
            logger.debug(f"Contenido de la respuesta: {respuesta_texto}")
            return respuesta_texto
        except RateLimitError:
            logger.error("Excediste tu cuota actual de OpenAI en gpt_message.")
            return "Excediste tu cuota actual de OpenAI."
        except OpenAIError as oe:
            logger.error(f"Error de OpenAI en gpt_message: {oe}", exc_info=True)
            return "No se pudo procesar tu solicitud a OpenAI."
        except Exception as e:
            logger.error(f"Error generando respuesta con GPT en gpt_message: {e}", exc_info=True)
            return "Error inesperado."

    @backoff.on_exception(backoff.expo, OpenAIError, max_tries=3)
    async def generate_response_with_retries(self, prompt: str, context: Optional[Dict] = None) -> str:
        import json
        full_prompt = prompt
        if context:
            full_prompt += "\nContexto adicional:\n" + json.dumps(context)
        logger.debug(f"Generando respuesta con reintentos para el prompt: {full_prompt}")
        try:
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=self.model,
                messages=[{"role": "user", "content": full_prompt}],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                top_p=self.top_p
            )
            respuesta_texto = response.choices[0].message.content.strip()
            logger.debug(f"Contenido de la respuesta: {respuesta_texto}")
            return respuesta_texto
        except OpenAIError as oe:
            logger.error(f"Error de OpenAI durante reintentos: {oe}", exc_info=True)
            raise oe
        except Exception as e:
            logger.error(f"Error generando respuesta con GPT en generate_response_with_retries: {e}", exc_info=True)
            raise e
