# /home/pablo/app/com/chatbot/workflow/common/common.py
import logging
import re
from typing import Dict, Any, List, Optional, Tuple, Union
from forex_python.converter import CurrencyRates
from app.ats.chatbot.workflow.common.profile.profile_questions import get_questions
from django.core.files.storage import default_storage
from app.ats.utils.signature.pdf_generator import (
    generate_contract_pdf,
    generate_cv_pdf,
    generate_candidate_summary,
    add_signature,
    merge_signed_documents,
    generate_personality_report
)
from app.ats.utils.cv_generator.cv_generator import CVGenerator
from app.ats.utils.cv_generator.cv_template import CVTemplate
from app.ats.utils.cv_generator.cv_utils import CVUtils
from django.conf import settings
import os
from app.ats.utils.signature.digital_sign import request_digital_signature
from app.ats.utils.salario import (
    calcular_neto, calcular_bruto, calcular_isr_mensual, calcular_cuotas_imss, 
    obtener_tipo_cambio, DATOS_PPA, DATOS_COLI, DATOS_BIGMAC, UMA_DIARIA_2025
)
from app.ats.chatbot.validation import truth_analyzer
# Deferred imports to prevent circular dependencies
def get_send_functions():
    from app.ats.chatbot.integrations.services import send_menu, send_message, send_image, send_options_async, send_smart_options
    return send_menu, send_message, send_image, send_options_async

# Initialize the functions when the module is first imported
send_menu, send_message, send_image, send_options_async = get_send_functions()
from app.models import BusinessUnit, ConfiguracionBU, Person, ChatState, DivisionTransition
from django.conf import settings
from urllib.parse import urlparse
from asgiref.sync import sync_to_async
from app.ats.chatbot.workflow.assessments.personality import get_questions_personality, get_random_tipi_questions
from app.ats.chatbot.workflow.assessments.personality.personality_workflow import PersonalityAssessment
from app.ats.ml.core.utils import BUSINESS_UNIT_HIERARCHY


logger = logging.getLogger(__name__)

def get_workflow_context(user: Person, business_unit: BusinessUnit, channel: str) -> Dict[str, Any]:
    """Obtiene el contexto necesario para el flujo de trabajo.
    
    Args:
        user: Instancia del modelo Person.
        business_unit: Unidad de negocio actual.
        channel: Canal de comunicación (e.g., 'whatsapp').
        
    Returns:
        Diccionario con el contexto del flujo.
    """
    return {
        'user_id': user.id,
        'business_unit': {
            'id': business_unit.id,
            'name': business_unit.name,
            'type': business_unit.type
        },
        'channel': channel,
        'timestamp': timezone.now().isoformat()
    }

# =========================================================
# Creación y Actualización de Perfil
# =========================================================
async def iniciar_creacion_perfil(plataforma: str, user_id: str, unidad_negocio: BusinessUnit, estado_chat: ChatState, persona: Person):
    """Inicia el proceso de creación de perfil, ofreciendo opciones según la unidad de negocio.

    Args:
        plataforma: Plataforma de comunicación (e.g., 'whatsapp').
        user_id: ID del usuario en la plataforma.
        unidad_negocio: Instancia de BusinessUnit.
        estado_chat: Estado actual del chat.
        persona: Instancia del modelo Person.
    """
    if not isinstance(unidad_negocio, BusinessUnit):
        logger.error(f"Unidad de negocio inválida para user_id={user_id}")
        await send_message(plataforma, user_id, "Error: Unidad de negocio no válida. Intenta de nuevo.", "default")
        return
    
    bu_name = unidad_negocio.name.lower().replace('®', '').strip()
    explicaciones = obtener_explicaciones_metodos(bu_name)
    
    opciones = [
        {"id": "dynamic", "title": "1. Dinámico", "description": explicaciones["dynamic"]},
        {"id": "template", "title": "2. Template", "description": explicaciones["template"] + " (solo WhatsApp)"},
        {"id": "cv", "title": "3. CV", "description": explicaciones["cv"]}
    ]
    if bu_name in ["huntred", "huntred_executive", "huntu"]:
        opciones.append({"id": "linkedin", "title": "4. LinkedIn", "description": "Vincula tu perfil de LinkedIn."})

    mensaje = "¡Vamos a crear tu perfil! 📝\nElige cómo prefieres hacerlo:\n" + "\n".join([f"{opt['title']}: {opt['description']}" for opt in opciones])
    if plataforma == "whatsapp":
        payload = {
            "messaging_product": "whatsapp",
            "to": user_id,
            "type": "interactive",
            "interactive": {
                "type": "list",
                "header": {"type": "text", "text": "Crear Perfil"},
                "body": {"text": mensaje},
                "action": {
                    "button": "Seleccionar",
                    "sections": [{"title": "Métodos", "rows": [{"id": opt["id"], "title": opt["title"]} for opt in opciones]}]
                }
            }
        }
        await send_whatsapp_message(payload, bu_name)
    else:
        await send_message(plataforma, user_id, mensaje, bu_name)
        await send_options_async(plataforma, user_id, "Selecciona una opción (ej. 1, 2, 3):",
                           [{"title": opt["title"], "payload": opt["id"]} for opt in opciones], bu_name)
    
    estado_chat.state = "selecting_profile_method"
    estado_chat.context = estado_chat.context or {}
    estado_chat.context['profile_creation_method'] = None
    await sync_to_async(estado_chat.save)()
    logger.info(f"[iniciar_creacion_perfil] Opciones ofrecidas a {user_id} para {bu_name}")

async def iniciar_actualizacion_perfil(plataforma: str, user_id: str, unidad_negocio: BusinessUnit, estado_chat: ChatState, persona: Person):
    """Inicia el proceso de actualización de perfil."""
    bu_name = unidad_negocio.name.lower().replace('®', '').strip()
    
    if not persona.is_profile_complete():
        await send_message(plataforma, user_id, "Tu perfil no está completo. Te recomendamos completar primero la creación de perfil.", bu_name)
        await iniciar_creacion_perfil(plataforma, user_id, unidad_negocio, estado_chat, persona)
        return
    
    campos = ["nombre", "apellido paterno", "apellido materno", "email", "teléfono", "habilidades", "experiencia", "educación", "certificaciones", "estatus migratorio"]
    mensaje = f"¿Qué quieres actualizar? Elige un campo:\n" + "\n".join([f"- {c}" for c in campos])
    await send_message(plataforma, user_id, mensaje, bu_name)
    estado_chat.state = "updating_profile"
    await sync_to_async(estado_chat.save)()
    logger.info(f"[iniciar_actualizacion_perfil] Solicitando campo a actualizar para {user_id}")
  
