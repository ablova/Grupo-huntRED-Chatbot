# /home/pablo/app/ats/pricing/views.py
"""
Vistas para el módulo de pricing de Grupo huntRED®.

Este módulo contiene las vistas para gestionar propuestas, promociones especiales y
añadir empresas y contactos directamente desde la interfaz de usuario.
"""

import os
import json
from decimal import Decimal
from datetime import datetime, timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.views.generic.edit import FormView
from django.urls import reverse, reverse_lazy
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.db.models import Q, Sum, Count, F, Value, CharField
from django.db.models.functions import Concat
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from app.models import (
    BusinessUnit, Opportunity, Contact, Company, 
    TalentAnalysisRequest, ProposalTemplate, Promotion
)
from app.ats.pricing.talent_360_pricing import Talent360Pricing
from app.ats.pricing.proposal_renderer import generate_proposal
from app.ats.pricing.forms import (
    Talent360RequestForm, CompanyForm, ContactForm, 
    BulkAnalysisRequestForm, PromotionCodeForm
)
from app.ats.pricing.models import (
    PricingStrategy,
    PricePoint,
    DiscountRule,
    ReferralFee,
    PricingCalculation,
    PricingPayment,
    PricingProposal,
    ProposalSection,
    ProposalTemplate
)
from app.ats.pricing.services import (
    PricingService,
    BillingService,
    RecommendationService
)

import logging
logger = logging.getLogger(__name__)


@login_required
def pricing_dashboard(request):
    """Vista del dashboard de pricing"""
    context = {
        'strategies': PricingStrategy.objects.filter(
            business_unit__in=request.user.business_units.all()
        ),
        'price_points': PricePoint.objects.filter(
            business_unit__in=request.user.business_units.all()
        ),
        'discount_rules': DiscountRule.objects.filter(
            business_unit__in=request.user.business_units.all()
        ),
        'referral_fees': ReferralFee.objects.filter(
            business_unit__in=request.user.business_units.all()
        )
    }
    return render(request, 'pricing/dashboard.html', context)


@login_required
def strategy_detail(request, strategy_id):
    """Vista de detalle de estrategia de pricing"""
    strategy = get_object_or_404(
        PricingStrategy,
        id=strategy_id,
        business_unit__in=request.user.business_units.all()
    )
    context = {
        'strategy': strategy,
        'price_points': strategy.price_points.all(),
        'discount_rules': strategy.discount_rules.all(),
        'referral_fees': strategy.referral_fees.all()
    }
    return render(request, 'pricing/strategy_detail.html', context)


@login_required
def create_proposal(request):
    """Vista para crear una nueva propuesta"""
    if request.method == 'POST':
        # Procesar formulario
        pass
    context = {
        'templates': ProposalTemplate.objects.filter(
            business_unit__in=request.user.business_units.all()
        )
    }
    return render(request, 'pricing/create_proposal.html', context)


@login_required
def proposal_detail(request, proposal_id):
    """Vista de detalle de propuesta"""
    proposal = get_object_or_404(
        PricingProposal,
        id=proposal_id,
        oportunidad__business_unit__in=request.user.business_units.all()
    )
    context = {
        'proposal': proposal,
        'sections': proposal.secciones.all().order_by('orden')
    }
    return render(request, 'pricing/proposal_detail.html', context)


@login_required
@require_http_methods(['POST'])
@csrf_exempt
def calculate_price(request):
    """API para calcular precio"""
    try:
        data = json.loads(request.body)
        service = PricingService()
        result = service.calculate_price(
            business_unit=request.user.business_unit,
            service_type=data.get('service_type'),
            duration=data.get('duration'),
            complexity=data.get('complexity'),
            requirements=data.get('requirements', [])
        )
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
@require_http_methods(['POST'])
@csrf_exempt
def create_payment(request):
    """API para crear pago"""
    try:
        data = json.loads(request.body)
        service = BillingService()
        result = service.create_payment(
            business_unit=request.user.business_unit,
            amount=data.get('amount'),
            currency=data.get('currency'),
            payment_method=data.get('payment_method'),
            metadata=data.get('metadata', {})
        )
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
@require_http_methods(['POST'])
@csrf_exempt
def get_recommendations(request):
    """API para obtener recomendaciones de pricing"""
    try:
        data = json.loads(request.body)
        service = RecommendationService()
        result = service.get_recommendations(
            business_unit=request.user.business_unit,
            service_type=data.get('service_type'),
            market_data=data.get('market_data', {}),
            historical_data=data.get('historical_data', {})
        )
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


