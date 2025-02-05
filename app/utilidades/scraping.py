# /home/pablollh/app/scraping.py

# Módulos estándar de Python
import json
import asyncio
import logging
import random
import requests
import aiohttp
from django.db import transaction
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

# Librerías de terceros
from abc import ABC, abstractmethod
from aiohttp import ClientTimeout
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from prometheus_client import Counter, Histogram, start_http_server
from tenacity import retry, stop_after_attempt, wait_exponential, before_sleep_log
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options

# Funcionalidad de Django
from asgiref.sync import sync_to_async
from django.utils.timezone import now

# Modelos y componentes de la aplicación
from app.models import (
    DominioScraping, Vacante, RegistroScraping, ConfiguracionBU,
    BusinessUnit, PLATFORM_CHOICES
)
from app.utilidades.loader import DIVISION_SKILLS, DIVISIONES, BUSINESS_UNITS
from app.chatbot.utils import clean_text
#from app.chatbot import ChatBotHandler  # Solo si se usa en scraping

logging.basicConfig(
    level=logging.INFO,  # Cambia a DEBUG para más detalles
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scraping.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def assign_business_unit_to_vacante(vacante):
   business_rules = {
       "huntRED": {
           "subdirector", "director", "vp", "ceo", "presidente", 
           "board", "consejero", "estratégico", "executive", 
           "alta dirección", "gerente", "chief"
       },
       "huntu": {
           "trainee", "junior", "recién egresado", "entry level", 
           "practicante", "pasante", "becario", "líder", 
           "coordinador", "analista", "senior", "lead"
       },
       "amigro": {
           "migrante", "trabajador internacional",  
           "operativo", "cajero", "auxiliar", "soporte", 
           "campos agrícolas", "construcción", "servicio", 
           "operador"
       }
   }
   
   title = vacante["title"].lower()
   
   for bu, keywords in business_rules.items():
       if keywords.intersection(title.split()):
           return bu
   
   return "amigro"  # Default

@transaction.atomic
async def save_vacantes(jobs: List[JobListing], dominio: DominioScraping):
    """
    Guarda las vacantes extraídas en la base de datos.
    """
    for job in jobs:
        try:
            business_unit = assign_business_unit_to_vacante(job)
            business_unit_obj = await sync_to_async(BusinessUnit.objects.get)(name=business_unit)

            skills = extract_skills(job.description or "")
            divisions = associate_divisions(skills)

            vacante, created = await sync_to_async(Vacante.objects.update_or_create)(
                titulo=job.title,
                empresa=job.company,
                defaults={
                    "salario": job.salary.get('min', None) if job.salary else None,
                    "ubicacion": job.location,
                    "descripcion": job.description,
                    "requisitos": job.requirements,
                    "beneficios": ", ".join(job.benefits or []),
                    "modalidad": job.job_type,
                    "skills_required": skills,
                    "divisiones": divisions,
                    "dominio_origen": dominio,
                    "business_unit": business_unit_obj,
                    "fecha_publicacion": job.posted_date or now(),
                    "remote_friendly": True if job.job_type and 'remote' in job.job_type.lower() else False,
                    "business_unit": business_unit_obj,
                }
            )
            msg = "creada" if created else "actualizada"
            logger.info(f"🔄 Vacante {msg}: {vacante.titulo}")
        except Exception as e:
            logger.error(f"Error guardando vacante {job.title}: {e}")


# =============================================
# Manejo de Sessiones y Condicionales Generales
# =============================================
async def get_session():
    """
    Obtiene un token de sesión desde el perfil de usuario en Amigro de manera asíncrona.
    """
    headers = {'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N)'}
    url = "https://huntred.com/my-profile/"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=10) as response:
                response.raise_for_status()
                text = await response.text()
                soup = BeautifulSoup(text, "html.parser")
                input_tag = soup.find("input", {"id": "login_security"})
                if input_tag and input_tag.get("value"):
                    return input_tag.get("value")
                else:
                    logger.error("No se encontró el input 'login_security' en la respuesta.")
                    return None
    except aiohttp.ClientError as e:
        logger.error(f"Error obteniendo sesión: {e}")
        return None
    except Exception as e:
        logger.error(f"Error procesando sesión: {e}")
        return None

