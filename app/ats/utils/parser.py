# /home/pablo/app/com/utils/parser.py
from typing import Dict, List, Optional, Any, Tuple, Union
import sys
import logging
import unicodedata
import email
import asyncio
import re
import concurrent.futures
import io
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Union
from tempfile import NamedTemporaryFile
import unicodedata
from bs4 import BeautifulSoup
import trafilatura
from app.ats.utils.scraping_utils import PlaywrightAntiDeteccion
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
from spacy.matcher import Matcher
from spacy.tokens import Doc
import psutil
import gc

# Check for resume-parser
try:
    import resume_parser as resumeparse
    HAS_RESUME_PARSER = True
except ImportError:
    HAS_RESUME_PARSER = False
    logger.warning("resume-parser not installed. Some features may be limited.")

# External libraries
try:
    import trafilatura
    import pdfplumber
    from docx import Document
    from langdetect import detect, LangDetectException
    from langdetect.lang_detect_exception import LangDetectException as LDE
    import spacy
    from resume_parser import resumeparse
    from spacy.language import Language
    from spacy_langdetect import LanguageDetector
    from aioimaplib import aioimaplib
    from tempfile import NamedTemporaryFile
    from contextlib import ExitStack
    from django.utils.timezone import now
    from django.db import transaction
    from django.core.cache import cache
    from django.core.mail import send_mail
    from django.template.loader import render_to_string
    from asgiref.sync import sync_to_async
    from app.ats.chatbot.utils import ChatbotUtils
    get_nlp_processor = ChatbotUtils.get_nlp_processor
    from app.ats.chatbot.nlp import NLPProcessor
    from app.models import ConfiguracionBU, Person, BusinessUnit, Division, Skill, Conversation, Vacante
    from app.ats.chatbot.integrations.services import EmailService, MessageService
    from app.ats.chatbot.components.chat_state_manager import ChatStateManager
    from app.ats.chatbot.workflow.common.common import get_possible_transitions, process_business_unit_transition
    from app.ats.chatbot.workflow.business_units.huntred.huntred import process_huntred_candidate
    from app.ats.chatbot.workflow.business_units.huntu.huntu import process_huntu_candidate
    from app.ats.chatbot.workflow.business_units.amigro.amigro import process_amigro_candidate
    from app.ats.chatbot.workflow.business_units.sexsi.sexsi import process_sexsi_payment
    from app.ats.tasks import process_message
    from app.ats.utils.report_generator import ReportGenerator
except ImportError as e:
    logging.error(f"Missing required package: {e}")
    raise

# Logging setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

# Configuration
DEFAULT_LANGUAGE = 'es'
MAX_WORKERS = 4  # Number of parallel workers for processing
CACHE_TIMEOUT = 60 * 60 * 24  # 24 hours cache

# Global cache for division skills
DIVISION_SKILLS_CACHE = None

# SpaCy language models
NLP_MODELS = {}

def get_nlp(lang: str = 'es') -> Language:
    """Get or load a spaCy language model with caching."""
    if lang not in NLP_MODELS:
        try:
            if lang == 'es':
                NLP_MODELS[lang] = spacy.load('es_core_news_lg')
            else:
                NLP_MODELS[lang] = spacy.load('en_core_web_lg')
            
            # Add language detection pipeline if not present
            if 'language_detector' not in NLP_MODELS[lang].pipe_names:
                def create_lang_detector(nlp, name):
                    return LanguageDetector()
                Language.factory('language_detector', func=create_lang_detector)
                NLP_MODELS[lang].add_pipe('language_detector', last=True)
                
        except OSError:
            logger.warning(f"SpaCy model for {lang} not found, downloading...")
            try:
                import subprocess
                subprocess.run([sys.executable, "-m", "spacy", "download", 
                              f"{lang}_core_news_lg" if lang == 'es' else "en_core_web_lg"], 
                             check=True)
                return get_nlp(lang)
            except Exception as e:
                logger.error(f"Failed to download spaCy model: {e}")
                return None
    return NLP_MODELS[lang]

# IMAP folder configuration
FOLDER_CONFIG = {
    "inbox": "INBOX",
    "cv_folder": "INBOX.CV",
    "parsed_folder": "INBOX.Parsed",
    "error_folder": "INBOX.Error",
}

@lru_cache(maxsize=1024)
def detect_language(text: str, default: str = DEFAULT_LANGUAGE) -> str:
    """
    Detect the language of the given text with improved caching and fallback.
    
    Args:
        text: The text to analyze
        default: Default language to return if detection fails
        
    Returns:
        str: Language code (es, en, etc.)
    """
    if not text or not text.strip():
        return default
    
    # Check cache first
    cache_key = f'lang_detect:{hash(text[:200])}'
    cached = cache.get(cache_key)
    if cached is not None:
        return cached
    
    try:
        # Try with spaCy first for better accuracy
        nlp = get_nlp('es')  # Start with Spanish model
        if nlp:
            doc = nlp(text[:5000])  # Limit text length for performance
            if hasattr(doc, '_.language'):
                lang = doc._.language.get('language')
                if lang and lang in ['es', 'en']:  # We only care about Spanish and English
                    cache.set(cache_key, lang, CACHE_TIMEOUT)
                    return lang
        
        # Fallback to langdetect
        lang = detect(text[:1000])  # Use first 1000 chars for better accuracy
        if lang in ['es', 'en']:
            cache.set(cache_key, lang, CACHE_TIMEOUT)
            return lang
            
        return default
        
    except (LangDetectException, LDE) as e:
        logger.warning(f"Language detection error: {e}")
        return default
    except Exception as e:
        logger.error(f"Unexpected error in language detection: {e}", exc_info=True)
        return default

@lru_cache(maxsize=4096)
def normalize_text(text: str, lang: str = None) -> str:
    """
    Normalize text by removing accents and converting to lowercase.
    
    Args:
        text: Text to normalize
        lang: Optional language code for language-specific normalization
        
    Returns:
        str: Normalized text
    """
    if not text:
        return ""
        
    # Check cache
    cache_key = f'norm_text:{hash(text[:100])}:{lang}'
    cached = cache.get(cache_key)
    if cached is not None:
        return cached
    
    try:
        # Basic normalization
        normalized = ''.join(
            char for char in unicodedata.normalize('NFD', str(text))
            if unicodedata.category(char) != 'Mn'
        ).lower().strip()
        
        # Language-specific normalization
        if lang == 'es':
            # Handle Spanish-specific cases
            normalized = normalized.replace('ñ', 'n')
        
        # Cache the result
        cache.set(cache_key, normalized, CACHE_TIMEOUT)
        return normalized
        
    except Exception as e:
        logger.error(f"Error normalizing text: {e}", exc_info=True)
        return str(text).lower().strip()

def load_division_skills() -> Dict[str, List[str]]:
    """Carga las habilidades de las divisiones una vez y las almacena en caché global."""
    global DIVISION_SKILLS_CACHE
    if DIVISION_SKILLS_CACHE is None:
        try:
            divisions = Division.objects.all()
            DIVISION_SKILLS_CACHE = {
                division.name: list(Skill.objects.filter(division=division).values_list('name', flat=True))
                for division in divisions
            }
        except Exception as e:
            logger.error(f"Error cargando habilidades de divisiones: {e}")
            DIVISION_SKILLS_CACHE = {"finance": ["budgeting"], "tech": ["programming"]}
    return DIVISION_SKILLS_CACHE


