# Ubicación del archivo: /home/pablo/app/config/admin_cache.py
"""
Sistema de caché para optimización de operaciones administrativas.

Este módulo implementa un sistema de caché basado en Redis para optimizar
las operaciones del panel de administración, especialmente las consultas
frecuentes, siguiendo las reglas globales de Grupo huntRED®.
"""

import hashlib
import json
import logging
from functools import wraps
from django.core.cache import cache
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.conf import settings
import time

logger = logging.getLogger('admin_cache')

# Configuraciones de caché
CACHE_PREFIX = 'admin_cache:'
DEFAULT_TIMEOUT = getattr(settings, 'ADMIN_CACHE_TIMEOUT', 3600)  # 1 hora por defecto
ENABLE_ADMIN_CACHE = getattr(settings, 'ENABLE_ADMIN_CACHE', True)

def generate_cache_key(prefix, *args, **kwargs):
    """
    Genera una clave de caché única basada en los argumentos proporcionados.
    
    Args:
        prefix (str): Prefijo para la clave de caché
        *args: Argumentos posicionales para incorporar en la clave
        **kwargs: Argumentos nombrados para incorporar en la clave
        
    Returns:
        str: Clave de caché única
    """
    # Creando una representación única de los argumentos
    key_parts = [prefix]
    
    # Añadiendo args
    for arg in args:
        if hasattr(arg, '__dict__'):
            key_parts.append(str(id(arg)))
        else:
            key_parts.append(str(arg))
    
    # Añadiendo kwargs ordenados
    for k in sorted(kwargs.keys()):
        v = kwargs[k]
        if hasattr(v, '__dict__'):
            key_parts.append(f"{k}:{id(v)}")
        else:
            key_parts.append(f"{k}:{v}")
    
    # Generando hash MD5 de la representación
    key_str = '_'.join(key_parts)
    hashed = hashlib.md5(key_str.encode()).hexdigest()
    
    return f"{CACHE_PREFIX}{prefix}:{hashed}"

def cached_admin_method(timeout=DEFAULT_TIMEOUT, prefix=None):
    """
    Decorador para cachear métodos de administración Django.
    
    Este decorador cachea los resultados de los métodos de las clases
    ModelAdmin de Django para mejorar rendimiento en vistas frecuentes.
    
    Args:
        timeout (int): Tiempo en segundos que el resultado permanecerá en caché
        prefix (str): Prefijo opcional para la clave de caché
        
    Returns:
        function: Decorador configurado
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not ENABLE_ADMIN_CACHE:
                return func(*args, **kwargs)
            
            # Generando clave de caché
            cache_prefix = prefix or func.__name__
            cache_key = generate_cache_key(cache_prefix, *args, **kwargs)
            
            # Intentando obtener del caché
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_result
            
            # Si no está en caché, calculamos el resultado
            logger.debug(f"Cache miss for {cache_key}")
            start_time = time.time()
            result = func(*args, **kwargs)
            elapsed = time.time() - start_time
            
            # Guardando en caché solo si el tiempo de cálculo lo justifica
            if elapsed > 0.05:  # Solo cachear operaciones que toman más de 50ms
                try:
                    cache.set(cache_key, result, timeout)
                    logger.debug(f"Cached result for {cache_key} ({elapsed:.4f}s)")
                except Exception as e:
                    logger.error(f"Error caching result: {str(e)}")
            
            return result
        return wrapper
    return decorator

def invalidate_model_cache(model):
    """
    Invalida todas las claves de caché relacionadas con un modelo específico.
    
    Args:
        model: Modelo de Django cuyo caché se invalidará
    """
    model_name = model.__name__.lower()
    cache_pattern = f"{CACHE_PREFIX}{model_name}*"
    
    # Obteniendo todas las claves que coinciden con el patrón
    # Esto depende de la implementación específica de Redis
    if hasattr(cache, 'delete_pattern'):
        cache.delete_pattern(cache_pattern)
    else:
        logger.warning(f"Cache backend does not support delete_pattern for {cache_pattern}")

# Señales para invalidar caché automáticamente
def setup_cache_signals(models_list):
    """
    Configura señales para invalidar automáticamente el caché cuando los modelos cambian.
    
    Args:
        models_list (list): Lista de modelos de Django a monitorear
    """
    for model in models_list:
        # Función de invalidación específica para el modelo
        def invalidate_cache(sender, instance, **kwargs):
            model_name = sender.__name__.lower()
            logger.debug(f"Invalidating cache for {model_name} (id: {instance.id})")
            invalidate_model_cache(sender)
        
        # Registrando señales
        post_save.connect(invalidate_cache, sender=model)
        post_delete.connect(invalidate_cache, sender=model)
        
        logger.debug(f"Registered cache invalidation signals for {model.__name__}")

class CachedAdminMixin:
    """
    Mixin para añadir caché a clases de administración Django.
    
    Este mixin sobrescribe métodos comunes de ModelAdmin para
    implementar caché y mejorar el rendimiento del panel admin.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Lista de métodos a cachear
        self._cached_methods = getattr(self, 'cached_methods', [
            'get_queryset', 
            'get_changelist_instance',
            'get_search_results'
        ])
        
        # Aplicando caché a los métodos especificados
        self._apply_cache_to_methods()
    
    def _apply_cache_to_methods(self):
        """Aplica decoradores de caché a los métodos especificados."""
        model_name = self.model.__name__.lower()
        
        for method_name in self._cached_methods:
            if hasattr(self, method_name) and callable(getattr(self, method_name)):
                original_method = getattr(self, method_name)
                cached_method = cached_admin_method(
                    timeout=getattr(self, 'cache_timeout', DEFAULT_TIMEOUT),
                    prefix=f"{model_name}_{method_name}"
                )(original_method)
                
                setattr(self, method_name, cached_method)
    
    def get_list_display(self, request):
        """Versión cacheada de get_list_display."""
        cache_key = f"{CACHE_PREFIX}{self.model.__name__.lower()}_list_display_{request.user.id}"
        result = cache.get(cache_key)
        
        if result is None:
            result = super().get_list_display(request)
            cache.set(cache_key, result, DEFAULT_TIMEOUT)
            
        return result

