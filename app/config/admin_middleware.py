# Ubicación del archivo: /home/pablo/app/config/admin_middleware.py
"""
Middleware para auditoría y monitoreo de operaciones administrativas.

Este middleware registra todas las operaciones realizadas en el panel de
administración para fines de auditoría y seguridad, siguiendo las reglas
globales de Grupo huntRED®.
"""

import json
import logging
import time
from datetime import datetime
from django.utils import timezone
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.contenttypes.models import ContentType
from django.db import connection
from django.conf import settings

logger = logging.getLogger('admin_audit')

class AdminAuditMiddleware:
    """
    Middleware para auditar operaciones administrativas.
    
    Este middleware captura y registra todas las operaciones realizadas
    en el panel de administración, generando logs detallados y registros
    en la base de datos para fines de auditoría y seguridad.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        """Procesando request/response y auditando operaciones admin."""
        is_admin = request.path.startswith('/admin/')
        
        # Registrando inicio de la petición
        start_time = time.time()
        
        if is_admin:
            self._log_admin_request(request)
            
        # Procesando la petición
        response = self.get_response(request)
        
        # Registrando resultado de la petición
        if is_admin:
            process_time = time.time() - start_time
            self._log_admin_response(request, response, process_time)
        
        return response
        
    def _log_admin_request(self, request):
        """Registrando detalles de la petición administrativa."""
        if not request.user.is_authenticated:
            return
            
        # Datos básicos de la petición
        log_data = {
            'timestamp': timezone.now().isoformat(),
            'user': request.user.username,
            'method': request.method,
            'path': request.path,
            'is_ajax': request.headers.get('X-Requested-With') == 'XMLHttpRequest',
            'is_secure': request.is_secure(),
            'remote_addr': self._get_client_ip(request),
            'business_unit': self._extract_business_unit(request),
        }
        
        # Datos específicos según el método HTTP
        if request.method in ['POST', 'PUT', 'PATCH']:
            # Evitando registrar datos sensibles
            safe_data = self._sanitize_request_data(request.POST)
            log_data['data'] = safe_data
        
        # Registrando en el log
        logger.info(f"ADMIN REQUEST: {json.dumps(log_data)}")
    
    def _log_admin_response(self, request, response, process_time):
        """Registrando detalles de la respuesta administrativa."""
        if not request.user.is_authenticated:
            return
            
        # Datos básicos de la respuesta
        log_data = {
            'timestamp': timezone.now().isoformat(),
            'user': request.user.username,
            'path': request.path,
            'status_code': response.status_code,
            'process_time': f"{process_time:.4f}s",
            'db_queries': len(connection.queries),
        }
        
        # Datos específicos para cambios en la BD
        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE'] and hasattr(response, 'status_code'):
            # Detectando tipo de operación
            if 'add' in request.path:
                operation = 'addition'
            elif 'delete' in request.path:
                operation = 'deletion'
            elif 'change' in request.path:
                operation = 'change'
            else:
                operation = 'unknown'
                
            log_data['operation'] = operation
            
            # Intentando extraer el modelo afectado
            model_name = self._extract_model_name(request.path)
            if model_name:
                log_data['model'] = model_name
        
        # Registrando en el log
        logger.info(f"ADMIN RESPONSE: {json.dumps(log_data)}")
        
        # Si es una operación que modificó datos, registrar en LogEntry
        self._create_log_entry(request, response, log_data)
    
    def _create_log_entry(self, request, response, log_data):
        """Creando entrada en LogEntry para operaciones importantes."""
        # Solo registrar operaciones exitosas que modifican datos
        if request.method not in ['POST', 'PUT', 'PATCH', 'DELETE'] or response.status_code >= 400:
            return
            
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return
            
        # Solo procesar si hay suficiente información
        if 'operation' not in log_data or 'model' not in log_data:
            return
            
        try:
            # Mapeando operación a constantes de LogEntry
            action_flag = {
                'addition': ADDITION,
                'change': CHANGE,
                'deletion': DELETION
            }.get(log_data['operation'], CHANGE)
            
            # Intentando obtener ContentType
            app_label, model = self._parse_model_path(log_data['model'])
            if not app_label or not model:
                return
                
            content_type = ContentType.objects.get(app_label=app_label, model=model)
            
            # Determinando object_id
            object_id = self._extract_object_id(request.path)
            if not object_id and action_flag != ADDITION:
                return
                
            # Creando entrada de log
            LogEntry.objects.create(
                user_id=request.user.id,
                content_type_id=content_type.id,
                object_id=object_id or 0,
                object_repr=f"{model.title()} {object_id or 'nuevo'}",
                action_flag=action_flag,
                change_message=json.dumps([{
                    "time": log_data.get('process_time', ''),
                    "ip": log_data.get('remote_addr', ''),
                    "bu": log_data.get('business_unit', '')
                }])
            )
        except Exception as e:
            logger.error(f"Error creando LogEntry: {str(e)}")
    
    def _sanitize_request_data(self, data):
        """Sanitizando datos de la petición para eliminar información sensible."""
        if not data:
            return {}
            
        # Copiando datos para no modificar el original
        safe_data = {}
        
        # Lista de campos a excluir (sensibles)
        sensitive_fields = [
            'password', 'token', 'secret', 'key', 'api_key', 'auth',
            'session', 'cookie', 'csrf', 'card', 'credit', 'ccv'
        ]
        
        # Copiando solo datos seguros
        for key, value in data.items():
            # Verificando si es un campo sensible
            is_sensitive = any(field in key.lower() for field in sensitive_fields)
            
            if is_sensitive:
                safe_data[key] = '*** REDACTED ***'
            else:
                # Truncando valores muy largos
                if isinstance(value, str) and len(value) > 200:
                    safe_data[key] = value[:200] + '... [truncated]'
                else:
                    safe_data[key] = value
        
        return safe_data
        
    def _get_client_ip(self, request):
        """Obteniendo IP real del cliente considerando proxies."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # Tomando la primera IP (cliente original)
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', 'unknown')
        return ip
    
    def _extract_business_unit(self, request):
        """Extrayendo Business Unit relacionada con la petición."""
        # Intentando extraer de la URL
        path_parts = request.path.split('/')
        for i, part in enumerate(path_parts):
            if part == 'business_unit' and i + 1 < len(path_parts):
                return path_parts[i + 1]
        
        # Intentando extraer de los parámetros
        bu = request.GET.get('business_unit', None)
        if bu:
            return bu
            
        # Intentando extraer de los datos POST
        bu = request.POST.get('business_unit', None)
        if bu:
            return bu
            
        return 'unknown'
    
    def _extract_model_name(self, path):
        """Extrayendo nombre del modelo desde la URL."""
        # Formato típico: /admin/app_label/model/action/
        parts = path.strip('/').split('/')
        if len(parts) >= 3 and parts[0] == 'admin':
            return f"{parts[1]}/{parts[2]}"
        return None
    
    def _parse_model_path(self, model_path):
        """Parseando ruta del modelo en app_label y model."""
        if not model_path or '/' not in model_path:
            return None, None
            
        parts = model_path.split('/')
        if len(parts) == 2:
            return parts[0], parts[1]
            
        return None, None
    
    def _extract_object_id(self, path):
        """Extrayendo ID del objeto desde la URL."""
        # Formato típico para edición: /admin/app_label/model/object_id/change/
        parts = path.strip('/').split('/')
        if len(parts) >= 4 and parts[-1] in ['change', 'delete']:
            try:
                return int(parts[-2])
            except (ValueError, IndexError):
                pass
        return None


