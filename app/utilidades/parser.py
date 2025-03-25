# /home/pablo/app/utilidades/parser.py
import logging
import unicodedata
import email
import asyncio
import json
from aioimaplib import aioimaplib
from email.header import decode_header
from tempfile import NamedTemporaryFile
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from langdetect import detect
from PyPDF2 import PdfReader
from contextlib import ExitStack
from django.utils.timezone import now
from docx import Document
from asgiref.sync import sync_to_async

# Importaciones del proyecto
from app.models import ConfiguracionBU, Person, BusinessUnit
from app.chatbot.nlp import NLPProcessor
from app.chatbot.integrations.services import send_email

# Configuración de logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Instancia global de NLPProcessor
NLP_PROCESSOR = NLPProcessor(language="es", mode="candidate", analysis_depth="deep")

# Diccionario de carpetas IMAP
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

# ✅ IMAPCVProcessor (Funciona perfecto, no tocar)
class IMAPCVProcessor:
    def __init__(self, business_unit: BusinessUnit):
        self.business_unit = business_unit
        self.config = self._load_config(business_unit)
        self.parser = CVParser(business_unit)
        self.stats = {"processed": 0, "created": 0, "updated": 0, "errors": 0}
        self.FOLDER_CONFIG = FOLDER_CONFIG

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
            raise ValueError(f"No configuration found for business unit: {business_unit.name}")

    async def _connect_imap(self, config: Dict):
        """Conecta al servidor IMAP de forma asíncrona."""
        try:
            client = aioimaplib.IMAP4_SSL(config['server'], config['port'])
            await client.wait_hello_from_server()
            await client.login(config['username'], config['password'])
            if not await self._verify_folders(client):
                raise ValueError("Carpetas IMAP no configuradas correctamente")
            logger.info(f"✅ Conectado al servidor IMAP: {config['server']}")
            return client
        except Exception as e:
            logger.error(f"❌ Error conectando al servidor IMAP: {e}")
            return None

    async def _verify_folders(self, mail) -> bool:
        """Verifica la existencia de las carpetas IMAP necesarias."""
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
        """Mueve un correo a la carpeta destino."""
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
        """Procesa un correo individual y maneja errores."""
        try:
            resp, data = await mail.fetch(email_id, "(RFC822)")
            if resp != "OK":
                raise ValueError(f"Error obteniendo correo {email_id}")

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
                    subject=f"CV Parser Error: {email_id}",
                    to_email=self.business_unit.admin_email,
                    body=f"Error processing CV email {email_id}: {str(e)}",
                    from_email="noreply@huntred.com"
                )

    async def process_emails(self):
        """Procesa todos los correos en la carpeta CV."""
        mail = await self._connect_imap(self.config)
        if not mail:
            return

        try:
            resp, _ = await mail.select(self.FOLDER_CONFIG['cv_folder'])
            if resp != "OK":
                raise ValueError(f"Error seleccionando {self.FOLDER_CONFIG['cv_folder']}")

            resp, messages = await mail.search("ALL")
            if resp != "OK":
                raise ValueError("Error en búsqueda de mensajes")

            email_ids = messages[0].split()
            logger.info(f"📬 Total de correos a procesar: {len(email_ids)}")
            batch_size = 10
            for i in range(0, len(email_ids), batch_size):
                batch = email_ids[i:i + batch_size]
                logger.info(f"📤 Procesando lote de {len(batch)} correos")
                for email_id in batch:
                    await self._process_single_email(mail, email_id)
                    await asyncio.sleep(2)  # Pausa para evitar sobrecarga

            await mail.expunge()
            logger.info("🗑️ Correos eliminados después de procesar")

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
        <h2>Resumen del Procesamiento de CVs para {self.business_unit.name}:</h2>
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
        
