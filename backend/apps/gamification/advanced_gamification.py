"""
Sistema Avanzado de Gamificación huntRED® v2
===========================================

Funcionalidades:
- Sistema completo de puntos, badges y niveles
- Leaderboards dinámicos por período y categoría
- Challenges y achievements personalizables
- Sistema de rewards con valor real
- Análisis de engagement y motivación
- Mecánicas de juego avanzadas
- Integración con todos los módulos del sistema
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import json
import logging
import math
from collections import defaultdict

logger = logging.getLogger(__name__)

class ActionType(Enum):
    """Tipos de acciones que generan puntos."""
    # Perfil y aplicación
    PROFILE_COMPLETE = "profile_complete"
    CV_UPLOAD = "cv_upload"
    APPLICATION_SUBMIT = "application_submit"
    
    # Entrevistas
    INTERVIEW_ATTEND = "interview_attend"
    INTERVIEW_FEEDBACK = "interview_feedback"
    INTERVIEW_RESCHEDULE = "interview_reschedule"
    
    # Referencias y verificaciones
    REFERENCE_PROVIDE = "reference_provide"
    REFERENCE_RESPOND = "reference_respond"
    BACKGROUND_CHECK_COMPLETE = "background_check_complete"
    
    # Assessments
    ASSESSMENT_COMPLETE = "assessment_complete"
    ASSESSMENT_PERFECT_SCORE = "assessment_perfect_score"
    
    # Actividad social
    SOCIAL_SHARE = "social_share"
    REFERRAL_MADE = "referral_made"
    REFERRAL_HIRED = "referral_hired"
    
    # Logros especiales
    JOB_OFFER_RECEIVED = "job_offer_received"
    JOB_OFFER_ACCEPTED = "job_offer_accepted"
    LONG_TERM_ENGAGEMENT = "long_term_engagement"
    
    # Acciones de reclutadores
    CANDIDATE_SOURCED = "candidate_sourced"
    SUCCESSFUL_PLACEMENT = "successful_placement"
    CLIENT_SATISFACTION = "client_satisfaction"

class BadgeType(Enum):
    """Tipos de badges disponibles."""
    # Badges de progreso
    NEWCOMER = "newcomer"
    EXPLORER = "explorer"
    VETERAN = "veteran"
    MASTER = "master"
    
    # Badges de habilidades
    TECH_WIZARD = "tech_wizard"
    COMMUNICATION_PRO = "communication_pro"
    LEADER = "leader"
    TEAM_PLAYER = "team_player"
    
    # Badges de logros
    PERFECT_SCORER = "perfect_scorer"
    SPEED_DEMON = "speed_demon"
    CONSISTENT = "consistent"
    OVERACHIEVER = "overachiever"
    
    # Badges especiales
    EARLY_ADOPTER = "early_adopter"
    COMMUNITY_BUILDER = "community_builder"
    MENTOR = "mentor"
    AMBASSADOR = "ambassador"

class ChallengeType(Enum):
    """Tipos de challenges disponibles."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    SEASONAL = "seasonal"
    SPECIAL_EVENT = "special_event"
    ACHIEVEMENT = "achievement"

class RewardType(Enum):
    """Tipos de rewards disponibles."""
    # Rewards virtuales
    POINTS = "points"
    BADGE = "badge"
    TITLE = "title"
    AVATAR = "avatar"
    
    # Rewards con valor real
    GIFT_CARD = "gift_card"
    COURSE_ACCESS = "course_access"
    MENTORING_SESSION = "mentoring_session"
    PRIORITY_SUPPORT = "priority_support"
    
    # Rewards premium
    INTERVIEW_COACHING = "interview_coaching"
    RESUME_REVIEW = "resume_review"
    CAREER_CONSULTATION = "career_consultation"
    NETWORKING_EVENT = "networking_event"

@dataclass
class GamificationAction:
    """Acción que genera puntos en el sistema."""
    id: str
    user_id: str
    action_type: ActionType
    points_earned: int
    multiplier: float = 1.0
    bonus_points: int = 0
    
    # Contexto
    entity_id: Optional[str] = None  # ID del job, assessment, etc.
    entity_type: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Tracking
    timestamp: datetime = field(default_factory=datetime.now)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    @property
    def total_points(self) -> int:
        return int((self.points_earned * self.multiplier) + self.bonus_points)