class IMAPCVProcessor:
    def __init__(self, business_unit: BusinessUnit, batch_size: int = 10, sleep_time: float = 2.0):
        """Inicializa el procesador de CVs por IMAP."""
        self.business_unit = business_unit
        self.config = self._load_config(business_unit)
        self.parser = CVParser(business_unit)
        self.stats = {"processed": 0, "created": 0, "updated": 0, "errors": 0}
        self.FOLDER_CONFIG = FOLDER_CONFIG
        self.batch_size = batch_size
        self.sleep_time = sleep_time

    def _load_config(self, business_unit: BusinessUnit) -> Dict:
        """Carga la configuración IMAP desde la base de datos."""
        try:
            config = ConfiguracionBU.objects.get(business_unit=business_unit)
            return {
                'server': 'mail.huntred.com',
                'port': 993,
                'username': config.smtp_username,
                'password': config.smtp_password,
            }
        except ConfiguracionBU.DoesNotExist:
            raise ValueError(f"No se encontró configuración para la unidad de negocio: {business_unit.name}")

    async def _connect_imap(self, config: Dict) -> Optional[aioimaplib.IMAP4_SSL]:
        """Conecta al servidor IMAP de forma asíncrona."""
        try:
            client = aioimaplib.IMAP4_SSL(config['server'], config['port'])
            await client.wait_hello_from_server()
            await client.login(config['username'], config['password'])
            if not await self._verify_folders(client):
                raise ValueError("Las carpetas IMAP no están configuradas correctamente")
            logger.info(f"✅ Conectado al servidor IMAP: {config['server']}")
            return client
        except Exception as e:
            logger.error(f"❌ Error conectando al servidor IMAP: {e}")
            return None

    async def _verify_folders(self, mail) -> bool:
        """Verifica la existencia de las carpetas IMAP requeridas."""
        for folder_key, folder_name in self.FOLDER_CONFIG.items():
            try:
                resp, folder_list = await mail.list(pattern=folder_name)
                if not folder_list:
                    logger.error(f"❌ Carpeta no encontrada: {folder_name}")
                    return False
            except Exception as e:
                logger.error(f"❌ Error verificando carpeta {folder_name}: {e}")
                return False
        return True

    async def _move_email(self, mail, msg_id: str, dest_folder: str):
        """Mueve un correo a la carpeta de destino."""
        try:
            await mail.copy(msg_id, dest_folder)
            await mail.store(msg_id, '+FLAGS', '\\Deleted')
            logger.info(f"📩 Correo {msg_id} movido a {dest_folder}")
        except Exception as e:
            logger.error(f"❌ Error moviendo correo {msg_id} a {dest_folder}: {e}")

    def _update_stats(self, result: Dict):
        """Actualiza las estadísticas de procesamiento."""
        if result.get("status") == "created":
            self.stats["created"] += 1
        elif result.get("status") == "updated":
            self.stats["updated"] += 1
        self.stats["processed"] += 1

    async def _process_single_email(self, mail, email_id: str):
        """Procesa un solo correo y maneja errores."""
        try:
            resp, data = await mail.fetch(email_id, "(RFC822)")
            if resp != "OK":
                raise ValueError(f"Error al obtener correo {email_id}")

            message = email.message_from_bytes(data[0][1])
            attachments = self.parser.extract_attachments(message)

            if not attachments:
                logger.warning(f"⚠️ Correo {email_id} sin adjuntos válidos")
                await self._move_email(mail, email_id, self.FOLDER_CONFIG['error_folder'])
                self.stats["errors"] += 1
                return

            with ExitStack() as stack:
                for attachment in attachments:
                    temp_file = stack.enter_context(NamedTemporaryFile(delete=False))
                    temp_path = Path(temp_file.name)
                    temp_path.write_bytes(attachment['content'])

                    text = self.parser.extract_text_from_file(temp_path)
                    if text:
                        parsed_data = await self.parser.parse(text)
                        if parsed_data:
                            email_addr = parsed_data.get("email", "")
                            phone = parsed_data.get("phone", "")
                            candidate = await sync_to_async(Person.objects.filter)(email=email_addr).first() or \
                                        await sync_to_async(Person.objects.filter)(phone=phone).first()

                            if candidate:
                                await self.parser._update_candidate(candidate, parsed_data, temp_path)
                                self._update_stats({"status": "updated"})
                            else:
                                await self.parser._create_new_candidate(parsed_data, temp_path)
                                self._update_stats({"status": "created"})

            await self._move_email(mail, email_id, self.FOLDER_CONFIG['parsed_folder'])

        except Exception as e:
            logger.error(f"❌ Error procesando correo {email_id}: {e}")
            await self._move_email(mail, email_id, self.FOLDER_CONFIG['error_folder'])
            self.stats["errors"] += 1
            if self.business_unit.admin_email:
                email_service = EmailService(self.business_unit)
                await email_service.send_email(
                    subject=f"Error en CV Parser: {email_id}",
                    to_email=self.business_unit.admin_email,
                    body=f"Error procesando CV en correo {email_id}: {str(e)}",
                    from_email="noreply@huntred.com"
                )

    async def process_emails(self):
        """Procesa todos los correos en la carpeta de CVs."""
        mail = await self._connect_imap(self.config)
        if not mail:
            return

        try:
            resp, _ = await mail.select(self.FOLDER_CONFIG['cv_folder'])
            if resp != "OK":
                raise ValueError(f"Error seleccionando {self.FOLDER_CONFIG['cv_folder']}")

            resp, messages = await mail.search("ALL")
            if resp != "OK":
                raise ValueError("Error buscando mensajes")

            email_ids = messages[0].split()
            logger.info(f"📬 Total de correos a procesar: {len(email_ids)}")
            for i in range(0, len(email_ids), self.batch_size):
                batch = email_ids[i:i + self.batch_size]
                logger.info(f"📤 Procesando lote de {len(batch)} correos")
                await asyncio.gather(*[self._process_single_email(mail, email_id) for email_id in batch])
                await asyncio.sleep(self.sleep_time)
                logger.info(f"Procesados {len(batch)} emails")

            await mail.expunge()
            logger.info("🗑️ Correos eliminados expurgados")

        finally:
            await mail.logout()
            logger.info("🔌 Desconectado del servidor IMAP")
            await self._generate_summary_and_send_report(**self.stats)

    async def _generate_summary_and_send_report(self, processed: int, created: int, updated: int, errors: int):
        """Genera y envía un resumen del procesamiento."""
        admin_email = self.business_unit.admin_email
        if not admin_email:
            logger.warning("⚠️ Correo del administrador no configurado")
            return

        summary = f"""
        <h2>Resumen de Procesamiento de CVs para {self.business_unit.name}:</h2>
        <ul>
            <li>Total de correos procesados: {processed}</li>
            <li>Nuevos candidatos creados: {created}</li>
            <li>Candidatos actualizados: {updated}</li>
            <li>Errores encontrados: {errors}</li>
        </ul>
        """
        logger.info(f"📊 Resumen generado:\n{summary}")

        email_service = EmailService(self.business_unit)
        await email_service.send_email(
            subject=f"Resumen de Procesamiento de CVs - {self.business_unit.name}",
            to_email=admin_email,
            body=summary,
            from_email="noreply@huntred.com"
        )


