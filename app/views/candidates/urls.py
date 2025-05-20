from django.urls import path
from django.contrib.auth.decorators import login_required
from app.views.candidatos_views import (
    candidato_dashboard, list_candidatos, add_application,
    candidato_details, generate_challenges
)

urlpatterns = [
    path('', login_required(candidato_dashboard), name='candidato_dashboard'),
    path('list/', login_required(list_candidatos), name='list_candidatos'),
    path('add/', login_required(add_application), name='add_application'),
    path('<int:candidato_id>/', login_required(candidato_details), name='candidato_details'),
    path('generate_challenges/<int:user_id>/', login_required(generate_challenges), name='generate_challenges'),
] 