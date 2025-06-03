from rest_framework import permissions

class IsIntegrationOwner(permissions.BasePermission):
    """
    Permiso personalizado para permitir solo a los propietarios de una integración
    acceder a ella.
    """
    def has_object_permission(self, request, view, obj):
        # Los propietarios pueden realizar cualquier acción
        return obj.user == request.user

class IsIntegrationConfigOwner(permissions.BasePermission):
    """
    Permiso personalizado para permitir solo a los propietarios de una configuración
    acceder a ella.
    """
    def has_object_permission(self, request, view, obj):
        # Los propietarios pueden realizar cualquier acción
        return obj.integration.user == request.user

class IsIntegrationLogOwner(permissions.BasePermission):
    """
    Permiso personalizado para permitir solo a los propietarios de un log
    acceder a él.
    """
    def has_object_permission(self, request, view, obj):
        # Los propietarios pueden realizar cualquier acción
        return obj.integration.user == request.user 