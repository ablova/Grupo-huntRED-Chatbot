"""
Utilidades de optimización ORM para Grupo huntRED®.
Este módulo implementa patrones y herramientas para optimizar
el rendimiento de las consultas a base de datos en todo el sistema.
"""

import logging
import functools
import time
from typing import Any, Dict, List, Optional, Union, Callable, Type, TypeVar
from django.db import models, connection
from django.db.models import QuerySet, Q, F, Count, Prefetch
from django.core.cache import cache
from asgiref.sync import sync_to_async
from app.ats.utils.logging_manager import LoggingManager

logger = LoggingManager.get_logger('database')

# Definición de tipos para anotaciones
T = TypeVar('T')
ModelType = TypeVar('ModelType', bound=models.Model)

class QueryOptimizer:
    """
    Clase para optimizar consultas a base de datos en todo el sistema.
    Implementa patrones para consultas eficientes según las reglas globales.
    """
    
    @staticmethod
    def optimize_query(queryset: QuerySet, select_related: List[str] = None, 
                      prefetch_related: List[str] = None, 
                      annotate: Dict = None) -> QuerySet:
        """
        Optimiza un queryset aplicando selects y prefetches de forma inteligente.
        
        Args:
            queryset: QuerySet original a optimizar
            select_related: Campos para select_related
            prefetch_related: Campos para prefetch_related
            annotate: Anotaciones a aplicar
            
        Returns:
            QuerySet optimizado
        """
        if select_related:
            queryset = queryset.select_related(*select_related)
            
        if prefetch_related:
            queryset = queryset.prefetch_related(*prefetch_related)
            
        if annotate:
            queryset = queryset.annotate(**annotate)
            
        return queryset
    
    @staticmethod
    def get_related_fields(model_class: Type[models.Model]) -> Dict[str, List[str]]:
        """
        Analiza un modelo y devuelve campos para optimizar automáticamente.
        
        Args:
            model_class: Clase del modelo a analizar
            
        Returns:
            Dict con listas de campos para select_related y prefetch_related
        """
        select_related_fields = []
        prefetch_related_fields = []
        
        for field in model_class._meta.get_fields():
            # Relaciones directas para select_related
            if isinstance(field, (models.ForeignKey, models.OneToOneField)):
                # Obtener nombre del campo
                field_name = field.name
                select_related_fields.append(field_name)
                
            # Relaciones inversas para prefetch_related
            if isinstance(field, (models.ManyToManyField, models.ManyToOneRel, models.ManyToManyRel)):
                field_name = field.name
                prefetch_related_fields.append(field_name)
                
        return {
            'select_related': select_related_fields,
            'prefetch_related': prefetch_related_fields
        }
    
    @staticmethod
    def apply_optimized_query(queryset: QuerySet, model_class: Type[models.Model] = None) -> QuerySet:
        """
        Aplica optimizaciones automáticas basadas en el modelo del queryset.
        
        Args:
            queryset: QuerySet a optimizar
            model_class: Clase del modelo (opcional, se infiere del queryset)
            
        Returns:
            QuerySet optimizado
        """
        if not model_class:
            model_class = queryset.model
            
        # Obtener campos relacionados
        related_fields = QueryOptimizer.get_related_fields(model_class)
        
        # Aplicar optimizaciones
        return QueryOptimizer.optimize_query(
            queryset,
            select_related=related_fields['select_related'],
            prefetch_related=related_fields['prefetch_related']
        )
    
    @staticmethod
    def optimize_for_business_units(queryset: QuerySet) -> QuerySet:
        """
        Optimiza consultas que involucran Business Units según las reglas globales.
        
        Args:
            queryset: QuerySet a optimizar
            
        Returns:
            QuerySet optimizado
        """
        model_class = queryset.model
        
        # Verificar si el modelo tiene relación con BusinessUnit
        has_bu_relation = False
        for field in model_class._meta.get_fields():
            if field.name == 'bu' or field.name == 'business_unit':
                has_bu_relation = True
                break
        
        if has_bu_relation:
            # Optimizar consulta con select_related para bu
            queryset = queryset.select_related('bu')
        
        return queryset


# Decoradores para optimización automática

