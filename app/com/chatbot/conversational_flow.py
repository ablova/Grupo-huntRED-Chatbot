from django.db import transaction
from django.utils import timezone
from app.models import IntentPattern, StateTransition, IntentTransition, ContextCondition, ChatState, Person, BusinessUnit
import logging
from app.com.utils.visualization import FlowVisualization as BaseFlowVisualization
import re

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

class FlowVisualization(BaseFlowVisualization):
    """
    Clase para generar visualizaciones del flujo conversacional, extendiendo la implementación base.
    Soporta características específicas de canales y necesidades de unidades de negocio, incluyendo notificaciones y alertas.
    """
    def __init__(self, business_unit: BusinessUnit):
        super().__init__()
        self.business_unit = business_unit
        self.notification_handlers = {}
        self.alert_handlers = {}
        self._initialize_handlers()

    def _initialize_handlers(self):
        """
        Inicializa los manejadores de notificaciones y alertas basados en la unidad de negocio.
        Configura características específicas para cada canal y necesidades de la unidad de negocio.
        """
        if self.business_unit.name == 'huntRED':
            self.notification_handlers['whatsapp'] = self._send_whatsapp_notification
            self.notification_handlers['telegram'] = self._send_telegram_notification
            self.alert_handlers['urgent'] = self._handle_urgent_alert
        elif self.business_unit.name == 'Amigro':
            self.notification_handlers['email'] = self._send_email_notification
            self.alert_handlers['standard'] = self._handle_standard_alert
        elif self.business_unit.name == 'huntU':
            self.notification_handlers['sms'] = self._send_sms_notification
            self.alert_handlers['info'] = self._handle_info_alert
        # Configuración para otras unidades de negocio
        else:
            self.notification_handlers['default'] = self._send_default_notification
            self.alert_handlers['default'] = self._handle_default_alert
        logger.info(f"Handlers initialized for business unit: {self.business_unit.name}")

    def generate_flow_diagram(self):
        """
        Genera un diagrama visual del flujo conversacional.
        Este método puede ser extendido para agregar funcionalidades específicas del chatbot.
        """
        return super().generate_process_flow()

    def generate_candidate_flow(self, person: Person):
        """
        Genera una visualización del flujo de un candidato específico.
        """
        return super().generate_candidate_timeline(person)

    def send_notification(self, channel: str, message: str, person: Person = None):
        """
        Envía una notificación a través del canal especificado.
        Selecciona el manejador adecuado basado en el canal y la unidad de negocio.
        Si el canal especificado falla debido a limitaciones, intenta un canal alternativo.

        Args:
            channel (str): Canal a través del cual enviar la notificación.
            message (str): Mensaje de la notificación.
            person (Person, optional): Persona a la que va dirigida la notificación.
        """
        handler = self.notification_handlers.get(channel, self.notification_handlers.get('default'))
        if handler:
            try:
                handler(message, person)
                logger.info(f"Notification sent via {channel} for {self.business_unit.name}")
            except Exception as e:
                logger.error(f"Error sending notification via {channel}: {str(e)}")
                # Intentar un canal alternativo si el inicial falla
                fallback_channel = self._get_fallback_channel(channel)
                if fallback_channel and fallback_channel != channel:
                    logger.info(f"Attempting fallback to {fallback_channel} for {self.business_unit.name}")
                    fallback_handler = self.notification_handlers.get(fallback_channel, self.notification_handlers.get('default'))
                    try:
                        fallback_handler(message, person)
                        logger.info(f"Notification sent via fallback {fallback_channel} for {self.business_unit.name}")
                    except Exception as fallback_e:
                        logger.error(f"Error sending notification via fallback {fallback_channel}: {str(fallback_e)}")
                else:
                    logger.warning(f"No fallback channel available for {channel}")
        else:
            logger.warning(f"No notification handler found for channel: {channel}")

    def _get_fallback_channel(self, failed_channel: str) -> str:
        """
        Determina un canal alternativo en caso de que el canal inicial falle.

        Args:
            failed_channel (str): Canal que falló.

        Returns:
            str: Canal alternativo, o vacío si no hay alternativa.
        """
        fallback_options = {
            'whatsapp': 'telegram',
            'telegram': 'email',
            'sms': 'email',
            'email': 'default'
        }
        return fallback_options.get(failed_channel, '')

    def trigger_alert(self, alert_type: str, message: str, person: Person = None):
        """
        Dispara una alerta basada en el tipo especificado.
        Selecciona el manejador adecuado basado en el tipo de alerta y la unidad de negocio.

        Args:
            alert_type (str): Tipo de alerta a disparar.
            message (str): Mensaje de la alerta.
            person (Person, optional): Persona asociada con la alerta.
        """
        handler = self.alert_handlers.get(alert_type, self.alert_handlers.get('default'))
        if handler:
            try:
                handler(message, person)
                logger.info(f"Alert triggered of type {alert_type} for {self.business_unit.name}")
            except Exception as e:
                logger.error(f"Error triggering alert of type {alert_type}: {str(e)}")
        else:
            logger.warning(f"No alert handler found for type: {alert_type}")

    def _send_whatsapp_notification(self, message: str, person: Person = None):
        """Simula el envío de una notificación por WhatsApp. Verifica limitaciones."""
        # Implementación específica para WhatsApp
        # Simulación de verificación de limitaciones (ejemplo: conversación no iniciada por destinatario)
        if person and not hasattr(person, 'whatsapp_conversation_started') or not getattr(person, 'whatsapp_conversation_started', False):
            raise Exception("WhatsApp conversation not initiated by recipient")
        logger.info(f"WhatsApp notification: {message} to {person.nombre if person else 'N/A'}")

    def _send_telegram_notification(self, message: str, person: Person = None):
        """Simula el envío de una notificación por Telegram."""
        # Implementación específica para Telegram
        logger.info(f"Telegram notification: {message} to {person.nombre if person else 'N/A'}")

    def _send_email_notification(self, message: str, person: Person = None):
        """Simula el envío de una notificación por Email."""
        # Implementación específica para Email
        logger.info(f"Email notification: {message} to {person.email if person else 'N/A'}")

    def _send_sms_notification(self, message: str, person: Person = None):
        """Simula el envío de una notificación por SMS."""
        # Implementación específica para SMS
        logger.info(f"SMS notification: {message} to {person.telefono if person else 'N/A'}")

    def _send_default_notification(self, message: str, person: Person = None):
        """Método por defecto para enviar notificaciones."""
        logger.info(f"Default notification: {message} to {person.nombre if person else 'N/A'}")

    def _handle_urgent_alert(self, message: str, person: Person = None):
        """Maneja alertas urgentes."""
        logger.warning(f"Urgent alert: {message} for {person.nombre if person else 'N/A'}")

    def _handle_standard_alert(self, message: str, person: Person = None):
        """Maneja alertas estándar."""
        logger.info(f"Standard alert: {message} for {person.nombre if person else 'N/A'}")

    def _handle_info_alert(self, message: str, person: Person = None):
        """Maneja alertas informativas."""
        logger.info(f"Info alert: {message} for {person.nombre if person else 'N/A'}")

    def _handle_default_alert(self, message: str, person: Person = None):
        """Maneja alertas por defecto."""
        logger.info(f"Default alert: {message} for {person.nombre if person else 'N/A'}")
