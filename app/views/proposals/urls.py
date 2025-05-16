# /home/pablo/app/views/proposals/urls.py
#
# Configuración de URLs para el módulo. Define endpoints, vistas y patrones de URL.

from django.urls import path
from .views import ProposalViews
from .signature_views import ProposalSignatureView

urlpatterns = [
    # Vistas principales de propuestas
    path('proposals/', ProposalViews.as_view(), name='proposal_list'),
    path('proposals/generate/<int:opportunity_id>/', ProposalViews.as_view(), name='generate_proposal'),
    
    # Vistas de firma
    path('proposals/sign/<int:proposal_id>/', ProposalSignatureView.as_view(), name='proposal_sign'),
    path('proposals/sign/status/<int:proposal_id>/', ProposalSignatureView.as_view(), name='proposal_sign_status'),
]