async def iniciar_perfil_conversacional(plataforma: str, user_id: str, unidad_negocio: BusinessUnit, estado_chat: ChatState, persona: Person):
    """Inicia el flujo conversacional usando profile_questions.py."""
    bu_name = unidad_negocio.name.lower().replace('®', '').strip()
    questions = get_questions(bu_name)
    
    # Buscar el primer campo faltante
    for field, question_data in questions.items():
        if question_data.get("subfield"):
            if not persona.metadata.get(question_data["subfield"]):
                break
        elif not getattr(persona, question_data["field"], None):
            break
    else:
        await finalizar_creacion_perfil(plataforma, user_id, unidad_negocio, estado_chat, persona)
        return
    
    estado_chat.state = f"profile_creation_{field}"
    estado_chat.context['profile_creation'] = estado_chat.context.get('profile_creation', {})
    await sync_to_async(estado_chat.save)()
    
    question = question_data["question"].format(**estado_chat.context.get('profile_creation', {}))
    
    if plataforma == "whatsapp":
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": user_id,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {"text": question},
                "action": {
                    "buttons": [
                        {"type": "reply", "reply": {"id": "skip_field", "title": "Omitir"}},
                        {"type": "reply", "reply": {"id": "upload_cv", "title": "Cargar CV"}},
                        {"type": "reply", "reply": {"id": "back_to_menu", "title": "Volver al Menú"}}
                    ]
                }
            }
        }
        await send_whatsapp_message(payload, bu_name)
    else:
        await send_message(plataforma, user_id, question, bu_name)
        await send_options_async(plataforma, user_id, "Opciones:",
                           [{"title": "Omitir", "payload": "skip_field"},
                            {"title": "Cargar CV", "payload": "upload_cv"},
                            {"title": "Volver al Menú", "payload": "back_to_menu"}],
                           bu_name)
    logger.info(f"[iniciar_perfil_conversacional] Solicitando {field} para {user_id}")

async def finalizar_creacion_perfil(plataforma: str, user_id: str, unidad_negocio: BusinessUnit, estado_chat: ChatState, persona: Person):
    """Finaliza el proceso de creación de perfil y ofrece pruebas o transiciones."""
    bu_name = unidad_negocio.name.lower().replace('®', '').strip()
    
    if persona.is_profile_complete():
        # Generar CV automáticamente
        try:
            # Crear directorio para los documentos si no existe
            user_doc_dir = os.path.join(settings.MEDIA_ROOT, 'cv', str(persona.id))
            os.makedirs(user_doc_dir, exist_ok=True)
            
            # Generar CV básico
            cv_filename = f"cv_{persona.id}.pdf"
            cv_path = os.path.join(user_doc_dir, cv_filename)
            
            # Inicializar generador de CV con configuración para incluir plan de desarrollo
            cv_generator = CVGenerator(include_growth_plan=False)
            
            # Generar sólo el CV inicialmente
            cv_generator.save_cv(persona, cv_path, language='es')
            
            # Notificar al usuario
            await send_message(plataforma, user_id, "¡Perfil completo! 🎉 He generado automáticamente tu CV profesional.", bu_name)
            
            # Guardar la referencia al CV en el contexto del chat
            estado_chat.context["generated_cv_path"] = cv_path
            await sync_to_async(estado_chat.save)()
            
            # Si el usuario tiene test de personalidad completo, generar también el plan de desarrollo
            if hasattr(persona, 'personality_test') and persona.personality_test and getattr(settings, 'ENABLE_ML_FEATURES', False):
                try:
                    # Generar CV con plan de desarrollo incluido
                    cv_plan_filename = f"cv_plan_{persona.id}.pdf"
                    cv_plan_path = os.path.join(user_doc_dir, cv_plan_filename)
                    
                    # Crear un nuevo generador con plan de desarrollo habilitado
                    plan_generator = CVGenerator(include_growth_plan=True)
                    
                    # Generar CV con plan incorporado
                    final_path = plan_generator.save_cv(persona, cv_plan_path, language='es')
                    
                    # Guardar la referencia al CV con plan en el contexto del chat
                    estado_chat.context["generated_cv_plan_path"] = final_path
                    await sync_to_async(estado_chat.save)()
                    
                    # Notificar al usuario sobre el documento mejorado
                    await send_message(plataforma, user_id, "¡Además, basado en tus resultados de personalidad, he creado un Plan de Desarrollo Profesional personalizado! 📈 Lo encontrarás adjunto a tu CV.", bu_name)
                except Exception as e:
                    logger.error(f"Error generando plan de desarrollo para {persona.id}: {str(e)}")
        except Exception as e:
            logger.error(f"Error generando CV para {persona.id}: {str(e)}")
        
        # Evaluar transición a BU superior
        target_bu = await evaluar_transicion(persona, unidad_negocio)
        if target_bu:
            await send_message(plataforma, user_id, f"¡Felicidades! Puedes transicionar a {target_bu.capitalize()}. ¿Quieres hacerlo?", bu_name)
            estado_chat.state = "offering_division_change"
            estado_chat.context["possible_transitions"] = [target_bu]
            await sync_to_async(estado_chat.save)()
        else:
            # Ofrecer prueba de personalidad si no la ha realizado
            if not hasattr(persona, 'personality_test') or not persona.personality_test:
                await ofrecer_prueba_personalidad(plataforma, user_id, unidad_negocio, estado_chat, persona)
            else:
                # Si ya tiene prueba de personalidad, ofrecer otros servicios
                await send_message(plataforma, user_id, "¿En qué más puedo ayudarte hoy?", bu_name)
                await send_menu(plataforma, user_id, bu_name)
    else:
        missing_fields = [f for f in ["nombre", "apellido_paterno", "email", "phone", "skills"] if not getattr(persona, f)]
        await send_message(plataforma, user_id, f"Faltan datos: {', '.join(missing_fields)}. Por favor, complétalos.", bu_name)
        estado_chat.state = f"profile_creation_{missing_fields[0]}"
        await sync_to_async(estado_chat.save)()
        question = get_questions(bu_name)[missing_fields[0]]["question"].format(**estado_chat.context.get('profile_creation', {}))
        if plataforma == "whatsapp":
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": user_id,
                "type": "interactive",
                "interactive": {
                    "type": "button",
                    "body": {"text": question},
                    "action": {
                        "buttons": [
                            {"type": "reply", "reply": {"id": "skip_field", "title": "Omitir"}},
                            {"type": "reply", "reply": {"id": "upload_cv", "title": "Cargar CV"}}
                        ]
                    }
                }
            }
            await send_whatsapp_message(payload, bu_name)
        else:
            await send_message(plataforma, user_id, question, bu_name)
            await send_options_async(plataforma, user_id, "Opciones:",
                               [{"title": "Omitir", "payload": "skip_field"}, {"title": "Cargar CV", "payload": "upload_cv"}],
                               bu_name)
    
    logger.info(f"[finalizar_creacion_perfil] Perfil {'completo' if persona.is_profile_complete() else 'incompleto'} para {user_id}")

async def continuar_registro(plataforma: str, user_id: str, unidad_negocio: BusinessUnit, estado_chat: ChatState, persona: Person):
    """Determina y ejecuta el siguiente paso en el proceso de registro."""
    bu_name = unidad_negocio.name.lower()
    
    # Verificar qué información falta
    campos_faltantes = []
    
    if not persona.email:
        campos_faltantes.append("email")
    if not persona.phone:
        campos_faltantes.append("phone")
    if not persona.name:
        campos_faltantes.append("name")
    
    if campos_faltantes:
        # Selecciona el primer campo faltante
        next_field = campos_faltantes[0]
        estado_chat.state = f"waiting_for_{next_field}"
        
        # Guarda el campo siguiente si hay más de uno
        if len(campos_faltantes) > 1:
            estado_chat.context['next_field'] = f"waiting_for_{campos_faltantes[1]}"
        else:
            estado_chat.context['next_field'] = "profile_completed"
        
        await sync_to_async(estado_chat.save)()
        
        # Solicita el siguiente campo
        messages = {
            "name": "Por favor, ingresa tu nombre completo (nombre y apellido).",
            "email": "Por favor, ingresa tu dirección de correo electrónico.",
            "phone": "Por favor, ingresa tu número de teléfono con formato internacional (ej: +521234567890)."
        }
        
        await send_message(plataforma, user_id, messages[next_field], bu_name)
        return True
    
    # Si ya están todos los campos básicos, ofrecer prueba de personalidad
    await send_message(plataforma, user_id, "¡Perfil básico completado! 🎉", bu_name)
    estado_chat.state = "offering_personality_test"
    await sync_to_async(estado_chat.save)()
    await ofrecer_prueba_personalidad(plataforma, user_id, unidad_negocio, estado_chat, persona)
    return True
  
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