class Talent360RequestListView(LoginRequiredMixin, ListView):
    """Lista de solicitudes de Análisis de Talento 360°."""
    model = TalentAnalysisRequest
    template_name = 'pricing/talent360_request_list.html'
    context_object_name = 'talent_requests'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = super().get_queryset().order_by('-created_at')
        
        # Filtros
        search_query = self.request.GET.get('search', '')
        status_filter = self.request.GET.get('status', '')
        date_from = self.request.GET.get('date_from', '')
        date_to = self.request.GET.get('date_to', '')
        
        if search_query:
            queryset = queryset.filter(
                Q(opportunity__company_name__icontains=search_query) |
                Q(opportunity__contact__name__icontains=search_query) |
                Q(opportunity__name__icontains=search_query)
            )
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        if date_from:
            date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
            queryset = queryset.filter(created_at__date__gte=date_from)
        
        if date_to:
            date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
            queryset = queryset.filter(created_at__date__lte=date_to)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        context['status_filter'] = self.request.GET.get('status', '')
        context['date_from'] = self.request.GET.get('date_from', '')
        context['date_to'] = self.request.GET.get('date_to', '')
        
        # Añadir opciones para filtro de estatus
        context['status_choices'] = TalentAnalysisRequest.STATUS_CHOICES
        
        return context


class Talent360RequestCreateView(LoginRequiredMixin, CreateView):
    """Crear una nueva solicitud de Análisis de Talento 360°."""
    model = TalentAnalysisRequest
    form_class = Talent360RequestForm
    template_name = 'pricing/talent360_request_form.html'
    success_url = reverse_lazy('pricing:talent360_request_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Formularios para crear empresa y contacto en la misma vista
        context['company_form'] = CompanyForm()
        context['contact_form'] = ContactForm()
        return context
    
    def form_valid(self, form):
        # Asignar el consultor actual como creador
        form.instance.created_by = self.request.user
        
        # Calcular precio basado en cantidad de usuarios
        user_count = form.cleaned_data['user_count']
        pricing_data = Talent360Pricing.calculate_total(user_count=user_count)
        form.instance.calculated_price = pricing_data['total']
        
        # Aplicar código promocional si existe
        promo_code = form.cleaned_data.get('promotion_code')
        if promo_code:
            try:
                promotion = Promotion.objects.get(
                    code=promo_code,
                    is_active=True,
                    valid_until__gte=timezone.now().date()
                )
                # Aplicar descuento
                discount_amount = (pricing_data['total'] * promotion.discount_percentage / 100)
                form.instance.discount_amount = discount_amount
                form.instance.final_price = pricing_data['total'] - discount_amount
                form.instance.promotion_applied = promotion
                
                # Actualizar uso de la promoción
                promotion.times_used += 1
                promotion.save()
            except Promotion.DoesNotExist:
                messages.error(self.request, "El código promocional no es válido o ha expirado.")
        
        # Guardar y generar propuesta si está configurado
        response = super().form_valid(form)
        
        if form.cleaned_data.get('generate_proposal', False):
            # La propuesta se generará automáticamente por la señal post_save
            messages.success(
                self.request, 
                f"Solicitud creada exitosamente para {form.instance.opportunity.company_name}. "
                f"La propuesta se está generando automáticamente."
            )
        else:
            messages.success(
                self.request, 
                f"Solicitud creada exitosamente para {form.instance.opportunity.company_name}."
            )
        
        return response


class CompanyCreateView(LoginRequiredMixin, CreateView):
    """Crear una nueva empresa."""
    model = Company
    form_class = CompanyForm
    template_name = 'pricing/company_form.html'
    
    def get_success_url(self):
        # Redirigir de vuelta a donde vino
        next_url = self.request.GET.get('next')
        if next_url:
            return next_url
        return reverse('pricing:company_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        
        # Si es una solicitud AJAX, devolver JSON
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'id': self.object.id,
                'name': self.object.name,
                'message': f"Empresa {self.object.name} creada exitosamente."
            })
        
        messages.success(self.request, f"Empresa {self.object.name} creada exitosamente.")
        return response
    
    def form_invalid(self, form):
        # Si es una solicitud AJAX, devolver errores en JSON
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'errors': form.errors.as_json()
            }, status=400)
        
        return super().form_invalid(form)
