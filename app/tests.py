# Ubicación: /home/pablollh/app/tests.py

from django.test import TestCase, Client
from unittest.mock import patch
from app.models import BusinessUnit
from app.chatbot import ChatBotHandler

class ChatbotTestCase(TestCase):
    def setUp(self):
        self.business_unit = BusinessUnit.objects.create(name='amigro')
        self.handler = ChatBotHandler()
        self.client = Client()

    @patch('app.chatbot.ChatBotHandler.generate_dynamic_response', return_value="Respuesta de prueba GPT")
    def test_process_message_no_known_intents(self, mock_gpt):
        # Simula un mensaje sin intención conocida
        response = self.client.post('/test_interaction/', data={'user_id': '5215512345678', 'message': 'Hola, necesito ayuda'}, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('success', response.json()['status'])

    @patch('app.chatbot.ChatBotHandler.generate_dynamic_response', return_value="Respuesta GPT")
    def test_process_message_saludo_intent(self, mock_gpt):
        # Simula un saludo conocido
        with patch('app.utils.analyze_text', return_value={"intents":["saludo"], "entities":[],"sentiment":{}}):
            response = self.client.post('/test_interaction/', data={'user_id': '5215512345678', 'message': 'Hola'}, content_type='application/json')
            self.assertEqual(response.status_code, 200)
            # Debe haber respondido con un saludo sin necesitar GPT
            # Como no mockeamos send_message, no assertamos el contenido, 
            # solo el status_code y el success.