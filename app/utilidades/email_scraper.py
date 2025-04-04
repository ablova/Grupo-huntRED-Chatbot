import asyncio
import aioimaplib
import email
import logging
import re
import json
import random
import gc
import os
import time
import psutil
from datetime import datetime
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from django.utils import timezone
from asgiref.sync import sync_to_async
from app.models import Vacante, BusinessUnit, DominioScraping, Worker, ConfiguracionBU, USER_AGENTS
from playwright.async_api import async_playwright
import aiohttp
import environ
from urllib.parse import urlparse, urljoin
import smtplib
from email.mime.text import MIMEText

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
EMAIL_ACCOUNT = env("EMAIL_ACCOUNT", default="pablo@huntred.com")
EMAIL_PASSWORD = env("EMAIL_PASSWORD", default="Natalia&Patricio1113!")
SMTP_SERVER = env("SMTP_SERVER", default="mail.huntred.com")
SMTP_PORT = env.int("SMTP_PORT", default=587)
CONNECTION_TIMEOUT = 60
BATCH_SIZE_DEFAULT = 15
MAX_RETRIES = 3
RETRY_DELAY = 5

FOLDER_CONFIG = {
    "inbox": "INBOX",
    "jobs_folder": "INBOX.Jobs",
    "parsed_folder": "INBOX.Parsed",
    "error_folder": "INBOX.Error",
}

JOB_KEYWORDS = ["job", "vacante", "opportunity", "empleo", "position", "director", "analista", "gerente", "asesor"]
EXCLUDED_TEXTS = ["unsubscribe", "manage", "help", "profile", "feed"]

BUSINESS_UNITS_KEYWORDS = {
    'huntRED®': {'manager': 2, 'director': 3, 'gerente': 2, 'jefe': 4},
    'huntRED® Executive': {'vp': 4, 'chief': 5, 'executive': 4, 'estrategico': 3},
    'huntu': {'developer': 2, 'engineer': 2, 'junior': 3, 'programador': 2},
    'amigro': {'migration': 4, 'worker': 2, 'operator': 2, 'migración': 4}
}
SENIORITY_KEYWORDS = {'junior': 1, 'senior': 3, 'manager': 4, 'director': 5, 'chief': 5}

