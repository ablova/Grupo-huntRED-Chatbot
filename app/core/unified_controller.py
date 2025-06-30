"""
CONTROLADOR UNIFICADO - Grupo huntRED®
Gestión centralizada de todo el sistema: diseño, scraping, recursos y optimizaciones
"""

import os
import json
import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.core.cache import cache
from django.templatetags.static import static

from app.core.design_controller import DesignController
from app.ats.utils.scraping.robust_scraping_system import RobustScrapingSystem

logger = logging.getLogger(__name__)

@dataclass
class SystemMetrics:
    """Métricas del sistema"""
    scraping_success_rate: float = 0.0
    cache_hit_rate: float = 0.0
    response_time_avg: float = 0.0
    error_rate: float = 0.0
    active_sessions: int = 0
    last_updated: datetime = field(default_factory=datetime.now)

class UnifiedController:
    """
    Controlador unificado para todo el sistema huntRED®
    """
    
    def __init__(self):
        self.design_controller = DesignController()
        self.scraping_system = RobustScrapingSystem()
        self.metrics = SystemMetrics()
        self.config = self._load_config()
        self.active_sessions = {}
        
        # Inicializar sistema
        self._initialize_system()
    
    def _load_config(self) -> Dict[str, Any]:
        """Carga configuración del sistema"""
        config_path = Path(settings.BASE_DIR) / 'config' / 'unified_config.json'
        
        default_config = {
            'performance': {
                'enable_cache': True,
                'cache_ttl': 3600,
                'max_concurrent_scraping': 5,
                'enable_compression': True,
                'enable_minification': True
            },
            'scraping': {
                'enable_robust_mode': True,
                'max_retries': 3,
                'timeout': 30,
                'enable_proxy_rotation': True,
                'enable_anti_detection': True
            },
            'design': {
                'default_theme': 'default',
                'enable_dark_mode': True,
                'enable_animations': True,
                'enable_responsive': True
            },
            'monitoring': {
                'enable_metrics': True,
                'metrics_interval': 300,
                'enable_alerts': True,
                'alert_threshold': 0.8
            }
        }
        
        try:
            if config_path.exists():
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                    # Merge con configuración por defecto
                    return self._merge_configs(default_config, user_config)
        except Exception as e:
            logger.warning(f"No se pudo cargar configuración personalizada: {e}")
        
        return default_config
    
    def _merge_configs(self, default: Dict, user: Dict) -> Dict:
        """Combina configuraciones por defecto y personalizada"""
        result = default.copy()
        
        for key, value in user.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _initialize_system(self):
        """Inicializa el sistema unificado"""
        logger.info("🚀 Inicializando Controlador Unificado")
        
        # Verificar directorios necesarios
        self._ensure_directories()
        
        # Inicializar métricas
        self._start_metrics_collection()
        
        # Verificar conectividad
        self._check_connectivity()
        
        logger.info("✅ Controlador Unificado inicializado correctamente")
    
    def _ensure_directories(self):
        """Asegura que existan los directorios necesarios"""
        directories = [
            'logs',
            'cache',
            'temp',
            'config',
            'backups'
        ]
        
        for directory in directories:
            dir_path = Path(settings.BASE_DIR) / directory
            dir_path.mkdir(exist_ok=True)
    
    def _start_metrics_collection(self):
        """Inicia recolección de métricas"""
        if self.config['monitoring']['enable_metrics']:
            asyncio.create_task(self._collect_metrics_loop())
    
    async def _collect_metrics_loop(self):
        """Loop de recolección de métricas"""
        while True:
            try:
                # Obtener métricas de scraping
                scraping_stats = self.scraping_system.get_stats()
                
                # Actualizar métricas del sistema
                self.metrics.scraping_success_rate = scraping_stats.get('success_rate', 0.0)
                self.metrics.cache_hit_rate = scraping_stats.get('cache_hit_rate', 0.0)
                self.metrics.error_rate = scraping_stats.get('failed_requests', 0) / max(scraping_stats.get('total_requests', 1), 1) * 100
                self.metrics.active_sessions = len(self.active_sessions)
                self.metrics.last_updated = datetime.now()
                
                # Guardar métricas en cache
                cache.set('system_metrics', self.metrics, 3600)
                
                # Verificar alertas
                if self.config['monitoring']['enable_alerts']:
                    await self._check_alerts()
                
            except Exception as e:
                logger.error(f"Error recolectando métricas: {e}")
            
            # Esperar intervalo
            await asyncio.sleep(self.config['monitoring']['metrics_interval'])
    
    async def _check_alerts(self):
        """Verifica y envía alertas si es necesario"""
        threshold = self.config['monitoring']['alert_threshold']
        
        if self.metrics.scraping_success_rate < threshold * 100:
            await self._send_alert(
                'warning',
                f'Baja tasa de éxito en scraping: {self.metrics.scraping_success_rate:.1f}%'
            )
        
        if self.metrics.error_rate > (1 - threshold) * 100:
            await self._send_alert(
                'error',
                f'Alta tasa de errores: {self.metrics.error_rate:.1f}%'
            )
    
    async def _send_alert(self, level: str, message: str):
        """Envía alerta del sistema"""
        alert_data = {
            'level': level,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'metrics': {
                'scraping_success_rate': self.metrics.scraping_success_rate,
                'error_rate': self.metrics.error_rate,
                'active_sessions': self.metrics.active_sessions
            }
        }
        
        # Guardar alerta
        cache.set(f'alert_{datetime.now().timestamp()}', alert_data, 86400)
        
        # Log de alerta
        if level == 'error':
            logger.error(f"🚨 ALERTA: {message}")
        else:
            logger.warning(f"⚠️ ALERTA: {message}")
    
    def _check_connectivity(self):
        """Verifica conectividad del sistema"""
        try:
            # Verificar acceso a archivos estáticos
            static_path = Path(settings.STATIC_ROOT)
            if not static_path.exists():
                logger.warning("Directorio de archivos estáticos no encontrado")
            
            # Verificar configuración de cache
            cache.set('connectivity_test', 'ok', 60)
            test_result = cache.get('connectivity_test')
            if test_result != 'ok':
                logger.warning("Cache no funciona correctamente")
            
            logger.info("✅ Conectividad del sistema verificada")
            
        except Exception as e:
            logger.error(f"❌ Error verificando conectividad: {e}")
    
    # ===== MÉTODOS DE DISEÑO =====
    
    def get_design_assets(self, page_type: str = 'default', theme: str = None) -> Dict[str, Any]:
        """Obtiene assets de diseño optimizados"""
        theme = theme or self.config['design']['default_theme']
        
        # Obtener assets del controlador de diseño
        head_assets = self.design_controller.generate_head_assets(page_type)
        body_assets = self.design_controller.generate_body_assets()
        
        # Aplicar configuración de tema
        theme_css = self.design_controller.get_theme_css_variables(theme)
        
        # Optimizar según configuración
        if self.config['performance']['enable_minification']:
            head_assets = self._optimize_assets(head_assets)
            body_assets = self._optimize_assets(body_assets)
        
        return {
            'head': head_assets,
            'body': body_assets,
            'theme_css': theme_css,
            'theme_name': theme,
            'config': {
                'enable_animations': self.config['design']['enable_animations'],
                'enable_responsive': self.config['design']['enable_responsive'],
                'enable_dark_mode': self.config['design']['enable_dark_mode']
            }
        }
    
    def _optimize_assets(self, assets: Dict[str, Any]) -> Dict[str, Any]:
        """Optimiza assets según configuración"""
        if not self.config['performance']['enable_minification']:
            return assets
        
        # Filtrar assets críticos
        if 'critical_css' in assets:
            assets['critical_css'] = assets['critical_css'][:3]  # Solo 3 CSS críticos
        
        # Optimizar JavaScript
        if 'async_js' in assets:
            assets['async_js'] = assets['async_js'][:2]  # Solo 2 JS async
        
        return assets
    
    def get_component_classes(self, component_type: str, variant: str = 'default') -> str:
        """Obtiene clases CSS para componentes"""
        return self.design_controller.get_component_classes(component_type, variant)
    
    def get_theme_config(self, theme_name: str = None) -> Dict[str, Any]:
        """Obtiene configuración de tema"""
        theme_name = theme_name or self.config['design']['default_theme']
        theme = self.design_controller.themes.get(theme_name, self.design_controller.themes['default'])
        
        return {
            'name': theme.name,
            'primary_color': theme.primary_color,
            'secondary_color': theme.secondary_color,
            'accent_color': theme.accent_color,
            'dark_mode': theme.dark_mode,
            'variables': theme.variables
        }
    
    # ===== MÉTODOS DE SCRAPING =====
    
    async def scrape_url(self, url: str, platform: str = None, max_retries: int = None) -> Dict[str, Any]:
        """Scraping de URL con configuración optimizada"""
        try:
            # Configurar retries según configuración
            if max_retries is None:
                max_retries = self.config['scraping']['max_retries']
            
            # Ejecutar scraping
            result = await self.scraping_system.scrape_url(url, max_retries)
            
            # Registrar métricas
            self._record_scraping_metric(result)
            
            return {
                'success': result.success,
                'data': result.data,
                'error': result.error,
                'platform': result.platform,
                'response_time': result.response_time,
                'retry_count': result.retry_count
            }
            
        except Exception as e:
            logger.error(f"Error en scraping unificado: {e}")
            return {
                'success': False,
                'error': str(e),
                'platform': platform,
                'response_time': 0.0
            }
    
    async def scrape_multiple_urls(self, urls: List[str], max_concurrent: int = None) -> List[Dict[str, Any]]:
        """Scraping de múltiples URLs"""
        try:
            # Configurar concurrencia
            if max_concurrent is None:
                max_concurrent = self.config['scraping']['max_retries']
            
            # Ejecutar scraping
            results = await self.scraping_system.scrape_multiple_urls(urls, max_concurrent)
            
            # Convertir a formato unificado
            unified_results = []
            for result in results:
                unified_results.append({
                    'success': result.success,
                    'data': result.data,
                    'error': result.error,
                    'platform': result.platform,
                    'url': result.url,
                    'response_time': result.response_time,
                    'retry_count': result.retry_count
                })
            
            return unified_results
            
        except Exception as e:
            logger.error(f"Error en scraping múltiple: {e}")
            return []
    
    def _record_scraping_metric(self, result):
        """Registra métrica de scraping"""
        if result.success:
            self.metrics.scraping_success_rate = (
                (self.metrics.scraping_success_rate * 0.9) + (100 * 0.1)
            )
        else:
            self.metrics.scraping_success_rate = (
                (self.metrics.scraping_success_rate * 0.9) + (0 * 0.1)
            )
    
    # ===== MÉTODOS DE SESIÓN =====
    
    def create_session(self, session_id: str, user_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Crea una nueva sesión del sistema"""
        session_data = {
            'id': session_id,
            'created_at': datetime.now(),
            'last_activity': datetime.now(),
            'user_data': user_data or {},
            'scraping_requests': 0,
            'design_requests': 0,
            'errors': 0
        }
        
        self.active_sessions[session_id] = session_data
        
        logger.info(f"📱 Sesión creada: {session_id}")
        return session_data
    
    def update_session(self, session_id: str, activity_type: str = 'general'):
        """Actualiza actividad de sesión"""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            session['last_activity'] = datetime.now()
            
            if activity_type == 'scraping':
                session['scraping_requests'] += 1
            elif activity_type == 'design':
                session['design_requests'] += 1
            elif activity_type == 'error':
                session['errors'] += 1
    
    def close_session(self, session_id: str):
        """Cierra una sesión"""
        if session_id in self.active_sessions:
            session_data = self.active_sessions.pop(session_id)
            
            # Registrar métricas de sesión
            duration = (datetime.now() - session_data['created_at']).total_seconds()
            
            logger.info(f"📱 Sesión cerrada: {session_id} (duración: {duration:.1f}s)")
    
    def cleanup_inactive_sessions(self, max_inactive_minutes: int = 30):
        """Limpia sesiones inactivas"""
        cutoff_time = datetime.now() - timedelta(minutes=max_inactive_minutes)
        
        inactive_sessions = [
            session_id for session_id, session in self.active_sessions.items()
            if session['last_activity'] < cutoff_time
        ]
        
        for session_id in inactive_sessions:
            self.close_session(session_id)
        
        if inactive_sessions:
            logger.info(f"🧹 Limpiadas {len(inactive_sessions)} sesiones inactivas")
    
    # ===== MÉTODOS DE MONITOREO =====
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas completas del sistema"""
        scraping_stats = self.scraping_system.get_stats()
        
        return {
            'scraping': {
                'success_rate': self.metrics.scraping_success_rate,
                'cache_hit_rate': self.metrics.cache_hit_rate,
                'error_rate': self.metrics.error_rate,
                'total_requests': scraping_stats.get('total_requests', 0),
                'successful_requests': scraping_stats.get('successful_requests', 0),
                'failed_requests': scraping_stats.get('failed_requests', 0),
                'blocked_requests': scraping_stats.get('blocked_requests', 0)
            },
            'sessions': {
                'active_sessions': self.metrics.active_sessions,
                'total_sessions_created': len(self.active_sessions)
            },
            'performance': {
                'response_time_avg': self.metrics.response_time_avg,
                'cache_enabled': self.config['performance']['enable_cache'],
                'compression_enabled': self.config['performance']['enable_compression']
            },
            'system': {
                'last_updated': self.metrics.last_updated.isoformat(),
                'uptime': (datetime.now() - self.metrics.last_updated).total_seconds()
            }
        }
    
    def get_system_health(self) -> Dict[str, Any]:
        """Obtiene estado de salud del sistema"""
        metrics = self.get_system_metrics()
        
        # Calcular scores de salud
        scraping_health = metrics['scraping']['success_rate'] / 100
        session_health = min(metrics['sessions']['active_sessions'] / 100, 1.0)
        error_health = 1 - (metrics['scraping']['error_rate'] / 100)
        
        overall_health = (scraping_health + session_health + error_health) / 3
        
        return {
            'overall_health': overall_health,
            'status': 'healthy' if overall_health > 0.8 else 'warning' if overall_health > 0.6 else 'critical',
            'components': {
                'scraping': {
                    'health': scraping_health,
                    'status': 'healthy' if scraping_health > 0.8 else 'warning' if scraping_health > 0.6 else 'critical'
                },
                'sessions': {
                    'health': session_health,
                    'status': 'healthy' if session_health > 0.8 else 'warning' if session_health > 0.6 else 'critical'
                },
                'errors': {
                    'health': error_health,
                    'status': 'healthy' if error_health > 0.8 else 'warning' if error_health > 0.6 else 'critical'
                }
            },
            'recommendations': self._get_health_recommendations(overall_health, metrics)
        }
    
    def _get_health_recommendations(self, overall_health: float, metrics: Dict) -> List[str]:
        """Obtiene recomendaciones basadas en métricas"""
        recommendations = []
        
        if overall_health < 0.8:
            if metrics['scraping']['success_rate'] < 80:
                recommendations.append("Considerar ajustar configuración de scraping")
            
            if metrics['scraping']['error_rate'] > 20:
                recommendations.append("Revisar conectividad y proxies")
            
            if metrics['sessions']['active_sessions'] > 100:
                recommendations.append("Limpiar sesiones inactivas")
        
        if metrics['scraping']['cache_hit_rate'] < 50:
            recommendations.append("Optimizar estrategia de cache")
        
        return recommendations
    
    # ===== MÉTODOS DE CONFIGURACIÓN =====
    
    def update_config(self, new_config: Dict[str, Any]):
        """Actualiza configuración del sistema"""
        self.config = self._merge_configs(self.config, new_config)
        
        # Guardar configuración
        config_path = Path(settings.BASE_DIR) / 'config' / 'unified_config.json'
        try:
            with open(config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            
            logger.info("✅ Configuración actualizada y guardada")
        except Exception as e:
            logger.error(f"Error guardando configuración: {e}")
    
    def get_config(self, section: str = None) -> Dict[str, Any]:
        """Obtiene configuración del sistema"""
        if section:
            return self.config.get(section, {})
        return self.config
    
    # ===== MÉTODOS DE LIMPIEZA =====
    
    async def cleanup(self):
        """Limpia recursos del sistema"""
        logger.info("🧹 Iniciando limpieza del sistema")
        
        # Limpiar sesiones inactivas
        self.cleanup_inactive_sessions()
        
        # Limpiar sistema de scraping
        await self.scraping_system.cleanup()
        
        # Limpiar cache si es necesario
        if self.config['performance']['enable_cache']:
            # Solo limpiar cache antiguo
            pass
        
        logger.info("✅ Limpieza del sistema completada")
    
    def get_system_info(self) -> Dict[str, Any]:
        """Obtiene información completa del sistema"""
        return {
            'version': '2.0.0',
            'name': 'Grupo huntRED® Unified Controller',
            'description': 'Controlador unificado para diseño, scraping y optimizaciones',
            'config': self.config,
            'metrics': self.get_system_metrics(),
            'health': self.get_system_health(),
            'active_sessions_count': len(self.active_sessions),
            'uptime': (datetime.now() - self.metrics.last_updated).total_seconds()
        }

# Instancia global del controlador unificado
unified_controller = UnifiedController() 