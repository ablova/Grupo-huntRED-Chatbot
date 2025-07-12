# /home/pablo/app/tests/test_chatbot/test_conversational_flow.py
#
# Implementación para el módulo. Proporciona funcionalidad específica del sistema.

import pytest
from unittest.mock import patch, Mock
from app.ats.chatbot.flow.conversational_flow import ConversationalFlowManager
from app.models import Person, BusinessUnit, IntentPattern, StateTransition, ChatState

def create_test_data():
    # Crear datos de prueba
    business_unit = BusinessUnit.objects.create(name="test_bu")
    person = Person.objects.create(nombre="Test")
    
    # Crear patrones de intent
    intent1 = IntentPattern.objects.create(
        name="greeting",
        patterns="hola\nhi",
        business_units=business_unit
    )
    
    # Crear transiciones de estado
    StateTransition.objects.create(
        current_state="initial",
        next_state="greeting",
        business_unit=business_unit
    )
    
    return business_unit, person

@pytest.fixture
def flow_manager():
    business_unit, person = create_test_data()
    return ConversationalFlowManager(business_unit)

def test_process_message_success(flow_manager):
    """Test que verifica el procesamiento exitoso de un mensaje"""
    person = Person.objects.first()
    response = flow_manager.process_message(person, "hola")
    
    assert response["success"] is True
    assert response["current_state"] == "greeting"

def test_process_message_invalid_intent(flow_manager):
    """Test que verifica el manejo de intents inválidos"""
    person = Person.objects.first()
    response = flow_manager.process_message(person, "mensaje_invalido")
    
    assert response["success"] is False
    assert "error" in response

def test_context_conditions(flow_manager):
    """Test que verifica el manejo de condiciones de contexto"""
    person = Person.objects.first()
    
    # Establecer contexto
    chat_state = ChatState.objects.create(
        person=person,
        business_unit=flow_manager.business_unit,
        state="initial"
    )
    chat_state.context = {"has_profile": True}
    chat_state.save()
    
    # Intento que requiere contexto
    intent = IntentPattern.objects.create(
        name="profile",
        patterns="mi perfil",
        business_units=flow_manager.business_unit
    )
    
    response = flow_manager.process_message(person, "mi perfil")
    assert response["success"] is True
    
    # Intento sin contexto requerido
    response = flow_manager.process_message(person, "otro mensaje")
    assert response["success"] is False
    assert "required_context" in response
