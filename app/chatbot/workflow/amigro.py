# home/pablo/app/chatbot/workflow/amigro.py

import os
import datetime
import logging
from celery import shared_task
from app.models import Person, Vacante, BusinessUnit, Application
from app.utilidades.signature.pdf_generator import generate_contract_pdf
from app.utilidades.signature.digital_sign import request_digital_signature
from app.chatbot.integrations.services import send_email, send_message, send_options, send_menu, MENU_OPTIONS_BY_BU

logger = logging.getLogger(__name__)

# Diccionario de países frecuentes basado en volumen histórico de migración a México
PAISES_FRECUENTES = [
    {"title": "El Salvador", "payload": "El Salvador"},
    {"title": "Guatemala", "payload": "Guatemala"},
    {"title": "Honduras", "payload": "Honduras"},
    {"title": "Estados Unidos", "payload": "Estados Unidos"},
    {"title": "Otros", "payload": "otros_pais"}
]

# Opciones de estatus migratorio
ESTATUS_MIGRATORIO = [
    {"title": "Residente Permanente", "payload": "residente_permanente"},
    {"title": "Residente Temporal", "payload": "residente_temporal"},
    {"title": "Sin Documentación", "payload": "sin_documentacion"},
    {"title": "En Trámite", "payload": "en_tramite"},
    {"title": "Otro", "payload": "otro_estatus"}
]

async def continuar_perfil_amigro(plataforma: str, user_id: str, unidad_negocio: BusinessUnit, estado_chat: ChatState, persona: Person):
    """Continúa el flujo conversacional para Amigro con campos específicos e interactivos."""
    bu_name = unidad_negocio.name.lower()

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
        elif estado_chat.context.get('tipo_candidato') == "extranjero":
            if estado_chat.state != "waiting_for_pais":
                await send_message(plataforma, user_id, "¿De qué país vienes? Selecciona una opción:", bu_name)
                await send_options(plataforma, user_id, "Elige tu país:", PAISES_FRECUENTES, bu_name)
                estado_chat.state = "waiting_for_pais"
                await sync_to_async(estado_chat.save)()
            return
        return

    # Preguntar estatus migratorio
    if "migratory_status" not in persona.metadata:
        if estado_chat.state != "waiting_for_migratory_status":
            await send_message(plataforma, user_id, "¿Cuál es tu estatus migratorio actual en México?", bu_name)
            await send_options(plataforma, user_id, "Selecciona una opción:", ESTATUS_MIGRATORIO, bu_name)
            estado_chat.state = "waiting_for_migratory_status"
            await sync_to_async(estado_chat.save)()
        return

    # Perfil completo
    recap_message = await obtener_resumen_perfil(persona)
    await send_message(plataforma, user_id, recap_message, bu_name)
    estado_chat.state = "profile_complete_pending_confirmation"
    await sync_to_async(estado_chat.save)()

async def create_or_update_profile(platform, user_id, person, chat_state, business_unit):
    """Flujo específico para Amigro."""
    from app.chatbot.workflow.common import create_or_update_profile as common_profile

    # Ejecutar flujo común primero
    await common_profile(platform, user_id, person, chat_state, business_unit)

    if chat_state.state == "profile_basic_complete":
        if not person.nacionalidad:
            await send_message(platform, user_id, "¿Cuál es tu nacionalidad?", "amigro")
            chat_state.state = "waiting_for_nacionalidad"
            await sync_to_async(chat_state.save)()
            return
        if "migratory_status" not in person.metadata:
            await send_message(platform, user_id, "¿Cuál es tu estatus migratorio? (Ej. Residente, Temporal)", "amigro")
            chat_state.state = "waiting_for_migratory_status"
            await sync_to_async(chat_state.save)()
            return

        # Perfil completo para Amigro
        await send_message(platform, user_id, "¡Listo! Tu perfil para Amigro está completo. ¿En qué te ayudo ahora?", "amigro")
        chat_state.state = "idle"
        await sync_to_async(chat_state.save)()
        
async def send_amigro_specific_menu(platform: str, user_id: str, business_unit: BusinessUnit):
    services = Services(business_unit)
    amigro_options = MENU_OPTIONS_BY_BU["amigro"]
    # Personalización específica si es necesario
    await services.send_menu(platform, user_id)  # Usa el menú de amigro directamente

