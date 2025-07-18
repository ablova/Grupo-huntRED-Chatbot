# /home/pablo/app/com/proposals/urls.py
#
# Configuración de URLs para el módulo. Define endpoints, vistas y patrones de URL.

from django.urls import path
from app.ats.views.proposals import ProposalView

urlpatterns = [
    path('', ProposalView.as_view().proposal_list, name='proposal_list'),
    path('generate/<int:opportunity_id>/', ProposalView.as_view().generate_proposal, name='generate_proposal'),
    path('convert/<int:proposal_id>/', ProposalView.as_view().convert_to_contract, name='convert_to_contract'),
]
