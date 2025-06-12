# /home/pablo/app/com/chatbot/workflow/business_units/huntred_executive.py
"""
Módulo para el flujo de trabajo de HuntRED Executive.

Este módulo maneja el proceso de reclutamiento y selección para posiciones
C-level y miembros de consejo, siguiendo un proceso más riguroso y especializado.
"""

import logging
from typing import List, Dict, Any
from celery import shared_task
from asgiref.sync import sync_to_async
from app.models import Person, Application, BusinessUnit, ChatState, Division
from app.ats.utils.signature.pdf_generator import generate_contract_pdf
from app.ats.utils.signature.digital_sign import request_digital_signature
from app.ats.integrations.services import send_message, send_options_async
from app.ats.chatbot.workflow.common.common import (
    iniciar_creacion_perfil, ofrecer_prueba_personalidad, continuar_registro,
    transfer_candidate_to_new_division, get_possible_transitions
)

logger = logging.getLogger(__name__)

# Niveles ejecutivos para HuntRED Executive
NIVELES_EJECUTIVOS = [
    {"title": "Chief Executive Officer (CEO)", "payload": "ceo"},
    {"title": "Chief Financial Officer (CFO)", "payload": "cfo"},
    {"title": "Chief Operating Officer (COO)", "payload": "coo"},
    {"title": "Chief Technology Officer (CTO)", "payload": "cto"},
    {"title": "Chief Marketing Officer (CMO)", "payload": "cmo"},
    {"title": "Chief Human Resources Officer (CHRO)", "payload": "chro"},
    {"title": "Chief Legal Officer (CLO)", "payload": "clo"},
    {"title": "Chief Risk Officer (CRO)", "payload": "cro"},
    {"title": "Chief Transformation Officer (CTO)", "payload": "cto_transformation"},
    {"title": "Chief Digital Officer (CDO)", "payload": "cdo"},
    {"title": "Miembro del Consejo de Administración", "payload": "board_member"},
    {"title": "Miembro del Comité Ejecutivo", "payload": "exec_committee"},
    {"title": "Otro", "payload": "otro_nivel"}
]

# Tipos de consejos
TIPOS_CONSEJO = [
    {"title": "Consejo de Administración", "payload": "board"},
    {"title": "Comité Ejecutivo", "payload": "exec_committee"},
    {"title": "Comité de Auditoría", "payload": "audit_committee"},
    {"title": "Comité de Nominación", "payload": "nomination_committee"},
    {"title": "Comité de Compensación", "payload": "compensation_committee"},
    {"title": "Consejo de Recursos Humanos", "payload": "hr_board"},
    {"title": "Consejo de Atracción y Retención", "payload": "attraction_retention_board"},
    {"title": "Consejo de Planeación Financiera", "payload": "financial_planning_board"},
    {"title": "Consejo de Riesgo", "payload": "risk_board"},
    {"title": "Otro", "payload": "otro_consejo"}
]

async def iniciar_flujo_huntred_executive(plataforma: str, user_id: str, unidad_negocio: BusinessUnit, 
                                        estado_chat: ChatState, persona: Person):
    """
    Inicia el flujo conversacional para HuntRED Executive.
    
    Args:
        plataforma: Plataforma de comunicación
        user_id: ID del usuario
        unidad_negocio: Instancia de BusinessUnit (HuntRED Executive)
        estado_chat: Instancia de ChatState
        persona: Instancia de Person
    """
    bu_name = unidad_negocio.name.lower()
    await send_message(plataforma, user_id, 
                      "¡Bienvenido a HuntRED Executive! 👔 Especializamos en posiciones C-level y miembros de consejo. "
                      "Vamos a crear tu perfil ejecutivo.", 
                      bu_name)
    await iniciar_creacion_perfil(plataforma, user_id, unidad_negocio, estado_chat, persona)

