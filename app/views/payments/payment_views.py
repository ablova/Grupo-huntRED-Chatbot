"""
💰 VISTAS DE PAGOS - huntRED

Vistas para gestión de pagos, transacciones y procesamiento de pagos.
"""

import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q, Sum, Count
from django.core.cache import cache
from django.utils.translation import gettext as _
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.exceptions import PermissionDenied
from django.utils import timezone

from app.ats.pricing.models.payments import PaymentTransaction, PaymentIntent
from app.ats.pricing.services.payment_service import PaymentService
from app.ats.empleadores.models import Empleador
from app.models import BusinessUnit
from app.ats.utils.rbac import RBAC

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
class PaymentTransactionListView(LoginRequiredMixin, BUFilterMixin, CacheMixin, ListView):
    """Vista para listar transacciones de pago con filtrado por BU y caché."""
    model = PaymentTransaction
    template_name = 'pricing/payment_transaction_list.html'
    context_object_name = 'transactions'
    paginate_by = 20
    cache_timeout = 180  # 3 minutos
    
    def get_queryset(self):
        """Filtra y ordena el queryset con optimizaciones."""
        queryset = super().get_queryset()
        
        # Prefetch relacionados para reducir consultas
        queryset = queryset.select_related('business_unit', 'customer').prefetch_related('payment_intent')
        
        # Filtros adicionales
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
            
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(customer__name__icontains=search) |
                Q(reference__icontains=search) |
                Q(description__icontains=search)
            )
        
        # Ordenar
        order_by = self.request.GET.get('order_by', '-created_at')
        return queryset.order_by(order_by)
    
    def get_context_data(self, **kwargs):
        """Agrega datos adicionales al contexto."""
        context = super().get_context_data(**kwargs)
        
        # Añadir estadísticas al contexto
        context['total_transactions'] = self.get_queryset().count()
        context['total_amount'] = self.get_queryset().aggregate(Sum('amount'))['amount__sum'] or 0
        context['status_counts'] = dict(self.get_queryset().values_list('status').annotate(Count('id')))
        
        # Añadir filtros activos
        context['active_filters'] = {
            'status': self.request.GET.get('status', ''),
            'search': self.request.GET.get('search', ''),
            'order_by': self.request.GET.get('order_by', '-created_at'),
            'bu_id': self.request.GET.get('bu_id', '')
        }
        
        return context


class PaymentTransactionCreateView(LoginRequiredMixin, CreateView):
    """Vista para crear transacciones de pago."""
    model = PaymentTransaction
    template_name = 'pricing/payment_transaction_form.html'
    fields = ['customer', 'amount', 'currency', 'payment_method', 'description', 'reference']
    success_url = reverse_lazy('payment-transaction-list')
    
    def form_valid(self, form):
        """Asigna valores iniciales a la transacción."""
        # Establecer BU basado en el customer si no se especifica
        if not form.instance.business_unit and form.instance.customer and hasattr(form.instance.customer, 'business_unit'):
            form.instance.business_unit = form.instance.customer.business_unit
            
        # Establecer estado inicial
        form.instance.status = 'pending'
        
        # Establecer usuario creador
        form.instance.created_by = self.request.user
        
        messages.success(self.request, _('Transacción de pago creada exitosamente.'))
        return super().form_valid(form)


class PaymentTransactionDetailView(LoginRequiredMixin, DetailView):
    """Vista para detalles de transacciones de pago."""
    model = PaymentTransaction
    template_name = 'pricing/payment_transaction_detail.html'
    context_object_name = 'transaction'
    
    def get_queryset(self):
        """Optimiza la consulta con prefetch."""
        return PaymentTransaction.objects.select_related('business_unit', 'customer', 'payment_intent')
    
    def get_context_data(self, **kwargs):
        """Añade información adicional al contexto."""
        context = super().get_context_data(**kwargs)
        
        # Añadir información de la intención de pago
        if self.object.payment_intent:
            context['payment_intent'] = self.object.payment_intent
        
        return context


