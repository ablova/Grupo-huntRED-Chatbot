from functools import wraps
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required

def super_admin_required(view_func):
    """
    Decorador que requiere que el usuario sea super admin.
    """
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_superuser:
            messages.error(request, 'No tienes permisos para acceder a esta página.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def bu_complete_required(view_func):
    """
    Decorador que requiere que el usuario sea consultor BU completo.
    """
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if request.user.role not in ['SUPER_ADMIN', 'BU_COMPLETE']:
            messages.error(request, 'No tienes permisos para acceder a esta página.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def bu_division_required(view_func):
    """
    Decorador que requiere que el usuario sea consultor BU de división.
    """
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if request.user.role not in ['SUPER_ADMIN', 'BU_COMPLETE', 'BU_DIVISION']:
            messages.error(request, 'No tienes permisos para acceder a esta página.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def business_unit_required(bu_name):
    """
    Decorador que requiere que el usuario tenga acceso a una unidad de negocio específica.
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.has_bu_access(bu_name):
                messages.error(request, f'No tienes acceso a la unidad de negocio {bu_name}.')
                return redirect('dashboard')
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def division_required(division_name):
    """
    Decorador que requiere que el usuario tenga acceso a una división específica.
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.has_division_access(division_name):
                messages.error(request, f'No tienes acceso a la división {division_name}.')
                return redirect('dashboard')
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def permission_required(permission):
    """
    Decorador que requiere que el usuario tenga un permiso específico.
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.userpermission_set.filter(permission=permission).exists():
                messages.error(request, f'No tienes el permiso requerido: {permission}.')
                return redirect('dashboard')
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def verified_user_required(view_func):
    """
    Decorador que requiere que el usuario esté verificado.
    """
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if request.user.verification_status != 'APPROVED':
            messages.error(request, 'Tu cuenta aún no está verificada.')
            return redirect('document_verification')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def active_user_required(view_func):
    """
    Decorador que requiere que el usuario esté activo.
    """
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if request.user.status != 'ACTIVE':
            messages.error(request, 'Tu cuenta está inactiva o pendiente de aprobación.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped_view