# Optimización de consultas con select_related y prefetch_related
class OptimizedQuerysetMixin:
    """
    Mixin para optimizar las consultas en el panel admin.
    
    Este mixin implementa optimizaciones automáticas de consultas SQL
    mediante el uso de select_related y prefetch_related para reducir
    el número de consultas, siguiendo las reglas globales de Grupo huntRED®.
    """
    
    # Lista de campos para aplicar select_related
    optimized_select_related = []
    
    # Lista de campos para aplicar prefetch_related
    optimized_prefetch_related = []
    
    # Lista de campos a indexar dinámicamente
    dynamic_indexed_fields = []
    
    def get_queryset(self, request):
        """Sobrescribiendo get_queryset para aplicar optimizaciones automáticas."""
        qs = super().get_queryset(request)
        
        # Aplicando select_related si está configurado
        if hasattr(self, 'optimized_select_related') and self.optimized_select_related:
            qs = qs.select_related(*self.optimized_select_related)
        
        # Aplicando prefetch_related si está configurado
        if hasattr(self, 'optimized_prefetch_related') and self.optimized_prefetch_related:
            qs = qs.prefetch_related(*self.optimized_prefetch_related)
            
        # Aplicando optimizaciones basadas en la página actual
        if hasattr(request, 'GET'):
            current_view = self._detect_current_view(request)
            
            # Optimizaciones específicas según la vista
            if current_view == 'changelist':
                qs = self._optimize_for_changelist(qs, request)
            elif current_view == 'change':
                qs = self._optimize_for_change(qs, request)
                
        return qs
    
    def _detect_current_view(self, request):
        """Detecta la vista admin actual basada en la URL."""
        path = request.path
        
        if '/change/' in path:
            return 'change'
        elif '/add/' in path:
            return 'add'
        elif '/delete/' in path:
            return 'delete'
        else:
            return 'changelist'
            
    def _optimize_for_changelist(self, queryset, request):
        """Aplica optimizaciones específicas para la vista de lista."""
        # Añadiendo optimizaciones específicas para listas
        order_field = request.GET.get('o')
        if order_field:
            # Si hay ordenamiento, nos aseguramos de incluir esos campos en la consulta
            try:
                order_field = int(order_field)
                if abs(order_field) <= len(self.list_display):
                    field_index = abs(order_field) - 1
                    field_name = self.list_display[field_index]
                    
                    # Si es un método, no podemos usar el campo para optimizar
                    if not callable(getattr(self, field_name, None)) and not field_name.startswith('get_'):
                        # Verificando si es una relación
                        if '__' in field_name:
                            relation = field_name.split('__')[0]
                            if relation not in self.optimized_select_related:
                                queryset = queryset.select_related(relation)
            except (ValueError, IndexError):
                pass
        
        return queryset
        
    def _optimize_for_change(self, queryset, request):
        """Aplica optimizaciones específicas para la vista de edición."""
        # Optimizaciones específicas para la vista de detalle
        # En general, cargamos todas las relaciones para edición
        model_fields = self.model._meta.fields
        
        # Detectando automáticamente campos relacionados
        for field in model_fields:
            if field.is_relation and field.many_to_one:
                field_name = field.name
                if field_name not in self.optimized_select_related:
                    queryset = queryset.select_related(field_name)
                    
        return queryset
