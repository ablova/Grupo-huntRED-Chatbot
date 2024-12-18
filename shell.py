#SIncronizacion GIT
cd /Users/pablollh/Documents/GitHub/AmigroBot-mejorado_AI
git add .
git commit -m "Actualización repositorio Git (date)"
git remote remove production
git remote add production git@ai.huntred.com:/home/pablollh/git/chatbot.git
git push production main

#git remote -v
sudo journalctl -u gunicorn -f
sudo journalctl -u celery -f
cat /home/pablollh/logs/error.log

gcloud compute ssh pablollh@amigro --zone=us-central1-a --project=amigro 

ssh -i ~/.ssh/id_rsa_chatbot git@35.209.109.141
ssh ai.huntred.com

sudo journalctl --vacuum-time=2minutes
sudo journalctl --rotate


#______________
# Manejo y mejora de memoria
# Check detailed memory usage
free -h
# List top memory-consuming processes
ps aux --sort=-%mem | head -n 15
# Check specifically for Python and Celery processes
ps aux | grep -E "python|celery"

# Check Celery worker processes
celery -A ai_huntred inspect stats
celery -A ai_huntred inspect registered

# List active Celery workers
ps aux | grep celery-worker

# Install memory profiler
pip install memory_profiler

# Run your Django application with memory profiling
python -m memory_profiler manage.py
# Analyze memory usage of specific tasks
python -m memory_profiler app/tasks.py

# Use Django's manage.py to run with proper environment
# Use Django's manage.py to run with proper environment
python manage.py shell

# Then in the Python shell, you can import and profile specific tasks
from memory_profiler import profile
from ai_huntred import your_specific_task

# Example of profiling a specific task
@profile
def profile_task():
    your_specific_task.delay()  # or call directly if needed

profile_task()

# Then in the Python shell, you can import and profile specific tasks
from memory_profiler import profile
from ai_huntred import your_specific_task

# Example of profiling a specific task
@profile
def profile_task():
    your_specific_task.delay()  # or call directly if needed

profile_task()

# Use supervisord to manage and auto-restart workers
pip install supervisor

# Sample supervisord configuration
[program:celery-worker]
command=/path/to/venv/bin/celery -A ai_huntred worker
autostart=true
autorestart=true
stderr_logfile=/var/log/celery/worker.err.log
stdout_logfile=/var/log/celery/worker.out.log

# Example Celery worker configuration
app.conf.update(
    task_acks_late=True,
    worker_max_memory_per_child=200000,  # Restart worker after 200MB
    worker_max_tasks_per_child=1000
)

from app.models import WhatsAppAPI, MetaAPI, TelegramAPI, InstagramAPI, MessengerAPI
whatsapp_api = WhatsAppAPI.objects.first()
print(whatsapp_api.api_token, whatsapp_api.phoneID, whatsapp_api.v_api)

meta_api = MetaAPI.objects.first()
print(meta_api.verify_token, meta_api.app_secret)

# Verificar TelegramAPI
telegram_api = TelegramAPI.objects.first()
if telegram_api:
    print(telegram_api.api_key)
else:
    print("No se encontró configuración de TelegramAPI.")

# Verificar InstagramAPI
instagram_api = InstagramAPI.objects.first()
if instagram_api:
    print(instagram_api.access_token)
else:
    print("No se encontró configuración de InstagramAPI.")

# Verificar MessengerAPI
messenger_api = MessengerAPI.objects.first()
if messenger_api:
    print(messenger_api.page_access_token)
else:
    print("No se encontró configuración de MessengerAPI.")

# En lugar de handle_message, usar send_message
send_message('whatsapp', 525518490291, f"Respuesta: Prueba desde shell de webhook")


from ai_huntred import send_whatsapp_message

# Ejecuta la tarea en segundo plano
send_whatsapp_message.delay('525518490291', 'Hola desde el chatbot de Amigro, desde shell!')


celery -A ai_huntred worker --loglevel=info

from ai_huntred.celery import debug_task
debug_task.delay()

celery -A ai_huntred worker --loglevel=info
celery -A ai_huntred beat --loglevel=info

from ai_huntred import check_and_update_whatsapp_token
check_and_update_whatsapp_token.delay()

from app.models import WhatsAppAPI
# Obtener el primer registro de la API
api_data = WhatsAppAPI.objects.first()
# Acceder a los valores
phone_id = api_data.phoneID
api_token = api_data.api_token
v_api = api_data.v_api

print(f"phoneID: {phone_id}")
print(f"API Token: {api_token}")
print(f"API Version: {v_api}")

import requests  # Importar requests
import json
from app.models import WhatsAppAPI, TelegramAPI, MessengerAPI
from app.integrations.services import send_logo

telegram_api = TelegramAPI.objects.first()
bot_token = telegram_api.api_key
api_data = WhatsAppAPI.objects.first()
phone_id = api_data.phoneID
v_api = api_data.v_api
api_token = api_data.api_token 
user_id = 871198362  # PLLH Telegram
phone_number = '525518490291'  #PLLH WA
PSID = '25166616082937314' # huntRED Messenger

print(f"BOT Token: {bot_token}")
print(f"Telegram API: {telegram_api}")


send_logo('whatsapp', phone_number)
send_logo('telegram', user_id)
send_logo('messenger', sender_id)
# Inicia el shell de Django
python manage.py shell

curl -X POST "https://api.telegram.org/bot5875713338:AAEl4RDu95KuB-oz4JqxMKLRnWr6j8bHky0/sendMessage" \
-H "Content-Type: application/json" \
-d '{"chat_id": "871198362", "text": "Mensaje desde curl directo"}'


# Importa las funciones y modelos
from app.integrations.services import send_menu
from app.models import WhatsAppAPI, TelegramAPI, MessengerAPI

# Verifica las configuraciones de las APIs
whatsapp_api = WhatsAppAPI.objects.first()
telegram_api = TelegramAPI.objects.first()
messenger_api = MessengerAPI.objects.first()
phone_number = '525518490291'
user_id = 871198362
PSID = '25166616082937314' # huntRED 

# Envía el logo por WhatsApp
send_menu('whatsapp', phone_number)  # Reemplaza con tu número
# Envía el logo por Telegram
send_menu('telegram', user_id)  # Reemplaza con tu chat ID
# Envía el logo por Messenger
send_menu('messenger', PSID)  # Reemplaza con tu PSID

url = f"https://graph.facebook.com/{v_api}/{phone_id}/messages"
headers = {
    "Authorization": f"Bearer {api_token}",
    "Content-Type": "application/json"
}
payload = {
    "messaging_product": "whatsapp",
    "to": phone_number,
    "type": "text",
    "text": {
        "body": "Hello, this is a test message from Amigro!"
    }
}

# Enviar la solicitud HTTP POST
response = requests.post(url, headers=headers, data=json.dumps(payload))

# Imprimir la respuesta JSON
print(response.json())

#separados en otro proceso
curl -X POST https://graph.facebook.com/v20.0/114521714899382/messages \
-H "Authorization: Bearer EAAJaOsnq2vgBO5ZB0Ub2E1v6VGMIA58Btx5jNAxIVm3yte05QUcy5ggf5k3IGf9EnZCqaZCBczuJT9jYcpMRWD93j24ZCabZA00B5VHP0rqNJDWJImWxtxoPayJxt8BaZAZALuqtL6UdFH3qT8aAdrtBnScrSSKXYqAje9Q9gxUJdbojefZCZAcFekVU7oHphwZC2q3xvyXVwU3M83yo2nwTEnMeyxRlVOhDbuZCnkBl9EZD" \
-H "Content-Type: application/json" \
-d '{
  "messaging_product": "whatsapp",
  "to": "525518490291",
  "type": "text",
  "text": {
    "body": "Hello, this is a test message from Amigro from shell!"
  }}'


curl -X GET "https://api.telegram.org/bot5875713338:AAEl4RDu95KuB-oz4JqxMKLRnWr6j8bHky0/getWebhookInfo"
curl https://api.telegram.org/bot5875713338:AAEl4RDu95KuB-oz4JqxMKLRnWr6j8bHky0/getWebhookInfo


from app.integrations.services import reset_chat_state
user_id = '525518490291'  # Cambia esto con tu ID de Telegram
platform = 'whatsapp'

reset_chat_state(user_id, platform)

Here is the token for bot Amigro @Amigrobot:

5875713338:AAEl4RDu95KuB-oz4JqxMKLRnWr6j8bHky0

from app.vacantes import consult
from app.integrations.telegram import send_telegram_message
from app.models import TelegramAPI

# Usuario de prueba de Telegram (ID)
user_id = 871198362  # Aquí el ID del usuario de prueba

# Carga el token del bot de Telegram
telegram_api = TelegramAPI.objects.first()
bot_token = telegram_api.api_key

# Consulta las vacantes
vacantes = consult(1, "https://huntred.com/jm-ajax/get_listings/")

# Formatea el mensaje con la información de vacantes
mensaje_vacantes = "Vacantes disponibles para ti:\n"
for vacante in vacantes:
    mensaje_vacantes += f"• {vacante['title']} - {vacante['company']} en {vacante['location']['address']}\n"
    mensaje_vacantes += f"  Tipo: {vacante['job_type']}, Salario: {vacante['salary']}\n\n"

# Envía el mensaje de vacantes por Telegram
send_telegram_message.delay(user_id, mensaje_vacantes, bot_token)


from app.models import WhatsAppAPI
# Obtener el primer registro de la API
api_data = WhatsAppAPI.objects.first()
# Acceder a los valores
phone_id = api_data.phoneID
api_token = api_data.api_token
v_api = api_data.v_api
from app.integrations.whatsapp import send_whatsapp_message
send_whatsapp_message('525518490291', 'Prueba desde Shell', api_token, phone_id, v_api)
from app.integrations.whatsapp import send_whatsapp_buttons
buttons = [{"type": "reply", "reply": {"id": "1", "title": "Opción 1"}},{"type": "reply", "reply": {"id": "2", "title": "Opción 2"}}]
send_whatsapp_buttons('525518490291', 'Selecciona una opción:', buttons, api_token, phone_id, 'v20.0')
send_w


# Función de prueba para enviar la plantilla de registro en WhatsApp
def test_whatsapp_registration_template():
    # Configura el número de teléfono de prueba y la plantilla
    phone_number = '525518490291'  # Reemplaza con un número válido para pruebas
    template_name = 'registro_amigro'   # Nombre de la plantilla en Facebook Developer
    whatsapp_api = WhatsAppAPI.objects.first()  # Obtén la configuración de WhatsApp
    from app.integrations.whatsapp import send_whatsapp_template
    # Enviar la plantilla de registro
    status_code, response_text = send_whatsapp_template(phone_number, template_name, whatsapp_api.api_token, whatsapp_api.phoneID)
    
    if status_code == 200:
        print(f"Prueba exitosa: Plantilla enviada a {test_phone_number}")
    else:
        print(f"Error en la prueba: {status_code} - {response_text}")

