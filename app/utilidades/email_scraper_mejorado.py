import asyncio
import aioimaplib
import email
import logging
import re
import json
import random
from typing import List, Dict, Optional, Tuple, Set
from bs4 import BeautifulSoup
from django.utils import timezone
from asgiref.sync import sync_to_async
from app.models import Vacante, BusinessUnit, DominioScraping, Worker, USER_AGENTS
from urllib.parse import urlparse, urljoin
import aiohttp
import environ
from datetime import datetime

# Configuración de entorno
env = environ.Env()
environ.Env.read_env()

# Configuración de logging
log_file = f"/home/pablo/logs/email_scraper_{datetime.now().strftime('%Y%m%d')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Constantes
IMAP_SERVER = env("IMAP_SERVER", default="mail.huntred.com")
EMAIL_ACCOUNT = env("EMAIL_ACCOUNT", default="pablo@huntred.com")
EMAIL_PASSWORD = env("EMAIL_PASSWORD", default="Natalia&Patricio1113!")
CONNECTION_TIMEOUT = 60
BATCH_SIZE_DEFAULT = 10
MAX_RETRIES = 3
RETRY_DELAY = 5

# Carpetas IMAP
FOLDER_CONFIG = {
    "inbox": "INBOX",
    "jobs_folder": "INBOX.Jobs",
    "parsed_folder": "INBOX.Parsed",
    "error_folder": "INBOX.Error",
    "linkedin_folder": "INBOX.LinkedIn",
}

# Palabras clave para identificar alertas de trabajo
JOB_KEYWORDS = [
    "job", "vacante", "opportunity", "empleo", "position", 
    "director", "analista", "gerente", "asesor", "trabajo",
    "career", "linkedin"
]

# Textos a excluir
EXCLUDED_TEXTS = ["unsubscribe", "manage", "help", "profile", "feed", "preferences"]



# Cache para dominios y BusinessUnits
dominio_cache = {}
business_unit_cache = {}
already_processed_urls = set()


