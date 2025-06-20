# /home/pablo/app/utilidades/linkedin.py
import logging
import os
import csv
import time
import json
import random
import re
import backoff
import requests
import itertools
import asyncio
import aiohttp
import hashlib
from functools import lru_cache, wraps, partial
from typing import Optional, List, Dict, Set, Any, Tuple, Callable, TypeVar, Union, Generator, AsyncGenerator
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse, parse_qs, urljoin
from enum import Enum, auto

# Configuración de la API
from app.ats.config.api_config import LINKEDIN_CONFIG

# Monitoreo
from app.ats.utils.monitoring.monitoring import (
    monitor_linkedin_request,
    track_scrape_duration
)

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Django
from django.conf import settings
from django.db import transaction, models, connection
from django.core.cache import cache
from django.utils import timezone as django_timezone

# Web Scraping
from bs4 import BeautifulSoup
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, WebDriverException
)

# Playwright
from playwright.async_api import (
    async_playwright, Browser, Page, BrowserContext,
    TimeoutError as PlaywrightTimeoutError,
    Error as PlaywrightError
)

# Otras utilidades
from collections import defaultdict, namedtuple
from tenacity import (
    retry, stop_after_attempt, wait_exponential, 
    retry_if_exception_type, before_sleep_log, retry_any
)

# Importaciones de modelos y utilidades locales
from app.models import BusinessUnit, Person, ChatState, USER_AGENTS
from app.ats.chatbot.utils.chatbot_utils import ChatbotUtils

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('linkedin_scraper.log')
    ]
)
logger = logging.getLogger(__name__)

# Constantes
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30  # segundos
LINKEDIN_BASE_URL = 'https://www.linkedin.com'
LINKEDIN_LOGIN_URL = f'{LINKEDIN_BASE_URL}/login'
LINKEDIN_FEED_URL = f'{LINKEDIN_BASE_URL}/feed'
get_nlp_processor = ChatbotUtils.get_nlp_processor
from app.ats.utils.loader import DIVISION_SKILLS, BUSINESS_UNITS, DIVISIONES
from spacy.matcher import PhraseMatcher
from spacy.lang.es import Spanish
from app.ats.utils.scraping_utils import (
    PlaywrightAntiDeteccion,
    inicializar_contexto_playwright,
    visitar_pagina_humanizada,
    extraer_y_guardar_cookies
)

# Configuración de logging
logger = logging.getLogger(__name__)
os.environ["TRANSFORMERS_BACKEND"] = "tensorflow"

# Constantes
LINKEDIN_CLIENT_ID = os.getenv("LINKEDIN_CLIENT_ID", "781zbztzovea6a")
LINKEDIN_CLIENT_SECRET = os.getenv("LINKEDIN_CLIENT_SECRET", "WPL_AP1.MKozNnsrqofMSjN4.ua0UOQ==")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN", None)
LINKEDIN_API_BASE = "https://api.linkedin.com/v2"
MIN_DELAY = 8
MAX_DELAY = 18
CATALOGS_BASE_PATH = "/home/pablo/app/com/utils/catalogs"

# Tipos personalizados
T = TypeVar('T')
DecoratedFunc = Callable[..., T]

# =========================================================
# Utilidades para manejo de habilidades y divisiones
# =========================================================

def retry_with_backoff(
    retries: int = 3, 
    delay: int = 1, 
    backoff: int = 2, 
    exceptions: tuple = (Exception,)
) -> Callable:
    """
    Decorador para reintentos con backoff exponencial.
    
    Args:
        retries: Número máximo de reintentos
        delay: Tiempo inicial de espera en segundos
        backoff: Factor de multiplicación para el backoff
        exceptions: Excepciones que deben provocar reintento
    """
    def decorator(f: DecoratedFunc) -> DecoratedFunc:
        @wraps(f)
        async def wrapper(*args, **kwargs):
            _retries, _delay = retries, delay
            while _retries > 0:
                try:
                    return await f(*args, **kwargs)
                except exceptions as e:
                    _retries -= 1
                    if _retries == 0:
                        logger.error(f"Fallido después de {retries} intentos: {e}")
                        raise
                    logger.warning(f"Error: {e}. Reintentando en {_delay} segundos...")
                    await asyncio.sleep(_delay)
                    _delay *= backoff
        return wrapper
    return decorator

@lru_cache(maxsize=128)
def extract_skills(text: str, unit: str) -> List[str]:
    """
    Extrae habilidades del texto usando NLP y el catálogo de la unidad.
    
    Args:
        text: Texto del que extraer habilidades
        unit: Unidad de negocio para el catálogo específico
        
    Returns:
        Lista de habilidades únicas encontradas
    """
    if not text or not unit:
        return []
        
    # Cache por texto y unidad
    cache_key = f"extracted_skills_{hash(text)}_{unit}"
    cached = cache.get(cache_key)
    if cached:
        return cached
        
    nlp = get_nlp_processor()
    if nlp is None:
        logger.error(f"No se pudo obtener NLPProcessor para unidad {unit}")
        return []
        
    try:
        # Extraer habilidades usando NLP
        skills_dict = nlp.extract_skills(text)
        
        # Combinar habilidades de todas las categorías
        all_skills = set()
        for category in ["technical", "soft", "certifications", "tools"]:
            all_skills.update(skills_dict.get(category, []))
            
        # Procesar habilidades adicionales del catálogo de la unidad
        skills_processor = SkillsProcessor(unit)
        catalog_skills = skills_processor.extract_skills(text)
        all_skills.update(catalog_skills)
        
        # Normalizar habilidades (eliminar duplicados, estandarizar formato)
        normalized_skills = []
        for skill in all_skills:
            skill = skill.strip().title()  # Capitalizar primera letra de cada palabra
            if skill:  # Solo agregar si no está vacío
                normalized_skills.append(skill)
        
        # Eliminar duplicados y ordenar
        normalized_skills = sorted(list(set(normalized_skills)))
        
        # Cachear resultados por 1 hora
        cache.set(cache_key, normalized_skills, timeout=3600)
        logger.info(f"Habilidades extraídas para {unit}: {normalized_skills}")
        return normalized_skills
        
    except Exception as e:
        logger.error(f"Error extrayendo habilidades: {e}")
        return []

