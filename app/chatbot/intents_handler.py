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
from app.chatbot.workflow.common import calcular_salario_chatbot, iniciar_creacion_perfil, iniciar_perfil_conversacional, iniciar_prueba, send_welcome_message
from app.ml.ml_model import MatchmakingLearningSystem, BUSINESS_UNIT_HIERARCHY
from app.chatbot.intents_optimizer import intent_optimizer
from app.chatbot.channel_config import ChannelConfig
from app.chatbot.metrics import chatbot_metrics

logger = logging.getLogger('chatbot')

# Cache para almacenar respuestas previas (mensaje -> respuesta)
response_cache = {}

# Diccionario de intents y sus respuestas
INTENT_PATTERNS = {
    "start_command": {
        "patterns": [r"\/start"],
        "responses": ["¡Hola! Bienvenido al mejor asistente de reclutamiento. ¿Cómo puedo ayudarte hoy?"],
        "priority": 1
    },
    "saludo": {
        "patterns": [r"\b(hola|hi|buenos\s+días|buenas\s+tardes|buenas\s+noches|saludos|hey)\b"],
        "responses": {
            "amigro": ["¡Hola! 👋 Soy Amigro, aquí para apoyarte en tu búsqueda laboral en México, encontrando trabajo digno y alineado a tu experiencia e interéses."],
            "huntu": ["¡Hola! 🌟 Huntu está listo para ayudarte a dar pasos profesionales sólidos y de gran impacto para tu carrera."],
            "huntred": ["¡Saludos! 🤝 HuntRED te ayuda a encontrar roles gerenciales clave."],
            "huntred_executive": ["¡Hola! HuntRED® Executive, tu aliado para posiciones de alto nivel."],
            "sexsi": ["¡Saludos! Sexsi asegura que todo sea claro y consensuado. ¿En qué te ayudo?"],
            "default": ["¡Hola! Soy tu asistente de reclutamiento. ¿En qué puedo ayudarte?"]
        },
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
        "responses": {
            "amigro": ["Amigro® 🌍 (amigro.org) usa IA para facilitar el acceso laboral a migrantes en México."],
            "huntu": ["Huntu 🚀 conecta estudiantes con internships y empleos de inicio profesional."],
            "huntred": ["HuntRED 💼 especializa en colocar gerentes y directivos en roles clave."],
            "huntred_executive": ["HuntRED® Executive 🎯 encuentra líderes para consejos y direcciones."],
            "sexsi": ["Sexsi 📜 crea contratos consensuados para relaciones sexuales seguras y legales."],
            "default": ["Somos un asistente de reclutamiento para diversas necesidades laborales."]
        },
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
        "priority": 20
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
    "crear_perfil": {
        "patterns": [r"\b(crear\s+perfil|iniciar\s+perfil|comenzar\s+perfil)\b"],
        "responses": ["¡Vamos a crear tu perfil! Empecemos con tu nombre."],
        "priority": 30
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
    },
    "migratory_status": {  # Nueva intención para Amigro
        "patterns": [r"\b(estatus\s+migratorio|permiso\s+trabajo|visa|refugio)\b"],
        "responses": {
            "amigro": ["Puedo ayudarte con tu estatus migratorio. ¿Tienes permiso de trabajo o necesitas apoyo con eso?"],
            "default": ["Este servicio está disponible solo para Amigro. ¿En qué más te ayudo?"]
        },
        "priority": 30
    },
    "internship_search": {  # Nueva intención para Huntu
        "patterns": [r"\b(prácticas|internship|pasantía|empleo\s+estudiantil)\b"],
        "responses": {
            "huntu": ["Busco internships perfectos para estudiantes como tú. ¿Qué área te interesa?"],
            "default": ["Este servicio está disponible solo para Huntu. ¿En qué más te ayudo?"]
        },
        "priority": 30
    },
    "executive_roles": {  # Nueva intención para HuntRED y HuntRED Executive
        "patterns": [r"\b(director|consejo|ejecutivo|alto\s+nivel)\b"],
        "responses": {
            "huntred": ["Te ayudo a encontrar roles gerenciales. ¿Qué nivel buscas?"],
            "huntred_executive": ["Conecto líderes con posiciones ejecutivas. ¿Qué rol te interesa?"],
            "default": ["Este servicio es para HuntRED o Executive. ¿En qué más te ayudo?"]
        },
        "priority": 30
    },
    "create_contract": {  # Nueva intención para Sexsi
        "patterns": [r"\b(crear\s+contrato|acuerdo|consentimiento)\b"],
        "responses": {
            "sexsi": ["Vamos a crear un contrato consensuado. ¿Qué términos quieres incluir?"],
            "default": ["Este servicio está disponible solo para Sexsi. ¿En qué más te ayudo?"]
        },
        "priority": 30
    },
    "transition_to_higher_bu": {  # Nueva intención para transiciones ascendentes
        "patterns": [r"\b(transicionar|subir de nivel|ascender)\b"],
        "responses": ["Voy a evaluar si cumples con los requisitos para subir de nivel."],
        "priority": 30
    }
}

# Lista de botones principales
main_options = [
    {"title": "💼 Ver Vacantes", "payload": "show_jobs"},
    {"title": "📄 Subir CV", "payload": "upload_cv"},
    {"title": "📋 Ver Menú", "payload": "show_menu"},
    {"title": "📝 Crear o Actualizar Perfil", "payload": "actualizar_perfil"},
    {"title": "📞 Contactar Reclutador", "payload": "solicitar_contacto_reclutador"},
    {"title": "🔝 Subir de Nivel", "payload": "transition_to_higher_bu"}
]

def detect_intents(text: str) -> List[str]:
    """Detecta intents en el texto, incluyendo payloads exactos, ordenados por prioridad."""
    if not text:
        return []
    detected_intents = []
    
    # Verificar payloads exactos primero
    if text.startswith('/'):
        command = text[1:].strip()
        for intent, data in INTENT_PATTERNS.items():
            if command == intent:
                detected_intents.append(intent)
                break
    
    # Verificar patrones de regex
    if not detected_intents:
        # Optimizar patrones usando el optimizador
        optimized_patterns = {
            intent: IntentOptimizer.optimize_patterns(data['patterns'])
            for intent, data in INTENT_PATTERNS.items()
        }
        
        compiled_patterns = {
            intent: IntentOptimizer.compile_patterns(patterns)
            for intent, patterns in optimized_patterns.items()
        }
        
        for intent, compiled in sorted(compiled_patterns.items(), key=lambda x: INTENT_PATTERNS[x[0]]['priority']):
            for pattern in compiled:
                if pattern.search(text.lower()):
                    detected_intents.append(intent)
                    break
            if detected_intents:
                break
    
    # Registrar métrica de detección de intents
    ChatbotMetrics.track_message('intent_detection', 'completed', success=bool(detected_intents))
    
    return detected_intents

def get_tos_url(business_unit: BusinessUnit) -> str:
    tos_urls = {
        "huntred": "https://huntred.com/tos",
        "huntred executive": "https://huntred.com/executive/tos",
        "huntu": "https://huntu.mx/tos",
        "amigro": "https://amigro.org/tos",
        "sexsi": "https://sexsi.org/tos"
    }
    return tos_urls.get(business_unit.name.lower(), "https://huntred.com/tos")

async def handle_known_intents(intents: List[str], platform: str, user_id: str, chat_state: ChatState, business_unit: BusinessUnit, text: str, handler=None) -> bool:
    """Maneja los intents conocidos de manera optimizada."""
    if not intents:
        return False

    bu_name_lower = business_unit.name.lower().replace('®', '').strip()
    cache_key = f"intent:{user_id}:{text}"
    cached_response = cache.get(cache_key)

    if cached_response:
        await send_message(platform, user_id, cached_response, bu_name_lower)
        logger.info(f"[handle_known_intents] Respuesta desde caché: {cached_response}")
        return True

    primary_intent = intents[0]
    
    try:
        configuracion = await sync_to_async(lambda: ConfiguracionBU.objects.get(business_unit=business_unit))()

        # Respuestas básicas desde INTENT_PATTERNS
        if primary_intent in INTENT_PATTERNS:
            responses = INTENT_PATTERNS[primary_intent]['responses']
            # Manejar respuestas según tipo
            if isinstance(responses, list):
                # Si responses es una lista, elegir una respuesta directamente
                response = random.choice(responses)
            else:
                # Si responses es un diccionario, elegir según la unidad de negocio
                response = random.choice(responses.get(bu_name_lower, responses.get('default', ['Opción no disponible'])))
            await send_message(platform, user_id, response, bu_name_lower)
            cache.set(cache_key, response, timeout=600)

        # 1. INICIO Y PRESENTACIÓN
        if primary_intent == "start_command":
            await send_menu(platform, user_id, business_unit)
            return True
        elif primary_intent == "saludo":
            from app.chatbot.workflow.common import send_welcome_message
            await send_welcome_message(user_id, platform, business_unit)
            if handler and not handler.is_profile_complete(chat_state.person, business_unit):
                tos_url = get_tos_url(business_unit)
                await send_message(platform, user_id, f"📜 Revisa nuestros Términos de Servicio: {tos_url}", bu_name_lower)
                await send_options(platform, user_id, "¿Aceptas los Términos de Servicio?",
                                   [{"title": "Sí", "payload": "tos_accept"}, {"title": "No", "payload": "tos_reject"}],
                                   bu_name_lower)
            return True
        elif primary_intent == "tos_accept":
            user = chat_state.person
            user.tos_accepted = True
            await sync_to_async(user.save)()
            chat_state.state = "profile_in_progress"
            await sync_to_async(chat_state.save)()
            await send_menu(platform, user_id, business_unit)
            return True
        elif primary_intent == "show_menu":
            await send_menu(platform, user_id, business_unit)
            return True
        
        # 2. CREACIÓN Y GESTIÓN DE PERFIL
        elif primary_intent in ["crear_perfil", "actualizar_perfil"]:
            from app.chatbot.workflow.common import iniciar_creacion_perfil
            if not handler.is_profile_complete(user, business_unit):
                # Perfil incompleto o no existe, iniciar creación
                logger.info(f"[handle_known_intents] Perfil incompleto para {user_id}, iniciando creación")
                await iniciar_creacion_perfil(platform, user_id, business_unit, chat_state, user)
            else:
                # Perfil completo, permitir actualización
                await send_message(platform, user_id, "¿Qué quieres actualizar? Puedes decirme: nombre, email, teléfono, habilidades, experiencia o salario esperado.", bu_name_lower)
                chat_state.state = "updating_profile"
                await sync_to_async(chat_state.save)()
            return True
        elif primary_intent == "mi_perfil":
            from app.chatbot.workflow.common import obtener_resumen_perfil
            if not handler.is_profile_complete(user, business_unit):
                await send_message(platform, user_id, "Primero necesitas crear un perfil. ¿Deseas hacerlo ahora?", bu_name_lower)
                await send_options(platform, user_id, "Selecciona una opción:",
                                   [{"title": "Sí", "payload": "crear_perfil"}, {"title": "No", "payload": "no_action"}],
                                   bu_name_lower)
            else:
                recap_message = await obtener_resumen_perfil(user)
                await send_message(platform, user_id, recap_message, bu_name_lower)
                chat_state.state = "waiting_for_profile_confirmation"
                await sync_to_async(chat_state.save)()
            return True
        elif primary_intent in ["upload_cv", "cargar_cv"]:
            chat_state.state = "waiting_for_cv"
            await send_message(platform, user_id, "Por favor, envía tu CV como archivo adjunto (PDF o Word).", bu_name_lower)
            await sync_to_async(chat_state.save)()
            return True
        elif primary_intent == "prueba_personalidad":
            from app.chatbot.workflow.common import ofrecer_prueba_personalidad
            await ofrecer_prueba_personalidad(platform, user_id, business_unit, chat_state, user)
            return True

        # 3. BÚSQUEDA DE VACANTES
        elif primary_intent in ["show_jobs", "ver_vacantes"]:
            from app.utilidades.vacantes import VacanteManager
            manager = VacanteManager({"business_unit": business_unit})
            await manager.initialize()
            jobs = await manager.match_person_with_jobs(user)
            if jobs:
                await present_job_listings(platform, user_id, [j["job"] for j in jobs] if primary_intent == "show_jobs" else jobs, business_unit, chat_state)
            else:
                await send_message(platform, user_id, "No encontré vacantes para tu perfil aún. ¿Quieres subir tu CV?", bu_name_lower)
                await send_options(platform, user_id, "¿Subir CV?",
                                   [{"title": "Sí", "payload": "upload_cv"}, {"title": "No", "payload": "no_action"}],
                                   bu_name_lower)
            return True
        elif primary_intent == "solicitar_ayuda_postulacion":
            await send_options(platform, user_id, "¿En qué parte necesitas ayuda?",
                               [{"title": "Buscar Vacante", "payload": "show_jobs"}, {"title": "Aplicar", "payload": "apply_job"}],
                               bu_name_lower)
            return True
        elif primary_intent == "consultar_estado_postulacion":
            chat_state.state = "waiting_for_status_email"
            await send_message(platform, user_id, "Por favor, proporciona el email con el que te postulaste.", bu_name_lower)
            await sync_to_async(chat_state.save)()
            return True
        elif primary_intent == "busqueda_impacto":
            await send_options(platform, user_id, "¿Qué tipo de impacto buscas?",
                               [{"title": "Social", "payload": "impact_social"}, {"title": "Ambiental", "payload": "impact_environmental"}],
                               bu_name_lower)
            return True

        # 4. INFORMACIÓN SALARIAL
        elif primary_intent == "calcular_salario":
            from app.chatbot.workflow.common import calcular_salario_chatbot
            response = await calcular_salario_chatbot(platform, user_id, text, bu_name_lower)
            if response:
                cache.set(cache_key, response, timeout=600)
            return True
        elif primary_intent == "consultar_sueldo_mercado":
            chat_state.state = "waiting_for_salary_position"
            await send_message(platform, user_id, "Dime el puesto o área para consultar el sueldo de mercado.", bu_name_lower)
            await sync_to_async(chat_state.save)()
            return True

        # 5. PREPARACIÓN PARA ENTREVISTAS
        elif primary_intent == "solicitar_tips_entrevista":
            await send_options(platform, user_id, "¿Quieres más tips o practicar una entrevista?",
                               [{"title": "Más Tips", "payload": "more_tips"}, {"title": "Practicar", "payload": "practice_interview"}],
                               bu_name_lower)
            return True

        # 6. APOYO GRUPAL Y SOCIAL
        elif primary_intent == "travel_in_group":
            if chatbot:
                await chatbot.handle_group_invitation_input(platform, user_id, text, chat_state, business_unit, user)
            else:
                logger.error("Chatbot instance not provided for travel_in_group intent")
                await send_message(platform, user_id, "Ups, algo salió mal al intentar invitar a alguien.", bu_name_lower)
            return True

        # 7. CONTACTO Y AYUDA
        elif primary_intent in ["contacto", "solicitar_contacto_reclutador"]:
            user = chat_state.person
            admin_phone = configuracion.telefono_bu or "525518490291"
            candidate_info = {
                "Nombre": f"{user.nombre or ''} {user.apellido_paterno or ''} {user.apellido_materno or ''}".strip(),
                "Nacionalidad": user.nacionalidad,
                "Email": user.email,
                "Teléfono": user.phone,
                "Idioma Preferido": user.preferred_language,
                "Estado de Búsqueda": user.job_search_status,
                "Tipos de Empleo": user.desired_job_types,
                "Habilidades": user.skills,
                "Años de Experiencia": user.experience_years,
                "Salario Esperado": user.salary_data.get("expected_salary") if user.salary_data else None,
                "Ubicación Deseada": user.metadata.get("desired_locations") if user.metadata else None,
                "Estatus Migratorio": user.metadata.get("migratory_status") if user.metadata else None,
                "Estado del Perfil": "Completo" if user.is_profile_complete() else "Incompleto"
            }
            if not user.phone and not user.email:
                await send_message(platform, user_id, "Necesitamos tu teléfono o email para contactarte.", bu_name_lower)
                return False
            recap_message = "Candidato requiere asistencia:\n" + "\n".join([f"{k}: {v}" for k, v in candidate_info.items() if v])
            await send_message(platform, admin_phone, recap_message, bu_name_lower)
            await send_message(platform, user_id, "Un reclutador te contactará pronto.", bu_name_lower)
            return True
        elif primary_intent == "ayuda":
            await send_options(platform, user_id, "¿Qué necesitas?",
                               [{"title": "Cómo usar el bot", "payload": "help_usage"}, {"title": "FAQ", "payload": "help_faq"}],
                               bu_name_lower)
            return True
        elif primary_intent == "help_usage":
            await send_message(platform, user_id, "Cómo usar el bot: [instrucciones detalladas].", bu_name_lower)
            return True
        elif primary_intent == "help_faq":
            await send_message(platform, user_id, "Preguntas frecuentes: [lista de FAQs].", bu_name_lower)
            return True
        elif primary_intent == "retry_conversation":
            chat_state.state = "initial"
            chat_state.context = {}
            await sync_to_async(chat_state.save)()
            await send_menu(platform, user_id, business_unit)
            return True

        # 8. INTENTS ESPECÍFICOS POR UNIDAD DE NEGOCIO
        if bu_name_lower == "amigro":
            if primary_intent == "migratory_status":
                from app.chatbot.workflow.amigro import ESTATUS_MIGRATORIO
                await send_message(platform, user_id, "¿Cuál es tu estatus migratorio actual en México?", bu_name_lower)
                await send_options(platform, user_id, "Selecciona una opción:", ESTATUS_MIGRATORIO, bu_name_lower)
                chat_state.state = "waiting_for_migratory_status"
                await sync_to_async(chat_state.save)()
                return True
        elif bu_name_lower == "huntu" and primary_intent == "internship_search":
            chat_state.state = "waiting_for_internship_area"
            await send_message(platform, user_id, "Dime el área de interés (ej. TI, marketing).", bu_name_lower)
            await sync_to_async(chat_state.save)()
            return True
        elif bu_name_lower in ["huntred", "huntred_executive"] and primary_intent == "executive_roles":
            chat_state.state = "waiting_for_role_level"
            await send_message(platform, user_id, "¿Qué nivel buscas? (ej. gerente, director)", bu_name_lower)
            await sync_to_async(chat_state.save)()
            return True
        elif bu_name_lower == "sexsi" and primary_intent == "create_contract":
            chat_state.state = "waiting_for_contract_terms"
            await send_message(platform, user_id, "Describe los términos del contrato.", bu_name_lower)
            await sync_to_async(chat_state.save)()
            return True

        # 9. TRANSICIÓN A UNIDAD SUPERIOR
        elif primary_intent == "transition_to_higher_bu":
            ml_system = MatchmakingLearningSystem(business_unit=bu_name_lower)
            transition_proba = ml_system.predict_transition(chat_state.person)
            if transition_proba > 0.7:  # Umbral ajustable
                possible_transitions = ml_system.get_possible_transitions(bu_name_lower)
                if possible_transitions:
                    message = "¡Felicidades! Tus habilidades y experiencia sugieren que podrías calificar para una unidad superior:\n"
                    options = []
                    for bu in possible_transitions:
                        options.append({"title": bu.capitalize(), "payload": f"move_to_{bu}"})
                    message += "\n".join([f"{i+1}. {opt['title']}" for i, opt in enumerate(options)])
                    message += "\nResponde con el número o 'No' para quedarte en tu unidad actual."
                    await send_message(platform, user_id, message, bu_name_lower)
                    chat_state.state = "offering_division_change"
                    chat_state.context["possible_transitions"] = possible_transitions
                    await sync_to_async(chat_state.save)()
                else:
                    await send_message(platform, user_id, "Actualmente no hay unidades superiores a las que puedas transicionar.", bu_name_lower)
            else:
                await send_message(platform, user_id, "Aún no cumples con los requisitos para transicionar a una unidad superior. Sigue desarrollando tus habilidades.", bu_name_lower)
            return True

        # 10. MANEJO DE RESPUESTAS DE TRANSICIÓN
        elif chat_state.state == "offering_division_change":
            if text.lower() == "no":
                await send_message(platform, user_id, "¡Entendido! Seguirás en tu unidad actual.", bu_name_lower)
                chat_state.state = "idle"
                await sync_to_async(chat_state.save)()
                return True
            try:
                seleccion = int(text) - 1
                possible_transitions = chat_state.context.get("possible_transitions", [])
                if 0 <= seleccion < len(possible_transitions):
                    target_bu_name = possible_transitions[seleccion]
                    new_bu = BusinessUnit.objects.get(name=target_bu_name)
                    persona = chat_state.person
                    persona.business_unit = new_bu
                    await sync_to_async(persona.save)()
                    await send_message(platform, user_id, f"¡Bienvenido a {target_bu_name.capitalize()}! Vamos a actualizar tu perfil.", bu_name_lower)
                    if target_bu_name == "huntu":
                        from app.chatbot.workflow.huntu import continuar_perfil_huntu
                        await continuar_perfil_huntu(plataforma, user_id, new_bu, chat_state, persona)
                    estado_chat.state = "profile_in_progress"
                    await sync_to_async(chat_state.save)()
                else:
                    await send_message(platform, user_id, "Selecciona una opción válida o 'No'.", bu_name_lower)
            except ValueError:
                await send_message(platform, user_id, "Responde con un número válido o 'No'.", bu_name_lower)
            return True

        return False

    except Exception as e:
        logger.error(f"Error en handle_known_intents: {e}", exc_info=True)
        await send_message(platform, user_id, "Ups, algo salió mal y no comprendí exactamente qué necesitabas. ¿Intentamos de nuevo?", bu_name_lower)
        await send_menu(platform, user_id, business_unit)
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