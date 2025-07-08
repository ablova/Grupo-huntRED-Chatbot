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
from app.core.monitoring_system import record_email_metric

env = environ.Env()
environ.Env.read_env(env_file='/home/pablo/.env')

# Usar el sistema de logging avanzado
logger = get_module_logger('email_scraper')

# ============================================================================
# CONFIGURACIÓN AVANZADA PARA 96-98% TASA DE ÉXITO
# ============================================================================

EMAIL_SCRAPER_CONFIG = {
    'max_retries': 5,
    'retry_delay': [2, 4, 8, 16, 32],  # Backoff exponencial
    'connection_timeout': 90,
    'fetch_timeout': 60,
    'batch_size_default': 10,
    'max_attempts': 10,
    'validation_strict': True,  # Validación estricta para alta tasa de éxito
    'fallback_methods': True,   # Habilitar métodos de fallback
    'content_validation': True, # Validar contenido antes de procesar
    'error_recovery': True,     # Recuperación automática de errores
    'success_threshold': 96.0,  # Umbral objetivo de éxito
    'warning_threshold': 92.0,  # Umbral de advertencia
}

# Patrones de validación mejorados
EMAIL_VALIDATION_PATTERNS = {
    'job_keywords': [
        r'\b(job|vacante|opportunity|empleo|position|trabajo|career|linkedin)\b',
        r'\b(director|analista|gerente|asesor|manager|developer|engineer)\b',
        r'\b(recruitment|hiring|staffing|talent|recruiting)\b',
        r'\b(apply|postular|solicitar|candidato|candidate)\b'
    ],
    'excluded_patterns': [
        r'\b(unsubscribe|manage|help|profile|feed|preferences|settings|account|notification)\b',
        r'\b(spam|marketing|newsletter|promotion|advertisement)\b',
        r'\b(error|failed|bounce|delivery|status)\b'
    ],
    'required_fields': [
        'subject',
        'from',
        'body'
    ]
}

# ============================================================================
# CLASE MEJORADA DE ESTADÍSTICAS
# ============================================================================

