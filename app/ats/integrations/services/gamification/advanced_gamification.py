# app/ats/integrations/services/gamification/advanced_gamification.py
"""
GAMIFICACIÓN AVANZADA - Grupo huntRED®
Sistema de gamificación con niveles dinámicos, competencias, recompensas inteligentes y analytics
"""

import logging
import json
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import numpy as np
from django.utils import timezone
from django.core.cache import cache

from .predictive_analytics import predictive_analytics
from app.ats.integrations.services.gamification.achievement import Achievement

logger = logging.getLogger(__name__)

@dataclass
class UserLevel:
    """Nivel de usuario"""
    level: int
    experience: int
    experience_to_next: int
    title: str
    badge: str
    unlocked_features: List[str]

@dataclass
class Reward:
    """Recompensa"""
    id: str
    type: str  # points, badge, feature, discount, bonus
    value: Any
    description: str
    expires_at: Optional[datetime] = None

@dataclass
class Competition:
    """Competencia"""
    id: str
    name: str
    description: str
    start_date: datetime
    end_date: datetime
    participants: List[str]
    leaderboard: List[Dict[str, Any]]
    rewards: List[Reward]

class AdvancedGamification:
    """
    Sistema de gamificación avanzado
    """
    
    def __init__(self):
        # Configuración de niveles
        self.level_config = {
            'base_experience': 100,
            'experience_multiplier': 1.5,
            'max_level': 50,
            'titles': [
                'Novato', 'Aprendiz', 'Aspirante', 'Candidato', 'Profesional',
                'Experto', 'Maestro', 'Gurú', 'Leyenda', 'Mito'
            ]
        }
        
        # Configuración de logros
        self.achievements = self._load_achievements()
        
        # Configuración de recompensas
        self.reward_templates = self._load_reward_templates()
        
        # Competencias activas
        self.active_competitions = {}
        
        # Cache de usuarios
        self.user_cache = {}
        
        # Métricas
        self.metrics = {
            'total_users': 0,
            'total_achievements': 0,
            'total_rewards': 0,
            'active_competitions': 0,
            'avg_user_level': 0.0
        }
    
    def _load_achievements(self) -> Dict[str, Dict[str, Any]]:
        """Carga configuración de logros"""
        return {
            'first_profile': {
                'name': 'Primer Paso',
                'description': 'Completa tu perfil por primera vez',
                'icon': '👤',
                'points': 50,
                'rarity': 'common'
            },
            'profile_complete': {
                'name': 'Perfil Completo',
                'description': 'Completa el 100% de tu perfil',
                'icon': '✅',
                'points': 100,
                'rarity': 'common'
            },
            'first_application': {
                'name': 'Primera Aplicación',
                'description': 'Envía tu primera aplicación',
                'icon': '📝',
                'points': 75,
                'rarity': 'common'
            },
            'application_streak': {
                'name': 'Serie de Aplicaciones',
                'description': 'Aplica a 5 trabajos en una semana',
                'icon': '🔥',
                'points': 200,
                'rarity': 'rare'
            },
            'first_interview': {
                'name': 'Primera Entrevista',
                'description': 'Completa tu primera entrevista',
                'icon': '🎯',
                'points': 150,
                'rarity': 'rare'
            },
            'job_offer': {
                'name': '¡Oferta de Trabajo!',
                'description': 'Recibe tu primera oferta de trabajo',
                'icon': '🎉',
                'points': 500,
                'rarity': 'epic'
            },
            'referral_master': {
                'name': 'Maestro de Referencias',
                'description': 'Refiere a 10 personas exitosamente',
                'icon': '🌟',
                'points': 300,
                'rarity': 'epic'
            },
            'perfect_match': {
                'name': 'Match Perfecto',
                'description': 'Encuentra el trabajo ideal en menos de 30 días',
                'icon': '💎',
                'points': 1000,
                'rarity': 'legendary'
            }
        }
    
    def _load_reward_templates(self) -> Dict[str, Dict[str, Any]]:
        """Carga plantillas de recompensas"""
        return {
            'level_up': {
                'type': 'points',
                'base_value': 100,
                'multiplier': 1.2,
                'description': '¡Subiste de nivel!'
            },
            'achievement_unlock': {
                'type': 'badge',
                'base_value': 'achievement_badge',
                'description': '¡Nuevo logro desbloqueado!'
            },
            'streak_bonus': {
                'type': 'points',
                'base_value': 50,
                'multiplier': 1.5,
                'description': '¡Bonus por racha!'
            },
            'competition_winner': {
                'type': 'feature',
                'base_value': 'premium_features',
                'description': '¡Ganador de competencia!'
            },
            'referral_bonus': {
                'type': 'points',
                'base_value': 25,
                'multiplier': 1.0,
                'description': '¡Bonus por referido!'
            }
        }
    
    async def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """
        Obtiene perfil completo de gamificación del usuario
        """
        try:
            # Intentar obtener de cache
            cache_key = f"gamification_profile:{user_id}"
            cached_profile = cache.get(cache_key)
            
            if cached_profile:
                return cached_profile
            
            # Obtener datos del usuario
            user_data = await self._get_user_data(user_id)
            
            # Calcular nivel
            level_info = self._calculate_level(user_data.get('experience', 0))
            
            # Obtener logros
            achievements = await self._get_user_achievements(user_id)
            
            # Obtener recompensas activas
            active_rewards = await self._get_active_rewards(user_id)
            
            # Calcular estadísticas
            stats = await self._calculate_user_stats(user_id)
            
            # Crear perfil completo
            profile = {
                'user_id': user_id,
                'level': level_info,
                'achievements': achievements,
                'active_rewards': active_rewards,
                'stats': stats,
                'last_updated': timezone.now().isoformat()
            }
            
            # Cachear perfil
            cache.set(cache_key, profile, 1800)  # 30 minutos
            
            return profile
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo perfil de gamificación: {e}")
            return {'user_id': user_id, 'error': str(e)}
    
    def _calculate_level(self, experience: int) -> UserLevel:
        """Calcula nivel basado en experiencia"""
        try:
            level = 1
            exp_needed = self.level_config['base_experience']
            current_exp = experience
            
            # Calcular nivel actual
            while current_exp >= exp_needed and level < self.level_config['max_level']:
                current_exp -= exp_needed
                level += 1
                exp_needed = int(exp_needed * self.level_config['experience_multiplier'])
            
            # Calcular experiencia para siguiente nivel
            experience_to_next = exp_needed - current_exp
            
            # Determinar título
            title_index = min((level - 1) // 5, len(self.level_config['titles']) - 1)
            title = self.level_config['titles'][title_index]
            
            # Determinar badge
            badge = self._get_level_badge(level)
            
            # Características desbloqueadas
            unlocked_features = self._get_unlocked_features(level)
            
            return UserLevel(
                level=level,
                experience=current_exp,
                experience_to_next=experience_to_next,
                title=title,
                badge=badge,
                unlocked_features=unlocked_features
            )
            
        except Exception as e:
            logger.error(f"❌ Error calculando nivel: {e}")
            return UserLevel(
                level=1,
                experience=0,
                experience_to_next=100,
                title='Novato',
                badge='🥉',
                unlocked_features=[]
            )
    
    def _get_level_badge(self, level: int) -> str:
        """Obtiene badge del nivel"""
        if level <= 5:
            return '🥉'
        elif level <= 15:
            return '🥈'
        elif level <= 30:
            return '🥇'
        elif level <= 45:
            return '💎'
        else:
            return '👑'
    
    def _get_unlocked_features(self, level: int) -> List[str]:
        """Obtiene características desbloqueadas por nivel"""
        features = []
        
        if level >= 5:
            features.append('advanced_search')
        if level >= 10:
            features.append('priority_applications')
        if level >= 15:
            features.append('direct_messaging')
        if level >= 20:
            features.append('salary_insights')
        if level >= 25:
            features.append('interview_prep')
        if level >= 30:
            features.append('mentorship_access')
        if level >= 35:
            features.append('exclusive_jobs')
        if level >= 40:
            features.append('career_coaching')
        if level >= 45:
            features.append('vip_support')
        
        return features
    
    async def award_experience(self, user_id: str, action: str, 
                             value: int = 1, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Otorga experiencia al usuario por una acción
        """
        try:
            # Obtener perfil actual
            profile = await self.get_user_profile(user_id)
            current_level = profile['level']['level']
            current_exp = profile['level']['experience']
            
            # Calcular experiencia a otorgar
            base_exp = self._get_action_experience(action)
            bonus_exp = self._calculate_bonus_experience(context)
            total_exp = (base_exp + bonus_exp) * value
            
            # Actualizar experiencia
            new_exp = current_exp + total_exp
            
            # Calcular nuevo nivel
            new_level_info = self._calculate_level(new_exp)
            
            # Verificar si subió de nivel
            level_up = new_level_info.level > current_level
            
            # Generar recompensa por subir de nivel
            level_reward = None
            if level_up:
                level_reward = await self._generate_level_reward(user_id, new_level_info.level)
            
            # Actualizar datos del usuario
            await self._update_user_experience(user_id, new_exp)
            
            # Verificar logros
            new_achievements = await self._check_achievements(user_id, action, context)
            
            # Limpiar cache
            cache.delete(f"gamification_profile:{user_id}")
            
            return {
                'user_id': user_id,
                'action': action,
                'experience_gained': total_exp,
                'new_level': new_level_info.level,
                'level_up': level_up,
                'level_reward': level_reward,
                'new_achievements': new_achievements,
                'total_experience': new_exp
            }
            
        except Exception as e:
            logger.error(f"❌ Error otorgando experiencia: {e}")
            return {'error': str(e)}
    
    def _get_action_experience(self, action: str) -> int:
        """Obtiene experiencia base por acción"""
        action_exp = {
            'profile_update': 10,
            'profile_complete': 50,
            'job_search': 5,
            'job_apply': 25,
            'interview_schedule': 30,
            'interview_complete': 75,
            'job_offer': 200,
            'referral_sent': 15,
            'referral_accepted': 50,
            'daily_login': 5,
            'weekly_goal': 100,
            'feedback_given': 10,
            'skill_added': 15,
            'certification_added': 25
        }
        
        return action_exp.get(action, 5)
    
    def _calculate_bonus_experience(self, context: Dict[str, Any]) -> int:
        """Calcula experiencia bonus basada en contexto"""
        try:
            bonus = 0
            
            if not context:
                return bonus
            
            # Bonus por racha
            if context.get('streak_days', 0) >= 7:
                bonus += 20
            elif context.get('streak_days', 0) >= 3:
                bonus += 10
            
            # Bonus por horario
            current_hour = timezone.now().hour
            if 9 <= current_hour <= 17:  # Horario laboral
                bonus += 5
            
            # Bonus por día de la semana
            current_weekday = timezone.now().weekday()
            if current_weekday < 5:  # Lunes a viernes
                bonus += 3
            
            return bonus
            
        except Exception as e:
            logger.error(f"❌ Error calculando bonus de experiencia: {e}")
            return 0
    
    async def _generate_level_reward(self, user_id: str, level: int) -> Reward:
        """Genera recompensa por subir de nivel"""
        try:
            template = self.reward_templates['level_up']
            
            # Calcular valor de la recompensa
            base_value = template['base_value']
            multiplier = template['multiplier']
            reward_value = int(base_value * (multiplier ** (level - 1)))
            
            reward = Reward(
                id=f"level_{level}_reward",
                type=template['type'],
                value=reward_value,
                description=f"¡Subiste al nivel {level}!",
                expires_at=timezone.now() + timedelta(days=30)
            )
            
            # Guardar recompensa
            await self._save_reward(user_id, reward)
            
            return reward
            
        except Exception as e:
            logger.error(f"❌ Error generando recompensa de nivel: {e}")
            return None
    
    async def _check_achievements(self, user_id: str, action: str, 
                                context: Dict[str, Any]) -> List[Achievement]:
        """Verifica si el usuario desbloqueó nuevos logros"""
        try:
            new_achievements = []
            user_stats = await self._get_user_stats(user_id)
            
            # Verificar logros basados en acción
            if action == 'profile_complete' and user_stats.get('profile_completion', 0) >= 100:
                achievement = await self._unlock_achievement(user_id, 'profile_complete')
                if achievement:
                    new_achievements.append(achievement)
            
            elif action == 'job_apply':
                applications_count = user_stats.get('applications_sent', 0)
                if applications_count == 1:
                    achievement = await self._unlock_achievement(user_id, 'first_application')
                    if achievement:
                        new_achievements.append(achievement)
                
                # Verificar racha de aplicaciones
                if context and context.get('weekly_applications', 0) >= 5:
                    achievement = await self._unlock_achievement(user_id, 'application_streak')
                    if achievement:
                        new_achievements.append(achievement)
            
            elif action == 'interview_complete':
                interviews_count = user_stats.get('interviews_completed', 0)
                if interviews_count == 1:
                    achievement = await self._unlock_achievement(user_id, 'first_interview')
                    if achievement:
                        new_achievements.append(achievement)
            
            elif action == 'job_offer':
                achievement = await self._unlock_achievement(user_id, 'job_offer')
                if achievement:
                    new_achievements.append(achievement)
            
            return new_achievements
            
        except Exception as e:
            logger.error(f"❌ Error verificando logros: {e}")
            return []
    
    async def _unlock_achievement(self, user_id: str, achievement_id: str) -> Optional[Achievement]:
        """Desbloquea un logro para el usuario"""
        try:
            # Verificar si ya está desbloqueado
            existing_achievements = await self._get_user_achievements(user_id)
            if any(a['id'] == achievement_id for a in existing_achievements):
                return None
            
            # Obtener configuración del logro
            achievement_config = self.achievements.get(achievement_id)
            if not achievement_config:
                return None
            
            # Crear logro
            achievement = Achievement(
                id=achievement_id,
                name=achievement_config['name'],
                description=achievement_config['description'],
                icon=achievement_config['icon'],
                points=achievement_config['points'],
                unlocked_at=timezone.now(),
                rarity=achievement_config['rarity']
            )
            
            # Guardar logro
            await self._save_achievement(user_id, achievement)
            
            # Otorgar puntos por logro
            await self.award_experience(user_id, 'achievement_unlock', 
                                      value=achievement.points)
            
            return achievement
            
        except Exception as e:
            logger.error(f"❌ Error desbloqueando logro: {e}")
            return None
    
    async def create_competition(self, name: str, description: str, 
                               duration_days: int = 7, rewards: List[Dict[str, Any]] = None) -> Competition:
        """
        Crea una nueva competencia
        """
        try:
            competition_id = f"comp_{int(timezone.now().timestamp())}"
            
            competition = Competition(
                id=competition_id,
                name=name,
                description=description,
                start_date=timezone.now(),
                end_date=timezone.now() + timedelta(days=duration_days),
                participants=[],
                leaderboard=[],
                rewards=rewards or []
            )
            
            # Guardar competencia
            self.active_competitions[competition_id] = competition
            
            self.metrics['active_competitions'] = len(self.active_competitions)
            
            logger.info(f"🏆 Nueva competencia creada: {name}")
            return competition
            
        except Exception as e:
            logger.error(f"❌ Error creando competencia: {e}")
            return None
    
    async def join_competition(self, user_id: str, competition_id: str) -> bool:
        """
        Une un usuario a una competencia
        """
        try:
            competition = self.active_competitions.get(competition_id)
            if not competition:
                return False
            
            if user_id not in competition.participants:
                competition.participants.append(user_id)
                competition.leaderboard.append({
                    'user_id': user_id,
                    'score': 0,
                    'joined_at': timezone.now().isoformat()
                })
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error uniendo usuario a competencia: {e}")
            return False
    
    async def update_competition_score(self, user_id: str, competition_id: str, 
                                     points: int) -> bool:
        """
        Actualiza puntuación de usuario en competencia
        """
        try:
            competition = self.active_competitions.get(competition_id)
            if not competition:
                return False
            
            # Buscar usuario en leaderboard
            for entry in competition.leaderboard:
                if entry['user_id'] == user_id:
                    entry['score'] += points
                    break
            
            # Ordenar leaderboard
            competition.leaderboard.sort(key=lambda x: x['score'], reverse=True)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error actualizando puntuación: {e}")
            return False
    
    async def get_leaderboard(self, competition_id: str) -> List[Dict[str, Any]]:
        """
        Obtiene leaderboard de una competencia
        """
        try:
            competition = self.active_competitions.get(competition_id)
            if not competition:
                return []
            
            return competition.leaderboard[:10]  # Top 10
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo leaderboard: {e}")
            return []
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas del sistema de gamificación"""
        try:
            return {
                'total_users': self.metrics['total_users'],
                'total_achievements': self.metrics['total_achievements'],
                'total_rewards': self.metrics['total_rewards'],
                'active_competitions': self.metrics['active_competitions'],
                'avg_user_level': round(self.metrics['avg_user_level'], 2),
                'last_updated': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo métricas: {e}")
            return {}
    
    # Métodos auxiliares para persistencia
    
    async def _get_user_data(self, user_id: str) -> Dict[str, Any]:
        """Obtiene datos del usuario"""
        try:
            # Simular datos (en producción, obtener de la base de datos)
            return {
                'experience': 1250,
                'level': 8,
                'achievements': ['first_profile', 'profile_complete'],
                'rewards': ['level_5_reward', 'achievement_badge'],
                'stats': {
                    'applications_sent': 15,
                    'interviews_completed': 3,
                    'profile_completion': 95
                }
            }
        except Exception as e:
            logger.error(f"❌ Error obteniendo datos del usuario: {e}")
            return {}
    
    async def _get_user_achievements(self, user_id: str) -> List[Dict[str, Any]]:
        """Obtiene logros del usuario"""
        try:
            # Simular logros (en producción, obtener de la base de datos)
            return [
                {
                    'id': 'first_profile',
                    'name': 'Primer Paso',
                    'description': 'Completa tu perfil por primera vez',
                    'icon': '👤',
                    'unlocked_at': '2024-01-15T10:30:00Z'
                }
            ]
        except Exception as e:
            logger.error(f"❌ Error obteniendo logros: {e}")
            return []
    
    async def _get_active_rewards(self, user_id: str) -> List[Dict[str, Any]]:
        """Obtiene recompensas activas del usuario"""
        try:
            # Simular recompensas (en producción, obtener de la base de datos)
            return [
                {
                    'id': 'level_5_reward',
                    'type': 'points',
                    'value': 100,
                    'description': '¡Subiste al nivel 5!',
                    'expires_at': '2024-02-15T10:30:00Z'
                }
            ]
        except Exception as e:
            logger.error(f"❌ Error obteniendo recompensas: {e}")
            return []
    
    async def _get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Obtiene estadísticas del usuario"""
        try:
            # Simular estadísticas (en producción, obtener de la base de datos)
            return {
                'applications_sent': 15,
                'interviews_completed': 3,
                'profile_completion': 95,
                'days_active': 45,
                'referrals_sent': 2,
                'referrals_accepted': 1
            }
        except Exception as e:
            logger.error(f"❌ Error obteniendo estadísticas: {e}")
            return {}
    
    async def _calculate_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Calcula estadísticas del usuario"""
        try:
            stats = await self._get_user_stats(user_id)
            
            # Calcular estadísticas adicionales
            stats['success_rate'] = (
                stats.get('interviews_completed', 0) / 
                max(stats.get('applications_sent', 1), 1) * 100
            )
            
            stats['activity_score'] = min(stats.get('days_active', 0) / 30 * 100, 100)
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Error calculando estadísticas: {e}")
            return {}
    
    async def _update_user_experience(self, user_id: str, experience: int):
        """Actualiza experiencia del usuario"""
        try:
            # En producción, actualizar en la base de datos
            logger.info(f"📈 Experiencia actualizada para usuario {user_id}: {experience}")
        except Exception as e:
            logger.error(f"❌ Error actualizando experiencia: {e}")
    
    async def _save_achievement(self, user_id: str, achievement: Achievement):
        """Guarda logro del usuario"""
        try:
            # En producción, guardar en la base de datos
            logger.info(f"🏆 Logro guardado: {achievement.name} para usuario {user_id}")
            self.metrics['total_achievements'] += 1
        except Exception as e:
            logger.error(f"❌ Error guardando logro: {e}")
    
    async def _save_reward(self, user_id: str, reward: Reward):
        """Guarda recompensa del usuario"""
        try:
            # En producción, guardar en la base de datos
            logger.info(f"🎁 Recompensa guardada: {reward.description} para usuario {user_id}")
            self.metrics['total_rewards'] += 1
        except Exception as e:
            logger.error(f"❌ Error guardando recompensa: {e}")

# Instancia global
advanced_gamification = AdvancedGamification() 