def cached_query(timeout: int = 300, key_prefix: str = None, 
                include_user: bool = False, include_bu: bool = False):
    """
    Decorador para cachear resultados de consultas en todo el sistema.
    
    Args:
        timeout: Tiempo de expiración en segundos
        key_prefix: Prefijo personalizado para la clave de caché
        include_user: Si se debe incluir el usuario en la clave de caché
        include_bu: Si se debe incluir la BU en la clave de caché
        
    Returns:
        Decorador configurado
    """
    def decorator(func: Callable[..., QuerySet]) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Generar clave de caché
            if key_prefix:
                prefix = key_prefix
            else:
                prefix = f"{func.__module__}.{func.__name__}"
            
            # Crear clave base
            key_parts = [prefix]
            
            # Añadir usuario si es necesario
            if include_user:
                request = None
                for arg in args:
                    if hasattr(arg, 'user') and hasattr(arg, 'method'):
                        request = arg
                        break
                
                if request and hasattr(request, 'user') and request.user.is_authenticated:
                    key_parts.append(f"user_{request.user.id}")
                else:
                    key_parts.append("user_anonymous")
                    
            # Añadir BU si es necesario
            if include_bu:
                request = None
                for arg in args:
                    if hasattr(arg, 'user') and hasattr(arg, 'method'):
                        request = arg
                        break
                
                bu_id = None
                if request:
                    bu_id = request.GET.get('bu_id') or getattr(request, 'active_bu_id', None)
                
                if bu_id:
                    key_parts.append(f"bu_{bu_id}")
            
            # Añadir parámetros determinantes
            for arg in args[1:]:  # Excluir self
                key_parts.append(str(arg))
                
            for k, v in sorted(kwargs.items()):
                key_parts.append(f"{k}_{v}")
                
            cache_key = ":".join(key_parts)
            
            # Intentar obtener de caché
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Ejecutar consulta
            start_time = time.time()
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            
            # Si es muy lento, loguear para análisis
            if duration > 0.5:  # 500ms
                logger.warning(f"Slow query detected: {func.__name__} took {duration:.3f}s")
            
            # Solo cachear si es un QuerySet o lista
            if isinstance(result, (QuerySet, list)):
                cache.set(cache_key, result, timeout)
            
            return result
        return wrapper
    return decorator


def optimized_query(select_related: List[str] = None, prefetch_related: List[str] = None,
                   apply_default_optimizations: bool = True, apply_bu_optimizations: bool = True):
    """
    Decorador para optimizar QuerySets automáticamente en todo el sistema.
    
    Args:
        select_related: Campos específicos para select_related
        prefetch_related: Campos específicos para prefetch_related
        apply_default_optimizations: Si aplicar optimizaciones por defecto
        apply_bu_optimizations: Si aplicar optimizaciones de BU
        
    Returns:
        Decorador configurado
    """
    def decorator(func: Callable[..., QuerySet]) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            
            # Si no es QuerySet, devolver sin modificar
            if not isinstance(result, QuerySet):
                return result
            
            # Aplicar optimizaciones específicas
            if select_related or prefetch_related:
                result = QueryOptimizer.optimize_query(
                    result,
                    select_related=select_related,
                    prefetch_related=prefetch_related
                )
            
            # Aplicar optimizaciones predeterminadas
            if apply_default_optimizations:
                result = QueryOptimizer.apply_optimized_query(result)
            
            # Aplicar optimizaciones de BU
            if apply_bu_optimizations:
                result = QueryOptimizer.optimize_for_business_units(result)
            
            return result
        return wrapper
    return decorator


class AsyncQuerySet:
    """
    Clase para convertir QuerySets a operaciones asíncronas eficientes.
    Facilita el uso de operaciones de base de datos en código asíncrono.
    """
    
    def __init__(self, queryset: QuerySet):
        """
        Inicializa el wrapper asíncrono.
        
        Args:
            queryset: QuerySet original a convertir
        """
        self.queryset = queryset
    
    async def all(self):
        """Versión asíncrona de QuerySet.all()"""
        return await sync_to_async(list)(self.queryset)
    
    async def get(self, **kwargs):
        """Versión asíncrona de QuerySet.get()"""
        get_func = sync_to_async(self.queryset.get)
        return await get_func(**kwargs)
    
    async def filter(self, **kwargs):
        """Versión asíncrona de QuerySet.filter()"""
        filtered = self.queryset.filter(**kwargs)
        return AsyncQuerySet(filtered)
    
    async def exclude(self, **kwargs):
        """Versión asíncrona de QuerySet.exclude()"""
        excluded = self.queryset.exclude(**kwargs)
        return AsyncQuerySet(excluded)
    
    async def update(self, **kwargs):
        """Versión asíncrona de QuerySet.update()"""
        update_func = sync_to_async(self.queryset.update)
        return await update_func(**kwargs)
    
    async def delete(self):
        """Versión asíncrona de QuerySet.delete()"""
        delete_func = sync_to_async(self.queryset.delete)
        return await delete_func()
    
    async def count(self):
        """Versión asíncrona de QuerySet.count()"""
        count_func = sync_to_async(self.queryset.count)
        return await count_func()
    
    async def first(self):
        """Versión asíncrona de QuerySet.first()"""
        first_func = sync_to_async(lambda qs: qs.first())
        return await first_func(self.queryset)
    
    async def last(self):
        """Versión asíncrona de QuerySet.last()"""
        last_func = sync_to_async(lambda qs: qs.last())
        return await last_func(self.queryset)
    
    async def exists(self):
        """Versión asíncrona de QuerySet.exists()"""
        exists_func = sync_to_async(self.queryset.exists)
        return await exists_func()
    
    async def values(self, *fields):
        """Versión asíncrona de QuerySet.values()"""
        values = self.queryset.values(*fields)
        return await sync_to_async(list)(values)
    
    async def values_list(self, *fields, flat=False):
        """Versión asíncrona de QuerySet.values_list()"""
        values_list = self.queryset.values_list(*fields, flat=flat)
        return await sync_to_async(list)(values_list)


