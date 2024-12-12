# Ubicación /home/amigro/app/parser.py

import imaplib
import email
from pathlib import Path
import spacy
from app.models import Person, ConfiguracionBU


class CVParser:
    def __init__(self, business_unit):
        """
        Initializes the CVParser for a specific business unit.
        """
        self.business_unit = business_unit
        self.nlp = spacy.load("es_core_news_sm")
        self.analysis_points = self.get_analysis_points()
        self.cross_analysis = self.get_cross_analysis()

    def get_analysis_points(self):
        """
        Returns the primary analysis points based on the business unit.
        """
        analysis_points = {
            'huntRED®': ['leadership_skills', 'executive_experience', 'achievements', 'management_experience'],
            'huntRED® Executive': ['strategic_planning', 'board_experience', 'global_exposure', 'executive_experience'],
            'huntU®': ['education', 'projects', 'skills', 'potential_for_growth'],
            'Amigro®': ['work_authorization', 'language_skills', 'international_experience', 'skills'],
        }
        default_analysis = ['skills', 'experience', 'education']
        return analysis_points.get(self.business_unit, default_analysis)

    def get_cross_analysis(self):
        """
        Returns analysis points for cross-checking between units to ensure flexibility.
        """
        cross_analysis = {
            'huntRED®': ['strategic_planning', 'board_experience'],  # Consider huntRED Executive attributes
            'huntRED® Executive': ['management_experience', 'achievements'],  # Consider huntRED attributes
            'huntU®': ['achievements', 'management_experience'],  # Check readiness for huntRED
            'Amigro®': []  # No cross-analysis for Amigro, as the boundary is clear
        }
        return cross_analysis.get(self.business_unit, [])

    def parse(self, cv_text):
        """
        Parses the CV text to extract relevant information based on the business unit and cross-analysis.
        """
        doc = self.nlp(cv_text)
        results = {}

        # Primary analysis
        for point in self.analysis_points:
            results[point] = self.extract_information(doc, point)

        # Cross-analysis
        if self.cross_analysis:
            results['cross_analysis'] = {}
            for point in self.cross_analysis:
                results['cross_analysis'][point] = self.extract_information(doc, point)

        return results

    def extract_information(self, doc, point):
        """
        Placeholder method to extract specific information based on a point of analysis.
        """
        # Replace with actual NLP logic
        return f"Extracted information for {point}"

    def parse_and_match_candidate(self, file_path):
        """
        Procesa un CV y busca coincidencias de candidatos existentes.
        """
        parsed_data = self._extract_text(file_path)
        email = parsed_data.get("email")
        phone = parsed_data.get("phone")

        # Buscar candidato existente
        candidate = Person.objects.filter(
            email=email
        ).first() or Person.objects.filter(phone=phone).first()

        if candidate:
            self._update_candidate(candidate, parsed_data, file_path)
        else:
            self._create_new_candidate(parsed_data, file_path)

    def _extract_text(self, file_path):
        """
        Extrae texto desde archivos de CV (PDF o Word).
        """
        return {
            "nombre": "Nombre Ejemplo",
            "apellido_paterno": "Apellido Paterno",
            "apellido_materno": "Apellido Materno",
            "email": "example@example.com",
            "phone": "1234567890",
            "skills": "Python, Django, Machine Learning"
        }

    def _update_candidate(self, candidate, parsed_data, file_path):
        """
        Actualiza información del candidato existente.
        """
        candidate.cv_file = file_path
        candidate.cv_analysis = parsed_data
        candidate.cv_parsed = True
        candidate.save()

    def _create_new_candidate(self, parsed_data, file_path):
        """
        Crea un nuevo candidato si no existe.
        """
        Person.objects.create(
            nombre=parsed_data.get("nombre"),
            apellido_paterno=parsed_data.get("apellido_paterno"),
            apellido_materno=parsed_data.get("apellido_materno"),
            email=parsed_data.get("email"),
            phone=parsed_data.get("phone"),
            skills=parsed_data.get("skills"),
            cv_file=file_path,
            cv_parsed=True,
            cv_analysis=parsed_data
        )

class IMAPCVProcessor:
    def __init__(self, business_unit):
        """
        Inicializa el procesador con la configuración dinámica de la unidad de negocio.
        """
        self.config = self._load_config(business_unit)
        self.parser = CVParser(business_unit)

    def _load_config(self, business_unit):
        """
        Carga la configuración de IMAP desde ConfiguracionBU.
        """
        try:
            config = ConfiguracionBU.objects.get(business_unit=business_unit)
            return {
                'server': config.smtp_host,
                'port': config.smtp_port,
                'username': config.smtp_username,
                'password': config.smtp_password,
                'use_tls': config.smtp_use_tls,
                'cv_folder': "CV",
                'parsed_folder': "Parsed"
            }
        except ConfiguracionBU.DoesNotExist:
            raise ValueError(f"No configuration found for business unit: {business_unit}")

    def process_emails(self):
        """
        Procesa los emails utilizando los valores dinámicos.
        """
        with imaplib.IMAP4_SSL(self.config['server']) as mail:
            mail.login(self.config['username'], self.config['password'])
            mail.select(self.config['cv_folder'])

            status, messages = mail.search(None, 'ALL')
            for num in messages[0].split():
                _, data = mail.fetch(num, '(RFC822)')
                msg = email.message_from_bytes(data[0][1])
                self._process_email(msg, mail, num)

    def _process_email(self, msg, mail, msg_id):
        """
        Procesa un email individual y extrae los CVs adjuntos.
        """
        for part in msg.walk():
            if part.get_content_type() in ['application/pdf', 'application/msword']:
                filename = part.get_filename()
                file_path = Path(f"/tmp/{filename}")
                with open(file_path, 'wb') as f:
                    f.write(part.get_payload(decode=True))

                self.parser.parse_and_match_candidate(file_path)

        # Mueve el correo a la carpeta Parsed
        mail.store(msg_id, '+FLAGS', '\\Deleted')
        mail.append(self.config['parsed_folder'])