class CVParser:
    """
    Enhanced CV Parser with parallel processing and language support.
    
    Features:
    - Parallel processing of multiple CVs
    - Support for multiple languages (Spanish/English)
    - Fallback mechanisms for different file formats
    - Integration with resume-parser when available
    - Caching for improved performance
    """
    
    def __init__(self, business_unit: BusinessUnit, max_workers: int = None):
        """Initialize the CV Parser with business unit context."""
        self.business_unit = business_unit
        self.max_workers = max_workers or MAX_WORKERS
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        
        # Initialize NLP components
        self.nlp = get_nlp()
        self.matcher = Matcher(self.nlp.vocab)
        self._init_skill_patterns()
        
        # Initialize resume parser if available
        self.resume_parser = None
        if HAS_RESUME_PARSER:
            try:
                self.resume_parser = resumeparse.ResumeParser()
            except Exception as e:
                logger.warning(f"Could not initialize resume parser: {e}")
        
        # Initialize legacy components
        self._init_legacy()
        self._init_business_unit_skills()
    
    def _init_skill_patterns(self):
        """Initialize skill patterns for the matcher."""
        patterns = [
            [{"LOWER": "python"}],
            [{"LOWER": "java"}],
            [{"LOWER": "javascript"}],
            [{"LOWER": "machine"}, {"LOWER": "learning"}],
            [{"LOWER": "data"}, {"LOWER": "science"}],
            [{"LOWER": "artificial"}, {"LOWER": "intelligence"}],
            [{"LOWER": "cloud"}, {"LOWER": "computing"}],
            [{"LOWER": "devops"}],
            [{"LOWER": "agile"}],
            [{"LOWER": "scrum"}],
            # Add more patterns as needed
        ]
        self.matcher.add("SKILLS", patterns)
    
    def _init_legacy(self):
        """Legacy initialization for backward compatibility."""
        self.DIVISION_SKILLS = load_division_skills()
        self.email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        self.phone_pattern = r'\b\d{10}\b'
    
    def _init_business_unit_skills(self):
        """Initialize skills specific to each business unit."""
        self.HUNTRED_TECH_SKILLS = {
            'python', 'django', 'fastapi', 'sql', 'nosql', 'aws', 'gcp', 'azure',
            'devops', 'ci/cd', 'kubernetes', 'docker', 'terraform', 'ansible',
            'machine_learning', 'deep_learning', 'nlp', 'computer_vision'
        }
        
        # Add other business unit skills here...
    
    def __del__(self):
        """Clean up resources."""
        self.executor.shutdown(wait=True)
    
    async def parse_resume(self, file_content: bytes, file_extension: str = None) -> Dict:
        """Parse a single resume asynchronously.
        
        Args:
            file_content: Binary content of the resume file
            file_extension: File extension (e.g., 'pdf', 'docx')
            
        Returns:
            Dict: Parsed resume data
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self._parse_resume_sync,
            file_content,
            file_extension
        )
    
    def _parse_resume_sync(self, file_content: bytes, file_extension: str = None) -> Dict:
        """Synchronously parse a single resume with fallback mechanisms."""
        try:
            # Try with resume_parser first if available
            if self.resume_parser and file_extension in ['pdf', 'docx', 'doc']:
                with NamedTemporaryFile(suffix=f'.{file_extension}', delete=False) as temp_file:
                    temp_file.write(file_content)
                    temp_path = temp_file.name
                
                try:
                    parsed = self.resume_parser.parse_file(temp_path)
                    if parsed and any(parsed.values()):
                        return self._process_parsed_resume(parsed)
                except Exception as e:
                    logger.warning(f"Resume parser failed: {e}")
                finally:
                    try:
                        Path(temp_path).unlink()
                    except Exception:
                        pass
            
            # Fall back to custom parsing
            text = self._extract_text(file_content, file_extension)
            if not text:
                return {"error": "No text could be extracted from the file"}
            
            # Detect language and process
            lang = detect_language(text)
            normalized_text = normalize_text(text, lang)
            
            # Basic entity extraction
            email = self._extract_email(normalized_text)
            phone = self._extract_phone(normalized_text)
            
            return {
                "email": email,
                "phone": phone,
                "language": lang,
                "text_length": len(normalized_text),
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Error parsing resume: {e}", exc_info=True)
            return {"error": str(e), "status": "error"}
    
    async def parse_resume_batch(self, files: List[Tuple[bytes, str]]) -> List[Dict]:
        """Procesa un lote de CVs de manera optimizada."""
        results = []
        chunk_size = self._calculate_optimal_chunk_size(files)
        
        for i in range(0, len(files), chunk_size):
            chunk = files[i:i + chunk_size]
            try:
                chunk_results = await self._process_chunk(chunk)
                results.extend(chunk_results)
                
                # Verificar salud del sistema
                if await self._check_system_health():
                    await asyncio.sleep(self.sleep_time)
                    
            except Exception as e:
                logger.error(f"Error procesando chunk: {e}")
                # Continuar con el siguiente chunk
                continue
                
        return results

    def _calculate_optimal_chunk_size(self, files: List[Tuple[bytes, str]]) -> int:
        """Calcula el tamaño óptimo de chunk basado en el tamaño de los archivos."""
        if not files:
            return 1
            
        total_size = sum(len(content) for content, _ in files)
        avg_size = total_size / len(files)
        
        # Ajustar chunk_size basado en el tamaño promedio
        if avg_size > 1000000:  # > 1MB
            return 1
        elif avg_size > 500000:  # > 500KB
            return 2
        elif avg_size > 100000:  # > 100KB
            return 5
        else:
            return 10

    async def _process_chunk(self, chunk: List[Tuple[bytes, str]]) -> List[Dict]:
        """Procesa un chunk de archivos de manera asíncrona."""
        tasks = []
        for content, extension in chunk:
            task = asyncio.create_task(self._process_single_file(content, extension))
            tasks.append(task)
            
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filtrar resultados exitosos
        valid_results = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Error procesando archivo: {result}")
                continue
            if result:
                valid_results.append(result)
                
        return valid_results

    async def _process_single_file(self, content: bytes, extension: str) -> Optional[Dict]:
        """Procesa un solo archivo con manejo de errores robusto."""
        try:
            # Crear archivo temporal
            with NamedTemporaryFile(suffix=extension, delete=False) as temp_file:
                temp_path = Path(temp_file.name)
                temp_path.write_bytes(content)
                
                # Extraer texto
                text = self.extract_text_from_file(temp_path)
                if not text:
                    raise ValueError("No se pudo extraer texto del archivo")
                    
                # Procesar con NLP
                doc = self.nlp(text)
                
                # Extraer entidades
                entities = self._extract_entities(text)
                validated_entities = self._validate_entities(entities)
                
                # Analizar experiencia y educación
                experience = self._process_experience(doc, self.business_unit)
                education = self._process_education(doc, self.business_unit)
                
                # Analizar nivel de experiencia
                experience_level = self._analyze_experience_level(doc)
                
                # Analizar sentimiento y tono
                sentiment_analysis = self._analyze_sentiment_and_tone(text)
                
                # Generar mensaje de bienvenida
                welcome_message = self._generate_welcome_message(
                    self.business_unit, 
                    experience_level,
                    sentiment_analysis
                )
                
                return {
                    "text": text,
                    "entities": validated_entities,
                    "experience": experience,
                    "education": education,
                    "experience_level": experience_level,
                    "sentiment_analysis": sentiment_analysis,
                    "welcome_message": welcome_message,
                    "metadata": {
                        "processed_at": datetime.now().isoformat(),
                        "file_type": extension,
                        "file_size": len(content)
                    }
                }
                
        except Exception as e:
            logger.error(f"Error procesando archivo: {e}")
            return None
            
        finally:
            # Limpiar archivo temporal
            try:
                if temp_path.exists():
                    temp_path.unlink()
            except Exception as e:
                logger.warning(f"Error eliminando archivo temporal: {e}")

    async def _check_system_health(self) -> bool:
        """Verifica la salud del sistema y ajusta parámetros si es necesario."""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            
            # Verificar uso de memoria
            if memory_info.rss > 500 * 1024 * 1024:  # > 500MB
                logger.warning("Alto uso de memoria detectado")
                gc.collect()
                return True
                
            # Verificar uso de CPU
            cpu_percent = process.cpu_percent(interval=0.1)
            if cpu_percent > 80:
                logger.warning("Alto uso de CPU detectado")
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Error verificando salud del sistema: {e}")
            return False

    async def _handle_error(self, error: Exception, context: str) -> None:
        """Maneja errores de manera centralizada."""
        error_type = type(error).__name__
        error_msg = str(error)
        
        # Registrar error
        logger.error(f"Error en {context}: {error_type} - {error_msg}")
        
        # Notificar si es crítico
        if isinstance(error, (MemoryError, OSError)):
            await self._send_error_notification(error_type, error_msg, context)
            
        # Ajustar parámetros si es necesario
        if isinstance(error, MemoryError):
            self.max_workers = max(1, self.max_workers - 1)
        elif isinstance(error, TimeoutError):
            self.sleep_time *= 1.5

    async def _send_error_notification(self, error_type: str, error_msg: str, context: str) -> None:
        """Envía notificación de error crítico."""
        try:
            subject = f"Error crítico en CV Parser: {error_type}"
            body = f"""
            Contexto: {context}
            Error: {error_msg}
            Timestamp: {datetime.now().isoformat()}
            """
            
            await sync_to_async(send_mail)(
                subject=subject,
                message=body,
                from_email="noreply@huntred.com",
                recipient_list=["admin@huntred.com"],
                fail_silently=True
            )
        except Exception as e:
            logger.error(f"Error enviando notificación: {e}")

    def _extract_text(self, file_content: bytes, file_extension: str) -> str:
        """Extract text from different file formats."""
        try:
            if file_extension == 'pdf':
                return self._extract_text_from_pdf(file_content)
            elif file_extension in ['docx', 'doc']:
                return self._extract_text_from_docx(file_content)
            elif file_extension in ['txt', 'md']:
                return file_content.decode('utf-8', errors='ignore')
            else:
                logger.warning(f"Unsupported file extension: {file_extension}")
                return ""
                
        except Exception as e:
            logger.error(f"Error extracting text: {e}")
            return ""
    
    def _extract_email(self, text: str) -> str:
        """Extract email address from text."""
        email_match = re.search(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', text)
        return email_match.group(0) if email_match else ""
    
    def _extract_phone(self, text: str) -> str:
        """Extract phone number from text."""
        # Match various phone number formats
        phone_match = re.search(
            r'(\+\d{1,3}[-.\s]?)?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}',
            text
        )
        return phone_match.group(0) if phone_match else ""
    
    def _process_parsed_resume(self, parsed: Dict) -> Dict:
        """Process and normalize the output from resume-parser."""
        try:
            # Basic normalization
            result = {
                'name': parsed.get('name', '').strip(),
                'email': parsed.get('email', '').lower().strip(),
                'phone': parsed.get('phone', '').strip(),
                'skills': [s.strip() for s in parsed.get('skills', []) if s.strip()],
                'education': [e.strip() for e in parsed.get('education', []) if e.strip()],
                'experience': parsed.get('experience', []),
                'languages': [l.strip() for l in parsed.get('languages', []) if l.strip()],
                'raw': parsed
            }
            
            # Detect language from text if not specified
            if not parsed.get('language'):
                text = ' '.join([
                    result['name'],
                    ' '.join(result['skills']),
                    ' '.join(result['education'])
                ])
                result['language'] = detect_language(text)
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing parsed resume: {e}", exc_info=True)
            return {"error": str(e), "status": "error", "raw": parsed}

    async def parse(self, text: str) -> Dict:
        """Procesa un CV y extrae información relevante."""
        try:
            # Detectar idioma
            detected_lang = detect_language(text)
            logger.info(f" Detected language: {detected_lang}")
            
            # Procesar con NLP
            analysis = await self.nlp.analyze(text)
            
            # Extraer skills específicas para la unidad de negocio
            skills = self._extract_skills(analysis, self.business_unit)
            
            # Extraer entidades (email, phone)
            entities = self._extract_entities(text)
            
            # Procesar experiencia según la unidad de negocio
            experience = self._process_experience(analysis, self.business_unit)
            
            # Procesar educación según la unidad de negocio
            education = self._process_education(analysis, self.business_unit)
            
            # Analizar nivel de experiencia
            experience_level = self._analyze_experience_level(analysis)
            
            # Analizar sentimiento y tono
            sentiment_analysis = self._analyze_sentiment_and_tone(text)
            
            # Generar mensaje de bienvenida específico
            welcome_message = self._generate_welcome_message(self.business_unit, experience_level, sentiment_analysis)
            
            return {
                "email": entities["email"],
                "phone": entities["phone"],
                "skills": skills,
                "experience": experience,
                "education": education,
                "sentiment_analysis": sentiment_analysis,
                "experience_level": experience_level,
                "welcome_message": welcome_message
            }
            
        except Exception as e:
            logger.error(f"❌ Error analizando texto del CV: {e}")
            return {}

    def extract_attachments(self, message) -> List[Dict]:
        """Extrae adjuntos de un mensaje de correo."""
        attachments = []
        for part in message.walk():
            if part.get_content_maintype() == 'multipart':
                continue
            if part.get('Content-Disposition') is None:
                continue
            filename = part.get_filename()
            if filename:
                content = part.get_payload(decode=True)
                attachments.append({'filename': filename, 'content': content})
        logger.info(f"📎 Encontrados {len(attachments)} adjuntos")
        return attachments
    
    def _extract_skills(self, analysis: Dict, business_unit: BusinessUnit) -> Dict:
        """Extrae skills específicas para la unidad de negocio."""
        skills = analysis.get("skills", {"technical": [], "soft": [], "tools": [], "certifications": []})
        
        # Filtrar skills según la unidad de negocio
        if business_unit.name.lower() == 'huntred':
            return self._filter_huntred_skills(skills)
        elif business_unit.name.lower() == 'huntu':
            return self._filter_huntu_skills(skills)
        elif business_unit.name.lower() == 'sexsi':
            return self._filter_sexsi_skills(skills)
        return skills
    
    def _filter_huntred_skills(self, skills: Dict) -> Dict:
        """Filtra skills específicas para HuntRED."""
        return {
            "technical": [s for s in skills["technical"] if s.lower() in self.HUNTRED_TECH_SKILLS],
            "soft": [s for s in skills["soft"] if s.lower() in self.HUNTRED_SOFT_SKILLS],
            "tools": [s for s in skills["tools"] if s.lower() in self.HUNTRED_TOOLS],
            "certifications": [s for s in skills["certifications"] if s.lower() in self.HUNTRED_CERTS]
        }
    
    def _filter_huntu_skills(self, skills: Dict) -> Dict:
        """Filtra skills específicas para Huntu."""
        return {
            "technical": [s for s in skills["technical"] if s.lower() in self.HUNTU_TECH_SKILLS],
            "soft": [s for s in skills["soft"] if s.lower() in self.HUNTU_SOFT_SKILLS],
            "tools": [s for s in skills["tools"] if s.lower() in self.HUNTU_TOOLS],
            "certifications": [s for s in skills["certifications"] if s.lower() in self.HUNTU_CERTS]
        }
    
    def _filter_sexsi_skills(self, skills: Dict) -> Dict:
        """Filtra skills específicas para SEXSI."""
        return {
            "technical": [s for s in skills["technical"] if s.lower() in self.SEXSI_TECH_SKILLS],
            "soft": [s for s in skills["soft"] if s.lower() in self.SEXSI_SOFT_SKILLS],
            "tools": [s for s in skills["tools"] if s.lower() in self.SEXSI_TOOLS],
            "certifications": [s for s in skills["certifications"] if s.lower() in self.SEXSI_CERTS]
        }
    
    def _extract_entities(self, text: str) -> Dict:
        """Extrae entidades usando spaCy NER y patrones personalizados."""
        doc = self.nlp(text)
        entities = {
            "name": [],
            "email": [],
            "phone": [],
            "organization": [],
            "location": [],
            "skills": [],
            "education": [],
            "experience": [],
            "certifications": [],
            "languages": []
        }

        # Extraer entidades nombradas con spaCy
        for ent in doc.ents:
            if ent.label_ == "PER":
                entities["name"].append(ent.text)
            elif ent.label_ == "ORG":
                entities["organization"].append(ent.text)
            elif ent.label_ == "LOC":
                entities["location"].append(ent.text)
            elif ent.label_ == "DATE":
                # Intentar extraer años de experiencia
                if "año" in ent.text.lower() or "year" in ent.text.lower():
                    entities["experience"].append(ent.text)

        # Extraer emails con patrón mejorado
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        entities["email"] = re.findall(email_pattern, text)

        # Extraer teléfonos con patrón internacional
        phone_pattern = r'(?:\+\d{1,3}[-.\s]?)?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}'
        entities["phone"] = re.findall(phone_pattern, text)

        # Extraer habilidades usando el matcher y patrones específicos
        matches = self.matcher(doc)
        entities["skills"] = [doc[start:end].text for _, start, end in matches]

        # Extraer certificaciones
        cert_pattern = r'(?:AWS|Azure|GCP|Oracle|Microsoft|Cisco|CompTIA|PMP|ITIL|Scrum|Agile)[^.,\n]*'
        entities["certifications"] = re.findall(cert_pattern, text, re.IGNORECASE)

        # Extraer idiomas
        lang_pattern = r'(?:Inglés|Español|Francés|Alemán|Italiano|Portugués|Chino|Japonés|Ruso)[^.,\n]*'
        entities["languages"] = re.findall(lang_pattern, text, re.IGNORECASE)

        # Extraer educación con patrón mejorado
        education_pattern = r'(?:Bachelor|Master|PhD|B\.S\.|M\.S\.|B\.A\.|M\.A\.|Licenciatura|Maestría|Doctorado|Ingeniería|Grado|Diplomatura)[^.,\n]*'
        entities["education"] = re.findall(education_pattern, text, re.IGNORECASE)

        # Extraer experiencia con patrón mejorado
        experience_pattern = r'(?:\d+\s*(?:años|years|yr|yrs)\s+de\s+experiencia|experience|experiencia)[^.,\n]*'
        entities["experience"] = re.findall(experience_pattern, text, re.IGNORECASE)

        return entities

    def _validate_entities(self, entities: Dict) -> Dict:
        """Valida y limpia las entidades extraídas."""
        validated = {}
        
        # Validar email con patrón más estricto
        validated["email"] = next(
            (email for email in entities["email"] 
             if re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email)),
            ""
        )
        
        # Validar teléfono con formato internacional
        validated["phone"] = next(
            (phone for phone in entities["phone"] 
             if re.match(r'^\+?\d{8,15}$', phone.replace(' ', '').replace('-', ''))),
            ""
        )
        
        # Validar nombre (debe ser una cadena no vacía y tener al menos dos palabras)
        names = [name for name in entities["name"] if len(name.split()) >= 2]
        validated["name"] = names[0] if names else ""
        
        # Validar organizaciones (eliminar duplicados y normalizar)
        validated["organizations"] = list(set(
            org.strip() for org in entities["organization"] 
            if org.strip() and len(org) > 2
        ))
        
        # Validar ubicaciones (eliminar duplicados y normalizar)
        validated["locations"] = list(set(
            loc.strip() for loc in entities["location"] 
            if loc.strip() and len(loc) > 2
        ))
        
        # Validar habilidades (eliminar duplicados, normalizar y filtrar por relevancia)
        validated["skills"] = list(set(
            skill.strip().lower() for skill in entities["skills"] 
            if skill.strip() and len(skill) > 2
        ))
        
        # Validar certificaciones
        validated["certifications"] = list(set(
            cert.strip() for cert in entities["certifications"]
            if cert.strip() and len(cert) > 2
        ))
        
        # Validar idiomas
        validated["languages"] = list(set(
            lang.strip() for lang in entities["languages"]
            if lang.strip() and len(lang) > 2
        ))
        
        # Validar educación
        validated["education"] = list(set(
            edu.strip() for edu in entities["education"]
            if edu.strip() and len(edu) > 2
        ))
        
        # Validar experiencia
        validated["experience"] = list(set(
            exp.strip() for exp in entities["experience"]
            if exp.strip() and len(exp) > 2
        ))
        
        return validated

    def _process_experience(self, analysis: Dict, business_unit: BusinessUnit) -> List:
        """Procesa la experiencia según la unidad de negocio."""
        experience = analysis.get("experience", [])
        
        if business_unit.name.lower() == 'huntred':
            return self._process_huntred_experience(experience)
        elif business_unit.name.lower() == 'huntu':
            return self._process_huntu_experience(experience)
        elif business_unit.name.lower() == 'sexsi':
            return self._process_sexsi_experience(experience)
        return experience
    
    def _process_huntred_experience(self, experience: List) -> List:
        """Procesa la experiencia para HuntRED."""
        processed = []
        for exp in experience:
            role = exp.get("role", "").lower()
            company = exp.get("company", "").lower()
            years = exp.get("years", 0)
            
            # Validar experiencia relevante para HuntRED
            if any(skill in role for skill in self.HUNTRED_TECH_SKILLS) or \
               any(skill in company for skill in self.HUNTRED_TECH_SKILLS):
                processed.append({
                    "role": exp["role"],
                    "company": exp["company"],
                    "years": years,
                    "level": self._get_experience_level(years)
                })
        return processed
    
    def _process_huntu_experience(self, experience: List) -> List:
        """Procesa la experiencia para Huntu."""
        processed = []
        for exp in experience:
            role = exp.get("role", "").lower()
            company = exp.get("company", "").lower()
            years = exp.get("years", 0)
            
            # Validar experiencia relevante para Huntu
            if any(skill in role for skill in self.HUNTU_TECH_SKILLS) or \
               any(skill in company for skill in self.HUNTU_TECH_SKILLS):
                processed.append({
                    "role": exp["role"],
                    "company": exp["company"],
                    "years": years,
                    "level": self._get_experience_level(years)
                })
        return processed
    
    def _process_sexsi_experience(self, experience: List) -> List:
        """Procesa la experiencia para SEXSI."""
        processed = []
        for exp in experience:
            role = exp.get("role", "").lower()
            company = exp.get("company", "").lower()
            years = exp.get("years", 0)
            
            # Validar experiencia relevante para SEXSI
            if any(skill in role for skill in self.SEXSI_TECH_SKILLS) or \
               any(skill in company for skill in self.SEXSI_TECH_SKILLS):
                processed.append({
                    "role": exp["role"],
                    "company": exp["company"],
                    "years": years,
                    "level": self._get_experience_level(years)
                })
        return processed
    
    def _get_experience_level(self, years: int) -> str:
        """Obtiene el nivel de experiencia basado en años."""
        if years >= 10:
            return "expert"
        elif years >= 5:
            return "senior"
        elif years >= 2:
            return "mid"
        else:
            return "junior"
    
    def _process_education(self, analysis: Dict, business_unit: BusinessUnit) -> List:
        """Procesa la educación según la unidad de negocio."""
        education = analysis.get("education", [])
        
        if business_unit.name.lower() == 'huntred':
            return self._process_huntred_education(education)
        elif business_unit.name.lower() == 'huntu':
            return self._process_huntu_education(education)
        elif business_unit.name.lower() == 'sexsi':
            return self._process_sexsi_education(education)
        return education
    
    def _process_huntred_education(self, education: List) -> List:
        """Procesa la educación para HuntRED."""
        processed = []
        for edu in education:
            degree = edu.get("degree", "").lower()
            institution = edu.get("institution", "").lower()
            
            # Validar educación relevante para HuntRED
            if any(word in degree for word in ["computer", "software", "engineering", "technology", "data", "analytics"]):
                processed.append({
                    "degree": edu["degree"],
                    "institution": edu["institution"],
                    "year": edu.get("year", "")
                })
        return processed
    
    def _process_huntu_education(self, education: List) -> List:
        """Procesa la educación para Huntu."""
        processed = []
        for edu in education:
            degree = edu.get("degree", "").lower()
            institution = edu.get("institution", "").lower()
            
            # Validar educación relevante para Huntu
            if any(word in degree for word in ["computer", "software", "engineering", "technology", "data", "analytics"]):
                processed.append({
                    "degree": edu["degree"],
                    "institution": edu["institution"],
                    "year": edu.get("year", "")
                })
        return processed
    
    def _process_sexsi_education(self, education: List) -> List:
        """Procesa la educación para SEXSI."""
        processed = []
        for edu in education:
            degree = edu.get("degree", "").lower()
            institution = edu.get("institution", "").lower()
            
            # Validar educación relevante para SEXSI
            if any(word in degree for word in ["communication", "psychology", "sociology", "humanities"]):
                processed.append({
                    "degree": edu["degree"],
                    "institution": edu["institution"],
                    "year": edu.get("year", "")
                })
        return processed
    
    def _analyze_experience_level(self, analysis: Dict) -> Dict:
        """Analiza el nivel de experiencia del candidato."""
        experience = analysis.get("experience", [])
        total_years = sum([exp.get("years", 0) for exp in experience])
        
        if total_years >= 10:
            return {"level": "expert", "years": total_years}
        elif total_years >= 5:
            return {"level": "senior", "years": total_years}
        elif total_years >= 2:
            return {"level": "mid", "years": total_years}
        else:
            return {"level": "junior", "years": total_years}
    
    def _analyze_sentiment_and_tone(self, text: str) -> Dict:
        """Analiza el sentimiento y tono del texto del CV."""
        try:
            doc = self.nlp(text)
            
            # Análisis de sentimiento básico
            sentiment_score = 0
            positive_words = set(['excelente', 'experto', 'experiencia', 'habilidad', 'logro', 'éxito', 'innovador'])
            negative_words = set(['básico', 'limitado', 'poco', 'mínimo', 'inicial'])
            
            for token in doc:
                if token.text.lower() in positive_words:
                    sentiment_score += 1
                elif token.text.lower() in negative_words:
                    sentiment_score -= 1
            
            # Determinar sentimiento
            if sentiment_score > 2:
                sentiment = "muy positivo"
            elif sentiment_score > 0:
                sentiment = "positivo"
            elif sentiment_score < -2:
                sentiment = "muy negativo"
            elif sentiment_score < 0:
                sentiment = "negativo"
            else:
                sentiment = "neutral"
            
            # Análisis de tono
            tone = {
                "profesional": 0,
                "técnico": 0,
                "creativo": 0,
                "formal": 0
            }
            
            # Palabras clave para cada tono
            tone_keywords = {
                "profesional": ['experiencia', 'responsabilidad', 'liderazgo', 'gestión', 'equipo'],
                "técnico": ['tecnología', 'desarrollo', 'implementación', 'optimización', 'arquitectura'],
                "creativo": ['innovación', 'diseño', 'creatividad', 'solución', 'idea'],
                "formal": ['objetivo', 'meta', 'resultado', 'proceso', 'sistema']
            }
            
            # Contar ocurrencias de palabras clave
            for tone_type, keywords in tone_keywords.items():
                for keyword in keywords:
                    tone[tone_type] += len(re.findall(r'\b' + keyword + r'\b', text.lower()))
            
            # Determinar tono dominante
            dominant_tone = max(tone.items(), key=lambda x: x[1])[0]
            
            # Análisis de confianza
            confidence_indicators = [
                'experto', 'experiencia', 'dominio', 'conocimiento', 'habilidad',
                'capacidad', 'aptitud', 'competencia', 'maestría', 'pericia'
            ]
            
            confidence_score = sum(
                1 for word in confidence_indicators 
                if word in text.lower()
            )
            
            confidence_level = "alto" if confidence_score > 5 else "medio" if confidence_score > 2 else "bajo"
            
            return {
                "sentiment": {
                    "score": sentiment_score,
                    "label": sentiment
                },
                "tone": {
                    "analysis": tone,
                    "dominant": dominant_tone
                },
                "confidence": {
                    "score": confidence_score,
                    "level": confidence_level
                }
            }
            
        except Exception as e:
            logger.error(f"Error en análisis de sentimiento: {e}")
            return {
                "sentiment": {"score": 0, "label": "neutral"},
                "tone": {"analysis": {}, "dominant": "neutral"},
                "confidence": {"score": 0, "level": "bajo"}
            }

    def _generate_welcome_message(self, business_unit: BusinessUnit, experience_level: Dict, sentiment_analysis: Dict = None) -> str:
        """Genera un mensaje de bienvenida personalizado basado en el análisis."""
        bu_name = business_unit.name.lower()
        experience_years = experience_level.get('years', 0)
        experience_label = experience_level.get('level', 'junior')
        
        # Mensajes base según la unidad de negocio
        base_messages = {
            'huntred': f"¡Bienvenido/a a HuntRED! 💼 Con {experience_years} años de experiencia, ",
            'huntu': f"¡Bienvenido/a a Huntu! 🏆 Con {experience_years} años de experiencia, ",
            'sexsi': f"¡Bienvenido/a a SEXSI! 📜 Con {experience_years} años de experiencia, "
        }
        
        # Mensajes según el nivel de experiencia
        experience_messages = {
            'expert': "tu perfil destaca por su amplia experiencia y conocimientos avanzados. ",
            'senior': "tienes un perfil sólido y bien establecido. ",
            'mid': "tienes un buen nivel de experiencia. ",
            'junior': "estás comenzando tu carrera profesional. "
        }
        
        # Mensajes según el tono detectado
        tone_messages = {
            'profesional': "Tu enfoque profesional es muy valorado. ",
            'técnico': "Tu perfil técnico es muy interesante. ",
            'creativo': "Tu enfoque creativo es muy apreciado. ",
            'formal': "Tu perfil formal es muy adecuado. "
        }
        
        # Mensajes según el nivel de confianza
        confidence_messages = {
            'alto': "Tu perfil muestra gran seguridad y dominio. ",
            'medio': "Tu perfil muestra buena confianza. ",
            'bajo': "Tu perfil muestra potencial de crecimiento. "
        }
        
        # Construir mensaje
        message = base_messages.get(bu_name, "¡Bienvenido/a a Grupo huntRED! ")
        message += experience_messages.get(experience_label, "")
        
        if sentiment_analysis:
            message += tone_messages.get(sentiment_analysis['tone']['dominant'], "")
            message += confidence_messages.get(sentiment_analysis['confidence']['level'], "")
        
        message += "Por favor, responde con el código de verificación que recibirá en su email."
        
        return message

    def extract_text_from_file(self, file_path: Path) -> Optional[str]:
        """Extrae texto de archivos PDF, DOCX, HTML o imágenes usando métodos avanzados."""
        try:
            if file_path.suffix.lower() == '.pdf':
                return self._extract_text_from_pdf(file_path)
            elif file_path.suffix.lower() in ['.doc', '.docx']:
                return self._extract_text_from_docx(file_path)
            elif file_path.suffix.lower() == '.html':
                return self._extract_text_from_html(file_path)
            elif file_path.suffix.lower() in ['.jpg', '.jpeg', '.png']:
                return self._extract_text_from_image(file_path)
            else:
                logger.warning(f"⚠️ Formato no soportado: {file_path}")
                return None
        except Exception as e:
            logger.error(f"❌ Error extrayendo texto de {file_path}: {e}")
            return None

    def _extract_text_from_pdf(self, file_path: Path) -> str:
        """Extrae texto de PDFs usando PyMuPDF para mejor precisión."""
        text = ""
        try:
            doc = fitz.open(str(file_path))
            for page in doc:
                # Extraer texto con mejor precisión
                text += page.get_text("text", sort=True)
                # Extraer tablas si existen
                tables = page.find_tables()
                if tables:
                    for table in tables:
                        text += "\n" + table.to_text()
            return text.strip()
        except Exception as e:
            logger.error(f"Error extrayendo texto de PDF: {e}")
            # Fallback a pdfplumber con mejor manejo de tablas
            try:
                with pdfplumber.open(str(file_path)) as pdf:
                    text = ""
                    for page in pdf.pages:
                        text += page.extract_text() or ""
                        # Extraer tablas
                        tables = page.extract_tables()
                        if tables:
                            for table in tables:
                                text += "\n" + "\n".join([" | ".join(row) for row in table])
                    return text.strip()
            except Exception as e2:
                logger.error(f"Error en fallback de PDF: {e2}")
                return ""

    def _extract_text_from_docx(self, file_path: Path) -> str:
        """Extrae texto de documentos DOCX."""
        doc = Document(str(file_path))
        return "\n".join(para.text for para in doc.paragraphs)

    def _extract_text_from_html(self, file_path: Path) -> str:
        """Extrae texto de archivos HTML."""
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        return trafilatura.extract(html_content) or ""

    def _extract_text_from_image(self, file_path: Path) -> str:
        """Extrae texto de imágenes usando OCR."""
        try:
            image = Image.open(str(file_path))
            return pytesseract.image_to_string(image)
        except Exception as e:
            logger.error(f"Error en OCR: {e}")
            return ""

    async def _update_candidate(self, candidate: Person, parsed_data: Dict, file_path: Path):
        """Actualiza un candidato existente de forma asíncrona."""
        candidate.cv_file = str(file_path)
        candidate.cv_analysis = parsed_data
        candidate.cv_parsed = True
        candidate.metadata.update({
            "last_cv_update": now().isoformat(),
            "skills": parsed_data["skills"],
            "experience": parsed_data["experience"],
            "education": parsed_data["education"],
            "sentiment": parsed_data["sentiment"]
        })
        await sync_to_async(candidate.save)()
        logger.info(f"✅ Perfil actualizado: {candidate.nombre} {candidate.apellido_paterno}")

    async def _create_new_candidate(self, parsed_data: Dict, file_path: Path):
        """Crea un nuevo candidato de forma asíncrona."""
        candidate = await sync_to_async(Person.objects.create)(
            nombre=parsed_data.get("nombre", "Unknown"),
            apellido_paterno=parsed_data.get("apellido_paterno", ""),
            email=parsed_data.get("email", ""),
            phone=parsed_data.get("phone", ""),
            cv_file=str(file_path),
            cv_parsed=True,
            cv_analysis=parsed_data,
            metadata={
                "last_cv_update": now().isoformat(),
                "skills": parsed_data["skills"],
                "experience": parsed_data["experience"],
                "education": parsed_data["education"],
                "sentiment": parsed_data["sentiment"]
            }
        )
        logger.info(f"✅ Nuevo perfil creado: {candidate.nombre} {candidate.apellido_paterno}")

def parse_document(file_path: str, business_unit_name: str) -> Dict:
    """
    Parse a CV document from a file path.
    
    Example usage:
    ```python
    result = parse_document("path/to/resume.pdf", "huntRED")
    print(f"Extracted email: {result.get('email')}")
    print(f"Skills: {', '.join(result.get('skills', []))}")
    ```
    
    Args:
        file_path: Path to the CV file
        business_unit_name: Name of the business unit
        
    Returns:
        Dict: Parsed CV data or error information
    """
    try:
        business_unit = BusinessUnit.objects.get(name=business_unit_name)
        parser = CVParser(business_unit)
        
        with open(file_path, 'rb') as f:
            file_content = f.read()
        
        file_extension = Path(file_path).suffix[1:].lower()
        return parser._parse_resume_sync(file_content, file_extension)
        
    except Exception as e:
        logger.error(f"Error parsing document {file_path}: {e}", exc_info=True)
        return {"error": str(e), "status": "error"}

async def parse_document_async(file_path: str, business_unit_name: str) -> Dict:
    """
    Asynchronously parse a CV document from a file path.
    
    Example usage:
    ```python
    result = await parse_document_async("path/to/resume.pdf", "huntRED")
    print(f"Extracted email: {result.get('email')}")
    print(f"Skills: {', '.join(result.get('skills', []))}")
    ```
    
    Args:
        file_path: Path to the CV file
        business_unit_name: Name of the business unit
        
    Returns:
        Dict: Parsed CV data or error information
    """
    try:
        business_unit = await sync_to_async(BusinessUnit.objects.get)(name=business_unit_name)
        parser = CVParser(business_unit)
        
        with open(file_path, 'rb') as f:
            file_content = f.read()
        
        file_extension = Path(file_path).suffix[1:].lower()
        return await parser.parse_resume(file_content, file_extension)
        
    except Exception as e:
        logger.error(f"Error parsing document {file_path}: {e}", exc_info=True)
        return {"error": str(e), "status": "error"}

def parse_job_listing(content, source_url, source_type="web"):
    """Parse job listing content from web or email sources to extract structured information."""
    try:
        soup = BeautifulSoup(content, "html.parser")
        job_info = {}
        
        if source_type == "web":
            title_elem = soup.find(["h1", "h2", "h3"], class_=["title", "job-title", "header"]) or soup.find(["h1", "h2", "h3"])
            company_elem = soup.find(["span", "div"], class_=["company", "employer", "organization"])
            desc_elem = soup.find(["div", "section"], class_=["description", "summary", "details", "content"])
            url_elem = soup.find("a", href=True, text=re.compile(r"apply|postular|solicitar", re.I))
            
            job_info["title"] = title_elem.get_text(strip=True) if title_elem else "Untitled Job"
            job_info["company"] = company_elem.get_text(strip=True) if company_elem else "Unknown Company"
            job_info["description"] = desc_elem.get_text(strip=True)[:1000] if desc_elem else "No description available"
            job_info["url"] = urljoin(source_url, url_elem["href"]) if url_elem else source_url
            job_info["source"] = urlparse(source_url).netloc
        
        elif source_type == "email":
            job_info["title"] = soup.title.get_text(strip=True) if soup.title else "Untitled Email Job"
            company_elem = soup.find(text=re.compile(r"from|de|empresa|company", re.I))
            job_info["company"] = company_elem.strip() if company_elem else "Unknown Sender"
            job_info["description"] = soup.get_text(strip=True)[:1000]
            job_info["url"] = extract_url(content) or source_url
            job_info["source"] = "Email Scraping"
        
        logger.info(f"Parsed job listing: {job_info['title']} from {job_info['company']}")
        return job_info if any(keyword in job_info["title"].lower() or keyword in job_info["description"].lower() for keyword in JOB_KEYWORDS) else None
    except Exception as e:
        logger.error(f"Error parsing job listing from {source_type}: {str(e)}", exc_info=True)
        return None

def extract_url(text):
    """Extract the first URL from text content."""
    try:
        url_pattern = re.compile(r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[-\w./?%&=]*")
        urls = url_pattern.findall(text)
        return urls[0] if urls else ""
    except Exception as e:
        logger.error(f"Error extracting URL: {str(e)}")
        return ""

async def save_job_to_vacante(job_info, bu):
    """Save parsed job information to Vacante model with async operation."""
    try:
        vacante = Vacante(
            nombre=job_info["title"],
            empresa=job_info["company"],
            descripcion=job_info["description"],
            url=job_info["url"],
            business_unit=bu,
            fuente=f"{job_info['source']} Parsing",
            fecha_publicacion=timezone.now(),
        )
        await sync_to_async(vacante.save)()
        logger.info(f"Saved parsed vacante: {job_info['title']}")
        return vacante
    except Exception as e:
        logger.error(f"Error saving parsed vacante: {str(e)}", exc_info=True)
        return None

class Parser:
    """Clase base para parsing de contenido HTML/JSON."""
    
    def __init__(self):
        self._cache = {}
        self._cache_ttl = 3600  # 1 hora
        
    def _get_cached_result(self, key: str) -> Optional[Dict]:
        """Obtiene resultado del caché si existe y es válido."""
        if key in self._cache:
            cached = self._cache[key]
            if time.time() - cached['timestamp'] < self._cache_ttl:
                return cached['data']
        return None
        
    def _set_cached_result(self, key: str, data: Dict):
        """Guarda resultado en caché."""
        self._cache[key] = {
            'data': data,
            'timestamp': time.time()
        }
        
    def parse_job_listing(self, content: str, url: str, source_type: str = "web") -> Dict:
        """
        Parsea una oferta de trabajo y extrae información relevante.
        
        Args:
            content: Contenido HTML/JSON de la oferta
            url: URL de la oferta
            source_type: Tipo de fuente (web, api, etc)
            
        Returns:
            Dict con la información extraída
        """
        cache_key = f"parse_{url}"
        cached = self._get_cached_result(cache_key)
        if cached:
            return cached
            
        try:
            if source_type == "json":
                data = json.loads(content)
                result = self._parse_json_job(data)
            else:
                result = self._parse_html_job(content)
                
            # Enriquecer con información adicional
            result.update({
                'url': url,
                'source_type': source_type,
                'parsed_at': datetime.now().isoformat()
            })
            
            # Guardar en caché
            self._set_cached_result(cache_key, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error parsing job listing: {e}")
            return {
                'url': url,
                'error': str(e)
            }
            
    def _parse_html_job(self, content: str) -> Dict:
        """Parsea una oferta de trabajo en formato HTML."""
        # Usar trafilatura para extraer el contenido principal
        main_content = trafilatura.extract(content) or content
        soup = BeautifulSoup(main_content, "html.parser")
        
        # Extraer información básica
        title = self._extract_title(soup)
        description = self._extract_description(soup)
        location = self._extract_location(soup)
        company = self._extract_company(soup)
        skills = self._extract_skills(soup)
        salary = self._extract_salary(soup)
        posted_date = self._extract_posted_date(soup)
        
        return {
            'title': title,
            'description': description,
            'location': location,
            'company': company,
            'skills': skills,
            'salary': salary,
            'posted_date': posted_date
        }
        
    def _parse_json_job(self, data: Dict) -> Dict:
        """Parsea una oferta de trabajo en formato JSON."""
        return {
            'title': data.get('title', ''),
            'description': data.get('description', ''),
            'location': data.get('location', {}).get('name', ''),
            'company': data.get('company', {}).get('name', ''),
            'skills': data.get('skills', []),
            'salary': data.get('salary', {}),
            'posted_date': data.get('posted_date', '')
        }
        
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extrae el título de la oferta."""
        title_elem = (
            soup.find('h1') or 
            soup.find('h2') or 
            soup.find(class_=re.compile(r'title|heading', re.I))
        )
        return title_elem.get_text(strip=True) if title_elem else ''
        
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extrae la descripción de la oferta."""
        desc_elem = (
            soup.find(class_=re.compile(r'description|content|details', re.I)) or
            soup.find('div', {'role': 'main'}) or
            soup.find('main')
        )
        return desc_elem.get_text(strip=True) if desc_elem else ''
        
    def _extract_location(self, soup: BeautifulSoup) -> str:
        """Extrae la ubicación de la oferta."""
        loc_elem = (
            soup.find(class_=re.compile(r'location|city|place', re.I)) or
            soup.find('span', {'itemprop': 'jobLocation'})
        )
        return loc_elem.get_text(strip=True) if loc_elem else ''
        
    def _extract_company(self, soup: BeautifulSoup) -> str:
        """Extrae el nombre de la empresa."""
        comp_elem = (
            soup.find(class_=re.compile(r'company|employer', re.I)) or
            soup.find('span', {'itemprop': 'hiringOrganization'})
        )
        return comp_elem.get_text(strip=True) if comp_elem else ''
        
    def _extract_skills(self, soup: BeautifulSoup) -> List[str]:
        """Extrae las habilidades requeridas."""
        skills = []
        
        # Buscar en secciones comunes de habilidades
        skill_sections = soup.find_all(class_=re.compile(r'skills|requirements|qualifications', re.I))
        for section in skill_sections:
            items = section.find_all(['li', 'p'])
            skills.extend([item.get_text(strip=True) for item in items])
            
        # Buscar en la descripción
        if not skills:
            desc = self._extract_description(soup)
            skills = self._extract_skills_from_text(desc)
            
        return list(set(skills))  # Eliminar duplicados
        
    def _extract_skills_from_text(self, text: str) -> List[str]:
        """Extrae habilidades de un texto usando expresiones regulares."""
        skills = []
        
        # Patrones comunes de habilidades
        patterns = [
            r'(?i)experience with\s+([^.,]+)',
            r'(?i)knowledge of\s+([^.,]+)',
            r'(?i)proficient in\s+([^.,]+)',
            r'(?i)expertise in\s+([^.,]+)',
            r'(?i)strong\s+([^.,]+)\s+skills',
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text)
            skills.extend([m.group(1).strip() for m in matches])
            
        return list(set(skills))
        
    def _extract_salary(self, soup: BeautifulSoup) -> Dict:
        """Extrae información del salario."""
        salary_elem = (
            soup.find(class_=re.compile(r'salary|compensation', re.I)) or
            soup.find('span', {'itemprop': 'baseSalary'})
        )
        
        if not salary_elem:
            return {}
            
        salary_text = salary_elem.get_text(strip=True)
        
        # Extraer rango de salario
        range_match = re.search(r'(\d+(?:,\d+)*)\s*-\s*(\d+(?:,\d+)*)', salary_text)
        if range_match:
            return {
                'min': int(range_match.group(1).replace(',', '')),
                'max': int(range_match.group(2).replace(',', '')),
                'currency': 'EUR' if '€' in salary_text else 'USD'
            }
            
        # Extraer salario fijo
        fixed_match = re.search(r'(\d+(?:,\d+)*)', salary_text)
        if fixed_match:
            return {
                'amount': int(fixed_match.group(1).replace(',', '')),
                'currency': 'EUR' if '€' in salary_text else 'USD'
            }
            
        return {}
        
    def _extract_posted_date(self, soup: BeautifulSoup) -> str:
        """Extrae la fecha de publicación."""
        date_elem = (
            soup.find(class_=re.compile(r'date|posted|published', re.I)) or
            soup.find('time') or
            soup.find('span', {'itemprop': 'datePosted'})
        )
        return date_elem.get_text(strip=True) if date_elem else ''
