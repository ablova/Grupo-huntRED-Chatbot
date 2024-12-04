# /home/amigro/app/scraping.py

import asyncio
import aiohttp
import logging
import random
import json
import subprocess
from bs4 import BeautifulSoup
from requests import Session, RequestException
from tenacity import retry, wait_exponential, stop_after_attempt
from django.utils.timezone import now
from django.db import transaction
from app.models import DominioScraping, Vacante, RegistroScraping, PLATFORM_CHOICES, ConfiguracionBU
from .utils import clean_text
from django.db.models import Count
import scrapy
from scrapy import Spider
from selenium import webdriver


# Configurar logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# User agents
USER_AGENTS = [
    # Chrome en Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",

    # Chrome en MacOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",

    # Chrome en Linux 
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    
    # Firefox en Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/114.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0",
    
    # Firefox en MacOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/114.0",
    
    # Safari en MacOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15",

    # Edge en Windows 
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.51",
]

# Crear sesión reutilizable
session = Session()

def get_session():
    """
    Obtiene un token de sesión desde el perfil de usuario en Amigro.
    """
    headers = {'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N)'}
    try:
        response = s.get("https://amigro.org/my-profile/", headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        data = soup.find("input", {"id": "login_security"}).get("value")
        return data
    except requests.RequestException as e:
        logger.error(f"Error obteniendo sesión: {e}")
        return None

def consult(page, url, business_unit=None):
    from app.models import ConfiguracionBU
    import urllib.parse

    try:
        configuracion = (
            business_unit if business_unit else ConfiguracionBU.objects.get(id=4)
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
        response = s.get(url, headers=headers, params=payload)
        response.raise_for_status()

        logger.debug(f"Respuesta recibida: {response.status_code} {response.text[:500]}...")
        if response.headers.get('Content-Type', '').startswith('application/json'):
            return response.json()
        else:
            logger.error(f"Respuesta no válida (Content-Type: {response.headers.get('Content-Type', '')})")
            return []

    except Exception as e:
        logger.error(f"Error en consulta API ({url}): {e}", exc_info=True)
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
    
    except ConfiguracionBU.DoesNotExist:
        logger.error("No se encontró la configuración predeterminada para la BusinessUnit con id=4.")
        return []
    except requests.RequestException as e:
        logger.error(f"Error en la solicitud a la API de WordPress: {e}")
        return []
    except Exception as e:
        logger.error(f"Error inesperado: {e}")
        return []

def register(username, email, password, name, lastname):
    """
    Realiza el registro de un usuario en WordPress.
    """
    data_session = get_session()
    if not data_session:
        return "Error obteniendo la sesión para registro."

    url = "https://amigro.org/wp-admin/admin-ajax.php"
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

    url = "https://amigro.org/wp-login.php"
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
    url = "https://amigro.org/wp-login.php"
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

@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
async def fetch_with_retry(session, url):
    async with session.get(url) as response:
        response.raise_for_status()
        return await response.text()
    
class EthicalScraper:
    def __init__(self, rate_limit=2):  # 2 requests/segundo
        self.semaphore = asyncio.Semaphore(rate_limit)

    async def fetch_with_respect(self, session, url):
        async with self.semaphore:
            try:
                async with session.get(url, timeout=10) as response:
                    response.raise_for_status()
                    return await response.text()
            except Exception as e:
                logger.error(f"Error en fetch_with_respect: {e}")
                return None

class BaseScraper:
    """
    Clase base para scrapers.
    """
    def __init__(self, dominio, cookies=None):
        self.dominio = dominio
        self.headers = {'User-Agent': random.choice(USER_AGENTS)}
        self.cookies = validate_json(cookies) if cookies else None

    def get(self, url):
        """
        Realiza una solicitud HTTP GET.
        """
        try:
            response = session.get(url, headers=self.headers, cookies=self.cookies)
            response.raise_for_status()
            return response.text
        except RequestException as e:
            logger.error(f"Error al realizar la solicitud a {url}: {e}")
            return None

    async def fetch(self, session, url):
        """
        Realiza una solicitud HTTP GET utilizando aiohttp.
        """
        try:
            async with session.get(url, headers=self.headers, timeout=10) as response:
                response.raise_for_status()
                if response.headers.get("Content-Type", "").startswith("application/json"):
                    return await response.json()
                return await response.text()
        except Exception as e:
            logger.error(f"Error al realizar la solicitud a {url}: {e}")
            return None

    async def scrape(self):
        """
        Método abstracto a implementar por subclases.
        """
        raise NotImplementedError("El método 'scrape' debe ser implementado.")    
# Implementaciones específicas de scrapers
class WorkdayScraper(BaseScraper):
    async def scrape(self):
        vacantes = []
        page = 1
        logger.info(f"Iniciando WorkdayScraper para dominio: {self.dominio}")
        
        async with aiohttp.ClientSession() as session:
            while True:
                url = f"{self.dominio}?page={page}"
                try:
                    response = await self.fetch(session, url)
                    if not response:
                        logger.warning(f"Sin respuesta en {url}. Finalizando scraping.")
                        break

                    jobs = await self.parse_jobs(response)
                    if not jobs:
                        logger.info(f"No se encontraron más vacantes en {url}.")
                        break

                    vacantes.extend(jobs)
                    logger.debug(f"Página {page}: {len(jobs)} vacantes extraídas.")
                    page += 1
                except Exception as e:
                    logger.error(f"Error en scraping Workday (página {page}): {e}", exc_info=True)
                    break

        logger.info(f"WorkdayScraper finalizado. Total de vacantes: {len(vacantes)}")
        return vacantes

    async def parse_jobs(self, data):
        if isinstance(data, str):
            try:
                data = json.loads(data)  # Convertir el string a JSON
            except json.JSONDecodeError:
                logger.error("Respuesta no es JSON válido.")
                return []
        # Procesar JSON si es válido
        return [
            {
                "title": job.get("title", "No especificado"),
                "location": job.get("location", {}).get("city", "No especificado"),
                "details": await self.get_job_details(job.get("detailUrl"))
            }
            for job in data.get("jobs", [])
        ]

    async def get_job_details(self, url):
        try:
            async with aiohttp.ClientSession() as session:
                response = await self.fetch(session, url)
                soup = BeautifulSoup(response, 'html.parser')
                description = soup.find("div", class_="job-description").get_text(strip=True)
                return {"description": description}
        except Exception as e:
            logger.error(f"Error obteniendo detalles del trabajo: {e}")
            return {"description": "No disponible"}

class PhenomPeopleScraper(BaseScraper):
    async def scrape(self):
        vacantes = []
        page = 1
        logger.info(f"Iniciando PhenomPeopleScraper para dominio: {self.dominio}")
        async with aiohttp.ClientSession() as session:
            while True:
                url = f"{self.dominio}?page={page}"
                try:
                    response = await self.fetch(session, url)
                    if not response:
                        logger.warning(f"No se obtuvo respuesta en {url}. Finalizando scraping.")
                        break
                    soup = BeautifulSoup(response, "html.parser")
                    jobs = await self.parse_jobs(soup)
                    if not jobs:
                        logger.info(f"No se encontraron más vacantes en {url}.")
                        break
                    vacantes.extend(jobs)
                    logger.debug(f"Página {page}: {len(jobs)} vacantes extraídas.")
                    page += 1
                except Exception as e:
                    logger.error(f"Error en PhenomPeopleScraper (página {page}): {e}")
                    break
        return vacantes

    async def parse_jobs(self, soup):
        jobs = []
        job_cards = soup.find_all("div", class_="job-card")  # Ajustar el selector
        for card in job_cards:
            try:
                title = card.find("h3").get_text(strip=True)
                location = card.find("span", class_="job-location").get_text(strip=True)
                link = card.find("a", href=True)["href"]
                jobs.append({"title": title, "location": location, "link": link})
            except AttributeError as e:
                logger.warning(f"Error procesando una tarjeta de trabajo: {e}")
                continue
        return jobs
    
class OracleScraper(BaseScraper):
    async def scrape(self):
        vacantes = []
        page = 1
        async with aiohttp.ClientSession() as session:
            while True:
                url = f"{self.dominio}/jobs?page={page}"
                try:
                    response = await self.fetch(session, url)
                    if not response:
                        break

                    # Verifica si la respuesta es un string o JSON
                    if isinstance(response, str):
                        logger.error(f"Respuesta inesperada: texto plano en lugar de JSON")
                        break

                    jobs = await self.parse_jobs(response)
                    if not jobs:
                        break
                    vacantes.extend(jobs)
                    page += 1
                except Exception as e:
                    logger.error(f"Error en OracleScraper: {e}")
                    break
        return vacantes

    async def parse_jobs(self, data):
        vacantes = []
        for job in data.get('jobList', []):
            vacantes.append({
                "title": job.get("title", "No especificado"),
                "location": job.get("location", {}).get("city", "No especificado"),
                "link": job.get("detailUrl"),
                "details": await self.get_job_details(job.get("detailUrl"))
            })
        return vacantes

    async def get_job_details(self, job_url):
        async with aiohttp.ClientSession() as session:
            try:
                response = await self.fetch(session, f"{self.dominio}{job_url}")
                soup = BeautifulSoup(response, "html.parser")

                return {
                    "description": soup.find("div", class_="job-description").get_text(strip=True) if soup.find("div", class_="job-description") else "No disponible",
                    "requirements": soup.find("div", class_="job-requirements").get_text(strip=True) if soup.find("div", class_="job-requirements") else "No disponible",
                    "benefits": soup.find("div", class_="job-benefits").get_text(strip=True) if soup.find("div", class_="job-benefits") else "No disponible",
                }
            except Exception as e:
                logger.error(f"Error obteniendo detalles del trabajo: {e}")
                return {}

class SAPScraper(BaseScraper):
    async def scrape(self):
        vacantes = []
        page = 1
        async with aiohttp.ClientSession() as session:
            while True:
                url = f"{self.dominio}/jobs?page={page}"
                try:
                    response = await self.fetch(session, url)
                    jobs = await self.parse_jobs(response)
                    if not jobs:
                        break
                    vacantes.extend(jobs)
                    page += 1
                except Exception as e:
                    logger.error(f"Error en SAPScraper: {e}")
                    break
        return vacantes

    async def parse_jobs(self, data):
        vacantes = []
        for job in data.get('jobs', []):
            vacantes.append({
                "title": clean_text(job.get("title", "No especificado")),
                "location": clean_text(job.get("location", {}).get("city", "No especificado")),
                "link": job.get("detailUrl"),
                "details": await self.get_job_details(job.get("detailUrl"))
            })
        return vacantes

    async def get_job_details(self, url):
        try:
            async with aiohttp.ClientSession() as session:
                response = await self.fetch(session, f"{self.dominio}{url}")
                soup = BeautifulSoup(response, 'html.parser')
                return {
                    "description": soup.find("div", class_="job-description").get_text(strip=True) if soup.find("div", class_="job-description") else "No disponible",
                    "requirements": soup.find("div", class_="job-requirements").get_text(strip=True) if soup.find("div", class_="job-requirements") else "No disponible",
                    "benefits": soup.find("div", class_="job-benefits").get_text(strip=True) if soup.find("div", class_="job-benefits") else "No disponible"
                }
        except Exception as e:
            logger.error(f"Error obteniendo detalles del trabajo en SAP: {e}")
            return {}
        
class LinkedInScraper(BaseScraper):
    async def scrape(self):
        vacantes = []
        page = 0
        async with aiohttp.ClientSession() as session:
            while True:
                url = f"{self.dominio}?start={page * 25}"
                try:
                    response = await self.fetch(session, url)
                    soup = BeautifulSoup(response, 'html.parser')
                    jobs = await self.parse_jobs(soup)
                    if not jobs:
                        break
                    vacantes.extend(jobs)
                    page += 1
                except Exception as e:
                    logger.error(f"Error en LinkedInScraper: {e}")
                    break
        return vacantes

    async def parse_jobs(self, soup):
        jobs = []
        job_cards = soup.find_all("div", class_="result-card__contents")
        for card in job_cards:
            title = card.find("h3", class_="result-card__title").get_text(strip=True)
            company = card.find("h4", class_="result-card__subtitle").get_text(strip=True)
            location = card.find("span", class_="job-result-card__location").get_text(strip=True)
            link = card.find("a", class_="result-card__full-card-link")['href']
            jobs.append({"title": title, "company": company, "location": location, "link": link})
        return jobs
    
class IndeedScraper(BaseScraper):
    async def scrape(self):
        vacantes = []
        page = 0
        async with aiohttp.ClientSession() as session:
            while True:
                url = f"{self.dominio}?start={page * 10}"
                try:
                    response = await self.fetch(session, url)
                    soup = BeautifulSoup(response, 'html.parser')
                    jobs = await self.parse_jobs(soup)
                    if not jobs:
                        break
                    vacantes.extend(jobs)
                    page += 1
                except Exception as e:
                    logger.error(f"Error en IndeedScraper: {e}")
                    break
        return vacantes

    async def parse_jobs(self, soup):
        jobs = []
        job_cards = soup.find_all("div", class_="job_seen_beacon")
        for card in job_cards:
            title = card.find("h2", class_="jobTitle").get_text(strip=True)
            company = card.find("span", class_="companyName").get_text(strip=True)
            location = card.find("div", class_="companyLocation").get_text(strip=True)
            link = card.find("a", class_="jcs-JobTitle")['href']
            jobs.append({"title": title, "company": company, "location": location, "link": link})
        return jobs

class ADPScraper(BaseScraper):
    async def scrape(self):
        vacantes = []
        page = 1
        async with aiohttp.ClientSession() as session:
            while True:
                url = f"{self.dominio}/search?page={page}"
                try:
                    response = await self.fetch(session, url)
                    data = json.loads(response)
                    jobs = await self.parse_jobs(data)
                    if not jobs:
                        break
                    vacantes.extend(jobs)
                    page += 1
                except Exception as e:
                    logger.error(f"Error en ADPScraper: {e}")
                    break
        return vacantes

    async def parse_jobs(self, data):
        return [
            {
                "title": job.get("jobTitle", "No especificado"),
                "location": job.get("jobLocation", "No especificado"),
                "link": job.get("jobUrl", "No disponible"),
            }
            for job in data.get("jobs", [])
        ]

class PeopleSoftScraper(BaseScraper):
    async def scrape(self):
        vacantes = []
        async with aiohttp.ClientSession() as session:
            url = f"{self.dominio}/joblist"
            try:
                response = await self.fetch(session, url)
                soup = BeautifulSoup(response, 'html.parser')
                vacantes = await self.parse_jobs(soup)
            except Exception as e:
                logger.error(f"Error en PeopleSoftScraper: {e}")
        return vacantes

    async def parse_jobs(self, soup):
        jobs = []
        for job_card in soup.find_all("div", class_="job-card"):
            title = job_card.find("h3").get_text(strip=True)
            location = job_card.find("span", class_="location").get_text(strip=True)
            link = job_card.find("a", href=True)["href"]
            jobs.append({"title": title, "location": location, "link": link})
        return jobs

class Meta4Scraper(BaseScraper):
    async def scrape(self):
        vacantes = []
        async with aiohttp.ClientSession() as session:
            url = f"{self.dominio}/opportunities"
            try:
                response = await self.fetch(session, url)
                soup = BeautifulSoup(response, 'html.parser')
                vacantes = await self.parse_jobs(soup)
            except Exception as e:
                logger.error(f"Error en Meta4Scraper: {e}")
        return vacantes

    async def parse_jobs(self, soup):
        return [
            {
                "title": job.find("h3").get_text(strip=True),
                "location": job.find("span", class_="location").get_text(strip=True),
                "link": job.find("a", href=True)["href"],
            }
            for job in soup.find_all("div", class_="job-item")
        ]

class CornerstoneScraper(BaseScraper):
    async def scrape(self):
        vacantes = []
        page = 1
        async with aiohttp.ClientSession() as session:
            while True:
                url = f"{self.dominio}/joblist?page={page}"
                try:
                    response = await self.fetch(session, url)
                    jobs = await self.parse_jobs(response)
                    if not jobs:
                        break
                    vacantes.extend(jobs)
                    page += 1
                except Exception as e:
                    logger.error(f"Error en CornerstoneScraper: {e}")
                    break
        return vacantes

    async def parse_jobs(self, data):
        return [
            {
                "title": job.get("title", "No especificado"),
                "location": job.get("location", "No especificado"),
                "link": job.get("url", "No disponible"),
            }
            for job in data.get("jobs", [])
        ]

class UKGScraper(BaseScraper):
    async def scrape(self):
        vacantes = []
        page = 1
        async with aiohttp.ClientSession() as session:
            while True:
                url = f"{self.dominio}/search?page={page}"
                try:
                    response = await self.fetch(session, url)
                    data = json.loads(response)
                    jobs = await self.parse_jobs(data)
                    if not jobs:
                        break
                    vacantes.extend(jobs)
                    page += 1
                except Exception as e:
                    logger.error(f"Error en UKGScraper: {e}")
                    break
        return vacantes

    async def parse_jobs(self, data):
        return [
            {
                "title": job.get("title", "No especificado"),
                "location": job.get("location", "No especificado"),
                "link": job.get("url", "No disponible"),
            }
            for job in data.get("results", [])
        ]

class GreenhouseScraper(BaseScraper):
    async def scrape(self):
        vacantes = []
        page = 1
        logger.info(f"Iniciando Greenhouse para dominio: {self.dominio}")
        
        async with aiohttp.ClientSession() as session:
            while True:
                url = f"{self.dominio}?page={page}"
                try:
                    response = await self.fetch(session, url)
                    if not response:
                        logger.warning(f"Sin respuesta en {url}. Finalizando scraping.")
                        break

                    jobs = await self.parse_jobs(response)
                    if not jobs:
                        logger.info(f"No se encontraron más vacantes en {url}.")
                        break

                    vacantes.extend(jobs)
                    logger.debug(f"Página {page}: {len(jobs)} vacantes extraídas.")
                    page += 1
                except Exception as e:
                    logger.error(f"Error en scraping Workday (página {page}): {e}", exc_info=True)
                    break

        logger.info(f"Greenhouse finalizado. Total de vacantes: {len(vacantes)}")
        return vacantes

    async def parse_jobs(self, response):
        try:
            soup = BeautifulSoup(response, "html.parser")
            job_cards = soup.find_all("div", class_="opening")
            return [
                {
                    "title": job.find("a").get_text(strip=True),
                    "location": job.find("span", class_="location").get_text(strip=True),
                    "link": job.find("a")["href"]
                }
                for job in job_cards
            ]
        except Exception as e:
            logger.error(f"Error procesando trabajos: {e}")
            return []
    def get_job_details(self, link):
        """
        Obtiene detalles adicionales de una vacante desde su página específica.
        """
        try:
            full_url = f"{self.dominio}{link}"
            response = self.get(full_url)
            if not response:
                return {"description": "No disponible"}
            soup = BeautifulSoup(response, "html.parser")
            description = soup.find("div", class_="section-wrapper").get_text(strip=True)
            return {"description": description}
        except Exception as e:
            logger.error(f"Error obteniendo detalles del trabajo: {e}")
            return {"description": "Error al obtener detalles"}

class GlassdoorScraper(BaseScraper):
    async def extract_jobs(self, url):
        # Implementar scraping específico de Glassdoor
        return []

class ComputrabajoScraper(BaseScraper):
    async def extract_jobs(self, url):
        # Implementar scraping específico de Computrabajo
        return []
# Implementación específica para Accenture
class AccentureScraper(BaseScraper):
    async def scrape(self):
        vacantes = []
        page = 1
        logger.info(f"Iniciando AccentureScraper para dominio: {self.dominio}")

        async with aiohttp.ClientSession() as session:
            while True:
                url = f"{self.dominio}/mx-es/careers/jobsearch?pg={page}"
                logger.info(f"Procesando página: {page}")
                response = await self.fetch(session, url)
                
                if not response:
                    logger.warning(f"Sin respuesta en {url}. Finalizando scraping.")
                    break

                jobs = self.parse_jobs(response)
                if not jobs:
                    logger.info(f"No se encontraron más vacantes en {url}.")
                    break

                vacantes.extend(jobs)
                logger.debug(f"Página {page}: {len(jobs)} vacantes extraídas.")
                page += 1

        logger.info(f"AccentureScraper finalizado. Total de vacantes: {len(vacantes)}")
        return vacantes

    def parse_jobs(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        job_cards = soup.find_all("div", class_="cmp-teaser card")
        
        if not job_cards:
            logger.warning("No se encontraron tarjetas de empleo en la página.")
            return []

        vacantes = []
        for card in job_cards:
            try:
                # Extraer título
                title_tag = card.find("h3", class_="cmp-teaser__title")
                title = title_tag.get_text(strip=True) if title_tag else "No especificado"

                # Extraer URL de detalles
                detail_link = card.find("a", class_="cmp-teaser__title-link")
                detail_url = detail_link['href'] if detail_link and 'href' in detail_link.attrs else None
                if detail_url and not detail_url.startswith("http"):
                    detail_url = f"https://www.accenture.com{detail_url}"

                # Extraer ubicación
                region_tag = card.find("div", class_="cmp-teaser-region")
                city_tag = card.find("div", class_="cmp-teaser-city")
                region = region_tag.get_text(strip=True) if region_tag else "No especificado"
                city = city_tag.get_text(strip=True) if city_tag else "No especificado"
                location = f"{region}, {city}"

                # Extraer habilidades
                skill_tag = card.find("span", class_="cmp-teaser__job-listing-semibold skill")
                skill = skill_tag.get_text(strip=True) if skill_tag else "No especificado"

                # Extraer fecha de publicación
                posted_date_tag = card.find("p", class_="cmp-teaser__job-listing-posted-date")
                posted_date = posted_date_tag.get_text(strip=True) if posted_date_tag else "No especificado"

                # Extraer descripción (opcional, si se desea obtener del listado)
                # description_tag = card.find("div", class_="cmp-teaser__description")
                # description = description_tag.get_text(strip=True) if description_tag else "No disponible"

                # Obtener detalles adicionales si se tiene la URL
                details = {}
                if detail_url:
                    details = asyncio.run(self.get_job_details(detail_url))
                
                vacante = {
                    "title": title,
                    "location": location,
                    "skill": skill,
                    "posted_date": posted_date,
                    "detail_url": detail_url,
                    "description": details.get("description", "No disponible")
                }
                vacantes.append(vacante)
            except Exception as e:
                logger.error(f"Error al parsear una tarjeta de empleo: {e}", exc_info=True)
                continue

        return vacantes

    async def get_job_details(self, url):
        """
        Extrae detalles adicionales de una oferta de empleo específica.
        """
        try:
            async with aiohttp.ClientSession() as session:
                response = await self.fetch(session, url)
                if not response:
                    logger.warning(f"No se pudo obtener detalles de la URL: {url}")
                    return {"description": "No disponible"}

                soup = BeautifulSoup(response, 'html.parser')
                description_tag = soup.find("div", class_="job-description")
                description = description_tag.get_text(strip=True) if description_tag else "No disponible"
                return {"description": description}
        except Exception as e:
            logger.error(f"Error obteniendo detalles del trabajo en {url}: {e}")
            return {"description": "No disponible"}

SCRAPER_MAP = {
    "workday": WorkdayScraper,
    "phenom_people": PhenomPeopleScraper,
    "oracle_hcm": OracleScraper,
    "sap_successfactors": SAPScraper,
    "adp": ADPScraper,
    "peoplesoft": PeopleSoftScraper,
    "meta4": Meta4Scraper,
    "cornerstone": CornerstoneScraper,
    "ukg": UKGScraper,
    "linkedin": LinkedInScraper,
    "indeed": IndeedScraper,
    "greenhouse": GreenhouseScraper,
    "glassdor": GlassdoorScraper,
    "computrabajo": ComputrabajoScraper,
    "accenture": AccentureScraper,
    "otro": BaseScraper,  # Genérico por defecto
}

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
        
@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
async def run_scraper(dominio_scraping):
    """
    Ejecuta el proceso de scraping para un dominio específico con manejo de errores y reintentos.
    """
    logger.info(f"Iniciando scraping para dominio: {dominio_scraping.dominio}")

    try:
        # Obtener el scraper correspondiente
        scraper = get_scraper_for_platform(
            dominio_scraping.plataforma,
            dominio_scraping.dominio,
            dominio_scraping.cookies
        )

        # Validar si el scraper tiene implementado el método 'scrape'
        if isinstance(scraper, BaseScraper):
            logger.error(f"El scraper para {dominio_scraping.dominio} no está implementado.")
            return []

        logger.debug(f"Scraper seleccionado: {scraper.__class__.__name__}")

        # Ejecutar el scraping y procesar las vacantes
        vacantes = await scraper.scrape()
        if vacantes:
            logger.info(f"Vacantes encontradas: {len(vacantes)}")
        else:
            logger.warning(f"No se encontraron vacantes para {dominio_scraping.dominio}.")

        return vacantes

    except Exception as e:
        logger.error(f"Error ejecutando scraper en {dominio_scraping.dominio}: {e}", exc_info=True)
        return []


def get_scraper_for_platform(plataforma, dominio_url, cookies=None):
    scraper_class = SCRAPER_MAP.get(plataforma.lower(), BaseScraper)
    return scraper_class(dominio_url, cookies)
  
@transaction.atomic
async def save_vacantes(vacantes, dominio):
    for vacante in vacantes:
        Vacante.objects.update_or_create(
            titulo=vacante["title"],
            empresa=vacante["company"],
            defaults={
                "ubicacion": vacante["location"],
                "url_original": vacante["link"],
                "descripcion": vacante.get("details", {}).get("description", ""),
                "dominio_origen": dominio,
            }
        )
        logger.info(f"Vacante guardada: {vacante['title']} para {vacante['company']}")

async def scrape_domains(dominios):
    tasks = []
    for dominio in dominios:
        tasks.append(scrape_single_domain(dominio))
    await asyncio.gather(*tasks)

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

async def run_scraper(dominio):
    """
    Ejecuta el proceso de scraping para un dominio específico.
    """
    url = dominio.dominio
    logger.info(f"Iniciando scraping para {dominio.empresa} ({url})")

    # Primer intento con requests
    html_content = await fetch_with_requests(url)

    # Si requests falla, intentar con Selenium
    if not html_content:
        logger.info(f"Intentando con Selenium para {url}")
        html_content = await fetch_with_selenium(url)

    if not html_content:
        logger.error(f"No se pudo obtener el contenido de {url}")
        return []

    # Intentar extraer datos con diferentes métodos
    vacantes = []

    # 1. Extracción de JSON-LD
    json_ld_data = extract_json_ld(html_content, url)
    if json_ld_data:
        vacantes.extend(json_ld_data)
        logger.info(f"Vacantes extraídas con JSON-LD para {dominio.empresa}")
    else:
        # 2. Extracción de datos en JavaScript
        js_data = extract_js_data(html_content, "jobData")
        if js_data:
            vacantes.extend(js_data)
            logger.info(f"Vacantes extraídas desde JavaScript para {dominio.empresa}")
        else:
            # 3. Extracción mediante parsing de HTML
            job_data = extract_job_details(html_content)
            if job_data:
                vacantes.append(job_data)
                logger.info(f"Vacantes extraídas mediante parsing de HTML para {dominio.empresa}")
            else:
                logger.warning(f"No se pudieron extraer vacantes para {dominio.empresa}")

    return vacantes

def extract_json_ld(html_content, url):
    # Implementa la lógica para extraer datos en formato JSON-LD
    pass  # Reemplaza con tu implementación

def extract_js_data(html_content, variable_name):
    # Implementa la lógica para extraer datos de variables JavaScript
    pass  # Reemplaza con tu implementación

def extract_job_details(html_content):
    # Implementa la lógica para extraer detalles de trabajos desde el HTML
    pass  # Reemplaza con tu implementación

async def run_all_scrapers():
    """
    Ejecuta el scraper para todos los dominios activos.
    """
    dominios = DominioScraping.objects.filter(activo=True)
    tasks = [run_scraper(dominio) for dominio in dominios]
    results = await asyncio.gather(*tasks)
    # Procesa los resultados según sea necesario