# common.py - Funciones comunes para los workflows
import logging
import re    

from django.core.files.storage import default_storage
from app.utilidades.signature.pdf_generator import (
    generate_cv_pdf, generate_contract_pdf, merge_signed_documents, generate_candidate_summary
)
from app.utilidades.signature.digital_sign import request_digital_signature
from app.utilidades.salario import calcular_neto, calcular_bruto, obtener_tipo_cambio

from app.chatbot.integrations.services import send_email, send_message, send_menu, send_image
from django.conf import settings

logger = logging.getLogger(__name__)


def send_welcome_message(user_id, platform, business_unit):
    """ Envía un mensaje de bienvenida, el logo de la unidad y el menú de servicios. """
    # Obtener el nombre de la unidad de negocio
    business_unit_name = business_unit.name.lower()

    # Definir el mensaje de bienvenida
    welcome_messages = {
        "huntred": "Bienvenido a huntRED® 🚀\nSomos expertos en encontrar el mejor talento para empresas líderes.",
        "huntred_executive": "Bienvenido a huntRED® Executive 🌟\nNos especializamos en colocación de altos ejecutivos.",
        "huntu": "Bienvenido a huntU® 🏆\nConectamos talento joven con oportunidades de alto impacto.",
        "amigro": "Bienvenido a Amigro® 🌍\nFacilitamos el acceso laboral a migrantes en Latinoamérica.",
        "sexsi": "Bienvenido a SEXSI 🔐\nAquí puedes gestionar acuerdos de consentimiento seguros y firmarlos digitalmente.",
    }

    # Obtener el logo de la unidad de negocio
    logo_urls = {
        "huntred": settings.MEDIA_URL + "huntred.png",
        "huntred_executive": settings.MEDIA_URL + "executive.png",
        "huntu": settings.MEDIA_URL + "huntu.png",
        "amigro": settings.MEDIA_URL + "amigro.png",
        "sexsi": settings.MEDIA_URL + "sexsi.png",
    }

    welcome_message = welcome_messages.get(business_unit_name, "Bienvenido a nuestra plataforma 🎉")
    logo_url = logo_urls.get(business_unit_name, settings.MEDIA_URL + "Grupo_huntRED.png")

    # Enviar mensaje de bienvenida
    send_message(platform, user_id, welcome_message, business_unit)

    # Enviar logo de la unidad de negocio
    send_image(platform, user_id, "Aquí tienes nuestro logo 📌", logo_url, business_unit)

    # Enviar menú de servicios
    send_menu(platform, user_id, business_unit)

    return "Mensaje de bienvenida enviado correctamente."

def generate_and_send_contract(candidate, client, job_position, business_unit):
    """
    Genera la Carta Propuesta para el candidato y la envía para su firma digital.
    En Huntu y HuntRED®, también se envía al cliente para su firma.
    """
    contract_path = generate_contract_pdf(candidate, client, job_position, business_unit)

    # Enviar contrato al candidato para firma digital
    request_digital_signature(
        user=candidate,
        document_path=contract_path,
        document_name=f"Carta Propuesta - {job_position.title}.pdf"
    )

    # Enviar al cliente en Huntu y HuntRED®
    if business_unit.name.lower() in ["huntu", "huntred"]:
        request_digital_signature(
            user=client,
            document_path=contract_path,
            document_name=f"Carta Propuesta - {job_position.title}.pdf"
        )

    return contract_path

def send_candidate_summary(candidate, client):
    """ Genera y envía el resumen del candidato al cliente """
    file_path = generate_candidate_summary(candidate)

    send_email(
        to=client.contact_email,
        subject=f"Resumen del candidato {candidate.full_name} - {candidate.position}",
        body="Adjunto encontrarás el resumen del candidato.",
        attachments=[file_path]
    )

    return f"Resumen de {candidate.full_name} enviado a {client.contact_email}"

def generate_final_signed_contract(candidate, business_unit):
    """
    Genera el reporte final consolidando el PDF con todas las firmas.
    """
    contract_path = f"{business_unit.name.lower()}/contracts/{candidate.id}.pdf"
    signed_path = f"{business_unit.name.lower()}/contracts/signed_{candidate.id}.pdf"

    try:
        # Unir documentos firmados
        merge_signed_documents(contract_path, signed_path)

        # Guardar archivo final
        default_storage.save(signed_path, open(signed_path, "rb"))

        return signed_path
    except Exception as e:
        return f"Error al generar documento firmado: {e}"


