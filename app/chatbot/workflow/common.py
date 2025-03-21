# /home/pablo/app/chatbot/workflow/common.py
import logging
import re
from forex_python.converter import CurrencyRates
from django.core.files.storage import default_storage
from app.utilidades.signature.pdf_generator import (
    generate_cv_pdf, generate_contract_pdf, merge_signed_documents, generate_candidate_summary
)
from app.utilidades.signature.digital_sign import request_digital_signature
from app.utilidades.salario import (
    calcular_neto, calcular_bruto, calcular_isr_mensual, calcular_cuotas_imss, 
    obtener_tipo_cambio, DATOS_PPA, DATOS_COLI, DATOS_BIGMAC, UMA_DIARIA_2025
)
from app.chatbot.integrations.services import send_email, send_message, send_options, send_image
from app.models import BusinessUnit, ConfiguracionBU, Person, ChatState
from django.conf import settings
from urllib.parse import urlparse
from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)

# Diccionario de explicaciones para los métodos de creación de perfil
EXPLICACIONES_METODOS = {
    "default": {
        "dynamic": "Te haré preguntas una por una para completar tu perfil paso a paso.",
        "template": "Te enviaré un formulario inteligente para que llenes tus datos de una vez (solo en WhatsApp).",
        "cv": "Envía tu CV y extraeré automáticamente la información para tu perfil."
    },
    "amigro": {
        "dynamic": "Ideal si prefieres una conversación guiada sobre tu situación migratoria y experiencia.",
        "template": "Perfecto si quieres ingresar tus datos rápidamente en un solo paso (solo en WhatsApp).",
        "cv": "Si ya tienes un CV, puedo analizarlo para ahorrarte tiempo."
    },
    "huntu": {
        "dynamic": "Te guiaré para destacar tus habilidades como recién egresado.",
        "template": "Llena un formulario rápido para enfocarte en tus logros académicos (solo en WhatsApp).",
        "cv": "Envía tu CV y lo adaptaré a las oportunidades para jóvenes profesionales."
    },
    "huntred": {
        "dynamic": "Te ayudaré a detallar tu experiencia profesional paso a paso.",
        "template": "Ingresa tus datos clave en un formulario rápido (solo en WhatsApp).",
        "cv": "Sube tu CV y lo analizaré para encontrar las mejores vacantes ejecutivas."
    }
}

def obtener_explicaciones_metodos(bu_name: str) -> dict:
    """Devuelve las explicaciones de los métodos según la unidad de negocio."""
    return EXPLICACIONES_METODOS.get(bu_name.lower(), EXPLICACIONES_METODOS["default"])

async def iniciar_creacion_perfil(plataforma: str, user_id: str, unidad_negocio: BusinessUnit, estado_chat: ChatState, persona: Person):
    """Inicia la creación del perfil ofreciendo tres opciones al usuario."""
    bu_name = unidad_negocio.name.lower()

    if estado_chat.state != "asking_profile_method":
        explicaciones = obtener_explicaciones_metodos(bu_name)
        mensaje = (
            "¿Cómo prefieres crear tu perfil?\n\n"
            f"**Dinámico**: {explicaciones['dynamic']}\n"
            f"**Formulario**: {explicaciones['template']}\n"
            f"**CV**: {explicaciones['cv']}\n\n"
            "Selecciona una opción:"
        )
        botones = [
            {"title": "Dinámico", "payload": "profile_dynamic"},
            {"title": "Formulario", "payload": "profile_template"},
            {"title": "CV", "payload": "profile_cv"}
        ]
        await send_message(plataforma, user_id, mensaje, unidad_negocio.name.lower())
        await send_options(plataforma, user_id, "Elige una opción:", botones, unidad_negocio.name.lower())
        estado_chat.state = "asking_profile_method"
        await sync_to_async(estado_chat.save)()

