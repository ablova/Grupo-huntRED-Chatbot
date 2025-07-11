# app/ats/pricing/services/integrations/wordpress_sync_service.py
"""
Servicio de sincronización con WordPress (migrado del módulo antiguo).
"""
import requests
import logging
import time
import json
from typing import Optional, Dict, Any, Tuple
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from django.core.mail import EmailMessage
from django.db import transaction

from app.ats.models import Oportunidad, Empleador, SincronizacionError, SincronizacionLog
from app.models import ConfiguracionBU, BusinessUnit, User, PricingBaseline, Addons, Coupons, PaymentMilestone

logger = logging.getLogger('wordpress_sync')

# Configuración de WordPress por Business Unit
WORDPRESS_CONFIG = {
    'huntRED': {
        'base_url': 'https://huntred.com/wp-json/wp/v2',
        'auth_token': None,  # Se obtendrá de settings
        'endpoints': {
            'baselines': 'pricing/baselines',
            'addons': 'pricing/addons',
            'coupons': 'pricing/coupons',
            'milestones': 'pricing/milestones'
        }
    },
    'huntU': {
        'base_url': 'https://huntu.mx/wp-json/wp/v2',
        # El token de autenticación ahora se obtiene dinámicamente de BusinessUnit.get_integration_config
        'endpoints': {
            'baselines': 'pricing/baselines',
            'addons': 'pricing/addons',
            'coupons': 'pricing/coupons',
            'milestones': 'pricing/milestones'
        }
    },
    'Amigro': {
        'base_url': 'https://amigro.org/wp-json/wp/v2',
        # El token de autenticación ahora se obtiene dinámicamente de BusinessUnit.get_integration_config
        'endpoints': {
            'baselines': 'pricing/baselines',
            'addons': 'pricing/addons',
            'coupons': 'pricing/coupons',
            'milestones': 'pricing/milestones'
        }
    }
}

# Configuración de timeouts y reintentos
WORDPRESS_SETTINGS = {
    'retry_attempts': 3,
    'retry_delay': 2.0,
    'cache_timeout': 600,
    'request_timeout': 30
}