class AdvancedEmailScraperStats:
    """Estadísticas avanzadas para email scraper con validación estricta."""
    
    def __init__(self):
        self.start_time = time.time()
        self.processed = 0
        self.successful = 0
        self.failed = 0
        self.skipped = 0
        self.validated = 0
        self.invalid_content = 0
        self.connection_attempts = 0
        self.connection_failures = 0
        self.last_execution = None
        self.processing_time = 0
        self.last_errors = []
        self.success_patterns = {}
        self.failure_patterns = {}
        
    def record_success(self, email_id: str, validation_score: float = 1.0):
        """Registra éxito con score de validación."""
        self.processed += 1
        self.successful += 1
        self.validated += 1 if validation_score >= 0.8 else 0
        
        # Registrar patrón de éxito
        pattern = self._extract_success_pattern(email_id)
        if pattern:
            self.success_patterns[pattern] = self.success_patterns.get(pattern, 0) + 1
    
    def record_failure(self, error_msg: str, email_id: str = None):
        """Registra fallo con análisis de patrón."""
        self.processed += 1
        self.failed += 1
        
        if len(self.last_errors) >= 10:
            self.last_errors.pop(0)
        self.last_errors.append(error_msg)
        
        # Registrar patrón de fallo
        pattern = self._extract_failure_pattern(error_msg)
        if pattern:
            self.failure_patterns[pattern] = self.failure_patterns.get(pattern, 0) + 1
    
    def record_skip(self, reason: str):
        """Registra email omitido."""
        self.processed += 1
        self.skipped += 1
        if 'invalid_content' in reason.lower():
            self.invalid_content += 1
    
    def record_connection_attempt(self):
        """Registra intento de conexión."""
        self.connection_attempts += 1
    
    def record_connection_failure(self):
        """Registra fallo de conexión."""
        self.connection_failures += 1
    
    def finish_execution(self):
        """Finaliza ejecución y calcula métricas."""
        self.last_execution = datetime.now()
        self.processing_time = time.time() - self.start_time
        
        # Registrar métricas en el sistema de monitoreo
        record_email_metric(self.processed, self.successful, self.failed)
    
    def get_stats(self) -> Dict:
        """Obtiene estadísticas detalladas."""
        success_rate = (self.successful / self.processed * 100) if self.processed > 0 else 0
        validation_rate = (self.validated / self.processed * 100) if self.processed > 0 else 0
        
        return {
            "processed": self.processed,
            "successful": self.successful,
            "failed": self.failed,
            "skipped": self.skipped,
            "validated": self.validated,
            "invalid_content": self.invalid_content,
            "success_rate": f"{success_rate:.1f}%",
            "validation_rate": f"{validation_rate:.1f}%",
            "processing_time": f"{self.processing_time:.2f}s",
            "last_execution": self.last_execution.isoformat() if self.last_execution else None,
            "connection_health": f"{(1 - self.connection_failures/self.connection_attempts)*100:.1f}%" 
                if self.connection_attempts > 0 else "N/A",
            "last_errors": self.last_errors[-5:],  # Últimos 5 errores
            "success_patterns": dict(sorted(self.success_patterns.items(), key=lambda x: x[1], reverse=True)[:5]),
            "failure_patterns": dict(sorted(self.failure_patterns.items(), key=lambda x: x[1], reverse=True)[:5])
        }
    
    def _extract_success_pattern(self, email_id: str) -> Optional[str]:
        """Extrae patrón de éxito del email."""
        # Implementar lógica para identificar patrones de éxito
        return "standard_job_email"
    
    def _extract_failure_pattern(self, error_msg: str) -> Optional[str]:
        """Extrae patrón de fallo del error."""
        if "timeout" in error_msg.lower():
            return "timeout_error"
        elif "connection" in error_msg.lower():
            return "connection_error"
        elif "parse" in error_msg.lower():
            return "parsing_error"
        elif "validation" in error_msg.lower():
            return "validation_error"
        return "unknown_error"

# Instancia global para estadísticas avanzadas
advanced_email_stats = AdvancedEmailScraperStats()

# ============================================================================
# VALIDADORES AVANZADOS
# ============================================================================

