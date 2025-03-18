import asyncio
from app.chatbot.integrations.services import send_message
mensaje = "Por otro lado ya es un proceso que tiene mucho retraso y si no fuera tuyo, estaría persiguiendo al consultor para saber que sucede. En mi scoreboard sale ya -35 días por lo que si a mi ya me urge resolverlo. Si es la única forma que sale pronto demosle."
await send_message("whatsapp", "525518490291", mensaje, "amigro")

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
sudo du -sh /home/pablo/* | sort -h | tail -n 20 &&
sudo du -sh /home/pablollh/* | sort -h | tail -n 20 &&
swapon --show &&
sudo swapoff -a &&
iotop &&
# Eliminar procesos Zombie
sudo kill -9 $(ps -ef | awk '/systemctl.*less/ {print $2,$3}' | tr ' ' '\n' | sort -u)
&& sudo find /var/log -type f -size +10M &&
sudo sysctl vm.drop_caches=3 &&
sudo rm -rf /tmp/* &&
sudo journalctl --vacuum-time=10m &&
sleep 60 &&
swapon --show &&
sudo swapon -a && sleep 5 && sudo swapoff -a && sleep 5 && sudo swapon -a

# Eliminar procesos Zombie
sudo kill -9 $(ps -ef | awk '/systemctl.*less/ {print $2,$3}' | tr ' ' '\n' | sort -u)

sudo chown -R pablo:ai_huntred /home/pablo && \
sudo find /home/pablo -type d -exec chmod 755 {} \; && \
sudo find /home/pablo -type f -exec chmod 644 {} \; && \
sudo chmod -R 775 /home/pablo/media && \
sudo chmod -R 775 /home/pablo/static && \
sudo chmod -R 775 /home/pablo/logs && \
sudo chmod 640 /home/pablo/*/settings.py && \
sudo chmod 640 /home/pablo/.env && \
sudo find /home/pablo -name '*.sh' -exec chmod 755 {} \; && \
sudo chmod 755 /home/pablo/manage.py && \
echo 'Permisos corregidos correctamente'



# Elimina archivos __pycache__ y .pyc
sudo find /home/pablo/venv -name "__pycache__" -type d -exec sudo rm -rf {} +
sudo find /home/pablo/venv -name "*.pyc" -delete
sudo find /home/pablo/venv -name "*.pyo" -delete
sudo find /home/pablo/venv -name "*.pyd" -delete

# Elimina directorios de tests que vienen con los paquetes
sudo find /home/pablo/venv -path "*/tests*" -type d -exec sudo rm -rf {} +

# Elimina documentación
sudo find /home/pablo/venv -path "*/doc*" -type d -exec sudo rm -rf {} +
sudo find /home/pablo/venv -path "*/docs*" -type d -exec sudo rm -rf {} +
sudo find /home/pablo/venv -path "*/examples*" -type d -exec sudo rm -rf {} +

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

# === Activar colores en la terminal ===
export LS_OPTIONS='--color=auto'
alias ls='ls $LS_OPTIONS'
alias ll='ls -la $LS_OPTIONS'
alias grep='grep --color=auto'

# === Personalizar el prompt (PS1) con colores ===
export PS1="\[\033[1;32m\]\u@\h:\[\033[1;34m\]\w\[\033[1;36m\]\$ \[\033[0m\]"

# === Alias generales ===
alias iniciar='cd /home/pablo && source venv/bin/activate'
alias apt-todo='sudo apt-get update -y && sudo apt-get upgrade -y && sudo apt autoremove -y'

# === Alias para edición rápida de archivos principales ===
alias edit_ai_urls='sudo rm /home/pablo/ai_huntred/urls.py && sudo nano /home/pablo/ai_huntred/urls.py'
alias edit_settings='sudo rm /home/pablo/ai_huntred/settings.py && sudo nano /home/pablo/ai_huntred/settings.py'
alias edit_celery='sudo rm /home/pablo/ai_huntred/celery.py && sudo nano /home/pablo/ai_huntred/celery.py'

