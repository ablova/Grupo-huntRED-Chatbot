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
        from app.chatbot.nlp import nlp_processor  # Importamos el NLP
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

    async def generate_response(self, prompt: str, business_unit=None) -> str:
        """
        Genera una respuesta utilizando OpenAI con timeout.
        """
        if not self.client:
            return "⚠ GPT no está inicializado."

        business_unit_name = business_unit.name if business_unit else "General"
        prompt_type = self.detectar_intencion(prompt)
        context = self.gpt_api.get_prompt(prompt_type, default="Proporciona información clara y concisa.")
        full_prompt = f"[{business_unit_name} | {prompt_type}] {context}\n\nUsuario: {prompt}"

        logger.debug(f"Generando respuesta con timeout para: {full_prompt[:100]}...")

        try:
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    self.client.chat.completions.create,
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "Eres un experto en empleabilidad y desarrollo profesional."},
                        {"role": "user", "content": full_prompt}
                    ],
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    top_p=self.top_p
                ),
                timeout=10.0  # ⏳ Timeout de 10 segundos
            )

            respuesta_texto = response.choices[0].message.content.strip()
            logger.debug(f"📩 Respuesta generada: {respuesta_texto}")
            return respuesta_texto

        except asyncio.TimeoutError:
            logger.warning("[GPT] ⏳ Tiempo de espera agotado en la consulta.")
            return "Lo siento, estoy teniendo problemas para responder en este momento."
        except OpenAIError as oe:
            logger.error(f"❌ Error de OpenAI: {oe}", exc_info=True)
            return "Hubo un problema con OpenAI."
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
        """
        Genera respuesta con OpenAI usando timeout.
        """
        logger.debug(f"Generando respuesta con timeout en gpt_message para: {text}")

        try:
            client = OpenAI(api_key=api_token)

            response = await asyncio.wait_for(
                asyncio.to_thread(
                    client.chat.completions.create,
                    model=model,
                    messages=[{"role": "user", "content": text}],
                    max_tokens=150,
                    temperature=0.7,
                    top_p=1.0
                ),
                timeout=10.0  # ⏳ Timeout de 10 segundos
            )

            respuesta_texto = response.choices[0].message.content.strip()
            logger.debug(f"📩 Respuesta generada: {respuesta_texto}")
            return respuesta_texto

        except asyncio.TimeoutError:
            logger.warning("[GPT] ⏳ Timeout en gpt_message.")
            return "Lo siento, no pude procesar tu solicitud a tiempo."
        except OpenAIError as oe:
            logger.error(f"❌ Error de OpenAI en gpt_message: {oe}", exc_info=True)
            return "No se pudo procesar tu solicitud con OpenAI."
        except Exception as e:
            logger.error(f"❌ Error inesperado en gpt_message: {e}", exc_info=True)
            return "Hubo un problema al generar la respuesta."

    @backoff.on_exception(backoff.expo, OpenAIError, max_tries=3)
    async def generate_response_with_retries(self, prompt: str, context: Optional[Dict] = None) -> str:
        """
        Genera respuesta con OpenAI y reintentos, agregando timeout.
        """
        import json
        full_prompt = prompt
        if context:
            full_prompt += "\nContexto adicional:\n" + json.dumps(context)
        logger.debug(f"Generando respuesta con reintentos y timeout para: {full_prompt[:100]}...")

        try:
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    self.client.chat.completions.create,
                    model=self.model,
                    messages=[{"role": "user", "content": full_prompt}],
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    top_p=self.top_p
                ),
                timeout=10.0  # ⏳ Timeout de 10 segundos
            )

            respuesta_texto = response.choices[0].message.content.strip()
            logger.debug(f"📩 Respuesta generada: {respuesta_texto}")
            return respuesta_texto

        except asyncio.TimeoutError:
            logger.warning("[GPT] ⏳ Timeout en generate_response_with_retries.")
            return "Lo siento, no pude procesar tu solicitud a tiempo."
        except OpenAIError as oe:
            logger.error(f"❌ Error de OpenAI en generate_response_with_retries: {oe}", exc_info=True)
            raise oe
        except Exception as e:
            logger.error(f"❌ Error inesperado en generate_response_with_retries: {e}", exc_info=True)
            raise e
        
    def generate_personalized_message(self, candidate, vacancy, classifier, llm_generator):
        """
        Genera un mensaje personalizado usando habilidades estandarizadas.
        """
        candidate_skills = " ".join(candidate.skills.split(',') if candidate.skills else [])
        job_skills = " ".join(vacancy.skills_required if vacancy.skills_required else [])
        prompt = f"Context: Candidato con habilidades: {candidate_skills}. Vacante requiere: {job_skills}. Genera un mensaje personalizado invitando al candidato a aplicar."
        return llm_generator.generate_response(prompt)

class LLMChatGenerator:
    def __init__(self, model_name="huggyllama/llama-2-7b-chat-hf"):
        self.generator = pipeline("text-generation", model=model_name)

    def generate_response(self, prompt, max_length=100, temperature=0.7):
        response = self.generator(prompt, max_length=max_length, temperature=temperature)
        return response[0]["generated_text"]
    
    def generate_personalized_message(self, candidate, vacancy, classifier, llm_generator):
        """
        Genera un mensaje personalizado usando habilidades estandarizadas.
        """
        candidate_skills = " ".join(candidate.skills.split(',') if candidate.skills else [])
        job_skills = " ".join(vacancy.skills_required if vacancy.skills_required else [])
        prompt = f"Context: Candidato con habilidades: {candidate_skills}. Vacante requiere: {job_skills}. Genera un mensaje personalizado invitando al candidato a aplicar."
        return llm_generator.generate_response(prompt)
    