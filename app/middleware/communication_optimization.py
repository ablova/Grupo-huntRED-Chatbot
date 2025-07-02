"""
🎯 Middleware de Optimización de Comunicación

Este middleware optimiza automáticamente las comunicaciones basándose en:
- Análisis de sentimientos del usuario
- Patrones de engagement
- Preferencias de comunicación
- Timing óptimo

Se integra con el sistema de notificaciones para mejorar la efectividad.
"""

import logging
import json
from typing import Dict, Any, Optional
from django.http import JsonResponse
from django.utils import timezone
from django.core.cache import cache

from app.ml.aura.predictive.sentiment_analyzer import SentimentAnalyzer
from app.models import Person, Notification

logger = logging.getLogger(__name__)

class CommunicationOptimizationMiddleware:
    """
    Middleware que optimiza las comunicaciones en tiempo real.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.sentiment_analyzer = SentimentAnalyzer()
        self.optimization_cache_ttl = 1800  # 30 minutos
        
    def __call__(self, request):
        # Procesar la solicitud
        response = self.get_response(request)
        
        # Optimizar comunicaciones si es necesario
        if self._should_optimize_communication(request):
            self._optimize_communication(request, response)
        
        return response
    
    def _should_optimize_communication(self, request) -> bool:
        """Determina si se debe optimizar la comunicación."""
        # Solo optimizar para usuarios autenticados
        if not request.user.is_authenticated:
            return False
        
        # Solo optimizar para ciertos tipos de solicitudes
        if request.path.startswith('/api/notifications/') or \
           request.path.startswith('/api/communication/'):
            return True
        
        return False
    
    def _optimize_communication(self, request, response):
        """Optimiza la comunicación basándose en el contexto."""
        try:
            user_id = request.user.id
            
            # Obtener perfil de comunicación del usuario
            user_profile = self._get_user_communication_profile(user_id)
            
            # Analizar sentimiento actual si hay contenido
            if request.body:
                content = request.body.decode('utf-8')
                sentiment_analysis = self._analyze_content_sentiment(content, user_id)
                
                # Optimizar contenido si es necesario
                if sentiment_analysis['sentiment_label'] == 'negative':
                    optimized_content = self._optimize_negative_sentiment_content(content)
                    # Aquí podrías modificar la respuesta o registrar la optimización
                
                # Registrar análisis para aprendizaje
                self._record_communication_analysis(user_id, content, sentiment_analysis)
            
            # Agregar headers de optimización si es necesario
            if hasattr(response, 'headers'):
                response.headers['X-Communication-Optimized'] = 'true'
                response.headers['X-User-Profile'] = json.dumps(user_profile)
                
        except Exception as e:
            logger.error(f"Error optimizing communication: {e}")
    
    def _get_user_communication_profile(self, user_id: int) -> Dict[str, Any]:
        """Obtiene el perfil de comunicación del usuario."""
        cache_key = f"comm_profile_{user_id}"
        profile = cache.get(cache_key)
        
        if not profile:
            try:
                person = Person.objects.get(id=user_id)
                
                # Obtener historial de notificaciones
                notifications = Notification.objects.filter(
                    recipient_id=user_id
                ).order_by('-created_at')[:20]
                
                # Analizar patrones
                response_rate = self._calculate_response_rate(notifications)
                preferred_channels = self._get_preferred_channels(notifications)
                activity_patterns = self._get_activity_patterns(notifications)
                
                profile = {
                    'user_id': user_id,
                    'preferred_language': person.preferred_language or 'es_MX',
                    'response_rate': response_rate,
                    'preferred_channels': preferred_channels,
                    'activity_patterns': activity_patterns,
                    'communication_style': self._infer_communication_style(person),
                    'last_optimization': timezone.now().isoformat()
                }
                
                cache.set(cache_key, profile, self.optimization_cache_ttl)
                
            except Person.DoesNotExist:
                profile = self._get_default_profile(user_id)
        
        return profile
    
    def _calculate_response_rate(self, notifications) -> float:
        """Calcula la tasa de respuesta del usuario."""
        if not notifications:
            return 0.5  # Tasa por defecto
        
        responded = sum(1 for n in notifications if n.status == 'SENT')
        return responded / len(notifications)
    
    def _get_preferred_channels(self, notifications) -> list:
        """Obtiene los canales preferidos del usuario."""
        if not notifications:
            return ['email', 'whatsapp', 'telegram']
        
        channel_counts = {}
        for notification in notifications:
            channel = notification.channel
            channel_counts[channel] = channel_counts.get(channel, 0) + 1
        
        # Ordenar por frecuencia
        sorted_channels = sorted(
            channel_counts.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        return [channel for channel, _ in sorted_channels]
    
    def _get_activity_patterns(self, notifications) -> Dict[str, Any]:
        """Obtiene los patrones de actividad del usuario."""
        if not notifications:
            return {
                'peak_hours': [9, 10, 11, 14, 15, 16],
                'quiet_hours': [0, 1, 2, 3, 4, 5, 6, 7, 8, 22, 23],
                'timezone': 'America/Mexico_City'
            }
        
        hours = [n.created_at.hour for n in notifications]
        hour_counts = {}
        
        for hour in hours:
            hour_counts[hour] = hour_counts.get(hour, 0) + 1
        
        if hour_counts:
            max_count = max(hour_counts.values())
            peak_hours = [
                hour for hour, count in hour_counts.items() 
                if count >= max_count * 0.8
            ]
            
            min_count = min(hour_counts.values())
            quiet_hours = [
                hour for hour, count in hour_counts.items() 
                if count <= min_count * 1.2
            ]
        else:
            peak_hours = [9, 10, 11, 14, 15, 16]
            quiet_hours = [0, 1, 2, 3, 4, 5, 6, 7, 8, 22, 23]
        
        return {
            'peak_hours': peak_hours,
            'quiet_hours': quiet_hours,
            'timezone': 'America/Mexico_City'
        }
    
    def _infer_communication_style(self, person: Person) -> str:
        """Infiere el estilo de comunicación del usuario."""
        # Basarse en datos de personalidad si están disponibles
        if person.personality_data:
            personality = person.personality_data
            if personality.get('extraversion', 0) > 0.7:
                return 'extroverted'
            elif personality.get('introversion', 0) > 0.7:
                return 'introverted'
        
        # Basarse en experiencia
        if person.experience_years and person.experience_years > 5:
            return 'professional'
        elif person.skills and len(person.skills) > 10:
            return 'detailed'
        else:
            return 'standard'
    
    def _analyze_content_sentiment(self, content: str, user_id: int) -> Dict[str, Any]:
        """Analiza el sentimiento del contenido."""
        try:
            # Usar el analizador de sentimientos existente
            sentiment_result = self.sentiment_analyzer.analyze_text_sentiment(content, user_id)
            
            return {
                'sentiment_score': sentiment_result.sentiment_score,
                'sentiment_label': sentiment_result.sentiment_label,
                'confidence': sentiment_result.confidence,
                'categories': sentiment_result.categories,
                'keywords': sentiment_result.keywords,
                'timestamp': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return {
                'sentiment_score': 0.0,
                'sentiment_label': 'neutral',
                'confidence': 0.5,
                'categories': {},
                'keywords': [],
                'timestamp': timezone.now().isoformat()
            }
    
    def _optimize_negative_sentiment_content(self, content: str) -> str:
        """Optimiza contenido para sentimientos negativos."""
        # Agregar elementos empáticos
        empathetic_phrases = [
            "Entiendo que esto puede ser frustrante",
            "Estamos aquí para ayudarte",
            "Tu experiencia es importante para nosotros",
            "Apreciamos tu paciencia"
        ]
        
        import random
        optimized_content = f"{random.choice(empathetic_phrases)}. {content}"
        
        return optimized_content
    
    def _record_communication_analysis(self, user_id: int, content: str, analysis: Dict[str, Any]):
        """Registra el análisis de comunicación para aprendizaje."""
        try:
            # Guardar en caché para análisis posterior
            cache_key = f"comm_analysis_{user_id}_{timezone.now().strftime('%Y%m%d')}"
            
            existing_analyses = cache.get(cache_key, [])
            existing_analyses.append({
                'content': content[:100],  # Primeros 100 caracteres
                'analysis': analysis,
                'timestamp': timezone.now().isoformat()
            })
            
            # Mantener solo los últimos 10 análisis
            if len(existing_analyses) > 10:
                existing_analyses = existing_analyses[-10:]
            
            cache.set(cache_key, existing_analyses, 86400)  # 24 horas
            
        except Exception as e:
            logger.error(f"Error recording communication analysis: {e}")
    
    def _get_default_profile(self, user_id: int) -> Dict[str, Any]:
        """Obtiene un perfil por defecto."""
        return {
            'user_id': user_id,
            'preferred_language': 'es_MX',
            'response_rate': 0.5,
            'preferred_channels': ['email', 'whatsapp', 'telegram'],
            'activity_patterns': {
                'peak_hours': [9, 10, 11, 14, 15, 16],
                'quiet_hours': [0, 1, 2, 3, 4, 5, 6, 7, 8, 22, 23],
                'timezone': 'America/Mexico_City'
            },
            'communication_style': 'standard',
            'last_optimization': timezone.now().isoformat()
        }

class SentimentAwareNotificationMiddleware:
    """
    Middleware que ajusta las notificaciones basándose en sentimientos.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.sentiment_analyzer = SentimentAnalyzer()
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Si es una respuesta de notificación, optimizarla
        if self._is_notification_response(response):
            self._optimize_notification_response(request, response)
        
        return response
    
    def _is_notification_response(self, response) -> bool:
        """Determina si la respuesta es de una notificación."""
        if hasattr(response, 'content'):
            try:
                content = json.loads(response.content)
                return 'notification' in str(content).lower()
            except:
                pass
        return False
    
    def _optimize_notification_response(self, request, response):
        """Optimiza la respuesta de notificación."""
        try:
            if not request.user.is_authenticated:
                return
            
            # Obtener perfil del usuario
            user_profile = self._get_user_communication_profile(request.user.id)
            
            # Ajustar respuesta basándose en el perfil
            if user_profile['sentiment_label'] == 'negative':
                # Para usuarios con sentimiento negativo, ser más empático
                self._add_empathetic_headers(response)
            elif user_profile['sentiment_label'] == 'positive':
                # Para usuarios con sentimiento positivo, ser más celebrativo
                self._add_celebratory_headers(response)
            
            # Agregar información de optimización
            if hasattr(response, 'headers'):
                response.headers['X-Communication-Profile'] = json.dumps(user_profile)
                
        except Exception as e:
            logger.error(f"Error optimizing notification response: {e}")
    
    def _add_empathetic_headers(self, response):
        """Agrega headers empáticos a la respuesta."""
        if hasattr(response, 'headers'):
            response.headers['X-Communication-Tone'] = 'empathetic'
            response.headers['X-Response-Priority'] = 'high'
    
    def _add_celebratory_headers(self, response):
        """Agrega headers celebrativos a la respuesta."""
        if hasattr(response, 'headers'):
            response.headers['X-Communication-Tone'] = 'celebratory'
            response.headers['X-Response-Priority'] = 'normal'
    
    def _get_user_communication_profile(self, user_id: int) -> Dict[str, Any]:
        """Obtiene el perfil de comunicación del usuario."""
        # Implementación simplificada
        return {
            'user_id': user_id,
            'sentiment_label': 'neutral',
            'preferred_channels': ['email', 'whatsapp'],
            'response_rate': 0.7
        }