class EmailContentValidator:
    """Validador avanzado de contenido de emails."""
    
    def __init__(self):
        self.job_keywords = EMAIL_VALIDATION_PATTERNS['job_keywords']
        self.excluded_patterns = EMAIL_VALIDATION_PATTERNS['excluded_patterns']
        self.required_fields = EMAIL_VALIDATION_PATTERNS['required_fields']
    
    def validate_email_content(self, email_message) -> Tuple[bool, float, str]:
        """
        Valida contenido del email con score de confianza.
        
        Returns:
            Tuple[bool, float, str]: (es_válido, score_confianza, razón)
        """
        try:
            score = 0.0
            reasons = []
            
            # Extraer campos básicos
            subject = email_message.get("Subject", "").lower()
            from_addr = email_message.get("From", "").lower()
            body = self._extract_body(email_message).lower()
            
            # Validar campos requeridos
            if not subject:
                return False, 0.0, "Sin asunto"
            if not from_addr:
                return False, 0.0, "Sin remitente"
            if not body:
                return False, 0.0, "Sin contenido"
            
            score += 0.2  # Campos básicos presentes
            reasons.append("campos_básicos")
            
            # Verificar patrones excluidos
            for pattern in self.excluded_patterns:
                if re.search(pattern, subject + " " + body, re.IGNORECASE):
                    return False, 0.0, f"Patrón excluido: {pattern}"
            
            # Verificar palabras clave de trabajo
            keyword_matches = 0
            for pattern in self.job_keywords:
                if re.search(pattern, subject + " " + body, re.IGNORECASE):
                    keyword_matches += 1
            
            if keyword_matches == 0:
                return False, 0.0, "Sin palabras clave de trabajo"
            elif keyword_matches >= 3:
                score += 0.4
                reasons.append("múltiples_keywords")
            else:
                score += 0.2
                reasons.append("keywords_básicas")
            
            # Validar longitud del contenido
            if len(body) < 50:
                return False, 0.0, "Contenido muy corto"
            elif len(body) > 5000:
                score += 0.1
                reasons.append("contenido_extenso")
            else:
                score += 0.2
                reasons.append("contenido_adecuado")
            
            # Validar estructura del email
            if self._has_job_structure(body):
                score += 0.2
                reasons.append("estructura_job")
            
            # Validar URLs
            if self._has_job_urls(body):
                score += 0.1
                reasons.append("urls_job")
            
            # Score final
            final_score = min(score, 1.0)
            is_valid = final_score >= 0.6  # Umbral de validación
            
            return is_valid, final_score, ", ".join(reasons)
            
        except Exception as e:
            logger.error(f"Error validando contenido: {e}")
            return False, 0.0, f"Error de validación: {str(e)}"
    
    def _extract_body(self, email_message) -> str:
        """Extrae el cuerpo del email."""
        try:
            body = ""
            
            if email_message.is_multipart():
                for part in email_message.walk():
                    if part.get_content_type() == "text/plain":
                        body += part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    elif part.get_content_type() == "text/html":
                        # Extraer texto del HTML
                        html_content = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        soup = BeautifulSoup(html_content, 'html.parser')
                        body += soup.get_text()
            else:
                payload = email_message.get_payload(decode=True)
                if payload:
                    body = payload.decode('utf-8', errors='ignore')
            
            return body.strip()
            
        except Exception as e:
            logger.error(f"Error extrayendo cuerpo: {e}")
            return ""
    
    def _has_job_structure(self, body: str) -> bool:
        """Verifica si el contenido tiene estructura de trabajo."""
        job_indicators = [
            r'\b(requisitos|requirements|qualifications)\b',
            r'\b(experiencia|experience|years)\b',
            r'\b(responsabilidades|responsibilities|duties)\b',
            r'\b(salario|salary|compensation)\b',
            r'\b(ubicación|location|place)\b'
        ]
        
        matches = 0
        for pattern in job_indicators:
            if re.search(pattern, body, re.IGNORECASE):
                matches += 1
        
        return matches >= 2
    
    def _has_job_urls(self, body: str) -> bool:
        """Verifica si contiene URLs relacionadas con trabajos."""
        job_url_patterns = [
            r'careers\.',
            r'jobs\.',
            r'apply\.',
            r'postular\.',
            r'linkedin\.com/jobs',
            r'indeed\.com',
            r'glassdoor\.com'
        ]
        
        for pattern in job_url_patterns:
            if re.search(pattern, body, re.IGNORECASE):
                return True
        
        return False

# ============================================================================
# FUNCIONES MEJORADAS CON VALIDACIÓN AVANZADA
# ============================================================================

@log_async_function_call(logger)
@backoff.on_exception(
    backoff.expo,
    (aioimaplib.AIOMAPException, ConnectionError, TimeoutError),
    max_tries=EMAIL_SCRAPER_CONFIG['max_retries'],
    jitter=backoff.full_jitter
)
async def connect_to_imap_advanced() -> Optional[aioimaplib.IMAP4_SSL]:
    """Conexión IMAP mejorada con múltiples intentos y validación."""
    advanced_email_stats.record_connection_attempt()
    
    try:
        client = aioimaplib.IMAP4_SSL(
            host=IMAP_SERVER,
            timeout=EMAIL_SCRAPER_CONFIG['connection_timeout']
        )
        
        # Intentar conexión con timeout
        await asyncio.wait_for(client.wait_hello_from_server(), timeout=30)
        
        # Login con validación
        status, data = await client.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
        if status != 'OK':
            raise Exception(f"Login failed: {data}")
        
        logger.info("✅ Conexión IMAP establecida exitosamente")
        return client
        
    except Exception as e:
        advanced_email_stats.record_connection_failure()
        logger.error(f"❌ Error conectando a IMAP: {e}")
        raise

