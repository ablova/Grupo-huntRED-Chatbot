from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings

class PermissionMiddleware(MiddlewareMixin):
    """
    Middleware para verificar permisos de usuario.
    """
    def process_request(self, request):
        if not hasattr(request, 'user'):
            return None

        if not request.user.is_authenticated:
            return None

        # URLs que no requieren verificación de permisos
        exempt_urls = [
            reverse('login'),
            reverse('logout'),
            reverse('signup'),
            reverse('forgot_password'),
            reverse('reset_password', args=['token']),
            reverse('document_verification'),
        ]

        if request.path in exempt_urls:
            return None

        # Verificar si el usuario está activo
        if request.user.status != 'ACTIVE':
            messages.error(request, 'Tu cuenta está inactiva o pendiente de aprobación.')
            return redirect('dashboard')

        # Verificar si el usuario está verificado (excluir superusuarios)
        if not request.user.is_superuser and request.user.verification_status != 'VERIFIED':
            messages.error(request, 'Tu cuenta aún no está verificada.')
            return redirect('document_verification')

        # Verificar permisos específicos según la URL
        required_permissions = {
            'admin:estadisticas:interacciones': ['ACCESS_STATS'],
            'dashboard': ['ACCESS_DASHBOARD'],
            'applications': ['MANAGE_APPLICATIONS'],
            'application_detail': ['VIEW_APPLICATION'],
            'update_application': ['UPDATE_APPLICATION'],
            'delete_application': ['DELETE_APPLICATION'],
            'applications:notes': ['MANAGE_NOTES'],
            'applications:attachments': ['MANAGE_ATTACHMENTS'],
            'applications:tasks': ['MANAGE_TASKS'],
            'applications:reminders': ['MANAGE_REMINDERS'],
            'applications:events': ['MANAGE_EVENTS'],
            'applications:documents': ['MANAGE_DOCUMENTS'],
            'applications:links': ['MANAGE_LINKS'],
            'applications:comments': ['MANAGE_COMMENTS'],
            'applications:ratings': ['MANAGE_RATINGS'],
            'applications:tags': ['MANAGE_TAGS'],
            'applications:labels': ['MANAGE_LABELS'],
            'applications:status': ['MANAGE_STATUS'],
            'applications:priority': ['MANAGE_PRIORITY'],
            'applications:type': ['MANAGE_TYPE'],
            'applications:stage': ['MANAGE_STAGE'],
            'applications:source': ['MANAGE_SOURCE'],
            'applications:medium': ['MANAGE_MEDIUM'],
            'applications:campaign': ['MANAGE_CAMPAIGN'],
            'applications:content': ['MANAGE_CONTENT'],
            'applications:form': ['MANAGE_FORM'],
            'applications:field': ['MANAGE_FIELD'],
            'applications:option': ['MANAGE_OPTION'],
            'applications:rule': ['MANAGE_RULE'],
            'applications:action': ['MANAGE_ACTION'],
            'applications:condition': ['MANAGE_CONDITION'],
            'applications:trigger': ['MANAGE_TRIGGER'],
            'applications:workflow': ['MANAGE_WORKFLOW'],
            'applications:step': ['MANAGE_STEP'],
            'applications:transition': ['MANAGE_TRANSITION'],
            'applications:state': ['MANAGE_STATE'],
            'applications:event_type': ['MANAGE_EVENT_TYPE'],
            'applications:event_status': ['MANAGE_EVENT_STATUS'],
            'applications:event_priority': ['MANAGE_EVENT_PRIORITY'],
        }

        # Obtener el nombre de la vista actual
        if not hasattr(request, 'resolver_match') or request.resolver_match is None:
            return None
            
        view_name = request.resolver_match.view_name

        # Verificar si la vista requiere permisos específicos
        if view_name in required_permissions:
            for permission in required_permissions[view_name]:
                if not request.user.has_permission(permission):
                    messages.error(request, f'No tienes el permiso requerido: {permission}')
                    return redirect('dashboard')

        return None

class RoleMiddleware(MiddlewareMixin):
    """
    Middleware para verificar roles de usuario.
    """
    def process_request(self, request):
        if not hasattr(request, 'user'):
            return None

        if not request.user.is_authenticated:
            return None

        # URLs que no requieren verificación de rol
        exempt_urls = [
            reverse('login'),
            reverse('logout'),
            reverse('signup'),
            reverse('forgot_password'),
            reverse('reset_password', args=['token']),
            reverse('document_verification'),
        ]

        if request.path in exempt_urls:
            return None

        # Verificar rol específico según la URL
        required_roles = {
            'admin:estadisticas:interacciones': ['SUPER_ADMIN'],
            'finalize_candidates': ['BU_COMPLETE', 'SUPER_ADMIN'],
            'submit_application': ['BU_DIVISION', 'BU_COMPLETE', 'SUPER_ADMIN'],
        }

        # Obtener el nombre de la vista actual
        if not hasattr(request, 'resolver_match') or request.resolver_match is None:
            return None
            
        view_name = request.resolver_match.view_name

        # Verificar si la vista requiere un rol específico
        if view_name in required_roles:
            if request.user.role not in required_roles[view_name]:
                messages.error(request, 'No tienes el rol requerido para acceder a esta página.')
                return redirect('dashboard')

        return None

class BusinessUnitMiddleware(MiddlewareMixin):
    """
    Middleware para verificar acceso a unidades de negocio.
    """
    def process_request(self, request):
        if not hasattr(request, 'user'):
            return None

        if not request.user.is_authenticated:
            return None

        # URLs que no requieren verificación de unidad de negocio
        exempt_urls = [
            reverse('login'),
            reverse('logout'),
            reverse('signup'),
            reverse('forgot_password'),
            reverse('reset_password', args=['token']),
            reverse('document_verification'),
        ]

        if request.path in exempt_urls:
            return None

        # Obtener el nombre de la vista actual
        if not hasattr(request, 'resolver_match') or request.resolver_match is None:
            return None
            
        view_name = request.resolver_match.view_name

        # Verificar acceso a unidades de negocio específicas
        if 'business_unit' in request.resolver_match.kwargs:
            bu_name = request.resolver_match.kwargs['business_unit']
            if not request.user.has_bu_access(bu_name):
                messages.error(request, f'No tienes acceso a la unidad de negocio {bu_name}.')
                return redirect('dashboard')

        return None

class DivisionMiddleware(MiddlewareMixin):
    """
    Middleware para verificar acceso a divisiones.
    """
    def process_request(self, request):
        if not hasattr(request, 'user'):
            return None

        if not request.user.is_authenticated:
            return None

        # URLs que no requieren verificación de división
        exempt_urls = [
            reverse('login'),
            reverse('logout'),
            reverse('signup'),
            reverse('forgot_password'),
            reverse('reset_password', args=['token']),
            reverse('document_verification'),
        ]

        if request.path in exempt_urls:
            return None

        # Obtener el nombre de la vista actual
        if not hasattr(request, 'resolver_match') or request.resolver_match is None:
            return None
            
        view_name = request.resolver_match.view_name

        # Verificar acceso a divisiones específicas
        if 'division' in request.resolver_match.kwargs:
            division_name = request.resolver_match.kwargs['division']
            if not request.user.has_division_access(division_name):
                messages.error(request, f'No tienes acceso a la división {division_name}.')
                return redirect('dashboard')

        return None
