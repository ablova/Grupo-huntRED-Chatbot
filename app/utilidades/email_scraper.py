# /home/pablo/app/utilidades/email_scraper.py
import asyncio
import aioimaplib
import email
import logging
import re
import random
import os
from datetime import datetime
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from django.utils import timezone
from functools import wraps
from asgiref.sync import sync_to_async
from app.models import Vacante, BusinessUnit, ConfiguracionBU, DominioScraping, Worker, USER_AGENTS
from app.ml.utils.scrape import MLScraper
from app.utilidades.scraping_utils import ScrapingMetrics, SystemHealthMonitor, ScrapingCache, generate_summary_report
from app.chatbot.gpt import GPTHandler
from urllib.parse import urlparse, urljoin
import aiohttp
import environ
import smtplib
from email.mime.text import MIMEText
from playwright.async_api import async_playwright

env = environ.Env()
environ.Env.read_env(env_file='/home/pablo/.env')

log_dir = "/home/pablo/logs"
log_file = os.path.join(log_dir, f"email_scraper_{datetime.now().strftime('%Y%m%d')}.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler(log_file), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

IMAP_SERVER = env("IMAP_SERVER", default="mail.huntred.com")
EMAIL_ACCOUNT = env("EMAIL_ACCOUNT", default="pablo@huntred.com")
EMAIL_PASSWORD = env("EMAIL_PASSWORD", default="Natalia&Patricio1113!")
SMTP_SERVER = env("SMTP_SERVER", default="mail.huntred.com")
SMTP_PORT = env.int("SMTP_PORT", default=465)
CONNECTION_TIMEOUT = env.int("CONNECTION_TIMEOUT", default=90)
BATCH_SIZE_DEFAULT = env.int("BATCH_SIZE_DEFAULT", default=10)
MAX_RETRIES = env.int("MAX_RETRIES", default=3)
RETRY_DELAY = env.int("RETRY_DELAY", default=5)
MAX_ATTEMPTS = env.int("MAX_ATTEMPTS", default=10)

FOLDER_CONFIG = {
    "inbox": "INBOX",
    "jobs_folder": "INBOX.Jobs",
    "parsed_folder": "INBOX.Parsed",
    "error_folder": "INBOX.Error",
}

JOB_KEYWORDS = [
    "job", "vacante", "opportunity", "empleo", "position", 
    "director", "analista", "gerente", "asesor", "trabajo",
    "career", "linkedin"
]
EXCLUDED_TEXTS = [
    "unsubscribe", "manage", "help", "profile", "feed", 
    "preferences", "settings", "account", "notification"
]

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
        self.metrics = ScrapingMetrics("email_scraper")
        self.health_monitor = SystemHealthMonitor()
        self.cache = ScrapingCache()
        self.session = None
        self.gpt_handler = GPTHandler()
        self.ml_scraper = MLScraper()
        self.nlp = NLPProcessor(language="es", mode="opportunity")
        self.skill_classifier = SkillClassifier()
        logger.info(f"Initializing EmailScraperV2 with account: {self.email_account}")

    async def process_email_content(self, content: str) -> Dict:
        """Procesa el contenido del correo usando NLP y clasificación de habilidades."""
        try:
            # Analizar el contenido
            analysis = await self.nlp.analyze(content)
            
            # Clasificar habilidades
            if analysis.get("skills"):
                skill_classification = await self.skill_classifier.classify_skills(analysis["skills"])
                analysis["skill_classification"] = skill_classification
            
            # Extraer información relevante
            job_info = await self._extract_job_info(analysis)
            
            # Validar y completar información
            complete_info = await self._validate_and_complete_info(job_info)
            
            return complete_info
            
        except Exception as e:
            logger.error(f"Error processing email content: {e}")
            return {"error": str(e)}

    async def _extract_job_info(self, analysis: Dict) -> Dict:
        """Extrae información de trabajo del análisis."""
        job_info = {
            "title": analysis.get("entities", {}).get("job_title"),
            "company": analysis.get("entities", {}).get("company"),
            "location": analysis.get("entities", {}).get("location"),
            "description": analysis.get("description"),
            "skills": analysis.get("skills", []),
            "requirements": analysis.get("requirements", []),
            "salary": analysis.get("salary", {})
        }
        return job_info

    async def _validate_and_complete_info(self, job_info: Dict) -> Dict:
        """Valida y completa la información del trabajo."""
        # Validar campos requeridos
        required_fields = ["title", "company", "description"]
        missing_fields = [f for f in required_fields if not job_info.get(f)]
        
        if missing_fields:
            # Intentar completar campos faltantes
            job_info = await self._complete_missing_fields(job_info)
            
            # Si aún faltan campos, marcar como incompleto
            missing_fields = [f for f in required_fields if not job_info.get(f)]
            if missing_fields:
                job_info["status"] = "incomplete"
                job_info["missing_fields"] = missing_fields
            else:
                job_info["status"] = "complete"
        
        return job_info

    async def _complete_missing_fields(self, job_info: Dict) -> Dict:
        """Completar campos faltantes usando GPT y ML."""
        try:
            # Usar GPT para completar campos faltantes
            prompt = f"Completa la información faltante para el puesto: {job_info.get('title', '')}\n"
            for field in ["company", "location", "description"]:
                if not job_info.get(field):
                    prompt += f"{field}:\n"
            
            response = await self.gpt_handler.generate_response(prompt)
            data = json.loads(response)
            
            # Actualizar información
            for field in data:
                if field in job_info and not job_info[field]:
                    job_info[field] = data[field]
                    
            return job_info
            
        except Exception as e:
            logger.error(f"Error completing missing fields: {e}")
            return job_info

    async def _init_http_session(self):
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=90))
        await self.gpt_handler.initialize()

    async def create_folders(self):
        try:
            for folder in FOLDER_CONFIG.values():
                resp, data = await self.mail.create(folder)
                if resp == "OK":
                    logger.info(f"Carpeta {folder} creada o ya existe")
                else:
                    logger.error(f"No se pudo crear la carpeta {folder}: {data}")
        except Exception as e:
            logger.error(f"Error creando carpetas: {e}")

    async def _basic_connect(self) -> Optional[aioimaplib.IMAP4_SSL]:
        for attempt in range(MAX_RETRIES):
            try:
                if self.mail:
                    await self.mail.logout()
                self.mail = aioimaplib.IMAP4_SSL(self.imap_server, port=993, timeout=CONNECTION_TIMEOUT)
                await asyncio.wait_for(self.mail.wait_hello_from_server(), timeout=CONNECTION_TIMEOUT)
                await asyncio.wait_for(self.mail.login(self.email_account, self.password), timeout=CONNECTION_TIMEOUT)
                await self.create_folders()
                resp, data = await asyncio.wait_for(self.mail.select(FOLDER_CONFIG['jobs_folder']), timeout=CONNECTION_TIMEOUT)
                if resp == "OK":
                    logger.info(f"Connected to {self.imap_server} with {self.email_account}")
                    return self.mail
                logger.error(f"Failed to select {FOLDER_CONFIG['jobs_folder']}: {data}")
                self.mail = None
                return None
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed: {e}")
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(self.health_monitor.retry_delay * (2 ** attempt))
        self.mail = None
        return None

    async def ensure_connection(self) -> bool:
        if not self.mail:
            return False
        try:
            await asyncio.wait_for(self.mail.noop(), timeout=10)
            return True
        except Exception as e:
            logger.warning(f"Connection check failed: {e}")
            self.mail = None
            return False

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
                        logger.warning(f"IMAP operation failed in {func.__name__}: {e}")
                        retry_count += 1
                        await asyncio.sleep(self.health_monitor.retry_delay * (2 ** retry_count))
                        self.mail = None
                else:
                    retry_count += 1
                    await asyncio.sleep(self.health_monitor.retry_delay * (2 ** retry_count))
            raise ConnectionError(f"Failed to execute {func.__name__} after {MAX_RETRIES} retries")
        return wrapper

    @with_imap_connection
    async def fetch_email(self, email_id: str) -> Optional[email.message.Message]:
        try:
            resp, data = await asyncio.wait_for(self.mail.fetch(email_id, "(RFC822)"), timeout=CONNECTION_TIMEOUT)
            if resp != "OK" or not data or not isinstance(data[0], tuple) or len(data[0]) < 2:
                logger.warning(f"Fetch failed for email {email_id}: {data}")
                return None
            email_data = data[0][1]
            if isinstance(email_data, bytearray):
                email_data = bytes(email_data)
            if not isinstance(email_data, bytes):
                logger.warning(f"Email data is not bytes for {email_id}")
                return None
            message = email.message_from_bytes(email_data)
            logger.debug(f"Fetched email {email_id}")
            return message
        except Exception as e:
            logger.error(f"Error fetching email {email_id}: {e}")
            return None

    async def is_email_processed(self, message: email.message.Message) -> bool:
        message_id = message.get("Message-ID", "").strip()
        if not message_id:
            return False
        cache_key = f"processed_email_{message_id}"
        if await self.cache.get(cache_key):
            logger.info(f"Correo duplicado detectado: {message_id}")
            return True
        await self.cache.set(cache_key, {"processed": True})
        return False

    async def fetch_html(self, url: str, cookies: Dict = None, headers: Dict = None) -> str:
        """Obtiene contenido HTML de una URL con manejo de errores mejorado."""
        url = url.replace("https://https://", "https://")
        default_headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": "https://www.google.com/",
        }
        headers = {**default_headers, **(headers or {})}
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        
        # Verificar si ya se ha procesado esta URL
        cache_key = f"html_{url}"
        cached = await self.cache.get(cache_key)
        if cached:
            logger.info(f"Using cached content for {url}")
            return cached
            
        try:
            async with self.session.get(url, headers=headers, cookies=cookies) as response:
                if response.status == 200:
                    content = await response.text()
                    # Guardar en cache con TTL
                    await self.cache.set(cache_key, content, ttl=3600)  # 1 hora
                    return content
                else:
                    logger.error(f"Failed to fetch {url}: {response.status}")
                    return ""
                    
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return ""

        if "linkedin.com" in domain:
            for attempt in range(MAX_RETRIES):
                async with async_playwright() as p:
                    browser = await p.chromium.launch(headless=True)
                    try:
                        context = await browser.new_context(user_agent=headers["User-Agent"], viewport={"width": 1280, "height": 720})
                        if cookies:
                            await context.add_cookies([
                                {"name": k, "value": v, "domain": domain, "path": "/"}
                                for k, v in cookies.items()
                            ])
                        page = await context.new_page()
                        normalized_url = url.replace("/comm/jobs/", "/jobs/")
                        await page.goto(normalized_url, wait_until="networkidle", timeout=60000)
                        login_prompt = await page.query_selector("input#session_key, input#username")
                        if login_prompt:
                            logger.warning(f"Authentication prompt detected for {url}")
                            return ""
                        await page.wait_for_selector("h1, h2, div.jobs-unified-top-card", timeout=20000)
                        content = await page.content()
                        logger.debug(f"Fetched {url} with Playwright (attempt {attempt + 1})")
                        return content
                    finally:
                        await browser.close()
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(self.health_monitor.retry_delay)
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
                    await asyncio.sleep(self.health_monitor.retry_delay)
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
            details = await self.ml_scraper.extract_job_details(job_data["url_original"], job_data.get("dominio_origen", {}).plataforma)
            if not details:
                logger.warning(f"No details from MLScraper for {job_data.get('url_original')}")
                domain = await self.get_dominio_scraping(job_data["url_original"])
                if domain and domain.plataforma == "linkedin":
                    content = await self.fetch_html(job_data["url_original"], domain.cookies)
                    details = await self.ml_scraper.extract_job_details(content, "linkedin")
            if not details:
                return job_data
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
            self.metrics.errors_total.inc()
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

    async def fallback_extract_vacancies(self, message: email.message.Message) -> List[Dict]:
        job_listings = []
        text_content = ""
        for part in message.walk():
            if part.get_content_type() == "text/plain":
                text_content += part.get_payload(decode=True).decode()
            elif part.get_content_type() == "text/html":
                html = part.get_payload(decode=True).decode()
                soup = BeautifulSoup(html, "html.parser")
                text_content += soup.get_text()
        
        if any(keyword in text_content.lower() for keyword in JOB_KEYWORDS) and \
           not any(excluded in text_content.lower() for excluded in EXCLUDED_TEXTS):
            urls = re.findall(r'https?://[^\s<>"]+|www\.[^\s<>"]+', text_content)
            for url in urls:
                domain = await self.get_dominio_scraping(url)
                job_data = {
                    "titulo": "Vacante sin título",
                    "url_original": url,
                    "empresa": None,
                    "ubicacion": "No especificada",
                    "descripcion": "Extraído de correo",
                    "skills_required": [],
                    "fecha_publicacion": timezone.now(),
                    "dominio_origen": domain
                }
                job_listings.append(await self.scrape_vacancy_details_from_url(job_data))
        return job_listings

    async def process_job_alert_email(self, email_id: str) -> List[Dict]:
        message = await self.fetch_email(email_id)
        if not message or await self.is_email_processed(message):
            return []
        
        platform = await self.ml_scraper.classify_email(message)
        job_listings = []
        if platform == "unknown":
            job_listings = await self.fallback_extract_vacancies(message)
        else:
            job_listings = await self.ml_scraper.extract_vacancies_from_email(message)
        
        enriched_jobs = await asyncio.gather(
            *(self.scrape_vacancy_details_from_url(job) for job in job_listings),
            return_exceptions=True
        )
        valid_jobs = [job for job in enriched_jobs if isinstance(job, dict)]
        self.stats["vacantes_extraidas"] += len(valid_jobs)
        self.metrics.emails_processed.inc()
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

    async def send_summary_email(self):
        msg = MIMEText(await generate_summary_report(self.stats, self.health_monitor.actions_taken))
        msg["Subject"] = "Email Scraper Summary"
        msg["From"] = self.email_account
        msg["To"] = "pablo@huntred.com, huntred.com@gmail.com"
        try:
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=30) as server:
                server.starttls()
                server.login(self.email_account, self.password)
                server.send_message(msg)
                logger.info("Summary email sent")
        except Exception as e:
            logger.error(f"Error sending summary email: {e}")

    
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


