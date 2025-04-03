# /home/pablo/app/utilidades/email_scraper.py
import asyncio
import aioimaplib
import email
import logging
import re
import json
import random
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from django.utils import timezone
from asgiref.sync import sync_to_async
from app.models import Vacante, BusinessUnit, DominioScraping, Worker, ConfiguracionBU, USER_AGENTS
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import aiohttp
import environ
from urllib.parse import urlparse, urljoin
from app.chatbot.nlp import NLPProcessor

# Configuración de entorno
env = environ.Env()
environ.Env.read_env(env_file='/home/pablo/.env')

# Configuración de logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("/home/pablo/logs/email_scraper_v2.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Constantes
IMAP_SERVER = env("IMAP_SERVER", default="mail.huntred.com")
CONNECTION_TIMEOUT = 30
BATCH_SIZE_DEFAULT = 20
JOB_KEYWORDS = ["job", "vacante", "opportunity", "empleo", "position", "director", "analista", "gerente", "asesor"]
EXCLUDED_TEXTS = ["unsubscribe", "manage", "help", "profile", "feed"]
FOLDER_CONFIG = {
    "inbox": "INBOX",
    "jobs_folder": "INBOX.Jobs",
    "parsed_folder": "INBOX.Parsed",
    "error_folder": "INBOX.Error",
}

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

# Instancia global de NLPProcessor
try:
    NLP_PROCESSOR = NLPProcessor(language="es", mode="opportunity", analysis_depth="deep")
except Exception as e:
    logger.warning(f"No se pudo inicializar NLPProcessor: {e}")
    NLP_PROCESSOR = None

