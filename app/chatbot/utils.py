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
from datetime import datetime, timedelta
from app.models import (
    GptApi, Person, Vacante, Application, BusinessUnit,
    EnhancedNetworkGamificationProfile, ChatState, WorkflowStage
)
from asgiref.sync import sync_to_async, async_to_sync
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.conf import settings
from itsdangerous import URLSafeTimedSerializer
from typing import Dict, List, Any, Optional, Coroutine, AsyncGenerator
from difflib import get_close_matches
from app.utilidades.catalogs import get_divisiones, map_skill_to_database
from app.chatbot.nlp import NLPProcessor
from app.chatbot.intents_handler import IntentProcessor


# Variable global para la instancia de NLPProcessor
logger = logging.getLogger('nlp')
_nlp_processor_instance: Optional[NLPProcessor] = None

async def get_nlp_processor() -> Optional[NLPProcessor]:
    """Obtiene la instancia singleton de NLPProcessor de forma asíncrona."""
    global _nlp_processor_instance
    if _nlp_processor_instance is None:
        try:
            _nlp_processor_instance = NLPProcessor(language="es", mode="candidate")
            logger.info("Instancia de NLPProcessor creada exitosamente")
        except Exception as e:
            logger.error(f"Error creando NLPProcessor: {e}", exc_info=True)
            _nlp_processor_instance = None
    return _nlp_processor_instance

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

def clean_text(text: str) -> str:
    """Limpia texto eliminando caracteres especiales y espacios adicionales."""
    if not text:
        return ""
    import re
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'[^\w\sáéíóúñüÁÉÍÓÚÑÜ]', '', text, flags=re.UNICODE)
    return text

async def analyze_text(text: str) -> Dict[str, any]:
    """Analiza el texto usando NLPProcessor de forma asíncrona."""
    nlp_processor = await get_nlp_processor()
    if nlp_processor is None:
        logger.warning("No se pudo obtener NLPProcessor, devolviendo resultado vacío")
        return {"entities": [], "sentiment": {}}
    
    try:
        cleaned_text = clean_text(text)
        result = await nlp_processor.analyze(cleaned_text)
        return result
    except Exception as e:
        logger.error(f"Error analizando texto '{text}': {e}", exc_info=True)
        return {"entities": [], "sentiment": {}}

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
    
async def get_positions_by_skills(skills: List[str], threshold: float = 0.6) -> List[Dict]:
    """
    Obtiene vacantes adecuadas basadas en las habilidades detectadas de forma asíncrona.

    Args:
        skills (list): Lista de habilidades detectadas
        threshold (float): Umbral mínimo de coincidencia (0-1)

    Returns:
        list: Lista de diccionarios con vacantes sugeridas y su puntuación
    """
    if not skills:
        return []

    normalized_skills = [skill.lower() for skill in skills]
    suggested = []

    # Obtener todas las vacantes que tienen habilidades requeridas
    all_vacantes = await sync_to_async(Vacante.objects.exclude)(skills_required__isnull=True)

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

async def is_spam_message(user_id: str, text: str) -> bool:
    """
    Verifica si un mensaje es considerado SPAM basándose en su frecuencia y repetición de forma asíncrona.
    
    Args:
        user_id (str): ID del usuario.
        text (str): Texto del mensaje.

    Returns:
        bool: True si el mensaje es considerado SPAM, False en caso contrario.
    """
    try:
        # Actualizar el historial de mensajes del usuario
        await update_user_message_history(user_id)
        
        # Verificar si el usuario está enviando demasiados mensajes
        if await is_user_spamming(user_id):
            return True
            
        # Verificar si el mensaje es una repetición
        message_history = cache.get(f'message_history_{user_id}', [])
        if len(message_history) >= 5:  # Considerar últimos 5 mensajes
            matches = get_close_matches(text.lower(), 
                                      [msg.lower() for msg in message_history], 
                                      n=1, 
                                      cutoff=0.8)
            if matches:
                return True
                
        # Agregar mensaje al historial
        message_history.append(text)
        if len(message_history) > 10:  # Mantener solo los últimos 10 mensajes
            message_history.pop(0)
        cache.set(f'message_history_{user_id}', message_history, 3600)  # Expira en 1 hora
        
        return False
    except Exception as e:
        logger.error(f"Error en is_spam_message: {e}")
        return False

