"""Re-exportación de modelos desde app.models.

Este archivo existe solo para mantener compatibilidad con código existente.
Todas las referencias nuevas deben importar directamente desde app.models.
"""

from app.models import (
    BusinessUnit,
    BusinessUnitMembership,
    Company,
    Person,
    Application,
    Interview,
    Vacancy,
    Proposal,
    Opportunity,
    Contract,
    Coupon,
    PricingBaseline,
    PaymentMilestone
)

__all__ = [
    'BusinessUnit',
    'BusinessUnitMembership',
    'Company',
    'Person',
    'Application',
    'Interview',
    'Vacancy',
    'Proposal',
    'Opportunity',
    'Contract',
    'Coupon',
    'PricingBaseline',
    'PaymentMilestone'
] 