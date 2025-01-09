# /home/pablollh/app/linkedin.py

import logging
import os
import csv
import time
import random
import backoff
import requests
from typing import Optional, List, Dict
from datetime import datetime
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from bs4 import BeautifulSoup
from app.models import Person, BusinessUnit, USER_AGENTS
from app.catalogs import DIVISION_SKILLS
from app.nlp import sn  # SkillNer instance
from spacy.matcher import PhraseMatcher
from spacy.lang.es import Spanish

logger = logging.getLogger(__name__)

# Inicializar spaCy y PhraseMatcher
nlp = Spanish()
phrase_matcher = PhraseMatcher(nlp.vocab)

# Inicializar SkillExtractor correctamente
skill_extractor = SkillExtractor(phraseMatcher=phrase_matcher)

LINKEDIN_CLIENT_ID = os.getenv("LINKEDIN_CLIENT_ID", "781zbztzovea6a")
LINKEDIN_CLIENT_SECRET = os.getenv("LINKEDIN_CLIENT_SECRET", "WPL_AP1.MKozNnsrqofMSjN4.ua0UOQ==")
ACCESS_TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN", None) 
LINKEDIN_API_BASE = "https://api.linkedin.com/v2"

MIN_DELAY = 8
MAX_DELAY = 18

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
        logger.info(f"Persona procesada: {person.nombre} {person.email}")
    else:
        logger.warning(f"No se pudo procesar: {first_name} {last_name}")

def save_person_record(
    first_name: str,
    last_name: str,
    linkedin_url: Optional[str],
    email: Optional[str],
    birthday: Optional[str],
    company: Optional[str],
    position: Optional[str],
    business_unit: BusinessUnit,
    skills: Optional[List[str]] = None,
    phone: Optional[str] = None
) -> Person:
    """
    Crea o actualiza un registro en la base de datos.
    """
    with transaction.atomic():
        existing = deduplicate_persons(first_name, last_name, email, company, position)
        if existing:
            # Actualiza datos existentes
            updated = False
            if linkedin_url and 'linkedin_url' not in existing.metadata:
                existing.metadata['linkedin_url'] = linkedin_url
                updated = True
            if company:
                existing.metadata['last_company'] = company
                updated = True
            if position:
                existing.metadata['last_position'] = position
                updated = True
            if email and not existing.email:
                existing.email = email
                updated = True
            if skills:
                extracted_skills = extract_skills(", ".join(skills))
                existing.metadata['skills'] = list(set(existing.metadata.get('skills', []) + extracted_skills))
                divisions = associate_divisions(extracted_skills)
                existing.metadata['divisions'] = list(set(existing.metadata.get('divisions', []) + divisions))
                updated = True
            if phone and not existing.phone:
                existing.phone = phone
                updated = True
            if birthday and not existing.fecha_nacimiento:
                try:
                    existing.fecha_nacimiento = datetime.strptime(birthday, "%d/%m/%Y").date()
                    updated = True
                except ValueError:
                    pass
            if updated:
                existing.save()
            return existing
        else:
            # Crear nuevo registro
            person = Person(
                number_interaction=f"LI-{int(time.time())}-{random.randint(100,999)}",
                nombre=first_name,
                apellido_paterno=last_name,
                email=email,
                phone=phone,
                fecha_nacimiento=datetime.strptime(birthday, "%d/%m/%Y").date() if birthday else None,
                metadata={
                    'linkedin_url': linkedin_url,
                    'last_company': company,
                    'last_position': position,
                    'skills': extract_skills(", ".join(skills)) if skills else [],
                    'divisions': associate_divisions(extract_skills(", ".join(skills))) if skills else []
                }
            )
            person.save()
            return person

def normalize_skills(raw_skills):
    """
    Normaliza habilidades utilizando el catálogo de habilidades en `DIVISION_SKILLS`.
    """
    normalized = []
    for skill in raw_skills:
        # Buscar habilidades en el catálogo centralizado
        normalized_skill = next((division_skill for division_skill in DIVISION_SKILLS if skill.lower() in division_skill.lower()), None)
        if normalized_skill:
            normalized.append(normalized_skill)
        else:
            normalized.append(skill)
    return normalized

# =========================================================
# Manejo de CSV
# =========================================================

def process_csv(csv_path: str, business_unit: BusinessUnit):
    """
    Procesa un archivo CSV para crear o actualizar registros de personas.
    Columnas esperadas: First Name, Last Name, URL, Email Address, Cumpleaños, Company, Position, Skills, Phone.
    """
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            fn = normalize_name(row.get('First Name', ''))
            ln = normalize_name(row.get('Last Name', ''))
            linkedin_url = row.get('URL', '').strip() or None
            email = row.get('Email Address', '').strip() or None
            birthday = row.get('Cumpleaños', '').strip() or None
            company = row.get('Company', '').strip() or None
            position = row.get('Position', '').strip() or None
            skills = row.get('Skills', '').strip().split(',') if row.get('Skills') else []
            phone = row.get('Phone', '').strip() or None

            # Guardar o actualizar registro
            person = save_person_record(
                fn, ln, linkedin_url, email, birthday, company, position, business_unit, skills, phone
            )
            logger.info(f"Persona procesada: {person.nombre} {person.apellido_paterno} - {person.email}")
    logger.info("Procesamiento CSV completado.")

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
                metadata__linkedin_url=linkedin_url
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


