# /home/pablo/app/analytics/urls.py
#
# Configuración de URLs para el módulo. Define endpoints, vistas y patrones de URL.

from django.urls import path
from app.ats.views.analytics import AnalyticsDashboardView

urlpatterns = [
    path('dashboard/', AnalyticsDashboardView.as_view(), name='analytics_dashboard'),
    path('predict-conversion/', AnalyticsDashboardView.as_view(), name='predict_conversion'),
]