# Llama a la función de prueba
test_whatsapp_registration_template()
from app.models import WhatsAppAPI
# Obtener el primer registro de la API
api_data = WhatsAppAPI.objects.first()
phone_id = api_data.phoneID
api_token = api_data.api_token
v_api = api_data.v_api
phone_number = '525518490291'  # Reemplaza con un número válido para pruebas
template_name = 'nueva_posicion_amigro'
send_whatsapp_template()

def test_whatsapp_registration_template():
    phone_number = '525518490291'  # Reemplaza con un número válido para pruebas
    template_name = 'registro_amigro'   # Nombre de la plantilla en Facebook Developer
    whatsapp_api = WhatsAppAPI.objects.first()  # Obtén la configuración de WhatsApp
    from app.integrations.whatsapp import send_whatsapp_template
    
    # Enviar la plantilla de registro
    status_code, response_text = send_whatsapp_template(phone_number, template_name, whatsapp_api.api_token, whatsapp_api.phoneID)
    
    if status_code == 200:
        print(f"Prueba exitosa: Plantilla enviada a {phone_number}")
    else:
        print(f"Error en la prueba: {status_code} - {response_text}")

# Llamada de prueba
test_whatsapp_registration_template()


import requests
import json

def send_whatsapp_menu_with_buttons(phone_number, api_token, phone_id, version='v20.0'):
    url = f"https://graph.facebook.com/{version}/{phone_id}/messages"
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json',
    }

    # Definimos los botones para el menú
    data = {
        "messaging_product": "whatsapp",
        "to": phone_number,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "header": {
                "type": "text",
                "text": "Bienvenido a Amigro, elige una opción:"
            },
            "body": {
                "text": "Selecciona una opción para continuar:"
            },
            "action": {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {
                            "id": "1",
                            "title": "Opción 1"
                        }
                    },
                    {
                        "type": "reply",
                        "reply": {
                            "id": "2",
                            "title": "Opción 2"
                        }
                    },
                    {
                        "type": "reply",
                        "reply": {
                            "id": "2",
                            "title": "Opción 2"
                        }
                    },
                    {
                        "type": "reply",
                        "reply": {
                            "id": "2",
                            "title": "Opción 2"
                        }
                    },
                    {
                        "type": "reply",
                        "reply": {
                            "id": "2",
                            "title": "Opción 2"
                        }
                    },
                    # Puedes añadir hasta 3 botones
                ]
            }
        }
    }

    # Enviar solicitud POST a la API de WhatsApp
    response = requests.post(url, headers=headers, data=json.dumps(data))
    
    return response.status_code, response.text

# Ejemplo de prueba para enviar el menú
phone_number = '525518490291'
api_token = 'your_api_token'
phone_id = 'your_phone_id'

status_code, response_text = send_whatsapp_menu_with_buttons(phone_number, api_token, phone_id)

if status_code == 200:
    print(f"Menú enviado exitosamente al número {phone_number}")
else:
    print(f"Error al enviar el menú: {status_code} - {response_text}")



curl -X POST "https://graph.facebook.com/v20.0/{PAGE_ID}/messages" \
      -d "recipient={'id':sender_id}" \
      -d "messaging_type=RESPONSE" \
      -d "message={'text':'hello, world'}" \
      -d "access_token={PAGE_ACCESS_TOKEN}"

from chatbot.chatbot import ChatBotHandler
from app.models import Person, FlowModel

# Crear una instancia del chatbot
chatbot = ChatBotHandler()

# Supongamos que tienes un flujo cargado
flow = FlowModel.objects.first()
user_id = 871198362  # Cambia esto por un ID de usuario real o de prueba
platform = 'telegram'  # Cambia según la plataforma que estés probando
message = "Hola, quiero saber sobre la plataforma de Amigro, registrarme"  # Un mensaje de prueba

# Procesar el mensaje
response, options = await chatbot.process_message(platform, user_id, message)

# Mostrar la respuesta y opciones generadas
print(response, options)

# Crear una instancia del chatbot
chatbot = ChatBotHandler()

# ID de usuario para pruebas de WhatsApp
phone_number = '525518490291'
platform = 'whatsapp'
message = "Estoy buscando oportunidades laborales"

# Procesar el mensaje
response, options = await chatbot.process_message(platform, phone_number, message)

# Mostrar la respuesta y opciones generadas
print(response, options)

import asyncio
from chatbot.chatbot import ChatBotHandler

async def run_test():
    chatbot = ChatBotHandler()
    platform = 'whatsapp'
    user_id = '525518490291'
    message = 'Estoy buscando oportunidades laborales'
    
    response, options = await chatbot.process_message(platform, user_id, message)
    print(response, options)

# Ejecutar la función asíncrona
asyncio.run(run_test())



import asyncio
from chatbot.chatbot import ChatBotHandler

async def run_test():
    chatbot = ChatBotHandler()
    platform = 'whatsapp'
    user_id = '525518490291'
    message = 'Estoy ingresando a México, quiero registrarme'
    
    response, options = await chatbot.process_message(platform, user_id, message)
    print(response, options)

# Ejecutar la función asíncrona
asyncio.run(run_test())
#PRUEBA IMPORTANTE PARA ENVIAR MENSAJE
import requests
from app.models import WhatsAppAPI
whatsapp_api = WhatsAppAPI.objects.first() 
if whatsapp_api:
    access_token = whatsapp_api.api_token
    phone_number_id = whatsapp_api.phoneID
    v_api = whatsapp_api.v_api  
    to_number = "525518490291"  
    message_text = "¡Hola desde la prueba de Django Shell usando DB y envio de imagen!"
    url = f"https://graph.facebook.com/{v_api}/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {"body": message_text}
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response Body: {response.json()}")
        if response.status_code == 200:
            print(f"Mensaje enviado correctamente a {to_number}")
        else:
            print(f"Error al enviar mensaje: {response.status_code}")
    except requests.RequestException as e:
        print(f"Error enviando mensaje a WhatsApp: {e}")
else:
    print("No se encontró configuración de API de WhatsApp en la base de datos.")



from app.integrations.services import send_options
from asgiref.sync import async_to_sync
from app.models import Pregunta, Buttons
pregunta_tos = Pregunta.objects.get(id=4)
botones = [
    {
        "type": "reply", 
        "reply": {
            "id": str(button.id), 
            "title": button.name
        }
    }
    for button in Buttons.objects.filter(pregunta=pregunta_tos)
]
to_number = '5215518490291'  
mensaje_texto = pregunta_tos.name  
print(mensaje_texto)
print(botones)

async_to_sync(send_options)('whatsapp', to_number, mensaje_texto, botones)

from app.models import Pregunta, Buttons
pregunta_tos = Pregunta.objects.get(id=4)
print(Buttons.objects.filter(pregunta=pregunta_tos))


from app.models import Pregunta, Buttons
pregunta_tos = Pregunta.objects.get(id=4)
print(pregunta_tos)
botones = pregunta_tos.botones_pregunta.all()
print(botones) 


from app.models import Pregunta, Buttons, SubPregunta
preguntas = Pregunta.objects.all()
for pregunta in preguntas:
    if pregunta.option == 'Si / No': 
        button_si = Buttons.objects.create(name='Sí')
        button_no = Buttons.objects.create(name='No')
        pregunta.botones_pregunta.set([button_si, button_no])
        print(f'Botones asociados a la pregunta: {pregunta.name}')
sub_preguntas = SubPregunta.objects.all()
for sub_pregunta in sub_preguntas:
    if sub_pregunta.option == 'Si / No': 
        button_si = Buttons.objects.create(name='Sí')
        button_no = Buttons.objects.create(name='No')
        sub_pregunta.botones_sub_pregunta.set([button_si, button_no])
        print(f'Botones asociados a la subpregunta: {sub_pregunta.name}')


from app.models import Pregunta, Buttons
from app.integrations.services import send_options
from asgiref.sync import async_to_sync
pregunta_tos = Pregunta.objects.get(id=4)
buttons = [
    {
        "type": "reply",
        "reply": {
            "id": str(button.id),
            "title": button.name
        }
    }
    for button in Buttons.objects.filter(pregunta=pregunta_tos)
]
message = {
    "type": "interactive",
    "interactive": {
        "type": "button",
        "header": {
            "type": "text",
            "text": "Aceptación de TOS"
        },
        "body": {
            "text": "Elige una opción:"
        },
        "footer": {
            "text": "⬇️ Por favor selecciona una de las siguientes opciones"
        },
        "action": {
            "buttons": buttons
        }
    }
}
user_id = '5215518490291'
platform = 'whatsapp'
import json
async_to_sync(send_options)(platform, user_id, message, buttons)


from asgiref.sync import async_to_sync
from app.models import Person  
from app.vacantes import match_person_with_jobs  
from chatbot.chatbot import send_message  
person = Person.objects.get(phone='525518490291') 
recommended_jobs = match_person_with_jobs(person)
if recommended_jobs:
    vacantes_message = "Estas son las vacantes recomendadas para ti:\n"
    for idx, (job, score) in enumerate(recommended_jobs):
        vacantes_message += f"{idx + 1}. {job.title} en {job.company}\n"
    vacantes_message += "Por favor, responde con el número de la vacante que te interesa."
    async_to_sync(send_message)('whatsapp', person.phone, vacantes_message)
    print(f"Vacantes enviadas a {person.name}")
else:
    print("No se encontraron vacantes.")




import requests
import json

