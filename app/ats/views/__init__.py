"""Módulo de vistas."""

from .proposal_views import (
    ProposalListView,
    ProposalDetailView,
    ProposalCreateView,
    ProposalUpdateView
)
from .interview_views import (
    InterviewListView,
    InterviewDetailView,
    InterviewCreateView,
    InterviewUpdateView
)
from .offer_views import (
    OfferListView,
    OfferDetailView,
    OfferCreateView,
    OfferUpdateView
)
from .onboarding_views import (
    OnboardingListView,
    OnboardingDetailView,
    OnboardingCreateView,
    OnboardingUpdateView
)

__all__ = [
    'ProposalListView',
    'ProposalDetailView',
    'ProposalCreateView',
    'ProposalUpdateView',
    'InterviewListView',
    'InterviewDetailView',
    'InterviewCreateView',
    'InterviewUpdateView',
    'OfferListView',
    'OfferDetailView',
    'OfferCreateView',
    'OfferUpdateView',
    'OnboardingListView',
    'OnboardingDetailView',
    'OnboardingCreateView',
    'OnboardingUpdateView'
] 