alias edit_models='sudo rm /home/pablo/app/models.py && sudo nano /home/pablo/app/models.py'
alias edit_tasks='sudo rm /home/pablo/app/tasks.py && sudo nano /home/pablo/app/tasks.py'
alias edit_admin='sudo rm /home/pablo/app/admin.py && sudo nano /home/pablo/app/admin.py'
alias edit_urls='sudo rm /home/pablo/app/urls.py && sudo nano /home/pablo/app/urls.py'
alias edit_signal='sudo rm /home/pablo/app/signal.py && sudo nano /home/pablo/app/signal.py'
alias edit_monitoring='sudo rm /home/pablo/app/monitoring.py && sudo nano /home/pablo/app/monitoring.py'

# === Alias para edición de archivos en utilidades ===
alias edit_catalogs='sudo rm /home/pablo/app/utilidades/catalogs.py && sudo nano /home/pablo/app/utilidades/catalogs.py'
alias edit_loader='sudo rm /home/pablo/app/utilidades/loader.py && sudo nano /home/pablo/app/utilidades/loader.py'
alias edit_calendar='sudo rm /home/pablo/app/utilidades/google_calendar.py && sudo nano /home/pablo/app/utilidades/google_calendar.py'
alias edit_reports='sudo rm /home/pablo/app/utilidades/report_generator.py && sudo nano /home/pablo/app/utilidades/report_generator.py'
alias edit_parser='sudo rm /home/pablo/app/utilidades/parser.py && sudo nano /home/pablo/app/utilidades/parser.py'
alias edit_vacantes='sudo rm /home/pablo/app/utilidades/vacantes.py && sudo nano /home/pablo/app/utilidades/vacantes.py'
alias edit_linkedin='sudo rm /home/pablo/app/utilidades/linkedin.py && sudo nano /home/pablo/app/utilidades/linkedin.py'

# === Alias para chatbot e integraciones ===
alias edit_chatbot='sudo rm /home/pablo/app/chatbot/chatbot.py && sudo nano /home/pablo/app/chatbot/chatbot.py'
alias edit_nlp='sudo rm /home/pablo/app/chatbot/nlp.py && sudo nano /home/pablo/app/chatbot/nlp.py'
alias edit_gpt='sudo rm /home/pablo/app/chatbot/gpt.py && sudo nano /home/pablo/app/chatbot/gpt.py'
alias utils='sudo rm /home/pablo/app/chatbot/utils.py && sudo nano /home/pablo/app/chatbot/utils.py'
alias edit_intent='sudo rm /home/pablo/app/chatbot/intents_handles.py && sudo nano /home/pablo/app/chatbot/intents_handler.py'
alias edit_whatsapp='sudo rm /home/pablo/app/chatbot/integrations/whatsapp.py && sudo nano /home/pablo/app/chatbot/integrations/whatsapp.py'
alias edit_telegram='sudo rm /home/pablo/app/chatbot/integrations/telegram.py && sudo nano /home/pablo/app/chatbot/integrations/telegram.py'
alias edit_messenger='sudo rm /home/pablo/app/chatbot/integrations/messenger.py && sudo nano /home/pablo/app/chatbot/integrations/messenger.py'
alias edit_instagram='sudo rm /home/pablo/app/chatbot/integrations/instagram.py && sudo nano /home/pablo/app/chatbot/integrations/instagram.py'
alias edit_services='sudo rm /home/pablo/app/chatbot/integrations/services.py && sudo nano /home/pablo/app/chatbot/integrations/services.py'
alias edit_common='sudo rm /home/pablo/app/chatbot/workflow/common.py && sudo nano /home/pablo/app/chatbot/workflow/common.py'
alias edit_amigro='sudo rm /home/pablo/app/chatbot/workflow/amigro.py && sudo nano /home/pablo/app/chatbot/workflow/amigro.py'
alias edit_executive='sudo rm /home/pablo/app/chatbot/workflow/executive.py && sudo nano /home/pablo/app/chatbot/workflow/executive.py'
alias edit_huntred='sudo rm /home/pablo/app/chatbot/workflow/huntred.py && sudo nano /home/pablo/app/chatbot/workflow/huntred.py'
alias edit_huntu='sudo rm /home/pablo/app/chatbot/workflow/huntu.py && sudo nano /home/pablo/app/chatbot/workflow/huntu.py'

