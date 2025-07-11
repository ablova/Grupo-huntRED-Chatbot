# app/ml/aura/networking/network_matchmaker.py
"""
AURA - Network Matchmaker Avanzado
Sugerencias de conexiones estratégicas usando GNN, personalización por segmento y unidad de negocio.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from app.ml.aura.graph_builder import GNNManager

logger = logging.getLogger(__name__)

class NetworkMatchmaker:
    """
    Motor avanzado de matchmaking de red:
    - Usa la GNN para sugerir conexiones estratégicas (mentores, aliados, oportunidades).
    - Personaliza sugerencias por segmento, objetivo y unidad de negocio.
    - Explica el valor de cada conexión sugerida.
    - Hooks para integración con notificaciones y gamificación.
    """
    def __init__(self):
        self.gnn = GNNManager()
        self.last_matches = {}

    def suggest_connections(self, user_id: str, goal: Optional[str] = None, business_unit: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Sugiere conexiones estratégicas para el usuario.
        Args:
            user_id: ID del usuario
            goal: objetivo actual (opcional)
            business_unit: contexto de unidad de negocio (opcional)
        Returns:
            lista de conexiones sugeridas con explicación
        """
        matches = self.gnn.suggest_connections(user_id, goal, business_unit)
        suggestions = []
        for match in matches:
            suggestions.append({
                'user_id': match['user_id'],
                'name': match['name'],
                'reason': match['reason'],
                'mutual_connections': match.get('mutual_connections', []),
                'potential_value': match.get('potential_value'),
                'explanation': match.get('explanation'),
            })
        self.last_matches[user_id] = suggestions
        logger.info(f"NetworkMatchmaker: sugerencias generadas para {user_id}.")
        return suggestions

# Ejemplo de uso:
# matchmaker = NetworkMatchmaker()
# result = matchmaker.suggest_connections('user_123', goal='mentoring', business_unit='huntRED')

network_matchmaker = NetworkMatchmaker() 