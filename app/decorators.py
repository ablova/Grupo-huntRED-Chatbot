# app/decorators.py
from functools import wraps
from django.http import HttpResponseForbidden, HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_http_methods
import logging
import json

logger = logging.getLogger(__name__)

# Roles definidos en el sistema
ROLES = {
    'super_admin': 'Super Admin',
    'consultant_bu_complete': 'Consultant (BU Complete)',
    'consultant_bu_division': 'Consultant (BU Division)'
}

# Decorador específico para super admin
def super_admin_required(view_func):
    """
    Decorador para restringir el acceso a vistas solo para super administradores.
    
    Args:
        view_func: Vista a restringir
        
    Returns:
        Vista decorada con restricción de super administrador
    """
    return role_required('super_admin')(view_func)

# Decorador para verificar si un usuario está activo
def active_user_required(view_func):
    """
    Decorador para restringir el acceso a vistas solo para usuarios activos.
    Verifica que el usuario tenga el atributo is_active en True.
    
    Args:
        view_func: Vista a restringir
        
    Returns:
        Vista decorada con restricción de usuario activo
    """
    @wraps(view_func)
    @login_required(login_url='login')
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_active:
            logger.warning(f"Access denied for inactive user {request.user.username}")
            return HttpResponseForbidden("Tu cuenta está inactiva. Contacta a un administrador.")
        logger.info(f"Access granted for active user {request.user.username}")
        return view_func(request, *args, **kwargs)
    return _wrapped_view

# Decorador específico para consultores con acceso completo a unidad de negocio
def bu_complete_required(view_func):
    """
    Decorador para restringir el acceso a vistas solo para consultores con acceso
    completo a una unidad de negocio.
    
    Args:
        view_func: Vista a restringir
        
    Returns:
        Vista decorada con restricción de rol
    """
    return role_required('consultant_bu_complete')(view_func)

# Decorador específico para consultores con acceso limitado a división
def bu_division_required(view_func):
    """
    Decorador para restringir el acceso a vistas solo para consultores con acceso
    limitado a una división de unidad de negocio.
    
    Args:
        view_func: Vista a restringir
        
    Returns:
        Vista decorada con restricción de rol
    """
    return role_required('consultant_bu_division')(view_func)

