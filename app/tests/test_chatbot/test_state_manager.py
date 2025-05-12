# /home/pablo/app/tests/test_chatbot/test_state_manager.py
#
# Implementación para el módulo. Proporciona funcionalidad específica del sistema.

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.com.chatbot.chat_state_manager import ChatStateManager
from app.models import Person, BusinessUnit, ChatState
from app.com.chatbot.workflow.common import get_workflow_context

@pytest.fixture
def mock_person():
    person = MagicMock(spec=Person)
    person.id = 1
    return person

@pytest.fixture
def mock_business_unit():
    bu = MagicMock(spec=BusinessUnit)
    bu.id = 1
    return bu

@pytest.fixture
def mock_redis():
    redis = AsyncMock()
    redis.get.return_value = None
    redis.setex.return_value = None
    return redis

@pytest.fixture
def mock_get_redis_connection(mock_redis):
    with patch('app.chatbot.chat_state_manager.get_redis_connection') as mock:
        mock.return_value = mock_redis
        yield mock

@pytest.fixture
def state_manager(mock_person, mock_business_unit, mock_get_redis_connection):
    return ChatStateManager(mock_person, mock_business_unit, 'whatsapp')

@pytest.mark.asyncio
async def test_initialize(state_manager, mock_redis):
    # Test cache miss
    await state_manager.initialize()
    mock_redis.get.assert_called_once()
    mock_redis.setex.assert_called_once()

@pytest.mark.asyncio
async def test_update_state(state_manager, mock_redis):
    # Test successful state update
    result = await state_manager.update_state('NEW_STATE', 'TEST_INTENT')
    assert result is True
    assert state_manager.current_state == 'NEW_STATE'
    assert state_manager.last_intent == 'TEST_INTENT'
    
    # Test error handling
    mock_redis.setex.side_effect = Exception('Redis error')
    result = await state_manager.update_state('ERROR_STATE')
    assert result is False

@pytest.mark.asyncio
async def test_context_management(state_manager, mock_redis):
    # Test context operations
    await state_manager.set_context('test_key', 'test_value')
    value = await state_manager.get_context('test_key')
    assert value == 'test_value'
    
    # Test context stack
    await state_manager.push_context({'new_key': 'new_value'})
    await state_manager.pop_context()
    assert await state_manager.get_context('test_key') == 'test_value'

@pytest.mark.asyncio
async def test_fallback_handling(state_manager, mock_redis):
    # Test fallback mechanism
    state_manager.fallback_states = ['FALLBACK_STATE']
    state_manager.error_count = 3
    
    await state_manager.update_state('ERROR_STATE')
    assert state_manager.current_state == 'FALLBACK_STATE'
    assert state_manager.error_count == 0

@pytest.mark.asyncio
async def test_metrics_tracking(state_manager, mock_redis):
    # Test metrics tracking
    await state_manager.update_state('TEST_STATE', 'TEST_INTENT')
    assert state_manager.metrics.get('state_transitions') == 1
    assert state_manager.metrics.get('intent_TEST_INTENT') == 1

    # Test context metrics
    await state_manager.get_context('nonexistent_key')
    await state_manager.set_context('existing_key', 'value')
    assert state_manager.metrics.get('context_misses') == 1
    assert state_manager.metrics.get('context_hits') == 1
