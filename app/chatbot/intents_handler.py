# Ubicación: /home/pablo/app/chatbot/intents_handler.py
import logging
from typing import Dict, List, Any
from asgiref.sync import sync_to_async
from app.models import ChatState, Person, BusinessUnit
from app.chatbot.integrations.services import send_message, send_email, send_options, reset_chat_state, send_menu, MENU_OPTIONS_BY_BU
from app.utilidades.vacantes import VacanteManager

logger = logging.getLogger(__name__)

async def handle_known_intents(intents: List[str], platform: str, user_id: str, chat_state: ChatState, business_unit: BusinessUnit, user: Person, text: str = "") -> bool:
    """
    Maneja los intents conocidos del usuario.
    Devuelve True si se manejó una intención, False si no.
    Integra detección básica por palabras clave y manejo de intents predefinidos.
    """
    from app.chatbot.chatbot import ChatBotHandler
    text = text.strip().lower()
    chat_bot_handler = ChatBotHandler()

    logger.info(f"[handle_known_intents] 🔎 Procesando mensaje: '{text}'")
    logger.info(f"[handle_known_intents] 📌 Intents recibidos: {intents}")

    # Mostrar información del usuario
    logger.info(f"[handle_known_intents] 🆔 User ID: {user_id}")
    logger.info(f"[handle_known_intents] 🏢 Business Unit: {business_unit.name}")
    logger.info(f"[handle_known_intents] 📜 Chat State Context: {chat_state.context}")

    # Si hay intents detectados por NLP
    if intents:
        logger.info(f"[handle_known_intents] ✅ Intents detectados: {intents}")
    else:
        logger.info(f"[handle_known_intents] ⚠️ No se detectó ningún intent.")

    # Diccionario de respuestas predefinidas para intents
    INTENT_RESPONSES = {
        "saludo": "¡Hola! ¿En qué puedo ayudarte hoy?",
        "despedida": "¡Hasta luego! Si necesitas más ayuda, contáctame de nuevo.",
        "iniciar_conversacion": "¡Claro! Empecemos de nuevo. ¿En qué puedo ayudarte?",
        "solicitar_ayuda_postulacion": "Puedo guiarte en el proceso de postulación. ¿Qué necesitas saber?",
        "busqueda_impacto": "Entiendo que buscas un trabajo con impacto social. ¿Deseas ver vacantes con propósito?",
        "solicitar_informacion_empresa": "¿Sobre qué empresa necesitas información? Puedo contarte sobre sus valores, cultura o posiciones disponibles.",
        "solicitar_tips_entrevista": "Para entrevistas: investiga la empresa, sé puntual, muestra logros cuantificables y prepara ejemplos de situaciones pasadas.",
        "consultar_sueldo_mercado": "¿Para qué posición o nivel buscas el rango salarial de mercado? Puedo darte una estimación.",
        "actualizar_perfil": "Claro, ¿qué dato de tu perfil deseas actualizar? (Ejemplo: nombre, email, experiencia, expectativas salariales)",
        "notificaciones": "Puedo enviarte notificaciones automáticas sobre cambios en tus procesos. ¿Quieres activarlas? Responde 'sí' para confirmar.",
        "agradecimiento": "¡De nada! ¿En qué más puedo ayudarte?",
    }
    # Lista de botones principales
    main_options = [
        {"title": "💼 Ver Vacantes", "payload": "show_jobs"},
        {"title": "📄 Subir CV", "payload": "upload_cv"},
        {"title": "📋 Ver Menú", "payload": "show_menu"}
    ]
    # Detección básica de intents por palabras clave (integrada desde detect_basic_intents)
    detected_intents = intents.copy()  # Copia los intents pasados (pueden venir de NLP)
    # Detección por palabras clave ampliada 
    if not detected_intents:  # Si no hay intents pre-detectados, analizamos el texto
        if any(greeting in text for greeting in ["hola", "hi", "saludos", "buenos días", "buenas tardes", "buenas noches", "inicio", "iniciar", "start", "go", "activar", "hey", "qué tal", "buen día"]):
            detected_intents.append("greeting")
        if any(cv_keyword in text for cv_keyword in ["menu", "menú", "opciones", "lista", "que puedes hacer", "qué puedes hacer", "servicios"]):
            detected_intents.append("show_menu")
        if any(cv_keyword in text for cv_keyword in ["cv", "currículum", "curriculum", "resume", "hoja de vida", "subir", "enviar"]):
            detected_intents.append("upload_cv")
        if any(cv_keyword in text for cv_keyword in ["vacante", "vacantes", "oportunidad", "oportunidades", "empleo", "puestos", "listado"]):
            detected_intents.append("show_jobs")
        if "ayuda" in text or "help" in text:
            detected_intents.append("solicitar_ayuda")

    logger.debug(f"[handle_known_intents] Intents detectados: {detected_intents}, Texto: {text}")

    # Manejo de intents detectados
    for intent in detected_intents:
        # Intents predefinidos en INTENT_RESPONSES
        if intent in INTENT_RESPONSES:
            response = INTENT_RESPONSES[intent]
            await send_message(platform, user_id, response, business_unit.name.lower())
            return True

        # Intent "greeting" (saludo o inicio de conversación)
        if intent == "greeting":
            await chat_bot_handler.send_complete_initial_messages(platform, user_id, business_unit)
            return True

        # Intent "show_menu"
        if intent == "show_menu":
            await send_menu(platform, user_id, business_unit.name.lower())
            return True

        # Intent "upload_cv"
        if intent == "upload_cv":
            response = "¡Perfecto! Puedes enviarme tu CV por este medio y lo procesaré para extraer la información relevante. Por favor, adjunta el archivo en tu próximo mensaje."
            await send_message(platform, user_id, response, business_unit.name.lower())
            chat_state.state = "waiting_for_cv"
            await sync_to_async(chat_state.save)()
            return True

        # Intent "show_jobs"
        if intent == "show_jobs":
            recommended_jobs = await sync_to_async(VacanteManager.match_person_with_jobs)(user)
            if recommended_jobs:
                chat_state.context['recommended_jobs'] = recommended_jobs
                await sync_to_async(chat_state.save)()
                await present_job_listings(platform, user_id, recommended_jobs, business_unit, chat_state)
            else:
                await send_message(platform, user_id, "No encontré vacantes para tu perfil por ahora.", business_unit.name.lower())
            return True

        # Otros intents existentes
        if intent == "reset_chat_state":
            await reset_chat_state(user_id, business_unit, platform)
            await send_message(platform, user_id, f"🧹 ¡Listo, {user.nombre}! Tu conversación en {platform} ha sido reiniciada. ¿En qué puedo ayudarte ahora?", business_unit.name.lower())
            return True

        if intent == "consultar_estatus":
            response = "Por favor, proporciona tu correo electrónico asociado a la aplicación."
            await send_message(platform, user_id, response, business_unit.name.lower())
            chat_state.context['awaiting_status_email'] = True
            await sync_to_async(chat_state.save)()
            return True

        if intent in ["travel_in_group", "travel_with_family"]:
            response = (
                "Entiendo, ¿te gustaría invitar a tus acompañantes para que también obtengan oportunidades laborales? "
                "Envíame su nombre completo y teléfono en el formato: 'Nombre Apellido +52XXXXXXXXXX'."
            )
            await send_message(platform, user_id, response, business_unit.name.lower())
            chat_state.context['awaiting_group_invitation'] = True
            await sync_to_async(chat_state.save)()
            return True

        if intent == "ver_vacantes":  # Similar a "show_jobs", pero mantenemos consistencia
            recommended_jobs = await sync_to_async(VacanteManager.match_person_with_jobs)(user)
            if recommended_jobs:
                chat_state.context['recommended_jobs'] = recommended_jobs
                await sync_to_async(chat_state.save)()
                await present_job_listings(platform, user_id, recommended_jobs, business_unit, chat_state)
            else:
                await send_message(platform, user_id, "No encontré vacantes para tu perfil por ahora.", business_unit.name.lower())
            return True

        if intent in ["tos_accept", "tos_reject"]:
            if intent == "tos_accept":
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

        if intent == "calcular_salario":
            response = "¿Qué deseas calcular?\n1. Salario neto (desde bruto)\n2. Salario bruto (desde neto)\nResponde con '1' o '2'."
            await send_message(platform, user_id, response, business_unit.name.lower())
            chat_state.state = "waiting_for_salary_calc_type"
            await sync_to_async(chat_state.save)()
            return True

        if intent == "consultar_requisitos_vacante":
            response = "Por favor, dime el nombre o ID de la vacante sobre la que quieres saber los requisitos."
            await send_message(platform, user_id, response, business_unit.name.lower())
            chat_state.state = "waiting_for_vacancy_id"
            await sync_to_async(chat_state.save)()
            return True

        if intent == "solicitar_contacto_reclutador":
            response = "Te conectaré con un reclutador. Por favor, espera mientras te asignamos uno."
            await send_message(platform, user_id, response, business_unit.name.lower())
            response_recruit = "Un candidato requiere asistencia especial, te paso sus datos - "
            await send_message(platform, "525518490291", response_recruit, business_unit.name.lower())
            return True

        if intent == "preparacion_entrevista":  # Consolidado con "solicitar_tips_entrevista"
            response = "Para entrevistas: investiga la empresa, sé puntual, muestra logros cuantificables y prepara ejemplos de situaciones pasadas. ¿Necesitas más ayuda?"
            await send_message(platform, user_id, response, business_unit.name.lower())
            return True

        if intent == "consultar_beneficios":
            response = "¿Qué tipo de beneficios te interesan?"
            benefit_buttons = [
                {"title": "🏥 Salud", "payload": "beneficio_salud"},
                {"title": "💰 Bonos", "payload": "beneficio_bonos"},
                {"title": "📆 Días libres", "payload": "beneficio_dias_libres"}
            ]
            await send_message(platform, user_id, response, business_unit.name.lower(), options=benefit_buttons)
            return True

        if intent == "consultar_horario":
            response = "¿Buscas un horario específico?"
            horario_buttons = [
                {"title": "⏳ Jornada Completa", "payload": "horario_completo"},
                {"title": "⏰ Medio Tiempo", "payload": "horario_medio_tiempo"},
                {"title": "🔄 Flexible", "payload": "horario_flexible"}
            ]
            await send_message(platform, user_id, response, business_unit.name.lower(), options=horario_buttons)
            return True

        if intent == "consultar_tipo_contrato":
            response = "¿Qué tipo de contrato buscas?"
            contrato_buttons = [
                {"title": "📄 Indefinido", "payload": "contrato_indefinido"},
                {"title": "📌 Por Proyecto", "payload": "contrato_proyecto"},
                {"title": "💼 Freelance", "payload": "contrato_freelance"}
            ]
            await send_message(platform, user_id, response, business_unit.name.lower(), options=contrato_buttons)
            return True

        if intent == "preguntar_reubicacion":
            response = "¿Estás dispuesto a reubicarte por una oportunidad laboral?"
            reubicacion_buttons = [
                {"title": "✅ Sí", "payload": "reubicacion_si"},
                {"title": "❌ No", "payload": "reubicacion_no"},
                {"title": "🤔 Depende (ubicación/posición)", "payload": "reubicacion_depende"}
            ]
            await send_message(platform, user_id, response, business_unit.name.lower(), options=reubicacion_buttons)
            return True

    logger.info(f"No se manejó ningún intent conocido para: {text}")
    await send_message(platform, user_id, "No entendí tu mensaje. ¿Qué te gustaría hacer?", business_unit.name.lower())
    await send_options(platform, user_id, "Elige una opción:", main_options, business_unit.name.lower())
    return False
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
            await sync_to_async(SkillSet.objects.update_or_create)(
                person=user,
                defaults={'skills': parsed_data['skills']}
            )
            saved_attributes.append(f"skills: {parsed_data['skills']}")

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