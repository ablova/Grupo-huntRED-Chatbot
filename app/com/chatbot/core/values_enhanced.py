"""
Módulo Mejorado de Valores Fundamentales para el Chatbot.

Combina los enfoques de detección contextual de valores con un sistema
de caché en memoria para preferencias de usuario, permitiendo una personalización
más efectiva de las interacciones basadas en los valores de asistencia, solidaridad,
sinergia y pasión auténtica.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from asgiref.sync import sync_to_async
from django.utils import timezone

from app.com.chatbot.core.values import ValuesPrinciples

# Configuración de logging para trazabilidad eficiente
logger = logging.getLogger(__name__)


class UserPreferencesCache:
    """
    Caché en memoria para preferencias de usuario que optimiza
    la personalización de mensajes basados en valores.
    """
    def __init__(self):
        self._cache: Dict[str, Dict] = {}
        self._max_entries = 10000  # Prevenir crecimiento excesivo
        self._pruning_threshold = 0.9  # Umbral de limpieza (90%)
    
    def get(self, user_id: str) -> Optional[Dict]:
        """Obtiene las preferencias de un usuario."""
        return self._cache.get(str(user_id))
    
    def set(self, user_id: str, preferences: Dict) -> None:
        """
        Establece las preferencias de un usuario con manejo de capacidad
        para optimizar el uso de memoria.
        """
        # Pruning preventivo si se acerca al límite
        if len(self._cache) > self._max_entries * self._pruning_threshold:
            self._prune_cache()
        
        # Actualizar preferencias
        self._cache[str(user_id)] = preferences
    
    def update(self, user_id: str, updates: Dict) -> Dict:
        """Actualiza las preferencias de un usuario preservando datos existentes."""
        user_id = str(user_id)
        current = self._cache.get(user_id, {})
        current.update(updates)
        self._cache[user_id] = current
        return current
    
    def _prune_cache(self) -> None:
        """
        Elimina entradas menos recientes para mantener el tamaño del caché.
        Optimizado para CPU y se ejecuta solo cuando es necesario.
        """
        if len(self._cache) <= self._max_entries * 0.8:  # Margen de seguridad
            return
            
        # Ordenar por timestamp de última interacción
        entries = [(k, v.get('last_interaction', datetime.min)) for k, v in self._cache.items()]
        entries.sort(key=lambda x: x[1])
        
        # Eliminar el 20% más antiguo
        cutoff = int(len(entries) * 0.2)
        for i in range(cutoff):
            if i < len(entries):
                del self._cache[entries[i][0]]
        
        logger.info(f"Cache pruning completed: removed {cutoff} entries")


class EnhancedValuesIntegration:
    """
    Integración mejorada de valores fundamentales combinando detección contextual
    con personalización basada en preferencias de usuario.
    """
    
    def __init__(self):
        # Caché de preferencias para optimizar rendimiento
        self.user_preferences = UserPreferencesCache()
        
        # Mensajes predefinidos por contexto
        self.context_messages = {
            'career': [
                "Estamos aquí para impulsar tu carrera profesional con pasión y compromiso.",
                "Juntos construiremos un camino sólido para tu crecimiento profesional.",
                "Tu éxito profesional es nuestra prioridad, caminamos juntos en este proceso."
            ],
            'operational': [
                "Nuestra sinergia optimizará tus operaciones con pasión y compromiso.",
                "Trabajamos en equipo para potenciar la eficiencia de tus procesos.",
                "Cada detalle operativo es importante para nosotros como lo es para ti."
            ],
            'recruitment': [
                "Reclutamos con pasión, buscando el mejor talento para transformar tu organización.",
                "El proceso de selección es un camino que recorremos juntos, con apoyo constante.",
                "Cada candidato representa una oportunidad de sinergia y crecimiento mutuo."
            ],
            'network': [
                "Las conexiones profesionales que creamos juntos son el cimiento de un futuro exitoso.",
                "Nuestra red es tu red, construyendo puentes para oportunidades destacadas.",
                "Creamos relaciones auténticas, no solo contactos profesionales."
            ]
        }
        
        # Mensajes de respaldo para contextos no específicos
        self.support_messages = [
            "Estamos aquí para apoyarte en cada paso de tu camino profesional.",
            "Nuestra pasión es construir sinergias que impulsen tu desarrollo.",
            "El éxito compartido es nuestra meta, trabajamos juntos para lograrlo.",
            "Cada interacción es una oportunidad para crecer y avanzar juntos.",
            "Tu crecimiento profesional es el motor que impulsa nuestro compromiso."
        ]
    
    async def get_personalized_message(self, user_id: str, context: str, emotional_context: str = 'neutral') -> str:
        """
        Genera un mensaje personalizado basado en el contexto y las preferencias del usuario,
        optimizado para reflejar los valores fundamentales.
        
        Args:
            user_id (str): Identificador del usuario
            context (str): Contexto de la interacción
            emotional_context (str): Contexto emocional detectado
            
        Returns:
            str: Mensaje personalizado con valores integrados
        """
        try:
            # Obtener o inicializar preferencias
            user_data = self.user_preferences.get(user_id) or {}
            
            # Determinar contexto específico
            specific_context = context.lower()
            if specific_context not in self.context_messages:
                specific_context = 'career'  # Default a contexto de carrera
            
            # Seleccionar mensaje según contexto y personalización
            message_pool = self.context_messages.get(specific_context, self.support_messages)
            
            # Selección pseudo-aleatoria pero determinista basada en ID y fecha
            message_index = (hash(str(user_id) + datetime.now().strftime('%Y-%m-%d')) % len(message_pool))
            message = message_pool[message_index]
            
            # Enriquecer según contexto emocional si no es neutral
            if emotional_context != 'neutral':
                message = await self._enhance_for_emotional_context(message, emotional_context)
            
            # Actualizar preferencias
            timestamp = timezone.now()
            self.user_preferences.update(user_id, {
                'last_context': specific_context,
                'last_interaction': timestamp,
                'emotional_context': emotional_context,
                'messages_count': user_data.get('messages_count', 0) + 1
            })
            
            return message
            
        except Exception as e:
            logger.error(f"Error en get_personalized_message: {str(e)}")
            return "Estamos aquí para apoyarte en tu desarrollo profesional."
    
    async def _enhance_for_emotional_context(self, message: str, emotional_context: str) -> str:
        """
        Enriquece un mensaje según el contexto emocional detectado.
        
        Args:
            message (str): Mensaje base
            emotional_context (str): Contexto emocional
            
        Returns:
            str: Mensaje enriquecido para el contexto emocional
        """
        if emotional_context == 'job_search_frustration':
            return f"Entendemos que la búsqueda puede ser desafiante a veces. {message}"
        elif emotional_context == 'career_uncertainty':
            return f"En momentos de incertidumbre, estamos aquí para orientarte. {message}"
        elif emotional_context == 'achievement_moment':
            return f"¡Felicidades por este logro! {message}"
        else:
            return message
    
    async def enhance_response(self, 
                            original_response: str, 
                            user_id: str, 
                            context: str = 'career',
                            values_metadata: Dict = None) -> str:
        """
        Mejora una respuesta del sistema integrando valores fundamentales
        de manera personalizada según el usuario y contexto.
        
        Args:
            original_response (str): Respuesta original
            user_id (str): ID del usuario
            context (str): Contexto de la interacción
            values_metadata (Dict): Metadatos de valores detectados
            
        Returns:
            str: Respuesta mejorada con valores integrados
        """
        try:
            emotional_context = 'neutral'
            if values_metadata and 'emotional_context' in values_metadata:
                emotional_context = values_metadata['emotional_context']
            
            # Obtener mensaje personalizado
            value_message = await self.get_personalized_message(
                user_id, 
                context, 
                emotional_context
            )
            
            # Solo usar ValuesPrinciples para modificaciones sutiles cuando sea necesario
            if len(original_response) < 50:
                # Para respuestas cortas, añadir mensaje al final
                return f"{original_response} {value_message}"
            else:
                # Para respuestas largas, mejor usar las modificaciones sutiles
                return await ValuesPrinciples.enhance_response(
                    original_response,
                    emotional_context
                )
                
        except Exception as e:
            logger.error(f"Error en enhance_response: {str(e)}")
            return original_response
    
    async def track_interaction(self, user_id: str, interaction_data: Dict[str, Any]) -> None:
        """
        Registra datos de interacción para mejorar personalización futura.
        Optimizado para rendimiento con actualizaciones asíncronas.
        
        Args:
            user_id (str): ID del usuario
            interaction_data (Dict): Datos de la interacción
        """
        try:
            # Obtener preferencias actuales
            current = self.user_preferences.get(user_id) or {}
            
            # Actualizar historial de interacciones de manera eficiente
            interactions = current.get('interactions', [])
            interactions.append({
                'timestamp': timezone.now().isoformat(),
                'type': interaction_data.get('type', 'message'),
                'context': interaction_data.get('context', 'general'),
                'success': interaction_data.get('success', True)
            })
            
            # Limitar tamaño del historial
            if len(interactions) > 20:
                interactions = interactions[-20:]
            
            # Actualizar preferencias
            self.user_preferences.update(user_id, {
                'interactions': interactions,
                'last_interaction': timezone.now(),
                'interaction_count': current.get('interaction_count', 0) + 1
            })
            
        except Exception as e:
            logger.error(f"Error en track_interaction: {str(e)}")


# Instancia global para uso en todo el sistema
VALUES_INTEGRATION = EnhancedValuesIntegration()