async def consult(page, url, business_unit=None):
    from app.models import ConfiguracionBU
    import urllib.parse

    try:
        configuracion = (
            business_unit if business_unit else await sync_to_async(ConfiguracionBU.objects.get)(id=4)
        )
        jwt_token = configuracion.jwt_token
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {jwt_token}',
            'User-Agent': 'PostmanRuntime/7.42.0'
        }
        payload = {
            'lang': '',
            'search_keywords': '',
            'search_location': '',
            'filter_job_type[]': ['freelance', 'full-time', 'internship', 'part-time', 'temporary'],
            'per_page': 10,
            'orderby': 'title',
            'order': 'desc',
            'page': page
        }
        
        logger.info(f"Enviando solicitud a {url} con payload: {payload}")
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=payload) as response:
                response.raise_for_status()
                content_type = response.headers.get('Content-Type', '')
                if content_type.startswith('application/json'):
                    vacantes_json = await response.json()
                else:
                    logger.error(f"Respuesta no válida (Content-Type: {content_type})")
                    vacantes_json = []

    except ConfiguracionBU.DoesNotExist:
        logger.error("No se encontró la configuración predeterminada para la BusinessUnit con id=4.")
        return []
    except aiohttp.ClientError as e:
        logger.error(f"Error en la solicitud a la API de WordPress: {e}")
        return []
    except Exception as e:
        logger.error(f"Error inesperado: {e}")
        return []

    vacantes = []
    for vacante in vacantes_json:
        try:
            vacantes.append({
                "id": vacante.get("id", "ID no disponible"),
                "title": vacante.get("title", {}).get("rendered", "Título no disponible"),
                "salary": vacante.get("meta", {}).get("_salary_min", "No especificado"),
                "job_type": vacante.get("job-types", ["No especificado"]),
                "company": vacante.get("meta", {}).get("_company_name", "No especificado"),
                "whatsapp": vacante.get("meta", {}).get("_job_whatsapp", "No disponible"),
                "location": {
                    "address": vacante.get("meta", {}).get("_job_address", "No especificado"),
                    "longitude": vacante.get("meta", {}).get("_job_longitude", "No disponible"),
                    "latitude": vacante.get("meta", {}).get("_job_latitude", "No disponible")
                },
                "agenda": {
                    f"slot {i}": vacante.get("meta", {}).get(f"_job_booking_{i}", "No disponible") for i in range(1, 11)
                }
            })
        except Exception as e:
            logger.warning(f"Error procesando vacante con ID {vacante.get('id')}: {e}")
            continue
    
    logger.info(f"Vacantes procesadas: {len(vacantes)}")
    return vacantes

def register(username, email, password, name, lastname):
    """
    Realiza el registro de un usuario en WordPress.
    """
    data_session = get_session()
    if not data_session:
        return "Error obteniendo la sesión para registro."

    url = "https://huntred.com/wp-admin/admin-ajax.php"
    payload = (
        f'action=workscoutajaxregister&role=candidate&username={username}&email={email}'
        f'&password={password}&first-name={name}&last-name={lastname}&privacy_policy=on'
        f'&register_security={data_session}'
    )
    headers = {'Content-Type': 'application/x-www-form-urlencoded', 'user-agent': 'Mozilla/5.0'}
    try:
        response = s.post(url, headers=headers, data=payload)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        logger.error(f"Error registrando usuario: {e}")
        return None

def login(username, password):
    """
    Realiza el inicio de sesión de un usuario en WordPress.
    """
    data_session = get_session()
    if not data_session:
        return "Error obteniendo la sesión para login."

    url = "https://huntred.com/wp-login.php"
    payload = f'_wp_http_referer=%2Fmy-profile%2F&log={username}&pwd={password}&login_security={data_session}'
    headers = {'Content-Type': 'application/x-www-form-urlencoded', 'user-agent': 'Mozilla/5.0'}
    try:
        response = s.post(url, headers=headers, data=payload)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        return soup.find('div', {'class': 'user-avatar-title'})
    except requests.RequestException as e:
        logger.error(f"Error iniciando sesión: {e}")
        return None

