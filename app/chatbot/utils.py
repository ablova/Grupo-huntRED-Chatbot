# Ubicación en servidor: /home/pablo/app/chatbot/utils.py

import math
import os
import json
import logging
import re
import requests
import time
import asyncio
import pandas as pd
from datetime import datetime
from app.models import GptApi
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.conf import settings
from itsdangerous import URLSafeTimedSerializer
from typing import Dict, List, Any
from app.utilidades.catalogs import get_divisiones, map_skill_to_database
from app.chatbot.nlp import NLPProcessor


logger = logging.getLogger(__name__)


# Cargar catálogo desde el JSON centralizado
CATALOG_PATH = os.path.join(settings.BASE_DIR, 'app', 'utilidades', 'catalogs', 'catalogs.json')
def load_catalog() -> dict:
    """Carga el catálogo de habilidades desde catalogs.json."""
    if not os.path.exists(CATALOG_PATH):
        logger.error(f"Archivo de catálogo no encontrado: {CATALOG_PATH}")
        return {}
    try:
        with open(CATALOG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Error al cargar catálogo desde {CATALOG_PATH}: {e}")
        return {}

def get_all_skills_for_unit(unit_name: str = "huntRED®") -> List[str]:
    """Devuelve todas las habilidades de una unidad de negocio desde catalogs.json."""
    skills = []
    try:
        catalog = load_catalog()
        unit_data = catalog.get(unit_name, {})
        for division, roles in unit_data.items():
            for role, attributes in roles.items():
                skills.extend(attributes.get("Habilidades Técnicas", []))
                skills.extend(attributes.get("Habilidades Blandas", []))
                skills.extend(attributes.get("Herramientas", []))
        return list(set(skills))  # Eliminar duplicados
    except Exception as e:
        logger.error(f"Error obteniendo habilidades de {unit_name}: {e}")
        return []
    
def map_skill_to_database(llm_skill: str, database_skills: List[str], cutoff: float = 0.6) -> str:
    """Mapea una habilidad extraída por GPT a la base de datos usando similitud."""
    if llm_skill in database_skills:
        return llm_skill
    closest_match = get_close_matches(llm_skill, database_skills, n=1, cutoff=cutoff)
    return closest_match[0] if closest_match else None

def clean_text(text: str) -> str:
    """Limpia texto eliminando caracteres especiales y espacios adicionales."""
    if not text:
        return ""
    import re
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'[^\w\sáéíóúñüÁÉÍÓÚÑÜ]', '', text, flags=re.UNICODE)
    return text

def analyze_text(text: str) -> dict:
    """Analiza el texto del usuario y extrae intenciones, entidades y sentimiento."""
    try:
        cleaned = text.strip()
        loop = asyncio.get_event_loop()
        if loop.is_running():
            return asyncio.run_coroutine_threadsafe(nlp_processor.analyze(cleaned), loop).result()
        else:
            return asyncio.run(nlp_processor.analyze(cleaned))
    except Exception as e:
        logger.error(f"Error analizando texto: {e}", exc_info=True)
        return {"intents": [], "entities": [], "sentiment": {}}

def validate_term_in_catalog(term: str, catalog: List[str]) -> bool:
    """ Valida si un término existe en un catálogo especificado. """
    return term.lower() in [item.lower() for item in catalog]

def get_all_divisions():
    """ Obtiene todas las divisiones disponibles en los catálogos. """
    return get_divisiones()

def prioritize_interests(skills: List[str]) -> tuple[List[str], Dict[str, int]]:
    """ Asigna prioridad a los intereses detectados basándose en la frecuencia. """
    priorities = {}
    for skill in skills:
        priorities[skill] = priorities.get(skill, 0) + 1
    sorted_interests = dict(sorted(priorities.items(), key=lambda x: x[1], reverse=True))
    return list(sorted_interests.keys()), sorted_interests