async def iniciar_perfil_conversacional(plataforma: str, user_id: str, unidad_negocio: BusinessUnit, estado_chat: ChatState, persona: Person):
    """Inicia el flujo conversacional básico para la creación del perfil."""
    bu_name = unidad_negocio.name.lower()

    if not persona.nombre or persona.nombre == "Nuevo Usuario":
        await send_message(plataforma, user_id, "¡Hola! ¿Cuál es tu nombre?", bu_name)
        estado_chat.state = "waiting_for_nombre"
        await sync_to_async(estado_chat.save)()
        return
    if not persona.apellido_paterno:
        await send_message(plataforma, user_id, f"Gracias, {persona.nombre}. ¿Cuál es tu apellido paterno?", bu_name)
        estado_chat.state = "waiting_for_apellido_paterno"
        await sync_to_async(estado_chat.save)()
        return
    if not persona.email:
        await send_message(plataforma, user_id, "¿Cuál es tu correo electrónico?", bu_name)
        estado_chat.state = "waiting_for_email"
        await sync_to_async(estado_chat.save)()
        return
    if not persona.phone:
        await send_message(plataforma, user_id, "Por último, ¿cuál es tu número de teléfono?", bu_name)
        estado_chat.state = "waiting_for_phone"
        await sync_to_async(estado_chat.save)()
        return

    # Delegar a workflows específicos por unidad de negocio
    if bu_name == "amigro":
        from app.chatbot.workflow.amigro import continuar_perfil_amigro
        await continuar_perfil_amigro(plataforma, user_id, unidad_negocio, estado_chat, persona)
    elif bu_name == "huntu":
        from app.chatbot.workflow.huntu import continuar_perfil_huntu
        await continuar_perfil_huntu(plataforma, user_id, unidad_negocio, estado_chat, persona)
    else:
        recap_message = await obtener_resumen_perfil(persona)
        await send_message(plataforma, user_id, recap_message, bu_name)
        estado_chat.state = "profile_complete_pending_confirmation"
        await sync_to_async(estado_chat.save)()