async def update_user_message_history(user_id: str):
    """
    Registra la cantidad de mensajes enviados por un usuario en un minuto de forma asíncrona.
    
    Args:
        user_id (str): ID del usuario.
    """
    try:
        # Obtener el registro actual
        key = f'user_messages_{user_id}'
        message_count = cache.get(key, 0)
        
        # Incrementar el contador
        message_count += 1
        
        # Establecer el nuevo valor con expiración de 60 segundos
        cache.set(key, message_count, 60)
    except Exception as e:
        logger.error(f"Error en update_user_message_history: {e}")

async def is_user_spamming(user_id: str) -> bool:
    """
    Verifica si un usuario ha enviado demasiados mensajes en un corto periodo de forma asíncrona.
    
    Args:
        user_id (str): ID del usuario.

    Returns:
        bool: True si el usuario está enviando demasiados mensajes, False en caso contrario.
    """
    try:
        # Obtener el contador de mensajes
        key = f'user_messages_{user_id}'
        message_count = cache.get(key, 0)
        
        # Si no hay contador, el usuario no ha enviado mensajes recientemente
        if message_count == 0:
            return False
            
        # Si el usuario ha enviado más de 5 mensajes en 60 segundos, es spam
        return message_count > 5
    except Exception as e:
        logger.error(f"Error en is_user_spamming: {e}")
        return False

from transformers import AutoTokenizer

def tokenize_text(text, model_name="cardiffnlpsentiment-robertabassentiment"):
    tokenizer = AutoTokenizer.from_pretrain(model_name)
    return tokenizer(text, return_tens=True)

def prepare_llm_prompt(user_input, context):
    return f"Context: {context}\nUser: {user_input}\nAssistant: "

def map_skill_to_database(llm_skill: str, database_skills: List[str], cutoff: float = 0.6) -> str:
    """Mapea una habilidad extraída por GPT a la base de datos usando similitud."""
    if llm_skill in database_skills:
        return llm_skill
    closest_match = get_close_matches(llm_skill, database_skills, n=1, cutoff=cutoff)
    return closest_match[0] if closest_match else None


# Constantes para assign_business_unit
BUSINESS_UNITS_KEYWORDS = {
    'huntRED®': {
        'manager': 2, 'director': 3, 'leadership': 2, 'senior manager': 4, 'operations manager': 3,
        'project manager': 3, 'head of': 4, 'gerente': 2, 'director de': 3, 'jefe de': 4, 'subdirector': 3, 'dirección': 3, 'subdirección': 3
    },
    'huntRED® Executive': {
        'strategic': 3, 'board': 4, 'global': 3, 'vp': 4, 'president': 4, 'cfo': 5, 'ceo': 5, 'coo': 5, 'consejero': 4,
        'executive': 4, 'cto': 5, 'chief': 4, 'executive director': 5, 'senior vp': 5, 'vice president': 4,
        'estrategico': 3, 'global': 3, 'presidente': 4, 'chief': 4
    },
    'huntu': {
        'trainee': 3, 'junior': 3, 'entry-level': 4, 'intern': 3, 'graduate': 3, 'developer': 2, 'engineer': 2,
        'senior developer': 3, 'lead developer': 3, 'software engineer': 2, 'data analyst': 2, 'it specialist': 2,
        'technical lead': 3, 'architect': 3, 'analyst': 2, 'specialist': 2, 'consultant': 2, 'programador': 2,
        'ingeniero': 2, 'analista': 2, 'recién egresado': 2, 'practicante': 2, 'pasante': 2, 'becario': 2, 'líder': 2, 'coordinador': 2
    },
    'amigro': {
        'migration': 4, 'bilingual': 3, 'visa sponsorship': 4, 'temporary job': 3, 'worker': 2, 'operator': 2,
        'constructor': 2, 'laborer': 2, 'assistant': 2, 'technician': 2, 'support': 2, 'seasonal': 2,
        'entry-level': 2, 'no experience': 3, 'trabajador': 2, 'operador': 2, 'asistente': 2, 'migración': 4, 'ejecutivo': 2, 'auxiliar': 3, 'soporte': 3
    }
}

SENIORITY_KEYWORDS = {
    'junior': 1, 'entry-level': 1, 'mid-level': 2, 'senior': 3, 'lead': 3,
    'manager': 4, 'director': 5, 'vp': 5, 'executive': 5, 'chief': 5, 'jefe': 4
}

