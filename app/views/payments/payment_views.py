"""
Vistas para la gestión de pagos.
Este módulo implementa las vistas para la gestión de pagos, empleadores, workers y oportunidades,
con integración del sistema RBAC y optimizaciones de rendimiento.
"""
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.utils.translation import gettext as _
from django.db.models import Q, Sum, Count
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.core.cache import cache
import asyncio
import logging

from app.models import Pago, Empleador, Worker, Oportunidad, BusinessUnit
from app.ats.utils.rbac import RBAC
from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)

# Mixins personalizados para reutilización de código
class CacheMixin:
    """Mixin para implementar cache en las vistas."""
    cache_timeout = 300  # 5 minutos por defecto
    
    def get_cache_key(self):
        """Genera una clave única para la caché basada en la vista y parámetros."""
        if not hasattr(self, 'request'):
            return None
            
        # Generar clave basada en URL y parámetros
        path = self.request.path
        query = self.request.GET.urlencode()
        user_id = self.request.user.id if self.request.user.is_authenticated else 'anonymous'
        return f"view_cache:{path}:{query}:{user_id}"
    
    def get_context_data(self, **kwargs):
        """Intenta obtener datos de caché primero, si no existe los genera."""
        cache_key = self.get_cache_key()
        
        if cache_key:
            cached_data = cache.get(cache_key)
            if cached_data:
                return cached_data
        
        context = super().get_context_data(**kwargs)
        
        if cache_key:
            cache.set(cache_key, context, self.cache_timeout)
            
        return context


class BUFilterMixin:
    """Mixin para filtrar por Business Unit."""
    
    def get_queryset(self):
        """Filtra el queryset por BU si está especificada."""
        queryset = super().get_queryset()
        
        # Obtener BU del request
        bu_id = self.kwargs.get('bu_id') or self.request.GET.get('bu_id')
        
        if bu_id:
            # Filtrar por BU
            return queryset.filter(bu_id=bu_id)
        
        # Si el usuario no es superadmin, limitar a sus BUs asignadas
        if not self.request.user.is_superuser and hasattr(self.request.user, 'profile'):
            user_bus = self.request.user.profile.business_units.values_list('id', flat=True)
            return queryset.filter(bu_id__in=user_bus)
            
        return queryset


# Vistas de Pago
class PagoListView(LoginRequiredMixin, BUFilterMixin, CacheMixin, ListView):
    """Vista para listar pagos con filtrado por BU y caché."""
    model = Pago
    template_name = 'pagos/pago_list.html'
    context_object_name = 'pagos'
    paginate_by = 20
    cache_timeout = 180  # 3 minutos
    
    def get_queryset(self):
        """Filtra y ordena el queryset con optimizaciones."""
        queryset = super().get_queryset()
        
        # Prefetch relacionados para reducir consultas
        queryset = queryset.select_related('empleador').prefetch_related('oportunidad')
        
        # Filtros adicionales
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(estado=status)
            
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(empleador__nombre__icontains=search) |
                Q(oportunidad__titulo__icontains=search) |
                Q(referencia__icontains=search)
            )
        
        # Ordenar
        order_by = self.request.GET.get('order_by', '-fecha_creacion')
        return queryset.order_by(order_by)
    
    def get_context_data(self, **kwargs):
        """Agrega datos adicionales al contexto."""
        context = super().get_context_data(**kwargs)
        
        # Añadir estadísticas al contexto
        context['total_pagos'] = self.get_queryset().count()
        context['total_monto'] = self.get_queryset().aggregate(Sum('monto'))['monto__sum'] or 0
        context['status_counts'] = dict(self.get_queryset().values_list('estado').annotate(Count('id')))
        
        # Añadir filtros activos
        context['active_filters'] = {
            'status': self.request.GET.get('status', ''),
            'search': self.request.GET.get('search', ''),
            'order_by': self.request.GET.get('order_by', '-fecha_creacion'),
            'bu_id': self.request.GET.get('bu_id', '')
        }
        
        return context


class PagoCreateView(LoginRequiredMixin, CreateView):
    """Vista para crear pagos."""
    model = Pago
    template_name = 'pagos/pago_form.html'
    fields = ['empleador', 'oportunidad', 'monto', 'metodo_pago', 'fecha_vencimiento', 'detalles']
    success_url = reverse_lazy('pago-list')
    
    def form_valid(self, form):
        """Asigna valores iniciales al pago."""
        # Establecer BU basado en el empleador si no se especifica
        if not form.instance.bu_id and form.instance.empleador and hasattr(form.instance.empleador, 'bu'):
            form.instance.bu = form.instance.empleador.bu
            
        # Establecer estado inicial
        form.instance.estado = 'pendiente'
        
        # Establecer usuario creador
        form.instance.creado_por = self.request.user
        
        messages.success(self.request, _('Pago creado exitosamente.'))
        return super().form_valid(form)


class PagoDetailView(LoginRequiredMixin, DetailView):
    """Vista para detalles de pagos."""
    model = Pago
    template_name = 'pagos/pago_detail.html'
    context_object_name = 'pago'
    
    def get_queryset(self):
        """Optimiza la consulta con prefetch."""
        return Pago.objects.select_related('empleador', 'oportunidad', 'bu')
    
    def get_context_data(self, **kwargs):
        """Añade información de historial al contexto."""
        context = super().get_context_data(**kwargs)
        
        # Añadir historial de cambios de estado
        context['historial'] = self.object.historial_set.all().order_by('-fecha_cambio')
        
        return context


