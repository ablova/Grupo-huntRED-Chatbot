"""Módulos de modelos para el sistema ATS."""

# Core models
from .core.business_unit import BusinessUnit
from .core.company import Company
from .core.contact import Contact
from .core.person import Person

# ATS models
from .ats.application import Application
from .ats.interview import Interview
from .ats.vacancy import Vacancy
from .ats.assessment import Assessment

# Proposal models
from .proposal.proposal import Proposal
from .proposal.offer import Offer
from .proposal.onboarding import Onboarding

# Pricing models
from .pricing.pricing_baseline import PricingBaseline
from .pricing.addon import Addon
from .pricing.coupon import Coupon
from .pricing.payment_milestone import PaymentMilestone

# Analytics models
from .analytics.opportunity import Opportunity
from .analytics.contract import Contract
from .analytics.analytics import Analytics

__all__ = [
    # Core
    'BusinessUnit', 'Company', 'Contact', 'Person',
    
    # ATS
    'Application', 'Interview', 'Vacancy', 'Assessment',
    
    # Proposal
    'Proposal', 'Offer', 'Onboarding',
    
    # Pricing
    'PricingBaseline', 'Addon', 'Coupon', 'PaymentMilestone',
    
    # Analytics
    'Opportunity', 'Contract', 'Analytics'
] 