# /home/pablo/app/views/proposals/urls.py
#
# Configuración de URLs para el módulo. Define endpoints, vistas y patrones de URL.

from django.urls import path
from app.ats.views.proposals.views import ProposalViews
from app.ats.views.proposals.signature_views import ProposalSignatureView
from . import views

app_name = 'proposals'

urlpatterns = [
    # Vistas principales de propuestas
    path('proposals/', ProposalViews.as_view(), name='proposal_list'),
    path('proposals/generate/<int:opportunity_id>/', ProposalViews.as_view(), name='generate_proposal'),
    
    # Vistas de firma
    path('proposals/sign/<int:proposal_id>/', ProposalSignatureView.as_view(), name='proposal_sign'),
    path('proposals/sign/status/<int:proposal_id>/', ProposalSignatureView.as_view(), name='proposal_sign_status'),
    
    # URLs para edición inline ultra mejorada
    path('client/<int:client_id>/update-info/', views.update_client_info, name='update_client_info'),
    path('company/<int:company_id>/update-contacts/', views.update_company_contacts, name='update_company_contacts'),
    path('company/<int:company_id>/add-invitee/', views.add_invitee, name='add_invitee'),
    path('company/<int:company_id>/remove-invitee/', views.remove_invitee, name='remove_invitee'),
]
