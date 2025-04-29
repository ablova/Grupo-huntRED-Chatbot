# home/pablo/app/chatbot/workflow/amigro.py
# /home/pablo/app/chatbot/workflow/amigro.py
import logging
import datetime
from typing import Dict, Any, List
from celery import shared_task
from asgiref.sync import sync_to_async
from django.conf import settings
from app.models import Person, Vacante, BusinessUnit, ChatState, Application
from app.utilidades.signature.pdf_generator import generate_contract_pdf, generate_candidate_summary
from app.utilidades.signature.digital_sign import request_digital_signature
from app.chatbot.integrations.services import send_email, send_message, send_options, send_menu
from app.chatbot.workflow.common import (
    iniciar_creacion_perfil, ofrecer_prueba_personalidad, continuar_registro,
    transfer_candidate_to_new_division, get_possible_transitions
)

logger = logging.getLogger(__name__)

# Opciones de países frecuentes para migrantes
PAISES_FRECUENTES = [
    {"title": "El Salvador", "payload": "el_salvador"},
    {"title": "Cuba", "payload": "cuba"},
    {"title": "Belice", "payload": "belice"},
    {"title": "Guatemala", "payload": "guatemala"},
    {"title": "Honduras", "payload": "honduras"},
    {"title": "Venezuela", "payload": "venezuela"},
    {"title": "Estados Unidos", "payload": "estados_unidos"},
    {"title": "Otro", "payload": "otro_pais"}
]

# Opciones de estatus migratorio
ESTATUS_MIGRATORIO = [
    {"title": "Residente Permanente", "payload": "residente_permanente"},
    {"title": "Residente Temporal", "payload": "residente_temporal"},
    {"title": "Sin Documentación", "payload": "sin_documentacion"},
    {"title": "En Trámite", "payload": "en_tramite"},
    {"title": "Otro", "payload": "otro_estatus"}
]

# Diccionario de despachos migratorios por país
MIGRATION_AGENCIES = {
    "estados_unidos": "us_migration@amigro.org",
    "cuba": "cu_migration@amigro.org",
    "venezuela": "ve_migration@amigro.org",
    "default": "global_migration@amigro.org"
}

async def iniciar_flujo_amigro(plataforma: str, user_id: str, unidad_negocio: BusinessUnit, 
                             estado_chat: ChatState, persona: Person):
    """
    Inicia el flujo conversacional para Amigro.
    
    Args:
        plataforma: Plataforma de comunicación.
        user_id: ID del usuario.
        unidad_negocio: Instancia de BusinessUnit (Amigro).
        estado_chat: Instancia de ChatState.
        persona: Instancia de Person.
    """
    bu_name = unidad_negocio.name.lower()
    await send_message(plataforma, user_id, 
                      "¡Bienvenido a Amigro! 🌍 Te ayudaremos a encontrar oportunidades laborales en México. Vamos a crear tu perfil.", 
                      bu_name)
    await iniciar_creacion_perfil(plataforma, user_id, unidad_negocio, estado_chat, persona)

