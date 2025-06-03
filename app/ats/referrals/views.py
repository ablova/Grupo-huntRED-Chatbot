from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from decimal import Decimal

from app.models import Person, Proposal
from .models import ReferralProgram
from .services import ReferralService

@login_required
def referral_dashboard(request):
    """
    Vista del dashboard de referidos.
    """
    person = get_object_or_404(Person, user=request.user)
    stats = ReferralService.get_referrer_stats(person)
    referrals = ReferralService.search_referrals(referrer=person)
    
    context = {
        'stats': stats,
        'referrals': referrals,
        'active_referrals': referrals.filter(status__in=['pending', 'validated']),
        'completed_referrals': referrals.filter(status='completed'),
        'rejected_referrals': referrals.filter(status='rejected')
    }
    
    return render(request, 'referrals/dashboard.html', context)

@login_required
@require_http_methods(['GET', 'POST'])
def create_referral(request):
    """
    Vista para crear una nueva referencia.
    """
    if request.method == 'POST':
        person = get_object_or_404(Person, user=request.user)
        company_name = request.POST.get('company_name')
        commission = request.POST.get('commission_percentage', '10.00')
        
        try:
            commission_decimal = Decimal(commission)
            referral = ReferralService.create_referral(
                referrer=person,
                company_name=company_name,
                commission_percentage=commission_decimal
            )
            messages.success(request, 'Referencia creada exitosamente')
            return redirect('referral_dashboard')
        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, 'Error al crear la referencia')
            
    return render(request, 'referrals/create.html')

@login_required
def referral_detail(request, referral_id):
    """
    Vista de detalle de una referencia.
    """
    person = get_object_or_404(Person, user=request.user)
    referral = get_object_or_404(ReferralProgram, id=referral_id, referrer=person)
    
    context = {
        'referral': referral,
        'commission': ReferralService.calculate_commission(
            referral,
            referral.proposal.pricing_total if referral.proposal else Decimal('0')
        ) if referral.proposal else Decimal('0')
    }
    
    return render(request, 'referrals/detail.html', context)

@login_required
@require_http_methods(['POST'])
def validate_referral(request, referral_id):
    """
    Vista para validar una referencia.
    """
    person = get_object_or_404(Person, user=request.user)
    referral = get_object_or_404(ReferralProgram, id=referral_id, referrer=person)
    
    if ReferralService.validate_referral(referral):
        messages.success(request, 'Referencia validada exitosamente')
    else:
        messages.error(request, 'No se pudo validar la referencia')
        
    return redirect('referral_detail', referral_id=referral_id)

@login_required
@require_http_methods(['POST'])
def reject_referral(request, referral_id):
    """
    Vista para rechazar una referencia.
    """
    person = get_object_or_404(Person, user=request.user)
    referral = get_object_or_404(ReferralProgram, id=referral_id, referrer=person)
    
    referral.reject_referral()
    messages.success(request, 'Referencia rechazada')
    
    return redirect('referral_dashboard')

@login_required
def referral_stats(request):
    """
    Vista para obtener estadísticas de referidos en formato JSON.
    """
    person = get_object_or_404(Person, user=request.user)
    stats = ReferralService.get_referrer_stats(person)
    
    return JsonResponse(stats)

@login_required
def search_referrals(request):
    """
    Vista para buscar referidos.
    """
    person = get_object_or_404(Person, user=request.user)
    query = request.GET.get('q', '')
    status = request.GET.get('status')
    
    referrals = ReferralService.search_referrals(
        query=query,
        status=status,
        referrer=person
    )
    
    context = {
        'referrals': referrals,
        'query': query,
        'status': status
    }
    
    return render(request, 'referrals/search.html', context) 