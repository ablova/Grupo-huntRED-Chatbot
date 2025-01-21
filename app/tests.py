# Ubicación: /home/pablollh/app/tests.py

import pytest
from datetime import datetime, timedelta
from django.test import TestCase, Client, override_settings
from unittest.mock import patch, MagicMock
from app.models import BusinessUnit, Person, ChatState, GptApi
from app.chatbot.chatbot import ChatBotHandler
from app.chatbot.gpt import GPTHandler
from app.chatbot.nlp import NLPProcessor
from app.chatbot.utils import fetch_data_from_url, validate_request_data
from app.utilidades.vacantes import VacanteManager, procesar_vacante
from django.db import connections


@override_settings(DEBUG=True)
class ChatbotTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.clean_test_database()

    @classmethod
    def tearDownClass(cls):
        cls.clean_test_database()
        for conn in connections.all():
            conn.close()
        super().tearDownClass()

    @staticmethod
    def clean_test_database():
        """Limpia todas las tablas de la base de datos de pruebas."""
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SET CONSTRAINTS ALL DEFERRED;")
            cursor.execute(
                """
                DO $$
                DECLARE
                    r RECORD;
                BEGIN
                    FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
                        EXECUTE 'TRUNCATE TABLE ' || quote_ident(r.tablename) || ' CASCADE;';
                    END LOOP;
                END $$;
                """
            )

    def setUp(self):
        """Configuración inicial"""
        self.client = Client()

        # Configuración de Business Unit y usuario
        self.business_unit = BusinessUnit.objects.create(
            name="amigro",
            admin_phone="525518490291"
        )
        self.person = Person.objects.create(
            nombre="Test User",
            phone="525518490291",
            email="test@huntred.com"
        )
        self.chat_state = ChatState.objects.create(
            user_id=self.person.phone,
            platform="whatsapp",
            business_unit=self.business_unit,
            person=self.person
        )

        # Configuración de JWT para el REST API
        self.jwt_token = "test_jwt_token"
        self.business_unit.jwt = self.jwt_token
        self.business_unit.save()

        self.handler = ChatBotHandler()

    # Prueba para fetch_data_from_url con REST API
    @patch("app.chatbot.utils.requests.get")
    def test_fetch_data_from_rest_api(self, mock_get):
        """Prueba la obtención de vacantes desde el REST API de WordPress con JWT"""
        # Mockear la respuesta del API
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = [
            {"id": 1, "title": {"rendered": "Vacante Test 1"}},
            {"id": 2, "title": {"rendered": "Vacante Test 2"}}
        ]

        # Endpoint del REST API
        url = "https://amigro.org/wp-json/wp/v2/vacantes"

        # Llamar a fetch_data_from_url con JWT
        headers = {"Authorization": f"Bearer {self.jwt_token}"}
        data = fetch_data_from_url(url, headers=headers)

        # Verificar resultados
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["title"]["rendered"], "Vacante Test 1")

    @patch("app.chatbot.utils.requests.get")
    def test_fetch_data_with_invalid_jwt(self, mock_get):
        """Prueba el manejo de errores con JWT inválido"""
        # Mockear respuesta de error
        mock_get.return_value.status_code = 401
        mock_get.return_value.json.return_value = {"message": "Invalid token"}

        # Endpoint del REST API
        url = "https://amigro.org/wp-json/wp/v2/vacantes"

        # Llamar a fetch_data_from_url con JWT inválido
        headers = {"Authorization": "Bearer invalid_jwt_token"}
        data = fetch_data_from_url(url, headers=headers)

        # Verificar que se maneje correctamente el error
        self.assertIsInstance(data, dict)
        self.assertIn("message", data)
        self.assertEqual(data["message"], "Invalid token")

    # Pruebas adicionales para chatbot.py
    def test_handle_known_intents(self):
        """Prueba el manejo de intenciones conocidas"""
        response = self.handler.handle_known_intents(
            intents=["saludo"],
            platform="whatsapp",
            user_id=self.person.phone,
            chat_state=self.chat_state,
            business_unit=self.business_unit
        )
        self.assertIsNotNone(response)

    def test_chatbot_response_flow(self):
        """Prueba el flujo completo de respuestas del chatbot"""
        response = self.client.post(
            "/test_interaction/",
            data={"user_id": self.person.phone, "message": "Hola"},
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("success", response.json())

    # Pruebas para gpt.py
    @patch("app.chatbot.gpt.OpenAI")
    def test_gpt_handler_response(self, mock_openai):
        """Prueba la respuesta generada por GPTHandler"""
        mock_openai.return_value.chat.completions.create.return_value = {
            "choices": [{"message": {"content": "París"}}]
        }
        gpt_handler = GPTHandler()
        response = gpt_handler.generate_response("¿Cuál es la capital de Francia?")
        self.assertIn("París", response)

    def test_gpt_handler_error_handling(self):
        """Prueba el manejo de errores en GPTHandler"""
        with self.assertRaises(ValueError):
            GPTHandler()

    # Pruebas para nlp.py
    def test_nlp_intent_recognition(self):
        """Prueba la detección de intenciones"""
        nlp_processor = NLPProcessor()
        intents = nlp_processor.extract_intents("Quiero buscar trabajo")
        self.assertIn("buscar_trabajo", intents)

    def test_nlp_gender_inference(self):
        """Prueba la inferencia de género"""
        nlp_processor = NLPProcessor()
        gender = nlp_processor.infer_gender("Maria")
        self.assertEqual(gender, "F")

@pytest.fixture
def mock_job_data():
    return {
        "business_unit": "huntRED",
        "job_title": "Desarrollador Backend",
        "job_description": "Desarrollo en Python y ML.",
        "company_name": "huntRED Technologies",
        "celular_responsable": "525512345678",
        "job_employee-email": "responsable@huntred.com"
    }

def test_generate_bookings():
    start_date = datetime.now() + timedelta(days=15)
    session_duration = 45
    bookings = VacanteManager.generate_bookings(start_date, session_duration)
    assert len(bookings) == 6  # Asegúrate de que se generen 6 horarios
    assert bookings[0].endswith("09:00")  # Comienza a las 9:00
    assert bookings[-1].endswith("14:00")  # Termina antes de las 14:00

def test_create_job_listing(mock_job_data):
    manager = VacanteManager(job_data=mock_job_data)
    result = manager.create_job_listing()
    assert result["status"] == "success"