@dataclass
class Badge:
    """Badge que puede ganar un usuario."""
    id: str
    badge_type: BadgeType
    name: str
    description: str
    icon_url: str
    
    # Criterios para obtener el badge
    requirements: Dict[str, Any] = field(default_factory=dict)
    points_required: int = 0
    actions_required: List[ActionType] = field(default_factory=list)
    
    # Rareza y valor
    rarity: str = "common"  # common, uncommon, rare, epic, legendary
    points_value: int = 0
    
    # Metadatos
    category: str = "general"
    is_hidden: bool = False  # Badge secreto
    expiry_date: Optional[datetime] = None
    
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class Challenge:
    """Challenge o reto que pueden completar los usuarios."""
    id: str
    challenge_type: ChallengeType
    name: str
    description: str
    
    # Objetivos
    target_value: int
    target_actions: List[ActionType] = field(default_factory=list)
    target_timeframe: timedelta = field(default_factory=lambda: timedelta(days=7))
    
    # Rewards
    completion_points: int = 0
    completion_badges: List[str] = field(default_factory=list)
    completion_rewards: List[Dict[str, Any]] = field(default_factory=list)
    
    # Estado
    is_active: bool = True
    start_date: datetime = field(default_factory=datetime.now)
    end_date: Optional[datetime] = None
    
    # Restricciones
    max_participants: Optional[int] = None
    required_level: int = 1
    required_badges: List[str] = field(default_factory=list)

@dataclass
class UserGamificationProfile:
    """Perfil de gamificación de un usuario."""
    user_id: str
    
    # Puntos y nivel
    total_points: int = 0
    level: int = 1
    current_level_points: int = 0
    points_to_next_level: int = 100
    
    # Estadísticas
    badges_earned: List[str] = field(default_factory=list)
    challenges_completed: List[str] = field(default_factory=list)
    achievements_unlocked: List[str] = field(default_factory=list)
    
    # Streaks y actividad
    current_streak: int = 0
    longest_streak: int = 0
    last_activity: Optional[datetime] = None
    
    # Ranking
    global_rank: int = 0
    category_ranks: Dict[str, int] = field(default_factory=dict)
    
    # Multiplicadores activos
    active_multipliers: Dict[str, float] = field(default_factory=dict)
    
    # Metadatos
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

