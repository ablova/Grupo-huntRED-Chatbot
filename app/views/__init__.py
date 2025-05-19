# /Users/pablollh/MEGA/GitHub/Grupo-huntRED-Chatbot/app/views/__init__.py
#
# Vista para el módulo. Implementa la lógica de presentación y manejo de peticiones HTTP.

# ATS
from app.views.ats.views import ATSViews

# Vistas del chatbot
from app.views.chatbot.views import ChatbotViews

# Vistas de propuestas
from app.views.proposals.views import ProposalViews

# Utilidades y decoradores
from app.views.utils.decorators import (
    login_required_json,
    chatbot_permission_required,
    role_required,
    bu_required,
    verify_token
)

# Vistas principales
from app.views.main_views import MainViews
