"""
URLs para el Sistema AURA

Configura las rutas para acceder a las APIs de AURA.
"""

from django.urls import path
from .api.endpoints import (
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

app_name = 'aura'

urlpatterns = [
    # Análisis de personas
    path('person/<int:person_id>/', get_person_aura, name='person_aura'),
    
    # Análisis de candidatos
    path('candidate/<int:candidate_id>/', get_candidate_aura, name='candidate_aura'),
    
    # Matches de trabajos
    path('job/<int:job_id>/matches/', get_job_aura_matches, name='job_matches'),
    
    # Insights de red
    path('network/<int:person_id>/insights/', get_network_insights, name='network_insights'),
    
    # Validación de experiencia
    path('validate-experience/', validate_experience, name='validate_experience'),
    
    # Análisis GNN
    path('gnn/<int:person_id>/analysis/', get_gnn_analysis, name='gnn_analysis'),
    
    # Detección de comunidades
    path('communities/<int:person_id>/', get_communities, name='communities'),
    
    # Análisis de influencia
    path('influence/<int:person_id>/', get_influence_analysis, name='influence_analysis'),
    
    # Sincronización de dashboard
    path('dashboard/<int:person_id>/sync/', sync_aura_dashboard, name='sync_dashboard'),
    
    # Métricas generales
    path('metrics/', get_aura_metrics, name='metrics'),
    
    # Estado de salud
    path('health/', get_aura_health, name='health'),
] 