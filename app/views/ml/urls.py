from django.urls import path
from django.contrib.auth.decorators import login_required
from app.views.ml_views import train_ml_api, predict_matches
from app.ats.views.ml_admin_views import (
    MLDashboardView, vacancy_analysis_view,
    candidate_growth_plan_view, candidate_growth_plan_pdf_view,
    dashboard_charts_api_view
)

urlpatterns = [
    # Rutas de predicción y entrenamiento
    path('predict_matches/<int:user_id>/', 
         login_required(predict_matches), 
         name='predict_matches'),
    path('train_model/', 
         login_required(train_ml_api), 
         name='train_model'),
    
    # Rutas del dashboard de ML
    path('dashboard/', 
         login_required(MLDashboardView.as_view()), 
         name='ml_dashboard'),
    path('vacancy_analysis/', 
         login_required(vacancy_analysis_view), 
         name='vacancy_analysis'),
    path('growth_plan/', 
         login_required(candidate_growth_plan_view), 
         name='growth_plan'),
    path('growth_plan/pdf/', 
         login_required(candidate_growth_plan_pdf_view), 
         name='growth_plan_pdf'),
    path('dashboard/charts/', 
         login_required(dashboard_charts_api_view), 
         name='dashboard_charts'),
] 