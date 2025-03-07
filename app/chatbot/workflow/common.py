# /home/pablo/app/chatbot/workflow/common.py - Funciones comunes para los workflows
import logging
import re    
from forex_python.converter import CurrencyRates
from django.core.files.storage import default_storage
from app.utilidades.signature.pdf_generator import (
    generate_cv_pdf, generate_contract_pdf, merge_signed_documents, generate_candidate_summary
)
from app.utilidades.signature.digital_sign import request_digital_signature
from app.utilidades.salario import calcular_neto, calcular_bruto, calcular_isr_mensual, calcular_cuotas_imss, obtener_tipo_cambio
# from currency_converter import CurrencyRates  # Se esta utilizando forex-python el cual ya esta instalado.

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
    # Estados Unidos
    'usd': 'USD', 'dólar': 'USD', 'dolar': 'USD', 'dolares': 'USD', 'dólares': 'USD',
    # México
    'mxn': 'MXN', 'peso': 'MXN', 'pesos': 'MXN', 'peso mexicano': 'MXN', 'pesos mexicanos': 'MXN',
    # Nicaragua
    'nio': 'NIO', 'córdoba': 'NIO', 'cordoba': 'NIO', 'cordobas': 'NIO', 'córdobas': 'NIO',
    # Colombia
    'cop': 'COP', 'peso colombiano': 'COP', 'pesos colombianos': 'COP',
    # Argentina
    'ars': 'ARS', 'peso argentino': 'ARS', 'pesos argentinos': 'ARS',
    # Brasil
    'brl': 'BRL', 'real': 'BRL', 'reales': 'BRL',
    # Chile
    'clp': 'CLP', 'peso chileno': 'CLP', 'pesos chilenos': 'CLP',
    # Ecuador (actualmente usa USD, anteriormente Sucre - ECS)
    'ecs': 'ECS', 'sucre': 'ECS', 'sucres': 'ECS',
    # Perú
    'pen': 'PEN', 'sol': 'PEN', 'soles': 'PEN', 'sol peruano': 'PEN', 'soles peruanos': 'PEN',
    # Uruguay
    'uyu': 'UYU', 'peso uruguayo': 'UYU', 'pesos uruguayos': 'UYU',
    # Paraguay
    'pyg': 'PYG', 'guaraní': 'PYG', 'guarani': 'PYG', 'guaranies': 'PYG', 'guaraníes': 'PYG',
    # Panamá (oficial USD, también usa balboa - PAB)
    'pab': 'PAB', 'balboa': 'PAB', 'balboas': 'PAB',
    # República Dominicana
    'dop': 'DOP', 'peso dominicano': 'DOP', 'pesos dominicanos': 'DOP',
    # Bolivia
    'bob': 'BOB', 'boliviano': 'BOB', 'bolivianos': 'BOB',
    # Cuba
    'cup': 'CUP', 'peso cubano': 'CUP', 'pesos cubanos': 'CUP',
    # Costa Rica
    'crc': 'CRC', 'colón': 'CRC', 'colon': 'CRC', 'colones': 'CRC',
    # Guatemala
    'gtq': 'GTQ', 'quetzal': 'GTQ', 'quetzales': 'GTQ',
    # Haití
    'htg': 'HTG', 'gourde': 'HTG', 'gourdes': 'HTG',
    # Honduras
    'hnl': 'HNL', 'lempira': 'HNL', 'lempiras': 'HNL',
    # India (alta migración global hacia EE.UU.)
    'inr': 'INR', 'rupia': 'INR', 'rupias': 'INR', 'rupia india': 'INR',
    # China (ya incluida, pero relevante para migración)
    'cny': 'CNY', 'yuan': 'CNY', 'renminbi': 'CNY',
    # Filipinas (alta migración hacia EE.UU.)
    'php': 'PHP', 'peso filipino': 'PHP', 'pesos filipinos': 'PHP',
    # Principales monedas internacionales
    'eur': 'EUR', 'euro': 'EUR', 'euros': 'EUR',
    'gbp': 'GBP', 'libra esterlina': 'GBP', 'libras esterlinas': 'GBP', 'libra': 'GBP',
    'cad': 'CAD', 'dólar canadiense': 'CAD', 'dolar canadiense': 'CAD',
    'jpy': 'JPY', 'yen': 'JPY', 'yenes': 'JPY',
    'cny': 'CNY', 'yuan': 'CNY', 'renminbi': 'CNY',
    'chf': 'CHF', 'franco suizo': 'CHF', 'francos suizos': 'CHF',
    'aud': 'AUD', 'dólar australiano': 'AUD', 'dolar australiano': 'AUD',

    # Opcional: Criptomonedas principales
    'btc': 'BTC', 'bitcoin': 'BTC', 'bitcoins': 'BTC',
    'eth': 'ETH', 'ethereum': 'ETH',
    'usdt': 'USDT', 'tether': 'USDT',
}

