# /home/pablo/app/com/chatbot/utils/gamification_utils.py
"""
Utilidades para gamificación del chatbot.
"""
import logging
from typing import Dict, List, Optional, Any
from django.core.cache import cache
from django.conf import settings
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class GamificationUtils:
    """Utilidades para gamificación del chatbot."""

    # Constantes para gamificación
    POINTS_PER_MESSAGE = 1
    POINTS_PER_CORRECT_ANSWER = 5
    POINTS_PER_COMPLETED_TASK = 10
    DAILY_POINTS_LIMIT = 100
    LEVEL_UP_THRESHOLD = 1000  # Puntos necesarios para subir de nivel

    @staticmethod
    def get_user_points(user_id: str) -> int:
        """Obtiene los puntos actuales del usuario."""
        cache_key = f"user_points:{user_id}"
        return cache.get(cache_key, 0)

    @staticmethod
    def add_points(user_id: str, points: int) -> int:
        """Añade puntos al usuario respetando el límite diario."""
        if points <= 0:
            return GamificationUtils.get_user_points(user_id)

        cache_key = f"user_points:{user_id}"
        daily_key = f"daily_points:{user_id}:{datetime.now().date()}"

        # Obtener puntos diarios actuales
        daily_points = cache.get(daily_key, 0)
        if daily_points >= GamificationUtils.DAILY_POINTS_LIMIT:
            return GamificationUtils.get_user_points(user_id)

        # Calcular puntos a añadir respetando el límite diario
        points_to_add = min(
            points,
            GamificationUtils.DAILY_POINTS_LIMIT - daily_points
        )

        # Actualizar puntos totales y diarios
        current_points = cache.get(cache_key, 0)
        new_points = current_points + points_to_add
        cache.set(cache_key, new_points)
        cache.set(daily_key, daily_points + points_to_add, timeout=86400)  # 24 horas

        return new_points

    @staticmethod
    def get_user_level(user_id: str) -> int:
        """Calcula el nivel actual del usuario basado en sus puntos."""
        points = GamificationUtils.get_user_points(user_id)
        return (points // GamificationUtils.LEVEL_UP_THRESHOLD) + 1

    @staticmethod
    def get_level_progress(user_id: str) -> Dict[str, Any]:
        """Obtiene el progreso del usuario hacia el siguiente nivel."""
        points = GamificationUtils.get_user_points(user_id)
        current_level = GamificationUtils.get_user_level(user_id)
        points_for_next_level = current_level * GamificationUtils.LEVEL_UP_THRESHOLD
        points_in_current_level = points % GamificationUtils.LEVEL_UP_THRESHOLD
        progress_percentage = (points_in_current_level / GamificationUtils.LEVEL_UP_THRESHOLD) * 100

        return {
            'current_level': current_level,
            'points': points,
            'points_for_next_level': points_for_next_level,
            'points_in_current_level': points_in_current_level,
            'progress_percentage': progress_percentage,
            'points_needed': points_for_next_level - points
        }

    @staticmethod
    def get_achievements(user_id: str) -> List[Dict[str, Any]]:
        """Obtiene los logros del usuario."""
        cache_key = f"user_achievements:{user_id}"
        return cache.get(cache_key, [])

    @staticmethod
    def add_achievement(user_id: str, achievement: Dict[str, Any]) -> None:
        """Añade un logro al usuario."""
        cache_key = f"user_achievements:{user_id}"
        achievements = cache.get(cache_key, [])
        
        # Verificar si el logro ya existe
        if not any(a['id'] == achievement['id'] for a in achievements):
            achievements.append(achievement)
            cache.set(cache_key, achievements)

    @staticmethod
    def get_leaderboard(limit: int = 10) -> List[Dict[str, Any]]:
        """Obtiene el ranking de usuarios."""
        cache_key = "global_leaderboard"
        leaderboard = cache.get(cache_key, [])
        
        if not leaderboard:
            # Aquí deberías obtener los datos de tu base de datos
            # Por ahora retornamos una lista vacía
            return []
        
        return leaderboard[:limit]

    @staticmethod
    def update_leaderboard(user_id: str, points: int) -> None:
        """Actualiza el ranking global."""
        cache_key = "global_leaderboard"
        leaderboard = cache.get(cache_key, [])
        
        # Actualizar o añadir usuario al ranking
        user_entry = next((entry for entry in leaderboard if entry['user_id'] == user_id), None)
        if user_entry:
            user_entry['points'] = points
        else:
            leaderboard.append({
                'user_id': user_id,
                'points': points,
                'level': GamificationUtils.get_user_level(user_id)
            })
        
        # Ordenar por puntos
        leaderboard.sort(key=lambda x: x['points'], reverse=True)
        
        # Mantener solo los top 100
        cache.set(cache_key, leaderboard[:100])

    @staticmethod
    def get_daily_challenges() -> List[Dict[str, Any]]:
        """Obtiene los desafíos diarios disponibles."""
        cache_key = f"daily_challenges:{datetime.now().date()}"
        challenges = cache.get(cache_key)
        
        if not challenges:
            # Aquí deberías obtener los desafíos de tu base de datos
            # Por ahora retornamos una lista vacía
            return []
        
        return challenges

    @staticmethod
    def complete_challenge(user_id: str, challenge_id: str) -> bool:
        """Marca un desafío como completado y otorga puntos."""
        cache_key = f"completed_challenges:{user_id}:{datetime.now().date()}"
        completed = cache.get(cache_key, [])
        
        if challenge_id in completed:
            return False
        
        # Obtener el desafío
        challenges = GamificationUtils.get_daily_challenges()
        challenge = next((c for c in challenges if c['id'] == challenge_id), None)
        
        if not challenge:
            return False
        
        # Marcar como completado y otorgar puntos
        completed.append(challenge_id)
        cache.set(cache_key, completed, timeout=86400)  # 24 horas
        
        GamificationUtils.add_points(user_id, challenge['points'])
        
        return True 