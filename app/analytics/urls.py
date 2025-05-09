from django.urls import path
from app.views.analytics import AnalyticsDashboardView

urlpatterns = [
    path('dashboard/', AnalyticsDashboardView.as_view(), name='analytics_dashboard'),
    path('predict-conversion/', AnalyticsDashboardView.as_view(), name='predict_conversion'),
]
