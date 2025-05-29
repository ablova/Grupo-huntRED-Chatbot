# /home/pablo/app/com/chatbot/workflow/assessments/succession_planning/urls.py
from django.urls import path
from . import views

app_name = 'succession_planning'

urlpatterns = [
    # Lista de planes de sucesión
    path('plans/', views.SuccessionPlanListView.as_view(), name='plan_list'),
    
    # Detalles de un plan de sucesión
    path('plans/<int:pk>/', views.SuccessionPlanDetailView.as_view(), name='plan_detail'),
    
    # Crear un nuevo plan de sucesión
    path('plans/create/', views.SuccessionPlanCreateView.as_view(), name='plan_create'),
    
    # Actualizar un plan de sucesión
    path('plans/<int:pk>/update/', views.SuccessionPlanUpdateView.as_view(), name='plan_update'),
    
    # Eliminar un plan de sucesión
    path('plans/<int:pk>/delete/', views.SuccessionPlanDeleteView.as_view(), name='plan_delete'),
    
    # Añadir candidato a un plan
    path('plans/<int:plan_id>/add-candidate/', views.add_candidate_to_plan, name='add_candidate'),
    
    # Eliminar candidato de un plan
    path('candidates/<int:pk>/remove/', views.remove_candidate_from_plan, name='remove_candidate'),
    
    # Realizar evaluación de preparación
    path('candidates/<int:candidate_id>/assess/', views.assess_candidate_readiness, name='assess_candidate'),
    
    # Ver historial de evaluaciones
    path('candidates/<int:pk>/assessments/', views.CandidateAssessmentsView.as_view(), name='candidate_assessments'),
    
    # API para obtener datos de candidatos (AJAX)
    path('api/candidates/search/', views.search_candidates, name='search_candidates'),
    
    # API para obtener datos de posiciones (AJAX)
    path('api/positions/search/', views.search_positions, name='search_positions'),
    
    # Dashboard de sucesión
    path('dashboard/', views.SuccessionDashboardView.as_view(), name='dashboard'),
    
    # Reportes
    path('reports/readiness/', views.ReadinessReportView.as_view(), name='readiness_report'),
    path('reports/gaps/', views.GapAnalysisReportView.as_view(), name='gap_analysis_report'),
]
