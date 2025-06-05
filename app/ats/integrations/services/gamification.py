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
from app.ats.chatbot.integrations.services import send_message

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

class Achievement:
    """Clase para manejar logros"""
    
    def __init__(self, 
                 achievement_type: AchievementType,
                 name: str,
                 description: str,
                 points: int,
                 requirements: Dict[str, Any],
                 icon: str = None):
        """
        Inicializa un logro
        
        Args:
            achievement_type: Tipo de logro
            name: Nombre del logro
            description: Descripción del logro
            points: Puntos otorgados
            requirements: Requisitos para desbloquear
            icon: Icono del logro
        """
        self.achievement_type = achievement_type
        self.name = name
        self.description = description
        self.points = points
        self.requirements = requirements
        self.icon = icon

class GamificationService:
    """Servicio de gamificación"""
    
    def __init__(self):
        """Inicializa el servicio de gamificación"""
        self.levels = self._initialize_levels()
        self.achievements = self._initialize_achievements()
        self.points_config = self._get_points_config()
    
    def _initialize_levels(self) -> List[Level]:
        """
        Inicializa los niveles disponibles
        
        Returns:
            List[Level]: Lista de niveles
        """
        return [
            Level(1, "Novato", 0, {"features": ["basic_menu"]}),
            Level(2, "Aprendiz", 100, {"features": ["quick_replies"]}),
            Level(3, "Intermedio", 500, {"features": ["evaluations"]}),
            Level(4, "Avanzado", 1000, {"features": ["references"]}),
            Level(5, "Experto", 2000, {"features": ["all_features"]})
        ]
        
    def _initialize_achievements(self) -> List[Achievement]:
        """
        Inicializa los logros disponibles
        
        Returns:
            List[Achievement]: Lista de logros
        """
        return [
            # Logros de mensajería
            Achievement(
                AchievementType.MESSAGE_MILESTONE,
                "Comunicador",
                "Envía 100 mensajes",
                50,
                {"messages_sent": 100},
                "message_icon"
            ),
            Achievement(
                AchievementType.QUICK_REPLY_MASTER,
                "Maestro de Respuestas Rápidas",
                "Usa 50 respuestas rápidas",
                75,
                {"quick_replies_used": 50},
                "quick_reply_icon"
            ),
            
            # Logros de evaluación
            Achievement(
                AchievementType.EVALUATION_NOVICE,
                "Evaluador Novato",
                "Completa 5 evaluaciones",
                100,
                {"evaluations_completed": 5},
                "evaluation_icon"
            ),
            Achievement(
                AchievementType.EVALUATION_EXPERT,
                "Evaluador Experto",
                "Completa 20 evaluaciones con puntuación alta",
                200,
                {"evaluations_completed": 20, "min_score": 8},
                "expert_icon"
            ),
            
            # Logros de referencia
            Achievement(
                AchievementType.REFERENCE_COLLECTOR,
                "Coleccionista de Referencias",
                "Obtén 10 referencias completadas",
                150,
                {"references_completed": 10},
                "reference_icon"
            ),
            Achievement(
                AchievementType.REFERENCE_QUALITY,
                "Referencias de Calidad",
                "Obtén 5 referencias con puntuación alta",
                200,
                {"high_quality_references": 5},
                "quality_icon"
            ),
            
            # Logros de perfil
            Achievement(
                AchievementType.PROFILE_COMPLETE,
                "Perfil Completo",
                "Completa todos los campos de tu perfil",
                100,
                {"profile_completion": 100},
                "profile_icon"
            ),
            Achievement(
                AchievementType.SKILL_MASTER,
                "Maestro de Habilidades",
                "Añade 10 habilidades a tu perfil",
                150,
                {"skills_added": 10},
                "skills_icon"
            ),
            
            # Logros de interacción
            Achievement(
                AchievementType.MENU_NAVIGATOR,
                "Navegador del Menú",
                "Accede a todas las secciones del menú",
                75,
                {"menu_sections_accessed": "all"},
                "menu_icon"
            ),
            Achievement(
                AchievementType.FEATURE_EXPLORER,
                "Explorador de Características",
                "Usa todas las características disponibles",
                100,
                {"features_used": "all"},
                "explorer_icon"
            ),
            
            # Logros de comunidad
            Achievement(
                AchievementType.RECOMMENDATION_GIVER,
                "Recomendador",
                "Da 5 recomendaciones",
                150,
                {"recommendations_given": 5},
                "recommendation_icon"
            ),
            Achievement(
                AchievementType.FEEDBACK_PROVIDER,
                "Proveedor de Feedback",
                "Proporciona feedback en 10 ocasiones",
                100,
                {"feedback_provided": 10},
                "feedback_icon"
            ),
            
            # Logros especiales
            Achievement(
                AchievementType.DAILY_STREAK,
                "Racha Diaria",
                "Usa el chatbot 7 días seguidos",
                200,
                {"daily_streak": 7},
                "streak_icon"
            ),
            Achievement(
                AchievementType.WEEKLY_CHALLENGE,
                "Desafío Semanal",
                "Completa todos los desafíos semanales",
                300,
                {"weekly_challenges_completed": "all"},
                "challenge_icon"
            )
        ]
        
    def _get_points_config(self) -> Dict[str, int]:
        """
        Obtiene la configuración de puntos por actividad
        
        Returns:
            Dict[str, int]: Configuración de puntos
        """
        return {
            ActivityType.MESSAGE_SENT.value: 1,
            ActivityType.MESSAGE_RECEIVED.value: 1,
            ActivityType.QUICK_REPLY.value: 2,
            ActivityType.BUTTON_CLICK.value: 1,
            ActivityType.EVALUATION_STARTED.value: 5,
            ActivityType.EVALUATION_COMPLETED.value: 10,
            ActivityType.EVALUATION_SCORE.value: 5,
            ActivityType.REFERENCE_REQUESTED.value: 5,
            ActivityType.REFERENCE_COMPLETED.value: 20,
            ActivityType.REFERENCE_QUALITY.value: 10,
            ActivityType.PROFILE_UPDATED.value: 5,
            ActivityType.SKILL_ADDED.value: 10,
            ActivityType.EXPERIENCE_ADDED.value: 15,
            ActivityType.MENU_ACCESS.value: 1,
            ActivityType.FEATURE_USED.value: 5,
            ActivityType.HELP_REQUESTED.value: 2,
            ActivityType.RECOMMENDATION_GIVEN.value: 15,
            ActivityType.RECOMMENDATION_RECEIVED.value: 10,
            ActivityType.FEEDBACK_PROVIDED.value: 5
        }
        
    async def record_activity(self, 
                            user_id: str,
                            activity_type: ActivityType,
                            data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Registra una actividad y actualiza puntos/logros
        
        Args:
            user_id: ID del usuario
            activity_type: Tipo de actividad
            data: Datos adicionales de la actividad
            
        Returns:
            Dict con el resultado de la actividad
        """
        try:
            # Obtener puntos por la actividad
            points = self.points_config.get(activity_type.value, 0)
            
            # Actualizar puntos del usuario
            user_points = await self._update_user_points(user_id, points)
            
            # Verificar logros
            new_achievements = await self._check_achievements(user_id, activity_type, data)
            
            # Verificar nivel
            new_level = await self._check_level(user_id, user_points)
            
            return {
                'points_earned': points,
                'total_points': user_points,
                'new_achievements': new_achievements,
                'new_level': new_level
            }
            
        except Exception as e:
            logger.error(f"Error recording activity: {str(e)}")
            raise
            
    async def _update_user_points(self, user_id: str, points: int) -> int:
        """
        Actualiza los puntos del usuario
        
        Args:
            user_id: ID del usuario
            points: Puntos a añadir
            
        Returns:
            int: Total de puntos actualizado
        """
        cache_key = f"user_points_{user_id}"
        current_points = cache.get(cache_key, 0)
        new_points = current_points + points
        cache.set(cache_key, new_points)
        return new_points
        
    async def _check_achievements(self,
                                user_id: str,
                                activity_type: ActivityType,
                                data: Dict[str, Any] = None) -> List[Achievement]:
        """
        Verifica si se han desbloqueado nuevos logros
        
        Args:
            user_id: ID del usuario
            activity_type: Tipo de actividad
            data: Datos adicionales de la actividad
            
        Returns:
            List[Achievement]: Lista de logros desbloqueados
        """
        new_achievements = []
        user_achievements = await self._get_user_achievements(user_id)
        
        for achievement in self.achievements:
            if achievement.achievement_type.value == activity_type.value:
                if await self._check_achievement_requirements(user_id, achievement, data):
                    if achievement not in user_achievements:
                        new_achievements.append(achievement)
                        await self._unlock_achievement(user_id, achievement)
                        
        return new_achievements
        
    async def _check_level(self, user_id: str, points: int) -> Optional[Level]:
        """
        Verifica si el usuario ha subido de nivel
        
        Args:
            user_id: ID del usuario
            points: Puntos totales del usuario
            
        Returns:
            Optional[Level]: Nuevo nivel o None
        """
        current_level = await self._get_user_level(user_id)
        
        for level in self.levels:
            if points >= level.points_required and level.level > current_level.level:
                await self._update_user_level(user_id, level)
                return level
                
        return None
        
    async def _get_user_achievements(self, user_id: str) -> List[Achievement]:
        """
        Obtiene los logros del usuario
        
        Args:
            user_id: ID del usuario
            
        Returns:
            List[Achievement]: Lista de logros
        """
        cache_key = f"user_achievements_{user_id}"
        return cache.get(cache_key, [])
        
    async def _unlock_achievement(self, user_id: str, achievement: Achievement):
        """
        Desbloquea un logro para el usuario
        
        Args:
            user_id: ID del usuario
            achievement: Logro a desbloquear
        """
        user_achievements = await self._get_user_achievements(user_id)
        user_achievements.append(achievement)
        
        cache_key = f"user_achievements_{user_id}"
        cache.set(cache_key, user_achievements)
        
    async def _get_user_level(self, user_id: str) -> Level:
        """
        Obtiene el nivel actual del usuario
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Level: Nivel actual
        """
        cache_key = f"user_level_{user_id}"
        level_number = cache.get(cache_key, 1)
        
        for level in self.levels:
            if level.level == level_number:
                return level
                
        return self.levels[0]
        
    async def _update_user_level(self, user_id: str, level: Level):
        """
        Actualiza el nivel del usuario
        
        Args:
            user_id: ID del usuario
            level: Nuevo nivel
        """
        cache_key = f"user_level_{user_id}"
        cache.set(cache_key, level.level)
        
    async def _check_achievement_requirements(self,
                                           user_id: str,
                                           achievement: Achievement,
                                           data: Dict[str, Any] = None) -> bool:
        """
        Verifica si se cumplen los requisitos de un logro
        
        Args:
            user_id: ID del usuario
            achievement: Logro a verificar
            data: Datos adicionales
            
        Returns:
            bool: True si se cumplen los requisitos
        """
        # Implementación específica para cada tipo de logro
        return False
        
    async def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Obtiene las estadísticas del usuario
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Dict con las estadísticas
        """
        return {
            'points': await self._get_user_points(user_id),
            'level': await self._get_user_level(user_id),
            'achievements': await self._get_user_achievements(user_id)
        }
        
    async def _get_user_points(self, user_id: str) -> int:
        """
        Obtiene los puntos del usuario
        
        Args:
            user_id: ID del usuario
            
        Returns:
            int: Puntos totales
        """
        cache_key = f"user_points_{user_id}"
        return cache.get(cache_key, 0)

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
