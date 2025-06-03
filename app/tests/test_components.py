import pytest
from django.test import TestCase
from django.utils import timezone
from asgiref.sync import async_to_sync
from app.models import Person, BusinessUnit
from app.ats.chatbot.components import (
    IntentDetector,
    StateManager,
    ContextManager,
    ResponseGenerator
)

class TestComponents(TestCase):
    def setUp(self):
        self.business_unit = BusinessUnit.objects.create(
            name="test_unit",
            description="Test business unit"
        )
        self.person = Person.objects.create(
            name="Test User",
            email="test@example.com"
        )

    def test_intent_detector(self):
        """Test detector de intents"""
        detector = IntentDetector(self.business_unit)
        intent = async_to_sync(detector.detect_intent)("Quiero crear mi perfil")
        assert intent is not None

    def test_state_manager(self):
        """Test gestor de estados"""
        manager = StateManager(self.business_unit)
        
        # Determinar siguiente estado
        next_state = async_to_sync(manager.determine_next_state)("crear_perfil")
        assert next_state is not None
        
        # Actualizar estado
        chat_state = ChatState.objects.create(
            person=self.person,
            business_unit=self.business_unit,
            state="initial"
        )
        
        result = async_to_sync(manager.update_state)(chat_state, next_state)
        assert result is True

    def test_context_manager(self):
        """Test gestor de contexto"""
        manager = ContextManager(self.business_unit)
        
        updates = {
            'last_intent': 'crear_perfil',
            'timestamp': timezone.now()
        }
        
        async_to_sync(manager.update_context)(updates)
        assert manager.context.get('last_intent') == 'crear_perfil'

    def test_response_generator(self):
        """Test generador de respuestas"""
        generator = ResponseGenerator(self.business_unit)
        
        response = async_to_sync(generator.generate_response)(
            "crear_perfil",
            "initial"
        )
        
        assert 'text' in response
        assert 'options' in response
        assert 'metadata' in response
