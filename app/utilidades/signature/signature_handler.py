# signature_handler.py - Manejo centralizado de firma electrónica y validación de identidad
from app.utilidades.pdf_generator import generate_contract_pdf
from app.utilidades.digital_sign import request_digital_signature
from django.core.files.storage import default_storage

def generate_and_send_contract(candidate, client, job_position, business_unit):
    """
    Genera la Carta Propuesta y la envía para su firma digital.
    """
    contract_path = f"{business_unit.name.lower()}/contracts/{candidate.id}.pdf"

    # Generar PDF con las condiciones laborales
    file_path = generate_contract_pdf(candidate, client, job_position, contract_path)

    # Enviar contrato al candidato para firma digital
    request_digital_signature(
        user=candidate,
        document_path=file_path,
        document_name=f"Carta Propuesta {job_position.title}.pdf"
    )

    # Enviar al cliente en Huntu y HuntRED®
    if business_unit.name.lower() in ["huntu", "huntred"]:
        request_digital_signature(
            user=client,
            document_path=file_path,
            document_name=f"Carta Propuesta {job_position.title}.pdf"
        )

    return file_path