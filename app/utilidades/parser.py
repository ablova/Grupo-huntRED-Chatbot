# /home/pablo/app/utilidades/parser.py
# ✅ Importaciones necesarias
import logging
import unicodedata
import imaplib
import email
import asyncio
import json
from email.header import decode_header
from tempfile import NamedTemporaryFile
from pathlib import Path
from datetime import datetime
from functools import lru_cache
from typing import List, Dict, Optional
from langdetect import detect
from PyPDF2 import PdfReader
from django.utils.timezone import now
from docx import Document

# ✅ Importaciones del proyecto
from app.models import ConfiguracionBU, Person, Vacante, Division, Skill, BusinessUnit
from app.utilidades.vacantes import VacanteManager
from app.chatbot.nlp import NLPProcessor

# ✅ Configuración de logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# ✅ Importación de servicios adicionales
from app.chatbot.integrations.services import send_email, send_message

# ✅ Diccionario de carpetas por acción en IMAP
FOLDER_CONFIG = {
    "inbox": "INBOX",
    "cv_folder": "INBOX.CV",
    "parsed_folder": "INBOX.Parsed",
    "error_folder": "INBOX.Error",
}

def detect_language(text: str) -> str:
    """
    Detecta el idioma del texto usando langdetect. El NLPProcessor manejará la traducción a inglés si es necesario.
    """
    try:
        detected_lang = detect(text)
        return detected_lang  # Devolvemos el idioma detectado directamente
    except Exception as e:
        logger.error(f"Error detectando idioma: {e}")
        return "es"  # Default a español si falla

def normalize_text(text: str) -> str:
    """
    Normaliza el texto eliminando acentos y convirtiendo a minúsculas.
    """
    text = unicodedata.normalize('NFD', text)
    text = ''.join(char for char in text if unicodedata.category(char) != 'Mn')
    return text.lower()