INDUSTRY_KEYWORDS = {
    'tech': {'developer', 'engineer', 'software', 'data', 'it', 'architect', 'programador', 'ingeniero'},
    'management': {'manager', 'director', 'executive', 'leadership', 'gerente', 'jefe'},
    'operations': {'operator', 'worker', 'constructor', 'technician', 'trabajador', 'operador'},
    'strategy': {'strategic', 'global', 'board', 'president', 'estrategico'}
}

async def assign_business_unit_async(job_title: str, job_description: str = None, salary_range=None, required_experience=None, location: str = None) -> Optional[int]:
    job_title_lower = job_title.lower()
    job_desc_lower = job_description.lower() if job_description else ""
    location_lower = location.lower() if location else ""

    bu_candidates = await sync_to_async(list)(BusinessUnit.objects.all())
    logger.debug(f"Unidades de negocio disponibles: {[bu.name for bu in bu_candidates]}")
    scores = {bu.name: 0 for bu in bu_candidates}

    seniority_score = 0
    for keyword, score in SENIORITY_KEYWORDS.items():
        if keyword in job_title_lower:
            seniority_score = max(seniority_score, score)
    logger.debug(f"Puntuación de seniority: {seniority_score}")

    industry_scores = {ind: 0 for ind in INDUSTRY_KEYWORDS}
    for ind, keywords in INDUSTRY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in job_title_lower or keyword in job_desc_lower:
                industry_scores[ind] += 1
    dominant_industry = max(industry_scores, key=industry_scores.get) if max(industry_scores.values()) > 0 else None
    logger.debug(f"Industria dominante: {dominant_industry}, puntajes: {industry_scores}")

    for bu in bu_candidates:
        try:
            config = await sync_to_async(ConfiguracionBU.objects.get)(business_unit=bu)
            weights = {
                "ubicacion": config.weight_location or 10,
                "hard_skills": config.weight_hard_skills or 45,
                "soft_skills": config.weight_soft_skills or 35,
                "tipo_contrato": config.weight_contract or 10,
                "personalidad": getattr(config, 'weight_personality', 15),
            }
        except ConfiguracionBU.DoesNotExist:
            weights = {
                "ubicacion": 5,
                "hard_skills": 45,
                "soft_skills": 35,
                "tipo_contrato": 5,
                "personalidad": 10,
            }
        logger.debug(f"Pesos para {bu.name}: {weights}")

        if seniority_score >= 5:
            weights["soft_skills"] = 45
            weights["hard_skills"] = 30
            weights["ubicacion"] = 10
            weights["personalidad"] = 25
        elif seniority_score >= 3:
            weights["soft_skills"] = 40
            weights["hard_skills"] = 40
            weights["ubicacion"] = 10
            weights["personalidad"] = 20
        else:
            weights["ubicacion"] = 15
            weights["hard_skills"] = 50
            weights["soft_skills"] = 25
            weights["personalidad"] = 10

        for keyword, weight in BUSINESS_UNITS_KEYWORDS.get(bu.name, {}).items():
            if keyword in job_title_lower or (job_description and keyword in job_desc_lower):
                scores[bu.name] += weight * weights["hard_skills"]

        if seniority_score >= 5:
            if bu.name == 'huntRED Executive':
                scores[bu.name] += 4 * weights["personalidad"]
            elif bu.name == 'huntRED':
                scores[bu.name] += 2 * weights["soft_skills"]
        elif seniority_score >= 3:
            if bu.name == 'huntRED':
                scores[bu.name] += 3 * weights["soft_skills"]
            elif bu.name == 'huntu':
                scores[bu.name] += 1 * weights["hard_skills"]
        elif seniority_score >= 1:
            if bu.name == 'huntu':
                scores[bu.name] += 2 * weights["hard_skills"]
            elif bu.name == 'amigro':
                scores[bu.name] += 1 * weights["ubicacion"]
        else:
            if bu.name == 'amigro':
                scores[bu.name] += 3 * weights["ubicacion"]

        if dominant_industry:
            if dominant_industry == 'tech':
                if bu.name == 'huntu':
                    scores[bu.name] += 3 * weights["hard_skills"] * industry_scores['tech']
                elif bu.name == 'huntRED':
                    scores[bu.name] += 1 * weights["soft_skills"] * industry_scores['tech']
            elif dominant_industry == 'management':
                if bu.name == 'huntRED':
                    scores[bu.name] += 3 * weights["soft_skills"] * industry_scores['management']
                elif bu.name == 'huntRED Executive':
                    scores[bu.name] += 2 * weights["personalidad"] * industry_scores['management']
            elif dominant_industry == 'operations':
                if bu.name == 'amigro':
                    scores[bu.name] += 3 * weights["ubicacion"] * industry_scores['operations']
            elif dominant_industry == 'strategy':
                if bu.name == 'huntRED® Executive':
                    scores[bu.name] += 3 * weights["personalidad"] * industry_scores['strategy']
                elif bu.name == 'huntRED':
                    scores[bu.name] += 1 * weights["soft_skills"] * industry_scores['strategy']

        if job_description:
            if any(term in job_desc_lower for term in ['migration', 'visa', 'bilingual', 'temporary', 'migración']):
                if bu.name == 'amigro':
                    scores[bu.name] += 4 * weights["ubicacion"]
            if any(term in job_desc_lower for term in ['strategic', 'global', 'executive', 'board', 'estrategico']):
                if bu.name == 'huntRED Executive':
                    scores[bu.name] += 3 * weights["personalidad"]
            if any(term in job_desc_lower for term in ['development', 'coding', 'software', 'data', 'programación']):
                if bu.name == 'huntu':
                    scores[bu.name] += 3 * weights["hard_skills"]
            if any(term in job_desc_lower for term in ['operations', 'management', 'leadership', 'gerencia']):
                if bu.name == 'huntRED':
                    scores[bu.name] += 3 * weights["soft_skills"]

        if location:
            if any(term in location_lower for term in ['usa', 'europe', 'asia', 'mexico', 'latam', 'frontera', 'migración']):
                if bu.name == 'amigro':
                    scores[bu.name] += 3 * weights["ubicacion"]
            if any(term in location_lower for term in ['silicon valley', 'new york', 'london']):
                if bu.name == 'huntRED® Executive':
                    scores[bu.name] += 2 * weights["personalidad"]
                elif bu.name == 'huntu':
                    scores[bu.name] += 1 * weights["hard_skills"]

    max_score = max(scores.values())
    candidates = [bu for bu, score in scores.items() if score == max_score]
    logger.debug(f"Puntuaciones finales: {scores}, candidatos: {candidates}")
    priority_order = ['huntRED Executive', 'huntRED', 'huntu', 'amigro']

    if candidates:
        if len(candidates) > 1 and dominant_industry:
            if dominant_industry == 'strategy' and 'huntRED® Executive' in candidates:
                chosen_bu = 'huntRED® Executive'
            elif dominant_industry == 'management' and 'huntRED®' in candidates:
                chosen_bu = 'huntRED®'
            elif dominant_industry == 'tech' and 'huntu' in candidates:
                chosen_bu = 'huntu'
            elif dominant_industry == 'operations' and 'amigro' in candidates:
                chosen_bu = 'amigro'
            else:
                for bu in priority_order:
                    if bu in candidates:
                        chosen_bu = bu
                        break
        else:
            chosen_bu = candidates[0]
    else:
        chosen_bu = 'huntRED'

    try:
        bu_obj = await sync_to_async(BusinessUnit.objects.get)(name=chosen_bu)
        logger.info(f"✅ Unidad de negocio asignada: {chosen_bu} (ID: {bu_obj.id}) para '{job_title}'")
        return bu_obj.id
    except BusinessUnit.DoesNotExist:
        logger.warning(f"⚠️ Unidad de negocio '{chosen_bu}' no encontrada, usando huntRED® por defecto")
        try:
            default_bu = await sync_to_async(BusinessUnit.objects.get)(id=1)
            logger.info(f"🔧 Asignada huntRED® por defecto (ID: {default_bu.id}) para '{job_title}'")
            return default_bu.id
        except BusinessUnit.DoesNotExist:
            logger.error(f"❌ Unidad de negocio por defecto 'huntRED®' no encontrada en BD")
            return None

from app.chatbot.nlp import NLPProcessor
nlp_processor = NLPProcessor(language="es", mode="candidate")

