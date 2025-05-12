import requests
import logging
import time
import json
from typing import Optional, Dict, Any, Tuple
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from app.pagos.models import Oportunidad, Empleador
from app.com.utils.vacantes import VacanteManager
from app.models import ConfiguracionBU, BusinessUnit
from asgiref.sync import sync_to_async

logger = logging.getLogger('wordpress_sync')

class WordPressSync:
    def __init__(self, retry_attempts: int = 3, retry_delay: float = 2.0):
        """
        Inicializa el sincronizador de WordPress.
        
        Args:
            retry_attempts: Número máximo de reintentos para llamadas fallidas
            retry_delay: Tiempo de espera entre reintentos en segundos
        """
        self.base_url = settings.WORDPRESS_API_URL
        self.auth = (settings.WORDPRESS_USERNAME, settings.WORDPRESS_PASSWORD)
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay
        self.cache_timeout = 600  # 10 minutos
        self.vacante_manager = None
        
    async def initialize(self):
        """Inicializa el VacanteManager de manera asíncrona."""
        if not self.vacante_manager:
            self.vacante_manager = VacanteManager({
                'business_unit': 'default',
                'job_title': 'default',
                'job_description': 'default',
                'company_name': 'default'
            })
            await self.vacante_manager.initialize()

    @sync_to_async
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None):
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
        
        for attempt in range(self.retry_attempts):
            try:
                response = requests.request(
                    method,
                    url,
                    json=data,
                    auth=self.auth,
                    timeout=10
                )
                
                if response.status_code in [200, 201]:
                    logger.info(f"Solicitud exitosa a {method} {url}")
                    return True, response.json()
                
                logger.warning(f"Intento {attempt + 1} fallido. Status: {response.status_code}")
                
                if attempt < self.retry_attempts - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                    
            except requests.RequestException as e:
                logger.error(f"Error en la solicitud: {str(e)}")
                if attempt < self.retry_attempts - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
        
        return False, {"error": "Max retries exceeded"}

    async def sincronizar_oportunidad(self, oportunidad: Oportunidad):
        """
        Sincroniza una oportunidad con WordPress.
        
        Args:
            oportunidad: Instancia de Oportunidad a sincronizar
            
        Returns:
            Tuple[bool, Dict]: (éxito, respuesta)
        """
        logger.info(f"Iniciando sincronización de oportunidad: {oportunidad.id}")
        
        # Verificar si la oportunidad ya existe en cache
        cache_key = f"wp_sync_{oportunidad.id}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            logger.info(f"Encontrado en cache: {oportunidad.id}")
            return True, cached_data
            
        # Preparar datos para sincronización
        data = {
            'title': oportunidad.titulo,
            'content': oportunidad.descripcion,
            'status': 'publish',
            'meta': {
                'tipo_contrato': oportunidad.tipo_contrato,
                'salario_minimo': str(oportunidad.salario_minimo),
                'salario_maximo': str(oportunidad.salario_maximo),
                'pais': oportunidad.pais,
                'ciudad': oportunidad.ciudad,
                'modalidad': oportunidad.modalidad,
                'empleador_id': str(oportunidad.empleador.id),
                'business_unit': oportunidad.empleador.business_unit.name if oportunidad.empleador.business_unit else 'default'
            }
        }
        
        # Intentar sincronizar
        success, response = await self._make_request('POST', 'wp-json/wp/v2/posts', data)
        
        if success:
            # Guardar en cache
            cache.set(cache_key, response, self.cache_timeout)
            logger.info(f"Sincronización exitosa para {oportunidad.id}")
            
            # Actualizar estado de sincronización
            oportunidad.sincronizado = True
            oportunidad.fecha_ultima_sincronizacion = timezone.now()
            await sync_to_async(oportunidad.save)()
            
            # Notificar al empleador si es necesario
            await self._notify_empleador(oportunidad.empleador, 'nueva_oportunidad')
            
        else:
            logger.error(f"Error al sincronizar {oportunidad.id}: {response}")
            
        return success, response

    async def _notify_empleador(self, empleador: Empleador, evento: str):
        """
        Notifica al empleador sobre eventos relacionados con la sincronización.
        
        Args:
            empleador: Instancia de Empleador
            evento: Tipo de evento (nueva_oportunidad, actualizacion_oportunidad, etc.)
        """
        try:
            if not empleador.email:
                logger.warning(f"No se puede notificar a {empleador.id}: email no disponible")
                return
                
            subject = {
                'nueva_oportunidad': 'Nueva oportunidad sincronizada',
                'nueva_cuenta': 'Cuenta sincronizada exitosamente',
                'actualizacion_oportunidad': 'Oportunidad actualizada',
                'eliminacion_oportunidad': 'Oportunidad eliminada'
            }.get(evento, 'Notificación de sincronización')
            
            await send_email(
                to=empleador.email,
                subject=subject,
                template=f'sync_{evento}',
                context={'empleador': empleador}
            )
            logger.info(f"Notificación enviada a {empleador.email} para evento {evento}")
            
        except Exception as e:
            logger.error(f"Error al notificar a {empleador.id}: {str(e)}")

    async def sincronizar_empleador(self, empleador: Empleador):
        """
        Sincroniza un empleador con WordPress.
        
        Args:
            empleador: Instancia de Empleador a sincronizar
            
        Returns:
            Tuple[bool, Dict]: (éxito, respuesta)
        """
        logger.info(f"Iniciando sincronización de empleador: {empleador.id}")
        
        data = {
            'title': empleador.razon_social,
            'content': f"Razón social: {empleador.razon_social}\n"
                      f"RFC: {empleador.rfc}\n"
                      f"Dirección: {empleador.direccion_fiscal}\n"
                      f"Business Unit: {empleador.business_unit.name if empleador.business_unit else 'N/A'}",
            'status': 'publish',
            'meta': {
                'rfc': empleador.rfc,
                'direccion_fiscal': empleador.direccion_fiscal,
                'clabe': empleador.clabe,
                'banco': empleador.banco,
                'business_unit': empleador.business_unit.name if empleador.business_unit else 'default'
            }
        }
        
        success, response = await self._make_request('POST', 'wp-json/wp/v2/posts', data)
        
        if success:
            logger.info(f"Sincronización exitosa para {empleador.id}")
            empleador.sincronizado = True
            empleador.fecha_ultima_sincronizacion = timezone.now()
            await sync_to_async(empleador.save)()
            
            # Notificar al empleador si es necesario
            await self._notify_empleador(empleador, 'nueva_cuenta')
        else:
            logger.error(f"Error al sincronizar {empleador.id}: {response}")
            
        return success, response

    async def actualizar_oportunidad(self, oportunidad: Oportunidad, wp_id: int):
        """
        Actualiza una oportunidad existente en WordPress.
        
        Args:
            oportunidad: Instancia de Oportunidad a actualizar
            wp_id: ID de la publicación en WordPress
            
        Returns:
            Tuple[bool, Dict]: (éxito, respuesta)
        """
        logger.info(f"Iniciando actualización de oportunidad: {oportunidad.id}")
        
        data = {
            'title': oportunidad.titulo,
            'content': oportunidad.descripcion,
            'meta': {
                'tipo_contrato': oportunidad.tipo_contrato,
                'salario_minimo': str(oportunidad.salario_minimo),
                'salario_maximo': str(oportunidad.salario_maximo),
                'pais': oportunidad.pais,
                'ciudad': oportunidad.ciudad,
                'modalidad': oportunidad.modalidad,
                'empleador_id': str(oportunidad.empleador.id),
                'business_unit': oportunidad.empleador.business_unit.name if oportunidad.empleador.business_unit else 'default'
            }
        }
        
        # Intentar actualizar
        success, response = await self._make_request('POST', f'wp-json/wp/v2/posts/{wp_id}', data)
        
        if success:
            logger.info(f"Actualización exitosa para {oportunidad.id}")
            oportunidad.fecha_ultima_sincronizacion = timezone.now()
            await sync_to_async(oportunidad.save)()
            
            # Notificar cambios si es necesario
            await self._notify_empleador(oportunidad.empleador, 'actualizacion_oportunidad')
        else:
            logger.error(f"Error al actualizar {oportunidad.id}: {response}")
            
        return success, response

    async def eliminar_oportunidad(self, wp_id: int, oportunidad_id: int):
        """
        Elimina una oportunidad de WordPress.
        
        Args:
            wp_id: ID de la publicación en WordPress
            oportunidad_id: ID de la oportunidad en el sistema
            
        Returns:
            Tuple[bool, Dict]: (éxito, respuesta)
        """
        logger.info(f"Iniciando eliminación de oportunidad: {oportunidad_id}")
        
        # Intentar eliminar
        success, response = await self._make_request('DELETE', f'wp-json/wp/v2/posts/{wp_id}')
        
        if success:
            logger.info(f"Eliminación exitosa para {oportunidad_id}")
            
            # Limpiar cache
            cache_key = f"wp_sync_{oportunidad_id}"
            cache.delete(cache_key)
            
            # Notificar al empleador si es necesario
            oportunidad = await sync_to_async(Oportunidad.objects.get)(id=oportunidad_id)
            await self._notify_empleador(oportunidad.empleador, 'eliminacion_oportunidad')
        else:
            logger.error(f"Error al eliminar {oportunidad_id}: {response}")
            
        return success, response