async def send_welcome_message(user_id: str, platform: str, business_unit: BusinessUnit) -> str:
    """Envía un mensaje de bienvenida, el logo de la unidad y el menú de servicios."""
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
    await send_message(platform, user_id, welcome_message, business_unit.name.lower())

    # Enviar logo de la unidad de negocio
    await send_image(platform, user_id, "Aquí tienes nuestro logo 📌", logo_url, business_unit.name.lower())

    # Enviar menú de servicios
    await send_menu(platform, user_id, business_unit.name.lower())

    return "Mensaje de bienvenida enviado correctamente."
# Manejo de Respuestas
# =========================================================
async def manejar_respuesta_perfil(plataforma: str, user_id: str, texto: str, unidad_negocio: BusinessUnit, estado_chat: ChatState, persona: Person, gpt_handler=None):
    """Maneja la respuesta del usuario en el flujo de creación o actualización de perfil.

    Args:
        plataforma: Plataforma de comunicación.
        user_id: ID del usuario en la plataforma.
        texto: Texto de la respuesta del usuario.
        unidad_negocio: Unidad de negocio actual.
        estado_chat: Estado actual del chat.
        persona: Instancia del modelo Person.
        gpt_handler: Manejador para procesar con GPT.
    """

    async def handle_selecting_method():
        if texto.lower() in ['1', 'dinámico', 'dinamico']:
            await iniciar_perfil_conversacional(plataforma, user_id, unidad_negocio, estado_chat, persona)
            return True
        
        elif texto.lower() in ['2', 'template']:
            if plataforma.lower() != 'whatsapp':
                await send_message(plataforma, user_id, "Lo siento, el método de plantilla solo está disponible para WhatsApp. Por favor, elige otro método.", bu_name)
                return False
            # Implementación pendiente - plantilla de WhatsApp
            estado_chat.state = "template_method"
            await sync_to_async(estado_chat.save)()
            await send_message(plataforma, user_id, "Ahora te guiaré a través de una serie de campos para completar tu perfil. Para cada campo, te mostraré el valor actual (si existe) y podrás actualizarlo.", bu_name)
            await continuar_registro(plataforma, user_id, unidad_negocio, estado_chat, persona)
            return True
        
        elif texto.lower() in ['3', 'cv']:
            estado_chat.state = "waiting_for_cv"
            await sync_to_async(estado_chat.save)()
            await send_message(plataforma, user_id, "Excelente. Por favor, envía tu CV como un archivo PDF o Word. Extraeré la información relevante automáticamente.", bu_name)
            return True
        
        elif texto.lower() in ['4', 'linkedin'] and bu_name in ["huntred", "huntred_executive", "huntu"]:
            estado_chat.state = "waiting_for_linkedin"
            await sync_to_async(estado_chat.save)()
            await send_message(plataforma, user_id, "Perfecto. Por favor, comparte el enlace a tu perfil de LinkedIn para que pueda extraer tu información profesional.", bu_name)
            return True
            
        else:
            await send_message(plataforma, user_id, "No entendí tu elección. Por favor, selecciona una opción válida (1-4).", bu_name)
            return False
    
    async def handle_profile_creation():
        current_field = estado_chat.state.replace("profile_creation_", "")
        question_data = questions.get(current_field)
        
        if not question_data:
            logger.error(f"[manejar_respuesta_perfil] Campo desconocido: {current_field}")
            estado_chat.state = "initial"
            await sync_to_async(estado_chat.save)()
            await send_menu(plataforma, user_id, unidad_negocio)
            return False
        
        if texto.lower() == "skip_field" and question_data["validation"](("")):
            next_field = question_data["next"]
            if next_field:
                estado_chat.state = f"profile_creation_{next_field}"
                next_question = questions[next_field]["question"].format(**estado_chat.context.get('profile_creation', {}))
                await send_message(plataforma, user_id, next_question, bu_name)
                await send_options_async(plataforma, user_id, "Opciones:",
                                   [{"title": "Omitir", "payload": "skip_field"},
                                    {"title": "Cargar CV", "payload": "upload_cv"},
                                    {"title": "Volver al Menú", "payload": "back_to_menu"}],
                                   bu_name)
            else:
                await finalizar_creacion_perfil(plataforma, user_id, unidad_negocio, estado_chat, persona)
            await sync_to_async(estado_chat.save)()
            return True
        
        if texto.lower() == "upload_cv":
            estado_chat.state = "waiting_for_cv"
            await send_message(plataforma, user_id, "Por favor, envía tu CV como archivo adjunto (PDF o Word).", bu_name)
            await sync_to_async(estado_chat.save)()
            return True
        
        if not question_data["validation"](texto):
            await send_message(plataforma, user_id, f"Respuesta no válida para {current_field}. Ejemplo: {question_data['question'].split('Ejemplo: ')[-1] if 'Ejemplo: ' in question_data['question'] else 'Formato correcto'}", bu_name)
            return True
        
        if "transform" in question_data:
            value = question_data["transform"](texto)
        else:
            value = texto
        
        if question_data.get("subfield"):
            persona.metadata = persona.metadata or {}
            persona.metadata[question_data["subfield"]] = value
        else:
            setattr(persona, question_data["field"], value)
        
        estado_chat.context['profile_creation'][current_field] = texto
        await sync_to_async(persona.save)()
        
        next_field = question_data["next"]
        if next_field:
            estado_chat.state = f"profile_creation_{next_field}"
            next_question = questions[next_field]["question"].format(**estado_chat.context.get('profile_creation', {}))
            if plataforma == "whatsapp":
                payload = {
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": user_id,
                    "type": "interactive",
                    "interactive": {
                        "type": "button",
                        "body": {"text": next_question},
                        "action": {
                            "buttons": [
                                {"type": "reply", "reply": {"id": "skip_field", "title": "Omitir"}},
                                {"type": "reply", "reply": {"id": "upload_cv", "title": "Cargar CV"}},
                                {"type": "reply", "reply": {"id": "back_to_menu", "title": "Volver al Menú"}}
                            ]
                        }
                    }
                }
                await send_whatsapp_message(payload, bu_name)
            else:
                await send_message(plataforma, user_id, next_question, bu_name)
                await send_options_async(plataforma, user_id, "Opciones:",
                                   [{"title": "Omitir", "payload": "skip_field"},
                                    {"title": "Cargar CV", "payload": "upload_cv"},
                                    {"title": "Volver al Menú", "payload": "back_to_menu"}],
                                   bu_name)
        else:
            await finalizar_creacion_perfil(plataforma, user_id, unidad_negocio, estado_chat, persona)
        
        await sync_to_async(estado_chat.save)()
        return True
    
    async def handle_cv_upload():
        parser = CVParser(unidad_negocio)
        try:
            from pathlib import Path
            file_path = Path(texto)
            cv_text = parser.extract_text_from_file(file_path)
            if cv_text:
                parsed_data = parser.parse(cv_text)
                if parsed_data:
                    for key, value in parsed_data.items():
                        if key in ["email", "phone"] and value:
                            if key == "email" and re.match(r"[^@]+@[^@]+\.[^@]+", value):
                                setattr(persona, key, value)
                            elif key == "phone":
                                try:
                                    parsed_phone = phonenumbers.parse(value, "MX")
                                    if phonenumbers.is_valid_number(parsed_phone):
                                        formatted_phone = phonenumbers.format_number(parsed_phone, phonenumbers.PhoneNumberFormat.E164)
                                        setattr(persona, key, formatted_phone)
                                except:
                                    logger.warning(f"Teléfono inválido en CV para {user_id}: {value}")
                        elif key == "skills":
                            persona.skills = ", ".join(value) if isinstance(value, list) else value
                        elif key == "experience":
                            persona.metadata["experience"] = value
                        elif key == "education":
                            persona.metadata["education"] = value
                    persona.cv_file = str(file_path)
                    persona.cv_parsed = True
                    persona.cv_analysis = parsed_data
                    persona.metadata["last_cv_update"] = now().isoformat()
                    await sync_to_async(persona.save)()
                    await send_message(plataforma, user_id, "Tu CV ha sido procesado y tu perfil actualizado.", bu_name)
                    await finalizar_creacion_perfil(plataforma, user_id, unidad_negocio, estado_chat, persona)
                else:
                    await send_message(plataforma, user_id, "No se pudo extraer información de tu CV. Intenta con otro método.", bu_name)
                    estado_chat.state = "selecting_profile_method"
                    await sync_to_async(estado_chat.save)()
            else:
                await send_message(plataforma, user_id, "No se pudo leer tu CV. Asegúrate de enviar un PDF o Word válido.", bu_name)
        except Exception as e:
            logger.error(f"Error procesando CV para {user_id}: {str(e)}", exc_info=True)
            await send_message(plataforma, user_id, "Error procesando tu CV. Intenta con otro archivo (PDF o Word).", bu_name)
            estado_chat.state = "selecting_profile_method"
            await sync_to_async(estado_chat.save)()
        return True
    
    async def handle_linkedin():
        linkedin_url = texto
        if not re.match(r"^https?://([a-z]{2,3}\.)?linkedin\.com/.*", linkedin_url, re.IGNORECASE):
            logger.warning(f"Invalid LinkedIn URL para {user_id}: {linkedin_url}")
            await send_message(plataforma, user_id, "Por favor, proporciona una URL válida de LinkedIn (ej: https://linkedin.com/in/tu-perfil).", bu_name)
            return True
        
        try:
            scraped_data = await scrape_linkedin_profile(linkedin_url, bu_name)
            if scraped_data:
                if "email" in scraped_data and scraped_data["email"]:
                    if re.match(r"[^@]+@[^@]+\.[^@]+", scraped_data["email"]):
                        persona.email = scraped_data["email"]
                if "phone" in scraped_data and scraped_data["phone"]:
                    try:
                        parsed_phone = phonenumbers.parse(scraped_data["phone"], "MX")
                        if phonenumbers.is_valid_number(parsed_phone):
                            persona.phone = phonenumbers.format_number(parsed_phone, phonenumbers.PhoneNumberFormat.E164)
                    except:
                        logger.warning(f"Teléfono inválido en LinkedIn para {user_id}: {scraped_data['phone']}")
                update_person_from_scrape(persona, scraped_data)
                persona.metadata["linkedin_url"] = linkedin_url
                await sync_to_async(persona.save)()
                await send_message(plataforma, user_id, "Tu perfil de LinkedIn ha sido procesado y tu perfil actualizado.", bu_name)
                await finalizar_creacion_perfil(plataforma, user_id, unidad_negocio, estado_chat, persona)
            else:
                await send_message(plataforma, user_id, "No se pudo procesar tu perfil de LinkedIn. Intenta con otro método.", bu_name)
                estado_chat.state = "selecting_profile_method"
                await sync_to_async(estado_chat.save)()
        except Exception as e:
            logger.error(f"Error procesando LinkedIn para {user_id}: {str(e)}", exc_info=True)
            await send_message(plataforma, user_id, "Error procesando LinkedIn. Verifica la URL e intenta de nuevo.", bu_name)
            estado_chat.state = "selecting_profile_method"
            await sync_to_async(estado_chat.save)()
        return True
    
    async def handle_updating_profile():
        fields_map = {
            "nombre": "nombre",
            "apellido paterno": "apellido_paterno",
            "apellido materno": "apellido_materno",
            "email": "email",
            "teléfono": "phone",
            "habilidades": "skills",
            "experiencia": "metadata.experience",
            "educación": "metadata.education",
            "certificaciones": "metadata.certifications",
            "estatus migratorio": "metadata.migratory_status"
        }
        field = next((k for k, v in fields_map.items() if k in texto.lower()), None)
        if not field:
            await send_message(plataforma, user_id, "Por favor, especifica qué campo quieres actualizar (ej: nombre, email, habilidades).", bu_name)
            return True
        
        estado_chat.state = f"waiting_for_{fields_map[field].split('.')[0]}"
        estado_chat.context['update_field'] = fields_map[field]
        await sync_to_async(estado_chat.save)()
        await send_message(plataforma, user_id, f"Por favor, ingresa tu nuevo {field}.", bu_name)
        return True
    
    async def handle_validation():
        field = estado_chat.state.replace("waiting_for_", "")
        update_field = estado_chat.context.get('update_field', field)
        
        if update_field.startswith("metadata."):
            subfield = update_field.split(".")[1]
            question_data = next((q for q in questions.values() if q.get("subfield") == subfield), None)
        else:
            question_data = questions.get(field)
        
        if not question_data:
            await send_message(plataforma, user_id, "Campo no válido. Intenta de nuevo.", bu_name)
            estado_chat.state = "updating_profile"
            await sync_to_async(estado_chat.save)()
            return True
        
        if not question_data["validation"](texto):
            await send_message(plataforma, user_id, f"Respuesta no válida para {field}. Ejemplo: {question_data['question'].split('Ejemplo: ')[-1] if 'Ejemplo: ' in question_data['question'] else 'Formato correcto'}", bu_name)
            return True
        
        if "transform" in question_data:
            value = question_data["transform"](texto)
        else:
            value = texto
        
        if update_field.startswith("metadata."):
            persona.metadata = persona.metadata or {}
            persona.metadata[update_field.split(".")[1]] = value
        else:
            setattr(persona, update_field, value)
        
        await sync_to_async(persona.save)()
        await send_message(plataforma, user_id, f"¡{field.capitalize()} actualizado correctamente!", bu_name)
        estado_chat.state = "updating_profile"
        await sync_to_async(estado_chat.save)()
        return True
    
    # Dispatch según el estado
    if estado_chat.state == "selecting_profile_method":
        return await handle_selecting_method()
    elif estado_chat.state.startswith("profile_creation_"):
        return await handle_profile_creation()
    elif estado_chat.state == "waiting_for_cv":
        return await handle_cv_upload()
    elif estado_chat.state == "waiting_for_linkedin":
        return await handle_linkedin()
    elif estado_chat.state == "updating_profile":
        return await handle_updating_profile()
    elif estado_chat.state.startswith("waiting_for_"):
        return await handle_validation()
    
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
        from app.ats.chatbot.workflow.amigro import continuar_perfil_amigro
        await continuar_perfil_amigro(plataforma, user_id, unidad_negocio, estado_chat, persona)
    elif bu_name == "huntu":
        from app.ats.chatbot.workflow.huntu import continuar_perfil_huntu
        await continuar_perfil_huntu(plataforma, user_id, unidad_negocio, estado_chat, persona)
    else:
        await iniciar_perfil_conversacional(plataforma, user_id, unidad_negocio, estado_chat, persona)

