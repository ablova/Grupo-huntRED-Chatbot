"""
Tareas Celery para notificaciones estratégicas automáticas.
"""
import logging
from typing import Dict, Any
from celery import shared_task
from django.utils import timezone
from datetime import timedelta

from app.ats.notifications.strategic_notifications import StrategicNotificationService

logger = logging.getLogger(__name__)

@shared_task(bind=True, name='monitor_strategic_notifications')
def monitor_strategic_notifications(self, business_unit: str = None):
    """
    Tarea para monitorear y enviar notificaciones estratégicas.
    """
    try:
        logger.info(f"Iniciando monitoreo de notificaciones estratégicas para {business_unit or 'todas las unidades'}")
        
        # Crear instancia del servicio
        notification_service = StrategicNotificationService()
        
        # Importar asyncio para manejar async
        import asyncio
        
        # Ejecutar monitoreo
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(
                notification_service.monitor_and_notify(business_unit)
            )
        finally:
            loop.close()
        
        logger.info("Monitoreo de notificaciones estratégicas completado exitosamente")
        
        return {
            'success': True,
            'message': 'Monitoreo completado',
            'business_unit': business_unit,
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error en monitoreo de notificaciones estratégicas: {str(e)}")
        
        # Notificar error
        try:
            notification_service = StrategicNotificationService()
            import asyncio
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                loop.run_until_complete(
                    notification_service._send_error_notification(str(e))
                )
            finally:
                loop.close()
        except Exception as notify_error:
            logger.error(f"Error enviando notificación de error: {str(notify_error)}")
        
        # Re-raise para que Celery maneje el retry
        raise

@shared_task(bind=True, name='send_manual_strategic_notification')
def send_manual_strategic_notification(
    self,
    title: str,
    message: str,
    recipients: list,
    priority: str = 'medium',
    context: Dict[str, Any] = None
):
    """
    Tarea para enviar notificación manual.
    """
    try:
        logger.info(f"Enviando notificación manual: {title}")
        
        # Crear instancia del servicio
        notification_service = StrategicNotificationService()
        
        # Importar enum de prioridad
        from app.ats.notifications.strategic_notifications import NotificationPriority
        
        priority_enum = NotificationPriority(priority)
        
        # Importar asyncio para manejar async
        import asyncio
        
        # Ejecutar envío
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(
                notification_service.send_manual_notification(
                    title=title,
                    message=message,
                    recipients=recipients,
                    priority=priority_enum,
                    context=context or {}
                )
            )
        finally:
            loop.close()
        
        logger.info(f"Notificación manual enviada exitosamente: {title}")
        
        return {
            'success': True,
            'message': 'Notificación enviada',
            'title': title,
            'recipients': recipients,
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error enviando notificación manual: {str(e)}")
        raise

@shared_task(bind=True, name='monitor_campaign_notifications')
def monitor_campaign_notifications(self, business_unit: str = None):
    """
    Tarea específica para monitorear notificaciones de campañas.
    """
    try:
        logger.info(f"Monitoreando notificaciones de campañas para {business_unit or 'todas las unidades'}")
        
        # Crear instancia del servicio
        notification_service = StrategicNotificationService()
        
        # Importar asyncio para manejar async
        import asyncio
        
        # Ejecutar monitoreo de campañas
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(
                notification_service._monitor_campaigns(business_unit)
            )
        finally:
            loop.close()
        
        logger.info("Monitoreo de campañas completado")
        
        return {
            'success': True,
            'message': 'Monitoreo de campañas completado',
            'business_unit': business_unit,
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error monitoreando campañas: {str(e)}")
        raise

@shared_task(bind=True, name='monitor_insights_notifications')
def monitor_insights_notifications(self, business_unit: str = None):
    """
    Tarea específica para monitorear notificaciones de insights estratégicos.
    """
    try:
        logger.info(f"Monitoreando insights estratégicos para {business_unit or 'todas las unidades'}")
        
        # Crear instancia del servicio
        notification_service = StrategicNotificationService()
        
        # Importar asyncio para manejar async
        import asyncio
        
        # Ejecutar monitoreo de insights
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(
                notification_service._monitor_strategic_insights(business_unit)
            )
        finally:
            loop.close()
        
        logger.info("Monitoreo de insights completado")
        
        return {
            'success': True,
            'message': 'Monitoreo de insights completado',
            'business_unit': business_unit,
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error monitoreando insights: {str(e)}")
        raise

@shared_task(bind=True, name='monitor_critical_metrics_notifications')
def monitor_critical_metrics_notifications(self, business_unit: str = None):
    """
    Tarea específica para monitorear métricas críticas.
    """
    try:
        logger.info(f"Monitoreando métricas críticas para {business_unit or 'todas las unidades'}")
        
        # Crear instancia del servicio
        notification_service = StrategicNotificationService()
        
        # Importar asyncio para manejar async
        import asyncio
        
        # Ejecutar monitoreo de métricas críticas
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(
                notification_service._monitor_critical_metrics(business_unit)
            )
        finally:
            loop.close()
        
        logger.info("Monitoreo de métricas críticas completado")
        
        return {
            'success': True,
            'message': 'Monitoreo de métricas críticas completado',
            'business_unit': business_unit,
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error monitoreando métricas críticas: {str(e)}")
        raise

@shared_task(bind=True, name='monitor_environmental_factors_notifications')
def monitor_environmental_factors_notifications(self, business_unit: str = None):
    """
    Tarea específica para monitorear factores del entorno.
    """
    try:
        logger.info(f"Monitoreando factores del entorno para {business_unit or 'todas las unidades'}")
        
        # Crear instancia del servicio
        notification_service = StrategicNotificationService()
        
        # Importar asyncio para manejar async
        import asyncio
        
        # Ejecutar monitoreo de factores del entorno
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(
                notification_service._monitor_environmental_factors(business_unit)
            )
        finally:
            loop.close()
        
        logger.info("Monitoreo de factores del entorno completado")
        
        return {
            'success': True,
            'message': 'Monitoreo de factores del entorno completado',
            'business_unit': business_unit,
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error monitoreando factores del entorno: {str(e)}")
        raise

@shared_task(bind=True, name='cleanup_old_notifications')
def cleanup_old_notifications(self, days: int = 30):
    """
    Tarea para limpiar notificaciones antiguas del cache.
    """
    try:
        logger.info(f"Limpiando notificaciones antiguas (más de {days} días)")
        
        # Crear instancia del servicio
        notification_service = StrategicNotificationService()
        
        # Obtener fecha límite
        cutoff_date = timezone.now() - timedelta(days=days)
        
        # Limpiar notificaciones antiguas del cache
        keys_to_remove = []
        for key, timestamp in notification_service.last_notifications.items():
            if timestamp < cutoff_date:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del notification_service.last_notifications[key]
        
        logger.info(f"Limpieza completada. Eliminadas {len(keys_to_remove)} notificaciones antiguas")
        
        return {
            'success': True,
            'message': 'Limpieza completada',
            'removed_count': len(keys_to_remove),
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error en limpieza de notificaciones: {str(e)}")
        raise

@shared_task(bind=True, name='generate_notification_report')
def generate_notification_report(self, business_unit: str = None, days: int = 7):
    """
    Tarea para generar reporte de notificaciones enviadas.
    """
    try:
        logger.info(f"Generando reporte de notificaciones para {business_unit or 'todas las unidades'} (últimos {days} días)")
        
        # Crear instancia del servicio
        notification_service = StrategicNotificationService()
        
        # Obtener fecha límite
        cutoff_date = timezone.now() - timedelta(days=days)
        
        # Filtrar notificaciones recientes
        recent_notifications = {
            key: timestamp for key, timestamp in notification_service.last_notifications.items()
            if timestamp >= cutoff_date
        }
        
        # Agrupar por tipo
        notification_types = {}
        for key in recent_notifications.keys():
            if '_' in key:
                notification_type = key.split('_')[0]
                if notification_type not in notification_types:
                    notification_types[notification_type] = 0
                notification_types[notification_type] += 1
        
        report = {
            'total_notifications': len(recent_notifications),
            'notification_types': notification_types,
            'business_unit': business_unit,
            'period_days': days,
            'generated_at': timezone.now().isoformat()
        }
        
        logger.info(f"Reporte generado: {report['total_notifications']} notificaciones")
        
        return {
            'success': True,
            'report': report
        }
        
    except Exception as e:
        logger.error(f"Error generando reporte de notificaciones: {str(e)}")
        raise 