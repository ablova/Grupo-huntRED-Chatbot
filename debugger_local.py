#!/usr/bin/env python3
"""
DEBUGGER COMPLETO LOCAL para Grupo huntRED®
Réplica exacta de la configuración del servidor con capacidades avanzadas de debugging

Autor: Assistant
Fecha: 2025-01-27
"""

import os
import sys
import json
import time
import psutil
import logging
import traceback
import threading
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict, deque

import redis
import psycopg2
from psycopg2.extras import RealDictCursor
import django
from django.conf import settings
from django.core.management import execute_from_command_line
from django.db import connections
from django.test.utils import get_runner
import celery
from celery import Celery
import requests

# Configuración del debugger
DEBUG_CONFIG = {
    'log_level': 'DEBUG',
    'log_format': '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    'log_file': 'debugger.log',
    'max_log_size': 50 * 1024 * 1024,  # 50MB
    'backup_count': 5,
    'enable_profiling': True,
    'enable_memory_tracking': True,
    'enable_performance_monitoring': True,
    'monitor_interval': 5,  # segundos
    'alert_thresholds': {
        'cpu_percent': 80,
        'memory_percent': 85,
        'disk_percent': 90,
        'response_time': 5.0,
    }
}

@dataclass
class SystemMetrics:
    """Métricas del sistema"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_percent: float
    disk_used_gb: float
    disk_free_gb: float
    load_average: List[float]
    active_connections: int
    python_processes: int

@dataclass
class DatabaseMetrics:
    """Métricas de la base de datos"""
    timestamp: datetime
    active_connections: int
    idle_connections: int
    max_connections: int
    slow_queries: int
    database_size_mb: float
    table_count: int
    index_count: int

@dataclass
class CeleryMetrics:
    """Métricas de Celery"""
    timestamp: datetime
    active_tasks: int
    scheduled_tasks: int
    failed_tasks: int
    successful_tasks: int
    workers_online: int
    queue_length: int

@dataclass
class ApplicationMetrics:
    """Métricas de la aplicación"""
    timestamp: datetime
    response_times: List[float]
    error_count: int
    request_count: int
    cache_hit_ratio: float
    session_count: int

class Logger:
    """Sistema de logging avanzado"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.setup_logging()
        
    def setup_logging(self):
        """Configura el sistema de logging"""
        # Crear directorio de logs si no existe
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)
        
        # Configurar el logger principal
        self.logger = logging.getLogger('debugger')
        self.logger.setLevel(getattr(logging, self.config['log_level']))
        
        # Handler para archivo con rotación
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(
            log_dir / self.config['log_file'],
            maxBytes=self.config['max_log_size'],
            backupCount=self.config['backup_count']
        )
        file_handler.setLevel(logging.DEBUG)
        
        # Handler para consola
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(self.config['log_format'])
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Agregar handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        # Loggers específicos para diferentes componentes
        self.setup_component_loggers()
    
    def setup_component_loggers(self):
        """Configura loggers específicos para cada componente"""
        components = ['django', 'celery', 'redis', 'postgres', 'performance', 'security']
        
        for component in components:
            logger = logging.getLogger(f'debugger.{component}')
            logger.setLevel(logging.DEBUG)
            
            # Handler específico para el componente
            handler = logging.FileHandler(f'logs/{component}.log')
            handler.setFormatter(logging.Formatter(self.config['log_format']))
            logger.addHandler(handler)
    
    def log(self, level: str, message: str, component: str = 'main', **kwargs):
        """Log con metadatos adicionales"""
        logger = logging.getLogger(f'debugger.{component}')
        log_data = {
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'component': component,
            **kwargs
        }
        
        getattr(logger, level.lower())(json.dumps(log_data, ensure_ascii=False))

