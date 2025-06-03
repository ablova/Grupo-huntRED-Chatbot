"""
URL configuration for assessment-related endpoints.
"""

from django.urls import path
from app.ats.chatbot.views.assessment_views import (
    start_assessment,
    process_assessment_response,
    get_assessment_results
)

urlpatterns = [
    # Start a new assessment
    path('assessments/start/', start_assessment, name='start_assessment'),
    
    # Process user response to an assessment question
    path('assessments/respond/', process_assessment_response, name='process_assessment_response'),
    
    # Get assessment results
    path('assessments/results/<str:assessment_type>/<str:user_id>/', 
         get_assessment_results, name='get_assessment_results'),
]