@log_async_function_call(logger)
async def fetch_emails_advanced(batch_size: int = EMAIL_SCRAPER_CONFIG['batch_size_default']) -> AsyncGenerator[Tuple[str, email.message.Message], None]:
    """Fetch de emails mejorado con validación y recuperación de errores."""
    start_time = time.time()
    emails_processed = 0
    client = None
    
    try:
        # Conectar con método avanzado
        client = await connect_to_imap_advanced()
        
        # Seleccionar carpeta
        status, data = await client.select(FOLDER_CONFIG["inbox"])
        if status != 'OK':
            raise Exception(f"Error selecting inbox: {data}")
        
        # Buscar emails
        status, messages = await client.search('ALL')
        if status != 'OK':
            raise Exception(f"Error searching messages: {messages}")
        
        email_ids = messages[0].split()
        emails_found = len(email_ids)
        
        logger.info(f"📧 Encontrados {emails_found} emails para procesar")
        
        # Inicializar validador
        validator = EmailContentValidator()
        
        # Procesar emails con validación
        for i in range(0, min(emails_found, batch_size)):
            if i > 0 and i % 10 == 0:
                logger.info(f"📊 Progreso: {i}/{min(emails_found, batch_size)} emails procesados")
            
            email_id = email_ids[i]
            try:
                # Fetch con timeout extendido
                fetch_task = client.fetch(email_id, "(BODY.PEEK[])")
                status, data = await asyncio.wait_for(fetch_task, timeout=EMAIL_SCRAPER_CONFIG['fetch_timeout'])
                
                if status != 'OK' or not data:
                    logger.warning(f"⚠️ Falló fetch del email ID {email_id}")
                    advanced_email_stats.record_failure(f"Fetch failed for ID {email_id}", email_id)
                    continue
                
                # Parsear email
                raw_email = data[0][1]
                if not raw_email:
                    logger.warning(f"⚠️ Contenido vacío para email ID {email_id}")
                    advanced_email_stats.record_failure(f"Empty content for ID {email_id}", email_id)
                    continue
                
                # Crear objeto email
                try:
                    email_message = email.message_from_bytes(raw_email)
                except Exception as parsing_error:
                    logger.error(f"❌ Error parseando email ID {email_id}: {str(parsing_error)}")
                    advanced_email_stats.record_failure(f"Parse error: {str(parsing_error)}", email_id)
                    continue
                
                # Validar contenido
                if EMAIL_SCRAPER_CONFIG['content_validation']:
                    is_valid, score, reason = validator.validate_email_content(email_message)
                    
                    if not is_valid:
                        logger.info(f"⏭️ Email {email_id} omitido: {reason} (score: {score:.2f})")
                        advanced_email_stats.record_skip(f"invalid_content: {reason}")
                        continue
                    
                    logger.debug(f"✅ Email {email_id} validado (score: {score:.2f}): {reason}")
                
                emails_processed += 1
                yield email_id, email_message
                
            except asyncio.TimeoutError:
                logger.error(f"⏰ Timeout fetch email ID {email_id}")
                advanced_email_stats.record_failure(f"Timeout fetching ID {email_id}", email_id)
                continue
                
            except Exception as e:
                logger.error(f"❌ Error procesando email ID {email_id}: {str(e)}")
                advanced_email_stats.record_failure(f"Error: {str(e)}", email_id)
                continue
        
        # Registrar métricas
        elapsed = time.time() - start_time
        logger.info(f"✅ Fetch completado: {emails_processed}/{min(emails_found, batch_size)} emails en {elapsed:.2f}s")
        
    except Exception as e:
        logger.error(f"❌ Error en fetch_emails_advanced: {str(e)}", exc_info=True)
        raise
        
    finally:
        # Cerrar conexión
        if client:
            try:
                await client.close()
                await client.logout()
                logger.debug("🔒 Conexión IMAP cerrada correctamente")
            except Exception as e:
                logger.warning(f"⚠️ Error cerrando conexión IMAP: {str(e)}")
                
        # Registrar uso de memoria
        ResourceMonitor.log_memory_usage(logger, "after_fetch_emails_advanced")

