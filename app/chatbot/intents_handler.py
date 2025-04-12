# /home/pablo/app/chatbot/intents_handler.py
import re
import logging
import asyncio
from typing import List, Dict, Any, Optional
from asgiref.sync import sync_to_async
from app.models import ChatState, Person, BusinessUnit, ConfiguracionBU
from app.chatbot.integrations.services import send_message, send_options, send_menu
from django.core.cache import cache
from django.utils import timezone
import random
from app.chatbot.workflow.common import calcular_salario_chatbot, iniciar_creacion_perfil, iniciar_perfil_conversacional, iniciar_prueba

logger = logging.getLogger(__name__)

# Cache para almacenar respuestas previas (mensaje -> respuesta)
response_cache = {}

# Diccionario de intents y sus respuestas
INTENT_PATTERNS = {
    "start_command": {
        "patterns": [r"\/start"],
        "responses": ["¡Hola! Bienvenido a tu asistente de reclutamiento. ¿Cómo puedo ayudarte hoy?"],
        "priority": 1
    },
    "saludo": {
        "patterns": [r"\b(hola|hi|buenos\s+días|buenas\s+tardes|buenas\s+noches|saludos|hey)\b"],
        "responses": [
            "¡Hola! 👋 Soy tu asistente de reclutamiento. ¿En qué puedo ayudarte hoy?",
            "¡Hola! 🌟 Bienvenido(a). ¿Cómo puedo apoyarte en tu búsqueda laboral?",
            "¡Saludos! 🤝 Estoy aquí para ayudarte con oportunidades laborales. ¿Qué necesitas?"
        ],
        "priority": 2
    },
    "tos_accept": {
        "patterns": [r"\b(tos_accept|accept_tos)\b"],
        "responses": ["Aceptaste los Términos de Servicio. ¡Continuemos!"],
        "priority": 3
    },
    "show_menu": {
        "patterns": [r"\b(menú|menu|opciones\s+disponibles|qué\s+puedes\s+hacer|qué\s+haces|servicios)\b"],
        "responses": ["Aquí tienes las opciones disponibles:"],
        "priority": 4
    },
    "presentacion_bu": {
        "patterns": [r"\b(qué\s+es\s+amigro|qué\s+hace\s+amigro|acerca\s+de\s+amigro|quiénes\s+son\s+ustedes|about\s+amigro)\b"],
        "responses": [
            "Amigro® 🌍 (amigro.org) es una organización que usa IA conversacional para facilitar el acceso laboral a mexicanos que regresan y migrantes de Latinoamérica en México. Te ayudamos a encontrar oportunidades según tu perfil, intereses y situación migratoria."
        ],
        "priority": 5
    },
    "show_jobs": {
        "patterns": [r"\b(ver\s+vacantes|mostrar\s+vacantes|vacante(s)?|oportunidad(es)?|empleo(s)?|trabajo(s)?|puestos|listado\s+de\s+vacantes)\b"],
        "responses": ["Te voy a mostrar vacantes recomendadas según tu perfil. Un momento..."],
        "priority": 10
    },
    "upload_cv": {
        "patterns": [r"\b(subir\s+cv|enviar\s+cv|cv|currículum|curriculum|resume|hoja\s+de\s+vida)\b"],
        "responses": ["¡Perfecto! Envíame tu CV en PDF o Word y lo procesaré para actualizar tu perfil. Adjunta el archivo en tu próximo mensaje."],
        "priority": 15
    },
    "cargar_cv": {
        "patterns": [r"\bcargar_cv\b"],
        "responses": ["¡Perfecto! Envíame tu CV en PDF o Word para cargarlo."],
        "priority": 18
    },
    "prueba_personalidad": {
        "patterns": [r"\bprueba_personalidad\b"],
        "responses": ["¡Vamos a iniciar tu prueba de personalidad! Esto te ayudará a conocer mejor tu perfil profesional."],
        "priority": 20  # Prioridad ajustable según tu lógica
    },  
    "contacto": {
        "patterns": [r"\bcontacto\b"],
        "responses": ["Te conectaré con un reclutador. Espera un momento."],
        "priority": 24
    },
    "ayuda": {
        "patterns": [r"\b(ayuda|faq)\b"],
        "responses": ["¿En qué necesitas ayuda? Puedo explicarte cómo usar el bot o resolver dudas comunes."],
        "priority": 25
    },
    "solicitar_ayuda_postulacion": {
        "patterns": [r"\b(ayuda\s+con\s+postulación|cómo\s+postular(me)?|aplicar\s+a\s+vacante|postular(me)?)\b"],
        "responses": ["Te puedo guiar para postularte. ¿A qué vacante te interesa aplicar o necesitas ayuda con el proceso?"],
        "priority": 20
    },
    "consultar_estado_postulacion": {
        "patterns": [r"\b(estado\s+de\s+mi\s+postulación|seguimiento\s+a\s+mi\s+aplicación|cómo\s+va\s+mi\s+proceso)\b"],
        "responses": ["Dame tu correo asociado a la postulación y te daré el estado actual."],
        "priority": 25
    },
    "actualizar_perfil": {
        "patterns": [r"\b(actualizar\s+perfil|cambiar\s+datos|modificar\s+información|editar\s+mi\s+perfil)\b"],
        "responses": ["¿Qué quieres actualizar? Puedes decirme: nombre, email, teléfono, habilidades, experiencia o salario esperado."],
        "priority": 30
    },
    "travel_in_group": {
        "patterns": [
            r"\b(travel_in_group|invitar|invita|invitar\s+a|invitación|"
            r"pasa\s+la\s+voz|pasar\s+la\s+voz|corre\s+la\s+voz|"
            r"reclutamiento\s+en\s+grupo|grupo\s+de\s+reclutamiento|"
            r"traer\s+a\s+alguien|recomendar\s+a\s+alguien|"
            r"amigo|conocido|familiar|compañero)\b"
        ],
        "responses": ["Voy a ayudarte a invitar a alguien. ¿Cuál es su nombre?"],
        "priority": 35
    },
    "solicitar_tips_entrevista": {
        "patterns": [r"\b(tips\s+para\s+entrevista|consejos\s+entrevista|preparación\s+entrevista|cómo\s+prepararme\s+para\s+entrevista)\b"],
        "responses": [
            "Claro, aquí tienes algunos consejos: investiga la empresa, llega puntual, prepara ejemplos de tus logros y practica respuestas a preguntas comunes. ¿Te gustaría más ayuda con algo específico?"
        ],
        "priority": 40
    },
    "calcular_salario": {
        "patterns": [r"\bcalcular_salario\b", r"salario\s*(bruto|neto)\s*=\s*[\d,\.]+k?"],
        "responses": ["Voy a calcular tu salario. Por favor, dime cuánto ganas (ej. 'salario bruto = 20k MXN mensual') y cualquier detalle extra como bonos o prestaciones, o en qué moneda lo tienes (yo te lo convierto si es necesario)."],
        "priority": 17
    },
    "consultar_sueldo_mercado": {
        "patterns": [r"\b(sueldo\s+mercado|rango\s+salarial|cuánto\s+pagan|salario\s+para\s+.*)\b"],
        "responses": ["¿Para qué posición o nivel quieres saber el rango salarial? Puedo darte una estimación basada en el mercado."],
        "priority": 50
    },
    "solicitar_contacto_reclutador": {
        "patterns": [r"\b(hablar\s+con\s+reclutador|contactar\s+a\s+alguien|necesito\s+un\s+reclutador)\b"],
        "responses": ["Te conectaré con un reclutador. Por favor, espera mientras te asigno uno."],
        "priority": 55
    },
    "busqueda_impacto": {
        "patterns": [r"\b(impacto\s+social|trabajo\s+con\s+propósito|vacantes\s+con\s+impacto)\b"],
        "responses": ["¿Buscas trabajo con impacto social? Puedo mostrarte vacantes con propósito. ¿Te interesa?"],
        "priority": 60
    },
    "agradecimiento": {
        "patterns": [r"\b(gracias|muchas\s+gracias|te\s+agradezco|thank\s+you)\b"],
        "responses": ["¡De nada! 😊 ¿En qué más puedo ayudarte?"],
        "priority": 65
    },
    "despedida": {
        "patterns": [r"\b(adiós|hasta\s+luego|bye|chao|nos\s+vemos)\b"],
        "responses": [
            "¡Hasta pronto! 👋 Si necesitas más ayuda, aquí estaré.",
            "¡Adiós! 🌟 Que tengas un gran día. Vuelve cuando quieras.",
            "¡Chao! 😊 Estoy a un mensaje de distancia si me necesitas."
        ],
        "priority": 70
    },
    "retry_conversation": {
        "patterns": [r"\b(intentemos\s+de\s+nuevo|volvamos\s+a\s+intentar|retry|de\s+nuevo|empezar\s+otra\s+vez)\b"],
        "responses": ["¡Claro! Vamos a empezar de nuevo. ¿En qué te ayudo ahora?"],
        "priority": 75
    }
}

