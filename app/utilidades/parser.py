# Ubicación /home/pablo/app/utilidades/parser.py

import unicodedata
import imaplib
import email
import asyncio
import email
from tempfile import NamedTemporaryFile
from email import message_from_bytes
from email.header import decode_header
from app.models import ConfiguracionBU, Person, Vacante
from app.utilidades.vacantes import VacanteManager
from functools import lru_cache
from pathlib import Path
import spacy
from app.models import Person, ConfiguracionBU, Division, Skill, BusinessUnit
from typing import List, Dict, Tuple, Optional
from django.utils.timezone import now
from datetime import datetime

import logging
from PyPDF2 import PdfReader
import docx
from langdetect import detect

# ✅ Importación segura del módulo NLP
try:
    import app.chatbot.nlp as nlp_module  # Importación del módulo
    sn = nlp_module.sn if hasattr(nlp_module, "sn") else None
except ImportError as e:
    logging.error(f"Error importando NLP: {e}", exc_info=True)
    sn = None

# ✅ Si `sn` no está disponible, lanzar advertencia
if sn is None:
    logging.warning("⚠ Warning: SkillExtractor (`sn`) no se pudo importar correctamente desde nlp.py")

# ✅ Importación de servicios adicionales
from app.chatbot.integrations.services import send_message, send_email

logger = logging.getLogger(__name__)

def detect_language(text):
    try:
        return detect(text)
    except Exception as e:
        logger.error(f"Error detectando idioma: {e}")
        return "unknown"

def load_spacy_model_by_language(language):
    models = {
        "es": "es_core_news_sm",
        "en": "en_core_web_sm",
    }
    return spacy.load(models.get(language, "en_core_web_sm"))

# Diccionario de folders por acción
FOLDER_CONFIG = {
    "inbox": "INBOX",
    "cv_folder": "INBOX.CV",  # Reemplaza por la ruta correcta
    "parsed_folder": "INBOX.Parsed",
    "error_folder": "INBOX.Error",
}

@lru_cache(maxsize=1)
def load_spacy_model():
    return spacy.load("es_core_news_sm")

def normalize_text(text):
    """
    Normaliza el texto eliminando acentos y convirtiendo a minúsculas.
    """
    text = unicodedata.normalize('NFD', text)
    text = ''.join(char for char in text if unicodedata.category(char) != 'Mn')
    return text.lower()

