# Ubicación del archivo: /home/pablo/app/com/utils/admin_registry.py
"""
Módulo central de registro de administradores de Django.

Este módulo importa y registra todas las clases de administración de Django
para mantener una configuración centralizada y modular.
"""

# Importing shared admin modules
from django.contrib import admin

# Importing specific admin modules from each app
from app.ats.utils.admin_base import BaseModelAdmin, TokenMaskingMixin
from app.ats.utils.admin_business_unit import BusinessUnitAdminConfig
from app.ats.utils.admin_utils import register_admin_configurations

# Función para inicializar todas las configuraciones de admin
def init_admin_configurations():
    """Inicializando todas las configuraciones de administración del sistema"""
    
    # Configuración del sitio admin
    admin.site.site_header = "Administración de Grupo huntRED®"
    admin.site.site_title = "Portal Administrativo"
    admin.site.index_title = "Bienvenido al Panel de Administración"
    
    # Registrando configuraciones de admin desde apps específicas
    register_admin_configurations()
    
    # Configurando componentes adicionales del admin
    # Como menu, permisos, etc.

# Aplicar configuraciones cuando se importa este módulo
init_admin_configurations()
