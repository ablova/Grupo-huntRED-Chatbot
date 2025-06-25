from django.urls import path
from app.views.dashboard.consultant_views import (
    ConsultantDashboardView, ConsultantMetricsView, 
    ConsultantMarketInsightsView, ConsultantProductivityView,
    ConsultantCompetitorAnalysisView, ConsultantRecommendationsView,
    ConsultantRecentActivitiesView, ConsultantUpcomingTasksView,
    ConsultantAuraInsightsView, ConsultantAuraCandidateAnalysisView,  # Nuevas vistas de AURA
    ConsultantAuraVacancyAnalysisView
)

urlpatterns = [
    # Dashboard principal
    path('dashboard/<str:consultant_id>/', ConsultantDashboardView.as_view(), name='consultant_dashboard'),
    
    # Métricas y analytics
    path('metrics/<str:consultant_id>/', ConsultantMetricsView.as_view(), name='consultant_metrics'),
    path('market-insights/<str:consultant_id>/', ConsultantMarketInsightsView.as_view(), name='consultant_market_insights'),
    path('productivity/<str:consultant_id>/', ConsultantProductivityView.as_view(), name='consultant_productivity'),
    path('competitor-analysis/<str:consultant_id>/', ConsultantCompetitorAnalysisView.as_view(), name='consultant_competitor_analysis'),
    path('recommendations/<str:consultant_id>/', ConsultantRecommendationsView.as_view(), name='consultant_recommendations'),
    
    # Actividades y tareas
    path('recent-activities/<str:consultant_id>/', ConsultantRecentActivitiesView.as_view(), name='consultant_recent_activities'),
    path('upcoming-tasks/<str:consultant_id>/', ConsultantUpcomingTasksView.as_view(), name='consultant_upcoming_tasks'),
    
    # Vistas de AURA
    path('aura-insights/<str:consultant_id>/', ConsultantAuraInsightsView.as_view(), name='consultant_aura_insights'),
    path('aura-candidate-analysis/<str:consultant_id>/<str:candidate_id>/', ConsultantAuraCandidateAnalysisView.as_view(), name='consultant_aura_candidate_analysis'),
    path('aura-vacancy-analysis/<str:consultant_id>/<str:vacancy_id>/', ConsultantAuraVacancyAnalysisView.as_view(), name='consultant_aura_vacancy_analysis'),
] 