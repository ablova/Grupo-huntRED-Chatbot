"""
Vistas centralizadas para el módulo de pagos.
Este paquete contiene todas las vistas relacionadas con pagos y transacciones.
"""

from app.views.payments.payment_views import (
    PagoListView, PagoCreateView, PagoDetailView, PagoUpdateView, PagoDeleteView,
    EmpleadorListView, EmpleadorCreateView, EmpleadorDetailView, EmpleadorUpdateView, EmpleadorDeleteView,
    WorkerListView, WorkerCreateView, WorkerDetailView, WorkerUpdateView, WorkerDeleteView,
    OportunidadListView, OportunidadCreateView, OportunidadDetailView, OportunidadUpdateView, OportunidadDeleteView,
)

from app.views.payments.webhook_views import (
    stripe_webhook_handler,
    paypal_webhook_handler,
    process_webhook,
)

from app.views.payments.dashboard_views import (
    PaymentDashboardView,
    PaymentAnalyticsView,
)

__all__ = [
    # Vistas básicas de Pagos
    'PagoListView', 'PagoCreateView', 'PagoDetailView', 'PagoUpdateView', 'PagoDeleteView',
    # Vistas de Empleador
    'EmpleadorListView', 'EmpleadorCreateView', 'EmpleadorDetailView', 'EmpleadorUpdateView', 'EmpleadorDeleteView',
    # Vistas de Worker
    'WorkerListView', 'WorkerCreateView', 'WorkerDetailView', 'WorkerUpdateView', 'WorkerDeleteView',
    # Vistas de Oportunidad
    'OportunidadListView', 'OportunidadCreateView', 'OportunidadDetailView', 'OportunidadUpdateView', 'OportunidadDeleteView',
    # Webhook handlers
    'stripe_webhook_handler', 'paypal_webhook_handler', 'process_webhook',
    # Dashboard
    'PaymentDashboardView', 'PaymentAnalyticsView',
]