def generate_verification_token(key):
    """ Genera un token seguro para verificación. """
    serializer = URLSafeTimedSerializer(settings.SECRET_KEY)
    return serializer.dumps(key, salt='verification-salt')

def confirm_verification_token(token, expiration=3600):
    """ Valida un token de verificación con tiempo de expiración. """
    serializer = URLSafeTimedSerializer(settings.SECRET_KEY)
    try:
        key = serializer.loads(token, salt='verification-salt', max_age=expiration)
    except Exception:
        return False
    return key

def validate_request_data(data, required_fields):
    """ Valida que los datos enviados cumplan con los campos requeridos. """
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        raise ValidationError(f"Faltan los campos requeridos: {', '.join(missing_fields)}")

def format_template_response(template: str, **kwargs) -> str:
    """ Formatea una plantilla de texto con variables dinámicas. """
    try:
        return template.format(**kwargs)
    except KeyError as e:
        logger.error(f"Error al formatear plantilla: {str(e)}")
        return template

def validate_request_fields(required_fields: list, data: Dict) -> bool:
    """ Valida que todos los campos requeridos estén presentes en el payload. """
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        logger.warning(f"Faltan campos requeridos: {missing_fields}")
        return False
    return True

def log_with_correlation_id(message: str, correlation_id: str, level: str = "info"):
    """ Registra mensajes con un ID de correlación para rastrear flujos de forma única. """
    log_message = f"[CorrelationID: {correlation_id}] {message}"
    if level == "info":
        logger.info(log_message)
    elif level == "warning":
        logger.warning(log_message)
    elif level == "error":
        logger.error(log_message)
    else:
        logger.debug(log_message)

def get_all_skills_for_unit(unit_name: str = "huntRED®") -> list:
    """ Devuelve todas las habilidades de una unidad de negocio. """
    skills = []
    try:
        catalog = load_catalog()
        unit_data = catalog.get(unit_name, {})
        for division, roles in unit_data.items():
            for role, attributes in roles.items():
                for key in ["Habilidades Técnicas", "Habilidades Blandas", "Herramientas"]:
                    skills.extend(attributes.get(key, []))
        return list(set(skills))
    except Exception as e:
        logger.error(f"Error obteniendo habilidades de {unit_name}: {e}")
        return []
    
def get_positions_by_skills(skills: List[str], threshold: float = 0.6) -> List[Dict]:
    """
    Obtiene vacantes adecuadas basadas en las habilidades detectadas.

    Args:
        skills (list): Lista de habilidades detectadas
        threshold (float): Umbral mínimo de coincidencia (0-1)

    Returns:
        list: Lista de diccionarios con vacantes sugeridas y su puntuación
    """
    from app.models import Vacante

    if not skills:
        return []

    normalized_skills = [skill.lower() for skill in skills]
    suggested = []

    # Obtener todas las vacantes que tienen habilidades requeridas
    all_vacantes = Vacante.objects.exclude(skills_required__isnull=True)

    for vacante in all_vacantes:
        try:
            # Obtener habilidades requeridas para esta vacante
            position_skills = []
            if isinstance(vacante.skills_required, dict) and 'skills' in vacante.skills_required:
                position_skills = [s.lower() for s in vacante.skills_required['skills']]
            elif isinstance(vacante.skills_required, list):
                position_skills = [s.lower() for s in vacante.skills_required]
            else:
                continue
            
            if not position_skills:
                continue

            # Calcular coincidencia
            matches = sum(1 for skill in normalized_skills if skill in position_skills)
            score = matches / len(position_skills) if len(position_skills) > 0 else 0
            
            if score >= threshold:
                suggested.append({
                    'position': vacante.titulo,
                    'score': round(score * 100, 1),
                    'business_unit': vacante.business_unit.name if vacante.business_unit else None,
                    'empresa': vacante.empresa,
                    'id': vacante.id
                })
        except Exception as e:
            logger.error(f"Error al procesar vacante {vacante.id}: {e}")
            continue

    # Ordenar por puntuación descendente
    suggested.sort(key=lambda x: x['score'], reverse=True)
    return suggested

