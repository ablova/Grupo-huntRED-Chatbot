"""Re-exportación de modelos desde app.models y módulos especializados.

Este archivo existe para mantener compatibilidad con código existente.
Todas las referencias nuevas deben importar directamente desde app.models o módulos específicos.
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
    PaymentMilestone,
    DiscountCoupon,
    ClientFeedback,
    ClientFeedbackSchedule,
    # Modelos de pricing que están en app.models
    Service,
    Invoice,
    Order,
    LineItem,
    # Modelos de gamificación que están en app.models
    Badge,
    # Modelos de notificaciones
    Notification,
    NotificationChannel,
    NotificationTemplate,
    NotificationConfig,
    # Modelos de feedback
    Feedback,
    # Modelos de evaluación
    Assessment,
    Offer
)

# Importar modelos de módulos especializados
from ..gamification.models import UserBadge
from ..pricing.models import (
    Bundle,
    PricingStrategy,
    PricePoint,
    DiscountRule,
    ReferralFee,
    PaymentGateway,
    BankAccount,
    PaymentTransaction,
    PACConfiguration,
    Empleador,
    Empleado,
    Oportunidad,
    PagoRecurrente,
    SincronizacionLog,
    SincronizacionError,
    CFDIExhibition,
    PartialPayment,
    ScheduledPayment,
    ScheduledPaymentExecution
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
    'PaymentMilestone',
    'DiscountCoupon',
    'ClientFeedback',
    'ClientFeedbackSchedule',
    'Service',
    'Invoice',
    'Order',
    'LineItem',
    'Badge',
    'UserBadge',
    'Notification',
    'NotificationChannel',
    'NotificationTemplate',
    'NotificationConfig',
    'Feedback',
    'Assessment',
    'Offer',
    'Bundle',
    'PricingStrategy',
    'PricePoint',
    'DiscountRule',
    'ReferralFee',
    'PaymentGateway',
    'BankAccount',
    'PaymentTransaction',
    'PACConfiguration',
    'Empleador',
    'Empleado',
    'Oportunidad',
    'PagoRecurrente',
    'SincronizacionLog',
    'SincronizacionError',
    'CFDIExhibition',
    'PartialPayment',
    'ScheduledPayment',
    'ScheduledPaymentExecution'
] 