class PagoUpdateView(LoginRequiredMixin, UpdateView):
    """Vista para actualizar pagos."""
    model = Pago
    template_name = 'pagos/pago_form.html'
    fields = ['empleador', 'oportunidad', 'monto', 'metodo_pago', 'fecha_vencimiento', 'estado', 'detalles']
    
    def get_success_url(self):
        """Redirecciona a la vista de detalle tras actualización."""
        return reverse_lazy('pago-detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        """Registra cambios importantes en el historial."""
        # Verificar si ha cambiado el estado
        if 'estado' in form.changed_data:
            # Registrar cambio en historial
            from app.models import PagoHistorial
            old_status = self.get_object().estado
            new_status = form.cleaned_data['estado']
            
            PagoHistorial.objects.create(
                pago=self.object,
                estado_anterior=old_status,
                estado_nuevo=new_status,
                usuario=self.request.user,
                comentario=f"Cambio de estado de {old_status} a {new_status}"
            )
            
            messages.success(self.request, _('Estado de pago actualizado de {} a {}.').format(old_status, new_status))
        
        return super().form_valid(form)


class PagoDeleteView(LoginRequiredMixin, DeleteView):
    """Vista para eliminar pagos."""
    model = Pago
    template_name = 'pagos/pago_confirm_delete.html'
    success_url = reverse_lazy('pago-list')
    
    def delete(self, request, *args, **kwargs):
        """Personaliza la eliminación para registrar la acción."""
        messages.success(request, _('Pago eliminado exitosamente.'))
        return super().delete(request, *args, **kwargs)


# Implementaremos las clases similares para Empleador, Worker y Oportunidad
# Siguiendo el mismo patrón con sus especificidades

class EmpleadorListView(LoginRequiredMixin, BUFilterMixin, ListView):
    model = Empleador
    template_name = 'pagos/empleador_list.html'
    context_object_name = 'empleadores'
    paginate_by = 20


class EmpleadorCreateView(LoginRequiredMixin, CreateView):
    model = Empleador
    template_name = 'pagos/empleador_form.html'
    fields = ['nombre', 'email', 'telefono', 'direccion', 'bu', 'rfc', 'detalles']
    success_url = reverse_lazy('empleador-list')


class EmpleadorDetailView(LoginRequiredMixin, DetailView):
    model = Empleador
    template_name = 'pagos/empleador_detail.html'
    context_object_name = 'empleador'


class EmpleadorUpdateView(LoginRequiredMixin, UpdateView):
    model = Empleador
    template_name = 'pagos/empleador_form.html'
    fields = ['nombre', 'email', 'telefono', 'direccion', 'bu', 'rfc', 'detalles']
    
    def get_success_url(self):
        return reverse_lazy('empleador-detail', kwargs={'pk': self.object.pk})


class EmpleadorDeleteView(LoginRequiredMixin, DeleteView):
    model = Empleador
    template_name = 'pagos/empleador_confirm_delete.html'
    success_url = reverse_lazy('empleador-list')


# Worker views
class WorkerListView(LoginRequiredMixin, BUFilterMixin, ListView):
    model = Worker
    template_name = 'pagos/worker_list.html'
    context_object_name = 'workers'
    paginate_by = 20


class WorkerCreateView(LoginRequiredMixin, CreateView):
    model = Worker
    template_name = 'pagos/worker_form.html'
    fields = ['empleador', 'nombre', 'email', 'telefono', 'puesto', 'salario', 'fecha_inicio', 'detalles']
    success_url = reverse_lazy('worker-list')


class WorkerDetailView(LoginRequiredMixin, DetailView):
    model = Worker
    template_name = 'pagos/worker_detail.html'
    context_object_name = 'worker'


class WorkerUpdateView(LoginRequiredMixin, UpdateView):
    model = Worker
    template_name = 'pagos/worker_form.html'
    fields = ['empleador', 'nombre', 'email', 'telefono', 'puesto', 'salario', 'fecha_inicio', 'detalles']
    
    def get_success_url(self):
        return reverse_lazy('worker-detail', kwargs={'pk': self.object.pk})


class WorkerDeleteView(LoginRequiredMixin, DeleteView):
    model = Worker
    template_name = 'pagos/worker_confirm_delete.html'
    success_url = reverse_lazy('worker-list')


# Oportunidad views
class OportunidadListView(LoginRequiredMixin, BUFilterMixin, ListView):
    model = Oportunidad
    template_name = 'pagos/oportunidad_list.html'
    context_object_name = 'oportunidades'
    paginate_by = 20


class OportunidadCreateView(LoginRequiredMixin, CreateView):
    model = Oportunidad
    template_name = 'pagos/oportunidad_form.html'
    fields = ['empleador', 'titulo', 'descripcion', 'valor_total', 'estado', 'fecha_inicio', 'fecha_fin', 'bu']
    success_url = reverse_lazy('oportunidad-list')


class OportunidadDetailView(LoginRequiredMixin, DetailView):
    model = Oportunidad
    template_name = 'pagos/oportunidad_detail.html'
    context_object_name = 'oportunidad'


class OportunidadUpdateView(LoginRequiredMixin, UpdateView):
    model = Oportunidad
    template_name = 'pagos/oportunidad_form.html'
    fields = ['empleador', 'titulo', 'descripcion', 'valor_total', 'estado', 'fecha_inicio', 'fecha_fin', 'bu']
    
    def get_success_url(self):
        return reverse_lazy('oportunidad-detail', kwargs={'pk': self.object.pk})


class OportunidadDeleteView(LoginRequiredMixin, DeleteView):
    model = Oportunidad
    template_name = 'pagos/oportunidad_confirm_delete.html'
    success_url = reverse_lazy('oportunidad-list')