# === Alias para edición de views ===
alias edit_views='sudo rm /home/pablo/app/views.py && sudo nano /home/pablo/app/views.py'
alias edit_candidatos_views='sudo rm /home/pablo/app/views/candidatos_views.py && sudo nano /home/pablo/app/views/candidatos_views.py'
alias edit_vacantes_views='sudo rm /home/pablo/app/views/vacantes_views.py && sudo nano /home/pablo/app/views/vacantes_views.py'
alias edit_clientes_views='sudo rm /home/pablo/app/views/clientes_views.py && sudo nano /home/pablo/app/views/clientes_views.py'
alias edit_chatbot_views='sudo rm /home/pablo/app/views/chatbot_views.py && sudo nano /home/pablo/app/views/chatbot_views.py'
alias edit_utilidades_views='sudo rm /home/pablo/app/views/utilidades_views.py && sudo nano /home/pablo/app/views/utilidades_views.py'
alias edit_integraciones_views='sudo rm /home/pablo/app/views/integraciones_views.py && sudo nano /home/pablo/app/views/integraciones_views.py'
alias edit_auth_views='sudo rm /home/pablo/app/views/auth_views.py && sudo nano /home/pablo/app/views/auth_views.py'

alias edit_forms='sudo rm /home/pablo/app/forms.py && sudo nano /home/pablo/app/forms.py'
alias edit_serializers='sudo rm /home/pablo/app/serializers.py && sudo nano /home/pablo/app/serializers.py'
alias edit_permissions='sudo rm /home/pablo/app/permissions.py && sudo nano /home/pablo/app/permissions.py'
alias edit_middlewares='sudo rm /home/pablo/app/middleware.py && sudo nano /home/pablo/app/middleware.py'

# === Alias para logs y procesos en segundo plano ===
alias logs_celery='sudo journalctl -u celery -f'
alias logs_gunicorn='sudo journalctl -u gunicorn -f'
alias logs_nginx='sudo journalctl -u nginx -f'
alias logs_all='sudo tail -f /home/pablo/logs/*.log'

# === Alias generales ===
alias reload_aliases='source ~/.bashrc'
alias rserver='sudo systemctl restart gunicorn nginx'
alias check_logs='tail -f /home/pablo/logs/*.log'
alias clear_logs='sudo rm -rf /home/pablo/logs/*.log && touch /home/pablo/logs/empty.log'
alias edit_env='sudo nano /home/pablo/.env'
alias edit_alias='nano ~/.bashrc'

