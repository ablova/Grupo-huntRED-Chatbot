# /home/pablo/app/ats/chatbot/utils/chatbot_utils.py
"""
Utilidades básicas del chatbot.
"""
import logging
import re
import time
from typing import Dict, List, Optional, Any
from django.utils import timezone
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.conf import settings
from itsdangerous import URLSafeTimedSerializer
from app.ats.utils.nlp import create_nlp_processor

logger = logging.getLogger(__name__)

class ChatbotUtils:
    """Utilidades básicas para el funcionamiento del chatbot."""

    # Constantes para control de spam
    SPAM_DETECTION_WINDOW = 30  # 30 segundos
    MAX_MESSAGE_REPEATS = 3     # Cuántas veces puede repetir el mismo mensaje antes de ser SPAM
    MAX_MESSAGES_PER_MINUTE = 10  # Límite de mensajes por usuario por minuto

    @staticmethod
    def clean_text(text: str) -> str:
        """Limpia texto eliminando caracteres especiales y espacios adicionales."""
        if not text:
            return ""
        text = re.sub(r'\s+', ' ', text).strip()
        text = re.sub(r'[^\w\sáéíóúñüÁÉÍÓÚÑÜ]', '', text, flags=re.UNICODE)
        return text

    @staticmethod
    def is_spam_message(user_id: str, text: str) -> bool:
        """Verifica si un mensaje es considerado SPAM."""
        if not text:
            return False

        text_cleaned = re.sub(r'\W+', '', text.lower().strip())
        cache_key = f"spam_check:{user_id}"
        user_messages = cache.get(cache_key, [])

        current_time = time.time()
        user_messages.append((text_cleaned, current_time))
        
        user_messages = [(msg, ts) for msg, ts in user_messages 
                        if current_time - ts < ChatbotUtils.SPAM_DETECTION_WINDOW]

        message_count = sum(1 for msg, _ in user_messages if msg == text_cleaned)
        if message_count >= ChatbotUtils.MAX_MESSAGE_REPEATS:
            return True

        cache.set(cache_key, user_messages, timeout=ChatbotUtils.SPAM_DETECTION_WINDOW)
        return False

    @staticmethod
    def update_user_message_history(user_id: str):
        """Registra la cantidad de mensajes enviados por un usuario en un minuto."""
        cache_key = f"msg_count:{user_id}"
        timestamps = cache.get(cache_key, [])
        current_time = time.time()

        timestamps = [ts for ts in timestamps if current_time - ts < 60]
        timestamps.append(current_time)
        
        cache.set(cache_key, timestamps, timeout=60)

    @staticmethod
    def is_user_spamming(user_id: str) -> bool:
        """Verifica si un usuario ha enviado demasiados mensajes en un corto periodo."""
        cache_key = f"msg_count:{user_id}"
        timestamps = cache.get(cache_key, [])
        return len(timestamps) > ChatbotUtils.MAX_MESSAGES_PER_MINUTE

    @staticmethod
    def generate_verification_token(key: str) -> str:
        """Genera un token seguro para verificación."""
        serializer = URLSafeTimedSerializer(settings.SECRET_KEY)
        return serializer.dumps(key, salt='verification-salt')

    @staticmethod
    def confirm_verification_token(token: str, expiration: int = 3600) -> Optional[str]:
        """Valida un token de verificación con tiempo de expiración."""
        serializer = URLSafeTimedSerializer(settings.SECRET_KEY)
        try:
            key = serializer.loads(token, salt='verification-salt', max_age=expiration)
            return key
        except Exception:
            return None

    @staticmethod
    def validate_request_data(data: Dict, required_fields: List[str]) -> None:
        """Valida que los datos enviados cumplan con los campos requeridos."""
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise ValidationError(f"Faltan los campos requeridos: {', '.join(missing_fields)}")

    @staticmethod
    def format_template_response(template: str, **kwargs) -> str:
        """Formatea una plantilla de texto con variables dinámicas."""
        try:
            return template.format(**kwargs)
        except KeyError as e:
            logger.error(f"Error al formatear plantilla: {str(e)}")
            return template

    @staticmethod
    def log_with_correlation_id(message: str, correlation_id: str, level: str = "info"):
        """Registra mensajes con un ID de correlación para rastrear flujos de forma únicos."""
        log_message = f"[CorrelationID: {correlation_id}] {message}"
        if level == "info":
            logger.info(log_message)
        elif level == "warning":
            logger.warning(log_message)
        elif level == "error":
            logger.error(log_message)
        else:
            logger.debug(log_message)

    @staticmethod
    def get_nlp_processor(business_unit=None, **kwargs):
        """
        Obtiene una instancia del procesador NLP.
        
        Args:
            business_unit: Unidad de negocio para el análisis
            **kwargs: Argumentos adicionales para el procesador
            
        Returns:
            NLPProcessor: Instancia del procesador NLP
        """
        return create_nlp_processor(business_unit, **kwargs) 