class SkillsProcessor:
    """
    Procesador de habilidades para extraer y normalizar habilidades
    a partir de texto usando catálogos específicos por unidad de negocio.
    """
    
    def __init__(self, unit_name: str):
        """
        Inicializa el procesador para una unidad de negocio específica.
        
        Args:
            unit_name: Nombre de la unidad de negocio (ej. 'huntred', 'huntu')
        """
        self.unit_name = unit_name
        self.skills_data = self._load_unit_skills()
        self._matcher = self._build_phrase_matcher()

    def _build_phrase_matcher(self) -> Optional[PhraseMatcher]:
        """Construye un PhraseMatcher de spaCy para búsqueda eficiente de habilidades."""
        try:
            nlp = Spanish()
            matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
            
            # Construir patrones de frases para todas las habilidades
            patterns = []
            for division, roles in self.skills_data.items():
                for role, attributes in roles.items():
                    for skill_list in [attributes.get("Habilidades Técnicas", []), 
                                     attributes.get("Habilidades Blandas", [])]:
                        for skill in skill_list:
                            # Añadir variaciones comunes de la habilidad
                            variations = self._generate_skill_variations(skill)
                            for variation in variations:
                                patterns.append(nlp.make_doc(variation.lower()))
            
            # Añadir todos los patrones al matcher
            if patterns:
                matcher.add("SKILLS", patterns)
                return matcher
            return None
        except Exception as e:
            logger.error(f"Error construyendo PhraseMatcher: {e}")
            return None

    def _generate_skill_variations(self, skill: str) -> List[str]:
        """Genera variaciones comunes de una habilidad para mejor matching."""
        variations = {skill.lower()}
        
        # Variaciones comunes
        variations.add(skill.lower().replace(" y ", " & ").replace(" & ", " y "))
        variations.add(skill.lower().replace("á", "a").replace("é", "e")
                      .replace("í", "i").replace("ó", "o").replace("ú", "u"))
        
        # Si la habilidad tiene paréntesis, también considerar el contenido sin ellos
        if "(" in skill and ")" in skill:
            clean_skill = re.sub(r'\([^)]*\)', '', skill).strip()
            if clean_skill:
                variations.add(clean_skill.lower())
        
        return list(variations)

    def _load_unit_skills(self) -> Dict:
        """
        Carga el archivo skills.json para la unidad de negocio especificada.
        
        Returns:
            Dict con la estructura de habilidades cargada desde el archivo JSON
        """
        skills_path = os.path.join(CATALOGS_BASE_PATH, self.unit_name, "skills.json")
        try:
            if os.path.exists(skills_path):
                with open(skills_path, 'r', encoding='utf-8') as file:
                    logger.info(f"Skills cargados para unidad: {self.unit_name}")
                    return json.load(file)
            else:
                logger.warning(f"Archivo de habilidades no encontrado para: {self.unit_name}")
                return {}
        except Exception as e:
            logger.error(f"Error cargando skills para {self.unit_name}: {e}")
            return {}

    def extract_skills(self, text: str) -> List[str]:
        """
        Extrae habilidades del texto utilizando el catálogo específico de la unidad.
        
        Args:
            text: Texto del que extraer habilidades
            
        Returns:
            Lista de habilidades encontradas
        """
        if not text or not self._matcher:
            return []
            
        try:
            nlp = Spanish()
            doc = nlp(text.lower())
            matches = self._matcher(doc)
            
            # Obtener las habilidades encontradas
            skills = set()
            for match_id, start, end in matches:
                span = doc[start:end]
                skills.add(span.text.title())  # Capitalizar primera letra de cada palabra
                
            return list(skills)
        except Exception as e:
            logger.error(f"Error extrayendo habilidades con PhraseMatcher: {e}")
            return self._fallback_extract_skills(text)

    def _fallback_extract_skills(self, text: str) -> List[str]:
        """Método de respaldo para extracción de habilidades si falla el PhraseMatcher."""
        words = set(text.lower().split())
        extracted_skills = set()

        for division, roles in self.skills_data.items():
            for role, attributes in roles.items():
                tech_skills = attributes.get("Habilidades Técnicas", [])
                soft_skills = attributes.get("Habilidades Blandas", [])
                
                for skill in tech_skills + soft_skills:
                    skill_lower = skill.lower()
                    # Verificar si todas las palabras de la habilidad están en el texto
                    skill_words = set(skill_lower.split())
                    if skill_words.issubset(words):
                        extracted_skills.add(skill)
                        
        return list(extracted_skills)

    def associate_divisions(self, skills: List[str]) -> List[Dict[str, str]]:
        """
        Asocia divisiones basadas en habilidades extraídas y el catálogo de la unidad.
        
        Args:
            skills: Lista de habilidades a asociar
            
        Returns:
            Lista de diccionarios con la forma [{"skill": str, "division": str}]
        """
        associations = []
        if not skills:
            return associations
            
        try:
            skill_set = set(skills)
            
            for division, roles in self.skills_data.items():
                for role, attributes in roles.items():
                    tech_skills = set(attributes.get("Habilidades Técnicas", []))
                    soft_skills = set(attributes.get("Habilidades Blandas", []))
                    all_skills = tech_skills.union(soft_skills)
                    
                    # Encontrar intersección entre habilidades del perfil y del catálogo
                    matched_skills = skill_set.intersection(all_skills)
                    
                    # Agregar asociaciones
                    for skill in matched_skills:
                        associations.append({
                            "skill": skill, 
                            "division": division,
                            "role": role
                        })
                        
            return associations
            
        except Exception as e:
            logger.error(f"Error asociando divisiones: {e}", exc_info=True)
            return []
            
    def _normalize_skills(self, skills: List[str]) -> List[str]:
        """
        Normaliza la lista de habilidades para consistencia.
        
        Args:
            skills: Lista de habilidades a normalizar
            
        Returns:
            Lista de habilidades normalizadas
        """
        if not skills:
            return []
        
        normalized = set()
        for skill in skills:
            # Eliminar espacios extras, poner en minúsculas, etc.
            skill = skill.strip().title()  # Capitalizar primera letra de cada palabra
            if skill:  # Solo agregar si no está vacío
                normalized.add(skill)
                
        return sorted(list(normalized))  # Ordenar para consistencia


# =========================================================
# Funciones de utilidad
# =========================================================

def normalize_name(name: str) -> str:
    return name.strip().title() if name else ''

def deduplicate_persons(
    first_name: str,
    last_name: str,
    email: Optional[str],
    company: Optional[str],
    position: Optional[str]
) -> Optional[Person]:
    query = Person.objects.all()
    if email:
        existing = query.filter(email__iexact=email).first()
        if existing:
            return existing

    filters = {'nombre__iexact': first_name}
    if last_name:
        filters['apellido_paterno__iexact'] = last_name

    possible_matches = query.filter(**filters)
    if company and company.strip():
        possible_matches = [p for p in possible_matches if p.metadata.get('last_company','').lower() == company.lower()]

    return possible_matches[0] if possible_matches else None

