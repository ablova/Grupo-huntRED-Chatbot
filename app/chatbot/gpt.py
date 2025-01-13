# /home/pablollh/app/chatbot/gpt.py
import logging
import openai
import backoff
from typing import Dict, Optional
from app.models import GptApi
from app.integrations.services import send_email
from django.conf import settings
from openai import OpenAIError, RateLimitError  # Importar excepciones desde openai

logger = logging.getLogger(__name__)

class GPTHandler:
    def __init__(self):
        gpt_api = GptApi.objects.first()
        if gpt_api:
            openai.api_key = gpt_api.api_token
            if gpt_api.organization:
                openai.organization = gpt_api.organization
            # Ajusta el nombre del modelo a uno válido en tu cuenta
            self.model = gpt_api.model or "gpt-4.0-mini"
        else:
            raise ValueError("No hay GPT API configurada en la base de datos.")
        
    def generate_response(self, prompt: str, context: Optional[Dict] = None) -> str:
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                temperature=0.7
            )
            return response.choices[0].message.content.strip()

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
        subject = "Se acabó la cuota de OpenAI"
        body = (
            "Hola,\n\n"
            "El sistema ha detectado que se ha excedido la cuota de OpenAI.\n\n"
            "Por favor, revisa el plan y detalles de facturación de OpenAI para continuar con el servicio.\n\n"
            "Saludos."
        )
        # Lista de correos para notificar
        emails = ["pablo@huntred.com", "finanzas@huntred.com"]
        for email in emails:
            try:
                send_email(
                    business_unit_name="Amigro", 
                    subject=subject, 
                    to_email=email, 
                    body=body
                )
            except Exception as e:
                logger.error(f"No se pudo enviar el correo de notificación de cuota excedida a {email}: {e}")

    def gpt_message(api_token: str, text: str, model: str = "gpt-4.0-mini"):
        openai.api_key = api_token
        try:
            response = openai.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": text}],
                max_tokens=150,
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
    #    except RateLimitError:
    #        logger.error("Excediste tu cuota actual de OpenAI en gpt_message.")
    #        return {"error": "Excediste tu cuota actual de OpenAI."}
    #    except OpenAIError as oe:
    #        logger.error(f"Error de OpenAI en gpt_message: {oe}", exc_info=True)
    #        return {"error": "No se pudo procesar tu solicitud a OpenAI."}
        except Exception as e:
            logger.error(f"Error generando respuesta con GPT en gpt_message: {e}", exc_info=True)
            return {"error": "Error inesperado."}
    
    @backoff.on_exception(backoff.expo, OpenAIError, max_tries=3)
    def generate_response_with_retries(self, prompt: str, context: Optional[Dict] = None) -> str:
        """
        Genera una respuesta con reintentos en caso de errores.
        """
        response = openai.ChatCompletion.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()