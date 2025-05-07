from typing import Dict, Any, Optional, List
import logging
from django.db import transaction
from app.models import ChatState, Person, BusinessUnit
from app.chatbot.workflow.common import chatbot_metrics

logger = logging.getLogger(__name__)

class ChatStateTransition:
    def __init__(self, current_state: str, next_state: str, conditions: Dict[str, Any] = None):
        self.current_state = current_state
        self.next_state = next_state
        self.conditions = conditions or {}

    def is_valid_transition(self, person: Person) -> bool:
        """Verifica si la transición es válida según las condiciones."""
        for key, value in self.conditions.items():
            if key == 'min_experience':
                if person.experience_years < value:
                    return False
            elif key == 'min_salary':
                if person.salary_data.get('current_salary', 0) < value:
                    return False
            elif key == 'has_cv':
                if not person.cv_file:
                    return False
            elif key == 'has_profile':
                if not person.is_profile_complete():
                    return False
            elif key == 'has_test':
                if not person.has_completed_test():
                    return False
        return True

class ChatStateManager:
    def __init__(self, business_unit: BusinessUnit):
        self.business_unit = business_unit
        self.state_transitions = self._initialize_state_transitions()

    def _initialize_state_transitions(self) -> Dict[str, List[ChatStateTransition]]:
        """Inicializa las transiciones de estado según la unidad de negocio."""
        transitions = {
            "initial": [
                ChatStateTransition("initial", "waiting_for_tos"),
                ChatStateTransition("initial", "profile_in_progress", {"has_cv": True}),
            ],
            "waiting_for_tos": [
                ChatStateTransition("waiting_for_tos", "profile_in_progress", {"has_tos_accepted": True}),
                ChatStateTransition("waiting_for_tos", "initial"),
            ],
            "profile_in_progress": [
                ChatStateTransition("profile_in_progress", "profile_complete", {"has_profile": True}),
                ChatStateTransition("profile_in_progress", "initial"),
            ],
            "profile_complete": [
                ChatStateTransition("profile_complete", "applied", {"has_applied": True}),
                ChatStateTransition("profile_complete", "profile_in_progress"),
            ],
            "applied": [
                ChatStateTransition("applied", "scheduled", {"has_interview_scheduled": True}),
                ChatStateTransition("applied", "profile_complete"),
            ],
            "scheduled": [
                ChatStateTransition("scheduled", "interviewed", {"has_completed_interview": True}),
                ChatStateTransition("scheduled", "applied"),
            ],
            "interviewed": [
                ChatStateTransition("interviewed", "offered", {"has_offer": True}),
                ChatStateTransition("interviewed", "applied"),
            ],
            "offered": [
                ChatStateTransition("offered", "signed", {"has_signed_contract": True}),
                ChatStateTransition("offered", "interviewed"),
            ],
            "signed": [
                ChatStateTransition("signed", "hired", {"has_started_job": True}),
                ChatStateTransition("signed", "offered"),
            ],
            "hired": [
                ChatStateTransition("hired", "idle", {"has_completed_probation": True}),
                ChatStateTransition("hired", "signed"),
            ],
            "idle": [
                ChatStateTransition("idle", "profile_complete", {"has_updated_profile": True}),
                ChatStateTransition("idle", "initial"),
            ],
        }

        # Ajustar transiciones según la unidad de negocio
        if self.business_unit.name.lower() == "amigro":
            transitions["initial"].append(
                ChatStateTransition("initial", "migratory_status", {"has_migration_docs": True})
            )
        elif self.business_unit.name.lower() == "huntu":
            transitions["profile_complete"].append(
                ChatStateTransition("profile_complete", "internship_search", {"is_student": True})
            )
        elif self.business_unit.name.lower() == "huntred":
            transitions["profile_complete"].append(
                ChatStateTransition("profile_complete", "executive_search", {"has_executive_experience": True})
            )

        return transitions

    async def transition_to_state(self, chat_state: ChatState, new_state: str) -> bool:
        """Realiza una transición de estado."""
        current_state = chat_state.state
        
        # Verificar si la transición es válida
        transitions = self.state_transitions.get(current_state, [])
        valid_transitions = [t for t in transitions if t.next_state == new_state]
        
        if not valid_transitions:
            logger.warning(f"Transición no válida: {current_state} -> {new_state}")
            return False
            
        # Verificar condiciones de la transición
        person = await sync_to_async(chat_state.person.refresh_from_db)()
        for transition in valid_transitions:
            if transition.is_valid_transition(person):
                # Actualizar estado
                chat_state.state = new_state
                chat_state.last_transition = timezone.now()
                
                # Guardar cambios con transacción
                try:
                    async with transaction.atomic():
                        await sync_to_async(chat_state.save)()
                        
                        # Registrar métrica de transición
                        chatbot_metrics.track_message(
                            'state_transition',
                            'completed',
                            success=True,
                            state_transition=f"{current_state}->{new_state}"
                        )
                        
                        return True
                except Exception as e:
                    logger.error(f"Error cambiando estado: {str(e)}")
                    return False
                    
        logger.warning(f"Condiciones no cumplidas para transición: {current_state} -> {new_state}")
        return False

    def get_available_transitions(self, chat_state: ChatState) -> List[str]:
        """Obtiene las transiciones disponibles desde el estado actual."""
        current_state = chat_state.state
        transitions = self.state_transitions.get(current_state, [])
        
        person = chat_state.person
        available_transitions = []
        
        for transition in transitions:
            if transition.is_valid_transition(person):
                available_transitions.append(transition.next_state)
                
        return available_transitions

    def get_state_description(self, state: str) -> str:
        """Obtiene la descripción del estado."""
        descriptions = {
            "initial": "Estado inicial",
            "waiting_for_tos": "Esperando aceptación de TOS",
            "profile_in_progress": "Creando perfil",
            "profile_complete": "Perfil completo",
            "applied": "Solicitud enviada",
            "scheduled": "Entrevista programada",
            "interviewed": "Entrevista completada",
            "offered": "Oferta recibida",
            "signed": "Contrato firmado",
            "hired": "Contratado",
            "idle": "Inactivo",
        }
        
        # Ajustar descripciones según la unidad de negocio
        if self.business_unit.name.lower() == "amigro":
            descriptions["migratory_status"] = "Verificando estatus migratorio"
        elif self.business_unit.name.lower() == "huntu":
            descriptions["internship_search"] = "Buscando internships"
        elif self.business_unit.name.lower() == "huntred":
            descriptions["executive_search"] = "Buscando posiciones ejecutivas"
        
        return descriptions.get(state, "Estado desconocido")

# Instancia global
chat_state_manager = ChatStateManager

# Funciones auxiliares
async def validate_state_transition(chat_state: ChatState, new_state: str) -> bool:
    """Valida si una transición de estado es válida."""
    return await chat_state_manager(chat_state.business_unit).transition_to_state(chat_state, new_state)

async def get_available_actions(chat_state: ChatState) -> List[str]:
    """Obtiene las acciones disponibles según el estado actual."""
    return chat_state_manager(chat_state.business_unit).get_available_transitions(chat_state)

async def get_current_state_description(chat_state: ChatState) -> str:
    """Obtiene la descripción del estado actual."""
    return chat_state_manager(chat_state.business_unit).get_state_description(chat_state.state)
