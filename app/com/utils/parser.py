# /home/pablo/app/com/utils/parser.py
from typing import Dict, List, Optional, Any
import sys
import logging
import unicodedata
import email
import asyncio
import re
from aioimaplib import aioimaplib
from tempfile import NamedTemporaryFile
from langdetect import detect
from pathlib import Path
import pdfplumber
from contextlib import ExitStack
from django.utils.timezone import now
from django.db import transaction
from django.core.mail import send_mail
from django.template.loader import render_to_string
from docx import Document
from asgiref.sync import sync_to_async
from app.com.chatbot.utils import ChatbotUtils
get_nlp_processor = ChatbotUtils.get_nlp_processor
from app.com.chatbot.nlp import NLPProcessor
from app.models import ConfiguracionBU, Person, BusinessUnit, Division, Skill, Conversation, Vacante
from app.com.chatbot.integrations.services import EmailService, MessageService
from app.com.chatbot.components.chat_state_manager import ChatStateManager
from app.com.chatbot.workflow.common.common import get_possible_transitions, process_business_unit_transition
from app.com.chatbot.workflow.business_units.huntred.huntred import process_huntred_candidate
from app.com.chatbot.workflow.business_units.huntu.huntu import process_huntu_candidate
from app.com.chatbot.workflow.business_units.amigro.amigro import process_amigro_candidate
from app.com.chatbot.workflow.business_units.sexsi.sexsi import process_sexsi_payment
from app.com.tasks import process_message
from app.com.utils.report_generator import ReportGenerator
try:
    import trafilatura
except ImportError:
    pass

# Logging setup
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


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
    def __init__(self, business_unit: BusinessUnit):
        """Inicializa el parser de CVs."""
        self.business_unit = business_unit
        self.DIVISION_SKILLS = load_division_skills()
        self.nlp = NLPProcessor(language="es", mode="candidate")
        self.email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        self.phone_pattern = r'\b\d{10}\b'
        
        # Skills específicas por unidad de negocio
        self.HUNTRED_TECH_SKILLS = {
            'python', 'django', 'fastapi', 'sql', 'nosql', 'aws', 'gcp', 'azure',
            'devops', 'ci/cd', 'kubernetes', 'docker', 'terraform', 'ansible',
            'machine_learning', 'deep_learning', 'nlp', 'computer_vision'
        }
        
        self.HUNTRED_SOFT_SKILLS = {
            'leadership', 'team_management', 'project_management', 'strategic_thinking',
            'problem_solving', 'decision_making', 'communication', 'negotiation',
            'change_management', 'stakeholder_management'
        }
        
        self.HUNTRED_TOOLS = {
            'jira', 'confluence', 'git', 'github', 'gitlab', 'bitbucket',
            'docker', 'kubernetes', 'terraform', 'ansible', 'aws', 'gcp', 'azure'
        }
        
        self.HUNTRED_CERTS = {
            'aws_certified', 'azure_certified', 'google_cloud_certified',
            'scrum_master', 'pmp', 'itil', 'cisa', 'cipt', 'cipt_plus'
        }
        
        self.HUNTU_TECH_SKILLS = {
            'python', 'javascript', 'java', 'c#', 'php', 'ruby', 'go',
            'sql', 'nosql', 'aws', 'gcp', 'azure', 'devops', 'ci/cd',
            'kubernetes', 'docker', 'terraform', 'ansible'
        }
        
        self.HUNTU_SOFT_SKILLS = {
            'teamwork', 'communication', 'problem_solving', 'time_management',
            'adaptability', 'creativity', 'critical_thinking', 'attention_to_detail'
        }
        
        self.HUNTU_TOOLS = {
            'github', 'gitlab', 'bitbucket', 'jira', 'confluence',
            'docker', 'kubernetes', 'terraform', 'ansible', 'aws', 'gcp', 'azure'
        }
        
        self.HUNTU_CERTS = {
            'oracle_certified', 'microsoft_certified', 'aws_certified',
            'azure_certified', 'google_cloud_certified', 'scrum_master', 'pmp'
        }
        
        self.SEXSI_TECH_SKILLS = {
            'communication', 'empathy', 'boundaries', 'consent', 'negotiation',
            'conflict_resolution', 'active_listening', 'emotional_intelligence'
        }
        
        self.SEXSI_SOFT_SKILLS = {
            'emotional_intelligence', 'boundary_setting', 'consent_management',
            'risk_assessment', 'conflict_resolution', 'active_listening',
            'empathy', 'communication'
        }
        
        self.SEXSI_TOOLS = {
            'contract_management', 'risk_assessment', 'compliance',
            'documentation', 'communication_platforms', 'scheduling'
        }
        
        self.SEXSI_CERTS = {
            'sexual_health_certified', 'consent_training', 'risk_management',
            'communication_skills', 'boundary_setting', 'ethical_practices'
        }

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
            
            # Generar mensaje de bienvenida específico
            welcome_message = self._generate_welcome_message(self.business_unit, experience_level)
            
            return {
                "email": entities["email"],
                "phone": entities["phone"],
                "skills": skills,
                "experience": experience,
                "education": education,
                "sentiment": analysis.get("sentiment", "neutral"),
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
        """Extrae entidades (email, phone) del texto."""
        entities = {
            "email": re.search(self.email_pattern, text).group(0) if re.search(self.email_pattern, text) else "",
            "phone": re.search(self.phone_pattern, text).group(0) if re.search(self.phone_pattern, text) else ""
        }
        return entities
    
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
    
    def _generate_welcome_message(self, business_unit: BusinessUnit, experience_level: Dict) -> str:
        """Genera un mensaje de bienvenida específico para la unidad de negocio."""
        bu_name = business_unit.name.lower()
        
        if bu_name == 'huntred':
            return f"¡Bienvenido/a a HuntRED! 💼 Basado en tu experiencia de {experience_level['years']} años, " \
                   f"pareces calificar para roles {experience_level['level']}. Por favor, responde con el código de verificación que recibirá en su email."
        elif bu_name == 'huntu':
            return f"¡Bienvenido/a a Huntu! 🏆 Con {experience_level['years']} años de experiencia, " \
                   f"pareces calificar para roles {experience_level['level']}. Por favor, responde con el código de verificación que recibirá en su email."
        elif bu_name == 'sexsi':
            return f"¡Bienvenido/a a SEXSI! 📜 Con {experience_level['years']} años de experiencia, " \
                   f"pareces calificar para roles {experience_level['level']}. Por favor, responde con el código de verificación que recibirá en su email."
        return "Bienvenido/a a Grupo huntRED. Por favor, responde con el código de verificación que recibirá en su email."

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
    """Parsea un documento CV directamente desde una ruta de archivo."""
    try:
        # Obtener la unidad de negocio
        business_unit = BusinessUnit.objects.get(name=business_unit_name)
        parser = CVParser(business_unit)
        
        # Extraer texto del documento
        text = parser.extract_text_from_file(Path(file_path))
        if not text:
            return {"status": "error", "message": f"No se pudo extraer texto del archivo {file_path}"}
        
        # Realizar el análisis de forma síncrona
        event_loop = asyncio.get_event_loop()
        parsed_data = event_loop.run_until_complete(parser.parse(text))
        
        return {
            "status": "success",
            "data": parsed_data
        }
        
    except Exception as e:
        logger.error(f"❌ Error procesando documento {file_path}: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

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