# # # # EL IMAPCVPROCESSOR FUNCIONA PERFECTO NO TOCAR 
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
        """
        Carga la configuración de IMAP desde ConfiguracionBU.
        """
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
            attachments = parser.extract_attachments(message)

            if not attachments:
                logger.warning(f"Correo {email_id} sin adjuntos válidos.")
                self._move_email(mail, email_id, self.FOLDER_CONFIG['error_folder'])
                return

            for attachment in attachments:
                temp_path = Path(f"/tmp/{attachment['filename']}")
                temp_path.write_bytes(attachment['content'])

                try:
                    text = parser.extract_text_from_file(temp_path)
                    if text:
                        parsed_data = CVParser.parse(text)

                        if parsed_data:
                            email = parsed_data.get("email")
                            phone = parsed_data.get("phone")

                            candidate = Person.objects.filter(email=email).first() or Person.objects.filter(phone=phone).first()

                            if candidate:
                                self._update_candidate(candidate, parsed_data, temp_path)
                            else:
                                self._create_new_candidate(parsed_data, temp_path)

                except Exception as e:
                    logger.error(f"Error procesando adjunto {attachment['filename']}: {e}")
                finally:
                    temp_path.unlink()  # Eliminar archivo temporal

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

            # Procesar en lotes
            for i in range(0, len(email_ids), batch_size):
                batch = email_ids[i:i + batch_size]
                for email_id in batch:
                    self._process_single_email(mail, email_id)
        finally:
            mail.close()
            mail.logout()

        self._generate_summary_and_send_report(**self.stats)

    def _generate_summary_and_send_report(self, candidates_processed, candidates_created, candidates_updated):
        """
        Genera y envía un resumen del procesamiento al administrador.
        """
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
            # Ejecutar `send_email` usando asyncio.run
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



    def _process_job_alert_email(self, mail, email_id, message):
        """
        Procesa correos de alertas de empleo de LinkedIn y Glassdoor.
        """
        try:
            sender = message["From"]
            subject = message["Subject"]

            if not sender or not subject:
                return

            # Identificar correos de LinkedIn y Glassdoor
            if sender.lower() not in ['jobs-noreply@linkedin.com', 'jobalerts-noreply@linkedin.com', 'jobs-listings@linkedin.com', 'alerts@glassdoor.com', 'noreply@glassdoor.com', 'TalentCommunity@talent.honeywell.com', 'santander@myworkday.com']:
                return  # Si no es un remitente válido, ignorar

            # Extraer contenido del correo
            body = None
            if message.is_multipart():
                for part in message.walk():
                    if part.get_content_type() == "text/html":
                        body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                        break
            else:
                body = message.get_payload(decode=True).decode("utf-8", errors="ignore")

            if not body:
                logger.warning(f"Correo {email_id} de {sender} sin contenido HTML procesable.")
                return

            # Parsear el HTML para encontrar vacantes
            soup = BeautifulSoup(body, "html.parser")
            job_listings = []

            # LinkedIn: Buscar vacantes en el cuerpo del correo
            for job_section in soup.find_all("a", href=True):
                job_title = job_section.get_text(strip=True)
                job_link = job_section["href"]

                # Validar que sea una vacante real
                if "linkedin.com/jobs/view" in job_link:
                    job_listings.append({
                        "job_title": job_title,
                        "job_link": job_link,
                        "company_name": "LinkedIn Alert",
                        "job_description": f"Vacante detectada desde LinkedIn: {job_title}",
                        "business_unit": 4  # Ajustar según la unidad de negocio
                    })

            if not job_listings:
                logger.warning(f"No se detectaron vacantes en correo {email_id}")
                return

            # Crear vacantes en el sistema
            for job_data in job_listings:
                vacante_manager = VacanteManager(job_data)
                vacante_manager.create_job_listing()

            # Mover el correo procesado
            self._move_email(mail, email_id, self.FOLDER_CONFIG['parsed_folder'])

        except Exception as e:
            logger.error(f"Error procesando alerta de empleo {email_id}: {e}")
            self._move_email(mail, email_id, self.FOLDER_CONFIG['error_folder'])


