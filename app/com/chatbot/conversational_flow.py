from django.db import transaction
from django.utils import timezone
from .models import IntentPattern, StateTransition, IntentTransition, ContextCondition, ChatState
from app.models import Person, BusinessUnit
import logging

logger = logging.getLogger(__name__)

class ConversationalFlowManager:
    """
    Gestor de flujo conversacional para el chatbot.
    
    Características:
    - Manejo de estados de conversación
    - Transiciones de estado basadas en intents
    - Gestión de contexto y memoria
    - Integración con ML para respuestas dinámicas
    
    Estructura:
    1. Manejo de estados
    2. Detección de intents
    3. Transiciones de estado
    4. Gestión de contexto
    5. Generación de respuestas
    
    Uso:
    1. Inicializar con unidad de negocio
    2. Procesar mensajes usando process_message()
    3. Obtener respuestas usando get_response()
    
    Ejemplo:
    ```python
    flow_manager = ConversationalFlowManager(business_unit)
    response = flow_manager.process_message(person, "Hola")
    ```
    """

    def __init__(self, business_unit: BusinessUnit):
        """
        Inicializa el gestor de flujo conversacional.
        
        Args:
            business_unit (BusinessUnit): Unidad de negocio asociada
        """
        self.business_unit = business_unit
        self.current_state = None
        self.context = {}
        
        # Inicializar componentes
        self.intent_detector = IntentDetector(business_unit)
        self.state_manager = StateManager(business_unit)
        self.context_manager = ContextManager(business_unit)
        self.response_generator = ResponseGenerator(business_unit)

    async def process_message(self, person: Person, message: str) -> dict:
        """
        Procesa un mensaje y determina la siguiente acción del flujo conversacional.
        
        Args:
            person (Person): El usuario que envía el mensaje
            message (str): El mensaje recibido
            
        Returns:
            dict: Respuesta con:
                - next_state: Estado siguiente
                - response: Respuesta al usuario
                - actions: Acciones a realizar
                - context: Contexto actualizado
        """
        try:
            with transaction.atomic():
                # 1. Obtener o crear el estado actual del chat
                chat_state, _ = await ChatState.objects.aget_or_create(
                    person=person,
                    business_unit=self.business_unit
                )
                
                # 2. Detectar intent
                intent = await self.intent_detector.detect_intent(message)
                
                # 3. Verificar condiciones de contexto
                if not await self.context_manager.check_conditions(intent):
                    return await self._handle_context_failure()
                
                # 4. Determinar transición de estado
                next_state = await self.state_manager.determine_next_state(intent)
                
                # 5. Actualizar estado
                await self.state_manager.update_state(chat_state, next_state)
                
                # 6. Generar respuesta
                response = await self.response_generator.generate_response(intent, next_state)
                
                return {
                    'success': True,
                    'current_state': next_state,
                    'response': response,
                    'context': self.context
                }
                
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def _determine_intent(self, message: str) -> str:
        """
        Determina el intent del mensaje basado en los patrones configurados.
        """
        # Buscar el intent con mayor prioridad que coincida con el mensaje
        patterns = IntentPattern.objects.filter(
            business_units=self.business_unit,
            enabled=True
        ).order_by('-priority')
        
        for pattern in patterns:
            if self._matches_patterns(message, pattern.patterns):
                return pattern.name
        
        return 'default_intent'

    def _matches_patterns(self, message: str, patterns: str) -> bool:
        """
        Verifica si el mensaje coincide con alguno de los patrones.
        """
        if not patterns:
            return False
            
        for pattern in patterns.split('\n'):
            if pattern and re.search(pattern.strip(), message, re.IGNORECASE):
                return True
        return False

    def _check_context_conditions(self, intent: str) -> bool:
        """
        Verifica si se cumplen las condiciones de contexto necesarias.
        """
        conditions = ContextCondition.objects.filter(
            intent=intent,
            business_unit=self.business_unit
        )
        
        for condition in conditions:
            if not self._evaluate_condition(condition):
                return False
        return True

    def _evaluate_condition(self, condition: ContextCondition) -> bool:
        """
        Evalúa una condición de contexto.
        """
        value = self.context.get(condition.name)
        if not value:
            return False
            
        if condition.type == 'boolean':
            return bool(value)
        elif condition.type == 'numeric':
            return float(value) >= float(condition.value)
        elif condition.type == 'string':
            return str(value) == str(condition.value)
        return False

    def _determine_next_state(self, intent: str) -> str:
        """
        Determina el siguiente estado basado en el intent actual.
        """
        try:
            transition = IntentTransition.objects.get(
                current_intent=intent,
                business_unit=self.business_unit
            )
            return transition.next_intent
        except IntentTransition.DoesNotExist:
            return 'default_state'

    def _get_response(self, intent: str, state: str) -> str:
        """
        Obtiene la respuesta apropiada para el intent y estado actual.
        """
        try:
            # Aquí podrías implementar una lógica más compleja usando GPT o templates
            return f"Respuesta para intent '{intent}' en estado '{state}'"
        except Exception as e:
            logger.error(f"Error getting response: {str(e)}")
            return "Lo siento, hubo un error al procesar tu mensaje."

    def _handle_context_failure(self) -> dict:
        """
        Maneja el caso donde las condiciones de contexto no se cumplen.
        """
        return {
            'success': False,
            'error': "No se cumplen las condiciones de contexto necesarias",
            'required_context': [cond.name for cond in 
                               ContextCondition.objects.filter(
                                   business_unit=self.business_unit
                               )]
        }

