# /home/pablo/app/utilidades/email_scraper.py

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
            "processed_emails": [],
            "vacantes_completas": [],
            "vacantes_incompletas": [],
            "vacantes_ratificadas": 0  # Integrado directamente
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

    async def ratify_existing_vacancy(self, job_data: Dict) -> bool:
        """Verifica y actualiza una vacante existente en la base de datos."""
        try:
            vacante = await sync_to_async(Vacante.objects.filter(
                url_original=job_data["url_original"]
            ).first)()

            if not vacante:
                return False

            updated = False
            for key, value in job_data.items():
                current_value = getattr(vacante, key, None)
                if current_value != value and value:  # Solo actualiza si hay un valor nuevo y diferente
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

    async def save_or_update_vacante(self, job_data: Dict) -> bool:
        """Guarda o actualiza una vacante con asignación dinámica de business_unit."""
        try:
            # Importar localmente para evitar problemas de ámbito
            from app.models import BusinessUnit, Vacante, Worker
            logger.debug("Imports locales realizados correctamente dentro de save_or_update_vacante")

            # Log para verificar los datos de entrada
            logger.debug(f"Datos de entrada: título={job_data.get('titulo')}, descripción={job_data.get('descripcion', '')[:50]}..., ubicación={job_data.get('ubicacion')}")

            # Asignar unidad de negocio dinámicamente
            business_unit_id = await assign_business_unit_async(
                job_title=job_data["titulo"],
                job_description=job_data.get("descripcion", ""),
                location=job_data.get("ubicacion", "")
            )
            logger.debug(f"Business unit ID asignado por assign_business_unit_async: {business_unit_id}")

            # Obtener la unidad de negocio
            if business_unit_id:
                business_unit = await sync_to_async(BusinessUnit.objects.get)(id=business_unit_id)
            else:
                business_unit = await sync_to_async(BusinessUnit.objects.get)(name="huntRED®")
            logger.debug(f"Business unit obtenida: {business_unit}")

            # Intentar ratificar primero
            if await self.ratify_existing_vacancy(job_data):
                return True

            # Si no existe, crear nueva
            worker_tuple = await sync_to_async(Worker.objects.get_or_create)(
                name=job_data["empresa"].name, defaults={"company": job_data["empresa"].name}
            )
            worker = worker_tuple[0]
            logger.debug(f"Worker creado/obtenido: {worker}")

            # Manejar el campo salario
            salario_raw = job_data.get("salario", "")
            try:
                salario = float(salario_raw) if salario_raw else None  # Convertir a float o None si está vacío
            except (ValueError, TypeError):
                salario = None  # Si no es un número válido, usar None
            logger.debug(f"Salario procesado: {salario}")

            vacante = Vacante(
                url_original=job_data["url_original"],
                titulo=job_data["titulo"][:500],
                empresa=worker,
                ubicacion=job_data["ubicacion"][:300],
                descripcion=job_data["descripcion"][:3000],
                modalidad=job_data["modalidad"],
                requisitos=job_data["requisitos"][:1000],
                beneficios=job_data["beneficios"][:1000],
                skills_required=job_data["skills_required"],
                salario=salario,  # Usar el valor procesado
                business_unit=business_unit,
                fecha_publicacion=job_data["fecha_publicacion"],
                activa=True,
                procesamiento_count=1
            )
            await sync_to_async(vacante.save)()
            self.stats["vacantes_guardadas"] += 1
            logger.info(f"Vacante creada: {vacante.titulo}")
            return True
        except Exception as e:
            logger.error(f"Error guardando vacante {job_data.get('titulo', 'Unknown')}: {e}")
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

        # Lista de términos que no son vacantes
        NON_JOB_TITLES = [
            "gestionar alertas", "ver todos los empleos", "buscar empleos", "empleos guardados",
            "see more", "ver más", "alertas", "publicar", "promocionar"
        ]

        for link in soup.find_all("a", href=True):
            href = link["href"].strip().lower()
            link_text = link.get_text(strip=True).lower()

            # Filtrar enlaces que no son vacantes
            if any(non_job in link_text for non_job in NON_JOB_TITLES) or \
               not ("/jobs/view/" in href or any(keyword in link_text for keyword in JOB_KEYWORDS)):
                continue

            job_title = self.format_title(link_text)
            if not job_title or len(job_title) < 10:  # Títulos muy cortos no son vacantes válidas
                continue

            job_container = link.find_parent(['div', 'li', 'tr']) or link.parent
            if not job_container:
                continue

            # Extraer empresa de forma más precisa
            company_elem = (job_container.find(class_=re.compile(r'company|organization|employer', re.I)) or
                           job_container.find(string=re.compile(r'^\w+\s+\w+$', re.I)))
            empresa_name = company_elem.get_text(strip=True) if company_elem else "LinkedIn"
            empresa_tuple = await sync_to_async(Worker.objects.get_or_create)(
                name=empresa_name, defaults={"company": empresa_name}
            )
            empresa = empresa_tuple[0]

            # Extraer ubicación y modalidad
            location_elem = job_container.find(string=re.compile(r'(?:ciudad|área|remote|remoto|híbrido|presencial)', re.I))
            location = location_elem.strip()[:300] if location_elem else "No especificada"
            modality = "Remoto" if "remoto" in location.lower() else "Híbrido" if "híbrido" in location.lower() else "Presencial" if "presencial" in location.lower() else None

            # Extraer descripción inicial
            description = job_container.get_text(strip=True)[:1000]

            job_data = {
                "titulo": job_title,
                "url_original": href,
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
        return job_listings

    async def enrich_vacancy_from_url(self, job_data: Dict) -> Dict:
        """Enriquece la vacante visitando su URL con reintentos."""
        for attempt in range(MAX_RETRIES):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(job_data["url_original"], timeout=aiohttp.ClientTimeout(total=30)) as response:
                        if response.status == 200:
                            html = await response.text()
                            soup = BeautifulSoup(html, "html.parser")

                            # Descripción
                            desc_elem = soup.select_one(".description, .job-description, [class*=description]")
                            job_data["descripcion"] = desc_elem.get_text(strip=True)[:3000] if desc_elem else job_data["descripcion"]

                            # Modalidad
                            text = job_data["descripcion"].lower()
                            job_data["modalidad"] = (
                                "Remoto" if "remoto" in text or "remote" in text else
                                "Híbrido" if "híbrido" in text or "hybrid" in text else
                                "Presencial" if "presencial" in text or "on-site" in text else
                                job_data["modalidad"]
                            )

                            # Requisitos
                            req_elem = soup.select_one(".requirements, [class*=requirements], [class*=qualifications]")
                            job_data["requisitos"] = req_elem.get_text(strip=True)[:1000] if req_elem else ""

                            # Salario (si está presente)
                            salary_elem = soup.find(string=re.compile(r'\$|salario|salary|mxn|usd', re.I))
                            job_data["salario"] = salary_elem.strip()[:100] if salary_elem else ""

                            # Skills
                            skills = re.findall(r'\b(?:python|java|sql|excel|ingles|liderazgo|comunicacion|análisis)\b', text, re.I)
                            job_data["skills_required"] = list(set(skills))

                            return job_data
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1}/{MAX_RETRIES} failed for {job_data['url_original']}: {e}")
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(RETRY_DELAY)
        return job_data  # Devuelve datos parciales si falla

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
                        if await self.save_or_update_vacante(job):  # Sin necesidad de business_unit
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