async def process_all_emails():
    scraper = EmailScraperV2()
    batch_size = BATCH_SIZE_DEFAULT
    attempt = 0
    while attempt < MAX_ATTEMPTS:
        attempt += 1
        if not await scraper._basic_connect():
            logger.error(f"Could not connect to IMAP server, attempt {attempt}/{MAX_ATTEMPTS}")
            if attempt == MAX_ATTEMPTS:
                await scraper.send_summary_email()
                break
            await asyncio.sleep(scraper.health_monitor.retry_delay * (2 ** attempt))
            continue
        try:
            resp, data = await asyncio.wait_for(scraper.mail.search("ALL"), timeout=CONNECTION_TIMEOUT)
            if resp != "OK":
                logger.error(f"Failed to search emails: {resp}")
                break
            email_ids = data[0].decode().split()
            if not email_ids:
                logger.info("No more emails in INBOX/Jobs")
                break
            for i in range(0, len(email_ids), batch_size):
                recommendations = await scraper.health_monitor.check_health(scraper.stats["correos_procesados"], scraper.stats["correos_error"])
                if recommendations.get("reduce_batch"):
                    batch_size = max(1, batch_size // 2)
                    logger.info(f"Batch size reduced to {batch_size}")
                if recommendations.get("run_gc"):
                    gc.collect()
                    logger.info("Executed gc.collect()")
                current_batch_size = min(batch_size, len(email_ids) - i)
                batch = email_ids[i:i + current_batch_size]
                logger.info(f"Processing batch of {current_batch_size} emails")
                await scraper.process_email_batch(batch_size=current_batch_size)
                await scraper.send_summary_email()
                if i + current_batch_size < len(email_ids):
                    await asyncio.sleep(scraper.health_monitor.retry_delay)
        finally:
            if scraper.mail:
                await scraper.mail.logout()
            if scraper.session and not scraper.session.closed:
                await scraper.session.close()
        break

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ai_huntred.settings")
    import django
    django.setup()
    asyncio.run(process_all_emails())