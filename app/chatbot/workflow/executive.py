# /home/pablo/app/chatbot/workflow/executive.py
import logging
from typing import List
from celery import shared_task
from asgiref.sync import sync_to_async
from app.models import Person, Application, BusinessUnit, ChatState
from app.utilidades.signature.pdf_generator import generate_contract_pdf
from app.utilidades.signature.digital_sign import request_digital_signature
from app.chatbot.integrations.services import send_message
from app.chatbot.workflow.common import (
    iniciar_creacion_perfil, ofrecer_prueba_personalidad, continuar_registro
)

logger = logging.getLogger(__name__)

async def iniciar_flujo_huntred_executive(plataforma: str, user_id: str, unidad_negocio: BusinessUnit, 
                                        estado_chat: ChatState, persona: Person):
    """
    Inicia el flujo conversacional para HuntRED Executive.
    
    Args:
        plataforma: Plataforma de comunicación.
        user_id: ID del usuario.
        unidad_negocio: Instancia de BusinessUnit (HuntRED Executive).
        estado_chat: Instancia de ChatState.
        persona: Instancia de Person.
    """
    bu_name = unidad_negocio.name.lower()
    await send_message(plataforma, user_id, 
                      "¡Bienvenido a HuntRED Executive! 🌟 Nos especializamos en colocación de altos ejecutivos. Vamos a crear tu perfil.", 
                      bu_name)
    await iniciar_creacion_perfil(plataforma, user_id, unidad_negocio, estado_chat, persona)

async def continuar_perfil_huntred_executive(plataforma: str, user_id: str, unidad_negocio: BusinessUnit, 
                                           estado_chat: ChatState, persona: Person):
    """
    Continúa el flujo conversacional para completar el perfil en HuntRED Executive.
    
    Args:
        plataforma: Plataforma de comunicación.
        user_id: ID del usuario.
        unidad_negocio: Instancia de BusinessUnit (HuntRED Executive).
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

    # Perfil completo (no hay transiciones ascendentes, ya que es la unidad más alta)
    await send_message(plataforma, user_id, "¡Perfil completo! 🎉 Pronto te contactaremos con oportunidades ejecutivas.", bu_name)
    estado_chat.state = "completed"
    await sync_to_async(estado_chat.save)()

async def manejar_respuesta_huntred_executive(plataforma: str, user_id: str, texto: str, 
                                            unidad_negocio: BusinessUnit, estado_chat: ChatState, 
                                            persona: Person) -> bool:
    """
    Maneja respuestas específicas de HuntRED Executive.
    
    Args:
        plataforma: Plataforma de comunicación.
        user_id: ID del usuario.
        texto: Respuesta del usuario.
        unidad_negocio: Instancia de BusinessUnit (HuntRED Executive).
        estado_chat: Instancia de ChatState.
        persona: Instancia de Person.
        
    Returns:
        bool: True si la respuesta fue manejada, False si no.
    """
    return False  # No hay respuestas específicas por ahora

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

async def is_profile_complete_huntred_executive(persona: Person) -> bool:
    """
    Verifica si el perfil está completo para HuntRED Executive.
    
    Args:
        persona: Instancia de Person.
        
    Returns:
        bool: True si el perfil está completo, False si no.
    """
    return await is_profile_basic_complete(persona)

@shared_task
def process_huntred_executive_candidate(person_id: int):
    """
    Procesa un candidato de HuntRED Executive, generando contratos.
    
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