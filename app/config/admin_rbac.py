# Ubicación del archivo: /home/pablo/app/config/admin_rbac.py
"""
Sistema de control de acceso basado en roles (RBAC) para administración.

Este módulo implementa el sistema RBAC especificado en las reglas globales de
Grupo huntRED®, con tres roles principales: Super Admin, Consultant (BU Complete),
y Consultant (BU Division).
"""

import functools
import logging
from django.contrib.auth.models import User, Group, Permission
from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.conf import settings
from django.db.models import Q

# Importaciones para el futuro soporte de consultas optimizadas
from app.models import BusinessUnit, Division

logger = logging.getLogger('admin_rbac')

# Definición de roles según las reglas globales
SUPER_ADMIN_ROLE = 'super_admin'
BU_COMPLETE_ROLE = 'bu_complete'
BU_DIVISION_ROLE = 'bu_division'

# Mapeo de roles a grupos de Django
ROLE_GROUP_MAPPING = {
    SUPER_ADMIN_ROLE: 'Super Administradores',
    BU_COMPLETE_ROLE: 'Consultores BU Completo',
    BU_DIVISION_ROLE: 'Consultores BU División'
}

# Definición de permisos por rol
ROLE_PERMISSIONS = {
    SUPER_ADMIN_ROLE: {
        'app': ['*'],  # Todos los permisos
        'auth': ['*'],  # Todos los permisos de administración de usuarios
        'admin': ['*']  # Todos los permisos administrativos
    },
    BU_COMPLETE_ROLE: {
        'app': ['view_*', 'add_*', 'change_*', 'delete_*'],  # Todos los permisos para su BU
        'auth': ['view_user'],  # Solo ver usuarios
        'admin': ['view_logentry']  # Solo ver logs
    },
    BU_DIVISION_ROLE: {
        'app': ['view_*', 'add_*', 'change_*'],  # Permisos limitados para su división
        'auth': [],  # Sin permisos de usuarios
        'admin': []  # Sin permisos administrativos
    }
}

