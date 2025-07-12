# /home/pablo/app/ats/integrations/chatbot_integration.py
from django.conf import settings
from django.core.cache import cache
from django.db import transaction
import logging
from typing import Dict, Any, Optional, List
from app.models import Conversation, ChatMessage, Notification, Person, BusinessUnit, Vacante 
from app.tasks import process_message, send_notification
from app.ats.utils.report_generator import ReportGenerator
from app.ats.chatbot.components.chat_state_manager import ChatStateManager
from app.ats.chatbot.components.context_manager import ConversationContext as ContextManager
from app.ats.chatbot.flow.conversational_flow import ConversationalFlowManager
from app.ats.chatbot.core.intents_handler import IntentHandler
from app.ats.chatbot.nlp.nlp import NLPProcessor
from app.ats.chatbot.core.gpt import GPTHandler
from app.ats.chatbot.workflow.common.common import get_possible_transitions, process_business_unit_transition
from app.ats.chatbot.workflow.business_units.huntred.huntred import process_huntred_candidate
from app.ats.chatbot.workflow.business_units.huntred_executive import process_huntred_executive_candidate
from app.ats.chatbot.workflow.business_units.huntu.huntu import process_huntu_candidate
from app.ats.chatbot.workflow.business_units.amigro.amigro import process_amigro_candidate
from app.ats.chatbot.workflow.business_units.sexsi.sexsi import process_sexsi_payment

# Integración con nuevas funcionalidades ML
from app.ml.core.job_description_generator import JobDescriptionGenerator
from app.ml.core.cv_analyzer import CVAnalyzer

logger = logging.getLogger('app.ats.integrations.chatbot_integration')