import re

def normalizar_numero(valor_str):
    """Convierte un string numérico (ej. '10k', '12,345.67') a float."""
    valor_str = valor_str.lower().replace(',', '')
    if 'k' in valor_str:
        return float(valor_str.replace('k', '')) * 1000
    return float(valor_str)

def extraer_moneda(mensaje):
    """Extrae la moneda del mensaje usando CURRENCY_MAP."""
    mensaje = mensaje.lower()
    for key, value in CURRENCY_MAP.items():
        if key in mensaje:
            return value
    return 'MXN'  # Por defecto

def parsear_mensaje(mensaje):
    data = {}
    mensaje = mensaje.lower()

    # Buscar salario bruto
    match_bruto = re.search(r'salario[-\s]?bruto\s*=\s*([\d,\.]+k?)', mensaje, re.IGNORECASE)
    if match_bruto:
        data['salario_bruto'] = normalizar_numero(match_bruto.group(1))
        data['tipo'] = 'bruto'
    
    # Buscar salario neto
    match_neto = re.search(r'salario[-\s]?neto\s*=\s*([\d,\.]+k?)', mensaje, re.IGNORECASE)
    if match_neto:
        data['salario_neto'] = normalizar_numero(match_neto.group(1))
        data['tipo'] = 'neto'

    # Si no se especifica bruto o neto, buscar un valor genérico
    if 'salario_bruto' not in data and 'salario_neto' not in data:
        match_valor = re.search(r'(\d+(?:[,\.]\d+)?k?)', mensaje)
        if match_valor:
            data['salario_bruto'] = normalizar_numero(match_valor.group(1))
            data['tipo'] = 'bruto'  # Por defecto

    # Frecuencia
    if 'hora' in mensaje:
        data['frecuencia'] = 'hora'
    elif 'semanal' in mensaje:
        data['frecuencia'] = 'semanal'
    elif 'quincenal' in mensaje:
        data['frecuencia'] = 'quincenal'
    elif 'mensual' in mensaje:
        data['frecuencia'] = 'mensual'
    elif 'anual' in mensaje:
        data['frecuencia'] = 'anual'
    else:
        data['frecuencia'] = 'mensual'  # Por defecto

    # Moneda
    data['moneda'] = extraer_moneda(mensaje)

    # Bono
    match_bono = re.search(r'(\d+)\s*mes(?:es)?\s*de\s*bono', mensaje, re.IGNORECASE)
    if match_bono:
        data['bono'] = int(match_bono.group(1))
    else:
        data['bono'] = 0

    # Prestaciones adicionales
    if re.search(r'sin prestaciones adicionales', mensaje, re.IGNORECASE):
        data['prestaciones_adicionales'] = False
    else:
        data['prestaciones_adicionales'] = True

    return data

def get_business_unit_domain(business_unit):
    domains = {
        "huntred": "huntred.com",
        "huntred_executive": "executive.huntred.com",
        "huntu": "huntu.com",
        "amigro": "amigro.com",
        "sexsi": "sexsi.com"
    }
    return domains.get(business_unit.name.lower() if hasattr(business_unit, 'name') else business_unit, "huntred.com")