async def manejar_respuesta_perfil(plataforma: str, user_id: str, texto: str, unidad_negocio: BusinessUnit, estado_chat: ChatState, persona: Person, gpt_handler=None):
    """Maneja todas las respuestas del flujo de creación de perfiles."""
    bu_name = unidad_negocio.name.lower()

    # Respuesta a la selección del método de creación
    if estado_chat.state == "asking_profile_method":
        if texto == "profile_dynamic":
            estado_chat.context['use_gpt'] = GPT_ENABLED and gpt_handler is not None
            await iniciar_perfil_conversacional(plataforma, user_id, unidad_negocio, estado_chat, persona)
        elif texto == "profile_template" and plataforma == "whatsapp":
            template_name = f"registro_{bu_name}"
            try:
                await send_whatsapp_template(user_id, template_name, unidad_negocio)
                estado_chat.state = "waiting_for_template_response"
                await sync_to_async(estado_chat.save)()
            except Exception as e:
                logger.warning(f"No se pudo enviar template {template_name}: {e}. Usando flujo conversacional.")
                await iniciar_perfil_conversacional(plataforma, user_id, unidad_negocio, estado_chat, persona)
        elif texto == "profile_cv":
            await send_message(plataforma, user_id, "Por favor, envía tu CV como archivo adjunto (PDF o Word).", bu_name)
            estado_chat.state = "waiting_for_cv"
            await sync_to_async(estado_chat.save)()
        else:
            await send_message(plataforma, user_id, "Opción no válida. Selecciona 'Dinámico', 'Formulario' o 'CV'.", bu_name)
        return True

    # Respuestas en el flujo conversacional
    if estado_chat.state.startswith("waiting_for_"):
        field = estado_chat.state.replace("waiting_for_", "")
        if estado_chat.context.get('use_gpt') and GPT_ENABLED and gpt_handler:
            await procesar_respuesta_con_gpt(plataforma, user_id, texto, unidad_negocio, estado_chat, persona, gpt_handler)
        else:
            if field in ['nombre', 'apellido_paterno', 'email', 'phone', 'nacionalidad']:
                if field == 'email' and not re.match(r"[^@]+@[^@]+\.[^@]+", texto):
                    await send_message(plataforma, user_id, "Por favor, ingresa un email válido.", bu_name)
                    return True
                setattr(persona, field, texto.capitalize() if field in ['nombre', 'apellido_paterno'] else texto)
                await sync_to_async(persona.save)()
                if bu_name == "amigro":
                    from app.chatbot.workflow.amigro import continuar_perfil_amigro
                    await continuar_perfil_amigro(plataforma, user_id, unidad_negocio, estado_chat, persona)
                elif bu_name == "huntu":
                    from app.chatbot.workflow.huntu import continuar_perfil_huntu
                    await continuar_perfil_huntu(plataforma, user_id, unidad_negocio, estado_chat, persona)
                else:
                    await iniciar_perfil_conversacional(plataforma, user_id, unidad_negocio, estado_chat, persona)
            elif field == "tipo_candidato" and bu_name == "amigro":
                if texto in ["mexicano", "extranjero"]:
                    estado_chat.context['tipo_candidato'] = texto
                    await sync_to_async(estado_chat.save)()
                    from app.chatbot.workflow.amigro import continuar_perfil_amigro
                    await continuar_perfil_amigro(plataforma, user_id, unidad_negocio, estado_chat, persona)
                else:
                    await send_message(plataforma, user_id, "Por favor, selecciona 'Mexicano' o 'Extranjero'.", bu_name)
            elif field == "pais" and bu_name == "amigro":
                if texto == "otros_pais":
                    await send_message(plataforma, user_id, "Por favor, escribe el nombre de tu país de origen.", bu_name)
                    estado_chat.state = "waiting_for_pais_texto"
                else:
                    persona.nacionalidad = texto.capitalize()
                    await sync_to_async(persona.save)()
                    from app.chatbot.workflow.amigro import continuar_perfil_amigro
                    await continuar_perfil_amigro(plataforma, user_id, unidad_negocio, estado_chat, persona)
                await sync_to_async(estado_chat.save)()
            elif field == "pais_texto" and bu_name == "amigro":
                persona.nacionalidad = texto.capitalize()
                await sync_to_async(persona.save)()
                from app.chatbot.workflow.amigro import continuar_perfil_amigro
                await continuar_perfil_amigro(plataforma, user_id, unidad_negocio, estado_chat, persona)
            elif field == "migratory_status" and bu_name == "amigro":
                if texto == "otro_estatus":
                    await send_message(plataforma, user_id, "Por favor, especifica tu estatus migratorio.", bu_name)
                    estado_chat.state = "waiting_for_migratory_status_texto"
                else:
                    persona.metadata['migratory_status'] = texto.replace("_", " ").capitalize()
                    await sync_to_async(persona.save)()
                    from app.chatbot.workflow.amigro import continuar_perfil_amigro
                    await continuar_perfil_amigro(plataforma, user_id, unidad_negocio, estado_chat, persona)
                await sync_to_async(estado_chat.save)()
            elif field == "migratory_status_texto" and bu_name == "amigro":
                persona.metadata['migratory_status'] = texto.capitalize()
                await sync_to_async(persona.save)()
                from app.chatbot.workflow.amigro import continuar_perfil_amigro
                await continuar_perfil_amigro(plataforma, user_id, unidad_negocio, estado_chat, persona)
            elif field == "experience" and bu_name == "huntu":
                persona.work_experience = texto
                await sync_to_async(persona.save)()
                from app.chatbot.workflow.huntu import continuar_perfil_huntu
                await continuar_perfil_huntu(plataforma, user_id, unidad_negocio, estado_chat, persona)
        return True

    # Correcciones intuitivas
    if texto.startswith("cambiar") or texto.startswith("corregir"):
        field = texto.split(" ")[1].lower()
        valid_fields = ["nombre", "apellido_paterno", "email", "phone", "nacionalidad", "migratory_status", "experience"]
        if field in valid_fields:
            estado_chat.state = f"correcting_{field}"
            await sync_to_async(estado_chat.save)()
            await send_message(plataforma, user_id, f"Claro, ¿cuál es tu nuevo {field}?", bu_name)
            return True
        await send_message(plataforma, user_id, "No reconozco ese campo. Usa 'cambiar [campo]' como 'cambiar email'.", bu_name)
        return True

    if estado_chat.state.startswith("correcting_"):
        field = estado_chat.state.replace("correcting_", "")
        if field in ['nombre', 'apellido_paterno', 'email', 'phone', 'nacionalidad']:
            if field == 'email' and not re.match(r"[^@]+@[^@]+\.[^@]+", texto):
                await send_message(plataforma, user_id, "Por favor, ingresa un email válido.", bu_name)
                return True
            setattr(persona, field, texto.capitalize() if field in ['nombre', 'apellido_paterno'] else texto)
            await sync_to_async(persona.save)()
            await send_message(plataforma, user_id, f"{field.capitalize()} actualizado correctamente.", bu_name)
            estado_chat.state = "profile_in_progress"
            await sync_to_async(estado_chat.save)()
            await iniciar_creacion_perfil(plataforma, user_id, unidad_negocio, estado_chat, persona)
        elif field == "migratory_status" and bu_name == "amigro":
            persona.metadata['migratory_status'] = texto.capitalize()
            await sync_to_async(persona.save)()
            await send_message(plataforma, user_id, "Estatus migratorio actualizado correctamente.", bu_name)
            estado_chat.state = "profile_in_progress"
            await sync_to_async(estado_chat.save)()
            await iniciar_creacion_perfil(plataforma, user_id, unidad_negocio, estado_chat, persona)
        elif field == "experience" and bu_name == "huntu":
            persona.work_experience = texto
            await sync_to_async(persona.save)()
            await send_message(plataforma, user_id, "Experiencia laboral actualizada correctamente.", bu_name)
            estado_chat.state = "profile_in_progress"
            await sync_to_async(estado_chat.save)()
            await iniciar_creacion_perfil(plataforma, user_id, unidad_negocio, estado_chat, persona)
        return True

    # Confirmación final
    if estado_chat.state == "profile_complete_pending_confirmation":
        if texto == "sí":
            persona.profile_complete = True
            await sync_to_async(persona.save)()
            await send_message(plataforma, user_id, "¡Perfecto! Tu perfil está completo. ¿En qué te ayudo ahora?", bu_name)
            estado_chat.state = "idle"
            await sync_to_async(estado_chat.save)()
        elif texto == "no":
            await send_message(plataforma, user_id, "¿Qué te gustaría corregir? Usa 'cambiar [campo]' (ej. 'cambiar email').", bu_name)
            estado_chat.state = "profile_in_progress"
            await sync_to_async(estado_chat.save)()
        else:
            await send_message(plataforma, user_id, "Por favor, responde 'sí' o 'no'.", bu_name)
        return True

    return False

