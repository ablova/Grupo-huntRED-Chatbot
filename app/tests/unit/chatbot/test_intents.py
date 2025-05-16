"""
Tests unitarios para el manejo de intenciones del chatbot
Ubicación: /app/tests/unit/chatbot/test_intents.py
Responsabilidad: Verificación de funcionalidad del manejo de intenciones

Created: 2025-05-15
Updated: 2025-05-15
"""

import pytest
from app.com.chatbot.core.intents.handler import IntentHandler
from app.com.models import Company

def test_process_intent_proposal_request():
    """Test para procesamiento de solicitud de propuesta"""
    handler = IntentHandler()
    message = "Quiero una propuesta para mi empresa"
    response = handler.process_intent(message, 'whatsapp')
    assert 'propuesta' in response.lower()

def test_process_intent_contract_request():
    """Test para procesamiento de solicitud de contrato"""
    handler = IntentHandler()
    message = "Necesito un contrato para mis servicios"
    response = handler.process_intent(message, 'whatsapp')
    assert 'contrato' in response.lower()

def test_rate_limiting():
    """Test para verificación de límite de tasa"""
    handler = IntentHandler()
    message = "Prueba de límite de tasa"
    
    # Primera llamada
    handler.process_intent(message, 'whatsapp')
    
    # Segunda llamada inmediata
    with pytest.raises(RateLimitError):
        handler.process_intent(message, 'whatsapp')
