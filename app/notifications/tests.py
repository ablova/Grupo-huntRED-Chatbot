# /home/pablo/app/notifications/tests.py
#
# Pruebas para el módulo. Verifica la correcta funcionalidad de componentes específicos.

from django.test import TestCase
from django.contrib.auth.models import User
from .notifications_manager import NotificationsManager
from .config import NotificationsConfig
from .recipients import CandidateRecipient, ConsultantRecipient, ClientRecipient
from .channels import EmailChannel, WhatsAppChannel, XChannel
from .templates import ProposalTemplate, PaymentTemplate, OpportunityTemplate
import logging

logger = logging.getLogger('app.notifications.tests')

class NotificationsTestCase(TestCase):
    """Casos de prueba para el sistema de notificaciones."""
    
    def setUp(self):
        """Configuración inicial para los tests."""
        # Crear usuarios de prueba
        self.candidate = User.objects.create_user(
            username='candidate',
            email='candidate@huntred.com',
            password='test123'
        )
        
        self.consultant = User.objects.create_user(
            username='consultant',
            email='consultant@huntred.com',
            password='test123'
        )
        
        self.client = User.objects.create_user(
            username='client',
            email='client@huntred.com',
            password='test123'
        )
        
        # Inicializar gestor de notificaciones
        self.manager = NotificationsManager()
    
    def test_send_proposal_notification(self):
        """Test para enviar notificación de propuesta."""
        recipient = CandidateRecipient(self.candidate)
        context = {
            'name': 'Test Candidate',
            'position': 'Developer',
            'company': 'huntRED',
            'location': 'CDMX',
            'salary': '100000',
            'status': 'Pendiente'
        }
        
        success = self.manager.send_notification(
            recipient,
            'proposal',
            context
        )
        
        self.assertTrue(success)
    
    def test_send_payment_notification(self):
        """Test para enviar notificación de pago."""
        recipient = ConsultantRecipient(self.consultant)
        context = {
            'name': 'Test Consultant',
            'reference': 'PAY123',
            'amount': 50000.0,
            'date': '2025-05-09',
            'status': 'Pagado'
        }
        
        success = self.manager.send_notification(
            recipient,
            'payment',
            context
        )
        
        self.assertTrue(success)
    
    def test_send_opportunity_notification(self):
        """Test para enviar notificación de oportunidad."""
        recipient = ClientRecipient(self.client)
        context = {
            'name': 'Test Client',
            'position': 'Manager',
            'company': 'huntRED',
            'location': 'CDMX',
            'salary': '150000',
            'requirements': '5+ años de experiencia'
        }
        
        success = self.manager.send_notification(
            recipient,
            'opportunity',
            context
        )
        
        self.assertTrue(success)

    def test_send_fiscal_notification(self):
        """Test para enviar notificación fiscal."""
        recipient = FiscalRecipient(self.client)
        context = {
            'name': 'Test Fiscal',
            'company': 'huntRED',
            'rfc': 'HNT000101HNT',
            'position': 'Responsable Fiscal',
            'status': 'Activo'
        }
        
        success = self.manager.send_notification(
            recipient,
            'fiscal',
            context
        )
        
        self.assertTrue(success)

    def test_send_collector_notification(self):
        """Test para enviar notificación de cobro."""
        recipient = CollectorRecipient(self.consultant)
        context = {
            'name': 'Test Collector',
            'company': 'huntRED',
            'position': 'Responsable de Cobro',
            'payment_terms': 'Neto 30',
            'status': 'Activo'
        }
        
        success = self.manager.send_notification(
            recipient,
            'collector',
            context
        )
        
        self.assertTrue(success)

    def test_send_interview_notification(self):
        """Test para enviar notificación de entrevista."""
        recipient = InterviewRecipient(self.candidate)
        context = {
            'name': 'Test Candidate',
            'position': 'Developer',
            'interview_time': '2025-05-10 10:00',
            'interview_location': 'CDMX',
            'interviewers': ['Juan Pérez', 'María García']
        }
        
        success = self.manager.send_notification(
            recipient,
            'interview',
            context
        )
        
        self.assertTrue(success)

    def test_send_all_notifications(self):
        """Test para enviar todas las notificaciones a un destinatario."""
        recipient = CandidateRecipient(self.candidate)
        
        # Notificación de propuesta
        proposal_context = {
            'name': 'Test Candidate',
            'position': 'Developer',
            'company': 'huntRED',
            'location': 'CDMX',
            'salary': '100000',
            'status': 'Pendiente'
        }
        
        # Notificación de oportunidad
        opportunity_context = {
            'name': 'Test Candidate',
            'position': 'Manager',
            'company': 'huntRED',
            'location': 'CDMX',
            'salary': '150000',
            'requirements': '5+ años de experiencia'
        }
        
        # Notificación de entrevista
        interview_context = {
            'name': 'Test Candidate',
            'position': 'Developer',
            'interview_time': '2025-05-10 10:00',
            'interview_location': 'CDMX',
            'interviewers': ['Juan Pérez', 'María García']
        }
        
        # Enviar todas las notificaciones
        proposal_success = self.manager.send_notification(
            recipient,
            'proposal',
            proposal_context
        )
        
        opportunity_success = self.manager.send_notification(
            recipient,
            'opportunity',
            opportunity_context
        )
        
        interview_success = self.manager.send_notification(
            recipient,
            'interview',
            interview_context
        )
        
        self.assertTrue(proposal_success)
        self.assertTrue(opportunity_success)
        self.assertTrue(interview_success)
    
    def test_send_bulk_notifications(self):
        """Test para enviar notificaciones en masa."""
        recipients = [
            CandidateRecipient(self.candidate),
            ConsultantRecipient(self.consultant),
            ClientRecipient(self.client)
        ]
        
        context = {
            'name': 'Test',
            'position': 'Developer',
            'company': 'huntRED',
            'location': 'CDMX',
            'salary': '100000',
            'status': 'Pendiente'
        }
        
        results = self.manager.send_bulk_notifications(
            recipients,
            'proposal',
            context
        )
        
        self.assertTrue(all(results.values()))
    
    def test_channel_priority(self):
        """Test para verificar la prioridad de los canales."""
        channels = NotificationsConfig.get_priority_channels()
        
        self.assertEqual(
            channels,
            [('email', 1), ('whatsapp', 2), ('x', 3)]
        )
    
    def test_template_rendering(self):
        """Test para verificar el renderizado de templates."""
        template = ProposalTemplate()
        context = {
            'name': 'Test',
            'position': 'Developer',
            'company': 'huntRED',
            'location': 'CDMX',
            'salary': '100000',
            'status': 'Pendiente'
        }
        
        rendered = template.render(context)
        self.assertIn('Test', rendered)
        self.assertIn('Developer', rendered)
        self.assertIn('huntRED', rendered)
        self.assertIn('CDMX', rendered)
        self.assertIn('100000', rendered)
        self.assertIn('Pendiente', rendered)