class CVParser:
    def __init__(self, business_unit: str):
        """
        Initialize the CVParser with specific configurations for a business unit.
        """
        self.business_unit = business_unit
        self.nlp = self.load_spacy_model()
        self.analysis_points = self.get_analysis_points()
        self.cross_analysis = self.get_cross_analysis()
        self.DIVISION_SKILLS = self._load_division_skills()

    def detect_language(self, text: str) -> str:
        """
        Detects the language of the text.
        """
        try:
            language = detect(text)
            logger.info(f"Idioma detectado: {language}")
            return language
        except Exception as e:
            logger.error(f"Error detectando idioma: {e}")
            return "unknown"

    def load_spacy_model(self, language: str) -> spacy.Language:
        """
        Loads a SpaCy model dynamically based on the language detected.
        """
        models = {
            "es": "es_core_news_sm",
            "en": "en_core_web_sm",
        }
        model_name = models.get(language, "en_core_web_sm")  # Default to English
        try:
            logger.info(f"Cargando modelo SpaCy para idioma: {language}")
            return spacy.load(model_name)
        except Exception as e:
            logger.error(f"Error cargando modelo SpaCy para {language}: {e}")
            raise

    def prepare_nlp_model(self, text: str):
        """
        Detecta el idioma y prepara el modelo NLP correspondiente.
        """
        language = self.detect_language(text)
        self.nlp = self.load_spacy_model(language)
        logger.info(f"Modelo NLP cargado para idioma: {language}")


    def get_analysis_points(self) -> Dict:
        """
        Load analysis points for parsing.
        """
        logger.info("Cargando puntos de análisis...")
        # Replace with real implementation, e.g., loading from config or database
        return {"education": [], "skills": [], "experience": []}

    def get_cross_analysis(self) -> Dict:
        """
        Load cross-analysis configuration.
        """
        logger.info("Cargando análisis cruzado...")
        # Replace with real implementation
        return {"division_specific": []}

    def _load_division_skills(self) -> Dict:
        """
        Load skills mapping for the division.
        """
        logger.info("Cargando habilidades específicas por división...")
        # Replace with real implementation
        return {"finance": ["budgeting", "forecasting"], "tech": ["programming", "AI"]}

    def extract_attachments(self, message) -> List[Dict]:
        """
        Extract attachments from an email message.
        """
        attachments = []
        for part in message.walk():
            if part.get_content_maintype() == 'multipart':
                continue
            if part.get('Content-Disposition') is None:
                continue

            filename = part.get_filename()
            if filename:
                content = part.get_payload(decode=True)
                attachments.append({
                    'filename': filename,
                    'content': content
                })
        logger.info(f"Se encontraron {len(attachments)} adjuntos.")
        return attachments

    def extract_text_from_file(self, file_path: Path) -> Optional[str]:
        """
        Extract text from a PDF or DOCX file.
        """
        if not file_path.exists():
            logger.error(f"Archivo no encontrado: {file_path}")
            return None

        try:
            if file_path.suffix.lower() == '.pdf':
                reader = PdfReader(str(file_path))
                text = ' '.join(page.extract_text() for page in reader.pages)
            elif file_path.suffix.lower() in ['.doc', '.docx']:
                doc = docx.Document(str(file_path))
                text = "\n".join(para.text for para in doc.paragraphs)
            else:
                logger.warning(f"Formato de archivo no soportado: {file_path}")
                return None
                
            if not text.strip():
                logger.warning(f"No se pudo extraer texto de: {file_path}")
                return None
                
            return text
        except Exception as e:
            logger.error(f"Error extrayendo texto de {file_path}: {e}")
            return None

    def parse(self, text: str) -> Dict:
        """
        Parse text from a CV to extract relevant information.
        """
        logger.info("Iniciando análisis de texto...")

        # Preparar modelo de NLP dinámicamente según el idioma
        self.prepare_nlp_model(text)

        parsed_data = {"education": [], "experience": [], "skills": []}

        try:
            doc = self.nlp(text)

            # Extract education
            parsed_data["education"] = self._extract_education(doc)

            # Extract experience
            parsed_data["experience"] = self._extract_experience(doc)

            # Extract skills
            parsed_data["skills"] = self._extract_skills(doc)

            logger.info("Análisis completado con éxito.")
            return parsed_data
        except Exception as e:
            logger.error(f"Error analizando texto: {e}")
            return {}


    def get_analysis_points(self):
        """
        Returns the primary analysis points based on the business unit.
        """
        analysis_points = {
            'huntRED®': ['leadership_skills', 'executive_experience', 'achievements', 'management_experience', 'responsibilities', 'language_skills'],
            'huntRED® Executive': ['strategic_planning', 'board_experience', 'global_exposure', 'executive_experience', 'responsibilities', 'language_skills', 'international_experience'],
            'huntu': ['education', 'projects', 'skills', 'potential_for_growth', 'achievements'],
            'amigro': ['work_authorization', 'language_skills', 'international_experience', 'skills'],
        }
        default_analysis = ['skills', 'experience', 'education']
        return analysis_points.get(self.business_unit.name, default_analysis)

    def get_cross_analysis(self):
        """
        Returns analysis points for cross-checking between units to ensure flexibility.
        """
        cross_analysis = {
            'huntRED®': ['strategic_planning', 'board_experience'],  # Consider huntRED Executive attributes
            'huntRED® Executive': ['management_experience', 'achievements'],  # Consider huntRED attributes
            'huntu': ['achievements', 'management_experience'],  # Check readiness for huntRED
            'amigro': []  # No cross-analysis for Amigro, as the boundary is clear
        }
        return cross_analysis.get(self.business_unit.name, [])

    def extract_information(self, doc, point):
        """
        Extrae información específica basada en un punto de análisis.
        """
        if point == "skills":
            return self.extract_skills(doc)
        elif point == "experience":
            return self.extract_experience(doc)
        elif point == "education":
            return self.extract_education(doc)
        elif point == "achievements":
            return self.extract_achievements(doc)
        elif point == "management_experience":
            return self.extract_management_experience(doc)
        elif point == "leadership_skills":
            return self.extract_leadership_skills(doc)
        elif point == "language_skills":
            return self.extract_language_skills(doc)
        elif point == "work_authorization":
            return self.extract_work_authorization(doc)
        elif point == "strategic_planning":
            return self.extract_strategic_planning(doc)
        elif point == "board_experience":
            return self.extract_board_experience(doc)
        elif point == "global_exposure":
            return self.extract_global_exposure(doc)
        elif point == "international_experience":
            return self.extract_international_experience(doc)
        else:
            return f"Analysis point '{point}' is not defined."

    # Métodos específicos mejorados
    def extract_skills(self, doc):
        """
        Extrae habilidades del texto utilizando SkillNer.
        """
        skills = sn.extract_skills(doc.text)
        extracted_skills = [skill['skill'] for skill in skills]
        logger.debug(f"Habilidades extraídas: {extracted_skills}")
        return extracted_skills

    def extract_experience(self, doc):
        """
        Extrae experiencia laboral en formato estructurado.
        """
        experiences = []
        experience_keywords = ["trabajé", "trabajo", "puesto", "empleo", "cargo", "experiencia", "desempeñé"]
        for sent in doc.sents:
            if any(keyword in sent.text.lower() for keyword in experience_keywords):
                experiences.append(sent.text.strip())
        logger.debug(f"Experiencias extraídas: {experiences}")
        return experiences

    def extract_education(self, doc):
        """
        Extrae información educativa en formato estructurado.
        """
        education = []
        education_keywords = ["licenciatura", "maestría", "doctorado", "carrera", "universidad", "instituto"]
        for sent in doc.sents:
            if any(keyword in sent.text.lower() for keyword in education_keywords):
                education.append(sent.text.strip())
        logger.debug(f"Educación extraída: {education}")
        return education

    def extract_achievements(self, doc):
        """
        Extrae logros destacados.
        """
        achievements = []
        achievement_keywords = ["logré", "alcancé", "implementé", "desarrollé", "aumenté", "reduje", "optimizé"]
        for sent in doc.sents:
            if any(keyword in sent.text.lower() for keyword in achievement_keywords):
                achievements.append(sent.text.strip())
        logger.debug(f"Logros extraídos: {achievements}")
        return achievements

    def extract_management_experience(self, doc):
        """
        Extrae experiencia en gestión.
        """
        management_experience = []
        management_keywords = ["lideré", "supervisé", "coordinar", "dirigir", "gerente", "manager"]
        for sent in doc.sents:
            if any(keyword in sent.text.lower() for keyword in management_keywords):
                management_experience.append(sent.text.strip())
        logger.debug(f"Experiencia de gestión extraída: {management_experience}")
        return management_experience

    def extract_leadership_skills(self, doc):
        """
        Extrae habilidades de liderazgo.
        """
        leadership_skills = []
        leadership_keywords = ["liderazgo", "trabajo en equipo", "comunicación", "motivación", "influencia"]
        for token in doc:
            if token.text.lower() in leadership_keywords:
                leadership_skills.append(token.text)
        logger.debug(f"Habilidades de liderazgo extraídas: {leadership_skills}")
        return leadership_skills

    def extract_language_skills(self, doc):
        """
        Extrae habilidades lingüísticas.
        """
        languages = []
        language_keywords = ["español", "inglés", "francés", "alemán", "portugués", "bilingüe"]
        for token in doc:
            if token.text.lower() in language_keywords:
                languages.append(token.text)
        logger.debug(f"Habilidades lingüísticas extraídas: {languages}")
        return languages

    def extract_work_authorization(self, doc):
        """
        Extrae información sobre autorización de trabajo.
        """
        work_authorization = []
        work_keywords = ["permiso de trabajo", "visa", "estatus migratorio", "autorización laboral"]
        for sent in doc.sents:
            if any(keyword in sent.text.lower() for keyword in work_keywords):
                work_authorization.append(sent.text.strip())
        logger.debug(f"Autorización de trabajo extraída: {work_authorization}")
        return work_authorization

    # Métodos adicionales para análisis específicos
    def extract_strategic_planning(self, doc):
        """
        Extrae información relacionada con planificación estratégica.
        """
        strategic_planning = []
        keywords = ["planificación estratégica", "estrategia empresarial", "desarrollo estratégico"]
        for sent in doc.sents:
            if any(keyword in sent.text.lower() for keyword in keywords):
                strategic_planning.append(sent.text.strip())
        logger.debug(f"Planificación estratégica extraída: {strategic_planning}")
        return strategic_planning

    def extract_board_experience(self, doc):
        """
        Extrae experiencia en consejos de administración.
        """
        board_experience = []
        keywords = ["consejo de administración", "miembro del consejo", "board member"]
        for sent in doc.sents:
            if any(keyword in sent.text.lower() for keyword in keywords):
                board_experience.append(sent.text.strip())
        logger.debug(f"Experiencia en consejo de administración extraída: {board_experience}")
        return board_experience

    def extract_global_exposure(self, doc):
        """
        Extrae información sobre exposición global.
        """
        global_exposure = []
        keywords = ["exposición global", "trabajo internacional", "proyectos en el extranjero"]
        for sent in doc.sents:
            if any(keyword in sent.text.lower() for keyword in keywords):
                global_exposure.append(sent.text.strip())
        logger.debug(f"Exposición global extraída: {global_exposure}")
        return global_exposure

    def extract_international_experience(self, doc):
        """
        Extrae experiencia internacional.
        """
        international_experience = []
        keywords = ["experiencia internacional", "trabajo en el extranjero", "proyectos internacionales"]
        for sent in doc.sents:
            if any(keyword in sent.text.lower() for keyword in keywords):
                international_experience.append(sent.text.strip())
        logger.debug(f"Experiencia internacional extraída: {international_experience}")
        return international_experience

    def associate_divisions(skills: List[str]) -> List[str]:
        associated_divisions = set()
        skills_lower = set(skill.lower() for skill in skills)
        for division, division_skills in DIVISION_SKILLS.items():
            if skills_lower.intersection(set(skill.lower() for skill in division_skills)):
                associated_divisions.add(division)
        return list(associated_divisions)

    def validate_candidate_data(data):
        required_fields = ["nombre", "apellido_paterno", "email"]
        for field in required_fields:
            if not data.get(field):
                raise ValueError(f"El campo {field} es obligatorio y está vacío.")
        
    def parse_and_match_candidate(self, file_path):
        """
        Procesa un CV y busca coincidencias de candidatos existentes.
        """
        parsed_data = self._extract_text(file_path)
        if not parsed_data:
            logger.warning(f"No se pudo extraer datos del CV: {file_path}")
            return

        email = parsed_data.get("email")
        phone = parsed_data.get("phone")

        # Buscar candidato existente
        candidate = Person.objects.filter(email=email).first() or Person.objects.filter(phone=phone).first()

        if candidate:
            self._update_candidate(candidate, parsed_data, file_path)
        else:
            self._create_new_candidate(parsed_data, file_path)

    def extract_text_from_file(self, file_path):
        """
        Extrae texto de un archivo PDF o DOCX.
        
        Args:
            file_path (Path): Ruta al archivo a procesar
            
        Returns:
            str: Texto extraído del archivo o None si hay un error
        """
        try:
            if file_path.suffix.lower() == '.pdf':
                reader = PdfReader(str(file_path))
                text = ''.join(page.extract_text() for page in reader.pages)
            elif file_path.suffix.lower() in ['.doc', '.docx']:
                doc = docx.Document(str(file_path))
                text = "\n".join(para.text for para in doc.paragraphs)
            else:
                logger.warning(f"Formato de archivo no soportado: {file_path}")
                return None
                
            if not text.strip():
                logger.warning(f"No se pudo extraer texto del archivo: {file_path}")
                return None
                
            return text
        except Exception as e:
            logger.error(f"Error al extraer texto de {file_path}: {e}")
            return None

    def _extract_text(self, file_path):
        """
        Extrae texto desde archivos de CV (PDF o Word).
        """
        try:
            if file_path.suffix.lower() == '.pdf':
                text = extract_text_pdf(str(file_path))
            elif file_path.suffix.lower() in ['.doc', '.docx']:
                doc = docx.Document(str(file_path))
                text = "\n".join([para.text for para in doc.paragraphs])
            else:
                logger.warning(f"Formato de archivo no soportado: {file_path}")
                return {}
            
            # Procesamiento básico del texto para extraer información relevante
            parsed_data = self.parse(text)
            return parsed_data
        except Exception as e:
            logger.error(f"Error extrayendo texto de {file_path}: {e}")
            return {}

    def _update_candidate(self, candidate, parsed_data, file_path):
        """
        Actualiza información del candidato existente.
        """
        candidate.cv_file = file_path
        candidate.cv_analysis = parsed_data
        candidate.cv_parsed = True
        candidate.metadata["last_cv_update"] = now().isoformat()

        # Extraer y asociar habilidades y divisiones
        skills = self.extract_skills(parsed_data.get("skills", ""))
        divisions = self.associate_divisions(skills)
        candidate.metadata["skills"] = list(set(candidate.metadata.get("skills", []) + skills))
        candidate.metadata["divisions"] = list(set(candidate.metadata.get("divisions", []) + divisions))

        candidate.save()
        logger.info(f"Perfil actualizado: {candidate.nombre} {candidate.apellido_paterno}")

    def _create_new_candidate(self, parsed_data, file_path):
        """
        Crea un nuevo candidato si no existe.
        """
        skills = self.extract_skills(parsed_data.get("skills", ""))
        divisions = self.associate_divisions(skills)

        candidate = Person.objects.create(
            nombre=parsed_data.get("nombre"),
            apellido_paterno=parsed_data.get("apellido_paterno"),
            apellido_materno=parsed_data.get("apellido_materno"),
            email=parsed_data.get("email"),
            phone=parsed_data.get("phone"),
            skills=parsed_data.get("skills"),
            cv_file=file_path,
            cv_parsed=True,
            cv_analysis=parsed_data,
            metadata={
                "last_cv_update": now().isoformat(),
                "skills": skills,
                "divisions": divisions,
                "created_at": now().isoformat(),  # Se agrega fecha de creación en metadata
            }
        )
        logger.info(f"Nuevo perfil creado: {candidate.nombre} {candidate.apellido_paterno}")

def send_error_alert(message):
    try:
        asyncio.run(send_email(
            subject="Error Crítico en Procesamiento de CVs",
            body=message,
            to_email="admin@huntred.com",
            from_email="noreply@huntred.com",
        ))
    except Exception as e:
        logger.error(f"No se pudo enviar la alerta: {e}")


