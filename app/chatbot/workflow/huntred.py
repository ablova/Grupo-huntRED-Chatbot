# huntred.py - Workflow para HuntRED
from celery import shared_task
from app.models import Candidate, Process
from app.chatbot.workflow.common import send_candidate_summary
from app.utilidades.signature.pdf_generator import generate_contract_pdf

@shared_task
def process_huntred_candidate(candidate_id):
    """Genera la Carta Propuesta y la envía para firma digital en HuntRED."""
    candidate = Candidate.objects.get(id=candidate_id)
    process = Process.objects.filter(candidate=candidate).first()

    if not process or not process.client:
        return "Candidato sin proceso o cliente asignado."

    # Generar y enviar contrato para firma digital
    contract_path = generate_contract_pdf(candidate, process.client, process.job_position, process.business_unit)

    request_digital_signature(
        user=candidate,
        document_path=contract_path,
        document_name=f"Carta Propuesta - {process.job_position.title}.pdf"
    )

    send_email(
        business_unit_name="huntred",
        subject=f"Carta Propuesta - {process.job_position.title}",
        to_email=candidate.email,
        body="Adjunto encontrarás tu carta propuesta.",
        from_email="notificaciones@huntred.com",
    )

    return f"Contrato generado y enviado a {candidate.full_name}"

from celery import shared_task
from app.models import Candidate, Process
from app.chatbot.workflow.common import generate_and_send_contract

@shared_task
def process_huntred_candidate(candidate_id):
    """ Genera la Carta Propuesta y la envía para firma digital en HuntRED. """
    candidate = Candidate.objects.get(id=candidate_id)
    process = Process.objects.filter(candidate=candidate).first()

    if not process or not process.client:
        return "Candidato sin proceso o cliente asignado."

    # Generar y enviar contrato para firma digital
    generate_and_send_contract(candidate, process.client, process.job_position, process.business_unit)

    return f"Contrato generado y enviado a {candidate.full_name}"