# === Alias para gestión del sistema ===
alias migrate='python /home/pablo/manage.py migrate'
alias makemigrations='python /home/pablo/manage.py makemigrations'
alias collectstatic='python /home/pablo/manage.py collectstatic --noinput'
alias shell='python /home/pablo/manage.py shell'
alias monitor_django='python /home/pablo/manage.py runprofileserver'
alias inspect_model='python /home/pablo/manage.py inspectdb'
alias restart_celery='sudo systemctl restart celery'
alias restart_gunicorn='sudo systemctl restart gunicorn'
alias restart_nginx='sudo systemctl restart nginx'
alias smart_reload='cd /home/pablo && python manage.py check && (systemctl is-active --quiet celery && sudo systemctl restart celery) && (systemctl is-active --quiet gunicorn && sudo systemctl restart gunicorn)'
alias restart_all='sudo systemctl restart gunicorn nginx celery-worker celery-beat celery-ml celery-scraping'
alias up_git='sudo truncate -s 0 /home/pablo/logs/*.log && sudo truncate -s 0 /var/log/nginx/access.log && sudo truncate -s 0 /var/log/nginx/error.log && sudo truncate -s 0 /var/log/syslog && sudo truncate -s 0 /var/log/auth.log && sudo truncate -s 0 /var/log/dmesg && sudo truncate -s 0 /var/log/kern.log && sudo logrotate -f /etc/logrotate.conf && sudo journalctl --vacuum-time=1s && sudo journalctl --vacuum-size=50M && sleep 5'
alias up2_git='cd /home/pablo && source venv/bin/activate && git fetch origin && git reset --hard origin/main && git clean -fd && git status && git log -1 && sleep 10 && sudo systemctl restart gunicorn nginx && python manage.py makemigrations && python manage.py migrate'
alias zombie='sudo kill -9 $(ps -ef | grep "systemctl.*less" | awk "{print \$2,\$3}" | tr " " "\n" | sort -u) && sudo find /var/log -type f -size +10M'
alias rmem='sudo sysctl vm.drop_caches=3 && sudo rm -rf /tmp/* && sudo journalctl --vacuum-time=10m && sleep 40 && swapon --show && sudo swapon -a'


# Then in the Python shell, you can import and profile specific tasks
from memory_profiler import profile
from ai_huntred import your_specific_task

# # # PRUEBAS SHELL

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
process_csv('/home/pablo/connections.csv', business_unit)


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
csv_path = "/home/pablo/connections.csv"

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

# Prueba 1: Cargar configuración
unit_name = "huntRED"  # Cambia al nombre de la unidad que desees probar
unit = BusinessUnit.objects.get(name=unit_name)
imap_processor = IMAPCVProcessor(unit)

# Prueba 2: Verificar configuración IMAP
config = imap_processor._load_config(unit)

try:
    mail = imap_processor._connect_imap(config)
    if mail:
        print("Conexión exitosa al servidor IMAP.")
        mail.logout()
    else:
        print("No se pudo conectar al servidor IMAP.")
except Exception as e:
    print(f"Error: {e}")


# Prueba 4: Procesar correos y adjuntos
imap_processor.process_emails()

import email
from email import message_from_bytes
from pathlib import Path
from app.utilidades.parser import IMAPCVProcessor
from app.models import BusinessUnit

unit_name = "huntRED"
unit = BusinessUnit.objects.get(name=unit_name)
imap_processor = IMAPCVProcessor(unit)  # Crear una instancia
parser = imap_processor.parser  # Obtener la instancia de CVParser desde IMAPCVProcessor


# Probar extracción de adjuntos
mail = imap_processor._connect_imap(imap_processor.config)
mail.select(imap_processor.FOLDER_CONFIG['cv_folder'])
status, messages = mail.search(None, 'ALL')
email_ids = messages[0].split()

# Procesar solo los primeros 10 correos
for email_id in email_ids[:2]:  # Rebanando la lista para limitar a 2 para las pruebas

    status, data = mail.fetch(email_id, "(RFC822)")
    message = email.message_from_bytes(data[0][1])
    attachments = imap_processor.parser.extract_attachments(message)
    
    if attachments:
        print(f"Adjuntos encontrados en correo {email_id}:")
        for attachment in attachments:
            print(f"  - Nombre: {attachment['filename']}, Tamaño: {len(attachment['content'])} bytes")
    else:
        print(f"Correo {email_id} no tiene adjuntos válidos.")
# Procesar archivos
for attachment in attachments:
    temp_path = Path(f"/tmp/{attachment['filename']}")
    temp_path.write_bytes(attachment['content'])

    try:
        # Usar la instancia del parser
        text = parser.extract_text_from_file(temp_path)
        if text:
            parsed_data = parser.parse(text)
            email = parsed_data.get("email")
            phone = parsed_data.get("phone")

            candidate = Person.objects.filter(email=email).first() or Person.objects.filter(phone=phone).first()
            if candidate:
                parser._update_candidate(candidate, parsed_data, temp_path)
            else:
                parser._create_new_candidate(parsed_data, temp_path)

            imap_processor.stats["processed"] += 1
    except Exception as e:
        logger.error(f"Error procesando el archivo {attachment['filename']}: {e}")
    finally:
        temp_path.unlink()  # Limpiar archivo temporal