class EmailScraper:
    """Clase principal para el scraping de correos electrónicos con alertas de empleo"""
    
    def __init__(self, email_account: str = EMAIL_ACCOUNT, password: str = EMAIL_PASSWORD, imap_server: str = IMAP_SERVER):
        self.email_account = email_account
        self.password = password
        self.imap_server = imap_server
        self.mail = None
        self.valid_domains = []
        self.valid_senders = []
        self.connection_timeout = CONNECTION_TIMEOUT
        self.stats = {
            "correos_procesados": 0,
            "correos_exitosos": 0,
            "correos_error": 0,
            "vacantes_extraidas": 0,
            "vacantes_guardadas": 0,
            "vacantes_linkedin": 0,
            "vacantes_santander": 0,
            "vacantes_honeywell": 0,
            "vacantes_otros": 0,
        }
    
    async def initialize(self):
        """Inicializa el scraper cargando dominios y senders válidos"""
        self.valid_domains = await self._get_email_scraping_domains()
        self.valid_senders = await self._get_valid_senders()
        logger.info(f"Dominios válidos: {self.valid_domains}")
        logger.info(f"Remitentes válidos: {len(self.valid_senders)} configurados")
        return await self.connect()
    
    async def _get_email_scraping_domains(self) -> List[Dict]:
        """Obtiene los dominios que tienen habilitado el email scraping"""
        dominios = await sync_to_async(list)(DominioScraping.objects.filter(
            activo=True, 
            email_scraping_enabled=True
        ).values('id', 'empresa', 'dominio', 'base_url', 'valid_senders'))
        
        # Guardar en caché para acceso rápido
        for dominio in dominios:
            dominio_cache[dominio['dominio']] = dominio
        
        return dominios
    
    async def _get_valid_senders(self) -> List[str]:
        """Obtiene la lista de remitentes válidos de los dominios configurados"""
        valid_senders = []
        for dominio in self.valid_domains:
            if dominio.get('valid_senders'):
                if isinstance(dominio['valid_senders'], list):
                    valid_senders.extend(dominio['valid_senders'])
                elif isinstance(dominio['valid_senders'], str):
                    try:
                        senders = json.loads(dominio['valid_senders'])
                        if isinstance(senders, list):
                            valid_senders.extend(senders)
                    except json.JSONDecodeError:
                        valid_senders.append(dominio['valid_senders'])
        
        # Añadir dominios explícitamente
        valid_senders.extend(['linkedin', 'santander', 'honeywell'])
        return list(set(valid_senders))  # Eliminar duplicados
    
    async def connect(self) -> Optional[aioimaplib.IMAP4_SSL]:
        """Establece conexión con el servidor IMAP"""
        for attempt in range(MAX_RETRIES):
            try:
                if self.mail:
                    try:
                        await self.mail.logout()
                    except Exception:
                        pass
                
                self.mail = aioimaplib.IMAP4_SSL(self.imap_server, timeout=self.connection_timeout)
                await asyncio.wait_for(self.mail.wait_hello_from_server(), timeout=self.connection_timeout)
                await asyncio.wait_for(self.mail.login(self.email_account, self.password), timeout=self.connection_timeout)
                await self.mail.select(FOLDER_CONFIG["jobs_folder"])
                logger.info(f"✅ Conectado a {self.imap_server} con {self.email_account}")
                return self.mail
            except asyncio.TimeoutError:
                logger.error(f"⏱️ Timeout en intento {attempt + 1}/{MAX_RETRIES}")
            except Exception as e:
                logger.error(f"❌ Error en intento {attempt + 1}/{MAX_RETRIES}: {e}")
            
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(RETRY_DELAY)
        
        logger.error(f"❌ No se pudo conectar tras {MAX_RETRIES} intentos")
        return None
    
    async def ensure_connection(self) -> bool:
        """Asegura que haya una conexión activa al servidor IMAP"""
        try:
            if not self.mail:
                return await self.connect() is not None
            
            await asyncio.wait_for(self.mail.noop(), timeout=self.connection_timeout)
            return True
        except Exception as e:
            logger.warning(f"Conexión perdida: {e}")
            return await self.connect() is not None
    
    async def fetch_email(self, email_id: str) -> Optional[email.message.Message]:
        """Obtiene un correo de forma asincrónica con reintentos"""
        for attempt in range(MAX_RETRIES):
            try:
                if not await self.ensure_connection():
                    return None
                
                # Obtener el correo
                resp, data = await asyncio.wait_for(
                    self.mail.fetch(email_id, "(RFC822)"),
                    timeout=self.connection_timeout
                )
                
                # Validar respuesta
                if resp != "OK" or not data or len(data) < 2:
                    logger.error(f"Fallo al obtener correo {email_id}: {resp} {data}")
                    if attempt < MAX_RETRIES - 1:
                        await asyncio.sleep(RETRY_DELAY)
                        continue
                    return None
                
                # Verificar si el cuerpo del correo es válido
                if isinstance(data[1], (bytes, bytearray)):
                    message = email.message_from_bytes(data[1])
                    logger.debug(f"Correo {email_id} obtenido correctamente")
                    return message
                
                logger.error(f"No se encontró cuerpo válido para {email_id}: {data}")
            except Exception as e:
                logger.error(f"Error al obtener correo {email_id} en intento {attempt + 1}: {e}")
            
            # Esperar antes del siguiente intento
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(RETRY_DELAY)
        
        return None  # Si todos los intentos fallan
        
    async def process_job_alert_email(self, email_id: str) -> List[Dict]:
        """Procesa un correo electrónico para extraer vacantes"""
        message = await self.fetch_email(email_id)
        if not message:
            logger.info(f"No se obtuvo correo para ID {email_id}")
            await self.move_email(email_id, FOLDER_CONFIG["error_folder"])
            return []
        
        sender = message.get("From", "").lower()
        subject = message.get("Subject", "").lower()
        
        # Identificar origen del correo
        is_linkedin = "linkedin" in sender or "linkedin" in subject
        is_santander = "santander" in sender or "santander" in subject
        is_honeywell = "honeywell" in sender or "honeywell" in subject
        
        # Determinar si es un correo válido para procesar
        is_valid_sender = any(valid_sender.lower() in sender for valid_sender in self.valid_senders)
        is_job_alert = any(keyword in subject for keyword in JOB_KEYWORDS)
        
        logger.info(f"Análisis de correo {email_id}:")
        logger.info(f"- Remitente: {sender}")
        logger.info(f"- Asunto: {subject}")
        logger.info(f"- LinkedIn: {is_linkedin}, Santander: {is_santander}, Honeywell: {is_honeywell}")
        logger.info(f"- Remitente válido: {is_valid_sender}, Alerta de trabajo: {is_job_alert}")
        
        # Si es LinkedIn, siempre procesarlo
        if is_linkedin:
            logger.info(f"✅ Procesando correo de LinkedIn: {subject}")
        # Para otros, verificar si es un remitente válido o tiene keywords de trabajo
        elif not (is_valid_sender or is_job_alert):
            logger.info(f"❌ Correo {email_id} omitido - no es alerta válida")
            await self.move_email(email_id, FOLDER_CONFIG["parsed_folder"])
            return []
        
        # Extraer cuerpo HTML del correo
        body = await self.extract_html_body(message)
        if not body:
            logger.warning(f"No se encontró contenido HTML en correo {email_id}")
            await self.move_email(email_id, FOLDER_CONFIG["error_folder"])
            return []
        
        # Extraer vacantes del HTML
        job_listings = await self.extract_vacancies_from_html(body)
        if not job_listings:
            logger.info(f"No se encontraron vacantes en correo {email_id}")
            await self.move_email(email_id, FOLDER_CONFIG["parsed_folder"])
            return []
        
        # Marcar el origen de las vacantes
        for job in job_listings:
            job["is_linkedin"] = is_linkedin
            job["is_santander"] = is_santander
            job["is_honeywell"] = is_honeywell
            
            # Usar el remitente como origen si no se identifica
            if not (is_linkedin or is_santander or is_honeywell):
                job["source"] = sender.split('@')[-1] if '@' in sender else "unknown"
        
        # Actualizar estadísticas
        self.stats["vacantes_extraidas"] += len(job_listings)
        if is_linkedin:
            self.stats["vacantes_linkedin"] += len(job_listings)
        elif is_santander:
            self.stats["vacantes_santander"] += len(job_listings)
        elif is_honeywell:
            self.stats["vacantes_honeywell"] += len(job_listings)
        else:
            self.stats["vacantes_otros"] += len(job_listings)
        
        # Enriquecer vacantes con información adicional
        enriched_jobs = []
        for job in job_listings:
            try:
                enriched_job = await self.enrich_vacancy(job)
                if enriched_job:
                    enriched_jobs.append(enriched_job)
            except Exception as e:
                logger.error(f"Error al enriquecer vacante {job.get('titulo', 'Unknown')}: {e}")
        
        logger.info(f"✅ Extraídas y enriquecidas {len(enriched_jobs)} vacantes del correo {email_id}")
        return enriched_jobs
    
    async def extract_html_body(self, message) -> Optional[str]:
        """Extrae el cuerpo HTML de un correo"""
        if message.is_multipart():
            for part in message.walk():
                if part.get_content_type() == "text/html":
                    return part.get_payload(decode=True).decode("utf-8", errors="ignore")
        else:
            return message.get_payload(decode=True).decode("utf-8", errors="ignore")
        return None
    
    async def move_email(self, email_id: str, destination_folder: str) -> bool:
        """Mueve un correo a otra carpeta"""
        try:
            if not await self.ensure_connection():
                return False
            
            await self.mail.copy(email_id, destination_folder)
            await self.mail.store(email_id, "+FLAGS", "\\Deleted")
            return True
        except Exception as e:
            logger.error(f"Error al mover correo {email_id} a {destination_folder}: {e}")
            return False
    
    async def extract_vacancies_from_html(self, html: str) -> List[Dict]:
        """Extrae vacantes del código HTML de un correo"""
        try:
            soup = BeautifulSoup(html, "html.parser")
            job_listings = []
            
            # Buscar secciones de trabajo
            job_sections = soup.find_all(['div', 'section', 'table'], class_=lambda x: x and any(term in str(x).lower() for term in ['job', 'vacancy', 'position', 'empleo', 'vacante']))
            if not job_sections:
                job_sections = [soup]  # Si no hay secciones específicas, usar todo el HTML
            
            for section in job_sections:
                # Buscar enlaces que puedan ser ofertas de trabajo
                for link in section.find_all("a", href=True):
                    href = link["href"].strip()
                    link_text = link.get_text(strip=True)
                    
                    # Ignorar enlaces de exclusión
                    if any(excluded in link_text.lower() for excluded in EXCLUDED_TEXTS):
                        continue
                    
                    # Verificar que es un enlace válido
                    if not href or href == "#" or "mailto:" in href:
                        continue
                    
                    # Normalizar URL
                    if href.startswith("https://https://"):
                        href = href.replace("https://https://", "https://")
                    
                    # Si la URL ya fue procesada, omitir
                    if href in already_processed_urls:
                        logger.debug(f"URL ya procesada: {href}")
                        continue
                    
                    # Marcar como procesada
                    already_processed_urls.add(href)
                    
                    # Verificar si es un enlace de trabajo
                    is_job_link = (
                        any(keyword in link_text.lower() for keyword in JOB_KEYWORDS) or
                        any(keyword in href.lower() for keyword in ['/job/', 'career', 'position', 'vacancy']) or
                        'linkedin.com/jobs' in href
                    )
                    
                    if is_job_link:
                        # Buscar contenedor con más información
                        job_container = link.find_parent(['div', 'section', 'tr', 'td'])
                        if not job_container:
                            job_container = link.parent
                        
                        # Extraer título del trabajo (limpiando el texto)
                        job_title = self.format_title(link_text)
                        
                        # Extraer ubicación
                        location = self.extract_location(job_container, link)
                        
                        # Extraer descripción
                        description = self.extract_description(job_container)
                        
                        # Crear registro de vacante
                        job_data = {
                            "titulo": job_title,
                            "url_original": href,
                            "ubicacion": location or "No especificada",
                            "descripcion": description or "",
                            "fecha_publicacion": timezone.now(),
                            "requisitos": "",
                            "beneficios": "",
                            "modalidad": None,
                            "skills_required": []
                        }
                        
                        # Validar campos requeridos
                        if job_data["titulo"] and job_data["url_original"]:
                            job_listings.append(job_data)
            
            # Remover duplicados por URL
            unique_jobs = []
            seen_urls = set()
            for job in job_listings:
                if job["url_original"] not in seen_urls:
                    seen_urls.add(job["url_original"])
                    unique_jobs.append(job)
            
            logger.info(f"Extraídas {len(unique_jobs)} vacantes únicas de HTML")
            return unique_jobs
            
        except Exception as e:
            logger.error(f"Error al extraer vacantes de HTML: {e}")
            return []
    
    def format_title(self, title: str) -> str:
        """Formatea el título de la vacante para mejor presentación"""
        if not title:
            return "Sin título"
        
        # Limpiar caracteres especiales
        title = re.sub(r"[^\w\s\-áéíóúÁÉÍÓÚñÑ&]", " ", title)
        # Normalizar espacios
        title = re.sub(r"\s+", " ", title).strip()
        # Limitar longitud
        return title[:200] if len(title) > 200 else title
    
    def extract_location(self, container, link) -> str:
        """Extrae la ubicación del trabajo"""
        location = ""
        
        # Buscar en elementos específicos
        location_element = container.find(['span', 'div'], class_=lambda x: x and any(term in str(x).lower() for term in ['location', 'ubicacion', 'lugar']))
        if location_element:
            location = location_element.get_text(strip=True)
        else:
            # Buscar texto entre paréntesis
            next_text = link.find_next(string=True)
            if next_text and "(" in next_text and ")" in next_text:
                location_match = re.search(r'\((.*?)\)', next_text)
                if location_match:
                    location = location_match.group(1)
        
        return location
    
    def extract_description(self, container) -> str:
        """Extrae la descripción del trabajo"""
        description = ""
        
        # Buscar en elementos específicos
        desc_element = container.find(['div', 'p'], class_=lambda x: x and any(term in str(x).lower() for term in ['description', 'descripcion', 'details', 'detalles']))
        if desc_element:
            description = desc_element.get_text(strip=True)
        else:
            # Usar todo el contenido del contenedor como descripción
            description = container.get_text(strip=True)
            # Eliminar contenido del enlace para no duplicar el título
            link_text = container.find('a').get_text(strip=True) if container.find('a') else ""
            if link_text and link_text in description:
                description = description.replace(link_text, "").strip()
        
        # Limitar longitud
        return description[:1000] if len(description) > 1000 else description 
    
    async def enrich_vacancy(self, job_data: Dict) -> Dict:
        """Enriquece la información de una vacante accediendo a su URL"""
        if not job_data.get("url_original"):
            return job_data
        
        url = job_data["url_original"]
        logger.debug(f"Enriqueciendo vacante: {job_data.get('titulo', 'Sin título')} - {url}")
        
        # Intentar con aiohttp primero (más ligero y rápido)
        try:
            headers = {
                "User-Agent": random.choice(USER_AGENTS),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3",
            }
            
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=20)) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, "html.parser")
                        
                        # Extraer descripción completa
                        description = self.extract_full_description(soup)
                        if description:
                            job_data["descripcion"] = description
                        
                        # Detectar modalidad de trabajo
                        modalidad = self.detect_modalidad(soup, description)
                        if modalidad:
                            job_data["modalidad"] = modalidad
                        
                        # Extraer requisitos
                        requisitos = self.extract_requirements(soup)
                        if requisitos:
                            job_data["requisitos"] = requisitos
                        
                        # Extraer beneficios
                        beneficios = self.extract_benefits(soup)
                        if beneficios:
                            job_data["beneficios"] = beneficios
                        
                        # Extraer skills requeridos
                        skills = self.extract_skills(soup, description)
                        if skills:
                            job_data["skills_required"] = skills
                        
                        # Obtener salario si está disponible
                        salario = self.extract_salary(soup)
                        if salario:
                            job_data["salario"] = salario
                            
                        # Limpiar memoria
                        del html
                        del soup
                        
                        return job_data
        except Exception as e:
            logger.warning(f"Error al enriquecer con aiohttp: {e}")
        
        # Si fallamos con aiohttp, devolver los datos sin enriquecer
        return job_data
    
    def extract_full_description(self, soup) -> str:
        """Extrae la descripción completa de la página de la vacante"""
        selectors = [
            "div[data-automation-id='jobPostingDescription']",
            "div.job-description",
            "section#description",
            "div.description",
            "div[class*='job-description']",
            "div[class*='description']",
            "div.details-pane__content"
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        
        # Si no encontramos descripción, usar el texto de la página
        main_content = soup.find('main')
        if main_content:
            return main_content.get_text(strip=True)
        
        return ""
    
    def detect_modalidad(self, soup, description) -> Optional[str]:
        """Detecta la modalidad de trabajo (remoto, híbrido, presencial)"""
        text = (description or "").lower()
        
        if any(term in text for term in ["remoto", "remote", "teletrabajo", "trabajo a distancia", "home office"]):
            return "remoto"
        elif any(term in text for term in ["híbrido", "hybrid", "hibrido", "flexible"]):
            return "hibrido"
        elif any(term in text for term in ["presencial", "on-site", "oficina", "in office", "en la oficina"]):
            return "presencial"
        
        return None
    
    def extract_requirements(self, soup) -> str:
        """Extrae los requisitos de la vacante"""
        selectors = [
            "div.requirements", 
            "ul.qualifications", 
            "div[class*='requirements']",
            "div[class*='qualifications']",
            "div.job-criteria"
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        
        return ""
    
    def extract_benefits(self, soup) -> str:
        """Extrae los beneficios de la vacante"""
        selectors = [
            "div.benefits", 
            "section.perks", 
            "div[class*='benefits']", 
            "div[class*='perks']",
            "div.compensation"
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        
        return ""
    
    def extract_skills(self, soup, description) -> List[str]:
        """Extrae las habilidades requeridas para la vacante"""
        skills = []
        
        # Buscar lista de skills
        skills_element = soup.find(['div', 'ul'], class_=lambda x: x and any(term in str(x).lower() for term in ['skills', 'habilidades', 'competencias']))
        if skills_element:
            skills = [skill.strip() for skill in skills_element.get_text().split(',')]
        
        # Buscar también en la descripción
        if description:
            # Palabras clave comunes en TI
            tech_keywords = ["python", "java", "javascript", "react", "angular", "node", "aws", "azure", "cloud", "sql", "nosql", "mongodb", "docker", "kubernetes", "devops", "agile", "scrum"]
            for keyword in tech_keywords:
                if re.search(r'\b' + keyword + r'\b', description.lower()):
                    skills.append(keyword)
        
        return list(set(skills))  # Eliminar duplicados
    
    def extract_salary(self, soup) -> Optional[str]:
        """Extrae información de salario si está disponible"""
        selectors = [
            "div.salary", 
            "div[class*='salary']", 
            "div.compensation",
            "span[class*='salary']"
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        
        # Buscar patrones de salario en el texto
        text = soup.get_text()
        salary_patterns = [
            r'\$[\d,.]+\s*-\s*\$[\d,.]+',
            r'[\d,.]+\s*a\s*[\d,.]+\s*euros',
            r'[\d,.]+\s*a\s*[\d,.]+\s*€',
            r'[\d,.]+\s*a\s*[\d,.]+\s*MXN',
            r'[\d,.]+K\s*-\s*[\d,.]+K'
        ]
        
        for pattern in salary_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)
        
        return None
    
    async def save_vacancy(self, job_data: Dict, business_unit: BusinessUnit = None) -> bool:
        """Guarda una vacante en la base de datos"""
        try:
            # Validar que tenemos los datos necesarios
            if not job_data or not isinstance(job_data, dict):
                logger.warning("job_data es None o no es un diccionario")
                return False
            
            # Validar campos requeridos
            if not job_data.get("titulo") or not job_data.get("url_original"):
                logger.warning(f"Faltan campos requeridos para la vacante {job_data.get('titulo', 'Unknown')}")
                return False
            
            # Determinar empresa basada en URL o fuente
            empresa_name = "Desconocido"
            if job_data.get("is_linkedin"):
                empresa_name = "LinkedIn"
            elif job_data.get("is_santander"):
                empresa_name = "Santander"
            elif job_data.get("is_honeywell"):
                empresa_name = "Honeywell"
            elif job_data.get("source"):
                empresa_name = job_data["source"].capitalize()
            
            # Crear o actualizar el Worker
            worker, created = await sync_to_async(Worker.objects.get_or_create)(
                name=empresa_name,
                defaults={
                    "company": empresa_name,
                    "job_description": job_data.get("descripcion", "")[:1000] if job_data.get("descripcion") else "",
                    "address": job_data.get("ubicacion", "")[:200] if job_data.get("ubicacion") else "",
                    "required_skills": ", ".join(job_data.get("skills_required", []))[:500],
                    "job_type": job_data.get("modalidad", "")[:50] if job_data.get("modalidad") else None
                }
            )
            
            # Truncar datos para evitar errores de longitud
            truncated_data = {
                "titulo": job_data.get("titulo", "")[:300],
                "empresa": worker,
                "ubicacion": job_data.get("ubicacion", "")[:300],
                "descripcion": job_data.get("descripcion", "")[:3000] if job_data.get("descripcion") else "",
                "modalidad": job_data.get("modalidad", "")[:20] if job_data.get("modalidad") else None,
                "requisitos": job_data.get("requisitos", "")[:1000] if job_data.get("requisitos") else "",
                "beneficios": job_data.get("beneficios", "")[:1000] if job_data.get("beneficios") else "",
                "skills_required": job_data.get("skills_required", []),
                "business_unit": business_unit,
                "fecha_publicacion": job_data.get("fecha_publicacion", timezone.now()),
                "activa": True
            }
            
            # Crear o actualizar la Vacante
            vacante, created = await sync_to_async(Vacante.objects.get_or_create)(
                url_original=job_data["url_original"],
                defaults=truncated_data
            )
            
            if not created:
                # Actualizar campos con datos nuevos solo si es necesario
                for field, value in truncated_data.items():
                    if getattr(vacante, field) != value and value:  # Solo actualizar si hay valor nuevo
                        setattr(vacante, field, value)
                await sync_to_async(vacante.save)()
            
            action = "creada" if created else "actualizada"
            logger.info(f"✅ Vacante {action}: {vacante.titulo} | Empresa: {worker.name}")
            
            # Actualizar estadísticas
            self.stats["vacantes_guardadas"] += 1
            
            return True
            
        except Exception as e:
            logger.error(f"Error al guardar vacante {job_data.get('titulo', 'Unknown')}: {e}")
            return False
    
    async def get_default_business_unit(self) -> Optional[BusinessUnit]:
        """Obtiene una unidad de negocio por defecto"""
        if not business_unit_cache.get("default"):
            try:
                # Intentar obtener huntRED® primero
                huntred = await sync_to_async(BusinessUnit.objects.filter)(name="huntRED®").first()
                if huntred:
                    business_unit_cache["default"] = huntred
                else:
                    # Si no existe, usar la primera unidad de negocio
                    first_bu = await sync_to_async(BusinessUnit.objects.first)()
                    business_unit_cache["default"] = first_bu
            except Exception as e:
                logger.error(f"Error al obtener unidad de negocio por defecto: {e}")
                return None
        
        return business_unit_cache.get("default")
    
    async def classify_emails(self, batch_size: int = BATCH_SIZE_DEFAULT) -> Tuple[List[str], List[str], List[str]]:
        """Clasifica los correos por origen (LinkedIn, otros)"""
        if not await self.ensure_connection():
            return [], [], []
        
        try:
            resp, data = await self.mail.search("ALL")
            if resp != "OK":
                logger.error(f"Fallo al buscar correos: {resp}")
                return [], [], []
            
            email_ids = data[0].decode().split()
            if not email_ids:
                logger.info("No hay correos para procesar")
                return [], [], []
            
            email_ids = email_ids[:batch_size] if len(email_ids) > batch_size else email_ids
            
            # Listas para clasificar correos
            linkedin_ids = []
            santander_ids = []
            other_ids = []
            
            for email_id in email_ids:
                try:
                    resp, data = await self.mail.fetch(email_id, "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT)])")
                    if resp == "OK" and data:
                        header_data = data[0][1].decode().lower()
                        
                        if "linkedin" in header_data:
                            linkedin_ids.append(email_id)
                        elif "santander" in header_data:
                            santander_ids.append(email_id)
                        else:
                            other_ids.append(email_id)
                except Exception as e:
                    logger.error(f"Error al clasificar correo {email_id}: {e}")
                    other_ids.append(email_id)  # Por defecto, al no poder clasificar
            
            logger.info(f"Clasificación de correos:")
            logger.info(f"- LinkedIn: {len(linkedin_ids)}")
            logger.info(f"- Santander: {len(santander_ids)}")
            logger.info(f"- Otros: {len(other_ids)}")
            
            return linkedin_ids, santander_ids, other_ids
            
        except Exception as e:
            logger.error(f"Error al clasificar correos: {e}")
            return [], [], []
    
    async def run(self, batch_size: int = BATCH_SIZE_DEFAULT) -> None:
        """Ejecuta el proceso de scraping de correos"""
        if not await self.ensure_connection():
            logger.error("No se pudo conectar al servidor IMAP, finalizando")
            return
        
        try:
            # Clasificar correos por origen
            linkedin_ids, santander_ids, other_ids = await self.classify_emails(batch_size)
            
            # Obtener unidad de negocio por defecto
            default_business_unit = await self.get_default_business_unit()
            if not default_business_unit:
                logger.error("No se encontró BusinessUnit por defecto, finalizando")
                return
            
            # Procesar primero correos de LinkedIn (mayor prioridad)
            await self.process_emails(linkedin_ids, "LinkedIn", default_business_unit)
            
            # Luego procesar correos de Santander
            await self.process_emails(santander_ids, "Santander", default_business_unit)
            
            # Finalmente procesar otros correos
            await self.process_emails(other_ids, "Otros", default_business_unit)
            
            # Mostrar estadísticas
            self.log_statistics()
            
        except Exception as e:
            logger.error(f"Error en ejecución principal: {e}", exc_info=True)
        finally:
            try:
                await self.mail.logout()
            except Exception as e:
                logger.warning(f"Error durante logout: {e}")
                self.mail = None
    
    async def process_emails(self, email_ids: List[str], source: str, default_business_unit: BusinessUnit) -> None:
        """Procesa una lista de correos de una fuente específica"""
        if not email_ids:
            logger.info(f"No hay correos de {source} para procesar")
            return
        
        logger.info(f"Procesando {len(email_ids)} correos de {source}")
        
        for idx, email_id in enumerate(email_ids):
            if not await self.ensure_connection():
                logger.error(f"Conexión perdida mientras se procesaba {source} ({idx+1}/{len(email_ids)})")
                break
            
            logger.info(f"Procesando correo de {source} {idx+1}/{len(email_ids)}")
            job_listings = await self.process_job_alert_email(email_id)
            
            if not job_listings:
                self.stats["correos_procesados"] += 1
                continue
            
            # Guardar cada vacante en la base de datos
            success_count = 0
            for job_data in job_listings:
                try:
                    # Clasificar la vacante a una unidad de negocio
                    bu_id = await assign_business_unit(
                        job_title=job_data.get("titulo", ""),
                        job_description=job_data.get("descripcion", ""),
                        location=job_data.get("ubicacion", "")
                    )
                    
                    # Obtener la unidad de negocio correspondiente
                    if bu_id:
                        bu = await sync_to_async(BusinessUnit.objects.get)(id=bu_id)
                    else:
                        bu = default_business_unit
                    
                    # Guardar la vacante
                    if await self.save_vacancy(job_data, bu):
                        success_count += 1
                        
                except Exception as e:
                    logger.error(f"Error al clasificar/guardar vacante: {e}")
            
            # Actualizar contadores
            self.stats["correos_procesados"] += 1
            
            # Mover el correo a la carpeta correspondiente
            if success_count == len(job_listings):
                await self.move_email(email_id, FOLDER_CONFIG["parsed_folder"])
                self.stats["correos_exitosos"] += 1
                logger.info(f"✅ Correo {email_id} procesado exitosamente: {success_count}/{len(job_listings)} vacantes guardadas")
            else:
                await self.move_email(email_id, FOLDER_CONFIG["error_folder"])
                self.stats["correos_error"] += 1
                logger.warning(f"⚠️ Correo {email_id} con errores: {success_count}/{len(job_listings)} vacantes guardadas")
    
    def log_statistics(self) -> None:
        """Muestra estadísticas del proceso de scraping"""
        logger.info("=" * 50)
        logger.info("ESTADÍSTICAS DE SCRAPING:")
        logger.info(f"- Correos procesados: {self.stats['correos_procesados']}")
        logger.info(f"- Correos exitosos: {self.stats['correos_exitosos']}")
        logger.info(f"- Correos con error: {self.stats['correos_error']}")
        logger.info(f"- Vacantes extraídas: {self.stats['vacantes_extraidas']}")
        logger.info(f"- Vacantes guardadas: {self.stats['vacantes_guardadas']}")
        logger.info(f"- LinkedIn: {self.stats['vacantes_linkedin']}")
        logger.info(f"- Santander: {self.stats['vacantes_santander']}")
        logger.info(f"- Honeywell: {self.stats['vacantes_honeywell']}")
        logger.info(f"- Otros: {self.stats['vacantes_otros']}")
        logger.info("=" * 50)


async def assign_business_unit(job_title: str, job_description: str = None, location: str = None) -> Optional[int]:
    """Asigna una unidad de negocio a una vacante"""
    # Texto a analizar
    job_title_lower = job_title.lower() if job_title else ""
    job_desc_lower = job_description.lower() if job_description else ""
    location_lower = location.lower() if location else ""
    
    # Calcular puntuación para cada unidad de negocio
    try:
        bu_list = await sync_to_async(list)(BusinessUnit.objects.all())
        if not bu_list:
            logger.error("No hay unidades de negocio configuradas")
            return None
        
        scores = {bu.id: 0 for bu in bu_list}
        
        # Determinar nivel de seniority
        seniority_score = 0
        for term, score in [
            ("junior", 1), ("trainee", 1), ("entry", 1), 
            ("mid", 2), ("senior", 3), ("lead", 3), 
            ("manager", 4), ("director", 5), ("vp", 5), ("chief", 5)
        ]:
            if term in job_title_lower or term in job_desc_lower:
                seniority_score = max(seniority_score, score)
        
        # Analizar por unidad de negocio
        for bu in bu_list:
            bu_score = 0
            
            # LinkedIn tiene alta prioridad para huntu y huntRED
            if "linkedin" in job_title_lower or "linkedin" in job_desc_lower:
                if bu.name == "huntu":
                    bu_score += 20
                elif bu.name == "huntRED®":
                    bu_score += 15
            
            # Asignar basado en seniority
            if seniority_score >= 4:  # Director, VP, Chief
                if bu.name == "huntRED® Executive":
                    bu_score += 30
                elif bu.name == "huntRED®":
                    bu_score += 20
            elif seniority_score == 3:  # Senior, Lead
                if bu.name == "huntRED®":
                    bu_score += 25
                elif bu.name == "huntu":
                    bu_score += 10
            elif seniority_score <= 2:  # Junior, Mid
                if bu.name == "huntu":
                    bu_score += 20
                elif bu.name == "amigro":
                    bu_score += 10
            
            # Análisis por keywords técnicos (huntu)
            tech_keywords = ["developer", "software", "engineer", "data", "it", "tech", "programador", "desarrollador", "analista"]
            for keyword in tech_keywords:
                if keyword in job_title_lower or keyword in job_desc_lower:
                    if bu.name == "huntu":
                        bu_score += 5
            
            # Análisis por keywords de management (huntRED)
            mgmt_keywords = ["manager", "director", "executive", "gerente", "jefe", "líder", "management", "business"]
            for keyword in mgmt_keywords:
                if keyword in job_title_lower or keyword in job_desc_lower:
                    if bu.name == "huntRED®":
                        bu_score += 5
                    elif bu.name == "huntRED® Executive" and seniority_score >= 4:
                        bu_score += 8
            
            # Análisis por keywords de migración (amigro)
            migration_keywords = ["migration", "visa", "abroad", "international", "migración", "temporal", "extranjero"]
            for keyword in migration_keywords:
                if keyword in job_title_lower or keyword in job_desc_lower or keyword in location_lower:
                    if bu.name == "amigro":
                        bu_score += 15
            
            scores[bu.id] = bu_score
        
        # Obtener la unidad de negocio con mayor puntuación
        max_score = max(scores.values())
        if max_score == 0:
            # Si ninguna tiene puntuación, asignar a huntRED por defecto
            default_id = await sync_to_async(lambda: BusinessUnit.objects.filter(name="huntRED®").first().id)()
            return default_id
        
        best_bu_id = max(scores, key=scores.get)
        logger.info(f"Unidad asignada: {best_bu_id} para '{job_title}' con puntuación {max_score}")
        return best_bu_id
    
    except Exception as e:
        logger.error(f"Error al asignar unidad de negocio: {e}")
        # Intentar obtener huntRED por defecto
        try:
            default_id = await sync_to_async(lambda: BusinessUnit.objects.filter(name="huntRED®").first().id)()
            return default_id
        except:
            return None


async def run_email_scraper(batch_size: int = BATCH_SIZE_DEFAULT, email: str = EMAIL_ACCOUNT, password: str = EMAIL_PASSWORD) -> None:
    """Ejecuta el proceso completo de scraping de correos"""
    scraper = EmailScraper(email_account=email, password=password)
    if await scraper.initialize():
        await scraper.run(batch_size=batch_size)
    else:
        logger.error("No se pudo inicializar el scraper")


if __name__ == "__main__":
    import os
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ai_huntred.settings")
    import django
    django.setup()
    
    import argparse
    parser = argparse.ArgumentParser(description="Scraper de correos para vacantes")
    parser.add_argument("--batch", type=int, default=BATCH_SIZE_DEFAULT, help="Tamaño del lote de correos a procesar")
    parser.add_argument("--email", type=str, default=EMAIL_ACCOUNT, help="Cuenta de correo a utilizar")
    parser.add_argument("--password", type=str, default=EMAIL_PASSWORD, help="Contraseña de la cuenta de correo")
    args = parser.parse_args()
    
    asyncio.run(run_email_scraper(batch_size=args.batch, email=args.email, password=args.password)) 