# /home/pablo/app/email_scraper_v2.py

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
from app.models import Vacante, BusinessUnit, DominioScraping, Worker
from app.utilidades.scraping import ScrapingPipeline, get_scraper, JobListing
from django.core.exceptions import ObjectDoesNotExist
import aiohttp
import environ
from urllib.parse import urlparse, urljoin
import smtplib
from email.mime.text import MIMEText
from prometheus_client import Counter, Histogram, CollectorRegistry

# Configuración de entorno y logging (sin cambios)
env = environ.Env()
environ.Env.read_env(env_file='/home/pablo/.env')
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("/home/pablo/logs/email_scraper_v2.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Constantes (sin cambios)
IMAP_SERVER = "mail.huntred.com"
EMAIL_ACCOUNT = "pablo@huntred.com"
EMAIL_PASSWORD = "Natalia&Patricio1113!"
SMTP_SERVER = "mail.huntred.com"
SMTP_PORT = 587
CONNECTION_TIMEOUT = 60
BATCH_SIZE_DEFAULT = 15
MAX_RETRIES = 3
RETRY_DELAY = 5
MAX_ATTEMPTS = 10

FOLDER_CONFIG = {
    "inbox": "INBOX",
    "jobs_folder": "INBOX.Jobs",
    "parsed_folder": "INBOX.Parsed",
    "error_folder": "INBOX.Error",
}

JOB_KEYWORDS = ["job", "vacante", "opportunity", "empleo", "position", "director", "analista", "gerente", "asesor"]
EXCLUDED_TEXTS = ["unsubscribe", "manage", "help", "profile", "feed"]
DATA_MINIMIZATION = True
LOG_DATA_PROCESSING = True

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
    # Sin cambios en esta clase
    def __init__(self, scraper):
        self.scraper = scraper
        self.start_time = time.time()
        self.last_check = self.start_time
        self.check_interval = 60
        self.stats = {
            "memory_usage": [],
            "cpu_usage": [],
            "error_rate": 0,
            "success_rate": 0,
            "connection_failures": 0,
            "reconnection_attempts": 0,
            "successful_reconnections": 0
        }
        self.error_threshold = 0.3
        self.memory_threshold = 500
        self.cpu_threshold = 80
        self.actions_taken = []
        self.stats_file = f"/home/pablo/logs/scraper_stats_{datetime.now().strftime('%Y%m%d_%H%M')}.log"
        with open(self.stats_file, "w") as f:
            f.write("timestamp,memory_mb,cpu_percent,errors,successes,connections,reconnects\n")

    async def check_health(self) -> Dict:
        # Implementación sin cambios
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
            "processed_emails": [],
            "vacantes_completas": [],
            "vacantes_incompletas": [],
            "vacantes_ratificadas": 0
        }
        self.pipeline = ScrapingPipeline()
        self.metrics = Metrics()

    async def connect(self) -> Optional[aioimaplib.IMAP4_SSL]:
        # Implementación sin cambios
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
        # Implementación sin cambios
        try:
            if not self.mail:
                return await self.connect() is not None
            await asyncio.wait_for(self.mail.noop(), timeout=CONNECTION_TIMEOUT)
            return True
        except Exception:
            return await self.connect() is not None

    async def fetch_email(self, email_id: str) -> Optional[email.message.Message]:
        # Implementación sin cambios
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

    def format_title(self, title: str combo) -> str:
        # Implementación sin cambios
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
        # Implementación sin cambios
        try:
            vacante = await sync_to_async(Vacante.objects.filter(url_original=job_data["url_original"]).first)()
            if not vacante:
                return False

            updated = False
            for key, value in job_data.items():
                current_value = getattr(vacante, key, None)
                if current_value != value and value:
                    if key == "titulo":
                        value = value[:500]
                    elif key in ["ubicacion", "requisitos", "beneficios"]:
                        value = value[:1000]
                    elif key == "descripcion":
                        value = value[:3000]
                    setattr(vacante, key, value)
                    updated = True

            if updated:
                vacante.procesamiento_count += 1
                await sync_to_async(vacante.save)()
                self.stats["vacantes_ratificadas"] += 1
                logger.info(f"Vacante ratificada: {vacante.titulo}, intentos: {vacante.procesamiento_count}")
            return True
        except Exception as e:
            logger.error(f"Error ratificando vacante {job_data['titulo']}: {e}")
            return False

    async def scrape_vacancy_details_from_url(self, job_data: Dict) -> Dict:
        url = job_data["url_original"]
        logger.debug(f"Scraping details from URL: {url}")
        domain_obj = await self.get_dominio_scraping(url)
        
        if not domain_obj:
            logger.warning(f"No se encontró dominio para {url}, usando scraper por defecto")
            domain_obj = DominioScraping(dominio=urlparse(url).netloc, plataforma="default")

        try:
            scraper_class = await get_scraper(domain_obj)
            async with scraper_class as scraper:
                if domain_obj.cookies:
                    valid_cookies = {k: str(v) for k, v in domain_obj.cookies.items() if v is not None}
                    scraper.cookies.update(valid_cookies)
                    logger.debug(f"Cookies aplicadas: {valid_cookies}")
                
                with self.metrics.scraping_duration.time():
                    details = await scraper.get_job_details(url)
                
                if not details:
                    logger.warning(f"No se obtuvieron detalles de {url}")
                    return job_data

                # Crear JobListing con valores por defecto si faltan datos
                job_listing = JobListing(
                    title=details.get("title", job_data.get("titulo", "Sin título")),
                    location=details.get("location", job_data.get("ubicacion", "No especificada")),
                    company=details.get("company", job_data["empresa"].name if job_data.get("empresa") else "Unknown"),
                    description=details.get("description", job_data.get("descripcion", "")),
                    skills=details.get("skills", job_data.get("skills_required", [])),
                    posted_date=details.get("posted_date", job_data["fecha_publicacion"].isoformat()),
                    url=url,
                    salary=details.get("salary"),
                    job_type=details.get("job_type", job_data.get("modalidad")),
                    contract_type=details.get("contract_type"),
                    benefits=details.get("benefits", [])
                )

                # Verificar que pipeline esté inicializado correctamente
                if not hasattr(self.pipeline, 'process') or not callable(self.pipeline.process):
                    logger.error("ScrapingPipeline no está correctamente inicializado")
                    return job_data

                processed_jobs = await self.pipeline.process([vars(job_listing)])
                if not processed_jobs or not isinstance(processed_jobs, list):
                    logger.warning(f"No se procesaron trabajos para {url}")
                    return job_data

                enriched_job = processed_jobs[0]
                salario_raw = enriched_job.get("salary")
                salario = None
                if salario_raw is not None:
                    try:
                        salario = float(salario_raw)
                    except (ValueError, TypeError):
                        logger.debug(f"Salario no convertible a float: {salario_raw}")

                # Actualizar job_data con manejo seguro de valores
                job_data.update({
                    "titulo": enriched_job.get("title", job_data.get("titulo", "Sin título"))[:500],
                    "ubicacion": enriched_job.get("location", job_data.get("ubicacion", "No especificada"))[:300],
                    "empresa": job_data.get("empresa") or await sync_to_async(Worker.objects.get_or_create)(
                        name=enriched_job.get("company", "Unknown"), 
                        defaults={"company": enriched_job.get("company", "Unknown")}
                    )[0],
                    "descripcion": enriched_job.get("description", "")[:3000],
                    "modalidad": enriched_job.get("job_type", job_data.get("modalidad")),
                    "requisitos": enriched_job.get("requirements", "")[:1000],
                    "beneficios": ", ".join(enriched_job.get("benefits", []))[:1000],
                    "skills_required": enriched_job.get("skills", []),
                    "salario": salario,
                    "fecha_publicacion": enriched_job.get("posted_date") or job_data["fecha_publicacion"]
                })
                
                logger.debug(f"Enriched job data: {json.dumps(job_data, default=str)}")
                self.metrics.vacantes_procesadas.inc(1)
                return job_data

        except Exception as e:
            logger.error(f"Failed to scrape details from {url}: {e}", exc_info=True)
            self.metrics.scraping_errors.inc(1)
            return job_data

    async def save_or_update_vacante(self, job_data: Dict) -> bool:
        try:
            logger.debug(f"Guardando vacante: {job_data.get('titulo', 'Sin título')}")
            
            business_unit_id = await assign_business_unit(
                job_title=job_data.get("titulo", ""),
                job_description=job_data.get("descripcion", ""),
                location=job_data.get("ubicacion", "")
            )
            
            business_unit = await sync_to_async(BusinessUnit.objects.get)(
                id=business_unit_id) if business_unit_id else await sync_to_async(BusinessUnit.objects.get)(name="huntRED®")

            if await self.ratify_existing_vacancy(job_data):
                return True

            if not job_data.get("empresa"):
                logger.error(f"No se pudo asignar empresa para {job_data.get('titulo', 'Unknown')}")
                return False

            # Crear vacante con valores por defecto para campos opcionales
            vacante = Vacante(
                url_original=job_data["url_original"],
                titulo=job_data["titulo"][:500],
                empresa=job_data["empresa"],
                ubicacion=job_data["ubicacion"][:300],
                descripcion=job_data["descripcion"][:3000],
                modalidad=job_data.get("modalidad"),
                requisitos=job_data.get("requisitos", "")[:1000],
                beneficios=job_data.get("beneficios", "")[:1000],
                skills_required=job_data.get("skills_required", []),
                salario=job_data.get("salario"),  # Puede ser None
                business_unit=business_unit,
                fecha_publicacion=job_data["fecha_publicacion"],
                activa=True,
                procesamiento_count=1
            )
            await sync_to_async(vacante.save)()
            self.stats["vacantes_guardadas"] += 1
            logger.info(f"Vacante creada: {vacante.titulo}")
            if LOG_DATA_PROCESSING:
                logger.info(f"GDPR: Processed vacancy {vacante.titulo} at {datetime.now().isoformat()}")
            return True
        except Exception as e:
            logger.error(f"Error guardando vacante {job_data.get('titulo', 'Unknown')}: {e}", exc_info=True)
            return False

    async def get_dominio_scraping(self, url: str) -> Optional[DominioScraping]:
        # Implementación sin cambios
        domain = urlparse(url).netloc
        return await sync_to_async(DominioScraping.objects.filter(dominio__contains=domain).first)()

    async def extract_vacancies_from_html(self, html: str) -> List[Dict]:
        # Implementación sin cambios
        soup = BeautifulSoup(html, "html.parser")
        job_listings = []

        try:
            default_empresa = (await sync_to_async(Worker.objects.get_or_create)(name="Unknown", defaults={"company": "Unknown"}))[0]
            logger.debug(f"Default empresa obtenida: {default_empresa.name}")
        except Exception as e:
            logger.error(f"Error al obtener/crear empresa por defecto: {e}")
            return []

        NON_JOB_TITLES = [
            "gestionar alertas", "ver todos los empleos", "buscar empleos", "empleos guardados",
            "see more", "ver más", "alertas", "publicar", "promocionar"
        ]

        empresas_to_fetch = set()
        links = soup.find_all("a", href=True)
        for link in links:
            href = link["href"].strip().lower()
            link_text = link.get_text(strip=True).lower()
            if any(non_job in link_text for non_job in NON_JOB_TITLES) or \
               not ("/jobs/view/" in href or any(keyword in link_text for keyword in JOB_KEYWORDS)):
                continue
            job_container = link.find_parent(['div', 'li', 'tr']) or link.parent
            if not job_container:
                continue
            company_elem = (job_container.find(class_=re.compile(r'company|organization|employer', re.I)) or
                            job_container.find(string=re.compile(r'^\w+\s+\w+$', re.I)))
            empresa_name = company_elem.get_text(strip=True) if company_elem else "LinkedIn"
            empresas_to_fetch.add(empresa_name)

        existing_empresas = await sync_to_async(list)(Worker.objects.filter(name__in=empresas_to_fetch))
        empresas_dict = {e.name: e for e in existing_empresas}
        missing_empresas = [name for name in empresas_to_fetch if name not in empresas_dict]
        if missing_empresas:
            new_empresas = [Worker(name=name, company=name) for name in missing_empresas]
            await sync_to_async(Worker.objects.bulk_create)(new_empresas)
            empresas_dict.update({e.name: e for e in new_empresas})

        for link in links:
            href = link["href"].strip().lower()
            link_text = link.get_text(strip=True).lower()
            if any(non_job in link_text for non_job in NON_JOB_TITLES) or \
               not ("/jobs/view/" in href or any(keyword in link_text for keyword in JOB_KEYWORDS)):
                continue
            job_title = self.format_title(link_text)
            if not job_title or len(job_title) < 10:
                continue
            job_container = link.find_parent(['div', 'li', 'tr']) or link.parent
            if not job_container:
                continue
            company_elem = (job_container.find(class_=re.compile(r'company|organization|employer', re.I)) or
                            job_container.find(string=re.compile(r'^\w+\s+\w+$', re.I)))
            empresa_name = company_elem.get_text(strip=True) if company_elem else "LinkedIn"
            empresa = empresas_dict.get(empresa_name, default_empresa)
            location_elem = job_container.find(string=re.compile(r'(?:ciudad|área|remote|remoto|híbrido|presencial)', re.I))
            location = location_elem.strip()[:300] if location_elem else "No especificada"
            modality = "Remoto" if "remoto" in location.lower() else "Híbrido" if "híbrido" in location.lower() else "Presencial" if "presencial" in location.lower() else None
            description = job_container.get_text(strip=True)[:1000]
            job_data = {
                "titulo": job_title,
                "url_original": href if href.startswith("http") else urljoin("https://www.linkedin.com", href),
                "empresa": empresa,
                "ubicacion": location,
                "modalidad": modality,
                "descripcion": description,
                "requisitos": "",
                "beneficios": "",
                "skills_required": [],
                "fecha_publicacion": timezone.now(),
                "dominio_origen": await self.get_dominio_scraping(href)
            }
            if job_data["titulo"] and job_data["url_original"]:
                job_listings.append(job_data)

        logger.info(f"Extracted {len(job_listings)} valid vacancies from HTML")
        self.metrics.vacantes_procesadas.inc(len(job_listings))
        return job_listings

    async def process_email_batch(self, batch_size: int = BATCH_SIZE_DEFAULT):
        # Implementación sin cambios
        if not await self.ensure_connection():
            return

        try:
            resp, data = await self.mail.search("ALL")
            if resp != "OK" or not data or not isinstance(data[0], bytes):
                logger.error(f"Failed to search emails: resp={resp}, data={data}")
                return
            email_ids = data[0].decode().split()[:batch_size]
            if not email_ids:
                logger.info("No emails found in batch")
                return

            for email_id in email_ids:
                job_listings = await self.process_job_alert_email(email_id)
                self.stats["correos_procesados"] += 1
                if not job_listings:
                    await self.move_email(email_id, FOLDER_CONFIG["parsed_folder"])
                    continue

                successes = 0
                for job in job_listings:
                    if await self.save_or_update_vacante(job):
                        successes += 1

                if successes == len(job_listings):
                    await self.move_email(email_id, FOLDER_CONFIG["parsed_folder"])
                    self.stats["correos_exitosos"] += 1
                else:
                    await self.move_email(email_id, FOLDER_CONFIG["error_folder"])
                    self.stats["correos_error"] += 1
                    logger.warning(f"Email {email_id} had {len(job_listings) - successes} failures out of {len(job_listings)} vacancies")
        except Exception as e:
            logger.error(f"Unexpected error in process_email_batch: {e}", exc_info=True)
            self.metrics.scraping_errors.inc(1)

    async def process_job_alert_email(self, email_id: str) -> List[Dict]:
        # Implementación sin cambios
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
        if not isinstance(job_listings, list):
            logger.error(f"extract_vacancies_from_html returned invalid data: {job_listings}")
            return []

        self.stats["vacantes_extraidas"] += len(job_listings)
        
        enriched_jobs = await asyncio.gather(*(self.scrape_vacancy_details_from_url(job) for job in job_listings))

        for job in enriched_jobs:
            if job.get("descripcion") and job.get("modalidad"):
                self.stats["vacantes_completas"].append(job["titulo"])
            else:
                self.stats["vacantes_incompletas"].append(job["titulo"])

        self.stats["processed_emails"].append({"email_id": email_id, "subject": subject, "domain": domain})
        if LOG_DATA_PROCESSING:
            logger.info(f"GDPR: Processed email {email_id} with subject {subject} from {domain} at {datetime.now().isoformat()}")
        return [job for job in enriched_jobs if job]

    async def move_email(self, email_id: str, folder: str):
        # Implementación sin cambios
        try:
            if await self.ensure_connection():
                await self.mail.copy(email_id, folder)
                await self.mail.store(email_id, "+FLAGS", "\\Deleted")
                await self.mail.expunge()
                logger.debug(f"Email {email_id} moved to {folder} and deleted from INBOX.Jobs")
        except Exception as e:
            logger.error(f"Error moving email {email_id} to {folder}: {e}")

    async def send_summary_email(self, actions_taken: List[str]):
        # Implementación sin cambios
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
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(self.email_account, self.password)
                server.send_message(msg)
                logger.info("📧 Summary sent to pablo@huntred.com")
        except Exception as e:
            logger.error(f"Error sending summary email: {e}")