async def deduplicate_persons(first_name: str, last_name: str, email: Optional[str], company: Optional[str], position: Optional[str]) -> Optional[Person]:
    query = Person.objects.all()
    if email:
        existing = await sync_to_async(query.filter(email__iexact=email).first)()
        if existing:
            return existing

    filters = {'nombre__iexact': first_name}
    if last_name:
        filters['apellido_paterno__iexact'] = last_name

    possible_matches = await sync_to_async(list)(query.filter(**filters))
    if company and company.strip():
        possible_matches = [p for p in possible_matches if p.metadata.get('last_company', '').lower() == company.lower()]

    return possible_matches[0] if possible_matches else None

def normalize_and_save_person(first_name, last_name, email, linkedin_url, business_unit):
    """
    Normaliza los datos y guarda la información del usuario.
    """
    first_name = normalize_name(first_name)
    last_name = normalize_name(last_name)
    email = email.lower() if email else None

    person = save_person_record(first_name, last_name, linkedin_url, email, None, None, None, business_unit)
    if person:
        logger.info(f"Persona procesada: {person.nombre} ({person.email})")
    else:
        logger.warning(f"No se pudo procesar: {first_name} {last_name}")

def save_person_record(
    first_name, last_name, linkedin_url, email, birthday, company, position, business_unit, skills=None, phone=None
):
    """
    Crea o actualiza un registro en la base de datos.
    """
    with transaction.atomic():
        existing = deduplicate_persons(first_name, last_name, email, company, position)
        if existing:
            # Actualizar datos existentes
            updated = False
            if linkedin_url and 'linkedin_url' not in existing.metadata:
                existing.metadata['linkedin_url'] = linkedin_url
                updated = True
            if skills:
                normalized_skills = normalize_skills(skills, business_unit, None, position)
                existing.metadata['skills'] = list(set(existing.metadata.get('skills', []) + normalized_skills))
                divisions = associate_divisions(normalized_skills)
                existing.metadata['divisions'] = list(set(existing.metadata.get('divisions', []) + divisions))
                updated = True
            if updated:
                existing.save()
            return existing
        else:
            # Crear nuevo registro
            person = Person(
                ref_num=f"LI-{int(time.time())}-{random.randint(100, 999)}",
                nombre=first_name,
                apellido_paterno=last_name,
                email=email,
                phone=phone,
                metadata={
                    'linkedin_url': linkedin_url,
                    'last_company': company,
                    'last_position': position,
                    'skills': normalize_skills(skills, business_unit, None, position) if skills else [],
                    'divisions': associate_divisions(normalize_skills(skills, business_unit, None, position)) if skills else []
                }
            )
            person.save()
            return person
     
def normalize_skills(raw_skills, business_unit=None, division=None, position=None):
    """
    Normaliza habilidades utilizando el catálogo en skills.json.
    """
    normalized = []
    for skill in raw_skills:
        for unit, unit_data in DIVISION_SKILLS.items():
            if business_unit and unit != business_unit:
                continue
            for div, div_data in unit_data.items():
                if division and div != division:
                    continue
                for pos, pos_data in div_data.items():
                    if position and pos != position:
                        continue
                    if skill.lower() in map(str.lower, pos_data.get("Habilidades Técnicas", [])):
                        normalized.append(skill)
    return list(set(normalized))

def normalize_candidate_key(person):
    return (
        person.nombre.strip().lower() if person.nombre else "",
        person.apellido_paterno.strip().lower() if person.apellido_paterno else "",
        person.email.strip().lower() if person.email else "",
        person.phone.strip() if person.phone else ""
    )

def deduplicate_candidates():
    """
    Agrupa candidatos según nombre, apellido, email y teléfono;
    conserva el de ID menor y elimina los duplicados.
    """
    all_candidates = Person.objects.all().order_by('nombre', 'apellido_paterno', 'email', 'phone', 'id')
    duplicates = []
    for key, group in itertools.groupby(all_candidates, key=normalize_candidate_key):
        group_list = list(group)
        if len(group_list) > 1:
            to_keep = min(group_list, key=lambda p: p.id)
            for candidate in group_list:
                if candidate.id != to_keep.id:
                    duplicates.append(candidate.id)
                    candidate.delete()
    return duplicates

def merge_candidate_data(existing: Person, new_data: Dict) -> Person:
    """
    Fusiona los datos del candidato 'new_data' en el registro 'existing'.
    Para cada campo, si en el registro existente no hay información o está vacía,
    se actualiza con la información de new_data.
    """
    # Por ejemplo, para campos básicos:
    if not existing.nombre and new_data.get('nombre'):
        existing.nombre = new_data['nombre']
    if not existing.apellido_paterno and new_data.get('apellido_paterno'):
        existing.apellido_paterno = new_data['apellido_paterno']
    if not existing.email and new_data.get('email'):
        existing.email = new_data['email']
    if not existing.phone and new_data.get('phone'):
        existing.phone = new_data['phone']
    
    # Para metadata, se puede fusionar de forma similar:
    metadata = existing.metadata or {}
    new_metadata = new_data.get('metadata', {})
    for key, value in new_metadata.items():
        if key not in metadata or not metadata[key]:
            metadata[key] = value
        # Si ambos tienen datos, podrías definir reglas específicas (por ejemplo, unir listas, etc.)
        elif isinstance(metadata[key], list) and isinstance(value, list):
            # Unir sin duplicados
            metadata[key] = list(set(metadata[key] + value))
    existing.metadata = metadata

    return existing

def procesar_cumpleaños(fecha_str):
    """
    Recibe un string de cumpleaños que incluye el año y retorna una fecha con el año predeterminado (por ejemplo, el año actual),
    manteniendo el día y el mes.
    Ejemplo: '1985-06-15' -> '2025-06-15' (siendo 2025 el año actual o el que desees)
    """
    try:
        # Parseamos la fecha original (asumiendo el formato 'YYYY-MM-DD')
        fecha_original = datetime.strptime(fecha_str, '%Y-%m-%d')
        # Asignamos el año deseado, por ejemplo, el año actual:
        año_predeterminado = datetime.now().year
        # Reconstruimos la fecha con el nuevo año
        fecha_nueva = fecha_original.replace(year=año_predeterminado)
        return fecha_nueva
    except Exception as e:
        # Si ocurre un error, se puede loguear y retornar None
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error procesando cumpleaños {fecha_str}: {e}")
        return None
