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