# Ubicación del archivo: /home/pablo/app/config/admin_registry.py
"""
Registrador centralizado de configuraciones de administración de Django.

Este módulo implementa el registro centralizado de todos los administradores de Django
del sistema, siguiendo las reglas globales de Grupo huntRED®.
"""

from django.contrib import admin
import importlib
import logging

# Importando clases base y mixins
from .admin_base import BaseModelAdmin, TokenMaskingMixin, ReadOnlyAdminMixin
from .admin_cache import CachedAdminMixin, OptimizedQuerysetMixin, setup_cache_signals
from .admin_rbac import RBACModelMixin, setup_rbac_groups, rbac_admin_site

# Importando administradores desde diferentes módulos
from .admin_core import (
    # Core models
    PersonAdmin, 
    ApplicationAdmin, 
    VacanteAdmin, 
    BusinessUnitAdmin,
    
    # Configuration models
    ConfiguracionAdmin,
    
    # Gamification models
    GamificationProfileAdmin,
    GamificationAchievementAdmin, 
    GamificationBadgeAdmin, 
    GamificationEventAdmin,
    
    # Workflow models
    WorkflowStageAdmin,
    ChatStateAdmin
)

# Importando administradores de scraping
from .admin_scraping import (
    DominioScrapingAdmin,
    RegistroScrapingAdmin,
    ReporteScrapingAdmin
)

# Importando administradores de pricing
from .admin_pricing import (
    PricingBaselineAdmin,
    AddonsAdmin,
    CouponsAdmin,
    PaymentMilestonesAdmin,
    PricingSimulatorAdmin
)

# Importando modelos desde app.models
from app.models import (
    # Core models
    Person, 
    Application, 
    Vacante, 
    BusinessUnit,
    
    # Configuration models
    Configuracion,
    
    # Gamification models
    EnhancedNetworkGamificationProfile,
    GamificationAchievement, 
    GamificationBadge, 
    GamificationEvent,
    
    # Workflow models
    WorkflowStage,
    ChatState,
    
    # Scraping models
    DominioScraping,
    RegistroScraping,
    ReporteScraping
)

logger = logging.getLogger(__name__)

# Mapeo de modelos a sus clases de administración correspondientes
ADMIN_CLASS_MAPPING = {
    # Core models
    Person: PersonAdmin,
    Application: ApplicationAdmin,
    Vacante: VacanteAdmin,
    BusinessUnit: BusinessUnitAdmin,
    
    # Configuration models
    Configuracion: ConfiguracionAdmin,
    
    # Gamification models
    EnhancedNetworkGamificationProfile: GamificationProfileAdmin,
    GamificationAchievement: GamificationAchievementAdmin,
    GamificationBadge: GamificationBadgeAdmin,
    GamificationEvent: GamificationEventAdmin,
    
    # Workflow models
    WorkflowStage: WorkflowStageAdmin,
    ChatState: ChatStateAdmin,
    
    # Scraping models
    DominioScraping: DominioScrapingAdmin,
    RegistroScraping: RegistroScrapingAdmin,
    ReporteScraping: ReporteScrapingAdmin
}

# Módulos de administración específicos que podrían proporcionar sus propios registros
ADMIN_MODULES = [
    'app.com.notifications.admin',
    'app.com.pagos.admin',
    'app.com.proposals.admin',
    'app.com.publish.admin',
    'app.sexsi.admin'
]

def _register_model_admin(model, admin_class, force=False):
    """Registrando modelo con su clase admin correspondiente"""
    try:
        if force:
            try:
                admin.site.unregister(model)
            except admin.sites.NotRegistered:
                pass
        admin.site.register(model, admin_class)
        logger.debug(f"Registrado modelo {model.__name__} con {admin_class.__name__}")
    except Exception as e:
        logger.warning(f"Error al registrar {model.__name__}: {str(e)}")

def _initialize_admin_modules():
    """Inicializando módulos admin específicos importándolos"""
    for module_path in ADMIN_MODULES:
        try:
            importlib.import_module(module_path)
            logger.debug(f"Importado módulo admin: {module_path}")
        except ImportError as e:
            logger.warning(f"No se pudo importar el módulo admin {module_path}: {str(e)}")

def initialize_admin(force_register=False):
    """
    Inicializando todas las configuraciones de administración del sistema.
    
    Args:
        force_register (bool): Si es True, fuerza el re-registro de modelos
                               incluso si ya están registrados.
    """
    # Configuración del sitio admin
    admin.site.site_header = "Administración de Grupo huntRED®"
    admin.site.site_title = "Portal Administrativo"
    admin.site.index_title = "Bienvenido al Panel de Administración"
    
    # Registrando modelos con sus clases admin correspondientes
    for model, admin_class in ADMIN_CLASS_MAPPING.items():
        _register_model_admin(model, admin_class, force=force_register)
    
    # Inicializando módulos admin específicos
    _initialize_admin_modules()
    
    logger.info("Configuración de administración inicializada correctamente")
    
    return True
