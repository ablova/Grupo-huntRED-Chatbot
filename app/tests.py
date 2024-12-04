# /home/amigro/app/tests.py

import json
import pytest
import requests
from unittest.mock import patch, AsyncMock
from django.urls import reverse
from django.http import HttpResponse
from django.contrib.auth.models import User
from app.models import (
    Etapa, Pregunta, Person, WhatsAppAPI, MetaAPI, FlowModel, ChatState,
    BusinessUnit, Configuracion, ConfiguracionBU
)
from app.chatbot import ChatBotHandler
from app.vacantes import VacanteManager
from app.integrations.whatsapp import handle_incoming_message, registro_amigro, nueva_posicion_amigro, send_message
from app.tasks import send_whatsapp_message
from asgiref.sync import sync_to_async

# Configuración del logger para pruebas
import logging
logger = logging.getLogger(__name__)
handler = logging.FileHandler('/home/amigro/logs/tests.log')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

# -----------------------------------
# Fixtures para datos de prueba
# -----------------------------------

WHATSAPP_API_TOKEN="EAAJaOsnq2vgBOxatkizgaMhE6dk4jEtbWchTiuHK7XXDbsZAlekvZCldWTajCXABVAGQW9XUbZAdy6IZBoUqZBctEHm6H5mSfP9nAbQ5dZAPbf9P1WkHh4keLT400yhvvbZAEq34e9dlkIp2RwsPqK9ghG6H244SZAFK4V5Oo7FiDl9DdM5j5EhXCY5biTrn7cmzYwZDZD"
WHATSAPP_PHONE_ID="114521714899382"
WHATSAPP_WABID="104851739211207"
META_APP_ID="662158495636216"
META_APP_SECRET="7732534605ab6a7b96c8e8e81ce02e6b"
META_VERIFY_TOKEN="amigro_secret_token"
WORDPRESS_JWT_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOjEsIm5hbWUiOiJQYWJsbyIsImlhdCI6MTczMTAwNzY0OCwiZXhwIjoxODg4Njg3NjQ4fQ.BQezJzmVVpcaG2ZIbkMagezkt-ORoO5wyrG0odWZrlg"

@pytest.fixture
def business_unit(db):
    return BusinessUnit.objects.create(
        name="amigro",
        description="Unidad de negocio Amigro®",
        whatsapp_enabled=True,
        telegram_enabled=True,
        messenger_enabled=True,
        instagram_enabled=True,
        scrapping_enabled=True
    )

@pytest.fixture
def meta_api(business_unit):
    assert META_APP_ID is not None, "El ID de la aplicación no puede ser nulo"
    assert META_APP_SECRET is not None, "El secreto de la aplicación no puede ser nulo"
    assert META_VERIFY_TOKEN is not None, "El token de verificación no puede ser nulo"
    
    return MetaAPI.objects.create(
        business_unit=business_unit,
        app_id=META_APP_ID,
        app_secret=META_APP_SECRET,
        verify_token=META_VERIFY_TOKEN
    )

@pytest.fixture
def whatsapp_api(business_unit, meta_api):
    return WhatsAppAPI.objects.create(
        business_unit=business_unit,
        name="Amigro® WhatsApp",
        phoneID=WHATSAPP_PHONE_ID,
        api_token=WHATSAPP_API_TOKEN,
        WABID=WHATSAPP_WABID,
        v_api="v21.0",
        meta_api=meta_api,
    )

@pytest.fixture
def configuracion(business_unit):
    return ConfiguracionBU.objects.create(
        business_unit=business_unit,
        jwt_token=WORDPRESS_JWT_TOKEN,
        dominio_bu="https://amigro.org",
        dominio_rest_api="https://amigro.org/wp-json"
    )

@pytest.fixture
def flow_model():
    return FlowModel.objects.create(name="Flujo de Prueba")

@pytest.fixture
def etapa():
    return Etapa.objects.create(nombre="Registro")

@pytest.fixture
def pregunta(flow_model, etapa):
    return Pregunta.objects.create(
        name="¿Cuál es tu nombre?",
        content="Por favor, ingresa tu nombre completo.",
        input_type="text",
        etapa=etapa,
        flow=flow_model
    )

