"""
AURA - Auto Summarizer Avanzado
Resúmenes automáticos de actividad, reuniones y eventos usando GNN y contexto de usuario.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from app.ml.aura.graph_builder import GNNManager

logger = logging.getLogger(__name__)

class AutoSummarizer:
    """
    Motor avanzado de resúmenes automáticos:
    - Usa la GNN para resumir actividad, reuniones y eventos relevantes.
    - Personaliza el resumen según contexto, logros y objetivos.
    - Hooks para integración con dashboards y notificaciones.
    """
    def __init__(self):
        self.gnn = GNNManager()
        self.last_summaries = {}

    def summarize(self, user_id: str, activities: List[Dict[str, Any]], business_unit: Optional[str] = None) -> Dict[str, Any]:
        """
        Resume actividad, reuniones y eventos del usuario.
        Args:
            user_id: ID del usuario
            activities: lista de actividades/eventos
            business_unit: contexto de unidad de negocio (opcional)
        Returns:
            dict con resumen generado
        """
        summary = self.gnn.summarize_activity(user_id, activities, business_unit)
        self.last_summaries[user_id] = summary
        logger.info(f"AutoSummarizer: resumen generado para {user_id}.")
        return {'user_id': user_id, 'summary': summary, 'timestamp': datetime.now().isoformat()}

# Ejemplo de uso:
# summarizer = AutoSummarizer()
# result = summarizer.summarize('user_123', activities, business_unit='huntRED') 