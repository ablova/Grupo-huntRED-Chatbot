# app/ats/onboarding/dashboard_share.py
"""
Módulo para la gestión de dashboards compartidos con clientes.

Este módulo implementa la generación y gestión de enlaces únicos para compartir
dashboards de cliente con acceso restringido y temporal.
"""

import logging
import secrets
from datetime import timedelta

from django.http import JsonResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.conf import settings
from django.urls import reverse
from django.contrib import messages
from asgiref.sync import sync_to_async

from app.models import Company as Empresa, BusinessUnit
# from app.models import ClientDashboardShare, ClientDashboardAccessLog
from app.ats.utilidades.auth_utils import has_bu_permission, get_user_business_units

logger = logging.getLogger(__name__)

class DashboardShareView(View):
    """
    Vista para la gestión de enlaces compartidos de dashboards para clientes.
    Incluye funcionalidades para crear, listar, editar y eliminar enlaces.
    """
    
    @method_decorator(login_required)
    async def get(self, request):
        """
        Muestra el panel de gestión de enlaces compartidos.
        """
        # Obtener unidades de negocio permitidas para el usuario
        @sync_to_async
        def get_allowed_bus():
            return get_user_business_units(request.user)
        
        business_units = await get_allowed_bus()
        
        # Obtener enlaces compartidos de las BUs permitidas
        @sync_to_async
        def get_dashboard_shares():
            shares = []
            for bu in business_units:
                bu_shares = ClientDashboardShare.objects.filter(
                    business_unit=bu
                ).select_related('empresa', 'business_unit', 'created_by')
                shares.extend(bu_shares)
            return shares
        
        dashboard_shares = await get_dashboard_shares()
        
        # Agrupar enlaces por empresa para mejor visualización
        shares_by_empresa = {}
        for share in dashboard_shares:
            empresa_id = share.empresa.id
            if empresa_id not in shares_by_empresa:
                shares_by_empresa[empresa_id] = {
                    'empresa': share.empresa,
                    'shares': []
                }
            shares_by_empresa[empresa_id]['shares'].append(share)
        
        # Ordenar por empresa
        shares_by_empresa = dict(sorted(
            shares_by_empresa.items(), 
            key=lambda item: item[1]['empresa'].name
        ))
        
        # Pasar datos al template
        context = {
            'business_units': business_units,
            'shares_by_empresa': shares_by_empresa,
            'user_is_admin': request.user.is_staff or request.user.is_superuser,
        }
        
        return render(request, 'dashboard/client/manage_shares.html', context)
    
    @method_decorator(login_required)
    async def post(self, request):
        """
        Crea o actualiza un enlace compartido.
        """
        try:
            # Validar permisos
            business_unit_id = request.POST.get('business_unit_id')
            empresa_id = request.POST.get('empresa_id')
            
            @sync_to_async
            def check_permission():
                return has_bu_permission(request.user, business_unit_id)
            
            has_permission = await check_permission()
            if not has_permission:
                return JsonResponse({'error': 'No tiene permisos para esta operación'}, status=403)
            
            # Obtener datos del formulario
            share_id = request.POST.get('share_id')
            name = request.POST.get('name')
            expiry_days = int(request.POST.get('expiry_days', 30))
            allow_satisfaction = request.POST.get('allow_satisfaction', False) == 'on'
            allow_onboarding = request.POST.get('allow_onboarding', False) == 'on'
            allow_recommendations = request.POST.get('allow_recommendations', False) == 'on'
            require_auth = request.POST.get('require_auth', False) == 'on'
            
            # Calcular fecha de caducidad
            expiry_date = timezone.now() + timedelta(days=expiry_days)
            
            @sync_to_async
            def save_dashboard_share():
                if share_id:
                    # Actualizar enlace existente
                    share = get_object_or_404(ClientDashboardShare, id=share_id)
                    
                    if share.created_by != request.user and not request.user.is_staff:
                        raise PermissionError("No puede editar este enlace")
                    
                    share.name = name
                    share.expiry_date = expiry_date
                    share.allow_satisfaction_view = allow_satisfaction
                    share.allow_onboarding_view = allow_onboarding
                    share.allow_recommendations_view = allow_recommendations
                    share.require_auth = require_auth
                    share.save()
                else:
                    # Crear nuevo enlace
                    business_unit = get_object_or_404(BusinessUnit, id=business_unit_id)
                    empresa = get_object_or_404(Empresa, id=empresa_id)
                    
                    share = ClientDashboardShare.objects.create(
                        business_unit=business_unit,
                        empresa=empresa,
                        created_by=request.user,
                        name=name,
                        expiry_date=expiry_date,
                        allow_satisfaction_view=allow_satisfaction,
                        allow_onboarding_view=allow_onboarding,
                        allow_recommendations_view=allow_recommendations,
                        require_auth=require_auth
                    )
                
                # Generar URL completa
                dashboard_url = f"{settings.SITE_URL}/onboarding/dashboard/client/share/{share.token}/"
                return {'id': share.id, 'url': dashboard_url, 'name': share.name}
            
            result = await save_dashboard_share()
            return JsonResponse(result)
            
        except Exception as e:
            logger.error(f"Error en DashboardShareView.post: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)
    
    @method_decorator(login_required)
    async def delete(self, request, share_id):
        """
        Elimina un enlace compartido.
        """
        try:
            @sync_to_async
            def delete_share():
                share = get_object_or_404(ClientDashboardShare, id=share_id)
                
                # Solo el creador o un admin puede eliminar
                if share.created_by != request.user and not request.user.is_staff:
                    raise PermissionError("No tiene permisos para eliminar este enlace")
                
                share.delete()
            
            await delete_share()
            return JsonResponse({'success': True})
            
        except Exception as e:
            logger.error(f"Error en DashboardShareView.delete: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)


class SharedDashboardView(View):
    """
    Vista pública (no requiere login) para mostrar el dashboard compartido.
    Solo accesible a través del token y si no ha caducado.
    """
    
    async def get(self, request, token):
        """
        Muestra el dashboard compartido si el token es válido.
        """
        try:
            @sync_to_async
            def get_share_data():
                try:
                    # Obtener enlace por token
                    share = get_object_or_404(
                        ClientDashboardShare, 
                        token=token, 
                        is_active=True
                    )
                    
                    # Verificar si no ha caducado
                    if share.is_expired:
                        return {'expired': True, 'share': share}
                    
                    # Registrar acceso
                    access_log = ClientDashboardAccessLog(
                        dashboard_share=share,
                        ip_address=request.META.get('REMOTE_ADDR'),
                        user_agent=request.META.get('HTTP_USER_AGENT'),
                        referrer=request.META.get('HTTP_REFERER')
                    )
                    access_log.save()
                    
                    # Actualizar contador de accesos
                    share.register_access()
                    
                    return {
                        'expired': False,
                        'share': share,
                        'empresa': share.empresa,
                        'business_unit': share.business_unit
                    }
                except ClientDashboardShare.DoesNotExist:
                    return {'invalid': True}
            
            share_data = await get_share_data()
            
            if share_data.get('invalid'):
                raise Http404("Enlace no encontrado o inválido")
            
            if share_data.get('expired'):
                return render(request, 'dashboard/client/shared_expired.html', {
                    'share': share_data['share']
                })
            
            # Preparar contexto para la vista
            context = {
                'share': share_data['share'],
                'empresa': share_data['empresa'],
                'business_unit': share_data['business_unit'],
                'is_shared_view': True,
                'allow_satisfaction': share_data['share'].allow_satisfaction_view,
                'allow_onboarding': share_data['share'].allow_onboarding_view,
                'allow_recommendations': share_data['share'].allow_recommendations_view,
            }
            
            return render(request, 'dashboard/client/shared_dashboard.html', context)
            
        except Http404:
            return render(request, 'dashboard/client/shared_invalid.html')
        except Exception as e:
            logger.error(f"Error en SharedDashboardView.get: {str(e)}")
            return render(request, 'dashboard/client/shared_error.html', {
                'error': "Ha ocurrido un error al mostrar el dashboard compartido."
            })


@login_required
async def regenerate_token(request, share_id):
    """
    Regenera el token de un enlace compartido existente.
    Útil si un token se ha visto comprometido.
    """
    try:
        @sync_to_async
        def update_token():
            share = get_object_or_404(ClientDashboardShare, id=share_id)
            
            # Solo el creador o un admin puede regenerar
            if share.created_by != request.user and not request.user.is_staff:
                raise PermissionError("No tiene permisos para esta operación")
            
            # Generar nuevo token
            share.token = secrets.token_urlsafe(32)
            share.save(update_fields=['token'])
            
            # Generar URL completa
            dashboard_url = f"{settings.SITE_URL}/onboarding/dashboard/client/share/{share.token}/"
            return {'id': share.id, 'url': dashboard_url, 'name': share.name}
        
        result = await update_token()
        return JsonResponse(result)
        
    except Exception as e:
        logger.error(f"Error en regenerate_token: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
async def extend_expiry(request, share_id):
    """
    Extiende la fecha de caducidad de un enlace compartido.
    """
    try:
        days = int(request.POST.get('days', 30))
        
        @sync_to_async
        def extend_share_expiry():
            share = get_object_or_404(ClientDashboardShare, id=share_id)
            
            # Solo el creador o un admin puede extender
            if share.created_by != request.user and not request.user.is_staff:
                raise PermissionError("No tiene permisos para esta operación")
            
            # Extender caducidad
            share.extend_expiry(days=days)
            
            return {
                'id': share.id, 
                'expiry_date': share.expiry_date.strftime('%d/%m/%Y'),
                'days_remaining': share.days_remaining
            }
        
        result = await extend_share_expiry()
        return JsonResponse(result)
        
    except Exception as e:
        logger.error(f"Error en extend_expiry: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
async def share_stats(request, share_id):
    """
    Obtiene estadísticas detalladas de un enlace compartido.
    """
    try:
        @sync_to_async
        def get_share_stats():
            share = get_object_or_404(
                ClientDashboardShare.objects.select_related('empresa', 'business_unit'), 
                id=share_id
            )
            
            # Verificar permisos
            if not (share.created_by == request.user or request.user.is_staff or has_bu_permission(request.user, share.business_unit.id)):
                raise PermissionError("No tiene permisos para ver estas estadísticas")
            
            # Obtener logs de acceso
            access_logs = share.access_logs.order_by('-access_time')[:20]
            
            # Preparar datos para la vista
            logs_data = []
            for log in access_logs:
                logs_data.append({
                    'date': log.access_time.strftime('%d/%m/%Y %H:%M:%S'),
                    'ip': log.ip_address or '-',
                    'user_agent': log.user_agent or '-',
                    'referrer': log.referrer or '-'
                })
            
            return {
                'share': {
                    'id': share.id,
                    'name': share.name,
                    'empresa': share.empresa.name,
                    'business_unit': share.business_unit.name,
                    'created_date': share.created_date.strftime('%d/%m/%Y'),
                    'expiry_date': share.expiry_date.strftime('%d/%m/%Y'),
                    'days_remaining': share.days_remaining,
                    'is_expired': share.is_expired,
                    'access_count': share.access_count,
                    'last_accessed': share.last_accessed.strftime('%d/%m/%Y %H:%M:%S') if share.last_accessed else '-',
                },
                'access_logs': logs_data
            }
        
        stats = await get_share_stats()
        return JsonResponse(stats)
        
    except Exception as e:
        logger.error(f"Error en share_stats: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)
