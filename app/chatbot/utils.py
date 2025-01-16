# /home/pablollh/app/chatbot/utils.py

import math
import re
import os
import logging
import requests
from datetime import datetime
from app.models import GptApi
from app.chatbot.nlp import NLPProcessor
from django.core.exceptions import ValidationError
from itsdangerous import URLSafeTimedSerializer
from django.conf import settings
from typing import Dict, List
import json

logger = logging.getLogger(__name__)

# Inicializar el NLPProcessor una sola vez
nlp_processor = NLPProcessor()

# Cargar catálogo
JSON_PATH = os.path.join(settings.BASE_DIR, 'app', 'utilidades', 'catalogs', 'catalogs.json')
try:
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        catalog_data = json.load(f)
        BUSINESS_UNITS = catalog_data.get("BUSINESS_UNITS", [])
        DIVISIONES = catalog_data.get("DIVISIONES", [])
        DIVISION_SKILLS = catalog_data.get("DIVISION_SKILLS", {})
except Exception as e:
    logger.error(f"Error al cargar el catálogo desde {JSON_PATH}: {e}")
    BUSINESS_UNITS = []
    DIVISIONES = []
    DIVISION_SKILLS = {}

def clean_text(text: str) -> str:
    """
    Limpia texto eliminando caracteres especiales y espacios adicionales.
    """
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text)  # Reducir múltiples espacios
    text = re.sub(r'[^\w\sáéíóúñüÁÉÍÓÚÑÜ]', '', text, flags=re.UNICODE)  # Eliminar caracteres especiales
    return text.strip()

def get_gpt_config() -> dict:
    """
    Obtiene la configuración para GPT desde la base de datos.
    """
    gpt_api = GptApi.objects.first()
    if not gpt_api:
        raise ValueError("No se encuentra configuración GPT en la base de datos.")
    return {
        "model": gpt_api.model,
        "max_tokens": gpt_api.max_tokens or 150,
        "temperature": gpt_api.temperature or 0.7,
        "top_p": gpt_api.top_p or 1.0
    }

def analyze_text(text: str) -> dict:
    """
    Analiza el texto del usuario y extrae intenciones, entidades y sentimiento.
    Hace uso del NLPProcessor definido en nlp.py.
    """
    try:
        cleaned = clean_text(text)
        return nlp_processor.analyze(cleaned)
    except Exception as e:
        logger.error(f"Error analizando texto: {e}", exc_info=True)
        return {"intents": [], "entities": [], "sentiment": {}}

def validate_term_in_catalog(term: str, catalog: List[str]) -> bool:
    """
    Valida si un término existe en un catálogo especificado.

    Args:
        term (str): El término a buscar.
        catalog (list): El catálogo donde buscar el término.

    Returns:
        bool: True si el término está en el catálogo, False de lo contrario.
    """
    return term.lower() in [item.lower() for item in catalog]

def get_division_skills(division: str) -> dict:
    """
    Obtiene las habilidades técnicas y blandas de una división.

    Args:
        division (str): Nombre de la división.

    Returns:
        dict: Diccionario con habilidades técnicas y blandas, o vacío si no se encuentra.
    """
    return DIVISION_SKILLS.get(division, {})

def handle_openai_error(error):
    """
    Maneja errores comunes de OpenAI y proporciona mensajes adecuados.
    """
    if isinstance(error, requests.exceptions.RequestException):
        return "Error de red al comunicarse con OpenAI."
    return "Hubo un problema al procesar tu solicitud con OpenAI."

def validate_date(date_str: str) -> bool:
    """
    Valida si un string es una fecha en formato DD/MM/AAAA.
    """
    match = re.match(r"^(0[1-9]|[12][0-9]|3[01])/(0[1-9]|1[012])/\d{4}$", date_str)
    return bool(match)

def sanitize_business_unit_name(name: str) -> str:
    """
    Convierte el nombre de la BusinessUnit a un formato adecuado para filenames.
    Por ejemplo: 'Hunt RED' -> 'huntred'
    """
    return re.sub(r'\W+', '', name).lower()

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calcula la distancia en kilómetros entre dos puntos geográficos usando la fórmula de Haversine.
    """
    R = 6371  # Radio de la Tierra en km
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c

def fetch_data_from_url(url):
    """
    Realiza una solicitud HTTP para obtener datos desde una URL.
    """
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": f"Failed to fetch data from {url}"}
    
def generate_verification_token(key):
    serializer = URLSafeTimedSerializer(settings.SECRET_KEY)
    return serializer.dumps(key, salt='verification-salt')

def confirm_verification_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(settings.SECRET_KEY)
    try:
        key = serializer.loads(
            token,
            salt='verification-salt',
            max_age=expiration
        )
    except Exception:
        return False
    return key

def analyze_name_gender(name: str) -> str:
    """
    Analiza el género basado en el nombre usando NLPProcessor.
    """
    return nlp_processor.infer_gender(name)

def parse_cv_file(filepath: str) -> dict:
    """
    Parsear el contenido de un archivo de CV.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as file:
            content = file.read()
        return {"content": content}  # Analizar con NLP u otra herramienta
    except Exception as e:
        logger.error(f"Error al leer CV: {filepath}, {e}")
        return {}
    
def validate_request_data(data, required_fields):
    """
    Valida que los datos enviados cumplan con los campos requeridos.
    """
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        raise ValidationError(f"Faltan los campos requeridos: {', '.join(missing_fields)}")

def format_template_response(template: str, **kwargs) -> str:
    """
    Formatea una plantilla de texto con variables dinámicas.
    """
    try:
        return template.format(**kwargs)
    except KeyError as e:
        logger.error(f"Error al formatear plantilla: {str(e)}")
        return template

# Ejemplo de uso:
# response = format_template_response("Hola {nombre}, tienes {mensajes} nuevos mensajes.", nombre="Juan", mensajes=3)
# print(response)  # Hola Juan, tienes 3 nuevos mensajes.

def validate_request_fields(required_fields: list, data: Dict) -> bool:
    """
    Valida que todos los campos requeridos estén presentes en el payload.

    Args:
        required_fields (list): Lista de campos requeridos.
        data (dict): Datos proporcionados en la solicitud.

    Returns:
        bool: True si todos los campos están presentes, False de lo contrario.
    """
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        logger.warning(f"Faltan campos requeridos: {missing_fields}")
        return False
    return True

def log_with_correlation_id(message: str, correlation_id: str, level: str = "info"):
    """
    Registra mensajes con un ID de correlación para rastrear flujos de forma única.

    Args:
        message (str): El mensaje a registrar.
        correlation_id (str): El ID único de correlación.
        level (str): Nivel del log (info, warning, error).
    """
    log_message = f"[CorrelationID: {correlation_id}] {message}"
    if level == "info":
        logger.info(log_message)
    elif level == "warning":
        logger.warning(log_message)
    elif level == "error":
        logger.error(log_message)
    else:
        logger.debug(log_message)