# Prueba 5: Confirmar creación/actualización de candidatos
from app.models import Person
candidates = Person.objects.all()
print(f"Total de candidatos creados/actualizados: {candidates.count()}")
for candidate in candidates:
    print(f"Candidato Ajustado / Creado - {candidate.nombre} {candidate.apellido_paterno} - {candidate.email}")


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
dominios = DominioScraping.objects.filter(activo=True)
print(f"Dominios activos: {[d.dominio for d in dominios]}")

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

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

options = Options()
options.add_argument("--headless")
driver = webdriver.Chrome(options=options)

driver.get("https://santander.wd3.myworkdayjobs.com/es/SantanderCareers?locationCountry=e2adff9272454660ac4fdb56fc70bb51")
html_content = driver.page_source
print(html_content)

driver.quit()

import asyncio
from app.models import DominioScraping
from app.utilidades.scraping import run_scraper

# Obtener todos los dominios activos
dominios_activos = DominioScraping.objects.filter(activo=True)

if dominios_activos.exists():
    for dominio in dominios_activos:
        print(f"\n=== Iniciando scraping para el dominio: {dominio.dominio} ===")
        try:
            vacantes = asyncio.run(run_scraper(dominio))
            print(f"Vacantes extraídas para {dominio.dominio}: {len(vacantes)}")
            for vacante in vacantes[:3]:  # Muestra las primeras 3 vacantes
                print(f"- {vacante.get('title', 'Título no disponible')} ({vacante.get('location', 'Ubicación no disponible')})")
        except Exception as e:
            print(f"❌ Error durante el scraping de {dominio.dominio}: {e}")
else:
    print("No hay dominios activos configurados.")


import asyncio
from app.models import DominioScraping
from app.utilidades.scraping import run_scraper, save_vacantes

# Obtener el dominio de LinkedIn por ID
linkedin_dominio = DominioScraping.objects.get(id=27)

# Ejecutar el scraping
print(f"Iniciando scraping para: {linkedin_dominio.dominio}")
print(f"Iniciando scraping para: {linkedin_dominio.plataforma}")
vacantes = asyncio.run(run_scraper(linkedin_dominio))

# Mostrar resultados
print(f"Vacantes extraídas: {len(vacantes)}")
for vacante in vacantes[:3]:  # Muestra las primeras 3 vacantes
    print(f"- {vacante['title']} en {vacante['company']} ({vacante['location']}) - {vacante['link']}")

response = await self.fetch(session, url)
print(response)  # Verifica el HTML completo para analizarlo


# Guardar vacantes en la base de datos
asyncio.run(save_vacantes(vacantes, linkedin_dominio))
print("Vacantes guardadas correctamente.")


import asyncio
from app.models import DominioScraping

async def main():
    # Obtener un dominio específico
    dominio_scraping = await sync_to_async(DominioScraping.objects.get)(id=27)
    # Ejecutar el scraper
    vacantes = await run_scraper(dominio_scraping)
    print(f"Vacantes extraídas: {len(vacantes)}")
    for vacante in vacantes[:3]:  # Mostrar las primeras 3 vacantes
        print(f"- {vacante['title']} en {vacante['company']} ({vacante['location']})")

# Ejecutar el código
asyncio.run(main())


# /home/pablo/app/utilidades/salario.py
# Paquetes de importación
import requests  # Para obtener tipos de cambio desde una API externa


# Diccionarios de datos estáticos (actualizar periódicamente con fuentes confiables)
DATOS_PPA = {
    "México": 0.48, "USA": 1.0, "Nicaragua": 0.35, "Colombia": 0.45, "Argentina": 0.52, "Brasil": 0.60
}

