# app/ml/aura/api/__init__.py
"""
API de AURA - Inicializador del paquete
"""

# Importar y exponer los endpoints como AuraAPIEndpoints
from app.ml.aura.api.endpoints import (
    get_person_aura,
    get_candidate_aura,
    get_job_aura_matches,
    get_network_insights,
    validate_experience,
    get_gnn_analysis,
    get_communities,
    get_influence_analysis,
    sync_aura_dashboard,
    get_aura_metrics,
    get_aura_health
)

# Crear un alias para la clase AuraAPIEndpoints
class AuraAPIEndpoints:
    """Clase contenedora para los endpoints de la API de AURA"""
    get_person_aura = get_person_aura
    get_candidate_aura = get_candidate_aura
    get_job_aura_matches = get_job_aura_matches
    get_network_insights = get_network_insights
    validate_experience = validate_experience
    get_gnn_analysis = get_gnn_analysis
    get_communities = get_communities
    get_influence_analysis = get_influence_analysis
    sync_aura_dashboard = sync_aura_dashboard
    get_aura_metrics = get_aura_metrics
    get_aura_health = get_aura_health

# Exportar la clase para que esté disponible al importar desde app.ml.aura.api
__all__ = ['AuraAPIEndpoints']
