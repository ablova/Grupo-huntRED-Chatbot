"""
URLs para el dashboard de clientes.

Define las rutas para acceder al dashboard interactivo y sus APIs.
"""

from django.urls import path
from . import dashboard_views, dashboard_api

urlpatterns = [
    # Vistas del dashboard
    path('dashboard/client/', dashboard_views.ClientDashboardView.as_view(), name='client_dashboard'),
    path('dashboard/client/satisfaction/', dashboard_views.ClientSatisfactionDashboardView.as_view(), name='client_satisfaction_dashboard'),
    path('dashboard/client/onboarding/', dashboard_views.OnboardingMetricsDashboardView.as_view(), name='onboarding_metrics_dashboard'),
    path('dashboard/client/recommendations/', dashboard_views.RecommendationsDashboardView.as_view(), name='recommendations_dashboard'),
    
    # APIs para el dashboard
    path('api/dashboard/data/', dashboard_api.DashboardDataAPI.as_view(), name='dashboard_data_api'),
]
