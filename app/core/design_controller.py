"""
Controlador Unificado de Diseño para Grupo huntRED®

Este módulo centraliza toda la gestión de:
- Recursos CSS/JS
- Temas y configuraciones
- Componentes reutilizables
- Optimización de assets
- Gestión de dependencias
"""

import os
import json
import hashlib
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from django.conf import settings
from django.core.cache import cache
from django.templatetags.static import static

logger = logging.getLogger(__name__)

@dataclass
class AssetConfig:
    """Configuración de un asset"""
    name: str
    path: str
    type: str  # 'css', 'js', 'img', 'font'
    version: str = "1.0.0"
    dependencies: List[str] = field(default_factory=list)
    minified: bool = True
    critical: bool = False
    async_load: bool = False
    defer_load: bool = False

@dataclass
class ThemeConfig:
    """Configuración de tema"""
    name: str
    primary_color: str
    secondary_color: str
    accent_color: str
    dark_mode: bool = False
    custom_css: str = ""
    variables: Dict[str, str] = field(default_factory=dict)

class DesignController:
    """
    Controlador centralizado para gestión de diseño y recursos
    """
    
    def __init__(self):
        self.assets = self._initialize_assets()
        self.themes = self._initialize_themes()
        self.components = self._initialize_components()
        self.cache_key = "design_controller_assets"
        self._load_asset_manifest()
    
    def _initialize_assets(self) -> Dict[str, AssetConfig]:
        """Inicializa configuración de assets centralizados"""
        return {
            # CSS Principal - Sistema Moderno
            'modern-ui': AssetConfig(
                name='modern-ui-system',
                path='css/modern-ui-system.css',
                type='css',
                version='2.0.0',
                critical=True,
                minified=True
            ),
            
            # CSS Avanzado - Optimizaciones
            'advanced-ui': AssetConfig(
                name='advanced-ui',
                path='css/advanced-ui.css',
                type='css',
                version='1.5.0',
                dependencies=['modern-ui'],
                minified=True
            ),
            
            # JavaScript Principal - Sistema Moderno
            'modern-ui-js': AssetConfig(
                name='modern-ui-system',
                path='js/modern-ui-system.js',
                type='js',
                version='2.0.0',
                dependencies=['modern-ui'],
                async_load=True,
                minified=True
            ),
            
            # JavaScript de Utilidades
            'utils-js': AssetConfig(
                name='utils',
                path='js/utils.js',
                type='js',
                version='1.0.0',
                defer_load=True,
                minified=True
            ),
            
            # JavaScript de Analytics
            'analytics-js': AssetConfig(
                name='analytics',
                path='js/analytics.js',
                type='js',
                version='1.0.0',
                async_load=True,
                minified=True
            ),
            
            # Fuentes
            'inter-font': AssetConfig(
                name='inter-font',
                path='fonts/inter.css',
                type='css',
                version='1.0.0',
                critical=True,
                minified=True
            ),
            
            # Iconos
            'fontawesome': AssetConfig(
                name='fontawesome',
                path='vendor/fontawesome/css/all.min.css',
                type='css',
                version='6.0.0',
                critical=False,
                minified=True
            ),
            
            # Chart.js para gráficos
            'chartjs': AssetConfig(
                name='chartjs',
                path='vendor/chart.js/chart.min.js',
                type='js',
                version='3.9.0',
                dependencies=['modern-ui-js'],
                defer_load=True,
                minified=True
            ),
            
            # Lodash para utilidades
            'lodash': AssetConfig(
                name='lodash',
                path='vendor/lodash/lodash.min.js',
                type='js',
                version='4.17.21',
                defer_load=True,
                minified=True
            )
        }
    
    def _initialize_themes(self) -> Dict[str, ThemeConfig]:
        """Inicializa configuraciones de temas"""
        return {
            'default': ThemeConfig(
                name='Default',
                primary_color='#2563eb',
                secondary_color='#10b981',
                accent_color='#f59e0b',
                dark_mode=False,
                variables={
                    '--primary-500': '#2563eb',
                    '--secondary-500': '#10b981',
                    '--accent-500': '#f59e0b'
                }
            ),
            'dark': ThemeConfig(
                name='Dark Mode',
                primary_color='#3b82f6',
                secondary_color='#10b981',
                accent_color='#f59e0b',
                dark_mode=True,
                variables={
                    '--bg-primary': '#0a0a0a',
                    '--text-primary': '#ffffff',
                    '--primary-500': '#3b82f6'
                }
            ),
            'corporate': ThemeConfig(
                name='Corporate',
                primary_color='#1e40af',
                secondary_color='#059669',
                accent_color='#d97706',
                dark_mode=False,
                variables={
                    '--primary-500': '#1e40af',
                    '--secondary-500': '#059669',
                    '--accent-500': '#d97706'
                }
            )
        }
    
    def _initialize_components(self) -> Dict[str, Dict[str, Any]]:
        """Inicializa componentes reutilizables"""
        return {
            'buttons': {
                'primary': 'btn-modern btn-primary',
                'secondary': 'btn-modern btn-secondary',
                'ghost': 'btn-modern btn-ghost',
                'outline': 'btn-modern btn-outline',
                'small': 'btn-modern btn-sm',
                'large': 'btn-modern btn-lg'
            },
            'cards': {
                'default': 'card-modern',
                'metric': 'card-modern metric-card',
                'chart': 'card-modern chart-card',
                'candidate': 'card-modern candidate-card',
                'assessment': 'card-modern assessment-card'
            },
            'forms': {
                'input': 'input-modern',
                'select': 'input-modern',
                'textarea': 'input-modern',
                'toggle': 'toggle',
                'checkbox': 'checkbox-modern'
            },
            'layout': {
                'container': 'container',
                'grid': 'grid',
                'flex': 'd-flex',
                'sidebar': 'sidebar-modern',
                'navbar': 'navbar-modern'
            },
            'animations': {
                'fade-in': 'animate-fade-in-up',
                'slide-in': 'animate-slide-in-left',
                'scale-in': 'animate-scale-in',
                'pulse': 'animate-pulse'
            }
        }
    
    def _load_asset_manifest(self):
        """Carga el manifest de assets para cache busting"""
        try:
            manifest_path = os.path.join(settings.STATIC_ROOT, 'manifest.json')
            if os.path.exists(manifest_path):
                with open(manifest_path, 'r') as f:
                    self.manifest = json.load(f)
            else:
                self.manifest = {}
        except Exception as e:
            logger.warning(f"No se pudo cargar manifest.json: {e}")
            self.manifest = {}
    
    def get_asset_url(self, asset_name: str) -> str:
        """Obtiene URL del asset con cache busting"""
        if asset_name not in self.assets:
            logger.warning(f"Asset no encontrado: {asset_name}")
            return ""
        
        asset = self.assets[asset_name]
        base_path = asset.path
        
        # Aplicar cache busting si hay manifest
        if base_path in self.manifest:
            base_path = self.manifest[base_path]
        
        return static(base_path)
    
    def get_critical_css(self) -> List[str]:
        """Obtiene CSS crítico para inline"""
        critical_assets = []
        for asset_name, asset in self.assets.items():
            if asset.type == 'css' and asset.critical:
                critical_assets.append(asset_name)
        return critical_assets
    
    def get_async_js(self) -> List[str]:
        """Obtiene JavaScript para carga asíncrona"""
        async_assets = []
        for asset_name, asset in self.assets.items():
            if asset.type == 'js' and asset.async_load:
                async_assets.append(asset_name)
        return async_assets
    
    def get_defer_js(self) -> List[str]:
        """Obtiene JavaScript para carga diferida"""
        defer_assets = []
        for asset_name, asset in self.assets.items():
            if asset.type == 'js' and asset.defer_load:
                defer_assets.append(asset_name)
        return defer_assets
    
    def get_theme_css_variables(self, theme_name: str = 'default') -> str:
        """Genera variables CSS para el tema"""
        if theme_name not in self.themes:
            theme_name = 'default'
        
        theme = self.themes[theme_name]
        css_variables = []
        
        for var_name, var_value in theme.variables.items():
            css_variables.append(f"{var_name}: {var_value};")
        
        return "\n".join(css_variables)
    
    def get_component_classes(self, component_type: str, variant: str = 'default') -> str:
        """Obtiene clases CSS para un componente"""
        if component_type not in self.components:
            return ""
        
        component = self.components[component_type]
        if variant not in component:
            variant = 'default'
        
        return component.get(variant, "")
    
    def generate_head_assets(self, page_type: str = 'default') -> Dict[str, Any]:
        """Genera assets para el head del HTML"""
        assets = {
            'critical_css': [],
            'async_css': [],
            'fonts': [],
            'meta': []
        }
        
        # CSS Crítico
        for asset_name in self.get_critical_css():
            assets['critical_css'].append({
                'name': asset_name,
                'url': self.get_asset_url(asset_name),
                'inline': True
            })
        
        # CSS Asíncrono
        for asset_name, asset in self.assets.items():
            if asset.type == 'css' and not asset.critical:
                assets['async_css'].append({
                    'name': asset_name,
                    'url': self.get_asset_url(asset_name),
                    'preload': True
                })
        
        # Fuentes
        for asset_name, asset in self.assets.items():
            if asset.type == 'css' and 'font' in asset_name:
                assets['fonts'].append({
                    'name': asset_name,
                    'url': self.get_asset_url(asset_name),
                    'preload': True
                })
        
        # Meta tags específicos por página
        if page_type == 'dashboard':
            assets['meta'].extend([
                {'name': 'viewport', 'content': 'width=device-width, initial-scale=1.0'},
                {'name': 'theme-color', 'content': '#2563eb'},
                {'name': 'description', 'content': 'Dashboard Moderno - Grupo huntRED®'}
            ])
        
        return assets
    
    def generate_body_assets(self) -> Dict[str, Any]:
        """Genera assets para el body del HTML"""
        assets = {
            'async_js': [],
            'defer_js': [],
            'inline_js': []
        }
        
        # JavaScript Asíncrono
        for asset_name in self.get_async_js():
            assets['async_js'].append({
                'name': asset_name,
                'url': self.get_asset_url(asset_name)
            })
        
        # JavaScript Diferido
        for asset_name in self.get_defer_js():
            assets['defer_js'].append({
                'name': asset_name,
                'url': self.get_asset_url(asset_name)
            })
        
        # JavaScript Inline para inicialización
        assets['inline_js'].append({
            'name': 'init',
            'code': self._generate_init_script()
        })
        
        return assets
    
    def _generate_init_script(self) -> str:
        """Genera script de inicialización"""
        return """
        document.addEventListener('DOMContentLoaded', function() {
            // Inicializar sistema moderno
            if (window.ModernUI) {
                window.ModernUI.init();
            }
            
            // Inicializar analytics
            if (window.Analytics) {
                window.Analytics.init();
            }
            
            // Aplicar tema
            const theme = localStorage.getItem('theme') || 'default';
            document.documentElement.setAttribute('data-theme', theme);
        });
        """
    
    def optimize_assets(self) -> Dict[str, Any]:
        """Optimiza y minifica assets"""
        optimization_report = {
            'css_files': 0,
            'js_files': 0,
            'total_size': 0,
            'optimizations': []
        }
        
        try:
            for asset_name, asset in self.assets.items():
                file_path = os.path.join(settings.STATIC_ROOT, asset.path)
                
                if os.path.exists(file_path):
                    file_size = os.path.getsize(file_path)
                    optimization_report['total_size'] += file_size
                    
                    if asset.type == 'css':
                        optimization_report['css_files'] += 1
                    elif asset.type == 'js':
                        optimization_report['js_files'] += 1
                    
                    # Verificar si necesita minificación
                    if asset.minified and not file_path.endswith('.min.'):
                        optimization_report['optimizations'].append({
                            'asset': asset_name,
                            'action': 'minify',
                            'current_size': file_size
                        })
            
            # Cachear reporte
            cache.set('asset_optimization_report', optimization_report, 3600)
            
        except Exception as e:
            logger.error(f"Error optimizando assets: {e}")
        
        return optimization_report
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas de performance"""
        cached_report = cache.get('asset_optimization_report')
        if cached_report:
            return cached_report
        
        return self.optimize_assets()

# Instancia global del controlador
design_controller = DesignController() 