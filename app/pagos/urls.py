# /home/pablo/app/pagos/urls.py
#
# Configuración de URLs para el módulo. Define endpoints, vistas y patrones de URL.

from django.urls import path
from app.pagos.views.payment_views import (
    payment_list, initiate_payment, webhook_payment_status,
    refund_payment, payment_history, payment_details
)

app_name = 'pagos'

urlpatterns = [
    # Rutas de pagos
    path('', payment_list, name='payment-list'),
    path('iniciar/', initiate_payment, name='initiate-payment'),
    path('webhook/', webhook_payment_status, name='webhook-payment-status'),
    path('reembolso/<int:payment_id>/', refund_payment, name='refund-payment'),
    path('historial/', payment_history, name='payment-history'),
    path('detalles/<int:payment_id>/', payment_details, name='payment-details'),
    
    # Rutas de empleadores
    path('empleadores/', EmpleadorListView.as_view(), name='empleador-list'),
    path('empleadores/crear/', EmpleadorCreateView.as_view(), name='empleador-create'),
    path('empleadores/<int:pk>/', EmpleadorDetailView.as_view(), name='empleador-detail'),
    path('empleadores/<int:pk>/editar/', EmpleadorUpdateView.as_view(), name='empleador-update'),
    path('empleadores/<int:pk>/eliminar/', EmpleadorDeleteView.as_view(), name='empleador-delete'),
    
    # Rutas de trabajadores
    path('trabajadores/', WorkerListView.as_view(), name='worker-list'),
    path('trabajadores/crear/', WorkerCreateView.as_view(), name='worker-create'),
    path('trabajadores/<int:pk>/', WorkerDetailView.as_view(), name='worker-detail'),
    path('trabajadores/<int:pk>/editar/', WorkerUpdateView.as_view(), name='worker-update'),
    path('trabajadores/<int:pk>/eliminar/', WorkerDeleteView.as_view(), name='worker-delete'),
    
    # Rutas de oportunidades
    path('oportunidades/', OportunidadListView.as_view(), name='oportunidad-list'),
    path('oportunidades/crear/', OportunidadCreateView.as_view(), name='oportunidad-create'),
    path('oportunidades/<int:pk>/', OportunidadDetailView.as_view(), name='oportunidad-detail'),
    path('oportunidades/<int:pk>/editar/', OportunidadUpdateView.as_view(), name='oportunidad-update'),
    path('oportunidades/<int:pk>/eliminar/', OportunidadDeleteView.as_view(), name='oportunidad-delete'),
]
