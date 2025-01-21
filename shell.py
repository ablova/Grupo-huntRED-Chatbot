# Sincronizacion GIT
cd /Users/pablollh/Documents/GitHub/AmigroBot-mejorado_AI
git add .
git commit -m "Mejoras en operacion y ejecucion repositorio Git (date)"
git remote remove production
git remote add production git@ai.huntred.com:/home/pablollh/git/chatbot.git
git push production main

#git remote -v
clear && sudo journalctl -u gunicorn -f
sudo journalctl -u celery -f
cat /home/pablollh/logs/error.log
sudo systemctl restart gunicorn && sudo journalctl --vacuum-time=2minutes && sudo truncate -s 0 /home/pablollh/logs/*.log

##  CONEXION A GCLOUD
gcloud compute ssh pablo@grupo-huntred --zone=us-central1-a --project=grupo-huntred 
cd /home/pablollh && source venv/bin/activate
sudo apt-get update -y && sudo apt-get upgrade -y && sudo apt-get autoremove -y && sudo apt update -y && sudo apt upgrade -y && sudo apt autoremove -y && sudo apt-get clean -y && sudo apt clean -y 
sudo reboot


ssh -i ~/.ssh/id_rsa_chatbot git@34.57.227.244
ssh ai.huntred.com

sudo journalctl --vacuum-time=2minutes
sudo journalctl --rotate

#Ingreso a base de datos
psql -U grupo_huntred_ai_user -h localhost -d postgres


#______________
# Manejo y mejora de memoria
# Check detailed memory usage
df -h &&
free -h &&
sudo du -h / | sort -h | tail -n 20 &&
sudo du -sh /home/pablollh/* &&
swapon --show &&
iotop &&
sudo find /var/log -type f -size +10M &&
sudo sysctl vm.drop_caches=3 &&
sudo rm -rf /tmp/* &&
sudo journalctl --vacuum-time=10m

# Eliminar procesos Zombie
sudo kill -9 $(ps -ef | awk '/systemctl.*less/ {print $2,$3}' | tr ' ' '\n' | sort -u)


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

#Crear ALIAS
nano ~/.bashrc && source ~/.bashrc

# Then in the Python shell, you can import and profile specific tasks
from memory_profiler import profile
from ai_huntred import your_specific_task

# # # PRUEBAS SHELL
Envio de mensajes de whatsapp
import asyncio
from app.models import WhatsAppAPI
from app.chatbot.integrations.whatsapp import send_whatsapp_message

async def test_send_message():
    phone_id = "114521714899382"  # ID del número configurado en WhatsAppAPI
    user_id = "5215518490291"  # Número de destino
    message = "Prueba directa después del ajuste"

    # Ejecutar la función de envío
    await send_whatsapp_message(
        user_id=user_id,
        message=message,
        phone_id=phone_id
    )

# Ejecutar la prueba
asyncio.run(test_send_message())

import asyncio
from app.chatbot.integrations.whatsapp import send_whatsapp_message

async def test_send_buttons():
    user_id = "5215518490291"
    message = "Selecciona una opción:"
    phone_id = "114521714899382"
    buttons = [
        {"type": "reply", "reply": {"id": "opcion_1", "title": "Opción 1 - PARA RESPONDER"}},
        {"type": "reply", "reply": {"id": "opcion_2", "title": "Opción 2 - No es la correcta"}}
    ]

    await send_whatsapp_message(
        user_id=user_id,
        message=message,
        buttons=buttons,
        phone_id=phone_id
    )

asyncio.run(test_send_buttons())


import asyncio
from app.chatbot.integrations.whatsapp import handle_interactive_message
payload = {
    "interactive": {
        "type": "button_reply",
        "button_reply": {"id": "opcion_1", "title": "Opción 1"}
    }
}
asyncio.run(handle_interactive_message(payload, "5215518490291", "amigro"))


ENvio de mensaje telegram.
import asyncio
from app.models import TelegramAPI
from app.chatbot.integrations.telegram import send_telegram_message

async def test_send_message():
    chat_id = 871198362  # ID del chat de Telegram
    message = "Prueba directa desde función send_telegram_message"

    # Ejecutar la función de envío
    await send_telegram_message(chat_id, message)

# Ejecutar la prueba
asyncio.run(test_send_message())

import asyncio
from app.chatbot.integrations.telegram import send_telegram_buttons

async def test_send_buttons():
    chat_id = 871198362
    message = "Selecciona una opción:"
    buttons = [
        {"title": "Opción 1", "payload": "opcion_1"},
        {"title": "Opción 2", "payload": "opcion_2"}
    ]
    api_token = "5875713338:AAEl4RDu95KuB-oz4JqxMKLRnWr6j8bHky0"  # Reemplazar con el token correcto

    await send_telegram_buttons(chat_id, message, buttons, api_token)

asyncio.run(test_send_buttons())

from app.chatbot.chatbot import ChatBotHandler
import openai 

handler = ChatBotHandler()

response = handler.process_message(
    platform='whatsapp',
    user_id='5215518490291',
    text='Hola, quiero saber más.',
    business_unit=None  # Reemplazar con un objeto válido si es necesario
)

print(response)


from app.models import BusinessUnit

# Obtén un objeto válido de BusinessUnit
business_unit = BusinessUnit.objects.get(name="amigro")  # Ajusta según tus datos

# Ejecuta nuevamente la prueba
import asyncio
from app.chatbot.integrations.whatsapp import handle_interactive_message

payload = {
    "interactive": {
        "type": "button_reply",
        "button_reply": {"id": "opcion_1", "title": "Opción 1"}
    }
}
asyncio.run(handle_interactive_message(payload, "5215518490291", business_unit))

from app.chatbot.gpt import GPTHandler

gpt_handler = GPTHandler()
response = gpt_handler.generate_response("Hola, ¿puedes ayudarme?")
print(response)

import asyncio
from app.chatbot.integrations.whatsapp import handle_interactive_message

from app.models import BusinessUnit

# Obtén un objeto válido de BusinessUnit
business_unit = BusinessUnit.objects.get(name="amigro")  # Ajusta según tus datos
async def test_interactive_with_gpt():
    payload = {
        "interactive": {
            "type": "button_reply",
            "button_reply": {"id": "opcion_1", "title": "Opción 1"}
        }
    }
    response = await handle_interactive_message(payload, "5215518490291", business_unit)
    print(response)

asyncio.run(test_interactive_with_gpt())



________________________________________________________________________
from app.models import BusinessUnit

# Revisa los registros existentes
print(BusinessUnit.objects.all())

# Si no existe, crea uno
BusinessUnit.objects.create(name="Amigro")

import asyncio
from app.chatbot.integrations.whatsapp import handle_interactive_message
from app.models import BusinessUnit

# Obtén el objeto BusinessUnit
business_unit = BusinessUnit.objects.get(name="Amigro")

whatsapp_configs = WhatsAppAPI.objects.filter(business_unit=business_unit)
print(whatsapp_configs)

async def test_interactive_with_gpt():
    payload = {
        "interactive": {
            "type": "button_reply",
            "button_reply": {"id": "opcion_1", "title": "Opción 1"}
        }
    }
    response = await handle_interactive_message(payload, "5215518490291", business_unit)
    print(response)

asyncio.run(test_interactive_with_gpt())


import asyncio
from app.chatbot.gpt import GPTHandler

async def test_gpt():
    gpt_handler = GPTHandler()
    response = await gpt_handler.generate_response("Hola, ¿puedes ayudarme?")
    print(response)

asyncio.run(test_gpt())

whatsapp_configs = WhatsAppAPI.objects.filter(business_unit=business_unit)
print(whatsapp_configs)


### EJECUTAR PROCESAR CSV
from app.utilidades.linkedin import process_csv
from app.models import BusinessUnit

# Obtener la BusinessUnit con ID 1
business_unit = BusinessUnit.objects.get(id=1)

# Ejecutar la función
process_csv('/home/pablollh/connections.csv', business_unit)


### PROCESAR CON LINKEDIN
from app.utilidades.linkedin import scrape_linkedin_profile, update_person_from_scrape
from app.models import Person

# Procesar todos los candidatos en Person
persons = Person.objects.all()

for person in persons:
    linkedin_url = person.metadata.get("linkedin_url") if person.metadata else None
    if not linkedin_url:
        print(f"⚠️ {person.nombre} no tiene URL de LinkedIn, omitiendo.")
        continue  # Saltar si no tiene URL

    try:
        print(f"Procesando: {person.nombre} ({linkedin_url})")
        scraped_data = scrape_linkedin_profile(linkedin_url)
        update_person_from_scrape(person, scraped_data)
        print(f"✅ Actualizado: {person.nombre}")
    except Exception as e:
        print(f"❌ Error procesando {person.nombre} ({linkedin_url}): {e}")

from app.utilidades.linkedin import process_linkedin_updates
process_linkedin_updates()

from app.chatbot.nlp import sn
from app.utilidades.linkedin import extract_skills, associate_divisions
from app.utilidades.loader import BUSINESS_UNITS, DIVISIONES, DIVISION_SKILLS

# Validar los métodos de sn
print("== Validación de métodos de SkillExtractor ==")
#print(f"Métodos disponibles en sn: {dir(sn)}")

# Probar extract_skills con texto
test_text = "Python, Machine Learning, Data Analysis"
skills = extract_skills(test_text)
print(f"Habilidades extraídas: {skills}")

# Probar associate_divisions con habilidades normalizadas
divisions = associate_divisions(skills)
print(f"Divisiones asociadas: {divisions}")

# Verificar habilidades para una división específica
division = "Tecnologías de la Información"  # Cambiar según la división a verificar
division_skills = DIVISION_SKILLS.get(division, {})
print(f"Habilidades para la división '{division}': {division_skills}")

# Cargar y verificar catálogos
print("== Verificación de catálogos ==")
print(f"Unidades de negocio: {len(BUSINESS_UNITS)}")
print(f"Divisiones: {len(DIVISIONES)}")
print(f"Divisiones con habilidades: {len(DIVISION_SKILLS)}")


### Y esto es para usarlos desde el CSV para los candidatos del archivo ya están importados en la base de datos. Puedes identificarlos utilizando el campo linkedin_url y asegurarte de procesarlos correctamente.
from app.utilidades.linkedin import scrape_linkedin_profile, update_person_from_scrape, main_test
from app.models import Person, BusinessUnit
import csv

# Ruta al archivo connections.csv
csv_path = "/home/pablollh/connections.csv"

# Leer las URLs desde el archivo
with open(csv_path, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    urls = [row['URL'].strip() for row in reader if row.get('URL')]

# Filtrar personas con URLs en el archivo
persons = Person.objects.filter(linkedin_url__in=urls)

# Procesar cada persona
processed_count = 0
errors_count = 0

for person in persons:
    linkedin_url = person.linkedin_url
    try:
        print(f"Procesando: {person.nombre} ({linkedin_url})")
        scraped_data = scrape_linkedin_profile(linkedin_url)
        update_person_from_scrape(person, scraped_data)
        processed_count += 1
        print(f"✅ Actualizado: {person.nombre}")
    except Exception as e:
        print(f"❌ Error procesando {person.nombre} ({linkedin_url}): {e}")
        errors_count += 1

# Resumen del procesamiento
print(f"Resumen: Procesados: {processed_count}, Errores: {errors_count}")


for candidate in Person.objects.filter(metadata__linkedin_url__isnull=False)[:5]:
    scraped_data = scrape_linkedin_profile(candidate.metadata['linkedin_url'], 'huntred')
    print(scraped_data)


from app.utilidades.catalogs import get_all_skills_for_unit
from app.utilidades.linkedin import main_test
unit = "amigro"
skills = get_all_skills_for_unit(unit)
print(f"Todas las habilidades para {unit}: {skills}")

main_test()

_________

from app.utilidades.catalogs import get_all_skills_for_unit

unit = "huntred"
skills = get_all_skills_for_unit(unit)
print(f"Habilidades cargadas para {unit}: {skills}")

from app.models import Person

candidatos = Person.objects.filter(metadata__linkedin_url__isnull=False)[:10]
for candidato in candidatos:
    print(candidato.nombre, candidato.metadata.get('linkedin_url'))

from app.models import Person
from app.utilidades.catalogs import get_all_skills_for_unit, validate_skill_in_unit
from app.utilidades.linkedin import scrape_linkedin_profile, update_person_from_scrape

def procesar_candidatos(unit_name: str):
    # Cargar habilidades para la unidad de negocio
    skills = get_all_skills_for_unit(unit_name)
    if not skills:
        print(f"No se encontraron habilidades para la unidad {unit_name}.")
        return

    # Filtrar candidatos con LinkedIn
    candidatos = Person.objects.filter(metadata__linkedin_url__isnull=False)
    print(f"{candidatos.count()} candidatos encontrados con LinkedIn.")

    for candidato in candidatos:
        linkedin_url = candidato.metadata.get('linkedin_url')
        print(f"Procesando: {candidato.nombre} - {linkedin_url}")

        # Scraping de LinkedIn
        scraped_data = scrape_linkedin_profile(linkedin_url)
        if not scraped_data:
            print(f"No se pudo obtener información de LinkedIn para {candidato.nombre}.")
            continue

        # Relación con habilidades
        texto_perfil = " ".join([
            scraped_data.get('headline', ''),
            scraped_data.get('experience', ''),
            scraped_data.get('skills', ''),
        ])

        habilidades_relacionadas = [
            skill for skill in skills if validate_skill_in_unit(skill, unit_name)
        ]
        print(f"Habilidades relacionadas para {candidato.nombre}: {habilidades_relacionadas}")

        # Actualizar información del candidato
        update_person_from_scrape(candidato, scraped_data)
        print(f"Actualización completada para {candidato.nombre}.")

try:
    procesar_candidatos("huntred")
except Exception as e:
    print(f"Error procesando candidatos: {e}")

from app.models import Person, BusinessUnit
from app.utilidades.catalogs import get_all_skills_for_unit, validate_skill_in_unit
from app.utilidades.linkedin import scrape_linkedin_profile, update_person_from_scrape
for candidate in Person.objects.filter(linkedin_url__isnull=False)[:1]:
    linkedin_url = candidate.linkedin_url
    print(f"Scrapeando: {linkedin_url}")
    scraped_data = scrape_linkedin_profile(linkedin_url, 'huntred')
    print(scraped_data)

## CORRER CV PARSER EN CORREOS
from app.models import BusinessUnit
from app.utilidades.parser import IMAPCVProcessor

unit_name = "huntRED"  # Cambia al nombre de la unidad que desees probar
unit = BusinessUnit.objects.get(name=unit_name)


# Prueba 1: Cargar configuración
unit_name = "huntRED"  # Cambia al nombre de la unidad que desees probar
unit = BusinessUnit.objects.get(name=unit_name)
imap_processor = IMAPCVProcessor(unit)

# Prueba 2: Verificar configuración IMAP
config = imap_processor._load_config(unit)
print("Configuración de Servicor de Correo (SMTP) cargada:")
print(config)

# Prueba 3: Conexión al servidor de correo
try:
    mail = imap_processor._connect_imap(config)
    if mail:
        print("Conexión exitosa al servidor .")
        mail.logout()
    else:
        print("Fallo en la conexión al servidor .")
except Exception as e:
    print(f"Error durante la conexión: {e}")

# Prueba 4: Procesar correos y adjuntos
imap_processor.process_emails()

# Prueba 5: Confirmar creación/actualización de candidatos
from app.models import Person
candidates = Person.objects.all()
print(f"Total de candidatos creados/actualizados: {candidates.count()}")
for candidate in candidates:
    print(f"{candidate.nombre} {candidate.apellido_paterno} - {candidate.email}")


from app.models import Person

# Total de candidatos en la base de datos
total_candidatos = Person.objects.count()
print(f"Total de candidatos en la base de datos: {total_candidatos}")

# Verificar creación reciente (últimas 24 horas)
from django.utils.timezone import now, timedelta
hace_24_horas = now() - timedelta(hours=24)
nuevos_candidatos = Person.objects.filter(fecha_creacion__gte=hace_24_horas).count()
print(f"Nuevos candidatos creados en las últimas 24 horas: {nuevos_candidatos}")

# Ver detalles de los más recientes
candidatos_recientes = Person.objects.filter(fecha_creacion__gte=hace_24_horas).values('nombre', 'email', 'metadata')[:10]
print("Candidatos recientes (10 primeros):")
for candidato in candidatos_recientes:
    print(candidato)
candidatos_skills = Person.objects.exclude(metadata__skills=[]).values('nombre', 'metadata__skills', 'metadata__divisions')[:10]
print("Candidatos con skills y divisiones procesadas:")
for candidato in candidatos_skills:
    print(candidato)
from app.utilidades.parser import IMAPCVProcessor
from app.models import BusinessUnit

# Selecciona una unidad de negocio
unit = BusinessUnit.objects.get(name="huntRED")
imap_processor = IMAPCVProcessor(unit)

# Ejecuta el procesamiento
imap_processor.process_emails()
from app.tasks import check_emails_and_parse_cvs

check_emails_and_parse_cvs.delay()

from app.utilidades.parser import IMAPCVProcessor
from app.models import BusinessUnit

# Procesar correos de la unidad "huntRED"
unit = BusinessUnit.objects.get(name="huntRED")
imap_processor = IMAPCVProcessor(unit)

imap_processor.process_emails()

from app.chatbot.integrations.services import send_email
import asyncio
asyncio.run(send_email(
    business_unit_name="huntRED",
    subject="Prueba de Envío",
    to_email="pablo@huntred.com",
    body="<p>Este es un correo de prueba.</p>",
    from_email="hola@huntred.com"
))
password="Natalia&Patricio1113!"

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

smtp_host = "mail.huntred.com"
smtp_port = 465
smtp_user = "hola@huntred.com"
smtp_password = password

msg = MIMEMultipart()
msg['From'] = smtp_user
msg['To'] = "pablo@huntred.com"
msg['Subject'] = "Prueba de Envío"
msg.attach(MIMEText("<h1>Esto es una prueba</h1>", 'html'))

try:
    with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
        server.login(smtp_user, smtp_password)
        server.send_message(msg)
        print("Correo enviado correctamente.")
except Exception as e:
    print(f"Error: {e}")

import imaplib

server = imaplib.IMAP4_SSL("mail.huntred.com", 993)
server.login("hola@huntred.com", password)
status, mailboxes = server.list()
print("Buzones disponibles:", mailboxes)

# Intenta seleccionar la carpeta CV
status, data = server.select("CV")
print("Estado de selección:", status, data)

server.logout()



## PRUEBA VACANTES
from app.utilidades.vacantes import VacanteManager
import requests

def test_vacante_manager():
    test_data = {
        'business_unit': '4',  # Reemplazar con un valor válido
        'job_id': 12345,          # Ejemplo de ID
    }

    try:
        manager = VacanteManager(test_data)
        print(f"API URL: {manager.api_url}")
        print(f"Dominio URL: {manager.wp_url}")
        print(f"Headers: {manager.headers}")
        print(f"Conexión WP URL: {manager.wp_url}")

        # Probar conexión con la API
        response = requests.get(manager.api_url, headers=manager.headers)
        print(f"GET Response Code: {response.status_code}")
        if response.status_code == 200:
            print(f"Response JSON: {response.json()}")
        else:
            print(f"Error: {response.text}")

        # Probar POST (simulando un nuevo job listing)
        post_data = {
            "title": "Ejemplo de Vacante",
            "content": "Descripción de ejemplo",
            "status": "publish",
        }
        post_response = requests.post(manager.api_url, json=post_data, headers=manager.headers)
        print(f"POST Response Code: {post_response.status_code}")
        if post_response.status_code == 201:
            print("Vacante creada con éxito.")
        else:
            print(f"Error en creación: {post_response.text}")

    except Exception as e:
        print(f"Error durante la prueba: {e}")

# Ejecutar la prueba
test_vacante_manager()


from app.models import DominioScraping
import asyncio
from app.utilidades.scraping import run_scraper, scrape_domains, get_scraper_for_platform

# 1. Verificar los dominios activos
#dominios = DominioScraping.objects.filter(activo=True)
#print(f"Dominios activos: {[d.dominio for d in dominios]}")

# 2. Probar scraping general
# Probar con el primer dominio activo
if dominios.exists():
    dominio = dominios.first()
    print(f"Probando scraping para el dominio: {dominio.dominio}")
    asyncio.run(run_scraper(dominio))

# 3. Probar los scrapers de cada plataforma
for dominio in dominios:
    print(f"Probando scraper para la plataforma: {dominio.plataforma}")
    scraper = get_scraper_for_platform(dominio.plataforma, dominio.dominio, dominio.cookies)
    if scraper:
        print(f"Scraper obtenido para {dominio.dominio}: {scraper}")
        vacantes = scraper.scrape()
        print(f"Vacantes extraídas: {len(vacantes)}")
    else:
        print(f"No se pudo obtener scraper para {dominio.dominio}.")
