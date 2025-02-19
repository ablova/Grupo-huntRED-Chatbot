# home/pablo/app/chatbot/workflow/amigro.py

import os
import datetime
from celery import shared_task
from app.models import Person, Vacante, BusinessUnit, Application
from app.utilidades.signature.pdf_generator import generate_contract_pdf
from app.utilidades.signature.digital_sign import request_digital_signature
from app.chatbot.integrations.services import EmailService



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

    send_email(
        to="legal@amigro.org",
        subject=f"Contratación Confirmada: {candidate.full_name} - {job_position.title}",
        body=f"El candidato {candidate.full_name} ha sido contratado para la posición {job_position.title}.\n\n"
             f"Cliente: {process.client.name if process.client else 'No asignado'}\n"
             f"Fecha: {datetime.date.today()}",
    )

    return f"Notificación de contratación enviada para {candidate.full_name}"