def role_required(*required_roles):
    """
    Decorador para restringir el acceso a vistas basadas en roles de usuario.
    Requiere que el usuario esté autenticado y tenga uno de los roles especificados.

    Args:
        *required_roles: Lista de roles requeridos para acceder a la vista.

    Returns:
        Decorador que verifica el rol del usuario.
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required(login_url='login')
        def _wrapped_view(request, *args, **kwargs):
            if not hasattr(request.user, 'role') or request.user.role not in required_roles:
                logger.warning(f"Access denied for user {request.user.username} with role {getattr(request.user, 'role', 'none')} to view requiring roles {required_roles}")
                if request.user.is_authenticated:
                    return HttpResponseForbidden("You do not have permission to access this page.")
                else:
                    return HttpResponseRedirect(reverse('login'))
            logger.info(f"Access granted for user {request.user.username} with role {request.user.role} to view requiring roles {required_roles}")
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def bu_access(bu_name=None, division=None):
    """
    Decorador para restringir el acceso basado en la unidad de negocio (BU) y división.
    Aplicable a consultores con acceso completo a BU o limitado a una división.

    Args:
        bu_name (str, optional): Nombre de la unidad de negocio requerida.
        division (str, optional): División específica dentro de la BU.

    Returns:
        Decorador que verifica el acceso a la BU y división.
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required(login_url='login')
        def _wrapped_view(request, *args, **kwargs):
            if not hasattr(request.user, 'role'):
                logger.warning(f"Access denied for user {request.user.username}: No role defined")
                return HttpResponseForbidden("You do not have permission to access this page.")

            user_role = request.user.role
            if user_role == 'super_admin':
                logger.info(f"Super Admin access granted for user {request.user.username} to BU {bu_name or 'any'} and division {division or 'any'}")
                return view_func(request, *args, **kwargs)

            if bu_name and hasattr(request.user, 'business_unit') and request.user.business_unit.name != bu_name:
                logger.warning(f"Access denied for user {request.user.username}: Not authorized for BU {bu_name}")
                return HttpResponseForbidden(f"You are not authorized to access data for {bu_name}.")

            if division and user_role == 'consultant_bu_division':
                if not hasattr(request.user, 'division') or request.user.division != division:
                    logger.warning(f"Access denied for user {request.user.username}: Not authorized for division {division}")
                    return HttpResponseForbidden(f"You are not authorized to access data for division {division}.")

            logger.info(f"Access granted for user {request.user.username} with role {user_role} to BU {bu_name or 'any'} and division {division or 'any'}")
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def permission_required(permission):
    """
    Decorador para restringir el acceso basado en permisos específicos.

    Args:
        permission (str): Permiso específico requerido.

    Returns:
        Decorador que verifica si el usuario tiene el permiso.
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required(login_url='login')
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.has_perm(permission):
                logger.warning(f"Permission denied for user {request.user.username}: Lacks permission {permission}")
                raise PermissionDenied
            logger.info(f"Permission granted for user {request.user.username}: Has permission {permission}")
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def rbac_required(allowed_roles):
    """
    Decorador para restringir el acceso a vistas según una lista de roles permitidos.
    Compatible con @method_decorator y vistas basadas en clase o función.
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required(login_url='login')
        def _wrapped_view(request, *args, **kwargs):
            user_role = getattr(request.user, 'role', None)
            if user_role not in allowed_roles:
                logger.warning(f"Access denied for user {getattr(request.user, 'username', 'anon')} with role {user_role} (required: {allowed_roles})")
                return HttpResponseForbidden("No tienes permisos para acceder a esta vista.")
            logger.info(f"Access granted for user {getattr(request.user, 'username', 'anon')} with role {user_role}")
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def check_role_access(allowed_roles):
    """
    Decorador para verificar acceso basado en roles del usuario.
    Compatible con vistas asíncronas y síncronas.
    
    Args:
        allowed_roles (list): Lista de roles permitidos para acceder a la vista.
    
    Returns:
        Decorador que verifica el rol del usuario.
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required(login_url='login')
        def _wrapped_view(request, *args, **kwargs):
            # Obtener el rol del usuario
            user_role = getattr(request.user, 'role', None)
            
            # Verificar si el usuario tiene un rol válido
            if not user_role:
                logger.warning(f"Access denied for user {getattr(request.user, 'username', 'anon')}: No role defined")
                if request.headers.get('accept') == 'application/json':
                    return JsonResponse({
                        'error': 'No tienes permisos para acceder a esta funcionalidad',
                        'code': 'NO_ROLE'
                    }, status=403)
                return HttpResponseForbidden("No tienes permisos para acceder a esta funcionalidad.")
            
            # Verificar si el rol del usuario está en la lista de roles permitidos
            if user_role not in allowed_roles:
                logger.warning(f"Access denied for user {getattr(request.user, 'username', 'anon')} with role {user_role} (required: {allowed_roles})")
                if request.headers.get('accept') == 'application/json':
                    return JsonResponse({
                        'error': f'Tu rol ({user_role}) no tiene permisos para esta funcionalidad',
                        'code': 'INSUFFICIENT_PERMISSIONS',
                        'required_roles': allowed_roles,
                        'user_role': user_role
                    }, status=403)
                return HttpResponseForbidden(f"Tu rol ({user_role}) no tiene permisos para esta funcionalidad.")
            
            logger.info(f"Access granted for user {getattr(request.user, 'username', 'anon')} with role {user_role}")
            return view_func(request, *args, **kwargs)
        
        return _wrapped_view
    return decorator