async def manejar_respuesta_prueba(plataforma: str, user_id: str, texto: str, unidad_negocio: BusinessUnit, estado_chat: ChatState, persona: Person):
    """Procesa las respuestas del usuario durante una prueba."""
    test_type = estado_chat.context.get('test_type')
    if not test_type or estado_chat.state != f'taking_{test_type}':
        return False

    domain = estado_chat.context['domain']
    questions = get_questions_personality(test_type, domain)
    if test_type == 'TIPI':
        questions = get_random_tipi_questions(domain)
    step = estado_chat.context['current_step']
    step_key = estado_chat.context.get('current_step_key')

    # Validar respuesta
    valid_range = range(1, 6) if test_type in ['huntBigFive', '16PF', 'NEO'] else range(1, 8) if test_type == 'TIPI' else None
    options = ['a', 'b', 'c', 'd'] if test_type == 'DISC' else None
    try:
        respuesta = texto.lower() if test_type == 'DISC' else int(texto)
        if (valid_range and respuesta not in valid_range) or (options and respuesta not in options):
            await send_message(plataforma, user_id, f'Por favor, responde con una opción válida.', unidad_negocio.name.lower())
            return True
    except ValueError:
        await send_message(plataforma, user_id, f'Por favor, responde con una opción válida.', unidad_negocio.name.lower())
        return True

    # Guardar respuesta y avanzar
    if test_type in ['huntBigFive', '16PF', 'NEO']:
        if step_key not in estado_chat.context['answers']:
            estado_chat.context['answers'][step_key] = []
        estado_chat.context['answers'][step_key].append(respuesta)
    else:
        estado_chat.context['answers'][step] = respuesta

    estado_chat.context['current_step'] += 1
    if test_type in ['huntBigFive', '16PF', 'NEO']:
        trait_questions = questions[step_key]
        if estado_chat.context['current_step'] < len(trait_questions):
            await enviar_pregunta(plataforma, user_id, test_type, domain, estado_chat, unidad_negocio)
        else:
            traits = list(questions.keys())
            current_idx = traits.index(step_key)
            if current_idx + 1 < len(traits):
                estado_chat.context['current_step'] = 0
                estado_chat.context['current_step_key'] = traits[current_idx + 1]
                await enviar_pregunta(plataforma, user_id, test_type, domain, estado_chat, unidad_negocio)
            else:
                await finalizar_prueba(plataforma, user_id, test_type, estado_chat, persona, unidad_negocio)
    else:
        if estado_chat.context['current_step'] < (len(questions) if test_type == 'DISC' else len(questions) * 2):
            await enviar_pregunta(plataforma, user_id, test_type, domain, estado_chat, unidad_negocio)
        else:
            await finalizar_prueba(plataforma, user_id, test_type, estado_chat, persona, unidad_negocio)
    await sync_to_async(estado_chat.save)()
    return True

