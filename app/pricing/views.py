"""
Vistas para el módulo de precios.
"""
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse, HttpResponseForbidden, HttpResponseBadRequest
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.utils import timezone
from django.core.exceptions import ValidationError

from .models import DiscountCoupon, TeamEvaluation, PromotionBanner
from .forms import (
    DiscountCouponForm, TeamEvaluationRequestForm, 
    PromotionBannerForm, TeamEvaluationCompleteForm
)
from .utils.promotions import generate_team_evaluation_offer


def is_staff_user(user):
    """Verifica si el usuario es miembro del staff."""
    return user.is_staff


@require_http_methods(["POST"])
@login_required
def apply_coupon(request):
    """
    Aplica un código de descuento a un carrito o pedido.
    """
    try:
        data = json.loads(request.body)
        code = data.get('code')
        amount = float(data.get('amount', 0))
        
        if not code or amount <= 0:
            return JsonResponse({
                'success': False,
                'error': 'Datos de solicitud inválidos'
            }, status=400)
        
        from .services.discount_service import PricingService
        result = PricingService.apply_discount_coupon(code, request.user, amount)
        
        return JsonResponse(result)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Formato de solicitud inválido'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def request_team_evaluation(request):
    """
    Vista para solicitar una evaluación de equipo.
    """
    # Verificar si ya tiene una evaluación pendiente
    existing_eval = TeamEvaluation.objects.filter(
        user=request.user,
        status__in=['pending', 'in_progress'],
        expires_at__gt=timezone.now()
    ).first()
    
    if existing_eval:
        messages.info(request, 'Ya tienes una evaluación de equipo en proceso.')
        return redirect('pricing:team_evaluation_detail', pk=existing_eval.pk)
    
    if request.method == 'POST':
        form = TeamEvaluationRequestForm(request.POST)
        if form.is_valid():
            team_size = form.cleaned_data['team_size']
            
            # Crear la oferta de evaluación
            result = generate_team_evaluation_offer(
                user=request.user,
                team_size=team_size,
                validity_days=7  # 1 semana para completar la evaluación
            )
            
            if result['success']:
                messages.success(request, '¡Solicitud de evaluación creada con éxito!')
                return redirect('pricing:team_evaluation_detail', pk=result['evaluation'].pk)
            else:
                messages.error(request, result.get('error', 'Error al crear la evaluación'))
    else:
        form = TeamEvaluationRequestForm()
    
    return render(request, 'pricing/team_evaluation_request.html', {
        'form': form,
        'active_tab': 'team_evaluation'
    })


@login_required
def team_evaluation_detail(request, pk):
    """
    Muestra los detalles de una evaluación de equipo.
    """
    evaluation = get_object_or_404(TeamEvaluation, pk=pk, user=request.user)
    
    # Verificar si el usuario es el propietario o es staff
    if evaluation.user != request.user and not request.user.is_staff:
        return HttpResponseForbidden("No tienes permiso para ver esta evaluación")
    
    # Si la evaluación está pendiente o en progreso, verificar si ha expirado
    if evaluation.status in ['pending', 'in_progress'] and evaluation.is_expired():
        evaluation.status = 'expired'
        evaluation.save(update_fields=['status'])
    
    context = {
        'evaluation': evaluation,
        'active_tab': 'team_evaluation',
        'can_edit': evaluation.status in ['pending', 'in_progress'] and not evaluation.is_expired()
    }
    
    return render(request, 'pricing/team_evaluation_detail.html', context)


@login_required
def complete_team_evaluation(request, pk):
    """
    Completa una evaluación de equipo.
    """
    evaluation = get_object_or_404(TeamEvaluation, pk=pk, user=request.user)
    
    # Verificar si la evaluación puede ser completada
    if evaluation.status not in ['pending', 'in_progress'] or evaluation.is_expired():
        messages.error(request, 'Esta evaluación no puede ser completada')
        return redirect('pricing:team_evaluation_detail', pk=pk)
    
    if request.method == 'POST':
        form = TeamEvaluationCompleteForm(request.POST, instance=evaluation)
        if form.is_valid():
            evaluation = form.save(commit=False)
            evaluation.status = 'completed'
            evaluation.save()
            
            # Aquí podrías agregar lógica adicional, como enviar notificaciones, etc.
            
            messages.success(request, '¡Evaluación completada con éxito!')
            return redirect('pricing:team_evaluation_detail', pk=pk)
    else:
        form = TeamEvaluationCompleteForm(instance=evaluation)
    
    return render(request, 'pricing/team_evaluation_complete.html', {
        'form': form,
        'evaluation': evaluation,
        'active_tab': 'team_evaluation'
    })


