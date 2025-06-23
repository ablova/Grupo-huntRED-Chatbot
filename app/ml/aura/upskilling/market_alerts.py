"""
AURA - Market Alerts Avanzado
Alertas predictivas de tendencias y oportunidades personalizadas usando GNN y análisis de mercado.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from app.ml.aura.graph_builder import GNNManager

logger = logging.getLogger(__name__)

class MarketAlerts:
    """
    Motor avanzado de alertas de mercado:
    - Analiza tendencias emergentes y oportunidades relevantes para el usuario.
    - Cruza datos de la GNN, skills y red para personalizar la relevancia.
    - Integra con el orquestador para notificaciones omnicanal.
    """
    def __init__(self):
        self.gnn = GNNManager()
        self.last_alerts = {}

    def get_alerts(self, user_id: str, business_unit: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Genera alertas de mercado personalizadas para el usuario.
        Args:
            user_id: ID del usuario
            business_unit: contexto de unidad de negocio (opcional)
        Returns:
            lista de alertas relevantes
        """
        user_profile = self.gnn.get_user_profile(user_id)
        trends = self.gnn.get_market_trends(business_unit)
        alerts = []
        for trend in trends:
            if self.gnn.is_trend_relevant(user_profile, trend):
                alerts.append({
                    'trend': trend['name'],
                    'description': trend['description'],
                    'relevance': trend['relevance_score'],
                    'action': trend.get('suggested_action'),
                    'explanation': f"Relevante por tu perfil y red en {business_unit or 'el mercado global'}"
                })
        self.last_alerts[user_id] = alerts
        logger.info(f"MarketAlerts: alertas generadas para {user_id}.")
        return alerts

# Ejemplo de uso:
# alerts = MarketAlerts()
# result = alerts.get_alerts('user_123') 