@shared_task
def process_amigro_candidate(candidate_id):
    """Genera la Carta Propuesta y la envía para firma digital en Amigro."""
    candidate = Person.objects.get(id=candidate_id)
    application = Application.objects.filter(user=candidate).first()

    if not application or not application.vacancy:
        return "Candidato sin vacante asignada."

    # Generar y enviar contrato para firma digital
    generate_and_send_contract(candidate, application.vacancy, application.vacancy.titulo, application.business_unit)

    return f"Contrato generado y enviado a {candidate.nombre}"

# Diccionario dinámico de despachos migratorios por país
MIGRATION_AGENCIES = {
    "USA": "us_migration@amigro.org",
    "Canada": "ca_migration@amigro.org",
    "Spain": "es_migration@amigro.org",
    "default": "global_migration@amigro.org"
}

def get_migration_agency(candidate):
    """ Retorna el correo del despacho migratorio según el país del candidato. """
    return MIGRATION_AGENCIES.get(candidate.nationality, MIGRATION_AGENCIES["default"])

@shared_task
def generate_candidate_summary_task(candidate_id):
    """ Genera un documento PDF con el resumen del candidato y lo envía al cliente. """
    candidate = Candidate.objects.get(id=candidate_id)
    process = Process.objects.filter(candidate=candidate).first()
    client = process.client if process else None
    job_position = process.job_position if process else None

    if not client or not job_position:
        return "No client or job position assigned for candidate."

    # Generar el documento
    file_path = generate_candidate_summary(candidate)
    
    # Enviar el documento al cliente
    send_email(
        to=client.contact_email,
        subject=f"Resumen del candidato {candidate.full_name} - {job_position.title}",
        body="Adjunto encontrarás el resumen del candidato.",
        attachments=[file_path]
    )
    
    # Guardar una copia en el sistema
    default_storage.save(f"candidate_summaries/{candidate.id}.pdf", open(file_path, "rb"))
    
    return f"Resumen de {candidate.full_name} enviado a {client.contact_email}"

@shared_task
def send_migration_docs_task(candidate_id):
    """ Envía la documentación al despacho migratorio si el candidato no es mexicano. """
    candidate = Candidate.objects.get(id=candidate_id)
    process = Process.objects.filter(candidate=candidate).first()
    job_position = process.job_position if process else None

    if candidate.nationality.lower() == "mexicano":
        return "El candidato es mexicano. No se requiere gestión migratoria."

    migration_agency_email = get_migration_agency(candidate)

    send_email(
        to=migration_agency_email,
        subject=f"Documentación de {candidate.full_name} - {job_position.title}",
        body="Adjunto encontrarás la documentación del candidato.",
        attachments=[candidate.documents]
    )

    # Notificar a legal@amigro.org con copia
    send_email(
        to="legal@amigro.org",
        subject=f"Copia: Documentación de {candidate.full_name} - {job_position.title}",
        body=f"Se ha enviado la documentación de {candidate.full_name} al despacho migratorio.",
        cc=[migration_agency_email]
    )

    return f"Documentación de {candidate.full_name} enviada a {migration_agency_email}"

@shared_task
def follow_up_migration_task(candidate_id):
    """ Hace seguimiento al despacho migratorio después de unos días. """
    candidate = Candidate.objects.get(id=candidate_id)
    process = Process.objects.filter(candidate=candidate).first()
    job_position = process.job_position if process else None

    migration_agency_email = get_migration_agency(candidate)

    send_email(
        to=migration_agency_email,
        subject=f"Seguimiento: {candidate.full_name} - {job_position.title}",
        body=f"¿Podrían proporcionarnos una actualización sobre el proceso de {candidate.full_name}?",
        cc=["legal@amigro.org"]
    )

    return f"Seguimiento enviado al despacho migratorio para {candidate.full_name}"

@shared_task
def notify_legal_on_hire(candidate_id):
    """ Notifica a legal@amigro.org cuando un candidato es contratado. """
    candidate = Candidate.objects.get(id=candidate_id)
    process = Process.objects.filter(candidate=candidate).first()
    job_position = process.job_position if process else None

    if not job_position:
        return "No job position assigned for candidate."

    email_recipient = "legal@amigro.org"
    email_subject = f"Contratación Confirmada: {candidate.full_name} - {job_position.title}"
    email_body = (
        f"El candidato {candidate.full_name} ha sido contratado para la posición {job_position.title}.\n\n"
        f"Cliente: {process.client.name if process.client else 'No asignado'}\n"
        f"Fecha: {datetime.date.today()}"
    )

    try:
        send_email(to=email_recipient, subject=email_subject, body=email_body)
        return f"Notificación de contratación enviada para {candidate.full_name}"
    except Exception as e:
        return f"Error al enviar la notificación: {str(e)}"