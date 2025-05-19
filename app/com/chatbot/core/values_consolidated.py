# /home/pablo/app/com/chatbot/core/values_consolidated.py
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


class ValuesPrinciples:
    """
    Clase que implementa los valores fundamentales en cada interacción del chatbot.
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
    
    @classmethod
    async def detect_emotional_context(cls, message_text):
        """
        Detecta el contexto emocional a partir del texto del mensaje.
        """
        message_text = message_text.lower()
        
        for context, data in cls.EMOTIONAL_CONTEXTS.items():
            for indicator in data['indicators']:
                if indicator in message_text:
                    return context
        
        return 'neutral'
    
    @classmethod
    async def enhance_response(cls, original_response, emotional_context, user_data=None):
        """
        Mejora la respuesta del chatbot integrando los valores fundamentales.
        
        Args:
            original_response: Respuesta original generada por el chatbot
            emotional_context: Contexto emocional detectado
            user_data: Datos adicionales del usuario si están disponibles
        
        Returns:
            Respuesta mejorada que refleja los valores fundamentales
        """
        if emotional_context == 'neutral':
            # Sutil mejora para contexto neutral
            enhanced = cls._add_warmth(original_response)
        else:
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
            # Si la respuesta creció más del 30%, recortar elementos no esenciales
            enhanced = cls._optimize_length(enhanced)
            
        return enhanced
    
    @staticmethod
    def _add_warmth(text):
        """Añade un toque sutil de calidez a las respuestas neutrales."""
        # Detectar si el texto termina en un signo de interrogación o es una pregunta
        if text.strip().endswith('?'):
            return text  # No modificar preguntas
            
        # Evitar modificar textos muy cortos
        if len(text) < 20:
            return text
            
        # Pequeñas modificaciones que añaden calidez sin cambiar el significado
        warmth_elements = [
            (". ", ". Recuerda que estamos aquí para apoyarte. "),
            ("Gracias", "Muchas gracias"),
            ("por favor", "por favor, con gusto"),
            ("podemos", "juntos podemos"),
            ("te ayudará", "te ayudará en tu crecimiento profesional")
        ]
        
        # Solo aplicar una modificación para mantener naturalidad
        for original, warm in warmth_elements:
            if original in text and not "estamos aquí para apoyarte" in text:
                return text.replace(original, warm, 1)
                
        # Si ninguna modificación aplica, añadir un cierre cálido
        if not any(x in text for x in ["éxito", "suerte", "adelante", "apoyarte"]):
            return f"{text} ¡Estamos para apoyarte en cada paso!"
            
        return text
    
    @staticmethod
    def _add_support_layer(text):
        """Añade elementos de apoyo emocional al texto."""
        support_phrases = [
            "Entiendo que la búsqueda puede ser desafiante, pero estamos contigo en este proceso.",
            "Es natural sentir frustración en estos momentos, pero cada experiencia te acerca más a tu objetivo.",
            "Tu perseverancia te distingue, y eso es exactamente lo que valoran los empleadores."
        ]
        
        # Seleccionar una frase apropiada y añadirla al inicio o final
        # según donde tenga mejor coherencia
        selected = support_phrases[0]  # Por simplicidad tomamos la primera
        
        if text.startswith(("Entiendo", "Comprendo", "Lamento")):
            # Ya tiene un elemento de apoyo al inicio
            return f"{text} {selected}"
        else:
            return f"{selected} {text}"
    
    @staticmethod
    def _add_motivation_layer(text):
        """Añade elementos motivacionales al texto."""
        motivation_phrases = [
            "Cada paso que das te acerca a tu objetivo profesional.",
            "Tu determinación es tu mayor fortaleza en este proceso.",
            "Las oportunidades correctas reconocen el valor que tú aportas."
        ]
        
        selected = motivation_phrases[1]  # Por simplicidad
        
        # Colocar al final para servir como cierre motivacional
        if text.endswith((".", "!", "?")):
            return f"{text} {selected}"
        else:
            return f"{text}. {selected}"
    
    @staticmethod
    def _add_perspective_layer(text):
        """Añade perspectiva ampliada al texto."""
        perspective_phrases = [
            "Esta etapa es solo un componente de tu desarrollo profesional continuo.",
            "Cada interacción construye tu red profesional, independientemente del resultado inmediato.",
            "La carrera profesional es un maratón, no una carrera corta."
        ]
        
        selected = perspective_phrases[0]  # Por simplicidad
        
        if len(text.split()) > 30:
            # Para textos largos, integramos en lugar de añadir
            sentences = text.split('. ')
            if len(sentences) > 2:
                insertion_point = len(sentences) // 2
                sentences.insert(insertion_point, selected)
                return '. '.join(sentences)
        
        return f"{text} {selected}"
    
    @staticmethod
    def _add_clarity_layer(text):
        """Añade elementos de claridad al texto."""
        clarity_phrases = [
            "Analicemos esto paso a paso para brindarte claridad.",
            "Permíteme ayudarte a estructurar este proceso para mayor claridad.",
            "Veamos las opciones desde una perspectiva organizada."
        ]
        
        selected = clarity_phrases[0]  # Por simplicidad
        
        # Colocar al inicio para establecer el tono de la respuesta
        return f"{selected} {text}"
    
    @staticmethod
    def _optimize_length(text):
        """Optimiza la longitud del texto manteniendo los elementos esenciales."""
        # Implementación simple: si hay frases repetitivas, eliminar redundancias
        sentences = text.split('. ')
        unique_content = []
        themes_covered = set()
        
        for sentence in sentences:
            # Extraer tema principal de la frase (simplificado)
            words = set(sentence.lower().split())
            theme = frozenset(w for w in words if len(w) > 4 and w not in 
                             {"estamos", "aunque", "porque", "siempre", "también"})
            
            # Si el tema no ha sido cubierto o es la primera/última frase, incluir
            if not theme or not any(len(theme.intersection(t)) > len(theme) * 0.5 for t in themes_covered) or \
               sentence == sentences[0] or sentence == sentences[-1]:
                unique_content.append(sentence)
                themes_covered.add(theme)
        
        return '. '.join(unique_content)


class ValuesIntegrator:
    """
    Clase que integra los valores fundamentales en el flujo de trabajo del chatbot.
    """
    
    @classmethod
    async def process_incoming_message(cls, message_text, user_data=None):
        """
        Procesa un mensaje entrante y detecta oportunidades para reflejar valores.
        
        Args:
            message_text: Texto del mensaje del usuario
            user_data: Datos adicionales del usuario si están disponibles
            
        Returns:
            Dict con metadatos de valores a considerar en la respuesta
        """
        # Detectar contexto emocional
        emotional_context = await ValuesPrinciples.detect_emotional_context(message_text)
        
        # Determinar etapa de carrera si es posible
        career_stage = await cls._detect_career_stage(message_text, user_data)
        
        # Identificar oportunidades para mostrar valores específicos
        value_opportunities = await cls._identify_value_opportunities(message_text, emotional_context, career_stage)
        
        # Registrar para análisis y mejora continua
        await cls._log_value_context(emotional_context, career_stage, value_opportunities)
        
        return {
            'emotional_context': emotional_context,
            'career_stage': career_stage,
            'value_opportunities': value_opportunities
        }
    
    @classmethod
    async def apply_values_to_response(cls, original_response, values_metadata):
        """
        Aplica los valores fundamentales a una respuesta del chatbot.
        
        Args:
            original_response: Respuesta original del chatbot
            values_metadata: Metadatos de valores detectados
            
        Returns:
            Respuesta mejorada que refleja los valores fundamentales
        """
        return await ValuesPrinciples.enhance_response(
            original_response,
            values_metadata.get('emotional_context', 'neutral')
        )
    
    @classmethod
    async def _detect_career_stage(cls, message_text, user_data=None):
        """
        Detecta la etapa de carrera del usuario basado en el mensaje y datos disponibles.
        """
        # Implementar lógica para detectar etapa de carrera
        # (exploración, transición, crecimiento, etc.)
        # Por simplicidad, devolvemos un valor predeterminado
        return 'exploring'
    
    @classmethod
    async def _identify_value_opportunities(cls, message_text, emotional_context, career_stage):
        """
        Identifica oportunidades específicas para mostrar valores.
        """
        opportunities = []
        
        # Simplificado: añadir valores según el contexto
        if emotional_context == 'job_search_frustration':
            opportunities.append('show_empathy')
            opportunities.append('provide_perspective')
        elif emotional_context == 'career_uncertainty':
            opportunities.append('offer_guidance')
            opportunities.append('highlight_potential')
        elif emotional_context == 'achievement_moment':
            opportunities.append('celebrate_success')
            opportunities.append('suggest_next_growth')
        
        # Añadir valores según la etapa de carrera
        if career_stage == 'exploring':
            opportunities.append('share_exploration_resources')
        elif career_stage == 'transitioning':
            opportunities.append('recognize_courage')
        elif career_stage == 'advancing':
            opportunities.append('acknowledge_expertise')
        
        return opportunities
    
    @classmethod
    async def _log_value_context(cls, emotional_context, career_stage, value_opportunities):
        """
        Registra el contexto de valores para análisis y mejora continua.
        """
        # En un entorno de producción, registraríamos esto para análisis
        # Pero aquí simplemente lo registramos en el logger
        logger.info(
            f"Values Context - Emotional: {emotional_context}, "
            f"Career Stage: {career_stage}, "
            f"Opportunities: {value_opportunities}"
        )


class ValuesEnhancer:
    """
    Clase que integra valores fundamentales a las respuestas del chatbot,
    con personalización basada en contexto y preferencias de usuario.
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
VALUES_INTEGRATION = ValuesEnhancer()
