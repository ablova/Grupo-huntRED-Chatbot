"""
AURA - Organizational Analytics Avanzado
Análisis de red organizacional, benchmarking, movilidad interna usando GNN, integración con dashboards y reporting.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from app.ml.aura.graph_builder import GNNManager

logger = logging.getLogger(__name__)

@dataclass
class OrgNetworkNode:
    """Nodo de la red organizacional"""
    user_id: str
    name: str
    department: str
    position: str
    influence_score: float
    skills: List[str]
    connections: List[str] = field(default_factory=list)

@dataclass
class OrgNetworkEdge:
    """Arista de la red organizacional"""
    from_user: str
    to_user: str
    interaction_strength: float
    collaboration_score: float
    last_interaction: Optional[datetime] = None

@dataclass
class OrgAnalyticsReport:
    """Reporte ejecutivo de análisis organizacional"""
    generated_at: datetime
    summary: str
    key_findings: List[str]
    recommendations: List[str]
    network_metrics: Dict[str, Any]
    visualizations: Dict[str, Any]

class OrganizationalAnalytics:
    """
    Motor avanzado de análisis organizacional:
    - Analiza la red organizacional, detecta silos, influencers y oportunidades de colaboración.
    - Benchmarking de talento y skills frente al mercado usando la GNN.
    - Sugerencias de formación y movilidad interna.
    - Hooks para dashboards y reporting.
    """
    def __init__(self):
        self.gnn = GNNManager()
        self.last_analysis = None
        self.org_network = {}
        self.org_edges = []
        self.reports = []

    def analyze(self, org_id: str, business_unit: Optional[str] = None) -> Dict[str, Any]:
        """
        Analiza la red organizacional y genera insights clave.
        Args:
            org_id: ID de la organización
            business_unit: contexto de unidad de negocio (opcional)
        Returns:
            dict con silos, influencers, oportunidades y benchmarking
        """
        analysis = self.gnn.analyze_organization(org_id, business_unit)
        self.last_analysis = analysis
        logger.info(f"OrganizationalAnalytics: análisis generado para {org_id}.")
        return analysis

    def recommend_training(self, org_id: str, business_unit: Optional[str] = None) -> Dict[str, Any]:
        """
        Recomienda formación y movilidad interna.
        """
        recommendations = self.gnn.recommend_training(org_id, business_unit)
        logger.info(f"OrganizationalAnalytics: formación recomendada para {org_id}.")
        return recommendations

    def benchmark(self, org_id: str, business_unit: Optional[str] = None) -> Dict[str, Any]:
        """
        Benchmarking de talento y skills frente al mercado.
        """
        benchmark = self.gnn.benchmark_organization(org_id, business_unit)
        logger.info(f"OrganizationalAnalytics: benchmarking generado para {org_id}.")
        return benchmark

    def build_org_network(self, user_data: List[Dict[str, Any]], interactions: List[Dict[str, Any]]):
        """Construye la red organizacional a partir de datos de usuarios e interacciones"""
        # Aquí se integraría con la GNN para construir la red
        logger.info("OrganizationalAnalytics: red organizacional construida.")

    def detect_silos_and_influencers(self) -> Dict[str, Any]:
        """Detecta silos y usuarios clave en la organización"""
        silos = self.gnn.detect_silos()
        influencers = self.gnn.detect_influencers()
        return {'silos': silos, 'influencers': influencers}

    def suggest_internal_mobility(self) -> List[Dict[str, Any]]:
        """Sugiere movimientos internos y oportunidades de desarrollo"""
        mobility = self.gnn.suggest_mobility()
        return mobility

    def generate_report(self) -> OrgAnalyticsReport:
        """Genera un reporte ejecutivo de la red organizacional"""
        report = OrgAnalyticsReport(
            generated_at=datetime.now(),
            summary="Análisis completo de la red organizacional",
            key_findings=["Silos detectados", "Influencers identificados", "Oportunidades de colaboración"],
            recommendations=["Formación recomendada", "Movilidad interna sugerida"],
            network_metrics=self.gnn.get_network_metrics(),
            visualizations=self.gnn.get_visualizations()
        )
        self.reports.append(report)
        return report

# Ejemplo de uso:
# org_analytics = OrganizationalAnalytics()
# result = org_analytics.analyze('org_123', business_unit='huntRED')
# report = org_analytics.generate_report() 