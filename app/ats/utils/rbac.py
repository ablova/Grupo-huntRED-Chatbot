"""
Sistema centralizado de control de acceso basado en roles (RBAC) con caché Redis.
Este módulo proporciona decoradores y utilidades para gestionar permisos en toda la aplicación.
"""
from functools import wraps
from django.core.cache import cache
from django.conf import settings
from django.http import HttpResponseForbidden, HttpResponseBadRequest, HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import gettext as _
import logging
import json
from app.models import BusinessUnit

logger = logging.getLogger(__name__)

class RBAC:
    """Sistema de control de acceso basado en roles con caché Redis para optimizar rendimiento."""
    
    # Definición de roles y sus permisos
    ROLES = {
        'super_admin': {'*': ['*']},  # Acceso total
        'consultant_bu_complete': {},  # Acceso a todos los datos de su BU
        'consultant_bu_division': {}   # Acceso a división específica de BU
    }
    
    CACHE_TTL = getattr(settings, 'RBAC_CACHE_TTL', 3600)  # 1 hora por defecto
    
    @classmethod
    def requires_permission(cls, resource, action, bu_required=True, redirect_url=None):
        """
        Decorador para verificar permisos en vistas y APIs.
        
        Args:
            resource: Recurso al que se desea acceder (ej: 'vacante', 'person')
            action: Acción a realizar (ej: 'view', 'edit', 'delete')
            bu_required: Si True, se requiere un BU_id en la solicitud
            redirect_url: URL a la que redirigir si no tiene permisos (None = usar forbidden response)
            
        Returns:
            Decorador que verifica permisos antes de ejecutar la vista
        """
        def decorator(view_func):
            @wraps(view_func)
            async def wrapped_view(request, *args, **kwargs):
                user = request.user
                
                # Verificar autenticación
                if not user.is_authenticated:
                    if redirect_url:
                        return HttpResponseRedirect(reverse(redirect_url))
                    return cls._unauthorized_response()
                
                # Determinar BU del contexto
                bu_id = kwargs.get('bu_id') or request.GET.get('bu_id')
                
                # Si se requiere BU y no se proporciona, error
                if bu_required and not bu_id:
                    return cls._missing_bu_response()
                
                # Verificar permisos (con caché)
                has_permission = await cls.check_permission(user.id, resource, action, bu_id)
                
                if not has_permission:
                    logger.warning(f"Permission denied: User {user.id} - {resource}.{action} - BU: {bu_id}")
                    if redirect_url:
                        return HttpResponseRedirect(reverse(redirect_url))
                    return cls._forbidden_response()
                
                # Loggear acceso exitoso en nivel DEBUG para no saturar logs
                logger.debug(f"Access granted: User {user.id} - {resource}.{action} - BU: {bu_id}")
                
                # Proceder con la vista si tiene permisos
                return await view_func(request, *args, **kwargs)
            return wrapped_view
        return decorator
    
    @classmethod
    async def check_permission(cls, user_id, resource, action, bu_id=None):
        """
        Verifica si el usuario tiene permisos para el recurso y acción.
        Utiliza caché Redis para evitar consultas repetitivas a la base de datos.
        
        Args:
            user_id: ID del usuario
            resource: Recurso (ej: 'vacante', 'person')
            action: Acción (ej: 'view', 'edit', 'delete')
            bu_id: ID de la business unit (opcional)
            
        Returns:
            bool: True si tiene permiso, False en caso contrario
        """
        # Verificar en caché primero
        cache_key = f"rbac:permission:{user_id}:{resource}:{action}:{bu_id}"
        cached_result = await cache.aget(cache_key)
        
        if cached_result is not None:
            return cached_result == "1"
        
        # Verificar permisos en la base de datos
        has_permission = await cls._check_db_permission(user_id, resource, action, bu_id)
        
        # Guardar en caché (con TTL para evitar permisos obsoletos)
        await cache.aset(cache_key, "1" if has_permission else "0", timeout=cls.CACHE_TTL)
        
        return has_permission
    
    @classmethod
    async def _check_db_permission(cls, user_id, resource, action, bu_id=None):
        """
        Verifica permisos consultando la base de datos.
        Este método debería ser implementado según el esquema de permisos específico.
        
        Args:
            user_id: ID del usuario
            resource: Recurso 
            action: Acción
            bu_id: ID de la business unit (opcional)
            
        Returns:
            bool: True si tiene permiso, False en caso contrario
        """
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        try:
            user = await User.objects.aget(id=user_id)
            
            # Super admin tiene todos los permisos
            if user.is_superuser:
                return True
                
            # Si el usuario es staff, verificar permisos específicos
            if user.is_staff:
                # Verificar rol del usuario
                user_role = await cls._get_user_role(user)
                
                # Super admin tiene acceso a todo
                if user_role == 'super_admin':
                    return True
                
                # Para consultant_bu_complete, verificar que el BU coincida
                if user_role == 'consultant_bu_complete' and bu_id:
                    user_bus = await cls._get_user_business_units(user)
                    return str(bu_id) in [str(b.id) for b in user_bus]
                
                # Para consultant_bu_division, verificar BU y permiso específico
                if user_role == 'consultant_bu_division' and bu_id:
                    # Verificar combinación de BU y permiso
                    return await cls._check_division_permission(user, bu_id, resource, action)
            
            return False
        except Exception as e:
            logger.error(f"Error checking permissions: {str(e)}")
            return False
    
    @staticmethod
    async def _get_user_role(user):
        """Obtiene el rol del usuario."""
        # Esta implementación debería adaptarse al modelo de datos
        # Por ahora asumimos que el rol está en user.profile.role
        if hasattr(user, 'profile') and hasattr(user.profile, 'role'):
            return user.profile.role
        return None
    
    @staticmethod
    async def _get_user_business_units(user):
        """Obtiene las business units a las que tiene acceso el usuario."""
        # Esta implementación debe adaptarse al modelo de datos específico
        if hasattr(user, 'profile') and hasattr(user.profile, 'business_units'):
            return await user.profile.business_units.all()
        return []
    
    @staticmethod
    async def _check_division_permission(user, bu_id, resource, action):
        """Verifica permisos específicos de división para un BU."""
        # Implementar lógica específica según el modelo de datos
        return False
    
    @staticmethod
    def _unauthorized_response():
        """Respuesta para usuarios no autenticados."""
        return HttpResponseForbidden(_("Debes iniciar sesión para acceder a este recurso."))
    
    @staticmethod
    def _missing_bu_response():
        """Respuesta para solicitudes sin BU cuando es requerido."""
        return HttpResponseBadRequest(_("Se requiere especificar una unidad de negocio."))
    
    @staticmethod
    def _forbidden_response():
        """Respuesta para usuarios sin permisos suficientes."""
        return HttpResponseForbidden(_("No tienes permisos suficientes para acceder a este recurso."))
    
    @classmethod
    async def invalidate_permission_cache(cls, user_id, resource=None, action=None, bu_id=None):
        """
        Invalida la caché de permisos para un usuario.
        
        Args:
            user_id: ID del usuario
            resource: Recurso específico (None para todos)
            action: Acción específica (None para todas)
            bu_id: ID de business unit específica (None para todas)
        """
        if not resource and not action and not bu_id:
            # Invalidar todas las cachés del usuario
            pattern = f"rbac:permission:{user_id}:*"
            keys = await cache.keys(pattern)
            for key in keys:
                await cache.adelete(key)
        else:
            # Invalidar caché específica
            cache_key = f"rbac:permission:{user_id}"
            if resource:
                cache_key += f":{resource}"
                if action:
                    cache_key += f":{action}"
                    if bu_id:
                        cache_key += f":{bu_id}"
                        await cache.adelete(cache_key)
                    else:
                        pattern = f"{cache_key}:*"
                        keys = await cache.keys(pattern)
                        for key in keys:
                            await cache.adelete(key)
                else:
                    pattern = f"{cache_key}:*"
                    keys = await cache.keys(pattern)
                    for key in keys:
                        await cache.adelete(key)
            else:
                pattern = f"{cache_key}:*"
                keys = await cache.keys(pattern)
                for key in keys:
                    await cache.adelete(key)

