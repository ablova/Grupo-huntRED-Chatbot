# /home/amigro/app/tests.py

from django.test import TestCase
from django.urls import reverse
from app.models import Pregunta, ChatState, FlowModel
from app.chatbot import ChatBotHandler
import json

class FlowFunctionsTests(TestCase):
    def setUp(self):
        self.flow = FlowModel.objects.create(name='Flujo de Prueba', description='Descripción del flujo de prueba')

    def test_load_flow_data(self):
        response = self.client.get(reverse('load_flow_data', args=[self.flow.id]))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('flow_data', data)

    def test_export_chatbot_flow(self):
        flow_data = {'nodes': [], 'links': []}
        response = self.client.post(reverse('export_chatbot_flow'), data=json.dumps(flow_data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'exported')

    def test_save_flow_structure(self):
        flow_structure = {'flowmodel_id': self.flow.id, 'nodes': [], 'links': []}
        response = self.client.post(reverse('save_flow_structure'), data=json.dumps(flow_structure), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')

class ChatbotTests(TestCase):    
    def setUp(self):
        self.test_url = reverse('send-test-message')
        self.default_data = {
            'platform': 'whatsapp',
            'functions': ['enviar_logo'],
            'action': 'Sending logo test'
        }

    def test_send_logo_whatsapp(self):
        """
        Test sending the Amigro logo via WhatsApp.
        """
        response = self.client.post(self.test_url, data=json.dumps(self.default_data), content_type='application/json')
        self.assertEqual(response.status_code, 200)

    def test_send_image(self):
        """
        Test sending an image to WhatsApp.
        """
        data = self.default_data
        data['functions'] = ['send_image']
        data['action'] = 'https://amigro.org/registro.png'
        response = self.client.post(self.test_url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        
    def test_send_menu(self):
        """
        Test sending a menu via WhatsApp.
        """
        data = self.default_data
        data['functions'] = ['send_menu']
        response = self.client.post(self.test_url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)

    def test_send_question(self):
        pregunta = Pregunta.objects.create(name="Pregunta de Test", content="Contenido de prueba")
        data = self.default_data.copy()
        data['functions'] = ['send_question']
        data['question_id'] = pregunta.id
        response = self.client.post(self.test_url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)

    def test_enviar_whatsapp_plantilla(self):
        data = self.default_data.copy()
        data['functions'] = ['enviar_whatsapp_plantilla']
        response = self.client.post(self.test_url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)

    def test_mostrar_vacantes(self):
        data = self.default_data.copy()
        data['functions'] = ['mostrar_vacantes']
        response = self.client.post(self.test_url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)

class ProcessMessageTests(TestCase):
    def setUp(self):
        self.handler = ChatBotHandler()
        self.platform = 'whatsapp'
        self.sender_id = '525512345678'
        self.business_unit = None  # Ajusta según tu configuración

    async def test_process_greeting_message(self):
        message = 'Hola'
        response, options = await self.handler.process_message(self.platform, self.sender_id, message, self.business_unit)
        self.assertIsNotNone(response)
        # Puedes añadir más aserciones basadas en la lógica esperada

    async def test_process_unknown_message(self):
        message = 'Mensaje desconocido'
        response, options = await self.handler.process_message(self.platform, self.sender_id, message, self.business_unit)
        self.assertIsNotNone(response)
        # Añade aserciones adicionales si es necesario

class PreguntaCRUDTests(TestCase):
    def setUp(self):
        self.pregunta = Pregunta.objects.create(name="Pregunta Inicial")

    def test_create_pregunta(self):
        response = self.client.post(reverse('create_pregunta'), data=json.dumps({'name': 'Nueva Pregunta'}), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('id', data)
        nueva_pregunta = Pregunta.objects.get(id=data['id'])
        self.assertEqual(nueva_pregunta.name, 'Nueva Pregunta')

    def test_update_pregunta(self):
        update_data = {'name': 'Pregunta Actualizada'}
        response = self.client.put(reverse('update_pregunta', args=[self.pregunta.id]), data=json.dumps(update_data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.pregunta.refresh_from_db()
        self.assertEqual(self.pregunta.name, 'Pregunta Actualizada')

    def test_delete_pregunta(self):
        response = self.client.delete(reverse('delete_pregunta', args=[self.pregunta.id]))
        self.assertEqual(response.status_code, 200)
        with self.assertRaises(Pregunta.DoesNotExist):
            Pregunta.objects.get(id=self.pregunta.id)