# /home/pablo/app/com/pagos/sync/wordpress.py
import requests
import logging
import time
import json
from typing import Optional, Dict, Any, Tuple
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from django.core.mail import EmailMessage
from app.pagos.models import Oportunidad, Empleador, SincronizacionError, SincronizacionLog, Candidato
from app.com.utils.vacantes import VacanteManager
from app.models import ConfiguracionBU, BusinessUnit, User, PricingBaseline, Addons, Coupons, PaymentMilestones
from asgiref.sync import sync_to_async
from celery.exceptions import MaxRetriesExceededError
from app.com.pagos.config.wordpress import WORDPRESS_CONFIG, WORDPRESS_SETTINGS

logger = logging.getLogger('wordpress_sync')

class WordPressSync:
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
        
        # Configurar autenticación
        self.base_url = self.config['base_url']
        self.auth_token = self.config['auth_token'] or settings.WORDPRESS_AUTH_TOKEN
        self.auth = (self.auth_token, '')
        
        self.vacante_manager = None
        self.current_retries = 0
        
    async def initialize(self):
        """Inicializa el VacanteManager de manera asíncrona."""
        if not self.vacante_manager:
            self.vacante_manager = VacanteManager({
                'business_unit': self.business_unit,
                'job_title': 'default',
                'job_description': 'default',
                'company_name': 'default'
            })
            await self.vacante_manager.initialize()

    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None):
        """
        Realiza una solicitud HTTP a la API de WordPress con manejo de reintentos.
        
        Args:
            method: Método HTTP (GET, POST, PUT, DELETE)
            endpoint: Endpoint de la API
            data: Datos a enviar (opcional)
            
        Returns:
            Respuesta de la API
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
                    timeout=30
                )
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.RequestException as e:
                self.current_retries += 1
                
                # Registrar error en la base de datos
                error = SincronizacionError.objects.create(
                    mensaje=str(e),
                    intento=self.current_retries
                )
                
                # Si es el último intento, lanzar la excepción
                if attempt == self.retry_attempts - 1:
                    raise
                    
                # Esperar antes de reintentar
                time.sleep(self.retry_delay * (attempt + 1))
                
    async def sincronizar_baselines(self, baselines: QuerySet) -> Dict[str, Any]:
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
                self._make_request('POST', endpoint, data)
                
                stats['success'] += 1
            except Exception as e:
                stats['errors'].append({
                    'id': baseline.id,
                    'error': str(e)
                })
            
            stats['total'] += 1
        
        return stats

    async def sincronizar_addons(self, addons: QuerySet) -> Dict[str, Any]:
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
                self._make_request('POST', endpoint, data)
                
                stats['success'] += 1
            except Exception as e:
                stats['errors'].append({
                    'id': addon.id,
                    'error': str(e)
                })
            
            stats['total'] += 1
        
        return stats

    async def sincronizar_coupons(self, coupons: QuerySet) -> Dict[str, Any]:
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
                self._make_request('POST', endpoint, data)
                
                stats['success'] += 1
            except Exception as e:
                stats['errors'].append({
                    'id': coupon.id,
                    'error': str(e)
                })
            
            stats['total'] += 1
        
        return stats

    async def sincronizar_milestones(self, milestones: QuerySet) -> Dict[str, Any]:
        """
        Sincroniza los hitos de pago con WordPress.
        
        Args:
            milestones: QuerySet de PaymentMilestones
            
        Returns:
            Dict con estadísticas de la sincronización
        """
        stats = {'total': 0, 'success': 0, 'errors': []}
        
        for milestone in milestones:
            try:
                data = {
                    'bu': milestone.bu.name,
                    'milestone_name': milestone.milestone_name,
                    'percentage': str(milestone.percentage),
                    'trigger_event': milestone.trigger_event,
                    'due_date_offset': milestone.due_date_offset
                }
                
                # Usar el endpoint específico para milestones
                endpoint = self.config['endpoints']['milestones']
                self._make_request('POST', endpoint, data)
                
                stats['success'] += 1
            except Exception as e:
                stats['errors'].append({
                    'id': milestone.id,
                    'error': str(e)
                })
            
            stats['total'] += 1
        
        return stats

    async def sincronizar_oportunidad(self, oportunidad_id: int) -> Dict[str, Any]:
        try:
            oportunidad = await sync_to_async(Oportunidad.objects.get)(id=oportunidad_id)
            
            # Verificar si ya existe en WordPress
            wp_id = await sync_to_async(self._get_wp_id)(oportunidad)
            
            if wp_id:
                # Actualizar
                await sync_to_async(self._update_wp_opportunity)(oportunidad, wp_id)
            else:
                # Crear nuevo
                wp_id = await sync_to_async(self._create_wp_opportunity)(oportunidad)
                
            return {
                'wp_id': wp_id,
                'status': 'success',
                'message': 'Sincronización exitosa'
            }
            
        except Exception as e:
            # Registrar error
            await sync_to_async(SincronizacionError.objects.create)(
                oportunidad_id=oportunidad_id,
                mensaje=str(e),
                intento=self.current_retries
            )
            raise

    def _get_wp_id(self, oportunidad: Oportunidad) -> Optional[int]:
        """
        Obtiene el ID de WordPress para una oportunidad.
        
        Args:
            oportunidad: Oportunidad a verificar
            
        Returns:
            ID de WordPress si existe, None si no
        """
        try:
            response = self._make_request(
                'GET',
                f'opportunities?external_id={oportunidad.id}'
            )
            if response and isinstance(response, list) and len(response) > 0:
                return response[0].get('id')
            return None
            
        except Exception as e:
            logger.error(f"Error obteniendo WP ID: {str(e)}")
            return None

    def _create_wp_opportunity(self, oportunidad: Oportunidad) -> int:
        """
        Crea una nueva oportunidad en WordPress.
        
        Args:
            oportunidad: Oportunidad a crear
            
        Returns:
            ID de la oportunidad creada en WordPress
        """
        data = {
            'external_id': str(oportunidad.id),
            'title': oportunidad.titulo,
            'description': oportunidad.descripcion,
            'status': oportunidad.estado,
            'created_at': oportunidad.fecha_creacion.isoformat(),
            # Agregar otros campos necesarios
        }
        
        response = self._make_request('POST', 'opportunities', data)
        return response.get('id')

    def _update_wp_opportunity(self, oportunidad: Oportunidad, wp_id: int) -> None:
        """
        Actualiza una oportunidad existente en WordPress.
        
        Args:
            oportunidad: Oportunidad a actualizar
            wp_id: ID de la oportunidad en WordPress
        """
        data = {
            'title': oportunidad.titulo,
            'description': oportunidad.descripcion,
            'status': oportunidad.estado,
            'updated_at': timezone.now().isoformat(),
            # Agregar otros campos necesarios
        }
        
        self._make_request(
            'PUT',
            f'opportunities/{wp_id}',
            data
        )

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

    async def sincronizar_empresa(self, empleador: Empleador) -> Tuple[bool, Dict]:
        """
        Sincroniza una empresa con WordPress.
        
        Args:
            empleador: Instancia de Empleador a sincronizar
            
        Returns:
            Tuple[bool, Dict]: (éxito, respuesta)
        """
        logger.info(f"Iniciando sincronización de empresa: {empleador.id}")
        
        # Verificar si ya existe en cache
        cache_key = f"wp_sync_empresa_{empleador.id}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            logger.info(f"Encontrado en cache: {empleador.id}")
            return True, cached_data
            
        # Preparar datos para sincronización
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
                'business_unit': empleador.business_unit.name if empleador.business_unit else 'default',
                'email': empleador.email,
                'telefono': empleador.telefono,
                'website': empleador.website
            }
        }
        
        # Intentar sincronizar
        success, response = await self._make_request('POST', 'wp-json/wp/v2/posts', data)
        
        if success:
            # Guardar en cache
            cache.set(cache_key, response, self.cache_timeout)
            logger.info(f"Sincronización exitosa para empresa {empleador.id}")
            
            # Actualizar estado de sincronización
            empleador.sincronizado = True
            empleador.fecha_ultima_sincronizacion = timezone.now()
            await sync_to_async(empleador.save)()
            
            # Notificar al empleador
            await self._notify_empleador(empleador, 'nueva_empresa')
            
        else:
            logger.error(f"Error al sincronizar empresa {empleador.id}: {response}")
            
        return success, response

    async def sincronizar_candidato(self, candidato: Candidato) -> Tuple[bool, Dict]:
        """
        Sincroniza un candidato con WordPress.
        
        Args:
            candidato: Instancia de Candidato a sincronizar
            
        Returns:
            Tuple[bool, Dict]: (éxito, respuesta)
        """
        logger.info(f"Iniciando sincronización de candidato: {candidato.id}")
        
        # Verificar si ya existe en cache
        cache_key = f"wp_sync_candidato_{candidato.id}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            logger.info(f"Encontrado en cache: {candidato.id}")
            return True, cached_data
            
        # Preparar datos para sincronización
        data = {
            'title': f"Perfil de {candidato.nombre} {candidato.apellidos}",
            'content': f"Nombre: {candidato.nombre} {candidato.apellidos}\n"
                      f"Email: {candidato.email}\n"
                      f"Teléfono: {candidato.telefono}\n"
                      f"Experiencia: {candidato.anios_experiencia} años\n"
                      f"Especialidad: {candidato.especialidad if candidato.especialidad else 'N/A'}",
            'status': 'publish',
            'meta': {
                'nombre': candidato.nombre,
                'apellidos': candidato.apellidos,
                'email': candidato.email,
                'telefono': candidato.telefono,
                'anios_experiencia': candidato.anios_experiencia,
                'especialidad': candidato.especialidad,
                'estado': candidato.estado,
                'ciudad': candidato.ciudad,
                'modalidad': candidato.modalidad,
                'salario_minimo': str(candidato.salario_minimo) if candidato.salario_minimo else 'N/A',
                'salario_maximo': str(candidato.salario_maximo) if candidato.salario_maximo else 'N/A'
            }
        }
        
        # Intentar sincronizar
        success, response = await self._make_request('POST', 'wp-json/wp/v2/posts', data)
        
        if success:
            # Guardar en cache
            cache.set(cache_key, response, self.cache_timeout)
            logger.info(f"Sincronización exitosa para candidato {candidato.id}")
            
            # Actualizar estado de sincronización
            candidato.sincronizado = True
            candidato.fecha_ultima_sincronizacion = timezone.now()
            await sync_to_async(candidato.save)()
            
            # Notificar al candidato si tiene email
            if candidato.email:
                email = EmailMessage(
                    subject='Perfil sincronizado en huntRED®',
                    body=f'Su perfil ha sido sincronizado exitosamente en nuestro sistema.',
                    to=[candidato.email]
                )
                await sync_to_async(email.send)()
            
        else:
            logger.error(f"Error al sincronizar candidato {candidato.id}: {response}")
            
        return success, response

    async def sincronizar_pricing(self) -> Dict[str, Any]:
        """
        Sincroniza la configuración de pricing con WordPress.
        
        Returns:
            Dict con estadísticas de la sincronización de pricing
        """
        stats = {
            'baselines': {'total': 0, 'exitos': 0, 'errores': 0},
            'addons': {'total': 0, 'exitos': 0, 'errores': 0},
            'coupons': {'total': 0, 'exitos': 0, 'errores': 0},
            'milestones': {'total': 0, 'exitos': 0, 'errores': 0}
        }
        
        try:
            # Sincronizar baselines
            baselines = PricingBaseline.objects.all()
            stats['baselines']['total'] = len(baselines)
            for baseline in baselines:
                success = await self._sincronizar_baseline(baseline)
                stats['baselines']['exitos' if success else 'errores'] += 1
            
            # Sincronizar addons
            addons = Addons.objects.all()
            stats['addons']['total'] = len(addons)
            for addon in addons:
                success = await self._sincronizar_addon(addon)
                stats['addons']['exitos' if success else 'errores'] += 1
            
            # Sincronizar coupons
            coupons = Coupons.objects.all()
            stats['coupons']['total'] = len(coupons)
            for coupon in coupons:
                success = await self._sincronizar_coupon(coupon)
                stats['coupons']['exitos' if success else 'errores'] += 1
            
            # Sincronizar payment milestones
            milestones = PaymentMilestones.objects.all()
            stats['milestones']['total'] = len(milestones)
            for milestone in milestones:
                success = await self._sincronizar_milestone(milestone)
                stats['milestones']['exitos' if success else 'errores'] += 1
            
            return stats
            
        except Exception as e:
            logger.error(f"Error en sincronización de pricing: {str(e)}")
            raise

    async def _sincronizar_baseline(self, baseline: PricingBaseline) -> bool:
        """
        Sincroniza un PricingBaseline con WordPress.
        
        Args:
            baseline: Instancia de PricingBaseline a sincronizar
            
        Returns:
            bool: True si la sincronización fue exitosa
        """
        data = {
            'title': f"Baseline Pricing - {baseline.bu.name} - {baseline.model}",
            'content': f"Configuración de precios base para {baseline.bu.name} - {baseline.model}",
            'status': 'publish',
            'meta': {
                'bu': baseline.bu.name,
                'model': baseline.model,
                'base_price': str(baseline.base_price),
                'percentage': str(baseline.percentage),
                'active': baseline.active,
                'created_at': baseline.created_at.isoformat(),
                'updated_at': baseline.updated_at.isoformat()
            }
        }
        
        success, _ = await self._make_request('POST', 'wp-json/wp/v2/pricing/baselines', data)
        return success

    async def _sincronizar_addon(self, addon: Addons) -> bool:
        """
        Sincroniza un Addon con WordPress.
        
        Args:
            addon: Instancia de Addons a sincronizar
            
        Returns:
            bool: True si la sincronización fue exitosa
        """
        data = {
            'title': f"Addon - {addon.name}",
            'content': f"Descripción del addon: {addon.description if addon.description else 'N/A'}",
            'status': 'publish',
            'meta': {
                'name': addon.name,
                'description': addon.description or '',
                'price': str(addon.price),
                'max_per_vacancy': addon.max_per_vacancy,
                'active': addon.active,
                'created_at': addon.created_at.isoformat(),
                'updated_at': addon.updated_at.isoformat()
            }
        }
        
        success, _ = await self._make_request('POST', 'wp-json/wp/v2/pricing/addons', data)
        return success

    async def _sincronizar_coupon(self, coupon: Coupons) -> bool:
        """
        Sincroniza un Coupon con WordPress.
        
        Args:
            coupon: Instancia de Coupons a sincronizar
            
        Returns:
            bool: True si la sincronización fue exitosa
        """
        data = {
            'title': f"Coupon - {coupon.code}",
            'content': f"Cupón de descuento: {coupon.code}",
            'status': 'publish',
            'meta': {
                'code': coupon.code,
                'type': coupon.type,
                'value': str(coupon.value),
                'valid_until': coupon.valid_until.isoformat() if coupon.valid_until else None,
                'max_uses': coupon.max_uses,
                'current_uses': coupon.current_uses,
                'active': coupon.active,
                'created_at': coupon.created_at.isoformat(),
                'updated_at': coupon.updated_at.isoformat()
            }
        }
        
        success, _ = await self._make_request('POST', 'wp-json/wp/v2/pricing/coupons', data)
        return success

    async def _sincronizar_milestone(self, milestone: PaymentMilestones) -> bool:
        """
        Sincroniza un PaymentMilestone con WordPress.
        
        Args:
            milestone: Instancia de PaymentMilestones a sincronizar
            
        Returns:
            bool: True si la sincronización fue exitosa
        """
        data = {
            'title': f"Payment Milestone - {milestone.milestone_name}",
            'content': f"Hito de pago: {milestone.milestone_name}",
            'status': 'publish',
            'meta': {
                'bu': milestone.bu.name,
                'milestone_name': milestone.milestone_name,
                'percentage': str(milestone.percentage),
                'trigger_event': milestone.trigger_event,
                'due_date_offset': milestone.due_date_offset,
                'active': milestone.active,
                'created_at': milestone.created_at.isoformat(),
                'updated_at': milestone.updated_at.isoformat()
            }
        }
        
        success, _ = await self._make_request('POST', 'wp-json/wp/v2/pricing/milestones', data)
        return success

    async def sincronizar_todos(self) -> Dict[str, Any]:
        """
        Sincroniza todos los registros (empresas, candidatos, oportunidades y pricing).
        
        Returns:
            Dict con estadísticas de la sincronización
        """
        stats = {
            'empresas': {'total': 0, 'exitos': 0, 'errores': 0},
            'candidatos': {'total': 0, 'exitos': 0, 'errores': 0},
            'oportunidades': {'total': 0, 'exitos': 0, 'errores': 0},
            'pricing': {
                'baselines': {'total': 0, 'exitos': 0, 'errores': 0},
                'addons': {'total': 0, 'exitos': 0, 'errores': 0},
                'coupons': {'total': 0, 'exitos': 0, 'errores': 0},
                'milestones': {'total': 0, 'exitos': 0, 'errores': 0}
            }
        }
        
        try:
            # Sincronizar empresas
            empresas = Empleador.objects.filter(sincronizado=False)
            stats['empresas']['total'] = len(empresas)
            for empresa in empresas:
                success, _ = await self.sincronizar_empresa(empresa)
                stats['empresas']['exitos' if success else 'errores'] += 1
            
            # Sincronizar candidatos
            candidatos = Candidato.objects.filter(sincronizado=False)
            stats['candidatos']['total'] = len(candidatos)
            for candidato in candidatos:
                success, _ = await self.sincronizar_candidato(candidato)
                stats['candidatos']['exitos' if success else 'errores'] += 1
            
            # Sincronizar oportunidades
            oportunidades = Oportunidad.objects.filter(sincronizado=False)
            stats['oportunidades']['total'] = len(oportunidades)
            for oportunidad in oportunidades:
                success, _ = await self.sincronizar_oportunidad(oportunidad.id)
                stats['oportunidades']['exitos' if success else 'errores'] += 1
            
            # Sincronizar pricing
            pricing_stats = await self.sincronizar_pricing()
            stats['pricing'] = pricing_stats
            
            return stats
            
        except Exception as e:
            logger.error(f"Error en sincronización general: {str(e)}")
            raise

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
            
            # Implementación básica de send_email usando Django's EmailMessage
            from django.core.mail import EmailMessage
            
            email = EmailMessage(
                subject=subject,
                body=f"Se ha realizado una {evento} para su cuenta.",
                to=[empleador.email]
            )
            await sync_to_async(email.send)()
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
        success, response = await self._make_request('PUT', f'wp-json/wp/v2/posts/{wp_id}', data)
        
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
