"""Configuración de URLs."""

from django.urls import path, include
from .views import (
    ProposalListView,
    ProposalDetailView,
    ProposalCreateView,
    ProposalUpdateView,
    InterviewListView,
    InterviewDetailView,
    InterviewCreateView,
    InterviewUpdateView,
    OfferListView,
    OfferDetailView,
    OfferCreateView,
    OfferUpdateView,
    OnboardingListView,
    OnboardingDetailView,
    OnboardingCreateView,
    OnboardingUpdateView
)

app_name = 'ats'

urlpatterns = [
    # Propuestas
    path('proposals/', ProposalListView.as_view(), name='proposal_list'),
    path('proposals/<uuid:pk>/', ProposalDetailView.as_view(), name='proposal_detail'),
    path('proposals/create/', ProposalCreateView.as_view(), name='proposal_create'),
    path('proposals/<uuid:pk>/update/', ProposalUpdateView.as_view(), name='proposal_update'),
    
    # Entrevistas
    path('interviews/', InterviewListView.as_view(), name='interview_list'),
    path('interviews/<uuid:pk>/', InterviewDetailView.as_view(), name='interview_detail'),
    path('interviews/create/', InterviewCreateView.as_view(), name='interview_create'),
    path('interviews/<uuid:pk>/update/', InterviewUpdateView.as_view(), name='interview_update'),
    
    # Ofertas
    path('offers/', OfferListView.as_view(), name='offer_list'),
    path('offers/<uuid:pk>/', OfferDetailView.as_view(), name='offer_detail'),
    path('offers/create/', OfferCreateView.as_view(), name='offer_create'),
    path('offers/<uuid:pk>/update/', OfferUpdateView.as_view(), name='offer_update'),
    
    # Onboarding
    path('onboarding/', OnboardingListView.as_view(), name='onboarding_list'),
    path('onboarding/<uuid:pk>/', OnboardingDetailView.as_view(), name='onboarding_detail'),
    path('onboarding/create/', OnboardingCreateView.as_view(), name='onboarding_create'),
    path('onboarding/<uuid:pk>/update/', OnboardingUpdateView.as_view(), name='onboarding_update'),
]

"""
URLs para el Sistema ATS con integración de AURA

Configura las rutas para acceder a las funcionalidades de AURA
desde el dashboard de huntRED.
"""

from django.urls import path
from app.ats.views.aura_views import (
    aura_dashboard,
    person_aura_view,
    candidate_aura_view,
    job_aura_matches_view,
    network_insights_view,
    aura_communities_view,
    aura_influencers_view,
    validate_experience_view,
    aura_settings_view
)

app_name = 'ats'

urlpatterns += [
    # 🌟 AURA - SISTEMA DE INTELIGENCIA RELACIONAL
    path('aura/', aura_dashboard, name='aura_dashboard'),
    path('aura/person/<int:person_id>/', person_aura_view, name='person_aura'),
    path('aura/candidate/<int:candidate_id>/', candidate_aura_view, name='candidate_aura'),
    path('aura/job/<int:job_id>/matches/', job_aura_matches_view, name='job_aura_matches'),
    path('aura/network/<int:person_id>/insights/', network_insights_view, name='network_insights'),
    path('aura/communities/', aura_communities_view, name='aura_communities'),
    path('aura/influencers/', aura_influencers_view, name='aura_influencers'),
    path('aura/validate-experience/', validate_experience_view, name='validate_experience'),
    path('aura/settings/', aura_settings_view, name='aura_settings'),
] 