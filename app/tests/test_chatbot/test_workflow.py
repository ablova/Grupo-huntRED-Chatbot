import pytest
from django.test import Client
from app.com.chatbot.views import ChatbotView
from app.com.chatbot.workflow.personality import PersonalityAnalyzer
from app.com.chatbot.components.state_manager import ChatStateManager
import asyncio
import os
from unittest.mock import patch, AsyncMock, MagicMock
from app.models import Person, BusinessUnit, ChatState
from app.com.chatbot.chat_state_manager import ChatStateManager
from app.com.chatbot.intents_handler import IntentProcessor
from app.com.chatbot.integrations.whatsapp import WhatsAppHandler
from app.com.chatbot.workflow.common import finalizar_creacion_perfil
from app.com.utils.cv_generator.cv_generator import CVGenerator

# Mock data for testing
TEST_USER_ID = 'test_user_123'
TEST_PLATFORM = 'whatsapp'
TEST_MESSAGE = 'Hello, I am looking for a job.'

@pytest.fixture
def client():
    return Client()

@pytest.fixture
def chat_state_manager():
    return ChatStateManager()

@pytest.fixture
def personality_analyzer():
    return PersonalityAnalyzer()

@pytest.mark.django_db
class TestChatbotWorkflow:
    def test_initial_message_handling(self, client):
        """Test if the chatbot handles initial messages correctly."""
        response = client.post(f'/chatbot/{TEST_PLATFORM}/', 
                              {'user_id': TEST_USER_ID, 'message': TEST_MESSAGE},
                              content_type='application/json')
        assert response.status_code == 200
        assert 'response' in response.json()
        assert 'state' in response.json()

    def test_state_management(self, chat_state_manager):
        """Test if chat state is managed correctly across interactions."""
        initial_state = chat_state_manager.get_state(TEST_USER_ID, TEST_PLATFORM)
        assert initial_state == 'initial'
        chat_state_manager.update_state(TEST_USER_ID, TEST_PLATFORM, 'awaiting_response')
        updated_state = chat_state_manager.get_state(TEST_USER_ID, TEST_PLATFORM)
        assert updated_state == 'awaiting_response'

    def test_personality_analysis(self, personality_analyzer):
        """Test personality analysis based on user input."""
        analysis_result = personality_analyzer.analyze_text(TEST_MESSAGE)
        assert isinstance(analysis_result, dict)
        assert 'trait' in analysis_result
        assert 'score' in analysis_result

    @pytest.mark.asyncio
    async def test_async_message_processing(self, client):
        """Test asynchronous processing of messages."""
        response = await client.post(f'/chatbot/{TEST_PLATFORM}/', 
                                    {'user_id': TEST_USER_ID, 'message': TEST_MESSAGE},
                                    content_type='application/json')
        assert response.status_code == 200
        assert 'response' in response.json()

    def test_error_handling(self, client):
        """Test error handling for invalid inputs."""
        response = client.post(f'/chatbot/{TEST_PLATFORM}/', 
                              {'user_id': '', 'message': ''},
                              content_type='application/json')
        assert response.status_code == 400
        assert 'error' in response.json()

    @pytest.mark.asyncio
    async def test_initial_message_handling_regular_user():
        """Test the handling of initial messages from a regular user."""
        user = Person(id=1, email="user@example.com")
        bu = BusinessUnit(name="test_bu")
        handler = WhatsAppHandler(user_id="12345", phone_number_id="67890", business_unit=bu)
        
        with patch.object(handler, 'initialize', new=AsyncMock(return_value=True)):
            message = {"from": "12345", "text": {"body": "Hola"}}
            response = await handler.handle_message(message)
            assert response is not None
            assert "response" in response
            assert "Hola" in response.get("response", "")

    @pytest.mark.asyncio
    async def test_state_management_regular_user():
        """Test state initialization and updates for regular user interactions."""
        user = Person(id=1, email="user@example.com")
        bu = BusinessUnit(name="test_bu")
        manager = ChatStateManager(user, bu, channel="whatsapp")
        
        with patch('aioredis.Redis', new=AsyncMock):
            await manager.initialize()
            state = await manager.get_state()
            assert state == "initial"
            
            await manager.update_state("profile_in_progress")
            updated_state = await manager.get_state()
            assert updated_state == "profile_in_progress"

    @pytest.mark.asyncio
    async def test_personality_analysis_regular_user():
        """Test personality analysis processing for regular users."""
        user = Person(id=1, email="user@example.com")
        bu = BusinessUnit(name="test_bu")
        processor = IntentProcessor(user, bu)
        
        with patch.object(processor, '_call_gpt_api', new=AsyncMock(return_value={"personalidad": " extrovertida"})):
            analysis = await processor.analyze_personality("Soy muy sociable y me gusta trabajar en equipo.")
            assert "extrovertida" in analysis.get("personalidad", "")

    @pytest.mark.asyncio
    async def test_async_message_processing_regular_user():
        """Test asynchronous processing of messages for regular users."""
        user = Person(id=1, email="user@example.com")
        bu = BusinessUnit(name="test_bu")
        handler = WhatsAppHandler(user_id="12345", phone_number_id="67890", business_unit=bu)
        
        with patch.object(handler, 'initialize', new=AsyncMock(return_value=True)):
            with patch.object(handler, '_send_response', new=AsyncMock(return_value=True)):
                message = {"from": "12345", "text": {"body": "¿Cómo estás?"}}
                response = await handler.handle_message(message)
                assert response is not None
                assert "response" in response

    @pytest.mark.asyncio
    async def test_error_handling_regular_user():
        """Test error handling during user interaction."""
        user = Person(id=1, email="user@example.com")
        bu = BusinessUnit(name="test_bu")
        handler = WhatsAppHandler(user_id="12345", phone_number_id="67890", business_unit=bu)
        
        with patch.object(handler, 'initialize', new=AsyncMock(side_effect=Exception("Initialization failed"))):
            message = {"from": "12345", "text": {"body": "Hola"}}
            response = await handler.handle_message(message)
            assert response is not None
            assert "error" in response
            assert "Initialization failed" in response.get("error", "")
    
    @pytest.mark.asyncio
    @patch('app.com.utils.cv_generator.cv_generator.CVGenerator.save_cv')
    @patch('os.makedirs')
    @patch('app.com.chatbot.workflow.common.send_message', new=AsyncMock())
    @patch('app.com.chatbot.workflow.common.send_menu', new=AsyncMock())
    @patch('asgiref.sync.sync_to_async', return_value=AsyncMock())
    async def test_cv_and_development_plan_generation(self, mock_sync_to_async, mock_makedirs, mock_save_cv):
        """Test automatic generation of CV and development plan when profile is completed."""
        # Configure mocks
        mock_makedirs.return_value = None
        mock_save_cv.return_value = "/path/to/generated/cv.pdf"
        
        # Create test objects
        persona = MagicMock(spec=Person)
        persona.id = 123
        persona.is_profile_complete.return_value = True
        persona.personality_test = True
        
        unidad_negocio = MagicMock(spec=BusinessUnit)
        unidad_negocio.name = "huntRED®"
        
        estado_chat = MagicMock(spec=ChatState)
        estado_chat.context = {}
        
        # Test with ML features enabled
        with patch('django.conf.settings.ENABLE_ML_FEATURES', True):
            # Call function
            await finalizar_creacion_perfil("whatsapp", "525518490291", unidad_negocio, estado_chat, persona)
            
            # Verify CV was generated
            assert mock_save_cv.call_count >= 1, "CV generator should be called at least once"
            
            # Check context was updated
            assert "generated_cv_path" in estado_chat.context, "CV path should be added to chat context"
            
            # For personality test users with ML enabled, we should generate the development plan
            cv_paths = [call_args[0][1] for call_args in mock_save_cv.call_args_list]
            assert any("cv_plan" in path for path in cv_paths), "Development plan should be generated for users with personality test"
    
    @pytest.mark.asyncio
    @patch('app.com.utils.cv_generator.cv_generator.CVGenerator.save_cv')
    @patch('os.makedirs')
    @patch('app.com.chatbot.workflow.common.send_message', new=AsyncMock())
    @patch('app.com.chatbot.workflow.common.send_menu', new=AsyncMock())
    @patch('asgiref.sync.sync_to_async', return_value=AsyncMock())
    async def test_cv_generation_without_development_plan(self, mock_sync_to_async, mock_makedirs, mock_save_cv):
        """Test generation of CV without development plan when profile is completed but no personality test."""
        # Configure mocks
        mock_makedirs.return_value = None
        mock_save_cv.return_value = "/path/to/generated/cv.pdf"
        
        # Create test objects
        persona = MagicMock(spec=Person)
        persona.id = 123
        persona.is_profile_complete.return_value = True
        persona.personality_test = False
        
        unidad_negocio = MagicMock(spec=BusinessUnit)
        unidad_negocio.name = "huntRED®"
        
        estado_chat = MagicMock(spec=ChatState)
        estado_chat.context = {}
        
        # Test with ML features enabled but no personality test
        with patch('django.conf.settings.ENABLE_ML_FEATURES', True):
            # Call function
            await finalizar_creacion_perfil("whatsapp", "12345", unidad_negocio, estado_chat, persona)
            
            # Verify only basic CV was generated
            assert mock_save_cv.call_count == 1, "Only basic CV should be generated"
            
            # Check context was updated with only CV path
            assert "generated_cv_path" in estado_chat.context, "CV path should be added to chat context"
            assert "generated_cv_plan_path" not in estado_chat.context, "Plan path should not be added when no personality test"
