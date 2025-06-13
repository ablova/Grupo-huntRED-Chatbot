# /home/pablo/app/com/pagos/urls.py
#
# Configuración de URLs para el módulo. Define endpoints, vistas y patrones de URL.

from django.urls import path
from .views import (
    # Vistas basadas en funciones
    create_payment,
    execute_payment,
    create_payout,
    process_webhook,
    
    # Vistas basadas en clases
    PagoListView,
    PagoDetailView,
    EmpleadorListView,
    EmpleadorDetailView,
    WorkerListView,
    WorkerDetailView,
    OportunidadListView,
    OportunidadDetailView
)

app_name = 'pagos'

urlpatterns = [
    # URLs para pagos
    path('pagos/', PagoListView.as_view(), name='pago_list'),
    path('pagos/<int:pk>/', PagoDetailView.as_view(), name='pago_detail'),
    path('pagos/crear/', create_payment, name='pago_create'),
    path('pagos/<int:pk>/ejecutar/', execute_payment, name='pago_execute'),
    path('pagos/crear-payout/', create_payout, name='pago_create_payout'),
    path('webhook/', process_webhook, name='pago_webhook'),
    
    # URLs para empleadores
    path('empleadores/', EmpleadorListView.as_view(), name='empleador_list'),
    path('empleadores/<int:pk>/', EmpleadorDetailView.as_view(), name='empleador_detail'),
    
    # URLs para trabajadores
    path('trabajadores/', WorkerListView.as_view(), name='worker_list'),
    path('trabajadores/<int:pk>/', WorkerDetailView.as_view(), name='worker_detail'),
    
    # URLs para oportunidades
    path('oportunidades/', OportunidadListView.as_view(), name='oportunidad_list'),
    path('oportunidades/<int:pk>/', OportunidadDetailView.as_view(), name='oportunidad_detail'),
]
