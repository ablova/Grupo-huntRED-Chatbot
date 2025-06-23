"""
AURA - Impact Ranking Avanzado
Ranking de impacto social/profesional usando GNN, integración con dashboards y gamificación.
"""

import logging
from typing import List, Dict, Any, Optional
from app.ml.aura.graph_builder import GNNManager

logger = logging.getLogger(__name__)

class ImpactRanking:
    """
    Motor avanzado de ranking de impacto:
    - Calcula el ranking de impacto social/profesional usando la GNN.
    - Integra con dashboards y sistemas de gamificación.
    - Personalización por unidad de negocio.
    """
    def __init__(self):
        self.gnn = GNNManager()
        self.last_ranking = None

    def get(self, business_unit: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Devuelve el ranking de impacto social/profesional.
        Args:
            business_unit: contexto de unidad de negocio (opcional)
        Returns:
            lista de usuarios ordenados por impacto
        """
        ranking = self.gnn.get_impact_ranking(business_unit)
        self.last_ranking = ranking
        logger.info(f"ImpactRanking: ranking generado para {business_unit or 'global'}.")
        return ranking

# Ejemplo de uso:
# ranking = ImpactRanking()
# result = ranking.get(business_unit='huntRED') 