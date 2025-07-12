# app/views/candidates/urls.py 
# - URLs para el módulo de candidatos.
# Optimización: Diseño modular para URLs de candidatos.
# Mejora: Diseño dinámico con herencia de clases para URLs de candidatos, manteniendo nombres como 'candidato_dashboard'.
# Type hints y comentarios para mejores prácticas.

from typing import Dict, Any, List  # Type hints para legibilidad y errores tempranos.
from django.urls import path  # Importación de path para URLs.
from django.contrib.auth.decorators import login_required  # Importación de login_required para decoradores.

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