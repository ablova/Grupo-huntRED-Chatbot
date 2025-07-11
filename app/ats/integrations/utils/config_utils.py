# app/ats/integrations/utils/config_utils.py
"""
Utilidades para configuración de integraciones.
"""

import json
import logging
from typing import Dict, Any, Optional, Union
from django.conf import settings

logger = logging.getLogger(__name__)

def get_integration_config(integration_name: str, key: Optional[str] = None, default: Any = None) -> Any:
    """
    Obtiene la configuración de una integración específica.
    
    Args:
        integration_name: Nombre de la integración (ej. 'slack', 'teams', 'zapier')
        key: Clave específica de configuración (opcional)
        default: Valor por defecto si no se encuentra la configuración
        
    Returns:
        Configuración completa o valor específico de la configuración
    """
    try:
        # Intentar obtener la configuración desde la base de datos
        from app.ats.integrations.models import IntegrationConfig
        
        config_obj = IntegrationConfig.objects.filter(
            integration_name=integration_name,
            is_active=True
        ).first()
        
        if config_obj and config_obj.config:
            config = json.loads(config_obj.config) if isinstance(config_obj.config, str) else config_obj.config
            
            if key:
                return config.get(key, default)
            return config
    except Exception as e:
        logger.warning(f"Error al obtener configuración de BD para {integration_name}: {str(e)}")
    
    # Fallback a configuración en settings
    try:
        integration_settings = getattr(settings, f"{integration_name.upper()}_CONFIG", {})
        
        if key:
            return integration_settings.get(key, default)
        return integration_settings or default
    except Exception as e:
        logger.error(f"Error al obtener configuración para {integration_name}: {str(e)}")
        return default

def set_integration_config(integration_name: str, config: Dict[str, Any], key: Optional[str] = None, value: Any = None) -> bool:
    """
    Establece la configuración para una integración específica.
    
    Args:
        integration_name: Nombre de la integración
        config: Diccionario de configuración completo (ignorado si key y value están presentes)
        key: Clave específica a actualizar
        value: Valor a establecer para la clave específica
        
    Returns:
        True si la operación fue exitosa, False en caso contrario
    """
    try:
        from app.ats.integrations.models import IntegrationConfig
        
        config_obj, created = IntegrationConfig.objects.get_or_create(
            integration_name=integration_name,
            defaults={'is_active': True}
        )
        
        # Obtener configuración actual
        current_config = {}
        if config_obj.config:
            current_config = json.loads(config_obj.config) if isinstance(config_obj.config, str) else config_obj.config
        
        # Actualizar configuración
        if key and value is not None:
            current_config[key] = value
        elif config:
            current_config = config
            
        # Guardar configuración actualizada
        config_obj.config = json.dumps(current_config)
        config_obj.save()
        
        logger.info(f"Configuración actualizada para {integration_name}")
        return True
    except Exception as e:
        logger.error(f"Error al establecer configuración para {integration_name}: {str(e)}")
        return False

def delete_integration_config(integration_name: str, key: Optional[str] = None) -> bool:
    """
    Elimina la configuración de una integración o una clave específica.
    
    Args:
        integration_name: Nombre de la integración
        key: Clave específica a eliminar (si es None, se elimina toda la configuración)
        
    Returns:
        True si la operación fue exitosa, False en caso contrario
    """
    try:
        from app.ats.integrations.models import IntegrationConfig
        
        config_obj = IntegrationConfig.objects.filter(
            integration_name=integration_name
        ).first()
        
        if not config_obj:
            logger.warning(f"No existe configuración para {integration_name}")
            return False
            
        if key:
            # Eliminar solo una clave específica
            current_config = json.loads(config_obj.config) if isinstance(config_obj.config, str) else config_obj.config
            if key in current_config:
                del current_config[key]
                config_obj.config = json.dumps(current_config)
                config_obj.save()
                logger.info(f"Clave {key} eliminada de la configuración de {integration_name}")
                return True
            return False
        else:
            # Eliminar toda la configuración
            config_obj.delete()
            logger.info(f"Configuración eliminada para {integration_name}")
            return True
    except Exception as e:
        logger.error(f"Error al eliminar configuración para {integration_name}: {str(e)}")
        return False
