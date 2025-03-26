# /home/pablo/app/chatbot/intents_handler.py
import re
import logging
from typing import List, Dict, Any, Optional
from asgiref.sync import sync_to_async
from app.models import ChatState, Person, BusinessUnit
from app.chatbot.integrations.services import send_message, send_options, send_menu
from django.core.cache import cache
from django.utils import timezone
import random

logger = logging.getLogger(__name__)

# Cache para almacenar respuestas previas (mensaje -> respuesta)
response_cache = {}

# Mantener el diccionario de intents existente
INTENT_PATTERNS = {
    'saludo': [
        "¡Hola! 👋 Bienvenido a Amigro®. Soy tu asistente virtual y estoy aquí para ayudarte a encontrar oportunidades laborales. ¿En qué puedo ayudarte?",
        "¡Hola! 🌟 Me alegra verte por aquí. ¿Qué te gustaría hacer hoy?",
        "¡Bienvenido! 🤝 ¿Cómo puedo ayudarte en tu búsqueda de empleo?"
    ],
    'presentacion_bu': [
        "Bienvenido a Amigro® 🌍 - amigro.org, somos una organización que facilitamos el acceso laboral a mexicanos regresando y migrantes de Latinoamérica ingresando a México, mediante Inteligencia Artificial Conversacional",
        "Por lo que platicaremos un poco de tu trayectoria profesional, tus intereses, tu situación migratoria, etc. Es importante ser lo más preciso posible, ya que con eso podremos identificar las mejores oportunidades para tí, tu familia, y en caso de venir en grupo, favorecerlo."
    ],
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

    for intent, data in INTENT_PATTERNS.items():
        for pattern in data["patterns"]:
            if re.search(pattern, message_lower):
                detected_intents.append(intent)
                break  # Evitar duplicar el mismo intent

    # Ordenar por prioridad (menor número = mayor prioridad)
    detected_intents.sort(key=lambda x: INTENT_PATTERNS[x]["priority"])
    return detected_intents

async def handle_known_intents(intents: List[str], platform: str, user_id: str, chat_state, business_unit, user, text: str) -> bool:
    """Maneja intents conocidos del mensaje."""
    try:
        if not intents:
            return False

        logger.info(f"[handle_known_intents] 🔎 Procesando intents: {intents}")
        
        # Obtener el intent principal
        primary_intent = intents[0]
        
        # Si existe una respuesta para el intent en el diccionario
        if primary_intent in INTENT_PATTERNS:
            # Seleccionar una respuesta aleatoria para el intent
            response = random.choice(INTENT_PATTERNS[primary_intent])
            
            # Enviar la respuesta
            await send_message(platform, user_id, response, business_unit.name)
            
            # Acciones específicas según el intent
            if primary_intent == 'saludo':
                # Después del saludo, mostrar la presentación del business unit
                if 'presentacion_bu' in INTENT_PATTERNS:
                    for msg in INTENT_PATTERNS['presentacion_bu']:
                        await send_message(platform, user_id, msg, business_unit.name)
                
                # Si el usuario no tiene perfil completo, mostrar TOS y menú
                if not getattr(user, 'is_profile_complete', False):
                    tos_url = f"https://{business_unit.name.lower()}.org/tos"
                    await send_message(platform, user_id, f"📜 Por favor, revisa nuestros Términos de Servicio: {tos_url}", business_unit.name)
                    await send_options(platform, user_id, "¿Aceptas nuestros Términos de Servicio?", 
                                     [{"title": "Sí", "payload": "tos_accept"},
                                      {"title": "No", "payload": "tos_reject"}],
                                     business_unit.name)
            
            return True

        return False

    except Exception as e:
        logger.error(f"[handle_known_intents] ❌ Error: {e}", exc_info=True)
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