CURRENCY_MAP = {
    'usd': 'USD',
    'dólar': 'USD',
    'dolar': 'USD',
    'us dollars': 'USD',
    'mxn': 'MXN',
    'peso': 'MXN',
    'pesos': 'MXN',
    'pesos mexicanos': 'MXN',
    'eur': 'EUR',
    'euro': 'EUR',
    'cop': 'COP',
    'colombiano': 'COP',
    'pen': 'PEN',
    'sol': 'PEN',
    'brl': 'BRL',
    'real': 'BRL',
    'clp': 'CLP',
    'peso chileno': 'CLP'
}

def extraer_moneda(mensaje):
    """
    Extrae la divisa a partir del mensaje usando sinónimos comunes.
    """
    mensaje = mensaje.lower()
    for key, value in CURRENCY_MAP.items():
        if key in mensaje:
            return value
    return 'MXN'  # Valor por defecto

def parsear_mensaje(mensaje):
    data = {}

    # Buscar salario-bruto
    match_bruto = re.search(r'salario[-\s]?bruto\s*=\s*([\d,\.]+k?)', mensaje, re.IGNORECASE)
    if match_bruto:
        data['salario_bruto'] = normalizar_numero(match_bruto.group(1))
    
    # Buscar salario-neto
    match_neto = re.search(r'salario[-\s]?neto\s*=\s*([\d,\.]+k?)', mensaje, re.IGNORECASE)
    if match_neto:
        data['salario_neto'] = normalizar_numero(match_neto.group(1))
    
    # Extraer moneda usando el diccionario
    data['moneda'] = extraer_moneda(mensaje)
    
    # Buscar periodo: anual o mensual
    match_periodo = re.search(r'\b(anual|mensual)\b', mensaje, re.IGNORECASE)
    if match_periodo:
        data['periodo'] = match_periodo.group(1).lower()
    else:
        data['periodo'] = 'mensual'
    
    # Buscar bono
    match_bono = re.search(r'(\d+)\s*mes(?:es)?\s*de\s*bono', mensaje, re.IGNORECASE)
    if match_bono:
        data['bono'] = int(match_bono.group(1))
    
    # Detectar si se indica "sin prestaciones adicionales"
    if re.search(r'sin prestaciones adicionales', mensaje, re.IGNORECASE):
        data['prestaciones_adicionales'] = False
    else:
        data['prestaciones_adicionales'] = True

    return data

def calcular_salario_chatbot(mensaje):
    """
    Calcula el salario basado en la información extraída del mensaje del chatbot, 
    incluyendo salario bruto/neto, periodo, moneda, bono y prestaciones adicionales.
    """
    data = parsear_mensaje(mensaje)
    
    # Si tenemos salario-bruto
    if 'salario_bruto' in data:
        salario_bruto = data['salario_bruto']
        if data.get('periodo') == 'anual':
            salario_bruto /= 12  # Convertir a mensual

        # Si hay bono, lo sumamos
        if 'bono' in data:
            salario_bruto += (salario_bruto * data['bono']) / 12
        
        # Obtener tipo de cambio actualizado para la moneda de destino
        tipo_cambio = obtener_tipo_cambio(data.get('moneda', 'USD'))

        # Calcular el salario neto
        resultado = calcular_neto(
            salario_bruto,
            tipo_trabajador='asalariado',
            incluye_prestaciones=data.get('prestaciones_adicionales', False),
            moneda=data.get('moneda', 'MXN'),
            tipo_cambio=tipo_cambio
        )
    elif 'salario_neto' in data:
        salario_neto = data['salario_neto']
        if data.get('periodo') == 'anual':
            salario_neto /= 12  # Convertir a mensual
        
        # Obtener tipo de cambio actualizado para la moneda de destino
        tipo_cambio = obtener_tipo_cambio(data.get('moneda', 'USD'))

        # Calcular el salario bruto
        resultado = calcular_bruto(
            salario_neto,
            tipo_trabajador='asalariado',
            incluye_prestaciones=data.get('prestaciones_adicionales', False),
            moneda=data.get('moneda', 'MXN'),
            tipo_cambio=tipo_cambio
        )

    return f"El resultado del cálculo es: {resultado}"