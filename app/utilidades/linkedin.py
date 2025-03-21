# /home/pablo/app/utilidades/linkedin.py
import logging
import os
import csv
import time
import json
import random
import backoff
import requests
import itertools
from typing import Optional, List, Dict
from datetime import datetime
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from collections import defaultdict  # <--- Importado correctamente
from app.models import BusinessUnit, Person, ChatState, USER_AGENTS
from app.chatbot.nlp import NLPProcessor
from app.utilidades.loader import DIVISION_SKILLS, BUSINESS_UNITS, DIVISIONES
from spacy.matcher import PhraseMatcher
from spacy.lang.es import Spanish

logger = logging.getLogger(__name__)
os.environ["TRANSFORMERS_BACKEND"] = "tensorflow"




LINKEDIN_CLIENT_ID = os.getenv("LINKEDIN_CLIENT_ID", "781zbztzovea6a")
LINKEDIN_CLIENT_SECRET = os.getenv("LINKEDIN_CLIENT_SECRET", "WPL_AP1.MKozNnsrqofMSjN4.ua0UOQ==")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN", None)
LINKEDIN_API_BASE = "https://api.linkedin.com/v2"

MIN_DELAY = 8
MAX_DELAY = 18
# Ruta base de los catálogos
CATALOGS_BASE_PATH = "/home/pablo/app/utilidades/catalogs"

# =========================================================
# Clase para manejar habilidades y divisiones
# =========================================================

def extract_skills(text: str, unit: str) -> List[str]:
    nlp = NLPProcessor(language="es", mode="candidate", analysis_depth="deep")
    skills_dict = nlp.extract_skills(text)
    skills = list(set(skills_dict["technical"] + skills_dict["soft"] + skills_dict["certifications"] + skills_dict["tools"]))
    logger.info(f"Habilidades extraídas (deep) para {unit}: {skills}")
    return skills

class SkillsProcessor:
    def __init__(self, unit_name: str):
        self.unit_name = unit_name
        self.skills_data = self._load_unit_skills()

    def _load_unit_skills(self) -> Dict:
        """
        Carga el archivo skills.json para la unidad de negocio especificada.
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
        """
        try:
            words = text.lower().split()
            extracted_skills = set()

            for division, roles in self.skills_data.items():
                for role, attributes in roles.items():
                    tech_skills = attributes.get("Habilidades Técnicas", [])
                    soft_skills = attributes.get("Habilidades Blandas", [])
                    all_skills = tech_skills + soft_skills
                    for skill in all_skills:
                        if all(word in words for word in skill.lower().split()):
                            extracted_skills.add(skill)

            return list(extracted_skills)
        except Exception as e:
            logger.error(f"Error extrayendo habilidades: {e}")
            return []

    def associate_divisions(self, skills: List[str]) -> List[Dict[str, str]]:
        """
        Asocia divisiones basadas en habilidades extraídas y el catálogo de la unidad.
        """
        associations = []
        try:
            for skill in skills:
                for division, roles in self.skills_data.items():
                    for role, attributes in roles.items():
                        tech_skills = attributes.get("Habilidades Técnicas", [])
                        soft_skills = attributes.get("Habilidades Blandas", [])
                        all_skills = tech_skills + soft_skills
                        if skill in all_skills:
                            associations.append({"skill": skill, "division": division})
        except Exception as e:
            logger.error(f"Error asociando divisiones: {e}")
        return associations


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
def process_csv(csv_path: str, business_unit: BusinessUnit):
    count = 0
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            count += 1
            fn = normalize_name(row.get('First Name', ''))
            ln = normalize_name(row.get('Last Name', ''))
            linkedin_url = row.get('URL', '').strip() or None
            email = row.get('Email Address', '').strip() or None
            phone_number = row.get('Phone', '').strip() or None

            candidate_data = {
                'nombre': fn,
                'apellido_paterno': ln,
                'linkedin_url': linkedin_url,
                'email': email,
                'phone': phone_number,
                'metadata': {}
            }

            try:
                candidate = deduplicate_persons(fn, ln, email, None, None)
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

                # Si existe linkedin_url y se quiere enriquecer, realizar scraping:
                if linkedin_url:
                    scraped_data = scrape_linkedin_profile(linkedin_url, business_unit.name.lower())
                    if scraped_data:
                        update_person_from_scrape(candidate, scraped_data)
                        logger.info(f"Enriquecido candidato {candidate.nombre} con datos de LinkedIn")
            except Exception as e:
                logger.error(f"Error procesando registro: {fn} {ln} ({email}): {e}", exc_info=True)

            if count % 100 == 0:
                logger.info(f"Avance: Se han procesado {count} registros.")
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