def send_whatsapp_template(phone_number, nombre, apellido, token):
    url = "https://graph.facebook.com/v21.0/114521714899382/messages"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "to": phone_number,
        "type": "template",
        "template": {
            "name": "registro_amigro",
            "language": {
                "code": "es_MX"
            },
            "components": [
                {
                    "type": "body",
                    "parameters": [
                        {
                            "type": "text",
                            "text": nombre
                        },
                        {
                            "type": "text",
                            "text": apellido
                        }
                    ]
                }
            ]
        }
    }
    
    # Imprimir información de depuración
    print("\n=== Información de la petición ===")
    print(f"URL: {url}")
    print("\nHeaders:")
    print(json.dumps(headers, indent=2))
    print("\nPayload:")
    print(json.dumps(payload, indent=2))
    
    try:
        # Realizar la petición con verify=True para asegurar conexión segura
        response = requests.post(
            url, 
            headers=headers, 
            json=payload,
            verify=True
        )
        
        print("\n=== Respuesta del servidor ===")
        print(f"Status Code: {response.status_code}")
        print("Headers de respuesta:")
        print(json.dumps(dict(response.headers), indent=2))
        print("\nContenido de la respuesta:")
        print(json.dumps(response.json(), indent=2))
        
        return response.json()
        
    except requests.exceptions.RequestException as e:
        print(f"\n=== Error en la petición ===")
        print(f"Tipo de error: {type(e).__name__}")
        print(f"Descripción: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            print("\nDetalles de la respuesta de error:")
            print(f"Status Code: {e.response.status_code}")
            try:
                error_json = e.response.json()
                print("Respuesta JSON:")
                print(json.dumps(error_json, indent=2))
            except json.JSONDecodeError:
                print("Respuesta texto plano:")
                print(e.response.text)
        return None

# Ejemplo de uso
token = "EAAJaOsnq2vgBOxatkizgaMhE6dk4jEtbWchTiuHK7XXDbsZAlekvZCldWTajCXABVAGQW9XUbZAdy6IZBoUqZBctEHm6H5mSfP9nAbQ5dZAPbf9P1WkHh4keLT400yhvvbZAEq34e9dlkIp2RwsPqK9ghG6H244SZAFK4V5Oo7FiDl9DdM5j5EhXCY5biTrn7cmzYwZDZD"  # Reemplaza con tu token real
resultado = send_whatsapp_template(
    phone_number="525518490291",
    nombre="Pablo",
    apellido="LLH",
    token=token
)


import requests
import json
from requests.exceptions import Timeout, RequestException

def send_whatsapp_template(phone_number, token, image_url):
    url = "https://graph.facebook.com/v21.0/114521714899382/messages"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "to": phone_number,  # Número de teléfono del destinatario
        "type": "template",
        "template": {
            "name": "registro_amigro",  # Nombre de la plantilla
            "language": {
                "code": "es_MX"  # Idioma de la plantilla
            },
            "components": [
                {
                    "type": "header",  # Encabezado con imagen
                    "parameters": [
                        {
                            "type": "image",
                            "image": {
                                "link": image_url  # URL de la imagen que será enviada en el encabezado
                            }
                        }
                    ]
                },
                {
                    "type": "body",  # Cuerpo del mensaje
                    "parameters": []  # No se envían parámetros variables aquí
                },
                {
                    "type": "button",  # Botón con URL
                    "sub_type": "FLOW",
                    "index": "0",
                    "parameters": [
                        {
                            "type": "text",
                            "text": "https://huntred.com"  # Enlace que será abierto al pulsar el botón
                        }
                    ]
                }
            ]
        }
    }
    
    print("\n=== Información de la petición ===")
    print(f"URL: {url}")
    print("\nHeaders:")
    print(json.dumps(headers, indent=2))
    print("\nPayload:")
    print(json.dumps(payload, indent=2))
    
    try:
        # Realiza la petición POST con un timeout de 30 segundos
        response = requests.post(
            url, 
            headers=headers, 
            json=payload,
            verify=True,
            timeout=30  # Timeout de 30 segundos
        )
        
        # Forzar raise_for_status para que se levante una excepción en caso de error

        
        # Forzar el raise si hay error HTTP
        response.raise_for_status()
        
        print("\n=== Respuesta del servidor ===")
        print(f"Status Code: {response.status_code}")
        print("Contenido de la respuesta:")
        print(json.dumps(response.json(), indent=2))
        
        return response.json()
        
    except Timeout:
        print("Error: La petición excedió el tiempo de espera (30 segundos)")
        return None
    except requests.exceptions.HTTPError as e:
        print(f"Error HTTP: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_json = e.response.json()
                print("Detalles del error:")
                print(json.dumps(error_json, indent=2))
            except json.JSONDecodeError:
                print("Respuesta del error (texto plano):")
                print(e.response.text)
        return None
    except RequestException as e:
        print(f"Error en la petición: {str(e)}")
        return None
    except Exception as e:
        print(f"Error inesperado: {str(e)}")
        return None

# Ejemplo de uso con una URL de imagen de ejemplo
image_url = "https://huntred.com/registro.png"  # Reemplaza con tu URL de imagen
token = "EAAJaOsnq2vgBOxatkizgaMhE6dk4jEtbWchTiuHK7XXDbsZAlekvZCldWTajCXABVAGQW9XUbZAdy6IZBoUqZBctEHm6H5mSfP9nAbQ5dZAPbf9P1WkHh4keLT400yhvvbZAEq34e9dlkIp2RwsPqK9ghG6H244SZAFK4V5Oo7FiDl9DdM5j5EhXCY5biTrn7cmzYwZDZD"  # Reemplaza con tu token real

# Prueba de la función
try:
    resultado = send_whatsapp_template(
        phone_number="525518490291",
        token=token,
        image_url=image_url
    )
    
    if resultado:
        print("\nMensaje enviado exitosamente!")
    else:
        print("\nNo se pudo enviar el mensaje")
except Exception as e:
    print(f"\nError al ejecutar la función: {str(e)}")


from app.models import Pregunta
pregunta = Pregunta.objects.get(id=77)
print(pregunta.action_type)

# Importar las dependencias necesarias
from app.models import Pregunta, WhatsAppAPI
from app.integrations.whatsapp import send_whatsapp_decision_buttons
import asyncio

# Definir manualmente el ID de la pregunta
question_id = 84
pregunta = Pregunta.objects.get(id=question_id)

# Obtener la configuración de WhatsApp API
whatsapp_api = WhatsAppAPI.objects.first()

# Crear botones para "Sí" y "No"
buttons = [
    {"title": "Sí"},
    {"title": "No"}
]

# Definir el número de teléfono de prueba (cambia esto según el destinatario)
user_id = '525518490291'  # Ejemplo de número de WhatsApp

# Definir el mensaje que acompaña los botones
message = pregunta.content

# Ejecutar la función asíncrona para enviar los botones de Sí/No
asyncio.run(send_whatsapp_decision_buttons(
    user_id,
    message,
    buttons,
    whatsapp_api.api_token,
    whatsapp_api.phoneID,
    whatsapp_api.v_api
))



# Importar los modelos y funciones necesarios
from app.models import Pregunta, ChatState, WhatsAppAPI
from chatbot.chatbot import ChatBotHandler
from app.integrations.whatsapp import send_message
import asyncio

# Inicializar el chatbot
handler = ChatBotHandler()

# Simular el estado de un evento para el usuario
user_id = '525518490291'
platform = 'whatsapp'
event = asyncio.run(handler.get_or_create_event(user_id, platform))

# Simular la pregunta actual (pregunta 77, por ejemplo)
event.current_question = Pregunta.objects.get(id=77)
event.save()

# Simular una respuesta "No" del usuario
user_message = "No"

# Procesar la respuesta y obtener el siguiente paso
response, options = asyncio.run(handler.process_message(platform, user_id, user_message))

# Imprimir el resultado
print("Payload enviado a la API:", payload)
print(response, options)


# Importar las dependencias necesarias
from app.models import Pregunta, WhatsAppAPI
from app.integrations.whatsapp import send_whatsapp_buttons
import asyncio

# Definir manualmente el ID de la pregunta (en este caso, 84)
question_id = 84
pregunta = Pregunta.objects.get(id=question_id)

# Verificar que la pregunta tenga botones
if pregunta.botones_pregunta.exists():
    print(f"Botones detectados para la pregunta {question_id}:")
    botones = pregunta.botones_pregunta.all()
    for boton in botones:
        print(boton.name)
else:
    print(f"La pregunta {question_id} no tiene botones asociados.")

# Obtener la configuración de la API de WhatsApp
whatsapp_api = WhatsAppAPI.objects.first()

# Verificar que se ha obtenido correctamente la configuración de WhatsApp
if not whatsapp_api:
    print("Error: No se encontró la configuración de WhatsApp API.")
else:
    buttons = [{"title": boton.name} for boton in botones]
    user_id = '525518490291'  # Ejemplo de número de WhatsApp
    message = pregunta.content
    try:
        asyncio.run(send_whatsapp_buttons(
            user_id,
            message,
            buttons,
            whatsapp_api.api_token,
            whatsapp_api.phoneID,
            whatsapp_api.v_api
        ))
        print(f"Botones enviados correctamente a {user_id}.")
    except Exception as e:
        print(f"Error al enviar los botones: {e}")


# Importar los modelos y funciones necesarios
from app.models import Pregunta, ChatState, WhatsAppAPI
from chatbot.chatbot import ChatBotHandler
from app.integrations.whatsapp import send_message
import asyncio

# Inicializar el chatbot
handler = ChatBotHandler()

# Simular el estado de un evento para el usuario
user_id = '525518490291'
platform = 'whatsapp'
event = asyncio.run(handler.get_or_create_event(user_id, platform))

# Simular la pregunta actual (pregunta 84)
event.current_question = Pregunta.objects.get(id=84)
event.save()

# Simular una respuesta "No" del usuario
user_message = "No"

# Procesar la respuesta y obtener el siguiente paso
response, options = asyncio.run(handler.process_message(platform, user_id, user_message))

# Imprimir el resultado
print("Respuesta procesada:", response)
print("Opciones generadas:", options)


from app.models import Pregunta

# Definir el ID de la pregunta a verificar (ejemplo: 84)
question_id = 55
pregunta = Pregunta.objects.get(id=question_id)

# Verificar si la pregunta tiene botones asignados
if pregunta.botones_pregunta.exists():
    print(f"Botones detectados para la pregunta {question_id}:")
    botones = pregunta.botones_pregunta.all()
    for boton in botones:
        print(boton.name)
else:
    print(f"La pregunta {question_id} no tiene botones asociados.")

from app.models import Pregunta, WhatsAppAPI
from app.integrations.whatsapp import send_whatsapp_buttons
import asyncio

# Definir manualmente el ID de la pregunta (ejemplo: 84)
question_id = 55
pregunta = Pregunta.objects.get(id=question_id)

# Verificar si la pregunta tiene botones
if pregunta.botones_pregunta.exists():
    print(f"Botones detectados para la pregunta {question_id}:")
    botones = pregunta.botones_pregunta.all()
    for boton in botones:
        print(boton.name)
else:
    print(f"La pregunta {question_id} no tiene botones asociados.")

# Obtener la configuración de la API de WhatsApp
whatsapp_api = WhatsAppAPI.objects.first()

if not whatsapp_api:
    print("Error: No se encontró la configuración de WhatsApp API.")
else:
    buttons = [{"title": boton.name} for boton in botones]
    
    user_id = '525518490291'  # Número de teléfono del destinatario
    
    message = pregunta.content
    try:
        asyncio.run(send_whatsapp_buttons(
            user_id,
            message,
            buttons,
            whatsapp_api.api_token,
            whatsapp_api.phoneID,
            whatsapp_api.v_api
        ))
        print(f"Botones enviados correctamente a {user_id}.")
    except Exception as e:
        print(f"Error al enviar los botones: {e}")

from app.models import BotonPregunta

# Verificar si los botones "Menú" y "No" ya existen
boton_menu, created_menu = BotonPregunta.objects.get_or_create(name="Menú")
boton_no, created_no = BotonPregunta.objects.get_or_create(name="No")

if created_menu:
    print("El botón 'Menú' ha sido creado.")
else:
    print("El botón 'Menú' ya existía.")

if created_no:
    print("El botón 'No' ha sido creado.")
else:
    print("El botón 'No' ya existía.")

from app.models import Pregunta
question_id = 84
pregunta = Pregunta.objects.get(id=question_id)
pregunta.botones_pregunta.add(boton_menu, boton_no)
print(f"Botones asignados a la pregunta {pregunta.id}:")
for boton in pregunta.botones_pregunta.all():
    print(f"  - {boton.name}")

# Ver los botones asignados a la pregunta 85
question_id = 84
pregunta = Pregunta.objects.get(id=question_id)

if pregunta.botones_pregunta.exists():
    print(f"Botones asignados a la pregunta {pregunta.id} - '{pregunta.content}':")
    botones = pregunta.botones_pregunta.all()
    for boton in botones:
        print(f"  - {boton.name}")
else:
    print(f"La pregunta {pregunta.id} no tiene botones asignados.")



preguntas = Pregunta.objects.all()
for pregunta in preguntas:
    if pregunta.botones_pregunta.exists():
        print(f"Pregunta {pregunta.id} - '{pregunta.content}' tiene los siguientes botones:")
        for boton in pregunta.botones_pregunta.all():
            print(f"  - {boton.name}")

from app.models import Pregunta, WhatsAppAPI
import asyncio
import httpx  # Asegúrate de tener httpx instalado

async def send_whatsapp_buttons(user_id, message, buttons, api_token, phoneID, version_api):
    url = f"https://graph.facebook.com/{version_api}/{phoneID}/messages"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    # Formatear los botones para WhatsApp
    formatted_buttons = []
    for idx, button in enumerate(buttons):
        formatted_button = {
            "type": "reply",
            "reply": {
                "id": f"btn_{idx}",
                "title": button['title'][:20]  # Límite de 20 caracteres por título
            }
        }
        formatted_buttons.append(formatted_button)
    
    # Payload para el envío de botones
    payload = {
        "messaging_product": "whatsapp",
        "to": user_id,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {
                "text": message[:1024]  # Limitar el texto a 1024 caracteres
            },
            "action": {
                "buttons": formatted_buttons
            }
        }
    }
    
    # Enviar el mensaje a la API de WhatsApp
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()  # Levantar excepción si hubo un error en la API
            print(f"Botones enviados correctamente a {user_id}")
            return response.json()
    except httpx.HTTPStatusError as e:
        print(f"Error en la API de WhatsApp: {e.response.text}")
    except Exception as e:
        print(f"Error enviando los botones: {e}")