DATOS_COLI = {
    "Ciudad de México": 50.2, "Nueva York": 100.0, "Managua": 40.0, 
    "Bogotá": 45.0, "Buenos Aires": 45.0, "São Paulo": 48.5
}

DATOS_BIGMAC = {
    "México": 4.5, "USA": 5.7, "Nicaragua": 3.0, "Colombia": 3.5, "Argentina": 3.8, "Brasil": 4.2
}
DIVISA_BASE = {
    "MXN": 20, "USD": 1.0, "Nicaragua": 36.82
}

# Constantes y tablas aplicables para 2025
UMA_DIARIA_2025 = 108.00  # Unidad de Medida y Actualización diaria
ISR_BRACKETS_2025 = [     # Tabla de ISR mensual (limite inferior, limite superior, cuota fija, tasa)
    (0.01, 7735.00, 0.00, 0.0192),
    (7735.01, 65651.07, 148.51, 0.0640),
    (65651.08, 115375.90, 3844.02, 0.1088),
    (115375.91, 134119.41, 9264.16, 0.16),
    (134119.42, 160577.65, 12264.16, 0.1792),
    (160577.66, 323862.00, 17005.47, 0.2136),
    (323862.01, 510451.00, 51883.01, 0.2352),
    (510451.01, 974535.03, 95768.74, 0.30),
    (974535.04, 1291380.04, 234993.95, 0.32),
    (1291380.05, float('inf'), 338944.34, 0.35)
]

SUBSIDIO_EMPLEO_MAX = 475.00      # Subsidio al empleo máximo
SUBSIDIO_EMPLEO_LIMITE = 10171.00 # Límite para aplicar subsidio

# Funciones para obtener datos externos
def obtener_tipo_cambio(moneda_origen):
    if moneda_origen == 'MXN':
        return 1.0
    try:
        api_url = "https://api.exchangerate-api.com/v4/latest/USD"
        response = requests.get(api_url)
        response.raise_for_status()  # Levanta excepción si hay error HTTP
        rates = response.json()['rates']
        usd_to_mxn = rates.get('MXN', 20.3)  # Default a 20.31 si falla
        usd_to_origen = rates.get(moneda_origen, 1.0)  # Default a 1.0 si no está la moneda
        if usd_to_origen == 0:  # Evitar división por cero
            raise ValueError(f"Tasa inválida para {moneda_origen}")
        return usd_to_mxn / usd_to_origen  # Tipo de cambio moneda_origen -> MXN
    except Exception as e:
        print(f"Advertencia: Fallo al obtener tipo de cambio para {moneda_origen} -> MXN ({str(e)}). Usando valor por defecto.")
        return 20.3 if moneda_origen == 'USD' else 1.0  # Default para USD, 1.0 para MXN u otras


# Funciones de cálculo
def calcular_isr_mensual(base_gravable: float) -> float:
    """
    Calcula el ISR mensual antes de subsidio para un ingreso gravable dado.
    
    Args:
        base_gravable (float): Ingreso gravable mensual.
    
    Returns:
        float: ISR calculado.
    """
    impuesto = 0.0
    for lim_inf, lim_sup, cuota_fija, tasa in ISR_BRACKETS_2025:
        if base_gravable >= lim_inf and base_gravable <= lim_sup:
            excedente = base_gravable - lim_inf
            impuesto = cuota_fija + excedente * tasa
            break
    return impuesto

def calcular_cuotas_imss(salario_bruto: float) -> float:
    """
    Calcula aproximadamente las cuotas obrero (trabajador) del IMSS a retener.
    
    Args:
        salario_bruto (float): Salario bruto mensual.
    
    Returns:
        float: Cuotas del IMSS a descontar.
    """
    cuota_obrero = salario_bruto * 0.027  # Aproximación simple
    return cuota_obrero