class RBACModelMixin:
    """
    Mixin para implementar restricciones RBAC a nivel de modelo.
    
    Este mixin filtra los queryset según el rol y BU/División del usuario.
    """
    
    def get_queryset(self, request):
        """Filtrando queryset según rol y BU/División del usuario."""
        queryset = super().get_queryset(request)
        
        # Super Admin no tiene restricciones
        if is_super_admin(request.user):
            return queryset
            
        # Verificando roles con acceso restringido
        user_role = get_user_role(request.user)
        
        if user_role == BU_COMPLETE_ROLE:
            # Acceso al BU completo asignado al usuario
            business_units = get_user_business_units(request.user)
            if not business_units:
                return queryset.none()  # Sin BUs asignadas, no muestra nada
                
            # Filtrando por BU si el modelo tiene campo business_unit
            if hasattr(self.model, 'business_unit'):
                return queryset.filter(business_unit__in=business_units)
                
        elif user_role == BU_DIVISION_ROLE:
            # Acceso a divisiones específicas
            divisions = get_user_divisions(request.user)
            if not divisions:
                return queryset.none()  # Sin divisiones asignadas, no muestra nada
                
            # Filtrando según la estructura del modelo
            if hasattr(self.model, 'division'):
                return queryset.filter(division__in=divisions)
            elif hasattr(self.model, 'business_unit'):
                # Obteniendo BUs asociadas a las divisiones
                business_units = BusinessUnit.objects.filter(division__in=divisions).distinct()
                return queryset.filter(business_unit__in=business_units)
                
        # Valores predeterminados si no hay filtros específicos
        if hasattr(self.model, 'business_unit') or hasattr(self.model, 'division'):
            return queryset.none()  # Por defecto, no mostrar nada si requiere filtros
            
        return queryset
    
    def has_view_permission(self, request, obj=None):
        """Verificando permiso de vista según RBAC."""
        base_permission = super().has_view_permission(request, obj)
        if not base_permission:
            return False
            
        # Verificando acceso al objeto según RBAC
        return self._has_object_permission(request, obj)
    
    def has_change_permission(self, request, obj=None):
        """Verificando permiso de modificación según RBAC."""
        base_permission = super().has_change_permission(request, obj)
        if not base_permission:
            return False
            
        # Super Admin siempre tiene permiso
        if is_super_admin(request.user):
            return True
            
        # Verificando rol y acceso al objeto
        user_role = get_user_role(request.user)
        
        # BU Division no puede modificar ciertos objetos
        if user_role == BU_DIVISION_ROLE and obj and self._is_restricted_for_division(obj):
            return False
            
        return self._has_object_permission(request, obj)
    
    def has_delete_permission(self, request, obj=None):
        """Verificando permiso de eliminación según RBAC."""
        base_permission = super().has_delete_permission(request, obj)
        if not base_permission:
            return False
            
        # Super Admin siempre tiene permiso
        if is_super_admin(request.user):
            return True
            
        # Verificando rol y acceso al objeto
        user_role = get_user_role(request.user)
        
        # BU Division no puede eliminar
        if user_role == BU_DIVISION_ROLE:
            return False
            
        return self._has_object_permission(request, obj)
    
    def _has_object_permission(self, request, obj):
        """Verificando si el usuario tiene acceso al objeto específico."""
        if obj is None:
            return True  # Sin objeto, verificamos a nivel de queryset
            
        # Super Admin siempre tiene acceso
        if is_super_admin(request.user):
            return True
            
        user_role = get_user_role(request.user)
        
        if user_role == BU_COMPLETE_ROLE:
            # Verificando acceso por BU
            if hasattr(obj, 'business_unit'):
                user_bus = get_user_business_units(request.user)
                return obj.business_unit in user_bus
                
        elif user_role == BU_DIVISION_ROLE:
            # Verificando acceso por Division
            if hasattr(obj, 'division'):
                user_divisions = get_user_divisions(request.user)
                return obj.division in user_divisions
            elif hasattr(obj, 'business_unit') and hasattr(obj.business_unit, 'division'):
                user_divisions = get_user_divisions(request.user)
                return obj.business_unit.division in user_divisions
                
        # Por defecto, denegar acceso a objetos que requieren filtro
        if hasattr(obj, 'business_unit') or hasattr(obj, 'division'):
            return False
            
        return True
    
    def _is_restricted_for_division(self, obj):
        """Verificando si el objeto está restringido para consultores de división."""
        # Lista de atributos restringidos
        restricted_attributes = ['is_global', 'is_template', 'is_default', 'is_system']
        
        # Verificando atributos restringidos
        for attr in restricted_attributes:
            if hasattr(obj, attr) and getattr(obj, attr, False):
                return True
                
        # Verificando si es un objeto de configuración
        restricted_models = ['Configuracion', 'ConfiguracionBU', 'ApiConfig', 'GptApi']
        if obj.__class__.__name__ in restricted_models:
            return True
            
        return False

def is_super_admin(user):
    """
    Verifica si un usuario tiene el rol de Super Admin.
    
    Args:
        user: Usuario de Django a verificar
        
    Returns:
        bool: True si el usuario es Super Admin, False en caso contrario
    """
    if user.is_superuser:
        return True
        
    return user.groups.filter(name=ROLE_GROUP_MAPPING[SUPER_ADMIN_ROLE]).exists()

def get_user_role(user):
    """
    Obtiene el rol principal del usuario.
    
    Args:
        user: Usuario de Django
        
    Returns:
        str: Código del rol (SUPER_ADMIN_ROLE, BU_COMPLETE_ROLE, BU_DIVISION_ROLE)
             o None si no tiene rol asignado
    """
    if is_super_admin(user):
        return SUPER_ADMIN_ROLE
        
    # Verificando otros roles
    for role, group_name in ROLE_GROUP_MAPPING.items():
        if user.groups.filter(name=group_name).exists():
            return role
            
    return None

