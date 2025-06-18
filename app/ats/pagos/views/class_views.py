from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from app.ats.pagos.models import Pago, Empleado
from app.ats.empleadores.models import Empleador
from app.ats.vacantes.models import Vacante
from app.ats.models import Oportunidad

@method_decorator(csrf_exempt, name='dispatch')
class PagoListView(LoginRequiredMixin, ListView):
    """Lista de pagos del usuario."""
    model = Pago
    template_name = 'pagos/pago_list.html'
    context_object_name = 'pagos'
    
    def get_queryset(self):
        return Pago.objects.filter(empleado=self.request.user.person)

@method_decorator(csrf_exempt, name='dispatch')
class PagoDetailView(LoginRequiredMixin, DetailView):
    """Detalles de un pago específico."""
    model = Pago
    template_name = 'pagos/pago_detail.html'
    context_object_name = 'pago'

@method_decorator(csrf_exempt, name='dispatch')
class EmpleadorListView(LoginRequiredMixin, ListView):
    """Lista de empleadores."""
    model = Empleador
    template_name = 'pagos/empleador_list.html'
    context_object_name = 'empleadores'

@method_decorator(csrf_exempt, name='dispatch')
class EmpleadorDetailView(LoginRequiredMixin, DetailView):
    """Detalles de un empleador específico."""
    model = Empleador
    template_name = 'pagos/empleador_detail.html'
    context_object_name = 'empleador'

@method_decorator(csrf_exempt, name='dispatch')
class EmpleadoListView(LoginRequiredMixin, ListView):
    model = Empleado
    template_name = 'pagos/empleado_list.html'
    context_object_name = 'empleados'
    paginate_by = 20

@method_decorator(csrf_exempt, name='dispatch')
class EmpleadoDetailView(LoginRequiredMixin, DetailView):
    model = Empleado
    template_name = 'pagos/empleado_detail.html'
    context_object_name = 'empleado'

@method_decorator(csrf_exempt, name='dispatch')
class OportunidadListView(LoginRequiredMixin, ListView):
    """Lista de oportunidades."""
    model = Oportunidad
    template_name = 'pagos/oportunidad_list.html'
    context_object_name = 'oportunidades'

@method_decorator(csrf_exempt, name='dispatch')
class OportunidadDetailView(LoginRequiredMixin, DetailView):
    """Detalles de una oportunidad específica."""
    model = Oportunidad
    template_name = 'pagos/oportunidad_detail.html'
    context_object_name = 'oportunidad' 