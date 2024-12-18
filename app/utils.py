# /home/pablollh/app/utils.py

import math
import re
import os
import logging
from datetime import datetime
from app.nlp import NLPProcessor
from django.core.exceptions import ValidationError
from itsdangerous import URLSafeTimedSerializer
from django.conf import settings

logger = logging.getLogger(__name__)

# Inicializar el NLPProcessor una sola vez
nlp_processor = NLPProcessor()



def clean_text(text: str) -> str:
    """
    Limpia texto eliminando caracteres especiales y espacios adicionales.
    """
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text)  # Reducir múltiples espacios
    text = re.sub(r'[^\w\sáéíóúñüÁÉÍÓÚÑÜ]', '', text, flags=re.UNICODE)  # Eliminar caracteres especiales exceptuando tildes
    return text.strip()

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