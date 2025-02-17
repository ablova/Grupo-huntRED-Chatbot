# huntred.py - Workflow para HuntRED
from celery import shared_task
from app.models import Candidate, Process
from app.chatbot.workflow.common import send_candidate_summary

@shared_task
def process_huntred_candidate(candidate_id):
    """ Ejecuta el workflow cuando un candidato es contratado en HuntRED """
    candidate = Candidate.objects.get(id=candidate_id)
    process = Process.objects.filter(candidate=candidate).first()

    if not process or not process.client:
        return "Candidato sin proceso o cliente asignado."

    send_candidate_summary(candidate, process.client)

    send_email(
        to="legal@huntred.com",
        subject=f"Confirmación de contratación: {candidate.full_name} - {candidate.position}",
        body=f"El candidato {candidate.full_name} ha sido contratado en {process.client.name}."
    )

    return f"Flujo de HuntRED ejecutado para {candidate.full_name}"

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