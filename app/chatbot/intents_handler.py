# Ubicación: /home/pablo/app/chatbot/intents_handler.py
import logging
from typing import List, Dict, Any, Tuple
from asgiref.sync import sync_to_async

from app.models import ChatState, Person, BusinessUnit
from app.chatbot.integrations.services import  send_message, send_email, send_options, reset_chat_state, send_menu, MENU_OPTIONS_BY_BU
from app.utilidades.vacantes import VacanteManager

logger = logging.getLogger(__name__)


async def handle_known_intents(intents: List[str], platform: str, user_id: str, chat_state: ChatState, business_unit: BusinessUnit, user: Person, text: str = "") -> bool:
    """
    Maneja los intents conocidos del usuario.
    Devuelve True si se manejó una intención, False si no.
    """
    text = text.lower().strip()

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

    # Detección por palabras clave
    greeting_keywords = ["hola", "buenos días", "buenas tardes", "buenas noches"]
    if any(keyword in text for keyword in greeting_keywords):
        response = INTENT_RESPONSES["saludo"]
        await send_message(platform, user_id, response, business_unit)
        return True

    cv_keywords = ["cv", "currículum", "curriculum", "resume", "hoja de vida"]
    if any(keyword in text for keyword in cv_keywords):
        response = "¡Perfecto! Puedes enviarme tu CV por este medio y lo procesaré para extraer la información relevante. Por favor, adjunta el archivo en tu próximo mensaje."
        await send_message(platform, user_id, response, business_unit)
        chat_state.state = "waiting_for_cv"
        await sync_to_async(chat_state.save)()
        return True

    # Manejo de intents detectados por NLP o texto directo
    for intent in intents or [text]:
        logger.debug(f"[handle_known_intents] Intent detectado: {intent}")

        if intent in INTENT_RESPONSES:
            response = INTENT_RESPONSES[intent]
            await send_message(platform, user_id, response, business_unit)
            return True

        # Intent "menu"
        if "menu" in intents or text == "menu":
            await send_menu(platform, user_id)
            return True

        if intent == "reset_chat_state":
            await reset_chat_state(user_id, business_unit, platform)
            await send_message(platform, user_id, f"🧹 ¡Listo, {user.nombre}! Tu conversación en {platform} ha sido reiniciada. ¿En qué puedo ayudarte ahora?", business_unit)
            return True

        if intent == "consultar_estatus":
            response = "Por favor, proporciona tu correo electrónico asociado a la aplicación."
            await send_message(platform, user_id, response, business_unit)
            chat_state.context['awaiting_status_email'] = True
            await sync_to_async(chat_state.save)()
            return True

        if intent in ["travel_in_group", "travel_with_family"]:
            response = (
                "Entiendo, ¿te gustaría invitar a tus acompañantes para que también obtengan oportunidades laborales? "
                "Envíame su nombre completo y teléfono en el formato: 'Nombre Apellido +52XXXXXXXXXX'."
            )
            await send_message(platform, user_id, response, business_unit)
            chat_state.context['awaiting_group_invitation'] = True
            await sync_to_async(chat_state.save)()
            return True

        if intent == "ver_vacantes":
            recommended_jobs = await sync_to_async(VacanteManager.match_person_with_jobs)(user)
            if recommended_jobs:
                chat_state.context['recommended_jobs'] = recommended_jobs
                await sync_to_async(chat_state.save)()
                await present_job_listings(platform, user_id, recommended_jobs, business_unit, chat_state)
            else:
                await send_message(platform, user_id, "No encontré vacantes para tu perfil por ahora.", business_unit)
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
                await send_message(platform, user_id, "📜 Consulta nuestros términos aquí: https://amigro.org/tos", business_unit)
            await send_message(platform, user_id, response, business_unit, options=tos_buttons)
            return True

        if intent == "calcular_salario":
            response = "¿Qué deseas calcular?\n1. Salario neto (desde bruto)\n2. Salario bruto (desde neto)\nResponde con '1' o '2'."
            await send_message(platform, user_id, response, business_unit)
            chat_state.state = "waiting_for_salary_calc_type"
            await sync_to_async(chat_state.save)()
            return True

        if intent == "consultar_requisitos_vacante":
            response = "Por favor, dime el nombre o ID de la vacante sobre la que quieres saber los requisitos."
            await send_message(platform, user_id, response, business_unit)
            chat_state.state = "waiting_for_vacancy_id"
            await sync_to_async(chat_state.save)()
            return True

        if intent == "solicitar_contacto_reclutador":
            response = "Te conectaré con un reclutador. Por favor, espera mientras te asignamos uno."
            await send_message(platform, user_id, response, business_unit)
            response_recruit = "Un candidato requiere asistencia especial, te paso sus datos - "
            await send_message(platform, 525518490291, response_recruit, business_unit)
            return True

        if intent == "preparacion_entrevista":  # Consolidado con "solicitar_tips_entrevista"
            response = "Para entrevistas: investiga la empresa, sé puntual, muestra logros cuantificables y prepara ejemplos de situaciones pasadas. ¿Necesitas más ayuda?"
            await send_message(platform, user_id, response, business_unit)
            return True

        if intent == "consultar_beneficios":
            response = "¿Qué tipo de beneficios te interesan?"
            benefit_buttons = [
                {"title": "🏥 Salud", "payload": "beneficio_salud"},
                {"title": "💰 Bonos", "payload": "beneficio_bonos"},
                {"title": "📆 Días libres", "payload": "beneficio_dias_libres"}
            ]
            await send_message(platform, user_id, response, business_unit, options=benefit_buttons)
            return True

        if intent == "consultar_horario":
            response = "¿Buscas un horario específico?"
            horario_buttons = [
                {"title": "⏳ Jornada Completa", "payload": "horario_completo"},
                {"title": "⏰ Medio Tiempo", "payload": "horario_medio_tiempo"},
                {"title": "🔄 Flexible", "payload": "horario_flexible"}
            ]
            await send_message(platform, user_id, response, business_unit, options=horario_buttons)
            return True

        if intent == "consultar_tipo_contrato":
            response = "¿Qué tipo de contrato buscas?"
            contrato_buttons = [
                {"title": "📄 Indefinido", "payload": "contrato_indefinido"},
                {"title": "📌 Por Proyecto", "payload": "contrato_proyecto"},
                {"title": "💼 Freelance", "payload": "contrato_freelance"}
            ]
            await send_message(platform, user_id, response, business_unit, options=contrato_buttons)
            return True

        if intent == "preguntar_reubicacion":
            response = "¿Estás dispuesto a reubicarte por una oportunidad laboral?"
            reubicacion_buttons = [
                {"title": "✅ Sí", "payload": "reubicacion_si"},
                {"title": "❌ No", "payload": "reubicacion_no"},
                {"title": "🤔 Depende (ubicación/posición)", "payload": "reubicacion_depende"}
            ]
            await send_message(platform, user_id, response, business_unit, options=reubicacion_buttons)
            return True

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
    
    Args:
        file_url (str): URL del archivo
        file_type (str): Tipo de archivo (pdf, doc, etc.)
        platform (str): Plataforma de mensajería
        user_id (str): ID del usuario
        business_unit (BusinessUnit): Unidad de negocio
        user (Person): Usuario
        chat_state (ChatState): Estado del chat
    """
    from app.utilidades.parser import parse_document
    
    await send_message(
        platform, 
        user_id, 
        "Estoy procesando tu documento. Esto tomará unos momentos...", 
        business_unit
    )
    
    try:
        # Procesar el documento según su tipo
        if file_type.lower() in ['pdf', 'application/pdf']:
            parsed_data = await sync_to_async(parse_document)(file_url, 'pdf')
        elif file_type.lower() in ['doc', 'docx', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
            parsed_data = await sync_to_async(parse_document)(file_url, 'doc')
        else:
            await send_message(
                platform, 
                user_id, 
                f"No puedo procesar archivos de tipo {file_type}. Por favor, envía tu archivo en PDF o Word. (lo siento, no me han enseñado como procesar otros archivos.)", 
                business_unit
            )
            return
        
        # Actualizar perfil del usuario con datos del CV
        user.cv_parsed = True
        user.cv_url = file_url
        user.cv_parsed_data = parsed_data
        
        if 'name' in parsed_data and not user.nombre:
            user.nombre = parsed_data['name']
        
        if 'email' in parsed_data and not user.email:
            user.email = parsed_data['email']
        
        if 'phone' in parsed_data and not user.phone:
            user.phone = parsed_data['phone']
        
        if 'skills' in parsed_data:
            await sync_to_async(SkillSet.objects.update_or_create)(
                person=user,
                defaults={'skills': parsed_data['skills']}
            )
        
        await sync_to_async(user.save)()
        
        # Responder al usuario con los datos extraídos
        response = (
            "✅ ¡He procesado tu CV correctamente!\n\n"
            "Datos extraídos:\n"
            f"👤 Nombre: {parsed_data.get('name', 'No detectado')}\n"
            f"📧 Email: {parsed_data.get('email', 'No detectado')}\n"
            f"📱 Teléfono: {parsed_data.get('phone', 'No detectado')}\n"
            f"🛠 Habilidades: {', '.join(parsed_data.get('skills', [])) or 'No detectadas'}\n\n"
            "¿Están correctos estos datos? Por favor, responde 'sí' para confirmar o 'no' para corregir."
        )
        
        await send_message(platform, user_id, response, business_unit)
        
        # Actualizar el estado para esperar confirmación
        chat_state.state = "waiting_for_cv_confirmation"
        chat_state.context['parsed_data'] = parsed_data
        await sync_to_async(chat_state.save)()
        
    except Exception as e:
        logger.error(f"Error procesando documento: {str(e)}")
        await send_message(
            platform, 
            user_id, 
            "❌ Hubo un problema al procesar tu documento. Por favor, intenta de nuevo.", 
            business_unit
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
        await send_message(platform, user_id, "No encontré vacantes que coincidan con tus filtros.", business_unit)
        return
    
    total_jobs = len(filtered_jobs)
    start_idx = page * jobs_per_page
    end_idx = min(start_idx + jobs_per_page, total_jobs)
    
    # Resto de la lógica sigue igual...
    # (Aquí iría el resto del código que ya tienes, adaptado para usar filtered_jobs)