def extract_contact_link(soup):
    link = soup.find('a', id='top-card-text-details-contact-info')
    if link and link.get('href'):
        return link.get('href')
    return None

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
                value = mail_link['href'].replace('mailto:','')
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

def extract_name(soup):
    h1 = soup.find('h1', class_='inline t-24 v-align-middle break-words')
    return h1.get_text(strip=True) if h1 else None

def extract_headline(soup):
    hd = soup.find('div', class_='text-body-medium break-words')
    return hd.get_text(strip=True) if hd else None

def extract_location(soup):
    loc = soup.find('span', class_='text-body-small inline t-black--light break-words')
    return loc.get_text(strip=True) if loc else None

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

def extract_skills(soup):
    skills_section = soup.find('section', id='skills')
    if not skills_section:
        return []
    skill_list = []
    lis = skills_section.select('ul li.artdeco-list__item')
    for li in lis:
        skill_div = li.find('div', class_='t-bold')
        if skill_div:
            sname = skill_div.get_text(strip=True)
            if sname and sname not in skill_list:
                skill_list.append(sname)
    return skill_list

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

def update_person_from_scrape(person: Person, scraped_data: dict):
    """
    Actualiza los datos de un perfil con la información scrapeada.
    """
    updated = False
    if scraped_data.get("headline"):
        person.metadata["headline"] = scraped_data["headline"]
        updated = True
    if scraped_data.get("experience"):
        person.experience_data = scraped_data["experience"]
        updated = True
    if scraped_data.get("education"):
        person.metadata["education"] = scraped_data["education"]
        updated = True
    if scraped_data.get("skills"):
        extracted_skills = extract_skills(" ".join(scraped_data["skills"]))
        person.metadata["skills"] = list(set(person.metadata.get("skills", []) + extracted_skills))
        divisions = associate_divisions(extracted_skills)
        person.metadata["divisions"] = list(set(person.metadata.get("divisions", []) + divisions))
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
    person.metadata.pop("linkedin_pending", None)  # Remove pending flag
    if updated:
        person.save()
        logger.info(f"Perfil actualizado: {person.nombre} {person.apellido_paterno}")

@backoff.on_exception(backoff.expo, requests.exceptions.RequestException, max_tries=5)
def scrape_linkedin_profile(link_url: str) -> dict:
    """
    Realiza scraping en LinkedIn para un perfil individual usando su URL.    
    """
    html = fetch_url(link_url)
    soup = BeautifulSoup(html, 'html.parser')

    data = {
        'name': extract_name(soup),
        'headline': extract_headline(soup),
        'location': extract_location(soup),
        'experience': extract_experience(soup),
        'education': extract_education(soup),
        'skills': extract_skills(soup),
        'languages': extract_languages(soup),
        'contact_info': extract_contact_info(soup)
    }
    return data

def scrape_linkedin_profile(link_url: str) -> dict:
    """
    Realiza scraping en LinkedIn para un perfil individual usando su URL.    
    """
    try:
        html = fetch_url(link_url)   # Asumes que fetch_url() obtiene la página con backoff
        if not html:
            logger.warning(f"No se pudo obtener HTML para {link_url}")
            return {}

        soup = BeautifulSoup(html, 'html.parser')

        # ... aquí extraes name, headline, location, experience, etc. ...
        # Pongamos un ejemplo para 'skills':

        # Supongamos que no hay un <section id="skills"> en LinkedIn normal
        # Sino que tu scraping obtiene un 'about_text' y luego usas nlp_processor.extract_skills:

        about_text = soup.find("div", class_="pv-about-section")
        if about_text:
            about_str = about_text.get_text(strip=True)
        else:
            about_str = ""

        # extraer skills:
        extracted_skills = nlp_processor.extract_skills(about_str)

        data = {
            'name': ...,
            'headline': ...,
            'location': ...,
            'experience': ...,
            'education': ...,
            'skills': extracted_skills,  # <--- lo que te interese
        }
        return data

    except Exception as e:
        logger.error(f"❌ Error scrapeando {link_url}: {e}", exc_info=True)
        return {}

def extract_skills(text: str) -> List[str]:
    """
    Extrae habilidades del texto utilizando SkillNer.
    """
    skills = sn.extract_skills(text)
    return [skill['skill'] for skill in skills]

def associate_divisions(skills: List[str]) -> List[str]:
    """
    Asocia divisiones basadas en las habilidades extraídas.
    """
    associated_divisions = set()
    for skill in skills:
        for division, division_skills in DIVISION_SKILLS.items():
            if skill in division_skills:
                associated_divisions.add(division)
    return list(associated_divisions)