async def continuar_perfil_amigro(plataforma: str, user_id: str, unidad_negocio: BusinessUnit, 
                                estado_chat: ChatState, persona: Person):
    """
    Continúa el flujo conversacional para completar el perfil en Amigro.
    
    Args:
        plataforma: Plataforma de comunicación.
        user_id: ID del usuario.
        unidad_negocio: Instancia de BusinessUnit (Amigro).
        estado_chat: Instancia de ChatState.
        persona: Instancia de Person.
    """
    bu_name = unidad_negocio.name.lower()
    
    # Asegurar que metadata sea un diccionario
    if not isinstance(persona.metadata, dict):
        persona.metadata = {}
        await sync_to_async(persona.save)()

    # Recolectar datos básicos (nombre, email, teléfono)
    if not await is_profile_basic_complete(persona):
        await continuar_registro(plataforma, user_id, unidad_negocio, estado_chat, persona)
        return

    # Preguntar si es mexicano o extranjero
    if not estado_chat.context.get('tipo_candidato'):
        mensaje = "¿Eres mexicano regresando a México o extranjero ingresando a México?"
        botones = [
            {"title": "Mexicano", "payload": "mexicano"},
            {"title": "Extranjero", "payload": "extranjero"}
        ]
        await send_message(plataforma, user_id, mensaje, bu_name)
        await send_options(plataforma, user_id, "Selecciona una opción:", botones, bu_name)
        estado_chat.state = "waiting_for_tipo_candidato"
        await sync_to_async(estado_chat.save)()
        return

    # Determinar nacionalidad
    if not persona.nacionalidad:
        if estado_chat.context.get('tipo_candidato') == "mexicano":
            persona.nacionalidad = "México"
            await sync_to_async(persona.save)()
            await continuar_perfil_amigro(plataforma, user_id, unidad_negocio, estado_chat, persona)
            return
        elif estado_chat.context.get('tipo_candidato') == "extranjero":
            if estado_chat.state != "waiting_for_pais":
                await send_message(plataforma, user_id, "¿De qué país vienes? Selecciona una opción:", bu_name)
                await send_options(plataforma, user_id, "Elige tu país:", PAISES_FRECUENTES, bu_name)
                estado_chat.state = "waiting_for_pais"
                await sync_to_async(estado_chat.save)()
            return

    # Preguntar estatus migratorio
    if "migratory_status" not in persona.metadata:
        if estado_chat.state != "waiting_for_migratory_status":
            await send_message(plataforma, user_id, "¿Cuál es tu estatus migratorio actual en México?", bu_name)
            await send_options(plataforma, user_id, "Selecciona una opción:", ESTATUS_MIGRATORIO, bu_name)
            estado_chat.state = "waiting_for_migratory_status"
            await sync_to_async(estado_chat.save)()
        return

    # Verificar transiciones posibles
    qualified_transitions = await get_possible_transitions(persona, unidad_negocio)
    if qualified_transitions:
        message = "¡Felicidades! Tus habilidades sugieren que podrías calificar para una unidad superior:\n"
        options = [{"title": bu.capitalize(), "payload": f"move_to_{bu}"} for bu in qualified_transitions]
        message += "\n".join([f"{i+1}. {opt['title']}" for i, opt in enumerate(options)])
        message += "\nResponde con el número o 'No' para quedarte en Amigro."
        await send_message(plataforma, user_id, message, bu_name)
        estado_chat.state = "offering_division_change"
        estado_chat.context["possible_transitions"] = qualified_transitions
        await sync_to_async(estado_chat.save)()
        return

    # Perfil completo
    await send_message(plataforma, user_id, "¡Perfil completo! 🎉 Pronto te contactaremos con oportunidades.", bu_name)
    estado_chat.state = "completed"
    await sync_to_async(estado_chat.save)()

async def manejar_respuesta_amigro(plataforma: str, user_id: str, texto: str, 
                                 unidad_negocio: BusinessUnit, estado_chat: ChatState, 
                                 persona: Person) -> bool:
    """
    Maneja respuestas específicas de Amigro, como tipo de candidato, nacionalidad y estatus migratorio.
    
    Args:
        plataforma: Plataforma de comunicación.
        user_id: ID del usuario.
        texto: Respuesta del usuario.
        unidad_negocio: Instancia de BusinessUnit (Amigro).
        estado_chat: Instancia de ChatState.
        persona: Instancia de Person.
        
    Returns:
        bool: True si la respuesta fue manejada, False si no.
    """
    bu_name = unidad_negocio.name.lower()
    texto_lower = texto.lower().strip()

    if estado_chat.state == "waiting_for_tipo_candidato":
        if texto_lower in ["mexicano", "extranjero"]:
            estado_chat.context['tipo_candidato'] = texto_lower
            await sync_to_async(estado_chat.save)()
            await continuar_perfil_amigro(plataforma, user_id, unidad_negocio, estado_chat, persona)
        else:
            await send_message(plataforma, user_id, "Por favor, selecciona 'Mexicano' o 'Extranjero'.", bu_name)
            botones = [
                {"title": "Mexicano", "payload": "mexicano"},
                {"title": "Extranjero", "payload": "extranjero"}
            ]
            await send_options(plataforma, user_id, "Selecciona una opción:", botones, bu_name)
        return True

    if estado_chat.state == "waiting_for_pais":
        valid_paises = [opt["payload"] for opt in PAISES_FRECUENTES]
        if texto_lower in valid_paises:
            nacionalidad = next(opt["title"] for opt in PAISES_FRECUENTES if opt["payload"] == texto_lower)
            persona.nacionalidad = nacionalidad
            await sync_to_async(persona.save)()
            await send_message(plataforma, user_id, f"¡Gracias! Nacionalidad registrada: {nacionalidad}.", bu_name)
            estado_chat.state = "profile_in_progress"
            await sync_to_async(estado_chat.save)()
            await continuar_perfil_amigro(plataforma, user_id, unidad_negocio, estado_chat, persona)
        else:
            await send_message(plataforma, user_id, "Por favor, selecciona un país válido.", bu_name)
            await send_options(plataforma, user_id, "Elige tu país:", PAISES_FRECUENTES, bu_name)
        return True

    if estado_chat.state == "waiting_for_migratory_status":
        valid_statuses = [opt["payload"] for opt in ESTATUS_MIGRATORIO]
        if texto_lower in valid_statuses:
            persona.metadata['migratory_status'] = texto_lower
            await sync_to_async(persona.save)()
            await send_message(plataforma, user_id, "¡Gracias! Tu estatus migratorio ha sido registrado.", bu_name)
            estado_chat.state = "profile_in_progress"
            await sync_to_async(estado_chat.save)()
            await continuar_perfil_amigro(plataforma, user_id, unidad_negocio, estado_chat, persona)
        else:
            await send_message(plataforma, user_id, "Por favor, selecciona una opción válida.", bu_name)
            await send_options(plataforma, user_id, "Selecciona una opción:", ESTATUS_MIGRATORIO, bu_name)
        return True

    return False

