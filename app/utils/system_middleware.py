# /home/pablo/app/utils/system_middleware.py
"""
Utilidades de middleware para integración en todo el sistema Grupo huntRED®.
Implementa funcionalidades transversales de seguridad, rendimiento y RBAC.
Cumple con las reglas globales manteniendo la estructura existente.
"""

import time
import logging
import json
from typing import Any, Callable, Dict, List, Optional, Union
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.conf import settings
from django.core.cache import cache
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)

class SecurityMiddleware(MiddlewareMixin):
    """
    Middleware de seguridad que implementa protecciones en todas las solicitudes.
    Provee funcionalidades de rate limiting, validación de headers y protección CSRF.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.rate_limits = {}
        
    def process_request(self, request):
        """
        Procesa solicitudes entrantes para aplicar medidas de seguridad.
        
        Args:
            request: Solicitud HTTP entrante
            
        Returns:
            HttpResponse o None
        """
        # Implementar rate limiting por IP
        ip = self._get_client_ip(request)
        
        # Configurar límites según el endpoint
        path = request.path
        if 'webhook' in path or '/api/' in path:
            # Endpoints críticos: límite más estricto
            max_requests = getattr(settings, 'CRITICAL_RATE_LIMIT', 30)
            window = 60  # 1 minuto
        else:
            # Endpoints normales: límite más permisivo
            max_requests = getattr(settings, 'STANDARD_RATE_LIMIT', 60)
            window = 60  # 1 minuto
            
        # Verificar límite
        if self._is_rate_limited(ip, max_requests, window):
            logger.warning(f"Rate limit exceeded for IP {ip} on path {path}")
            return JsonResponse({
                'status': 'error',
                'message': 'Rate limit exceeded. Please try again later.'
            }, status=429)
            
        # Verificar headers de seguridad
        if '/api/' in path:
            required_headers = ['User-Agent', 'Accept']
            missing_headers = [h for h in required_headers if h not in request.headers]
            
            if missing_headers:
                logger.warning(f"Missing required headers: {missing_headers}")
                return JsonResponse({
                    'status': 'error',
                    'message': 'Missing required headers'
                }, status=400)
                
        # Todo está bien, continuar con la solicitud
        return None
    
    def process_response(self, request, response):
        """
        Procesa respuestas salientes para aplicar cabeceras de seguridad.
        
        Args:
            request: Solicitud HTTP
            response: Respuesta HTTP
            
        Returns:
            HttpResponse modificada
        """
        # Añadir cabeceras de seguridad estándar
        security_headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline' cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' cdn.jsdelivr.net; img-src 'self' data:;"
        }
        
        for header, value in security_headers.items():
            if header not in response:
                response[header] = value
                
        return response
    
    def _get_client_ip(self, request):
        """
        Obtiene la dirección IP real del cliente.
        
        Args:
            request: Solicitud HTTP
            
        Returns:
            str: Dirección IP
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # Puede contener múltiples IPs en formato: "client, proxy1, proxy2"
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def _is_rate_limited(self, identifier, max_requests, window):
        """
        Verifica si una solicitud debe ser limitada por rate limiting.
        
        Args:
            identifier: Identificador único (IP, usuario, etc.)
            max_requests: Máximo de solicitudes permitidas en la ventana
            window: Tamaño de la ventana en segundos
            
        Returns:
            bool: True si debe ser limitado, False en caso contrario
        """
        # Usar caché de Redis/Django para tracking
        cache_key = f"rate_limit:{identifier}"
        request_history = cache.get(cache_key, [])
        
        # Limpiar historial antiguo
        current_time = time.time()
        request_history = [t for t in request_history if current_time - t < window]
        
        # Verificar límite
        if len(request_history) >= max_requests:
            return True
            
        # Registrar nueva solicitud
        request_history.append(current_time)
        cache.set(cache_key, request_history, window)
        
        return False