def calcular_neto(
    salario_bruto: float,
    tipo_trabajador: str = 'asalariado',
    incluye_prestaciones: bool = False,
    monto_vales: float = 0.0,
    fondo_ahorro: bool = False,
    porcentaje_fondo: float = 0.13,
    credito_infonavit: float = 0.0,
    pension_alimenticia: float = 0.0,
    aplicar_subsidio: bool = True,
    moneda: str = 'MXN',
    tipo_cambio: float = 1.0
) -> float:
    """
    Calcula el salario neto a partir del salario bruto, considerando todos los elementos posibles.
    
    Args:
        salario_bruto (float): Salario bruto mensual.
        tipo_trabajador (str): Tipo de trabajador (default: 'asalariado').
        incluye_prestaciones (bool): Si incluye vales u otras prestaciones (default: False).
        monto_vales (float): Monto de vales exentos (default: 0.0).
        fondo_ahorro (bool): Si incluye fondo de ahorro (default: False).
        porcentaje_fondo (float): Porcentaje del fondo de ahorro (default: 0.13).
        credito_infonavit (float): Monto o porcentaje del crédito Infonavit (default: 0.0).
        pension_alimenticia (float): Monto o porcentaje de pensión alimenticia (default: 0.0).
        aplicar_subsidio (bool): Si aplica subsidio al empleo (default: True).
        moneda (str): Moneda del salario (default: 'MXN').
        tipo_cambio (float): Tipo de cambio a MXN (default: 1.0).
    
    Returns:
        float: Salario neto calculado en MXN o en la moneda especificada.
    """
    bruto = salario_bruto
    base_gravable = bruto

    # Exención de vales si aplica
    if incluye_prestaciones and monto_vales > 0:
        base_gravable -= monto_vales

    # Cálculo de impuestos y retenciones
    isr = calcular_isr_mensual(base_gravable)
    imss = calcular_cuotas_imss(bruto)

    # Descuento por Infonavit
    infonavit_descuento = 0.0
    if credito_infonavit:
        if 0 < credito_infonavit < 1:  # Si es porcentaje
            infonavit_descuento = bruto * credito_infonavit
        else:  # Si es monto fijo
            infonavit_descuento = credito_infonavit

    # Descuento por pensión alimenticia
    pension_desc = 0.0
    if pension_alimenticia:
        if 0 < pension_alimenticia <= 1:  # Si es porcentaje
            pension_desc = bruto * pension_alimenticia
        else:  # Si es monto fijo
            pension_desc = pension_alimenticia

    # Descuento por fondo de ahorro
    ahorro_desc = 0.0
    if fondo_ahorro:
        ahorro_desc = porcentaje_fondo * bruto

    # Salario neto en MXN
    salario_neto_mxn = bruto - isr - imss - infonavit_descuento - pension_desc - ahorro_desc

    # Conversión a otra moneda si aplica
    if moneda != 'MXN':
        salario_neto_mxn /= tipo_cambio

    return salario_neto_mxn

def calcular_bruto(
    salario_neto: float,
    tipo_trabajador: str = 'asalariado',
    incluye_prestaciones: bool = False,
    monto_vales: float = 0.0,
    fondo_ahorro: bool = False,
    porcentaje_fondo: float = 0.13,
    credito_infonavit: float = 0.0,
    pension_alimenticia: float = 0.0,
    aplicar_subsidio: bool = True,
    moneda: str = 'MXN',
    tipo_cambio: float = 1.0
) -> float:
    """
    Calcula el salario bruto requerido para obtener un salario neto deseado usando búsqueda iterativa.
    
    Args:
        salario_neto (float): Salario neto deseado.
        (Otros parámetros son idénticos a calcular_neto)
    
    Returns:
        float: Salario bruto necesario.
    """
    objetivo = salario_neto
    bruto_min = salario_neto
    bruto_max = salario_neto * 2
    bruto_calculado = None

    # Búsqueda binaria para encontrar el bruto
    for _ in range(50):
        guess = (bruto_min + bruto_max) / 2.0
        neto_calculado = calcular_neto(
            guess,
            tipo_trabajador=tipo_trabajador,
            incluye_prestaciones=incluye_prestaciones,
            monto_vales=monto_vales,
            fondo_ahorro=fondo_ahorro,
            porcentaje_fondo=porcentaje_fondo,
            credito_infonavit=credito_infonavit,
            pension_alimenticia=pension_alimenticia,
            aplicar_subsidio=aplicar_subsidio,
            moneda=moneda,
            tipo_cambio=tipo_cambio
        )
        diferencia = neto_calculado - objetivo
        if abs(diferencia) < 1.0:  # Tolerancia de 1 peso
            bruto_calculado = guess
            break
        elif diferencia < 0:
            bruto_min = guess
        else:
            bruto_max = guess

    return bruto_calculado if bruto_calculado is not None else guess