# Funciones de conveniencia para importación directa
async def check_permission(user_id, resource, action, bu_id=None):
    """
    Función de conveniencia para verificar permisos.
    
    Args:
        user_id: ID del usuario
        resource: Recurso (ej: 'vacante', 'person')
        action: Acción (ej: 'view', 'edit', 'delete')
        bu_id: ID de la business unit (opcional)
        
    Returns:
        bool: True si tiene permiso, False en caso contrario
    """
    return await RBAC.check_permission(user_id, resource, action, bu_id)

def has_organization_access(user, organization_id=None):
    """
    Verifica si el usuario tiene acceso a una organización específica.
    
    Args:
        user: Usuario a verificar
        organization_id: ID de la organización (opcional, si no se proporciona verifica acceso general)
        
    Returns:
        bool: True si tiene acceso, False en caso contrario
    """
    # Super admin tiene acceso a todo
    if user.is_superuser:
        return True
    
    # Verificar si el usuario tiene rol de super admin
    if hasattr(user, 'role') and user.role == 'super_admin':
        return True
    
    # Si se especifica una organización, verificar acceso específico
    if organization_id:
        # Verificar si el usuario pertenece a esa organización
        if hasattr(user, 'business_unit') and user.business_unit:
            return str(user.business_unit.id) == str(organization_id)
        return False
    
    # Si no se especifica organización, verificar si tiene acceso a alguna
    return hasattr(user, 'business_unit') and user.business_unit is not None