class WordPressSyncService:
    """Servicio para sincronización con WordPress."""
    
    def __init__(self, business_unit: str, retry_attempts: int = None, retry_delay: float = None):
        """
        Inicializa el sincronizador de WordPress para una Business Unit específica.
        
        Args:
            business_unit: Nombre de la Business Unit (huntRED, huntU, Amigro)
            retry_attempts: Número máximo de reintentos para llamadas fallidas
            retry_delay: Tiempo de espera entre reintentos en segundos
        """
        self.business_unit = business_unit
        self.config = WORDPRESS_CONFIG.get(business_unit)
        if not self.config:
            raise ValueError(f"Business Unit no soportada: {business_unit}")
            
        # Usar configuración de settings o defaults
        self.retry_attempts = retry_attempts or WORDPRESS_SETTINGS['retry_attempts']
        self.retry_delay = retry_delay or WORDPRESS_SETTINGS['retry_delay']
        self.cache_timeout = WORDPRESS_SETTINGS['cache_timeout']
        self.request_timeout = WORDPRESS_SETTINGS['request_timeout']
        
        # Configurar autenticación desde BusinessUnit.get_integration_config
        self.base_url = self.config['base_url']
        self.auth_token = self._get_auth_token()
        self.auth = (self.auth_token, '') if self.auth_token else None
        
        self.current_retries = 0
        
    def _get_auth_token(self) -> Optional[str]:
        """
        Obtiene el token de autenticación desde BusinessUnit.get_integration_config.
        
        Returns:
            Token de autenticación o None si no está configurado
        """
        try:
            # Intentar obtener la business unit desde la base de datos
            bu_obj = BusinessUnit.objects.filter(nombre=self.business_unit).first()
            
            if bu_obj:
                # Obtener configuración de WordPress desde integration_config
                wp_config = bu_obj.get_integration_config('wordpress')
                if wp_config and 'auth_token' in wp_config:
                    return wp_config['auth_token']
            
            # Fallback a settings si no se encuentra en BD
            return getattr(settings, 'WORDPRESS_AUTH_TOKEN', None)
            
        except Exception as e:
            logger.error(f"Error al obtener token de autenticación para {self.business_unit}: {str(e)}")
            return None
        
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Tuple[bool, Dict]:
        """
        Realiza una solicitud HTTP a la API de WordPress con manejo de reintentos.
        
        Args:
            method: Método HTTP (GET, POST, PUT, DELETE)
            endpoint: Endpoint de la API
            data: Datos a enviar (opcional)
            
        Returns:
            Tuple[bool, Dict]: (éxito, respuesta)
        """
        url = f"{self.base_url}/{endpoint}"
        headers = {
            'Content-Type': 'application/json'
        }
        
        for attempt in range(self.retry_attempts):
            try:
                response = requests.request(
                    method,
                    url,
                    auth=self.auth,
                    headers=headers,
                    data=json.dumps(data) if data else None,
                    timeout=self.request_timeout
                )
                response.raise_for_status()
                return True, response.json()
                
            except requests.exceptions.RequestException as e:
                self.current_retries += 1
                
                # Registrar error en la base de datos
                error = SincronizacionError.objects.create(
                    oportunidad=None,  # Se asignará después si es necesario
                    mensaje=str(e),
                    intento=self.current_retries
                )
                
                logger.error(f"Error en intento {attempt + 1}/{self.retry_attempts}: {str(e)}")
                
                # Si es el último intento, lanzar la excepción
                if attempt == self.retry_attempts - 1:
                    return False, {'error': str(e)}
                    
                # Esperar antes de reintentar
                time.sleep(self.retry_delay * (attempt + 1))
        
        return False, {'error': 'Máximo de reintentos alcanzado'}
    
    def sincronizar_baselines(self, baselines) -> Dict[str, Any]:
        """
        Sincroniza las baselines de pricing con WordPress.
        
        Args:
            baselines: QuerySet de PricingBaseline
            
        Returns:
            Dict con estadísticas de la sincronización
        """
        stats = {'total': 0, 'success': 0, 'errors': []}
        
        for baseline in baselines:
            try:
                data = {
                    'bu': baseline.bu,
                    'model': baseline.model,
                    'base_price': str(baseline.base_price),
                    'percentage': str(baseline.percentage) if baseline.percentage else None
                }
                
                # Usar el endpoint específico para baselines
                endpoint = self.config['endpoints']['baselines']
                success, response = self._make_request('POST', endpoint, data)
                
                if success:
                    stats['success'] += 1
                else:
                    stats['errors'].append({
                        'id': baseline.id,
                        'error': response.get('error', 'Error desconocido')
                    })
                    
            except Exception as e:
                stats['errors'].append({
                    'id': baseline.id,
                    'error': str(e)
                })
            
            stats['total'] += 1
        
        return stats

    def sincronizar_addons(self, addons) -> Dict[str, Any]:
        """
        Sincroniza los addons con WordPress.
        
        Args:
            addons: QuerySet de Addons
            
        Returns:
            Dict con estadísticas de la sincronización
        """
        stats = {'total': 0, 'success': 0, 'errors': []}
        
        for addon in addons:
            try:
                data = {
                    'name': addon.name,
                    'price': str(addon.price),
                    'max_per_vacancy': addon.max_per_vacancy,
                    'active': addon.active
                }
                
                # Usar el endpoint específico para addons
                endpoint = self.config['endpoints']['addons']
                success, response = self._make_request('POST', endpoint, data)
                
                if success:
                    stats['success'] += 1
                else:
                    stats['errors'].append({
                        'id': addon.id,
                        'error': response.get('error', 'Error desconocido')
                    })
                    
            except Exception as e:
                stats['errors'].append({
                    'id': addon.id,
                    'error': str(e)
                })
            
            stats['total'] += 1
        
        return stats

    def sincronizar_coupons(self, coupons) -> Dict[str, Any]:
        """
        Sincroniza los cupones con WordPress.
        
        Args:
            coupons: QuerySet de Coupons
            
        Returns:
            Dict con estadísticas de la sincronización
        """
        stats = {'total': 0, 'success': 0, 'errors': []}
        
        for coupon in coupons:
            try:
                data = {
                    'code': coupon.code,
                    'type': coupon.type,
                    'value': str(coupon.value),
                    'valid_until': coupon.valid_until.isoformat(),
                    'max_uses': coupon.max_uses
                }
                
                # Usar el endpoint específico para coupons
                endpoint = self.config['endpoints']['coupons']
                success, response = self._make_request('POST', endpoint, data)
                
                if success:
                    stats['success'] += 1
                else:
                    stats['errors'].append({
                        'id': coupon.id,
                        'error': response.get('error', 'Error desconocido')
                    })
                    
            except Exception as e:
                stats['errors'].append({
                    'id': coupon.id,
                    'error': str(e)
                })
            
            stats['total'] += 1
        
        return stats

    def sincronizar_milestones(self, milestones) -> Dict[str, Any]:
        """
        Sincroniza los milestones con WordPress.
        
        Args:
            milestones: QuerySet de PaymentMilestone
            
        Returns:
            Dict con estadísticas de la sincronización
        """
        stats = {'total': 0, 'success': 0, 'errors': []}
        
        for milestone in milestones:
            try:
                data = {
                    'name': milestone.name,
                    'percentage': str(milestone.percentage),
                    'description': milestone.description
                }
                
                # Usar el endpoint específico para milestones
                endpoint = self.config['endpoints']['milestones']
                success, response = self._make_request('POST', endpoint, data)
                
                if success:
                    stats['success'] += 1
                else:
                    stats['errors'].append({
                        'id': milestone.id,
                        'error': response.get('error', 'Error desconocido')
                    })
                    
            except Exception as e:
                stats['errors'].append({
                    'id': milestone.id,
                    'error': str(e)
                })
            
            stats['total'] += 1
        
        return stats

    @transaction.atomic
    def sincronizar_oportunidad(self, oportunidad_id: int) -> Dict[str, Any]:
        """
        Sincroniza una oportunidad específica con WordPress.
        
        Args:
            oportunidad_id: ID de la oportunidad a sincronizar
            
        Returns:
            Dict con el resultado de la sincronización
        """
        try:
            # Obtener oportunidad
            oportunidad = Oportunidad.objects.get(id=oportunidad_id)
            
            # Registrar inicio de sincronización
            log = SincronizacionLog.objects.create(
                oportunidad=oportunidad,
                estado='EN_PROCESO'
            )
            
            # Preparar datos para WordPress
            data = {
                'title': oportunidad.titulo,
                'description': oportunidad.descripcion,
                'tipo_contrato': oportunidad.tipo_contrato,
                'salario_minimo': str(oportunidad.salario_minimo),
                'salario_maximo': str(oportunidad.salario_maximo),
                'pais': oportunidad.pais,
                'ciudad': oportunidad.ciudad,
                'modalidad': oportunidad.modalidad,
                'estado': oportunidad.estado,
                'empleador': {
                    'razon_social': oportunidad.empleador.razon_social,
                    'rfc': oportunidad.empleador.rfc,
                    'sitio_web': oportunidad.empleador.sitio_web
                }
            }
            
            # Enviar a WordPress
            success, response = self._make_request('POST', 'oportunidades', data)
            
            if success:
                # Actualizar log de sincronización
                log.estado = 'EXITO'
                log.detalle = response
                log.save()
                
                return {
                    'success': True,
                    'wp_id': response.get('id'),
                    'message': 'Oportunidad sincronizada exitosamente'
                }
            else:
                # Registrar error
                error = SincronizacionError.objects.create(
                    oportunidad=oportunidad,
                    mensaje=response.get('error', 'Error desconocido'),
                    intento=1
                )
                
                # Actualizar log de sincronización
                log.estado = 'ERROR'
                log.detalle = response
                log.save()
                
                return {
                    'success': False,
                    'error': response.get('error', 'Error desconocido')
                }
                
        except Oportunidad.DoesNotExist:
            return {
                'success': False,
                'error': f'Oportunidad {oportunidad_id} no encontrada'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def sincronizar_empleador(self, empleador: Empleador) -> Tuple[bool, Dict]:
        """
        Sincroniza un empleador con WordPress.
        
        Args:
            empleador: Instancia del empleador
            
        Returns:
            Tuple[bool, Dict]: (éxito, resultado)
        """
        try:
            data = {
                'razon_social': empleador.razon_social,
                'rfc': empleador.rfc,
                'direccion_fiscal': empleador.direccion_fiscal,
                'clabe': empleador.clabe,
                'banco': empleador.banco,
                'sitio_web': empleador.sitio_web,
                'telefono_oficina': empleador.telefono_oficina,
                'address': empleador.address,
                'estado': empleador.estado
            }
            
            success, response = self._make_request('POST', 'empleadores', data)
            
            if success:
                return True, {
                    'wp_id': response.get('id'),
                    'message': 'Empleador sincronizado exitosamente'
                }
            else:
                return False, {
                    'error': response.get('error', 'Error desconocido')
                }
                
        except Exception as e:
            return False, {'error': str(e)}

    def sincronizar_pricing(self) -> Dict[str, Any]:
        """
        Sincroniza toda la configuración de pricing con WordPress.
        
        Returns:
            Dict con estadísticas de la sincronización
        """
        try:
            # Obtener configuraciones de pricing para la Business Unit
            pricing_config = {
                'baselines': PricingBaseline.objects.filter(bu=self.business_unit),
                'addons': Addons.objects.filter(bu=self.business_unit),
                'coupons': Coupons.objects.filter(bu=self.business_unit),
                'milestones': PaymentMilestone.objects.filter(bu=self.business_unit)
            }
            
            # Sincronizar cada tipo de configuración
            stats = {
                'baselines': self.sincronizar_baselines(pricing_config['baselines']),
                'addons': self.sincronizar_addons(pricing_config['addons']),
                'coupons': self.sincronizar_coupons(pricing_config['coupons']),
                'milestones': self.sincronizar_milestones(pricing_config['milestones'])
            }
            
            return {
                'success': True,
                'stats': stats,
                'message': 'Pricing sincronizado exitosamente'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def sincronizar_todos(self) -> Dict[str, Any]:
        """
        Sincroniza todos los elementos con WordPress.
        
        Returns:
            Dict con estadísticas completas
        """
        try:
            # Sincronizar pricing
            pricing_result = self.sincronizar_pricing()
            
            # Sincronizar empleadores
            empleadores = Empleador.objects.all()
            empleadores_stats = {'total': 0, 'success': 0, 'errors': []}
            
            for empleador in empleadores:
                success, result = self.sincronizar_empleador(empleador)
                empleadores_stats['total'] += 1
                
                if success:
                    empleadores_stats['success'] += 1
                else:
                    empleadores_stats['errors'].append({
                        'id': empleador.id,
                        'error': result.get('error', 'Error desconocido')
                    })
            
            # Sincronizar oportunidades
            oportunidades = Oportunidad.objects.all()
            oportunidades_stats = {'total': 0, 'success': 0, 'errors': []}
            
            for oportunidad in oportunidades:
                result = self.sincronizar_oportunidad(oportunidad.id)
                oportunidades_stats['total'] += 1
                
                if result['success']:
                    oportunidades_stats['success'] += 1
                else:
                    oportunidades_stats['errors'].append({
                        'id': oportunidad.id,
                        'error': result.get('error', 'Error desconocido')
                    })
            
            return {
                'success': True,
                'stats': {
                    'pricing': pricing_result.get('stats', {}),
                    'empleadores': empleadores_stats,
                    'oportunidades': oportunidades_stats
                },
                'message': 'Sincronización completa finalizada'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            } 