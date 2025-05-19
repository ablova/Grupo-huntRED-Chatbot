"""
URLs para la gestión de dashboards compartidos.

Define las rutas para administrar, compartir y acceder a los dashboards de cliente.
"""

from django.urls import path
from app.com.onboarding.dashboard_share import (
    DashboardShareView, 
    SharedDashboardView, 
    regenerate_token,
    extend_expiry,
    share_stats
)

urlpatterns = [
    # Gestión de enlaces compartidos (requiere login)
    path('dashboard/client/share/', DashboardShareView.as_view(), name='manage_dashboard_shares'),
    path('dashboard/client/share/<int:share_id>/', DashboardShareView.as_view(), name='delete_dashboard_share'),
    path('dashboard/client/share/<int:share_id>/regenerate/', regenerate_token, name='regenerate_token'),
    path('dashboard/client/share/<int:share_id>/extend/', extend_expiry, name='extend_expiry'),
    path('dashboard/client/share/<int:share_id>/stats/', share_stats, name='share_stats'),
    
    # Acceso público a dashboards compartidos (no requiere login)
    path('dashboard/client/share/<str:token>/', SharedDashboardView.as_view(), name='shared_dashboard'),
]
