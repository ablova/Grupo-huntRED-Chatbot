"""
Sistema de Notificaciones Inteligentes para Grupo huntRED®

Este módulo proporciona un sistema de notificaciones inteligentes con:
- Personalización contextual basada en ML
- Timing inteligente de envío
- Análisis de engagement
- Optimización automática de contenido
"""
import asyncio
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Q, Count, Avg
from django.core.cache import cache

from app.models import (
    Person, Notification, BusinessUnit, Application, 
    Event, Interview, ClientFeedback, GamificationProfile
)
from app.ats.integrations.notifications.core.service import NotificationService
from app.ats.ml.recommendation_engine import RecommendationEngine
from app.ats.utils.cache import cache_result

logger = logging.getLogger(__name__)

class IntelligentNotificationService:
    """
    Servicio de notificaciones inteligentes con ML.
    
    Proporciona funcionalidades avanzadas:
    - Personalización contextual
    - Timing inteligente
    - Análisis de engagement
    - Optimización automática
    """
    
    def __init__(self, business_unit: Optional[BusinessUnit] = None):
        self.business_unit = business_unit
        self.notification_service = NotificationService()
        self.recommendation_engine = RecommendationEngine()
        
    async def send_intelligent_notification(
        self,
        recipient: Person,
        notification_type: str,
        context: Dict[str, Any],
        channels: List[str] = None,
        priority: str = 'normal',
        force_timing: bool = False
    ) -> Dict[str, Any]:
        """
        Envía una notificación inteligente optimizada.
        
        Args:
            recipient: Destinatario de la notificación
            notification_type: Tipo de notificación
            context: Contexto de la notificación
            channels: Canales de envío
            priority: Prioridad de la notificación
            force_timing: Forzar envío inmediato
            
        Returns:
            Dict con el resultado del envío
        """
        try:
            # Analizar comportamiento del usuario
            user_behavior = await self._analyze_user_behavior(recipient)
            
            # Personalizar contenido
            personalized_context = await self._personalize_content(
                recipient, notification_type, context, user_behavior
            )
            
            # Determinar timing óptimo
            optimal_timing = await self._get_optimal_timing(
                recipient, notification_type, user_behavior
            )
            
            # Seleccionar canales óptimos
            optimal_channels = await self._get_optimal_channels(
                recipient, notification_type, user_behavior
            )
            
            # Aplicar timing si no se fuerza
            if not force_timing and optimal_timing > timezone.now():
                # Programar envío para timing óptimo
                return await self._schedule_notification(
                    recipient, notification_type, personalized_context,
                    optimal_channels, optimal_timing
                )
            
            # Enviar notificación
            result = await self.notification_service.send_notification(
                recipient=recipient,
                template_name=notification_type,
                context=personalized_context,
                channels=optimal_channels or channels,
                notification_type=f'intelligent_{notification_type}',
                business_unit=self.business_unit
            )
            
            # Registrar métricas
            await self._record_notification_metrics(
                recipient, notification_type, result, user_behavior
            )
            
            return {
                'success': True,
                'personalized': True,
                'optimal_timing_used': not force_timing,
                'channels_used': optimal_channels,
                'result': result
            }
            
        except Exception as e:
            logger.error(f"Error en send_intelligent_notification: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def send_contextual_reminder(
        self,
        recipient: Person,
        reminder_type: str,
        related_object: Any,
        urgency_level: str = 'normal'
    ) -> Dict[str, Any]:
        """
        Envía recordatorio contextual inteligente.
        
        Args:
            recipient: Destinatario
            reminder_type: Tipo de recordatorio
            related_object: Objeto relacionado (Application, Interview, etc.)
            urgency_level: Nivel de urgencia
            
        Returns:
            Dict con el resultado
        """
        try:
            # Analizar contexto del recordatorio
            context_analysis = await self._analyze_reminder_context(
                recipient, reminder_type, related_object
            )
            
            # Determinar si el recordatorio es necesario
            if not context_analysis['should_send']:
                return {
                    'success': True,
                    'skipped': True,
                    'reason': context_analysis['skip_reason']
                }
            
            # Personalizar recordatorio
            personalized_context = await self._personalize_reminder(
                recipient, reminder_type, related_object, context_analysis
            )
            
            # Ajustar urgencia según análisis
            adjusted_urgency = await self._adjust_urgency_level(
                urgency_level, context_analysis
            )
            
            # Enviar recordatorio
            result = await self.send_intelligent_notification(
                recipient=recipient,
                notification_type=f'reminder_{reminder_type}',
                context=personalized_context,
                priority=adjusted_urgency
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error en send_contextual_reminder: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def send_engagement_optimized_notification(
        self,
        recipient: Person,
        notification_type: str,
        base_context: Dict[str, Any],
        engagement_goal: str = 'increase'
    ) -> Dict[str, Any]:
        """
        Envía notificación optimizada para engagement.
        
        Args:
            recipient: Destinatario
            notification_type: Tipo de notificación
            base_context: Contexto base
            engagement_goal: Objetivo de engagement
            
        Returns:
            Dict con el resultado
        """
        try:
            # Analizar historial de engagement
            engagement_history = await self._analyze_engagement_history(recipient)
            
            # Generar variantes de contenido
            content_variants = await self._generate_content_variants(
                notification_type, base_context, engagement_history
            )
            
            # Seleccionar mejor variante
            best_variant = await self._select_best_variant(
                content_variants, engagement_history, engagement_goal
            )
            
            # Determinar timing óptimo para engagement
            engagement_timing = await self._get_engagement_timing(
                recipient, engagement_history
            )
            
            # Enviar notificación optimizada
            result = await self.send_intelligent_notification(
                recipient=recipient,
                notification_type=notification_type,
                context=best_variant,
                force_timing=False
            )
            
            # A/B testing si está habilitado
            if await self._should_ab_test(recipient):
                await self._setup_ab_test(recipient, notification_type, content_variants)
            
            return result
            
        except Exception as e:
            logger.error(f"Error en send_engagement_optimized_notification: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def send_predictive_notification(
        self,
        recipient: Person,
        prediction_type: str,
        prediction_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Envía notificación predictiva basada en ML.
        
        Args:
            recipient: Destinatario
            prediction_type: Tipo de predicción
            prediction_data: Datos de la predicción
            
        Returns:
            Dict con el resultado
        """
        try:
            # Generar predicción personalizada
            personalized_prediction = await self._generate_personalized_prediction(
                recipient, prediction_type, prediction_data
            )
            
            # Crear contexto predictivo
            predictive_context = await self._create_predictive_context(
                recipient, prediction_type, personalized_prediction
            )
            
            # Determinar probabilidad de engagement
            engagement_probability = await self._calculate_engagement_probability(
                recipient, prediction_type, personalized_prediction
            )
            
            # Solo enviar si la probabilidad es alta
            if engagement_probability < 0.3:
                return {
                    'success': True,
                    'skipped': True,
                    'reason': 'Low engagement probability',
                    'probability': engagement_probability
                }
            
            # Enviar notificación predictiva
            result = await self.send_intelligent_notification(
                recipient=recipient,
                notification_type=f'predictive_{prediction_type}',
                context=predictive_context,
                priority='high' if engagement_probability > 0.7 else 'normal'
            )
            
            return {
                **result,
                'engagement_probability': engagement_probability,
                'prediction_confidence': personalized_prediction.get('confidence', 0)
            }
            
        except Exception as e:
            logger.error(f"Error en send_predictive_notification: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    # Métodos de análisis y personalización
    
    @cache_result(ttl=3600)  # 1 hora
    async def _analyze_user_behavior(self, recipient: Person) -> Dict[str, Any]:
        """Analiza el comportamiento del usuario para personalización."""
        try:
            # Obtener historial de notificaciones
            notification_history = Notification.objects.filter(
                recipient=recipient
            ).order_by('-created_at')[:100]
            
            # Analizar patrones de respuesta
            response_patterns = await self._analyze_response_patterns(notification_history)
            
            # Analizar preferencias de canal
            channel_preferences = await self._analyze_channel_preferences(notification_history)
            
            # Analizar timing preferido
            timing_preferences = await self._analyze_timing_preferences(notification_history)
            
            # Analizar engagement general
            engagement_metrics = await self._analyze_engagement_metrics(recipient)
            
            return {
                'response_patterns': response_patterns,
                'channel_preferences': channel_preferences,
                'timing_preferences': timing_preferences,
                'engagement_metrics': engagement_metrics,
                'last_activity': await self._get_last_activity(recipient),
                'preferred_content_type': await self._get_preferred_content_type(recipient)
            }
            
        except Exception as e:
            logger.error(f"Error analizando comportamiento: {str(e)}")
            return {}
    
    async def _personalize_content(
        self,
        recipient: Person,
        notification_type: str,
        base_context: Dict[str, Any],
        user_behavior: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Personaliza el contenido de la notificación."""
        try:
            personalized_context = base_context.copy()
            
            # Personalizar saludo
            personalized_context['greeting'] = await self._get_personalized_greeting(
                recipient, user_behavior
            )
            
            # Personalizar tono
            personalized_context['tone'] = await self._get_personalized_tone(
                recipient, user_behavior
            )
            
            # Personalizar call-to-action
            personalized_context['cta'] = await self._get_personalized_cta(
                recipient, notification_type, user_behavior
            )
            
            # Agregar elementos personalizados
            personalized_context['personal_elements'] = await self._get_personal_elements(
                recipient, notification_type, user_behavior
            )
            
            # Ajustar longitud según preferencias
            personalized_context = await self._adjust_content_length(
                personalized_context, user_behavior
            )
            
            return personalized_context
            
        except Exception as e:
            logger.error(f"Error personalizando contenido: {str(e)}")
            return base_context
    
    async def _get_optimal_timing(
        self,
        recipient: Person,
        notification_type: str,
        user_behavior: Dict[str, Any]
    ) -> datetime:
        """Determina el timing óptimo para el envío."""
        try:
            timing_prefs = user_behavior.get('timing_preferences', {})
            
            # Obtener hora preferida del usuario
            preferred_hour = timing_prefs.get('preferred_hour', 10)
            preferred_day = timing_prefs.get('preferred_day', 'weekday')
            
            # Calcular timing óptimo
            now = timezone.now()
            optimal_time = now.replace(
                hour=preferred_hour,
                minute=0,
                second=0,
                microsecond=0
            )
            
            # Ajustar para día preferido
            if preferred_day == 'weekday' and optimal_time.weekday() >= 5:
                # Si es fin de semana, mover al lunes
                days_ahead = 7 - optimal_time.weekday()
                optimal_time += timedelta(days=days_ahead)
            elif preferred_day == 'weekend' and optimal_time.weekday() < 5:
                # Si es día de semana, mover al sábado
                days_ahead = 5 - optimal_time.weekday()
                optimal_time += timedelta(days=days_ahead)
            
            # Si el tiempo óptimo ya pasó hoy, programar para mañana
            if optimal_time <= now:
                optimal_time += timedelta(days=1)
            
            return optimal_time
            
        except Exception as e:
            logger.error(f"Error calculando timing óptimo: {str(e)}")
            return timezone.now() + timedelta(hours=1)
    
    async def _get_optimal_channels(
        self,
        recipient: Person,
        notification_type: str,
        user_behavior: Dict[str, Any]
    ) -> List[str]:
        """Determina los canales óptimos para el envío."""
        try:
            channel_prefs = user_behavior.get('channel_preferences', {})
            
            # Obtener canales preferidos del usuario
            preferred_channels = channel_prefs.get('preferred_channels', ['email'])
            
            # Filtrar canales disponibles
            available_channels = []
            for channel in preferred_channels:
                if await self._is_channel_available(recipient, channel):
                    available_channels.append(channel)
            
            # Si no hay canales disponibles, usar fallback
            if not available_channels:
                available_channels = ['email']
            
            # Limitar a máximo 2 canales para evitar spam
            return available_channels[:2]
            
        except Exception as e:
            logger.error(f"Error determinando canales óptimos: {str(e)}")
            return ['email']
    
    async def _analyze_reminder_context(
        self,
        recipient: Person,
        reminder_type: str,
        related_object: Any
    ) -> Dict[str, Any]:
        """Analiza el contexto de un recordatorio."""
        try:
            context_analysis = {
                'should_send': True,
                'skip_reason': None,
                'urgency_level': 'normal',
                'personalization_data': {}
            }
            
            # Verificar si ya se envió un recordatorio reciente
            recent_reminders = Notification.objects.filter(
                recipient=recipient,
                notification_type__startswith='reminder_',
                created_at__gte=timezone.now() - timedelta(hours=24)
            ).count()
            
            if recent_reminders >= 3:
                context_analysis['should_send'] = False
                context_analysis['skip_reason'] = 'Too many recent reminders'
            
            # Analizar urgencia basada en el objeto relacionado
            if hasattr(related_object, 'deadline'):
                deadline = related_object.deadline
                time_until_deadline = deadline - timezone.now()
                
                if time_until_deadline <= timedelta(hours=24):
                    context_analysis['urgency_level'] = 'high'
                elif time_until_deadline <= timedelta(days=3):
                    context_analysis['urgency_level'] = 'medium'
            
            # Agregar datos de personalización
            context_analysis['personalization_data'] = await self._get_reminder_personalization(
                recipient, reminder_type, related_object
            )
            
            return context_analysis
            
        except Exception as e:
            logger.error(f"Error analizando contexto de recordatorio: {str(e)}")
            return {'should_send': True, 'skip_reason': None, 'urgency_level': 'normal'}
    
    async def _analyze_engagement_history(self, recipient: Person) -> Dict[str, Any]:
        """Analiza el historial de engagement del usuario."""
        try:
            # Obtener notificaciones recientes
            recent_notifications = Notification.objects.filter(
                recipient=recipient,
                created_at__gte=timezone.now() - timedelta(days=30)
            )
            
            # Calcular métricas de engagement
            total_sent = recent_notifications.count()
            total_opened = recent_notifications.filter(
                metadata__opened=True
            ).count()
            
            engagement_rate = (total_opened / total_sent * 100) if total_sent > 0 else 0
            
            # Analizar tendencias
            engagement_trend = await self._calculate_engagement_trend(recipient)
            
            # Identificar patrones de respuesta
            response_patterns = await self._identify_response_patterns(recipient)
            
            return {
                'engagement_rate': engagement_rate,
                'engagement_trend': engagement_trend,
                'response_patterns': response_patterns,
                'total_notifications': total_sent,
                'opened_notifications': total_opened
            }
            
        except Exception as e:
            logger.error(f"Error analizando historial de engagement: {str(e)}")
            return {}
    
    # Métodos auxiliares
    
    async def _schedule_notification(
        self,
        recipient: Person,
        notification_type: str,
        context: Dict[str, Any],
        channels: List[str],
        scheduled_time: datetime
    ) -> Dict[str, Any]:
        """Programa una notificación para envío futuro."""
        try:
            # Crear tarea programada
            from app.tasks.notifications import send_scheduled_notification
            
            task = send_scheduled_notification.delay(
                recipient_id=recipient.id,
                notification_type=notification_type,
                context=context,
                channels=channels,
                scheduled_time=scheduled_time.isoformat()
            )
            
            return {
                'success': True,
                'scheduled': True,
                'scheduled_time': scheduled_time,
                'task_id': task.id
            }
            
        except Exception as e:
            logger.error(f"Error programando notificación: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def _record_notification_metrics(
        self,
        recipient: Person,
        notification_type: str,
        result: Dict[str, Any],
        user_behavior: Dict[str, Any]
    ) -> None:
        """Registra métricas de la notificación enviada."""
        try:
            # Guardar métricas en caché para análisis posterior
            cache_key = f"notification_metrics_{recipient.id}_{notification_type}"
            metrics = {
                'timestamp': timezone.now().isoformat(),
                'notification_type': notification_type,
                'result': result,
                'user_behavior': user_behavior,
                'channels_used': result.get('channels_used', []),
                'personalized': result.get('personalized', False)
            }
            
            cache.set(cache_key, metrics, timeout=86400)  # 24 horas
            
        except Exception as e:
            logger.error(f"Error registrando métricas: {str(e)}")
    
    async def _get_personalized_greeting(self, recipient: Person, user_behavior: Dict[str, Any]) -> str:
        """Genera un saludo personalizado."""
        try:
            # Obtener hora actual
            current_hour = timezone.now().hour
            
            if current_hour < 12:
                time_greeting = "Buenos días"
            elif current_hour < 18:
                time_greeting = "Buenas tardes"
            else:
                time_greeting = "Buenas noches"
            
            # Agregar nombre si está disponible
            if recipient.name:
                return f"{time_greeting}, {recipient.name.split()[0]}"
            else:
                return time_greeting
                
        except Exception as e:
            logger.error(f"Error generando saludo: {str(e)}")
            return "Hola"
    
    async def _get_personalized_tone(self, recipient: Person, user_behavior: Dict[str, Any]) -> str:
        """Determina el tono personalizado para la comunicación."""
        try:
            engagement_metrics = user_behavior.get('engagement_metrics', {})
            engagement_rate = engagement_metrics.get('engagement_rate', 0)
            
            if engagement_rate > 80:
                return 'friendly'
            elif engagement_rate > 50:
                return 'professional'
            else:
                return 'encouraging'
                
        except Exception as e:
            logger.error(f"Error determinando tono: {str(e)}")
            return 'professional'
    
    async def _get_personalized_cta(
        self,
        recipient: Person,
        notification_type: str,
        user_behavior: Dict[str, Any]
    ) -> str:
        """Genera un call-to-action personalizado."""
        try:
            # CTA específicos por tipo de notificación
            cta_mapping = {
                'application_update': 'Ver detalles',
                'interview_scheduled': 'Confirmar asistencia',
                'reminder_followup': 'Completar seguimiento',
                'placement_completed': 'Ver oferta'
            }
            
            base_cta = cta_mapping.get(notification_type, 'Ver más')
            
            # Personalizar según comportamiento
            engagement_rate = user_behavior.get('engagement_metrics', {}).get('engagement_rate', 0)
            
            if engagement_rate < 30:
                return f"{base_cta} - ¡Es importante!"
            elif engagement_rate > 70:
                return base_cta
            else:
                return f"{base_cta} - Te esperamos"
                
        except Exception as e:
            logger.error(f"Error generando CTA: {str(e)}")
            return 'Ver más'
    
    async def _is_channel_available(self, recipient: Person, channel: str) -> bool:
        """Verifica si un canal está disponible para el usuario."""
        try:
            if channel == 'email':
                return bool(recipient.email)
            elif channel == 'whatsapp':
                return hasattr(recipient, 'whatsapp_enabled') and recipient.whatsapp_enabled
            elif channel == 'telegram':
                return hasattr(recipient, 'telegram_enabled') and recipient.telegram_enabled
            else:
                return True
                
        except Exception as e:
            logger.error(f"Error verificando canal: {str(e)}")
            return False 