# =========================================================
# Test de Personalidad
# =========================================================
async def ofrecer_prueba_personalidad(plataforma: str, user_id: str, unidad_negocio: BusinessUnit, estado_chat: ChatState, persona: Person, mensaje_base: str = ""):
    """Ofrece una prueba de personalidad al usuario."""
    bu_name = unidad_negocio.name.lower().replace('®', '').strip()
    pruebas = PRUEBAS_POR_UNIDAD.get(bu_name, [])
    
    if not pruebas:
        mensaje = "¡No hay pruebas de personalidad disponibles para esta unidad! Puedes explorar otras opciones desde el menú."
        estado_chat.state = "idle"
        await send_message(plataforma, user_id, mensaje, bu_name)
        await send_menu(plataforma, user_id, unidad_negocio)
        await sync_to_async(estado_chat.save)()
        return
    
    mensaje = mensaje_base + f"🧠 Mejora tu perfil con una prueba de personalidad para {bu_name}:\n" + "\n".join(
        [f"{i+1}. {p['nombre']} - {p['descripcion']}" for i, p in enumerate(pruebas)]
    ) + "\nResponde con el número de la prueba o 'No' para omitir."
    
    if plataforma == "whatsapp":
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": user_id,
            "type": "interactive",
            "interactive": {
                "type": "list",
                "header": {"type": "text", "text": "Pruebas de Personalidad"},
                "body": {"text": mensaje},
                "action": {
                    "button": "Seleccionar",
                    "sections": [
                        {
                            "title": "Pruebas",
                            "rows": [
                                {"id": f"test_{p['nombre'].lower()}", "title": p["nombre"]} for p in pruebas
                            ] + [{"id": "no_test", "title": "No, gracias"}]
                        }
                    ]
                }
            }
        }
        await send_whatsapp_message(payload, bu_name)
    else:
        await send_message(plataforma, user_id, mensaje, bu_name)
        await send_options_async(plataforma, user_id, "Selecciona una opción:",
                           [{"title": p["nombre"], "payload": f"test_{p['nombre'].lower()}"} for p in pruebas] +
                           [{"title": "No, gracias", "payload": "no_test"}],
                           bu_name)
    
    estado_chat.state = "offering_personality_test"
    await sync_to_async(estado_chat.save)()
    logger.info(f"[ofrecer_prueba_personalidad] Ofreciendo pruebas para {user_id}")

async def iniciar_prueba_personalidad(plataforma: str, user_id: str, unidad_negocio: BusinessUnit, estado_chat: ChatState, persona: Person, test_type: str):
    """Inicia una prueba de personalidad con un timeout de 5 segundos."""
    try:
        async with asyncio.timeout(5):
            domain = get_business_unit_domain(unidad_negocio)
            await iniciar_prueba(plataforma, user_id, test_type, domain, unidad_negocio, estado_chat, persona)
    except asyncio.TimeoutError:
        logger.error(f"Timeout al iniciar prueba {test_type} para user_id={user_id}")
        await send_message(plataforma, user_id, "Lo siento, tardé demasiado en iniciar la prueba. Intenta de nuevo.", unidad_negocio.name.lower())

async def iniciar_prueba(plataforma: str, user_id: str, test_type: str, domain: str, unidad_negocio: BusinessUnit, estado_chat: ChatState, persona: Person):
    """Configura el estado para comenzar una prueba de personalidad."""
    questions = get_questions_personality(test_type, domain)
    if not questions:
        await send_message(plataforma, user_id, "Error: No hay preguntas disponibles para esta prueba.", unidad_negocio.name.lower())
        estado_chat.state = "idle"
        await sync_to_async(estado_chat.save)()
        return
    estado_chat.state = f'taking_{test_type}'
    estado_chat.context['test_type'] = test_type
    estado_chat.context['domain'] = domain
    estado_chat.context['current_step'] = 0
    estado_chat.context['answers'] = {}
    await sync_to_async(estado_chat.save)()

    if test_type == 'TIPI':
        questions = get_random_tipi_questions(domain)
    first_step = list(questions.keys())[0] if test_type in ['huntBigFive', '16PF', 'NEO'] else None
    estado_chat.context['current_step_key'] = first_step

    await enviar_pregunta(plataforma, user_id, test_type, domain, estado_chat, unidad_negocio)