@pytest.fixture
def person():
    return Person.objects.create(
        name="Test User",
        email="testuser@example.com",
        phone="1234567890",
        skills="Python, Django",
        number_interaction="test_user_1"
    )

@pytest.fixture
def chat_state(db, person, flow_model):
    return ChatState.objects.create(
        user_id=person.phone,
        platform="whatsapp",
        current_question=None
    )

# -----------------------------------
# Pruebas de interacción con el chatbot
# -----------------------------------

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_chatbot_interaction(whatsapp_api, flow_model, pregunta, person):
    """
    Simula una interacción con el chatbot a través de WhatsApp.
    """
    # Crear un payload simulado de mensaje entrante
    payload = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {
                                    "from": person.phone,
                                    "text": {
                                        "body": "Hola"
                                    }
                                }
                            ],
                            "metadata": {
                                "phone_number_id": whatsapp_api.phoneID
                            }
                        }
                    }
                ]
            }
        ]
    }

    # Simular la función handle_incoming_message para evitar llamadas reales
    with patch('app.integrations.whatsapp.handle_incoming_message', new_callable=AsyncMock) as mock_handler:
        mock_handler.return_value = HttpResponse(status=200)    

        # Instanciar el cliente de pruebas proporcionado por pytest-django
        from django.test import AsyncClient
        client = AsyncClient()

        # Enviar una solicitud POST al webhook de WhatsApp
        response = await client.post(
            reverse('whatsapp_webhook'),
            data=json.dumps(payload),
            content_type="application/json"
        )

        assert response.status_code == 200
        mock_handler.assert_awaited_once()

# -----------------------------------
# Pruebas de creación de usuarios
# -----------------------------------

@pytest.mark.django_db(transaction=True)
def test_person_creation():
    """
    Verifica que los objetos Person se creen correctamente.
    """
    new_person = Person.objects.create(
        name="New User",
        email="newuser@example.com",
        phone="9876543210",
        skills="Java, Spring",
        number_interaction="test_user_2"
    )
    assert new_person.name == "New User"
    assert new_person.email == "newuser@example.com"
    assert new_person.phone == "9876543210"

# -----------------------------------
# Pruebas del flujo de preguntas
# -----------------------------------

@pytest.mark.django_db(transaction=True)
def test_pregunta_flow(flow_model, pregunta):
    """
    Valida la funcionalidad de las preguntas dentro del flujo.
    """
    assert pregunta.flow == flow_model
    assert pregunta.name == "¿Cuál es tu nombre?"

# -----------------------------------
# Pruebas de scraping y creacion de vacantes
# -----------------------------------

