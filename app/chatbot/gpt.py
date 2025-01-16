# /home/pablollh/app/chatbot/gpt.py

import logging
import openai
from typing import Dict, Optional
from openai.error import OpenAIError, RateLimitError
from app.models import GptApi
from app.chatbot.integrations.services import send_email
from django.conf import settings
from asgiref.sync import sync_to_async
import asyncio

# Configuración del logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Establece el nivel de logging según sea necesario

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

class GPTHandler:
    def __init__(self):
        logger.debug("Inicializando GPTHandler...")
        try:
            gpt_api = GptApi.objects.first()
            if gpt_api:
                logger.debug("Se encontró una instancia de GptApi en la base de datos.")
                logger.debug(f"Modelo: {gpt_api.model}, Organización: {gpt_api.organization}, Proyecto: {gpt_api.project}")

                openai.api_key = gpt_api.api_token
                if gpt_api.organization:
                    openai.organization = gpt_api.organization

                self.model = gpt_api.model or "gpt-4"
                self.max_tokens = gpt_api.max_tokens or 150
                self.temperature = gpt_api.temperature or 0.7
                self.top_p = gpt_api.top_p or 1.0
                logger.debug(f"Configurado para usar el modelo: {self.model}")
            else:
                logger.error("No se encontró una instancia de GptApi en la base de datos.")
                raise ValueError("No hay GPT API configurada en la base de datos.")
        except Exception as e:
            logger.exception("Error al inicializar GPTHandler: ", exc_info=True)
            raise e

    async def generate_response(self, prompt: str, context: Optional[Dict] = None) -> str:
        logger.debug(f"Generando respuesta para el prompt: {prompt}")
        try:
            response = await asyncio.to_thread(
                openai.ChatCompletion.create,
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                top_p=self.top_p
            )
            logger.debug("Respuesta recibida de OpenAI.")
            respuesta_texto = response["choices"][0]["message"]["content"].strip()
            logger.debug(f"Contenido de la respuesta: {respuesta_texto}")
            return respuesta_texto
        except RateLimitError:
            logger.error("Excediste tu cuota de OpenAI.")
            self._notify_quota_exceeded()
            return "Lo siento, se ha excedido la cuota actual de la API de OpenAI."
        except OpenAIError as oe:
            logger.error(f"Error de OpenAI: {oe}", exc_info=True)
            return "Lo siento, hubo un problema al procesar tu solicitud con GPT."
        except Exception as e:
            logger.error(f"Error generando respuesta con GPT: {e}", exc_info=True)
            return "Lo siento, ocurrió un error inesperado."

    def _notify_quota_exceeded(self):
        """
        Envía un correo notificando que se acabó la cuota de OpenAI.
        """
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
            openai.api_key = api_token
            response = await asyncio.to_thread(
                openai.ChatCompletion.create,
                model=model,
                messages=[{"role": "user", "content": text}],
                max_tokens=150,
                temperature=0.7,
                top_p=1.0
            )
            respuesta_texto = response["choices"][0]["message"]["content"].strip()
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
        """
        Genera una respuesta con reintentos en caso de errores.
        """
        logger.debug(f"Generando respuesta con reintentos para el prompt: {prompt}")
        try:
            response = await asyncio.to_thread(
                openai.ChatCompletion.create,
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                top_p=self.top_p
            )
            respuesta_texto = response["choices"][0]["message"]["content"].strip()
            logger.debug(f"Contenido de la respuesta: {respuesta_texto}")
            return respuesta_texto
        except OpenAIError as oe:
            logger.error(f"Error de OpenAI durante reintentos: {oe}", exc_info=True)
            raise oe
        except Exception as e:
            logger.error(f"Error generando respuesta con GPT en generate_response_with_retries: {e}", exc_info=True)
            raise e