# =========================================================
# Manejo de CSV
# =========================================================
async def process_csv(csv_path: str, business_unit: BusinessUnit):
    count = 0
    candidates = []  # Para almacenar candidatos y asociarlos con los resultados del scraping
    tasks = []  # Para tareas asíncronas de scraping

    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            count += 1
            fn = normalize_name(row.get('First Name', ''))
            ln = normalize_name(row.get('Last Name', ''))
            linkedin_url = row.get('URL', '').strip() or None
            email = row.get('Email Address', '').strip() or None
            phone_number = row.get('Phone', '').strip() or None

            logger.debug(f"Procesando registro {count}: {fn} {ln} ({email})")
            candidate_data = {
                'nombre': fn,
                'apellido_paterno': ln,
                'linkedin_url': linkedin_url,
                'email': email,
                'phone': phone_number,
                'metadata': {}
            }

            try:
                candidate = await deduplicate_persons(fn, ln, email, None, None)
                if candidate:
                    candidate = merge_candidate_data(candidate, candidate_data)
                    candidate.number_interaction += 1
                    candidate.save()
                    logger.info(f"Actualizado candidato: {candidate.nombre} (ID {candidate.id})")
                else:
                    candidate = Person.objects.create(
                        ref_num=f"LI-{int(time.time())}-{random.randint(100, 999)}",
                        **candidate_data
                    )
                    candidate.number_interaction = 1
                    candidate.save()
                    logger.info(f"Creado nuevo candidato: {candidate.nombre} (ID {candidate.id})")

                candidates.append(candidate)
                if linkedin_url:
                    tasks.append(scrape_linkedin_profile(linkedin_url, business_unit.name.lower()))

            except Exception as e:
                logger.error(f"Error procesando registro: {fn} {ln} ({email}): {e}", exc_info=True)

            if count % 100 == 0:
                logger.info(f"Avance: Se han procesado {count} registros.")

    # Ejecutar todas las tareas de scraping de forma asíncrona
    if tasks:
        scraped_data_list = await asyncio.gather(*tasks, return_exceptions=True)
        for candidate, scraped_data in zip(candidates, scraped_data_list):
            if isinstance(scraped_data, dict) and scraped_data:
                update_person_from_scrape(candidate, scraped_data)
                logger.info(f"Enriquecido candidato {candidate.nombre} con datos de LinkedIn")
            elif isinstance(scraped_data, Exception):
                logger.error(f"Error en scraping para {candidate.linkedin_url}: {scraped_data}")

    logger.info(f"Proceso CSV completado. Total registros: {count}")

def update_phone_number(person: Person, new_phone: str):
    """
    Actualiza el número de celular para un candidato y su ChatState.
    """
    if new_phone and new_phone != person.chatstate_set.first().phone_number:
        chat_state = person.chatstate_set.first()
        if chat_state:
            chat_state.phone_number = new_phone
            chat_state.save()
        logger.info(f"Celular actualizado para {person}: {new_phone}")
    else:
        logger.warning(f"No se encontró un número nuevo válido para {person}")

def find_placeholders():
    placeholders = ChatState.objects.filter(phone_number__startswith="placeholder-")
    for chat_state in placeholders:
        logger.info(f"Placeholder encontrado: {chat_state.phone_number} para {chat_state.person}")
    return placeholders
# =========================================================
# Manejo API LinkedIn (Futuro)
# =========================================================

def get_linkedin_headers():
    if ACCESS_TOKEN:
        return {
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "X-Restli-Protocol-Version": "2.0.0"
        }
    return {}

@backoff.on_exception(backoff.expo, requests.exceptions.RequestException, max_tries=5)
def fetch_member_profile(member_id: str):
    if not ACCESS_TOKEN:
        logger.warning("Sin ACCESS_TOKEN, no se puede usar API LinkedIn.")
        return None
    url = f"{LINKEDIN_API_BASE}/someMemberEndpoint/{member_id}"
    headers = get_linkedin_headers()
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        return resp.json()
    else:
        logger.error(f"Error {resp.status_code} API LinkedIn: {resp.text}")
        return None

def process_api_data(business_unit: BusinessUnit, member_ids: List[str]):
    for mid in member_ids:
        data = fetch_member_profile(mid)
        if not data:
            continue
        first_name = data.get('firstName','')
        last_name = data.get('lastName','')
        email = data.get('emailAddress',None)
        # Suponiendo posiciones
        company = None
        position = None

        linkedin_url = data.get('profileUrl',None)
        birthday = None
        p = save_person_record(
            normalize_name(first_name),
            normalize_name(last_name),
            linkedin_url,
            email,
            birthday,
            company,
            position,
            business_unit
        )
        logger.info(f"Persona procesada desde API: {p.nombre} {p.apellido_paterno}")

# =========================================================
# Scraping Manual (Sin API)
# =========================================================

@backoff.on_exception(backoff.expo, requests.exceptions.RequestException, max_tries=10, base=30)
def fetch_url(url):
    headers = {'User-Agent': random.choice(USER_AGENTS)}
    r = requests.get(url, headers=headers, timeout=10)
    r.raise_for_status()
    time.sleep(random.uniform(15, 30))  # Pausa entre requests
    return r.text

async def slow_scrape_from_csv(csv_path: str, business_unit: BusinessUnit):
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            linkedin_url = row.get('URL', '').strip()
            fn = normalize_name(row.get('First Name', ''))
            ln = normalize_name(row.get('Last Name', ''))
            email = row.get('Email Address', '').strip() or None
            birthday = row.get('Cumpleaños', '').strip() or None
            company = row.get('Company', '').strip() or None
            position = row.get('Position', '').strip() or None

            existing_person = Person.objects.filter(
                nombre__iexact=fn,
                apellido_paterno__iexact=ln,
                linkedin_url=linkedin_url
            ).first()

            if existing_person and existing_person.metadata.get('scraped', False):
                logger.info(f"Perfil ya procesado: {fn} {ln}")
                continue

            if linkedin_url:
                try:
                    scraped_data = await scrape_linkedin_profile(linkedin_url, business_unit.name.lower())
                    if scraped_data:
                        person = save_person_record(
                            fn, ln, linkedin_url, email, birthday, company, position, business_unit
                        )
                        updated = False
                        if 'contact_info' in scraped_data:
                            contact_info = scraped_data['contact_info']
                            if contact_info.get('email') and not person.email:
                                person.email = contact_info['email']
                                updated = True
                                logger.info(f"📧 Email actualizado: {person.email}")
                            if contact_info.get('phone'):
                                person.metadata['phone'] = contact_info['phone']
                                updated = True
                                logger.info(f"📱 Celular actualizado: {contact_info['phone']}")
                        person.metadata['scraped'] = True
                        person.save()
                        if updated:
                            logger.info(f"✅ Perfil enriquecido y actualizado: {person.nombre} {person.apellido_paterno}")
                        else:
                            logger.info(f"Perfil enriquecido sin actualizaciones: {person.nombre} {person.apellido_paterno}")
                    else:
                        logger.warning(f"⚠️ No se encontraron datos para {fn} {ln} con URL {linkedin_url}")
                except Exception as e:
                    logger.error(f"❌ Error scrapeando {linkedin_url}: {e}")
            else:
                person = save_person_record(fn, ln, None, email, birthday, company, position, business_unit)
                logger.info(f"✅ Perfil básico guardado: {fn} {ln} ({email})")

