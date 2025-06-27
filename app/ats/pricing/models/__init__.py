"""
Modelos del módulo de pricing unificado - ESTRUCTURA ORGANIZADA.
"""
# ============================================================================
# MODELOS DE PRICING
# ============================================================================
from app.ats.pricing.models.pricing import (
    PricingStrategy,
    PricePoint,
    DiscountRule,
    ReferralFee
)

from app.ats.pricing.models.service import (
    PricingCalculation,
    PricingPayment
)

from .feedback import ProposalFeedback, MeetingRequest

from app.ats.pricing.models.proposal import (
    PricingProposal,
    ProposalSection,
    ProposalTemplate
)

from app.ats.pricing.models.addons import BusinessUnitAddon

# ============================================================================
# MODELOS DE PAGOS (ORGANIZADOS)
# ============================================================================
from app.ats.pricing.models.payments import (
    # Gateways y transacciones
    PaymentGateway,
    BankAccount,
    PACConfiguration,
    
    # Pagos programados
    ScheduledPayment,
    ScheduledPaymentExecution,
    
    # CFDI en exhibiciones
    CFDIExhibition,
    PartialPayment
)

# PaymentTransaction desde app.models (no duplicado)
from app.models import PaymentTransaction

# ============================================================================
# MODELOS DE NEGOCIO (ORGANIZADOS)
# ============================================================================
from app.ats.pricing.models.business import (
    # Empleadores y empleados
    Empleador,
    Empleado,
    
    # Oportunidades y sincronización
    Oportunidad,
    PagoRecurrente,
    SincronizacionLog,
    SincronizacionError
)

# ============================================================================
# MODELOS DE SERVICIOS EXTERNOS
# ============================================================================
from .external_services import (
    ExternalServiceType,
    ExternalService,
    ExternalServiceMilestone,
    ExternalServiceInvoice,
    ExternalServiceActivity
)

# ============================================================================
# EXPORTACIÓN DE TODOS LOS MODELOS
# ============================================================================
__all__ = [
    # ========================================================================
    # MODELOS DE PRICING
    # ========================================================================
    'PricingStrategy',
    'PricePoint',
    'DiscountRule',
    'ReferralFee',
    
    # Modelos de servicio
    'PricingCalculation',
    'PricingPayment',
    
    # Modelos de feedback
    'ProposalFeedback',
    'MeetingRequest',
    
    # Modelos de propuestas
    'PricingProposal',
    'ProposalSection',
    'ProposalTemplate',
    
    # Modelos de addons
    'BusinessUnitAddon',
    
    # ========================================================================
    # MODELOS DE PAGOS
    # ========================================================================
    # Gateways y transacciones
    'PaymentGateway',
    'BankAccount',
    'PaymentTransaction',  # Desde app.models
    'PACConfiguration',
    
    # Pagos programados
    'ScheduledPayment',
    'ScheduledPaymentExecution',
    
    # CFDI en exhibiciones
    'CFDIExhibition',
    'PartialPayment',
    
    # ========================================================================
    # MODELOS DE NEGOCIO
    # ========================================================================
    # Empleadores y empleados
    'Empleador',
    'Empleado',
    
    # Oportunidades y sincronización
    'Oportunidad',
    'PagoRecurrente',
    'SincronizacionLog',
    'SincronizacionError',
    
    # ========================================================================
    # MODELOS DE SERVICIOS EXTERNOS
    # ========================================================================
    'ExternalServiceType',
    'ExternalService',
    'ExternalServiceMilestone',
    'ExternalServiceInvoice',
    'ExternalServiceActivity',
] 