class AdminPerformanceMiddleware:
    """
    Middleware para monitorear rendimiento de operaciones administrativas.
    
    Este middleware captura métricas de rendimiento para las operaciones
    en el panel de administración, generando alertas para operaciones lentas
    y proporcionando datos para optimización.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        # Umbral de tiempo para operaciones lentas (en segundos)
        self.slow_threshold = getattr(settings, 'ADMIN_SLOW_THRESHOLD', 1.0)
        
    def __call__(self, request):
        # Solo procesar peticiones administrativas
        if not request.path.startswith('/admin/'):
            return self.get_response(request)
            
        # Registrando tiempo y estado inicial
        start_time = time.time()
        initial_queries_count = len(connection.queries)
        
        # Procesando la petición
        response = self.get_response(request)
        
        # Calculando métricas
        process_time = time.time() - start_time
        queries_count = len(connection.queries) - initial_queries_count
        
        # Registrando métricas
        self._log_performance_metrics(request, response, process_time, queries_count)
        
        # Alertando si es una operación lenta
        if process_time > self.slow_threshold:
            self._alert_slow_operation(request, process_time, queries_count)
        
        return response
        
    def _log_performance_metrics(self, request, response, process_time, queries_count):
        """Registrando métricas de rendimiento."""
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return
            
        metrics = {
            'timestamp': timezone.now().isoformat(),
            'user': request.user.username,
            'path': request.path,
            'method': request.method,
            'status_code': response.status_code,
            'process_time': f"{process_time:.4f}s",
            'queries_count': queries_count,
        }
        
        logger.info(f"ADMIN PERFORMANCE: {json.dumps(metrics)}")
    
    def _alert_slow_operation(self, request, process_time, queries_count):
        """Generando alerta para operación lenta."""
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return
            
        alert = {
            'level': 'WARNING',
            'message': f"Operación administrativa lenta detectada",
            'timestamp': timezone.now().isoformat(),
            'user': request.user.username,
            'path': request.path,
            'method': request.method,
            'process_time': f"{process_time:.4f}s",
            'queries_count': queries_count,
            'threshold': f"{self.slow_threshold:.2f}s",
        }
        
        # Incluyendo detalles de las consultas si están disponibles
        if settings.DEBUG and hasattr(connection, 'queries'):
            slow_queries = [
                {'sql': q['sql'], 'time': q['time']} 
                for q in connection.queries[-queries_count:]
                if float(q['time']) > 0.1  # Filtrando consultas lentas
            ]
            
            if slow_queries:
                alert['slow_queries'] = slow_queries[:5]  # Limitando a 5 consultas
        
        logger.warning(f"SLOW ADMIN OPERATION: {json.dumps(alert)}")
        
        # Aquí se podrían enviar notificaciones adicionales
        # como Slack, correo, etc. para alertar a los administradores
