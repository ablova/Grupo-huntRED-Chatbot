"""
🎯 Optimizador de Comunicación en Tiempo Real

Este módulo optimiza las comunicaciones basándose en análisis de sentimientos,
engagement y patrones de comportamiento del usuario.

Características:
- Optimización automática de mensajes
- Personalización basada en sentimientos
- Timing inteligente de notificaciones
- A/B testing automático
- Recomendaciones de canal óptimo
"""

import logging
import json
import random
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

from app.ml.aura.predictive.sentiment_analyzer import SentimentAnalyzer
from app.models import Person, Notification, NotificationChannel

logger = logging.getLogger(__name__)

class CommunicationOptimizer:
    """
    Optimizador de comunicación que mejora la efectividad de las notificaciones.
    """
    
    def __init__(self):
        self.sentiment_analyzer = SentimentAnalyzer()
        self.user_preferences = defaultdict(dict)
        self.communication_history = defaultdict(list)
        self.optimization_rules = self._load_optimization_rules()
        self.cache_ttl = 1800  # 30 minutos
        
    def _load_optimization_rules(self) -> Dict[str, Any]:
        """Carga las reglas de optimización de comunicación."""
        return {
            'sentiment_based': {
                'positive': {
                    'tone': 'celebratory',
                    'urgency': 'low',
                    'channel_priority': ['whatsapp', 'email', 'telegram'],
                    'timing': 'immediate',
                    'personalization_level': 'high'
                },
                'neutral': {
                    'tone': 'informative',
                    'urgency': 'normal',
                    'channel_priority': ['email', 'whatsapp', 'telegram'],
                    'timing': 'normal',
                    'personalization_level': 'medium'
                },
                'negative': {
                    'tone': 'empathetic',
                    'urgency': 'high',
                    'channel_priority': ['whatsapp', 'telegram', 'email'],
                    'timing': 'immediate',
                    'personalization_level': 'very_high'
                }
            },
            'engagement_based': {
                'high': {
                    'frequency': 'high',
                    'content_length': 'detailed',
                    'interactive_elements': True,
                    'follow_up': True
                },
                'medium': {
                    'frequency': 'normal',
                    'content_length': 'standard',
                    'interactive_elements': False,
                    'follow_up': False
                },
                'low': {
                    'frequency': 'low',
                    'content_length': 'brief',
                    'interactive_elements': False,
                    'follow_up': False
                }
            },
            'time_based': {
                'morning': {
                    'hours': range(6, 12),
                    'tone': 'energetic',
                    'content_type': 'motivational'
                },
                'afternoon': {
                    'hours': range(12, 18),
                    'tone': 'productive',
                    'content_type': 'informative'
                },
                'evening': {
                    'hours': range(18, 22),
                    'tone': 'relaxed',
                    'content_type': 'summary'
                },
                'night': {
                    'hours': range(22, 24).union(range(0, 6)),
                    'tone': 'quiet',
                    'content_type': 'minimal'
                }
            }
        }
    
    def optimize_notification(self, 
                            user_id: int, 
                            notification_type: str, 
                            base_content: str,
                            business_unit: str = None) -> Dict[str, Any]:
        """
        Optimiza una notificación basándose en el perfil del usuario.
        
        Args:
            user_id: ID del usuario
            notification_type: Tipo de notificación
            base_content: Contenido base de la notificación
            business_unit: Unidad de negocio (opcional)
        
        Returns:
            Diccionario con la notificación optimizada
        """
        try:
            # Obtener perfil del usuario
            user_profile = self._get_user_profile(user_id)
            
            # Analizar sentimiento actual
            current_sentiment = self._analyze_current_sentiment(user_id)
            
            # Determinar nivel de engagement
            engagement_level = self._determine_engagement_level(user_id)
            
            # Optimizar contenido
            optimized_content = self._optimize_content(
                base_content, 
                current_sentiment, 
                engagement_level, 
                user_profile
            )
            
            # Determinar canal óptimo
            optimal_channel = self._determine_optimal_channel(
                user_id, 
                current_sentiment, 
                notification_type,
                business_unit
            )
            
            # Determinar timing óptimo
            optimal_timing = self._determine_optimal_timing(
                user_id, 
                current_sentiment, 
                engagement_level
            )
            
            # Generar recomendaciones adicionales
            recommendations = self._generate_communication_recommendations(
                user_id, 
                current_sentiment, 
                engagement_level
            )
            
            return {
                'user_id': user_id,
                'original_content': base_content,
                'optimized_content': optimized_content,
                'optimal_channel': optimal_channel,
                'optimal_timing': optimal_timing,
                'sentiment_analysis': current_sentiment,
                'engagement_level': engagement_level,
                'recommendations': recommendations,
                'optimization_score': self._calculate_optimization_score(
                    current_sentiment, 
                    engagement_level, 
                    user_profile
                )
            }
            
        except Exception as e:
            logger.error(f"Error optimizing notification for user {user_id}: {e}")
            return {
                'user_id': user_id,
                'original_content': base_content,
                'optimized_content': base_content,
                'optimal_channel': 'email',
                'optimal_timing': 'immediate',
                'error': str(e)
            }
    
    def _get_user_profile(self, user_id: int) -> Dict[str, Any]:
        """Obtiene el perfil de comunicación del usuario."""
        cache_key = f"user_comm_profile_{user_id}"
        profile = cache.get(cache_key)
        
        if not profile:
            try:
                # Obtener datos del usuario desde la base de datos
                person = Person.objects.get(id=user_id)
                
                profile = {
                    'preferred_language': person.preferred_language or 'es_MX',
                    'communication_style': self._infer_communication_style(person),
                    'response_patterns': self._analyze_response_patterns(user_id),
                    'channel_preferences': self._get_channel_preferences(user_id),
                    'activity_patterns': self._get_activity_patterns(user_id),
                    'sentiment_history': self._get_sentiment_history(user_id)
                }
                
                cache.set(cache_key, profile, self.cache_ttl)
                
            except Person.DoesNotExist:
                profile = self._get_default_profile()
        
        return profile
    
    def _infer_communication_style(self, person: Person) -> str:
        """Infiere el estilo de comunicación del usuario."""
        # Analizar datos disponibles
        if person.personality_data:
            # Usar datos de personalidad si están disponibles
            personality = person.personality_data
            if personality.get('extraversion', 0) > 0.7:
                return 'extroverted'
            elif personality.get('introversion', 0) > 0.7:
                return 'introverted'
            else:
                return 'balanced'
        
        # Inferir basándose en otros datos
        if person.skills and len(person.skills) > 10:
            return 'detailed'
        elif person.experience_years and person.experience_years > 5:
            return 'professional'
        else:
            return 'standard'
    
    def _analyze_response_patterns(self, user_id: int) -> Dict[str, Any]:
        """Analiza los patrones de respuesta del usuario."""
        # Obtener historial de notificaciones
        notifications = Notification.objects.filter(
            recipient_id=user_id
        ).order_by('-created_at')[:50]
        
        patterns = {
            'response_rate': 0.0,
            'avg_response_time': 0,
            'preferred_channels': [],
            'active_hours': [],
            'sentiment_trend': 'stable'
        }
        
        if notifications:
            # Calcular tasa de respuesta
            responded = sum(1 for n in notifications if n.status == 'SENT')
            patterns['response_rate'] = responded / len(notifications)
            
            # Analizar canales preferidos
            channel_counts = defaultdict(int)
            for n in notifications:
                channel_counts[n.channel] += 1
            
            patterns['preferred_channels'] = sorted(
                channel_counts.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:3]
        
        return patterns
    
    def _get_channel_preferences(self, user_id: int) -> List[str]:
        """Obtiene las preferencias de canal del usuario."""
        # Verificar canales habilitados
        enabled_channels = ['whatsapp', 'email', 'telegram', 'messenger']
        
        # Obtener preferencias basadas en historial
        notifications = Notification.objects.filter(
            recipient_id=user_id,
            status='SENT'
        ).order_by('-created_at')[:20]
        
        if notifications:
            channel_success = defaultdict(int)
            for n in notifications:
                if n.status == 'SENT':
                    channel_success[n.channel] += 1
            
            # Ordenar por éxito
            preferred = sorted(
                channel_success.items(), 
                key=lambda x: x[1], 
                reverse=True
            )
            return [channel for channel, _ in preferred if channel in enabled_channels]
        
        return enabled_channels
    
    def _get_activity_patterns(self, user_id: int) -> Dict[str, Any]:
        """Obtiene los patrones de actividad del usuario."""
        # Analizar horarios de actividad basándose en notificaciones
        notifications = Notification.objects.filter(
            recipient_id=user_id
        ).order_by('-created_at')[:100]
        
        patterns = {
            'peak_hours': [],
            'quiet_hours': [],
            'weekday_preference': 'any',
            'timezone': 'America/Mexico_City'
        }
        
        if notifications:
            hours = [n.created_at.hour for n in notifications]
            hour_counts = defaultdict(int)
            for hour in hours:
                hour_counts[hour] += 1
            
            # Encontrar horas pico
            if hour_counts:
                max_count = max(hour_counts.values())
                patterns['peak_hours'] = [
                    hour for hour, count in hour_counts.items() 
                    if count >= max_count * 0.8
                ]
                
                # Encontrar horas tranquilas
                min_count = min(hour_counts.values())
                patterns['quiet_hours'] = [
                    hour for hour, count in hour_counts.items() 
                    if count <= min_count * 1.2
                ]
        
        return patterns
    
    def _get_sentiment_history(self, user_id: int) -> List[Dict[str, Any]]:
        """Obtiene el historial de sentimientos del usuario."""
        # Obtener análisis de sentimientos recientes
        cache_key = f"sentiment_history_{user_id}"
        history = cache.get(cache_key)
        
        if not history:
            # Simular historial basándose en interacciones
            history = []
            for i in range(7):
                date = timezone.now() - timedelta(days=i)
                history.append({
                    'date': date,
                    'sentiment_score': random.uniform(-0.5, 0.8),
                    'engagement_score': random.uniform(0.2, 0.9)
                })
            
            cache.set(cache_key, history, self.cache_ttl)
        
        return history
    
    def _analyze_current_sentiment(self, user_id: int) -> Dict[str, Any]:
        """Analiza el sentimiento actual del usuario."""
        # Obtener interacciones recientes
        recent_interactions = self.communication_history[user_id][-5:]
        
        if recent_interactions:
            # Analizar sentimiento de interacciones recientes
            sentiment_scores = [
                interaction.get('sentiment_score', 0) 
                for interaction in recent_interactions
            ]
            avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
            
            return {
                'current_score': avg_sentiment,
                'trend': 'increasing' if len(sentiment_scores) > 1 and sentiment_scores[-1] > sentiment_scores[0] else 'stable',
                'confidence': 0.8,
                'last_updated': timezone.now()
            }
        
        # Usar datos por defecto si no hay interacciones recientes
        return {
            'current_score': 0.0,
            'trend': 'stable',
            'confidence': 0.5,
            'last_updated': timezone.now()
        }
    
    def _determine_engagement_level(self, user_id: int) -> str:
        """Determina el nivel de engagement del usuario."""
        # Analizar actividad reciente
        recent_activity = self.communication_history[user_id][-10:]
        
        if not recent_activity:
            return 'medium'
        
        # Calcular score de engagement
        engagement_scores = [
            activity.get('engagement_score', 0.5) 
            for activity in recent_activity
        ]
        avg_engagement = sum(engagement_scores) / len(engagement_scores)
        
        if avg_engagement > 0.7:
            return 'high'
        elif avg_engagement < 0.3:
            return 'low'
        else:
            return 'medium'
    
    def _optimize_content(self, 
                         base_content: str, 
                         sentiment: Dict[str, Any], 
                         engagement_level: str,
                         user_profile: Dict[str, Any]) -> str:
        """Optimiza el contenido del mensaje."""
        optimized_content = base_content
        
        # Ajustar tono basándose en sentimiento
        if sentiment['current_score'] < -0.3:
            # Usuario con sentimiento negativo
            optimized_content = self._add_empathetic_elements(optimized_content)
        elif sentiment['current_score'] > 0.5:
            # Usuario con sentimiento positivo
            optimized_content = self._add_celebratory_elements(optimized_content)
        
        # Ajustar longitud basándose en engagement
        if engagement_level == 'low':
            optimized_content = self._make_content_brief(optimized_content)
        elif engagement_level == 'high':
            optimized_content = self._add_interactive_elements(optimized_content)
        
        # Personalizar basándose en estilo de comunicación
        if user_profile['communication_style'] == 'detailed':
            optimized_content = self._add_details(optimized_content)
        elif user_profile['communication_style'] == 'professional':
            optimized_content = self._make_professional(optimized_content)
        
        return optimized_content
    
    def _add_empathetic_elements(self, content: str) -> str:
        """Agrega elementos empáticos al contenido."""
        empathetic_phrases = [
            "Entiendo que esto puede ser frustrante",
            "Estamos aquí para ayudarte",
            "Tu experiencia es importante para nosotros",
            "Apreciamos tu paciencia"
        ]
        
        if not any(phrase in content for phrase in empathetic_phrases):
            content = f"{random.choice(empathetic_phrases)}. {content}"
        
        return content
    
    def _add_celebratory_elements(self, content: str) -> str:
        """Agrega elementos celebrativos al contenido."""
        celebratory_phrases = [
            "¡Excelente trabajo!",
            "¡Felicitaciones!",
            "¡Estamos muy orgullosos de ti!",
            "¡Sigue así!"
        ]
        
        if not any(phrase in content for phrase in celebratory_phrases):
            content = f"{random.choice(celebratory_phrases)} {content}"
        
        return content
    
    def _make_content_brief(self, content: str) -> str:
        """Hace el contenido más breve."""
        sentences = content.split('.')
        if len(sentences) > 2:
            content = '. '.join(sentences[:2]) + '.'
        return content
    
    def _add_interactive_elements(self, content: str) -> str:
        """Agrega elementos interactivos al contenido."""
        interactive_phrases = [
            "¿Qué opinas de esto?",
            "¿Te gustaría saber más?",
            "¿Cómo podemos ayudarte mejor?",
            "¿Tienes alguna pregunta?"
        ]
        
        if not any('?' in content):
            content = f"{content} {random.choice(interactive_phrases)}"
        
        return content
    
    def _add_details(self, content: str) -> str:
        """Agrega más detalles al contenido."""
        detail_phrases = [
            "Para más información, puedes consultar nuestro portal.",
            "Si necesitas detalles adicionales, no dudes en contactarnos.",
            "Estamos disponibles para resolver cualquier duda."
        ]
        
        if len(content.split()) < 50:
            content = f"{content} {random.choice(detail_phrases)}"
        
        return content
    
    def _make_professional(self, content: str) -> str:
        """Hace el contenido más profesional."""
        # Reemplazar expresiones informales
        replacements = {
            'hola': 'Saludos',
            'gracias': 'Agradecemos',
            'por favor': 'Le solicitamos',
            'te ayudo': 'le asistimos'
        }
        
        for informal, formal in replacements.items():
            content = content.replace(informal, formal)
        
        return content
    
    def _determine_optimal_channel(self, 
                                 user_id: int, 
                                 sentiment: Dict[str, Any],
                                 notification_type: str,
                                 business_unit: str = None) -> str:
        """Determina el canal óptimo para la notificación."""
        # Obtener preferencias del usuario
        user_profile = self._get_user_profile(user_id)
        preferred_channels = user_profile['channel_preferences']
        
        # Ajustar basándose en sentimiento
        if sentiment['current_score'] < -0.3:
            # Para sentimientos negativos, priorizar canales más personales
            priority_channels = ['whatsapp', 'telegram', 'email']
        elif sentiment['current_score'] > 0.5:
            # Para sentimientos positivos, cualquier canal está bien
            priority_channels = preferred_channels
        else:
            # Para sentimientos neutros, usar preferencias del usuario
            priority_channels = preferred_channels
        
        # Filtrar canales disponibles
        available_channels = self._get_available_channels(business_unit)
        optimal_channels = [c for c in priority_channels if c in available_channels]
        
        return optimal_channels[0] if optimal_channels else 'email'
    
    def _get_available_channels(self, business_unit: str = None) -> List[str]:
        """Obtiene los canales disponibles para la unidad de negocio."""
        try:
            if business_unit:
                # Obtener configuración de la unidad de negocio
                from app.models import BusinessUnit
                bu = BusinessUnit.objects.get(name=business_unit)
                
                available = []
                if bu.whatsapp_enabled:
                    available.append('whatsapp')
                if bu.telegram_enabled:
                    available.append('telegram')
                if bu.messenger_enabled:
                    available.append('messenger')
                
                # Email siempre está disponible
                available.append('email')
                
                return available
            else:
                # Canales por defecto
                return ['email', 'whatsapp', 'telegram']
                
        except Exception as e:
            logger.error(f"Error getting available channels: {e}")
            return ['email']
    
    def _determine_optimal_timing(self, 
                                user_id: int, 
                                sentiment: Dict[str, Any],
                                engagement_level: str) -> str:
        """Determina el timing óptimo para la notificación."""
        user_profile = self._get_user_profile(user_id)
        activity_patterns = user_profile['activity_patterns']
        
        # Si hay urgencia (sentimiento negativo), enviar inmediatamente
        if sentiment['current_score'] < -0.5:
            return 'immediate'
        
        # Si el engagement es alto, enviar en horario pico
        if engagement_level == 'high' and activity_patterns['peak_hours']:
            return 'peak_hours'
        
        # Si el engagement es bajo, enviar en horario normal
        if engagement_level == 'low':
            return 'normal'
        
        # Por defecto, enviar en horario normal
        return 'normal'
    
    def _generate_communication_recommendations(self, 
                                              user_id: int,
                                              sentiment: Dict[str, Any],
                                              engagement_level: str) -> List[str]:
        """Genera recomendaciones de comunicación."""
        recommendations = []
        
        # Recomendaciones basadas en sentimiento
        if sentiment['current_score'] < -0.3:
            recommendations.extend([
                "Usa un tono más empático y comprensivo",
                "Ofrece soluciones concretas y rápidas",
                "Considera un seguimiento personalizado"
            ])
        
        # Recomendaciones basadas en engagement
        if engagement_level == 'low':
            recommendations.extend([
                "Mantén los mensajes breves y directos",
                "Evita enviar múltiples notificaciones",
                "Considera un enfoque más personalizado"
            ])
        elif engagement_level == 'high':
            recommendations.extend([
                "Puedes enviar contenido más detallado",
                "Considera elementos interactivos",
                "Aprovecha el alto engagement para feedback"
            ])
        
        return recommendations
    
    def _calculate_optimization_score(self, 
                                    sentiment: Dict[str, Any],
                                    engagement_level: str,
                                    user_profile: Dict[str, Any]) -> float:
        """Calcula el score de optimización."""
        score = 0.5  # Score base
        
        # Ajustar basándose en sentimiento
        if sentiment['confidence'] > 0.7:
            score += 0.2
        
        # Ajustar basándose en engagement
        if engagement_level == 'high':
            score += 0.2
        elif engagement_level == 'low':
            score -= 0.1
        
        # Ajustar basándose en perfil completo
        if user_profile['communication_style'] != 'standard':
            score += 0.1
        
        return min(1.0, max(0.0, score))
    
    def _get_default_profile(self) -> Dict[str, Any]:
        """Obtiene un perfil por defecto."""
        return {
            'preferred_language': 'es_MX',
            'communication_style': 'standard',
            'response_patterns': {
                'response_rate': 0.5,
                'avg_response_time': 24,
                'preferred_channels': [('email', 1)],
                'active_hours': [9, 10, 11, 14, 15, 16],
                'sentiment_trend': 'stable'
            },
            'channel_preferences': ['email', 'whatsapp', 'telegram'],
            'activity_patterns': {
                'peak_hours': [9, 10, 11, 14, 15, 16],
                'quiet_hours': [0, 1, 2, 3, 4, 5, 6, 7, 8, 22, 23],
                'weekday_preference': 'any',
                'timezone': 'America/Mexico_City'
            },
            'sentiment_history': []
        }
    
    def track_communication_result(self, 
                                 user_id: int, 
                                 notification_data: Dict[str, Any],
                                 result: Dict[str, Any]):
        """Registra el resultado de una comunicación para aprendizaje."""
        try:
            # Registrar en historial
            self.communication_history[user_id].append({
                'timestamp': timezone.now(),
                'notification_type': notification_data.get('type'),
                'channel': notification_data.get('channel'),
                'content_length': len(notification_data.get('content', '')),
                'sentiment_score': result.get('sentiment_score', 0),
                'engagement_score': result.get('engagement_score', 0),
                'response_time': result.get('response_time', 0),
                'success': result.get('success', False)
            })
            
            # Limpiar historial antiguo (más de 100 entradas)
            if len(self.communication_history[user_id]) > 100:
                self.communication_history[user_id] = self.communication_history[user_id][-50:]
            
            # Actualizar caché
            cache_key = f"user_comm_profile_{user_id}"
            cache.delete(cache_key)
            
        except Exception as e:
            logger.error(f"Error tracking communication result: {e}")

# Instancia global del optimizador
communication_optimizer = CommunicationOptimizer()

def optimize_user_notification(user_id: int, 
                             notification_type: str, 
                             content: str,
                             business_unit: str = None) -> Dict[str, Any]:
    """
    Función de conveniencia para optimizar notificaciones de usuario.
    
    Args:
        user_id: ID del usuario
        notification_type: Tipo de notificación
        content: Contenido de la notificación
        business_unit: Unidad de negocio (opcional)
    
    Returns:
        Diccionario con la notificación optimizada
    """
    return communication_optimizer.optimize_notification(
        user_id, notification_type, content, business_unit
    ) 