# Ejecutar el código para la pregunta 84

# Obtener la pregunta con botones
pregunta = Pregunta.objects.get(id=84)

# Verificar si la pregunta tiene botones
if pregunta.botones_pregunta.exists():
    print(f"Botones asignados a la pregunta {pregunta.id}:")
    for boton in pregunta.botones_pregunta.all():
        print(f"  - {boton.name}")
else:
    print(f"La pregunta {pregunta.id} no tiene botones asignados.")

# Obtener la configuración de WhatsApp API
whatsapp_api = WhatsAppAPI.objects.first()

# Si la pregunta tiene botones, enviar el mensaje
if pregunta.botones_pregunta.exists():
    buttons = [{"title": boton.name} for boton in pregunta.botones_pregunta.all()]
    user_id = '525518490291'
    message = pregunta.content
    
    # Enviar los botones a través de WhatsApp
    asyncio.run(send_whatsapp_buttons(
        user_id,
        message,
        buttons,
        whatsapp_api.api_token,
        whatsapp_api.phoneID,
        whatsapp_api.v_api
    ))
else:
    print("No se encontraron botones para esta pregunta.")



async def send_whatsapp_buttons(user_id, message, buttons, api_token, phoneID, version_api):
    url = f"https://graph.facebook.com/{version_api}/{phoneID}/messages"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    formatted_buttons = []
    for idx, button in enumerate(buttons):
        formatted_button = {
            "type": "reply",
            "reply": {
                "id": f"btn_{idx}", 
                "title": button['title'][:20] 
            }
        }
        formatted_buttons.append(formatted_button)

    payload = {
        "messaging_product": "whatsapp",
        "to": user_id,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {
                "text": message[:1024]  
            },
            "action": {
                "buttons": formatted_buttons
            }
        }
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            print(f"Botones enviados correctamente a {user_id}")
            return response.json()
    except httpx.HTTPStatusError as e:
        print(f"Error en la API de WhatsApp: {e.response.text}")
    except Exception as e:
        print(f"Error enviando los botones: {e}")




from app.models import Pregunta, WhatsAppAPI
from app.integrations.whatsapp import send_whatsapp_buttons
import asyncio

def dividir_botones(botones, n):
    for i in range(0, len(botones), n):
        yield botones[i:i + n]

pregunta_id = 69
pregunta = Pregunta.objects.get(id=pregunta_id)

if pregunta.botones_pregunta.exists():
    print(f"Botones asignados a la pregunta {pregunta.id}:")
    botones = pregunta.botones_pregunta.all()  
    whatsapp_api = WhatsAppAPI.objects.first()  
    user_id = '525518490291'  
    message = pregunta.content  

    for tercia in dividir_botones(list(botones), 3):
        buttons = [{"title": boton.name} for boton in tercia]
        print(f"Enviando los siguientes botones: {[boton['title'] for boton in buttons]}")
        
        asyncio.run(send_whatsapp_buttons(user_id, message, buttons, whatsapp_api.api_token, whatsapp_api.phoneID, whatsapp_api.v_api))
else:
    print(f"La pregunta {pregunta.id} no tiene botones asignados.")


from app.vacantes import procesar_vacante

# Datos de ejemplo para una nueva vacante (ajústalo según lo que desees probar)
data = {
    "screen_2_TextInput_0": "Desarrollador Backend Python",  # job_title
    "screen_2_TextArea_1": "Responsable del desarrollo backend en Python para plataformas",  # job_description
    "screen_3_DatePicker_0": "2024-10-31",  # Fecha para la primera opción de entrevista
    "screen_3_DatePicker_1": "2024-11-01",  # Fecha para la segunda opción de entrevista
    "screen_3_DatePicker_2": "2024-11-02",  # Fecha para la tercera opción de entrevista
    "screen_1_TextInput_0": "Amigro Technologies",  # Nombre de la empresa
    "screen_1_TextInput_4": "525512345678",  # WhatsApp del responsable
    "job_region": "Mexico City",  # Región del trabajo
    "job_type": "full-time",  # Tipo de trabajo
    "remote_position": "1",  # 1 si es remoto, 0 si no lo es
    "job_tags": ["Python", "Backend", "Full-time"]  # Etiquetas para el trabajo
}

# Procesar la vacante y crearla en WordPress
result = procesar_vacante(data)

# Verificar el resultado
if result["status"] == "success":
    print("Vacante creada exitosamente.")
else:
    print(f"Error al crear la vacante: {result['message']}")


Pruebas para la parte de los empleos
from app.integrations.whatsapp import send_whatsapp_message
from app.models import WhatsAppAPI
import asyncio

# Obtener credenciales de prueba de la API
whatsapp_api = WhatsAppAPI.objects.first()

# Enviar un mensaje de prueba
await send_whatsapp_message(
    user_id="123456789",  # Número de WhatsApp para pruebas
    message="¡Hola desde Amigro! Este es un mensaje de prueba.",
    token=whatsapp_api.api_token,
    phoneID=whatsapp_api.phoneID,
    api_version=whatsapp_api.v_api
)



import asyncio
from app.integrations.whatsapp import send_whatsapp_message
from app.models import WhatsAppAPI

# Obtener credenciales de prueba de la API
whatsapp_api = WhatsAppAPI.objects.first()

# Ejecutar el envío de mensaje en un bucle async
asyncio.run(send_whatsapp_message(
    user_id="525518490291",  # Número de WhatsApp para pruebas
    message="¡Hola desde Amigro! Este es un mensaje de prueba.",
    token=whatsapp_api.api_token,
    phoneID=whatsapp_api.phoneID,
    api_version=whatsapp_api.v_api
))

from app.models import Configuracion
from app.vacantes import VacanteManager

# Crear datos de prueba para una vacante
job_data = {
    "job_title": "Recolector en Campo,
    "job_description": "Jornalero para el campo mexicano, con rotacion entre fresa, uva y otros productos agricolas",
    "company_name": "Grupo Molina",
    "job_tags": [],
}

# Instancia de VacanteManager
vacante_manager = VacanteManager(job_data)

# Estimar salarios
salario_min, salario_max = vacante_manager.estimate_salary()
print(f"Salario estimado: Min: ${salario_min} - Max: ${salario_max}")

# Crear la vacante en WordPress
resultado = vacante_manager.create_job_listing()
print("Resultado de la creación de la vacante:", resultado)

# Enviar recapitulación al responsable
vacante_manager.send_recap_position()


import asyncio
from app.models import WhatsAppAPI
from app.integrations.whatsapp import send_whatsapp_message

async def test_whatsapp_message():
    whatsapp_api = WhatsAppAPI.objects.first()
    await send_whatsapp_message(
        user_id="525518490291",
        message="¡Hola desde Amigro! Este es un mensaje de prueba.",
        token=whatsapp_api.api_token,
        phoneID=whatsapp_api.phoneID,
        api_version=whatsapp_api.v_api
    )

# Ejecutar la función en el shell
asyncio.run(test_whatsapp_message())



import asyncio
from chatbot.chatbot import ChatBotHandler
from app.models import ChatState

async def test_new_position_request():
    user_id = "525518490291"  # ID de prueba del usuario
    platform = "whatsapp"
    
    # Crear o recuperar el estado del chat para el usuario
    event, created = await ChatState.objects.aget_or_create(user_id=user_id, platform=platform)
    
    # Crea la instancia del chatbot y procesa el mensaje de solicitud de nueva posición
    chat_handler = ChatBotHandler(api_name=platform)
    response, options = await chat_handler.process_message(platform, user_id, "crear posición")
    
    print("Respuesta:", response)
    print("Opciones:", options)

# Ejecutar la prueba
asyncio.run(test_new_position_request())

eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOjEsIm5hbWUiOiJQYWJsbyIsImlhdCI6MTczMTAwNzY0OCwiZXhwIjoxODg4Njg3NjQ4fQ.BQezJzmVVpcaG2ZIbkMagezkt-ORoO5wyrG0odWZrlg



from app.models import ConfiguracionBU, Person
from app.scraping import consult, login_to_wordpress, register
from app.vacantes import VacanteManager
business_unit = ConfiguracionBU.objects.filter(name="amigro").first()
if not business_unit:
    print("No se encontró la configuración para la BusinessUnit de Amigro")
else:
    print(f"Configuración encontrada: {business_unit}")

url_vacantes = f"{business_unit.dominio_bu}/wp-json/wp/v2/job-listings"  # Asegúrate que el URL esté correcto
vacantes = consult(page=1, url=url_vacantes, business_unit=business_unit)
print(vacantes)

response_registro = register(
    username="usuario_prueba",
    email="usuario_prueba@huntred.com",
    password="password123",
    name="Nombre",
    lastname="Apellido"
)
print(response_registro)

