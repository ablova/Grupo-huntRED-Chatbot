"""
Gestor centralizado de Business Units para Grupo huntRED®.
Este módulo implementa funcionalidades para gestionar de forma unificada
las reglas de negocio específicas de cada unidad de negocio.
"""

import logging
import json
from typing import Any, Dict, List, Optional, Union, Set
from django.conf import settings
from django.core.cache import cache
from django.db.models import QuerySet, Q
from asgiref.sync import sync_to_async

from app.utils.logging_manager import LoggingManager, log_function_call

logger = LoggingManager.get_logger('business_units')

class BusinessUnitManager:
    """
    Gestor centralizado para reglas y configuraciones específicas de Business Units.
    Implementa funcionalidades para los diferentes BUs del sistema Grupo huntRED®.
    """
    
    # Definición de Business Units disponibles en el sistema
    BUSINESS_UNITS = {
        'huntRED': {
            'name': 'huntRED',
            'display_name': 'huntRED®',
            'description': 'Reclutamiento middle/top management',
            'logo': 'assets/img/huntred_logo.png',
            'primary_color': '#C20E1A',
            'features': ['chatbot', 'ml', 'payments', 'publish', 'sign'],
            'thirdparty_integrations': ['stripe', 'gpt', 'blacktrust', 'sign']
        },
        'huntU': {
            'name': 'huntU',
            'display_name': 'huntU®',
            'description': 'Reclutamiento para undergraduates/graduates',
            'logo': 'assets/img/huntu_logo.png',
            'primary_color': '#0072CE',
            'features': ['chatbot', 'ml', 'payments', 'publish'],
            'thirdparty_integrations': ['stripe', 'gpt', 'blacktrust', 'sign']
        },
        'huntRED_Executive': {
            'name': 'huntRED_Executive',
            'display_name': 'huntRED® Executive',
            'description': 'Reclutamiento para C-level y board',
            'logo': 'assets/img/huntred_executive_logo.png',
            'primary_color': '#1A1A1A',
            'features': ['chatbot', 'ml', 'payments', 'publish', 'sign', 'executive_network'],
            'thirdparty_integrations': ['stripe', 'gpt', 'blacktrust', 'sign']
        },
        'Amigro': {
            'name': 'Amigro',
            'display_name': 'Amigro',
            'description': 'Oportunidades laborales para migrantes',
            'logo': 'assets/img/amigro_logo.png',
            'primary_color': '#40826D',
            'features': ['chatbot', 'ml', 'payments'],
            'thirdparty_integrations': ['gpt', 'stripe', 'incode']
        },
        'SEXSI': {
            'name': 'SEXSI',
            'display_name': 'SEXSI®',
            'description': 'Contratos íntimos',
            'logo': 'assets/img/sexsi_logo.png',
            'primary_color': '#FF4081',
            'features': ['contracts', 'payments', 'sign'],
            'thirdparty_integrations': ['stripe', 'blacktrust']
        },
        'MilkyLeak': {
            'name': 'MilkyLeak',
            'display_name': 'MilkyLeak',
            'description': 'Proyecto de redes sociales',
            'logo': 'assets/img/milkyleak_logo.png',
            'primary_color': '#9C27B0',
            'features': ['social', 'content', 'publish'],
            'thirdparty_integrations': ['gpt']
        }
    }
    
    # Mapa de relaciones entre Business Units
    BU_RELATIONSHIPS = {
        'huntRED': ['huntU', 'huntRED_Executive'],
        'huntU': ['huntRED'],
        'huntRED_Executive': ['huntRED'],
        'Amigro': [],
        'SEXSI': [],
        'MilkyLeak': []
    }
    
    # Configuraciones específicas para cada BU
    BU_CONFIGS = {
        'huntRED': {
            'default_commission_percentage': 20,
            'salary_range_min': 40000,
            'salary_range_max': 120000,
            'chatbot_greeting': '¡Hola! Soy el asistente de huntRED®. ¿En qué puedo ayudarte hoy?',
            'vacante_status_flow': ['nueva', 'en_proceso', 'candidatos_propuestos', 'entrevistas', 'oferta', 'contratado', 'cancelada'],
            'notification_channels': ['email', 'sms', 'internal'],
            'payment_methods': ['stripe', 'paypal', 'bank_transfer']
        },
        'huntU': {
            'default_commission_percentage': 15,
            'salary_range_min': 20000,
            'salary_range_max': 40000,
            'chatbot_greeting': '¡Hola! Soy el asistente de huntU®. ¿Cómo puedo ayudarte?',
            'vacante_status_flow': ['nueva', 'en_proceso', 'candidatos_propuestos', 'entrevistas', 'oferta', 'contratado', 'cancelada'],
            'notification_channels': ['email', 'whatsapp', 'internal'],
            'payment_methods': ['stripe', 'paypal']
        },
        'huntRED_Executive': {
            'default_commission_percentage': 25,
            'salary_range_min': 100000,
            'salary_range_max': None,
            'chatbot_greeting': 'Bienvenido a huntRED® Executive. ¿En qué puedo asistirle hoy?',
            'vacante_status_flow': ['nueva', 'en_proceso', 'candidatos_propuestos', 'entrevistas', 'evaluacion', 'oferta', 'contratado', 'cancelada'],
            'notification_channels': ['email', 'sms', 'internal'],
            'payment_methods': ['stripe', 'bank_transfer', 'wire_transfer']
        },
        'Amigro': {
            'default_commission_percentage': 10,
            'salary_range_min': 10000,
            'salary_range_max': 40000,
            'chatbot_greeting': '¡Hola! Soy el asistente de Amigro. ¿Cómo puedo ayudarte a encontrar trabajo?',
            'vacante_status_flow': ['nueva', 'en_proceso', 'entrevistas', 'contratado', 'cancelada'],
            'notification_channels': ['whatsapp', 'sms'],
            'payment_methods': ['stripe', 'cash']
        },
        'SEXSI': {
            'default_commission_percentage': 5,
            'contract_default_duration_days': 90,
            'chatbot_greeting': 'Bienvenido a SEXSI®. ¿En qué puedo ayudarte?',
            'contract_status_flow': ['borrador', 'pendiente_firma', 'firmado', 'activo', 'finalizado', 'cancelado'],
            'notification_channels': ['email', 'internal'],
            'payment_methods': ['stripe', 'paypal']
        },
        'MilkyLeak': {
            'subscription_price': 9.99,
            'premium_subscription_price': 19.99,
            'chatbot_greeting': '¡Hola! Soy el asistente de MilkyLeak. ¿En qué puedo ayudarte?',
            'content_types': ['post', 'story', 'video', 'stream'],
            'notification_channels': ['email', 'push'],
            'payment_methods': ['stripe', 'paypal']
        }
    }
    
    @classmethod
    @log_function_call(module='business_units')
    def get_business_unit(cls, bu_id_or_name: Union[int, str]) -> Dict:
        """
        Obtiene la configuración de una Business Unit específica.
        
        Args:
            bu_id_or_name: ID o nombre de la Business Unit
            
        Returns:
            Dict: Configuración completa de la BU
        """
        # Verificar cache primero
        cache_key = f"bu_config:{bu_id_or_name}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
            
        # Determinar si es ID o nombre
        bu_name = None
        
        if isinstance(bu_id_or_name, int) or (isinstance(bu_id_or_name, str) and bu_id_or_name.isdigit()):
            # Es un ID, obtener de la base de datos
            try:
                from app.models import BusinessUnit
                bu = BusinessUnit.objects.get(id=int(bu_id_or_name))
                bu_name = bu.name
            except Exception as e:
                logger.error(f"Error loading BusinessUnit with ID {bu_id_or_name}: {str(e)}")
                return None
        else:
            # Es un nombre
            bu_name = bu_id_or_name
        
        # Verificar si existe en las definiciones estáticas
        if bu_name in cls.BUSINESS_UNITS:
            # Combinar información estática con configuración específica
            result = cls.BUSINESS_UNITS[bu_name].copy()
            if bu_name in cls.BU_CONFIGS:
                result['config'] = cls.BU_CONFIGS[bu_name]
            
            # Obtener relaciones
            result['related_bus'] = cls.BU_RELATIONSHIPS.get(bu_name, [])
            
            # Guardar en caché (30 minutos)
            cache.set(cache_key, result, 1800)
            
            return result
        
        # Último recurso: buscar en la base de datos por nombre
        try:
            from app.models import BusinessUnit
            bu = BusinessUnit.objects.filter(name__iexact=bu_name).first()
            
            if bu:
                result = {
                    'name': bu.name,
                    'display_name': bu.display_name,
                    'description': bu.description,
                    'logo': bu.logo_url,
                    'primary_color': bu.primary_color,
                    'config': json.loads(bu.config) if bu.config else {}
                }
                
                # Guardar en caché (30 minutos)
                cache.set(cache_key, result, 1800)
                
                return result
        except Exception as e:
            logger.error(f"Error loading BusinessUnit '{bu_name}' from database: {str(e)}")
        
        return None
    
    @classmethod
    @log_function_call(module='business_units')
    def get_user_business_units(cls, user) -> List[Dict]:
        """
        Obtiene las Business Units asignadas a un usuario.
        
        Args:
            user: Usuario a consultar
            
        Returns:
            List[Dict]: Lista de BUs asignadas
        """
        if not user or not user.is_authenticated:
            return []
            
        # Verificar caché
        cache_key = f"user_bus:{user.id}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        # Lista para almacenar BUs
        user_bus = []
        
        # Si es superadmin, dar acceso a todas las BUs
        if user.is_superuser:
            for bu_name, bu_data in cls.BUSINESS_UNITS.items():
                bu_info = bu_data.copy()
                bu_info['config'] = cls.BU_CONFIGS.get(bu_name, {})
                user_bus.append(bu_info)
                
            # Guardar en caché (30 minutos)
            cache.set(cache_key, user_bus, 1800)
            
            return user_bus
        
        # Consultar BUs asignadas en base de datos
        try:
            # Verificar si existe perfil y tiene BUs asignadas
            if hasattr(user, 'profile') and hasattr(user.profile, 'business_units'):
                assigned_bus = user.profile.business_units.all()
                
                for bu in assigned_bus:
                    # Combinar información estática con datos de BD
                    bu_name = bu.name
                    
                    if bu_name in cls.BUSINESS_UNITS:
                        bu_info = cls.BUSINESS_UNITS[bu_name].copy()
                        bu_info['config'] = cls.BU_CONFIGS.get(bu_name, {})
                        bu_info['id'] = bu.id
                    else:
                        # Usar datos de la BD
                        bu_info = {
                            'id': bu.id,
                            'name': bu.name,
                            'display_name': bu.display_name,
                            'description': bu.description,
                            'logo': bu.logo_url,
                            'primary_color': bu.primary_color,
                            'config': json.loads(bu.config) if bu.config else {}
                        }
                    
                    user_bus.append(bu_info)
        except Exception as e:
            logger.error(f"Error loading user business units: {str(e)}")
        
        # Guardar en caché (15 minutos)
        cache.set(cache_key, user_bus, 900)
        
        return user_bus
    
    @classmethod
    @log_function_call(module='business_units')
    def filter_queryset_by_bu(cls, queryset: QuerySet, user, bu_id: Union[int, str] = None) -> QuerySet:
        """
        Filtra un queryset según la Business Unit y permisos del usuario.
        
        Args:
            queryset: QuerySet a filtrar
            user: Usuario actual
            bu_id: ID de Business Unit específica (opcional)
            
        Returns:
            QuerySet filtrado
        """
        # Verificar los permisos a través del RBAC
        from app.utils.rbac import RBAC
        
        # Si el usuario no está autenticado, no mostrar nada
        if not user or not user.is_authenticated:
            return queryset.none()
        
        # Si el usuario es superadmin y no se especifica BU, mostrar todo
        if user.is_superuser and not bu_id:
            return queryset
        
        # Si se especifica BU, verificar si el usuario tiene acceso
        if bu_id:
            has_access = False
            
            # Superadmin tiene acceso a todas las BUs
            if user.is_superuser:
                has_access = True
            # Verificar si la BU está en la lista de BUs asignadas
            elif hasattr(user, 'profile') and hasattr(user.profile, 'business_units'):
                has_access = user.profile.business_units.filter(id=bu_id).exists()
            
            if has_access:
                return queryset.filter(bu_id=bu_id)
            else:
                # No tiene acceso a esta BU específica
                return queryset.none()
        
        # Filtrar por BUs asignadas al usuario
        if hasattr(user, 'profile') and hasattr(user.profile, 'business_units'):
            assigned_bu_ids = user.profile.business_units.values_list('id', flat=True)
            return queryset.filter(bu_id__in=assigned_bu_ids)
        
        # Si no tiene BUs asignadas, no mostrar nada
        return queryset.none()
    
    @classmethod
    @log_function_call(module='business_units')
    def get_config_value(cls, bu_id_or_name: Union[int, str], key: str, default=None) -> Any:
        """
        Obtiene un valor de configuración específico para una BU.
        
        Args:
            bu_id_or_name: ID o nombre de la Business Unit
            key: Clave de configuración a obtener
            default: Valor por defecto si no existe
            
        Returns:
            Any: Valor de configuración
        """
        # Obtener configuración completa
        bu_config = cls.get_business_unit(bu_id_or_name)
        
        if not bu_config or 'config' not in bu_config:
            return default
            
        # Buscar la clave en la configuración
        return bu_config['config'].get(key, default)
    
    @classmethod
    @log_function_call(module='business_units')
    def set_config_value(cls, bu_id_or_name: Union[int, str], key: str, value: Any) -> bool:
        """
        Establece un valor de configuración para una BU.
        
        Args:
            bu_id_or_name: ID o nombre de la Business Unit
            key: Clave de configuración a establecer
            value: Valor a establecer
            
        Returns:
            bool: True si se estableció correctamente
        """
        # Primero intentar actualizar en la base de datos
        try:
            from app.models import BusinessUnit
            
            # Determinar si es ID o nombre
            filter_kwargs = {}
            if isinstance(bu_id_or_name, int) or (isinstance(bu_id_or_name, str) and bu_id_or_name.isdigit()):
                filter_kwargs['id'] = int(bu_id_or_name)
            else:
                filter_kwargs['name__iexact'] = bu_id_or_name
                
            # Obtener BU
            bu = BusinessUnit.objects.filter(**filter_kwargs).first()
            
            if bu:
                # Cargar configuración actual
                config = json.loads(bu.config) if bu.config else {}
                
                # Actualizar valor
                config[key] = value
                
                # Guardar
                bu.config = json.dumps(config)
                bu.save(update_fields=['config'])
                
                # Invalidar caché
                cache_key = f"bu_config:{bu_id_or_name}"
                cache.delete(cache_key)
                
                return True
        except Exception as e:
            logger.error(f"Error updating BusinessUnit config: {str(e)}")
        
        # Si no se pudo actualizar en BD, actualizar en memoria
        # (aunque se perderá al reiniciar el servidor)
        bu_name = None
        
        # Determinar nombre de BU
        if isinstance(bu_id_or_name, int) or (isinstance(bu_id_or_name, str) and bu_id_or_name.isdigit()):
            try:
                from app.models import BusinessUnit
                bu = BusinessUnit.objects.get(id=int(bu_id_or_name))
                bu_name = bu.name
            except Exception:
                return False
        else:
            bu_name = bu_id_or_name
            
        # Verificar si existe en las configuraciones
        if bu_name in cls.BU_CONFIGS:
            cls.BU_CONFIGS[bu_name][key] = value
            
            # Invalidar caché
            cache_key = f"bu_config:{bu_id_or_name}"
            cache.delete(cache_key)
            
            return True
            
        return False
    
    @classmethod
    @log_function_call(module='business_units')
    def get_available_business_units(cls) -> List[Dict]:
        """
        Obtiene la lista de todas las Business Units disponibles.
        
        Returns:
            List[Dict]: Lista de BUs
        """
        # Verificar caché
        cache_key = "all_business_units"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
            
        # Combinar datos estáticos con BD
        result = []
        
        # Primero añadir las BUs definidas estáticamente
        for bu_name, bu_data in cls.BUSINESS_UNITS.items():
            bu_info = bu_data.copy()
            bu_info['config'] = cls.BU_CONFIGS.get(bu_name, {})
            result.append(bu_info)
            
        # Luego buscar en la base de datos por si hay adicionales
        try:
            from app.models import BusinessUnit
            
            # Obtener BUs que no están en la lista estática
            db_bus = BusinessUnit.objects.exclude(name__in=cls.BUSINESS_UNITS.keys())
            
            for bu in db_bus:
                bu_info = {
                    'id': bu.id,
                    'name': bu.name,
                    'display_name': bu.display_name,
                    'description': bu.description,
                    'logo': bu.logo_url,
                    'primary_color': bu.primary_color,
                    'config': json.loads(bu.config) if bu.config else {}
                }
                result.append(bu_info)
        except Exception as e:
            logger.error(f"Error loading business units from database: {str(e)}")
            
        # Guardar en caché (1 hora)
        cache.set(cache_key, result, 3600)
        
        return result
