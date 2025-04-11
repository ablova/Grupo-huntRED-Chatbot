# /home/pablo/app/utilidades/parser.py
import sys
import logging
import unicodedata
import email
import asyncio
from aioimaplib import aioimaplib
from tempfile import NamedTemporaryFile
from typing import List, Dict, Optional
from langdetect import detect
from pathlib import Path
import pdfplumber
from contextlib import ExitStack
from django.utils.timezone import now
from docx import Document
from asgiref.sync import sync_to_async

# Project imports
from app.chatbot.chatbot import nlp_processor as NLPProcessorGlobal
from app.models import ConfiguracionBU, Person, BusinessUnit, Division, Skill
from app.chatbot.integrations.services import send_email

# Logging setup
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Diccionario global para almacenar instancias de NLPProcessor por idioma
NLP_PROCESSORS = {
    'es': NLPProcessorGlobal  # Instancia global para español
}
# Global cache for division skills
DIVISION_SKILLS_CACHE = None

# IMAP folder configuration
FOLDER_CONFIG = {
    "inbox": "INBOX",
    "cv_folder": "INBOX.CV",
    "parsed_folder": "INBOX.Parsed",
    "error_folder": "INBOX.Error",
}

def detect_language(text: str) -> str:
    """Detecta el idioma del texto."""
    try:
        return detect(text)
    except Exception as e:
        logger.error(f"Error detectando idioma: {e}")
        return "es"  # Default a español

def normalize_text(text: str) -> str:
    """Normaliza el texto eliminando acentos y convirtiendo a minúsculas."""
    return ''.join(char for char in unicodedata.normalize('NFD', text) if unicodedata.category(char) != 'Mn').lower()

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
                        parsed_data = self.parser.parse(text)
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
                await send_email(
                    business_unit_name=self.business_unit.name,
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

        await send_email(
            business_unit_name=self.business_unit.name,
            subject=f"Resumen de Procesamiento de CVs - {self.business_unit.name}",
            to_email=admin_email,
            body=summary,
            from_email="noreply@huntred.com"
        )

class CVParser:
    def __init__(self, business_unit: BusinessUnit):
        """Inicializa el parser de CVs."""
        self.business_unit = business_unit
        self.DIVISION_SKILLS = load_division_skills()

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

    def extract_text_from_file(self, file_path: Path) -> Optional[str]:
        """Extrae texto de archivos PDF, DOCX o HTML."""
        try:
            if file_path.suffix.lower() == '.pdf':
                with pdfplumber.open(str(file_path)) as pdf:
                    text = ' '.join([page.extract_text() or "" for page in pdf.pages])
            elif file_path.suffix.lower() in ['.doc', '.docx']:
                doc = Document(str(file_path))
                text = "\n".join(para.text for para in doc.paragraphs)
            elif file_path.suffix.lower() == '.html':
                with open(file_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                text = trafilatura.extract(html_content) or ""
            else:
                logger.warning(f"⚠️ Formato no soportado: {file_path}")
                return None
            return text.strip() if text.strip() else None
        except Exception as e:
            logger.error(f"❌ Error extrayendo texto de {file_path}: {e}")
            return None

    def parse(self, text: str) -> Dict:
        """Procesa el texto del CV usando NLPProcessor con detección de idioma."""
        # Validación inicial
        if not text or len(text.strip()) < 10:
            logger.warning("⚠️ Texto demasiado corto para análisis")
            return {}

        # Detectar idioma
        detected_lang = detect_language(text)

        # Verificar si ya existe una instancia para el idioma detectado
        if detected_lang not in NLP_PROCESSORS:
            # Crear una nueva instancia para el idioma detectado
            NLP_PROCESSORS[detected_lang] = NLPProcessorGlobal.__class__(
                language=detected_lang, 
                mode="candidate", 
                analysis_depth="deep"
            )
        
        # Obtener la instancia correspondiente
        nlp_processor = NLP_PROCESSORS[detected_lang]

        # Procesar el texto
        try:
            analysis = nlp_processor.analyze(text)
            skills = analysis.get("skills", {"technical": [], "soft": [], "tools": [], "certifications": []})
            entities = {
                "email": "",
                "phone": "",
            }  # Simplificación: asumimos que NLPProcessor no extrae email/phone directamente
            return {
                "email": entities["email"],
                "phone": entities["phone"],
                "skills": skills,
                "experience": analysis.get("experience", []),
                "education": analysis.get("education", []),
                "sentiment": analysis.get("sentiment", "neutral"),
                "experience_level": analysis.get("experience_level", {})
            }
        except Exception as e:
            logger.error(f"❌ Error analizando texto del CV: {e}")
            return {}

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