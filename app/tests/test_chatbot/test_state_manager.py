# /home/pablo/app/tests/test_chatbot/test_state_manager.py
#
# Implementación para el módulo. Proporciona funcionalidad específica del sistema.

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.ats.chatbot.components.chat_state_manager import ChatStateManager
from app.models import Person, BusinessUnit, ChatState
from app.ats.chatbot.workflow.common import get_workflow_context

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
    with patch('app.ats.chatbot.chat_state_manager.get_redis_connection') as mock:
        mock.return_value = mock_redis
        yield mock

@pytest.fixture
def state_manager(mock_person, mock_business_unit, mock_get_redis_connection):
    return ChatStateManager(mock_person, mock_business_unit, 'whatsapp')

@pytest.fixture
def chat_state_manager():
    return ChatStateManager()

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

@pytest.mark.asyncio
async def test_get_state_success(chat_state_manager):
    # Test successful state retrieval
    with patch.object(chat_state_manager.redis_client, 'get', return_value=b'{"key": "value"}') as mock_get:
        state = await chat_state_manager.get_state('chat123')
        assert state == {"key": "value"}
        mock_get.assert_called_once_with('chat:state:chat123')

@pytest.mark.asyncio
async def test_get_state_not_found(chat_state_manager):
    # Test state retrieval when no state exists
    with patch.object(chat_state_manager.redis_client, 'get', return_value=None) as mock_get:
        state = await chat_state_manager.get_state('chat123')
        assert state == {}
        mock_get.assert_called_once_with('chat:state:chat123')

@pytest.mark.asyncio
async def test_save_state_success(chat_state_manager):
    # Test successful state saving
    with patch.object(chat_state_manager.redis_client, 'set', return_value=True) as mock_set:
        result = await chat_state_manager.save_state('chat123', {'key': 'value'})
        assert result is True
        mock_set.assert_called_once()

@pytest.mark.asyncio
async def test_save_state_failure(chat_state_manager):
    # Test state saving failure
    with patch.object(chat_state_manager.redis_client, 'set', side_effect=Exception('Redis error')) as mock_set:
        result = await chat_state_manager.save_state('chat123', {'key': 'value'})
        assert result is False
        mock_set.assert_called_once()

@pytest.mark.asyncio
async def test_delete_state_success(chat_state_manager):
    # Test successful state deletion
    with patch.object(chat_state_manager.redis_client, 'delete', return_value=1) as mock_delete:
        result = await chat_state_manager.delete_state('chat123')
        assert result is True
        mock_delete.assert_called_once_with('chat:state:chat123')

@pytest.mark.asyncio
async def test_delete_state_failure(chat_state_manager):
    # Test state deletion failure
    with patch.object(chat_state_manager.redis_client, 'delete', side_effect=Exception('Redis error')) as mock_delete:
        result = await chat_state_manager.delete_state('chat123')
        assert result is False
        mock_delete.assert_called_once_with('chat:state:chat123')

@pytest.mark.asyncio
async def test_redis_retry_mechanism(chat_state_manager):
    # Test retry mechanism on Redis connection failure
    with patch.object(chat_state_manager, '_connect_redis', side_effect=[Exception('Connection failed'), MagicMock()]):
        await chat_state_manager._ensure_connection()
        assert chat_state_manager.redis_client is not None
