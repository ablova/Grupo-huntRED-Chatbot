"""
ANALYTICS PREDICTIVO DE GAMIFICACIÓN - Grupo huntRED®
Sistema inteligente para predecir engagement, optimizar recompensas y prevenir abandono
"""

import logging
import json
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import asyncio
from functools import lru_cache

from django.utils import timezone
from django.core.cache import cache

from app.models import Person, EnhancedNetworkGamificationProfile
from app.ats.utils.cache.advanced_cache_system import advanced_cache, cache_analytics

logger = logging.getLogger(__name__)

@dataclass
class UserEngagementMetrics:
    """Métricas de engagement del usuario"""
    user_id: str
    session_duration: float = 0.0
    actions_per_session: int = 0
    time_between_actions: float = 0.0
    completion_rate: float = 0.0
    reward_response_rate: float = 0.0
    last_activity: datetime = field(default_factory=timezone.now)
    engagement_score: float = 0.0
    abandonment_risk: float = 0.0

@dataclass
class RewardOptimization:
    """Optimización de recompensas"""
    reward_type: str
    effectiveness_score: float
    user_segment: str
    optimal_timing: str
    optimal_value: int
    success_rate: float

class PredictiveGamificationAnalytics:
    """
    Sistema de analytics predictivo para gamificación
    """
    
    def __init__(self):
        self.engagement_thresholds = {
            'high': 0.8,
            'medium': 0.6,
            'low': 0.4,
            'critical': 0.2
        }
        
        self.abandonment_risk_factors = {
            'inactivity_days': 0.3,
            'low_completion_rate': 0.25,
            'no_reward_response': 0.2,
            'short_sessions': 0.15,
            'high_bounce_rate': 0.1
        }
        
        # Cache para métricas
        self.metrics_cache = {}
        self.prediction_cache = {}
        
        # Configuración de generaciones
        self.generation_profiles = {
            'millennials': {
                'preferred_rewards': ['instant_gratification', 'social_recognition', 'achievement_badges'],
                'optimal_timing': 'immediate',
                'message_style': 'casual_emoji',
                'engagement_patterns': ['quick_wins', 'social_sharing', 'progressive_challenges']
            },
            'gen_x': {
                'preferred_rewards': ['value_proposition', 'career_advancement', 'expertise_recognition'],
                'optimal_timing': 'milestone',
                'message_style': 'professional_value',
                'engagement_patterns': ['goal_oriented', 'skill_development', 'mentorship']
            },
            'baby_boomers': {
                'preferred_rewards': ['stability_assurance', 'experience_recognition', 'mentorship_opportunities'],
                'optimal_timing': 'completion',
                'message_style': 'trust_building',
                'engagement_patterns': ['step_by_step', 'confidence_building', 'support_network']
            }
        }
    
    @cache_analytics(ttl=1800)
    async def predict_user_engagement(self, user_id: str) -> UserEngagementMetrics:
        """
        Predice el nivel de engagement de un usuario
        """
        try:
            # Obtener datos del usuario
            user_data = await self._get_user_activity_data(user_id)
            
            # Calcular métricas de engagement
            engagement_metrics = await self._calculate_engagement_metrics(user_data)
            
            # Predecir score de engagement
            engagement_score = await self._predict_engagement_score(engagement_metrics)
            
            # Calcular riesgo de abandono
            abandonment_risk = await self._calculate_abandonment_risk(engagement_metrics)
            
            # Crear objeto de métricas
            metrics = UserEngagementMetrics(
                user_id=user_id,
                session_duration=engagement_metrics.get('avg_session_duration', 0),
                actions_per_session=engagement_metrics.get('avg_actions_per_session', 0),
                time_between_actions=engagement_metrics.get('avg_time_between_actions', 0),
                completion_rate=engagement_metrics.get('completion_rate', 0),
                reward_response_rate=engagement_metrics.get('reward_response_rate', 0),
                last_activity=engagement_metrics.get('last_activity', timezone.now()),
                engagement_score=engagement_score,
                abandonment_risk=abandonment_risk
            )
            
            # Cachear resultados
            cache_key = f"engagement_metrics:{user_id}"
            advanced_cache.set(cache_key, metrics.__dict__, ttl=3600, tags=['gamification', 'analytics'])
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error prediciendo engagement para usuario {user_id}: {e}")
            return UserEngagementMetrics(user_id=user_id)
    
    @cache_analytics(ttl=3600)
    async def optimize_rewards_for_user(self, user_id: str) -> List[RewardOptimization]:
        """
        Optimiza recompensas para un usuario específico
        """
        try:
            # Obtener perfil del usuario
            user_profile = await self._get_user_profile(user_id)
            
            # Determinar generación
            generation = self._detect_user_generation(user_profile)
            
            # Obtener historial de recompensas
            reward_history = await self._get_reward_history(user_id)
            
            # Analizar efectividad de recompensas
            reward_effectiveness = await self._analyze_reward_effectiveness(reward_history)
            
            # Generar optimizaciones
            optimizations = []
            
            for reward_type in self.generation_profiles[generation]['preferred_rewards']:
                effectiveness = reward_effectiveness.get(reward_type, 0.5)
                
                optimization = RewardOptimization(
                    reward_type=reward_type,
                    effectiveness_score=effectiveness,
                    user_segment=generation,
                    optimal_timing=self.generation_profiles[generation]['optimal_timing'],
                    optimal_value=self._calculate_optimal_reward_value(effectiveness),
                    success_rate=effectiveness
                )
                
                optimizations.append(optimization)
            
            # Ordenar por efectividad
            optimizations.sort(key=lambda x: x.effectiveness_score, reverse=True)
            
            return optimizations
            
        except Exception as e:
            logger.error(f"Error optimizando recompensas para usuario {user_id}: {e}")
            return []
    
    async def predict_abandonment_risk(self, user_id: str) -> Dict[str, Any]:
        """
        Predice el riesgo de abandono de un usuario
        """
        try:
            # Obtener métricas de engagement
            engagement_metrics = await self.predict_user_engagement(user_id)
            
            # Calcular factores de riesgo
            risk_factors = await self._calculate_risk_factors(user_id, engagement_metrics)
            
            # Determinar nivel de riesgo
            risk_level = self._determine_risk_level(engagement_metrics.abandonment_risk)
            
            # Generar recomendaciones
            recommendations = await self._generate_retention_recommendations(
                user_id, engagement_metrics, risk_level
            )
            
            return {
                'user_id': user_id,
                'abandonment_risk': engagement_metrics.abandonment_risk,
                'risk_level': risk_level,
                'risk_factors': risk_factors,
                'recommendations': recommendations,
                'predicted_abandonment_date': self._predict_abandonment_date(engagement_metrics),
                'confidence_score': self._calculate_prediction_confidence(engagement_metrics)
            }
            
        except Exception as e:
            logger.error(f"Error prediciendo riesgo de abandono para usuario {user_id}: {e}")
            return {'user_id': user_id, 'abandonment_risk': 0.5, 'risk_level': 'unknown'}
    
    async def generate_retention_message(self, user_id: str, risk_level: str) -> str:
        """
        Genera mensaje de retención personalizado por generación
        """
        try:
            # Obtener perfil del usuario
            user_profile = await self._get_user_profile(user_id)
            generation = self._detect_user_generation(user_profile)
            
            # Obtener métricas de engagement
            engagement_metrics = await self.predict_user_engagement(user_id)
            
            # Generar mensaje según generación y nivel de riesgo
            if generation == 'millennials':
                return self._generate_millennial_message(risk_level, engagement_metrics)
            elif generation == 'gen_x':
                return self._generate_gen_x_message(risk_level, engagement_metrics)
            else:  # baby_boomers
                return self._generate_boomer_message(risk_level, engagement_metrics)
                
        except Exception as e:
            logger.error(f"Error generando mensaje de retención: {e}")
            return "¡No te pierdas las mejores oportunidades! Continúa tu proceso."
    
    async def get_engagement_insights(self, business_unit_id: str = None) -> Dict[str, Any]:
        """
        Obtiene insights de engagement para toda la plataforma o una BU específica
        """
        try:
            # Obtener métricas agregadas
            aggregated_metrics = await self._get_aggregated_engagement_metrics(business_unit_id)
            
            # Calcular tendencias
            trends = await self._calculate_engagement_trends(business_unit_id)
            
            # Identificar segmentos de usuarios
            user_segments = await self._identify_user_segments(business_unit_id)
            
            # Generar recomendaciones estratégicas
            strategic_recommendations = await self._generate_strategic_recommendations(
                aggregated_metrics, trends, user_segments
            )
            
            return {
                'aggregated_metrics': aggregated_metrics,
                'trends': trends,
                'user_segments': user_segments,
                'strategic_recommendations': strategic_recommendations,
                'generated_at': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo insights de engagement: {e}")
            return {}
    
    # Métodos privados de análisis
    
    async def _get_user_activity_data(self, user_id: str) -> Dict[str, Any]:
        """Obtiene datos de actividad del usuario"""
        try:
            # Obtener de cache primero
            cache_key = f"user_activity:{user_id}"
            cached_data = advanced_cache.get(cache_key)
            if cached_data:
                return cached_data
            
            # Obtener datos de la base de datos
            user = await self._get_user(user_id)
            if not user:
                return {}
            
            # Obtener perfil de gamificación
            gamification_profile = await self._get_gamification_profile(user)
            
            # Obtener historial de actividades
            activity_history = await self._get_activity_history(user_id)
            
            # Obtener métricas de sesión
            session_metrics = await self._get_session_metrics(user_id)
            
            data = {
                'user': user,
                'gamification_profile': gamification_profile,
                'activity_history': activity_history,
                'session_metrics': session_metrics
            }
            
            # Cachear datos
            advanced_cache.set(cache_key, data, ttl=1800, tags=['user_activity'])
            
            return data
            
        except Exception as e:
            logger.error(f"Error obteniendo datos de actividad: {e}")
            return {}
    
    async def _calculate_engagement_metrics(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calcula métricas de engagement"""
        try:
            if not user_data:
                return {}
            
            activity_history = user_data.get('activity_history', [])
            session_metrics = user_data.get('session_metrics', {})
            
            # Calcular métricas básicas
            total_sessions = len(session_metrics.get('sessions', []))
            total_actions = sum(session.get('action_count', 0) for session in session_metrics.get('sessions', []))
            
            avg_session_duration = (
                sum(session.get('duration', 0) for session in session_metrics.get('sessions', [])) / 
                max(total_sessions, 1)
            )
            
            avg_actions_per_session = total_actions / max(total_sessions, 1)
            
            # Calcular tasa de completación
            completed_tasks = sum(1 for activity in activity_history if activity.get('completed', False))
            total_tasks = len(activity_history)
            completion_rate = completed_tasks / max(total_tasks, 1)
            
            # Calcular respuesta a recompensas
            reward_activities = [a for a in activity_history if a.get('type') == 'reward']
            responded_rewards = sum(1 for a in reward_activities if a.get('responded', False))
            reward_response_rate = responded_rewards / max(len(reward_activities), 1)
            
            return {
                'avg_session_duration': avg_session_duration,
                'avg_actions_per_session': avg_actions_per_session,
                'completion_rate': completion_rate,
                'reward_response_rate': reward_response_rate,
                'total_sessions': total_sessions,
                'total_actions': total_actions,
                'last_activity': activity_history[-1].get('timestamp') if activity_history else timezone.now()
            }
            
        except Exception as e:
            logger.error(f"Error calculando métricas de engagement: {e}")
            return {}
    
    async def _predict_engagement_score(self, metrics: Dict[str, Any]) -> float:
        """Predice score de engagement usando ML simple"""
        try:
            # Factores de peso para el score
            weights = {
                'session_duration': 0.2,
                'actions_per_session': 0.25,
                'completion_rate': 0.3,
                'reward_response_rate': 0.25
            }
            
            # Normalizar métricas
            normalized_metrics = {
                'session_duration': min(metrics.get('avg_session_duration', 0) / 300, 1.0),  # 5 min = 1.0
                'actions_per_session': min(metrics.get('avg_actions_per_session', 0) / 10, 1.0),  # 10 actions = 1.0
                'completion_rate': metrics.get('completion_rate', 0),
                'reward_response_rate': metrics.get('reward_response_rate', 0)
            }
            
            # Calcular score ponderado
            engagement_score = sum(
                normalized_metrics[metric] * weight 
                for metric, weight in weights.items()
            )
            
            return min(max(engagement_score, 0.0), 1.0)
            
        except Exception as e:
            logger.error(f"Error prediciendo score de engagement: {e}")
            return 0.5
    
    async def _calculate_abandonment_risk(self, metrics: Dict[str, Any]) -> float:
        """Calcula riesgo de abandono"""
        try:
            risk_score = 0.0
            
            # Factor: Inactividad
            days_inactive = (timezone.now() - metrics.get('last_activity', timezone.now())).days
            if days_inactive > 7:
                risk_score += self.abandonment_risk_factors['inactivity_days']
            
            # Factor: Baja tasa de completación
            if metrics.get('completion_rate', 0) < 0.3:
                risk_score += self.abandonment_risk_factors['low_completion_rate']
            
            # Factor: No respuesta a recompensas
            if metrics.get('reward_response_rate', 0) < 0.2:
                risk_score += self.abandonment_risk_factors['no_reward_response']
            
            # Factor: Sesiones cortas
            if metrics.get('avg_session_duration', 0) < 60:  # Menos de 1 minuto
                risk_score += self.abandonment_risk_factors['short_sessions']
            
            return min(risk_score, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculando riesgo de abandono: {e}")
            return 0.5
    
    def _detect_user_generation(self, user_profile: Dict[str, Any]) -> str:
        """Detecta la generación del usuario basado en edad"""
        try:
            birth_year = user_profile.get('birth_year')
            if not birth_year:
                return 'gen_x'  # Default
            
            current_year = timezone.now().year
            age = current_year - birth_year
            
            if age < 30:
                return 'millennials'
            elif age < 55:
                return 'gen_x'
            else:
                return 'baby_boomers'
                
        except Exception as e:
            logger.error(f"Error detectando generación: {e}")
            return 'gen_x'
    
    def _generate_millennial_message(self, risk_level: str, metrics: UserEngagementMetrics) -> str:
        """Genera mensaje para millennials"""
        messages = {
            'low': [
                "🚀 ¡Sigues en racha! ¿Listo para el siguiente nivel?",
                "🔥 Tu perfil está destacando, ¿quieres ver las nuevas oportunidades?",
                "⚡ ¡Mantén el momentum! Solo faltan unos pasos para completar tu perfil."
            ],
            'medium': [
                "💪 ¡No te rindas! Estás muy cerca de encontrar tu oportunidad ideal.",
                "🎯 Tu objetivo está a la vista, ¿continuamos?",
                "✨ ¡Eres parte de algo grande! Completa tu perfil y descubre las mejores ofertas."
            ],
            'high': [
                "🎉 ¡Es tu momento! No dejes que las mejores oportunidades pasen de largo.",
                "💎 Eres un talento valioso, ¡demuéstralo completando tu perfil!",
                "🌟 ¡Únete a los que ya encontraron su camino! Solo faltan unos minutos."
            ],
            'critical': [
                "🚨 ¡ÚLTIMA OPORTUNIDAD! Las mejores ofertas se están cerrando.",
                "🔥 ¡NO TE LO PIERDAS! Tu perfil está 80% completo, ¡termina ahora!",
                "⚡ ¡ACCIÓN INMEDIATA! Solo 3 pasos para acceder a ofertas exclusivas."
            ]
        }
        
        return np.random.choice(messages.get(risk_level, messages['medium']))
    
    def _generate_gen_x_message(self, risk_level: str, metrics: UserEngagementMetrics) -> str:
        """Genera mensaje para Gen X"""
        messages = {
            'low': [
                "Tu experiencia es valiosa. ¿Quieres ver las oportunidades que se ajustan a tu perfil?",
                "Estás muy cerca de encontrar la posición ideal para tu carrera. ¿Continuamos?",
                "Tu perfil profesional está destacando. ¿Te gustaría ver las ofertas disponibles?"
            ],
            'medium': [
                "No dejes que tu experiencia se desperdicie. Completa tu perfil y accede a mejores oportunidades.",
                "Tu trayectoria profesional merece la mejor posición. ¿Quieres ver las ofertas exclusivas?",
                "Estás a un paso de encontrar la oportunidad que impulse tu carrera. ¿Continuamos?"
            ],
            'high': [
                "Tu experiencia es única. No dejes que las mejores oportunidades pasen de largo.",
                "Eres un profesional valioso. Completa tu perfil y accede a ofertas de alto nivel.",
                "Tu carrera merece lo mejor. Termina tu perfil y descubre las oportunidades que te esperan."
            ],
            'critical': [
                "¡ÚLTIMA OPORTUNIDAD! Las posiciones de alto nivel se están cerrando.",
                "¡NO TE LO PIERDAS! Tu experiencia es única, completa tu perfil ahora.",
                "¡ACCIÓN INMEDIATA! Solo faltan unos pasos para acceder a las mejores ofertas."
            ]
        }
        
        return np.random.choice(messages.get(risk_level, messages['medium']))
    
    def _generate_boomer_message(self, risk_level: str, metrics: UserEngagementMetrics) -> str:
        """Genera mensaje para Baby Boomers"""
        messages = {
            'low': [
                "Su experiencia es invaluable. ¿Le gustaría ver las oportunidades disponibles?",
                "Está muy cerca de encontrar la posición ideal. ¿Continuamos juntos?",
                "Su perfil profesional es excepcional. ¿Quiere ver las ofertas que se ajustan a su experiencia?"
            ],
            'medium': [
                "Su trayectoria profesional merece lo mejor. Complete su perfil y acceda a oportunidades exclusivas.",
                "Su experiencia es única. No deje que las mejores oportunidades pasen de largo.",
                "Está a un paso de encontrar la posición que valore su experiencia. ¿Continuamos?"
            ],
            'high': [
                "Su experiencia es extraordinaria. Complete su perfil y descubra las mejores ofertas.",
                "Es un profesional excepcional. No deje que las oportunidades se pierdan.",
                "Su carrera merece la mejor posición. Termine su perfil y acceda a ofertas exclusivas."
            ],
            'critical': [
                "¡ÚLTIMA OPORTUNIDAD! Las posiciones de alto nivel se están cerrando.",
                "¡NO SE LO PIERDA! Su experiencia es única, complete su perfil ahora.",
                "¡ACCIÓN INMEDIATA! Solo faltan unos pasos para acceder a las mejores ofertas."
            ]
        }
        
        return np.random.choice(messages.get(risk_level, messages['medium']))
    
    # Métodos auxiliares
    
    async def _get_user(self, user_id: str) -> Optional[Person]:
        """Obtiene usuario de la base de datos"""
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM app_person WHERE id = %s", [user_id])
                row = cursor.fetchone()
                if row:
                    return Person.objects.get(id=user_id)
            return None
        except Exception as e:
            logger.error(f"Error obteniendo usuario: {e}")
            return None
    
    async def _get_gamification_profile(self, user: Person) -> Optional[Dict[str, Any]]:
        """Obtiene perfil de gamificación del usuario"""
        try:
            profile = EnhancedNetworkGamificationProfile.objects.filter(person=user).first()
            if profile:
                return {
                    'level': profile.level,
                    'points': profile.points,
                    'achievements': profile.achievements,
                    'last_activity': profile.last_activity
                }
            return None
        except Exception as e:
            logger.error(f"Error obteniendo perfil de gamificación: {e}")
            return None
    
    async def _get_activity_history(self, user_id: str) -> List[Dict[str, Any]]:
        """Obtiene historial de actividades del usuario"""
        try:
            # Simular datos de actividad (en producción, obtener de la base de datos)
            return [
                {
                    'type': 'profile_update',
                    'completed': True,
                    'timestamp': timezone.now() - timedelta(hours=2),
                    'responded': True
                },
                {
                    'type': 'reward',
                    'completed': True,
                    'timestamp': timezone.now() - timedelta(hours=1),
                    'responded': True
                }
            ]
        except Exception as e:
            logger.error(f"Error obteniendo historial de actividades: {e}")
            return []
    
    async def _get_session_metrics(self, user_id: str) -> Dict[str, Any]:
        """Obtiene métricas de sesión del usuario"""
        try:
            # Simular datos de sesión (en producción, obtener de la base de datos)
            return {
                'sessions': [
                    {
                        'duration': 300,  # 5 minutos
                        'action_count': 8,
                        'timestamp': timezone.now() - timedelta(hours=1)
                    },
                    {
                        'duration': 180,  # 3 minutos
                        'action_count': 5,
                        'timestamp': timezone.now() - timedelta(hours=2)
                    }
                ]
            }
        except Exception as e:
            logger.error(f"Error obteniendo métricas de sesión: {e}")
            return {'sessions': []}

# Instancia global
predictive_analytics = PredictiveGamificationAnalytics() 