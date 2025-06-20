# /home/pablo/app/ats/utils/scraping/email_scraper.py
import asyncio
import aioimaplib
import email
import logging
import re
import random
import os
import time
import backoff
import traceback
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Generator, AsyncGenerator
from bs4 import BeautifulSoup
from django.utils import timezone
from functools import wraps
from asgiref.sync import sync_to_async
from app.models import Vacante, BusinessUnit, ConfiguracionBU, DominioScraping, USER_AGENTS
from app.ats.models.worker import Worker
from app.ml.core.utils.scraping import MLScraper
from app.ats.utils.scraping.scraping_utils import ScrapingMetrics, SystemHealthMonitor, ScrapingCache, generate_summary_report
from app.ats.chatbot.core.gpt import GPTHandler
from urllib.parse import urlparse, urljoin
import aiohttp
import environ
import smtplib
from email.mime.text import MIMEText
from playwright.async_api import async_playwright
from app.ats.utils.parser import parse_job_listing, save_job_to_vacante, extract_url
from app.ats.utils.logger_utils import get_module_logger, log_async_function_call, ResourceMonitor

env = environ.Env()
environ.Env.read_env(env_file='/home/pablo/.env')

# Usar el sistema de logging avanzado
logger = get_module_logger('email_scraper')

# Clase para monitorear el progreso
class EmailScraperStats:
    def __init__(self):
        self.start_time = time.time()
        self.processed = 0
        self.successful = 0
        self.failed = 0
        self.skipped = 0
        self.last_execution = None
        self.processing_time = 0
        self.last_errors = []
        self.connection_attempts = 0
        self.connection_failures = 0
    
    def record_success(self):
        self.processed += 1
        self.successful += 1
    
    def record_failure(self, error_msg: str):
        self.processed += 1
        self.failed += 1
        if len(self.last_errors) >= 10:
            self.last_errors.pop(0)
        self.last_errors.append(error_msg)
    
    def record_skip(self):
        self.processed += 1
        self.skipped += 1
    
    def record_connection_attempt(self):
        self.connection_attempts += 1
    
    def record_connection_failure(self):
        self.connection_failures += 1
    
    def finish_execution(self):
        self.last_execution = datetime.now()
        self.processing_time = time.time() - self.start_time
    
    def get_stats(self) -> Dict:
        success_rate = (self.successful / self.processed * 100) if self.processed > 0 else 0
        return {
            "processed": self.processed,
            "successful": self.successful,
            "failed": self.failed,
            "skipped": self.skipped,
            "success_rate": f"{success_rate:.1f}%",
            "processing_time": f"{self.processing_time:.2f}s",
            "last_execution": self.last_execution.isoformat() if self.last_execution else None,
            "connection_health": f"{(1 - self.connection_failures/self.connection_attempts)*100:.1f}%" 
                if self.connection_attempts > 0 else "N/A",
            "last_errors": self.last_errors
        }

# Instancia global para estadísticas
email_stats = EmailScraperStats()

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

# Circuit breaker para conexiones IMAP
class ImapCircuitBreaker:
    def __init__(self):
        self.failures = 0
        self.is_open = False
        self.last_failure_time = 0
        self.reset_timeout = 300  # 5 minutos
        self.threshold = 5  # fallos consecutivos para abrir
    
    def record_failure(self):
        self.failures += 1
        self.last_failure_time = time.time()
        if self.failures >= self.threshold:
            logger.warning(f"Circuit breaker abierto después de {self.failures} fallos consecutivos")
            self.is_open = True
    
    def record_success(self):
        self.failures = 0
        self.is_open = False
    
    def can_execute(self) -> bool:
        if not self.is_open:
            return True
        # Verificar si ha pasado suficiente tiempo para reintentar
        if time.time() - self.last_failure_time > self.reset_timeout:
            logger.info("Reiniciando circuit breaker para IMAP")
            self.is_open = False
            return True
        return False

# Instanciar el circuit breaker
imap_breaker = ImapCircuitBreaker()