async def procesar_respuesta_con_gpt(plataforma: str, user_id: str, texto: str, unidad_negocio: BusinessUnit, estado_chat: ChatState, persona: Person, gpt_handler):
    """Procesa respuestas en el flujo dinámico usando GPT."""
    bu_name = unidad_negocio.name.lower()
    field = estado_chat.state.replace("waiting_for_", "")
    prompt = (
        f"El usuario está proporcionando su {field} en un flujo conversacional. "
        f"Su respuesta fue: '{texto}'. Extrae el valor correspondiente para {field} de manera precisa. "
        f"Devuelve solo el valor extraído en texto plano, o 'NO_ENTENDIDO' si no se pudo interpretar."
    )
    respuesta_gpt = await gpt_handler.generate_response(prompt, unidad_negocio)

    if respuesta_gpt.strip() == "NO_ENTENDIDO":
        await send_message(plataforma, user_id, f"No entendí tu {field}. Por favor, intenta de nuevo.", bu_name)
        return

    if field == 'email' and not re.match(r"[^@]+@[^@]+\.[^@]+", respuesta_gpt):
        await send_message(plataforma, user_id, "Por favor, ingresa un email válido.", bu_name)
        return

    if field in ['nombre', 'apellido_paterno']:
        setattr(persona, field, respuesta_gpt.capitalize())
    else:
        setattr(persona, field, respuesta_gpt)
    await sync_to_async(persona.save)()

    if bu_name == "amigro":
        from app.chatbot.workflow.amigro import continuar_perfil_amigro
        await continuar_perfil_amigro(plataforma, user_id, unidad_negocio, estado_chat, persona)
    elif bu_name == "huntu":
        from app.chatbot.workflow.huntu import continuar_perfil_huntu
        await continuar_perfil_huntu(plataforma, user_id, unidad_negocio, estado_chat, persona)
    else:
        await iniciar_perfil_conversacional(plataforma, user_id, unidad_negocio, estado_chat, persona)