def slow_scrape_from_csv(csv_path: str, business_unit: BusinessUnit):
    """
    Scrape lento desde CSV, usando las URLs para enriquecer datos.
    """
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

            # Verificar si ya se procesó usando metadata
            existing_person = Person.objects.filter(
                nombre__iexact=fn,
                apellido_paterno__iexact=ln,
                linkedin_url=linkedin_url
            ).first()

            if existing_person and existing_person.metadata.get('scraped', False):
                logger.info(f"Perfil ya procesado: {fn} {ln}")
                continue  # Saltar si ya fue procesado

            if linkedin_url:
                # Realizar el scraping
                try:
                    scraped_data = scrape_linkedin_profile(linkedin_url)
                    if scraped_data:
                        # Guardar o actualizar el registro
                        person = save_person_record(
                            fn, ln, linkedin_url, email, birthday, company, position, business_unit
                        )

                        # Actualizar metadata si hay cambios en email o celular
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

                        # Marcar como procesado en metadata
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
                # Sin URL, solo guardamos básico
                person = save_person_record(
                    fn, ln, None, email, birthday, company, position, business_unit
                )
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

def scrape_linkedin_profile(link_url, unit):
    """
    Realiza scraping de un perfil de LinkedIn usando Playwright con cookies autenticadas.
    """
    try:
        with sync_playwright() as p:
            # Seleccionar un USER_AGENT aleatorio
            user_agent = random.choice(USER_AGENTS)
            
            # Lanzar el navegador con configuraciones robustas
            browser = p.chromium.launch(headless=True)  # Cambia a False para depurar visualmente
            context = browser.new_context(
                user_agent=user_agent,
                viewport={"width": 1280, "height": 720},
                locale="es-ES"  # Simula un navegador en español
            )
            
            # Ruta para almacenar cookies autenticadas
            cookies_file = "/home/pablo/skills_data/linkedin_cookies.json"
            
            # Verificar si hay cookies guardadas y válidas
            if os.path.exists(cookies_file):
                context.storage_state(path=cookies_file)
                logger.info(f"Cargando cookies desde {cookies_file}")
            else:
                logger.warning("No se encontraron cookies guardadas. Intentando login manual.")
                # Si no hay cookies, realizar login (puedes proporcionar tus credenciales aquí)
                page = context.new_page()
                page.goto("https://www.linkedin.com/login")
                page.fill("#username", "pablo@huntred.com")  # Reemplaza con tu email
                page.fill("#password", "Natalia&Patricio1113!")  # Reemplaza con tu contraseña
                page.click("button[type=submit]")
                page.wait_for_load_state("networkidle", timeout=60000)
                context.storage_state(path=cookies_file)  # Guardar cookies tras login
                logger.info(f"Cookies guardadas en {cookies_file}")
                page.close()

            # Abrir la página del perfil
            page = context.new_page()
            logger.info(f"Intentando acceder a {link_url}")
            page.goto(link_url, timeout=60000)  # Timeout aumentado a 60 segundos
            
            # Esperar a que la página cargue completamente
            page.wait_for_load_state("networkidle", timeout=60000)
            
            # Verificar si requiere login (título de la página de login)
            if "Log In or Sign Up" in page.title():
                logger.error(f"Autenticación fallida para {link_url}. Actualiza las credenciales o cookies.")
                browser.close()
                return {}

            # Obtener el contenido HTML
            content = page.content()
            soup = BeautifulSoup(content, "html.parser")
            
            # Extraer datos
            data = {
                "headline": extract_headline(soup),
                "location": extract_location(soup),
                "experience": extract_experience(soup),
                "education": extract_education(soup),
                "skills": extract_skills(soup.get_text(), unit),  # Esto usa NLPProcessor
                "languages": extract_languages(soup),
                "contact_info": extract_contact_info(soup),
            }
            
            # Normalizar habilidades y asociar divisiones
            data["skills"] = normalize_skills(data["skills"], unit)
            data["divisions"] = associate_divisions(data["skills"], unit)
            
            # Log de éxito
            logger.info(f"Scrapeado exitosamente {link_url}")
            
            # Cerrar el navegador
            browser.close()
            
            # Pausa aleatoria para evitar bloqueos
            time.sleep(random.uniform(10, 20))
            
            return data
            
    except Exception as e:
        logger.error(f"Error scrapeando {link_url}: {str(e)}", exc_info=True)
        return {}

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

def process_linkedin_updates():
    """
    Revisa todos los perfiles de LinkedIn en la base de datos y los actualiza.
    Muestra un resumen al finalizar.
    """
    persons = Person.objects.all()
    processed_count = 0
    constructed_count = 0
    errors_count = 0

    for person in persons:
        linkedin_url = person.linkedin_url

        # Construir URL si falta
        if not linkedin_url:
            linkedin_url = construct_linkedin_url(person.nombre, person.apellido_paterno)
            person.linkedin_url = linkedin_url  # Guardar en el campo del modelo
            person.save()
            constructed_count += 1
            logger.info(f"🌐 URL construida para {person.nombre}: {linkedin_url}")

        try:
            logger.info(f"Procesando: {person.nombre} ({linkedin_url})")
            scraped_data = scrape_linkedin_profile(linkedin_url)
            update_person_from_scrape(person, scraped_data)
            processed_count += 1
            logger.info(f"✅ Actualizado: {person.nombre}")
        except Exception as e:
            logger.error(f"❌ Error procesando {person.nombre} ({linkedin_url}): {e}")
            errors_count += 1

    logger.info(f"Resumen: Procesados: {processed_count}, URLs construidas: {constructed_count}, Errores: {errors_count}")

def process_linkedin_batch():
    from app.chatbot.nlp import process_recent_users_batch
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