class PaymentTransactionUpdateView(LoginRequiredMixin, UpdateView):
    """Vista para actualizar transacciones de pago."""
    model = PaymentTransaction
    template_name = 'pricing/payment_transaction_form.html'
    fields = ['customer', 'amount', 'currency', 'payment_method', 'status', 'description', 'reference']
    
    def get_success_url(self):
        """Redirecciona a la vista de detalle tras actualización."""
        return reverse_lazy('payment-transaction-detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        """Registra cambios importantes."""
        # Verificar si ha cambiado el estado
        if 'status' in form.changed_data:
            old_status = self.get_object().status
            new_status = form.cleaned_data['status']
            
            messages.success(self.request, _('Estado de transacción actualizado de {} a {}.').format(old_status, new_status))
        
        return super().form_valid(form)


class PaymentTransactionDeleteView(LoginRequiredMixin, DeleteView):
    """Vista para eliminar transacciones de pago."""
    model = PaymentTransaction
    template_name = 'pricing/payment_transaction_confirm_delete.html'
    success_url = reverse_lazy('payment-transaction-list')
    
    def delete(self, request, *args, **kwargs):
        """Sobrescribe el método delete para validaciones adicionales."""
        transaction = self.get_object()
        
        # Verificar que no esté procesada
        if transaction.status in ['completed', 'processing']:
            messages.error(request, _('No se puede eliminar una transacción procesada.'))
            return redirect('payment-transaction-detail', pk=transaction.pk)
        
        messages.success(request, _('Transacción eliminada exitosamente.'))
        return super().delete(request, *args, **kwargs)


# Vistas de Customer (Empleador)
class CustomerListView(LoginRequiredMixin, BUFilterMixin, ListView):
    """Vista para listar clientes."""
    model = Empleador  # Usar el modelo existente
    template_name = 'pricing/customer_list.html'
    context_object_name = 'customers'
    paginate_by = 20


class CustomerCreateView(LoginRequiredMixin, CreateView):
    """Vista para crear clientes."""
    model = Empleador  # Usar el modelo existente
    template_name = 'pricing/customer_form.html'
    fields = ['nombre', 'email', 'telefono', 'direccion', 'bu', 'rfc', 'detalles']
    success_url = reverse_lazy('customer-list')


class CustomerDetailView(LoginRequiredMixin, DetailView):
    """Vista para detalles de clientes."""
    model = Empleador  # Usar el modelo existente
    template_name = 'pricing/customer_detail.html'
    context_object_name = 'customer'


class CustomerUpdateView(LoginRequiredMixin, UpdateView):
    """Vista para actualizar clientes."""
    model = Empleador  # Usar el modelo existente
    template_name = 'pricing/customer_form.html'
    fields = ['nombre', 'email', 'telefono', 'direccion', 'bu', 'rfc', 'detalles']
    
    def get_success_url(self):
        return reverse_lazy('customer-detail', kwargs={'pk': self.object.pk})


class CustomerDeleteView(LoginRequiredMixin, DeleteView):
    """Vista para eliminar clientes."""
    model = Empleador  # Usar el modelo existente
    template_name = 'pricing/customer_confirm_delete.html'
    success_url = reverse_lazy('customer-list')


# Vistas de Payment Intent
class PaymentIntentListView(LoginRequiredMixin, BUFilterMixin, ListView):
    """Vista para listar intenciones de pago."""
    model = PaymentIntent
    template_name = 'pricing/payment_intent_list.html'
    context_object_name = 'payment_intents'
    paginate_by = 20


class PaymentIntentCreateView(LoginRequiredMixin, CreateView):
    """Vista para crear intenciones de pago."""
    model = PaymentIntent
    template_name = 'pricing/payment_intent_form.html'
    fields = ['customer', 'amount', 'currency', 'payment_method', 'description', 'metadata']
    success_url = reverse_lazy('payment-intent-list')


class PaymentIntentDetailView(LoginRequiredMixin, DetailView):
    """Vista para detalles de intenciones de pago."""
    model = PaymentIntent
    template_name = 'pricing/payment_intent_detail.html'
    context_object_name = 'payment_intent'


class PaymentIntentUpdateView(LoginRequiredMixin, UpdateView):
    """Vista para actualizar intenciones de pago."""
    model = PaymentIntent
    template_name = 'pricing/payment_intent_form.html'
    fields = ['customer', 'amount', 'currency', 'payment_method', 'description', 'metadata']
    
    def get_success_url(self):
        return reverse_lazy('payment-intent-detail', kwargs={'pk': self.object.pk})


class PaymentIntentDeleteView(LoginRequiredMixin, DeleteView):
    """Vista para eliminar intenciones de pago."""
    model = PaymentIntent
    template_name = 'pricing/payment_intent_confirm_delete.html'
    success_url = reverse_lazy('payment-intent-list')


# Vistas de API para procesamiento de pagos
@csrf_exempt
@require_http_methods(["POST"])
def process_payment_webhook(request):
    """Webhook para procesar notificaciones de pagos."""
    try:
        # Obtener datos del webhook
        data = request.POST.dict()
        
        # Procesar webhook
        payment_service = PaymentService()
        result = payment_service.process_webhook(data)
        
        return JsonResponse({'status': 'success', 'message': 'Webhook procesado'})
        
    except Exception as e:
        logger.error(f"Error procesando webhook: {str(e)}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@login_required
def payment_dashboard(request):
    """Dashboard de pagos."""
    # Obtener estadísticas
    total_transactions = PaymentTransaction.objects.count()
    total_amount = PaymentTransaction.objects.aggregate(Sum('amount'))['amount__sum'] or 0
    pending_transactions = PaymentTransaction.objects.filter(status='pending').count()
    completed_transactions = PaymentTransaction.objects.filter(status='completed').count()
    
    # Obtener transacciones recientes
    recent_transactions = PaymentTransaction.objects.select_related('customer').order_by('-created_at')[:10]
    
    context = {
        'total_transactions': total_transactions,
        'total_amount': total_amount,
        'pending_transactions': pending_transactions,
        'completed_transactions': completed_transactions,
        'recent_transactions': recent_transactions,
    }
    
    return render(request, 'pricing/payment_dashboard.html', context) 