# Lista de botones principales
main_options = [
    {"title": "💼 Ver Vacantes", "payload": "show_jobs"},
    {"title": "📄 Subir CV", "payload": "upload_cv"},
    {"title": "📋 Ver Menú", "payload": "show_menu"},
    {"title": "📝 Crear o Actualizar Perfil", "payload": "actualizar_perfil"},
    {"title": "📞 Contactar Reclutador", "payload": "solicitar_contacto_reclutador"}
]

def detect_intents(text: str) -> List[str]:
    """Detecta intents en el texto, incluyendo payloads exactos, ordenados por prioridad."""
    if not text:
        return []
    text = text.lower().strip()
    detected_intents = []
    
    # Primero, verificar si el texto coincide exactamente con un intent conocido (payloads)
    for intent, data in INTENT_PATTERNS.items():
        if text == intent:  # Coincidencia exacta para payloads como 'actualizar_perfil'
            detected_intents.append((intent, data.get('priority', 100)))
            logger.debug(f"[detect_intents] Intent exacto detectado: {intent}")
            break
    
    # Si no hay coincidencia exacta, buscar patrones regex
    if not detected_intents:
        for intent, data in INTENT_PATTERNS.items():
            for pattern in data['patterns']:
                if re.search(pattern, text):
                    detected_intents.append((intent, data.get('priority', 100)))
                    break  # Evita duplicados del mismo intent
    
    detected_intents.sort(key=lambda x: x[1])
    intents_list = [intent for intent, _ in detected_intents]
    logger.debug(f"[detect_intents] Intents detectados: {intents_list}")
    return intents_list