# Función de utilidad para optimizar notificaciones
def optimize_notification_for_user(user_id: int, 
                                 notification_type: str, 
                                 content: str,
                                 business_unit: str = None) -> Dict[str, Any]:
    """
    Optimiza una notificación para un usuario específico.
    
    Args:
        user_id: ID del usuario
        notification_type: Tipo de notificación
        content: Contenido de la notificación
        business_unit: Unidad de negocio (opcional)
    
    Returns:
        Diccionario con la notificación optimizada
    """
    try:
        # Obtener perfil del usuario
        cache_key = f"comm_profile_{user_id}"
        user_profile = cache.get(cache_key)
        
        if not user_profile:
            # Crear perfil por defecto
            user_profile = {
                'preferred_language': 'es_MX',
                'response_rate': 0.5,
                'preferred_channels': ['email', 'whatsapp', 'telegram'],
                'communication_style': 'standard'
            }
        
        # Analizar sentimiento del contenido
        sentiment_analyzer = SentimentAnalyzer()
        sentiment_result = sentiment_analyzer.analyze_text_sentiment(content, user_id)
        
        # Optimizar contenido basándose en sentimiento
        optimized_content = content
        if sentiment_result.sentiment_label == 'negative':
            optimized_content = f"Entiendo que esto puede ser frustrante. {content}"
        elif sentiment_result.sentiment_label == 'positive':
            optimized_content = f"¡Excelente! {content}"
        
        # Determinar canal óptimo
        optimal_channel = user_profile['preferred_channels'][0] if user_profile['preferred_channels'] else 'email'
        
        # Ajustar basándose en sentimiento
        if sentiment_result.sentiment_label == 'negative':
            # Para sentimientos negativos, priorizar canales más personales
            if 'whatsapp' in user_profile['preferred_channels']:
                optimal_channel = 'whatsapp'
            elif 'telegram' in user_profile['preferred_channels']:
                optimal_channel = 'telegram'
        
        return {
            'user_id': user_id,
            'original_content': content,
            'optimized_content': optimized_content,
            'optimal_channel': optimal_channel,
            'sentiment_analysis': {
                'score': sentiment_result.sentiment_score,
                'label': sentiment_result.sentiment_label,
                'confidence': sentiment_result.confidence
            },
            'user_profile': user_profile,
            'optimization_timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error optimizing notification for user {user_id}: {e}")
        return {
            'user_id': user_id,
            'original_content': content,
            'optimized_content': content,
            'optimal_channel': 'email',
            'error': str(e)
        } 