class SystemMonitor:
    """Monitor del sistema"""
    
    def __init__(self, logger: Logger):
        self.logger = logger
        self.metrics_history = deque(maxlen=1000)
        self.alerts = []
        
    def get_system_metrics(self) -> SystemMetrics:
        """Obtiene métricas del sistema"""
        # CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memoria
        memory = psutil.virtual_memory()
        
        # Disco
        disk = psutil.disk_usage('/')
        
        # Load average (solo en Unix)
        try:
            load_avg = list(os.getloadavg())
        except:
            load_avg = [0.0, 0.0, 0.0]
        
        # Conexiones activas
        connections = len(psutil.net_connections())
        
        # Procesos Python
        python_processes = len([p for p in psutil.process_iter(['name']) 
                               if 'python' in p.info['name'].lower()])
        
        metrics = SystemMetrics(
            timestamp=datetime.now(),
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            memory_used_mb=memory.used / 1024 / 1024,
            memory_available_mb=memory.available / 1024 / 1024,
            disk_percent=disk.percent,
            disk_used_gb=disk.used / 1024 / 1024 / 1024,
            disk_free_gb=disk.free / 1024 / 1024 / 1024,
            load_average=load_avg,
            active_connections=connections,
            python_processes=python_processes
        )
        
        self.metrics_history.append(metrics)
        self.check_alerts(metrics)
        
        return metrics
    
    def check_alerts(self, metrics: SystemMetrics):
        """Verifica alertas del sistema"""
        thresholds = DEBUG_CONFIG['alert_thresholds']
        
        if metrics.cpu_percent > thresholds['cpu_percent']:
            alert = f"CPU alta: {metrics.cpu_percent:.1f}%"
            self.logger.log('warning', alert, 'performance')
            
        if metrics.memory_percent > thresholds['memory_percent']:
            alert = f"Memoria alta: {metrics.memory_percent:.1f}%"
            self.logger.log('warning', alert, 'performance')
            
        if metrics.disk_percent > thresholds['disk_percent']:
            alert = f"Disco lleno: {metrics.disk_percent:.1f}%"
            self.logger.log('warning', alert, 'performance')

class DatabaseMonitor:
    """Monitor de la base de datos PostgreSQL"""
    
    def __init__(self, logger: Logger):
        self.logger = logger
        self.connection_params = self._get_db_params()
        
    def _get_db_params(self) -> Dict[str, str]:
        """Obtiene parámetros de conexión de la configuración Django"""
        try:
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_huntred.settings.development')
            django.setup()
            
            db_config = settings.DATABASES['default']
            return {
                'host': db_config['HOST'],
                'port': db_config['PORT'],
                'database': db_config['NAME'],
                'user': db_config['USER'],
                'password': db_config['PASSWORD']
            }
        except Exception as e:
            self.logger.log('error', f"Error obteniendo config DB: {e}", 'postgres')
            return {}
    
    def get_database_metrics(self) -> Optional[DatabaseMetrics]:
        """Obtiene métricas de la base de datos"""
        if not self.connection_params:
            return None
            
        try:
            conn = psycopg2.connect(**self.connection_params)
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Conexiones activas
            cursor.execute("""
                SELECT state, count(*) as count 
                FROM pg_stat_activity 
                WHERE datname = current_database()
                GROUP BY state
            """)
            connections_data = {row['state']: row['count'] for row in cursor.fetchall()}
            
            # Configuración máxima de conexiones
            cursor.execute("SHOW max_connections")
            max_connections = int(cursor.fetchone()[0])
            
            # Tamaño de la base de datos
            cursor.execute("""
                SELECT pg_size_pretty(pg_database_size(current_database()))::text as size,
                       pg_database_size(current_database()) / 1024 / 1024 as size_mb
            """)
            db_size = cursor.fetchone()
            
            # Conteo de tablas e índices
            cursor.execute("""
                SELECT 
                    (SELECT count(*) FROM information_schema.tables 
                     WHERE table_schema = 'public') as table_count,
                    (SELECT count(*) FROM pg_indexes 
                     WHERE schemaname = 'public') as index_count
            """)
            counts = cursor.fetchone()
            
            # Consultas lentas (últimas 24 horas)
            cursor.execute("""
                SELECT count(*) as slow_queries
                FROM pg_stat_statements 
                WHERE mean_time > 1000 
                AND calls > 10
            """)
            slow_queries_result = cursor.fetchone()
            slow_queries = slow_queries_result['slow_queries'] if slow_queries_result else 0
            
            metrics = DatabaseMetrics(
                timestamp=datetime.now(),
                active_connections=connections_data.get('active', 0),
                idle_connections=connections_data.get('idle', 0),
                max_connections=max_connections,
                slow_queries=slow_queries,
                database_size_mb=db_size['size_mb'],
                table_count=counts['table_count'],
                index_count=counts['index_count']
            )
            
            conn.close()
            return metrics
            
        except Exception as e:
            self.logger.log('error', f"Error monitoreando DB: {e}", 'postgres')
            return None

