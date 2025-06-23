"""
AURA - Event Recommender Avanzado
Recomendación de eventos y grupos relevantes usando GNN, personalización por intereses, industria y unidad de negocio.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from app.ml.aura.graph_builder import GNNManager

logger = logging.getLogger(__name__)

class EventRecommender:
    """
    Motor avanzado de recomendación de eventos y grupos:
    - Usa la GNN para identificar eventos y grupos relevantes para el usuario.
    - Personaliza sugerencias por intereses, industria y unidad de negocio.
    - Explica el valor de cada evento sugerido.
    - Hooks para integración con notificaciones y gamificación.
    """
    def __init__(self):
        self.gnn = GNNManager()
        self.last_recommendations = {}

    def recommend(self, user_id: str, interests: Optional[List[str]] = None, industry: Optional[str] = None, business_unit: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Recomienda eventos y grupos relevantes para el usuario.
        Args:
            user_id: ID del usuario
            interests: lista de intereses (opcional)
            industry: industria del usuario (opcional)
            business_unit: contexto de unidad de negocio (opcional)
        Returns:
            lista de eventos/grupos sugeridos con explicación
        """
        events = self.gnn.recommend_events(user_id, interests, industry, business_unit)
        recommendations = []
        for event in events:
            recommendations.append({
                'event_id': event['event_id'],
                'name': event['name'],
                'date': event.get('date'),
                'location': event.get('location'),
                'reason': event.get('reason'),
                'explanation': event.get('explanation'),
            })
        self.last_recommendations[user_id] = recommendations
        logger.info(f"EventRecommender: recomendaciones generadas para {user_id}.")
        return recommendations

# Ejemplo de uso:
# recommender = EventRecommender()
# result = recommender.recommend('user_123', interests=['AI', 'Networking'], industry='Tech', business_unit='huntRED') 