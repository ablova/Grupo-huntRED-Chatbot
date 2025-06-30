# app/ml/aura/gamification/achievement_system.py
"""
AURA - Sistema de Gamificación Avanzada
Achievement System & Professional Growth Gamification
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import hashlib
from app.ml.aura.graph_builder import GNNManager
from app.ats.integrations.services.gamification.achievement import Achievement

logger = logging.getLogger(__name__)


class AchievementType(Enum):
    """Tipos de logros disponibles"""
    NETWORK_GROWTH = "network_growth"
    INFLUENCE_BUILDING = "influence_building"
    COMMUNITY_LEADERSHIP = "community_leadership"
    SKILL_DEVELOPMENT = "skill_development"
    COLLABORATION = "collaboration"
    INNOVATION = "innovation"
    MENTORSHIP = "mentorship"
    KNOWLEDGE_SHARING = "knowledge_sharing"
    CAREER_MILESTONE = "career_milestone"
    NETWORK_QUALITY = "network_quality"


class BadgeRarity(Enum):
    """Rareza de las insignias"""
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"


@dataclass
class UserAchievement:
    """Logro obtenido por un usuario"""
    user_id: int
    achievement_id: str
    earned_at: datetime
    progress: float = 100.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UserProfile:
    """Perfil gamificado del usuario"""
    user_id: int
    level: int = 1
    experience: int = 0
    total_points: int = 0
    achievements_earned: int = 0
    current_streak: int = 0
    longest_streak: int = 0
    last_activity: datetime = field(default_factory=datetime.now)
    badges: List[str] = field(default_factory=list)
    stats: Dict[str, Any] = field(default_factory=dict)


class AchievementSystem:
    """
    Sistema principal de logros y gamificación
    """
    
    def __init__(self):
        self.gnn = GNNManager()
        self.last_achievements = {}
        self.achievements = {}
        self.user_profiles = {}
        self.user_achievements = {}
        self.level_thresholds = self._calculate_level_thresholds()
        self._initialize_achievements()
    
    def _calculate_level_thresholds(self) -> Dict[int, int]:
        """Calcula los umbrales de experiencia para cada nivel"""
        thresholds = {}
        base_exp = 100
        for level in range(1, 101):  # Máximo nivel 100
            thresholds[level] = int(base_exp * (level ** 1.5))
        return thresholds
    
    def _initialize_achievements(self):
        """Inicializa todos los logros disponibles"""
        self.achievements = {
            # Logros de crecimiento de red
            "first_connection": Achievement(
                id="first_connection",
                name="Primera Conexión",
                description="Establece tu primera conexión profesional",
                type=AchievementType.NETWORK_GROWTH,
                rarity=BadgeRarity.COMMON,
                points=10,
                icon="🔗",
                requirements={"connections": 1},
                rewards={"experience": 50, "badge": "network_starter"}
            ),
            
            "network_builder": Achievement(
                id="network_builder",
                name="Constructor de Redes",
                description="Alcanza 100 conexiones profesionales",
                type=AchievementType.NETWORK_GROWTH,
                rarity=BadgeRarity.UNCOMMON,
                points=100,
                icon="🌐",
                requirements={"connections": 100},
                rewards={"experience": 500, "badge": "network_builder"}
            ),
            
            "network_master": Achievement(
                id="network_master",
                name="Maestro de Redes",
                description="Alcanza 500 conexiones profesionales",
                type=AchievementType.NETWORK_GROWTH,
                rarity=BadgeRarity.RARE,
                points=500,
                icon="🌟",
                requirements={"connections": 500},
                rewards={"experience": 2000, "badge": "network_master"}
            ),
            
            # Logros de influencia
            "influence_riser": Achievement(
                id="influence_riser",
                name="Ascenso de Influencia",
                description="Alcanza un score de influencia de 0.7",
                type=AchievementType.INFLUENCE_BUILDING,
                rarity=BadgeRarity.UNCOMMON,
                points=200,
                icon="📈",
                requirements={"influence_score": 0.7},
                rewards={"experience": 1000, "badge": "influence_riser"}
            ),
            
            "thought_leader": Achievement(
                id="thought_leader",
                name="Líder de Pensamiento",
                description="Alcanza un score de influencia de 0.9",
                type=AchievementType.INFLUENCE_BUILDING,
                rarity=BadgeRarity.EPIC,
                points=1000,
                icon="💡",
                requirements={"influence_score": 0.9},
                rewards={"experience": 5000, "badge": "thought_leader"}
            ),
            
            # Logros de liderazgo comunitario
            "community_organizer": Achievement(
                id="community_organizer",
                name="Organizador Comunitario",
                description="Crea o lidera 3 comunidades",
                type=AchievementType.COMMUNITY_LEADERSHIP,
                rarity=BadgeRarity.RARE,
                points=300,
                icon="👥",
                requirements={"communities_led": 3},
                rewards={"experience": 1500, "badge": "community_organizer"}
            ),
            
            # Logros de desarrollo de habilidades
            "skill_learner": Achievement(
                id="skill_learner",
                name="Aprendiz de Habilidades",
                description="Añade 10 habilidades a tu perfil",
                type=AchievementType.SKILL_DEVELOPMENT,
                rarity=BadgeRarity.COMMON,
                points=50,
                icon="📚",
                requirements={"skills_count": 10},
                rewards={"experience": 250, "badge": "skill_learner"}
            ),
            
            "skill_master": Achievement(
                id="skill_master",
                name="Maestro de Habilidades",
                description="Añade 50 habilidades a tu perfil",
                type=AchievementType.SKILL_DEVELOPMENT,
                rarity=BadgeRarity.EPIC,
                points=800,
                icon="🎓",
                requirements={"skills_count": 50},
                rewards={"experience": 4000, "badge": "skill_master"}
            ),
            
            # Logros de colaboración
            "team_player": Achievement(
                id="team_player",
                name="Jugador de Equipo",
                description="Participa en 5 proyectos colaborativos",
                type=AchievementType.COLLABORATION,
                rarity=BadgeRarity.UNCOMMON,
                points=150,
                icon="🤝",
                requirements={"collaborative_projects": 5},
                rewards={"experience": 750, "badge": "team_player"}
            ),
            
            # Logros de innovación
            "innovator": Achievement(
                id="innovator",
                name="Innovador",
                description="Propón 3 ideas innovadoras",
                type=AchievementType.INNOVATION,
                rarity=BadgeRarity.RARE,
                points=400,
                icon="🚀",
                requirements={"innovations_proposed": 3},
                rewards={"experience": 2000, "badge": "innovator"}
            ),
            
            # Logros de mentoría
            "mentor": Achievement(
                id="mentor",
                name="Mentor",
                description="Mentorea a 5 profesionales",
                type=AchievementType.MENTORSHIP,
                rarity=BadgeRarity.EPIC,
                points=600,
                icon="🎯",
                requirements={"mentees_count": 5},
                rewards={"experience": 3000, "badge": "mentor"}
            ),
            
            # Logros de compartir conocimiento
            "knowledge_sharer": Achievement(
                id="knowledge_sharer",
                name="Compartidor de Conocimiento",
                description="Comparte 20 piezas de contenido valioso",
                type=AchievementType.KNOWLEDGE_SHARING,
                rarity=BadgeRarity.UNCOMMON,
                points=200,
                icon="📖",
                requirements={"content_shared": 20},
                rewards={"experience": 1000, "badge": "knowledge_sharer"}
            ),
            
            # Logros de hitos de carrera
            "career_launcher": Achievement(
                id="career_launcher",
                name="Lanzador de Carrera",
                description="Completa tu primer año profesional",
                type=AchievementType.CAREER_MILESTONE,
                rarity=BadgeRarity.COMMON,
                points=100,
                icon="🎉",
                requirements={"years_experience": 1},
                rewards={"experience": 500, "badge": "career_launcher"}
            ),
            
            "career_expert": Achievement(
                id="career_expert",
                name="Experto de Carrera",
                description="Completa 10 años de experiencia profesional",
                type=AchievementType.CAREER_MILESTONE,
                rarity=BadgeRarity.LEGENDARY,
                points=2000,
                icon="👑",
                requirements={"years_experience": 10},
                rewards={"experience": 10000, "badge": "career_expert"}
            ),
            
            # Logros de calidad de red
            "quality_networker": Achievement(
                id="quality_networker",
                name="Red de Calidad",
                description="Mantén un score de calidad de red de 0.8+",
                type=AchievementType.NETWORK_QUALITY,
                rarity=BadgeRarity.RARE,
                points=300,
                icon="⭐",
                requirements={"network_quality_score": 0.8},
                rewards={"experience": 1500, "badge": "quality_networker"}
            ),
            
            # Logros ocultos
            "early_adopter": Achievement(
                id="early_adopter",
                name="Adoptador Temprano",
                description="Únete a AURA en sus primeros días",
                type=AchievementType.CAREER_MILESTONE,
                rarity=BadgeRarity.LEGENDARY,
                points=1000,
                icon="🌅",
                requirements={"join_date": "2024-01-01"},
                rewards={"experience": 5000, "badge": "early_adopter"},
                is_hidden=True
            ),
            
            "streak_master": Achievement(
                id="streak_master",
                name="Maestro de Racha",
                description="Mantén una racha de actividad de 30 días",
                type=AchievementType.NETWORK_GROWTH,
                rarity=BadgeRarity.EPIC,
                points=500,
                icon="🔥",
                requirements={"activity_streak": 30},
                rewards={"experience": 2500, "badge": "streak_master"}
            )
        }
    
    def get_user_profile(self, user_id: int) -> UserProfile:
        """Obtiene o crea el perfil gamificado del usuario"""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = UserProfile(user_id=user_id)
        return self.user_profiles[user_id]
    
    def check_achievements(self, user_id: int, user_data: Dict[str, Any]) -> List[Achievement]:
        """
        Verifica qué logros puede obtener el usuario basado en sus datos
        """
        earned_achievements = []
        profile = self.get_user_profile(user_id)
        
        for achievement in self.achievements.values():
            # Saltar logros ya obtenidos
            if self.has_achievement(user_id, achievement.id):
                continue
            
            # Verificar si cumple los requisitos
            if self._check_requirements(achievement.requirements, user_data):
                earned_achievements.append(achievement)
        
        return earned_achievements
    
    def _check_requirements(self, requirements: Dict[str, Any], user_data: Dict[str, Any]) -> bool:
        """Verifica si el usuario cumple los requisitos de un logro"""
        for key, required_value in requirements.items():
            if key not in user_data:
                return False
            
            user_value = user_data[key]
            
            # Comparaciones específicas por tipo de dato
            if isinstance(required_value, (int, float)):
                if user_value < required_value:
                    return False
            elif isinstance(required_value, str):
                if key == "join_date":
                    # Verificar fecha de unión
                    try:
                        join_date = datetime.strptime(user_value, "%Y-%m-%d")
                        user_join_date = datetime.strptime(user_data.get("join_date", "2024-01-01"), "%Y-%m-%d")
                        if user_join_date > join_date:
                            return False
                    except:
                        return False
                elif user_value != required_value:
                    return False
            else:
                if user_value != required_value:
                    return False
        
        return True
    
    def award_achievement(self, user_id: int, achievement: Achievement) -> bool:
        """
        Otorga un logro al usuario
        """
        try:
            # Verificar que no lo tenga ya
            if self.has_achievement(user_id, achievement.id):
                return False
            
            # Crear registro de logro
            user_achievement = UserAchievement(
                user_id=user_id,
                achievement_id=achievement.id,
                earned_at=datetime.now()
            )
            
            # Guardar en el sistema
            if user_id not in self.user_achievements:
                self.user_achievements[user_id] = []
            self.user_achievements[user_id].append(user_achievement)
            
            # Actualizar perfil del usuario
            profile = self.get_user_profile(user_id)
            profile.achievements_earned += 1
            profile.total_points += achievement.points
            
            # Aplicar recompensas
            self._apply_rewards(user_id, achievement.rewards)
            
            # Calcular nuevo nivel
            self._calculate_level(user_id)
            
            logger.info(f"Logro otorgado: {achievement.name} a usuario {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error otorgando logro {achievement.id} a usuario {user_id}: {e}")
            return False
    
    def _apply_rewards(self, user_id: int, rewards: Dict[str, Any]):
        """Aplica las recompensas de un logro"""
        profile = self.get_user_profile(user_id)
        
        for reward_type, value in rewards.items():
            if reward_type == "experience":
                profile.experience += value
            elif reward_type == "badge":
                if value not in profile.badges:
                    profile.badges.append(value)
    
    def _calculate_level(self, user_id: int):
        """Calcula el nivel actual del usuario basado en su experiencia"""
        profile = self.get_user_profile(user_id)
        
        for level, threshold in self.level_thresholds.items():
            if profile.experience >= threshold:
                profile.level = level
            else:
                break
    
    def has_achievement(self, user_id: int, achievement_id: str) -> bool:
        """Verifica si el usuario tiene un logro específico"""
        if user_id not in self.user_achievements:
            return False
        
        return any(ua.achievement_id == achievement_id for ua in self.user_achievements[user_id])
    
    def get_user_achievements(self, user_id: int) -> List[UserAchievement]:
        """Obtiene todos los logros del usuario"""
        return self.user_achievements.get(user_id, [])
    
    def get_achievement_progress(self, user_id: int, achievement_id: str) -> float:
        """Obtiene el progreso de un logro específico"""
        if achievement_id not in self.achievements:
            return 0.0
        
        achievement = self.achievements[achievement_id]
        user_data = self._get_user_data_for_progress(user_id)
        
        # Calcular progreso basado en requisitos
        progress_values = []
        for key, required_value in achievement.requirements.items():
            if key in user_data:
                user_value = user_data[key]
                if isinstance(required_value, (int, float)) and required_value > 0:
                    progress = min(user_value / required_value, 1.0)
                    progress_values.append(progress)
        
        return sum(progress_values) / len(progress_values) if progress_values else 0.0
    
    def _get_user_data_for_progress(self, user_id: int) -> Dict[str, Any]:
        """Obtiene datos del usuario para calcular progreso"""
        # En implementación real, esto vendría de la base de datos
        return {
            "connections": 150,
            "influence_score": 0.75,
            "communities_led": 2,
            "skills_count": 25,
            "collaborative_projects": 3,
            "innovations_proposed": 1,
            "mentees_count": 2,
            "content_shared": 15,
            "years_experience": 5,
            "network_quality_score": 0.85,
            "activity_streak": 12
        }
    
    def get_leaderboard(self, category: str = "total_points", limit: int = 10) -> List[Tuple[int, UserProfile]]:
        """Obtiene el ranking de usuarios"""
        profiles = list(self.user_profiles.values())
        
        if category == "total_points":
            profiles.sort(key=lambda p: p.total_points, reverse=True)
        elif category == "level":
            profiles.sort(key=lambda p: p.level, reverse=True)
        elif category == "achievements":
            profiles.sort(key=lambda p: p.achievements_earned, reverse=True)
        elif category == "streak":
            profiles.sort(key=lambda p: p.current_streak, reverse=True)
        
        return [(profile.user_id, profile) for profile in profiles[:limit]]
    
    def get_achievement_suggestions(self, user_id: int) -> List[Achievement]:
        """Obtiene sugerencias de logros próximos a obtener"""
        user_data = self._get_user_data_for_progress(user_id)
        suggestions = []
        
        for achievement in self.achievements.values():
            if not self.has_achievement(user_id, achievement.id):
                progress = self.get_achievement_progress(user_id, achievement.id)
                if 0.3 <= progress < 1.0:  # Entre 30% y 99% de progreso
                    suggestions.append(achievement)
        
        # Ordenar por proximidad a completarse
        suggestions.sort(key=lambda a: self.get_achievement_progress(user_id, a.id), reverse=True)
        return suggestions[:5]
    
    def update_user_activity(self, user_id: int):
        """Actualiza la actividad del usuario y maneja rachas"""
        profile = self.get_user_profile(user_id)
        now = datetime.now()
        
        # Verificar si es actividad consecutiva
        if (now - profile.last_activity).days <= 1:
            profile.current_streak += 1
            if profile.current_streak > profile.longest_streak:
                profile.longest_streak = profile.current_streak
        else:
            profile.current_streak = 1
        
        profile.last_activity = now
    
    def get_daily_challenges(self, user_id: int) -> List[Dict[str, Any]]:
        """Genera desafíos diarios personalizados"""
        profile = self.get_user_profile(user_id)
        
        challenges = [
            {
                "id": "daily_connection",
                "title": "Nueva Conexión",
                "description": "Conecta con un nuevo profesional hoy",
                "type": "connection",
                "points": 20,
                "progress": 0,
                "target": 1
            },
            {
                "id": "daily_content",
                "title": "Compartir Conocimiento",
                "description": "Comparte una pieza de contenido valioso",
                "type": "content",
                "points": 30,
                "progress": 0,
                "target": 1
            },
            {
                "id": "daily_skill",
                "title": "Aprender Habilidad",
                "description": "Añade una nueva habilidad a tu perfil",
                "type": "skill",
                "points": 25,
                "progress": 0,
                "target": 1
            },
            {
                "id": "daily_community",
                "title": "Participación Comunitaria",
                "description": "Participa activamente en una comunidad",
                "type": "community",
                "points": 15,
                "progress": 0,
                "target": 1
            }
        ]
        
        return challenges
    
    def get_weekly_goals(self, user_id: int) -> List[Dict[str, Any]]:
        """Genera objetivos semanales personalizados"""
        profile = self.get_user_profile(user_id)
        
        goals = [
            {
                "id": "weekly_connections",
                "title": "Expansión de Red",
                "description": "Añade 10 nuevas conexiones esta semana",
                "type": "connections",
                "points": 100,
                "progress": 0,
                "target": 10,
                "deadline": datetime.now() + timedelta(days=7)
            },
            {
                "id": "weekly_influence",
                "title": "Crecimiento de Influencia",
                "description": "Aumenta tu score de influencia en 0.1",
                "type": "influence",
                "points": 150,
                "progress": 0,
                "target": 0.1,
                "deadline": datetime.now() + timedelta(days=7)
            },
            {
                "id": "weekly_content",
                "title": "Creador de Contenido",
                "description": "Comparte 5 piezas de contenido valioso",
                "type": "content",
                "points": 200,
                "progress": 0,
                "target": 5,
                "deadline": datetime.now() + timedelta(days=7)
            }
        ]
        
        return goals
    
    def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Obtiene estadísticas detalladas del usuario"""
        profile = self.get_user_profile(user_id)
        achievements = self.get_user_achievements(user_id)
        
        # Calcular estadísticas de logros
        achievement_types = {}
        rarity_counts = {}
        
        for ua in achievements:
            achievement = self.achievements.get(ua.achievement_id)
            if achievement:
                # Contar por tipo
                achievement_types[achievement.type.value] = achievement_types.get(achievement.type.value, 0) + 1
                
                # Contar por rareza
                rarity_counts[achievement.rarity.value] = rarity_counts.get(achievement.rarity.value, 0) + 1
        
        # Calcular progreso hacia siguiente nivel
        next_level_exp = self.level_thresholds.get(profile.level + 1, profile.experience)
        level_progress = ((profile.experience - self.level_thresholds.get(profile.level, 0)) / 
                         (next_level_exp - self.level_thresholds.get(profile.level, 0))) * 100
        
        return {
            "level": profile.level,
            "experience": profile.experience,
            "total_points": profile.total_points,
            "achievements_earned": profile.achievements_earned,
            "current_streak": profile.current_streak,
            "longest_streak": profile.longest_streak,
            "badges": profile.badges,
            "achievement_types": achievement_types,
            "rarity_counts": rarity_counts,
            "level_progress": level_progress,
            "next_level_exp": next_level_exp,
            "total_achievements": len(self.achievements),
            "completion_percentage": (profile.achievements_earned / len(self.achievements)) * 100
        }

    def award(self, user_id: str, achievement: str) -> Dict[str, Any]:
        """
        Otorga un logro/badge al usuario.
        Args:
            user_id: ID del usuario
            achievement: nombre del logro
        Returns:
            dict con logros actualizados
        """
        achievements = self.gnn.award_achievement(user_id, achievement)
        self.last_achievements[user_id] = achievements
        logger.info(f"AchievementSystem: logro '{achievement}' otorgado a {user_id}.")
        return {'user_id': user_id, 'achievements': achievements, 'timestamp': datetime.now().isoformat()}

    def get(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Devuelve los logros y badges del usuario.
        """
        achievements = self.gnn.get_achievements(user_id)
        return achievements

    def ranking(self, business_unit: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Devuelve el ranking de impacto social/profesional.
        """
        ranking = self.gnn.get_impact_ranking(business_unit)
        return ranking

# Instancia global del sistema de logros
achievement_system = AchievementSystem() 