# ✅ CVParser con integración completa de NLPProcessor
class CVParser:
    def __init__(self, business_unit: str, text_sample: Optional[str] = None):
        self.business_unit = business_unit.strip()
        self.detected_language = detect_language(text_sample) if text_sample else "es"
        # ✅ Inicializamos NLPProcessor con modo "candidate" y profundidad "deep"
        self.nlp_processor = NLPProcessor(
            language=self.detected_language,
            mode="candidate",
            analysis_depth="deep"
        )
        self.analysis_points = self.get_analysis_points()
        self.cross_analysis = self.get_cross_analysis()
        self.DIVISION_SKILLS = self._load_division_skills()

    def get_analysis_points(self) -> Dict:
        """✅ Devuelve los puntos de análisis basados en la unidad de negocio."""
        analysis_points = {
            'huntRED®': [
                'habilidades_liderazgo', 'experiencia_ejecutiva', 'logros', 'gestión_empresarial',
                'responsabilidades', 'idiomas', 'red_de_contactos', 'gestión_stakeholders'
            ],
            'huntRED® Executive': [
                'planificación_estratégica', 'experiencia_consejo', 'exposición_global', 'experiencia_ejecutiva',
                'responsabilidades', 'idiomas', 'experiencia_internacional', 'conocimiento_tecnológico'
            ],
            'huntU': [
                'educación', 'proyectos', 'habilidades_técnicas', 'potencial_crecimiento', 'logros', 'tecnología'
            ],
            'amigro': [
                'permiso_trabajo', 'idiomas', 'experiencia_internacional', 'habilidades', 'mano de obra',
                'habilidades_blandas', 'certificaciones'
            ],
            'huntRED® Tech': [
                'desarrollo_software', 'arquitectura_datos', 'inteligencia_artificial', 'ciberseguridad'
            ],
        }
        return analysis_points.get(self.business_unit, ['habilidades', 'experiencia', 'educación'])

    def get_cross_analysis(self) -> Dict:
        """✅ Devuelve los factores de análisis cruzado."""
        cross_analysis = {
            'huntRED®': ['planificación_estratégica', 'experiencia_consejo', 'potencial_liderazgo'],
            'huntRED® Executive': ['gestión_empresarial', 'logros', 'conocimiento_tecnológico'],
            'huntU': ['logros', 'gestión_empresarial', 'potencial_liderazgo'],
            'amigro': ['ubicación', 'viaja_con_familia', 'estatus_migratorio', 'certificaciones'],
            'huntRED® Tech': ['conocimiento_tecnológico', 'inteligencia_artificial', 'ciberseguridad'],
        }
        return cross_analysis.get(self.business_unit, [])

    def _load_division_skills(self) -> Dict:
        """✅ Carga habilidades específicas por división."""
        try:
            divisions = Division.objects.all()
            division_skills = {}
            for division in divisions:
                skills = Skill.objects.filter(division=division).values_list('name', flat=True)
                division_skills[division.name] = list(skills)
            return division_skills
        except Exception as e:
            logger.error(f"Error cargando habilidades de divisiones: {e}")
            return {"finance": ["budgeting"], "tech": ["programming"]}

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
        """Extrae texto de archivos PDF o DOCX."""
        try:
            if file_path.suffix.lower() == '.pdf':
                reader = PdfReader(str(file_path))
                text = ' '.join([page.extract_text() or "" for page in reader.pages])
            elif file_path.suffix.lower() in ['.doc', '.docx']:
                doc = Document(str(file_path))
                text = "\n".join(para.text for para in doc.paragraphs)
            else:
                logger.warning(f"⚠️ Formato no soportado: {file_path}")
                return None
            return text if text.strip() else None
        except Exception as e:
            logger.error(f"❌ Error extrayendo texto de {file_path}: {e}")
            return None

    def parse(self, text: str) -> Dict:
        """Analiza el texto del CV usando NLPProcessor global."""
        if not text or len(text.strip()) < 10:
            logger.warning("⚠️ Texto demasiado corto para análisis")
            return {}

        analysis = NLP_PROCESSOR.analyze(text)
        skills = analysis.get("skills", {"technical": [], "soft": [], "certifications": [], "tools": []})
        return {
            "email": analysis.get("entities", {}).get("email", ""),
            "phone": analysis.get("entities", {}).get("phone", ""),
            "skills": skills,
            "experience": analysis.get("experience", []),
            "education": analysis.get("education", []),
            "sentiment": analysis.get("sentiment", "neutral"),
            "experience_level": analysis.get("experience_level", {})
        }

    def _update_candidate(self, candidate: Person, parsed_data: Dict, file_path: Path):
        """✅ Actualiza un candidato existente."""
        candidate.cv_file = str(file_path)
        candidate.cv_analysis = parsed_data
        candidate.cv_parsed = True
        candidate.metadata["last_cv_update"] = now().isoformat()
        candidate.metadata["skills"] = parsed_data["skills"]
        candidate.metadata["experience"] = parsed_data["experience"]
        candidate.metadata["education"] = parsed_data["education"]
        candidate.metadata["sentiment"] = parsed_data["sentiment"]
        candidate.metadata["languages"] = list(set(candidate.metadata.get("languages", []) + [self.detected_language]))
        divisions = self.associate_divisions(
            parsed_data["skills"]["technical"] + parsed_data["skills"]["soft"]
        )
        candidate.metadata["divisions"] = list(set(candidate.metadata.get("divisions", []) + divisions))
        candidate.save()
        logger.info(f"Perfil actualizado: {candidate.nombre} {candidate.apellido_paterno}")

    async def _create_new_candidate(self, parsed_data: Dict, file_path: Path):
        """✅ Crea un nuevo candidato."""
        skills = parsed_data["skills"]
        divisions = self.associate_divisions(skills["technical"] + skills["soft"])
        candidate = Person.objects.create(
            nombre=parsed_data.get("nombre", "Unknown"),
            apellido_paterno=parsed_data.get("apellido_paterno", ""),
            email=parsed_data.get("email", ""),
            phone=parsed_data.get("phone", ""),
            cv_file=str(file_path),
            cv_parsed=True,
            cv_analysis=parsed_data,
            metadata={
                "last_cv_update": now().isoformat(),
                "skills": skills,
                "experience": parsed_data["experience"],
                "education": parsed_data["education"],
                "sentiment": parsed_data["sentiment"],
                "languages": [self.detected_language],
                "divisions": divisions,
                "created_at": now().isoformat(),
            }
        )
        logger.info(f"Nuevo perfil creado: {candidate.nombre} {candidate.apellido_paterno}")

    def associate_divisions(self, skills: List[str]) -> List[str]:
        """✅ Asocia divisiones basadas en habilidades."""
        associated_divisions = set()
        skills_lower = set(skill.lower() for skill in skills)
        for division, division_skills in self.DIVISION_SKILLS.items():
            if skills_lower.intersection(set(skill.lower() for skill in division_skills)):
                associated_divisions.add(division)
        return list(associated_divisions)

def send_error_alert(message):
    """✅ Envía una alerta de error."""
    try:
        asyncio.run(send_email(
            subject="Error Crítico en Procesamiento de CVs",
            body=message,
            to_email="admin@huntred.com",
            from_email="noreply@huntred.com",
        ))
    except Exception as e:
        logger.error(f"No se pudo enviar la alerta: {e}")

# Eliminamos métodos redundantes y obsoletos (extract_skills, extract_experience, etc.)
# ya que NLPProcessor los cubre completamente en el método parse.