async def is_profile_basic_complete(persona: Person) -> bool:
    """
    Verifica si los datos básicos del perfil están completos.
    
    Args:
        persona: Instancia de Person.
        
    Returns:
        bool: True si los datos básicos están completos, False si no.
    """
    required_fields = ['nombre', 'email', 'phone']
    return all(getattr(persona, field, None) for field in required_fields)

async def is_profile_complete_amigro(persona: Person) -> bool:
    """
    Verifica si el perfil está completo para Amigro.
    
    Args:
        persona: Instancia de Person.
        
    Returns:
        bool: True si el perfil está completo, False si no.
    """
    return await is_profile_basic_complete(persona) and bool(persona.nacionalidad and persona.metadata.get('migratory_status'))

def get_migration_agency(persona: Person) -> str:
    """Retorna el correo del despacho migratorio según la nacionalidad."""
    nacionalidad = persona.nacionalidad.lower() if persona.nacionalidad else ""
    return MIGRATION_AGENCIES.get(nacionalidad, MIGRATION_AGENCIES["default"])

# /home/pablo/app/chatbot/workflow/amigro.py (solo tareas de Celery ajustadas)
@shared_task
def process_amigro_candidate(person_id: int):
    """
    Procesa un candidato de Amigro, generando contratos.
    
    Args:
        person_id: ID de la persona.
    """
    try:
        person = Person.objects.get(id=person_id)
        application = Application.objects.filter(user=person).first()
        if not application or not application.vacancy:
            return "Candidato sin vacante asignada."

        contract_path = generate_contract_pdf(person, None, application.vacancy.titulo, person.business_unit)
        request_digital_signature(
            user=person,
            document_path=contract_path,
            document_name=f"Carta Propuesta - {application.vacancy.titulo}.pdf"
        )
        return f"Contrato generado y enviado a {person.nombre}"
    except Person.DoesNotExist:
        logger.error(f"Candidato {person_id} no encontrado.")
        return "Candidato no encontrado."
    except Exception as e:
        logger.error(f"Error procesando candidato {person_id}: {e}", exc_info=True)
        return f"Error: {str(e)}"

@shared_task
def generate_candidate_summary_task(person_id: int):
    """
    Genera un documento PDF con el resumen del candidato y lo envía al cliente.
    
    Args:
        person_id: ID de la persona.
    """
    try:
        person = Person.objects.get(id=person_id)
        application = Application.objects.filter(user=person).first()
        if not application or not application.vacancy or not application.vacancy.empresa:
            return "No cliente o vacante asignada para el candidato."

        file_path = generate_candidate_summary(person)
        send_email(
            to=application.vacancy.empresa.contact_email if hasattr(application.vacancy.empresa, 'contact_email') else "hola@huntred.com",
            subject=f"Resumen del candidato {person.nombre} - {application.vacancy.titulo}",
            body="Adjunto encontrarás el resumen del candidato.",
            attachments=[file_path]
        )
        default_storage.save(f"candidate_summaries/{person.id}.pdf", open(file_path, "rb"))
        return f"Resumen de {person.nombre} enviado"
    except Person.DoesNotExist:
        logger.error(f"Candidato {person_id} no encontrado.")
        return "Candidato no encontrado."
    except Exception as e:
        logger.error(f"Error generando resumen para {person_id}: {e}", exc_info=True)
        return f"Error: {str(e)}"