async def obtener_resumen_perfil(persona: Person) -> str:
    """Genera un resumen del perfil del usuario."""
    info_fields = {
        "Nombre": persona.nombre,
        "Apellido Paterno": persona.apellido_paterno,
        "Apellido Materno": persona.apellido_materno,
        "Email": persona.email,
        "Teléfono": persona.phone,
        "Nacionalidad": persona.nacionalidad,
        "Estatus Migratorio": persona.metadata.get('migratory_status') if 'migratory_status' in persona.metadata else None,
        "Experiencia Laboral": persona.work_experience
    }
    recap_lines = ["Recapitulación de tu información:"]
    faltante = []
    for etiqueta, valor in info_fields.items():
        if valor:
            recap_lines.append(f"{etiqueta}: {valor}")
        else:
            faltante.append(etiqueta)
    if faltante:
        recap_lines.append("\nInformación faltante: " + ", ".join(faltante))
    else:
        recap_lines.append("\nToda la información está completa.")
    recap_lines.append("\n¿Es correcta esta información? Responde 'Sí' o 'No'.")
    return "\n".join(recap_lines)

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

def normalizar_numero(valor_str):
    """Convierte un string numérico (ej. '10k', '12,345.67') a float."""
    try:
        valor_str = valor_str.lower().replace(',', '')
        if 'k' in valor_str:
            return float(valor_str.replace('k', '')) * 1000
        return float(valor_str)
    except (ValueError, AttributeError):
        return 0.0  # Valor por defecto si falla la conversión

def extraer_moneda(mensaje):
    """Extrae la moneda del mensaje usando CURRENCY_MAP."""
    mensaje = mensaje.lower()
    for key, value in CURRENCY_MAP.items():
        if key in mensaje:
            return value
    return 'MXN'  # Por defecto