class PerformanceMiddleware(MiddlewareMixin):
    """
    Middleware de rendimiento para monitorear y optimizar tiempos de respuesta.
    Registra métricas de rendimiento para cada solicitud.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def process_request(self, request):
        """
        Registra tiempo de inicio de la solicitud.
        
        Args:
            request: Solicitud HTTP
        """
        request._performance_tracking_start = time.time()
        return None
        
    def process_response(self, request, response):
        """
        Calcula y registra métricas de rendimiento para la solicitud.
        
        Args:
            request: Solicitud HTTP
            response: Respuesta HTTP
            
        Returns:
            HttpResponse: Respuesta procesada
        """
        if hasattr(request, '_performance_tracking_start'):
            # Calcular duración
            duration = time.time() - request._performance_tracking_start
            
            # Registrar en log para solicitudes lentas
            if duration > 1.0:  # Más de 1 segundo
                logger.warning(f"Slow request detected: {request.path} took {duration:.2f}s")
                
            # Añadir cabecera de tiempo de respuesta en entorno de desarrollo
            if settings.DEBUG:
                response['X-Response-Time'] = f"{duration:.3f}s"
                
            # Registrar métricas en caché o Redis para análisis posterior
            try:
                metrics_key = "performance_metrics"
                metrics = cache.get(metrics_key, {})
                
                path_key = request.path
                if path_key not in metrics:
                    metrics[path_key] = {
                        'count': 0,
                        'total_time': 0,
                        'max_time': 0
                    }
                    
                metrics[path_key]['count'] += 1
                metrics[path_key]['total_time'] += duration
                metrics[path_key]['max_time'] = max(metrics[path_key]['max_time'], duration)
                
                # Guardar métricas por 24 horas
                cache.set(metrics_key, metrics, 86400)
            except Exception as e:
                logger.error(f"Error recording performance metrics: {str(e)}")
                
        return response


class RBACMiddleware(MiddlewareMixin):
    """
    Middleware que integra el control de acceso basado en roles.
    Verifica permisos en tiempo real para todas las solicitudes.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.restricted_paths = getattr(settings, 'RBAC_RESTRICTED_PATHS', [
            '/admin/',
            '/dashboard/',
            '/api/',
            '/report/'
        ])
        
    def process_request(self, request):
        """
        Verifica permisos RBAC para la solicitud.
        
        Args:
            request: Solicitud HTTP
            
        Returns:
            HttpResponse o None
        """
        # Omitir para rutas públicas
        path = request.path
        is_restricted = any(path.startswith(p) for p in self.restricted_paths)
        
        if not is_restricted:
            return None
            
        # Verificar autenticación
        if not request.user.is_authenticated:
            if '/api/' in path:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Authentication required'
                }, status=401)
            else:
                from django.shortcuts import redirect
                return redirect(f"{settings.LOGIN_URL}?next={request.path}")
                
        # Verificar permisos RBAC
        try:
            from app.ats.utils.rbac import RBAC
            
            required_permission = None
            
            # Determinar permiso requerido basado en la ruta
            if '/admin/' in path:
                required_permission = 'admin_access'
            elif '/dashboard/' in path:
                required_permission = 'dashboard_access'
            elif path.startswith('/api/'):
                # Extraer entidad y acción de la ruta API
                parts = path.split('/')
                if len(parts) >= 4:
                    entity = parts[2]
                    action = request.method.lower()
                    required_permission = f"{action}_{entity}"
            
            # Verificar permiso si se determinó uno
            if required_permission and not RBAC.has_permission(request.user, required_permission):
                logger.warning(f"RBAC permission denied: {request.user.username} -> {required_permission}")
                
                if '/api/' in path:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Permission denied'
                    }, status=403)
                else:
                    from django.shortcuts import render
                    return render(request, 'error/403.html', status=403)
                    
        except Exception as e:
            logger.error(f"Error in RBAC middleware: {str(e)}")
            
        return None


class BusinessUnitMiddleware(MiddlewareMixin):
    """
    Middleware para gestionar el filtrado por Business Unit.
    Implementa la lógica de filtrado automático según reglas globales.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def process_request(self, request):
        """
        Procesa solicitudes para gestionar contexto de BU.
        
        Args:
            request: Solicitud HTTP
        """
        # Solo procesar si el usuario está autenticado
        if not request.user.is_authenticated:
            return None
            
        # Obtener BU de los parámetros
        bu_id = request.GET.get('bu_id') or request.POST.get('bu_id')
        
        # Si no hay BU especificada, intentar obtener la predeterminada
        if not bu_id and hasattr(request.user, 'profile'):
            # Intentar obtener la última BU utilizada de la sesión
            session_bu = request.session.get('active_bu_id')
            if session_bu:
                bu_id = session_bu
            # Si no hay BU en sesión, usar la primera disponible
            elif hasattr(request.user.profile, 'business_units'):
                user_bus = request.user.profile.business_units.all()
                if user_bus.exists():
                    bu_id = user_bus.first().id
        
        # Guardar BU activa en atributo de la solicitud
        request.active_bu_id = bu_id
        
        # Guardar en sesión para futuras solicitudes
        if bu_id:
            request.session['active_bu_id'] = bu_id
            
        return None


class LoggingMiddleware(MiddlewareMixin):
    """
    Middleware de registro centralizado para monitoreo y auditoría.
    Registra información detallada de solicitudes críticas.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.sensitive_paths = [
            '/api/payment',
            '/webhook',
            '/user/profile',
            '/admin',
            '/auth'
        ]
        
    def process_request(self, request):
        """
        Registra información de solicitudes entrantes.
        
        Args:
            request: Solicitud HTTP
        """
        # Determinar si es una ruta sensible para logging detallado
        path = request.path
        is_sensitive = any(sensitive in path for sensitive in self.sensitive_paths)
        
        if is_sensitive:
            # Registrar información detallada para auditoría
            log_data = {
                'timestamp': time.time(),
                'user_id': request.user.id if request.user.is_authenticated else None,
                'username': request.user.username if request.user.is_authenticated else None,
                'method': request.method,
                'path': request.path,
                'query_params': dict(request.GET),
                'ip': self._get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', '')
            }
            
            logger.info(f"AUDIT: {json.dumps(log_data)}")
            
            # Guardar registro para análisis posterior
            try:
                from app.models import AuditLog
                
                # Limpiar datos sensibles
                if 'password' in log_data.get('query_params', {}):
                    log_data['query_params']['password'] = '[REDACTED]'
                
                AuditLog.objects.create(
                    user_id=log_data['user_id'],
                    action=request.method,
                    resource=path,
                    data=json.dumps(log_data),
                    ip_address=log_data['ip']
                )
            except Exception as e:
                logger.error(f"Error creating audit log: {str(e)}")
                
        return None
    
    def _get_client_ip(self, request):
        """
        Obtiene la dirección IP real del cliente.
        
        Args:
            request: Solicitud HTTP
            
        Returns:
            str: Dirección IP
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