login_exitoso = login_to_wordpress(username="admin_amigro", password="password_admin")
print(f"Inicio de sesión: {'Exitoso' if login_exitoso else 'Fallido'}")

job_data = {
    "job_title": "Desarrollador Backend",
    "job_description": "Responsable de APIs y mantenimiento de sistemas en Python",
    "job_listing_type": "full-time",
    "job_listing_region": "México",
    "company_name": "Amigro S.A.",
    "celular_responsable": "5555555555",
    "job_tags": ["Python", "Django"],
    "_job_expires": "2024-12-31"
}

vacante_manager = VacanteManager(job_data)
resultado_creacion = vacante_manager.create_job_listing()
print(resultado_creacion)

from app.models import ConfiguracionBU
print(list(ConfiguracionBU.objects.values()))

business_unit = ConfiguracionBU.objects.filter(business_unit_id=4).first()
if not business_unit:
    print("No se encontró la configuración para la BusinessUnit de Amigro")
else:
    print(f"Configuración encontrada: {business_unit}")


sudo journalctl --since "03:07" --until "03:27"
crontab -l
sudo crontab -l

cat /etc/crontab
ls /etc/cron.*
cat /home/pablollh/logs/*.log | grep "03:0"
celery -A ai_huntred inspect active


import asyncio
from app.models import DominioScraping
from app.scraping import run_scraper

# Obtén una instancia del dominio a scrapear
try:
    dominio = DominioScraping.objects.get(empresa="Honeywell")  # Cambia "linkedin" según la plataforma.
except DominioScraping.DoesNotExist:
    print("El dominio especificado no existe en la base de datos.")
    dominio = None

if dominio:
    # Ejecuta el scraper y muestra los resultados
    vacantes = asyncio.run(run_scraper(dominio))
    print(f"Total de vacantes extraídas: {len(vacantes)}")
    for idx, vacante in enumerate(vacantes[:10], start=1):  # Muestra solo las primeras 10 vacantes
        print(f"{idx}. Título: {vacante.get('title', 'No especificado')}")
        print(f"   Ubicación: {vacante.get('location', 'No especificado')}")
        print(f"   Enlace: {vacante.get('link', 'No disponible')}")
        print(f"   Descripción: {vacante.get('details', {}).get('description', 'No disponible')}")
        print("-------------------------------------------------------------")
else:
    print("No se pudo encontrar el dominio para scrapear.")


dominio = DominioScraping.objects.get(empresa="Honeywell")
dominio.plataforma = "oracle_hcm"  # Configura correctamente la plataforma
dominio.save()  # Guarda el cambio en la base de datos
print(f"Plataforma actualizada: {dominio.plataforma}")


import asyncio
from app.models import DominioScraping
from app.scraping import run_scraper

# Cargar el dominio y ejecutar el scraper
dominio = DominioScraping.objects.get(empresa="Santander")

# Ejecuta el scraping y muestra los resultados
vacantes = asyncio.run(run_scraper(dominio))
print(f"Total de vacantes extraídas: {len(vacantes)}")
for idx, vacante in enumerate(vacantes[:10], start=1):  # Muestra solo las primeras 10 vacantes
    print(f"{idx}. Título: {vacante.get('title', 'No especificado')}")
    print(f"   Ubicación: {vacante.get('location', 'No especificado')}")
    print(f"   Enlace: {vacante.get('link', 'No disponible')}")
    print(f"   Descripción: {vacante.get('details', {}).get('description', 'No disponible')}")
    print("-------------------------------------------------------------")



INSERT INTO app_dominioscraping (empresa, dominio, plataforma, estado, verificado, cookies, creado_en, actualizado_en)
VALUES 
-- Carso (Oracle HCM)
('Carso', 'https://carso.oracle.com/careers', 'oracle_hcm', 'definido', false, '{"CALYPSO_CSRF_TOKEN": "example-token"}', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),

-- Bimbo (Workday)
('Bimbo', 'https://bimbo.wd3.myworkdayjobs.com/BimboCareers', 'workday', 'definido', false, '{"PLAY_SESSION": "example-session"}', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),

-- Walmart (SAP SuccessFactors)
('Walmart', 'https://walmart.sapsf.com/careers', 'sap_successfactors', 'definido', false, '{"SAP_SESSION": "example-session"}', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),

-- Nu Bank (Workday)
('Nu Bank', 'https://nubank.wd3.myworkdayjobs.com/NuBankCareers', 'workday', 'definido', false, '{"PLAY_SESSION": "example-session"}', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
-- Mondelez (Cornerstone)
('Mondelez', 'https://mondelez.cornerstoneondemand.com/careers', 'cornerstone', 'definido', false, '{"CSRFTOKEN": "example-token"}', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
-- Femsa (Meta4)
('Femsa', 'https://femsa.meta4.com/careers', 'meta4', 'definido', false, '{"META4_SESSION": "example-session"}', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),

-- Santander (Workday)
('Santander', 'https://santander.wd3.myworkdayjobs.com/SantanderCareers', 'workday', 'definido', false, '{"PLAY_SESSION": "fb16fee74907ad1e6a2a94153f4e5402dac17ffe"}', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),

-- Honeywell (Phenom People)
('Honeywell', 'https://careers.honeywell.com/mx/es', 'phenom_people', 'definido', false, '{"ORACLE_SESSION": "example-session"}', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

import asyncio
from app.models import DominioScraping
from app.scraping import run_scraper

# Listado de empresas para probar
empresas = ["Honeywell", "Santander", "Grupo Carso", "Grupo Bimbo", "Walmart de México y Centroamérica", "Nu Bank", "Incode", "Mondelez México"]

for empresa in empresas:
    try:
        dominio = DominioScraping.objects.get(empresa=empresa)
        print(f"Ejecutando scraping para: {empresa}")
        vacantes = asyncio.run(run_scraper(dominio))
        print(f"Total de vacantes extraídas para {empresa}: {len(vacantes)}")
        for idx, vacante in enumerate(vacantes[:10], start=1):  # Muestra las primeras 10 vacantes
            print(f"{idx}. Título: {vacante.get('title', 'No especificado')}")
            print(f"   Ubicación: {vacante.get('location', 'No especificado')}")
            print(f"   Enlace: {vacante.get('link', 'No disponible')}")
            print(f"   Descripción: {vacante.get('details', {}).get('description', 'No disponible')}")
            print("-------------------------------------------------------------")
    except Exception as e:
        print(f"Error ejecutando el scraper para {empresa}: {e}")






from app.models import GptApi

gpt_api, created = GptApi.objects.get_or_create(
    organization="org-fUd3JSW3yVdvb47ZwnookNBm",
    defaults={
        "api_token": "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",
        "project": "proj_CBAnjOYCKdqvT7ElOiKaJSJL",
        "model": "gpt-3.5-turbo",
        "form_pregunta": "Genera un formulario para recabar información de un candidato, para nuestras plataformas de atraccion de talento, particularmente para migrantes entrando a México.",
        "work_pregunta": "Describe el perfil laboral de un candidato con base en su experiencia y cruzalo con un análisis de personalidad (MBL y Big 5).",
    }
)

if not created:
    # Si ya existía, actualizar:
    gpt_api.api_token = "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"
    gpt_api.organization = "org-fUd3JSW3yVdvb47ZwnookNBm"
    gpt_api.project = "proj_CBAnjOYCKdqvT7ElOiKaJSJL"
    gpt_api.model = "gpt-3.5-turbo"
    gpt_api.form_pregunta = "Prompt por defecto para formularios"
    gpt_api.work_pregunta = "Prompt por defecto para perfiles laborales"
    gpt_api.save()



from app.gpt import GPTHandler
gpt_handler = GPTHandler()
response = gpt_handler.generate_response("Hola, ¿puedes presentarte, y ayudarme en crear el perfil de usuarios de huntred.com?")
print(response)


from app.chatbot import ChatBotHandler
from app.models import BusinessUnit
from asgiref.sync import sync_to_async

# Obtener la unidad de negocio de manera asíncrona
amigro_bu = await sync_to_async(BusinessUnit.objects.get)(name="amigro")

# Crear una instancia del chatbot handler
chatbot_handler = ChatBotHandler()

# Procesar el mensaje
await chatbot_handler.process_message(
    platform="whatsapp",
    user_id="525518490291",
    text="Hola",
    business_unit=amigro_bu
)
await chatbot_handler.process_message(
    platform="whatsapp",
    user_id="525518490291",
    text="Sí",
    business_unit=amigro_bu
)
await chatbot_handler.process_message(
    platform="whatsapp",
    user_id="525518490291",
    text="No",
    business_unit=amigro_bu
)
await chatbot_handler.process_message(
    platform="whatsapp",
    user_id="525518490291",
    text="Ver vacantes",
    business_unit=amigro_bu
)
await chatbot_handler.process_message(
    platform="whatsapp",
    user_id="525518490291",
    text="miemail@ejemplo.com",
    business_unit=amigro_bu
)
from app.integrations.services import send_image

configuracion_bu = amigro_bu.configuracionbu
await send_image(
    platform="whatsapp",
    user_id="525518490291",
    message="Aquí tienes nuestro logo:",
    image_url=configuracion_bu.logo_url,
    business_unit=amigro_bu
)



from app.scraping import run_scraper
from app.models import DominioScraping
import asyncio

dominio = DominioScraping.objects.get(empresa="Accenture")
vacantes = asyncio.run(run_scraper(dominio))
print(vacantes)

from app.scraping import run_all_scrapers

await run_all_scrapers()

from app.models import RegistroScraping

registros = RegistroScraping.objects.filter(estado="fallido")
for reg in registros:
    print(reg.error_log)


from app.models import DominioScraping

# Empresas y dominios
empresas = [
    {"nombre": "AbbVie", "dominio": "https://abbvie.wd5.myworkdayjobs.com/abbvie"},
    {"nombre": "Bristol Myers Squibb", "dominio": "https://bristolmyerssquibb.wd5.myworkdayjobs.com/bms"},
    {"nombre": "GSK", "dominio": "https://gsk.wd5.myworkdayjobs.com/careers"},
    {"nombre": "MSD", "dominio": "https://msd.wd5.myworkdayjobs.com/external"},
    {"nombre": "ExxonMobil", "dominio": "https://jobs.exxonmobil.com/"},
    {"nombre": "Johnson Controls", "dominio": "https://johnsoncontrols.wd5.myworkdayjobs.com/en-US/external"},
    {"nombre": "Fujifilm", "dominio": "https://fujifilm.wd5.myworkdayjobs.com/americas"},
    {"nombre": "Diageo", "dominio": "https://diageo.wd5.myworkdayjobs.com/global"},
    {"nombre": "Thales", "dominio": "https://thales.wd5.myworkdayjobs.com/careers"},
    {"nombre": "Roche", "dominio": "https://roche.wd5.myworkdayjobs.com/global_external"},
    {"nombre": "Toyota", "dominio": "https://toyota.wd5.myworkdayjobs.com/toyota"},
    {"nombre": "AstraZeneca", "dominio": "https://astrazeneca.wd5.myworkdayjobs.com/Careers"},
    {"nombre": "Abbott", "dominio": "https://abbott.wd5.myworkdayjobs.com/abbott"},
    {"nombre": "BD", "dominio": "https://bd.wd5.myworkdayjobs.com/en-US/External"},
    {"nombre": "Sanofi", "dominio": "https://sanofi.wd5.myworkdayjobs.com/CAREERS"},
    {"nombre": "Boston Scientific", "dominio": "https://bostonscientific.wd5.myworkdayjobs.com/bsc_jobs"},
    {"nombre": "ThyssenKrupp", "dominio": "https://thyssenkrupp.wd5.myworkdayjobs.com/thyssenkrupp_careers"},
    {"nombre": "AT&T", "dominio": "https://att.wd5.myworkdayjobs.com/Careers"},
    {"nombre": "Orange", "dominio": "https://orange.wd5.myworkdayjobs.com/orange"},
    {"nombre": "Chevron", "dominio": "https://chevron.wd5.myworkdayjobs.com/Careers"},
    {"nombre": "Iberdrola", "dominio": "https://iberdrola.wd5.myworkdayjobs.com/iberdrola_external"},
    {"nombre": "Veolia", "dominio": "https://veolia.wd5.myworkdayjobs.com/external"},
    {"nombre": "ABB", "dominio": "https://abb.wd5.myworkdayjobs.com/External"},
    {"nombre": "Hulu", "dominio": "https://hulu.wd5.myworkdayjobs.com/Hulu"},
    {"nombre": "Warner Bros", "dominio": "https://warnerbros.wd5.myworkdayjobs.com/Careers"},
    {"nombre": "Goodwill", "dominio": "https://goodwill.wd5.myworkdayjobs.com/external"},
    {"nombre": "Home Depot", "dominio": "https://homedepot.wd5.myworkdayjobs.com/Careers"},
    {"nombre": "Puma", "dominio": "https://puma.wd5.myworkdayjobs.com/puma_careers"},
    {"nombre": "Target", "dominio": "https://target.wd5.myworkdayjobs.com/targetjobs"},
    {"nombre": "Bank of America", "dominio": "https://bankofamerica.wd5.myworkdayjobs.com/BofA_Careers"},
    {"nombre": "Citi", "dominio": "https://citi.wd5.myworkdayjobs.com/Careers"},
    {"nombre": "Bupa", "dominio": "https://bupa.wd5.myworkdayjobs.com/Careers"},
    {"nombre": "Morgan Stanley", "dominio": "https://morganstanley.wd5.myworkdayjobs.com/MS"},
    {"nombre": "Santander", "dominio": "https://santander.wd5.myworkdayjobs.com/External"},
    {"nombre": "Accenture", "dominio": "https://accenture.wd5.myworkdayjobs.com/Careers"},
    {"nombre": "Alight", "dominio": "https://alight.wd5.myworkdayjobs.com/alight"},
    {"nombre": "PwC", "dominio": "https://pwc.wd5.myworkdayjobs.com/PwC"},
    {"nombre": "Deloitte", "dominio": "https://deloitte.wd5.myworkdayjobs.com/deloitte"},
    {"nombre": "Chubb", "dominio": "https://chubb.wd5.myworkdayjobs.com/chubb_external"},
    {"nombre": "Argon", "dominio": "https://argon.wd5.myworkdayjobs.com/careers"},
    {"nombre": "Aon", "dominio": "https://aon.wd5.myworkdayjobs.com/Aon"},
    {"nombre": "BBVA", "dominio": "https://bbva.wd5.myworkdayjobs.com/BBVA"},
    {"nombre": "Evercore", "dominio": "https://evercore.wd5.myworkdayjobs.com/External"},
    {"nombre": "ING", "dominio": "https://ing.wd5.myworkdayjobs.com/External"},
    {"nombre": "Skandia", "dominio": "https://skandia.wd5.myworkdayjobs.com/careers"},
    {"nombre": "Mastercard", "dominio": "https://mastercard.wd5.myworkdayjobs.com/External"},
    {"nombre": "Carlyle Group", "dominio": "https://carlyle.wd5.myworkdayjobs.com/careers"},
    {"nombre": "Prudential", "dominio": "https://prudential.wd5.myworkdayjobs.com/External"},
    {"nombre": "Vector", "dominio": "https://vector.wd5.myworkdayjobs.com/External"},
    {"nombre": "Visa", "dominio": "https://visa.wd5.myworkdayjobs.com/Jobs"},
    {"nombre": "BDO", "dominio": "https://bdo.wd5.myworkdayjobs.com/careers"},
    {"nombre": "Teleperformance", "dominio": "https://teleperformance.wd5.myworkdayjobs.com/external"},
    {"nombre": "Adobe", "dominio": "https://adobe.wd5.myworkdayjobs.com/en-US/external_experience"},
    {"nombre": "HP", "dominio": "https://hp.wd5.myworkdayjobs.com/External"},
    {"nombre": "LinkedIn", "dominio": "https://linkedin.wd5.myworkdayjobs.com/LinkedIn"},
    {"nombre": "Salesforce", "dominio": "https://salesforce.wd5.myworkdayjobs.com/careers"},
    {"nombre": "Okta", "dominio": "https://okta.wd5.myworkdayjobs.com/Okta_Careers"},
    {"nombre": "Dell", "dominio": "https://dell.wd5.myworkdayjobs.com/External"},
    {"nombre": "Siemens", "dominio": "https://siemens.wd5.myworkdayjobs.com/External"},
    {"nombre": "Spotify", "dominio": "https://spotify.wd5.myworkdayjobs.com/careers"},
    {"nombre": "Yahoo", "dominio": "https://yahoo.wd5.myworkdayjobs.com/careers"},
    {"nombre": "PepsiCo", "dominio": "https://pepsico.wd5.myworkdayjobs.com/PepsiCoCareers"},
    {"nombre": "Unilever", "dominio": "https://unilever.wd5.myworkdayjobs.com/External"},
    {"nombre": "Nestlé", "dominio": "https://nestle.wd5.myworkdayjobs.com/Nestle"},
    {"nombre": "Coca-Cola", "dominio": "https://coca-cola.wd5.myworkdayjobs.com/careers"},
    {"nombre": "Procter & Gamble", "dominio": "https://pg.wd5.myworkdayjobs.com/External"},
    {"nombre": "Danone", "dominio": "https://danone.wd5.myworkdayjobs.com/DanoneCareers"},
    {"nombre": "Mondelez", "dominio": "https://mondelez.wd5.myworkdayjobs.com/MDLZ"},
    {"nombre": "Grupo Bimbo", "dominio": "https://grupobimbo.wd5.myworkdayjobs.com/GBIMBO"},
    {"nombre": "General Electric", "dominio": "https://ge.wd5.myworkdayjobs.com/GE_Careers"},
    {"nombre": "Kimberly-Clark", "dominio": "https://kimberlyclark.wd5.myworkdayjobs.com/External"},
    {"nombre": "Heineken", "dominio": "https://heineken.wd5.myworkdayjobs.com/careers"},
    {"nombre": "Grupo Modelo (AB InBev)", "dominio": "https://abinbev.wd5.myworkdayjobs.com/abinbev"},
    {"nombre": "Colgate-Palmolive", "dominio": "https://colgate.wd5.myworkdayjobs.com/ColgateCareers"},
    {"nombre": "Johnson & Johnson", "dominio": "https://jnj.wd5.myworkdayjobs.com/External"},
    {"nombre": "Intel", "dominio": "https://intel.wd5.myworkdayjobs.com/External"},
    {"nombre": "Volkswagen", "dominio": "https://volkswagen.wd5.myworkdayjobs.com/Volkswagen_Careers"},
    {"nombre": "BMW", "dominio": "https://bmw.wd5.myworkdayjobs.com/BMW_Group_Careers"},
    {"nombre": "Mercedes-Benz", "dominio": "https://mercedesbenz.wd5.myworkdayjobs.com/MB_Careers"},
    {"nombre": "Continental", "dominio": "https://continental.wd5.myworkdayjobs.com/continental_careers"},
    {"nombre": "Samsung", "dominio": "https://samsung.wd5.myworkdayjobs.com/SamsungCareers"},
    {"nombre": "LG Electronics", "dominio": "https://lg.wd5.myworkdayjobs.com/LG_Careers"},
    {"nombre": "Nike", "dominio": "https://nike.wd5.myworkdayjobs.com/nike"},
    {"nombre": "Adidas", "dominio": "https://adidas.wd5.myworkdayjobs.com/adidas"},
    {"nombre": "Grupo Carso", "dominio": "https://carso.wd5.myworkdayjobs.com/CarsoCareers"},
    {"nombre": "Kraft Heinz", "dominio": "https://kraftheinz.wd5.myworkdayjobs.com/KraftHeinzCareers"},
    {"nombre": "Mars", "dominio": "https://mars.wd5.myworkdayjobs.com/Mars_Careers"},
    {"nombre": "3M", "dominio": "https://3m.wd5.myworkdayjobs.com/External"},
    {"nombre": "Cisco", "dominio": "https://cisco.wd5.myworkdayjobs.com/Cisco_Careers"},
    {"nombre": "Oracle", "dominio": "https://oracle.wd5.myworkdayjobs.com/careers"},
    {"nombre": "SAP", "dominio": "https://sap.wd5.myworkdayjobs.com/SAPCareers"},
    {"nombre": "American Express", "dominio": "https://americanexpress.wd5.myworkdayjobs.com/Careers"},
    {"nombre": "Delta Airlines", "dominio": "https://delta.wd5.myworkdayjobs.com/Delta_Careers"},
    {"nombre": "Aeroméxico", "dominio": "https://aeromexico.wd5.myworkdayjobs.com/External"},
    {"nombre": "Grupo Aeroportuario del Pacífico", "dominio": "https://gap.wd5.myworkdayjobs.com/GAP_Careers"},
    {"nombre": "IKEA", "dominio": "https://ikea.wd5.myworkdayjobs.com/ikea_careers"},
    {"nombre": "Walmart", "dominio": "https://walmart.wd5.myworkdayjobs.com/WalmartCareers"},
    {"nombre": "Starbucks", "dominio": "https://starbucks.wd5.myworkdayjobs.com/StarbucksCareers"},
]

# Iterar sobre empresas para validar y agregar
for empresa in empresas:
    if not DominioScraping.objects.filter(nombre=empresa["nombre"]).exists():
        DominioScraping.objects.create(
            nombre=empresa["nombre"],
            dominio=empresa["dominio"],
            activo=True,  # Activar para scraping
            plataforma="workday"  # Indicar plataforma de Workday
        )
        print(f"Empresa '{empresa['nombre']}' añadida exitosamente.")
    else:
        print(f"Empresa '{empresa['nombre']}' ya existe en la base de datos.")


cd /home/pablollh && source venv/bin/activate

from app.linkedin import slow_scrape_from_csv
from app.models import BusinessUnit

# Encuentra la Business Unit asociada
business_unit = BusinessUnit.objects.filter(name="huntRED").first()
if business_unit:
    slow_scrape_from_csv('/home/pablollh/connections.csv', business_unit)
else:
    print("No se encontró la Business Unit con el nombre 'huntRED'.")




def revert_scraped_flag():
    persons = Person.objects.filter(metadata__has_key='scraped')
    for person in persons:
        person.metadata.pop('scraped', None)
        person.save()
    logger.info(f"Revertido el estado 'scraped' en {persons.count()} perfiles.")

cat /home/pablollh/logs/debug.log | grep --color=auto -E "Perfil enriquecido"

from app.tasks import slow_scrape_from_csv
from app.models import BusinessUnit, revert_scraped_flag

# Asume que tienes una Business Unit creada
bu = BusinessUnit.objects.first()

# Ejecutar scraping
slow_scrape_from_csv('/home/pablollh/connections.csv', bu)

# Revertir estado si es necesario
revert_scraped_flag()

INFO 2024-12-13 16:46:07,616 linkedin Perfil enriquecido: 🌍 Enrique Nogales
INFO 2024-12-13 16:46:22,438 linkedin Perfil enriquecido: Jorge Arreola


import os
import django
import requests
from app.models import DominioScraping

# Función para validar la URL
def validar_url(url):
    try:
        response = requests.head(url, timeout=5, allow_redirects=True)
        return response.status_code in [200, 301, 302]
    except requests.RequestException:
        return False

# Empresas y dominios
empresas = [
    {"nombre": "AbbVie", "dominio": "https://careers.abbvie.com/en/jobs?q=Mexico&options=&page=1&la=0&lo=0&lr=100"},
    {"nombre": "Abbott", "dominio": "https://abbott.wd5.myworkdayjobs.com/abbottcareers?locations=3a9b3d42f0d30158bd74b154c47684e5"},
    {"nombre": "Bank of America", "dominio": "https://bankofamerica.wd5.myworkdayjobs.com/BofA_Careers"},
    {"nombre": "Citi", "dominio": "https://citi.wd5.myworkdayjobs.com/es/2?State_or_Province=1a3f3bf072024650a133222225fe65a9&State_or_Province=bd4da31ba1294e35a7c00c8d273c6dad&State_or_Province=2a9b3694d7b94021b65f6b6a4ec8c4dc&State_or_Province=03b158c518bf4ee4a346bf02784f3cbd&State_or_Province=92bdecb0bceb492d99b98a9bf4b79cae&State_or_Province=811e38f5c4d549e494e9b27bd00cf8a3&State_or_Province=39f4b697029248f28f15b04c0bb4564d&State_or_Province=1169a156f7374f5db661032d0772132d&State_or_Province=d22bee76e28110000edbaff29a73005a&State_or_Province=aa61022afa734cc484addf9c844464d0&State_or_Province=6878a9f5d78f47d4b60b0589c744f506&State_or_Province=b81b49dd746c4c7584e194c20f0addb5&State_or_Province=17dc9ef2582e48dab331a667ffb01637&State_or_Province=ab09b90fe08d42968d2e7b6ac3b43379&State_or_Province=ab032aee6d0f4780bfc6b6988e9c1692&State_or_Province=85d60fd3574542f8be5c31f6fb5ae313&State_or_Province=dc448b82dcaf493c80715385cebf2e6e&State_or_Province=3fd33c9f213646438363b317bbc70b1e&State_or_Province=34e05bc8deff49e2ba1f7365c5a59b8b&State_or_Province=e24ca71036f84293989b87e79a5ab4a2&State_or_Province=94732184ab0c413c9c7ab98e55ad7f30"},
]

for empresa in empresas:
    try:
        # Comprobar si la empresa ya existe
        if not DominioScraping.objects.filter(empresa=empresa["nombre"]).exists():
            # Validar la URL
            es_valida = validar_url(empresa["dominio"])

            # Crear el objeto en la base de datos
            DominioScraping.objects.create(
                empresa=empresa["nombre"],
                dominio=empresa["dominio"],
                activo=True,
                plataforma=empresa.get("plataforma", ""),  # Plataforma, si está disponible
                verificado=es_valida,  # Marcar como verificado solo si pasa la validación
                estado="definido" if es_valida else "libre",  # Estado según la validación
            )

            # Feedback del resultado
            if es_valida:
                print(f"✅ Empresa '{empresa['nombre']}' añadida exitosamente con URL válida.")
            else:
                print(f"⚠️ Empresa '{empresa['nombre']}' añadida pero la URL no es válida o no responde.")
        else:
            print(f"Empresa '{empresa['nombre']}' ya existe en la base de datos.")
    except Exception as e:
        # Manejo de errores específicos
        print(f"❌ Error al añadir la empresa '{empresa['nombre']}': {e}")


PhenomePeople   Roche              https://careers.roche.com/global/en/mexico-jobs/   
PhenomePeople   ABB                https://careers.abb/global/es/search-results?=Mexico
PhenomePeople   Netflix            https://explore.jobs.netflix.net/careers?location=Mexico%20D.F.%2C%20CDMX%2C%20Mexico&utm_source=Netflix+Careersite
EightFold AI    BostonScientific   https://bostonscientific.eightfold.ai/careers?query=mexico&pid=563602796959329&domain=bostonscientific.com&sort_by=relevance&triggerGoButton=true 
EightFold AI    MercadoLibre       https://mercadolibre.eightfold.ai/careers?location=Mexico&pid=26321883&domain=mercadolibre.com&sort_by=relevance&triggerGoButton=false&triggerGoButton=true
                                    https://mercadolibre.eightfold.ai/careers
No se por quien sean               https://jobs.thyssenkrupp.com/es?location=México&lat=23.6585116&lng=-102.0077097&placeId=512b57d3507e8059c05961095a3794a83740f00101f901febf010000000000c0020b&radius=0
No se por quien sean gestionados   https://www.attjobs.com.mx/buscar-trabajo/México
Radancy         Veolia             https://jobs.veolia.com/es/buscar-trabajo/Mexique/2702/2/3996063/23/-102/50/2
Me imagino que propio   Apple      https://jobs.apple.com/es-mx/search?location=mexico-MEXC
                Amazon             https://www.amazon.jobs/es/location/mexico-city-mexico
Puma                               https://about.puma.com/en/careers/job-openings?area=all&location=98
Bank of America                    https://careers.bankofamerica.com/en-us/job-search/mexico?ref=search&start=0&rows=10&search=getAllJobs
Citi (referencia a TalentBrew)     https://jobs.citi.com/search-jobs/Mexico/287/2/3996063/23/-102/50/2
Eightfold AI    MorganStanley      https://morganstanley.eightfold.ai/careers?location=Mexico&pid=549779378596&domain=morganstanley.com&sort_by=relevance&source=mscom
https://www.morganstanley.com/careers/career-opportunities-search#



from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json

# Configuración del navegador (puedes usar Safari, Chrome o Firefox)
options = Options()
options.add_argument("--headless")  # Para que se ejecute sin abrir el navegador (opcional)
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--start-maximized")

# Inicializar el navegador
driver = webdriver.Chrome(options=options)  # Usa 'webdriver.Safari()' si prefieres Safari

# URLs para validar
urls = [
    "https://abbvie.wd5.myworkdayjobs.com/abbvie",
    "https://bristolmyerssquibb.wd5.myworkdayjobs.com/bms",
    "https://gsk.wd5.myworkdayjobs.com/careers",
    "https://msd.wd5.myworkdayjobs.com/external",
    "https://jobs.exxonmobil.com/",
    "https://johnsoncontrols.wd5.myworkdayjobs.com/en-US/external",
    "https://fujifilm.wd5.myworkdayjobs.com/americas",
    "https://diageo.wd5.myworkdayjobs.com/global",
    "https://thales.wd5.myworkdayjobs.com/careers",
    # Agrega más URLs aquí...
]

# Lista para almacenar resultados
resultados = []

for url in urls:
    resultado = {"url": url, "status": "No cargada", "cookies": None, "error": None}
    try:
        driver.get(url)
        time.sleep(5)  # Espera para cargar la página
        
        # Comprobar si hay un banner de cookies
        try:
            cookies_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "Aceptar")]'))
            )
            cookies_button.click()
            resultado["status"] = "Cookies aceptadas"
        except Exception:
            resultado["status"] = "Sin cookies detectadas"

        # Extraer cookies de la página
        cookies = driver.get_cookies()
        resultado["cookies"] = cookies

    except Exception as e:
        resultado["error"] = str(e)
        print(f"Error en {url}: {e}")
    
    resultados.append(resultado)

# Cerrar el navegador
driver.quit()

# Guardar resultados en un archivo JSON para análisis posterior
with open("resultados_urls.json", "w") as f:
    json.dump(resultados, f, indent=4)

# Mostrar resultados en consola
for res in resultados:
    print(f"URL: {res['url']}, Estado: {res['status']}, Error: {res['error']}")
    if res["cookies"]:
        print(f"Cookies: {res['cookies']}")

sudo apt update
sudo apt install -y python3-pip chromium-browser chromedriver
pip install selenium


import os
import django
import requests
from app.models import DominioScraping

# Función para validar la URL
def validar_url(url):
    try:
        response = requests.head(url, timeout=5, allow_redirects=True)
        return response.status_code in [200, 301, 302]
    except requests.RequestException:
        return False

# Empresas y dominios con sus plataformas
empresas = [
    {"nombre": "AbbVie", "dominio": "https://careers.abbvie.com/en/jobs?q=Mexico&options=&page=1&la=0&lo=0&lr=100", "plataforma": "workday"},
    {"nombre": "Bristol Myers Squibb", "dominio": "https://bristolmyerssquibb.wd5.myworkdayjobs.com/bms", "plataforma": "workday"},
    {"nombre": "GSK", "dominio": "https://gsk.wd5.myworkdayjobs.com/GSKCareers/2/refreshFacet/318c8bb6f553100021d223d9780d30be", "plataforma": "workday"},
    {"nombre": "MSD", "dominio": "https://jobs.msd.com/gb/en/search-results?keywords=mexico", "plataforma": "workday"},
    {"nombre": "Roche", "dominio": "https://careers.roche.com/global/en/mexico-jobs/", "plataforma": "phenom_people"},
    {"nombre": "ABB", "dominio": "https://careers.abb/global/es/search-results?=Mexico", "plataforma": "phenom_people"},
    {"nombre": "Netflix", "dominio": "https://explore.jobs.netflix.net/careers?location=Mexico%20D.F.%2C%20CDMX%2C%20Mexico&utm_source=Netflix+Careersite", "plataforma": "phenom_people"},
    {"nombre": "BostonScientific", "dominio": "https://bostonscientific.eightfold.ai/careers?query=mexico&pid=563602796959329&domain=bostonscientific.com&sort_by=relevance&triggerGoButton=true", "plataforma": "eightfold_ai"},
    {"nombre": "MercadoLibre", "dominio": "https://mercadolibre.eightfold.ai/careers?location=Mexico&pid=26321883&domain=mercadolibre.com", "plataforma": "eightfold_ai"},
    {"nombre": "Morgan Stanley", "dominio": "https://morganstanley.eightfold.ai/careers?location=Mexico&pid=549779378596&domain=morganstanley.com", "plataforma": "eightfold_ai"},
    {"nombre": "Amazon", "dominio": "https://www.amazon.jobs/es/location/mexico-city-mexico", "plataforma": ""},
    {"nombre": "Apple", "dominio": "https://jobs.apple.com/es-mx/search?location=mexico-MEXC", "plataforma": ""},
    {"nombre": "Puma", "dominio": "https://about.puma.com/en/careers/job-openings?area=all&location=98", "plataforma": ""},
    {"nombre": "Bank of America", "dominio": "https://careers.bankofamerica.com/en-us/job-search/mexico", "plataforma": ""},
    {"nombre": "Citi", "dominio": "https://jobs.citi.com/search-jobs/Mexico/287/2/3996063/23/-102/50/2", "plataforma": ""},
    {"nombre": "Veolia", "dominio": "https://jobs.veolia.com/es/buscar-trabajo/Mexique/2702/2/3996063/23/-102/50/2", "plataforma": ""},
]

# Script para cargar configuraciones iniciales
for empresa in empresas:
    try:
        if not DominioScraping.objects.filter(empresa=empresa["nombre"]).exists():
            es_valida = validar_url(empresa["dominio"])  # Validación de la URL
            DominioScraping.objects.create(
                empresa=empresa["nombre"],
                dominio=empresa["dominio"],
                activo=True,
                plataforma=empresa["plataforma"],
                verificado=es_valida,  # Marca como verificado solo si pasa la validación
                estado="definido" if es_valida else "libre",
            )
            if es_valida:
                print(f"✅ Empresa '{empresa['nombre']}' añadida exitosamente con URL válida.")
            else:
                print(f"⚠️ Empresa '{empresa['nombre']}' añadida pero la URL no es válida o no responde.")
        else:
            print(f"Empresa '{empresa['nombre']}' ya existe en la base de datos.")
    except Exception as e:
        print(f"❌ Error al añadir la empresa '{empresa['nombre']}': {e}")


import requests
from app.models import DominioScraping


# Función para validar la URL
def validar_url(url):
    try:
        response = requests.head(url, timeout=5, allow_redirects=True)
        return response.status_code in [200, 301, 302]
    except requests.RequestException:
        return False

# Empresas y dominios con sus plataformas
empresas = [
    {"nombre": "BostonScientific", "dominio": "https://bostonscientific.eightfold.ai/careers?query=mexico&pid=563602796959329&domain=bostonscientific.com&sort_by=relevance&triggerGoButton=true", "plataforma": "eightfold_ai"},
    {"nombre": "MercadoLibre", "dominio": "https://mercadolibre.eightfold.ai/careers?location=Mexico&pid=26321883&domain=mercadolibre.com", "plataforma": "eightfold_ai"},
    {"nombre": "Morgan Stanley", "dominio": "https://morganstanley.eightfold.ai/careers?location=Mexico&pid=549779378596&domain=morganstanley.com", "plataforma": "eightfold_ai"},
    {"nombre": "ThyssenKrupp", "dominio": "https://jobs.thyssenkrupp.com/es?location=México&lat=23.6585116&lng=-102.0077097&placeId=512b57d3507e8059c05961095a3794a83740f00101f901febf010000000000c0020b&radius=0", "plataforma": "default"},
    {"nombre": "AT&T", "dominio": "https://www.attjobs.com.mx/buscar-trabajo/México", "plataforma": "default"},
    {"nombre": "Veolia", "dominio": "https://jobs.veolia.com/es/buscar-trabajo/Mexique/2702/2/3996063/23/-102/50/2", "plataforma": "radancy"},
    {"nombre": "Apple", "dominio": "https://jobs.apple.com/es-mx/search?location=mexico-MEXC", "plataforma": "default"},
    {"nombre": "Amazon", "dominio": "https://www.amazon.jobs/es/location/mexico-city-mexico", "plataforma": "default"},
    {"nombre": "Puma", "dominio": "https://about.puma.com/en/careers/job-openings?area=all&location=98", "plataforma": "default"},
    {"nombre": "Bank of America", "dominio": "https://careers.bankofamerica.com/en-us/job-search/mexico?ref=search&start=0&rows=10&search=getAllJobs", "plataforma": "default"},
    {"nombre": "Citi", "dominio": "https://jobs.citi.com/search-jobs/Mexico/287/2/3996063/23/-102/50/2", "plataforma": "talentbrew"},
]

# JSON de ejemplo para cookies
cookie_template = {
    "cookie_name": "example_cookie",
    "value": "example_value",
    "domain": ".example.com",
    "path": "/",
    "secure": True,
    "httpOnly": True
}

# Script para cargar configuraciones iniciales
for empresa in empresas:
    try:
        # Validar si la empresa ya existe
        if not DominioScraping.objects.filter(empresa=empresa["nombre"]).exists():
            # Validar URL
            es_valida = validar_url(empresa["dominio"])

            # Crear el registro
            DominioScraping.objects.create(
                empresa=empresa["nombre"],
                dominio=empresa["dominio"],
                activo=True,
                plataforma=empresa["plataforma"],
                verificado=es_valida,
                estado="definido" if es_valida else "libre",
                cookies=cookie_template if empresa["plataforma"] in ["default", "eightfold_ai"] else None,
            )
            # Feedback del resultado
            if es_valida:
                print(f"✅ Empresa '{empresa['nombre']}' añadida exitosamente con URL válida.")
            else:
                print(f"⚠️ Empresa '{empresa['nombre']}' añadida pero la URL no es válida o no responde.")
        else:
            print(f"Empresa '{empresa['nombre']}' ya existe en la base de datos.")
    except Exception as e:
        # Registrar errores
        print(f"❌ Error al añadir la empresa '{empresa['nombre']}': {e}")


import requests
from app.models import DominioScraping

# Función para validar la URL
def validar_url(url):
    try:
        response = requests.head(url, timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False

# Empresas y dominios
empresas = [
    {"nombre": "AbbVie", "dominio": "https://abbvie.wd5.myworkdayjobs.com/abbvie"},
    {"nombre": "Bristol Myers Squibb", "dominio": "https://bristolmyerssquibb.wd5.myworkdayjobs.com/bms"},
    {"nombre": "GSK", "dominio": "https://gsk.wd5.myworkdayjobs.com/careers"},
    {"nombre": "MSD", "dominio": "https://msd.wd5.myworkdayjobs.com/external"},
    {"nombre": "ExxonMobil", "dominio": "https://jobs.exxonmobil.com/"},
    {"nombre": "Johnson Controls", "dominio": "https://johnsoncontrols.wd5.myworkdayjobs.com/en-US/external"},
    {"nombre": "Fujifilm", "dominio": "https://fujifilm.wd5.myworkdayjobs.com/americas"},
    {"nombre": "Diageo", "dominio": "https://diageo.wd5.myworkdayjobs.com/global"},
    {"nombre": "Thales", "dominio": "https://thales.wd5.myworkdayjobs.com/careers"},
    {"nombre": "Roche", "dominio": "https://roche.wd5.myworkdayjobs.com/global_external"},
    {"nombre": "Toyota", "dominio": "https://toyota.wd5.myworkdayjobs.com/toyota"},
    {"nombre": "AstraZeneca", "dominio": "https://astrazeneca.wd5.myworkdayjobs.com/Careers"},
    {"nombre": "Abbott", "dominio": "https://abbott.wd5.myworkdayjobs.com/abbott"},
    {"nombre": "BD", "dominio": "https://bd.wd5.myworkdayjobs.com/en-US/External"},
    {"nombre": "Sanofi", "dominio": "https://sanofi.wd5.myworkdayjobs.com/CAREERS"},
    {"nombre": "Boston Scientific", "dominio": "https://bostonscientific.wd5.myworkdayjobs.com/bsc_jobs"},
    {"nombre": "ThyssenKrupp", "dominio": "https://thyssenkrupp.wd5.myworkdayjobs.com/thyssenkrupp_careers"},
    {"nombre": "AT&T", "dominio": "https://att.wd5.myworkdayjobs.com/Careers"},
    {"nombre": "Orange", "dominio": "https://orange.wd5.myworkdayjobs.com/orange"},
    {"nombre": "Chevron", "dominio": "https://chevron.wd5.myworkdayjobs.com/Careers"},
    {"nombre": "Iberdrola", "dominio": "https://iberdrola.wd5.myworkdayjobs.com/iberdrola_external"},
    {"nombre": "Veolia", "dominio": "https://veolia.wd5.myworkdayjobs.com/external"},
    {"nombre": "ABB", "dominio": "https://abb.wd5.myworkdayjobs.com/External"},
    {"nombre": "Hulu", "dominio": "https://hulu.wd5.myworkdayjobs.com/Hulu"},
    {"nombre": "Warner Bros", "dominio": "https://warnerbros.wd5.myworkdayjobs.com/Careers"},
    {"nombre": "Goodwill", "dominio": "https://goodwill.wd5.myworkdayjobs.com/external"},
    {"nombre": "Home Depot", "dominio": "https://homedepot.wd5.myworkdayjobs.com/Careers"},
    {"nombre": "Puma", "dominio": "https://puma.wd5.myworkdayjobs.com/puma_careers"},
    {"nombre": "Target", "dominio": "https://target.wd5.myworkdayjobs.com/targetjobs"},
    {"nombre": "Bank of America", "dominio": "https://bankofamerica.wd5.myworkdayjobs.com/BofA_Careers"},
    {"nombre": "Citi", "dominio": "https://citi.wd5.myworkdayjobs.com/Careers"},
    {"nombre": "Bupa", "dominio": "https://bupa.wd5.myworkdayjobs.com/Careers"},
    {"nombre": "Morgan Stanley", "dominio": "https://morganstanley.wd5.myworkdayjobs.com/MS"},
    {"nombre": "Santander", "dominio": "https://santander.wd5.myworkdayjobs.com/External"},
]

for empresa in empresas:
    if not DominioScraping.objects.filter(empresa=empresa["nombre"]).exists():
        if validar_url(empresa["dominio"]):
            DominioScraping.objects.create(
                empresa=empresa["nombre"],
                dominio=empresa["dominio"],
                activo=True,
                plataforma="workday",
            )
            print(f"Empresa '{empresa['nombre']}' añadida exitosamente.")
        else:
            print(f"⚠️ La URL de '{empresa['nombre']}' no es válida o no responde.")
    else:
        print(f"Empresa '{empresa['nombre']}' ya existe en la base de datos.")