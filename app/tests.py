# /home/pablo/app/tests.py
#
# Pruebas para el módulo. Verifica la correcta funcionalidad de componentes específicos.

import pytest
import asyncio
from datetime import datetime, timedelta
from django.test import TestCase, Client, override_settings
from unittest.mock import patch, MagicMock, AsyncMock
from app.models import BusinessUnit, Person, ChatState, GptApi
from app.ats.chatbot.core.chatbot import ChatBotHandler
from app.ats.chatbot.core.gpt import GPTHandler
from app.ats.chatbot.utils.chatbot_utils import ChatbotUtils
get_nlp_processor = ChatbotUtils.get_nlp_processor  # Reemplazar importación
from app.ats.chatbot.utils import fetch_data_from_url, validate_request_data
from app.ats.utils.vacantes import VacanteManager, procesar_vacante
from django.db import connections
from app.tasks import send_whatsapp_message_task, train_ml_task, ejecutar_scraping

# Marcar el módulo como compatible con asyncio
pytestmark = pytest.mark.asyncio

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

    # Pruebas para fetch_data_from_url con REST API
    @patch("app.ats.chatbot.utils.requests.get")
    def test_fetch_data_from_rest_api(self, mock_get):
        """Prueba la obtención de vacantes desde el REST API de WordPress con JWT"""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = [
            {"id": 1, "title": {"rendered": "Vacante Test 1"}},
            {"id": 2, "title": {"rendered": "Vacante Test 2"}}
        ]
        url = "https://amigro.org/wp-json/wp/v2/vacantes"
        headers = {"Authorization": f"Bearer {self.jwt_token}"}
        data = fetch_data_from_url(url, headers=headers)
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["title"]["rendered"], "Vacante Test 1")

    @patch("app.ats.chatbot.utils.requests.get")
    def test_fetch_data_with_invalid_jwt(self, mock_get):
        """Prueba el manejo de errores con JWT inválido"""
        mock_get.return_value.status_code = 401
        mock_get.return_value.json.return_value = {"message": "Invalid token"}
        url = "https://amigro.org/wp-json/wp/v2/vacantes"
        headers = {"Authorization": "Bearer invalid_jwt_token"}
        data = fetch_data_from_url(url, headers=headers)
        self.assertIsInstance(data, dict)
        self.assertIn("message", data)
        self.assertEqual(data["message"], "Invalid token")

    # Pruebas para chatbot.py
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
    @patch("app.ats.chatbot.core.gpt.OpenAI")
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

    # Pruebas para tareas Celery
    @patch("app.tasks.send_message")
    def test_send_whatsapp_message_task(self, mock_send_message):
        """Prueba la ejecución de la tarea Celery para enviar mensajes de WhatsApp."""
        mock_send_message.return_value = True
        result = send_whatsapp_message_task("525518490291", "Hola")
        self.assertIsNone(result)

    @patch("app.tasks.GrupohuntREDMLPipeline.train")
    def test_train_ml_task(self, mock_train):
        """Prueba la ejecución de la tarea Celery para entrenar modelos de Machine Learning."""
        mock_train.return_value = None
        result = train_ml_task()
        self.assertIsNone(result)

    @patch("app.tasks.run_scraper")
    def test_ejecutar_scraping(self, mock_scraper):
        """Prueba la ejecución del scraper desde Celery."""
        mock_scraper.return_value = []
        result = ejecutar_scraping()
        self.assertIsNone(result)

# Pruebas independientes con pytest
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

# Pruebas asíncronas para VacanteManager
@pytest.mark.asyncio
async def test_create_job_listing(mock_job_data):
    configuracion = type("Config", (), {"business_unit": type("Unit", (), {"name": "huntred"})})()
    manager = VacanteManager(mock_job_data, configuracion)
    with patch('app.utilidades.vacantes.sync_to_async', new_callable=AsyncMock) as mock_sync_to_async:
        with patch('app.utilidades.vacantes.aiohttp.ClientSession.post', new_callable=AsyncMock) as mock_post:
            mock_sync_to_async.return_value = None
            mock_post.return_value.status = 201
            await manager.initialize()
            result = await manager.create_job_listing()
            assert result["status"] == "success"
            assert "Vacante creada y notificaciones enviadas" in result["message"]

@pytest.mark.asyncio
async def test_wordpress_failure(mock_job_data):
    configuracion = type("Config", (), {"business_unit": type("Unit", (), {"name": "huntred"})})()
    manager = VacanteManager(mock_job_data, configuracion)
    with patch('app.utilidades.vacantes.sync_to_async', new_callable=AsyncMock) as mock_sync_to_async:
        with patch('app.utilidades.vacantes.aiohttp.ClientSession.post', new_callable=AsyncMock) as mock_post:
            mock_sync_to_async.return_value = None
            mock_post.side_effect = Exception("Error en WordPress")
            await manager.initialize()
            result = await manager.create_job_listing()
            assert result["status"] == "success"
            assert "Vacante publicada localmente" in result["message"]

if __name__ == "__main__":
    unittest.main()


# test_nlp.py
import unittest
import os
from app.ats.chatbot.extractors import ESCOExtractor, NICEExtractor, unify_data
from app.ats.chatbot.nlp.nlp import SkillExtractionPipeline, SkillExtractorManager

class TestNLPIntegration(unittest.TestCase):
    def test_esco_and_nice_integration(self):
        esco_ext = ESCOExtractor()
        nice_ext = NICEExtractor()
        
        # Obtener datos de ESCO y NICE
        esco_skills_data = esco_ext.get_skills(language="es", limit=2)
        nice_data = nice_ext.get_skills(sheet_name="Skills")

        # Verificar que no estén vacíos
        self.assertIsNotNone(esco_skills_data, "ESCO data is None")
        self.assertIsNotNone(nice_data, "NICE data is None")

        # Unificar
        unified_data = unify_data(esco_skills_data, nice_data)
        self.assertTrue(len(unified_data) > 0, "No se unificó ningún dato")

        # Probar pipeline básico
        pipeline = SkillExtractionPipeline()
        example_text = "Busco a alguien con Python y Django."
        extracted_skills = pipeline.extract_skills(example_text)
        # No sabemos con certeza qué detecta, pero al menos no debe dar error
        self.assertIsInstance(extracted_skills, list)

        # Probar extractor avanzado
        advanced_extractor = SkillExtractorManager.get_instance("es")
        result = advanced_extractor.extract_skills(example_text)
        self.assertIn("skills", result)
        self.assertIsInstance(result["skills"], list)
        print("Prueba completada con éxito:", result["skills"])

if __name__ == "__main__":
    unittest.main()