def parsear_mensaje(mensaje):
    """Parsea el mensaje para extraer datos de salario."""
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

    # Prestaciones específicas
    match_vales = re.search(r'vales\s*(?:de)?\s*([\d,\.]+k?)', mensaje, re.IGNORECASE)
    if match_vales:
        data['monto_vales'] = normalizar_numero(match_vales.group(1))
    else:
        data['monto_vales'] = 0.0

    data['fondo_ahorro'] = 'fondo de ahorro' in mensaje.lower()

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
        await send_message(platform, user_id, "Por favor, proporciona un salario válido.", business_unit_name)
        return

    # Obtener tipo de cambio
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
    bono_mensual_mxn = 0.0
    bono_mensual_orig = 0.0
    if data['bono'] > 0:
        bono_anual_mxn = data['bono'] * valor_mensual_mxn
        bono_mensual_mxn = bono_anual_mxn / 12
        valor_mensual_mxn += bono_mensual_mxn
        bono_mensual_orig = bono_mensual_mxn * tipo_cambio_inverso
        valor_mensual_orig += bono_mensual_orig

    # Parámetros adicionales para cálculos detallados
    incluye_prestaciones = data.get('prestaciones_adicionales', False)
    monto_vales = data.get('monto_vales', 0.0)
    fondo_ahorro = data.get('fondo_ahorro', False)
    porcentaje_fondo = data.get('porcentaje_fondo', 0.13)
    credito_infonavit = data.get('credito_infonavit', 0.0)
    pension_alimenticia = data.get('pension_alimenticia', 0.0)
    aplicar_subsidio = data.get('aplicar_subsidio', True)

    # Calcular bruto y neto en MXN con todos los detalles
    if data['tipo'] == 'bruto':
        salario_bruto_mxn = valor_mensual_mxn
        salario_neto_mxn = calcular_neto(
            salario_bruto_mxn,
            incluye_prestaciones=incluye_prestaciones,
            monto_vales=monto_vales,
            fondo_ahorro=fondo_ahorro,
            porcentaje_fondo=porcentaje_fondo,
            credito_infonavit=credito_infonavit,
            pension_alimenticia=pension_alimenticia,
            aplicar_subsidio=aplicar_subsidio
        )
    else:  # neto
        salario_neto_mxn = valor_mensual_mxn
        salario_bruto_mxn = calcular_bruto(
            salario_neto_mxn,
            incluye_prestaciones=incluye_prestaciones,
            monto_vales=monto_vales,
            fondo_ahorro=fondo_ahorro,
            porcentaje_fondo=porcentaje_fondo,
            credito_infonavit=credito_infonavit,
            pension_alimenticia=pension_alimenticia,
            aplicar_subsidio=aplicar_subsidio
        )

    # Conversión a moneda original
    salario_bruto_orig = salario_bruto_mxn * tipo_cambio_inverso
    salario_neto_orig = salario_neto_mxn * tipo_cambio_inverso

    # Cálculos detallados para mostrar en el mensaje
    base_gravable = salario_bruto_mxn - (monto_vales if incluye_prestaciones else 0.0)
    isr = calcular_isr_mensual(base_gravable)
    imss = calcular_cuotas_imss(salario_bruto_mxn)
    infonavit_descuento = credito_infonavit if credito_infonavit >= 1 else salario_bruto_mxn * credito_infonavit if credito_infonavit > 0 else 0.0
    pension_desc = pension_alimenticia if pension_alimenticia >= 1 else salario_bruto_mxn * pension_alimenticia if pension_alimenticia > 0 else 0.0
    ahorro_desc = salario_bruto_mxn * porcentaje_fondo if fondo_ahorro else 0.0
    subsidio = 0.0  # Pendiente de implementar si deseas lógica específica

    # Construir mensaje con formato mejorado
    msg = f"🤔 *Con base en el salario:* `{mensaje}`\n\n"
    msg += "```\n"
    msg += f"💰 Bruto Mensual : {salario_bruto_orig:>10,.2f} {data['moneda']} ({salario_bruto_mxn:,.2f} MXN)\n"
    msg += f"🏠 Neto Mensual  : {salario_neto_orig:>10,.2f} {data['moneda']} ({salario_neto_mxn:,.2f} MXN)\n"
    msg += "```\n"
    msg += "📊 *Detalles del cálculo:*\n"
    msg += "```\n"
    msg += f"🏛️ ISR            : {isr:>10,.2f} MXN\n"
    msg += f"🏥 IMSS           : {imss:>10,.2f} MXN\n"
    msg += f"🏡 Infonavit      : {infonavit_descuento:>10,.2f} MXN\n"
    msg += f"🏦 Fondo Ahorro   : {ahorro_desc:>10,.2f} MXN\n"
    msg += f"🍽️ Pensión Alim. : {pension_desc:>10,.2f} MXN\n"
    msg += f"💸 Subsidio Emp.  : {subsidio:>10,.2f} MXN\n"
    if incluye_prestaciones and monto_vales > 0:
        msg += f"🎟️ Vales (exento): {monto_vales:>10,.2f} MXN\n"
    if data['bono'] > 0:
        msg += f"🎁 Bono Mensual  : {bono_mensual_orig:>10,.2f} {data['moneda']} ({bono_mensual_mxn:,.2f} MXN)\n"
    msg += "```\n"

    # Leyenda si hay valores asumidos en 0
    campos_no_provistos = []
    if not incluye_prestaciones or monto_vales == 0: campos_no_provistos.append("Vales")
    if not fondo_ahorro: campos_no_provistos.append("Fondo de Ahorro")
    if credito_infonavit == 0: campos_no_provistos.append("Infonavit")
    if pension_alimenticia == 0: campos_no_provistos.append("Pensión Alimenticia")
    if not aplicar_subsidio or subsidio == 0: campos_no_provistos.append("Subsidio al Empleo")
    
    if campos_no_provistos:
        msg += f"📝 *Nota:* Basado en los datos provistos, los valores de {', '.join(campos_no_provistos)} se calculan en 0.\n"

    # Comparativa bidireccional
    pais_origen = {'MXN': 'México', 'USD': 'USA', 'NIO': 'Nicaragua', 'COP': 'Colombia', 'ARS': 'Argentina', 'BRL': 'Brasil'}.get(data['moneda'], 'Otro')
    ciudad_origen = {'México': 'Ciudad de México', 'USA': 'Nueva York', 'Nicaragua': 'Managua', 'Colombia': 'Bogotá', 'Argentina': 'Buenos Aires', 'Brasil': 'São Paulo'}.get(pais_origen, 'Otra ciudad')

    # Calcular ajustes para México
    adjustment_coli_mx = DATOS_COLI['Ciudad de México'] / DATOS_COLI.get(ciudad_origen, 50.0)
    adjustment_ppa_mx = DATOS_PPA['México'] / DATOS_PPA.get(pais_origen, 1.0)
    adjustment_bigmac_mx = DATOS_BIGMAC['México'] / DATOS_BIGMAC.get(pais_origen, 5.0)

    # Calcular ajustes para el país de origen
    adjustment_coli_orig = DATOS_COLI.get(ciudad_origen, 50.0) / DATOS_COLI['Ciudad de México']
    adjustment_ppa_orig = DATOS_PPA.get(pais_origen, 1.0) / DATOS_PPA['México']
    adjustment_bigmac_orig = DATOS_BIGMAC.get(pais_origen, 5.0) / DATOS_BIGMAC['México']

    # Construir tabla comparativa dinámica
    msg += "\n🌍 *Comparativa Salario Neto:*\n"
    msg += "```\n"
    msg += f"{'':<15} {'🇲🇽 México':<15} {(f'🌎 {pais_origen}' if data['moneda'] != 'MXN' else ''):<15}\n"
    msg += f"{'-' * 15} {'-' * 15} {'-' * 15 if data['moneda'] != 'MXN' else ''}\n"
    msg += f"📊 COLI         {salario_neto_mxn * adjustment_coli_mx:>10,.2f} MXN {(f'{salario_neto_orig * adjustment_coli_orig:>10,.2f} {data['moneda']}' if data['moneda'] != 'MXN' else '')}\n"
    msg += f"⚖️ PPA          {salario_neto_mxn * adjustment_ppa_mx:>10,.2f} MXN {(f'{salario_neto_orig * adjustment_ppa_orig:>10,.2f} {data['moneda']}' if data['moneda'] != 'MXN' else '')}\n"
    msg += f"🍔 BigMac Index {salario_neto_mxn * adjustment_bigmac_mx:>10,.2f} MXN {(f'{salario_neto_orig * adjustment_bigmac_orig:>10,.2f} {data['moneda']}' if data['moneda'] != 'MXN' else '')}\n"
    msg += "```\n"

    # Obtener el dominio desde ConfiguracionBU de manera asíncrona
    try:
        business_unit = await sync_to_async(BusinessUnit.objects.get)(name=business_unit_name)
        config = await sync_to_async(lambda: business_unit.configuracionbu)()
        if config and config.dominio_bu:
            parsed_url = urlparse(config.dominio_bu)
            domain = parsed_url.netloc or parsed_url.path  # Extrae el dominio limpio
            domain = domain.replace('www.', '')  # Elimina 'www.' si existe
        else:
            domain = "huntred.com"  # Dominio por defecto si no hay configuración
    except BusinessUnit.DoesNotExist:
        domain = "huntred.com"  # Dominio por defecto si la unidad no existe
    except ConfiguracionBU.DoesNotExist:
        domain = "huntred.com"  # Dominio por defecto si no hay ConfiguracionBU
    except Exception as e:
        logger.error(f"Error al obtener dominio para {business_unit_name}: {e}")
        domain = "huntred.com"  # Fallback en caso de error inesperado

    # Añadir referencia dinámica
    msg += f"\n📚 *Referencia:* https://{domain}/salario/"

    await send_message(platform, user_id, msg, business_unit_name)