def calcular_neto_equivalente(neto_origen: float, moneda_origen: str, modelo: str, datos_modelo: dict, tipo_cambio: float) -> float:
    """
    Calcula el salario neto equivalente en MXN ajustado por poder adquisitivo según el modelo seleccionado.
    
    Args:
        neto_origen (float): Salario neto en la moneda de origen.
        moneda_origen (str): Moneda del salario original (ej. 'USD').
        modelo (str): Modelo de ajuste ('PPA', 'COLI', 'BigMac').
        datos_modelo (dict): Datos necesarios según el modelo (ppa, coli_origen, etc.).
        tipo_cambio (float): Tipo de cambio a MXN.
    
    Returns:
        float: Salario neto equivalente en MXN.
    
    Raises:
        ValueError: Si el modelo no es reconocido.
    """
    if modelo == 'PPA':
        ppa = datos_modelo['ppa']
        return neto_origen * ppa
    elif modelo == 'COLI':
        coli_origen = datos_modelo['coli_origen']
        coli_destino = datos_modelo['coli_destino']
        neto_mxn = neto_origen * tipo_cambio
        return neto_mxn * (coli_destino / coli_origen)
    elif modelo == 'BigMac':
        precio_bigmac_origen = datos_modelo['precio_bigmac_origen']
        precio_bigmac_destino = datos_modelo['precio_bigmac_destino']
        neto_mxn = neto_origen * tipo_cambio
        return neto_mxn * (precio_bigmac_destino / (precio_bigmac_origen * tipo_cambio))
    else:
        raise ValueError("Modelo no reconocido")

import asyncio
import os
import django
from app.chatbot.workflow.common import calcular_salario_chatbot
from app.models import BusinessUnit
from asgiref.sync import sync_to_async

# Configurar el entorno Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_huntred.settings')  # Reemplaza con el nombre real de tu proyecto
django.setup()
# Obtener el nombre del BusinessUnit
async def get_amigro_business_unit_name():
    business_unit = await sync_to_async(BusinessUnit.objects.filter(name__iexact='amigro').first)()
    if not business_unit:
        raise Exception("No se encontró BusinessUnit 'amigro' en la base de datos.")
    print(f"La unidad de Amigro es: {business_unit} - ID {business_unit.id}")
    return business_unit.name

# Ejecutar pruebas detalladas de salario
async def ejecutar_pruebas_detalladas():
    business_unit_name = await get_amigro_business_unit_name()


    # Prueba 2: WhatsApp - Salario neto con bono
    mensaje_whatsapp = "Salario bruto = 100000000 COP mensual con 8 mes de bono"
    print(f"Enviando a WhatsApp: {mensaje_whatsapp}")
    await calcular_salario_chatbot("whatsapp", "525518490291", mensaje_whatsapp, business_unit_name)

if __name__ == "__main__":
    asyncio.run(ejecutar_pruebas_detalladas())


nohup python /home/pablo/nlp_pruebas_optimizadas.py &> /home/pablo/logs/nlp_pruebas_optimizadas.out & 
nohup python /home/pablo/nlp_pruebas.py &> /home/pablo/logs/nlp_pruebas.out &