# Vistas para la gestión de promociones (solo staff)
@user_passes_test(is_staff_user)
def promotion_list(request):
    """Lista de banners promocionales."""
    banners = PromotionBanner.objects.all().order_by('-start_date')
    return render(request, 'pricing/promotion_list.html', {
        'banners': banners,
        'active_tab': 'promotions'
    })


@user_passes_test(is_staff_user)
def promotion_create(request):
    """Crear un nuevo banner promocional."""
    if request.method == 'POST':
        form = PromotionBannerForm(request.POST, request.FILES)
        if form.is_valid():
            banner = form.save(commit=False)
            banner.created_by = request.user
            banner.save()
            messages.success(request, '¡Banner creado con éxito!')
            return redirect('pricing:promotion_list')
    else:
        form = PromotionBannerForm()
    
    return render(request, 'pricing/promotion_form.html', {
        'form': form,
        'title': 'Crear Banner Promocional',
        'active_tab': 'promotions'
    })


@user_passes_test(is_staff_user)
def promotion_edit(request, pk):
    """Editar un banner promocional existente."""
    banner = get_object_or_404(PromotionBanner, pk=pk)
    
    if request.method == 'POST':
        form = PromotionBannerForm(request.POST, request.FILES, instance=banner)
        if form.is_valid():
            form.save()
            messages.success(request, '¡Banner actualizado con éxito!')
            return redirect('pricing:promotion_list')
    else:
        form = PromotionBannerForm(instance=banner)
    
    return render(request, 'pricing/promotion_form.html', {
        'form': form,
        'banner': banner,
        'title': 'Editar Banner',
        'active_tab': 'promotions'
    })


@user_passes_test(is_staff_user)
def promotion_delete(request, pk):
    """Eliminar un banner promocional."""
    banner = get_object_or_404(PromotionBanner, pk=pk)
    
    if request.method == 'POST':
        banner.delete()
        messages.success(request, '¡Banner eliminado con éxito!')
        return redirect('pricing:promotion_list')
    
    return render(request, 'pricing/promotion_confirm_delete.html', {
        'banner': banner,
        'active_tab': 'promotions'
    })


# Vistas para la gestión de cupones (solo staff)
@user_passes_test(is_staff_user)
def coupon_list(request):
    """Lista de cupones de descuento."""
    coupons = DiscountCoupon.objects.all().order_by('-created_at')
    return render(request, 'pricing/coupon_list.html', {
        'coupons': coupons,
        'active_tab': 'coupons'
    })


@user_passes_test(is_staff_user)
def coupon_create(request):
    """Crear un nuevo cupón de descuento."""
    if request.method == 'POST':
        form = DiscountCouponForm(request.POST)
        if form.is_valid():
            coupon = form.save(commit=False)
            coupon.created_by = request.user
            
            # Si no se proporciona un código, generar uno automáticamente
            if not coupon.code:
                from .services.discount_service import PricingService
                coupon.code = PricingService.generate_unique_code()
            
            try:
                coupon.save()
                messages.success(request, f'¡Cupón {coupon.code} creado con éxito!')
                return redirect('pricing:coupon_detail', pk=coupon.pk)
            except ValidationError as e:
                form.add_error(None, e)
    else:
        form = DiscountCouponForm()
    
    return render(request, 'pricing/coupon_form.html', {
        'form': form,
        'title': 'Crear Cupón de Descuento',
        'active_tab': 'coupons'
    })


@user_passes_test(is_staff_user)
def coupon_detail(request, pk):
    """Ver los detalles de un cupón de descuento."""
    coupon = get_object_or_404(DiscountCoupon, pk=pk)
    return render(request, 'pricing/coupon_detail.html', {
        'coupon': coupon,
        'active_tab': 'coupons'
    })


@user_passes_test(is_staff_user)
def coupon_delete(request, pk):
    """Eliminar un cupón de descuento."""
    coupon = get_object_or_404(DiscountCoupon, pk=pk)
    
    if request.method == 'POST':
        code = coupon.code
        coupon.delete()
        messages.success(request, f'¡Cupón {code} eliminado con éxito!')
        return redirect('pricing:coupon_list')
    
    return render(request, 'pricing/coupon_confirm_delete.html', {
        'coupon': coupon,
        'active_tab': 'coupons'
    })
