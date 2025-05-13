# /home/pablo/app/views/__init__.py
#
# Vista para el módulo. Implementa la lógica de presentación y manejo de peticiones HTTP.

# ATS
from .ats.views import ATSViews

# Chatbot
from .chatbot.views import ChatbotViews

# Propuestas y Contratos
from .proposals.views import ProposalViews

# Utilidades
from .utils.decorators import (
    login_required,
    bu_complete_required,
    bu_division_required,
    permission_required,
    verified_user_required
)

# Vistas principales
from .main_views import MainViews
