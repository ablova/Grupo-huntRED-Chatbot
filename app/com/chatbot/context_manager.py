from typing import Dict, Any, Optional
import logging
from django.db import transaction
from asgiref.sync import sync_to_async
from app.models import ChatState, Person, BusinessUnit
from app.com.chatbot.workflow.common import chatbot_metrics

logger = logging.getLogger(__name__)

class ConversationContext:
    """
    Gestor de contexto de conversación para el chatbot.
    
    Mantiene el estado y contexto de la conversación, incluyendo:
    - Estado actual de la conversación
    - Información del usuario
    - Detalles de la unidad de negocio
    - Historial de la conversación
    - Preferencias y restricciones
    
    Características:
    - Caching de contexto
    - Validación de estados
    - Manejo de transiciones
    - Seguimiento de métricas
    """

    def __init__(self, chat_state: ChatState):
        """
        Inicializa el contexto de conversación.
        
        Args:
            chat_state (ChatState): Estado actual de la conversación
        """
        self.chat_state = chat_state
        self.person = chat_state.person
        self.business_unit = chat_state.business_unit
        self.context = self._build_initial_context()

    def _build_initial_context(self) -> Dict[str, Any]:
        """
        Construye el contexto inicial de la conversación.
        
        Returns:
            Dict[str, Any]: Contexto inicial con:
                - Estado actual
                - Información del usuario
                - Detalles de la unidad de negocio
                - Preferencias del usuario
        """
        return {
            'state': self.chat_state.state,
            'person': {
                'id': self.person.id,
                'name': self.person.name,
                'email': self.person.email,
                'phone': self.person.phone,
                'is_profile_complete': self.person.is_profile_complete(),
                'has_cv': bool(self.person.cv_file),
                'has_test': bool(self.person.test_results),
                'applied_jobs': self.person.applications.count(),
                'last_intent': self.chat_state.last_intent if hasattr(self.chat_state, 'last_intent') else None,
                'conversation_history': self.chat_state.conversation_history if hasattr(self.chat_state, 'conversation_history') else []
            },
            'business_unit': {
                'name': self.business_unit.name,
                'features': self.business_unit.get_features(),
                'restrictions': self.business_unit.get_restrictions()
            },
            'preferences': self.person.get_preferences()
        }

    async def update_context(self, updates: Dict[str, Any]) -> None:
        """
        Actualiza el contexto de la conversación.
        
        Args:
            updates (Dict[str, Any]): Actualizaciones para el contexto
        
        Raises:
            ValueError: Si se intenta actualizar un estado no válido
        """
        try:
            self.context.update(updates)
            
            # Actualizar estado si hay cambios relevantes
            if 'state' in updates and updates['state'] != self.chat_state.state:
                self.chat_state.state = updates['state']
                self.chat_state.last_transition = timezone.now()
                
                # Guardar cambios con transacción
                async with transaction.atomic():
                    await sync_to_async(self.chat_state.save)()
                    
                    # Registrar métrica de contexto
                    chatbot_metrics.track_message(
                        'context_update',
                        'completed',
                        success=True,
                        state_transition=f"{self.chat_state.state}"
                    )
        except Exception as e:
            logger.error(f"Error actualizando contexto: {str(e)}")
            raise

    def get_context(self) -> Dict[str, Any]:
        """Obtiene el contexto actual de la conversación."""
        return self.context

    def get_available_intents(self) -> List[str]:
        """Obtiene los intents disponibles basados en el contexto."""
        available_intents = []
        
        # Filtrar por estado del chat
        if self.context['state'] == 'initial':
            available_intents.extend(['start_command', 'saludo', 'crear_perfil', 'calcular_salario'])
        
        # Filtrar por completitud del perfil
        if self.context['person']['is_profile_complete']:
            available_intents.extend(['ver_vacantes', 'prueba_personalidad', 'cargar_cv'])
        
        # Filtrar por unidad de negocio
        bu_features = self.context['business_unit']['features']
        if 'migratory_status' in bu_features:
            available_intents.append('migratory_status')
        if 'internship_search' in bu_features:
            available_intents.append('internship_search')
        if 'executive_roles' in bu_features:
            available_intents.append('executive_roles')
        
        return available_intents

    def get_next_steps(self) -> List[Dict[str, Any]]:
        """Obtiene los siguientes pasos posibles basados en el contexto."""
        next_steps = []
        
        intent_transitions = {
            'crear_perfil': [
                {'intent': 'actualizar_perfil', 'condition': 'profile_complete'},
                {'intent': 'cargar_cv', 'condition': 'profile_complete'},
                {'intent': 'ver_vacantes', 'condition': 'profile_complete'}
            ],
            'ver_vacantes': [
                {'intent': 'aplicar_vacante', 'condition': 'profile_complete'},
                {'intent': 'consultar_estado_postulacion', 'condition': 'has_applied'},
                {'intent': 'solicitar_tips_entrevista', 'condition': 'has_interview'}
            ],
            'prueba_personalidad': [
                {'intent': 'ver_resultados', 'condition': 'test_completed'},
                {'intent': 'ver_vacantes', 'condition': 'profile_complete'}
            ]
        }
        
        if self.context['person']['last_intent'] in intent_transitions:
            for step in intent_transitions[self.context['person']['last_intent']]:
                condition = step['condition']
                if condition == 'profile_complete' and self.context['person']['is_profile_complete']:
                    next_steps.append(step)
                elif condition == 'has_applied' and self.context['person']['applied_jobs'] > 0:
                    next_steps.append(step)
                elif condition == 'has_interview' and self.context['person']['has_interview']:
                    next_steps.append(step)
                elif condition == 'test_completed' and self.context['person']['has_test']:
                    next_steps.append(step)
        
        return next_steps

    def get_fallback_intents(self) -> List[str]:
        """Obtiene los intents de fallback para el intent actual."""
        fallback_intents = {
            'ver_vacantes': ['crear_perfil', 'actualizar_perfil'],
            'aplicar_vacante': ['ver_vacantes', 'crear_perfil'],
            'prueba_personalidad': ['crear_perfil', 'ver_vacantes'],
            'cargar_cv': ['crear_perfil', 'ver_vacantes']
        }
        
        return fallback_intents.get(self.context['person']['last_intent'], ['saludo', 'help'])

    def validate_intent_transition(self, intent: str) -> bool:
        """Valida si la transición de intent es válida."""
        # Transiciones no permitidas
        invalid_transitions = [
            ('ver_vacantes', 'crear_perfil') if not self.context['person']['is_profile_complete'] else False,
            ('aplicar_vacante', 'ver_vacantes'),
            ('prueba_personalidad', 'ver_vacantes'),
            ('cargar_cv', 'ver_vacantes')
        ]
        
        for invalid in invalid_transitions:
            if invalid and invalid[0] == self.context['person']['last_intent'] and invalid[1] == intent:
                return False
        
        return True

    def get_transition_response(self, intent: str) -> str:
        """Obtiene la respuesta de transición entre intents."""
        transitions = {
            'crear_perfil': {
                'ver_vacantes': "¡Perfecto! Ahora que tienes tu perfil completo, vamos a buscar las mejores oportunidades para ti.",
                'cargar_cv': "¡Excelente! Ahora que tienes tu perfil, vamos a subir tu CV para completarlo.",
                'prueba_personalidad': "¡Perfecto! Ahora que tienes tu perfil, vamos a realizar la prueba de personalidad para recomendarte las mejores oportunidades."
            },
            'ver_vacantes': {
                'aplicar_vacante': "¡Perfecto! Vamos a aplicar a la vacante que más te interesa.",
                'prueba_personalidad': "¡Perfecto! Vamos a realizar la prueba de personalidad para recomendarte las mejores oportunidades."
            }
        }
        
        if self.context['person']['last_intent'] in transitions and intent in transitions[self.context['person']['last_intent']]:
            return transitions[self.context['person']['last_intent']][intent]
        
        return "¡Perfecto! Vamos a continuar con tu proceso de búsqueda laboral."

    def get_intent_priority(self, intent: str) -> int:
        """Obtiene la prioridad del intent basado en el contexto."""
        base_priority = 50  # Prioridad base
        
        # Ajustar prioridad según el contexto
        if intent == 'crear_perfil':
            if not self.context['person']['is_profile_complete']:
                base_priority += 10
        elif intent == 'ver_vacantes':
            if self.context['person']['is_profile_complete']:
                base_priority += 5
        elif intent == 'prueba_personalidad':
            if not self.context['person']['has_test']:
                base_priority += 7
        
        return base_priority