def get_user_business_units(user):
    """
    Obtiene las Business Units asignadas al usuario.
    
    Args:
        user: Usuario de Django
        
    Returns:
        QuerySet: Business Units asignadas al usuario
    """
    # Implementación específica según el modelo de datos
    # Asumiendo que hay una relación entre User y BusinessUnit
    if hasattr(user, 'business_units'):
        return user.business_units.all()
        
    # Fallback: intentar buscar en ConfiguracionBU
    from app.models import ConfiguracionBU
    if hasattr(ConfiguracionBU, 'user'):
        configs = ConfiguracionBU.objects.filter(user=user)
        if configs.exists():
            return BusinessUnit.objects.filter(
                id__in=configs.values_list('business_unit_id', flat=True)
            )
            
    # Última opción: verificar permisos específicos
    if user.has_perm('app.access_all_business_units'):
        return BusinessUnit.objects.all()
        
    return BusinessUnit.objects.none()

def get_user_divisions(user):
    """
    Obtiene las Divisiones asignadas al usuario.
    
    Args:
        user: Usuario de Django
        
    Returns:
        QuerySet: Divisiones asignadas al usuario
    """
    # Implementación específica según el modelo de datos
    # Asumiendo que hay una relación entre User y Division
    if hasattr(user, 'divisions'):
        return user.divisions.all()
        
    # Fallback: intentar buscar en configuraciones
    from app.models import ConfiguracionBU
    if hasattr(ConfiguracionBU, 'user') and hasattr(ConfiguracionBU, 'division'):
        configs = ConfiguracionBU.objects.filter(user=user)
        if configs.exists():
            return Division.objects.filter(
                id__in=configs.values_list('division_id', flat=True)
            )
            
    # Intentar obtener divisiones a través de BUs asignadas
    business_units = get_user_business_units(user)
    if business_units.exists():
        return Division.objects.filter(business_unit__in=business_units)
        
    return Division.objects.none()

def admin_role_required(role=SUPER_ADMIN_ROLE, redirect_url=None):
    """
    Decorador para restringir acceso a vistas según rol.
    
    Args:
        role (str): Rol mínimo requerido (SUPER_ADMIN_ROLE, BU_COMPLETE_ROLE, BU_DIVISION_ROLE)
        redirect_url (str): URL a redireccionar si no tiene permiso (opcional)
        
    Returns:
        function: Decorador configurado
    """
    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs):
            user_role = get_user_role(request.user)
            
            # Verificando si tiene al menos el rol requerido
            has_permission = False
            
            if user_role == SUPER_ADMIN_ROLE:
                has_permission = True
            elif user_role == BU_COMPLETE_ROLE:
                has_permission = role in [BU_COMPLETE_ROLE, BU_DIVISION_ROLE]
            elif user_role == BU_DIVISION_ROLE:
                has_permission = role == BU_DIVISION_ROLE
                
            if has_permission:
                return view_func(request, *args, **kwargs)
                
            # No tiene permiso, redireccionando
            messages.error(request, _("No tienes permiso para acceder a esta página."))
            
            if redirect_url:
                return redirect(redirect_url)
            else:
                return redirect(reverse('admin:index'))
                
        return wrapper
    return decorator

def setup_rbac_groups():
    """
    Configura los grupos y permisos iniciales para el sistema RBAC.
    
    Esta función debe ser ejecutada durante la migración inicial o
    configuración del sistema.
    """
    # Creando grupos
    for role, group_name in ROLE_GROUP_MAPPING.items():
        group, created = Group.objects.get_or_create(name=group_name)
        
        if created:
            logger.info(f"Grupo {group_name} creado para rol {role}")
            
        # Asignando permisos
        if role in ROLE_PERMISSIONS:
            assign_group_permissions(group, ROLE_PERMISSIONS[role])

