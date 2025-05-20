# /home/pablo/app/com/chatbot/core/values.py
"""
Módulo Consolidado de Valores Fundamentales para el Chatbot.

Este módulo define los principios y valores fundamentales que guían todas las interacciones
del sistema de chatbot con los usuarios. Estos valores no son simples mensajes, sino
una guía para el comportamiento y tono en cada punto de contacto, asegurando que el apoyo,
la solidaridad, la sinergia y la pasión auténtica se reflejen en cada interacción.

Principios:
1. Apoyo a Carreras: Cada interacción debe enfocarse en el crecimiento profesional
2. Solidaridad: El sistema muestra empatía genuina y comprensión
3. Sinergia: Buscamos construir relaciones mutuamente beneficiosas
4. Pasión Auténtica: Cada mensaje refleja nuestro compromiso con el éxito del usuario

Características:
- Detección contextual de estados emocionales
- Personalización basada en preferencias de usuario
- Adaptación inteligente del mensaje según el contexto
- Optimizado para rendimiento y bajo uso de CPU
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from asgiref.sync import sync_to_async
from django.utils import timezone

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


class ValuesManager:
    """
    Clase principal que gestiona todos los aspectos relacionados con los valores
    fundamentales del chatbot, incluyendo detección de contexto emocional,
    personalización de mensajes y mejora de respuestas.
    """
    
    # Categorías de situaciones emocionales que pueden enfrentar los usuarios
    EMOTIONAL_CONTEXTS = {
        'job_search_frustration': {
            'indicators': ['rechazado', 'difícil', 'frustrante', 'cansado de buscar', 'sin oportunidades'],
            'principles': ['apoyo', 'motivación', 'perspectiva']
        },
        'career_uncertainty': {
            'indicators': ['no sé qué hacer', 'indeciso', 'cambio de carrera', 'estancado'],
            'principles': ['claridad', 'exploración', 'potencial']
        },
        'achievement_moment': {
            'indicators': ['entrevista', 'oferta', 'aceptado', 'nuevo trabajo', 'oportunidad'],
            'principles': ['celebración', 'preparación', 'crecimiento']
        },
        'skills_development': {
            'indicators': ['aprender', 'mejorar', 'desarrollar', 'habilidades', 'capacitación'],
            'principles': ['guía', 'recursos', 'motivación']
        }
    }
    
    # Mensajes predefinidos por contexto
    CONTEXT_MESSAGES = {
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
    SUPPORT_MESSAGES = [
        "Estamos aquí para apoyarte en cada paso de tu camino profesional.",
        "Nuestra pasión es construir sinergias que impulsen tu desarrollo.",
        "El éxito compartido es nuestra meta, trabajamos juntos para lograrlo.",
        "Cada interacción es una oportunidad para crecer y avanzar juntos.",
        "Tu crecimiento profesional es el motor que impulsa nuestro compromiso."
    ]
    
    def __init__(self):
        self.user_preferences = UserPreferencesCache()
    
    @classmethod
    async def detect_emotional_context(cls, message_text: str) -> str:
        """
        Detecta el contexto emocional a partir del texto del mensaje.
        """
        message_text = message_text.lower()
        
        for context, data in cls.EMOTIONAL_CONTEXTS.items():
            for indicator in data['indicators']:
                if indicator in message_text:
                    return context
        
        return 'neutral'
    
    async def get_personalized_message(self, user_id: str, context: str, emotional_context: str = 'neutral') -> str:
        """
        Genera un mensaje personalizado basado en el contexto y las preferencias del usuario.
        """
        try:
            user_data = self.user_preferences.get(user_id) or {}
            specific_context = context.lower()
            
            if specific_context not in self.CONTEXT_MESSAGES:
                specific_context = 'career'
            
            message_pool = self.CONTEXT_MESSAGES.get(specific_context, self.SUPPORT_MESSAGES)
            message_index = (hash(str(user_id) + datetime.now().strftime('%Y-%m-%d')) % len(message_pool))
            message = message_pool[message_index]
            
            if emotional_context != 'neutral':
                message = await self._enhance_for_emotional_context(message, emotional_context)
            
            self.user_preferences.update(user_id, {
                'last_context': specific_context,
                'last_interaction': timezone.now(),
                'emotional_context': emotional_context,
                'messages_count': user_data.get('messages_count', 0) + 1
            })
            
            return message
            
        except Exception as e:
            logger.error(f"Error en get_personalized_message: {str(e)}")
            return "Estamos aquí para apoyarte en tu desarrollo profesional."
    
    async def _enhance_for_emotional_context(self, message: str, emotional_context: str) -> str:
        """Enriquece un mensaje según el contexto emocional detectado."""
        if emotional_context == 'job_search_frustration':
            return f"Entendemos que la búsqueda puede ser desafiante a veces. {message}"
        elif emotional_context == 'career_uncertainty':
            return f"En momentos de incertidumbre, estamos aquí para orientarte. {message}"
        elif emotional_context == 'achievement_moment':
            return f"¡Felicidades por este logro! {message}"
        return message
    
    async def enhance_response(self, 
                            original_response: str, 
                            user_id: str, 
                            context: str = 'career',
                            values_metadata: Dict = None) -> str:
        """
        Mejora una respuesta del sistema integrando valores fundamentales.
        """
        try:
            emotional_context = values_metadata.get('emotional_context', 'neutral') if values_metadata else 'neutral'
            
            if len(original_response) < 50:
                value_message = await self.get_personalized_message(user_id, context, emotional_context)
                return f"{original_response} {value_message}"
            else:
                return await self._enhance_response_with_principles(original_response, emotional_context)
                
        except Exception as e:
            logger.error(f"Error en enhance_response: {str(e)}")
            return original_response
    
    async def _enhance_response_with_principles(self, text: str, emotional_context: str) -> str:
        """Aplica principios de valores a una respuesta."""
        if emotional_context == 'neutral':
            return self._add_warmth(text)
            
        principles = self.EMOTIONAL_CONTEXTS.get(emotional_context, {}).get('principles', [])
        enhanced = text
        
        for principle in principles:
            if principle == 'apoyo':
                enhanced = self._add_support_layer(enhanced)
            elif principle == 'motivación':
                enhanced = self._add_motivation_layer(enhanced)
            elif principle == 'perspectiva':
                enhanced = self._add_perspective_layer(enhanced)
            elif principle == 'claridad':
                enhanced = self._add_clarity_layer(enhanced)
        
        if len(enhanced) > len(text) * 1.3:
            enhanced = self._optimize_length(enhanced)
            
        return enhanced
    
    @staticmethod
    def _add_warmth(text: str) -> str:
        """Añade un toque sutil de calidez a las respuestas neutrales."""
        if text.strip().endswith('?') or len(text) < 20:
            return text
            
        warmth_elements = [
            (". ", ". Recuerda que estamos aquí para apoyarte. "),
            ("Gracias", "Muchas gracias"),
            ("por favor", "por favor, con gusto"),
            ("podemos", "juntos podemos"),
            ("te ayudará", "te ayudará en tu crecimiento profesional")
        ]
        
        for original, warm in warmth_elements:
            if original in text and not "estamos aquí para apoyarte" in text:
                return text.replace(original, warm, 1)
                
        if not any(x in text for x in ["éxito", "suerte", "adelante", "apoyarte"]):
            return f"{text} ¡Estamos para apoyarte en cada paso!"
            
        return text
    
    @staticmethod
    def _add_support_layer(text: str) -> str:
        """Añade elementos de apoyo emocional al texto."""
        support_phrases = [
            "Entiendo que la búsqueda puede ser desafiante, pero estamos contigo en este proceso.",
            "Es natural sentir frustración en estos momentos, pero cada experiencia te acerca más a tu objetivo.",
            "Tu perseverancia te distingue, y eso es exactamente lo que valoran los empleadores."
        ]
        
        selected = support_phrases[0]
        return f"{selected} {text}" if not text.startswith(("Entiendo", "Comprendo", "Lamento")) else f"{text} {selected}"
    
    @staticmethod
    def _add_motivation_layer(text: str) -> str:
        """Añade elementos motivacionales al texto."""
        motivation_phrases = [
            "Cada paso que das te acerca a tu objetivo profesional.",
            "Tu determinación es tu mayor fortaleza en este proceso.",
            "Las oportunidades correctas reconocen el valor que tú aportas."
        ]
        
        selected = motivation_phrases[1]
        return f"{text} {selected}" if text.endswith((".", "!", "?")) else f"{text}. {selected}"
    
    @staticmethod
    def _add_perspective_layer(text: str) -> str:
        """Añade perspectiva ampliada al texto."""
        perspective_phrases = [
            "Esta etapa es solo un componente de tu desarrollo profesional continuo.",
            "Cada interacción construye tu red profesional, independientemente del resultado inmediato.",
            "La carrera profesional es un maratón, no una carrera corta."
        ]
        
        selected = perspective_phrases[0]
        if len(text.split()) > 30:
            sentences = text.split('. ')
            if len(sentences) > 2:
                insertion_point = len(sentences) // 2
                sentences.insert(insertion_point, selected)
                return '. '.join(sentences)
        return f"{text} {selected}"
    
    @staticmethod
    def _add_clarity_layer(text: str) -> str:
        """Añade elementos de claridad al texto."""
        clarity_phrases = [
            "Analicemos esto paso a paso para brindarte claridad.",
            "Permíteme ayudarte a estructurar este proceso para mayor claridad.",
            "Veamos las opciones desde una perspectiva organizada."
        ]
        
        return f"{clarity_phrases[0]} {text}"
    
    @staticmethod
    def _optimize_length(text: str) -> str:
        """Optimiza la longitud del texto manteniendo los elementos esenciales."""
        sentences = text.split('. ')
        unique_content = []
        themes_covered = set()
        
        for sentence in sentences:
            words = set(sentence.lower().split())
            theme = frozenset(w for w in words if len(w) > 4 and w not in 
                             {"estamos", "aunque", "porque", "siempre", "también"})
            
            if not theme or not any(len(theme.intersection(t)) > len(theme) * 0.5 for t in themes_covered) or \
               sentence == sentences[0] or sentence == sentences[-1]:
                unique_content.append(sentence)
                themes_covered.add(theme)
        
        return '. '.join(unique_content)
    
    async def track_interaction(self, user_id: str, interaction_data: Dict[str, Any]) -> None:
        """Registra datos de interacción para mejorar personalización futura."""
        try:
            current = self.user_preferences.get(user_id) or {}
            interactions = current.get('interactions', [])
            
            interactions.append({
                'timestamp': timezone.now().isoformat(),
                'type': interaction_data.get('type', 'message'),
                'context': interaction_data.get('context', 'general'),
                'success': interaction_data.get('success', True)
            })
            
            if len(interactions) > 20:
                interactions = interactions[-20:]
            
            self.user_preferences.update(user_id, {
                'interactions': interactions,
                'last_interaction': timezone.now(),
                'interaction_count': current.get('interaction_count', 0) + 1
            })
            
        except Exception as e:
            logger.error(f"Error en track_interaction: {str(e)}")


# Instancia global para uso en todo el sistema
VALUES_MANAGER = ValuesManager()