async def enviar_pregunta(plataforma: str, user_id: str, test_type: str, domain: str, estado_chat: ChatState, unidad_negocio: BusinessUnit):
    """Envía la siguiente pregunta de la prueba al usuario."""
    questions = get_questions_personality(test_type, domain)
    if test_type == 'TIPI':
        questions = get_random_tipi_questions(domain)
    step = estado_chat.context['current_step']
    step_key = estado_chat.context.get('current_step_key')

    if test_type in ['huntBigFive', '16PF', 'NEO']:
        trait_questions = questions[step_key]
        if step < len(trait_questions):
            question = trait_questions[step]['text']
            options = trait_questions[step]['options']
            await send_message(plataforma, user_id, f'{question}\nOpciones: {", ".join(options)}', unidad_negocio.name.lower())
    elif test_type == 'DISC':
        if step < len(questions):
            question = questions[step]['text']
            options = questions[step]['options']
            await send_message(plataforma, user_id, f'{question}\nOpciones: {", ".join(options)}', unidad_negocio.name.lower())
    elif test_type == 'TIPI':
        trait = list(questions.keys())[step // 2]
        q_idx = step % 2
        question = questions[trait][q_idx]['text']
        options = ['1 - Muy en desacuerdo', '2', '3', '4', '5', '6', '7 - Muy de acuerdo']
        await send_message(plataforma, user_id, f'{question}\nOpciones: {", ".join(options)}', unidad_negocio.name.lower())

async def finalizar_prueba(plataforma: str, user_id: str, test_type: str, estado_chat: ChatState, persona: Person, unidad_negocio: BusinessUnit):
    """Finaliza la prueba, calcula resultados y genera un reporte."""
    answers = estado_chat.context.get('answers', {})
    if test_type == 'huntBigFive' or test_type == 'NEO':
        for trait, responses in answers.items():
            score = sum(responses) / len(responses)
            setattr(persona, {'apertura': 'openness', 'conciencia': 'conscientiousness', 'extraversion': 'extraversion', 'amabilidad': 'agreeableness', 'neuroticismo': 'neuroticism'}[trait], score)
    elif test_type == 'DISC':
        d, i, s, c = 0, 0, 0, 0
        for ans in answers.values():
            if ans == 'a': d += 1
            elif ans == 'b': i += 1
            elif ans == 'c': s += 1
            elif ans == 'd': c += 1
        persona.metadata['disc'] = f'D{d}I{i}S{s}C{c}'
    elif test_type == 'TIPI':
        for idx, trait in enumerate(['extraversion', 'agreeableness', 'conscientiousness', 'neuroticism', 'openness']):
            direct = answers[idx * 2]; reverse = 8 - answers[idx * 2 + 1]
            score = (direct + reverse) / 2
            setattr(persona, trait, score)
    await sync_to_async(persona.save)()
    await send_message(plataforma, user_id, f'¡Gracias por completar la prueba {test_type}! Tus resultados han sido guardados.', unidad_negocio.name.lower())

    # Generar y enviar reporte
    report_path = generate_personality_report(persona, unidad_negocio)
    await send_image(plataforma, user_id, "Aquí está tu reporte de personalidad", report_path, unidad_negocio.name)
    
    # Enviar email con reporte adjunto
    email_body = f"Hola {persona.nombre},<br>Has completado la prueba {test_type} con {unidad_negocio.name}. Adjunto tu reporte de personalidad.<br>Saludos,<br>Equipo {unidad_negocio.name}"
    await send_email(
        subject=f"Prueba de Personalidad - {unidad_negocio.name}",
        to_email=persona.email,
        body=email_body,
        business_unit_name=unidad_negocio.name,
        attachments=[report_path]
    )
    import os
    os.remove(report_path)

    # Gamificación
    gamification_service = GamificationService()
    await gamification_service.award_points(persona, f"prueba_{test_type}", points=100)
    
    estado_chat.state = 'idle'
    await sync_to_async(estado_chat.save)()

def obtener_explicaciones_metodos(bu_name: str) -> dict:
    """Devuelve las explicaciones de los métodos según la unidad de negocio."""
    return EXPLICACIONES_METODOS.get(bu_name.lower(), EXPLICACIONES_METODOS["default"])

# =========================================================
# Cálculo del Salario
# =========================================================
async def calcular_salario_chatbot(platform, user_id, mensaje, business_unit_name):
    data = parsear_mensaje(mensaje)
    required_keys = ['moneda', 'tipo', 'frecuencia']
    if not all(key in data for key in required_keys):
        response = "Faltan datos requeridos (moneda, tipo, frecuencia)."
        await send_message(platform, user_id, response, business_unit_name)
        return response
    if 'salario_bruto' not in data and 'salario_neto' not in data:
        response = "Por favor, proporciona un salario válido (ej. 'salario bruto = 20k MXN mensual')."
        await send_message(platform, user_id, response, business_unit_name)
        return response

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
    msg = f"🤔 Con base en el salario: {mensaje}\n\n"
    msg += f"💰 Bruto Mensual : {salario_bruto_orig:>10,.2f} {data['moneda']} ({salario_bruto_mxn:,.2f} MXN)\n"
    msg += f"🏠 Neto Mensual  : {salario_neto_orig:>10,.2f} {data['moneda']} ({salario_neto_mxn:,.2f} MXN)\n"
    msg += "\n"
    msg += "📊 Detalles del cálculo:\n"
    msg += "\n"
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
    msg += "\n"

    # Leyenda si hay valores asumidos en 0
    campos_no_provistos = []
    if not incluye_prestaciones or monto_vales == 0:
        campos_no_provistos.append("Vales")
    if not fondo_ahorro:
        campos_no_provistos.append("Fondo de Ahorro")
    if credito_infonavit == 0:
        campos_no_provistos.append("Infonavit")
    if pension_alimenticia == 0:
        campos_no_provistos.append("Pensión Alimenticia")
    if not aplicar_subsidio or subsidio == 0:
        campos_no_provistos.append("Subsidio al Empleo")

    if campos_no_provistos:
        msg += f"📝 Nota: Basado en los datos provistos, los valores de {', '.join(campos_no_provistos)} se calculan en 0.\n"

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
    coli_part = f"{salario_neto_orig * adjustment_coli_orig:>10,.2f} {data['moneda']}" if data['moneda'] != 'MXN' else ''
    ppa_part = f"{salario_neto_orig * adjustment_ppa_orig:>10,.2f} {data['moneda']}" if data['moneda'] != 'MXN' else ''
    bigmac_part = f"{salario_neto_orig * adjustment_bigmac_orig:>10,.2f} {data['moneda']}" if data['moneda'] != 'MXN' else ''

    msg += "\n🌍 Comparativa Salario Neto:\n"
    msg += "\n"
    msg += f"{'':<15} {'🇲🇽 México':<15} {(f'🌎 {pais_origen}' if data['moneda'] != 'MXN' else ''):<15}\n"
    msg += f"{'-' * 15} {'-' * 15} {'-' * 15 if data['moneda'] != 'MXN' else ''}\n"
    msg += f"📊 COLI         {salario_neto_mxn * adjustment_coli_mx:>10,.2f} MXN {coli_part}\n"
    msg += f"⚖️ PPA          {salario_neto_mxn * adjustment_ppa_mx:>10,.2f} MXN {ppa_part}\n"
    msg += f"🍔 BigMac Index {salario_neto_mxn * adjustment_bigmac_mx:>10,.2f} MXN {bigmac_part}\n"
    msg += "\n"

    # Obtener el dominio desde ConfiguracionBU de manera asíncrona
    try:
        business_unit = await sync_to_async(BusinessUnit.objects.get)(name__iexact=business_unit_name)
        config = await sync_to_async(lambda: business_unit.configuracionbu)()
        domain = urlparse(config.dominio_bu).netloc or urlparse(config.dominio_bu).path
        
        # Asegurarse de que domain sea un string
        if isinstance(domain, bytes):
            domain = domain.decode('utf-8')
        domain = domain.replace('www.', '')
        
        # Resto del código...
    except (BusinessUnit.DoesNotExist, ConfiguracionBU.DoesNotExist, AttributeError) as e:
        logger.error(f"Error al obtener dominio para {business_unit_name}: {e}")
        domain = "huntred.com"

    # Añadir referencia dinámica
    msg += f"\n📚 Referencia: https://{domain}/salario/"

    await send_message(platform, user_id, msg, business_unit_name)
    return msg

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

# =========================================================
# Criterios de Transición de Unidad de Negocio
# =========================================================
async def evaluar_transicion(persona: Person, current_bu: BusinessUnit) -> Optional[str]:
    """Evalúa si el candidato puede transicionar a una unidad superior."""
    ml_system = MatchmakingLearningSystem(business_unit=current_bu.name.lower())
    transition_proba = ml_system.predict_transition(persona)
    if transition_proba > 0.7:
        possible_transitions = ml_system.get_possible_transitions(current_bu.name.lower())
        if possible_transitions:
            return possible_transitions[0]
    return None

async def transfer_candidate_to_new_division(person: Person, new_bu: BusinessUnit, plataforma: str, user_id: str):
    """
    Transfiere al candidato a una nueva unidad de negocio y registra la transición.
    
    Args:
        person: Instancia del modelo Person.
        new_bu: Nueva unidad de negocio.
        plataforma: Plataforma de comunicación (e.g., 'whatsapp').
        user_id: ID del usuario en la plataforma.
    """
    bu_name = new_bu.name.lower()
    is_eligible, details = TransitionCriteriaService.check_transition_eligibility(person, bu_name)
    if not is_eligible:
        await send_message(plataforma, user_id, f"No cumples con los requisitos para transicionar a {bu_name.capitalize()}. Detalles: {details}", bu_name)
        return

    old_bu = person.business_unit
    person.business_unit = new_bu
    await sync_to_async(person.save)()
    DivisionTransition.objects.create(
        person=person,
        from_division=old_bu.name if old_bu else "unknown",
        to_division=new_bu.name,
        success=True
    )
    await send_message(plataforma, user_id, f"¡Bienvenido a {bu_name.capitalize()}! Actualizaremos tu perfil para maximizar tus oportunidades.", bu_name)

    # Redirigir al flujo conversacional correspondiente
    if bu_name == "huntu":
        from app.ats.chatbot.workflow.huntu import continuar_perfil_huntu
        await continuar_perfil_huntu(plataforma, user_id, new_bu, ChatState.objects.get(user=person), person)
    elif bu_name == "amigro":
        from app.ats.chatbot.workflow.amigro import continuar_perfil_amigro
        await continuar_perfil_amigro(plataforma, user_id, new_bu, ChatState.objects.get(user=person), person)
    elif bu_name == "huntred":
        from app.ats.chatbot.workflow.huntred import continuar_perfil_huntred
        await continuar_perfil_huntred(plataforma, user_id, new_bu, ChatState.objects.get(user=person), person)
    elif bu_name == "huntred_executive":
        from app.ats.chatbot.workflow.huntred_executive import continuar_perfil_huntred_executive
        await continuar_perfil_huntred_executive(plataforma, user_id, new_bu, ChatState.objects.get(user=person), person)

class TransitionCriteriaService:
    """Servicio para evaluar y gestionar transiciones entre unidades de negocio."""

    @staticmethod
    def get_current_salary(person: Person) -> float:
        """Obtiene el salario actual de una persona."""
        try:
            return float(person.salary_data.get('current_salary', 0))
        except (ValueError, AttributeError, TypeError):
            return 0.0

    @staticmethod
    def get_skills_count(person: Person) -> int:
        """Cuenta el número total de habilidades de una persona."""
        if not person.skills:
            return 0
        if isinstance(person.skills, str):
            return len([s.strip() for s in person.skills.split(',')])
        elif person.metadata and 'skills' in person.metadata:
            if isinstance(person.metadata['skills'], list):
                return len(person.metadata['skills'])
        return 0

    @staticmethod
    def get_experience_months(person: Person) -> int:
        """Calcula los meses de experiencia de una persona."""
        if person.experience_years:
            return person.experience_years * 12
        if person.experience_data and isinstance(person.experience_data, dict):
            total_months = 0
            for exp in person.experience_data.get('experiences', []):
                total_months += (exp.get('years', 0) * 12) + exp.get('months', 0)
            return total_months
        return 0

    @staticmethod
    def calculate_profile_completeness(person: Person) -> float:
        """Calcula qué tan completo está el perfil de una persona."""
        fields_to_check = ['nombre', 'apellido_paterno', 'email', 'phone', 'skills', 'fecha_nacimiento', 'nationality']
        filled_fields = sum(1 for field in fields_to_check if getattr(person, field, None))
        if person.metadata:
            if person.metadata.get('soft_skills'): filled_fields += 1
            if person.metadata.get('education'): filled_fields += 1
            if person.metadata.get('certifications'): filled_fields += 1
        if person.cv_parsed:
            filled_fields += 1
        total_possible = len(fields_to_check) + 4
        return filled_fields / total_possible

    @classmethod
    def check_transition_eligibility(cls, person: Person, target_bu_name: str, proposed_salary: Optional[float] = None) -> Tuple[bool, Dict[str, Any]]:
        """Verifica si una persona es elegible para transicionar a otra unidad de negocio."""
        current_bu = person.business_unit
        if not current_bu:
            return False, {"error": "No se pudo determinar la unidad de negocio actual"}

        current_bu_name = current_bu.name.lower()
        target_bu_name = target_bu_name.lower()
        transition_key = f"{current_bu_name}_to_{target_bu_name}"

        if transition_key not in DIVISION_TRANSITION_CRITERIA:
            return False, {"error": f"Transición no definida: {transition_key}"}

        criteria = DIVISION_TRANSITION_CRITERIA[transition_key]
        evaluation = {}
        meets_criteria = True

        current_level = BUSINESS_UNIT_HIERARCHY.get(current_bu_name, 0)
        target_level = BUSINESS_UNIT_HIERARCHY.get(target_bu_name, 0)
        if current_level == 0 or target_level == 0:
            return False, {"error": "Unidad de negocio no válida"}

        if target_level > current_level:  # Ascenso
            if "min_skills" in criteria:
                skills_count = cls.get_skills_count(person)
                evaluation["skills"] = {"required": criteria["min_skills"], "actual": skills_count, "passed": skills_count >= criteria["min_skills"]}
                meets_criteria &= evaluation["skills"]["passed"]

            if "min_experience_months" in criteria:
                experience_months = cls.get_experience_months(person)
                evaluation["experience"] = {"required": criteria["min_experience_months"], "actual": experience_months, "passed": experience_months >= criteria["min_experience_months"]}
                meets_criteria &= evaluation["experience"]["passed"]

            if "min_salary_mxn" in criteria:
                current_salary = cls.get_current_salary(person)
                evaluation["min_salary"] = {"required": criteria["min_salary_mxn"], "actual": current_salary, "passed": current_salary >= criteria["min_salary_mxn"]}
                meets_criteria &= evaluation["min_salary"]["passed"]

            if proposed_salary and "min_salary_increase" in criteria:
                current_salary = cls.get_current_salary(person)
                if current_salary > 0:
                    salary_increase = (proposed_salary - current_salary) / current_salary
                    evaluation["salary_increase"] = {"required": criteria["min_salary_increase"], "actual": salary_increase, "passed": salary_increase >= criteria["min_salary_increase"]}
                    meets_criteria &= evaluation["salary_increase"]["passed"]

            if "profile_completeness" in criteria:
                completeness = cls.calculate_profile_completeness(person)
                evaluation["profile_completeness"] = {"required": criteria["profile_completeness"], "actual": completeness, "passed": completeness >= criteria["profile_completeness"]}
                meets_criteria &= evaluation["profile_completeness"]["passed"]

        return meets_criteria, evaluation

    @classmethod
    def execute_transition(cls, person: Person, target_bu_name: str, new_salary: Optional[float] = None, force: bool = False) -> Tuple[bool, str]:
        """Ejecuta la transición a una nueva unidad de negocio."""
        if not force:
            is_eligible, evaluation = cls.check_transition_eligibility(person, target_bu_name, new_salary)
            if not is_eligible:
                return False

def process_business_unit_transition(person_id: int, target_bu_name: str, new_salary: Optional[float] = None, force: bool = False) -> Dict[str, Any]:
    """
    Procesa una transición de unidad de negocio para una persona.
    
    Args:
        person_id: ID de la persona.
        target_bu_name: Nombre de la unidad de negocio objetivo (e.g., 'huntu').
        new_salary: Nuevo salario (opcional).
        force: Forzar la transición (opcional).
        
    Returns:
        Diccionario con resultado y detalles.
    """
    try:
        person = Person.objects.get(id=person_id)
    except Person.DoesNotExist:
        return {'success': False, 'message': f'Persona con ID {person_id} no encontrada'}

    success, message = TransitionCriteriaService.execute_transition(person, target_bu_name, new_salary, force)
    return {
        'success': success,
        'message': message,
        'person_id': person_id,
        'target_bu': target_bu_name,
        'new_salary': new_salary
    }

async def get_possible_transitions(person: Person, current_bu: BusinessUnit) -> List[str]:
    """
    Obtiene las unidades de negocio a las que una persona puede transicionar.
    
    Args:
        person: Instancia del modelo Person.
        current_bu: Unidad de negocio actual.
        
    Returns:
        Lista de nombres de unidades de negocio a las que puede transicionar.
    """
    current_bu_name = current_bu.name.lower()
    possible_keys = [key for key in DIVISION_TRANSITION_CRITERIA.keys() if key.startswith(current_bu_name)]
    qualified_transitions = []

    for key in possible_keys:
        target_bu_name = key.split("_to_")[1]
        is_eligible, _ = TransitionCriteriaService.check_transition_eligibility(person, target_bu_name)
        if is_eligible:
            qualified_transitions.append(target_bu_name)

    return qualified_transitions

async def get_possible_transitions_with_details(person: Person, current_bu: BusinessUnit) -> Dict[str, Dict[str, Any]]:
    """
    Obtiene las unidades de negocio a las que una persona puede transicionar con detalles.
    
    Args:
        person: Instancia del modelo Person.
        current_bu: Unidad de negocio actual.
        
    Returns:
        Diccionario con nombres de unidades y detalles de elegibilidad.
    """
    current_bu_name = current_bu.name.lower()
    possible_keys = [key for key in DIVISION_TRANSITION_CRITERIA.keys() if key.startswith(current_bu_name)]
    results = {}

    for key in possible_keys:
        target_bu_name = key.split("_to_")[1]
        is_eligible, details = TransitionCriteriaService.check_transition_eligibility(person, target_bu_name)
        results[target_bu_name] = {'eligible': is_eligible, 'details': details}

    return results

# =========================================================
# Funciones Auxiliares y de Generación de Documentos
# =========================================================
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

def get_business_unit_domain(business_unit):
    domains = {
        "huntred": "huntred.com",
        "huntred_executive": "executive.huntred.com",
        "huntu": "huntu.com",
        "amigro": "amigro.com",
        "sexsi": "sexsi.com"
    }
    return domains.get(business_unit.name.lower() if hasattr(business_unit, 'name') else business_unit, "huntred.com")

# =========================================================
# Constantes y configuraciones globales (sin categoría específica)
# =========================================================
PRUEBAS_POR_UNIDAD = {
    'amigro': [
        {'nombre': 'TIPI', 'descripcion': 'Prueba breve para conocer tus rasgos de personalidad.'},
        {'nombre': 'DISC', 'descripcion': 'Evalúa cómo te comportas en el trabajo.'}
    ],
    'huntu': [
        {'nombre': 'huntBigFive', 'descripcion': 'Explora tu personalidad y potencial profesional.'},
        {'nombre': 'MBTI', 'descripcion': 'Descubre tus preferencias laborales.'}
    ],
    'huntred': [
        {'nombre': '16PF', 'descripcion': 'Análisis detallado de tu personalidad y liderazgo.'},
        {'nombre': 'NEO', 'descripcion': 'Evalúa rasgos clave para la gestión.'}
    ],
    'huntred_executive': [
        {'nombre': 'DISC', 'descripcion': 'Evalúa tu estilo de liderazgo y toma de decisiones.'},
        {'nombre': 'huntBigFive', 'descripcion': 'Analiza tu personalidad con enfoque en liderazgo estratégico.'}
    ]
}
# Funciones Genéricas para Pruebas
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

# Criterios de transición definidos como configuración global
DIVISION_TRANSITION_CRITERIA = {
    "amigro_to_huntu": {
        "required_certifications": ["licenciatura"],
        "min_skills": 3,
        "min_experience_months": 18,
        "min_salary_mxn": 20000,
        "min_salary_increase": 0.20,
        "personality_traits": {"conscientiousness": 4.0},
        "profile_completeness": 0.8,
        "additional_requirements": {"cv_parsed": True, "job_search_status": ["activa", "remota"]}
    },
    "huntu_to_huntred": {
        "required_certifications": ["certificación relevante"],
        "required_experience": {"years": 2, "role": "profesional"},
        "min_skills": 5,
        "min_experience_months": 12,
        "min_salary_mxn": 45000,
        "min_salary_increase": 0.30,
        "personality_traits": {"extraversion": 4.5, "openness": 4.0},
        "profile_completeness": 0.9,
        "additional_requirements": {"experience_years": 2}
    },
    "huntred_to_huntred_executive": {
        "required_certifications": ["maestría"],
        "required_experience": {"years": 5, "role": "gerencial"},
        "min_skills": 7,
        "min_experience_months": 36,
        "min_salary_mxn": 150000,
        "min_salary_increase": 0.50,
        "personality_traits": {"extraversion": 4.5, "openness": 4.0, "conscientiousness": 4.5},
        "profile_completeness": 1.0,
        "additional_requirements": {"experience_years": 5}
    }
}

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
