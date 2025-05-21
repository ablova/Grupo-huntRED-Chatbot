"""
Módulo de Integración de Valores para el Chatbot.

Proporciona las clases y funciones necesarias para integrar los valores fundamentales
del Grupo huntRED® en el flujo de trabajo del chatbot, incluyendo middlewares y
extensiones para el manejo de estados.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from django.utils import timezone
from asgiref.sync import sync_to_async

from .core import ValuesPrinciples, UserPreferencesCache

logger = logging.getLogger(__name__)


class ValuesChatMiddleware:
    """
    Middleware que integra los valores fundamentales en el flujo de procesamiento
    de mensajes del chatbot.
    """
    
    def __init__(self, values_principles: Optional[ValuesPrinciples] = None):
        """Inicializa el middleware con una instancia de ValuesPrinciples."""
        self.values_principles = values_principles or ValuesPrinciples()
    
    async def process_message(self, message_text: str, user_data: Dict[str, Any], 
                            state_manager: Any = None) -> Dict[str, Any]:
        """
        Procesa un mensaje entrante integrando los valores fundamentales.
        
        Args:
            message_text: Texto del mensaje del usuario
            user_data: Datos del usuario para personalización
            state_manager: Instancia opcional de ChatStateManager
            
        Returns:
            Dict con el mensaje procesado y metadatos de valores
        """
        # Detectar contexto emocional
        emotional_context = await self.values_principles.detect_emotional_context(message_text)
        
        # Obtener etapa profesional (si está disponible en user_data o state_manager)
        career_stage = await self._detect_career_stage(message_text, user_data, state_manager)
        
        # Identificar oportunidades de valor
        value_opportunities = await self._identify_value_opportunities(
            message_text, emotional_context, career_stage
        )
        
        # Preparar metadatos de valores
        values_metadata = {
            'emotional_context': emotional_context,
            'career_stage': career_stage,
            'value_opportunities': value_opportunities,
            'timestamp': timezone.now().isoformat()
        }
        
        # Almacenar en el contexto de la conversación si hay un state_manager
        if state_manager and hasattr(state_manager, 'context'):
            if not hasattr(state_manager.context, 'values'):
                state_manager.context.values = {}
            state_manager.context.values.update(values_metadata)
        
        return {
            'original_text': message_text,
            'values_metadata': values_metadata
        }
    
    async def enhance_response(self, original_response: str, 
                             values_metadata: Dict[str, Any] = None) -> str:
        """
        Mejora una respuesta del chatbot integrando los valores fundamentales.
        
        Args:
            original_response: Respuesta original del chatbot
            values_metadata: Metadatos de valores previamente procesados
            
        Returns:
            str: Respuesta mejorada con valores integrados
        """
        if not values_metadata:
            return original_response
            
        emotional_context = values_metadata.get('emotional_context', 'neutral')
        return await self.values_principles.enhance_response(
            original_response, 
            emotional_context
        )
    
    async def _detect_career_stage(self, message_text: str, 
                                 user_data: Dict[str, Any] = None,
                                 state_manager: Any = None) -> str:
        """
        Detecta la etapa profesional del usuario basándose en el mensaje y datos disponibles.
        
        Args:
            message_text: Texto del mensaje del usuario
            user_data: Datos del usuario
            state_manager: Instancia opcional de ChatStateManager
            
        Returns:
            str: Identificador de la etapa profesional detectada
        """
        # Implementación básica - en una implementación real, esto podría ser más sofisticado
        # y considerar datos del perfil del usuario, historial de interacciones, etc.
        
        # Palabras clave para cada etapa profesional
        career_stage_keywords = {
            'exploring': ['carrera', 'iniciar', 'empezar', 'nuevo', 'primera vez'],
            'early': ['primer empleo', 'recién graduado', 'sin experiencia', 'júnior'],
            'mid': ['experiencia', 'cambio', 'crecer', 'desarrollar', 'avanzar'],
            'senior': ['liderar', 'equipo', 'gerente', 'director', 'estrategia'],
            'executive': ['ejecutivo', 'CEO', 'CTO', 'gerente general', 'alta dirección']
        }
        
        # Buscar palabras clave en el mensaje
        message_lower = message_text.lower()
        for stage, keywords in career_stage_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                return stage
        
        # Si no se detecta, usar 'exploring' como valor por defecto
        return 'exploring'
    
    async def _identify_value_opportunities(self, message_text: str, 
                                          emotional_context: str,
                                          career_stage: str) -> list:
        """
        Identifica oportunidades para integrar valores en la respuesta.
        
        Args:
            message_text: Texto del mensaje del usuario
            emotional_context: Contexto emocional detectado
            career_stage: Etapa profesional del usuario
            
        Returns:
            list: Lista de oportunidades de valor identificadas
        """
        opportunities = []
        
        # Oportunidades basadas en el contexto emocional
        if emotional_context == 'job_search_frustration':
            opportunities.extend(['support', 'motivation', 'perspective'])
        elif emotional_context == 'career_uncertainty':
            opportunities.extend(['guidance', 'clarity', 'exploration'])
        elif emotional_context == 'achievement_moment':
            opportunities.extend(['celebration', 'next_steps', 'growth'])
        elif emotional_context == 'skills_development':
            opportunities.extend(['learning', 'resources', 'skill_mapping'])
        
        # Oportunidades basadas en la etapa profesional
        if career_stage in ['exploring', 'early']:
            opportunities.extend(['career_guidance', 'skill_development', 'networking'])
        elif career_stage in ['mid', 'senior']:
            opportunities.extend(['leadership', 'mentoring', 'strategic_thinking'])
        elif career_stage == 'executive':
            opportunities.extend(['executive_development', 'thought_leadership', 'innovation'])
        
        # Eliminar duplicados manteniendo el orden
        return list(dict.fromkeys(opportunities))