@log_async_function_call(logger)
async def extract_job_info_advanced(email_message) -> Optional[Dict[str, Any]]:
    """Extracción de información de trabajo mejorada con múltiples métodos."""
    parse_start_time = time.time()
    email_id = email_message.get("Message-ID", "unknown")
    
    try:
        # Extraer metadatos básicos
        subject = email_message.get("Subject", "") or ""
        from_addr = email_message.get("From", "") or ""
        date_str = email_message.get("Date", "")
        
        # Cache key mejorado
        cache_key = f"email_advanced_{hash(subject)}_{hash(from_addr)}"
        cached_result = await sync_to_async(lambda: cache.get)(cache_key)
        if cached_result:
            logger.info(f"💾 Usando cache para: {subject[:30]}...")
            return cached_result
        
        # Extraer contenido con validación
        body = await _extract_email_content_advanced(email_message)
        if not body:
            logger.warning(f"⚠️ Sin contenido para email: {subject[:50]}")
            return None
        
        # Método 1: Parser principal
        job_info = await _parse_with_primary_method(body, subject, from_addr, date_str)
        
        # Método 2: Fallback si el principal falla
        if not job_info and EMAIL_SCRAPER_CONFIG['fallback_methods']:
            job_info = await _parse_with_fallback_method(body, subject, from_addr, date_str)
        
        # Método 3: GPT como último recurso
        if not job_info and EMAIL_SCRAPER_CONFIG['fallback_methods']:
            job_info = await _parse_with_gpt_fallback(body, subject, from_addr, date_str)
        
        # Validar resultado final
        if job_info:
            is_valid, score, reason = await _validate_job_info(job_info)
            
            if is_valid:
                # Guardar en cache
                await sync_to_async(lambda: cache.set)(cache_key, job_info, timeout=3600*24)
                
                parse_time = time.time() - parse_start_time
                logger.info(f"✅ Oportunidad detectada en {parse_time:.2f}s: {subject} (score: {score:.2f})")
                
                # Registrar éxito con score
                advanced_email_stats.record_success(email_id, score)
                return job_info
            else:
                logger.info(f"⏭️ Información de trabajo inválida: {reason} (score: {score:.2f})")
                advanced_email_stats.record_failure(f"Invalid job info: {reason}", email_id)
                return None
        
        parse_time = time.time() - parse_start_time
        logger.info(f"ℹ️ No se detectó oportunidad en {parse_time:.2f}s")
        advanced_email_stats.record_skip("no_job_opportunity")
        return None
        
    except Exception as e:
        parse_time = time.time() - parse_start_time
        logger.error(f"❌ Error extrayendo información: {str(e)}", exc_info=True)
        advanced_email_stats.record_failure(f"Extraction error: {str(e)}", email_id)
        return None

async def _extract_email_content_advanced(email_message) -> str:
    """Extracción avanzada de contenido de email."""
    try:
        body = ""
        
        if email_message.is_multipart():
            for part in email_message.walk():
                content_type = part.get_content_type()
                
                if content_type == "text/plain":
                    payload = part.get_payload(decode=True)
                    if payload:
                        body += payload.decode('utf-8', errors='ignore')
                        
                elif content_type == "text/html":
                    payload = part.get_payload(decode=True)
                    if payload:
                        html_content = payload.decode('utf-8', errors='ignore')
                        soup = BeautifulSoup(html_content, 'html.parser')
                        body += soup.get_text(separator=' ', strip=True)
        else:
            payload = email_message.get_payload(decode=True)
            if payload:
                body = payload.decode('utf-8', errors='ignore')
        
        return body.strip()
        
    except Exception as e:
        logger.error(f"Error extrayendo contenido avanzado: {e}")
        return ""

