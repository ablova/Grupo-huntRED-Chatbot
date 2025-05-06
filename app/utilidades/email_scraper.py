# /home/pablo/app/utilidades/email_scraper.py

import asyncio
import aioimaplib
import email
import logging
import re
import random
import gc
import os
import time
import psutil
from datetime import datetime
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from django.utils import timezone
from functools import wraps
from asgiref.sync import sync_to_async
from app.models import Vacante, BusinessUnit, ConfiguracionBU, DominioScraping, Worker, USER_AGENTS
from app.utilidades.scraping import ScrapingPipeline, get_scraper, JobListing, assign_business_unit
from django.core.exceptions import ObjectDoesNotExist
import aiohttp
import environ
from urllib.parse import urlparse, urljoin
import smtplib
from email.mime.text import MIMEText
from prometheus_client import Counter, Histogram, CollectorRegistry, start_http_server
from app.chatbot.gpt import GPTHandler
from playwright.async_api import async_playwright

# Configuración de entorno
env = environ.Env()
environ.Env.read_env(env_file='/home/pablo/.env')

# Configuración de logging
log_dir = "/home/pablo/logs"
log_file = os.path.join(log_dir, f"email_scraper_{datetime.now().strftime('%Y%m%d')}.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuración del servidor IMAP
IMAP_SERVER = env("IMAP_SERVER", default="mail.huntred.com")
EMAIL_ACCOUNT = env("EMAIL_ACCOUNT", default="pablo@huntred.com")
EMAIL_PASSWORD = env("EMAIL_PASSWORD", default="Natalia&Patricio1113!")
SMTP_SERVER = env("SMTP_SERVER", default="mail.huntred.com")
SMTP_PORT = env.int("SMTP_PORT", default=465)

# Configuración de timeouts y reintentos
CONNECTION_TIMEOUT = env.int("CONNECTION_TIMEOUT", default=90)  # Aumentado para conexiones lentas
BATCH_SIZE_DEFAULT = env.int("BATCH_SIZE_DEFAULT", default=10)  # Reducido para menor carga
MAX_RETRIES = env.int("MAX_RETRIES", default=3)
RETRY_DELAY = env.int("RETRY_DELAY", default=5)
MAX_ATTEMPTS = env.int("MAX_ATTEMPTS", default=10)

# Configuración de carpetas IMAP
FOLDER_CONFIG = {
    "inbox": "INBOX",
    "jobs_folder": "INBOX.Jobs",  # Valor inicial, se ajustará dinámicamente
    "parsed_folder": "INBOX.Parsed",
    "error_folder": "INBOX.Error",
}

# Palabras clave para identificar alertas de trabajo
JOB_KEYWORDS = [
    "job", "vacante", "opportunity", "empleo", "position", 
    "director", "analista", "gerente", "asesor", "trabajo",
    "career", "linkedin"
]

# Textos a excluir
EXCLUDED_TEXTS = [
    "unsubscribe", "manage", "help", "profile", "feed", 
    "preferences", "settings", "account", "notification"
]

# Configuración de monitoreo
DATA_MINIMIZATION = env.bool("DATA_MINIMIZATION", default=True)
LOG_DATA_PROCESSING = env.bool("LOG_DATA_PROCESSING", default=True)

# Configuración de métricas Prometheus
PROMETHEUS_PORT = env.int("PROMETHEUS_PORT", default=8002)
ALTERNATIVE_PORTS = [8003, 8004, 8005, 8006, 8007]

# Decorador para manejar conexiones IMAP
def with_imap_connection(func):
    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        retry_count = 0
        while retry_count < MAX_RETRIES:
            if not self.mail or not await self.ensure_connection():
                await self._basic_connect()
            if self.mail:
                try:
                    return await func(self, *args, **kwargs)
                except (aioimaplib.IMAP4.abort, asyncio.TimeoutError, ConnectionError) as e:
                    logger.warning(f"IMAP operation failed in {func.__name__}: {e}, retrying ({retry_count + 1}/{MAX_RETRIES})")
                    retry_count += 1
                    await asyncio.sleep(RETRY_DELAY * (2 ** retry_count))  # Backoff exponencial
                    self.mail = None
            else:
                retry_count += 1
                logger.error(f"No IMAP connection for {func.__name__}, retrying ({retry_count}/{MAX_RETRIES})")
                await asyncio.sleep(RETRY_DELAY * (2 ** retry_count))
        raise ConnectionError(f"Failed to execute {func.__name__} after {MAX_RETRIES} retries")
    return wrapper

class Metrics:
    def __init__(self):
        self.registry = CollectorRegistry()
        self.vacantes_procesadas = Counter(
            "vacantes_procesadas_total", "Total de vacantes procesadas", registry=self.registry
        )
        self.scraping_duration = Histogram(
            "scraping_duration_seconds", "Time spent scraping", registry=self.registry
        )
        self.scraping_errors = Counter(
            "scraping_errors_total", "Total scraping errors", registry=self.registry
        )

class SystemHealthMonitor:
    def __init__(self, scraper):
        self.scraper = scraper
        self.start_time = time.time()
        self.last_check = self.start_time
        self.check_interval = 60
        self.retry_delay = RETRY_DELAY  # Inicializar con el valor por defecto
        self.stats = {"memory_usage": [], "cpu_usage": [], "error_rate": 0, "success_rate": 0, "connection_failures": 0}
        self.error_threshold = 0.3
        self.memory_threshold = 500
        self.cpu_threshold = 80
        self.actions_taken = []

    async def check_health(self) -> Dict:
        current_time = time.time()
        if current_time - self.last_check < self.check_interval:
            return {}
        self.last_check = current_time

        process = psutil.Process(os.getpid())
        memory_mb = process.memory_info().rss / (1024 * 1024)
        cpu_percent = process.cpu_percent(interval=0.5)

        total_processed = self.scraper.stats["correos_procesados"]
        error_rate = self.scraper.stats["correos_error"] / total_processed if total_processed > 0 else 0
        success_rate = self.scraper.stats["correos_exitosos"] / total_processed if total_processed > 0 else 0

        self.stats["memory_usage"].append(memory_mb)
        self.stats["cpu_usage"].append(cpu_percent)
        self.stats["error_rate"] = error_rate
        self.stats["success_rate"] = success_rate

        recommendations = {}
        if memory_mb > self.memory_threshold:
            logger.warning(f"High memory usage: {memory_mb:.2f}MB")
            recommendations["run_gc"] = True
            self.actions_taken.append(f"High memory: {memory_mb:.2f}MB, running gc.collect()")
        if cpu_percent > self.cpu_threshold:
            logger.warning(f"High CPU usage: {cpu_percent:.2f}%")
            recommendations["reduce_batch"] = True
            self.actions_taken.append(f"High CPU: {cpu_percent:.2f}%, reducing batch_size")
        if error_rate > self.error_threshold:
            logger.warning(f"High error rate: {error_rate:.2%}")
            recommendations["increase_delay"] = True
            self.retry_delay = min(self.retry_delay * 2, 30)  # Ajustar el retraso
            self.actions_taken.append(f"High error rate: {error_rate:.2%}, increased retry delay to {self.retry_delay}")
        return recommendations
    
class EmailScraperV2:
    def __init__(self, email_account: str = EMAIL_ACCOUNT, password: str = EMAIL_PASSWORD, imap_server: str = IMAP_SERVER):
        self.email_account = email_account
        self.password = password
        self.imap_server = imap_server
        self.mail = None
        self.stats = {
            "correos_procesados": 0, "correos_exitosos": 0, "correos_error": 0,
            "vacantes_extraidas": 0, "vacantes_guardadas": 0,
            "processed_emails": [],
            "vacantes_completas": [],
            "vacantes_incompletas": [],
            "vacantes_ratificadas": 0
        }
        self.pipeline = ScrapingPipeline()
        self.metrics = Metrics()
        self.session = None
        self.gpt_handler = GPTHandler()
        logger.info(f"Initializing EmailScraperV2 with account: {self.email_account}")

    async def _init_http_session(self):
        """Inicializa una sesión HTTP asíncrona y GPTHandler."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=90))  # Aumentado timeout
        try:
            await self.gpt_handler.initialize()
        except Exception as e:
            logger.error(f"Error inicializando GPTHandler: {e}")

    async def _verify_folder(self) -> bool:
        """Verifica la existencia de la carpeta INBOX.Jobs usando SELECT."""
        try:
            if not self.mail:
                return False
            # Usar SELECT para verificar la carpeta directamente
            resp, data = await asyncio.wait_for(
                self.mail.select(FOLDER_CONFIG['jobs_folder']),
                timeout=CONNECTION_TIMEOUT
            )
            logger.info(f"SELECT {FOLDER_CONFIG['jobs_folder']} response: {resp}, data: {data}")
            if resp == "OK":
                logger.info(f"Folder {FOLDER_CONFIG['jobs_folder']} exists and is selectable")
                return True
            logger.error(f"Folder {FOLDER_CONFIG['jobs_folder']} not found or not selectable: {resp}, {data}")
            return False
        except Exception as e:
            logger.error(f"Error verifying folder {FOLDER_CONFIG['jobs_folder']}: {e}")
            return False

    async def _basic_connect(self) -> Optional[aioimaplib.IMAP4_SSL]:
        """Conexión básica con manejo de errores mejorado."""
        for attempt in range(MAX_RETRIES):
            try:
                if self.mail:
                    try:
                        await self.mail.logout()
                    except Exception:
                        pass
                self.mail = aioimaplib.IMAP4_SSL(self.imap_server, port=993, timeout=CONNECTION_TIMEOUT)
                await asyncio.wait_for(self.mail.wait_hello_from_server(), timeout=CONNECTION_TIMEOUT)
                await asyncio.wait_for(self.mail.login(self.email_account, self.password), timeout=CONNECTION_TIMEOUT)
                logger.info(f"IMAP login successful for {self.email_account}")
                if not await self._verify_folder():
                    logger.error("Failed to verify INBOX.Jobs folder")
                    self.mail = None
                    return None
                logger.info(f"✅ Connected to {self.imap_server} with {self.email_account}, selected {FOLDER_CONFIG['jobs_folder']}")
                return self.mail
            except aioimaplib.IMAP4.error as e:
                logger.error(f"❌ IMAP error on attempt {attempt + 1}: {e}")
            except ssl.SSLEOFError as e:
                logger.error(f"❌ SSL EOF error on attempt {attempt + 1}: {e}")
            except Exception as e:
                logger.error(f"❌ Attempt {attempt + 1} failed: {e}")
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(RETRY_DELAY * (2 ** attempt))
        self.mail = None
        return None

    async def ensure_connection(self) -> bool:
        """Verifica la conexión con manejo optimizado."""
        if not self.mail:
            return False
        try:
            await asyncio.wait_for(self.mail.noop(), timeout=10)  # Timeout reducido para NOOP
            return True
        except Exception as e:
            logger.warning(f"Connection check failed: {e}, attempting reconnect")
            self.mail = None
            return False

    @with_imap_connection
    async def fetch_email(self, email_id: str) -> Optional[email.message.Message]:
        """Obtiene un correo electrónico con validaciones mejoradas."""
        try:
            resp, data = await asyncio.wait_for(
                self.mail.fetch(email_id, "(RFC822)"),
                timeout=CONNECTION_TIMEOUT
            )
            logger.debug(f"Fetch response for email {email_id}: resp={resp}, data={data}")
            if resp != "OK":
                logger.warning(f"Fetch failed for email {email_id}: resp={resp}, data={data}")
                return None
            if not data or not isinstance(data[0], tuple) or len(data[0]) < 2:
                logger.warning(f"Invalid data structure for email {email_id}: {data}")
                return None
            email_data = data[0][1]
            # Convertir bytearray a bytes si es necesario
            if isinstance(email_data, bytearray):
                email_data = bytes(email_data)
            if not isinstance(email_data, bytes):
                logger.warning(f"Email data is not bytes for {email_id}: type={type(email_data)}")
                return None
            try:
                message = email.message_from_bytes(email_data)
                logger.debug(f"Successfully fetched and parsed email {email_id}")
                return message
            except email.errors.MessageParseError as e:
                logger.error(f"Failed to parse email {email_id}: {e}")
                return None
        except Exception as e:
            logger.error(f"Error fetching email {email_id}: {e}")
            return None

    async def fetch_html(self, url: str, cookies: Dict = None, headers: Dict = None) -> str:
        """Obtiene contenido HTML con Playwright para LinkedIn y aiohttp para otros casos."""
        if url.startswith("https://https://"):
            url = url.replace("https://https://", "https://")
        default_headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": "https://www.google.com/",
        }
        headers = {**default_headers, **(headers or {})}

        if "linkedin.com" in url:
            for attempt in range(MAX_RETRIES):
                try:
                    async with async_playwright() as p:
                        browser = await p.chromium.launch(headless=True)
                        context = await browser.new_context(
                            user_agent=headers["User-Agent"],
                            viewport={"width": 1280, "height": 720}
                        )
                        if cookies:
                            await context.add_cookies([
                                {"name": k, "value": v, "domain": "linkedin.com", "path": "/"}
                                for k, v in cookies.items()
                            ])
                        page = await context.new_page()
                        normalized_url = url.replace("/comm/jobs/", "/jobs/")
                        await page.goto(normalized_url, wait_until="networkidle", timeout=60000)
                        login_prompt = await page.query_selector("input#session_key, input#username")
                        if login_prompt:
                            logger.warning(f"Authentication prompt detected for {url}, skipping")
                            await browser.close()
                            return ""
                        await page.wait_for_selector("h1, h2, div.jobs-unified-top-card", timeout=20000)
                        content = await page.content()
                        logger.debug(f"Fetched {url} with Playwright (attempt {attempt + 1})")
                        await browser.close()
                        return content
                except Exception as e:
                    logger.error(f"Playwright error for {url} (attempt {attempt + 1}): {e}")
                    if attempt < MAX_RETRIES - 1:
                        await asyncio.sleep(RETRY_DELAY)
            return ""

        await self._init_http_session()
        for attempt in range(MAX_RETRIES):
            try:
                async with self.session.get(url, cookies=cookies or {}, headers=headers, timeout=aiohttp.ClientTimeout(total=90)) as response:
                    response.raise_for_status()
                    content = await response.text()
                    logger.debug(f"Fetched {url} with aiohttp (attempt {attempt + 1})")
                    return content
            except aiohttp.ClientResponseError as e:
                logger.error(f"HTTP error for {url} (attempt {attempt + 1}): {e}")
                if e.status == 403 and attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(RETRY_DELAY)
                else:
                    return ""
            except Exception as e:
                logger.error(f"Unexpected error fetching {url}: {e}")
                return ""
        return ""

    def format_title(self, title: str) -> str:
        """Formatea el título de una vacante."""
        replacements = {
            r"\bceo\b": "Chief Executive Officer", r"\bcoo\b": "Chief Operating Officer", r"\bcfo\b": "Chief Financial Officer",
            r"\bcto\b": "Chief Technology Officer", r"\bcmo\b": "Chief Marketing Officer", r"\bcio\b": "Chief Information Officer",
            r"\bvp\b": "Vicepresidente", r"\bdir gral\b": "Director General", r"\bgte gral\b": "Gerente General", r"\bdir\b": "Director",
            r"\bgte\b": "Gerente", r"\bjefe\b": "Jefe", r"\bsup\b": "Supervisor", r"\bcoord\b": "Coordinador", r"\bing\b": "Ingeniero",
            r"\bing\.\b": "Ingeniero", r"\blic\b": "Licenciado", r"\bmtro\b": "Maestro", r"\bdr\b": "Doctor", r"\bprof\b": "Profesor",
            r"\besp\b": "Especialista", r"\bconsult\b": "Consultor", r"\basist\b": "Asistente", r"\btec\b": "Técnico", r"\banal\b": "Analista",
            r"\bit\b": "IT", r"\brrhh\b": "Recursos Humanos", r"\bmkt\b": "Marketing", r"\bfin\b": "Finanzas", r"\blog\b": "Logística",
            r"\bventas\b": "Ventas", r"\bcompras\b": "Compras", r"\bop\b": "Operaciones", r"\bproducc\b": "Producción", r"\bmex\b": "México",
            r"\busa\b": "Estados Unidos",
        }
        title = title.lower()
        for pattern, replacement in replacements.items():
            title = re.sub(pattern, replacement, title)
        title = re.sub(r"[^a-zA-Z0-9áéíóúÁÉÍÓÚñÑüÜ&\- ]", "", title)
        title = re.sub(r"\s+", " ", title).strip()
        words = title.split()
        formatted_title = " ".join(
            word.capitalize() if word.lower() not in ["méxico", "it", "rrhh", "mkt"] else word for word in words
        )
        return formatted_title[:500]

    async def ratify_existing_vacancy(self, job_data: Dict) -> bool:
        try:
            vacante = await sync_to_async(Vacante.objects.filter(url_original=job_data["url_original"]).first)()
            if not vacante:
                return False
            updated = False
            for key, value in job_data.items():
                current_value = await sync_to_async(getattr)(vacante, key, None)
                if current_value != value and value:
                    if key == "titulo":
                        value = value[:500]
                    elif key in ["ubicacion", "requisitos", "beneficios"]:
                        value = value[:1000]
                    elif key == "descripcion":
                        value = value[:3000]
                    await sync_to_async(setattr)(vacante, key, value)
                    updated = True
            if updated:
                vacante.procesamiento_count += 1
                await sync_to_async(vacante.save)()
                self.stats["vacantes_ratificadas"] += 1
                logger.info(f"Vacante ratificada: {vacante.titulo}, intentos: {vacante.procesamiento_count}")
            return True
        except Exception as e:
            logger.error(f"Error ratificando vacante {job_data.get('titulo', 'Unknown')}: {e}")
            return False

    async def scrape_vacancy_details_from_url(self, job_data: Dict) -> Dict:
        try:
            pipeline = ScrapingPipeline()
            details = await pipeline.process([job_data])
            if not details or not isinstance(details, list) or not details[0]:
                logger.warning(f"No details from pipeline for {job_data.get('url_original', 'Unknown URL')}, trying LinkedInScraper")
                domain = await self.get_dominio_scraping(job_data["url_original"])
                if domain and domain.plataforma == "linkedin":
                    scraper = LinkedInScraper(domain, None)
                    details = [await scraper.get_job_details(job_data["url_original"])]
                    if not details or not details[0]:
                        logger.warning(f"LinkedInScraper failed for {job_data['url_original']}")
                        return job_data
                else:
                    return job_data
            details = details[0]
            return {
                "titulo": details.get("title", job_data.get("titulo", "Sin título"))[:500],
                "ubicacion": details.get("location", job_data.get("ubicacion", "No especificada"))[:300],
                "url_original": details.get("original_url", job_data.get("url_original", ""))[:1000],
                "descripcion": details.get("description", job_data.get("descripcion", "No disponible"))[:3000],
                "empresa": details.get("company", job_data.get("empresa", None)),
                "skills_required": details.get("skills", job_data.get("skills_required", [])),
                "fecha_publicacion": details.get("posted_date", job_data.get("fecha_publicacion", timezone.now())),
                "modalidad": details.get("modality", job_data.get("modalidad", None)),
                "business_unit": details.get("business_unit", job_data.get("business_unit", None)),
                "requisitos": details.get("requirements", job_data.get("requisitos", ""))[:1000],
                "beneficios": details.get("benefits", job_data.get("beneficios", ""))[:1000],
                "dominio_origen": job_data.get("dominio_origen", None)
            }
        except Exception as e:
            logger.error(f"Failed to scrape details from {job_data.get('url_original', 'Unknown URL')}: {e}")
            self.metrics.scraping_errors.inc(1)
            return job_data

    async def save_or_update_vacante(self, job_data: Dict) -> bool:
        try:
            url = job_data.get("url_original")
            if not url:
                logger.warning("No URL provided for vacancy")
                return False
            empresa = job_data.get("empresa")
            if isinstance(empresa, str):
                empresa, _ = await sync_to_async(Worker.objects.get_or_create)(
                    name=empresa, defaults={"company": empresa}
                )
            elif not empresa:
                empresa, _ = await sync_to_async(Worker.objects.get_or_create)(
                    name="Unknown", defaults={"company": "Unknown"}
                )
            vacante_data = {
                "titulo": job_data.get("titulo", "Sin título")[:500],
                "url_original": job_data.get("url_original", "")[:1000],
                "ubicacion": job_data.get("ubicacion", "No especificada")[:300],
                "descripcion": job_data.get("descripcion", "No disponible")[:3000],
                "empresa": empresa,
                "skills_required": job_data.get("skills_required", []),
                "fecha_publicacion": job_data.get("fecha_publicacion", timezone.now()),
                "modalidad": job_data.get("modalidad"),
                "business_unit": job_data.get("business_unit"),
                "requisitos": job_data.get("requisitos", "")[:1000],
                "beneficios": job_data.get("beneficios", "")[:1000],
                "dominio_origen": job_data.get("dominio_origen")
            }
            vacante, created = await sync_to_async(Vacante.objects.get_or_create)(
                url_original=vacante_data["url_original"],
                defaults=vacante_data
            )
            if not created:
                for key, value in vacante_data.items():
                    setattr(vacante, key, value)
            await sync_to_async(vacante.save)()
            self.stats["vacantes_guardadas"] += 1
            logger.info(f"Guardada vacante: {vacante_data['titulo']} ({vacante_data['url_original']})")
            return True
        except Exception as e:
            logger.error(f"Error guardando vacante {job_data.get('titulo', 'Sin título')}: {e}")
            self.metrics.scraping_errors.inc(1)
            return False

    async def get_dominio_scraping(self, url: str) -> Optional[DominioScraping]:
        domain = urlparse(url).netloc
        return await sync_to_async(DominioScraping.objects.filter(dominio__icontains=domain).first)() or \
            await sync_to_async(DominioScraping.objects.filter(dominio__icontains=domain.split('.')[-2:][0]).first)()

    async def extract_vacancies_from_html(self, html: str) -> List[Dict]:
        soup = BeautifulSoup(html, "html.parser")
        job_listings = []
        default_empresa = (await sync_to_async(Worker.objects.get_or_create)(
            name="Unknown", defaults={"company": "Unknown"}
        ))[0]
        NON_JOB_TITLES = [
            "gestionar alertas", "ver todos los empleos", "buscar empleos", "empleos guardados",
            "see more", "ver más", "alertas", "publicar", "promocionar", "premium"
        ]
        job_rows = soup.find_all("tr")
        for row in job_rows:
            link = row.find("a", href=re.compile(r"/jobs/view/"))
            if not link or any(non_job in link.get_text(strip=True).lower() for non_job in NON_JOB_TITLES):
                continue
            href = link["href"].strip()
            job_title = self.format_title(link.get_text(strip=True))[:500]
            if not job_title or len(job_title) < 10:
                continue
            full_url = href if href.startswith("http") else urljoin("https://www.linkedin.com", href)
            domain = await self.get_dominio_scraping(full_url)
            empresa_name = row.find(string=re.compile(r"^[A-Za-z0-9\s&.,-]+$", re.I)).strip() if row.find(string=re.compile(r"^[A-Za-z0-9\s&.,-]+$", re.I)) else "LinkedIn"
            empresa, _ = await sync_to_async(Worker.objects.get_or_create)(
                name=empresa_name, defaults={"company": empresa_name}
            )
            location = row.find(string=re.compile(r"(?:ciudad|área|remote|remoto|híbrido|presencial)", re.I)).strip()[:300] if row.find(string=re.compile(r"(?:ciudad|área|remote|remoto|híbrido|presencial)", re.I)) else "No especificada"
            modality = (
                "Remoto" if "remoto" in location.lower() else
                "Híbrido" if "híbrido" in location.lower() else
                "Presencial" if "presencial" in location.lower() else None
            )
            job_data = {
                "titulo": job_title,
                "url_original": full_url,
                "empresa": empresa,
                "ubicacion": location,
                "modalidad": modality,
                "descripcion": "No disponible",
                "requisitos": "",
                "beneficios": "",
                "skills_required": [],
                "fecha_publicacion": timezone.now(),
                "dominio_origen": domain
            }
            job_listings.append(job_data)
        logger.info(f"Extracted {len(job_listings)} valid vacancies from HTML")
        self.metrics.vacantes_procesadas.inc(len(job_listings))
        return job_listings

    async def process_email_batch(self, batch_size: int = BATCH_SIZE_DEFAULT):
        if not await self.ensure_connection():
            logger.error("No se pudo establecer conexión inicial con IMAP")
            return
        dynamic_delay = RETRY_DELAY
        retry_queue = []
        try:
            resp, data = await asyncio.wait_for(self.mail.search("ALL"), timeout=CONNECTION_TIMEOUT)
            if resp != "OK" or not data or not isinstance(data[0], bytes):
                logger.error(f"Error al buscar correos: resp={resp}, data={data}")
                return
            email_ids = data[0].decode().split()[:batch_size]
            if not email_ids:
                logger.info("No se encontraron correos para procesar")
                return
            sub_batch_size = max(1, batch_size // 4)
            for i in range(0, len(email_ids), sub_batch_size):
                sub_batch = email_ids[i:i + sub_batch_size]
                logger.info(f"Procesando sub-lote {i//sub_batch_size + 1} de {(len(email_ids) + sub_batch_size - 1)//sub_batch_size}")
                for email_id in sub_batch:
                    try:
                        if not email_id.isdigit() or int(email_id) <= 0:
                            logger.warning(f"ID de correo inválido: {email_id}")
                            await self.move_email(email_id, FOLDER_CONFIG["error_folder"])
                            self.stats["correos_error"] += 1
                            continue
                        gc.collect()
                        job_listings = await asyncio.wait_for(
                            self.process_job_alert_email(email_id),
                            timeout=600
                        )
                        self.stats["correos_procesados"] += 1
                        if not job_listings:
                            await self.move_email(email_id, FOLDER_CONFIG["parsed_folder"])
                            logger.debug(f"Correo {email_id} sin vacantes, movido a Parsed")
                            continue
                        successes = 0
                        for job in job_listings:
                            try:
                                if await self.save_or_update_vacante(job):
                                    successes += 1
                                    logger.info(f"Guardada vacante: {job['titulo']} ({job['url_original']})")
                            except Exception as e:
                                logger.error(f"Error guardando vacante {job['titulo']}: {e}")
                                self.metrics.scraping_errors.inc(1)
                        if successes == len(job_listings):
                            await self.move_email(email_id, FOLDER_CONFIG["parsed_folder"])
                            self.stats["correos_exitosos"] += 1
                            logger.info(f"✅ Correo {email_id} procesado: {successes}/{len(job_listings)} vacantes")
                        else:
                            retry_queue.append(email_id)
                            self.stats["correos_error"] += 1
                            logger.warning(f"⚠️ Correo {email_id} con errores: {successes}/{len(job_listings)} vacantes")
                    except asyncio.TimeoutError:
                        logger.error(f"Timeout procesando correo {email_id}")
                        retry_queue.append(email_id)
                        self.stats["correos_error"] += 1
                        self.metrics.scraping_errors.inc(1)
                    except Exception as e:
                        logger.error(f"Error procesando correo {email_id}: {e}")
                        retry_queue.append(email_id)
                        self.stats["correos_error"] += 1
                        self.metrics.scraping_errors.inc(1)
                    await asyncio.sleep(2)
                if i + sub_batch_size < len(email_ids):
                    logger.info(f"Pausa de {dynamic_delay} segundos...")
                    await asyncio.sleep(dynamic_delay)
            if retry_queue:
                logger.info(f"Reintentando {len(retry_queue)} correos...")
                for email_id in retry_queue[:MAX_RETRIES]:
                    try:
                        job_listings = await asyncio.wait_for(self.process_job_alert_email(email_id), timeout=600)
                        self.stats["correos_procesados"] += 1
                        if job_listings and all(await self.save_or_update_vacante(job) for job in job_listings):
                            await self.move_email(email_id, FOLDER_CONFIG["parsed_folder"])
                            self.stats["correos_exitosos"] += 1
                        else:
                            await self.move_email(email_id, FOLDER_CONFIG["error_folder"])
                            self.stats["correos_error"] += 1
                            logger.warning(f"Correo {email_id} movido a Error tras reintentos fallidos")
                    except Exception as e:
                        logger.error(f"Reintento fallido para correo {email_id}: {e}")
                        await self.move_email(email_id, FOLDER_CONFIG["error_folder"])
                        self.stats["correos_error"] += 1
                    await asyncio.sleep(dynamic_delay)
        except Exception as e:
            logger.error(f"Error en process_email_batch: {e}")
            self.metrics.scraping_errors.inc(1)

    async def process_job_alert_email(self, email_id: str) -> List[Dict]:
        message = await self.fetch_email(email_id)
        if not message:
            return []
        
        platform = await self.ml_scraper.classify_email(message)
        if platform == "unknown":
            await self.move_email(email_id, FOLDER_CONFIG["parsed_folder"])
            return []
        
        job_listings = await self.ml_scraper.extract_vacancies_from_email(message)
        enriched_jobs = await asyncio.gather(
            *(self.scrape_vacancy_details_from_url(job) for job in job_listings),
            return_exceptions=True
        )
        valid_jobs = [job for job in enriched_jobs if isinstance(job, dict)]
        return valid_jobs

    @with_imap_connection
    async def move_email(self, email_id: str, folder: str):
        try:
            if await self.ensure_connection():
                await self.mail.copy(email_id, folder)
                await self.mail.store(email_id, "+FLAGS", "\\Deleted")
                await self.mail.expunge()
                logger.debug(f"Email {email_id} moved to {folder} and deleted from INBOX.Jobs")
        except Exception as e:
            logger.error(f"Error moving email {email_id} to {folder}: {e}")

    async def send_summary_email(self, actions_taken: List[str]):
        processed_emails_info = "\n".join(
            f"ID: {email['email_id']}, Subject: {email['subject'][:50]}, Domain: {email['domain']}"
            for email in self.stats["processed_emails"]
        )
        vacantes_completas_info = "\n".join(self.stats["vacantes_completas"]) if self.stats["vacantes_completas"] else "Ninguna"
        vacantes_incompletas_info = "\n".join(self.stats["vacantes_incompletas"]) if self.stats["vacantes_incompletas"] else "Ninguna"
        actions_info = "\n".join(actions_taken) if actions_taken else "No corrective actions taken."
        msg = MIMEText(
            f"Scraping Summary:\n"
            f"Emails processed: {self.stats['correos_procesados']}\n"
            f"Successful emails: {self.stats['correos_exitosos']}\n"
            f"Emails with errors: {self.stats['correos_error']}\n"
            f"Vacancies extracted: {self.stats['vacantes_extraidas']}\n"
            f"Vacancies saved: {self.stats['vacantes_guardadas']}\n\n"
            f"Vacantes completas:\n{vacantes_completas_info}\n\n"
            f"Vacantes incompletas:\n{vacantes_incompletas_info}\n\n"
            f"Processed emails details:\n{processed_emails_info}\n\n"
            f"Issues detected and corrective actions:\n{actions_info}"
        )
        msg["Subject"] = "Email Scraper Summary"
        msg["From"] = self.email_account
        msg["To"] = "pablo@huntred.com, huntred.com@gmail.com"
        try:
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=30) as server:
                server.starttls()
                server.login(self.email_account, self.password)
                server.send_message(msg)
                logger.info("📧 Summary sent to pablo@huntred.com")
        except Exception as e:
            logger.error(f"Error sending summary email: {e}")

async def process_all_emails():
    scraper = EmailScraperV2()
    health_monitor = SystemHealthMonitor(scraper)
    batch_size = BATCH_SIZE_DEFAULT
    attempt = 0
    prometheus_started = False
    for port in [PROMETHEUS_PORT] + ALTERNATIVE_PORTS:
        try:
            start_http_server(port, registry=scraper.metrics.registry)
            logger.info(f"Prometheus server started on port {port}")
            prometheus_started = True
            break
        except OSError as e:
            logger.warning(f"Failed to start Prometheus server on port {port}: {e}")
    if not prometheus_started:
        logger.error("Could not start Prometheus server on any available port")
    while attempt < MAX_ATTEMPTS:
        attempt += 1
        if not await scraper._basic_connect():
            logger.error(f"Could not connect to IMAP server, attempt {attempt}/{MAX_ATTEMPTS}")
            if attempt == MAX_ATTEMPTS:
                logger.error("Max connection attempts reached, stopping...")
                await scraper.send_summary_email(health_monitor.actions_taken + ["Failed to connect after max attempts"])
                break
            await asyncio.sleep(health_monitor.retry_delay * (2 ** attempt))
            continue
        try:
            resp, data = await asyncio.wait_for(scraper.mail.search("ALL"), timeout=CONNECTION_TIMEOUT)
            if resp != "OK":
                logger.error(f"Failed to search emails: {resp}")
                break
            email_ids = data[0].decode().split()
            if not email_ids:
                logger.info("No more emails in INBOX/Jobs, processing finished")
                break
            for i in range(0, len(email_ids), batch_size):
                recommendations = await health_monitor.check_health()
                if recommendations.get("reduce_batch"):
                    batch_size = max(1, batch_size // 2)
                    logger.info(f"Batch size reducido a {batch_size} debido a alta carga")
                if recommendations.get("run_gc"):
                    gc.collect()
                    logger.info("Executed gc.collect() to free memory")
                current_batch_size = min(batch_size, len(email_ids) - i)
                batch = email_ids[i:i + current_batch_size]
                logger.info(f"Processing batch of {current_batch_size} emails out of {len(email_ids)} remaining")
                await scraper.process_email_batch(batch_size=current_batch_size)
                await scraper.send_summary_email(health_monitor.actions_taken)
                scraper.stats["vacantes_completas"] = []
                scraper.stats["vacantes_incompletas"] = []
                if i + current_batch_size < len(email_ids):
                    logger.info(f"Pausing {health_monitor.retry_delay} seconds before the next batch...")
                    await asyncio.sleep(health_monitor.retry_delay)
        except Exception as e:
            logger.error(f"Unexpected error in process_all_emails: {e}")
        finally:
            if scraper.mail:
                try:
                    await scraper.mail.logout()
                    logger.info("IMAP connection closed")
                except Exception as e:
                    logger.warning(f"Error closing IMAP connection: {e}")
                scraper.mail = None
            if scraper.session and not scraper.session.closed:
                await scraper.session.close()
                logger.info("HTTP session closed")
        logger.info("Last batch processed, finishing...")
        break

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ai_huntred.settings")
    import django
    django.setup()
    asyncio.run(process_all_emails())