@log_async_function_call(logger)
@backoff.on_exception(
    backoff.expo,
    (aioimaplib.AIOMAPException, ConnectionError, TimeoutError),
    max_tries=MAX_RETRIES,
    jitter=backoff.full_jitter
)
async def connect_to_imap():
    """Connect to IMAP server with advanced retry mechanism and circuit breaker pattern."""
    # Verificar estado del circuit breaker
    if not imap_breaker.can_execute():
        logger.warning("Circuit breaker activo, evitando conexión a IMAP")
        raise Exception("IMAP service unavailable due to repeated failures")
        
    email_stats.record_connection_attempt()
    
    try:
        # Registrar uso de memoria antes de la conexión
        ResourceMonitor.log_memory_usage(logger, "before_imap_connect")
        
        # Conectar con timeout
        client = aioimaplib.IMAP4_SSL(IMAP_SERVER, timeout=CONNECTION_TIMEOUT)
        await client.wait_hello_from_server()
        
        # Autenticar
        login_response = await client.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
        if login_response.result != 'OK':
            email_stats.record_connection_failure()
            imap_breaker.record_failure()
            raise aioimaplib.AIOMAPException(f"Login failed: {login_response}")
            
        # Verificar carpetas requeridas
        for folder_name in FOLDER_CONFIG.values():
            select_response = await client.select(folder_name)
            if select_response.result != 'OK':
                logger.warning(f"Folder {folder_name} not available or cannot be selected")
        
        logger.info("Connected to IMAP server successfully")
        imap_breaker.record_success()
        
        # Registrar uso de memoria después de la conexión exitosa
        ResourceMonitor.log_memory_usage(logger, "after_imap_connect")
        
        return client
    except Exception as e:
        email_stats.record_connection_failure()
        imap_breaker.record_failure()
        logger.error(f"IMAP connection failed: {str(e)}", exc_info=True, 
                   extra={"data": {"server": IMAP_SERVER, "account": EMAIL_ACCOUNT}})
        raise

@log_async_function_call(logger)
async def fetch_emails(batch_size=BATCH_SIZE_DEFAULT) -> AsyncGenerator[Tuple[str, email.message.Message], None]:
    """Fetch emails from the inbox with improved error handling and memory management.
    
    Args:
        batch_size: Número máximo de emails a procesar en una ejecución.
        
    Yields:
        Tupla de (email_id, email_message)
    """
    client = None
    start_time = time.time()
    emails_found = 0
    emails_processed = 0
    
    try:
        # Registrar uso de memoria al inicio
        ResourceMonitor.log_memory_usage(logger, "before_fetch_emails")
        
        # Conexión con circuit breaker
        client = await connect_to_imap()
        
        # Seleccionar carpeta con timeout
        select_task = client.select(FOLDER_CONFIG["inbox"])
        status, data = await asyncio.wait_for(select_task, timeout=30)
        
        if status != 'OK':
            raise Exception(f"Failed to select inbox: {data}")
        
        # Búsqueda de emails con timeout
        search_task = client.search(None, "ALL")
        status, data = await asyncio.wait_for(search_task, timeout=30)
        
        if status != 'OK' or not data or not data[0]:
            logger.warning("No emails found or search failed")
            return
            
        email_ids = data[0].split()
        emails_found = len(email_ids)
        logger.info(f"Found {emails_found} emails in inbox")
        
        # Procesar solo los primeros N emails (batch_size)
        for i in range(0, min(emails_found, batch_size)):
            if i > 0 and i % 10 == 0:  # Log de progreso cada 10 emails
                logger.info(f"Progress: {i}/{min(emails_found, batch_size)} emails processed")
                
            email_id = email_ids[i]
            try:
                # Fetch con timeout
                fetch_task = client.fetch(email_id, "(BODY.PEEK[])")
                status, data = await asyncio.wait_for(fetch_task, timeout=60)
                
                if status != 'OK' or not data:
                    logger.warning(f"Failed to fetch email ID {email_id}")
                    email_stats.record_failure(f"Fetch failed for ID {email_id}")
                    continue
                    
                # Parsear email
                raw_email = data[0][1]
                if not raw_email:
                    logger.warning(f"Empty email content for ID {email_id}")
                    email_stats.record_failure(f"Empty content for ID {email_id}")
                    continue
                
                # Crear objeto email con gestión de excepciones para emails mal formados
                try:
                    email_message = email.message_from_bytes(raw_email)
                    emails_processed += 1
                    yield email_id, email_message
                except Exception as parsing_error:
                    logger.error(f"Error parsing email ID {email_id}: {str(parsing_error)}", exc_info=True)
                    email_stats.record_failure(f"Parse error: {str(parsing_error)}")
                    continue
                    
            except asyncio.TimeoutError:
                logger.error(f"Timeout fetching email ID {email_id}")
                email_stats.record_failure(f"Timeout fetching ID {email_id}")
                continue
                
            except Exception as e:
                logger.error(f"Error processing email ID {email_id}: {str(e)}", exc_info=True)
                email_stats.record_failure(f"Error: {str(e)}")
                continue
                
        # Registrar métricas
        elapsed = time.time() - start_time
        logger.info(f"Fetch completed: {emails_processed}/{emails_found} emails in {elapsed:.2f}s")
        
    except Exception as e:
        logger.error(f"Error in fetch_emails: {str(e)}", exc_info=True,
                   extra={"data": {"batch_size": batch_size, "emails_found": emails_found}})
        raise
        
    finally:
        # Cerrar conexión
        if client:
            try:
                await client.close()
                await client.logout()
                logger.debug("IMAP connection closed properly")
            except Exception as e:
                logger.warning(f"Error closing IMAP connection: {str(e)}")
                
        # Registrar uso de memoria al final
        ResourceMonitor.log_memory_usage(logger, "after_fetch_emails")

