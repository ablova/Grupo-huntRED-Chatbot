import os
import sys
import pytest
import django
import asyncio
from unittest.mock import patch, MagicMock
from datetime import datetime

# Configuración de entorno de prueba
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_huntred.settings')
django.setup()

from app.models import Person, Feedback, Notification, Entrevista, Vacante, BusinessUnit
from app.ats.utils.feedback_service import FeedbackService
from app.ats.utils.whatsapp import WhatsAppApi

# Datos de prueba
TEST_PHONE = '+525518490291'
TEST_EMAIL = 'pablo@huntred.com'
TEST_TELEGRAM_ID = '871198362'
TEST_NAME = 'Pablo'
TEST_BU = 'huntRED'

class TestFeedbackService:
    """
    Tests para el servicio de feedback.
    """
    
    @pytest.fixture(scope="class")
    def test_interviewer(self):
        """Fixture para crear entrevistador de prueba."""
        person, created = Person.objects.get_or_create(
            phone=TEST_PHONE,
            defaults={
                'nombre': TEST_NAME,
                'email': TEST_EMAIL,
                'telegram_id': TEST_TELEGRAM_ID,
                'whatsapp_enabled': True
            }
        )
        return person
        
    @pytest.fixture(scope="class")
    def test_candidate(self):
        """Fixture para crear candidato de prueba."""
        candidate, created = Person.objects.get_or_create(
            nombre='Candidato Test',
            defaults={
                'email': 'candidato@test.com',
                'phone': '+5215555555555'
            }
        )
        return candidate
        
    @pytest.fixture(scope="class")
    def test_business_unit(self):
        """Fixture para crear BU de prueba."""
        bu, created = BusinessUnit.objects.get_or_create(
            name=TEST_BU
        )
        return bu
        
    @pytest.fixture(scope="class")
    def test_vacancy(self, test_business_unit):
        """Fixture para crear vacante de prueba."""
        vacancy, created = Vacante.objects.get_or_create(
            titulo='Vacante Test',
            defaults={
                'business_unit': test_business_unit,
                'descripcion': 'Vacante para tests',
                'ubicacion': 'Ciudad de México',
                'modalidad': 'Remoto',
                'experience_required': 3
            }
        )
        return vacancy
        
    @pytest.fixture(scope="class")
    def test_interview(self, test_candidate, test_interviewer, test_vacancy):
        """Fixture para crear entrevista de prueba."""
        interview, created = Entrevista.objects.get_or_create(
            candidato=test_candidate,
            tipo=test_interviewer,
            vacante=test_vacancy,
            defaults={
                'fecha': datetime.now(),
                'status': 'SCHEDULED'
            }
        )
        return interview
        
    @pytest.fixture(scope="class")
    def feedback_service(self):
        """Fixture para crear servicio de feedback."""
        return FeedbackService(TEST_BU)
        
    @pytest.mark.asyncio
    async def test_activation_link(self, feedback_service):
        """Test de generación de enlace de activación."""
        test_token = '12345678-abcd-1234-efgh-123456789abc'
        
        with patch.object(WhatsAppApi, 'get_activation_link', return_value=f'https://wa.me/{TEST_PHONE}?text=Activar%20{test_token}'):
            link = await feedback_service._get_whatsapp_activation_link(test_token)
            
            assert link is not None
            assert test_token in link
            
    @pytest.mark.asyncio
    async def test_send_feedback_notification(self, test_interview, feedback_service):
        """Test de envío de notificación de feedback."""
        with patch('app.ats.utils.notification_service.NotificationService.send_notification', return_value=MagicMock()):
            result = await feedback_service.send_feedback_notification(test_interview)
            
            assert result is not False
            
            # Verificar que se haya creado el feedback
            feedback = await Feedback.objects.filter(
                candidate=test_interview.candidato,
                interviewer=test_interview.tipo,
                feedback_type='INTERVIEW',
                status='PENDING'
            ).afirst()
            
            assert feedback is not None
            
    @pytest.mark.asyncio
    async def test_process_feedback(self, test_interview, feedback_service):
        """Test de procesamiento de feedback."""
        # Crear feedback pendiente
        feedback = await feedback_service._create_pending_feedback(test_interview)
        
        # Procesar feedback
        with patch.object(feedback_service, '_update_ml_with_feedback', return_value=None):
            processed = await feedback_service.process_feedback({
                'feedback_id': feedback.id,
                'is_candidate_liked': 'YES',
                'meets_requirements': 'YES',
                'missing_requirements': 'Python, Django',
                'additional_comments': 'Excelente candidato'
            })
            
            assert processed is not None
            assert processed.is_candidate_liked == 'YES'
            assert processed.meets_requirements == 'YES'
            assert processed.missing_requirements == 'Python, Django'
            assert processed.status == 'COMPLETED'
            
    @pytest.mark.asyncio
    async def test_skip_feedback(self, test_interview, feedback_service):
        """Test de omisión de feedback."""
        # Crear feedback pendiente
        feedback = await feedback_service._create_pending_feedback(test_interview)
        
        # Omitir feedback
        result = await feedback_service.skip_feedback(feedback.id)
        
        assert result is True
        
        # Verificar que se haya omitido
        skipped = await Feedback.objects.aget(id=feedback.id)
        assert skipped.status == 'SKIPPED'
        
    @pytest.mark.asyncio
    async def test_get_pending_feedback(self, test_interviewer, test_interview, feedback_service):
        """Test de obtención de feedback pendiente."""
        # Crear feedback pendiente
        feedback = await feedback_service._create_pending_feedback(test_interview)
        
        # Obtener pendientes
        pending = await feedback_service.get_pending_feedback(test_interviewer)
        
        assert len(pending) >= 1
        assert any(f.id == feedback.id for f in pending)
        
if __name__ == "__main__":
    pytest.main()