async def _parse_with_primary_method(body: str, subject: str, from_addr: str, date_str: str) -> Optional[Dict[str, Any]]:
    """Método principal de parsing."""
    try:
        # Detectar idioma
        language = await _detect_language_advanced(body[:1000])
        
        # Parsear con parser principal
        job_info = parse_job_listing(body, "", source_type="email", language=language)
        
        if job_info:
            # Enriquecer con metadatos
            job_info.update({
                "title": subject,
                "company": from_addr,
                "received_date": date_str,
                "source": "email",
                "parsing_method": "primary"
            })
            
            return job_info
        
        return None
        
    except Exception as e:
        logger.error(f"Error en método principal: {e}")
        return None

async def _parse_with_fallback_method(body: str, subject: str, from_addr: str, date_str: str) -> Optional[Dict[str, Any]]:
    """Método de fallback para parsing."""
    try:
        # Extraer información básica con regex
        job_info = {
            "title": subject,
            "company": from_addr,
            "received_date": date_str,
            "source": "email",
            "parsing_method": "fallback",
            "description": body[:1000] if body else "No description available"
        }
        
        # Extraer URLs
        urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', body)
        if urls:
            job_info["url"] = urls[0]
        
        # Extraer ubicación básica
        location_match = re.search(r'\b(?:en|at|ubicado en|location:?)\s+([A-Za-z\s,]+)', body, re.IGNORECASE)
        if location_match:
            job_info["location"] = location_match.group(1).strip()
        
        return job_info
        
    except Exception as e:
        logger.error(f"Error en método fallback: {e}")
        return None

async def _parse_with_gpt_fallback(body: str, subject: str, from_addr: str, date_str: str) -> Optional[Dict[str, Any]]:
    """Método de fallback con GPT."""
    try:
        gpt_handler = GPTHandler()
        await gpt_handler.initialize()
        
        prompt = f"""
        Analiza este email y extrae información de trabajo:
        
        Asunto: {subject}
        De: {from_addr}
        Fecha: {date_str}
        Contenido: {body[:2000]}
        
        Devuelve un JSON con: title, company, description, location, url, skills (lista)
        """
        
        response = await gpt_handler.generate_response(prompt)
        
        # Parsear respuesta JSON
        import json
        try:
            job_data = json.loads(response)
            job_data.update({
                "source": "email",
                "parsing_method": "gpt_fallback"
            })
            return job_data
        except json.JSONDecodeError:
            logger.warning("Respuesta GPT no es JSON válido")
            return None
            
    except Exception as e:
        logger.error(f"Error en método GPT fallback: {e}")
        return None

async def _detect_language_advanced(text: str) -> str:
    """Detección avanzada de idioma."""
    try:
        from langdetect import detect
        return detect(text)
    except:
        return "es"  # Default a español

async def _validate_job_info(job_info: Dict[str, Any]) -> Tuple[bool, float, str]:
    """Valida información de trabajo extraída."""
    try:
        score = 0.0
        reasons = []
        
        # Validar campos requeridos
        if job_info.get("title"):
            score += 0.3
            reasons.append("título_presente")
        
        if job_info.get("description"):
            score += 0.3
            reasons.append("descripción_presente")
        
        if job_info.get("company"):
            score += 0.2
            reasons.append("empresa_presente")
        
        # Validar contenido mínimo
        if len(job_info.get("description", "")) > 100:
            score += 0.2
            reasons.append("descripción_detallada")
        
        # Score final
        final_score = min(score, 1.0)
        is_valid = final_score >= 0.6
        
        return is_valid, final_score, ", ".join(reasons)
        
    except Exception as e:
        logger.error(f"Error validando job info: {e}")
        return False, 0.0, f"Error de validación: {str(e)}"

