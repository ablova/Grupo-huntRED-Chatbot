# /home/pablo/app/chatbot/intents_handler.py
import re
import logging
from typing import List, Dict, Any
from asgiref.sync import sync_to_async
from app.models import ChatState, Person, BusinessUnit
from app.chatbot.integrations.services import send_message, send_options, send_menu

logger = logging.getLogger(__name__)

# Cache para almacenar respuestas previas (mensaje -> respuesta)
response_cache = {}

# Definición de intents con patrones regex, respuestas y prioridad (menor número = mayor prioridad)
INTENTS = {
    "saludo": {
        "patterns": [r"\b(hola|hi|saludos|buen(os)?\s(días|tardes|noches)|hey|qué\s+tal)\b"],
        "responses": ["¡Hola! ¿En qué puedo ayudarte hoy?"],
        "priority": 1
    },
    "despedida": {
        "patterns": [r"\b(adiós|hasta\s+luego|chau|bye)\b"],
        "responses": ["¡Hasta luego! Si necesitas más ayuda, contáctame de nuevo."],
        "priority": 2
    },
    "iniciar_conversacion": {
        "patterns": [r"\b(inicio|iniciar|start|go|activar)\b"],
        "responses": ["¡Claro! Empecemos de nuevo. ¿En qué puedo ayudarte?"],
        "priority": 3
    },
    "solicitar_ayuda_postulacion": {
        "patterns": [r"\b(ayuda\s+postulacion|postular|aplicar|como\s+postular)\b"],
        "responses": ["Puedo guiarte en el proceso de postulación. ¿Qué necesitas saber?"],
        "priority": 4
    },
    "busqueda_impacto": {
        "patterns": [r"\b(impacto\s+social|trabajo\s+con\s+proposito|vacantes\s+con\s+impacto)\b"],
        "responses": ["Entiendo que buscas un trabajo con impacto social. ¿Deseas ver vacantes con propósito?"],
        "priority": 5
    },
    "solicitar_informacion_empresa": {
        "patterns": [r"\b(informacion\s+empresa|sobre\s+la\s+empresa|valores\s+empresa|cultura\s+empresa)\b"],
        "responses": ["¿Sobre qué empresa necesitas información? Puedo contarte sobre sus valores, cultura o posiciones disponibles."],
        "priority": 6
    },
    "solicitar_tips_entrevista": {
        "patterns": [r"\b(tips\s+entrevista|consejos\s+entrevista|preparacion\s+entrevista)\b"],
        "responses": ["Para entrevistas: investiga la empresa, sé puntual, muestra logros cuantificables y prepara ejemplos de situaciones pasadas."],
        "priority": 7
    },
    "consultar_sueldo_mercado": {
        "patterns": [r"\b(sueldo\s+mercado|rango\s+salarial|cuanto\s+pagan)\b"],
        "responses": ["¿Para qué posición o nivel buscas el rango salarial de mercado? Puedo darte una estimación."],
        "priority": 8
    },
    "actualizar_perfil": {
        "patterns": [r"\b(actualizar\s+perfil|cambiar\s+datos|modificar\s+informacion)\b"],
        "responses": ["Claro, ¿qué dato de tu perfil deseas actualizar? (Ejemplo: nombre, email, experiencia, expectativas salariales)"],
        "priority": 9
    },
    "notificaciones": {
        "patterns": [r"\b(notificaciones|alertas|avisos)\b"],
        "responses": ["Puedo enviarte notificaciones automáticas sobre cambios en tus procesos. ¿Quieres activarlas? Responde 'sí' para confirmar."],
        "priority": 10
    },
    "agradecimiento": {
        "patterns": [r"\b(gracias|muchas\s+gracias|te\s+agradezco)\b"],
        "responses": ["¡De nada! ¿En qué más puedo ayudarte?"],
        "priority": 11
    },
    "show_jobs": {
        "patterns": [r"\b(vacante|vacantes|oportunidad|oportunidades|empleo|puestos|listado)\b"],
        "responses": ["Te mostraré las vacantes disponibles según tu perfil."],
        "priority": 12
    },
    "upload_cv": {
        "patterns": [r"\b(cv|currículum|curriculum|resume|hoja\s+de\s+vida|subir|enviar)\b"],
        "responses": ["¡Perfecto! Puedes enviarme tu CV por este medio y lo procesaré para extraer la información relevante. Por favor, adjunta el archivo en tu próximo mensaje."],
        "priority": 13
    },
    "show_menu": {
        "patterns": [r"\b(menu|menú|opciones|lista|que\s+puedes\s+hacer|qué\s+puedes\s+hacer|servicios)\b"],
        "responses": ["Te mostraré el menú de opciones disponibles."],
        "priority": 14
    },
    "retry_conversation": {
        "patterns": [r"\b(intentemos\s+de\s+nuevo|volvamos\s+a\s+intentar|retry|de\s+nuevo)\b"],
        "responses": ["¡Claro! Vamos a intentarlo de nuevo. ¿En qué puedo ayudarte ahora?"],
        "priority": 15
    }
}