class SystemHealthMonitor:
    def __init__(self, scraper):
        self.scraper = scraper
        self.start_time = time.time()
        self.last_check = self.start_time
        self.check_interval = 60  # seconds
        self.stats = {
            "memory_usage": [],
            "cpu_usage": [],
            "error_rate": 0,
            "success_rate": 0,
            "connection_failures": 0,
            "reconnection_attempts": 0,
            "successful_reconnections": 0
        }
        self.error_threshold = 0.3  # 30% failure rate
        self.memory_threshold = 500  # MB
        self.cpu_threshold = 80  # %
        self.actions_taken = []  # Log of corrective actions
        self.stats_file = f"/home/pablo/logs/scraper_stats_{datetime.now().strftime('%Y%m%d_%H%M')}.log"
        with open(self.stats_file, "w") as f:
            f.write("timestamp,memory_mb,cpu_percent,errors,successes,connections,reconnects\n")

    async def check_health(self) -> Dict:
        """Check the current system and scraper health"""
        current_time = time.time()
        if current_time - self.last_check < self.check_interval:
            return {}
        self.last_check = current_time

        process = psutil.Process(os.getpid())
        memory_mb = process.memory_info().rss / (1024 * 1024)
        cpu_percent = process.cpu_percent(interval=1.0)

        total_processed = self.scraper.stats["correos_procesados"]
        if total_processed > 0:
            error_rate = self.scraper.stats["correos_error"] / total_processed
            success_rate = self.scraper.stats["correos_exitosos"] / total_processed
        else:
            error_rate = success_rate = 0

        self.stats["memory_usage"].append(memory_mb)
        self.stats["cpu_usage"].append(cpu_percent)
        self.stats["error_rate"] = error_rate
        self.stats["success_rate"] = success_rate

        with open(self.stats_file, "a") as f:
            f.write(f"{datetime.now().isoformat()},{memory_mb:.2f},{cpu_percent:.2f},"
                    f"{self.scraper.stats['correos_error']},{self.scraper.stats['correos_exitosos']},"
                    f"{self.stats['connection_failures']},{self.stats['reconnection_attempts']}\n")

        recommendations = {}
        if memory_mb > self.memory_threshold:
            logging.warning(f"High memory usage: {memory_mb:.2f}MB > {self.memory_threshold}MB")
            recommendations["run_gc"] = True
            self.actions_taken.append(f"High memory: {memory_mb:.2f}MB, running gc.collect()")
        if cpu_percent > self.cpu_threshold:
            logging.warning(f"High CPU usage: {cpu_percent:.2f}% > {self.cpu_threshold}%")
            recommendations["reduce_batch"] = True
            self.actions_taken.append(f"High CPU: {cpu_percent:.2f}%, reducing batch_size")
        if error_rate > self.error_threshold:
            logging.warning(f"High error rate: {error_rate:.2%} > {self.error_threshold:.2%}")
            self.actions_taken.append(f"High error rate: {error_rate:.2%}")

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
            "processed_emails": [],  # Track processed email details
            "vacantes_completas": [],  # Nuevas listas para vacantes completas e incompletas
            "vacantes_incompletas": []
        }

    async def connect(self) -> Optional[aioimaplib.IMAP4_SSL]:
        for attempt in range(MAX_RETRIES):
            try:
                if self.mail:
                    await self.mail.logout()
                self.mail = aioimaplib.IMAP4_SSL(self.imap_server, timeout=CONNECTION_TIMEOUT)
                await asyncio.wait_for(self.mail.wait_hello_from_server(), timeout=CONNECTION_TIMEOUT)
                await asyncio.wait_for(self.mail.login(self.email_account, self.password), timeout=CONNECTION_TIMEOUT)
                await self.mail.select(FOLDER_CONFIG["jobs_folder"])
                logger.info(f"✅ Connected to {self.imap_server}")
                return self.mail
            except Exception as e:
                logger.error(f"❌ Attempt {attempt + 1}/{MAX_RETRIES} failed: {e}")
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(RETRY_DELAY)
        return None

    async def ensure_connection(self) -> bool:
        try:
            if not self.mail:
                return await self.connect() is not None
            await asyncio.wait_for(self.mail.noop(), timeout=CONNECTION_TIMEOUT)
            return True
        except Exception:
            return await self.connect() is not None

    async def fetch_email(self, email_id: str) -> Optional[email.message.Message]:
        for attempt in range(MAX_RETRIES):
            try:
                if not await self.ensure_connection():
                    return None
                resp, data = await asyncio.wait_for(self.mail.fetch(email_id, "(RFC822)"), timeout=CONNECTION_TIMEOUT)
                if resp == "OK" and data and isinstance(data[1], (bytes, bytearray)):
                    return email.message_from_bytes(data[1])
            except Exception as e:
                logger.error(f"Error fetching email {email_id}, attempt {attempt + 1}: {e}")
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(RETRY_DELAY)
        return None

    def format_title(self, title: str) -> str:
        replacements = {
            # **C-Level y Alta Dirección**
            r"\bceo\b": "Chief Executive Officer",r"\bcoo\b": "Chief Operating Officer",r"\bcfo\b": "Chief Financial Officer",r"\bcto\b": "Chief Technology Officer",r"\bcmo\b": "Chief Marketing Officer",r"\bcio\b": "Chief Information Officer",r"\bvp\b": "Vicepresidente",
            
            # **Gerencias y Direcciones**
            r"\bdir gral\b": "Director General",r"\bgte gral\b": "Gerente General",r"\bdir\b": "Director",r"\bgte\b": "Gerente",r"\bjefe\b": "Jefe",r"\bsup\b": "Supervisor",r"\bcoord\b": "Coordinador",
            
            # **Abreviaturas Profesionales**
            r"\bing\b": "Ingeniero",r"\bing\.\b": "Ingeniero",r"\blic\b": "Licenciado",r"\bmtro\b": "Maestro",r"\bdr\b": "Doctor",r"\bprof\b": "Profesor",
            
            # **Especialistas y Cargos Intermedios**
            r"\besp\b": "Especialista",r"\bconsult\b": "Consultor",r"\basist\b": "Asistente",r"\btec\b": "Técnico",r"\banal\b": "Analista",
            
            # **Áreas Funcionales**
            r"\bit\b": "IT",r"\brrhh\b": "Recursos Humanos",r"\bmkt\b": "Marketing",r"\bfin\b": "Finanzas",r"\blog\b": "Logística",r"\bventas\b": "Ventas",r"\bcompras\b": "Compras",r"\bop\b": "Operaciones",r"\bproducc\b": "Producción",
            
            # **Nombres de Países y Ubicaciones**
            r"\bmex\b": "México",r"\busa\b": "Estados Unidos",
        }
        title = title.lower()
        # Aplicar reemplazos asegurando que sean palabras completas
        for pattern, replacement in replacements.items():
            title = re.sub(pattern, replacement, title)
        # Eliminar caracteres especiales innecesarios
        title = re.sub(r"[^a-zA-Z0-9áéíóúÁÉÍÓÚñÑüÜ&\- ]", "", title)
        # Normalizar espacios
        title = re.sub(r"\s+", " ", title).strip()
        # Capitalizar correctamente, manteniendo excepciones como "México", "IT", etc.
        words = title.split()
        formatted_title = " ".join(
            word.capitalize() if word.lower() not in ["méxico", "it", "rrhh", "mkt"] else word
            for word in words
        )
        return formatted_title[:300]  # Truncar a 300 caracteres

    async def save_or_update_vacante(self, job_data: Dict) -> bool:
        """Guarda o actualiza una vacante, asignando la unidad de negocio correcta."""
        try:
            worker_tuple = await sync_to_async(Worker.objects.get_or_create)(
                name=job_data["empresa"].name, defaults={"company": job_data["empresa"].name}
            )
            worker = worker_tuple[0]

            # Truncar el título a 500 caracteres
            job_data["titulo"] = job_data["titulo"][:500]

            # Asignar la unidad de negocio usando assign_business_unit_async
            from app.chatbot.utils import assign_business_unit_async
            business_unit_id = await assign_business_unit_async(
                job_title=job_data["titulo"],
                job_description=job_data.get("descripcion", ""),
                location=job_data.get("ubicacion", "")
            )

            # Obtener la instancia de BusinessUnit usando el ID
            if business_unit_id:
                business_unit = await sync_to_async(BusinessUnit.objects.get)(id=business_unit_id)
            else:
                # Usar una unidad por defecto si no se encuentra (por ejemplo, 'huntRED®')
                business_unit = await sync_to_async(BusinessUnit.objects.get)(name="huntRED®")

            # Verificar si la vacante ya existe por url_original
            vacante = await sync_to_async(Vacante.objects.filter(url_original=job_data["url_original"]).first)()

            if vacante:
                # Si existe, actualizarla si hay cambios
                vacante.procesamiento_count += 1
                updated = False
                for key, value in job_data.items():
                    if key == "titulo":
                        value = str(value)[:500]
                    elif key in ["ubicacion", "requisitos", "beneficios"]:
                        value = str(value)[:1000]
                    elif key == "descripcion":
                        value = str(value)[:3000]
                    if getattr(vacante, key) != value:
                        setattr(vacante, key, value)
                        updated = True
                vacante.business_unit = business_unit  # Actualizar la unidad de negocio
                if updated:
                    await sync_to_async(vacante.save)()
                    logger.info(f"Vacante actualizada: {vacante.titulo}, intentos: {vacante.procesamiento_count}")
                else:
                    logger.info(f"Vacante ya está actualizada: {vacante.titulo}, intentos: {vacante.procesamiento_count}")
                self.stats["vacantes_guardadas"] += 1
                return True
            else:
                # Si no existe, crear una nueva vacante
                vacante = Vacante(
                    url_original=job_data["url_original"],
                    titulo=job_data["titulo"],
                    empresa=worker,
                    ubicacion=job_data["ubicacion"][:300],
                    descripcion=job_data["descripcion"][:3000],
                    modalidad=job_data["modalidad"],
                    requisitos=job_data["requisitos"][:1000],
                    beneficios=job_data["beneficios"][:1000],
                    skills_required=job_data["skills_required"],
                    business_unit=business_unit,  # Asignar la unidad de negocio
                    fecha_publicacion=job_data["fecha_publicacion"],
                    activa=True,
                    procesamiento_count=1  # Primer intento
                )
                await sync_to_async(vacante.save)()
                logger.info(f"Vacante creada: {vacante.titulo}, intentos: {vacante.procesamiento_count}")
                self.stats["vacantes_guardadas"] += 1
                return True
        except Exception as e:
            logger.error(f"Error al guardar la vacante {job_data.get('titulo', 'Unknown')}: {e}")
            return False

    async def save_or_update_vacante(self, job_data: Dict, business_unit: BusinessUnit) -> bool:
        """Guarda o actualiza una vacante, truncando el título si es necesario."""
        try:
            worker_tuple = await sync_to_async(Worker.objects.get_or_create)(
                name=job_data["empresa"].name, defaults={"company": job_data["empresa"].name}
            )
            worker = worker_tuple[0]

            # Truncar el título a 500 caracteres antes de guardar
            job_data["titulo"] = job_data["titulo"][:500]

            vacante_tuple = await sync_to_async(Vacante.objects.get_or_create)(
                url_original=job_data["url_original"],
                defaults={
                    "titulo": job_data["titulo"],  # Ya truncado
                    "empresa": worker,
                    "ubicacion": job_data["ubicacion"][:300],
                    "descripcion": job_data["descripcion"][:3000],
                    "modalidad": job_data["modalidad"],
                    "requisitos": job_data["requisitos"][:1000],
                    "beneficios": job_data["beneficios"][:1000],
                    "skills_required": job_data["skills_required"],
                    "business_unit": business_unit,
                    "fecha_publicacion": job_data["fecha_publicacion"],
                    "activa": True
                }
            )
            vacante = vacante_tuple[0]
            if not vacante_tuple[1]:  # Si ya existe, actualizar
                for key, value in job_data.items():
                    if key == "titulo":
                        value = str(value)[:500]  # Truncar nuevamente por seguridad
                    elif key in ["ubicacion", "descripcion", "requisitos", "beneficios"]:
                        value = str(value)[:1000] if key != "descripcion" else str(value)[:3000]
                    setattr(vacante, key, value)
                await sync_to_async(vacante.save)()
            self.stats["vacantes_guardadas"] += 1
            logger.info(f"Vacancy {'created' if vacante_tuple[1] else 'updated'}: {vacante.titulo}")
            return True
        except Exception as e:
            logger.error(f"Error saving vacancy {job_data.get('titulo', 'Unknown')}: {e}")
            return False

    async def get_dominio_scraping(self, url: str) -> Optional[DominioScraping]:
        domain = urlparse(url).netloc
        return await sync_to_async(DominioScraping.objects.filter(dominio__contains=domain).first)()

    async def extract_vacancies_from_html(self, html: str) -> List[Dict]:
        soup = BeautifulSoup(html, "html.parser")
        job_listings = []
        default_empresa_tuple = await sync_to_async(Worker.objects.get_or_create)(
            name="Unknown", defaults={"company": "Unknown"}
        )
        default_empresa = default_empresa_tuple[0]

        for link in soup.find_all("a", href=True):
            href = link["href"].strip().lower()
            link_text = link.get_text(strip=True).lower()
            if any(excluded in link_text for excluded in EXCLUDED_TEXTS) or not href.startswith("http"):
                continue

            if any(keyword in link_text for keyword in JOB_KEYWORDS) or "/job/" in href:
                job_title = self.format_title(link.get_text(strip=True))
                job_container = link.find_parent(['div', 'section']) or link.parent
                location = job_container.find(string=re.compile(r'\(.*?\)')) or "No especificada"
                description = job_container.get_text(strip=True)[:1000]

                dominio = await self.get_dominio_scraping(href)
                if dominio:
                    empresa_tuple = await sync_to_async(Worker.objects.get_or_create)(
                        name=dominio.empresa or "Unknown", defaults={"company": dominio.empresa or "Unknown"}
                    )
                    empresa = empresa_tuple[0]
                else:
                    empresa = default_empresa

                job_data = {
                    "titulo": job_title, "url_original": href, "empresa": empresa,
                    "ubicacion": str(location), "descripcion": description, "modalidad": None,
                    "requisitos": "", "beneficios": "", "skills_required": [],
                    "fecha_publicacion": timezone.now(), "dominio_origen": dominio
                }
                if job_data["titulo"] and job_data["url_original"]:
                    job_listings.append(job_data)
        logger.info(f"Extracted {len(job_listings)} vacancies from HTML")
        return job_listings

    async def enrich_vacancy_from_url(self, job_data: Dict) -> Dict:
        dominio = await self.get_dominio_scraping(job_data["url_original"])
        cookies = dominio.cookies if dominio and dominio.cookies else []
        if isinstance(cookies, str):
            try:
                cookies = json.loads(cookies)
            except json.JSONDecodeError:
                cookies = []
        headers = {"User-Agent": random.choice(USER_AGENTS)}

        # Intentar con aiohttp con reintentos
        for attempt in range(MAX_RETRIES):
            try:
                async with aiohttp.ClientSession(cookies=cookies, headers=headers) as session:
                    async with session.get(job_data["url_original"], timeout=aiohttp.ClientTimeout(total=30)) as response:
                        if response.status == 200:
                            html = await response.text()
                            soup = BeautifulSoup(html, "html.parser")
                            desc_elem = soup.select_one(".job-description")
                            job_data["descripcion"] = desc_elem.get_text(strip=True)[:3000] if desc_elem else soup.get_text(strip=True)[:3000]
                            text = job_data["descripcion"].lower()
                            job_data["modalidad"] = "remoto" if "remoto" in text else "hibrido" if "híbrido" in text else "presencial" if "presencial" in text else None
                            req_elem = soup.select_one(".requirements")
                            job_data["requisitos"] = req_elem.get_text(strip=True)[:1000] if req_elem else ""
                            ben_elem = soup.select_one(".benefits")
                            job_data["beneficios"] = ben_elem.get_text(strip=True)[:1000] if ben_elem else ""
                            return job_data
            except Exception as e:
                logger.warning(f"aiohttp failed for {job_data['url_original']}, attempt {attempt + 1}/{MAX_RETRIES}: {e}")
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(RETRY_DELAY)

        # Fallback a Playwright con reintentos
        for attempt in range(MAX_RETRIES):
            try:
                async with async_playwright() as p:
                    browser = await p.chromium.launch(headless=True)
                    page = await browser.new_page()
                    if cookies and isinstance(cookies, list):
                        await page.context.add_cookies(cookies)
                    await page.goto(job_data["url_original"], wait_until="networkidle", timeout=180000)  # 180 segundos
                    html = await page.content()
                    soup = BeautifulSoup(html, "html.parser")
                    job_data["descripcion"] = soup.get_text(strip=True)[:3000]
                    text = job_data["descripcion"].lower()
                    job_data["modalidad"] = "remoto" if "remoto" in text else "hibrido" if "híbrido" in text else "presencial" if "presencial" in text else None
                    await browser.close()
                    return job_data
            except Exception as e:
                logger.error(f"Playwright failed for {job_data['url_original']}, attempt {attempt + 1}/{MAX_RETRIES}: {e}")
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(RETRY_DELAY)

        logger.error(f"All attempts failed for {job_data['url_original']}, returning partial data")
        return job_data

    async def process_job_alert_email(self, email_id: str) -> List[Dict]:
        message = await self.fetch_email(email_id)
        if not message:
            await self.move_email(email_id, FOLDER_CONFIG["error_folder"])
            return []

        sender = message.get("From", "").lower()
        subject = message.get("Subject", "").lower()
        domain = sender.split('@')[-1] if '@' in sender else "unknown"
        if not any(keyword in subject for keyword in JOB_KEYWORDS):
            await self.move_email(email_id, FOLDER_CONFIG["parsed_folder"])
            return []

        body = message.get_payload(decode=True).decode("utf-8", errors="ignore") if not message.is_multipart() else next(
            (part.get_payload(decode=True).decode("utf-8", errors="ignore") for part in message.walk() if part.get_content_type() == "text/html"), None
        )
        if not body:
            await self.move_email(email_id, FOLDER_CONFIG["error_folder"])
            return []

        job_listings = await self.extract_vacancies_from_html(body)
        self.stats["vacantes_extraidas"] += len(job_listings)
        enriched_jobs = await asyncio.gather(*(self.enrich_vacancy_from_url(job) for job in job_listings))

        # Rastrear vacantes completas e incompletas
        for job in enriched_jobs:
            if job.get("descripcion") and job.get("modalidad"):  # Ejemplo de criterios para "completa"
                self.stats["vacantes_completas"].append(job["titulo"])
            else:
                self.stats["vacantes_incompletas"].append(job["titulo"])

        self.stats["processed_emails"].append({"email_id": email_id, "subject": subject, "domain": domain})
        return [job for job in enriched_jobs if job]

    async def move_email(self, email_id: str, folder: str):
        try:
            if await self.ensure_connection():
                await self.mail.copy(email_id, folder)
                await self.mail.store(email_id, "+FLAGS", "\\Deleted")
                await self.mail.expunge()
                logger.debug(f"Email {email_id} moved to {folder} and deleted from INBOX.Jobs")
        except Exception as e:
            logger.error(f"Error moving email {email_id} to {folder}: {e}")


    async def process_email_batch(self, batch_size: int = BATCH_SIZE_DEFAULT):
        """Procesa un lote de correos con manejo robusto de errores."""
        if not await self.ensure_connection():
            return

        try:
            resp, data = await self.mail.search("ALL")
            if resp != "OK" or not data:
                logger.error("Failed to search emails")
                return
            email_ids = data[0].decode().split()[:batch_size]

            for email_id in email_ids:
                job_listings = await self.process_job_alert_email(email_id)
                self.stats["correos_procesados"] += 1
                if not job_listings:
                    await self.move_email(email_id, FOLDER_CONFIG["parsed_folder"])
                    continue

                # Procesar cada vacante individualmente
                successes = 0
                for job in job_listings:
                    if await self.save_or_update_vacante(job):  # Sin pasar default_bu
                        successes += 1

                if successes == len(job_listings):
                    await self.move_email(email_id, FOLDER_CONFIG["parsed_folder"])
                    self.stats["correos_exitosos"] += 1
                else:
                    await self.move_email(email_id, FOLDER_CONFIG["error_folder"])
                    self.stats["correos_error"] += 1
                    logger.warning(f"Email {email_id} had {len(job_listings) - successes} failures out of {len(job_listings)} vacancies")
        except Exception as e:
            logger.error(f"Error in process_email_batch: {e}")

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
        msg["To"] = "pablo@huntred.com"

        try:
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
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

    while True:
        if not await scraper.connect():
            logger.error("Could not connect to IMAP server, stopping...")
            break

        resp, data = await scraper.mail.search("ALL")
        if resp != "OK":
            logger.error(f"Failed to search emails: {resp}")
            break

        email_ids = data[0].decode().split()
        if not email_ids:
            logger.info("No more emails in INBOX.Jobs, processing finished")
            break

        current_batch_size = min(batch_size, len(email_ids))
        logger.info(f"Processing batch of {current_batch_size} emails out of {len(email_ids)} remaining")
        await scraper.process_email_batch(batch_size=current_batch_size)

        # Enviar resumen después de cada batch
        await scraper.send_summary_email(health_monitor.actions_taken)

        # Resetear estadísticas de vacantes para el próximo batch
        scraper.stats["vacantes_completas"] = []
        scraper.stats["vacantes_incompletas"] = []

        # Check health and apply corrective actions
        recommendations = await health_monitor.check_health()
        if recommendations.get("run_gc"):
            gc.collect()
            logger.info("Executed gc.collect() to free memory")
        if recommendations.get("reduce_batch"):
            batch_size = max(1, batch_size // 2)
            logger.info(f"Reduced batch_size to {batch_size} due to high CPU usage")

        # Cleanup after each batch
        try:
            await scraper.mail.logout()
        except asyncio.TimeoutError:
            logger.warning("Timeout closing IMAP connection, forcing closure...")
        except Exception as e:
            logger.error(f"Unexpected error closing IMAP connection: {e}")
        finally:
            scraper.mail = None

        if len(email_ids) > batch_size:
            logger.info(f"Pausing {RETRY_DELAY} seconds before the next batch...")
            await asyncio.sleep(RETRY_DELAY)
        else:
            logger.info("Last batch processed, finishing...")
            break

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ai_huntred.settings")
    import django
    django.setup()
    asyncio.run(process_all_emails())