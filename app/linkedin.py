# /home/amigro/app/linkedin.py

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

logger = logging.getLogger(__name__)

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

def save_person_record(
    first_name: str,
    last_name: str,
    linkedin_url: Optional[str],
    email: Optional[str],
    birthday: Optional[str],
    company: Optional[str],
    position: Optional[str],
    business_unit: BusinessUnit
) -> Person:
    with transaction.atomic():
        existing = deduplicate_persons(first_name, last_name, email, company, position)
        if existing:
            # Actualiza datos si faltan
            if email and not existing.email:
                existing.email = email
            if linkedin_url:
                existing.metadata['linkedin_url'] = linkedin_url
            if company:
                existing.metadata['last_company'] = company
            if position:
                existing.metadata['last_position'] = position
            if birthday and not existing.fecha_nacimiento:
                try:
                    dt = datetime.strptime(birthday, "%d/%m/%Y").date()
                    existing.fecha_nacimiento = dt
                except:
                    pass
            existing.save()
            return existing
        else:
            # Crear nuevo
            number_interaction = f"LI-{int(time.time())}-{random.randint(100,999)}"
            person = Person(
                number_interaction=number_interaction,
                nombre=first_name,
                apellido_paterno=last_name if last_name else '',
                email=email,
            )
            if birthday:
                try:
                    dt = datetime.strptime(birthday, "%d/%m/%Y").date()
                    person.fecha_nacimiento = dt
                except:
                    pass

            meta = {}
            if linkedin_url:
                meta['linkedin_url'] = linkedin_url
            if company:
                meta['last_company'] = company
            if position:
                meta['last_position'] = position

            person.metadata = meta
            person.save()
            return person

# =========================================================
# Manejo de CSV
# =========================================================

def process_csv(csv_path: str, business_unit: BusinessUnit):
    """
    Procesa CSV con columnas: First Name, Last Name, URL, Email Address, Cumpleaños, Company, Position
    """
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            fn = normalize_name(row.get('First Name', ''))
            ln = normalize_name(row.get('Last Name', ''))
            linkedin_url = row.get('URL','').strip()
            email = row.get('Email Address','').strip() or None
            birthday = row.get('Cumpleaños','').strip() or None
            company = row.get('Company','').strip() or None
            position = row.get('Position','').strip() or None

            p = save_person_record(fn, ln, linkedin_url, email, birthday, company, position, business_unit)
            logger.info(f"Persona procesada: {p.nombre} {p.apellido_paterno} - {p.email}")
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

@backoff.on_exception(backoff.expo, requests.exceptions.RequestException, max_tries=5)
def fetch_url(url):
    headers = {'User-Agent': random.choice(USER_AGENTS)}
    r = requests.get(url, headers=headers, timeout=10)
    r.raise_for_status()
    time.sleep(random.uniform(5, 15))  # Pausa entre requests
    return r.text

def slow_scrape_from_csv(csv_path: str, business_unit: BusinessUnit):
    """
    Scrape lento desde CSV, usando las URLs para enriquecer datos.
    """
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            linkedin_url = row.get('URL','').strip()
            fn = normalize_name(row.get('First Name',''))
            ln = normalize_name(row.get('Last Name',''))
            email = row.get('Email Address','').strip() or None
            birthday = row.get('Cumpleaños','').strip() or None
            company = row.get('Company','').strip() or None
            position = row.get('Position','').strip() or None

            if linkedin_url:
                try:
                    scraped_data = scrape_linkedin_profile(linkedin_url)
                    # Combinar datos
                    # Si scraped_data tiene first_name/last_name/empresa/posición, puedes usarlos:
                    # ejemplo: new_company = scraped_data.get('company') or company
                    # Por ahora asumo que scraped_data no da company directamente, sino en experience[0]
                    # Ajustar según tu lógica.
                    
                    person = save_person_record(fn, ln, linkedin_url, email, birthday, company, position, business_unit)
                    
                    # Guardar skills, experiencia, etc. en metadata (ejemplo)
                    changed = False
                    if 'skills' in scraped_data:
                        person.metadata['skills'] = scraped_data['skills']
                        changed = True
                    if 'experience' in scraped_data:
                        person.metadata['experience_data'] = scraped_data['experience']
                        changed = True
                    if 'education' in scraped_data:
                        person.metadata['education_data'] = scraped_data['education']
                        changed = True
                    if 'languages' in scraped_data:
                        person.metadata['languages'] = scraped_data['languages']
                        changed = True
                    if 'contact_info' in scraped_data and scraped_data['contact_info']:
                        ci = scraped_data['contact_info']
                        if ci.get('email') and not person.email:
                            person.email = ci['email']
                            changed = True
                        if ci.get('phone'):
                            person.metadata['phone'] = ci['phone']
                            changed = True
                        if ci.get('birthday') and not person.fecha_nacimiento:
                            # Intentar parsear birthday (sin año)
                            # persona.fecha_nacimiento - no podemos sin año, lo guardamos en metadata
                            person.metadata['birthday_day_month'] = ci['birthday']
                            changed = True
                    if changed:
                        person.save()

                    logger.info(f"Perfil enriquecido: {person.nombre} {person.apellido_paterno}")
                except Exception as e:
                    logger.error(f"Error scrapeando {linkedin_url}: {e}")
            else:
                # Sin URL, solo guardamos básico
                p = save_person_record(fn, ln, None, email, birthday, company, position, business_unit)

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

@backoff.on_exception(backoff.expo, requests.exceptions.RequestException, max_tries=5)
def scrape_linkedin_profile(link_url: str):
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
        'contact_info': {}
    }

    contact_link = extract_contact_link(soup)
    if contact_link:
        base = "https://www.linkedin.com"
        contact_url = base + contact_link
        try:
            contact_html = fetch_url(contact_url)
            csoup = BeautifulSoup(contact_html, 'html.parser')
            data['contact_info'] = extract_contact_info(csoup)
        except requests.exceptions.RequestException:
            pass

    return data