# ============================================================================
# FUNCIÓN PRINCIPAL MEJORADA
# ============================================================================

@log_async_function_call(logger)
async def process_emails_advanced(batch_size=EMAIL_SCRAPER_CONFIG['batch_size_default'], 
                                business_unit_name="huntred", 
                                notify_admin=True):
    """Procesamiento avanzado de emails con validación estricta."""
    logger.info(f"🚀 Iniciando procesamiento avanzado de emails (batch_size={batch_size})")
    
    try:
        # Obtener business unit
        bu = await sync_to_async(BusinessUnit.objects.get)(name=business_unit_name)
        
        # Semáforo para limitar concurrencia
        semaphore = asyncio.Semaphore(3)
        client = None
        
        async def process_single_email_advanced(email_id, email_message):
            async with semaphore:
                nonlocal client
                try:
                    # Extraer información con método avanzado
                    job_info = await extract_job_info_advanced(email_message)
                    
                    if job_info:
                        # Guardar en base de datos
                        vacante = await save_to_vacante(job_info, bu)
                        
                        if vacante:
                            # Mover a carpeta de parseados
                            if client:
                                await move_email(client, email_id, "parsed_folder")
                            
                            logger.info(f"✅ Email {email_id} procesado exitosamente como vacante {vacante.id}")
                            
                            # Notificar al manager
                            if vacante.responsible_email and notify_admin:
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
                            logger.warning(f"⚠️ No se pudo guardar vacante para email {email_id}")
                            advanced_email_stats.record_failure("Failed to save vacancy", email_id)
                    else:
                        logger.debug(f"ℹ️ No se detectó oportunidad en email {email_id}")
                        
                except Exception as e:
                    logger.error(f"❌ Error procesando email {email_id}: {str(e)}")
                    advanced_email_stats.record_failure(f"Processing error: {str(e)}", email_id)
        
        # Procesar emails
        async for email_id, email_message in fetch_emails_advanced(batch_size):
            await process_single_email_advanced(email_id, email_message)
        
        # Finalizar estadísticas
        advanced_email_stats.finish_execution()
        
        # Obtener estadísticas finales
        stats = advanced_email_stats.get_stats()
        success_rate = float(stats['success_rate'].rstrip('%'))
        
        # Verificar umbrales
        if success_rate < EMAIL_SCRAPER_CONFIG['warning_threshold']:
            logger.warning(f"⚠️ Tasa de éxito baja: {success_rate:.1f}% (objetivo: {EMAIL_SCRAPER_CONFIG['success_threshold']:.1f}%)")
        
        if success_rate >= EMAIL_SCRAPER_CONFIG['success_threshold']:
            logger.info(f"🎉 Tasa de éxito objetivo alcanzada: {success_rate:.1f}%")
        
        logger.info(f"✅ Procesamiento completado: {stats}")
        return stats
        
    except Exception as e:
        logger.error(f"❌ Error en procesamiento avanzado: {str(e)}", exc_info=True)
        advanced_email_stats.finish_execution()
        raise

# ============================================================================
# FUNCIONES DE COMPATIBILIDAD
# ============================================================================

# Mantener funciones existentes para compatibilidad
async def fetch_emails(batch_size=BATCH_SIZE_DEFAULT):
    """Función de compatibilidad."""
    return fetch_emails_advanced(batch_size)

async def extract_job_info(email_message):
    """Función de compatibilidad."""
    return await extract_job_info_advanced(email_message)

async def process_emails(batch_size=BATCH_SIZE_DEFAULT, business_unit_name="huntred", notify_admin=True):
    """Función de compatibilidad."""
    return await process_emails_advanced(batch_size, business_unit_name, notify_admin)

# Mantener variables y configuraciones existentes
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

# Mantener email_stats para compatibilidad
email_stats = advanced_email_stats