@shared_task
def send_migration_docs_task(person_id: int):
    """
    Envía documentación al despacho migratorio si el candidato no es mexicano.
    
    Args:
        person_id: ID de la persona.
    """
    try:
        person = Person.objects.get(id=person_id)
        if person.nacionalidad.lower() == "méxico":
            return "El candidato es mexicano. No se requiere gestión migratoria."

        application = Application.objects.filter(user=person).first()
        if not application or not application.vacancy:
            return "No vacante asignada para el candidato."

        migration_agency_email = get_migration_agency(person)
        send_email(
            to=migration_agency_email,
            subject=f"Documentación de {person.nombre} - {application.vacancy.titulo}",
            body="Adjunto encontrarás la documentación del candidato.",
            attachments=[person.metadata.get('documents', [])]
        )
        send_email(
            to="legal@amigro.org",
            subject=f"Copia: Documentación de {person.nombre} - {application.vacancy.titulo}",
            body=f"Se ha enviado la documentación de {person.nombre} al despacho migratorio.",
            cc=[migration_agency_email]
        )
        return f"Documentación de {person.nombre} enviada a {migration_agency_email}"
    except Person.DoesNotExist:
        logger.error(f"Candidato {person_id} no encontrado.")
        return "Candidato no encontrado."
    except Exception as e:
        logger.error(f"Error enviando documentación para {person_id}: {e}", exc_info=True)
        return f"Error: {str(e)}"

@shared_task
def follow_up_migration_task(person_id: int):
    """
    Hace seguimiento al despacho migratorio después de unos días.
    
    Args:
        person_id: ID de la persona.
    """
    try:
        person = Person.objects.get(id=person_id)
        application = Application.objects.filter(user=person).first()
        if not application or not application.vacancy:
            return "No vacante asignada para el candidato."

        migration_agency_email = get_migration_agency(person)
        send_email(
            to=migration_agency_email,
            subject=f"Seguimiento: {person.nombre} - {application.vacancy.titulo}",
            body=f"¿Podrían proporcionarnos una actualización sobre el proceso de {person.nombre}?",
            cc=["legal@amigro.org"]
        )
        return f"Seguimiento enviado al despacho migratorio para {person.nombre}"
    except Person.DoesNotExist:
        logger.error(f"Candidato {person_id} no encontrado.")
        return "Candidato no encontrado."
    except Exception as e:
        logger.error(f"Error enviando seguimiento para {person_id}: {e}", exc_info=True)
        return f"Error: {str(e)}"

@shared_task
def notify_legal_on_hire(person_id: int):
    """
    Notifica a legal@amigro.org cuando un candidato es contratado.
    
    Args:
        person_id: ID de la persona.
    """
    try:
        person = Person.objects.get(id=person_id)
        application = Application.objects.filter(user=person, status='hired').first()
        if not application or not application.vacancy:
            return "No vacante asignada o candidato no contratado."

        email_subject = f"Contratación Confirmada: {person.nombre} - {application.vacancy.titulo}"
        email_body = (
            f"El candidato {person.nombre} ha sido contratado para la posición {application.vacancy.titulo}.\n\n"
            f"Empresa: {application.vacancy.empresa.name if application.vacancy.empresa else 'No asignada'}\n"
            f"Fecha: {datetime.date.today()}"
        )
        send_email(to="legal@amigro.org", subject=email_subject, body=email_body)
        return f"Notificación de contratación enviada para {person.nombre}"
    except Person.DoesNotExist:
        logger.error(f"Candidato {person_id} no encontrado.")
        return "Candidato no encontrado."
    except Exception as e:
        logger.error(f"Error enviando notificación para {person_id}: {e}", exc_info=True)
        return f"Error: {str(e)}"