# /home/pablo/app/chatbot/integrations/invitaciones.py

import uuid
from django.conf import settings
from app.models import VerificationCode
from app.chatbot.integrations.services import send_email  # Asegúrate de que send_email esté correctamente implementado
import logging

logger = logging.getLogger(__name__)

def generar_codigo_verificacion(person):
    """
    Genera un código de verificación para el candidato y lo guarda en el modelo VerificationCode.
    Si ya existe un código pendiente para el mismo propósito, lo reutiliza.
    """
    # Buscar si ya existe un código pendiente para completar el perfil
    existing = VerificationCode.objects.filter(person=person, purpose='update_whatsapp', is_used=False).first()
    if existing:
        return str(existing.key)
    else:
        new_code = uuid.uuid4()
        VerificationCode.objects.create(person=person, key=new_code, purpose='update_whatsapp')
        return str(new_code)

def enviar_invitacion_completar_perfil(person, business_unit):
    """
    Envía un correo de invitación para completar el perfil.
    """
    codigo = generar_codigo_verificacion(person)
    # Construir el enlace (ajusta la URL base a la de tu sistema)
    enlace = f"https://{settings.ALLOWED_HOSTS[0]}/confirm?code={codigo}&bu={business_unit.name.lower()}"
    subject = f"Completa tu perfil en {business_unit.name}"
    body = f"""
Hola {person.nombre},

Hemos notado que tu perfil en {business_unit.name} está incompleto. Para que puedas acceder a todas las funcionalidades
y oportunidades de nuestra plataforma, te invitamos a completarlo.

Haz clic en el siguiente enlace para actualizar tu información:
{enlace}

Este enlace te redirigirá a nuestro bot y/o página web, donde podrás ingresar tus datos faltantes de manera segura.

¡Gracias por confiar en nosotros!

Saludos,
El equipo de {business_unit.name}
"""
    try:
        send_email(business_unit.name.lower(), subject, person.email, body)
        logger.info(f"Invitación enviada a {person.email}")
    except Exception as e:
        logger.error(f"Error enviando invitación a {person.email}: {e}")