def get_tos_url(business_unit: BusinessUnit) -> str:
    tos_urls = {
        "huntred": "https://huntred.com/tos",
        "huntred executive": "https://huntred.com/executive/tos",
        "huntu": "https://huntu.mx/tos",
        "amigro": "https://amigro.org/tos",
        "sexsi": "https://sexsi.org/tos"
    }
    return tos_urls.get(business_unit.name.lower(), "https://huntred.com/tos")

async def handle_known_intents(intents: List[str], platform: str, user_id: str, text: str, chat_state: ChatState, business_unit: BusinessUnit, user: Person, chatbot=None) -> bool:
    logger.info(f"[handle_known_intents] Entrada: intents={intents}, chat_state={type(chat_state)}, business_unit={type(business_unit)}")
    
    if not isinstance(business_unit, BusinessUnit):
        logger.error(f"business_unit no es un BusinessUnit, es {type(business_unit)}. Intentando usar el de chat_state.")
        business_unit = getattr(chat_state, 'business_unit', None)
        if not isinstance(business_unit, BusinessUnit):
            logger.error("No se pudo recuperar un BusinessUnit válido.")
            await send_message(platform, user_id, "Ups, algo salió mal. ¿Intentamos de nuevo?", "default")
            return False
    
    if not isinstance(chat_state, ChatState):
        logger.error(f"chat_state no es un ChatState, es {type(chat_state)}. Abortando.")
        await send_message(platform, user_id, "Ups, algo salió mal. Contacta a soporte.", business_unit.name.lower())
        return False
    
    logger.info(f"[handle_known_intents] 🔎 Procesando intents: {intents} para BU: {business_unit.name}")
    bu_name_lower = business_unit.name.lower()  # Definido antes del try
    
    try:
        if not intents:
            logger.info(f"[handle_known_intents] No se detectaron intents en: '{text}'")
            return False

        primary_intent = intents[0]
        cache_key = f"intent:{user_id}:{text}"
        cached_response = cache.get(cache_key)

        if cached_response:
            await send_message(platform, user_id, cached_response, bu_name_lower)
            logger.info(f"[handle_known_intents] Respuesta obtenida de caché: '{cached_response}'")
            return True

        configuracion = await sync_to_async(lambda: ConfiguracionBU.objects.get(business_unit=business_unit))()
        bu_name_lower = business_unit.name.lower()

        # INTENTS ORGANIZADOS POR FLUJO DE RECLUTAMIENTO
        if primary_intent in INTENT_PATTERNS:
            responses = INTENT_PATTERNS[primary_intent]['responses']
            response = random.choice(responses)
            await send_message(platform, user_id, response, business_unit.name.lower())
            cache.set(cache_key, response, timeout=600)

            # 1. INICIO Y PRESENTACIÓN
            if primary_intent == "start_command":
                await send_menu(platform, user_id, business_unit)
            elif primary_intent == "saludo":
                bu_responses = INTENT_PATTERNS['presentacion_bu']['responses'] if bu_name_lower == "amigro" else [f"¡Hola! Bienvenido(a) a {business_unit.name}."]
                for msg in bu_responses:
                    await send_message(platform, user_id, msg, bu_name_lower)
                if chatbot and not chatbot.is_profile_complete(user, business_unit):
                    tos_url = get_tos_url(business_unit)
                    await send_message(platform, user_id, f"📜 Revisa nuestros Términos de Servicio: {tos_url}", bu_name_lower)
                    await send_options(platform, user_id, "¿Aceptas los Términos de Servicio?", 
                                       [{"title": "Sí", "payload": "tos_accept"}, {"title": "No", "payload": "tos_reject"}],
                                       bu_name_lower)
            elif primary_intent == "tos_accept":
                await send_message(platform, user_id, f"📜 Aceptaste los Términos de Servicio: {get_tos_url(business_unit)}", bu_name_lower)
                user.tos_accepted = True
                await sync_to_async(user.save)()
                chat_state.state = "profile_in_progress"
                await sync_to_async(chat_state.save)()
                await send_menu(platform, user_id, business_unit)
                return True
            elif primary_intent == "show_menu":
                await send_menu(platform, user_id, business_unit)
                
            # 2. CREACIÓN Y GESTIÓN DE PERFIL
            elif primary_intent == "actualizar_perfil":
                chat_state.state = "profile_in_progress"
                await sync_to_async(chat_state.save)()
                await chatbot.start_profile_creation(platform, user_id, business_unit, chat_state, user)
                return True
            elif primary_intent == "mi_perfil":
                if not user.profile_complete:
                    await send_message(platform, user_id, "Primero necesitas crear un perfil. ¿Deseas hacerlo ahora?", business_unit.name.lower())
                    await send_options(platform, user_id, "Selecciona una opción:", 
                                    [{"title": "Sí", "payload": "actualizar_perfil"}, {"title": "No", "payload": "no_action"}],
                                    business_unit.name.lower())
                else:
                    await send_message(platform, user_id, "¿Qué deseas actualizar? Puedes decirme: nombre, email, teléfono, habilidades, experiencia o salario esperado.", business_unit.name.lower())
                    chat_state.state = "waiting_for_profile_field"
                    await sync_to_async(chat_state.save)()
                return True
            elif primary_intent == "upload_cv" or primary_intent == "cargar_cv":
                chat_state.state = "waiting_for_cv"
                await sync_to_async(chat_state.save)()
            elif primary_intent == "prueba_personalidad":
                from app.chatbot.workflow.common import iniciar_prueba_personalidad
                await iniciar_prueba_personalidad(platform, user_id, business_unit, chat_state, user, "tipi")
                return True
                
            # 3. BÚSQUEDA DE VACANTES
            elif primary_intent == "show_jobs":
                from app.utilidades.vacantes import VacanteManager
                manager = VacanteManager({"business_unit": business_unit})
                await manager.initialize()  # Inicializar con configuraciones de BU
                jobs = await manager.match_person_with_jobs(user)  # Método actualizado para ser dinámico
                if jobs:
                    await present_job_listings(platform, user_id, [j["job"] for j in jobs], business_unit, chat_state)
                else:
                    await send_message(platform, user_id, "No encontré vacantes para tu perfil aún. ¿Quieres subir tu CV para mejorar las recomendaciones?", bu_name_lower)
            elif primary_intent == "ver_vacantes":
                from app.utilidades.vacantes import VacanteManager
                jobs = await sync_to_async(VacanteManager.match_person_with_jobs)(user)
                if jobs:
                    await present_job_listings(platform, user_id, jobs, business_unit, chat_state)
                else:
                    await send_message(platform, user_id, "No encontré vacantes para tu perfil aún. ¿Quieres subir tu CV para mejorar las recomendaciones?", business_unit.name.lower())
                return True
            elif primary_intent == "solicitar_ayuda_postulacion":
                await send_options(platform, user_id, "¿En qué parte necesitas ayuda?", 
                                   [{"title": "Buscar Vacante", "payload": "show_jobs"}, {"title": "Aplicar", "payload": "apply_job"}],
                                   bu_name_lower)
            elif primary_intent == "consultar_estado_postulacion":
                chat_state.state = "waiting_for_status_email"
                await sync_to_async(chat_state.save)()
            elif primary_intent == "busqueda_impacto":
                await send_options(platform, user_id, "¿Qué tipo de impacto buscas?", 
                                   [{"title": "Social", "payload": "impact_social"}, {"title": "Ambiental", "payload": "impact_environmental"}],
                                   bu_name_lower)
                                   
            # 4. INFORMACIÓN SALARIAL
            elif primary_intent == "calcular_salario":
                response = await calcular_salario_chatbot(platform, user_id, text, bu_name_lower)
                if response:
                    cache.set(cache_key, response, timeout=600)
                    await send_message(platform, user_id, response, bu_name_lower)
                chat_state.state = "waiting_for_salary_details"
                await sync_to_async(chat_state.save)()
                logger.info(f"[handle_known_intents] Intent manejado: calcular_salario")
                return True
            elif primary_intent == "consultar_sueldo_mercado":
                chat_state.state = "waiting_for_salary_position"
                await sync_to_async(chat_state.save)()
                
            # 5. PREPARACIÓN PARA ENTREVISTAS
            elif primary_intent == "solicitar_tips_entrevista":
                await send_options(platform, user_id, "¿Quieres más tips o practicar una entrevista?", 
                                   [{"title": "Más Tips", "payload": "more_tips"}, {"title": "Practicar", "payload": "practice_interview"}],
                                   bu_name_lower)
                                   
            # 6. APOYO GRUPAL Y SOCIAL
            elif primary_intent == "travel_in_group":
                if chatbot:
                    await chatbot.handle_group_invitation_input(platform, user_id, text, chat_state, business_unit, user)
                else:
                    logger.error("Chatbot instance not provided for travel_in_group intent")
                    await send_message(platform, user_id, "Ups, algo salió mal al intentar invitar a alguien. Intenta de nuevo.", bu_name_lower)
                return True
                
            # 7. CONTACTO Y AYUDA
            elif primary_intent == "contacto" or primary_intent == "solicitar_contacto_reclutador":
                configuracion = await sync_to_async(lambda: ConfiguracionBU.objects.get(business_unit=business_unit))()
                admin_phone = configuracion.telefono_bu or "525518490291"
                
                # Recopilar información disponible del candidato
                candidate_info = {}
                
                if user.nombre:
                    candidate_info["Nombre"] = f"{user.nombre} {user.apellido_paterno or ''} {user.apellido_materno or ''}".strip()
                if user.nacionalidad:
                    candidate_info["Nacionalidad"] = user.nacionalidad
                if user.email:
                    candidate_info["Email"] = user.email
                if user.phone:
                    candidate_info["Teléfono"] = user.phone
                if user.preferred_language:
                    candidate_info["Idioma Preferido"] = user.preferred_language
                if user.job_search_status:
                    candidate_info["Estado de Búsqueda"] = user.job_search_status
                if user.desired_job_types:
                    candidate_info["Tipos de Empleo Deseados"] = user.desired_job_types
                if user.skills:
                    candidate_info["Habilidades"] = user.skills
                if user.experience_years is not None:
                    candidate_info["Años de Experiencia"] = user.experience_years
                if user.salary_data and "expected_salary" in user.salary_data:
                    candidate_info["Salario Esperado"] = user.salary_data["expected_salary"]
                if user.metadata and "desired_locations" in user.metadata:
                    candidate_info["Ubicación Deseada"] = user.metadata["desired_locations"]
                candidate_info["Estado del Perfil"] = "Completo" if user.is_profile_complete() else "Incompleto"
                
                # Verificar si faltan datos críticos
                if not user.phone and not user.email:
                    await send_message(platform, user_id, "Para contactarte, necesitamos al menos tu teléfono o email. Por favor, proporciónalos.", bu_name_lower)
                    return False
                
                # Formatear el mensaje con la información disponible
                recap_message = "Información del candidato que requiere asistencia:\n"
                for key, value in candidate_info.items():
                    recap_message += f"{key}: {value}\n"
                
                # Enviar el mensaje al administrador
                await send_message(platform, admin_phone, recap_message, bu_name_lower)
                
                # Confirmar al candidato
                await send_message(platform, user_id, "Un reclutador te contactará pronto.", bu_name_lower)
                return True
            elif primary_intent == "ayuda":
                await send_options(platform, user_id, "¿Qué necesitas?", 
                                   [{"title": "Cómo usar el bot", "payload": "help_usage"}, {"title": "FAQ", "payload": "help_faq"}],
                                   bu_name_lower)
            elif primary_intent == "help_usage":
                await send_message(platform, user_id, "Aquí te explico cómo usar el bot: [instrucciones detalladas].", business_unit.name.lower())
                return True
            elif primary_intent == "help_faq":
                await send_message(platform, user_id, "Preguntas frecuentes: [lista de FAQs].", business_unit.name.lower())
                return True
            elif primary_intent == "retry_conversation":
                chat_state.state = "initial"
                chat_state.context = {}
                await sync_to_async(chat_state.save)()
                await send_menu(platform, user_id, business_unit)

            logger.info(f"[handle_known_intents] Intent manejado: {primary_intent}")
            return True

        return False

    except Exception as e:
        logger.error(f"[handle_known_intents] ❌ Error: {e}", exc_info=True)
        await send_message(platform, user_id, "Ups, algo salió mal. ¿Intentamos de nuevo?", bu_name_lower)
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
    """Maneja la carga de documentos como CVs."""
    import requests
    from django.core.exceptions import ValidationError
    
    # Verificar tamaño del archivo
    response = requests.head(file_url)
    file_size = int(response.headers.get('Content-Length', 0)) / 1024 / 1024  # Tamaño en MB
    if file_size > 5:  # Límite de 5 MB
        await send_message(platform, user_id, "El archivo es demasiado grande (máximo 5 MB). Por favor, reduce su tamaño y vuelve a intentarlo.", business_unit.name.lower())
        return
    
    # Validar tipo de archivo
    valid_types = ['pdf', 'application/pdf', 'doc', 'docx', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
    if file_type.lower() not in valid_types:
        await send_message(platform, user_id, f"No puedo procesar archivos de tipo {file_type}. Usa PDF o Word.", business_unit.name.lower())
        return
    from app.utilidades.parser import parse_document
    
    await send_message(platform, user_id, "Estoy procesando tu documento. Esto tomará unos momentos...", business_unit.name.lower())
    
    try:
        if file_type.lower() in ['pdf', 'application/pdf']:
            parsed_data = await sync_to_async(parse_document)(file_url, 'pdf')
        elif file_type.lower() in ['doc', 'docx', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
            parsed_data = await sync_to_async(parse_document)(file_url, 'doc')
        else:
            await send_message(platform, user_id, f"No puedo procesar archivos de tipo {file_type}. Usa PDF o Word.", business_unit.name.lower())
            return
        
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
            user.skills = ', '.join(parsed_data['skills']) if isinstance(parsed_data['skills'], list) else parsed_data['skills']
            saved_attributes.append(f"skills: {user.skills}")

        await sync_to_async(user.save)()
        logger.info(f"[handle_document_upload] Atributos guardados para {user_id}: {', '.join(saved_attributes)}")

        response = (
            "✅ ¡He procesado tu CV correctamente!\n\n"
            "Datos extraídos:\n"
            f"👤 Nombre: {parsed_data.get('name', 'No detectado')}\n"
            f"📧 Email: {parsed_data.get('email', 'No detectado')}\n"
            f"📱 Teléfono: {parsed_data.get('phone', 'No detectado')}\n"
            f"🛠 Habilidades: {', '.join(parsed_data.get('skills', [])) or 'No detectadas'}\n\n"
            "¿Están correctos estos datos? Responde 'sí' para confirmar o 'no' para corregir."
        )
        await send_message(platform, user_id, response, business_unit.name.lower())
        
        chat_state.state = "waiting_for_cv_confirmation"
        chat_state.context['parsed_data'] = parsed_data
        await sync_to_async(chat_state.save)()
        
    except Exception as e:
        logger.error(f"Error procesando documento: {str(e)}", exc_info=True)
        await send_message(platform, user_id, "❌ Hubo un problema al procesar tu documento. Intenta de nuevo.", business_unit.name.lower())

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
    """Presenta listados de trabajo al usuario con paginación y filtros opcionales."""
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
    
    response = f"Aquí tienes algunas vacantes recomendadas (página {page + 1} de {total_jobs // jobs_per_page + 1}):\n"
    job_options = []
    for idx, job in enumerate(filtered_jobs[start_idx:end_idx], start=start_idx + 1):
        salary = f"${job.get('salary', 'N/A')}" if job.get('salary') else "N/A"
        location = job.get('location', 'No especificada')
        response += f"{idx}. {job['title']} - {job.get('company', 'N/A')} ({location}, Salario: {salary})\n"
        job_options.append({"title": f"Vacante {idx}", "payload": f"job_{idx-1}"})
    
    navigation_options = []
    if start_idx > 0:
        navigation_options.append({"title": "⬅️ Anterior", "payload": f"jobs_page_{page - 1}"})
    if end_idx < total_jobs:
        navigation_options.append({"title": "➡️ Siguiente", "payload": f"jobs_page_{page + 1}"})
    
    all_options = job_options + navigation_options
    await send_message(platform, user_id, response, business_unit.name.lower(), options=all_options if all_options else None)
    chat_state.context['current_jobs_page'] = page
    chat_state.context['recommended_jobs'] = filtered_jobs
    await sync_to_async(chat_state.save)()