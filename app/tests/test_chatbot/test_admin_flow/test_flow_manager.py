# /home/pablo/app/tests/test_chatbot/test_admin_flow/test_flow_manager.py
#
# Implementación para el módulo. Proporciona funcionalidad específica del sistema.

import unittest
from unittest.mock import patch, MagicMock
from app.ats.chatbot.admin.flow_manager import FlowManager
from app.models import ChatState

class TestFlowManager(unittest.TestCase):
    def setUp(self):
        self.flow_manager = FlowManager()
        self.chat_state = ChatState(
            id=1,
            person_id=1,
            vacancy_id=1,
            current_state="start",
            data={"steps": []}
        )

    def test_start_flow(self):
        """Test de inicio de flujo"""
        with patch('app.ats.chatbot.admin.flow_manager.ChatState.save') as mock_save:
            self.flow_manager.start_flow(self.chat_state)
            mock_save.assert_called()

    def test_next_step(self):
        """Test de paso siguiente"""
        with patch('app.ats.chatbot.admin.flow_manager.ChatState.save') as mock_save:
            self.flow_manager.next_step(self.chat_state)
            mock_save.assert_called()

    def test_complete_flow(self):
        """Test de finalización de flujo"""
        with patch('app.ats.chatbot.admin.flow_manager.ChatState.save') as mock_save:
            self.flow_manager.complete_flow(self.chat_state)
            mock_save.assert_called()

    def test_error_handling(self):
        """Test de manejo de errores"""
        with patch('app.ats.chatbot.admin.flow_manager.logger.error') as mock_error:
            self.flow_manager.handle_error(self.chat_state, "Test error")
            mock_error.assert_called()

    def test_state_validation(self):
        """Test de validación de estados"""
        valid = self.flow_manager.validate_state(self.chat_state, "start")
        self.assertTrue(valid)
        
        invalid = self.flow_manager.validate_state(self.chat_state, "invalid_state")
        self.assertFalse(invalid)

if __name__ == '__main__':
    unittest.main()
