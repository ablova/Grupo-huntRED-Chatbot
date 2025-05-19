from celery import shared_task
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
import logging
from app.models import SincronizacionLog, SincronizacionError
from app.com.pagos.sync.wordpress import WordPressSync
from app.pagos.models import Empleador, Oportunidad, Candidato
from typing import Dict, Any

logger = logging.getLogger('pagos_tasks')

@shared_task
def sincronizar_opportunidad_task(opportunidad_id: int) -> Dict[str, Any]:
    """
    Tarea Celery para sincronizar una oportunidad con WordPress.
    
    Args:
        oportunidad_id: ID de la oportunidad a sincronizar
        
    Returns:
        Dict con el resultado de la sincronización
    """
    try:
        # Inicializar sincronizador
        sync = WordPressSync()
        sync.initialize()
        
        # Registrar inicio de sincronización
        log = SincronizacionLog.objects.create(
            oportunidad_id=oportunidad_id,
            estado='in_progress'
        )
        
        # Realizar sincronización
        result = sync.sincronizar_oportunidad(opportunidad_id)
        
        # Actualizar log de sincronización
        log.estado = 'completed'
        log.resultado = result
        log.save()
        
        return result
        
    except Exception as e:
        # Registrar error
        error = SincronizacionError.objects.create(
            oportunidad_id=oportunidad_id,
            mensaje=str(e),
            intento=log.intentos + 1
        )
        
        # Actualizar log de sincronización
        log.estado = 'failed'
        log.error = error
        log.save()
        raise

@shared_task
def sincronizar_empresa_task(empresa_id: int) -> Dict[str, Any]:
    """
    Tarea Celery para sincronizar una empresa con WordPress.
    
    Args:
        empresa_id: ID de la empresa a sincronizar
        
    Returns:
        Dict con el resultado de la sincronización
    """
    try:
        # Inicializar sincronizador
        sync = WordPressSync()
        sync.initialize()
        
        # Obtener empresa
        empresa = Empleador.objects.get(id=empresa_id)
        
        # Realizar sincronización
        success, result = sync.sincronizar_empresa(empresa)
        
        # Registrar resultado
        if success:
            log = SincronizacionLog.objects.create(
                oportunidad_id=None,
                estado='completed',
                detalle={'empresa_id': empresa_id, 'resultado': result}
            )
        else:
            error = SincronizacionError.objects.create(
                oportunidad_id=None,
                mensaje=f"Error sincronizando empresa {empresa_id}: {result.get('error', 'Desconocido')}",
                intento=1
            )
            log = SincronizacionLog.objects.create(
                oportunidad_id=None,
                estado='failed',
                error=error
            )
        
        return {'success': success, 'result': result}
        
    except Exception as e:
        error = SincronizacionError.objects.create(
            oportunidad_id=None,
            mensaje=f"Error sincronizando empresa {empresa_id}: {str(e)}",
            intento=1
        )
        log = SincronizacionLog.objects.create(
            oportunidad_id=None,
            estado='failed',
            error=error
        )
        raise

@shared_task
def sincronizar_candidato_task(candidato_id: int) -> Dict[str, Any]:
    """
    Tarea Celery para sincronizar un candidato con WordPress.
    
    Args:
        candidato_id: ID del candidato a sincronizar
        
    Returns:
        Dict con el resultado de la sincronización
    """
    try:
        # Inicializar sincronizador
        sync = WordPressSync()
        sync.initialize()
        
        # Obtener candidato
        candidato = Candidato.objects.get(id=candidato_id)
        
        # Realizar sincronización
        success, result = sync.sincronizar_candidato(candidato)
        
        # Registrar resultado
        if success:
            log = SincronizacionLog.objects.create(
                oportunidad_id=None,
                estado='completed',
                detalle={'candidato_id': candidato_id, 'resultado': result}
            )
        else:
            error = SincronizacionError.objects.create(
                oportunidad_id=None,
                mensaje=f"Error sincronizando candidato {candidato_id}: {result.get('error', 'Desconocido')}",
                intento=1
            )
            log = SincronizacionLog.objects.create(
                oportunidad_id=None,
                estado='failed',
                error=error
            )
        
        return {'success': success, 'result': result}
        
    except Exception as e:
        error = SincronizacionError.objects.create(
            oportunidad_id=None,
            mensaje=f"Error sincronizando candidato {candidato_id}: {str(e)}",
            intento=1
        )
        log = SincronizacionLog.objects.create(
            oportunidad_id=None,
            estado='failed',
            error=error
        )
        raise

