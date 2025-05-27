# /home/pablo/app/com/pricing/__init__.py
"""
Módulo de pricing de Grupo huntRED®.

Este módulo maneja la generación de propuestas, cálculo de precios, 
y gestión de contratos siguiendo los principios de Apoyo, Solidaridad y Sinergia.

Componentes principales:
- Pricing Core: Cálculos de precios, addons y hitos de pago
- Proposal Generator: Propuestas dinámicas en HTML/PDF
- Contract Workflow: Gestión y firma de contratos
- Fiscal Management: Responsables fiscales y notificaciones
- Opportunity Ingestion: Alimentación del pipeline de oportunidades
- Analytics Engine: Insights y reportes basados en datos

Componentes avanzados:
- Volume Pricing: Descuentos por cantidad en múltiples posiciones
- Recurring Services: Servicios recurrentes con descuentos por duración
- Bundle Pricing: Paquetes de servicios con descuentos combinados
- Progressive Billing: Facturación por hitos personalizada por BU
"""

import logging
logger = logging.getLogger(__name__)

# Definición de versiones
__version__ = '2.0.0'
__author__ = 'Grupo huntRED®'

# Exportar clases principales para facilitar su uso
from app.com.pricing.utils import (
    calculate_pricing, calculate_pricing_opportunity, generate_milestones,
    apply_coupon, generate_proposal_pdf, create_payment_milestones,
    register_addon_service, get_registered_addon, get_all_registered_addons,
    calculate_addon_pricing, generate_addon_proposal
)

from app.com.pricing.volume_pricing import (
    VolumePricing, RecurringServicePricing, BundlePricing
)

from app.com.pricing.progressive_billing import ProgressiveBilling

from app.com.pricing.proposal_renderer import (
    ProposalRenderer, generate_proposal
)

# Interfaz unificada para pricing
try:
    from app.com.pricing.pricing_interface import PricingManager
    from app.com.pricing.talent_360_pricing import Talent360Pricing, register_talent_360_addon
    
    # Exportar todas las clases y funciones principales
    __all__ = [
        # Interfaces principales
        'PricingManager',
        'ProposalRenderer',
        'generate_proposal',
        
        # Módulos de pricing
        'VolumePricing',
        'RecurringServicePricing', 
        'BundlePricing',
        'ProgressiveBilling',
        'Talent360Pricing',
        
        # Funciones de utilidad
        'calculate_pricing',
        'calculate_pricing_opportunity',
        'generate_milestones',
        'register_addon_service',
        'register_talent_360_addon'
    ]
    
    logger.info("Módulo de pricing avanzado inicializado correctamente")
except ImportError as e:
    logger.warning(f"No se pudo importar la interfaz de pricing avanzado: {e}")
    __all__ = ['calculate_pricing', 'calculate_pricing_opportunity']

# Registro automático de servicios addon
def register_addons():
    """Registra automáticamente todos los servicios addon disponibles en el sistema."""
    logger.info("Registrando servicios addon...")
    
    # Registrar el servicio de Análisis de Talento 360°
    try:
        from app.com.pricing.talent_360_pricing import register_talent_360_addon
        register_talent_360_addon()
        logger.info("Servicio de Análisis de Talento 360° registrado exitosamente.")
    except ImportError as e:
        logger.warning(f"No se pudo registrar el servicio de Análisis de Talento 360°: {e}")
    except Exception as e:
        logger.error(f"Error al registrar el servicio de Análisis de Talento 360°: {e}", exc_info=True)
    
    # Registrar servicios adicionales de pricing avanzado
    try:
        # Registro de bundles predefinidos
        logger.info("Registrando bundles de servicios predefinidos...")
        
        # Aquí se podrían registrar bundles adicionales en el futuro
        # Por ejemplo: register_bundle_service('talent_acquisition', 'Paquete de Adquisición de Talento')
        
        logger.info("Bundles de servicios registrados exitosamente.")
    except Exception as e:
        logger.error(f"Error al registrar bundles de servicios: {e}", exc_info=True)
    
    logger.info("Registro de servicios addon completado.")

# Función para inicializar las configuraciones específicas por BusinessUnit
def initialize_pricing_configs():
    """Inicializa las configuraciones de pricing específicas para cada BusinessUnit."""
    logger.info("Inicializando configuraciones de pricing específicas por BusinessUnit...")
    
    try:
        from app.models import BusinessUnit, PricingBaseline
        
        # Verificar si existen las configuraciones base
        business_units = BusinessUnit.objects.all()
        
        for bu in business_units:
            # Configuración de pricing por defecto si no existe
            if not hasattr(bu, 'pricing_config') or not bu.pricing_config:
                logger.info(f"Inicializando pricing_config para {bu.name}")
                bu.pricing_config = {
                    'base_rate': '15.00',      # 15% del salario para huntRED por defecto
                    'base_type': 'percentage', # porcentaje o fijo
                    'addons': {
                        'background_check': {'rate': '10.00', 'type': 'percentage'},
                        'onboarding': {'amount': '5000.00', 'type': 'fixed'}
                    }
                }
                bu.save()
                
            # Verificar si existe la configuración de PricingBaseline
            try:
                PricingBaseline.objects.get(bu=bu)
            except PricingBaseline.DoesNotExist:
                logger.info(f"Creando PricingBaseline para {bu.name}")
                PricingBaseline.objects.create(
                    bu=bu,
                    model='percentage',
                    base_price=Decimal('0.00'),  # Solo aplica si model='fixed'
                    percentage=Decimal('15.00')  # 15% por defecto
                )
        
        logger.info("Configuraciones de pricing inicializadas correctamente.")
    except Exception as e:
        logger.error(f"Error al inicializar configuraciones de pricing: {e}", exc_info=True)

# Inicializar el módulo
def initialize_module():
    """Inicializa todos los componentes del módulo de pricing."""
    logger.info("Inicializando módulo de pricing...")
    
    # Registrar addons y servicios
    register_addons()
    
    # Inicializar configuraciones específicas
    initialize_pricing_configs()
    
    # Inicializar sistema de generación automática de propuestas
    try:
        from app.com.pricing.triggers import connect_signals
        connect_signals()
        logger.info("Sistema de generación automática de propuestas inicializado")
    except ImportError as e:
        logger.warning(f"No se pudo inicializar el sistema de generación automática: {e}")
    
    # Inicializar sistema de compatibilidad
    try:
        from app.com.pricing.compatibility import initialize_compatibility
        initialize_compatibility()
        logger.info("Sistema de compatibilidad entre directorios inicializado")
    except ImportError as e:
        logger.warning(f"No se pudo inicializar el sistema de compatibilidad: {e}")
    
    logger.info("Módulo de pricing inicializado completamente.")

# Inicializar todo el módulo
try:
    initialize_module()
except Exception as e:
    logger.error(f"Error al inicializar el módulo de pricing: {e}", exc_info=True)
    logger.info("Se continúa con la inicialización parcial del módulo de pricing.")
    register_addons()  # Al menos intentamos registrar los addons
