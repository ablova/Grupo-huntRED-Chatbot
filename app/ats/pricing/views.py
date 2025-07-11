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
from django.core.paginator import Paginator

from app.models import (
    BusinessUnit, Opportunity, Contract, Company, 
    TalentAnalysisRequest, ProposalTemplate, Invoice
)
from app.ats.pricing.talent_360_pricing import Talent360Pricing
from app.ats.pricing.proposal_renderer import generate_proposal
from app.ats.pricing.forms import (
    Talent360RequestForm, CompanyForm, ContactForm, 
    BulkAnalysisRequestForm
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
    ProposalTemplate,
    # Modelos de pagos y gateways
    PaymentGateway,
    PaymentTransaction,
    BankAccount,
    PACConfiguration,
    # Modelos migrados del módulo antiguo
    Empleador,
    Empleado,
    Oportunidad,
    PagoRecurrente,
    SincronizacionLog,
    SincronizacionError
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
        ),
        'signer': request.user.signer,
        'payment_responsible': request.user.payment_responsible,
        'fiscal_responsible': request.user.fiscal_responsible,
        'process_responsible': request.user.process_responsible,
        'report_invitees': request.user.report_invitees,
        'notification_preferences': request.user.notification_preferences,
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
        'sections': proposal.secciones.all().order_by('orden'),
        'signer': proposal.oportunidad.empleador.persona.signer,
        'payment_responsible': proposal.oportunidad.empleador.persona.payment_responsible,
        'fiscal_responsible': proposal.oportunidad.empleador.persona.fiscal_responsible,
        'process_responsible': proposal.oportunidad.empleador.persona.process_responsible,
        'report_invitees': proposal.oportunidad.empleador.persona.report_invitees,
        'notification_preferences': proposal.oportunidad.empleador.persona.notification_preferences,
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
        context['signer'] = self.request.user.signer
        context['payment_responsible'] = self.request.user.payment_responsible
        context['fiscal_responsible'] = self.request.user.fiscal_responsible
        context['process_responsible'] = self.request.user.process_responsible
        context['report_invitees'] = self.request.user.report_invitees
        context['notification_preferences'] = self.request.user.notification_preferences
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
            # Por ahora, simplemente registrar el código promocional
            # En el futuro, se puede implementar validación contra cupones de descuento
            form.instance.promotion_code = promo_code
            messages.info(self.request, f"Código promocional '{promo_code}' registrado.")
        
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


# ============================================================================
# VIEWS DE PAGOS, GATEWAYS Y FACTURACIÓN ELECTRÓNICA
# ============================================================================

