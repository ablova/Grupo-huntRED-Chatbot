import pytest
from django.test import TestCase
from django.utils import timezone
from asgiref.sync import async_to_sync
from app.models import Person, BusinessUnit, ChatState
from app.ats.chatbot.flow.conversational_flow_manager import ConversationalFlowManager

class TestConversationalFlowManager(TestCase):
    def setUp(self):
        self.business_unit = BusinessUnit.objects.create(
            name="test_unit",
            description="Test business unit"
        )
        self.person = Person.objects.create(
            name="Test User",
            email="test@example.com"
        )
        self.flow_manager = ConversationalFlowManager(self.business_unit)

    def test_process_message(self):
        """Test procesamiento de mensaje básico"""
        result = async_to_sync(self.flow_manager.process_message)(
            self.person,
            "Hola"
        )
        assert result['success'] is True
        assert 'response' in result

    def test_intent_detection(self):
        """Test detección de intents"""
        intent = async_to_sync(self.flow_manager.intent_detector.detect_intent)(
            "Quiero crear mi perfil"
        )
        assert intent is not None

    def test_state_transition(self):
        """Test transición de estado"""
        chat_state = ChatState.objects.create(
            person=self.person,
            business_unit=self.business_unit,
            state="initial"
        )
        
        new_state = async_to_sync(self.flow_manager.state_manager.determine_next_state)(
            "crear_perfil"
        )
        assert new_state is not None

    def test_context_management(self):
        """Test gestión de contexto"""
        updates = {
            'last_intent': 'crear_perfil',
            'timestamp': timezone.now()
        }
        
        async_to_sync(self.flow_manager.context_manager.update_context)(updates)
        assert self.flow_manager.context_manager.context.get('last_intent') == 'crear_perfil'