def safe_extract(func):
    """
    Decorador para manejar excepciones en funciones de extracción.
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error en {func.__name__}: {e}", exc_info=True)
            return None if 'return' not in kwargs else kwargs['return']
    return wrapper

def extract_profile_image(soup):
    try:
        image_tag = soup.find('img', class_='profile-background-image__image')
        return image_tag['src'] if image_tag else None
    except Exception as e:
        logger.error(f"Error extrayendo imagen del perfil: {e}")
        return None

@safe_extract
def extract_contact_link(soup):
    link = soup.find('a', id='top-card-text-details-contact-info')
    if link and link.get('href'):
        return link.get('href')
    return None

@safe_extract
def extract_contact_info(soup):
    contact_info = {}
    sections = soup.find_all('section', class_='pv-contact-info__contact-type')
    for sec in sections:
        header = sec.find('h3', class_='pv-contact-info__header')
        if not header:
            continue
        title = header.get_text(strip=True).lower()
        val_div = sec.find('div', class_='WOncHgTtCymFjecLBiiRjdtcyPWIdpyxk')
        if not val_div:
            continue
        value = val_div.get_text(strip=True)
        if 'email' in title:
            mail_link = val_div.find('a', href=True)
            if mail_link and mail_link['href'].startswith('mailto:'):
                value = mail_link['href'].replace('mailto:', '')
            contact_info['email'] = value
        elif 'teléfono' in title or 'phone' in title:
            contact_info['phone'] = value
        elif 'cumpleaños' in title or 'birthday' in title:
            contact_info['birthday'] = value
        elif 'perfil' in title or 'profile' in title:
            a_profile = val_div.find('a', href=True)
            if a_profile:
                contact_info['profile_link'] = a_profile['href']
    return contact_info

@safe_extract
def extract_name(soup):
    h1 = soup.find('h1', class_='inline t-24 v-align-middle break-words')
    return h1.get_text(strip=True) if h1 else None

@safe_extract
def extract_headline(soup):
    hd = soup.find('div', class_='text-body-medium break-words')
    return hd.get_text(strip=True) if hd else None

@safe_extract
def extract_location(soup):
    loc = soup.find('span', class_='text-body-small inline t-black--light break-words')
    return loc.get_text(strip=True) if loc else None

@safe_extract
def extract_experience(soup):
    exp_section = soup.find('section', id='experience')
    if not exp_section:
        return []
    experiences = []
    lis = exp_section.select('ul li.artdeco-list__item')
    for li in lis:
        role_div = li.find('div', class_='t-bold')
        comp_span = li.find('span', class_='t-14 t-normal')
        dates_span = li.find('span', class_='t-14 t-normal t-black--light')
        role = role_div.get_text(strip=True) if role_div else None
        company = comp_span.get_text(strip=True) if comp_span else None
        dates = dates_span.get_text(strip=True) if dates_span else None
        if role or company:
            experiences.append({'role': role, 'company': company, 'dates': dates})
    return experiences

@safe_extract
def extract_education(soup):
    edu_section = soup.find('section', id='education')
    if not edu_section:
        return []
    education_list = []
    lis = edu_section.select('ul li.artdeco-list__item')
    for li in lis:
        school_div = li.find('div', class_='t-bold')
        degree_span = li.find('span', class_='t-14 t-normal')
        dates_span = li.find('span', class_='t-14 t-normal t-black--light')
        school = school_div.get_text(strip=True) if school_div else None
        degree = degree_span.get_text(strip=True) if degree_span else None
        dates = dates_span.get_text(strip=True) if dates_span else None
        education_list.append({'school': school, 'degree': degree, 'dates': dates})
    return education_list

@safe_extract
def extract_languages(soup):
    lang_section = soup.find('section', id='languages')
    if not lang_section:
        return []
    language_list = []
    lis = lang_section.select('ul li.artdeco-list__item')
    for li in lis:
        lang_div = li.find('div', class_='t-bold')
        level_span = li.find('span', class_='t-14 t-normal t-black--light')
        lname = lang_div.get_text(strip=True) if lang_div else None
        level = level_span.get_text(strip=True) if level_span else None
        if lname:
            language_list.append({'language': lname, 'level': level})
    return language_list


def associate_divisions(skills: List[str], unit: str) -> List[Dict[str, str]]:
    processor = SkillsProcessor(unit)
    return processor.associate_divisions(skills)


def retry_with_backoff(retries=3, delay=1, backoff=2, exceptions=(Exception,)):
    """Decorador para reintentos con backoff exponencial.
    
    Args:
        retries: Número máximo de reintentos
        delay: Tiempo de espera inicial en segundos
        backoff: Factor de multiplicación para el backoff
        exceptions: Excepciones que deben capturarse y reintentarse
    """
    def decorator(f):
        @wraps(f)
        async def wrapper(*args, **kwargs):
            retry_count = 0
            current_delay = delay
            
            while retry_count < retries:
                try:
                    return await f(*args, **kwargs)
                except exceptions as e:
                    retry_count += 1
                    if retry_count == retries:
                        logger.error(f"Máximo de reintentos alcanzado ({retries}) para {f.__name__}")
                        raise
                    
                    logger.warning(
                        f"Error en {f.__name__} (intento {retry_count}/{retries}): {str(e)}. "
                        f"Reintentando en {current_delay} segundos..."
                    )
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff
        return wrapper
    return decorator


async def handle_linkedin_login(page, cookies_file):
    """Maneja el inicio de sesión en LinkedIn y guarda las cookies."""
    try:
        # Obtener credenciales de variables de entorno
        username = os.getenv('LINKEDIN_USERNAME')
        password = os.getenv('LINKEDIN_PASSWORD')
        
        if not username or not password:
            raise ValueError("Credenciales de LinkedIn no configuradas en las variables de entorno")
        
        # Navegar a la página de inicio de sesión
        await page.goto('https://www.linkedin.com/login', timeout=60000)
        
        # Rellenar credenciales
        await page.fill('input[name="session_key"]', username)
        await page.fill('input[name="session_password"]', password)
        
        # Hacer clic en el botón de inicio de sesión
        await page.click('button[type="submit"]')
        
        # Esperar a que se complete la navegación después del inicio de sesión
        await page.wait_for_load_state('networkidle', timeout=60000)
        
        # Verificar si el inicio de sesión fue exitoso
        if "feed" in page.url or "in" in page.url:
            logger.info("Inicio de sesión exitoso en LinkedIn")
            # Guardar cookies para futuras sesiones
            cookies = await page.context.cookies()
            with open(cookies_file, 'w') as f:
                json.dump(cookies, f)
            logger.info(f"Cookies guardadas en {cookies_file}")
        else:
            error_msg = await page.evaluate('''() => {
                const error = document.querySelector('.error-for-username, .error-for-password');
                return error ? error.innerText : 'Error desconocido';
            }''')
            raise Exception(f"Error en el inicio de sesión: {error_msg}")
            
    except Exception as e:
        logger.error(f"Error durante el inicio de sesión en LinkedIn: {str(e)}")
        raise


async def auto_scroll(page):
    """Desplaza la página hacia abajo para cargar contenido dinámico."""
    try:
        # Obtemos la altura del viewport
        viewport_height = await page.evaluate('window.innerHeight')
        
        # Obtenemos la altura total del documento
        total_height = await page.evaluate('document.body.scrollHeight')
        
        # Desplazamiento suave
        current_position = 0
        while current_position < total_height:
            # Desplazar hacia abajo el equivalente al 80% del viewport
            current_position += int(viewport_height * 0.8)
            await page.evaluate(f'window.scrollTo(0, {current_position})')
            
            # Esperar un tiempo aleatorio entre desplazamientos
            await asyncio.sleep(random.uniform(0.5, 1.5))
            
            # Actualizar la altura total en caso de carga dinámica
            new_height = await page.evaluate('document.body.scrollHeight')
            if new_height == total_height:
                # Si no hay más contenido, salir del bucle
                break
            total_height = new_height
            
    except Exception as e:
        logger.warning(f"Error durante el desplazamiento automático: {str(e)}")


def extract_personal_info(soup):
    """Extrae información personal del perfil."""
    try:
        name = soup.find('h1', class_='text-heading-xlarge').get_text(strip=True) if soup.find('h1', class_='text-heading-xlarge') else None
        headline = soup.find('div', class_='text-body-medium').get_text(strip=True) if soup.find('div', class_='text-body-medium') else None
        
        return {
            'name': name,
            'headline': headline,
        }
    except Exception as e:
        logger.warning(f"Error al extraer información personal: {str(e)}")
        return {}

def extract_about(soup):
    """Extrae la sección 'Acerca de' del perfil."""
    try:
        about_section = soup.find('div', {'id': 'about'})
        if about_section:
            about_content = about_section.find_next('div', class_='display-flex')
            return about_content.get_text(strip=True) if about_content else None
        return None
    except Exception as e:
        logger.warning(f"Error al extraer sección 'Acerca de': {str(e)}")
        return None

@retry_with_backoff(retries=3, delay=5, backoff=2)
@track_scrape_duration()
async def scrape_linkedin_profile(link_url: str, unit: str) -> Optional[Dict]:
    """
    Extrae información estructurada de un perfil de LinkedIn de manera asíncrona.
    
    Args:
        link_url: URL completa del perfil de LinkedIn
        unit: Unidad de negocio para el procesamiento de habilidades
        
    Returns:
        Dict con la información del perfil o None en caso de error
    """
    if not link_url or 'linkedin.com/in/' not in link_url:
        logger.error(f"URL de LinkedIn no válida: {link_url}")
        return None
    
    # Normalizar la URL
    if not link_url.startswith(('http://', 'https://')):
        link_url = f"https://{link_url}"
    
    # Verificar si ya tenemos datos en caché
    cache_key = f"linkedin_profile_{hashlib.md5(link_url.encode()).hexdigest()}"
    cached_data = cache.get(cache_key)
    if cached_data:
        logger.info(f"Datos en caché encontrados para {link_url}")
        return cached_data
    
    # Configuración del navegador desde la configuración
    browser_config = {
        'headless': LINKEDIN_CONFIG.get('HEADLESS', True),
        'args': [
            '--disable-gpu',
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--disable-setuid-sandbox',
            '--disable-accelerated-2d-canvas',
            '--no-first-run',
            '--no-zygote',
            '--single-process',
            '--disable-extensions',
            '--disable-web-security',
            '--disable-features=IsolateOrigins,site-per-process',
            '--disable-site-isolation-trials',
            '--disable-blink-features=AutomationControlled',
        ],
        'timeout': LINKEDIN_CONFIG.get('BROWSER_TIMEOUT', 30000)
    }
    
    # Inicializar Playwright
    async with async_playwright() as p:
        try:
            # Configurar el navegador con opciones de rendimiento
            browser = await p.chromium.launch(**browser_config)
            
            # Configuración del contexto
            context_config = {
                'viewport': {'width': 1920, 'height': 1080},
                'user_agent': LINKEDIN_CONFIG.get('USER_AGENT', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'),
                'locale': 'es-ES,es;q=0.9,en;q=0.8',
                'timezone_id': 'Europe/Madrid',
                'permissions': ['geolocation'],
                'color_scheme': 'light',
                'ignore_https_errors': True,
                'java_script_enabled': True,
                'bypass_csp': True,
                'offline': False,
                'has_touch': False,
                'is_mobile': False,
                'device_scale_factor': 1,
                'screen': {'width': 1920, 'height': 1080},
            }
            
            # Cargar cookies si existen
            cookies_file = LINKEDIN_CONFIG.get('COOKIES_FILE')
            if cookies_file and os.path.exists(cookies_file):
                with open(cookies_file, 'r') as f:
                    context_config['storage_state'] = json.load(f)
            
            # Crear un nuevo contexto
            context = await browser.new_context(**context_config)
            
            # Configurar la página
            page = await context.new_page()
            await page.set_default_timeout(LINKEDIN_CONFIG.get('PAGE_TIMEOUT', 30000))
            
            # Navegar al perfil con reintentos
            max_retries = LINKEDIN_CONFIG.get('MAX_RETRIES', 3)
            retry_delay = LINKEDIN_CONFIG.get('RETRY_DELAY', 5)
            
            for attempt in range(max_retries):
                try:
                    logger.info(f"Intento {attempt + 1}/{max_retries} - Navegando a {link_url}")
                    await page.goto(link_url, wait_until='domcontentloaded', timeout=60000)
                    
                    # Verificar si necesitamos iniciar sesión
                    if 'authwall' in page.url:
                        logger.warning("Se requiere inicio de sesión. Intentando autenticar...")
                        await handle_linkedin_login(page, LINKEDIN_CONFIG.get('COOKIES_FILE'))
                        await page.goto(link_url, wait_until='domcontentloaded', timeout=60000)
                    
                    # Esperar a que cargue el contenido dinámico
                    await page.wait_for_selector('div.pv-text-details__left-panel', timeout=10000)
                    break
                    
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    logger.warning(f"Error en el intento {attempt + 1}: {str(e)}. Reintentando en {retry_delay} segundos...")
                    await asyncio.sleep(retry_delay * (attempt + 1))  # Backoff exponencial
            
            # Extraer información personal
            personal_info = await extract_personal_info(page)
            
            # Extraer sección 'Acerca de'
            about = await extract_about(page)
            
            # Extraer experiencia laboral
            experience = await extract_experience(page)
            
            # Extraer educación
            education = await extract_education(page)
            
            # Extraer habilidades
            skills = await extract_skills(page, unit)
            
            # Extraer información de contacto si está disponible
            contact_info = await extract_contact_info(page)
            
            # Construir el diccionario de resultado
            result = {
                'personal_info': personal_info,
                'about': about,
                'experience': experience,
                'education': education,
                'skills': skills,
                'contact_info': contact_info,
                'profile_url': link_url,
                'scraped_at': datetime.now(timezone.utc).isoformat(),
                'source': 'linkedin',
                'unit': unit,
                'metadata': {
                    'scraping_method': 'playwright',
                    'browser': 'chromium',
                    'retries': 0,
                    'cached': False
                }
            }
            
            # Guardar en caché según la configuración
            cache_timeout = LINKEDIN_CONFIG.get('CACHE_TIMEOUT', 60*60*24)  # 24 horas por defecto
            if cache_timeout > 0:
                cache.set(cache_key, result, timeout=cache_timeout)
            
            return result
            
        except Exception as e:
            logger.error(f"Error al hacer scraping de {link_url}: {str(e)}", exc_info=True)
            
            # Intentar con Selenium si falla Playwright
            logger.info("Intentando con Selenium como respaldo...")
            try:
                result = await scrape_with_selenium(link_url, unit)
                if result:
                    result['metadata'] = {
                        'scraping_method': 'selenium',
                        'browser': 'chrome',
                        'retries': 0,
                        'cached': False
                    }
                return result
            except Exception as selenium_error:
                logger.error(f"Error en Selenium: {str(selenium_error)}")
                raise
                
        finally:
            # Obtener instancias de manera segura
            browser_instance = None
            context_instance = None
            
            try:
                browser_instance = locals().get('browser')
                context_instance = locals().get('context')
                
                # Guardar cookies para la próxima sesión si está habilitado
                if LINKEDIN_CONFIG.get('SAVE_COOKIES', True) and context_instance:
                    try:
                        cookies = await context_instance.cookies()
                        cookies_file = LINKEDIN_CONFIG.get('COOKIES_FILE')
                        if cookies and cookies_file:
                            os.makedirs(os.path.dirname(cookies_file), exist_ok=True)
                            with open(cookies_file, 'w') as f:
                                json.dump({'cookies': cookies}, f)
                    except Exception as cookie_error:
                        logger.error(f"Error al guardar cookies: {str(cookie_error)}")
                
                # Normalizar habilidades y asociar divisiones si hay un resultado
                if 'result' in locals() and result and isinstance(result, dict) and result.get('skills'):
                    try:
                        result['skills'] = await asyncio.get_event_loop().run_in_executor(
                            None, normalize_skills, result['skills'], unit
                        )
                        result['divisions'] = await asyncio.get_event_loop().run_in_executor(
                            None, associate_divisions, result['skills'], unit
                        )
                    except Exception as norm_error:
                        logger.error(f"Error al normalizar habilidades: {str(norm_error)}")
                        
                # Guardar cookies de sesión exitosa
                if context_instance:
                    try:
                        cookies = await context_instance.cookies()
                        cookies_file = LINKEDIN_CONFIG.get('COOKIES_FILE')
                        if cookies and cookies_file:
                            with open(cookies_file, 'w') as f:
                                json.dump(cookies, f)
                            logger.info("Cookies de sesión guardadas exitosamente")
                    except Exception as e:
                        logger.warning(f"Error al guardar cookies de sesión: {e}")
                        
            except Exception as cleanup_error:
                logger.error(f"Error durante la limpieza: {str(cleanup_error)}")
                raise
                
            finally:
                # Asegurarse de que el navegador se cierre
                if browser_instance:
                    try:
                        if not browser_instance.is_closed():
                            await browser_instance.close()
                    except Exception as close_error:
                        logger.error(f"Error al cerrar el navegador: {str(close_error)}")
                
                # Pausa aleatoria entre solicitudes para evitar bloqueos
                await asyncio.sleep(random.uniform(5, 15))
            
            logger.info(f"Perfil de {link_url} procesado exitosamente")
            return result


async def scrape_with_selenium(profile_url: str, unit: str) -> Optional[Dict]:
    """
    Función de respaldo que utiliza Selenium para el scraping de perfiles de LinkedIn.
    Se usa cuando falla la implementación con Playwright.
    """
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import (
        TimeoutException, NoSuchElementException, WebDriverException
    )
    
    driver = None
    try:
        # Configuración de opciones de Chrome
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument(f'user-agent={random.choice(USER_AGENTS)}')
        
        # Inicializar el navegador
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(60)  # 60 segundos de timeout
        
        # Navegar al perfil
        logger.info(f"[SELENIUM] Accediendo a {profile_url}")
        driver.get(profile_url)
        
        # Esperar a que cargue la página
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.pv-profile-section"))
        )
        
        # Desplazarse para cargar contenido dinámico
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)  # Esperar a que cargue el contenido
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        
        # Obtener el HTML procesado
        html_content = driver.page_source
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extraer datos del perfil
        profile_data = {
            'profile_url': profile_url,
            'scraped_at': datetime.now(timezone.utc).isoformat(),
            'personal_info': extract_personal_info(soup),
            'headline': extract_headline(soup),
            'location': extract_location(soup),
            'about': extract_about(soup),
            'experience': extract_experience(soup),
            'education': extract_education(soup),
            'languages': extract_languages(soup),
            'contact_info': extract_contact_info(soup),
        }
        
        # Extraer habilidades
        raw_text = soup.get_text()
        profile_data['skills'] = extract_skills(raw_text, unit)
        
        # Normalizar habilidades y asociar divisiones
        if profile_data['skills']:
            profile_data['skills'] = normalize_skills(profile_data['skills'], unit)
            profile_data['divisions'] = associate_divisions(profile_data['skills'], unit)
        
        logger.info(f"[SELENIUM] Perfil de {profile_url} procesado exitosamente")
        return profile_data
        
    except TimeoutException:
        logger.error(f"[SELENIUM] Timeout al cargar el perfil {profile_url}")
        return None
    except NoSuchElementException as e:
        logger.error(f"[SELENIUM] Elemento no encontrado en {profile_url}: {str(e)}")
        return None
    except WebDriverException as e:
        logger.error(f"[SELENIUM] Error del navegador al procesar {profile_url}: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"[SELENIUM] Error inesperado al procesar {profile_url}: {str(e)}")
        return None
    finally:
        if driver:
            try:
                driver.quit()
            except Exception as e:
                logger.warning(f"Error al cerrar el navegador: {str(e)}")
            
@backoff.on_exception(backoff.expo, Exception, max_tries=5, jitter=backoff.full_jitter)
async def fetch_page(page, url):
    await page.goto(url)

def update_person_from_scrape(person: Person, scraped_data: dict):
    """
    Actualiza los datos de un perfil con la información scrapeada solo si hay datos válidos.
    """
    if not scraped_data or not any(scraped_data.values()):
        logger.warning(f"No se encontraron datos válidos para actualizar {person.nombre}")
        return
    
    updated = False
    if scraped_data.get("headline"):
        person.metadata["headline"] = scraped_data["headline"]
        updated = True
    if scraped_data.get("experience"):
        person.metadata["experience"] = scraped_data["experience"]
        updated = True
    if scraped_data.get("education"):
        person.metadata["education"] = scraped_data["education"]
        updated = True
    if scraped_data.get("skills"):
        extracted_skills = extract_skills(" ".join(scraped_data["skills"]))
        person.metadata["skills"] = list(set(person.metadata.get("skills", []) + extracted_skills))
        updated = True
    if scraped_data.get("languages"):
        person.metadata["languages"] = scraped_data["languages"]
        updated = True
    if scraped_data.get("contact_info"):
        contact_info = scraped_data["contact_info"]
        if "email" in contact_info and not person.email:
            person.email = contact_info["email"]
            updated = True
        if "phone" in contact_info and not person.phone:
            person.phone = contact_info["phone"]
            updated = True

    person.metadata["linkedin_last_updated"] = timezone.now().isoformat()
    if updated:
        person.save()
        logger.info(f"Perfil actualizado: {person.nombre} {person.apellido_paterno}")
    else:
        logger.info(f"No se actualizó {person.nombre}: sin datos nuevos")

def construct_linkedin_url(first_name: str, last_name: str) -> str:
    """
    Construye una posible URL de LinkedIn a partir del nombre y apellido.
    """
    base_url = "https://www.linkedin.com/in/"
    name_slug = f"{first_name.lower()}-{last_name.lower()}".replace(" ", "-")
    return f"{base_url}{name_slug}"

async def process_linkedin_updates():
    persons = Person.objects.all()
    processed_count = 0
    constructed_count = 0
    errors_count = 0

    for person in persons:
        linkedin_url = person.linkedin_url
        if not linkedin_url:
            linkedin_url = construct_linkedin_url(person.nombre, person.apellido_paterno)
            person.linkedin_url = linkedin_url
            person.save()
            constructed_count += 1
            logger.info(f"🌐 URL construida para {person.nombre}: {linkedin_url}")

        try:
            logger.info(f"Procesando: {person.nombre} ({linkedin_url})")
            scraped_data = await scrape_linkedin_profile(linkedin_url, "amigro")  # Default unit
            update_person_from_scrape(person, scraped_data)
            processed_count += 1
            logger.info(f"✅ Actualizado: {person.nombre}")
        except Exception as e:
            logger.error(f"❌ Error procesando {person.nombre} ({linkedin_url}): {e}")
            errors_count += 1

    logger.info(f"Resumen: Procesados: {processed_count}, URLs construidas: {constructed_count}, Errores: {errors_count}")


def process_linkedin_batch():
    from app.ats.chatbot.nlp.nlp import process_recent_users_batch
    process_recent_users_batch()

def main_test():
    unit = "amigro"  # Cambiar según la unidad de negocio
    test_text = "Técnica relevante 1, Técnica relevante 2, Blanda relevante 1"

    # Extraer habilidades
    skills = extract_skills(test_text, unit)
    print(f"Habilidades extraídas para {unit}: {skills}")

    # Asociar divisiones
    associations = associate_divisions(skills, unit)
    for assoc in associations:
        print(f"Habilidad: {assoc['skill']} -> División: {assoc['division']}")

if __name__ == "__main__":
    main_test()

class LinkedInScraper:
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None

    async def initialize(self):
        """Inicializa el navegador y el contexto."""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=True)
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()

    async def close(self):
        """Cierra el navegador y libera recursos."""
        if self.browser:
            await self.browser.close()

    async def scrape_job(self, url: str) -> Dict:
        """Extrae información de una oferta de trabajo de LinkedIn."""
        try:
            await self.page.goto(url)
            await PlaywrightAntiDeteccion.simular_comportamiento_humano(self.page)
            
            # Extraer datos básicos
            title = await self.page.evaluate('() => document.querySelector(".job-details-jobs-unified-top-card__job-title")?.textContent?.trim()')
            company = await self.page.evaluate('() => document.querySelector(".job-details-jobs-unified-top-card__company-name")?.textContent?.trim()')
            location = await self.page.evaluate('() => document.querySelector(".job-details-jobs-unified-top-card__bullet")?.textContent?.trim()')
            
            # Extraer descripción
            description = await self.page.evaluate('() => document.querySelector(".job-details-jobs-unified-top-card__job-description")?.textContent?.trim()')
            
            # Extraer requisitos
            requirements = await self.page.evaluate('''
                () => {
                    const reqs = Array.from(document.querySelectorAll(".job-details-jobs-unified-top-card__job-description li"))
                        .map(li => li.textContent.trim());
                    return reqs;
                }
            ''')
            
            return {
                'title': title,
                'company': company,
                'location': location,
                'description': description,
                'requirements': requirements,
                'url': url,
                'source': 'linkedin',
                'scraped_at': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error scraping LinkedIn job {url}: {e}")
            return None

async def process_linkedin_jobs(urls: List[str]) -> List[Dict]:
    """Procesa una lista de URLs de ofertas de LinkedIn."""
    scraper = LinkedInScraper()
    try:
        await scraper.initialize()
        jobs = []
        for url in urls:
            job_data = await scraper.scrape_job(url)
            if job_data:
                jobs.append(job_data)
        return jobs
    finally:
        await scraper.close()