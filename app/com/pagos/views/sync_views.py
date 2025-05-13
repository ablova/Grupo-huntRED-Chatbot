from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from app.models import BusinessUnit
from app.com.pagos.tasks import sincronizar_pricing_task

@login_required
def sync_pricing_view(request, business_unit_slug):
    """
    Vista para iniciar la sincronización manual de pricing para una Business Unit específica.
    
    Args:
        request: HttpRequest
        business_unit_slug: Slug de la Business Unit
    
    Returns:
        Redirect a la página de configuración o JSONResponse
    """
    try:
        # Obtener la Business Unit
        business_unit = get_object_or_404(BusinessUnit, name=business_unit_slug)
        
        # Verificar que tiene configuración de WordPress
        if not business_unit.wordpress_base_url or not business_unit.wordpress_auth_token:
            messages.error(request, f"La Business Unit {business_unit.name} no tiene configurada la sincronización con WordPress.")
            return redirect('admin:app_businessunit_change', business_unit.id)
        
        # Iniciar tarea de sincronización
        sincronizar_pricing_task.delay(business_unit.name)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'message': f'Sincronización iniciada para {business_unit.name}'
            })
        
        messages.success(request, f'Sincronización iniciada para {business_unit.name}')
        return redirect('admin:app_businessunit_change', business_unit.id)
        
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)
        
        messages.error(request, f'Error al iniciar la sincronización: {str(e)}')
        return redirect('admin:app_businessunit_change', business_unit.id)

@login_required
def sync_all_pricing_view(request):
    """
    Vista para iniciar la sincronización manual de pricing para todas las Business Units.
    
    Args:
        request: HttpRequest
    
    Returns:
        Redirect a la página de configuración o JSONResponse
    """
    try:
        # Obtener todas las Business Units con configuración de WordPress
        business_units = BusinessUnit.objects.filter(
            wordpress_base_url__isnull=False,
            wordpress_auth_token__isnull=False
        )
        
        # Iniciar tarea de sincronización para cada Business Unit
        for bu in business_units:
            sincronizar_pricing_task.delay(bu.name)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'message': f'Sincronización iniciada para {len(business_units)} Business Units'
            })
        
        messages.success(request, f'Sincronización iniciada para {len(business_units)} Business Units')
        return redirect('admin:app_businessunit_changelist')
        
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)
        
        messages.error(request, f'Error al iniciar la sincronización: {str(e)}')
        return redirect('admin:app_businessunit_changelist')
