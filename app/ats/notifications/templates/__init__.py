"""Módulo de plantillas de notificaciones."""

from .base import BaseTemplate
from .proposal import ProposalTemplate
from .payment import PaymentTemplate
from .opportunity import OpportunityTemplate
from .interview import InterviewTemplate
from .collector import CollectorTemplate
from .fiscal import FiscalTemplate

__all__ = [
    'BaseTemplate',
    'ProposalTemplate',
    'PaymentTemplate',
    'OpportunityTemplate',
    'InterviewTemplate',
    'CollectorTemplate',
    'FiscalTemplate'
]