def solicitud(vacante_url, name, email, message, job_id):
    """
    Envía la solicitud para una vacante específica en WordPress.
    """
    payload = f'candidate_email={email}&application_message={message}&job_id={job_id}&candidate_name={name}'
    headers = {'Content-Type': 'application/x-www-form-urlencoded', 'user-agent': 'Mozilla/5.0'}
    try:
        response = s.post(vacante_url, headers=headers, data=payload, allow_redirects=True)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        texto = soup.find("p", class_="job-manager-message").text
        return texto
    except requests.RequestException as e:
        logger.error(f"Error enviando solicitud: {e}")
        return None

def login_to_wordpress(username, password):
    """
    Realiza el login en WordPress para la administración de vacantes.
    """
    url = "https://huntred.com/wp-login.php"
    payload = {
        'log': username,
        'pwd': password,
        'wp-submit': 'Log In'
    }
    headers = {'user-agent': 'Mozilla/5.0'}
    
    try:
        response = s.post(url, headers=headers, data=payload)
        response.raise_for_status()
        
        if "dashboard" in response.url:  # Si redirige al dashboard, el login fue exitoso
            logger.info("Inicio de sesión exitoso en WordPress")
            return True
        else:
            logger.error("Error al iniciar sesión en WordPress")
            return False
    except requests.RequestException as e:
        logger.error(f"Error iniciando sesión: {e}")
        return False

def validate_json(data):
    if isinstance(data, dict):
        return data  # Retorna el dict sin procesar
    try:
        return json.loads(data)
    except json.JSONDecodeError as e:
        logger.error(f"Error al procesar JSON: {e}")
        return {}
    
async def validar_url(url, check_content=False):
    """
    Valida si una URL es accesible y opcionalmente valida su contenido.
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.head(url, timeout=5) as response:
                if response.status != 200:
                    logger.warning(f"URL inaccesible: {url} - Estado {response.status}")
                    return False
            if check_content:
                async with session.get(url, timeout=10) as response:
                    content = await response.text()
                    if 'job' not in content.lower():
                        logger.warning(f"Contenido no relacionado con trabajos en {url}")
                        return False
        return True
    except Exception as e:
        logger.error(f"Error al validar URL {url}: {e}")
        return False

def exportar_vacantes_a_wordpress(business_unit, vacantes):
    """
    Exporta vacantes a WordPress mediante el login del cliente.
    """
    try:
        configuracion = ConfiguracionBU.objects.get(business_unit=business_unit)
    except ConfiguracionBU.DoesNotExist:
        logger.error(f"No se encontró configuración para Business Unit {business_unit}")
        return False

    # Login en WordPress
    if not login_to_wordpress(configuracion.usuario_wp, configuracion.password_wp):
        logger.error("Error al iniciar sesión en WordPress.")
        return False

    # Publicar cada vacante
    for vacante in vacantes:
        logger.debug(f"Vacante procesada: {vacante}")
        payload = {
            'job_title': vacante.titulo,
            'company': vacante.empresa,
            'description': vacante.descripcion,
            'location': vacante.ubicacion,
        }
        try:
            solicitud(configuracion.api_url, configuracion.usuario_wp, payload)
            logger.info(f"Vacante publicada: {vacante.titulo}")
        except Exception as e:
            logger.error(f"Error al publicar vacante {vacante.titulo}: {e}")

    return True


class CookieManager:
    def __init__(self, dominio, credentials):
        self.login_url = dominio
        self.credentials = credentials

    async def get_new_cookies(dominio_url):
        """
        Obtiene nuevas cookies directamente desde el dominio especificado.
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(dominio_url) as response:
                if response.status == 200:
                    cookies = session.cookie_jar.filter_cookies(dominio_url)
                    return {cookie.key: cookie.value for cookie in cookies.values()}
                else:
                    raise Exception(f"Error al obtener cookies para {dominio_url}: {response.status}")


class Command(BaseCommand):
    help = "Revalida las cookies para los dominios configurados"

    def handle(self, *args, **kwargs):
        dominios = DominioScraping.objects.filter(activo=True, login_url__isnull=False)
        for dominio in dominios:
            self.stdout.write(f"Revalidando cookies para {dominio.dominio}")
            try:
                manager = CookieManager(dominio.login_url, dominio.login_credentials)
                new_cookies = asyncio.run(manager.get_new_cookies())
                dominio.cookies = json.dumps(new_cookies)
                dominio.save()
                self.stdout.write(f"Cookies actualizadas para {dominio.dominio}")
            except Exception as e:
                self.stderr.write(f"Error revalidando cookies para {dominio.dominio}: {e}")