@shared_task
def sincronizar_pricing_task(business_unit: str) -> Dict[str, Any]:
    """
    Tarea Celery para sincronizar la configuración de pricing para una Business Unit específica.
    
    Args:
        business_unit: Nombre de la Business Unit (huntRED, huntU, Amigro)
        
    Returns:
        Dict con estadísticas de la sincronización
    """
    try:
        # Inicializar sincronizador para la Business Unit específica
        sync = WordPressSync(business_unit)
        sync.initialize()
        
        # Obtener configuraciones de pricing
        pricing_config = {
            'baselines': PricingBaseline.objects.filter(bu=business_unit),
            'addons': Addons.objects.filter(bu=business_unit),
            'coupons': Coupons.objects.filter(bu=business_unit),
            'milestones': PaymentMilestones.objects.filter(bu=business_unit)
        }
        
        # Sincronizar cada tipo de configuración
        stats = {
            'baselines': sync.sincronizar_baselines(pricing_config['baselines']),
            'addons': sync.sincronizar_addons(pricing_config['addons']),
            'coupons': sync.sincronizar_coupons(pricing_config['coupons']),
            'milestones': sync.sincronizar_milestones(pricing_config['milestones'])
        }
        
        # Registrar estadísticas
        log = SincronizacionLog.objects.create(
            oportunidad_id=None,
            estado='completed',
            detalle={'pricing': stats, 'business_unit': business_unit}
        )
        
        return stats
        
    except Exception as e:
        error = SincronizacionError.objects.create(
            oportunidad_id=None,
            mensaje=f"Error en sincronización de pricing para {business_unit}: {str(e)}",
            intento=1
        )
        log = SincronizacionLog.objects.create(
            oportunidad_id=None,
            estado='failed',
            error=error
        )
        raise

@shared_task
def sincronizar_todo_task() -> Dict[str, Any]:
    """
    Tarea Celery para sincronizar todos los registros (empresas, candidatos, oportunidades y pricing).
    
    Returns:
        Dict con estadísticas de la sincronización
    """
    try:
        # Inicializar sincronizador
        sync = WordPressSync()
        sync.initialize()
        
        # Realizar sincronización completa
        stats = sync.sincronizar_todos()
        
        # Registrar estadísticas
        log = SincronizacionLog.objects.create(
            oportunidad_id=None,
            estado='completed',
            detalle=stats
        )
        
        return stats
        
    except Exception as e:
        error = SincronizacionError.objects.create(
            oportunidad_id=None,
            mensaje=f"Error en sincronización completa: {str(e)}",
            intento=1
        )
        log = SincronizacionLog.objects.create(
            oportunidad_id=None,
            estado='failed',
            error=error
        )
        raise

@shared_task
def procesar_sincronizaciones_pendientes() -> None:
    """
    Tarea Celery para procesar todas las oportunidades pendientes de sincronización.
    """
    try:
        # Obtener oportunidades pendientes
        oportunidades = Oportunidad.objects.filter(
            sincronizado=False,
            fecha_creacion__lte=timezone.now()
        )
        
        # Procesar cada oportunidad
        for oportunidad in oportunidades:
            sincronizar_opportunidad_task.delay(oportunidad.id)
            
    except Exception as e:
        # Registrar error general
        logger.error(f"Error procesando sincronizaciones: {str(e)}")
        raise

@shared_task
def limpiar_logs_antiguos(dias: int = 30) -> None:
    """
    Tarea Celery para eliminar logs de sincronización antiguos.
    
    Args:
        dias: Número de días a mantener los logs
    """
    try:
        fecha_limite = timezone.now() - timezone.timedelta(days=dias)
        
        # Eliminar logs antiguos
        SincronizacionLog.objects.filter(
            fecha_creacion__lt=fecha_limite
        ).delete()
        
        # Eliminar errores antiguos
        SincronizacionError.objects.filter(
            fecha_creacion__lt=fecha_limite
        ).delete()
        
    except Exception as e:
        logger.error(f"Error limpiando logs antiguos: {str(e)}")
        raise
