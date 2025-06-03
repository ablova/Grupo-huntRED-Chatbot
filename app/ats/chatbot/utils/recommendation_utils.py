# /home/pablo/app/com/chatbot/utils/recommendation_utils.py
"""
Utilidades para el sistema de recomendaciones.
"""
import logging
from typing import Dict, List, Optional, Any
from django.core.cache import cache
from django.conf import settings
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
logger = logging.getLogger(__name__)


class RecommendationUtils:
    """Utilidades para el sistema de recomendaciones."""

    # Constantes para recomendaciones
    MAX_RECOMMENDATIONS = 5
    MIN_SIMILARITY_THRESHOLD = 0.3
    CACHE_TIMEOUT = 3600  # 1 hora

    @staticmethod
    def get_user_preferences(user_id: str) -> Dict[str, Any]:
        """Obtiene las preferencias del usuario."""
        cache_key = f"user_preferences:{user_id}"
        return cache.get(cache_key, {})

    @staticmethod
    def update_user_preferences(user_id: str, preferences: Dict[str, Any]) -> None:
        """Actualiza las preferencias del usuario."""
        cache_key = f"user_preferences:{user_id}"
        current_preferences = cache.get(cache_key, {})
        current_preferences.update(preferences)
        cache.set(cache_key, current_preferences, timeout=RecommendationUtils.CACHE_TIMEOUT)

    @staticmethod
    def get_user_history(user_id: str) -> List[Dict[str, Any]]:
        """Obtiene el historial de interacciones del usuario."""
        cache_key = f"user_history:{user_id}"
        return cache.get(cache_key, [])

    @staticmethod
    def add_to_history(user_id: str, interaction: Dict[str, Any]) -> None:
        """Añade una interacción al historial del usuario."""
        cache_key = f"user_history:{user_id}"
        history = cache.get(cache_key, [])
        history.append(interaction)
        # Mantener solo las últimas 100 interacciones
        history = history[-100:]
        cache.set(cache_key, history, timeout=RecommendationUtils.CACHE_TIMEOUT)

    @staticmethod
    def calculate_similarity(text1: str, text2: str) -> float:
        """Calcula la similitud entre dos textos usando TF-IDF y similitud del coseno."""
        if not text1 or not text2:
            return 0.0

        try:
            vectorizer = TfidfVectorizer()
            tfidf_matrix = vectorizer.fit_transform([text1, text2])
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            return float(similarity)
        except Exception as e:
            logger.error(f"Error calculando similitud: {str(e)}")
            return 0.0

    @staticmethod
    def get_recommendations(user_id: str, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Obtiene recomendaciones personalizadas para el usuario."""
        if not items:
            return []

        # Obtener preferencias y historial del usuario
        preferences = RecommendationUtils.get_user_preferences(user_id)
        history = RecommendationUtils.get_user_history(user_id)

        # Calcular puntuaciones para cada item
        scored_items = []
        for item in items:
            score = RecommendationUtils._calculate_item_score(item, preferences, history)
            if score >= RecommendationUtils.MIN_SIMILARITY_THRESHOLD:
                scored_items.append((item, score))

        # Ordenar por puntuación
        scored_items.sort(key=lambda x: x[1], reverse=True)

        # Retornar los mejores items
        return [item for item, _ in scored_items[:RecommendationUtils.MAX_RECOMMENDATIONS]]

    @staticmethod
    def _calculate_item_score(item: Dict[str, Any], preferences: Dict[str, Any], history: List[Dict[str, Any]]) -> float:
        """Calcula la puntuación de un item basado en preferencias e historial."""
        score = 0.0

        # Calcular similitud con preferencias
        if preferences:
            preference_text = ' '.join(str(v) for v in preferences.values())
            item_text = ' '.join(str(v) for v in item.values())
            score += RecommendationUtils.calculate_similarity(preference_text, item_text)

        # Calcular similitud con historial
        if history:
            history_scores = []
            for interaction in history[-10:]:  # Usar solo las últimas 10 interacciones
                interaction_text = ' '.join(str(v) for v in interaction.values())
                item_text = ' '.join(str(v) for v in item.values())
                similarity = RecommendationUtils.calculate_similarity(interaction_text, item_text)
                history_scores.append(similarity)
            
            if history_scores:
                score += np.mean(history_scores)

        return score

    @staticmethod
    def get_popular_items(items: List[Dict[str, Any]], limit: int = 5) -> List[Dict[str, Any]]:
        """Obtiene los items más populares basado en interacciones."""
        if not items:
            return []

        # Contar interacciones por item
        item_counts = {}
        for item in items:
            item_id = item.get('id')
            if item_id:
                item_counts[item_id] = item_counts.get(item_id, 0) + 1

        # Ordenar items por popularidad
        sorted_items = sorted(
            items,
            key=lambda x: item_counts.get(x.get('id', ''), 0),
            reverse=True
        )

        return sorted_items[:limit]

    @staticmethod
    def get_similar_items(item: Dict[str, Any], items: List[Dict[str, Any]], limit: int = 5) -> List[Dict[str, Any]]:
        """Obtiene items similares al item dado."""
        if not item or not items:
            return []

        # Calcular similitud con cada item
        scored_items = []
        item_text = ' '.join(str(v) for v in item.values())
        
        for other_item in items:
            if other_item.get('id') != item.get('id'):
                other_text = ' '.join(str(v) for v in other_item.values())
                similarity = RecommendationUtils.calculate_similarity(item_text, other_text)
                if similarity >= RecommendationUtils.MIN_SIMILARITY_THRESHOLD:
                    scored_items.append((other_item, similarity))

        # Ordenar por similitud
        scored_items.sort(key=lambda x: x[1], reverse=True)

        return [item for item, _ in scored_items[:limit]] 