class CeleryMonitor:
    """Monitor de Celery"""
    
    def __init__(self, logger: Logger):
        self.logger = logger
        self.celery_app = self._get_celery_app()
        
    def _get_celery_app(self) -> Optional[Celery]:
        """Obtiene la instancia de Celery"""
        try:
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_huntred.settings.development')
            from ai_huntred.celery_app import app
            return app
        except Exception as e:
            self.logger.log('error', f"Error conectando a Celery: {e}", 'celery')
            return None
    
    def get_celery_metrics(self) -> Optional[CeleryMetrics]:
        """Obtiene métricas de Celery"""
        if not self.celery_app:
            return None
            
        try:
            # Inspeccionar workers
            inspect = self.celery_app.control.inspect()
            
            # Tasks activas
            active_tasks = inspect.active()
            total_active = sum(len(tasks) for tasks in (active_tasks or {}).values())
            
            # Tasks programadas
            scheduled_tasks = inspect.scheduled()
            total_scheduled = sum(len(tasks) for tasks in (scheduled_tasks or {}).values())
            
            # Workers online
            stats = inspect.stats()
            workers_online = len(stats or {})
            
            # Estadísticas de Redis (broker)
            try:
                redis_client = redis.Redis.from_url(self.celery_app.conf.broker_url)
                queue_length = redis_client.llen('celery')
            except:
                queue_length = 0
            
            # Tasks exitosas y fallidas (estimación)
            failed_tasks = 0
            successful_tasks = 0
            
            metrics = CeleryMetrics(
                timestamp=datetime.now(),
                active_tasks=total_active,
                scheduled_tasks=total_scheduled,
                failed_tasks=failed_tasks,
                successful_tasks=successful_tasks,
                workers_online=workers_online,
                queue_length=queue_length
            )
            
            return metrics
            
        except Exception as e:
            self.logger.log('error', f"Error monitoreando Celery: {e}", 'celery')
            return None