class EmailScraperV2:
    def __init__(self, email_account: str, password: str, imap_server: str = IMAP_SERVER):
        self.email_account = email_account
        self.password = password
        self.imap_server = imap_server
        self.mail = None
        self.retry_count = 3
        self.retry_delay = 5  # segundos
        self.max_connection_attempts = 3
        self.connection_timeout = CONNECTION_TIMEOUT

    async def connect(self) -> Optional[aioimaplib.IMAP4_SSL]:
        for attempt in range(self.max_connection_attempts):
            try:
                if self.mail:
                    try:
                        await self.mail.logout()
                    except:
                        pass
                self.mail = aioimaplib.IMAP4_SSL(self.imap_server, timeout=self.connection_timeout)
                await asyncio.wait_for(self.mail.wait_hello_from_server(), timeout=self.connection_timeout)
                await asyncio.wait_for(self.mail.login(self.email_account, self.password), timeout=self.connection_timeout)
                await self.mail.select(FOLDER_CONFIG["jobs_folder"])
                logger.info(f"Conectado a {self.imap_server} con {self.email_account}")
                return self.mail
            except asyncio.TimeoutError:
                logger.error(f"Timeout en intento {attempt + 1}/{self.max_connection_attempts}")
            except Exception as e:
                logger.error(f"Error en intento {attempt + 1}/{self.max_connection_attempts}: {e}")
            if attempt < self.max_connection_attempts - 1:
                await asyncio.sleep(self.retry_delay)
        logger.error(f"No se pudo conectar tras {self.max_connection_attempts} intentos")
        return None

    async def ensure_connection(self) -> bool:
        try:
            if not self.mail:
                return await self.connect() is not None
            await asyncio.wait_for(self.mail.noop(), timeout=self.connection_timeout)
            return True
        except Exception as e:
            logger.warning(f"Conexión perdida: {e}")
            return await self.connect() is not None

    async def fetch_email(self, email_id: str) -> Optional[email.message.Message]:
        for attempt in range(self.retry_count):
            try:
                if not await self.ensure_connection():
                    return None
                resp, data = await asyncio.wait_for(
                    self.mail.fetch(email_id, "(RFC822)"),
                    timeout=self.connection_timeout
                )
                if resp != "OK" or not data or len(data) < 2:
                    logger.error(f"Fallo al obtener correo {email_id}: {resp} {data}")
                    if attempt < self.retry_count - 1:
                        await asyncio.sleep(self.retry_delay)
                    continue
                if isinstance(data[1], (bytes, bytearray)):
                    message = email.message_from_bytes(data[1])
                    logger.debug(f"Correo {email_id} obtenido, longitud: {len(data[1])}")
                    return message
                logger.error(f"No se encontró cuerpo válido para {email_id}: {data}")
                if attempt < self.retry_count - 1:
                    await asyncio.sleep(self.retry_delay)
            except Exception as e:
                logger.error(f"Error al obtener correo {email_id} en intento {attempt + 1}: {e}")
                if attempt < self.retry_count - 1:
                    await asyncio.sleep(self.retry_delay)
        return None

    def format_title(self, title: str) -> str:
        replacements = {
            "cta": "cuenta",
            "cta.": "cuenta",
            "mex": "México",
            "dir": "dirección",
            "gte": "gerente",
            "esp": "especialista",
        }
        title = title.lower()
        for old, new in replacements.items():
            title = title.replace(old, new)
        title = re.sub(r'\s+', ' ', title).strip()
        return title.title()[:100]  # Truncar a 100 caracteres aquí también

    async def get_dominio_scraping(self, url: str) -> Optional[DominioScraping]:
        domain = urlparse(url).netloc
        return await sync_to_async(DominioScraping.objects.filter(dominio__contains=domain).first)()

    async def get_valid_senders(self) -> List[str]:
        dominios = await sync_to_async(list)(DominioScraping.objects.filter(email_scraping_enabled=True).only('valid_senders'))
        return list(set(sender for dominio in dominios for sender in (dominio.valid_senders or [])))

    def extract_vacancies_from_html(self, html: str) -> List[Dict]:
        try:
            soup = BeautifulSoup(html, "html.parser")
            job_listings = []
            for link in soup.find_all("a", href=True):
                link_text = link.get_text(strip=True).lower()
                href = link["href"].lower()
                if any(excluded in link_text for excluded in EXCLUDED_TEXTS):
                    continue
                if href.startswith("https://https://"):
                    href = href.replace("https://https://", "https://")
                elif not href.startswith("http"):
                    href = urljoin("https://santander.wd3.myworkdayjobs.com", href)
                if any(keyword in link_text for keyword in JOB_KEYWORDS) or re.search(r"/job/", href):
                    job_title = self.format_title(link.get_text(strip=True))
                    job_link = href
                    location = ""
                    next_text = link.find_next(string=True)
                    if next_text and "(" in next_text and ")" in next_text:
                        location = re.search(r'\((.*?)\)', next_text).group(1)
                    job_listings.append({
                        "titulo": job_title,
                        "url_original": job_link,
                        "empresa": None,
                        "ubicacion": location or "No especificada",
                        "descripcion": "",
                        "modalidad": None,
                        "requisitos": "",
                        "beneficios": "",
                        "skills_required": [],
                        "fecha_publicacion": timezone.now(),
                        "dominio_origen": None,
                        "business_unit": None
                    })
            logger.debug(f"Extraídas {len(job_listings)} vacantes de HTML")
            return job_listings
        except Exception as e:
            logger.error(f"Error al extraer vacantes de HTML: {e}")
            return []

    async def process_job_alert_email(self, email_id: str) -> List[Dict]:
        message = await self.fetch_email(email_id)
        if not message:
            logger.info(f"No se obtuvo correo para ID {email_id}")
            await self.mail.copy(email_id, FOLDER_CONFIG["error_folder"])
            await self.mail.store(email_id, "+FLAGS", "\\Deleted")
            return []

        sender = message.get("From", "").lower()
        subject = message.get("Subject", "").lower()
        valid_senders = await self.get_valid_senders()
        is_valid_sender = any(valid_sender in sender for valid_sender in valid_senders)
        is_job_alert = any(keyword in subject for keyword in JOB_KEYWORDS)

        if not (is_valid_sender or is_job_alert):
            logger.info(f"Correo {email_id} omitido - no es alerta válida (Sender: {sender}, Subject: {subject})")
            await self.mail.copy(email_id, FOLDER_CONFIG["parsed_folder"])
            await self.mail.store(email_id, "+FLAGS", "\\Deleted")
            return []

        body = None
        if message.is_multipart():
            for part in message.walk():
                if part.get_content_type() == "text/html":
                    body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                    break
        else:
            body = message.get_payload(decode=True).decode("utf-8", errors="ignore")

        if not body:
            logger.warning(f"No se encontró contenido HTML en correo {email_id}")
            await self.mail.copy(email_id, FOLDER_CONFIG["error_folder"])
            await self.mail.store(email_id, "+FLAGS", "\\Deleted")
            return []

        job_listings = self.extract_vacancies_from_html(body)
        if not job_listings:
            logger.info(f"No se encontraron vacantes en correo {email_id}")
            await self.mail.copy(email_id, FOLDER_CONFIG["parsed_folder"])
            await self.mail.store(email_id, "+FLAGS", "\\Deleted")
            return []

        enriched_jobs = await asyncio.gather(*(self.enrich_vacancy_from_url(job) for job in job_listings))
        logger.info(f"Extraídas y enriquecidas {len(enriched_jobs)} vacantes del correo {email_id}")
        return enriched_jobs

    async def enrich_vacancy_from_url(self, job_data: Dict) -> Dict:
        dominio = await self.get_dominio_scraping(job_data["url_original"])
        cookies_raw = dominio.cookies if dominio and dominio.cookies else "[]"
        try:
            cookies = json.loads(cookies_raw) if isinstance(cookies_raw, str) else cookies_raw
            if not isinstance(cookies, list):
                cookies = []
        except json.JSONDecodeError:
            logger.warning(f"Error al decodificar cookies para {job_data['url_original']}: {cookies_raw}")
            cookies = []

        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }

        # Intentar con Playwright primero
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage', '--disable-gpu'],
                    timeout=300000  # 300 segundos para lanzar el navegador
                )
                context = await browser.new_context(
                    extra_http_headers=headers,
                    viewport={'width': 1920, 'height': 1080}
                )
                if cookies:
                    await context.add_cookies([{**cookie, "domain": urlparse(job_data["url_original"]).netloc} for cookie in cookies])
                page = await context.new_page()
                try:
                    await page.goto(job_data["url_original"], wait_until="networkidle", timeout=60000)
                    await page.wait_for_load_state("domcontentloaded", timeout=30000)

                    selectors = [
                        "div[data-automation-id='jobPostingDescription']",
                        "div.job-description",
                        "section#content",
                        "div.job-details",
                        "div.description",
                        "div[class*='job-description']",
                        "div[class*='description']"
                    ]
                    
                    desc = None
                    for selector in selectors:
                        desc = await page.query_selector(selector)
                        if desc:
                            job_data["descripcion"] = await desc.inner_text()
                            break
                    
                    if not job_data["descripcion"]:
                        content = await page.content()
                        soup = BeautifulSoup(content, "html.parser")
                        job_data["descripcion"] = soup.get_text(strip=True)

                    logger.debug(f"Descripción extraída para {job_data['titulo']}: {job_data['descripcion'][:100]}...")

                    text = job_data["descripcion"].lower()
                    if "remoto" in text or "remote" in text or "teletrabajo" in text:
                        job_data["modalidad"] = "remoto"
                    elif "híbrido" in text or "hybrid" in text or "hibrido" in text:
                        job_data["modalidad"] = "hibrido"
                    elif "presencial" in text or "on-site" in text or "oficina" in text:
                        job_data["modalidad"] = "presencial"

                    req_selectors = ["div.requirements", "ul.qualifications", "div[class*='requirements']", "div[class*='qualifications']"]
                    ben_selectors = ["div.benefits", "section.perks", "div[class*='benefits']", "div[class*='perks']"]
                    
                    for selector in req_selectors:
                        req = await page.query_selector(selector)
                        if req:
                            job_data["requisitos"] = await req.inner_text()
                            break
                            
                    for selector in ben_selectors:
                        ben = await page.query_selector(selector)
                        if ben:
                            job_data["beneficios"] = await ben.inner_text()
                            break

                    if NLP_PROCESSOR and job_data["descripcion"]:
                        analysis = NLP_PROCESSOR.analyze_opportunity(job_data["descripcion"])
                        job_data["skills_required"] = analysis["details"].get("skills", job_data["skills_required"])
                        job_data["modalidad"] = analysis["details"].get("contract_type", job_data["modalidad"]) or job_data["modalidad"]

                except PlaywrightTimeoutError as e:
                    logger.warning(f"Timeout en Playwright para {job_data['url_original']}: {e}, intentando con aiohttp...")
                    await page.close()
                    await browser.close()
                    return await self._enrich_with_aiohttp(job_data, headers, cookies)
                except Exception as e:
                    logger.warning(f"Error en Playwright para {job_data['url_original']}: {e}, intentando con aiohttp...")
                    await page.close()
                    await browser.close()
                    return await self._enrich_with_aiohttp(job_data, headers, cookies)
                finally:
                    await page.close()
                    await browser.close()

        except Exception as e:
            logger.warning(f"Fallo total en Playwright para {job_data['url_original']}: {e}, usando aiohttp como respaldo...")
            return await self._enrich_with_aiohttp(job_data, headers, cookies)

        if dominio:
            job_data["empresa"] = dominio.company_name or "Santander"
            job_data["dominio_origen"] = dominio
        else:
            job_data["empresa"] = "Santander"
        return job_data

    async def _enrich_with_aiohttp(self, job_data: Dict, headers: Dict, cookies: List[Dict]) -> Dict:
        """Método de respaldo usando aiohttp si Playwright falla."""
        try:
            async with aiohttp.ClientSession(cookies=cookies, headers=headers) as session:
                async with session.get(job_data["url_original"], timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, "html.parser")
                        desc = soup.select_one("div[data-automation-id='jobPostingDescription']") or \
                               soup.select_one("div.job-description") or \
                               soup.select_one("section#content")
                        job_data["descripcion"] = desc.get_text(strip=True) if desc else soup.get_text(strip=True)
                        logger.debug(f"Descripción extraída con aiohttp para {job_data['titulo']}: {job_data['descripcion'][:100]}...")

                        text = job_data["descripcion"].lower()
                        if "remoto" in text or "remote" in text or "teletrabajo" in text:
                            job_data["modalidad"] = "remoto"
                        elif "híbrido" in text or "hybrid" in text or "hibrido" in text:
                            job_data["modalidad"] = "hibrido"
                        elif "presencial" in text or "on-site" in text or "oficina" in text:
                            job_data["modalidad"] = "presencial"

                        req = soup.select_one("div.requirements") or soup.select_one("ul.qualifications")
                        job_data["requisitos"] = req.get_text(strip=True) if req else ""
                        ben = soup.select_one("div.benefits") or soup.select_one("section.perks")
                        job_data["beneficios"] = ben.get_text(strip=True) if ben else ""

                        if NLP_PROCESSOR and job_data["descripcion"]:
                            analysis = NLP_PROCESSOR.analyze_opportunity(job_data["descripcion"])
                            job_data["skills_required"] = analysis["details"].get("skills", job_data["skills_required"])
                            job_data["modalidad"] = analysis["details"].get("contract_type", job_data["modalidad"]) or job_data["modalidad"]
                    else:
                        logger.warning(f"Error HTTP {response.status} al enriquecer {job_data['url_original']}")
        except Exception as e:
            logger.error(f"Error con aiohttp para {job_data['url_original']}: {e}")
        return job_data

    async def save_or_update_vacante(self, job_data: Dict, business_unit: BusinessUnit) -> bool:
        try:
            truncated_title = job_data["titulo"][:100]
            vacante, created = await sync_to_async(Vacante.objects.get_or_create)(
                url_original=job_data["url_original"],
                defaults={
                    "titulo": truncated_title,
                    "empresa": job_data["empresa"],
                    "ubicacion": job_data["ubicacion"],
                    "descripcion": job_data["descripcion"],
                    "modalidad": job_data["modalidad"],
                    "requisitos": job_data["requisitos"],
                    "beneficios": job_data["beneficios"],
                    "skills_required": job_data["skills_required"],
                    "dominio_origen": job_data["dominio_origen"],
                    "business_unit": business_unit,
                    "fecha_publicacion": job_data["fecha_publicacion"],
                    "activa": True
                }
            )
            if not created:
                vacante.titulo = truncated_title
                vacante.empresa = job_data["empresa"]
                vacante.ubicacion = job_data["ubicacion"]
                vacante.descripcion = job_data["descripcion"] or vacante.descripcion
                vacante.modalidad = job_data["modalidad"] or vacante.modalidad
                vacante.requisitos = job_data["requisitos"] or vacante.requisitos
                vacante.beneficios = job_data["beneficios"] or vacante.beneficios
                vacante.skills_required = job_data["skills_required"] or vacante.skills_required
                vacante.dominio_origen = job_data["dominio_origen"] or vacante.dominio_origen
                vacante.business_unit = business_unit
                vacante.fecha_publicacion = job_data["fecha_publicacion"]
                vacante.activa = True
                await sync_to_async(vacante.save)()

            worker, worker_created = await sync_to_async(Worker.objects.get_or_create)(
                url_name=job_data["url_original"],
                defaults={
                    "name": truncated_title,
                    "company": job_data["empresa"],
                    "job_description": job_data["descripcion"],
                    "address": job_data["ubicacion"],
                    "required_skills": ", ".join(job_data["skills_required"]) if job_data["skills_required"] else "",
                    "job_type": job_data["modalidad"]
                }
            )
            if not worker_created:
                worker.name = truncated_title
                worker.company = job_data["empresa"]
                worker.job_description = job_data["descripcion"] or worker.job_description
                worker.address = job_data["ubicacion"]
                worker.required_skills = ", ".join(job_data["skills_required"]) if job_data["skills_required"] else worker.required_skills
                worker.job_type = job_data["modalidad"]
                await sync_to_async(worker.save)()

            action = "creada" if created else "actualizada"
            logger.info(f"Vacante {action}: {vacante.titulo} | Worker {action}: {worker.name}")
            return True
        except Exception as e:
            logger.error(f"Error al guardar/actualizar vacante {job_data['titulo']}: {e}")
            return False

    async def run(self, batch_size: int = BATCH_SIZE_DEFAULT) -> None:
        if not await self.connect():
            return

        try:
            resp, data = await self.mail.search("ALL")
            if resp != "OK":
                logger.error(f"Fallo al buscar correos: {resp}")
                return

            email_ids = data[0].decode().split()
            logger.info(f"Encontrados {len(email_ids)} correos para procesar")

            if not email_ids:
                logger.info("No hay correos para procesar")
                return

            sender_domain = self.email_account.split('@')[1]
            bu_queryset = await sync_to_async(BusinessUnit.objects.filter)(
                configuracionbu__dominio_bu__contains=sender_domain
            )
            default_business_unit = await sync_to_async(lambda: bu_queryset.first())() or \
                                    await sync_to_async(BusinessUnit.objects.first)()

            if not default_business_unit:
                logger.error("No se encontró BusinessUnit válida")
                return

            processed_count = 0
            success_count = 0
            error_count = 0

            for email_id in email_ids[:batch_size]:
                if not await self.ensure_connection():
                    logger.error("Conexión perdida y no se pudo reconectar")
                    break

                job_listings = await self.process_job_alert_email(email_id)
                if not job_listings:
                    processed_count += 1
                    continue

                tasks = []
                for job_data in job_listings:
                    bu_id = await assign_business_unit_async(
                        job_title=job_data["titulo"],
                        job_description=job_data["descripcion"],
                        location=job_data["ubicacion"]
                    )
                    bu = await sync_to_async(BusinessUnit.objects.get)(id=bu_id) if bu_id else default_business_unit
                    tasks.append(self.save_or_update_vacante(job_data, bu))

                results = await asyncio.gather(*tasks, return_exceptions=True)
                successes = sum(1 for r in results if r is True)
                failures = len(job_listings) - successes

                if failures == 0:
                    await self.mail.copy(email_id, FOLDER_CONFIG["parsed_folder"])
                    await self.mail.store(email_id, "+FLAGS", "\\Deleted")
                    success_count += 1
                    logger.info(f"Correo {email_id} movido a INBOX.Parsed: {successes} vacantes guardadas")
                else:
                    await self.mail.copy(email_id, FOLDER_CONFIG["error_folder"])
                    await self.mail.store(email_id, "+FLAGS", "\\Deleted")
                    error_count += 1
                    logger.warning(f"Correo {email_id} movido a INBOX.Error: {failures} vacantes fallaron de {len(job_listings)}")

                processed_count += 1

            logger.info(f"Procesamiento completado: {processed_count} correos procesados, {success_count} exitosos, {error_count} con errores")

        except Exception as e:
            logger.error(f"Error en ejecución principal: {e}", exc_info=True)
        finally:
            try:
                await self.mail.logout()
            except:
                pass

