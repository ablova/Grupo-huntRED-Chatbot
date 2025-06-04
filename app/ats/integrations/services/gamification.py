# /home/pablo/app/ats/integrations/services/gamification.py
"""
Enhanced Network Gamification Service

Sistema avanzado de gamificación para el seguimiento y recompensa de actividades
y logros de los usuarios en la plataforma.
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

logger = logging.getLogger("gamification")

class ActivityType(Enum):
    """Tipos de actividades rastreables en el sistema de gamificación."""
    # Actividades básicas
    PROFILE_UPDATE = "profile_update"
    SKILL_ENDORSEMENT = "skill_endorsement"
    REFERRAL = "successful_referral"
    CHALLENGE_COMPLETE = "completed_challenge"
    CONNECTION_MADE = "connection_made"
    
    # Actividades de contenido
    CONTENT_SHARED = "content_shared"
    FEEDBACK_PROVIDED = "feedback_provided"
    
    # Actividades de comunidad
    COMMUNITY_CONTRIBUTION = "community_contribution"
    MENTORSHIP = "mentorship"
    
    # Actividades de progreso
    DAILY_LOGIN = "daily_login"
    MILESTONE_REACHED = "milestone_reached"
    
    # Actividades profesionales
    JOB_APPLICATION = "job_application"
    INTERVIEW_COMPLETED = "interview_completed"
    CERTIFICATION_EARNED = "certification_earned"
    PROJECT_COMPLETION = "project_completion"

class ChallengeCategory(Enum):
    """Categorías de desafíos."""
    SKILLS = "Habilidades"
    NETWORK = "Red"
    COMMUNITY = "Comunidad"
    ACHIEVEMENT = "Logros"
    DAILY = "Diarios"
    WEEKLY = "Semanales"
    SEASONAL = "De temporada"

class GamificationService:
    """
    Servicio avanzado de gamificación que maneja puntos, logros y desafíos.
    """
    
    # Sistema de puntos base por tipo de actividad
    BASE_XP = {
        # Actividades básicas
        ActivityType.PROFILE_UPDATE: 10,
        ActivityType.SKILL_ENDORSEMENT: 15,
        ActivityType.REFERRAL: 50,
        ActivityType.CHALLENGE_COMPLETE: 25,
        ActivityType.CONNECTION_MADE: 5,
        
        # Actividades de contenido
        ActivityType.CONTENT_SHARED: 10,
        ActivityType.FEEDBACK_PROVIDED: 15,
        
        # Actividades de comunidad
        ActivityType.COMMUNITY_CONTRIBUTION: 20,
        ActivityType.MENTORSHIP: 40,
        
        # Actividades de progreso
        ActivityType.DAILY_LOGIN: 5,
        ActivityType.MILESTONE_REACHED: 100,
        
        # Actividades profesionales
        ActivityType.JOB_APPLICATION: 30,
        ActivityType.INTERVIEW_COMPLETED: 50,
        ActivityType.CERTIFICATION_EARNED: 75,
        ActivityType.PROJECT_COMPLETION: 60
    }
    
    # Categorías de XP para cada actividad
    XP_CATEGORIES = {
        ActivityType.PROFILE_UPDATE: 'skills',
        ActivityType.SKILL_ENDORSEMENT: 'skills',
        ActivityType.REFERRAL: 'network',
        ActivityType.CONNECTION_MADE: 'network',
        ActivityType.CONTENT_SHARED: 'community',
        ActivityType.FEEDBACK_PROVIDED: 'community',
        ActivityType.COMMUNITY_CONTRIBUTION: 'community',
        ActivityType.MENTORSHIP: 'community',
        ActivityType.DAILY_LOGIN: 'general',
        ActivityType.MILESTONE_REACHED: 'achievements',
        ActivityType.JOB_APPLICATION: 'skills',
        ActivityType.INTERVIEW_COMPLETED: 'skills',
        ActivityType.CERTIFICATION_EARNED: 'skills',
        ActivityType.PROJECT_COMPLETION: 'skills',
        ActivityType.CHALLENGE_COMPLETE: 'achievements'
    }
    
    def __init__(self, business_unit: Optional[BusinessUnit] = None):
        self.business_unit = business_unit
        self.cache_prefix = f"gamification_{business_unit.slug}_" if business_unit else "gamification_"
    
    async def _get_or_create_profile(self, user: Person) -> EnhancedNetworkGamificationProfile:
        """Obtiene o crea un perfil de gamificación."""
        return await sync_to_async(EnhancedNetworkGamificationProfile.objects.get_or_create)(
            user=user,
            defaults={
                'xp_total': 0,
                'current_level': 1,
                'xp_to_next_level': 100,
                'streak_days': 0,
                'last_activity_date': timezone.now().date(),
                'highest_streak': 0,
                'xp_skills': 0,
                'xp_network': 0,
                'xp_community': 0,
                'xp_achievements': 0,
                'total_challenges': 0,
                'total_badges': 0
            }
        )[0]
    
    async def record_activity(self, user: Person, activity_type: ActivityType, 
                            xp_amount: int = None, metadata: dict = None) -> Dict[str, Any]:
        """
        Registra una actividad del usuario y otorga XP correspondiente.
        
        Args:
            user: Usuario que realiza la actividad
            activity_type: Tipo de actividad (de ActivityType)
            xp_amount: Cantidad de XP a otorgar (opcional, usa el valor por defecto si no se especifica)
            metadata: Metadatos adicionales para el evento
            
        Returns:
            Dict con información sobre la operación
        """
        result = {"success": False, "xp_earned": 0, "level_up": False, "badges_earned": []}
        
        try:
            if not isinstance(activity_type, ActivityType):
                raise ValueError("Tipo de actividad no válido")
                
            xp_amount = xp_amount or self.BASE_XP.get(activity_type, 0)
            if xp_amount <= 0:
                return result
                
            async with transaction.atomic():
                # Obtener o crear perfil
                profile = await self._get_or_create_profile(user)
                
                # Obtener nivel actual antes de la actualización
                old_level = profile.current_level
                
                # Actualizar racha
                await sync_to_async(profile.update_streak)()
                
                # Añadir XP
                category = self.XP_CATEGORIES.get(activity_type, 'general')
                await sync_to_async(profile.add_xp)(xp_amount, category)
                
                # Registrar evento
                await sync_to_async(GamificationEvent.objects.create)(
                    user=user,
                    event_type=activity_type.value,
                    xp_earned=xp_amount,
                    metadata=metadata or {}
                )
                
                # Verificar logros
                badges = await self._check_achievements(user, activity_type, profile)
                
                # Actualizar resultado
                result.update({
                    "success": True,
                    "xp_earned": xp_amount,
                    "level_up": profile.current_level > old_level,
                    "badges_earned": badges,
                    "current_level": profile.current_level,
                    "xp_total": profile.xp_total,
                    "xp_to_next_level": profile.xp_to_next_level
                })
                
                # Notificar al usuario
                await self._notify_user_update(user, activity_type, result)
                
                return result
                
        except Exception as e:
            logger.error(f"[Gamification] Error registrando actividad: {str(e)}", exc_info=True)
            return result
    
    async def _check_achievements(self, user: Person, activity_type: ActivityType, 
                                profile: EnhancedNetworkGamificationProfile) -> List[Dict]:
        """Verifica si el usuario ha desbloqueado logros."""
        badges_earned = []
        
        # Verificar logros basados en actividad
        achievement_triggers = {
            ActivityType.PROFILE_UPDATE: "complete_profile",
            ActivityType.SKILL_ENDORSEMENT: "skill_expert",
            ActivityType.REFERRAL: "referral_master",
            ActivityType.DAILY_LOGIN: "daily_streak"
        }
        
        badge_name = achievement_triggers.get(activity_type)
        if badge_name:
            earned = await sync_to_async(profile.award_badge)(badge_name)
            if earned:
                badges_earned.append({"name": badge_name, "xp": 0})
        
        # Verificar logros por nivel
        level_badges = {
            5: "rising_star",
            10: "experienced",
            25: "veteran",
            50: "legendary"
        }
        
        badge_name = level_badges.get(profile.current_level)
        if badge_name:
            earned = await sync_to_async(profile.award_badge)(badge_name)
            if earned:
                badges_earned.append({"name": badge_name, "xp": 0})
        
        return badges_earned
    
    async def _notify_user_update(self, user: Person, activity_type: ActivityType, 
                                result: Dict[str, Any]) -> None:
        """Notifica al usuario sobre la actualización de su progreso."""
        try:
            messages = []
            
            # Mensaje de actividad
            activity_message = f"¡Actividad registrada! +{result['xp_earned']} XP por {activity_type.value.replace('_', ' ')}"
            messages.append(activity_message)
            
            # Mensaje de subida de nivel
            if result['level_up']:
                level_message = f"¡Nuevo nivel {result['current_level']} alcanzado!"
                messages.append(level_message)
            
            # Mensaje de logros
            for badge in result['badges_earned']:
                badge_message = f"¡Logro desbloqueado: {badge['name']}!"
                messages.append(badge_message)
            
            # Enviar mensaje consolidado
            if messages:
                platform = getattr(user, 'chat_state', {}).get('platform', 'whatsapp')
                business_unit = getattr(user, 'business_unit', self.business_unit)
                
                if platform and business_unit:
                    full_message = "\n".join(messages)
                    await send_message(
                        platform=platform,
                        user_id=user.phone,
                        message=full_message,
                        business_unit=business_unit.name if hasattr(business_unit, 'name') else str(business_unit)
                    )
                    
        except Exception as e:
            logger.error(f"[Gamification] Error notificando actualización: {str(e)}")
    
    async def get_user_progress(self, user: Person) -> Dict[str, Any]:
        """Obtiene el progreso actual del usuario."""
        try:
            profile = await self._get_or_create_profile(user)
            return await sync_to_async(profile.get_progress)()
        except Exception as e:
            logger.error(f"[Gamification] Error obteniendo progreso: {str(e)}")
            return {}
    
    async def get_leaderboard(self, category: str = None, limit: int = 10) -> List[Dict]:
        """Obtiene la tabla de clasificación."""
        try:
            # Implementar lógica de clasificación
            pass
        except Exception as e:
            logger.error(f"[Gamification] Error obteniendo clasificación: {str(e)}")
            return []
    
    async def generate_challenges(self, user: Person, category: str = None, 
                               limit: int = 3) -> List[Dict]:
        """Genera desafíos personalizados para el usuario."""
        try:
            # Implementar generación de desafíos
            pass
        except Exception as e:
            logger.error(f"[Gamification] Error generando desafíos: {str(e)}")
            return []

# Instancia global del servicio
gamification_service = GamificationService()