class PerformanceProfiler:
    """Profiler de rendimiento"""
    
    def __init__(self, logger: Logger):
        self.logger = logger
        self.request_times = deque(maxlen=1000)
        self.error_count = 0
        self.request_count = 0
        
    def profile_function(self, func):
        """Decorator para perfilar funciones"""
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                success = True
            except Exception as e:
                self.error_count += 1
                self.logger.log('error', f"Error en {func.__name__}: {e}", 'performance')
                raise
            finally:
                end_time = time.time()
                execution_time = end_time - start_time
                self.request_times.append(execution_time)
                self.request_count += 1
                
                self.logger.log('debug', 
                    f"Función {func.__name__} ejecutada en {execution_time:.3f}s",
                    'performance',
                    execution_time=execution_time,
                    function_name=func.__name__
                )
                
            return result
        return wrapper
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de rendimiento"""
        if not self.request_times:
            return {}
            
        times = list(self.request_times)
        return {
            'avg_response_time': sum(times) / len(times),
            'min_response_time': min(times),
            'max_response_time': max(times),
            'total_requests': self.request_count,
            'error_rate': self.error_count / self.request_count if self.request_count > 0 else 0,
            'requests_per_second': len(times) / (times[-1] - times[0]) if len(times) > 1 else 0
        }

class SecurityMonitor:
    """Monitor de seguridad"""
    
    def __init__(self, logger: Logger):
        self.logger = logger
        self.suspicious_activities = []
        
    def check_security_issues(self):
        """Verifica problemas de seguridad"""
        issues = []
        
        # Verificar configuraciones de Django
        try:
            if settings.DEBUG:
                issues.append("DEBUG=True en producción")
                
            if not settings.SECURE_SSL_REDIRECT:
                issues.append("SSL redirect no configurado")
                
            if not settings.SESSION_COOKIE_SECURE:
                issues.append("Cookies de sesión no seguras")
                
        except Exception as e:
            self.logger.log('error', f"Error verificando seguridad: {e}", 'security')
        
        # Verificar puertos abiertos
        suspicious_ports = [21, 23, 135, 139, 445]
        for port in suspicious_ports:
            connections = [conn for conn in psutil.net_connections() 
                          if conn.laddr.port == port and conn.status == 'LISTEN']
            if connections:
                issues.append(f"Puerto sospechoso {port} abierto")
        
        # Log de issues encontrados
        for issue in issues:
            self.logger.log('warning', f"Problema de seguridad: {issue}", 'security')
        
        return issues

class HealthChecker:
    """Verificador de salud del sistema"""
    
    def __init__(self, logger: Logger):
        self.logger = logger
        
    def check_django_health(self) -> Dict[str, bool]:
        """Verifica salud de Django"""
        health = {}
        
        try:
            # Verificar conexión a la base de datos
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            health['database'] = True
        except Exception as e:
            health['database'] = False
            self.logger.log('error', f"DB health check failed: {e}", 'django')
        
        try:
            # Verificar caché
            from django.core.cache import cache
            cache.set('health_check', 'ok', 60)
            health['cache'] = cache.get('health_check') == 'ok'
        except Exception as e:
            health['cache'] = False
            self.logger.log('error', f"Cache health check failed: {e}", 'django')
        
        return health
    
    def check_external_services(self) -> Dict[str, bool]:
        """Verifica servicios externos"""
        services = {}
        
        # Verificar Sentry
        try:
            if hasattr(settings, 'SENTRY_DSN') and settings.SENTRY_DSN:
                import sentry_sdk
                sentry_sdk.capture_message("Health check", level="info")
                services['sentry'] = True
            else:
                services['sentry'] = False
        except:
            services['sentry'] = False
        
        # Verificar APIs externas (ejemplo)
        external_apis = {
            'whatsapp': getattr(settings, 'WHATSAPP_API_URL', ''),
            # Agregar más APIs según sea necesario
        }
        
        for api_name, api_url in external_apis.items():
            if api_url:
                try:
                    response = requests.get(api_url, timeout=5)
                    services[api_name] = response.status_code == 200
                except:
                    services[api_name] = False
            else:
                services[api_name] = None
        
        return services

class LocalDebugger:
    """Debugger principal"""
    
    def __init__(self):
        self.logger = Logger(DEBUG_CONFIG)
        self.system_monitor = SystemMonitor(self.logger)
        self.db_monitor = DatabaseMonitor(self.logger)
        self.celery_monitor = CeleryMonitor(self.logger)
        self.profiler = PerformanceProfiler(self.logger)
        self.security_monitor = SecurityMonitor(self.logger)
        self.health_checker = HealthChecker(self.logger)
        
        self.running = False
        self.monitor_thread = None
        
        self.logger.log('info', "Debugger local inicializado", 'main')
    
    def start_monitoring(self):
        """Inicia el monitoreo continuo"""
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        self.logger.log('info', "Monitoreo iniciado", 'main')
    
    def stop_monitoring(self):
        """Detiene el monitoreo"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join()
        self.logger.log('info', "Monitoreo detenido", 'main')
    
    def _monitor_loop(self):
        """Loop principal de monitoreo"""
        while self.running:
            try:
                # Métricas del sistema
                system_metrics = self.system_monitor.get_system_metrics()
                
                # Métricas de la base de datos
                db_metrics = self.db_monitor.get_database_metrics()
                
                # Métricas de Celery
                celery_metrics = self.celery_monitor.get_celery_metrics()
                
                # Verificaciones de seguridad
                security_issues = self.security_monitor.check_security_issues()
                
                # Health checks
                django_health = self.health_checker.check_django_health()
                external_health = self.health_checker.check_external_services()
                
                # Log de métricas
                self.logger.log('info', 
                    "Métricas del sistema recolectadas",
                    'monitoring',
                    system_metrics=asdict(system_metrics),
                    db_metrics=asdict(db_metrics) if db_metrics else None,
                    celery_metrics=asdict(celery_metrics) if celery_metrics else None,
                    security_issues=security_issues,
                    django_health=django_health,
                    external_health=external_health
                )
                
            except Exception as e:
                self.logger.log('error', f"Error en loop de monitoreo: {e}", 'monitoring')
                self.logger.log('debug', traceback.format_exc(), 'monitoring')
            
            time.sleep(DEBUG_CONFIG['monitor_interval'])
    
    def run_django_command(self, command: List[str]):
        """Ejecuta comandos de Django con profiling"""
        @self.profiler.profile_function
        def execute_command():
            execute_from_command_line(['manage.py'] + command)
        
        try:
            execute_command()
            self.logger.log('info', f"Comando Django ejecutado: {' '.join(command)}", 'django')
        except Exception as e:
            self.logger.log('error', f"Error ejecutando comando Django: {e}", 'django')
            raise
    
    def run_tests(self, test_labels: List[str] = None):
        """Ejecuta tests con profiling"""
        @self.profiler.profile_function
        def execute_tests():
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_huntred.settings.development')
            django.setup()
            
            TestRunner = get_runner(settings)
            test_runner = TestRunner()
            failures = test_runner.run_tests(test_labels or [])
            return failures
        
        try:
            failures = execute_tests()
            self.logger.log('info', f"Tests ejecutados - Fallos: {failures}", 'django')
            return failures
        except Exception as e:
            self.logger.log('error', f"Error ejecutando tests: {e}", 'django')
            raise
    
    def generate_report(self) -> Dict[str, Any]:
        """Genera reporte completo del sistema"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'system_info': {
                'python_version': sys.version,
                'platform': os.name,
                'working_directory': os.getcwd(),
            },
            'performance_stats': self.profiler.get_performance_stats(),
            'recent_metrics': {
                'system': [asdict(m) for m in list(self.system_monitor.metrics_history)[-10:]],
            },
            'health_checks': {
                'django': self.health_checker.check_django_health(),
                'external_services': self.health_checker.check_external_services(),
            },
            'security_status': self.security_monitor.check_security_issues(),
        }
        
        # Guardar reporte
        report_file = f"debug_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        
        self.logger.log('info', f"Reporte generado: {report_file}", 'main')
        return report
    
    def interactive_shell(self):
        """Shell interactivo para debugging"""
        print("""
