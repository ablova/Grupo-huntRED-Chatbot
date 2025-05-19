"""
Integración de Valores Fundamentales en el Flujo del Chatbot.

Este módulo proporciona las clases y funciones necesarias para integrar
los valores fundamentales del Grupo huntRED® en el flujo de trabajo del chatbot.
"""

import logging
from asgiref.sync import sync_to_async
from django.utils import timezone

from app.com.chatbot.core.values import ValuesIntegrator, ValuesPrinciples

logger = logging.getLogger(__name__)


class ValuesChatMiddleware:
    """
    Middleware que integra los valores fundamentales en el flujo de procesamiento
    de mensajes del chatbot.
    """
    
    @classmethod
    async def process_message(cls, message_text, user_data, state_manager):
        """
        Procesa un mensaje entrante integrando los valores fundamentales.
        
        Args:
            message_text: Texto del mensaje del usuario
            user_data: Datos del usuario
            state_manager: Instancia de ChatStateManager
            
        Returns:
            Mensaje procesado con metadatos de valores
        """
        # Obtener metadatos de valores
        values_metadata = await ValuesIntegrator.process_incoming_message(
            message_text, 
            user_data
        )
        
        # Almacenar los metadatos en el contexto de la conversación
        if state_manager and hasattr(state_manager, 'context'):
            if not 'values' in state_manager.context:
                state_manager.context['values'] = {}
                
            state_manager.context['values'].update({
                'emotional_context': values_metadata.get('emotional_context', 'neutral'),
                'career_stage': values_metadata.get('career_stage', 'exploring'),
                'value_opportunities': values_metadata.get('value_opportunities', []),
                'last_updated': timezone.now().isoformat()
            })
        
        return {
            'original_text': message_text,
            'values_metadata': values_metadata
        }
    
    @classmethod
    async def enhance_response(cls, original_response, state_manager=None):
        """
        Mejora una respuesta del chatbot integrando los valores fundamentales.
        
        Args:
            original_response: Respuesta original del chatbot
            state_manager: Instancia de ChatStateManager (opcional)
            
        Returns:
            Respuesta mejorada que refleja los valores fundamentales
        """
        values_metadata = {}
        
        # Obtener los metadatos del contexto de la conversación si están disponibles
        if state_manager and hasattr(state_manager, 'context') and 'values' in state_manager.context:
            values_metadata = state_manager.context.get('values', {})
        
        # Aplicar valores a la respuesta
        enhanced_response = await ValuesIntegrator.apply_values_to_response(
            original_response,
            values_metadata
        )
        
        return enhanced_response


class ChatStateValuesExtension:
    """
    Extensión para ChatStateManager que integra los valores fundamentales
    en el flujo de procesamiento de mensajes y respuestas.
    """
    
    @classmethod
    async def extend_state_manager(cls, state_manager):
        """
        Extiende el ChatStateManager con funcionalidades de valores.
        
        Args:
            state_manager: Instancia de ChatStateManager a extender
        """
        # Asegurarse de que exista la sección de valores en el contexto
        if not hasattr(state_manager, 'context'):
            state_manager.context = {}
            
        if not 'values' in state_manager.context:
            state_manager.context['values'] = {
                'emotional_context': 'neutral',
                'career_stage': 'exploring',
                'value_opportunities': [],
                'last_updated': timezone.now().isoformat()
            }
        
        # Extender el método de procesamiento de mensajes
        original_process_message = state_manager.process_message
        
        async def extended_process_message(message_text, *args, **kwargs):
            # Procesar valores
            processed = await ValuesChatMiddleware.process_message(
                message_text, 
                {'user': state_manager.user, 'bu': state_manager.business_unit},
                state_manager
            )
            
            # Llamar al método original
            result = await original_process_message(processed['original_text'], *args, **kwargs)
            
            return result
        
        # Reemplazar el método
        state_manager.process_message = extended_process_message
        
        # Extender el método de generación de respuestas si existe
        if hasattr(state_manager, 'generate_response'):
            original_generate_response = state_manager.generate_response
            
            async def extended_generate_response(*args, **kwargs):
                # Llamar al método original
                original_response = await original_generate_response(*args, **kwargs)
                
                # Mejorar la respuesta con valores
                enhanced_response = await ValuesChatMiddleware.enhance_response(
                    original_response,
                    state_manager
                )
                
                return enhanced_response
            
            # Reemplazar el método
            state_manager.generate_response = extended_generate_response
        
        logger.info(f"ChatStateManager extended with values functionality for user {state_manager.user.id}")
        
        return state_manager
