"""
AURA - CV Generator Avanzado
Generación automática de CVs y perfiles usando GNN, personalización y explicabilidad.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional
from app.ml.aura.graph_builder import GNNManager

logger = logging.getLogger(__name__)

class CVGenerator:
    """
    Motor avanzado de generación de CVs y perfiles:
    - Usa la GNN para generar CVs personalizados y explicables.
    - Integra skills, logros, trayectorias y contexto de red.
    - Hooks para integración con dashboards y exportación.
    """
    def __init__(self):
        self.gnn = GNNManager()
        self.last_cvs = {}

    def generate(self, user_id: str, business_unit: Optional[str] = None) -> Dict[str, Any]:
        """
        Genera un CV personalizado para el usuario.
        Args:
            user_id: ID del usuario
            business_unit: contexto de unidad de negocio (opcional)
        Returns:
            dict con CV generado
        """
        cv = self.gnn.generate_cv(user_id, business_unit)
        self.last_cvs[user_id] = cv
        logger.info(f"CVGenerator: CV generado para {user_id}.")
        return {'user_id': user_id, 'cv': cv, 'timestamp': datetime.now().isoformat()}

# Ejemplo de uso:
# generator = CVGenerator()
# result = generator.generate('user_123', business_unit='huntRED') 