class GamificationEngine:
    """Motor principal del sistema de gamificación."""
    
    def __init__(self):
        self.user_profiles: Dict[str, UserGamificationProfile] = {}
        self.badges: Dict[str, Badge] = {}
        self.challenges: Dict[str, Challenge] = {}
        self.actions_log: List[GamificationAction] = []
        
        # Configuración de puntos por acción
        self.points_config = {
            ActionType.PROFILE_COMPLETE: 100,
            ActionType.CV_UPLOAD: 50,
            ActionType.APPLICATION_SUBMIT: 25,
            ActionType.INTERVIEW_ATTEND: 75,
            ActionType.INTERVIEW_FEEDBACK: 30,
            ActionType.REFERENCE_PROVIDE: 40,
            ActionType.REFERENCE_RESPOND: 60,
            ActionType.BACKGROUND_CHECK_COMPLETE: 20,
            ActionType.ASSESSMENT_COMPLETE: 50,
            ActionType.ASSESSMENT_PERFECT_SCORE: 150,
            ActionType.SOCIAL_SHARE: 10,
            ActionType.REFERRAL_MADE: 100,
            ActionType.REFERRAL_HIRED: 500,
            ActionType.JOB_OFFER_RECEIVED: 200,
            ActionType.JOB_OFFER_ACCEPTED: 1000,
            ActionType.CANDIDATE_SOURCED: 30,
            ActionType.SUCCESSFUL_PLACEMENT: 300,
            ActionType.CLIENT_SATISFACTION: 150
        }
        
        # Configuración de niveles
        self.level_config = {
            "base_points": 100,
            "multiplier": 1.5,
            "max_level": 100
        }
        
        # Setup inicial
        self._setup_default_badges()
        self._setup_default_challenges()
    
    def _setup_default_badges(self):
        """Configura badges por defecto del sistema."""
        
        badges = [
            # Badges de progreso
            Badge(
                id="newcomer_001",
                badge_type=BadgeType.NEWCOMER,
                name="Bienvenido",
                description="Completa tu perfil por primera vez",
                icon_url="/badges/newcomer.png",
                requirements={"actions": [ActionType.PROFILE_COMPLETE]},
                points_value=25,
                rarity="common"
            ),
            Badge(
                id="explorer_001",
                badge_type=BadgeType.EXPLORER,
                name="Explorador",
                description="Aplica a tu primer trabajo",
                icon_url="/badges/explorer.png",
                requirements={"actions": [ActionType.APPLICATION_SUBMIT]},
                points_value=50,
                rarity="common"
            ),
            Badge(
                id="veteran_001",
                badge_type=BadgeType.VETERAN,
                name="Veterano",
                description="Alcanza nivel 10",
                icon_url="/badges/veteran.png",
                requirements={"level": 10},
                points_value=200,
                rarity="uncommon"
            ),
            
            # Badges de habilidades
            Badge(
                id="tech_wizard_001",
                badge_type=BadgeType.TECH_WIZARD,
                name="Mago Técnico",
                description="Obtén puntuación perfecta en 3 assessments técnicos",
                icon_url="/badges/tech_wizard.png",
                requirements={"perfect_assessments": 3, "category": "technical"},
                points_value=300,
                rarity="rare"
            ),
            Badge(
                id="communication_pro_001",
                badge_type=BadgeType.COMMUNICATION_PRO,
                name="Pro de Comunicación",
                description="Recibe calificación excelente en 5 entrevistas",
                icon_url="/badges/communication_pro.png",
                requirements={"excellent_interviews": 5},
                points_value=250,
                rarity="rare"
            ),
            
            # Badges de logros
            Badge(
                id="perfect_scorer_001",
                badge_type=BadgeType.PERFECT_SCORER,
                name="Puntuación Perfecta",
                description="Obtén 100% en cualquier assessment",
                icon_url="/badges/perfect_scorer.png",
                requirements={"actions": [ActionType.ASSESSMENT_PERFECT_SCORE]},
                points_value=150,
                rarity="uncommon"
            ),
            Badge(
                id="speed_demon_001",
                badge_type=BadgeType.SPEED_DEMON,
                name="Demonio de Velocidad",
                description="Completa un assessment en tiempo récord",
                icon_url="/badges/speed_demon.png",
                requirements={"fast_completion": True},
                points_value=100,
                rarity="uncommon"
            ),
            
            # Badges especiales
            Badge(
                id="ambassador_001",
                badge_type=BadgeType.AMBASSADOR,
                name="Embajador huntRED®",
                description="Refiere 10 candidatos exitosos",
                icon_url="/badges/ambassador.png",
                requirements={"successful_referrals": 10},
                points_value=1000,
                rarity="legendary"
            )
        ]
        
        for badge in badges:
            self.badges[badge.id] = badge
    
    def _setup_default_challenges(self):
        """Configura challenges por defecto del sistema."""
        
        challenges = [
            # Challenge diario
            Challenge(
                id="daily_activity",
                challenge_type=ChallengeType.DAILY,
                name="Actividad Diaria",
                description="Realiza al menos 3 acciones hoy",
                target_value=3,
                target_actions=[],  # Cualquier acción cuenta
                target_timeframe=timedelta(days=1),
                completion_points=50
            ),
            
            # Challenge semanal
            Challenge(
                id="weekly_applications",
                challenge_type=ChallengeType.WEEKLY,
                name="Aplicador Semanal",
                description="Aplica a 5 trabajos esta semana",
                target_value=5,
                target_actions=[ActionType.APPLICATION_SUBMIT],
                target_timeframe=timedelta(days=7),
                completion_points=200,
                completion_badges=["explorer_002"]
            ),
            
            # Challenge mensual
            Challenge(
                id="monthly_interviews",
                challenge_type=ChallengeType.MONTHLY,
                name="Entrevistado del Mes",
                description="Asiste a 8 entrevistas este mes",
                target_value=8,
                target_actions=[ActionType.INTERVIEW_ATTEND],
                target_timeframe=timedelta(days=30),
                completion_points=500,
                completion_rewards=[
                    {"type": RewardType.COURSE_ACCESS.value, "value": "interview_mastery"}
                ]
            ),
            
            # Challenge especial
            Challenge(
                id="perfect_month",
                challenge_type=ChallengeType.SPECIAL_EVENT,
                name="Mes Perfecto",
                description="Obtén puntuación perfecta en todos los assessments de este mes",
                target_value=100,  # 100% de assessments perfectos
                target_actions=[ActionType.ASSESSMENT_PERFECT_SCORE],
                target_timeframe=timedelta(days=30),
                completion_points=1000,
                completion_badges=["perfect_scorer_002"],
                completion_rewards=[
                    {"type": RewardType.CAREER_CONSULTATION.value, "value": "1_hour_session"}
                ]
            )
        ]
        
        for challenge in challenges:
            self.challenges[challenge.id] = challenge
    
    async def track_action(self, user_id: str, action_type: ActionType,
                         entity_id: Optional[str] = None,
                         entity_type: Optional[str] = None,
                         metadata: Optional[Dict[str, Any]] = None,
                         custom_points: Optional[int] = None) -> GamificationAction:
        """Registra una acción del usuario y otorga puntos."""
        
        # Obtener o crear perfil
        profile = await self._get_or_create_profile(user_id)
        
        # Calcular puntos
        base_points = custom_points or self.points_config.get(action_type, 10)
        multiplier = await self._calculate_multiplier(user_id, action_type)
        bonus_points = await self._calculate_bonus_points(user_id, action_type, metadata or {})
        
        # Crear acción
        action = GamificationAction(
            id=str(uuid.uuid4()),
            user_id=user_id,
            action_type=action_type,
            points_earned=base_points,
            multiplier=multiplier,
            bonus_points=bonus_points,
            entity_id=entity_id,
            entity_type=entity_type,
            metadata=metadata or {}
        )
        
        # Registrar acción
        self.actions_log.append(action)
        
        # Actualizar perfil
        await self._update_profile_points(profile, action.total_points)
        await self._update_activity_streak(profile)
        await self._check_level_up(profile)
        await self._check_badge_awards(profile, action)
        await self._check_challenge_progress(profile, action)
        
        logger.info(f"Action tracked: {user_id} - {action_type.value} - {action.total_points} points")
        return action
    
    async def _get_or_create_profile(self, user_id: str) -> UserGamificationProfile:
        """Obtiene o crea el perfil de gamificación de un usuario."""
        
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = UserGamificationProfile(user_id=user_id)
        
        return self.user_profiles[user_id]
    
    async def _calculate_multiplier(self, user_id: str, action_type: ActionType) -> float:
        """Calcula el multiplicador de puntos para una acción."""
        
        profile = self.user_profiles.get(user_id)
        if not profile:
            return 1.0
        
        multiplier = 1.0
        
        # Multiplicador por nivel (más alto = más puntos)
        level_multiplier = 1.0 + (profile.level * 0.01)  # 1% por nivel
        multiplier *= level_multiplier
        
        # Multiplicador por streak
        if profile.current_streak >= 7:
            multiplier *= 1.2  # 20% bonus por streak de 7 días
        elif profile.current_streak >= 3:
            multiplier *= 1.1  # 10% bonus por streak de 3 días
        
        # Multiplicadores especiales activos
        for multiplier_type, value in profile.active_multipliers.items():
            multiplier *= value
        
        return round(multiplier, 2)
    
    async def _calculate_bonus_points(self, user_id: str, action_type: ActionType,
                                    metadata: Dict[str, Any]) -> int:
        """Calcula puntos bonus para una acción."""
        
        bonus = 0
        
        # Bonus por primera vez
        user_actions = [a for a in self.actions_log if a.user_id == user_id]
        if not any(a.action_type == action_type for a in user_actions):
            bonus += 25  # Bonus primera vez
        
        # Bonus por calidad (ej: puntuación en assessment)
        if action_type == ActionType.ASSESSMENT_COMPLETE:
            score = metadata.get("score", 0)
            if score >= 90:
                bonus += 50
            elif score >= 80:
                bonus += 25
        
        # Bonus por velocidad
        if metadata.get("fast_completion", False):
            bonus += 30
        
        # Bonus por fin de semana (aumentar engagement)
        if datetime.now().weekday() >= 5:  # Sábado o domingo
            bonus += 10
        
        return bonus
    
    async def _update_profile_points(self, profile: UserGamificationProfile, points: int):
        """Actualiza los puntos del perfil del usuario."""
        
        profile.total_points += points
        profile.current_level_points += points
        profile.updated_at = datetime.now()
        
        # Calcular puntos necesarios para próximo nivel
        required_points = self._calculate_level_points(profile.level + 1)
        profile.points_to_next_level = max(0, required_points - profile.total_points)
    
    def _calculate_level_points(self, level: int) -> int:
        """Calcula los puntos necesarios para alcanzar un nivel."""
        
        base = self.level_config["base_points"]
        multiplier = self.level_config["multiplier"]
        
        if level == 1:
            return 0
        
        # Fórmula exponencial: base * (multiplier ^ (level - 1))
        return int(base * (multiplier ** (level - 1)))
    
    async def _update_activity_streak(self, profile: UserGamificationProfile):
        """Actualiza el streak de actividad del usuario."""
        
        now = datetime.now()
        
        if profile.last_activity:
            # Verificar si es día consecutivo
            days_diff = (now.date() - profile.last_activity.date()).days
            
            if days_diff == 1:
                # Día consecutivo
                profile.current_streak += 1
                profile.longest_streak = max(profile.longest_streak, profile.current_streak)
            elif days_diff > 1:
                # Se rompió el streak
                profile.current_streak = 1
            # Si days_diff == 0 (mismo día), no cambiar streak
        else:
            # Primera actividad
            profile.current_streak = 1
            profile.longest_streak = 1
        
        profile.last_activity = now
    
    async def _check_level_up(self, profile: UserGamificationProfile):
        """Verifica si el usuario subió de nivel."""
        
        current_level_points = self._calculate_level_points(profile.level)
        next_level_points = self._calculate_level_points(profile.level + 1)
        
        if (profile.total_points >= next_level_points and 
            profile.level < self.level_config["max_level"]):
            
            old_level = profile.level
            profile.level += 1
            profile.current_level_points = profile.total_points - next_level_points
            
            # Calcular puntos para siguiente nivel
            following_level_points = self._calculate_level_points(profile.level + 1)
            profile.points_to_next_level = following_level_points - profile.total_points
            
            # Award level up bonus
            await self.track_action(
                profile.user_id,
                ActionType.LONG_TERM_ENGAGEMENT,
                metadata={"level_up": True, "new_level": profile.level},
                custom_points=profile.level * 50  # 50 puntos por nivel alcanzado
            )
            
            logger.info(f"Level up: {profile.user_id} from {old_level} to {profile.level}")
    
    async def _check_badge_awards(self, profile: UserGamificationProfile, action: GamificationAction):
        """Verifica si el usuario merece nuevos badges."""
        
        for badge_id, badge in self.badges.items():
            if badge_id in profile.badges_earned:
                continue  # Ya tiene este badge
            
            if await self._check_badge_requirements(profile, badge, action):
                await self._award_badge(profile, badge)
    
    async def _check_badge_requirements(self, profile: UserGamificationProfile,
                                      badge: Badge, action: GamificationAction) -> bool:
        """Verifica si se cumplen los requisitos para un badge."""
        
        requirements = badge.requirements
        
        # Verificar nivel requerido
        if "level" in requirements:
            if profile.level < requirements["level"]:
                return False
        
        # Verificar puntos requeridos
        if badge.points_required > 0:
            if profile.total_points < badge.points_required:
                return False
        
        # Verificar acciones específicas
        if "actions" in requirements:
            required_actions = requirements["actions"]
            user_actions = [a.action_type for a in self.actions_log if a.user_id == profile.user_id]
            
            for req_action in required_actions:
                if ActionType(req_action) not in user_actions:
                    return False
        
        # Verificar assessments perfectos
        if "perfect_assessments" in requirements:
            user_perfect_assessments = [
                a for a in self.actions_log 
                if (a.user_id == profile.user_id and 
                    a.action_type == ActionType.ASSESSMENT_PERFECT_SCORE)
            ]
            
            required_count = requirements["perfect_assessments"]
            category = requirements.get("category")
            
            if category:
                # Filtrar por categoría
                category_perfect = [
                    a for a in user_perfect_assessments
                    if a.metadata.get("category") == category
                ]
                if len(category_perfect) < required_count:
                    return False
            else:
                if len(user_perfect_assessments) < required_count:
                    return False
        
        # Verificar referencias exitosas
        if "successful_referrals" in requirements:
            user_referrals = [
                a for a in self.actions_log 
                if (a.user_id == profile.user_id and 
                    a.action_type == ActionType.REFERRAL_HIRED)
            ]
            if len(user_referrals) < requirements["successful_referrals"]:
                return False
        
        return True
    
    async def _award_badge(self, profile: UserGamificationProfile, badge: Badge):
        """Otorga un badge al usuario."""
        
        profile.badges_earned.append(badge.id)
        
        # Award points for badge
        if badge.points_value > 0:
            await self._update_profile_points(profile, badge.points_value)
        
        logger.info(f"Badge awarded: {profile.user_id} - {badge.name}")
    
    async def _check_challenge_progress(self, profile: UserGamificationProfile, action: GamificationAction):
        """Verifica el progreso en challenges activos."""
        
        for challenge_id, challenge in self.challenges.items():
            if not challenge.is_active:
                continue
            
            if challenge_id in profile.challenges_completed:
                continue  # Ya completó este challenge
            
            # Verificar si la acción cuenta para este challenge
            if (challenge.target_actions and 
                action.action_type not in challenge.target_actions):
                continue
            
            # Calcular progreso actual
            progress = await self._calculate_challenge_progress(profile.user_id, challenge)
            
            # Verificar si completó el challenge
            if progress >= challenge.target_value:
                await self._complete_challenge(profile, challenge)
    
    async def _calculate_challenge_progress(self, user_id: str, challenge: Challenge) -> int:
        """Calcula el progreso actual en un challenge."""
        
        # Obtener acciones del usuario en el timeframe del challenge
        end_time = datetime.now()
        start_time = end_time - challenge.target_timeframe
        
        user_actions = [
            a for a in self.actions_log
            if (a.user_id == user_id and 
                start_time <= a.timestamp <= end_time)
        ]
        
        if challenge.target_actions:
            # Contar acciones específicas
            relevant_actions = [
                a for a in user_actions
                if a.action_type in challenge.target_actions
            ]
            return len(relevant_actions)
        else:
            # Contar todas las acciones
            return len(user_actions)
    
    async def _complete_challenge(self, profile: UserGamificationProfile, challenge: Challenge):
        """Marca un challenge como completado y otorga rewards."""
        
        profile.challenges_completed.append(challenge.id)
        
        # Award completion points
        if challenge.completion_points > 0:
            await self._update_profile_points(profile, challenge.completion_points)
        
        # Award completion badges
        for badge_id in challenge.completion_badges:
            if badge_id not in profile.badges_earned and badge_id in self.badges:
                await self._award_badge(profile, self.badges[badge_id])
        
        # Process completion rewards
        for reward in challenge.completion_rewards:
            await self._process_reward(profile.user_id, reward)
        
        logger.info(f"Challenge completed: {profile.user_id} - {challenge.name}")
    
    async def _process_reward(self, user_id: str, reward: Dict[str, Any]):
        """Procesa un reward otorgado al usuario."""
        
        reward_type = RewardType(reward["type"])
        reward_value = reward["value"]
        
        # En un sistema real, esto integraría con otros servicios
        if reward_type == RewardType.COURSE_ACCESS:
            # Dar acceso a curso específico
            logger.info(f"Granted course access: {user_id} - {reward_value}")
        
        elif reward_type == RewardType.CAREER_CONSULTATION:
            # Programar consulta de carrera
            logger.info(f"Scheduled career consultation: {user_id} - {reward_value}")
        
        elif reward_type == RewardType.GIFT_CARD:
            # Generar gift card
            logger.info(f"Generated gift card: {user_id} - ${reward_value}")
    
    def get_leaderboard(self, category: str = "global", 
                       period: str = "all_time", 
                       limit: int = 50) -> List[Dict[str, Any]]:
        """Obtiene el leaderboard según categoría y período."""
        
        # Filtrar usuarios según criterios
        if period == "weekly":
            start_date = datetime.now() - timedelta(days=7)
        elif period == "monthly":
            start_date = datetime.now() - timedelta(days=30)
        elif period == "daily":
            start_date = datetime.now() - timedelta(days=1)
        else:
            start_date = None
        
        # Calcular puntos por usuario en el período
        user_points = defaultdict(int)
        
        for action in self.actions_log:
            if start_date and action.timestamp < start_date:
                continue
            
            # Filtrar por categoría si es necesario
            if category != "global":
                if action.metadata.get("category") != category:
                    continue
            
            user_points[action.user_id] += action.total_points
        
        # Si es all_time, usar puntos totales del perfil
        if period == "all_time":
            for user_id, profile in self.user_profiles.items():
                if category == "global":
                    user_points[user_id] = profile.total_points
        
        # Crear ranking
        leaderboard = []
        sorted_users = sorted(user_points.items(), key=lambda x: x[1], reverse=True)
        
        for rank, (user_id, points) in enumerate(sorted_users[:limit], 1):
            profile = self.user_profiles.get(user_id)
            if not profile:
                continue
            
            leaderboard.append({
                "rank": rank,
                "user_id": user_id,
                "points": points,
                "level": profile.level,
                "badges_count": len(profile.badges_earned),
                "current_streak": profile.current_streak,
                "total_points": profile.total_points
            })
        
        return leaderboard
    
    def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Obtiene estadísticas completas de un usuario."""
        
        profile = self.user_profiles.get(user_id)
        if not profile:
            return {"error": "User not found"}
        
        # Calcular estadísticas de acciones
        user_actions = [a for a in self.actions_log if a.user_id == user_id]
        actions_by_type = defaultdict(int)
        total_points_earned = 0
        
        for action in user_actions:
            actions_by_type[action.action_type.value] += 1
            total_points_earned += action.total_points
        
        # Calcular progreso en challenges activos
        active_challenges = []
        for challenge_id, challenge in self.challenges.items():
            if challenge.is_active and challenge_id not in profile.challenges_completed:
                progress = asyncio.run(self._calculate_challenge_progress(user_id, challenge))
                active_challenges.append({
                    "id": challenge_id,
                    "name": challenge.name,
                    "description": challenge.description,
                    "progress": progress,
                    "target": challenge.target_value,
                    "completion_percentage": min(100, (progress / challenge.target_value) * 100)
                })
        
        # Obtener badges con detalles
        earned_badges = []
        for badge_id in profile.badges_earned:
            if badge_id in self.badges:
                badge = self.badges[badge_id]
                earned_badges.append({
                    "id": badge_id,
                    "name": badge.name,
                    "description": badge.description,
                    "rarity": badge.rarity,
                    "icon_url": badge.icon_url
                })
        
        return {
            "profile": {
                "user_id": user_id,
                "total_points": profile.total_points,
                "level": profile.level,
                "current_level_points": profile.current_level_points,
                "points_to_next_level": profile.points_to_next_level,
                "current_streak": profile.current_streak,
                "longest_streak": profile.longest_streak,
                "global_rank": profile.global_rank
            },
            "activity": {
                "total_actions": len(user_actions),
                "actions_by_type": dict(actions_by_type),
                "total_points_earned": total_points_earned,
                "last_activity": profile.last_activity.isoformat() if profile.last_activity else None
            },
            "badges": {
                "total_earned": len(earned_badges),
                "badges": earned_badges
            },
            "challenges": {
                "completed": len(profile.challenges_completed),
                "active": active_challenges
            }
        }
    
    def get_engagement_analytics(self, date_range: Optional[tuple] = None) -> Dict[str, Any]:
        """Obtiene analíticas de engagement del sistema."""
        
        start_date, end_date = date_range or (datetime.now() - timedelta(days=30), datetime.now())
        
        # Filtrar acciones en el rango
        period_actions = [
            a for a in self.actions_log
            if start_date <= a.timestamp <= end_date
        ]
        
        # Métricas generales
        total_users = len(self.user_profiles)
        active_users = len(set(a.user_id for a in period_actions))
        total_actions = len(period_actions)
        total_points_awarded = sum(a.total_points for a in period_actions)
        
        # Acciones por tipo
        actions_by_type = defaultdict(int)
        for action in period_actions:
            actions_by_type[action.action_type.value] += 1
        
        # Distribución de niveles
        level_distribution = defaultdict(int)
        for profile in self.user_profiles.values():
            level_range = f"{(profile.level // 10) * 10}-{(profile.level // 10) * 10 + 9}"
            level_distribution[level_range] += 1
        
        # Badges más populares
        badge_popularity = defaultdict(int)
        for profile in self.user_profiles.values():
            for badge_id in profile.badges_earned:
                if badge_id in self.badges:
                    badge_popularity[self.badges[badge_id].name] += 1
        
        # Challenges más completados
        challenge_completion = defaultdict(int)
        for profile in self.user_profiles.values():
            for challenge_id in profile.challenges_completed:
                if challenge_id in self.challenges:
                    challenge_completion[self.challenges[challenge_id].name] += 1
        
        return {
            "overview": {
                "total_users": total_users,
                "active_users": active_users,
                "engagement_rate": (active_users / total_users * 100) if total_users > 0 else 0,
                "total_actions": total_actions,
                "avg_actions_per_user": total_actions / active_users if active_users > 0 else 0,
                "total_points_awarded": total_points_awarded
            },
            "activity": {
                "actions_by_type": dict(sorted(actions_by_type.items(), key=lambda x: x[1], reverse=True)),
                "daily_activity": self._calculate_daily_activity(period_actions)
            },
            "progression": {
                "level_distribution": dict(level_distribution),
                "avg_level": sum(p.level for p in self.user_profiles.values()) / total_users if total_users > 0 else 0
            },
            "achievements": {
                "popular_badges": dict(sorted(badge_popularity.items(), key=lambda x: x[1], reverse=True)[:10]),
                "completed_challenges": dict(sorted(challenge_completion.items(), key=lambda x: x[1], reverse=True))
            }
        }
    
    def _calculate_daily_activity(self, actions: List[GamificationAction]) -> Dict[str, int]:
        """Calcula actividad diaria en un período."""
        
        daily_activity = defaultdict(int)
        
        for action in actions:
            date_key = action.timestamp.strftime('%Y-%m-%d')
            daily_activity[date_key] += 1
        
        return dict(daily_activity)

# Funciones de utilidad
async def track_user_action(user_id: str, action: str, **kwargs) -> bool:
    """Función de conveniencia para tracking de acciones."""
    
    gamification = GamificationEngine()
    
    try:
        action_type = ActionType(action)
        await gamification.track_action(user_id, action_type, **kwargs)
        return True
    except ValueError:
        logger.error(f"Invalid action type: {action}")
        return False

def get_user_gamification_summary(user_id: str) -> Dict[str, Any]:
    """Obtiene resumen de gamificación para un usuario."""
    
    gamification = GamificationEngine()
    return gamification.get_user_stats(user_id)

# Exportaciones
__all__ = [
    'ActionType', 'BadgeType', 'ChallengeType', 'RewardType',
    'GamificationAction', 'Badge', 'Challenge', 'UserGamificationProfile',
    'GamificationEngine', 'track_user_action', 'get_user_gamification_summary'
]