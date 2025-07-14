"""
Utilidades de autenticación y autorización para el sistema ATS.
Proporciona funciones para verificar permisos de usuarios en unidades de negocio.
"""

from django.contrib.auth import get_user_model
from app.models import BusinessUnit
import logging

logger = logging.getLogger(__name__)

def has_bu_permission(user, business_unit_id):
    """
    Verifica si el usuario tiene permisos para acceder a una unidad de negocio específica.
    
    Args:
        user: Usuario a verificar
        business_unit_id: ID de la unidad de negocio
        
    Returns:
        bool: True si tiene permisos, False en caso contrario
    """
    # Super admin tiene acceso a todo
    if user.is_superuser:
        return True
    
    # Verificar si el usuario tiene rol de super admin
    if hasattr(user, 'role') and user.role == 'super_admin':
        return True
    
    # Verificar si el usuario pertenece a esa unidad de negocio
    if hasattr(user, 'business_unit') and user.business_unit:
        return str(user.business_unit.id) == str(business_unit_id)
    
    # Verificar si el usuario es staff y tiene acceso general
    if user.is_staff:
        return True
    
    return False

def get_user_business_units(user):
    """
    Obtiene las unidades de negocio a las que tiene acceso el usuario.
    
    Args:
        user: Usuario del cual obtener las unidades de negocio
        
    Returns:
        QuerySet: Unidades de negocio a las que tiene acceso
    """
    # Super admin tiene acceso a todas las unidades
    if user.is_superuser:
        return BusinessUnit.objects.all()
    
    # Verificar si el usuario tiene rol de super admin
    if hasattr(user, 'role') and user.role == 'super_admin':
        return BusinessUnit.objects.all()
    
    # Si el usuario tiene una unidad de negocio específica
    if hasattr(user, 'business_unit') and user.business_unit:
        return BusinessUnit.objects.filter(id=user.business_unit.id)
    
    # Si el usuario es staff, puede tener acceso a múltiples unidades
    if user.is_staff:
        # Por ahora, retornar todas las unidades activas
        return BusinessUnit.objects.filter(active=True)
    
    # Usuario sin permisos
    return BusinessUnit.objects.none() 