from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from app.ats.ats.ats.client_portal.models import ClientPortalAccess

def require_portal_feature(feature_code):
    """
    Decorador para verificar si el usuario tiene acceso a una característica específica del portal.
    
    Args:
        feature_code (str): Código de la característica requerida
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            try:
                portal_access = ClientPortalAccess.objects.get(user=request.user)
                
                if not portal_access.is_active:
                    messages.error(request, 'Tu acceso al portal está inactivo.')
                    return redirect('client_portal:dashboard')
                
                if not portal_access.has_feature(feature_code):
                    messages.warning(
                        request,
                        'No tienes acceso a esta característica. '
                        'Contacta a tu consultor para más información.'
                    )
                    return redirect('client_portal:dashboard')
                
                return view_func(request, *args, **kwargs)
                
            except ClientPortalAccess.DoesNotExist:
                messages.error(request, 'No tienes acceso al portal.')
                return redirect('login')
                
        return _wrapped_view
    return decorator 