class ChatbotIntegration:
    """Clase para gestionar la integración entre el módulo de comunicaciones y el chatbot."""
    
    def __init__(self):
        self.chat_state_manager = ChatStateManager()
        self.context_manager = ContextManager()
        self.conversational_flow = ConversationalFlowManager()
        self.intent_handler = IntentHandler()
        self.nlp_processor = NLPProcessor()
        self.gpt_handler = GPTHandler()
        
        # Inicializar nuevas funcionalidades ML
        self.job_generator = JobDescriptionGenerator()
        self.cv_analyzer = CVAnalyzer()
        
    def process_incoming_message(self, recipient_id: str, message: str, channel: str) -> Dict[str, Any]:
        """
        Procesa un mensaje entrante y gestiona la conversación.
        
        Args:
            recipient_id: ID del destinatario
            message: Contenido del mensaje
            channel: Canal de comunicación
        
        Returns:
            Dict[str, Any]: Resultado del procesamiento
        """
        try:
            with transaction.atomic():
                # Obtener o crear conversación
                conversation = self._get_or_create_conversation(recipient_id, channel)
                
                # Obtener usuario y unidad de negocio
                person = Person.objects.get(id=recipient_id)
                business_unit = person.business_unit
                
                # Actualizar contexto
                context = self.context_manager.update_context(
                    person,
                    message,
                    channel
                )
                
                # Procesar intención
                intent = self.intent_handler.process_intent(message)
                
                # Procesar mensaje según unidad de negocio
                response = self._process_message_by_business_unit(
                    person,
                    business_unit,
                    message,
                    intent,
                    context
                )
                
                # Actualizar estado
                new_state = self.chat_state_manager.update_state(
                    conversation.state,
                    intent,
                    business_unit
                )
                
                # Crear mensaje
                ChatMessage.objects.create(
                    conversation=conversation,
                    content=message,
                    direction='in',
                    status='received',
                    intent=intent
                )
                
                # Procesar mensaje
                process_message.delay(
                    conversation.id,
                    response,
                    channel,
                    business_unit
                )
                
                # Actualizar métricas
                ReportGenerator().generate_conversation_metrics(
                    conversation,
                    message,
                    response,
                    intent
                )
                
                return {
                    'success': True,
                    'conversation_id': conversation.id,
                    'state': new_state,
                    'response': response,
                    'intent': intent
                }
                
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _process_message_by_business_unit(self, person: Person, business_unit: BusinessUnit, 
                                        message: str, intent: str, context: Dict[str, Any]) -> str:
        """Procesa el mensaje según la unidad de negocio."""
        bu_name = business_unit.name.lower()
        
        if bu_name == 'huntred':
            return self._process_huntred_message(person, message, intent, context)
        elif bu_name == 'huntu':
            return self._process_huntu_message(person, message, intent, context)
        elif bu_name == 'sexsi':
            return self._process_sexsi_message(person, message, intent, context)
        else:
            return self._process_common_message(person, message, intent, context)
    
    def _process_huntred_message(self, person: Person, message: str, intent: str, context: Dict[str, Any]) -> str:
        """Procesa mensajes específicos para HuntRED."""
        if intent == 'payment':
            return process_huntred_candidate(person.id)
        elif intent == 'contract':
            return self.conversational_flow.generate_contract_response(person, context)
        return self._process_common_message(person, message, intent, context)
    
    def _process_huntu_message(self, person: Person, message: str, intent: str, context: Dict[str, Any]) -> str:
        """Procesa mensajes específicos para Huntu."""
        if intent == 'internship':
            return process_huntu_candidate(person.id)
        elif intent == 'resume_review':
            return self.conversational_flow.generate_resume_review_response(person, context)
        return self._process_common_message(person, message, intent, context)
    
    def _process_sexsi_message(self, person: Person, message: str, intent: str, context: Dict[str, Any]) -> str:
        """Procesa mensajes específicos para SEXSI."""
        if intent == 'payment':
            return process_sexsi_payment(person, context.get('amount'))
        elif intent == 'contract':
            return self.conversational_flow.generate_sexsi_contract_response(person, context)
        return self._process_common_message(person, message, intent, context)
    
    def _process_common_message(self, person: Person, message: str, intent: str, context: Dict[str, Any]) -> str:
        """Procesa mensajes comunes para todas las unidades de negocio."""
        # Procesar con GPT si es necesario
        if intent == 'complex_query':
            return self.gpt_handler.generate_response(message, person.business_unit)
            
        # Procesar con NLP para extraer información relevante
        nlp_result = self.nlp_processor.analyze(message)
        context.update(nlp_result)
        
        # Generar respuesta basada en el flujo conversacional
        return self.conversational_flow.generate_response(
            person,
            intent,
            context
        )
    
    def _get_or_create_conversation(self, recipient_id: str, channel: str) -> Conversation:
        """Obtiene o crea una conversación."""
        person = Person.objects.get(id=recipient_id)
        business_unit = person.business_unit
        
        # Obtener estado inicial según la unidad de negocio
        initial_state = self._get_initial_state(business_unit)
        
        conversation, created = Conversation.objects.get_or_create(
            recipient=person,
            channel=channel,
            defaults={'state': initial_state}
        )
        
        # Si la conversación ya existía, verificar si necesita una transición
        if not created:
            possible_transitions = get_possible_transitions(person, business_unit)
            if possible_transitions:
                new_bu = possible_transitions[0]  # Tomar la primera unidad posible
                process_business_unit_transition(person.id, new_bu)
                conversation.state = self._get_initial_state(new_bu)
                conversation.save()
        
        return conversation
    
    def _get_initial_state(self, business_unit: BusinessUnit) -> str:
        """Obtiene el estado inicial según la unidad de negocio."""
        bu_name = business_unit.name.lower()
        if bu_name == 'huntred':
            return 'PERFIL_GERENCIAL'
        elif bu_name == 'huntu':
            return 'PERFIL_ESTUDIANTE'
        elif bu_name == 'sexsi':
            return 'PERFIL_SEXSI'
        return 'PERFIL'
    
    def send_notification(self, recipient_id: str, notification_type: str, content: str) -> bool:
        """
        Envía una notificación al destinatario.
        
        Args:
            recipient_id: ID del destinatario
            notification_type: Tipo de notificación
            content: Contenido de la notificación
        
        Returns:
            bool: True si la notificación fue enviada exitosamente
        """
        try:
            # Obtener configuración del destinatario
            recipient_config = self._get_recipient_config(recipient_id)
            
            # Determinar canal preferido
            preferred_channel = self._get_preferred_channel(
                recipient_config,
                notification_type
            )
            
            # Enviar notificación
            send_notification.delay(
                recipient_id,
                notification_type,
                preferred_channel,
                content
            )
            
            # Actualizar métricas de notificación
            ReportGenerator().generate_notification_metrics(
                recipient_id,
                notification_type,
                preferred_channel
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending notification: {str(e)}")
            return False
    
    def _get_recipient_config(self, recipient_id: str) -> Dict[str, Any]:
        """Obtiene la configuración del destinatario."""
        person = Person.objects.get(id=recipient_id)
        return {
            'channels': person.get_preferred_channels(),
            'notification_types': person.get_notification_types(),
            'business_unit': person.business_unit.name,
            'preferences': person.preferences or {}
        }
    
    def _get_preferred_channel(self, config: dict, notification_type: str) -> str:
        """Determina el canal preferido para una notificación."""
        for channel in config['channels']:
            if notification_type in config['notification_types']:
                return channel
        return 'email'  # Canal por defecto
    
    def handle_verification(self, recipient_id: str, code: str) -> bool:
        """
        Maneja la verificación de un destinatario.
        
        Args:
            recipient_id: ID del destinatario
            code: Código de verificación
        
        Returns:
            bool: True si la verificación fue exitosa
        """
        try:
            person = Person.objects.get(id=recipient_id)
            
            # Verificar código
            if not self._verify_code(person, code):
                return False
                
            # Actualizar estado de verificación
            person.is_verified = True
            person.save()
            
            # Iniciar flujo de conversación
            self._initiate_conversation_flow(person)
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling verification: {str(e)}")
            return False
    
    def _verify_code(self, person: Person, code: str) -> bool:
        """Verifica el código de verificación."""
        cached_code = cache.get(f'verification_code_{person.id}')
        return cached_code == code
    
    def _initiate_conversation_flow(self, person: Person) -> None:
        """Inicia el flujo de conversación para un destinatario verificado."""
        try:
            # Crear conversación
            conversation = Conversation.objects.create(
                recipient=person,
                channel='email',
                state=self._get_initial_state(person.business_unit)
            )
            
            # Enviar mensaje de bienvenida según la unidad de negocio
            bu_name = person.business_unit.name.lower()
            if bu_name == 'huntred':
                message = "¡Bienvenido a HuntRED! 💼 Especializamos en roles gerenciales clave. Vamos a crear tu perfil."
            elif bu_name == 'huntu':
                message = "¡Bienvenido a Huntu! 🏆 Conectamos talento joven con oportunidades de alto impacto. Vamos a crear tu perfil."
            elif bu_name == 'sexsi':
                message = "¡Bienvenido a SEXSI! 📜 Creando contratos consensuados para relaciones sexuales seguras y legales."
            else:
                message = "¡Hola! Tu registro ha sido verificado exitosamente. Vamos a completar tu perfil."
            
            process_message.delay(
                conversation.id,
                message,
                'email',
                person.business_unit
            )
            
        except Exception as e:
            logger.error(f"Error initiating conversation flow: {str(e)}")

    async def handle_recruitment_assistant_request(
        self,
        user_id: str,
        request_type: str,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Maneja solicitudes del asistente de reclutamiento.
        
        Args:
            user_id: ID del usuario
            request_type: Tipo de solicitud
            context: Contexto adicional
            
        Returns:
            Dict con respuesta y datos
        """
        try:
            if request_type == 'generate_job_description':
                return await self._handle_job_description_generation(context)
            
            elif request_type == 'analyze_cv':
                return await self._handle_cv_analysis(context)
            
            elif request_type == 'compare_candidates':
                return await self._handle_candidate_comparison(context)
            
            elif request_type == 'generate_interview_questions':
                return await self._handle_interview_questions_generation(context)
            
            elif request_type == 'get_market_insights':
                return await self._handle_market_insights(context)
            
            else:
                return {
                    'success': False,
                    'error': f'Tipo de solicitud no reconocido: {request_type}'
                }
                
        except Exception as e:
            logger.error(f"Error manejando solicitud de asistente: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    async def _handle_job_description_generation(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Maneja la generación de descripción de puesto."""
        try:
            position = context.get('position')
            requirements = context.get('requirements', [])
            location = context.get('location', 'No especificado')
            experience_level = context.get('experience_level', 'mid')
            
            if not position:
                return {
                    'success': False,
                    'error': 'Se requiere el título del puesto'
                }
            
            # Generar descripción
            result = await self.job_generator.generate_job_description(
                position=position,
                requirements=requirements,
                location=location,
                experience_level=experience_level
            )
            
            return {
                'success': True,
                'data': result,
                'message': f'Descripción generada para: {position}'
            }
            
        except Exception as e:
            logger.error(f"Error generando descripción: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    async def _handle_cv_analysis(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Maneja el análisis de CV."""
        try:
            cv_text = context.get('cv_text')
            position = context.get('position')
            candidate_id = context.get('candidate_id')
            
            if not cv_text:
                return {
                    'success': False,
                    'error': 'Se requiere el contenido del CV'
                }
            
            # Analizar CV
            result = await self.cv_analyzer.analyze_cv(
                cv_text=cv_text,
                position=position,
                candidate_id=candidate_id
            )
            
            return {
                'success': True,
                'data': result,
                'message': 'Análisis de CV completado'
            }
            
        except Exception as e:
            logger.error(f"Error analizando CV: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    async def _handle_candidate_comparison(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Maneja la comparación de candidatos."""
        try:
            cv_analyses = context.get('cv_analyses', [])
            position = context.get('position')
            
            if not cv_analyses or not position:
                return {
                    'success': False,
                    'error': 'Se requieren análisis de CV y posición'
                }
            
            # Comparar candidatos
            result = await self.cv_analyzer.compare_candidates(
                cv_analyses=cv_analyses,
                position=position
            )
            
            return {
                'success': True,
                'data': result,
                'message': 'Comparación de candidatos completada'
            }
            
        except Exception as e:
            logger.error(f"Error comparando candidatos: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    async def _handle_interview_questions_generation(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Maneja la generación de preguntas de entrevista."""
        try:
            candidate_info = context.get('candidate_info', {})
            position = context.get('position')
            question_type = context.get('question_type', 'technical')
            
            if not candidate_info or not position:
                return {
                    'success': False,
                    'error': 'Se requiere información del candidato y posición'
                }
            
            # Generar preguntas
            result = await self.cv_analyzer.generate_interview_questions(
                candidate_info=candidate_info,
                position=position,
                question_type=question_type
            )
            
            return {
                'success': True,
                'data': result,
                'message': 'Preguntas de entrevista generadas'
            }
            
        except Exception as e:
            logger.error(f"Error generando preguntas: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    async def _handle_market_insights(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Maneja la obtención de insights de mercado."""
        try:
            position = context.get('position')
            location = context.get('location')
            
            if not position:
                return {
                    'success': False,
                    'error': 'Se requiere el título del puesto'
                }
            
            # Obtener insights
            result = await self.job_generator.get_market_insights(
                position=position,
                location=location
            )
            
            return {
                'success': True,
                'data': result,
                'message': 'Insights de mercado obtenidos'
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo insights: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    async def notify_ideal_candidate_selected(
        self,
        selected_candidate: Person,
        vacancy: Vacante,
        other_candidates: List[Person],
        selection_reason: str = None
    ) -> bool:
        """
        Notifica cuando se identifica el candidato ideal y agradece/descarta al resto.
        Integra con el sistema de notificaciones existente.
        """
        try:
            # Usar el sistema de notificaciones existente
            from app.ats.integrations.notifications.process.offer_notifications import OfferNotificationService
            
            notification_service = OfferNotificationService(self.business_unit)
            
            success = await notification_service.notify_ideal_candidate_selected(
                selected_candidate=selected_candidate,
                vacancy=vacancy,
                other_candidates=other_candidates,
                selection_reason=selection_reason
            )
            
            if success:
                logger.info(f"Candidato ideal seleccionado: {selected_candidate.full_name}")
                
                # Actualizar métricas
                await self._update_recruitment_metrics(
                    vacancy_id=vacancy.id,
                    selected_candidate_id=selected_candidate.id,
                    total_candidates=len(other_candidates) + 1
                )
            
            return success
            
        except Exception as e:
            logger.error(f"Error notificando candidato ideal: {str(e)}")
            return False

    async def _update_recruitment_metrics(
        self,
        vacancy_id: int,
        selected_candidate_id: int,
        total_candidates: int
    ):
        """Actualiza métricas de reclutamiento."""
        try:
            # Aquí se integraría con el sistema de métricas existente
            # Por ahora, solo logging
            logger.info(f"Métricas actualizadas - Vacante: {vacancy_id}, Candidato: {selected_candidate_id}, Total: {total_candidates}")
            
        except Exception as e:
            logger.error(f"Error actualizando métricas: {str(e)}")