# ✅ IMAPCVProcessor (Funciona perfecto, no tocar)
class IMAPCVProcessor:
    def __init__(self, business_unit):
        self.business_unit = business_unit
        self.config = self._load_config(business_unit)
        self.parser = CVParser(business_unit)
        self.stats = {"processed": 0, "created": 0, "updated": 0}
        self.FOLDER_CONFIG = FOLDER_CONFIG

    def _verify_folders(self, mail):
        for folder_key, folder_name in self.FOLDER_CONFIG.items():
            try:
                status, folder_list = mail.list(pattern=folder_name)
                if not folder_list:
                    logger.error(f"Carpeta no encontrada: {folder_name}")
                    return False
            except Exception as e:
                logger.error(f"Error verificando carpeta {folder_name}: {e}")
                return False
        return True
    
    def _load_config(self, business_unit):
        try:
            config = ConfiguracionBU.objects.get(business_unit=business_unit)
            return {
                'server': 'mail.huntred.com',
                'port': 993,
                'username': config.smtp_username,
                'password': config.smtp_password,
                'use_tls': True,
                'folders': FOLDER_CONFIG
            }
        except ConfiguracionBU.DoesNotExist:
            raise ValueError(f"No configuration found for business unit: {business_unit}")

    def _connect_imap(self, config):
        try:
            mail = imaplib.IMAP4_SSL(config['server'], config['port'])
            mail.login(config['username'], config['password'])
            if not self._verify_folders(mail):
                raise ValueError("Carpetas IMAP no configuradas correctamente")
            return mail
        except imaplib.IMAP4.error as e:
            logger.error(f"Error IMAP: {e}")
            return None

    def _move_email(self, mail, msg_id, dest_folder):
        try:
            mail.copy(msg_id, dest_folder)
            mail.store(msg_id, '+FLAGS', '\\Deleted')
            mail.expunge()
        except Exception as e:
            logger.error(f"Error moviendo correo a {dest_folder}: {e}")

    def _update_stats(self, result):
        if result.get("status") == "created":
            self.stats["created"] += 1
        elif result.get("status") == "updated":
            self.stats["updated"] += 1
        self.stats["processed"] += 1

    def _process_single_email(self, mail, email_id):
        try:
            status, data = mail.fetch(email_id, "(RFC822)")
            if status != 'OK':
                raise ValueError(f"Error obteniendo correo {email_id}")

            message = email.message_from_bytes(data[0][1])
            attachments = self.parser.extract_attachments(message)  # Usamos self.parser

            if not attachments:
                logger.warning(f"Correo {email_id} sin adjuntos válidos.")
                self._move_email(mail, email_id, self.FOLDER_CONFIG['error_folder'])
                return

            for attachment in attachments:
                temp_path = Path(f"/tmp/{attachment['filename']}")
                temp_path.write_bytes(attachment['content'])

                try:
                    text = self.parser.extract_text_from_file(temp_path)
                    if text:
                        parsed_data = self.parser.parse(text)  # Usamos parse del parser

                        if parsed_data:
                            email_addr = parsed_data.get("email", "")
                            phone = parsed_data.get("phone", "")

                            candidate = Person.objects.filter(email=email_addr).first() or Person.objects.filter(phone=phone).first()

                            if candidate:
                                self.parser._update_candidate(candidate, parsed_data, temp_path)
                                self._update_stats({"status": "updated"})
                            else:
                                self.parser._create_new_candidate(parsed_data, temp_path)
                                self._update_stats({"status": "created"})

                except Exception as e:
                    logger.error(f"Error procesando adjunto {attachment['filename']}: {e}")
                finally:
                    temp_path.unlink()

            self._move_email(mail, email_id, self.FOLDER_CONFIG['parsed_folder'])

        except Exception as e:
            logger.error(f"Error procesando correo {email_id}: {e}")
            self._move_email(mail, email_id, self.FOLDER_CONFIG['error_folder'])

    def process_emails(self):
        mail = self._connect_imap(self.config)
        if not mail:
            return

        try:
            status, _ = mail.select(self.FOLDER_CONFIG['cv_folder'])
            if status != 'OK':
                raise ValueError(f"Error seleccionando {self.FOLDER_CONFIG['cv_folder']}")

            status, messages = mail.search(None, 'ALL')
            if status != 'OK':
                raise ValueError("Error en búsqueda de mensajes")

            email_ids = messages[0].split()
            batch_size = 10  # Definimos batch_size aquí
            for i in range(0, len(email_ids), batch_size):
                batch = email_ids[i:i + batch_size]
                for email_id in batch:
                    self._process_single_email(mail, email_id)
        finally:
            mail.close()
            mail.logout()

        self._generate_summary_and_send_report(**self.stats)

    def _generate_summary_and_send_report(self, candidates_processed, candidates_created, candidates_updated):
        admin_email = self.business_unit.configuracionbu.correo_bu
        if not admin_email:
            logger.warning("Correo del administrador no configurado. Resumen no enviado.")
            return

        summary = f"""
        <h2>Resumen del Procesamiento de CVs para {self.business_unit.name}:</h2>
        <ul>
            <li>Total de candidatos procesados: {candidates_processed}</li>
            <li>Nuevos candidatos creados: {candidates_created}</li>
            <li>Candidatos actualizados: {candidates_updated}</li>
        </ul>
        """
        logger.info(f"Resumen generado:\n{summary}")

        try:
            result = asyncio.run(send_email(
                business_unit_name=self.business_unit.name,
                subject=f"Resumen de Procesamiento de CVs - {self.business_unit.name}",
                to_email=admin_email,
                body=summary,
                from_email="noreply@huntred.com",
            ))
            if result.get("status") == "success":
                logger.info(f"Resumen enviado correctamente a {admin_email}.")
            else:
                logger.error(f"Error en el envío del correo: {result.get('message')}")
        except Exception as e:
            logger.error(f"Error enviando el resumen: {e}", exc_info=True)

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
        """✅ Extrae adjuntos de un mensaje de correo."""
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
        logger.info(f"Se encontraron {len(attachments)} adjuntos.")
        return attachments

    def extract_text_from_file(self, file_path: Path) -> Optional[str]:
        """✅ Extrae texto de un archivo PDF o DOCX."""
        try:
            if file_path.suffix.lower() == '.pdf':
                reader = PdfReader(str(file_path))
                text = ' '.join([page.extract_text() or "" for page in reader.pages])
            elif file_path.suffix.lower() in ['.doc', '.docx']:
                doc = Document(str(file_path))
                text = "\n".join(para.text for para in doc.paragraphs)
            else:
                logger.warning(f"Formato no soportado: {file_path}")
                return None
            if not text.strip():
                logger.warning(f"No se extrajo texto de: {file_path}")
                return None
            return text
        except Exception as e:
            logger.error(f"Error extrayendo texto de {file_path}: {e}")
            return None

    def parse(self, text: str) -> Dict:
        if not text or len(text.strip()) < 10:
            logger.warning("Texto demasiado corto para análisis.")
            return {"education": [], "experience": [], "skills": []}

        # Usamos el análisis completo del NLPProcessor
        analysis = self.nlp_processor.analyze(text)
        skills = analysis.get("skills", {"technical": [], "soft": [], "certifications": [], "tools": []})
        entities = analysis.get("entities", [])
        experience_level = analysis.get("experience_level", {})
        ideal_positions = analysis.get("ideal_positions", [])  # Nueva funcionalidad

        parsed_data = {
            "skills": skills,
            "experience": analysis.get("experience", self._extract_experience(text, experience_level)),
            "education": analysis.get("education", self._extract_education(text, entities)),
            "sentiment": analysis.get("sentiment", "neutral"),
            "sentiment_score": analysis.get("sentiment_score", 0.0),
            "entities": entities,
            "experience_level": experience_level,
            "ideal_positions": ideal_positions  # Añadimos posiciones ideales
        }
        logger.info(f"Análisis completado: {parsed_data}")
        return parsed_data

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

    def _create_new_candidate(self, parsed_data: Dict, file_path: Path):
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