@log_async_function_call(logger)
async def extract_job_info(email_message) -> Optional[Dict[str, Any]]:
    """Extract job information from email content using consolidated parser.
    
    Args:
        email_message: Objeto email.message.Message a procesar
        
    Returns:
        Diccionario con información del trabajo o None si no se pudo extraer
    """
    parse_start_time = time.time()
    email_id = email_message.get("Message-ID", "unknown")
    content_stats = {"plain_text": 0, "html": 0, "attachments": 0}
    
    try:
        # Extraer metadatos básicos
        subject = email_message.get("Subject", "") or ""
        from_addr = email_message.get("From", "") or ""
        date_str = email_message.get("Date", "")
        body = ""
        
        # Cache key para evitar reprocesamiento (usando hash del contenido)
        cache_key = f"email_{hash(subject)}_{hash(from_addr)}"
        cached_result = await sync_to_async(lambda: cache.get)(cache_key)
        if cached_result:
            logger.info(f"Using cached job info for subject: {subject[:30]}...")
            return cached_result
        
        # Procesar contenido multipart
        if email_message.is_multipart():
            # Extraer todas las partes del mensaje
            for part in email_message.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))
                
                # Texto plano
                if content_type == "text/plain" and "attachment" not in content_disposition:
                    try:
                        payload = part.get_payload(decode=True)
                        if payload:
                            text = payload.decode("utf-8", errors="ignore")
                            body += text
                            content_stats["plain_text"] += len(text)
                    except Exception as e:
                        logger.warning(f"Error decoding plain text part: {str(e)}")
                
                # HTML
                elif content_type == "text/html" and "attachment" not in content_disposition:
                    try:
                        payload = part.get_payload(decode=True)
                        if payload:
                            html = payload.decode("utf-8", errors="ignore")
                            text = BeautifulSoup(html, "html.parser").get_text()
                            body += text
                            content_stats["html"] += len(text)
                    except Exception as e:
                        logger.warning(f"Error processing HTML part: {str(e)}")
                
                # Adjuntos (podría contener detalles del trabajo)
                elif "attachment" in content_disposition:
                    content_stats["attachments"] += 1
        else:
            # Contenido simple
            try:
                payload = email_message.get_payload(decode=True)
                if payload:
                    body = payload.decode("utf-8", errors="ignore")
                    content_stats["plain_text"] += len(body)
            except Exception as e:
                logger.error(f"Error decoding email body: {str(e)}", exc_info=True)
                body = ""
        
        # Registrar estadísticas de contenido
        logger.debug(f"Email content stats: {content_stats}",
                    extra={"data": {"content_stats": content_stats, "subject": subject[:50]}})
        
        # Analizar contenido para extraer información de trabajo
        if not body:
            logger.warning(f"Empty body for email with subject: {subject[:50]}")
            return None
            
        # Deteción de idioma para procesar correctamente
        try:
            language = detect_language(body[:1000])
            logger.debug(f"Detected language: {language}")
        except Exception as e:
            language = "es"  # Default a español
            logger.warning(f"Error detecting language: {str(e)}")
        
        # Parsear contenido
        job_info = parse_job_listing(body, "", source_type="email", language=language)
        
        # Enriquecer con metadatos del email
        if job_info:
            job_info["title"] = subject
            job_info["company"] = from_addr
            job_info["received_date"] = date_str
            job_info["source"] = "email"
            
            # Guardarlo en caché
            await sync_to_async(lambda: cache.set)(cache_key, job_info, timeout=3600*24)
            
            parse_time = time.time() - parse_start_time
            logger.info(f"Job opportunity detected in {parse_time:.2f}s: {subject}", 
                      extra={"data": {"parse_time": parse_time}})
            return job_info
            
        parse_time = time.time() - parse_start_time
        logger.info(f"No job opportunity detected in {parse_time:.2f}s")
        return None
        
    except Exception as e:
        parse_time = time.time() - parse_start_time
        logger.error(f"Error extracting job info from email {email_id}: {str(e)}", 
                   exc_info=True, 
                   extra={"data": {
                       "subject": subject if 'subject' in locals() else "unknown",
                       "parse_time": parse_time
                   }})
        return None

