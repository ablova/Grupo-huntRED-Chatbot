# /home/pablo/app/chatbot/workflow/huntu.py
import logging
from typing import List
from celery import shared_task
from asgiref.sync import sync_to_async
from app.models import Person, Application, BusinessUnit, ChatState
from app.utilidades.signature.pdf_generator import generate_contract_pdf
from app.utilidades.signature.digital_sign import request_digital_signature
from app.chatbot.integrations.services import send_message, send_options
from app.chatbot.workflow.common import (
    iniciar_creacion_perfil, ofrecer_prueba_personalidad, continuar_registro,
    transfer_candidate_to_new_division, get_possible_transitions
)

logger = logging.getLogger(__name__)

# Opciones de área de interés para Huntu (a alinear con Division en el futuro)
AREAS_INTERES = [
    {"title": "Tecnología", "payload": "tecnologia"},
    {"title": "Marketing", "payload": "marketing"},
    {"title": "Finanzas", "payload": "finanzas"},
    {"title": "Diseño", "payload": "diseno"},
    {"title": "Otro", "payload": "otro_area"}
]

async def iniciar_flujo_huntu(plataforma: str, user_id: str, unidad_negocio: BusinessUnit, 
                            estado_chat: ChatState, persona: Person):
    """
    Inicia el flujo conversacional para Huntu.
    
    Args:
        plataforma: Plataforma de comunicación.
        user_id: ID del usuario.
        unidad_negocio: Instancia de BusinessUnit (Huntu).
        estado_chat: Instancia de ChatState.
        persona: Instancia de Person.
    """
    bu_name = unidad_negocio.name.lower()
    await send_message(plataforma, user_id, 
                      "¡Bienvenido a Huntu! 🏆 Conectamos talento joven con oportunidades de alto impacto. Vamos a crear tu perfil.", 
                      bu_name)
    await iniciar_creacion_perfil(plataforma, user_id, unidad_negocio, estado_chat, persona)

async def continuar_perfil_huntu(plataforma: str, user_id: str, unidad_negocio: BusinessUnit, 
                               estado_chat: ChatState, persona: Person):
    """
    Continúa el flujo conversacional para completar el perfil en Huntu.
    
    Args:
        plataforma: Plataforma de comunicación.
        user_id: ID del usuario.
        unidad_negocio: Instancia de BusinessUnit (Huntu).
        estado_chat: Instancia de ChatState.
        persona: Instancia de Person.
    """
    bu_name = unidad_negocio.name.lower()
    
    # Asegurar que metadata sea un diccionario
    if not isinstance(persona.metadata, dict):
        persona.metadata = {}
        await sync_to_async(persona.save)()

    # Recolectar datos básicos (nombre, email, teléfono)
    if not await is_profile_basic_complete(persona):
        await continuar_registro(plataforma, user_id, unidad_negocio, estado_chat, persona)
        return

    # Preguntar área de interés
    if "area_interes" not in persona.metadata:
        if estado_chat.state != "waiting_for_area_interes":
            await send_message(plataforma, user_id, "¿En qué área te interesa trabajar? Selecciona una opción:", bu_name)
            await send_options(plataforma, user_id, "Elige un área:", AREAS_INTERES, bu_name)
            estado_chat.state = "waiting_for_area_interes"
            await sync_to_async(estado_chat.save)()
        return

    # Verificar transiciones posibles
    qualified_transitions = await get_possible_transitions(persona, unidad_negocio)
    if qualified_transitions:
        message = "¡Felicidades! Tus habilidades sugieren que podrías calificar para una unidad superior:\n"
        options = [{"title": bu.capitalize(), "payload": f"move_to_{bu}"} for bu in qualified_transitions]
        message += "\n".join([f"{i+1}. {opt['title']}" for i, opt in enumerate(options)])
        message += "\nResponde con el número o 'No' para quedarte en Huntu."
        await send_message(plataforma, user_id, message, bu_name)
        estado_chat.state = "offering_division_change"
        estado_chat.context["possible_transitions"] = qualified_transitions
        await sync_to_async(estado_chat.save)()
        return

    # Perfil completo
    await send_message(plataforma, user_id, "¡Perfil completo! 🎉 Pronto te contactaremos con oportunidades.", bu_name)
    estado_chat.state = "completed"
    await sync_to_async(estado_chat.save)()

async def manejar_respuesta_huntu(plataforma: str, user_id: str, texto: str, 
                                unidad_negocio: BusinessUnit, estado_chat: ChatState, 
                                persona: Person) -> bool:
    """
    Maneja respuestas específicas de Huntu, como el área de interés.
    
    Args:
        plataforma: Plataforma de comunicación.
        user_id: ID del usuario.
        texto: Respuesta del usuario.
        unidad_negocio: Instancia de BusinessUnit (Huntu).
        estado_chat: Instancia de ChatState.
        persona: Instancia de Person.
        
    Returns:
        bool: True si la respuesta fue manejada, False si no.
    """
    bu_name = unidad_negocio.name.lower()
    texto_lower = texto.lower().strip()

    if estado_chat.state == "waiting_for_area_interes":
        valid_areas = [opt["payload"] for opt in AREAS_INTERES]
        if texto_lower in valid_areas:
            area = next(opt["title"] for opt in AREAS_INTERES if opt["payload"] == texto_lower)
            persona.metadata['area_interes'] = area
            await sync_to_async(persona.save)()
            await send_message(plataforma, user_id, f"¡Gracias! Área registrada: {area}.", bu_name)
            estado_chat.state = "profile_in_progress"
            await sync_to_async(estado_chat.save)()
            await continuar_perfil_huntu(plataforma, user_id, unidad_negocio, estado_chat, persona)
        else:
            await send_message(plataforma, user_id, "Por favor, selecciona una opción válida.", bu_name)
            await send_options(plataforma, user_id, "Elige un área:", AREAS_INTERES, bu_name)
        return True

    return False

async def is_profile_basic_complete(persona: Person) -> bool:
    """
    Verifica si los datos básicos del perfil están completos.
    
    Args:
        persona: Instancia de Person.
        
    Returns:
        bool: True si los datos básicos están completos, False si no.
    """
    required_fields = ['nombre', 'email', 'phone']
    return all(getattr(persona, field, None) for field in required_fields)

async def is_profile_complete_huntu(persona: Person) -> bool:
    """
    Verifica si el perfil está completo para Huntu.
    
    Args:
        persona: Instancia de Person.
        
    Returns:
        bool: True si el perfil está completo, False si no.
    """
    return await is_profile_basic_complete(persona) and bool(persona.metadata.get('area_interes'))

@shared_task
def process_huntu_candidate(person_id: int):
    """
    Procesa un candidato de Huntu, generando contratos.
    
    Args:
        person_id: ID de la persona.
    """
    try:
        person = Person.objects.get(id=person_id)
        application = Application.objects.filter(user=person).first()
        if not application or not application.vacancy:
            return "Candidato sin vacante asignada."

        contract_path = generate_contract_pdf(person, None, application.vacancy.titulo, person.business_unit)
        request_digital_signature(
            user=person,
            document_path=contract_path,
            document_name=f"Carta Propuesta - {application.vacancy.titulo}.pdf"
        )
        return f"Contrato generado y enviado a {person.nombre}"
    except Person.DoesNotExist:
        logger.error(f"Candidato {person_id} no encontrado.")
        return "Candidato no encontrado."
    except Exception as e:
        logger.error(f"Error procesando candidato {person_id}: {e}", exc_info=True)
        return f"Error: {str(e)}"