# ========================
# Configuración General
# ========================
@dataclass
class JobListing:
    title: str
    location: str
    company: Optional[str] = None
    description: Optional[str] = None
    skills: Optional[List[str]] = None
    posted_date: Optional[str] = None
    url: Optional[str] = None
    salary: Optional[Dict[str, str]] = None  # Ejemplo: {"min": "50000", "max": "70000", "currency": "MXN"}
    responsible: Optional[str] = None  # Persona o equipo responsable de la vacante
    contract_type: Optional[str] = None  # Tipo de contrato: permanente, temporal, freelance
    experience_required: Optional[str] = None  # Años de experiencia requeridos
    education_level: Optional[str] = None  # Nivel educativo: Licenciatura, Maestría, etc.
    job_type: Optional[str] = None  # Presencial, remoto, híbrido
    benefits: Optional[List[str]] = None  # Lista de beneficios
    sectors: Optional[List[str]] = None  # Sectores o divisiones relacionadas (e.g., TI, Finanzas)
    languages_required: Optional[List[str]] = None  # Idiomas requeridos para el puesto
    application_deadline: Optional[str] = None  # Fecha límite de aplicación

def validate_job_data(job_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Valida y limpia los datos de una vacante.

    Args:
        job_data (Dict[str, Any]): Datos de la vacante a validar.

    Returns:
        Optional[Dict[str, Any]]: Datos validados y limpiados o None si faltan campos requeridos.
    """
    schema = {
        "title": str,
        "location": str,
        "company": str,
        "description": str,
        "url": str,
        # Añade más campos requeridos según sea necesario
    }
    
    validated_data = {}
    for key, expected_type in schema.items():
        value = job_data.get(key)
        if not isinstance(value, expected_type):
            logger.warning(f"Invalid {key}: {value} (Expected type: {expected_type.__name__})")
            continue
        validated_data[key] = clean_text(value)
    
    # Extracción y asociación de habilidades y divisiones
    skills = extract_skills(validated_data.get("description", ""))
    divisions = associate_divisions(skills)
    validated_data["skills"] = skills
    validated_data["divisions"] = divisions
    
    # Validar campos adicionales si es necesario
    if not all(field in validated_data for field in ["title", "location", "company", "description", "url"]):
        logger.warning(f"Missing required fields in job data: {job_data}")
        return None
    
    return validated_data

class ScrapingConfig:
    def __init__(self):
        self.RATE_LIMIT = 2  # requests por segundo
        self.MAX_RETRIES = 3
        self.TIMEOUT = 30
        self.MAX_CONCURRENT_REQUESTS = 10
        self.USER_AGENTS = USER_AGENTS

# Asegúrate de que el puerto para Prometheus esté libre o cámbialo
class ScrapingMetrics:
    def __init__(self):
        self.jobs_scraped = Counter('jobs_scraped_total', 'Total jobs scraped')
        self.scraping_duration = Histogram('scraping_duration_seconds', 'Time spent scraping')
        self.errors_total = Counter('scraping_errors_total', 'Total scraping errors')
        
        # Intenta iniciar el servidor de Prometheus en el puerto 8001 para evitar conflictos
        try:
            start_http_server(8001)
            logger.info("Servidor de métricas Prometheus iniciado en el puerto 8001")
        except OSError as e:
            if e.errno == 98:
                logger.warning("El puerto 8001 ya está en uso. No se pudo iniciar el servidor de métricas Prometheus.")
            else:
                logger.error(f"Error iniciando servidor de métricas Prometheus: {e}")

class ScrapingCache:
    def __init__(self):
        self.cache = {}
        self.TTL = 3600  # 1 hora

    async def get(self, key: str) -> Optional[Dict]:
        if key in self.cache:
            data, timestamp = self.cache[key]
            if (datetime.now() - timestamp).seconds < self.TTL:
                return data
            del self.cache[key]
        return None

    async def set(self, key: str, value: Dict):
        self.cache[key] = (value, datetime.now())

# Definición de scrapers y mapeo SCRAPER_MAP...
      
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    before_sleep=before_sleep_log(logger, logging.WARNING)
)
async def run_scraper(dominio_scraping):
    """
    Ejecuta el proceso de scraping para un dominio específico con manejo de cookies.
    """
    logger.info(f"Iniciando scraping para dominio: {dominio_scraping.dominio}")
    try:
        # Obtener el scraper adecuado para la plataforma
        scraper = get_scraper_for_platform(
            plataforma=dominio_scraping.plataforma,
            dominio_url=dominio_scraping.dominio,
            cookies=dominio_scraping.cookies
        )
        
        if scraper is None:
            logger.error(f"Scraper no inicializado para {dominio_scraping.dominio}")
            return []

        # Usar el scraper dentro de un contexto asincrónico
        async with scraper as scraper_instance:
            response = await scraper_instance.fetch(scraper_instance.url)
            # Procesar el contenido de la respuesta
            logger.info(f"Contenido obtenido para {scraper_instance.url}: {response[:200]}")  # Muestra los primeros 200 caracteres

    except Exception as e:
        logger.error(f"Error ejecutando scraper para {dominio_scraping.dominio}: {e}", exc_info=True)
        return []


    
def get_scraper_for_platform(plataforma, dominio_url, cookies=None):
    """
    Devuelve la instancia del scraper adecuado según la plataforma.
    """
    if plataforma == "workday":
        from app.utilidades.scraping import WorkdayScraper
        return WorkdayScraper(url=dominio_url, cookies=cookies)
    # Aquí puedes agregar más plataformas como "eightfold", "greenhouse", etc.
    elif plataforma == "eightfold":
        from app.utilidades.scraping import EightfoldScraper
        return EightfoldScraper(url=dominio_url, cookies=cookies)
    else:
        logger.warning(f"Plataforma no soportada: {plataforma}")
        return None



async def scrape_workflow(domains):
    """
    Ejecuta scraping en múltiples dominios de manera concurrente.
    """
    scrapers = [get_scraper_for_platform(d.platform, d.url) for d in domains]

    async def process_scraper(scraper):
        try:
            jobs = await scraper.scrape()
            validated_jobs = []
            for index, job in enumerate(jobs):
                validated_job, reason = validate_job_data(job)
                if validated_job:
                    validated_jobs.append(validated_job)
                else:
                    job_id = job.get("id", "Sin ID")
                    job_title = job.get("title", "Sin título")
                    logger.warning(
                        f"Vacante eliminada en posición {index}: ID={job_id}, Título='{job_title}'. "
                        f"Motivo: {reason}"
                    )
            await save_vacantes(validated_jobs, scraper.domain)
        except Exception as e:
            logger.error(f"Scraping failed for {scraper.domain}: {e}")

    await asyncio.gather(*(process_scraper(scraper) for scraper in scrapers))



async def fetch_with_requests(url):
    """
    Intenta obtener el contenido de la página usando requests.
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        logger.info(f"Contenido obtenido exitosamente con requests para {url}")
        return response.text
    except requests.RequestException as e:
        logger.warning(f"Error al obtener contenido con requests para {url}: {e}")
        return None

async def extraer_detalles_sublink(sublink):
    """
    Extrae los detalles específicos de un sublink.
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(sublink, timeout=10) as response:
                response.raise_for_status()
                soup = BeautifulSoup(await response.text(), 'html.parser')
                descripcion = soup.find("div", class_="descripcion").get_text(strip=True) if soup.find("div", class_="descripcion") else "Descripción no disponible."
                requisitos = soup.find("div", class_="requisitos").get_text(strip=True) if soup.find("div", class_="requisitos") else "Requisitos no disponibles."
                beneficios = soup.find("div", class_="beneficios").get_text(strip=True) if soup.find("div", class_="beneficios") else "Beneficios no disponibles."
                return {
                    "descripcion": descripcion,
                    "requisitos": requisitos,
                    "beneficios": beneficios,
                }
    except Exception as e:
        logger.error(f"Error al extraer detalles del sublink {sublink}: {e}")
        return {
            "descripcion": "Error al obtener la descripción.",
            "requisitos": "Error al obtener los requisitos.",
            "beneficios": "Error al obtener los beneficios.",
        }
  
async def fetch_with_selenium(url):
    """
    Si requests falla, intenta obtener el contenido usando Selenium.
    """
    try:
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        # Agrega más opciones si es necesario
        driver = webdriver.Chrome(options=options)
        driver.get(url)
        html_content = driver.page_source
        driver.quit()
        logger.info(f"Contenido obtenido exitosamente con Selenium para {url}")
        return html_content
    except WebDriverException as e:
        logger.error(f"Error al obtener contenido con Selenium para {url}: {e}")
        return None


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    before_sleep=before_sleep_log(logger, logging.WARNING)
)
async def fetch_with_retry(session, url):
    async with session.get(url) as response:
        response.raise_for_status()
        return await response.text()
    
def extract_data(html_content, data_type=None):
    """
    Extrae datos de una página según el tipo especificado.
    - data_type: Puede ser 'json-ld', 'javascript', o 'html'.
    """
    try:
        soup = BeautifulSoup(html_content, "html.parser")
        if data_type == "json-ld":
            script_tag = soup.find("script", type="application/ld+json")
            if script_tag:
                return json.loads(script_tag.string)
        elif data_type == "javascript":
            if "jobData" in html_content:
                start = html_content.index("jobData")
                start = html_content.index("{", start)
                end = html_content.index("};", start) + 1
                return json.loads(html_content[start:end])
        elif data_type == "html":
            job_cards = soup.find_all("div", class_="job-card")
            return [{"title": card.get_text(strip=True)} for card in job_cards]
    except Exception as e:
        logger.error(f"Error extrayendo datos ({data_type}): {e}")
    return []

async def fetch_job_details(url):
    """
    Obtiene detalles adicionales de un trabajo.
    """
    try:
        async with aiohttp.ClientSession() as session:
            response = await fetch_with_retry(session, url)
            soup = BeautifulSoup(response, "html.parser")
            description = soup.find("div", class_="job-description")
            return {"description": description.get_text(strip=True) if description else "No disponible"}
    except Exception as e:
        logger.error(f"Error obteniendo detalles del trabajo en {url}: {e}")
        return {"description": "Error al obtener detalles"}

async def scrape_single_domain(dominio):
    registro = RegistroScraping.objects.create(dominio=dominio, estado='parcial')
    logger.info(f"Iniciando scraping para dominio: {dominio.dominio} (ID registro: {registro.id})")
    try:
        scraper = get_scraper_for_platform(dominio.plataforma, dominio.dominio, dominio.cookies)
        vacantes = await scraper.scrape()
        await save_vacantes(vacantes, dominio)
        registro.estado = 'exitoso'
        registro.vacantes_encontradas = len(vacantes)
    except Exception as e:
        registro.estado = 'fallido'
        registro.error_log = str(e)
        logger.error(f"Error en scraping para {dominio.dominio}: {e}", exc_info=True)
    finally:
        registro.fecha_fin = now()
        registro.save()
        logger.info(f"Registro de scraping finalizado para {dominio.dominio} (Estado: {registro.estado})")

async def scrape_domains(dominios):
    tasks = []
    for dominio in dominios:
        tasks.append(scrape_single_domain(dominio))
    await asyncio.gather(*tasks)


    
async def scrape_domains_in_batches(dominios: List[DominioScraping], batch_size=5):
    for i in range(0, len(dominios), batch_size):
        batch = dominios[i:i + batch_size]
        await asyncio.gather(*(run_scraper(d) for d in batch))

async def run_all_scrapers():
    """
    Ejecuta scraping para todos los dominios activos.
    """
    dominios = await sync_to_async(list)(
        DominioScraping.objects.filter(activo=True)
    )

    await scrape_workflow(dominios)
    
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

# ========================
# Pipeline de Procesamiento
# ========================
class ScrapingPipeline:
    async def process(self, jobs: List[Dict]) -> List[Dict]:
        jobs = await self.clean_data(jobs)
        jobs = await self.enrich_data(jobs)
        jobs = await self.validate_data(jobs)
        return jobs

    async def clean_data(self, jobs: List[Dict]) -> List[Dict]:
        cleaned_jobs = []
        for job in jobs:
            job['title'] = job.get('title', '').strip()
            job['description'] = job.get('description', '').strip()
            if job['title'] and job['description']:
                cleaned_jobs.append(job)
        return cleaned_jobs

    async def enrich_data(self, jobs: List[Dict]) -> List[Dict]:
        for job in jobs:
            job['timestamp'] = datetime.now().isoformat()
        return jobs

    async def validate_data(self, jobs: List[Dict]) -> List[Dict]:
        valid_jobs = []
        for job in jobs:
            if self.is_valid_job(job):
                valid_jobs.append(job)
        return valid_jobs

    def is_valid_job(self, job: Dict) -> bool:
        required_fields = ['title', 'description', 'url']
        return all(field in job and job[field] for field in required_fields)

# ========================
# Clase Base Abstracta
# ========================
class BaseScraper:
    def __init__(self, url: str, config: Optional[ScrapingConfig] = None, cookies: Optional[Dict[str, str]] = None):
        self.url = url
        self.domain = url  # Atributo común para los scrapers
        self.config = config or ScraperConfig()
        self.cookies = cookies or {}
        self.session = None  # Inicializar sesión como None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=ClientTimeout(total=self.config.TIMEOUT),
            cookies=self.cookies,
            headers={'User-Agent': random.choice(self.config.USER_AGENTS)}
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def fetch(self, url: str) -> Optional[str]:
        """
        Realiza una solicitud GET al URL especificado usando la sesión activa.
        """
        try:
            async with self.session.get(url) as response:
                response.raise_for_status()
                logger.info(f"Fetch exitoso para {url}")
                return await response.text()
        except Exception as e:
            logger.error(f"Error al realizar fetch para {url}: {e}")
            return None

    async def paginate(self, base_url: str, endpoint: str, key: str, params: Optional[Dict[str, Any]] = None) -> List[Dict]:
        """
        Realiza la paginación automática y retorna una lista de resultados.
        """
        results = []
        page = 0

        while True:
            url = f"{base_url}{endpoint}?page={page}"
            logger.info(f"Procesando página: {page} - {url}")
            data = await self.fetch(url)

            if not data:
                logger.warning(f"No se encontraron más datos en {url}.")
                break

            items = extract_key(data, key)
            if not items:
                logger.warning(f"No se encontraron más elementos en {url}.")
                break

            results.extend(items)
            page += 1

        logger.info(f"Total de elementos paginados: {len(results)}")
        return results

    async def extract_details(self, job_url: str) -> Dict[str, Any]:
        """
        Extrae detalles específicos de una vacante desde su URL.
        """
        try:
            data = await self.fetch(job_url)
            if not data:
                logger.error(f"No se pudo obtener contenido para {job_url}")
                return {}

            soup = BeautifulSoup(data, "html.parser")
            description = soup.find("div", class_="job-description")
            return {
                "description": description.get_text(strip=True) if description else "No disponible"
            }
        except Exception as e:
            logger.error(f"Error al extraer detalles del trabajo en {job_url}: {e}")
            return {}

    async def scrape(self) -> List[Dict]:
        """
        Implementación principal del scraper, debe ser sobrescrito por clases hijas.
        """
        raise NotImplementedError("El método 'scrape' debe ser implementado por subclases.")

    async def transform_data(self, data: List[Dict]) -> List[Dict]:
        """
        Método opcional para transformar datos antes de devolverlos.
        Las subclases pueden sobrescribir este método.
        """
        return data


# Si no existe una definición, se puede crear una básica
class ScraperConfig:
    def __init__(self, **kwargs):
        # Agregar aquí configuraciones necesarias, si las hay
        self.headers = kwargs.get("headers", {})
        self.timeout = kwargs.get("timeout", 30)

# ========================
# Coordinador
# ========================
class ScrapingCoordinator:
    def __init__(self):
        self.config = ScrapingConfig()
        self.metrics = ScrapingMetrics()
        self.cache = ScrapingCache()
        self.pipeline = ScrapingPipeline()

    async def run_scrapers(self, scraper_configs: List[Dict]) -> Dict[str, List[Dict]]:
        results = {}
        tasks = []
        for config in scraper_configs:
            scraper_class = SCRAPER_MAP.get(config['type'])
            if not scraper_class:
                continue
            scraper = scraper_class(self.config, self.metrics, self.cache)
            tasks.append(self.run_single_scraper(scraper, config))
        completed_tasks = await asyncio.gather(*tasks, return_exceptions=True)
        for config, result in zip(scraper_configs, completed_tasks):
            if isinstance(result, Exception):
                logging.error(f"Error in scraper {config['type']}: {result}")
                continue
            results[config['type']] = result
        return results

    async def run_single_scraper(self, scraper: BaseScraper, config: Dict) -> List[Dict]:
        async with scraper:
            raw_jobs = await scraper.scrape()
            return await self.pipeline.process(raw_jobs)