def assign_group_permissions(group, permissions_config):
    """
    Asigna permisos a un grupo según la configuración.
    
    Args:
        group: Objeto Group de Django
        permissions_config: Diccionario con configuración de permisos
    """
    from django.contrib.contenttypes.models import ContentType
    
    # Limpiando permisos existentes
    group.permissions.clear()
    
    # Procesando cada app y sus permisos
    for app_label, codenames in permissions_config.items():
        # Comodín para todos los permisos de la app
        if '*' in codenames:
            content_types = ContentType.objects.filter(app_label=app_label)
            for ct in content_types:
                permissions = Permission.objects.filter(content_type=ct)
                group.permissions.add(*permissions)
        else:
            # Procesando patrones específicos
            for pattern in codenames:
                if pattern.endswith('_*'):
                    # Patrón para tipo de permiso (view_*, add_*, etc.)
                    prefix = pattern[:-1]  # Eliminando el asterisco
                    permissions = Permission.objects.filter(
                        content_type__app_label=app_label,
                        codename__startswith=prefix
                    )
                    group.permissions.add(*permissions)
                else:
                    # Permiso específico
                    try:
                        permission = Permission.objects.get(
                            content_type__app_label=app_label,
                            codename=pattern
                        )
                        group.permissions.add(permission)
                    except Permission.DoesNotExist:
                        logger.warning(f"Permiso {app_label}.{pattern} no encontrado")

class RBACAdminSite(admin.AdminSite):
    """
    AdminSite personalizado con soporte RBAC.
    
    Esta clase extiende el AdminSite estándar de Django para
    implementar restricciones de acceso basadas en roles.
    """
    
    def has_permission(self, request):
        """Verifica si el usuario tiene permiso para acceder al admin."""
        # Verificación básica de Django
        if not super().has_permission(request):
            return False
            
        # Verificando si tiene un rol asignado
        return get_user_role(request.user) is not None
    
    def each_context(self, request):
        """Añade contexto adicional a todas las plantillas admin."""
        context = super().each_context(request)
        
        # Añadiendo información de rol
        if hasattr(request, 'user') and request.user.is_authenticated:
            context['user_role'] = get_user_role(request.user)
            context['user_business_units'] = get_user_business_units(request.user)
            context['user_divisions'] = get_user_divisions(request.user)
            
        return context
    
    def get_app_list(self, request):
        """Filtra la lista de aplicaciones según el rol del usuario."""
        app_list = super().get_app_list(request)
        
        # Super Admin ve todo
        if is_super_admin(request.user):
            return app_list
            
        # Otros roles ven apps filtradas
        user_role = get_user_role(request.user)
        if not user_role:
            return []
            
        # Filtrando apps según rol
        filtered_app_list = []
        for app in app_list:
            # Verificando si debe mostrar la app completa
            show_app = True
            
            # Aplicaciones restringidas por rol
            restricted_apps = {
                BU_COMPLETE_ROLE: ['auth'],
                BU_DIVISION_ROLE: ['auth', 'admin', 'sites']
            }
            
            if user_role in restricted_apps and app['app_label'] in restricted_apps[user_role]:
                show_app = False
                
            if show_app:
                # Filtrando modelos dentro de la app
                filtered_models = []
                for model in app['models']:
                    # Restricciones específicas por modelo y rol
                    show_model = True
                    
                    # Modelos restringidos por rol
                    bu_complete_restricted = ['User', 'Group', 'Permission', 'ContentType', 'ApiConfig']
                    bu_division_restricted = bu_complete_restricted + ['Configuracion', 'ConfiguracionBU', 'BusinessUnit']
                    
                    if user_role == BU_COMPLETE_ROLE and model['object_name'] in bu_complete_restricted:
                        show_model = False
                    elif user_role == BU_DIVISION_ROLE and model['object_name'] in bu_division_restricted:
                        show_model = False
                        
                    if show_model:
                        filtered_models.append(model)
                
                if filtered_models:
                    app_copy = app.copy()
                    app_copy['models'] = filtered_models
                    filtered_app_list.append(app_copy)
        
        return filtered_app_list
        
# Creando instancia del AdminSite RBAC
rbac_admin_site = RBACAdminSite(name='rbac_admin')
