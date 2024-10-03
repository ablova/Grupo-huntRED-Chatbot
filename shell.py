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

send_logo('whatsapp', phone_number)
send_logo('telegram', user_id)
send_logo('messenger', sender_id)
# Inicia el shell de Django
python manage.py shell

# Importa las funciones y modelos
from app.integrations.services import send_logo
from app.models import WhatsAppAPI, TelegramAPI, MessengerAPI

# Verifica las configuraciones de las APIs
whatsapp_api = WhatsAppAPI.objects.first()
telegram_api = TelegramAPI.objects.first()
messenger_api = MessengerAPI.objects.first()
phone_number = '525518490291'
user_id = 871198362
PSID = '25166616082937314' # huntRED 

# Envía el logo por WhatsApp
send_logo('whatsapp', phone_number)  # Reemplaza con tu número
# Envía el logo por Telegram
send_logo('telegram', user_id)  # Reemplaza con tu chat ID
# Envía el logo por Messenger
send_logo('messenger', PSID)  # Reemplaza con tu PSID



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
user_id = '871198362'  # Cambia esto con tu ID de Telegram
platform = 'telegram'

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
send_whatsapp_message('525518490291', 'Prueba desde Shell', 'EAAJaOsnq2vgBOxFlPQZBYxWZB2E9isaAkZBt4SfCaLHOeBtJCbyKEfsIWV5qZAF5YElgCyrKbyDa21jXZAeZAHoa9wSILECQQRFVxXZCtxX5bph5CZC2dRbvFCKsMw0stLPIEO9y0S5klCmrZANGcUPTQV6ZB9aUbaNUwGI82lMfTpKHgC9JF45bJCblZBjZB9mznlwfeQZDZD', '114521714899382', 'v20.0')
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
template_name = 'registro_amigro'
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