# Lista de botones principales
main_options = [
    {"title": "💼 Ver Vacantes", "payload": "show_jobs"},
    {"title": "📄 Subir CV", "payload": "upload_cv"},
    {"title": "📋 Ver Menú", "payload": "show_menu"}
]

def detect_intents(message: str) -> List[str]:
    """
    Detecta todos los intents en un mensaje usando expresiones regulares.
    Retorna una lista de intents ordenada por prioridad.
    """
    detected_intents = []
    message_lower = message.lower().strip()

    for intent, data in INTENTS.items():
        for pattern in data["patterns"]:
            if re.search(pattern, message_lower):
                detected_intents.append(intent)
                break  # Evitar duplicar el mismo intent

    # Ordenar por prioridad (menor número = mayor prioridad)
    detected_intents.sort(key=lambda x: INTENTS[x]["priority"])
    return detected_intents

async def handle_known_intents(intents: List[str], platform: str, user_id: str, chat_state: ChatState, business_unit: BusinessUnit, user: Person, text: str = "") -> bool:
    """
    Maneja los intents conocidos del usuario.
    Devuelve True si se manejó una intención, False si no.
    Integra detección avanzada con regex y manejo de múltiples intents.
    """
    from app.chatbot.chatbot import ChatBotHandler
    chat_bot_handler = ChatBotHandler()

    text = text.strip().lower()
    logger.info(f"[handle_known_intents] 🔎 Procesando mensaje: '{text}'")
    logger.info(f"[handle_known_intents] 📌 Intents recibidos: {intents}")

    logger.info(f"[handle_known_intents] 🆔 User ID: {user_id}")
    logger.info(f"[handle_known_intents] 🏢 Business Unit: {business_unit.name}")
    logger.info(f"[handle_known_intents] 📜 Chat State Context: {chat_state.context}")

    # Usar cache si el mensaje ya fue procesado
    if text in response_cache:
        await send_message(platform, user_id, response_cache[text], business_unit.name.lower())
        logger.info(f"[handle_known_intents] 📥 Respuesta obtenida del cache para: '{text}'")
        return True

    # Manejar payloads de botones directamente
    if text in ["tos_accept", "tos_reject"]:
        tos_url = chat_bot_handler.get_tos_url(business_unit)  # Obtener URL dinámica
        if text == "tos_accept":
            user.tos_accepted = True
            await sync_to_async(user.save)()
            response = f"✅ Gracias por aceptar los Términos de Servicio de {business_unit.name}. Aquí tienes el Menú Principal:"
            await send_message(platform, user_id, response, business_unit.name.lower())
            await send_menu(platform, user_id, business_unit.name.lower())
            await chat_bot_handler.store_bot_message(chat_state, response)
        else:
            response = "⚠ No se puede continuar sin aceptar los TOS. Por favor, selecciona una opción:"
            tos_buttons = [
                {"title": "✅ Aceptar", "payload": "tos_accept"},
                {"title": "❌ Rechazar", "payload": "tos_reject"},
                {"title": "📜 Ver TOS", "url": tos_url}  # Usar URL dinámica
            ]
            if platform == "whatsapp":
                await send_message(platform, user_id, f"📜 Consulta nuestros términos aquí: {tos_url}", business_unit.name.lower())
            await send_message(platform, user_id, response, business_unit.name.lower(), options=tos_buttons)
            await chat_bot_handler.store_bot_message(chat_state, response)
        response_cache[text] = response
        return True

    # Detección de intents (NLP o regex)
    detected_intents = intents.copy()
    if not detected_intents:
        detected_intents = detect_intents(text)
        logger.debug(f"[handle_known_intents] Intents detectados por regex: {detected_intents}")

    if not detected_intents:
        tos_url = chat_bot_handler.get_tos_url(business_unit)  # Obtener URL dinámica para el caso por defecto
        response = "No entendí tu mensaje. ¿Qué te gustaría hacer? Puedes decir 'ver vacantes', 'subir mi CV' o 'menú'."
        await send_message(platform, user_id, response, business_unit.name.lower())
        await send_options(platform, user_id, "Elige una opción:", main_options, business_unit.name.lower())
        response_cache[text] = response
        logger.info(f"[handle_known_intents] ⚠️ No se detectó ningún intent, enviando respuesta por defecto.")
        return False

    # Procesar el intent de mayor prioridad (el primero en la lista)
    top_intent = detected_intents[0]
    logger.info(f"[handle_known_intents] ✅ Procesando intent principal: {top_intent}")

    if top_intent in INTENTS:
        response = INTENTS[top_intent]["responses"][0]
        if top_intent == "show_jobs":
            from app.utilidades.vacantes import VacanteManager
            recommended_jobs = await sync_to_async(VacanteManager.match_person_with_jobs)(user)
            if recommended_jobs:
                chat_state.context['recommended_jobs'] = recommended_jobs
                await sync_to_async(chat_state.save)()
                await present_job_listings(platform, user_id, recommended_jobs, business_unit, chat_state)
            else:
                response = "No encontré vacantes para tu perfil por ahora."
                await send_message(platform, user_id, response, business_unit.name.lower())
        elif top_intent == "upload_cv":
            await send_message(platform, user_id, response, business_unit.name.lower())
            chat_state.state = "waiting_for_cv"
            await sync_to_async(chat_state.save)()
        elif top_intent == "show_menu":
            await send_menu(platform, user_id, business_unit.name.lower())
        else:
            await send_message(platform, user_id, response, business_unit.name.lower())
        response_cache[text] = response
        return True

    # Manejo de intents específicos adicionales
    if top_intent == "greeting":
        await chat_bot_handler.send_complete_initial_messages(platform, user_id, business_unit)
        return True
    elif top_intent == "reset_chat_state":
        chat_state.state = "initial"
        chat_state.context = {}
        await sync_to_async(chat_state.save)()
        await send_message(platform, user_id, f"🧹 ¡Listo, {user.nombre}! Tu conversación en {platform} ha sido reiniciada. ¿En qué puedo ayudarte ahora?", business_unit.name.lower())
        return True
    elif top_intent == "consultar_estatus":
        response = "Por favor, proporciona tu correo electrónico asociado a la aplicación."
        await send_message(platform, user_id, response, business_unit.name.lower())
        chat_state.context['awaiting_status_email'] = True
        await sync_to_async(chat_state.save)()
        return True
    elif top_intent in ["travel_in_group", "travel_with_family"]:
        response = (
            "Entiendo, ¿te gustaría invitar a tus acompañantes para que también obtengan oportunidades laborales? "
            "Envíame su nombre completo y teléfono en el formato: 'Nombre Apellido +52XXXXXXXXXX'."
        )
        await send_message(platform, user_id, response, business_unit.name.lower())
        chat_state.context['awaiting_group_invitation'] = True
        await sync_to_async(chat_state.save)()
        return True
    elif top_intent in ["tos_accept", "tos_reject"]:
        if top_intent == "tos_accept":
            user.tos_accepted = True
            await sync_to_async(user.save)()
            response = "✅ Gracias por aceptar nuestros TOS. Ahora podemos continuar con el proceso."
        else:
            response = "⚠ No se puede continuar sin aceptar los TOS. Por favor, selecciona una opción:"
        tos_buttons = [
            {"title": "✅ Aceptar", "payload": "tos_accept"},
            {"title": "❌ Rechazar", "payload": "tos_reject"},
            {"title": "📜 Ver TOS", "url": "https://amigro.org/tos"}
        ]
        if platform == "whatsapp":
            await send_message(platform, user_id, "📜 Consulta nuestros términos aquí: https://amigro.org/tos", business_unit.name.lower())
        await send_message(platform, user_id, response, business_unit.name.lower(), options=tos_buttons)
        return True
    elif top_intent == "calcular_salario":
        response = "¿Qué deseas calcular?\n1. Salario neto (desde bruto)\n2. Salario bruto (desde neto)\nResponde con '1' o '2'."
        await send_message(platform, user_id, response, business_unit.name.lower())
        chat_state.state = "waiting_for_salary_calc_type"
        await sync_to_async(chat_state.save)()
        return True
    elif top_intent == "consultar_requisitos_vacante":
        response = "Por favor, dime el nombre o ID de la vacante sobre la que quieres saber los requisitos."
        await send_message(platform, user_id, response, business_unit.name.lower())
        chat_state.state = "waiting_for_vacancy_id"
        await sync_to_async(chat_state.save)()
        return True
    elif top_intent == "solicitar_contacto_reclutador":
        response = "Te conectaré con un reclutador. Por favor, espera mientras te asignamos uno."
        await send_message(platform, user_id, response, business_unit.name.lower())
        response_recruit = "Un candidato requiere asistencia especial, te paso sus datos - "
        await send_message(platform, "525518490291", response_recruit, business_unit.name.lower())
        return True
    elif top_intent == "preparacion_entrevista":
        response = "Para entrevistas: investiga la empresa, sé puntual, muestra logros cuantificables y prepara ejemplos de situaciones pasadas. ¿Necesitas más ayuda?"
        await send_message(platform, user_id, response, business_unit.name.lower())
        return True
    elif top_intent == "consultar_beneficios":
        response = "¿Qué tipo de beneficios te interesan?"
        benefit_buttons = [
            {"title": "🏥 Salud", "payload": "beneficio_salud"},
            {"title": "💰 Bonos", "payload": "beneficio_bonos"},
            {"title": "📆 Días libres", "payload": "beneficio_dias_libres"}
        ]
        await send_message(platform, user_id, response, business_unit.name.lower(), options=benefit_buttons)
        return True
    elif top_intent == "consultar_horario":
        response = "¿Buscas un horario específico?"
        horario_buttons = [
            {"title": "⏳ Jornada Completa", "payload": "horario_completo"},
            {"title": "⏰ Medio Tiempo", "payload": "horario_medio_tiempo"},
            {"title": "🔄 Flexible", "payload": "horario_flexible"}
        ]
        await send_message(platform, user_id, response, business_unit.name.lower(), options=horario_buttons)
        return True
    elif top_intent == "consultar_tipo_contrato":
        response = "¿Qué tipo de contrato buscas?"
        contrato_buttons = [
            {"title": "📄 Indefinido", "payload": "contrato_indefinido"},
            {"title": "📌 Por Proyecto", "payload": "contrato_proyecto"},
            {"title": "💼 Freelance", "payload": "contrato_freelance"}
        ]
        await send_message(platform, user_id, response, business_unit.name.lower(), options=contrato_buttons)
        return True
    elif top_intent == "preguntar_reubicacion":
        response = "¿Estás dispuesto a reubicarte por una oportunidad laboral?"
        reubicacion_buttons = [
            {"title": "✅ Sí", "payload": "reubicacion_si"},
            {"title": "❌ No", "payload": "reubicacion_no"},
            {"title": "🤔 Depende (ubicación/posición)", "payload": "reubicacion_depende"}
        ]
        await send_message(platform, user_id, response, business_unit.name.lower(), options=reubicacion_buttons)
        return True

    # Respuesta por defecto si no se manejó ningún intent
    tos_url = chat_bot_handler.get_tos_url(business_unit)  # Obtener URL dinámica
    response = "No entendí tu mensaje. ¿Qué te gustaría hacer? Puedes decir 'ver vacantes', 'subir mi CV' o 'menú'."
    await send_message(platform, user_id, response, business_unit.name.lower())
    await send_options(platform, user_id, "Elige una opción:", main_options, business_unit.name.lower())
    response_cache[text] = response
    logger.info(f"[handle_known_intents] ⚠️ Intent no manejado: {top_intent}, enviando respuesta por defecto.")
    return False