####---------------------------------------------------------
### UTILIDADES PARA FUNCIONES DE LOCALIZACION, VALIDACION, ETC
####--------------------------------------------------------

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
  

####---------------------------------------------------------
###   SPAM CONTROL
####--------------------------------------------------------
# Tiempo en segundos para considerar mensajes duplicados como SPAM
SPAM_DETECTION_WINDOW = 30  # 30 segundos
MAX_MESSAGE_REPEATS = 3  # Cuántas veces puede repetir el mismo mensaje antes de ser SPAM
MAX_MESSAGES_PER_MINUTE = 10  # Límite de mensajes por usuario por minuto

def is_spam_message(user_id: str, text: str) -> bool:
    """
    Verifica si un mensaje es considerado SPAM basándose en su frecuencia y repetición.
    
    Args:
        user_id (str): ID del usuario.
        text (str): Texto del mensaje.

    Returns:
        bool: True si el mensaje es considerado SPAM, False en caso contrario.
    """
    if not text:
        return False

    text_cleaned = re.sub(r'\W+', '', text.lower().strip())  # Limpiar caracteres especiales
    cache_key = f"spam_check:{user_id}"
    user_messages = cache.get(cache_key, [])

    # Registrar el nuevo mensaje
    current_time = time.time()
    user_messages.append((text_cleaned, current_time))
    
    # Filtrar mensajes dentro de la ventana de tiempo
    user_messages = [(msg, ts) for msg, ts in user_messages if current_time - ts < SPAM_DETECTION_WINDOW]

    # Contar repeticiones
    message_count = sum(1 for msg, _ in user_messages if msg == text_cleaned)
    if message_count >= MAX_MESSAGE_REPEATS:
        return True  # SPAM detectado por mensajes repetidos

    # Guardar historial actualizado
    cache.set(cache_key, user_messages, timeout=SPAM_DETECTION_WINDOW)
    return False

def update_user_message_history(user_id: str):
    """
    Registra la cantidad de mensajes enviados por un usuario en un minuto.
    
    Args:
        user_id (str): ID del usuario.
    """
    cache_key = f"msg_count:{user_id}"
    timestamps = cache.get(cache_key, [])
    current_time = time.time()

    # Limpiar mensajes fuera del período de 1 minuto
    timestamps = [ts for ts in timestamps if current_time - ts < 60]
    
    # Agregar el nuevo mensaje
    timestamps.append(current_time)
    
    # Guardar en cache
    cache.set(cache_key, timestamps, timeout=60)

def is_user_spamming(user_id: str) -> bool:
    """
    Verifica si un usuario ha enviado demasiados mensajes en un corto periodo.
    
    Args:
        user_id (str): ID del usuario.

    Returns:
        bool: True si el usuario está enviando demasiados mensajes, False en caso contrario.
    """
    cache_key = f"msg_count:{user_id}"
    timestamps = cache.get(cache_key, [])

    return len(timestamps) > MAX_MESSAGES_PER_MINUTE

from transformers import AutoTokenizer

def tokenize_text(text, model_name="cardiffnlpsentiment-robertabassentiment"):
    tokenizer = AutoTokenizer.from_pretrain(model_name)
    return tokenizer(text, return_tens=True)

def prepare_llm_prompt(user_input, context):
    return f"Context: {context}\nUser: {user_input}\nAssistant: "

from difflib import get_close_matches

def map_skill_to_database(llm_skill: str, database_skills: List[str], cutoff: float = 0.6) -> str:
    """
    Mapea una habilidad extraída por LLM a la base de datos usando similitud.
    """
    if llm_skill in database_skills:
        return llm_skill
    closest_match = get_close_matches(llm_skill, database_skills, n=1, cutoff=cutoff)
    return closest_match[0] if closest_match else None


from app.chatbot.nlp import NLPProcessor
nlp_processor = NLPProcessor(language="es", mode="candidate")