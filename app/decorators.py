from functools import wraps
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
import logging

logger = logging.getLogger(__name__)

# Roles definidos en el sistema
ROLES = {
    'super_admin': 'Super Admin',
    'consultant_bu_complete': 'Consultant (BU Complete)',
    'consultant_bu_division': 'Consultant (BU Division)'
}

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
