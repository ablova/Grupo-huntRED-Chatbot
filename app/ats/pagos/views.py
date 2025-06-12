# /home/pablo/app/com/pagos/views.py
#
# Vista para el módulo. Implementa la lógica de presentación y manejo de peticiones HTTP.

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from app.models import Pago, Empleador, Oportunidad
from app.ats.models.worker import Worker
from app.ats.pagos.sync.wordpressgateways.paypal import PayPalGateway
from app.ats.pagos.sync.wordpresssync.wordpress import WordPressSync

@method_decorator(csrf_exempt, name='dispatch')
class PagoListView(LoginRequiredMixin, ListView):
    model = Pago
    template_name = 'pagos/pago_list.html'
    context_object_name = 'pagos'
    
    def get_queryset(self):
        return Pago.objects.filter(empleado=self.request.user.person)

@method_decorator(csrf_exempt, name='dispatch')
class PagoCreateView(LoginRequiredMixin, CreateView):
    model = Pago
    template_name = 'pagos/pago_form.html'
    fields = ['monto', 'metodo', 'moneda']
    success_url = reverse_lazy('pagos:pago-list')
    
    def form_valid(self, form):
        form.instance.empleado = self.request.user.person
        return super().form_valid(form)

@method_decorator(csrf_exempt, name='dispatch')
class PagoDetailView(LoginRequiredMixin, DetailView):
    model = Pago
    template_name = 'pagos/pago_detail.html'
    context_object_name = 'pago'

@method_decorator(csrf_exempt, name='dispatch')
class PagoUpdateView(LoginRequiredMixin, UpdateView):
    model = Pago
    template_name = 'pagos/pago_form.html'
    fields = ['monto', 'metodo', 'moneda']
    success_url = reverse_lazy('pagos:pago-list')

@method_decorator(csrf_exempt, name='dispatch')
class PagoDeleteView(LoginRequiredMixin, DeleteView):
    model = Pago
    template_name = 'pagos/pago_confirm_delete.html'
    success_url = reverse_lazy('pagos:pago-list')

@method_decorator(csrf_exempt, name='dispatch')
class EmpleadorListView(LoginRequiredMixin, ListView):
    model = Empleador
    template_name = 'pagos/empleador_list.html'
    context_object_name = 'empleadores'

@method_decorator(csrf_exempt, name='dispatch')
class EmpleadorCreateView(LoginRequiredMixin, CreateView):
    model = Empleador
    template_name = 'pagos/empleador_form.html'
    fields = ['rfc', 'direccion_fiscal', 'banco', 'clabe']
    success_url = reverse_lazy('pagos:empleador-list')
    
    def form_valid(self, form):
        form.instance.persona = self.request.user.person
        return super().form_valid(form)

@method_decorator(csrf_exempt, name='dispatch')
class EmpleadorDetailView(LoginRequiredMixin, DetailView):
    model = Empleador
    template_name = 'pagos/empleador_detail.html'
    context_object_name = 'empleador'

@method_decorator(csrf_exempt, name='dispatch')
class EmpleadorUpdateView(LoginRequiredMixin, UpdateView):
    model = Empleador
    template_name = 'pagos/empleador_form.html'
    fields = ['rfc', 'direccion_fiscal', 'banco', 'clabe']
    success_url = reverse_lazy('pagos:empleador-list')

@method_decorator(csrf_exempt, name='dispatch')
class EmpleadorDeleteView(LoginRequiredMixin, DeleteView):
    model = Empleador
    template_name = 'pagos/empleador_confirm_delete.html'
    success_url = reverse_lazy('pagos:empleador-list')

@method_decorator(csrf_exempt, name='dispatch')
class WorkerListView(LoginRequiredMixin, ListView):
    model = Worker
    template_name = 'pagos/worker_list.html'
    context_object_name = 'workers'

@method_decorator(csrf_exempt, name='dispatch')
class WorkerCreateView(LoginRequiredMixin, CreateView):
    model = Worker
    template_name = 'pagos/worker_form.html'
    fields = ['especialidad', 'experiencia', 'disponibilidad']
    success_url = reverse_lazy('pagos:worker-list')
    
    def form_valid(self, form):
        form.instance.persona = self.request.user.person
        return super().form_valid(form)

@method_decorator(csrf_exempt, name='dispatch')
class WorkerDetailView(LoginRequiredMixin, DetailView):
    model = Worker
    template_name = 'pagos/worker_detail.html'
    context_object_name = 'worker'

@method_decorator(csrf_exempt, name='dispatch')
class WorkerUpdateView(LoginRequiredMixin, UpdateView):
    model = Worker
    template_name = 'pagos/worker_form.html'
    fields = ['especialidad', 'experiencia', 'disponibilidad']
    success_url = reverse_lazy('pagos:worker-list')

@method_decorator(csrf_exempt, name='dispatch')
class WorkerDeleteView(LoginRequiredMixin, DeleteView):
    model = Worker
    template_name = 'pagos/worker_confirm_delete.html'
    success_url = reverse_lazy('pagos:worker-list')

@method_decorator(csrf_exempt, name='dispatch')
class OportunidadListView(LoginRequiredMixin, ListView):
    model = Oportunidad
    template_name = 'pagos/oportunidad_list.html'
    context_object_name = 'oportunidades'

@method_decorator(csrf_exempt, name='dispatch')
class OportunidadCreateView(LoginRequiredMixin, CreateView):
    model = Oportunidad
    template_name = 'pagos/oportunidad_form.html'
    fields = ['empleador', 'titulo', 'descripcion', 'ubicacion', 'tipo_contrato', 'salario']
    success_url = reverse_lazy('pagos:oportunidad-list')
    
    def form_valid(self, form):
        form.instance.empleador = self.request.user.empleador
        return super().form_valid(form)

@method_decorator(csrf_exempt, name='dispatch')
class OportunidadDetailView(LoginRequiredMixin, DetailView):
    model = Oportunidad
    template_name = 'pagos/oportunidad_detail.html'
    context_object_name = 'oportunidad'

@method_decorator(csrf_exempt, name='dispatch')
class OportunidadUpdateView(LoginRequiredMixin, UpdateView):
    model = Oportunidad
    template_name = 'pagos/oportunidad_form.html'
    fields = ['empleador', 'titulo', 'descripcion', 'ubicacion', 'tipo_contrato', 'salario']
    success_url = reverse_lazy('pagos:oportunidad-list')

@method_decorator(csrf_exempt, name='dispatch')
class OportunidadDeleteView(LoginRequiredMixin, DeleteView):
    model = Oportunidad
    template_name = 'pagos/oportunidad_confirm_delete.html'
    success_url = reverse_lazy('pagos:oportunidad-list')

@csrf_exempt
def process_payment(request):
    if request.method == 'POST':
        try:
            pago_id = request.POST.get('pago_id')
            pago = get_object_or_404(Pago, id=pago_id)
            
            gateway = PayPalGateway()
            success, response = gateway.crear_pago(pago)
            
            if success:
                return JsonResponse({
                    'success': True,
                    'approval_url': response.approval_url
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': response
                })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    return JsonResponse({'success': False, 'error': 'Método no permitido'})