@login_required
def payment_dashboard(request):
    """Dashboard principal de pagos."""
    business_unit = request.user.business_unit
    
    # Estadísticas
    total_transactions = PaymentTransaction.objects.filter(
        invoice__business_unit=business_unit
    ).count()
    
    completed_transactions = PaymentTransaction.objects.filter(
        invoice__business_unit=business_unit,
        status='completed'
    ).count()
    
    total_amount = PaymentTransaction.objects.filter(
        invoice__business_unit=business_unit,
        status='completed'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Transacciones recientes
    recent_transactions = PaymentTransaction.objects.filter(
        invoice__business_unit=business_unit
    ).order_by('-created_at')[:10]
    
    # Gateways activos
    active_gateways = PaymentGateway.objects.filter(
        business_unit=business_unit,
        status='active'
    )
    
    context = {
        'total_transactions': total_transactions,
        'completed_transactions': completed_transactions,
        'total_amount': total_amount,
        'recent_transactions': recent_transactions,
        'active_gateways': active_gateways,
    }
    
    return render(request, 'pricing/payment_dashboard.html', context)


@login_required
def gateway_list(request):
    """Lista de gateways de pago."""
    business_unit = request.user.business_unit
    
    gateways = PaymentGateway.objects.filter(business_unit=business_unit)
    
    # Filtros
    gateway_type = request.GET.get('gateway_type')
    status = request.GET.get('status')
    
    if gateway_type:
        gateways = gateways.filter(gateway_type=gateway_type)
    if status:
        gateways = gateways.filter(status=status)
    
    # Paginación
    paginator = Paginator(gateways, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'gateway_types': PaymentGateway.GATEWAY_CHOICES,
        'status_choices': PaymentGateway.STATUS_CHOICES,
        'filters': {
            'gateway_type': gateway_type,
            'status': status,
        }
    }
    
    return render(request, 'pricing/gateway_list.html', context)


@login_required
def gateway_detail(request, gateway_id):
    """Detalle de un gateway de pago."""
    business_unit = request.user.business_unit
    gateway = get_object_or_404(PaymentGateway, id=gateway_id, business_unit=business_unit)
    
    # Transacciones del gateway
    transactions = PaymentTransaction.objects.filter(gateway=gateway).order_by('-created_at')[:50]
    
    # Estadísticas del gateway
    gateway_stats = transactions.aggregate(
        total_transactions=Count('id'),
        completed_transactions=Count('id', filter=Q(status='completed')),
        total_amount=Sum('amount', filter=Q(status='completed')),
        failed_transactions=Count('id', filter=Q(status='failed'))
    )
    
    context = {
        'gateway': gateway,
        'transactions': transactions,
        'gateway_stats': gateway_stats,
    }
    
    return render(request, 'pricing/gateway_detail.html', context)


@login_required
def gateway_create(request):
    """Crear nuevo gateway de pago."""
    business_unit = request.user.business_unit
    
    if request.method == 'POST':
        try:
            # Crear gateway
            gateway = PaymentGateway.objects.create(
                name=request.POST['name'],
                gateway_type=request.POST['gateway_type'],
                status=request.POST.get('status', 'inactive'),
                business_unit=business_unit,
                api_key=request.POST.get('api_key', ''),
                api_secret=request.POST.get('api_secret', ''),
                webhook_url=request.POST.get('webhook_url', ''),
                webhook_secret=request.POST.get('webhook_secret', ''),
                description=request.POST.get('description', ''),
                created_by=request.user
            )
            
            # Configurar monedas y métodos de pago según el tipo
            gateway.supported_currencies = _get_default_currencies(gateway.gateway_type)
            gateway.supported_payment_methods = _get_default_payment_methods(gateway.gateway_type)
            gateway.save()
            
            messages.success(request, f'Gateway "{gateway.name}" creado exitosamente.')
            return redirect('pricing:gateway_detail', gateway_id=gateway.id)
            
        except Exception as e:
            messages.error(request, f'Error creando gateway: {str(e)}')
    
    context = {
        'gateway_types': PaymentGateway.GATEWAY_CHOICES,
        'status_choices': PaymentGateway.STATUS_CHOICES,
    }
    
    return render(request, 'pricing/gateway_form.html', context)


@login_required
def gateway_edit(request, gateway_id):
    """Editar gateway de pago."""
    business_unit = request.user.business_unit
    gateway = get_object_or_404(PaymentGateway, id=gateway_id, business_unit=business_unit)
    
    if request.method == 'POST':
        try:
            # Actualizar gateway
            gateway.name = request.POST['name']
            gateway.gateway_type = request.POST['gateway_type']
            gateway.status = request.POST.get('status', 'inactive')
            gateway.api_key = request.POST.get('api_key', '')
            gateway.api_secret = request.POST.get('api_secret', '')
            gateway.webhook_url = request.POST.get('webhook_url', '')
            gateway.webhook_secret = request.POST.get('webhook_secret', '')
            gateway.description = request.POST.get('description', '')
            gateway.save()
            
            messages.success(request, f'Gateway "{gateway.name}" actualizado exitosamente.')
            return redirect('pricing:gateway_detail', gateway_id=gateway.id)
            
        except Exception as e:
            messages.error(request, f'Error actualizando gateway: {str(e)}')
    
    context = {
        'gateway': gateway,
        'gateway_types': PaymentGateway.GATEWAY_CHOICES,
        'status_choices': PaymentGateway.STATUS_CHOICES,
    }
    
    return render(request, 'pricing/gateway_form.html', context)


@login_required
def bank_account_list(request):
    """Lista de cuentas bancarias."""
    business_unit = request.user.business_unit
    
    accounts = BankAccount.objects.filter(business_unit=business_unit)
    
    # Filtros
    bank = request.GET.get('bank')
    account_type = request.GET.get('account_type')
    is_active = request.GET.get('is_active')
    
    if bank:
        accounts = accounts.filter(bank=bank)
    if account_type:
        accounts = accounts.filter(account_type=account_type)
    if is_active:
        accounts = accounts.filter(is_active=is_active == 'true')
    
    # Paginación
    paginator = Paginator(accounts, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'bank_choices': BankAccount.BANK_CHOICES,
        'account_type_choices': BankAccount.ACCOUNT_TYPE_CHOICES,
        'filters': {
            'bank': bank,
            'account_type': account_type,
            'is_active': is_active,
        }
    }
    
    return render(request, 'pricing/bank_account_list.html', context)


@login_required
def bank_account_create(request):
    """Crear nueva cuenta bancaria."""
    business_unit = request.user.business_unit
    
    if request.method == 'POST':
        try:
            # Crear cuenta bancaria
            account = BankAccount.objects.create(
                account_name=request.POST['account_name'],
                account_number=request.POST['account_number'],
                clabe=request.POST.get('clabe', ''),
                account_type=request.POST['account_type'],
                bank=request.POST['bank'],
                is_active=request.POST.get('is_active', 'true') == 'true',
                is_primary=request.POST.get('is_primary', 'false') == 'true',
                business_unit=business_unit,
                description=request.POST.get('description', ''),
                created_by=request.user
            )
            
            messages.success(request, f'Cuenta bancaria "{account.account_name}" creada exitosamente.')
            return redirect('pricing:bank_account_list')
            
        except Exception as e:
            messages.error(request, f'Error creando cuenta bancaria: {str(e)}')
    
    context = {
        'bank_choices': BankAccount.BANK_CHOICES,
        'account_type_choices': BankAccount.ACCOUNT_TYPE_CHOICES,
    }
    
    return render(request, 'pricing/bank_account_form.html', context)


@login_required
def transaction_list(request):
    """Lista de transacciones de pago."""
    business_unit = request.user.business_unit
    
    transactions = PaymentTransaction.objects.filter(
        invoice__business_unit=business_unit
    )
    
    # Filtros
    status = request.GET.get('status')
    payment_method = request.GET.get('payment_method')
    gateway = request.GET.get('gateway')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if status:
        transactions = transactions.filter(status=status)
    if payment_method:
        transactions = transactions.filter(payment_method=payment_method)
    if gateway:
        transactions = transactions.filter(gateway_id=gateway)
    if date_from:
        transactions = transactions.filter(created_at__gte=date_from)
    if date_to:
        transactions = transactions.filter(created_at__lte=date_to)
    
    # Paginación
    paginator = Paginator(transactions, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_choices': PaymentTransaction.STATUS_CHOICES,
        'payment_method_choices': PaymentTransaction.PAYMENT_METHOD_CHOICES,
        'gateways': PaymentGateway.objects.filter(business_unit=business_unit),
        'filters': {
            'status': status,
            'payment_method': payment_method,
            'gateway': gateway,
            'date_from': date_from,
            'date_to': date_to,
        }
    }
    
    return render(request, 'pricing/transaction_list.html', context)


@login_required
def transaction_detail(request, transaction_id):
    """Detalle de una transacción de pago."""
    business_unit = request.user.business_unit
    transaction = get_object_or_404(
        PaymentTransaction, 
        transaction_id=transaction_id,
        invoice__business_unit=business_unit
    )
    
    context = {
        'transaction': transaction,
    }
    
    return render(request, 'pricing/transaction_detail.html', context)


@login_required
def pac_configuration_list(request):
    """Lista de configuraciones de PAC."""
    business_unit = request.user.business_unit
    
    pac_configs = PACConfiguration.objects.filter(business_unit=business_unit)
    
    # Filtros
    pac_type = request.GET.get('pac_type')
    status = request.GET.get('status')
    
    if pac_type:
        pac_configs = pac_configs.filter(pac_type=pac_type)
    if status:
        pac_configs = pac_configs.filter(status=status)
    
    # Paginación
    paginator = Paginator(pac_configs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'pac_choices': PACConfiguration.PAC_CHOICES,
        'status_choices': PACConfiguration.STATUS_CHOICES,
        'filters': {
            'pac_type': pac_type,
            'status': status,
        }
    }
    
    return render(request, 'pricing/pac_configuration_list.html', context)


@login_required
def pac_configuration_create(request):
    """Crear nueva configuración de PAC."""
    business_unit = request.user.business_unit
    
    if request.method == 'POST':
        try:
            # Crear configuración PAC
            pac_config = PACConfiguration.objects.create(
                name=request.POST['name'],
                pac_type=request.POST['pac_type'],
                status=request.POST.get('status', 'inactive'),
                business_unit=business_unit,
                api_url=request.POST['api_url'],
                api_key=request.POST.get('api_key', ''),
                api_secret=request.POST.get('api_secret', ''),
                username=request.POST.get('username', ''),
                password=request.POST.get('password', ''),
                description=request.POST.get('description', ''),
                created_by=request.user
            )
            
            messages.success(request, f'Configuración PAC "{pac_config.name}" creada exitosamente.')
            return redirect('pricing:pac_configuration_list')
            
        except Exception as e:
            messages.error(request, f'Error creando configuración PAC: {str(e)}')
    
    context = {
        'pac_choices': PACConfiguration.PAC_CHOICES,
        'status_choices': PACConfiguration.STATUS_CHOICES,
    }
    
    return render(request, 'pricing/pac_configuration_form.html', context)


@login_required
def pac_configuration_edit(request, pac_id):
    """Editar configuración de PAC."""
    business_unit = request.user.business_unit
    pac_config = get_object_or_404(PACConfiguration, id=pac_id, business_unit=business_unit)
    
    if request.method == 'POST':
        try:
            # Actualizar configuración PAC
            pac_config.name = request.POST['name']
            pac_config.pac_type = request.POST['pac_type']
            pac_config.status = request.POST.get('status', 'inactive')
            pac_config.api_url = request.POST['api_url']
            pac_config.api_key = request.POST.get('api_key', '')
            pac_config.api_secret = request.POST.get('api_secret', '')
            pac_config.username = request.POST.get('username', '')
            pac_config.password = request.POST.get('password', '')
            pac_config.description = request.POST.get('description', '')
            pac_config.save()
            
            messages.success(request, f'Configuración PAC "{pac_config.name}" actualizada exitosamente.')
            return redirect('pricing:pac_configuration_list')
            
        except Exception as e:
            messages.error(request, f'Error actualizando configuración PAC: {str(e)}')
    
    context = {
        'pac_config': pac_config,
        'pac_choices': PACConfiguration.PAC_CHOICES,
        'status_choices': PACConfiguration.STATUS_CHOICES,
    }
    
    return render(request, 'pricing/pac_configuration_form.html', context)


@login_required
def process_payment(request, invoice_id):
    """Procesar pago de una factura."""
    business_unit = request.user.business_unit
    invoice = get_object_or_404(Invoice, id=invoice_id, business_unit=business_unit)
    
    if request.method == 'POST':
        try:
            gateway_id = request.POST.get('gateway_id')
            payment_method = request.POST.get('payment_method')
            amount = Decimal(request.POST.get('amount', invoice.total_amount))
            
            gateway = get_object_or_404(PaymentGateway, id=gateway_id, business_unit=business_unit)
            
            # Crear servicio de procesamiento
            from app.ats.pricing.services.payment_processing_service import PaymentProcessingService
            payment_service = PaymentProcessingService(business_unit)
            
            # Crear intención de pago
            result = payment_service.create_payment_intent(
                invoice=invoice,
                gateway=gateway,
                payment_method=payment_method,
                amount=amount
            )
            
            if result.get('success'):
                messages.success(request, 'Intención de pago creada exitosamente.')
                return JsonResponse(result)
            else:
                messages.error(request, f'Error creando intención de pago: {result.get("error")}')
                return JsonResponse(result, status=400)
                
        except Exception as e:
            messages.error(request, f'Error procesando pago: {str(e)}')
            return JsonResponse({'error': str(e)}, status=400)
    
    # Gateways disponibles
    gateways = PaymentGateway.objects.filter(
        business_unit=business_unit,
        status='active'
    )
    
    context = {
        'invoice': invoice,
        'gateways': gateways,
        'payment_methods': PaymentTransaction.PAYMENT_METHOD_CHOICES,
    }
    
    return render(request, 'pricing/process_payment.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def webhook_handler(request, gateway_id):
    """Maneja webhooks de gateways de pago."""
    try:
        gateway = get_object_or_404(PaymentGateway, id=gateway_id)
        
        # Verificar firma del webhook
        if not _verify_webhook_signature(request, gateway):
            return JsonResponse({'error': 'Firma inválida'}, status=400)
        
        # Procesar webhook
        from app.ats.pricing.services.payment_processing_service import PaymentProcessingService
        payment_service = PaymentProcessingService(gateway.business_unit)
        
        webhook_data = json.loads(request.body)
        success = payment_service.process_webhook(gateway, webhook_data)
        
        if success:
            return JsonResponse({'status': 'success'})
        else:
            return JsonResponse({'error': 'Error procesando webhook'}, status=400)
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


def _verify_webhook_signature(request, gateway):
    """Verifica la firma del webhook."""
    # Implementación básica - en producción verificar firma real
    return True


@login_required
def electronic_billing_dashboard(request):
    """Dashboard de facturación electrónica."""
    business_unit = request.user.business_unit
    
    # Estadísticas de facturación electrónica
    total_invoices = Invoice.objects.filter(
        business_unit=business_unit,
        electronic_billing_status__isnull=False
    ).count()
    
    stamped_invoices = Invoice.objects.filter(
        business_unit=business_unit,
        electronic_billing_status='stamped'
    ).count()
    
    pending_invoices = Invoice.objects.filter(
        business_unit=business_unit,
        electronic_billing_status='pending'
    ).count()
    
    # Configuraciones PAC activas
    active_pacs = PACConfiguration.objects.filter(
        business_unit=business_unit,
        status='active'
    )
    
    context = {
        'total_invoices': total_invoices,
        'stamped_invoices': stamped_invoices,
        'pending_invoices': pending_invoices,
        'active_pacs': active_pacs,
    }
    
    return render(request, 'pricing/electronic_billing_dashboard.html', context)


@login_required
def process_electronic_invoice(request, invoice_id):
    """Procesar facturación electrónica de una factura."""
    business_unit = request.user.business_unit
    invoice = get_object_or_404(Invoice, id=invoice_id, business_unit=business_unit)
    
    if request.method == 'POST':
        try:
            # Procesar facturación electrónica
            from app.ats.pricing.services.electronic_billing_service import ElectronicBillingService
            billing_service = ElectronicBillingService(business_unit)
            
            result = billing_service.process_invoice_electronic_billing(invoice)
            
            if result.get('success'):
                messages.success(request, 'Facturación electrónica procesada exitosamente.')
                return JsonResponse(result)
            else:
                messages.error(request, f'Error en facturación electrónica: {result.get("error")}')
                return JsonResponse(result, status=400)
                
        except Exception as e:
            messages.error(request, f'Error procesando facturación electrónica: {str(e)}')
            return JsonResponse({'error': str(e)}, status=400)
    
    context = {
        'invoice': invoice,
    }
    
    return render(request, 'pricing/process_electronic_invoice.html', context)


# Funciones auxiliares
def _get_default_currencies(gateway_type):
    """Obtiene las monedas por defecto para un tipo de gateway."""
    currency_map = {
        'stripe': ['USD', 'MXN', 'EUR'],
        'paypal': ['USD', 'MXN', 'EUR'],
        'conekta': ['MXN'],
        'mercadopago': ['MXN', 'USD'],
        'banorte': ['MXN'],
        'banamex': ['MXN'],
        'bbva': ['MXN'],
        'hsbc': ['MXN'],
        'santander': ['MXN'],
    }
    return currency_map.get(gateway_type, ['MXN'])


def _get_default_payment_methods(gateway_type):
    """Obtiene los métodos de pago por defecto para un tipo de gateway."""
    method_map = {
        'stripe': ['credit_card', 'debit_card'],
        'paypal': ['paypal'],
        'conekta': ['credit_card', 'debit_card', 'bank_transfer'],
        'mercadopago': ['credit_card', 'debit_card'],
        'banorte': ['bank_transfer'],
        'banamex': ['bank_transfer'],
        'bbva': ['bank_transfer'],
        'hsbc': ['bank_transfer'],
        'santander': ['bank_transfer'],
    }
    return method_map.get(gateway_type, ['credit_card'])


# ============================================================================
# VIEWS DE MODELOS MIGRADOS (EMPLEADORES, EMPLEADOS, OPORTUNIDADES)
# ============================================================================

@login_required
def empleador_list(request):
    """Lista de empleadores."""
    business_unit = request.user.business_unit
    
    empleadores = Empleador.objects.filter(
        persona__business_unit=business_unit
    )
    
    # Filtros
    search = request.GET.get('search', '')
    estado = request.GET.get('estado', '')
    
    if search:
        empleadores = empleadores.filter(
            Q(razon_social__icontains=search) |
            Q(rfc__icontains=search) |
            Q(persona__nombre__icontains=search) |
            Q(persona__apellido_paterno__icontains=search)
        )
    if estado:
        empleadores = empleadores.filter(estado=estado)
    
    # Paginación
    paginator = Paginator(empleadores, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'estado_choices': EstadoPerfil.choices,
        'filters': {
            'search': search,
            'estado': estado,
        }
    }
    
    return render(request, 'pricing/empleador_list.html', context)


@login_required
def empleador_create(request):
    """Crear nuevo empleador."""
    business_unit = request.user.business_unit
    
    if request.method == 'POST':
        try:
            # Crear persona primero
            from app.models import Person
            persona = Person.objects.create(
                nombre=request.POST['nombre'],
                apellido_paterno=request.POST['apellido_paterno'],
                apellido_materno=request.POST.get('apellido_materno', ''),
                email=request.POST['email'],
                telefono=request.POST.get('telefono', ''),
                business_unit=business_unit
            )
            
            # Crear empleador
            empleador = Empleador.objects.create(
                persona=persona,
                razon_social=request.POST['razon_social'],
                rfc=request.POST['rfc'],
                direccion_fiscal=request.POST['direccion_fiscal'],
                clabe=request.POST['clabe'],
                banco=request.POST['banco'],
                sitio_web=request.POST.get('sitio_web', ''),
                telefono_oficina=request.POST['telefono_oficina'],
                address=request.POST.get('address', ''),
                estado=request.POST.get('estado', EstadoPerfil.ACTIVO),
                documento_identidad=request.FILES.get('documento_identidad'),
                comprobante_domicilio=request.FILES.get('comprobante_domicilio')
            )
            
            messages.success(request, f'Empleador "{empleador.razon_social}" creado exitosamente.')
            return redirect('pricing:empleador_detail', empleador_id=empleador.id)
            
        except Exception as e:
            messages.error(request, f'Error creando empleador: {str(e)}')
    
    context = {
        'estado_choices': EstadoPerfil.choices,
    }
    
    return render(request, 'pricing/empleador_form.html', context)


@login_required
def empleador_detail(request, empleador_id):
    """Detalle de un empleador."""
    business_unit = request.user.business_unit
    empleador = get_object_or_404(
        Empleador, 
        id=empleador_id,
        persona__business_unit=business_unit
    )
    
    # Oportunidades del empleador
    oportunidades = Oportunidad.objects.filter(empleador=empleador).order_by('-fecha_creacion')
    
    context = {
        'empleador': empleador,
        'oportunidades': oportunidades,
    }
    
    return render(request, 'pricing/empleador_detail.html', context)


@login_required
def empleador_edit(request, empleador_id):
    """Editar empleador."""
    business_unit = request.user.business_unit
    empleador = get_object_or_404(
        Empleador, 
        id=empleador_id,
        persona__business_unit=business_unit
    )
    
    if request.method == 'POST':
        try:
            # Actualizar persona
            empleador.persona.nombre = request.POST['nombre']
            empleador.persona.apellido_paterno = request.POST['apellido_paterno']
            empleador.persona.apellido_materno = request.POST.get('apellido_materno', '')
            empleador.persona.email = request.POST['email']
            empleador.persona.telefono = request.POST.get('telefono', '')
            empleador.persona.save()
            
            # Actualizar empleador
            empleador.razon_social = request.POST['razon_social']
            empleador.rfc = request.POST['rfc']
            empleador.direccion_fiscal = request.POST['direccion_fiscal']
            empleador.clabe = request.POST['clabe']
            empleador.banco = request.POST['banco']
            empleador.sitio_web = request.POST.get('sitio_web', '')
            empleador.telefono_oficina = request.POST['telefono_oficina']
            empleador.address = request.POST.get('address', '')
            empleador.estado = request.POST.get('estado', EstadoPerfil.ACTIVO)
            
            if 'documento_identidad' in request.FILES:
                empleador.documento_identidad = request.FILES['documento_identidad']
            if 'comprobante_domicilio' in request.FILES:
                empleador.comprobante_domicilio = request.FILES['comprobante_domicilio']
            
            empleador.save()
            
            messages.success(request, f'Empleador "{empleador.razon_social}" actualizado exitosamente.')
            return redirect('pricing:empleador_detail', empleador_id=empleador.id)
            
        except Exception as e:
            messages.error(request, f'Error actualizando empleador: {str(e)}')
    
    context = {
        'empleador': empleador,
        'estado_choices': EstadoPerfil.choices,
    }
    
    return render(request, 'pricing/empleador_form.html', context)


@login_required
def empleado_list(request):
    """Lista de empleados."""
    business_unit = request.user.business_unit
    
    empleados = Empleado.objects.filter(
        persona__business_unit=business_unit
    )
    
    # Filtros
    search = request.GET.get('search', '')
    estado = request.GET.get('estado', '')
    
    if search:
        empleados = empleados.filter(
            Q(persona__nombre__icontains=search) |
            Q(persona__apellido_paterno__icontains=search) |
            Q(nss__icontains=search) |
            Q(ocupacion__icontains=search)
        )
    if estado:
        empleados = empleados.filter(estado=estado)
    
    # Paginación
    paginator = Paginator(empleados, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'estado_choices': EstadoPerfil.choices,
        'filters': {
            'search': search,
            'estado': estado,
        }
    }
    
    return render(request, 'pricing/empleado_list.html', context)


@login_required
def empleado_create(request):
    """Crear nuevo empleado."""
    business_unit = request.user.business_unit
    
    if request.method == 'POST':
        try:
            # Crear persona primero
            from app.models import Person
            persona = Person.objects.create(
                nombre=request.POST['nombre'],
                apellido_paterno=request.POST['apellido_paterno'],
                apellido_materno=request.POST.get('apellido_materno', ''),
                email=request.POST['email'],
                telefono=request.POST.get('telefono', ''),
                business_unit=business_unit
            )
            
            # Crear empleado
            empleado = Empleado.objects.create(
                persona=persona,
                nss=request.POST.get('nss', ''),
                ocupacion=request.POST['ocupacion'],
                experiencia_anios=request.POST.get('experiencia_anios', 0),
                clabe=request.POST['clabe'],
                banco=request.POST['banco'],
                estado=request.POST.get('estado', EstadoPerfil.ACTIVO),
                documento_identidad=request.FILES.get('documento_identidad'),
                comprobante_domicilio=request.FILES.get('comprobante_domicilio')
            )
            
            messages.success(request, f'Empleado "{empleado.persona.nombre} {empleado.persona.apellido_paterno}" creado exitosamente.')
            return redirect('pricing:empleado_detail', empleado_id=empleado.id)
            
        except Exception as e:
            messages.error(request, f'Error creando empleado: {str(e)}')
    
    context = {
        'estado_choices': EstadoPerfil.choices,
    }
    
    return render(request, 'pricing/empleado_form.html', context)


@login_required
def empleado_detail(request, empleado_id):
    """Detalle de un empleado."""
    business_unit = request.user.business_unit
    empleado = get_object_or_404(
        Empleado, 
        id=empleado_id,
        persona__business_unit=business_unit
    )
    
    context = {
        'empleado': empleado,
    }
    
    return render(request, 'pricing/empleado_detail.html', context)


@login_required
def empleado_edit(request, empleado_id):
    """Editar empleado."""
    business_unit = request.user.business_unit
    empleado = get_object_or_404(
        Empleado, 
        id=empleado_id,
        persona__business_unit=business_unit
    )
    
    if request.method == 'POST':
        try:
            # Actualizar persona
            empleado.persona.nombre = request.POST['nombre']
            empleado.persona.apellido_paterno = request.POST['apellido_paterno']
            empleado.persona.apellido_materno = request.POST.get('apellido_materno', '')
            empleado.persona.email = request.POST['email']
            empleado.persona.telefono = request.POST.get('telefono', '')
            empleado.persona.save()
            
            # Actualizar empleado
            empleado.nss = request.POST.get('nss', '')
            empleado.ocupacion = request.POST['ocupacion']
            empleado.experiencia_anios = request.POST.get('experiencia_anios', 0)
            empleado.clabe = request.POST['clabe']
            empleado.banco = request.POST['banco']
            empleado.estado = request.POST.get('estado', EstadoPerfil.ACTIVO)
            
            if 'documento_identidad' in request.FILES:
                empleado.documento_identidad = request.FILES['documento_identidad']
            if 'comprobante_domicilio' in request.FILES:
                empleado.comprobante_domicilio = request.FILES['comprobante_domicilio']
            
            empleado.save()
            
            messages.success(request, f'Empleado "{empleado.persona.nombre} {empleado.persona.apellido_paterno}" actualizado exitosamente.')
            return redirect('pricing:empleado_detail', empleado_id=empleado.id)
            
        except Exception as e:
            messages.error(request, f'Error actualizando empleado: {str(e)}')
    
    context = {
        'empleado': empleado,
        'estado_choices': EstadoPerfil.choices,
    }
    
    return render(request, 'pricing/empleado_form.html', context)


@login_required
def oportunidad_list(request):
    """Lista de oportunidades."""
    business_unit = request.user.business_unit
    
    oportunidades = Oportunidad.objects.filter(
        empleador__persona__business_unit=business_unit
    )
    
    # Filtros
    search = request.GET.get('search', '')
    estado = request.GET.get('estado', '')
    tipo_contrato = request.GET.get('tipo_contrato', '')
    modalidad = request.GET.get('modalidad', '')
    
    if search:
        oportunidades = oportunidades.filter(
            Q(titulo__icontains=search) |
            Q(descripcion__icontains=search) |
            Q(empleador__razon_social__icontains=search)
        )
    if estado:
        oportunidades = oportunidades.filter(estado=estado)
    if tipo_contrato:
        oportunidades = oportunidades.filter(tipo_contrato=tipo_contrato)
    if modalidad:
        oportunidades = oportunidades.filter(modalidad=modalidad)
    
    # Paginación
    paginator = Paginator(oportunidades, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'estado_choices': EstadoPerfil.choices,
        'tipo_contrato_choices': [
            ('tiempo_completo', 'Tiempo Completo'),
            ('medio_tiempo', 'Medio Tiempo'),
            ('freelance', 'Freelance'),
            ('proyecto', 'Por Proyecto')
        ],
        'modalidad_choices': [
            ('presencial', 'Presencial'),
            ('remoto', 'Remoto'),
            ('hibrido', 'Híbrido')
        ],
        'filters': {
            'search': search,
            'estado': estado,
            'tipo_contrato': tipo_contrato,
            'modalidad': modalidad,
        }
    }
    
    return render(request, 'pricing/oportunidad_list.html', context)


@login_required
def oportunidad_create(request):
    """Crear nueva oportunidad."""
    business_unit = request.user.business_unit
    
    if request.method == 'POST':
        try:
            empleador_id = request.POST.get('empleador_id')
            empleador = get_object_or_404(Empleador, id=empleador_id, persona__business_unit=business_unit)
            
            oportunidad = Oportunidad.objects.create(
                empleador=empleador,
                titulo=request.POST['titulo'],
                descripcion=request.POST['descripcion'],
                tipo_contrato=request.POST['tipo_contrato'],
                salario_minimo=Decimal(request.POST['salario_minimo']),
                salario_maximo=Decimal(request.POST['salario_maximo']),
                pais=request.POST['pais'],
                ciudad=request.POST['ciudad'],
                modalidad=request.POST['modalidad'],
                estado=request.POST.get('estado', EstadoPerfil.ACTIVO)
            )
            
            messages.success(request, f'Oportunidad "{oportunidad.titulo}" creada exitosamente.')
            return redirect('pricing:oportunidad_detail', oportunidad_id=oportunidad.id)
            
        except Exception as e:
            messages.error(request, f'Error creando oportunidad: {str(e)}')
    
    # Empleadores disponibles
    empleadores = Empleador.objects.filter(
        persona__business_unit=business_unit,
        estado=EstadoPerfil.ACTIVO
    )
    
    context = {
        'empleadores': empleadores,
        'estado_choices': EstadoPerfil.choices,
        'tipo_contrato_choices': [
            ('tiempo_completo', 'Tiempo Completo'),
            ('medio_tiempo', 'Medio Tiempo'),
            ('freelance', 'Freelance'),
            ('proyecto', 'Por Proyecto')
        ],
        'modalidad_choices': [
            ('presencial', 'Presencial'),
            ('remoto', 'Remoto'),
            ('hibrido', 'Híbrido')
        ],
    }
    
    return render(request, 'pricing/oportunidad_form.html', context)


@login_required
def oportunidad_detail(request, oportunidad_id):
    """Detalle de una oportunidad."""
    business_unit = request.user.business_unit
    oportunidad = get_object_or_404(
        Oportunidad, 
        id=oportunidad_id,
        empleador__persona__business_unit=business_unit
    )
    
    # Logs de sincronización
    sincronizaciones = SincronizacionLog.objects.filter(oportunidad=oportunidad).order_by('-fecha_creacion')
    errores = SincronizacionError.objects.filter(oportunidad=oportunidad).order_by('-fecha_creacion')
    
    context = {
        'oportunidad': oportunidad,
        'sincronizaciones': sincronizaciones,
        'errores': errores,
    }
    
    return render(request, 'pricing/oportunidad_detail.html', context)


@login_required
def oportunidad_edit(request, oportunidad_id):
    """Editar oportunidad."""
    business_unit = request.user.business_unit
    oportunidad = get_object_or_404(
        Oportunidad, 
        id=oportunidad_id,
        empleador__persona__business_unit=business_unit
    )
    
    if request.method == 'POST':
        try:
            oportunidad.titulo = request.POST['titulo']
            oportunidad.descripcion = request.POST['descripcion']
            oportunidad.tipo_contrato = request.POST['tipo_contrato']
            oportunidad.salario_minimo = Decimal(request.POST['salario_minimo'])
            oportunidad.salario_maximo = Decimal(request.POST['salario_maximo'])
            oportunidad.pais = request.POST['pais']
            oportunidad.ciudad = request.POST['ciudad']
            oportunidad.modalidad = request.POST['modalidad']
            oportunidad.estado = request.POST.get('estado', EstadoPerfil.ACTIVO)
            oportunidad.save()
            
            messages.success(request, f'Oportunidad "{oportunidad.titulo}" actualizada exitosamente.')
            return redirect('pricing:oportunidad_detail', oportunidad_id=oportunidad.id)
            
        except Exception as e:
            messages.error(request, f'Error actualizando oportunidad: {str(e)}')
    
    context = {
        'oportunidad': oportunidad,
        'estado_choices': EstadoPerfil.choices,
        'tipo_contrato_choices': [
            ('tiempo_completo', 'Tiempo Completo'),
            ('medio_tiempo', 'Medio Tiempo'),
            ('freelance', 'Freelance'),
            ('proyecto', 'Por Proyecto')
        ],
        'modalidad_choices': [
            ('presencial', 'Presencial'),
            ('remoto', 'Remoto'),
            ('hibrido', 'Híbrido')
        ],
    }
    
    return render(request, 'pricing/oportunidad_form.html', context)


@login_required
def sync_oportunidad_wordpress(request, oportunidad_id):
    """Sincronizar oportunidad con WordPress."""
    business_unit = request.user.business_unit
    oportunidad = get_object_or_404(
        Oportunidad, 
        id=oportunidad_id,
        empleador__persona__business_unit=business_unit
    )
    
    try:
        # Crear servicio de sincronización
        from app.ats.pricing.services.integrations.wordpress_sync_service import WordPressSyncService
        sync_service = WordPressSyncService(business_unit.name)
        
        # Sincronizar oportunidad
        result = sync_service.sincronizar_oportunidad(oportunidad.id)
        
        if result.get('success'):
            messages.success(request, 'Oportunidad sincronizada exitosamente con WordPress.')
        else:
            messages.error(request, f'Error sincronizando: {result.get("error")}')
            
    except Exception as e:
        messages.error(request, f'Error en sincronización: {str(e)}')
    
    return redirect('pricing:oportunidad_detail', oportunidad_id=oportunidad.id)


@login_required
def pago_recurrente_list(request):
    """Lista de pagos recurrentes."""
    business_unit = request.user.business_unit
    
    pagos_recurrentes = PagoRecurrente.objects.filter(
        pago_base__business_unit=business_unit
    )
    
    # Filtros
    activo = request.GET.get('activo', '')
    frecuencia = request.GET.get('frecuencia', '')
    
    if activo:
        pagos_recurrentes = pagos_recurrentes.filter(activo=activo == 'true')
    if frecuencia:
        pagos_recurrentes = pagos_recurrentes.filter(frecuencia=frecuencia)
    
    # Paginación
    paginator = Paginator(pagos_recurrentes, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'frecuencia_choices': [
            ('diario', 'Diario'),
            ('semanal', 'Semanal'),
            ('quincenal', 'Quincenal'),
            ('mensual', 'Mensual'),
            ('anual', 'Anual')
        ],
        'filters': {
            'activo': activo,
            'frecuencia': frecuencia,
        }
    }
    
    return render(request, 'pricing/pago_recurrente_list.html', context)


@login_required
def pago_recurrente_create(request):
    """Crear nuevo pago recurrente."""
    business_unit = request.user.business_unit
    
    if request.method == 'POST':
        try:
            # Crear pago base primero
            from app.models import Pago
            pago_base = Pago.objects.create(
                business_unit=business_unit,
                amount=Decimal(request.POST['amount']),
                currency=request.POST.get('currency', 'MXN'),
                description=request.POST['description'],
                created_by=request.user
            )
            
            # Crear pago recurrente
            pago_recurrente = PagoRecurrente.objects.create(
                pago_base=pago_base,
                frecuencia=request.POST['frecuencia'],
                fecha_proximo_pago=request.POST['fecha_proximo_pago'],
                fecha_fin=request.POST.get('fecha_fin'),
                activo=request.POST.get('activo', 'true') == 'true'
            )
            
            messages.success(request, f'Pago recurrente creado exitosamente.')
            return redirect('pricing:pago_recurrente_detail', pago_id=pago_recurrente.id)
            
        except Exception as e:
            messages.error(request, f'Error creando pago recurrente: {str(e)}')
    
    context = {
        'frecuencia_choices': [
            ('diario', 'Diario'),
            ('semanal', 'Semanal'),
            ('quincenal', 'Quincenal'),
            ('mensual', 'Mensual'),
            ('anual', 'Anual')
        ],
    }
    
    return render(request, 'pricing/pago_recurrente_form.html', context)


@login_required
def pago_recurrente_detail(request, pago_id):
    """Detalle de un pago recurrente."""
    business_unit = request.user.business_unit
    pago_recurrente = get_object_or_404(
        PagoRecurrente, 
        id=pago_id,
        pago_base__business_unit=business_unit
    )
    
    context = {
        'pago_recurrente': pago_recurrente,
    }
    
    return render(request, 'pricing/pago_recurrente_detail.html', context)


@login_required
def pago_recurrente_edit(request, pago_id):
    """Editar pago recurrente."""
    business_unit = request.user.business_unit
    pago_recurrente = get_object_or_404(
        PagoRecurrente, 
        id=pago_id,
        pago_base__business_unit=business_unit
    )
    
    if request.method == 'POST':
        try:
            pago_recurrente.frecuencia = request.POST['frecuencia']
            pago_recurrente.fecha_proximo_pago = request.POST['fecha_proximo_pago']
            pago_recurrente.fecha_fin = request.POST.get('fecha_fin')
            pago_recurrente.activo = request.POST.get('activo', 'true') == 'true'
            pago_recurrente.save()
            
            messages.success(request, 'Pago recurrente actualizado exitosamente.')
            return redirect('pricing:pago_recurrente_detail', pago_id=pago_recurrente.id)
            
        except Exception as e:
            messages.error(request, f'Error actualizando pago recurrente: {str(e)}')
    
    context = {
        'pago_recurrente': pago_recurrente,
        'frecuencia_choices': [
            ('diario', 'Diario'),
            ('semanal', 'Semanal'),
            ('quincenal', 'Quincenal'),
            ('mensual', 'Mensual'),
            ('anual', 'Anual')
        ],
    }
    
    return render(request, 'pricing/pago_recurrente_form.html', context)


@login_required
def wordpress_sync_dashboard(request):
    """Dashboard de sincronización con WordPress."""
    business_unit = request.user.business_unit
    
    # Estadísticas de sincronización
    total_syncs = SincronizacionLog.objects.filter(
        oportunidad__empleador__persona__business_unit=business_unit
    ).count()
    
    successful_syncs = SincronizacionLog.objects.filter(
        oportunidad__empleador__persona__business_unit=business_unit,
        estado='EXITO'
    ).count()
    
    failed_syncs = SincronizacionLog.objects.filter(
        oportunidad__empleador__persona__business_unit=business_unit,
        estado='ERROR'
    ).count()
    
    # Sincronizaciones recientes
    recent_syncs = SincronizacionLog.objects.filter(
        oportunidad__empleador__persona__business_unit=business_unit
    ).order_by('-fecha_creacion')[:10]
    
    # Errores recientes
    recent_errors = SincronizacionError.objects.filter(
        oportunidad__empleador__persona__business_unit=business_unit,
        resuelto=False
    ).order_by('-fecha_creacion')[:10]
    
    context = {
        'total_syncs': total_syncs,
        'successful_syncs': successful_syncs,
        'failed_syncs': failed_syncs,
        'recent_syncs': recent_syncs,
        'recent_errors': recent_errors,
    }
    
    return render(request, 'pricing/wordpress_sync_dashboard.html', context)


@login_required
def sync_all_wordpress(request):
    """Sincronizar todo con WordPress."""
    business_unit = request.user.business_unit
    
    try:
        # Crear servicio de sincronización
        from app.ats.pricing.services.integrations.wordpress_sync_service import WordPressSyncService
        sync_service = WordPressSyncService(business_unit.name)
        
        # Sincronizar todo
        result = sync_service.sincronizar_todos()
        
        if result.get('success'):
            messages.success(request, 'Sincronización completa exitosa.')
        else:
            messages.error(request, f'Error en sincronización: {result.get("error")}')
            
    except Exception as e:
        messages.error(request, f'Error en sincronización: {str(e)}')
    
    return redirect('pricing:wordpress_sync_dashboard')


@login_required
def sync_pricing_wordpress(request):
    """Sincronizar configuración de pricing con WordPress."""
    business_unit = request.user.business_unit
    
    try:
        # Crear servicio de sincronización
        from app.ats.pricing.services.integrations.wordpress_sync_service import WordPressSyncService
        sync_service = WordPressSyncService(business_unit.name)
        
        # Sincronizar pricing
        result = sync_service.sincronizar_pricing()
        
        if result.get('success'):
            messages.success(request, 'Pricing sincronizado exitosamente con WordPress.')
        else:
            messages.error(request, f'Error sincronizando pricing: {result.get("error")}')
            
    except Exception as e:
        messages.error(request, f'Error en sincronización: {str(e)}')
    
    return redirect('pricing:wordpress_sync_dashboard')


@login_required
def update_company_contacts(request, company_id):
    company = get_object_or_404(Company, id=company_id)
    if not (request.user.is_superuser or request.user.is_staff or request.user == company.account_manager):
        messages.error(request, "No tienes permisos para editar los contactos de esta empresa.")
        return redirect(request.META.get('HTTP_REFERER', '/'))

    if request.method == 'POST':
        form = CompanyForm(request.POST, instance=company)
        if form.is_valid():
            form.save()
            messages.success(request, "Contactos y notificaciones actualizados correctamente.")
            return redirect(request.META.get('HTTP_REFERER', '/'))
    else:
        form = CompanyForm(instance=company)

    return render(request, 'proposals/proposal_template.html', {
        'company': company,
        'form': form,
        # Agrega aquí otros contextos necesarios para la propuesta
    })