async def calcular_salario_chatbot(platform, user_id, mensaje, business_unit_name):
    data = parsear_mensaje(mensaje)
    if 'salario_bruto' not in data and 'salario_neto' not in data:
        from app.chatbot.integrations.services import send_message
        await send_message(platform, user_id, "Por favor, proporciona un salario válido.", business_unit_name)
        return

    # Obtener tipo de cambio usando exchangerate-api
    tipo_cambio = obtener_tipo_cambio(data['moneda'])
    tipo_cambio_inverso = 1 / tipo_cambio if tipo_cambio != 1.0 else 1.0

    # Estandarizar a mensual en moneda original y MXN
    valor = data['salario_bruto'] if data['tipo'] == 'bruto' else data['salario_neto']
    if data['frecuencia'] == 'hora':
        valor_mensual_orig = valor * 40 * 4
    elif data['frecuencia'] == 'semanal':
        valor_mensual_orig = valor * 4
    elif data['frecuencia'] == 'quincenal':
        valor_mensual_orig = valor * 2
    elif data['frecuencia'] == 'anual':
        valor_mensual_orig = valor / 12
    else:  # mensual
        valor_mensual_orig = valor
    valor_mensual_mxn = valor_mensual_orig * tipo_cambio

    # Ajustar bono
    if data['bono'] > 0:
        bono_anual_mxn = data['bono'] * valor_mensual_mxn
        bono_mensual_mxn = bono_anual_mxn / 12
        valor_mensual_mxn += bono_mensual_mxn
        bono_mensual_orig = bono_mensual_mxn * tipo_cambio_inverso
        valor_mensual_orig += bono_mensual_orig

    # Calcular bruto y neto en MXN
    if data['tipo'] == 'bruto':
        salario_bruto_mxn = valor_mensual_mxn
        salario_neto_mxn = calcular_neto(salario_bruto_mxn, incluye_prestaciones=data['prestaciones_adicionales'])
    else:  # neto
        salario_neto_mxn = valor_mensual_mxn
        salario_bruto_mxn = calcular_bruto(salario_neto_mxn, incluye_prestaciones=data['prestaciones_adicionales'])
    salario_bruto_orig = salario_bruto_mxn * tipo_cambio_inverso
    salario_neto_orig = salario_neto_mxn * tipo_cambio_inverso

    # Mensaje base
    msg = (
        f"Salario Bruto Mensual: {salario_bruto_orig:,.2f} {data['moneda']} ({salario_bruto_mxn:,.2f} MXN)\n"
        f"Salario Neto Mensual: {salario_neto_orig:,.2f} {data['moneda']} ({salario_neto_mxn:,.2f} MXN)\n"
        f"- ISR: {calcular_isr_mensual(salario_bruto_mxn):,.2f} MXN\n"
        f"- IMSS: {calcular_cuotas_imss(salario_bruto_mxn):,.2f} MXN\n"
        f"- Infonavit: {0.0} MXN\n"
    )

    # Comparativa bidireccional
    pais_origen = {
        'MXN': 'México', 'USD': 'USA', 'NIO': 'Nicaragua', 'COP': 'Colombia', 'ARS': 'Argentina', 'BRL': 'Brasil'
    }.get(data['moneda'], 'Otro')
    ciudad_origen = {
        'México': 'Ciudad de México', 'USA': 'Nueva York', 'Nicaragua': 'Managua', 
        'Colombia': 'Bogotá', 'Argentina': 'Buenos Aires', 'Brasil': 'São Paulo'
    }.get(pais_origen, 'Otra ciudad')

    if data['moneda'] != 'MXN':
        adjustment_coli = DATOS_COLI['Ciudad de México'] / DATOS_COLI.get(ciudad_origen, 50.0)
        adjustment_ppa = DATOS_PPA['México'] / DATOS_PPA.get(pais_origen, 1.0)
        adjustment_bigmac = DATOS_BIGMAC['México'] / DATOS_BIGMAC.get(pais_origen, 5.0)
        
        msg += (
            f"\nComparativa en México:\n"
            f"- COLI: {salario_neto_mxn * adjustment_coli:,.2f} MXN\n"
            f"- PPA: {salario_neto_mxn * adjustment_ppa:,.2f} MXN\n"
            f"- BigMac: {salario_neto_mxn * adjustment_bigmac:,.2f} MXN\n"
        )
    
    adjustment_coli_inv = DATOS_COLI.get(ciudad_origen, 50.0) / DATOS_COLI['Ciudad de México']
    adjustment_ppa_inv = DATOS_PPA.get(pais_origen, 1.0) / DATOS_PPA['México']
    adjustment_bigmac_inv = DATOS_BIGMAC.get(pais_origen, 5.0) / DATOS_BIGMAC['México']
    
    msg += (
        f"\nComparativa en {pais_origen}:\n"
        f"- COLI: {salario_neto_orig * adjustment_coli_inv:,.2f} {data['moneda']}\n"
        f"- PPA: {salario_neto_orig * adjustment_ppa_inv:,.2f} {data['moneda']}\n"
        f"- BigMac: {salario_neto_orig * adjustment_bigmac_inv:,.2f} {data['moneda']}\n"
    )

    msg += "\nReferencia: https://amigro.com/salario"
    from app.chatbot.integrations.services import send_message
    await send_message(platform, user_id, msg, business_unit_name)