async def save_to_vacante(job_info, bu):
    """Save extracted job info to Vacante model using parser utility."""
    return await save_job_to_vacante(job_info, bu)

async def move_email(client, email_id, folder):
    """Move email to specified folder with error handling."""
    try:
        await client.select(FOLDER_CONFIG["inbox"])
        await client.copy(email_id, FOLDER_CONFIG[folder])
        await client.delete(email_id)
        await client.expunge()
        logger.info(f"Moved email ID {email_id} to {folder}")
    except Exception as e:
        logger.error(f"Error moving email ID {email_id} to {folder}: {str(e)}")

@log_async_function_call(logger)
async def process_emails(batch_size=BATCH_SIZE_DEFAULT, business_unit_name="huntred", notify_admin=True):
    """Process emails to extract job positions with batch handling and robust error management.
    
    Args:
        batch_size: Número máximo de emails a procesar
        business_unit_name: Nombre de la unidad de negocio para la que se procesan los emails
        notify_admin: Si True, envía notificación al admin al finalizar
    """
    start_time = time.time()
    client = None
    email_stats.start_time = start_time  # Resetear estadísticas
    
    try:
        # Registrar uso de memoria inicial
        ResourceMonitor.log_memory_usage(logger, "process_emails_start")
        ResourceMonitor.log_cpu_usage(logger, "process_emails_start")
        
        # Obtener unidad de negocio
        try:
            bu = await sync_to_async(BusinessUnit.objects.get)(name=business_unit_name)
            logger.info(f"Processing emails for business unit: {business_unit_name}")
        except Exception as e:
            logger.error(f"Error getting business unit '{business_unit_name}': {str(e)}", exc_info=True)
            raise
            
        # Procesar emails en lotes
        semaphore = asyncio.Semaphore(5)  # Limitar procesamiento concurrente
        connection_pool = aiohttp.ClientSession()  # Pool de conexiones HTTP
        
        async def process_single_email(email_id, email_message):
            async with semaphore:  # Limitar concurrencia
                nonlocal client
                try:
                    # Extraer información del trabajo
                    job_info = await extract_job_info(email_message)
                    
                    if job_info:
                        # Guardar en base de datos
                        vacante = await save_to_vacante(job_info, bu)
                        
                        if vacante:
                            # Mover a carpeta de parseados
                            client = await connect_to_imap()
                            await move_email(client, email_id, "parsed_folder")
                            email_stats.record_success()
                            logger.info(f"Email {email_id} processed successfully and saved as vacancy {vacante.id}")
                            
                            # Notificar al manager apropiado según la clasificación
                            if vacante.responsible_email:
                                await send_email(
                                    business_unit_name=bu.name,
                                    subject=f"Nueva vacante detectada: {vacante.titulo}",
                                    to_email=vacante.responsible_email,
                                    body=f"Se ha detectado una nueva vacante: {vacante.titulo}\n\n"
                                         f"Empresa: {vacante.empresa}\n"
                                         f"Ubicación: {vacante.ubicacion}\n"
                                         f"Ver detalles: {settings.DOMAIN}/admin/app/vacante/{vacante.id}/change/",
                                    from_email="noreply@huntred.com"
                                )
                        else:
                            # Error al guardar - mover a carpeta de error
                            client = await connect_to_imap()
                            await move_email(client, email_id, "error_folder")
                            email_stats.record_failure("Failed to save vacancy")
                            logger.warning(f"Failed to save vacancy from email {email_id}")
                    else:
                        # No es una vacante - mover a carpeta de trabajos genéricos
                        client = await connect_to_imap()
                        await move_email(client, email_id, "jobs_folder")
                        email_stats.record_skip()
                        logger.info(f"Email {email_id} doesn't contain job information")                        
                except Exception as e:
                    # Error general - mover a carpeta de error
                    logger.error(f"Error processing email {email_id}: {str(e)}", exc_info=True)
                    email_stats.record_failure(str(e))
                    try:
                        client = await connect_to_imap()
                        await move_email(client, email_id, "error_folder")
                    except Exception as move_error:
                        logger.error(f"Failed to move email to error folder: {str(move_error)}")
                finally:
                    # Cerrar conexión IMAP si está abierta
                    if client:
                        try:
                            await client.close()
                            await client.logout()
                        except Exception:
                            pass
            
        # Procesar emails en paralelo (con límite de concurrencia)
        tasks = []
        async for email_id, email_message in fetch_emails(batch_size=batch_size):
            task = asyncio.create_task(process_single_email(email_id, email_message))
            tasks.append(task)
            
        if tasks:
            # Esperar a que todas las tareas terminen
            await asyncio.gather(*tasks)
        else:
            logger.info("No emails to process")
            
        # Finalizar pool de conexiones HTTP
        await connection_pool.close()
        
        # Registrar estadísticas finales
        end_time = time.time()
        email_stats.finish_execution()
        stats = email_stats.get_stats()
        
        # Registrar métricas finales
        logger.info(f"Email processing completed in {end_time - start_time:.2f}s", 
                  extra={"data": stats})
        ResourceMonitor.log_memory_usage(logger, "process_emails_end")
        ResourceMonitor.log_cpu_usage(logger, "process_emails_end")
        
        # Notificar al administrador
        if notify_admin and stats["processed"] > 0:
            admin_email = bu.admin_email or 'pablo@huntred.com'
            try:
                await send_email(
                    business_unit_name=bu.name,
                    subject=f"Resumen de procesamiento de emails - {datetime.now().strftime('%Y-%m-%d')}",
                    to_email=admin_email,
                    body=f"Resumen de procesamiento:\n\n"
                         f"Total procesados: {stats['processed']}\n"
                         f"Exitosos: {stats['successful']}\n"
                         f"Fallidos: {stats['failed']}\n"
                         f"Omitidos: {stats['skipped']}\n"
                         f"Tasa de éxito: {stats['success_rate']}\n"
                         f"Tiempo de procesamiento: {stats['processing_time']}\n\n"
                         f"Últimos errores:\n{chr(10).join(stats['last_errors'][:5]) if stats['last_errors'] else 'Ninguno'}",
                    from_email="noreply@huntred.com"
                )
                logger.info(f"Summary email sent to {admin_email}")
            except Exception as e:
                logger.error(f"Failed to send summary email: {str(e)}")
                
    except Exception as e:
        logger.error(f"Fatal error in process_emails: {str(e)}", exc_info=True)
        if notify_admin:
            try:
                await send_email(
                    business_unit_name="Sistema",
                    subject="⚠ ERROR: Fallo en procesamiento de emails",
                    to_email="pablo@huntred.com",
                    body=f"Ha ocurrido un error fatal en el procesamiento de emails:\n\n{str(e)}\n\n"
                         f"Detalles completos están disponibles en el log del servidor.",
                    from_email="noreply@huntred.com"
                )
            except Exception:
                pass  # No podemos hacer mucho si esto falla también
        raise

@shared_task
def process_emails_task(batch_size=BATCH_SIZE_DEFAULT, business_unit_name="huntred"):
    """Tarea Celery para procesar emails en segundo plano."""
    asyncio.run(process_emails(batch_size, business_unit_name))
    return "Email processing completed"

# Función para ejecución directa
async def process_all_emails(batch_size=BATCH_SIZE_DEFAULT):
    """Ejecuta el procesamiento completo de emails para todas las unidades de negocio."""
    for bu_name in ["huntred", "huntu", "amigro", "sexsi"]:
        try:
            logger.info(f"Processing emails for {bu_name}")
            await process_emails(batch_size, bu_name)
        except Exception as e:
            logger.error(f"Error processing emails for {bu_name}: {str(e)}", exc_info=True)

# Para ejecución desde línea de comandos
if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ai_huntred.settings")
    import django
    django.setup()
    asyncio.run(process_all_emails())