# Constantes para assign_business_unit
BUSINESS_UNITS_KEYWORDS = {
    'huntRED®': {
        'manager': 2, 'director': 3, 'leadership': 2, 'senior manager': 4, 'operations manager': 3,
        'project manager': 3, 'head of': 4, 'head de': 4, 'gerente': 2, 'director de': 3, 'jefe de': 4, 'subdirector': 3, 'dirección': 3, 'subdirección': 3
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

async def assign_business_unit_async(job_title: str, job_description: str = None, salary_range=None, required_experience=None, location: str = None) -> Optional[int]:
    job_title_lower = job_title.lower()
    job_desc_lower = job_description.lower() if job_description else ""
    location_lower = location.lower() if location else ""

    bu_candidates = await sync_to_async(list)(BusinessUnit.objects.all())
    logger.debug(f"Unidades de negocio disponibles: {[bu.name for bu in bu_candidates]}")
    scores = {bu.name: 0 for bu in bu_candidates}

    seniority_score = 0
    for keyword, score in SENIORITY_KEYWORDS.items():
        if keyword in job_title_lower:
            seniority_score = max(seniority_score, score)
    logger.debug(f"Puntuación de seniority: {seniority_score}")

    industry_scores = {ind: 0 for ind in INDUSTRY_KEYWORDS}
    for ind, keywords in INDUSTRY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in job_title_lower or keyword in job_desc_lower:
                industry_scores[ind] += 1
    dominant_industry = max(industry_scores, key=industry_scores.get) if max(industry_scores.values()) > 0 else None
    logger.debug(f"Industria dominante: {dominant_industry}, puntajes: {industry_scores}")

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
        logger.debug(f"Pesos para {bu.name}: {weights}")

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
            if bu.name == 'huntRED Executive':
                scores[bu.name] += 4 * weights["personalidad"]
            elif bu.name == 'huntRED':
                scores[bu.name] += 2 * weights["soft_skills"]
        elif seniority_score >= 3:
            if bu.name == 'huntRED':
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
                elif bu.name == 'huntRED':
                    scores[bu.name] += 1 * weights["soft_skills"] * industry_scores['tech']
            elif dominant_industry == 'management':
                if bu.name == 'huntRED':
                    scores[bu.name] += 3 * weights["soft_skills"] * industry_scores['management']
                elif bu.name == 'huntRED Executive':
                    scores[bu.name] += 2 * weights["personalidad"] * industry_scores['management']
            elif dominant_industry == 'operations':
                if bu.name == 'amigro':
                    scores[bu.name] += 3 * weights["ubicacion"] * industry_scores['operations']
            elif dominant_industry == 'strategy':
                if bu.name == 'huntRED® Executive':
                    scores[bu.name] += 3 * weights["personalidad"] * industry_scores['strategy']
                elif bu.name == 'huntRED':
                    scores[bu.name] += 1 * weights["soft_skills"] * industry_scores['strategy']

        if job_description:
            if any(term in job_desc_lower for term in ['migration', 'visa', 'bilingual', 'temporary', 'migración']):
                if bu.name == 'amigro':
                    scores[bu.name] += 4 * weights["ubicacion"]
            if any(term in job_desc_lower for term in ['strategic', 'global', 'executive', 'board', 'estrategico']):
                if bu.name == 'huntRED Executive':
                    scores[bu.name] += 3 * weights["personalidad"]
            if any(term in job_desc_lower for term in ['development', 'coding', 'software', 'data', 'programación']):
                if bu.name == 'huntu':
                    scores[bu.name] += 3 * weights["hard_skills"]
            if any(term in job_desc_lower for term in ['operations', 'management', 'leadership', 'gerencia']):
                if bu.name == 'huntRED':
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
    logger.debug(f"Puntuaciones finales: {scores}, candidatos: {candidates}")
    priority_order = ['huntRED Executive', 'huntRED', 'huntu', 'amigro']

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
        chosen_bu = 'huntRED'

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