async def assign_business_unit_async(job_title: str, job_description: str = None, salary_range=None, required_experience=None, location: str = None) -> Optional[int]:
    job_title_lower = job_title.lower()
    job_desc_lower = job_description.lower() if job_description else ""
    location_lower = location.lower() if location else ""

    bu_candidates = await sync_to_async(list)(BusinessUnit.objects.all())
    scores = {bu.name: 0 for bu in bu_candidates}

    seniority_score = 0
    for keyword, score in SENIORITY_KEYWORDS.items():
        if keyword in job_title_lower:
            seniority_score = max(seniority_score, score)

    industry_scores = {ind: 0 for ind in INDUSTRY_KEYWORDS}
    for ind, keywords in INDUSTRY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in job_title_lower or keyword in job_desc_lower:
                industry_scores[ind] += 1
    dominant_industry = max(industry_scores, key=industry_scores.get) if max(industry_scores.values()) > 0 else None

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
            if bu.name == 'huntRED® Executive':
                scores[bu.name] += 4 * weights["personalidad"]
            elif bu.name == 'huntRED®':
                scores[bu.name] += 2 * weights["soft_skills"]
        elif seniority_score >= 3:
            if bu.name == 'huntRED®':
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
                elif bu.name == 'huntRED®':
                    scores[bu.name] += 1 * weights["soft_skills"] * industry_scores['tech']
            elif dominant_industry == 'management':
                if bu.name == 'huntRED®':
                    scores[bu.name] += 3 * weights["soft_skills"] * industry_scores['management']
                elif bu.name == 'huntRED® Executive':
                    scores[bu.name] += 2 * weights["personalidad"] * industry_scores['management']
            elif dominant_industry == 'operations':
                if bu.name == 'amigro':
                    scores[bu.name] += 3 * weights["ubicacion"] * industry_scores['operations']
            elif dominant_industry == 'strategy':
                if bu.name == 'huntRED® Executive':
                    scores[bu.name] += 3 * weights["personalidad"] * industry_scores['strategy']
                elif bu.name == 'huntRED®':
                    scores[bu.name] += 1 * weights["soft_skills"] * industry_scores['strategy']

        if job_description:
            if any(term in job_desc_lower for term in ['migration', 'visa', 'bilingual', 'temporary', 'migración']):
                if bu.name == 'amigro':
                    scores[bu.name] += 4 * weights["ubicacion"]
            if any(term in job_desc_lower for term in ['strategic', 'global', 'executive', 'board', 'estrategico']):
                if bu.name == 'huntRED® Executive':
                    scores[bu.name] += 3 * weights["personalidad"]
            if any(term in job_desc_lower for term in ['development', 'coding', 'software', 'data', 'programación']):
                if bu.name == 'huntu':
                    scores[bu.name] += 3 * weights["hard_skills"]
            if any(term in job_desc_lower for term in ['operations', 'management', 'leadership', 'gerencia']):
                if bu.name == 'huntRED®':
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
    priority_order = ['huntRED® Executive', 'huntRED®', 'huntu', 'amigro']

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
        chosen_bu = 'huntRED®'

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