=== DEBUGGER INTERACTIVO HUNTRED ===
Comandos disponibles:
- status: Estado del sistema
- metrics: Métricas actuales
- health: Health checks
- security: Verificación de seguridad
- report: Generar reporte completo
- django <cmd>: Ejecutar comando Django
- test [labels]: Ejecutar tests
- monitor: Iniciar/detener monitoreo
- quit: Salir
        """)
        
        while True:
            try:
                command = input("\ndebugger> ").strip().split()
                if not command:
                    continue
                
                cmd = command[0].lower()
                
                if cmd == 'quit':
                    break
                elif cmd == 'status':
                    self._show_status()
                elif cmd == 'metrics':
                    self._show_metrics()
                elif cmd == 'health':
                    self._show_health()
                elif cmd == 'security':
                    self._show_security()
                elif cmd == 'report':
                    report = self.generate_report()
                    print(f"Reporte generado: {json.dumps(report, indent=2, ensure_ascii=False, default=str)}")
                elif cmd == 'django':
                    if len(command) > 1:
                        self.run_django_command(command[1:])
                    else:
                        print("Uso: django <comando>")
                elif cmd == 'test':
                    test_labels = command[1:] if len(command) > 1 else None
                    failures = self.run_tests(test_labels)
                    print(f"Tests completados - Fallos: {failures}")
                elif cmd == 'monitor':
                    if self.running:
                        self.stop_monitoring()
                        print("Monitoreo detenido")
                    else:
                        self.start_monitoring()
                        print("Monitoreo iniciado")
                else:
                    print(f"Comando desconocido: {cmd}")
                    
            except KeyboardInterrupt:
                print("\nSaliendo...")
                break
            except Exception as e:
                print(f"Error: {e}")
        
        self.stop_monitoring()
    
    def _show_status(self):
        """Muestra estado del sistema"""
        metrics = self.system_monitor.get_system_metrics()
        print(f"""
=== ESTADO DEL SISTEMA ===
CPU: {metrics.cpu_percent:.1f}%
Memoria: {metrics.memory_percent:.1f}% ({metrics.memory_used_mb:.0f}MB usado)
Disco: {metrics.disk_percent:.1f}% ({metrics.disk_free_gb:.1f}GB libre)
Conexiones: {metrics.active_connections}
Procesos Python: {metrics.python_processes}
        """)
    
    def _show_metrics(self):
        """Muestra métricas detalladas"""
        system_metrics = self.system_monitor.get_system_metrics()
        db_metrics = self.db_monitor.get_database_metrics()
        celery_metrics = self.celery_monitor.get_celery_metrics()
        
        print(f"=== MÉTRICAS DETALLADAS ===")
        print(f"Sistema: {asdict(system_metrics)}")
        if db_metrics:
            print(f"Base de datos: {asdict(db_metrics)}")
        if celery_metrics:
            print(f"Celery: {asdict(celery_metrics)}")
    
    def _show_health(self):
        """Muestra health checks"""
        django_health = self.health_checker.check_django_health()
        external_health = self.health_checker.check_external_services()
        
        print(f"=== HEALTH CHECKS ===")
        print(f"Django: {django_health}")
        print(f"Servicios externos: {external_health}")
    
    def _show_security(self):
        """Muestra estado de seguridad"""
        issues = self.security_monitor.check_security_issues()
        
        print(f"=== SEGURIDAD ===")
        if issues:
            print("Problemas encontrados:")
            for issue in issues:
                print(f"- {issue}")
        else:
            print("No se encontraron problemas de seguridad")

def main():
    """Función principal"""
    debugger = LocalDebugger()
    
    # Configurar directorio de trabajo
    if len(sys.argv) > 1 and sys.argv[1] == '--project-dir':
        os.chdir(sys.argv[2])
    
    try:
        # Iniciar monitoreo automáticamente
        debugger.start_monitoring()
        
        # Generar reporte inicial
        debugger.generate_report()
        
        # Iniciar shell interactivo
        debugger.interactive_shell()
        
    except KeyboardInterrupt:
        print("\nDeteniendo debugger...")
    finally:
        debugger.stop_monitoring()

if __name__ == "__main__":
    main()