@pytest.mark.django_db(transaction=True)
def test_scraping_vacantes(configuracion):
    """
    Realiza una llamada real a la REST API de WordPress para obtener las vacantes.
    """
    url = f"{configuracion.dominio_rest_api}/wp/v2/job-listings/"
    headers = {
        'Authorization': f'Bearer {configuracion.jwt_token}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'User-Agent': 'AmigroTestClient/1.0'
    }

    response = requests.get(url, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response Text: {response.text}")
    assert response.status_code == 200

@pytest.mark.django_db(transaction=True)
def test_crear_vacante(configuracion):
    """
    Prueba la creación de una vacante real en WordPress.
    """
    url = f"{configuracion.dominio_rest_api}/wp/v2/job-listings/"
    headers = {
        'Authorization': f'Bearer {configuracion.jwt_token}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'User-Agent': 'YourAppName/1.0'
    }

    payload = {
        "title": "Vacante de Prueba",
        "content": "Descripción de la vacante de prueba.",
        "status": "publish",
        # Agrega los campos necesarios
    }

    response = requests.post(url, headers=headers, json=payload)
    assert response.status_code == 201

    vacante = response.json()
    assert vacante['title']['rendered'] == "Vacante de Prueba"
    # Limpia la vacante creada si es necesario
    delete_url = f"{url}{vacante['id']}/?force=true"
    requests.delete(delete_url, headers=headers)


# -----------------------------------
# Pruebas de envío de mensajes
# -----------------------------------

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_enviar_mensaje_whatsapp(whatsapp_api):
    """
    Envía un mensaje real a través de la API de WhatsApp.
    """
    from app.integrations.whatsapp import send_whatsapp_message

    user_id = "525518490291"  # Número de teléfono de prueba en formato internacional

    response = await send_whatsapp_message(
        user_id=user_id,
        message="Mensaje de prueba desde las pruebas automatizadas del sistema de Grupo huntRED mediante pytest.",
        phone_id=whatsapp_api.phoneID
    )

    assert response is not None
    assert 'messages' in response

# -----------------------------------
# Pruebas de funciones del chatbot
# -----------------------------------

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_chatbot_process_message_with_user_and_event(whatsapp_api, flow_model, person):
    """
    Prueba el procesamiento de un mensaje entrante por el chatbot, incluyendo la creación de usuarios y eventos.
    """
    chatbot_handler = ChatBotHandler()
    user_id = "525518490291"  # ID específico para la prueba
    text = "Hola"
    business_unit = whatsapp_api.business_unit

    # Simular análisis de texto
    with patch('app.chatbot.analyze_text', return_value={"intents": ["saludo"]}), \
         patch('app.chatbot.send_message', new_callable=AsyncMock) as mock_send_message:

        # Ejecutar el método a probar
        await chatbot_handler.process_message('whatsapp', user_id, text, business_unit)

        # Verificar que se haya creado el evento
        from app.models import ChatState, Person
        event = await sync_to_async(ChatState.objects.filter(user_id=user_id, platform='whatsapp').first)()
        assert event is not None, "El evento debería haberse creado."

        # Verificar que se haya creado el usuario
        user = await sync_to_async(Person.objects.filter(phone=user_id).first)()
        assert user is not None, "El usuario debería haberse creado."
        assert user.phone == user_id, "El teléfono del usuario debería coincidir."

        # Verificar que el mensaje fue enviado
        mock_send_message.assert_awaited()

# -----------------------------------
# Pruebas de manejo de errores
# -----------------------------------

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_process_invalid_message(whatsapp_api, flow_model, person):
    """
    Verifica que el chatbot maneje correctamente un mensaje vacío.
    """
    chatbot_handler = ChatBotHandler()
    user_id = person.phone
    text = ""  # Mensaje vacío
    business_unit = whatsapp_api.business_unit

    with patch('app.chatbot.send_message', new_callable=AsyncMock) as mock_send_message:
        response, options = await chatbot_handler.process_message('whatsapp', user_id, text, business_unit)

        expected_response = "Para continuar, completa estos datos: name, apellido_paterno, skills, ubicacion, email"
        assert response == expected_response
        mock_send_message.assert_awaited_once_with('whatsapp', user_id, expected_response)

# -----------------------------------
# Pruebas de CRUD de Pregunta
# -----------------------------------

@pytest.mark.django_db(transaction=True)
def test_create_pregunta(client, flow_model):
    """
    Prueba la creación de una nueva pregunta.
    """
    # Crear y autenticar un usuario
    user = User.objects.create_user(username='testuser', password='testpass')
    client.login(username='testuser', password='testpass')

    # Crear una Etapa para asociar con la Pregunta
    etapa = Etapa.objects.create(nombre="Etapa de Prueba")
    # Crear Preguntas para next_si y next_no
    next_si_pregunta = Pregunta.objects.create(
        name="Pregunta Next Si",
        content="Contenido Next Si",
        input_type="text",
        flow=flow_model,
        etapa=etapa
    )

    next_no_pregunta = Pregunta.objects.create(
        name="Pregunta Next No",
        content="Contenido Next No",
        input_type="text",
        flow=flow_model,
        etapa=etapa
    )

    data = {
        "name": "Nueva Pregunta",
        "content": "Contenido de la nueva pregunta",
        "input_type": "text",  # Agrega campos obligatorios adicionales
        "flow": flow_model.id,
        "etapa": etapa.id,
        "active": True,
        "requires_response": True,
        "multi_select": False,
        "action_type": 'none',
        "next_si": next_si_pregunta.id,
        "next_no": next_no_pregunta.id,
    }
    response = client.post(
        reverse('create_pregunta'),
        data=data,
        content_type='application/json'
    )

    print(f"Status Code: {response.status_code}")
    print(f"Response Content: {response.content}")

    assert response.status_code == 200
    response_data = response.json()
    nueva_pregunta = Pregunta.objects.get(id=response_data['id'])
    assert nueva_pregunta.name == "Nueva Pregunta"

# -----------------------------------
# Pruebas adicionales según necesidades
# -----------------------------------
@pytest.mark.django_db(transaction=True)
@ pytest.mark.asyncio
async def test_send_whatsapp_template(whatsapp_api):
    """
    Prueba el envío de una plantilla de WhatsApp y verifica que se almacene la respuesta.
    """
    from app.integrations.whatsapp import registro_amigro

    user_id = "525512345678"  # Número de teléfono de prueba en formato internacional
    template_name = "registro_amigro"  # Nombre de la plantilla

    response = await registro_amigro(
        recipient=user_id,
        access_token=whatsapp_api.api_token,
        phone_id=whatsapp_api.phoneID,
        version_api=whatsapp_api.v_api,
        form_data={}  # Proporciona los datos necesarios
    )

    assert response is not None
    assert 'messages' in response

    # Aquí podrías agregar lógica para verificar que la respuesta se haya almacenado correctamente
# Puedes agregar más pruebas siguiendo este formato, cubriendo las funcionalidades que consideres importantes.

@pytest.mark.django_db(transaction=True)
def test_scraping_with_fallback_methods(configuracion):
    """
    Prueba que el scraping intente con Selenium si requests falla.
    """
    from app.models import DominioScraping
    from app.scraping import run_scraper

    # Crear un dominio de prueba
    dominio = DominioScraping.objects.create(
        empresa="Empresa de Prueba",
        dominio="https://www.ejemplo.com",
        activo=True
    )

    # Simular que requests falla y Selenium funciona
    with patch('app.scraping.fetch_with_requests', return_value=None) as mock_requests, \
         patch('app.scraping.fetch_with_selenium', return_value="<html>Contenido con Selenium</html>") as mock_selenium, \
         patch('app.scraping.extract_json_ld', return_value=[{"title": "Vacante Selenium"}]) as mock_extract_json_ld:

        vacantes = asyncio.run(run_scraper(dominio))

        # Verificar que fetch_with_requests fue llamado y devolvió None
        mock_requests.assert_called_once()
        # Verificar que fetch_with_selenium fue llamado
        mock_selenium.assert_called_once()
        # Verificar que se obtuvo la vacante
        assert len(vacantes) == 1
        assert vacantes[0]["title"] == "Vacante Selenium"

@pytest.mark.django_db(transaction=True)
def test_scraping_all_methods_fail(configuracion):
    """
    Prueba que el scraping maneje adecuadamente cuando todos los métodos fallan.
    """
    from app.models import DominioScraping
    from app.scraping import run_scraper

    # Crear un dominio de prueba
    dominio = DominioScraping.objects.create(
        empresa="Empresa de Prueba",
        dominio="https://www.ejemplo.com",
        activo=True
    )

    # Simular que ambos métodos fallan
    with patch('app.scraping.fetch_with_requests', return_value=None) as mock_requests, \
         patch('app.scraping.fetch_with_selenium', return_value=None) as mock_selenium:

        vacantes = asyncio.run(run_scraper(dominio))

        # Verificar que fetch_with_requests fue llamado
        mock_requests.assert_called_once()
        # Verificar que fetch_with_selenium fue llamado
        mock_selenium.assert_called_once()
        # Verificar que no se obtuvieron vacantes
        assert len(vacantes) == 0


# ------------------------
# Pruebas de Integración
# ------------------------

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_process_message(whatsapp_api, flow_model, person):
    """
    Prueba el procesamiento de un mensaje entrante por el chatbot.
    """
    chatbot_handler = ChatBotHandler()
    user_id = person.phone
    text = "Hola"
    business_unit = whatsapp_api.business_unit

    with patch('app.chatbot.send_message', new_callable=AsyncMock) as mock_send_message:
        response, _ = await chatbot_handler.process_message('whatsapp', user_id, text, business_unit)

        assert response is not None
        mock_send_message.assert_awaited()

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_enviar_mensaje_whatsapp(whatsapp_api):
    """
    Envía un mensaje real a través de la API de WhatsApp.
    """
    user_id = "525518490291"  # Número de teléfono de prueba en formato internacional

    response = await send_whatsapp_message(
        user_id=user_id,
        message="Mensaje de prueba.",
        phone_id=whatsapp_api.phoneID
    )

    assert response is not None

    """
    Prueba la creación de una nueva pregunta.
    """
    user = User.objects.create_user(username='testuser', password='testpass')
    client.login(username='testuser', password='testpass')

    etapa = Etapa.objects.create(nombre="Etapa de Prueba")

    data = {
        "name": "Nueva Pregunta",
        "content": "Contenido de la nueva pregunta",
        "input_type": "text",
        "flow": flow_model.id,
        "etapa": etapa.id,
    }
    response = client.post(
        reverse('create_pregunta'),
        data=data,
        content_type='application/json'
    )

    assert response.status_code == 200

# -----------------------------------
# Pruebas de las etapas principales
# -----------------------------------

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_process_message_basic_interaction(chat_state, business_unit):
    chatbot = ChatBotHandler()
    user_id = chat_state.user_id
    platform = chat_state.platform
    text = "Hola"

    with patch("app.integrations.services.send_message", new_callable=AsyncMock) as mock_send_message:
        await chatbot.process_message(platform, user_id, text, business_unit)

        mock_send_message.assert_awaited_once()
        assert chat_state.current_question == "Pregunta de bienvenida"

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_handle_known_intents(chat_state, business_unit):
    chatbot = ChatBotHandler()
    user_id = chat_state.user_id
    platform = chat_state.platform
    intents = [{"name": "saludo", "confidence": 0.9}]

    with patch("app.integrations.services.send_message", new_callable=AsyncMock) as mock_send_message:
        result = await chatbot.handle_known_intents(intents, platform, user_id, chat_state, business_unit)

        mock_send_message.assert_awaited_once_with(
            platform, user_id, "¡Hola! ¿Cómo puedo ayudarte hoy?", business_unit
        )
        assert result is True

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_get_first_question(flow_model, pregunta):
    chatbot = ChatBotHandler()
    question = await chatbot.get_first_question(flow_model)

    assert question == pregunta
    assert question.content == "Por favor, ingresa tu nombre completo."

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_determine_next_question(chat_state, pregunta):
    chatbot = ChatBotHandler()
    chat_state.current_question = pregunta
    await chat_state.asave()

    user_message = "Mi nombre es Pablo"
    analysis = {}
    context = {}

    response, options = await chatbot.determine_next_question(chat_state, user_message, analysis, context)

    assert response is not None
    assert "No hay más preguntas en este flujo." in response

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_send_profile_completion_email(person):
    chatbot = ChatBotHandler()

    with patch("app.integrations.services.send_email", new_callable=AsyncMock) as mock_send_email:
        await chatbot.send_profile_completion_email(person.phone, {"user_name": person.name})

        mock_send_email.assert_awaited_once()

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_handle_user_deviation(chat_state):
    chatbot = ChatBotHandler()

    with patch("app.integrations.services.send_options", new_callable=AsyncMock) as mock_send_options:
        await chatbot.handle_user_deviation(chat_state, "Mensaje inesperado")

        mock_send_options.assert_awaited_once()

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_process_user_message(chat_state):
    chatbot = ChatBotHandler()
    user_message = "¿Qué hay de nuevo?"
    analysis = {}
    context = {}

    response, options = await chatbot.process_user_message(chat_state, user_message, analysis, context)

    assert response == "No hay una pregunta actual en el flujo."

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_handle_whatsapp_template(chat_state, pregunta):
    chatbot = ChatBotHandler()
    chat_state.current_question = pregunta
    await chat_state.asave()

    with patch("app.integrations.services.send_message", new_callable=AsyncMock) as mock_send_message:
        response, _ = await chatbot._handle_whatsapp_template(chat_state, pregunta, {})

        mock_send_message.assert_awaited_once_with(
            chat_state.platform, chat_state.user_id, f"Enviando template: {pregunta.option}"
        )
        assert response is None

# -----------------------------------
# Pruebas adicionales específicas
# -----------------------------------

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_get_or_create_event(chat_state, flow_model):
    chatbot = ChatBotHandler()
    event = await chatbot.get_or_create_event(chat_state.user_id, chat_state.platform, flow_model)

    assert event.user_id == chat_state.user_id
    assert event.flow_model == flow_model

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_verify_user_profile(person):
    chatbot = ChatBotHandler()
    missing_message = await chatbot.verify_user_profile(person)

    assert missing_message is not None
    assert "Para continuar, completa estos datos:" in missing_message