async def handle_document_upload(
    file_url: str, 
    file_type: str, 
    platform: str, 
    user_id: str, 
    business_unit: BusinessUnit,
    user: Person,
    chat_state: ChatState
) -> None:
    """
    Maneja la carga de documentos como CVs.
    """
    from app.utilidades.parser import parse_document
    
    await send_message(
        platform, 
        user_id, 
        "Estoy procesando tu documento. Esto tomará unos momentos...", 
        business_unit.name.lower()
    )
    
    try:
        if file_type.lower() in ['pdf', 'application/pdf']:
            parsed_data = await sync_to_async(parse_document)(file_url, 'pdf')
        elif file_type.lower() in ['doc', 'docx', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
            parsed_data = await sync_to_async(parse_document)(file_url, 'doc')
        else:
            await send_message(
                platform, 
                user_id, 
                f"No puedo procesar archivos de tipo {file_type}. Por favor, envía tu archivo en PDF o Word.", 
                business_unit.name.lower()
            )
            return
        
        # Lista para rastrear los atributos guardados
        saved_attributes = []

        user.cv_parsed = True
        saved_attributes.append(f"cv_parsed: True")
        user.cv_url = file_url
        saved_attributes.append(f"cv_url: {file_url}")
        user.cv_parsed_data = parsed_data
        saved_attributes.append(f"cv_parsed_data: {parsed_data}")

        if 'name' in parsed_data and not user.nombre:
            user.nombre = parsed_data['name']
            saved_attributes.append(f"nombre: {parsed_data['name']}")
        if 'email' in parsed_data and not user.email:
            user.email = parsed_data['email']
            saved_attributes.append(f"email: {parsed_data['email']}")
        if 'phone' in parsed_data and not user.phone:
            user.phone = parsed_data['phone']
            saved_attributes.append(f"phone: {parsed_data['phone']}")
        if 'skills' in parsed_data:
            # Guardar las habilidades directamente en el campo skills de Person
            user.skills = ', '.join(parsed_data['skills']) if isinstance(parsed_data['skills'], list) else parsed_data['skills']
            saved_attributes.append(f"skills: {user.skills}")

        await sync_to_async(user.save)()
        
        # Log detallado de los atributos guardados
        logger.info(f"[handle_document_upload] Atributos guardados para {user_id}: {', '.join(saved_attributes)}")

        response = (
            "✅ ¡He procesado tu CV correctamente!\n\n"
            "Datos extraídos:\n"
            f"👤 Nombre: {parsed_data.get('name', 'No detectado')}\n"
            f"📧 Email: {parsed_data.get('email', 'No detectado')}\n"
            f"📱 Teléfono: {parsed_data.get('phone', 'No detectado')}\n"
            f"🛠 Habilidades: {', '.join(parsed_data.get('skills', [])) or 'No detectadas'}\n\n"
            "¿Están correctos estos datos? Por favor, responde 'sí' para confirmar o 'no' para corregir."
        )
        
        await send_message(platform, user_id, response, business_unit.name.lower())
        
        chat_state.state = "waiting_for_cv_confirmation"
        chat_state.context['parsed_data'] = parsed_data
        await sync_to_async(chat_state.save)()
        
    except Exception as e:
        logger.error(f"Error procesando documento: {str(e)}", exc_info=True)
        await send_message(
            platform, 
            user_id, 
            "❌ Hubo un problema al procesar tu documento. Por favor, intenta de nuevo.", 
            business_unit.name.lower()
        )

async def present_job_listings(
    platform: str, 
    user_id: str, 
    jobs: List[Dict[str, Any]],
    business_unit: BusinessUnit,
    chat_state: ChatState,
    page: int = 0,
    jobs_per_page: int = 3,
    filters: Dict[str, Any] = None
) -> None:
    """
    Presenta listados de trabajo al usuario con paginación y filtros opcionales.
    """
    filters = filters or {}
    filtered_jobs = jobs
    
    if 'location' in filters:
        filtered_jobs = [job for job in filtered_jobs if filters['location'].lower() in job.get('location', '').lower()]
    if 'min_salary' in filters:
        filtered_jobs = [job for job in filtered_jobs if float(job.get('salary', 0)) >= filters['min_salary']]
    
    if not filtered_jobs:
        await send_message(platform, user_id, "No encontré vacantes que coincidan con tus filtros.", business_unit.name.lower())
        return
    
    total_jobs = len(filtered_jobs)
    start_idx = page * jobs_per_page
    end_idx = min(start_idx + jobs_per_page, total_jobs)
    
    response = "Aquí tienes algunas vacantes recomendadas:\n"
    for idx, job in enumerate(filtered_jobs[start_idx:end_idx], start=start_idx + 1):
        response += f"{idx}. {job['title']} en {job.get('company', 'N/A')}\n"
    response += "Responde con el número de la vacante que te interesa o 'más' para ver más opciones."
    
    await send_message(platform, user_id, response, business_unit.name.lower())