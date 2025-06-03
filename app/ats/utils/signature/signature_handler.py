# signature_handler.py - Manejo centralizado de firma electrónica y validación de identidad
from app.ats.utils.pdf_generator import generate_contract_pdf
from app.ats.utils.signature.digital_signature_providers import get_signature_provider
from django.core.files.storage import default_storage

def generate_and_send_contract(candidate, client, job_position, business_unit):
    """
    Genera la Carta Propuesta y la envía para su firma digital.
    """
    contract_path = f"{business_unit.name.lower()}/contracts/{candidate.id}.pdf"

    # Generar PDF con las condiciones laborales
    file_path = generate_contract_pdf(candidate, client, job_position, contract_path)

    # Obtener el proveedor de firma digital configurado
    signature_provider = get_signature_provider(business_unit.name)

    # Preparar destinatarios
    recipients = [
        {
            "email": candidate.email,
            "name": f"{candidate.first_name} {candidate.last_name}"
        }
    ]
    
    # Agregar cliente para Huntu y HuntRED®
    if business_unit.name.lower() in ["huntu", "huntred"]:
        recipients.append({
            "email": client.email,
            "name": f"{client.first_name} {client.last_name}"
        })

    # Crear solicitud de firma
    signature_request = signature_provider.create_signature_request(
        document_path=file_path,
        recipients=recipients
    )

    return {
        "file_path": file_path,
        "signature_request": signature_request
    }