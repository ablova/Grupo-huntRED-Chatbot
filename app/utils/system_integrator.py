"""
Integrador de sistemas de optimización para Grupo huntRED®.
Este módulo centraliza la inicialización de todas las optimizaciones del sistema
y proporciona una interfaz unificada respetando la estructura existente.
"""

import logging
import importlib
import os
from typing import Dict, Any, List, Optional
from django.conf import settings
from django.core.cache import cache
from django.db.models import QuerySet
from django.apps import apps

logger = logging.getLogger(__name__)


class SystemIntegrator:
    """
    Integrador centralizado para todos los sistemas de optimización.
    Proporciona una interfaz unificada que respeta la estructura existente.
    """
    
    _initialized = False
    _components = {}
    
    @classmethod
    def initialize(cls):
        """
        Inicializa todos los componentes de optimización del sistema.
        Respeta la estructura existente y adapta las nuevas funcionalidades.
        """
        if cls._initialized:
            return True
            
        logger.info("Initializing Grupo huntRED® System Integrator")
        
        # Lista de componentes a inicializar
        components = [
            ('logging_manager', 'app.utils.logging_manager', 'LoggingManager', 'setup_logging'),
            ('system_config', 'app.utils.system_config', 'initialize_system_config', None),
            ('performance_tracker', 'app.utils.system_optimization', 'PerformanceTracker', None),
            ('business_unit_manager', 'app.utils.business_unit_manager', 'BusinessUnitManager', None),
            ('notification_service', 'app.utils.notification_service', 'NotificationService', None),
            ('orm_optimizer', 'app.utils.orm_optimizer', 'QueryOptimizer', None),
        ]
        
        # Inicializar componentes
        for name, module_path, class_name, method_name in components:
            try:
                module = importlib.import_module(module_path)
                
                if method_name:
                    # Si se especificó un método, llamarlo directamente
                    method = getattr(module, method_name)
                    method()
                    cls._components[name] = {'status': 'initialized', 'module': module}
                elif hasattr(module, class_name):
                    # Obtener la clase/objeto
                    component = getattr(module, class_name)
                    
                    # Si es una clase con un método initialize o setup
                    if hasattr(component, 'initialize'):
                        component.initialize()
                        cls._components[name] = {'status': 'initialized', 'instance': component}
                    elif hasattr(component, 'setup'):
                        component.setup()
                        cls._components[name] = {'status': 'initialized', 'instance': component}
                    else:
                        # Para componentes que se inicializan automáticamente al importar
                        cls._components[name] = {'status': 'imported', 'instance': component}
                        
                logger.info(f"Initialized component: {name}")
                
            except ImportError:
                logger.warning(f"Component not found: {name}")
                cls._components[name] = {'status': 'not_found'}
            except Exception as e:
                logger.error(f"Error initializing component {name}: {str(e)}")
                cls._components[name] = {'status': 'error', 'error': str(e)}
        
        # Integrar con modelos y servicios existentes
        cls._configure_backwards_compatibility()
        
        cls._initialized = True
        logger.info("Grupo huntRED® System Integrator initialized successfully")
        return True
    
    @classmethod
    def _configure_backwards_compatibility(cls):
        """
        Configura adaptadores para mantener compatibilidad con código existente.
        """
        # Integrar nuestro NotificationService con el existente
        try:
            # Intentar importar el servicio de notificaciones existente
            old_notification = importlib.import_module('app.ats.utils.notification_service')
            new_notification = importlib.import_module('app.utils.notification_service')
            
            # Inyectar funcionalidades avanzadas
            if hasattr(old_notification, 'NotificationService') and hasattr(new_notification, 'NotificationService'):
                # Extender el servicio existente con nuestras funcionalidades avanzadas
                old_service = old_notification.NotificationService
                new_service = new_notification.NotificationService
                
                # Método para enviar notificaciones usando el nuevo servicio
                def enhanced_send_notification(self, *args, **kwargs):
                    # Llamar al método original primero
                    result = self._original_send_notification(*args, **kwargs)
                    
                    # Si hay recipient y tiene una BU asociada, usar esa BU
                    recipient = kwargs.get('recipient') or (args[0] if args else None)
                    bu_name = None
                    
                    if hasattr(recipient, 'business_unit') and recipient.business_unit:
                        bu_name = recipient.business_unit.name
                    
                    # También enviar usando el nuevo servicio (como backup y para analytics)
                    try:
                        notification_type = kwargs.get('notification_type') or (args[1] if len(args) > 1 else None)
                        content = kwargs.get('content') or (args[2] if len(args) > 2 else None)
                        metadata = kwargs.get('metadata') or (args[3] if len(args) > 3 else None)
                        
                        new_service.send_notification(
                            recipient=recipient,
                            subject=notification_type,
                            message=content,
                            channel='whatsapp' if hasattr(recipient, 'whatsapp_enabled') and recipient.whatsapp_enabled else 'email',
                            metadata=metadata,
                            bu_name=bu_name
                        )
                    except Exception as e:
                        logger.debug(f"Error sending with enhanced notification service: {str(e)}")
                        
                    return result
                
                # Guardar el método original
                if not hasattr(old_service, '_original_send_notification'):
                    old_service._original_send_notification = old_service.send_notification
                    old_service.send_notification = enhanced_send_notification
                    
                logger.info("NotificationService compatibility layer configured")
                
        except ImportError:
            logger.debug("Original notification service not found, skipping compatibility layer")
        except Exception as e:
            logger.error(f"Error configuring notification compatibility: {str(e)}")
        
        # Configurar compatibilidad para BusinessUnitManager
        try:
            # Buscar métodos existentes de configuración de BU
            if hasattr(settings, 'get_channel_config') and cls._components.get('business_unit_manager', {}).get('instance'):
                original_get_channel_config = settings.get_channel_config
                bu_manager = cls._components['business_unit_manager']['instance']
                
                # Función mejorada que usa caché
                def enhanced_get_channel_config(business_unit, channel_type):
                    # Intentar obtener de nuestro sistema optimizado
                    try:
                        cache_key = f"channel_config:{business_unit}:{channel_type}"
                        cached = cache.get(cache_key)
                        
                        if cached:
                            return cached
                            
                        # Si no está en caché, obtener con el método original
                        result = original_get_channel_config(business_unit, channel_type)
                        
                        # Guardar en caché
                        cache.set(cache_key, result, 300)  # 5 minutos
                        return result
                    except Exception:
                        # Si falla, usar el método original como fallback
                        return original_get_channel_config(business_unit, channel_type)
                
                # Reemplazar el método existente
                settings.get_channel_config = enhanced_get_channel_config
                logger.info("BusinessUnit configuration compatibility layer configured")
                
        except Exception as e:
            logger.error(f"Error configuring BU compatibility: {str(e)}")
    
    @classmethod
    def get_component(cls, name: str) -> Any:
        """
        Obtiene un componente de optimización por nombre.
        
        Args:
            name: Nombre del componente
            
        Returns:
            El componente solicitado o None si no existe
        """
        if not cls._initialized:
            cls.initialize()
            
        component_info = cls._components.get(name)
        if not component_info:
            return None
            
        if 'instance' in component_info:
            return component_info['instance']
        elif 'module' in component_info:
            return component_info['module']
            
        return None
    
    @classmethod
    def get_business_unit_config(cls, bu_id_or_name: str, key: str = None, default: Any = None) -> Any:
        """
        Obtiene configuración de una Business Unit usando el sistema optimizado.
        
        Args:
            bu_id_or_name: ID o nombre de la Business Unit
            key: Clave específica a obtener
            default: Valor por defecto
            
        Returns:
            Configuración solicitada
        """
        bu_manager = cls.get_component('business_unit_manager')
        if not bu_manager:
            # Fallback a métodos tradicionales
            try:
                from app.models import ConfiguracionBU
                config = ConfiguracionBU.objects.filter(business_unit=bu_id_or_name).first()
                if not config:
                    return default
                    
                if not key:
                    return json.loads(config.config)
                    
                config_data = json.loads(config.config)
                return config_data.get(key, default)
            except Exception:
                return default
                
        # Usar el gestor optimizado
        if key:
            return bu_manager.get_config_value(bu_id_or_name, key, default)
        else:
            return bu_manager.get_business_unit(bu_id_or_name)
    
    @classmethod
    def optimize_query(cls, queryset: QuerySet) -> QuerySet:
        """
        Optimiza un QuerySet aplicando mejoras de rendimiento automáticas.
        
        Args:
            queryset: QuerySet a optimizar
            
        Returns:
            QuerySet optimizado
        """
        optimizer = cls.get_component('orm_optimizer')
        if not optimizer:
            return queryset
            
        return optimizer.apply_optimized_query(queryset)
    
    @classmethod
    def send_notification(cls, recipient, subject: str, message: str, 
                        channel: str = None, **kwargs) -> Dict:
        """
        Envía una notificación usando el servicio optimizado.
        
        Args:
            recipient: Destinatario de la notificación
            subject: Asunto
            message: Mensaje
            channel: Canal (email, whatsapp, sms, etc.)
            **kwargs: Parámetros adicionales
            
        Returns:
            Resultado del envío
        """
        notification_service = cls.get_component('notification_service')
        if not notification_service:
            # Fallback al servicio tradicional
            try:
                from app.ats.utils.notification_service import NotificationService
                old_service = NotificationService()
                
                # Adaptar parámetros
                notification_type = subject
                content = message
                metadata = kwargs.get('metadata')
                
                # Usar método asíncrono si está disponible
                if hasattr(old_service, 'send_notification'):
                    import asyncio
                    result = asyncio.run(old_service.send_notification(
                        recipient=recipient,
                        notification_type=notification_type,
                        content=content,
                        metadata=metadata
                    ))
                    return {'success': result is not None, 'notification': result}
                    
                return {'success': False, 'error': 'Notification service not available'}
            except Exception as e:
                return {'success': False, 'error': str(e)}
        
        # Usar el servicio optimizado
        return notification_service.send_notification(
            recipient=recipient,
            subject=subject,
            message=message,
            channel=channel,
            **kwargs
        )
    
    @classmethod
    def get_system_stats(cls) -> Dict:
        """
        Obtiene estadísticas del sistema optimizado.
        
        Returns:
            Dict con estadísticas del sistema
        """
        stats = {
            'initialized': cls._initialized,
            'components': {},
            'performance': {},
        }
        
        # Información de componentes
        for name, info in cls._components.items():
            stats['components'][name] = {
                'status': info.get('status'),
                'error': info.get('error')
            }
            
        # Métricas de rendimiento
        performance_tracker = cls.get_component('performance_tracker')
        if performance_tracker:
            try:
                stats['performance'] = performance_tracker.get_metrics_report()
            except Exception as e:
                stats['performance']['error'] = str(e)
                
        return stats


# Inicializar el sistema al importar el módulo
SystemIntegrator.initialize()
