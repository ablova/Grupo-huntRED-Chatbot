#SIncronizacion GIT
cd /Users/pablollh/Documents/GitHub/AmigroBot-mejorado_AI
git add .
git commit -m "Actualización repositorio Git (date)"
git remote remove production
git remote add production git@chatbot.amigro.org:/home/amigro/git/chatbot.git
git push production main

#git remote -v

sudo journalctl -u gunicorn -f
sudo journalctl -u celery -f
cat /home/amigro/logs/error.log


gcloud compute ssh pablollh@amigro --zone=us-central1-a --project=amigro 

ssh -i ~/.ssh/id_rsa_chatbot git@35.209.109.141
ssh chatbot.amigro.org



sudo journalctl --vacuum-time=5days
sudo journalctl --rotate

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


from app.tasks import send_whatsapp_message

# Ejecuta la tarea en segundo plano
send_whatsapp_message.delay('525518490291', 'Hola desde el chatbot de Amigro, desde shell!')


celery -A chatbot_django worker --loglevel=info

from chatbot_django.celery import debug_task
debug_task.delay()

celery -A chatbot_django worker --loglevel=info
celery -A chatbot_django beat --loglevel=info

from app.tasks import check_and_update_whatsapp_token
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
  }
}'


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
vacantes = consult(1, "https://amigro.org/jm-ajax/get_listings/")

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

from app.chatbot import ChatBotHandler
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
from app.chatbot import ChatBotHandler

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
from app.chatbot import ChatBotHandler

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
from app.chatbot import send_message  
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
                            "text": "https://amigro.org"  # Enlace que será abierto al pulsar el botón
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
image_url = "https://amigro.org/registro.png"  # Reemplaza con tu URL de imagen
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
from app.chatbot import ChatBotHandler
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
from app.chatbot import ChatBotHandler
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
from app.chatbot import ChatBotHandler
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