def async_queryset(model_or_queryset: Union[Type[models.Model], QuerySet]) -> AsyncQuerySet:
    """
    Convierte un modelo o queryset a una versión asíncrona.
    
    Args:
        model_or_queryset: Modelo o QuerySet a convertir
    
    Returns:
        AsyncQuerySet
    """
    if isinstance(model_or_queryset, type) and issubclass(model_or_queryset, models.Model):
        return AsyncQuerySet(model_or_queryset.objects.all())
    elif isinstance(model_or_queryset, QuerySet):
        return AsyncQuerySet(model_or_queryset)
    else:
        raise TypeError("Input must be a Model class or QuerySet")


class QueryPerformanceAnalyzer:
    """
    Clase para analizar y optimizar consultas SQL en todo el sistema.
    Permite identificar y resolver problemas de rendimiento de base de datos.
    """
    
    @classmethod
    def analyze_query(cls, queryset: QuerySet) -> Dict:
        """
        Analiza una consulta y proporciona información de rendimiento.
        
        Args:
            queryset: QuerySet a analizar
            
        Returns:
            Dict con información de análisis
        """
        # Extraer consulta SQL
        sql, params = queryset.query.sql_with_params()
        
        # Obtener número de joins
        joins_count = sql.count('JOIN')
        
        # Verificar si tiene índices adecuados
        has_where = 'WHERE' in sql
        has_order_by = 'ORDER BY' in sql
        
        # Ejecutar EXPLAIN
        from django.db import connection
        
        explain_results = []
        with connection.cursor() as cursor:
            try:
                cursor.execute(f"EXPLAIN {sql}", params)
                explain_results = cursor.fetchall()
            except Exception as e:
                logger.error(f"Error analyzing query: {str(e)}")
                
        # Analizar resultados
        analysis = {
            'sql': sql,
            'joins_count': joins_count,
            'has_where': has_where,
            'has_order_by': has_order_by,
            'explain_results': explain_results,
            'recommendations': []
        }
        
        # Generar recomendaciones
        if joins_count > 3:
            analysis['recommendations'].append(
                "La consulta tiene muchos JOINs. Considere usar select_related/prefetch_related."
            )
            
        if has_where and not analysis.get('explain_results'):
            analysis['recommendations'].append(
                "La consulta tiene filtros WHERE sin índices aparentes. Considere añadir índices."
            )
            
        if has_order_by and not analysis.get('explain_results'):
            analysis['recommendations'].append(
                "La consulta tiene ORDER BY sin índices aparentes. Considere añadir índices."
            )
            
        return analysis
    
    @classmethod
    def log_slow_queries(cls, threshold: float = 0.5):
        """
        Registra consultas lentas para análisis posterior.
        
        Args:
            threshold: Umbral en segundos para considerar una consulta como lenta
        """
        from django.db import connection
        
        for query in connection.queries:
            if float(query.get('time', 0)) > threshold:
                logger.warning(f"Slow query detected: {query.get('sql')[:500]}... took {query.get('time')}s")
                
    @classmethod
    def suggest_indexes(cls, model_class: Type[models.Model]) -> List[str]:
        """
        Sugiere índices para un modelo basados en patrones de uso.
        
        Args:
            model_class: Clase del modelo a analizar
            
        Returns:
            Lista de sugerencias de índices
        """
        suggestions = []
        
        # Analizar filtros comunes
        for field in model_class._meta.fields:
            if isinstance(field, (models.CharField, models.TextField)):
                if 'name' in field.name.lower() or 'title' in field.name.lower():
                    suggestions.append(f"Considere añadir índice a {field.name} para búsquedas")
                    
            if isinstance(field, models.DateField):
                if 'date' in field.name.lower() or 'created' in field.name.lower():
                    suggestions.append(f"Considere añadir índice a {field.name} para filtros temporales")
                    
            if field.name == 'bu_id' or field.name == 'business_unit_id':
                suggestions.append(f"Asegúrese de tener índice en {field.name} para filtros de BU")
                
        return suggestions
