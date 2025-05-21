"""
Módulo Core de Valores Fundamentales para el Chatbot.

Define los principios y valores fundamentales que guían las interacciones
del sistema de chatbot con los usuarios, incluyendo detección de contexto
emocional, personalización de mensajes y gestión de preferencias de usuario.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from django.utils import timezone

logger = logging.getLogger(__name__)


class UserPreferencesCache:
    """
    Caché en memoria para preferencias de usuario que optimiza
    la personalización de mensajes basados en valores.
    """
    def __init__(self, max_entries: int = 10000, pruning_threshold: float = 0.9):
        """
        Inicializa el caché de preferencias de usuario.
        
        Args:
            max_entries: Número máximo de entradas en caché
            pruning_threshold: Umbral (0-1) para iniciar la limpieza
        """
        self._cache: Dict[str, Dict] = {}
        self._max_entries = max_entries
        self._pruning_threshold = pruning_threshold
    
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


class ValuesPrinciples:
    """
    Clase que implementa los valores fundamentales en cada interacción del chatbot.
    
    Valores principales:
    - Apoyo a Carreras: Enfoque en el crecimiento profesional
    - Solidaridad: Empatía y comprensión genuinas
    - Sinergia: Relaciones mutuamente beneficiosas
    - Pasión Auténtica: Compromiso con el éxito del usuario
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
    
    @classmethod
    async def detect_emotional_context(cls, message_text: str) -> str:
        """
        Detecta el contexto emocional a partir del texto del mensaje.
        
        Args:
            message_text: Texto del mensaje a analizar
            
        Returns:
            str: Identificador del contexto emocional detectado o 'neutral'
        """
        message_text = message_text.lower()
        
        for context, data in cls.EMOTIONAL_CONTEXTS.items():
            for indicator in data['indicators']:
                if indicator in message_text:
                    return context
        
        return 'neutral'
    
    @classmethod
    async def enhance_response(cls, original_response: str, emotional_context: str = 'neutral') -> str:
        """
        Mejora una respuesta integrando los valores fundamentales.
        
        Args:
            original_response: Respuesta original del chatbot
            emotional_context: Contexto emocional detectado
            
        Returns:
            str: Respuesta mejorada con valores integrados
        """
        if emotional_context == 'neutral':
            return cls._add_warmth(original_response)
            
        # Aplicar principios específicos según el contexto emocional
        principles = cls.EMOTIONAL_CONTEXTS.get(emotional_context, {}).get('principles', [])
        enhanced = original_response
        
        for principle in principles:
            if principle == 'apoyo':
                enhanced = cls._add_support_layer(enhanced)
            elif principle == 'motivación':
                enhanced = cls._add_motivation_layer(enhanced)
            elif principle == 'perspectiva':
                enhanced = cls._add_perspective_layer(enhanced)
            elif principle == 'claridad':
                enhanced = cls._add_clarity_layer(enhanced)
            # ... y así sucesivamente para cada principio
        
        # Asegurar que la respuesta no sea excesivamente larga
        if len(enhanced) > len(original_response) * 1.3:
            enhanced = cls._optimize_length(enhanced)
            
        return enhanced
    
    @staticmethod
    def _add_warmth(text: str) -> str:
        """Añade un toque sutil de calidez a las respuestas neutrales."""
        if text.strip().endswith('?'):
            return text  # No modificar preguntas
            
        if len(text) < 20:
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
            "Sabemos que el camino puede ser difícil, pero no estás solo/a en esto."
        ]
        
        # Añadir una frase de apoyo al principio o al final según el contexto
        if any(p in text for p in ["puedo", "puedes", "ayuda"]):
            return f"{support_phrases[0]} {text}"
        elif any(e in text for e in ["difícil", "complicado", "problema"]):
            return f"{support_phrases[1]} {text}"
        else:
            return f"{text} {support_phrases[2]}"
    
    @staticmethod
    def _add_motivation_layer(text: str) -> str:
        """Añade un toque motivacional al texto."""
        motivation_phrases = [
            "Cada paso, por pequeño que sea, te acerca a tus metas profesionales.",
            "Recuerda que cada experiencia es una oportunidad de aprendizaje.",
            "Tu perseverancia es admirable y te llevará lejos en tu carrera."
        ]
        
        # Añadir una frase motivacional al final
        import random
        return f"{text} {random.choice(motivation_phrases)}"
    
    @staticmethod
    def _add_perspective_layer(text: str) -> str:
        """Añade perspectiva al mensaje."""
        perspective_phrases = [
            "A veces, un cambio de perspectiva puede revelar nuevas oportunidades.",
            "Es útil considerar diferentes enfoques para superar los desafíos.",
            "Cada obstáculo es una oportunidad para crecer y mejorar."
        ]
        
        import random
        return f"{text} {random.choice(perspective_phrases)}"
    
    @staticmethod
    def _add_clarity_layer(text: str) -> str:
        """Añade claridad al mensaje."""
        clarity_phrases = [
            "Vamos a desglosar esto para mayor claridad.",
            "Es importante entender esto claramente antes de continuar.",
            "Permíteme aclarar este punto importante."
        ]
        
        import random
        return f"{random.choice(clarity_phrases)} {text}"
    
    @staticmethod
    def _optimize_length(text: str) -> str:
        """Optimiza la longitud del texto si es necesario."""
        # Implementación básica - en una versión real, esto podría ser más sofisticado
        max_length = 500  # Longitud máxima razonable
        if len(text) > max_length:
            text = text[:max_length].rsplit('.', 1)[0] + '.'
        return text
