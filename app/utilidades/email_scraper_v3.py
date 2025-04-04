# /home/pablo/app/utilidades/email_scraper_v3.py
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

# Configuración de entorno
env = environ.Env()
environ.Env.read_env(env_file='/home/pablo/.env')

# Configuración de NLP
ENABLE_NLP = env.bool("ENABLE_NLP", default=False)

# Configuración de logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("/home/pablo/logs/email_scraper_v3.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Constantes
IMAP_SERVER = env("IMAP_SERVER", default="mail.huntred.com")
CONNECTION_TIMEOUT = 60
BATCH_SIZE_DEFAULT = 5
JOB_KEYWORDS = ["job", "vacante", "opportunity", "empleo", "position", "director", "analista", "gerente", "asesor"]
EXCLUDED_TEXTS = ["unsubscribe", "manage", "help", "profile", "feed"]
FOLDER_CONFIG = {
    "inbox": "INBOX",
    "jobs_folder": "INBOX.Jobs",
    "parsed_folder": "INBOX.Parsed",
    "error_folder": "INBOX.Error",
}

# ... (resto de las constantes igual que antes)

class EmailScraperV3:
    def __init__(self, email_account: str, password: str, imap_server: str = IMAP_SERVER):
        self.email_account = email_account
        self.password = password
        self.imap_server = imap_server
        self.mail = None
        self.retry_count = 3
        self.retry_delay = 5
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

    async def process_job_alert_email(self, email_id: str) -> List[Dict]:
        message = await self.fetch_email(email_id)
        if not message:
            logger.info(f"No se obtuvo correo para ID {email_id}")
            await self.mail.copy(email_id, FOLDER_CONFIG["error_folder"])
            await self.mail.store(email_id, "+FLAGS", "\\Deleted")
            return []

        sender = message.get("From", "").lower()
        subject = message.get("Subject", "").lower()
        
        # Priorizar correos de LinkedIn
        is_linkedin = "linkedin" in sender or "linkedin" in subject
        if is_linkedin:
            logger.info(f"Procesando correo de LinkedIn: {subject}")
        else:
            valid_senders = await self.get_valid_senders()
            is_valid_sender = any(valid_sender in sender for valid_sender in valid_senders)
            is_job_alert = any(keyword in subject for keyword in JOB_KEYWORDS)
            
            if not (is_valid_sender or is_job_alert):
                logger.info(f"Correo {email_id} omitido - no es alerta válida (Sender: {sender}, Subject: {subject})")
                await self.mail.copy(email_id, FOLDER_CONFIG["parsed_folder"])
                await self.mail.store(email_id, "+FLAGS", "\\Deleted")
                return []

        # Procesar el cuerpo del correo
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

        job_listings = await self.extract_vacancies_from_html(body)
        if not job_listings:
            logger.info(f"No se encontraron vacantes en correo {email_id}")
            await self.mail.copy(email_id, FOLDER_CONFIG["parsed_folder"])
            await self.mail.store(email_id, "+FLAGS", "\\Deleted")
            return []

        # Marcar como LinkedIn si corresponde
        for job in job_listings:
            if is_linkedin:
                job["is_linkedin"] = True

        enriched_jobs = await asyncio.gather(*(self.enrich_vacancy_from_url(job) for job in job_listings))
        logger.info(f"Extraídas y enriquecidas {len(enriched_jobs)} vacantes del correo {email_id}")
        return enriched_jobs

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

            # Separar correos de LinkedIn y otros
            linkedin_ids = []
            other_ids = []
            
            for email_id in email_ids:
                resp, data = await self.mail.fetch(email_id, "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT)])")
                if resp == "OK" and data:
                    header_data = data[0][1].decode()
                    if "linkedin" in header_data.lower():
                        linkedin_ids.append(email_id)
                    else:
                        other_ids.append(email_id)

            logger.info(f"Identificados {len(linkedin_ids)} correos de LinkedIn y {len(other_ids)} de otras fuentes")

            # Procesar primero LinkedIn
            for email_id in linkedin_ids[:batch_size]:
                if not await self.ensure_connection():
                    logger.error("Conexión perdida y no se pudo reconectar")
                    break

                job_listings = await self.process_job_alert_email(email_id)
                if not job_listings:
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
                    logger.info(f"Correo LinkedIn {email_id} procesado exitosamente")
                else:
                    await self.mail.copy(email_id, FOLDER_CONFIG["error_folder"])
                    await self.mail.store(email_id, "+FLAGS", "\\Deleted")
                    logger.warning(f"Error procesando correo LinkedIn {email_id}: {failures} vacantes fallaron")

            # Luego procesar otros correos
            for email_id in other_ids[:batch_size]:
                if not await self.ensure_connection():
                    logger.error("Conexión perdida y no se pudo reconectar")
                    break

                job_listings = await self.process_job_alert_email(email_id)
                if not job_listings:
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
                    logger.info(f"Correo {email_id} procesado exitosamente")
                else:
                    await self.mail.copy(email_id, FOLDER_CONFIG["error_folder"])
                    await self.mail.store(email_id, "+FLAGS", "\\Deleted")
                    logger.warning(f"Error procesando correo {email_id}: {failures} vacantes fallaron")

            logger.info(f"Procesamiento completado: {len(linkedin_ids) + len(other_ids)} correos procesados")

        except Exception as e:
            logger.error(f"Error en ejecución principal: {e}", exc_info=True)
        finally:
            try:
                await self.mail.logout()
            except asyncio.TimeoutError:
                logger.warning("Timeout durante logout, conexión cerrada forzosamente")
                self.mail = None

if __name__ == "__main__":
    import os
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ai_huntred.settings")
    import django
    django.setup()

    EMAIL_ACCOUNT = env("EMAIL_ACCOUNT", default="pablo@huntred.com")
    EMAIL_PASSWORD = env("EMAIL_PASSWORD", default="Natalia&Patricio1113!")
    
    async def process_all_emails():
        scraper = EmailScraperV3(EMAIL_ACCOUNT, EMAIL_PASSWORD)
        batch_size = 3
        pause_minutes = .5

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
                await asyncio.sleep(pause_minutes * 30)
            else:
                logger.info("Último lote procesado, finalizando...")
                break

    asyncio.run(process_all_emails()) 