async def process_all_emails():
    # Implementación sin cambios
    scraper = EmailScraperV2()
    health_monitor = SystemHealthMonitor(scraper)
    batch_size = BATCH_SIZE_DEFAULT
    attempt = 0

    try:
        from prometheus_client import start_http_server
        start_http_server(8001, registry=scraper.metrics.registry)
        logger.info("Prometheus server started on port 8001")
    except OSError as e:
        logger.warning(f"Failed to start Prometheus server: {e}")

    while attempt < MAX_ATTEMPTS:
        attempt += 1
        if not await scraper.connect():
            logger.error(f"Could not connect to IMAP server, attempt {attempt}/{MAX_ATTEMPTS}")
            if attempt == MAX_ATTEMPTS:
                logger.error("Max connection attempts reached, stopping...")
                break
            await asyncio.sleep(RETRY_DELAY)
            continue

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

        await scraper.send_summary_email(health_monitor.actions_taken)

        scraper.stats["vacantes_completas"] = []
        scraper.stats["vacantes_incompletas"] = []

        recommendations = await health_monitor.check_health()
        if recommendations.get("run_gc"):
            gc.collect()
            logger.info("Executed gc.collect() to free memory")
        if recommendations.get("reduce_batch"):
            batch_size = max(1, batch_size // 2)
            logger.info(f"Reduced batch_size to {batch_size} due to high CPU usage")

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