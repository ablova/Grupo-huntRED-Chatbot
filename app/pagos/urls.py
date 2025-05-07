from django.urls import path
from .views import *

app_name = 'pagos'

urlpatterns = [
    path('pagos/', PagoListView.as_view(), name='pago-list'),
    path('pagos/crear/', PagoCreateView.as_view(), name='pago-create'),
    path('pagos/<int:pk>/', PagoDetailView.as_view(), name='pago-detail'),
    path('pagos/<int:pk>/editar/', PagoUpdateView.as_view(), name='pago-update'),
    path('pagos/<int:pk>/eliminar/', PagoDeleteView.as_view(), name='pago-delete'),
    
    path('empleadores/', EmpleadorListView.as_view(), name='empleador-list'),
    path('empleadores/crear/', EmpleadorCreateView.as_view(), name='empleador-create'),
    path('empleadores/<int:pk>/', EmpleadorDetailView.as_view(), name='empleador-detail'),
    path('empleadores/<int:pk>/editar/', EmpleadorUpdateView.as_view(), name='empleador-update'),
    path('empleadores/<int:pk>/eliminar/', EmpleadorDeleteView.as_view(), name='empleador-delete'),
    
    path('trabajadores/', WorkerListView.as_view(), name='worker-list'),
    path('trabajadores/crear/', WorkerCreateView.as_view(), name='worker-create'),
    path('trabajadores/<int:pk>/', WorkerDetailView.as_view(), name='worker-detail'),
    path('trabajadores/<int:pk>/editar/', WorkerUpdateView.as_view(), name='worker-update'),
    path('trabajadores/<int:pk>/eliminar/', WorkerDeleteView.as_view(), name='worker-delete'),
    
    path('oportunidades/', OportunidadListView.as_view(), name='oportunidad-list'),
    path('oportunidades/crear/', OportunidadCreateView.as_view(), name='oportunidad-create'),
    path('oportunidades/<int:pk>/', OportunidadDetailView.as_view(), name='oportunidad-detail'),
    path('oportunidades/<int:pk>/editar/', OportunidadUpdateView.as_view(), name='oportunidad-update'),
    path('oportunidades/<int:pk>/eliminar/', OportunidadDeleteView.as_view(), name='oportunidad-delete'),
]
