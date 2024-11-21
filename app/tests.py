# /home/amigro/app/tests.py

from django.test import TestCase
from django.urls import reverse
from app.models import Pregunta, ChatState, FlowModel, Configuracion, BusinessUnit, ConfiguracionBU
import json
import logging

# Configuración del logger para pruebas
logger = logging.getLogger(__name__)
handler = logging.FileHandler('/home/amigro/logs/tests.log')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

class BaseTestCase(TestCase):
    """
    Clase base para centralizar configuraciones generales.
    """
    @classmethod
    def setUpTestData(cls):
        cls.configuracion = Configuracion.objects.create()
        cls.business_unit = BusinessUnit.objects.create(name="amigro", description="Unidad de negocio Amigro®")
        cls.configuracion_bu = ConfiguracionBU.objects.create(business_unit=cls.business_unit)
        cls.default_flow = FlowModel.objects.create(name="Flujo Default", description="Flujo utilizado en pruebas")
        logger.info("Configuraciones iniciales creadas para las pruebas.")

class FlowFunctionsTests(BaseTestCase):
    def setUp(self):
        self.flow = FlowModel.objects.create(name='Flujo de Prueba', description='Descripción del flujo de prueba')
        logger.info("Configuración inicial para pruebas de FlowFunctions.")

    def test_load_flow_data(self):
        response = self.client.get(reverse('load_flow_data', args=[self.flow.id]))
        logger.debug(f"Probando carga de datos para flujo ID {self.flow.id}. Status: {response.status_code}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('flow_data', data)

    def test_export_chatbot_flow(self):
        flow_data = {'nodes': [], 'links': []}
        response = self.client.post(reverse('export_chatbot_flow'), data=json.dumps(flow_data), content_type='application/json')
        logger.debug(f"Probando exportación de flujo. Status: {response.status_code}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'exported')

    def test_save_flow_structure(self):
        flow_structure = {'flowmodel_id': self.flow.id, 'nodes': [], 'links': []}
        response = self.client.post(reverse('save_flow_structure'), data=json.dumps(flow_structure), content_type='application/json')
        logger.debug(f"Probando guardar estructura del flujo. Status: {response.status_code}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')

class ChatbotTests(BaseTestCase):
    def setUp(self):
        self.test_url = reverse('send-test-message')
        self.default_data = {
            'platform': self.configuracion.default_platform,
            'functions': ['enviar_logo'],
            'action': 'Sending logo test',
            'phone_number': self.configuracion.test_phone_number
        }
        logger.info("Configuración inicial para pruebas de Chatbot.")

    def test_send_logo_whatsapp(self):
        response = self.client.post(self.test_url, data=json.dumps(self.default_data), content_type='application/json')
        logger.debug(f"Enviando logo a WhatsApp. Status: {response.status_code}")
        self.assertEqual(response.status_code, 200)

    def test_send_image(self):
        data = self.default_data.copy()
        data['functions'] = ['send_image']
        data['action'] = 'https://amigro.org/registro.png'
        response = self.client.post(self.test_url, data=json.dumps(data), content_type='application/json')
        logger.debug(f"Enviando imagen a WhatsApp. Status: {response.status_code}")
        self.assertEqual(response.status_code, 200)

    def test_send_question(self):
        pregunta = Pregunta.objects.create(name="Pregunta de Test", content="Contenido de prueba")
        data = self.default_data.copy()
        data['functions'] = ['send_question']
        data['question_id'] = pregunta.id
        response = self.client.post(self.test_url, data=json.dumps(data), content_type='application/json')
        logger.debug(f"Enviando pregunta ID {pregunta.id}. Status: {response.status_code}")
        self.assertEqual(response.status_code, 200)

class PreguntaCRUDTests(BaseTestCase):
    def setUp(self):
        self.pregunta = Pregunta.objects.create(name="Pregunta Inicial")
        logger.info("Configuración inicial para pruebas CRUD de Pregunta.")

    def test_create_pregunta(self):
        response = self.client.post(reverse('create_pregunta'), data=json.dumps({'name': 'Nueva Pregunta'}), content_type='application/json')
        logger.debug(f"Creando pregunta. Status: {response.status_code}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        nueva_pregunta = Pregunta.objects.get(id=data['id'])
        self.assertEqual(nueva_pregunta.name, 'Nueva Pregunta')

    def test_update_pregunta(self):
        update_data = {'name': 'Pregunta Actualizada'}
        response = self.client.put(reverse('update_pregunta', args=[self.pregunta.id]), data=json.dumps(update_data), content_type='application/json')
        logger.debug(f"Actualizando pregunta ID {self.pregunta.id}. Status: {response.status_code}")
        self.assertEqual(response.status_code, 200)
        self.pregunta.refresh_from_db()
        self.assertEqual(self.pregunta.name, 'Pregunta Actualizada')

    def test_delete_pregunta(self):
        response = self.client.delete(reverse('delete_pregunta', args=[self.pregunta.id]))
        logger.debug(f"Borrando pregunta ID {self.pregunta.id}. Status: {response.status_code}")
        self.assertEqual(response.status_code, 200)
        with self.assertRaises(Pregunta.DoesNotExist):
            Pregunta.objects.get(id=self.pregunta.id)