if __name__ == "__main__":
    import os
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ai_huntred.settings")
    import django
    django.setup()

    EMAIL_ACCOUNT = env("EMAIL_ACCOUNT", default="pablo@huntred.com")
    EMAIL_PASSWORD = env("EMAIL_PASSWORD", default="Natalia&Patricio1113!")

    async def process_all_emails():
        scraper = EmailScraperV2(EMAIL_ACCOUNT, EMAIL_PASSWORD)
        batch_size = 10
        pause_minutes = 5

        while True:
            if not await scraper.connect():
                logger.error("No se pudo conectar al servidor IMAP, deteniendo...")
                break

            resp, data = await scraper.mail.search("ALL")
            if resp != "OK":
                logger.error(f"Fallo al buscar correos: {resp}")
                break

            email_ids = data[0].decode().split()
            if not email_ids:
                logger.info("No hay más correos en INBOX.Jobs, procesamiento terminado")
                break

            logger.info(f"Procesando lote de {min(batch_size, len(email_ids))} correos de {len(email_ids)} restantes")
            await scraper.run(batch_size=batch_size)

            await scraper.mail.logout()

            if len(email_ids) > batch_size:
                logger.info(f"Pausando {pause_minutes} minutos antes del siguiente lote...")
                await asyncio.sleep(pause_minutes * 60)
            else:
                logger.info("Último lote procesado, finalizando...")
                break

    asyncio.run(process_all_emails())