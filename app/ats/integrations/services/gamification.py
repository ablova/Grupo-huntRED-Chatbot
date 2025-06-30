# /home/pablo/app/ats/integrations/services/gamification.py
"""
Sistema de gamificación para el chatbot

Este módulo proporciona funcionalidad para gamificar la interacción
con el chatbot, incluyendo puntos, logros y desafíos.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple, Set
from datetime import datetime, timedelta
from enum import Enum, auto
from django.utils import timezone
from django.core.cache import cache
from django.db import transaction
from django.db.models import Q, F, Sum, Count, Case, When, Value, IntegerField, Max
from asgiref.sync import sync_to_async
from celery import shared_task
from app.ats.tasks.base import with_retry

from app.models import (
    Person,
    BusinessUnit,
    EnhancedNetworkGamificationProfile,
    GamificationBadge,
    UserBadge,
    GamificationEvent,
    UserChallenge
)
from app.ats.integrations.services import send_message
from app.ats.integrations.services.gamification.achievement import Achievement

logger = logging.getLogger(__name__)

class ActivityType(Enum):
    """Tipos de actividades que pueden ser gamificadas"""
    
    # Actividades de mensajería
    MESSAGE_SENT = 'message_sent'
    MESSAGE_RECEIVED = 'message_received'
    QUICK_REPLY = 'quick_reply'
    BUTTON_CLICK = 'button_click'
    
    # Actividades de evaluación
    EVALUATION_STARTED = 'evaluation_started'
    EVALUATION_COMPLETED = 'evaluation_completed'
    EVALUATION_SCORE = 'evaluation_score'
    
    # Actividades de referencia
    REFERENCE_REQUESTED = 'reference_requested'
    REFERENCE_COMPLETED = 'reference_completed'
    REFERENCE_QUALITY = 'reference_quality'
    
    # Actividades de perfil
    PROFILE_UPDATED = 'profile_updated'
    SKILL_ADDED = 'skill_added'
    EXPERIENCE_ADDED = 'experience_added'
    
    # Actividades de interacción
    MENU_ACCESS = 'menu_access'
    FEATURE_USED = 'feature_used'
    HELP_REQUESTED = 'help_requested'
    
    # Actividades de comunidad
    RECOMMENDATION_GIVEN = 'recommendation_given'
    RECOMMENDATION_RECEIVED = 'recommendation_received'
    FEEDBACK_PROVIDED = 'feedback_provided'
    
    # Actividades de CV
    CV_GENERATED = 'cv_generated'
    CV_OPTIMIZED = 'cv_optimized'
    CV_SECTION_ENHANCED = 'cv_section_enhanced'
    CV_TEMPLATE_USED = 'cv_template_used'
    CV_PERSONALITY_MATCH = 'cv_personality_match'
    CV_OPTIMIZATION_SCORE = 'cv_optimization_score'

class AchievementType(Enum):
    """Tipos de logros disponibles"""
    
    # Logros de mensajería
    MESSAGE_MILESTONE = 'message_milestone'
    QUICK_REPLY_MASTER = 'quick_reply_master'
    BUTTON_EXPERT = 'button_expert'
    
    # Logros de evaluación
    EVALUATION_NOVICE = 'evaluation_novice'
    EVALUATION_EXPERT = 'evaluation_expert'
    PERFECT_SCORE = 'perfect_score'
    
    # Logros de referencia
    REFERENCE_COLLECTOR = 'reference_collector'
    REFERENCE_QUALITY = 'reference_quality'
    REFERENCE_SPEED = 'reference_speed'
    
    # Logros de perfil
    PROFILE_COMPLETE = 'profile_complete'
    SKILL_MASTER = 'skill_master'
    EXPERIENCE_SHARER = 'experience_sharer'
    
    # Logros de interacción
    MENU_NAVIGATOR = 'menu_navigator'
    FEATURE_EXPLORER = 'feature_explorer'
    HELPFUL_USER = 'helpful_user'
    
    # Logros de comunidad
    RECOMMENDATION_GIVER = 'recommendation_giver'
    RECOMMENDATION_RECEIVER = 'recommendation_receiver'
    FEEDBACK_PROVIDER = 'feedback_provider'
    
    # Logros especiales
    DAILY_STREAK = 'daily_streak'
    WEEKLY_CHALLENGE = 'weekly_challenge'
    MONTHLY_GOAL = 'monthly_goal'
    
    # Logros de CV
    CV_CREATOR = 'cv_creator'
    CV_OPTIMIZER = 'cv_optimizer'
    CV_MASTER = 'cv_master'
    CV_PERSONALITY_EXPERT = 'cv_personality_expert'
    CV_TEMPLATE_EXPLORER = 'cv_template_explorer'
    CV_PERFECTIONIST = 'cv_perfectionist'

class Level:
    """Clase para manejar niveles de usuario"""
    
    def __init__(self, level: int, name: str, points_required: int, rewards: Dict[str, Any]):
        """
        Inicializa un nivel
        
        Args:
            level: Número de nivel
            name: Nombre del nivel
            points_required: Puntos requeridos para alcanzar el nivel
            rewards: Recompensas por alcanzar el nivel
        """
        self.level = level
        self.name = name
        self.points_required = points_required
        self.rewards = rewards

class GamificationService:
    """
    Servicio de gamificación avanzado para Grupo huntRED®
    
    Mejoras implementadas:
    - Sistema de niveles dinámico
    - Competencias en tiempo real
    - Logros personalizados por BU
    - Recompensas inteligentes
    - Analytics predictivo
    - Integración con ML
    """
    
    def __init__(self):
        self.achievements = self._initialize_achievements()
        self.user_profiles = {}
        self.competitions = {}
        self.rewards_system = self._initialize_rewards()
        self.analytics = GamificationAnalytics()
        self._initialize_competitions()
    
    def _initialize_rewards(self) -> Dict[str, Dict[str, Any]]:
        """Sistema de recompensas inteligente"""
        return {
            'points': {
                'base_multiplier': 1.0,
                'streak_bonus': 0.1,
                'difficulty_bonus': 0.2,
                'time_bonus': 0.05
            },
            'badges': {
                'unlock_thresholds': {
                    'bronze': 100,
                    'silver': 500,
                    'gold': 1000,
                    'platinum': 2500,
                    'diamond': 5000
                },
                'special_badges': {
                    'early_adopter': {'condition': 'join_date_2024', 'points': 1000},
                    'streak_master': {'condition': 'streak_30_days', 'points': 500},
                    'community_leader': {'condition': 'help_others_50', 'points': 750}
                }
            },
            'features': {
                'premium_access': {'points_required': 2000},
                'priority_support': {'points_required': 1000},
                'advanced_analytics': {'points_required': 1500},
                'custom_themes': {'points_required': 500}
            },
            'real_world': {
                'mentorship': {'points_required': 3000},
                'networking_events': {'points_required': 1500},
                'job_recommendations': {'points_required': 2500},
                'certification_discounts': {'points_required': 1000}
            }
        }
    
    def _initialize_competitions(self):
        """Inicializa competencias dinámicas"""
        try:
            # Competencia semanal de engagement
            weekly_comp = Competition(
                id="weekly_engagement_2024",
                name="Engagement Semanal",
                description="Participa activamente durante la semana",
                type=CompetitionType.ENGAGEMENT,
                difficulty=ChallengeDifficulty.EASY,
                start_date=datetime.now(),
                end_date=datetime.now() + timedelta(days=7),
                max_participants=100,
                rewards={
                    "points": 500,
                    "badge": "weekly_warrior",
                    "feature_unlock": "priority_support"
                },
                rules=[
                    "Envía al menos 10 mensajes",
                    "Completa 3 evaluaciones",
                    "Actualiza tu perfil",
                    "Ayuda a otros usuarios"
                ]
            )
            
            # Competencia mensual de skills
            monthly_comp = Competition(
                id="skill_master_monthly",
                name="Maestro de Habilidades Mensual",
                description="Desarrolla y demuestra tus habilidades",
                type=CompetitionType.SKILL_DEVELOPMENT,
                difficulty=ChallengeDifficulty.INTERMEDIATE,
                start_date=datetime.now(),
                end_date=datetime.now() + timedelta(days=30),
                max_participants=50,
                rewards={
                    "points": 1500,
                    "badge": "skill_master",
                    "real_world": "mentorship_session"
                },
                rules=[
                    "Añade 20 nuevas habilidades",
                    "Completa 10 evaluaciones con puntuación alta",
                    "Genera 5 CVs optimizados",
                    "Participa en 3 sesiones de networking"
                ]
            )
            
            self.competitions[weekly_comp.id] = weekly_comp
            self.competitions[monthly_comp.id] = monthly_comp
            
            logger.info("Competencias inicializadas exitosamente")
            
        except Exception as e:
            logger.error(f"Error inicializando competencias: {str(e)}")
    
    async def record_activity(self, user: Person, activity_type: ActivityType, 
                            xp_amount: int = 0, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Registra actividad del usuario con sistema avanzado de recompensas
        """
        try:
            # Obtener perfil del usuario
            profile = await self._get_or_create_profile(user)
            
            # Calcular puntos base
            base_points = xp_amount or self._calculate_base_points(activity_type)
            
            # Aplicar multiplicadores
            final_points = await self._apply_point_multipliers(
                base_points, profile, activity_type, metadata
            )
            
            # Actualizar perfil
            profile.experience += final_points
            profile.total_points += final_points
            profile.last_activity = datetime.now()
            
            # Verificar logros desbloqueados
            new_achievements = await self._check_achievements(user, profile)
            
            # Verificar competencias
            competition_updates = await self._update_competitions(user, final_points, activity_type)
            
            # Generar analytics
            analytics_data = await self.analytics.record_activity(
                user, activity_type, final_points, metadata
            )
            
            # Guardar perfil
            await self._save_profile(profile)
            
            return {
                'points_earned': final_points,
                'new_level': profile.level,
                'badges_earned': new_achievements,
                'competition_updates': competition_updates,
                'analytics': analytics_data,
                'next_achievement': await self._get_next_achievement(profile)
            }
            
        except Exception as e:
            logger.error(f"Error registrando actividad: {str(e)}")
            return {'error': str(e)}
    
    async def _apply_point_multipliers(self, base_points: int, profile: UserProfile, 
                                     activity_type: ActivityType, metadata: Dict[str, Any]) -> int:
        """Aplica multiplicadores inteligentes a los puntos"""
        try:
            multiplier = 1.0
            
            # Multiplicador por racha
            if profile.current_streak > 0:
                streak_bonus = min(profile.current_streak * 0.1, 1.0)
                multiplier += streak_bonus
            
            # Multiplicador por dificultad
            if metadata and metadata.get('difficulty') == 'high':
                multiplier += 0.2
            
            # Multiplicador por tiempo (actividades rápidas)
            if metadata and metadata.get('completion_time'):
                time_bonus = min(metadata['completion_time'] * 0.05, 0.5)
                multiplier += time_bonus
            
            # Multiplicador por calidad
            if metadata and metadata.get('quality_score'):
                quality_bonus = metadata['quality_score'] * 0.3
                multiplier += quality_bonus
            
            # Multiplicador por novedad (primeras veces)
            if metadata and metadata.get('is_first_time'):
                multiplier += 0.5
            
            return int(base_points * multiplier)
            
        except Exception as e:
            logger.error(f"Error aplicando multiplicadores: {str(e)}")
            return base_points
    
    async def _check_achievements(self, user: Person, profile: UserProfile) -> List[str]:
        """Verifica logros desbloqueados con sistema inteligente"""
        try:
            new_achievements = []
            
            for achievement in self.achievements:
                if await self._check_achievement_conditions(user, profile, achievement):
                    if await self._award_achievement(user, achievement):
                        new_achievements.append(achievement.name)
            
            return new_achievements
            
        except Exception as e:
            logger.error(f"Error verificando logros: {str(e)}")
            return []
    
    async def _check_achievement_conditions(self, user: Person, profile: UserProfile, 
                                          achievement: Achievement) -> bool:
        """Verifica condiciones de logro con análisis avanzado"""
        try:
            # Verificar si ya tiene el logro
            if await self._has_achievement(user, achievement):
                return False
            
            # Verificar condiciones básicas
            for condition, value in achievement.requirements.items():
                if not await self._evaluate_condition(user, profile, condition, value):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error verificando condiciones: {str(e)}")
            return False
    
    async def _evaluate_condition(self, user: Person, profile: UserProfile, 
                                condition: str, value: Any) -> bool:
        """Evalúa condiciones de logro con lógica avanzada"""
        try:
            if condition == 'messages_sent':
                return profile.stats.get('messages_sent', 0) >= value
            
            elif condition == 'evaluations_completed':
                return profile.stats.get('evaluations_completed', 0) >= value
            
            elif condition == 'profile_completion':
                completion = await self._calculate_profile_completion(user)
                return completion >= value
            
            elif condition == 'daily_streak':
                return profile.current_streak >= value
            
            elif condition == 'skills_added':
                skills_count = await self._count_user_skills(user)
                return skills_count >= value
            
            elif condition == 'cvs_generated':
                cvs_count = await self._count_generated_cvs(user)
                return cvs_count >= value
            
            elif condition == 'perfect_personality_matches':
                perfect_matches = await self._count_perfect_matches(user)
                return perfect_matches >= value
            
            elif condition == 'optimization_score':
                best_score = await self._get_best_optimization_score(user)
                return best_score >= value
            
            return False
            
        except Exception as e:
            logger.error(f"Error evaluando condición {condition}: {str(e)}")
            return False
    
    async def _calculate_profile_completion(self, user: Person) -> float:
        """Calcula porcentaje de completitud del perfil"""
        try:
            required_fields = [
                'first_name', 'last_name', 'email', 'phone',
                'experience_years', 'education_level', 'skills'
            ]
            
            completed_fields = 0
            for field in required_fields:
                if hasattr(user, field) and getattr(user, field):
                    completed_fields += 1
            
            return (completed_fields / len(required_fields)) * 100
            
        except Exception as e:
            logger.error(f"Error calculando completitud: {str(e)}")
            return 0.0
    
    async def _count_user_skills(self, user: Person) -> int:
        """Cuenta habilidades del usuario"""
        try:
            # Implementar conteo de habilidades
            return len(getattr(user, 'skills', []) or [])
        except Exception as e:
            logger.error(f"Error contando habilidades: {str(e)}")
            return 0
    
    async def _count_generated_cvs(self, user: Person) -> int:
        """Cuenta CVs generados por el usuario"""
        try:
            # Implementar conteo de CVs generados
            return 0  # Placeholder
        except Exception as e:
            logger.error(f"Error contando CVs: {str(e)}")
            return 0
    
    async def _count_perfect_matches(self, user: Person) -> int:
        """Cuenta matches perfectos de personalidad"""
        try:
            # Implementar conteo de matches perfectos
            return 0  # Placeholder
        except Exception as e:
            logger.error(f"Error contando matches: {str(e)}")
            return 0
    
    async def _get_best_optimization_score(self, user: Person) -> float:
        """Obtiene el mejor score de optimización"""
        try:
            # Implementar obtención del mejor score
            return 0.0  # Placeholder
        except Exception as e:
            logger.error(f"Error obteniendo score: {str(e)}")
            return 0.0
    
    async def _update_competitions(self, user: Person, points: int, 
                                 activity_type: ActivityType) -> List[Dict[str, Any]]:
        """Actualiza competencias activas"""
        try:
            updates = []
            
            for competition in self.competitions.values():
                if competition.is_active():
                    # Verificar si el usuario participa
                    if await self._is_user_participating(user, competition):
                        # Actualizar progreso
                        progress = await self._update_competition_progress(
                            user, competition, points, activity_type
                        )
                        
                        if progress:
                            updates.append({
                                'competition_id': competition.id,
                                'competition_name': competition.name,
                                'progress': progress,
                                'position': await self._get_competition_position(user, competition)
                            })
            
            return updates
            
        except Exception as e:
            logger.error(f"Error actualizando competencias: {str(e)}")
            return []
    
    async def _is_user_participating(self, user: Person, competition: Competition) -> bool:
        """Verifica si el usuario participa en la competencia"""
        try:
            # Implementar verificación de participación
            return True  # Placeholder
        except Exception as e:
            logger.error(f"Error verificando participación: {str(e)}")
            return False
    
    async def _update_competition_progress(self, user: Person, competition: Competition,
                                         points: int, activity_type: ActivityType) -> Dict[str, Any]:
        """Actualiza progreso en competencia"""
        try:
            # Implementar actualización de progreso
            return {
                'points_earned': points,
                'total_progress': 0,
                'tasks_completed': 0
            }
        except Exception as e:
            logger.error(f"Error actualizando progreso: {str(e)}")
            return {}
    
    async def _get_competition_position(self, user: Person, competition: Competition) -> int:
        """Obtiene posición del usuario en la competencia"""
        try:
            # Implementar obtención de posición
            return 1  # Placeholder
        except Exception as e:
            logger.error(f"Error obteniendo posición: {str(e)}")
            return 0
    
    async def get_user_dashboard(self, user: Person) -> Dict[str, Any]:
        """Obtiene dashboard completo del usuario"""
        try:
            profile = await self._get_or_create_profile(user)
            
            # Obtener competencias activas
            active_competitions = [
                comp for comp in self.competitions.values() 
                if comp.is_active() and await self._is_user_participating(user, comp)
            ]
            
            # Obtener próximos logros
            next_achievements = await self._get_next_achievements(profile)
            
            # Obtener analytics personalizados
            user_analytics = await self.analytics.get_user_analytics(user)
            
            # Obtener recompensas disponibles
            available_rewards = await self._get_available_rewards(profile)
            
            return {
                'profile': {
                    'level': profile.level,
                    'experience': profile.experience,
                    'total_points': profile.total_points,
                    'current_streak': profile.current_streak,
                    'longest_streak': profile.longest_streak,
                    'badges_earned': len(profile.badges),
                    'achievements_earned': profile.achievements_earned
                },
                'active_competitions': [
                    {
                        'id': comp.id,
                        'name': comp.name,
                        'description': comp.description,
                        'end_date': comp.end_date.isoformat(),
                        'progress': await self._get_competition_progress(user, comp),
                        'position': await self._get_competition_position(user, comp)
                    }
                    for comp in active_competitions
                ],
                'next_achievements': next_achievements,
                'analytics': user_analytics,
                'available_rewards': available_rewards,
                'leaderboard_position': await self._get_leaderboard_position(user)
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo dashboard: {str(e)}")
            return {'error': str(e)}
    
    async def _get_next_achievements(self, profile: UserProfile) -> List[Dict[str, Any]]:
        """Obtiene próximos logros disponibles"""
        try:
            next_achievements = []
            
            for achievement in self.achievements:
                # Verificar si está cerca de desbloquear
                progress = await self._calculate_achievement_progress(profile, achievement)
                
                if 0.5 <= progress < 1.0:  # Entre 50% y 100%
                    next_achievements.append({
                        'name': achievement.name,
                        'description': achievement.description,
                        'progress': progress,
                        'points_required': achievement.points,
                        'icon': achievement.icon
                    })
            
            return sorted(next_achievements, key=lambda x: x['progress'], reverse=True)[:5]
            
        except Exception as e:
            logger.error(f"Error obteniendo próximos logros: {str(e)}")
            return []
    
    async def _calculate_achievement_progress(self, profile: UserProfile, 
                                            achievement: Achievement) -> float:
        """Calcula progreso hacia un logro específico"""
        try:
            # Implementar cálculo de progreso
            return 0.0  # Placeholder
        except Exception as e:
            logger.error(f"Error calculando progreso: {str(e)}")
            return 0.0
    
    async def _get_available_rewards(self, profile: UserProfile) -> List[Dict[str, Any]]:
        """Obtiene recompensas disponibles para el usuario"""
        try:
            available_rewards = []
            
            for reward_type, rewards in self.rewards_system.items():
                for reward_name, reward_config in rewards.items():
                    if isinstance(reward_config, dict) and 'points_required' in reward_config:
                        if profile.total_points >= reward_config['points_required']:
                            available_rewards.append({
                                'type': reward_type,
                                'name': reward_name,
                                'description': f"Desbloqueado con {reward_config['points_required']} puntos",
                                'points_required': reward_config['points_required']
                            })
            
            return available_rewards
            
        except Exception as e:
            logger.error(f"Error obteniendo recompensas: {str(e)}")
            return []
    
    async def _get_leaderboard_position(self, user: Person) -> int:
        """Obtiene posición del usuario en el leaderboard global"""
        try:
            # Implementar obtención de posición en leaderboard
            return 1  # Placeholder
        except Exception as e:
            logger.error(f"Error obteniendo posición: {str(e)}")
            return 0

# Instancia global del servicio
gamification_service = GamificationService()

@shared_task(bind=True, max_retries=3, queue='gamification')
@with_retry
async def process_gamification_event(self, user_id: str, event_type: str, data: Dict[str, Any]):
    """
    Procesa eventos de gamificación
    
    Args:
        user_id: ID del usuario
        event_type: Tipo de evento
        data: Datos del evento
    """
    try:
        service = GamificationService()
        await service.record_activity(user_id, ActivityType(event_type), data)
        logger.info(f"Evento de gamificación procesado: {event_type} para usuario {user_id}")
    except Exception as e:
        logger.error(f"Error procesando evento de gamificación: {str(e)}")
        raise self.retry(exc=e)

@shared_task(bind=True, max_retries=3, queue='gamification')
@with_retry
async def update_user_level(self, user_id: str):
    """
    Actualiza el nivel del usuario
    
    Args:
        user_id: ID del usuario
    """
    try:
        service = GamificationService()
        points = await service._get_user_points(user_id)
        new_level = await service._check_level(user_id, points)
        
        if new_level:
            await service._update_user_level(user_id, new_level)
            logger.info(f"Nivel actualizado para usuario {user_id}: {new_level.name}")
            
            # Notificar al usuario
            await send_message(
                platform='whatsapp',
                user_id=user_id,
                message=f"¡Felicidades! Has alcanzado el nivel {new_level.name}",
                business_unit=None
            )
    except Exception as e:
        logger.error(f"Error actualizando nivel de usuario: {str(e)}")
        raise self.retry(exc=e)

@shared_task(bind=True, max_retries=3, queue='gamification')
@with_retry
async def check_achievements(self, user_id: str):
    """
    Verifica logros del usuario
    
    Args:
        user_id: ID del usuario
    """
    try:
        service = GamificationService()
        stats = await service.get_user_stats(user_id)
        
        for achievement in service.achievements:
            if await service._check_achievement_requirements(user_id, achievement, stats):
                await service._unlock_achievement(user_id, achievement)
                logger.info(f"Logro desbloqueado para usuario {user_id}: {achievement.name}")
                
                # Notificar al usuario
                await send_message(
                    platform='whatsapp',
                    user_id=user_id,
                    message=f"¡Nuevo logro desbloqueado! {achievement.name}",
                    business_unit=None
                )
    except Exception as e:
        logger.error(f"Error verificando logros de usuario: {str(e)}")
        raise self.retry(exc=e)

@shared_task(bind=True, max_retries=3, queue='gamification')
@with_retry
async def process_rewards(self, user_id: str, reward_type: str, data: Dict[str, Any]):
    """
    Procesa recompensas para el usuario
    
    Args:
        user_id: ID del usuario
        reward_type: Tipo de recompensa
        data: Datos de la recompensa
    """
    try:
        service = GamificationService()
        level = await service._get_user_level(user_id)
        
        if reward_type in level.rewards:
            # Procesar recompensa
            reward = level.rewards[reward_type]
            logger.info(f"Recompensa procesada para usuario {user_id}: {reward_type}")
            
            # Notificar al usuario
            await send_message(
                platform='whatsapp',
                user_id=user_id,
                message=f"¡Has recibido una recompensa! {reward_type}",
                business_unit=None
            )
    except Exception as e:
        logger.error(f"Error procesando recompensa: {str(e)}")
        raise self.retry(exc=e)