# Funciones auxiliares
async def get_conversation_context(chat_state: ChatState) -> Dict[str, Any]:
    """Obtiene el contexto completo de la conversación."""
    context_manager = ConversationContext(chat_state)
    return context_manager.get_context()

async def update_conversation_context(chat_state: ChatState, updates: Dict[str, Any]) -> None:
    """Actualiza el contexto de la conversación."""
    context_manager = ConversationContext(chat_state)
    await context_manager.update_context(updates)

async def get_available_intents(chat_state: ChatState) -> List[str]:
    """Obtiene los intents disponibles para el estado actual."""
    context_manager = ConversationContext(chat_state)
    return context_manager.get_available_intents()

async def get_next_steps(chat_state: ChatState) -> List[Dict[str, Any]]:
    """Obtiene los siguientes pasos posibles."""
    context_manager = ConversationContext(chat_state)
    return context_manager.get_next_steps()

async def get_fallback_intents(chat_state: ChatState) -> List[str]:
    """Obtiene los intents de fallback para el intent actual."""
    context_manager = ConversationContext(chat_state)
    return context_manager.get_fallback_intents()

async def validate_intent_transition(chat_state: ChatState, intent: str) -> bool:
    """Valida si la transición de intent es válida."""
    context_manager = ConversationContext(chat_state)
    return context_manager.validate_intent_transition(intent)

async def get_transition_response(chat_state: ChatState, intent: str) -> str:
    """Obtiene la respuesta de transición entre intents."""
    context_manager = ConversationContext(chat_state)
    return context_manager.get_transition_response(intent)

async def get_intent_priority(chat_state: ChatState, intent: str) -> int:
    """Obtiene la prioridad del intent basado en el contexto."""
    context_manager = ConversationContext(chat_state)
    return context_manager.get_intent_priority(intent)