class FlowVisualization:
    """
    Clase para generar visualizaciones del flujo conversacional.
    """
    def __init__(self, business_unit: BusinessUnit):
        self.business_unit = business_unit

    def generate_flow_diagram(self):
        """
        Genera un diagrama visual del flujo conversacional.
        """
        try:
            import graphviz
            from django.db.models import Q
            
            # Crear un nuevo grafo
            dot = graphviz.Digraph(comment='Conversational Flow')
            
            # Obtener todas las transiciones
            transitions = StateTransition.objects.filter(
                Q(current_state__business_unit=self.business_unit) |
                Q(next_state__business_unit=self.business_unit)
            ).distinct()
            
            # Agregar nodos y aristas
            for transition in transitions:
                dot.node(transition.current_state.name, 
                        f"{transition.current_state.name}\n{transition.current_state.description}")
                dot.node(transition.next_state.name,
                        f"{transition.next_state.name}\n{transition.next_state.description}")
                
                dot.edge(transition.current_state.name,
                        transition.next_state.name,
                        label=transition.type)
            
            # Renderizar el grafo
            return dot
            
        except ImportError:
            logger.error("Graphviz no está instalado")
            return None
        except Exception as e:
            logger.error(f"Error generating flow diagram: {str(e)}")
            return None

    def generate_business_unit_dashboard(self):
        """
        Genera un dashboard visual del estado de los procesos por unidad de negocio.
        """
        try:
            from django.db.models import Count
            import pandas as pd
            import plotly.express as px
            
            # Obtener estadísticas de estados por candidato
            stats = ChatState.objects.filter(
                business_unit=self.business_unit
            ).values('state').annotate(
                count=Count('id')
            )
            
            # Convertir a DataFrame
            df = pd.DataFrame(stats)
            
            # Crear gráfico de barras
            fig = px.bar(
                df,
                x='state',
                y='count',
                title=f'Estado de Procesos - {self.business_unit.name}',
                labels={'state': 'Estado', 'count': 'Número de Candidatos'}
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error generating dashboard: {str(e)}")
            return None

    def generate_candidate_flow(self, person: Person):
        """
        Genera una visualización del flujo de un candidato específico.
        """
        try:
            import plotly.graph_objects as go
            
            # Obtener historial de estados
            history = ChatState.objects.filter(
                person=person,
                business_unit=self.business_unit
            ).order_by('last_transition')
            
            # Crear timeline
            fig = go.Figure()
            
            for state in history:
                fig.add_trace(go.Scatter(
                    x=[state.last_transition],
                    y=[state.state],
                    mode='markers+text',
                    text=state.state,
                    textposition="top center"
                ))
            
            fig.update_layout(
                title=f'Flujo de Conversación - {person.nombre} {person.apellido_paterno}',
                xaxis_title='Fecha',
                yaxis_title='Estado'
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error generating candidate flow: {str(e)}")
            return None
