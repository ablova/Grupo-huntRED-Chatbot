# /home/pablo/app/chatbot/integrations/invitaciones.py

import uuid
from django.conf import settings
from app.models import VerificationCode
from app.chatbot.integrations.services import send_email  # Asegúrate de que esta función esté correctamente implementada
import logging

logger = logging.getLogger(__name__)
logger.info("Inicio de la aplicación.")

def generar_codigo_verificacion(person):
    """
    Genera (o reutiliza) un código de verificación para el candidato.
    """
    existing = VerificationCode.objects.filter(person=person, purpose='update_whatsapp', is_used=False).first()
    if existing:
        return str(existing.key)
    else:
        new_code = uuid.uuid4()
        VerificationCode.objects.create(person=person, key=new_code, purpose='update_whatsapp')
        return str(new_code)

def construir_enlaces(codigo, business_unit):
    """
    Construye un diccionario con los enlaces para cada canal:
      - web: Un landing page donde se redirige al chatbot (p. ej., para completar el perfil)
      - whatsapp: Enlace que redirige al chatbot a través de WhatsApp
      - telegram: Enlace que redirige al chatbot a través de Telegram

    Puedes ajustar la lógica según la infraestructura y las URLs de cada canal.
    """
    base_url = settings.CHATBOT_BASE_URL  # Ej.: "https://www.tudominio.com/complete-profile"
    # Cada enlace incluirá el código de verificación y la unidad (para poder identificar el canal y la unidad)
    enlaces = {
        'web': f"{base_url}?code={codigo}&channel=web&bu={business_unit.name.lower()}",
        'whatsapp': f"{base_url}?code={codigo}&channel=whatsapp&bu={business_unit.name.lower()}",
        'telegram': f"{base_url}?code={codigo}&channel=telegram&bu={business_unit.name.lower()}",
    }
    return enlaces

def enviar_invitacion_completar_perfil(person, business_unit):
    """
    Envía un correo de invitación para que el candidato complete su perfil.
    El correo contiene tres enlaces (web, WhatsApp y Telegram) que redirigen al chatbot,
    pasando el código de verificación correspondiente.
    """
    codigo = generar_codigo_verificacion(person)
    enlaces = construir_enlaces(codigo, business_unit)
    
    subject = f"Completa tu perfil en {business_unit.name}"
    body = f"""
Hola {person.nombre},

Para aprovechar al máximo las oportunidades en {business_unit.name}, necesitamos que completes la información de tu perfil.

Por favor, elige uno de los siguientes métodos para actualizar tus datos de forma segura:

- **Web:** [Completar perfil]({enlaces['web']})
- **WhatsApp:** [Completar perfil]({enlaces['whatsapp']})
- **Telegram:** [Completar perfil]({enlaces['telegram']})

Al hacer clic en alguno de estos enlaces, se te pedirá confirmar tu identidad usando un código único y se establecerá tu ChatState, lo que nos ayudará a mejorar tu experiencia y personalizar nuestras ofertas.

¡Gracias por confiar en nosotros!

Saludos,
El equipo de {business_unit.name}
"""
    try:
        # Se asume que la función send_email acepta parámetros: business_unit_name, subject, destinatario, body.
        send_email(business_unit.name.lower(), subject, person.email, body)
        logger.info(f"Invitación enviada a {person.email}")
    except Exception as e:
        logger.error(f"Error enviando invitación a {person.email}: {e}")

# from app.tasks import enviar_invitaciones_completar_perfil
#result = enviar_invitaciones_completar_perfil.delay()
#print("Task launched, result id:", result.id)
# Para verificar el resultado (cuando se haya ejecutado)
#print(result.get(timeout=60))