async def continuar_perfil_huntred_executive(plataforma: str, user_id: str, unidad_negocio: BusinessUnit, 
                                           estado_chat: ChatState, persona: Person):
    """
    Continúa el flujo conversacional para completar el perfil en HuntRED Executive.
    
    Args:
        plataforma: Plataforma de comunicación
        user_id: ID del usuario
        unidad_negocio: Instancia de BusinessUnit (HuntRED Executive)
        estado_chat: Instancia de ChatState
        persona: Instancia de Person
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

    # Preguntar tipo de posición ejecutiva
    if "tipo_posicion_ejecutiva" not in persona.metadata:
        if estado_chat.state != "waiting_for_tipo_posicion":
            await send_message(plataforma, user_id, 
                             "¿Qué tipo de posición ejecutiva te interesa? Selecciona una opción:", 
                             bu_name)
            await send_options_async(plataforma, user_id, "Elige una posición:", NIVELES_EJECUTIVOS, bu_name)
            estado_chat.state = "waiting_for_tipo_posicion"
            await sync_to_async(estado_chat.save)()
        return

    # Preguntar experiencia en consejos
    if "experiencia_consejos" not in persona.metadata:
        if estado_chat.state != "waiting_for_experiencia_consejos":
            await send_message(plataforma, user_id, 
                             "¿Tienes experiencia en consejos directivos? Selecciona una opción:", 
                             bu_name)
            await send_options_async(plataforma, user_id, "Elige un tipo de consejo:", TIPOS_CONSEJO, bu_name)
            estado_chat.state = "waiting_for_experiencia_consejos"
            await sync_to_async(estado_chat.save)()
        return

    # Preguntar industria preferida
    if "industria_preferida" not in persona.metadata:
        if estado_chat.state != "waiting_for_industria":
            await send_message(plataforma, user_id, 
                             "¿En qué industria tienes más experiencia o prefieres trabajar?", 
                             bu_name)
            await send_options_async(plataforma, user_id, "Elige una industria:", 
                             await get_industry_options(), bu_name)
            estado_chat.state = "waiting_for_industria"
            await sync_to_async(estado_chat.save)()
        return

    # Perfil completo
    await send_message(plataforma, user_id, 
                      "¡Perfil ejecutivo completo! 🎉 Nuestro equipo especializado en C-level "
                      "te contactará pronto para discutir oportunidades específicas.", 
                      bu_name)
    estado_chat.state = "completed"
    await sync_to_async(estado_chat.save)()

async def manejar_respuesta_huntred_executive(plataforma: str, user_id: str, texto: str, 
                                            unidad_negocio: BusinessUnit, estado_chat: ChatState, 
                                            persona: Person) -> bool:
    """
    Maneja respuestas específicas de HuntRED Executive.
    
    Args:
        plataforma: Plataforma de comunicación
        user_id: ID del usuario
        texto: Respuesta del usuario
        unidad_negocio: Instancia de BusinessUnit (HuntRED Executive)
        estado_chat: Instancia de ChatState
        persona: Instancia de Person
        
    Returns:
        bool: True si la respuesta fue manejada, False si no
    """
    bu_name = unidad_negocio.name.lower()
    texto_lower = texto.lower().strip()

    if estado_chat.state == "waiting_for_tipo_posicion":
        valid_positions = [opt["payload"] for opt in NIVELES_EJECUTIVOS]
        if texto_lower in valid_positions:
            position = next(opt["title"] for opt in NIVELES_EJECUTIVOS if opt["payload"] == texto_lower)
            persona.metadata['tipo_posicion_ejecutiva'] = position
            await sync_to_async(persona.save)()
            await send_message(plataforma, user_id, f"¡Gracias! Posición registrada: {position}.", bu_name)
            estado_chat.state = "profile_in_progress"
            await sync_to_async(estado_chat.save)()
            await continuar_perfil_huntred_executive(plataforma, user_id, unidad_negocio, estado_chat, persona)
        else:
            await send_message(plataforma, user_id, "Por favor, selecciona una opción válida.", bu_name)
            await send_options_async(plataforma, user_id, "Elige una posición:", NIVELES_EJECUTIVOS, bu_name)
        return True

    elif estado_chat.state == "waiting_for_experiencia_consejos":
        valid_boards = [opt["payload"] for opt in TIPOS_CONSEJO]
        if texto_lower in valid_boards:
            board_type = next(opt["title"] for opt in TIPOS_CONSEJO if opt["payload"] == texto_lower)
            persona.metadata['experiencia_consejos'] = board_type
            await sync_to_async(persona.save)()
            await send_message(plataforma, user_id, f"¡Gracias! Experiencia registrada: {board_type}.", bu_name)
            estado_chat.state = "profile_in_progress"
            await sync_to_async(estado_chat.save)()
            await continuar_perfil_huntred_executive(plataforma, user_id, unidad_negocio, estado_chat, persona)
        else:
            await send_message(plataforma, user_id, "Por favor, selecciona una opción válida.", bu_name)
            await send_options_async(plataforma, user_id, "Elige un tipo de consejo:", TIPOS_CONSEJO, bu_name)
        return True

    return False

async def is_profile_basic_complete(persona: Person) -> bool:
    """
    Verifica si los datos básicos del perfil están completos.
    
    Args:
        persona: Instancia de Person
        
    Returns:
        bool: True si los datos básicos están completos, False si no
    """
    required_fields = ['nombre', 'email', 'phone']
    return all(getattr(persona, field, None) for field in required_fields)

async def is_profile_complete_huntred_executive(persona: Person) -> bool:
    """
    Verifica si el perfil está completo para HuntRED Executive.
    
    Args:
        persona: Instancia de Person
        
    Returns:
        bool: True si el perfil está completo, False si no
    """
    required_metadata = ['tipo_posicion_ejecutiva', 'experiencia_consejos', 'industria_preferida']
    return await is_profile_basic_complete(persona) and all(
        persona.metadata.get(field) for field in required_metadata
    )

@shared_task
def process_huntred_executive_candidate(person_id: int):
    """
    Procesa un candidato de HuntRED Executive.
    
    Args:
        person_id: ID de la persona
    """
    try:
        person = Person.objects.get(id=person_id)
        application = Application.objects.filter(user=person).first()
        if not application or not application.vacancy:
            return "Candidato sin vacante asignada."

        # Generar contrato ejecutivo
        contract_path = generate_contract_pdf(
            person, 
            None, 
            application.vacancy.titulo, 
            person.business_unit,
            is_executive=True
        )
        
        # Solicitar firma digital
        request_digital_signature(
            user=person,
            document_path=contract_path,
            document_name=f"Carta Propuesta Ejecutiva - {application.vacancy.titulo}.pdf"
        )
        
        return f"Contrato ejecutivo generado y enviado a {person.nombre}"
    except Person.DoesNotExist:
        logger.error(f"Candidato {person_id} no encontrado.")
        return "Candidato no encontrado."
    except Exception as e:
        logger.error(f"Error procesando candidato {person_id}: {e}", exc_info=True)
        return f"Error: {str(e)}"

async def get_industry_options() -> List[Dict[str, str]]:
    """
    Obtiene las opciones de industria para posiciones ejecutivas.
    
    Returns:
        List[Dict[str, str]]: Lista de opciones de industria
    """
    return [
        {"title": "Tecnología", "payload": "tech"},
        {"title": "Finanzas", "payload": "finance"},
        {"title": "Salud", "payload": "healthcare"},
        {"title": "Energía", "payload": "energy"},
        {"title": "Manufactura", "payload": "manufacturing"},
        {"title": "Retail", "payload": "retail"},
        {"title": "Servicios Profesionales", "payload": "professional_services"},
        {"title": "Otro", "payload": "other"}
    ] 