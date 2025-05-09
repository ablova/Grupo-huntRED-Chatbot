import re
import logging
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from . import config
from ..models import Person, Conversation
from ..tasks import process_message, send_notification
from ..utils.visualization.report_generator import ReportGenerator

logger = logging.getLogger('app.com.utilidades.parser')

class CVParser:
    """Clase para procesar CVs y gestionar la comunicación inicial."""
    
    def __init__(self):
        self.email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        self.phone_pattern = r'\b\d{10}\b'
        
    def process_cv(self, cv_data: dict) -> bool:
        """
        Procesa un CV recibido por email y gestiona la comunicación inicial.
        
        Args:
            cv_data: Diccionario con los datos del CV
                - name: str
                - email: str
                - phone: str
                - file_path: str
                - business_unit: str
        
        Returns:
            bool: True si el procesamiento fue exitoso, False en caso contrario
        """
        try:
            # Verificar si el usuario ya existe
            existing_person = Person.objects.filter(
                email=cv_data['email']
            ).first()
            
            if existing_person:
                logger.info(f"Person already exists: {existing_person.email}")
                return False
                
            # Crear nuevo usuario
            person = Person.objects.create(
                name=cv_data['name'],
                email=cv_data['email'],
                phone=self._clean_phone(cv_data['phone']),
                business_unit=cv_data['business_unit']
            )
            
            # Iniciar conversación
            self._initiate_conversation(person)
            
            # Enviar email de bienvenida
            self._send_welcome_email(person)
            
            # Generar reporte
            ReportGenerator().generate_conversation_metrics()
            
            logger.info(f"CV processed successfully for {person.email}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing CV: {str(e)}")
            return False
    
    def _clean_phone(self, phone: str) -> str:
        """Limpia el número de teléfono, dejando solo dígitos."""
        return re.sub(r'[^0-9]', '', phone) if phone else ''
    
    def _initiate_conversation(self, person: Person) -> None:
        """Inicia una conversación con el nuevo usuario."""
        try:
            # Crear conversación
            conversation = Conversation.objects.create(
                recipient=person,
                channel='email',
                state='INICIO'
            )
            
            # Enviar mensaje inicial
            message = "Bienvenido/a al sistema de Grupo huntRED. Por favor, responda con el código de verificación que recibirá en su email."
            process_message.delay(conversation.id, message, 'email')
            
        except Exception as e:
            logger.error(f"Error initiating conversation: {str(e)}")
    
    def _send_welcome_email(self, person: Person) -> None:
        """Envía un email de bienvenida con el código de verificación."""
        try:
            # Generar código de verificación
            verification_code = self._generate_verification_code()
            
            # Renderizar template
            context = {
                'name': person.name,
                'verification_code': verification_code,
                'business_unit': person.business_unit,
                'opportunities_link': f"{settings.BASE_URL}/oportunidades/{person.business_unit}"
            }
            
            # Enviar email
            send_mail(
                subject='Bienvenido/a a Grupo huntRED - Verificación de Registro',
                message=render_to_string('com/emails/welcome.txt', context),
                html_message=render_to_string('com/emails/welcome.html', context),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[person.email],
                fail_silently=False
            )
            
            # Crear notificación
            send_notification.delay(
                person.id,
                'welcome_email',
                'email',
                'Bienvenido/a a Grupo huntRED. Por favor, verifique su registro.'
            )
            
        except Exception as e:
            logger.error(f"Error sending welcome email: {str(e)}")
    
    def _generate_verification_code(self) -> str:
        """Genera un código de verificación único."""
        import random
        return ''.join(random.choices('0123456789', k=6))
    
    def _send_referral_message(self, person: Person) -> None:
        """Envía un mensaje para invitar a conocidos."""
        try:
            # Crear mensaje de invitación
            message = "¡Hola! ¿Conoces a alguien que podría estar interesado en oportunidades laborales? " \
                    "Puedes invitar a tus conocidos a través de este enlace: " \
                    f"{settings.BASE_URL}/invitar/{person.business_unit}"
            
            # Enviar mensaje
            process_message.delay(
                person.id,
                message,
                'email'
            )
            
        except Exception as e:
            logger.error(f"Error sending referral message: {str(e)}")
