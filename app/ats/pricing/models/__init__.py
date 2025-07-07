"""
Modelos del módulo de pricing unificado - ESTRUCTURA ORGANIZADA.
"""
from django.db import models
# ============================================================================
# MODELOS DE PRICING
# ============================================================================
from app.ats.pricing.models.pricing import (
    PricingStrategy,
    PricePoint,
    DiscountRule,
    ReferralFee
)

# Modelo Bundle para paquetes de pricing
class Bundle(models.Model):
    """Bundle model for pricing packages."""
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    duration_days = models.PositiveIntegerField(default=30)
    features = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'ats_pricing_bundle'
        verbose_name = 'Bundle'
        verbose_name_plural = 'Bundles'
    
    def __str__(self):
        return self.name

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
    'Bundle',
    
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