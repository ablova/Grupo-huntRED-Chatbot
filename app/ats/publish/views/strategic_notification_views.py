"""
Vistas para el dashboard de notificaciones estratégicas.
"""
import json
import logging
from typing import Dict, Any
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator
from django.views import View
from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta

from app.ats.notifications.strategic_notifications import StrategicNotificationService
from app.ats.publish.tasks.strategic_notification_tasks import (
    send_manual_strategic_notification,
    generate_notification_report,
    cleanup_old_notifications
)

logger = logging.getLogger(__name__)

def is_super_admin(user):
    """Verifica si el usuario es super admin."""
    return user.is_superuser

@login_required
@user_passes_test(is_super_admin)
def strategic_notifications_dashboard(request):
    """
    Vista principal del dashboard de notificaciones estratégicas.
    """
    return render(request, 'admin/strategic_notifications_dashboard.html')

@method_decorator(csrf_exempt, name='dispatch')
class StrategicNotificationAPIView(View):
    """
    API para gestionar notificaciones estratégicas.
    """
    
    def get(self, request, *args, **kwargs):
        """
        Obtiene notificaciones recientes.
        """
        try:
            # Obtener parámetros de filtro
            notification_type = request.GET.get('type')
            priority = request.GET.get('priority')
            business_unit = request.GET.get('business_unit')
            limit = int(request.GET.get('limit', 50))
            
            # Crear instancia del servicio
            notification_service = StrategicNotificationService()
            
            # Obtener notificaciones del cache
            notifications = []
            for key, timestamp in notification_service.last_notifications.items():
                # Filtrar por tipo si se especifica
                if notification_type and not key.startswith(notification_type):
                    continue
                
                # Crear objeto de notificación
                notification = {
                    'id': key,
                    'type': self._extract_type_from_key(key),
                    'priority': self._extract_priority_from_key(key),
                    'title': self._generate_title_from_key(key),
                    'message': self._generate_message_from_key(key),
                    'timestamp': timestamp.isoformat(),
                    'recipients': ['consultants', 'super_admins'],
                    'business_unit': business_unit or 'all'
                }
                
                # Filtrar por prioridad si se especifica
                if priority and notification['priority'] != priority:
                    continue
                
                notifications.append(notification)
            
            # Ordenar por timestamp (más recientes primero)
            notifications.sort(key=lambda x: x['timestamp'], reverse=True)
            
            # Limitar resultados
            notifications = notifications[:limit]
            
            return JsonResponse({
                'success': True,
                'notifications': notifications,
                'total': len(notifications)
            })
            
        except Exception as e:
            logger.error(f"Error obteniendo notificaciones: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500)
    
    def post(self, request, *args, **kwargs):
        """
        Envía notificación manual.
        """
        try:
            data = json.loads(request.body)
            
            title = data.get('title')
            message = data.get('message')
            priority = data.get('priority', 'medium')
            recipients = data.get('recipients', [])
            
            if not title or not message:
                return JsonResponse({
                    'success': False,
                    'message': 'Título y mensaje son requeridos'
                }, status=400)
            
            # Enviar notificación usando Celery
            task = send_manual_strategic_notification.delay(
                title=title,
                message=message,
                recipients=recipients,
                priority=priority
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Notificación enviada',
                'task_id': task.id
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'JSON inválido'
            }, status=400)
        except Exception as e:
            logger.error(f"Error enviando notificación: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500)
    
    def _extract_type_from_key(self, key: str) -> str:
        """Extrae el tipo de notificación de la clave."""
        if '_' in key:
            return key.split('_')[0]
        return 'unknown'
    
    def _extract_priority_from_key(self, key: str) -> str:
        """Extrae la prioridad de la clave."""
        if 'urgent' in key:
            return 'urgent'
        elif 'high' in key:
            return 'high'
        elif 'medium' in key:
            return 'medium'
        else:
            return 'low'
    
    def _generate_title_from_key(self, key: str) -> str:
        """Genera título basado en la clave."""
        type_mapping = {
            'campaign': 'Campaña',
            'sector': 'Sector',
            'process': 'Proceso',
            'error': 'Error',
            'strategic': 'Estratégico'
        }
        
        notification_type = self._extract_type_from_key(key)
        return f"{type_mapping.get(notification_type, 'Notificación')} - {key}"
    
    def _generate_message_from_key(self, key: str) -> str:
        """Genera mensaje basado en la clave."""
        return f"Notificación automática generada para: {key}"

@method_decorator(csrf_exempt, name='dispatch')
class StrategicNotificationStatsView(View):
    """
    Vista para estadísticas de notificaciones.
    """
    
    def get(self, request, *args, **kwargs):
        """
        Obtiene estadísticas de notificaciones.
        """
        try:
            # Crear instancia del servicio
            notification_service = StrategicNotificationService()
            
            # Calcular estadísticas
            total_notifications = len(notification_service.last_notifications)
            
            # Contar notificaciones urgentes
            urgent_notifications = sum(
                1 for key in notification_service.last_notifications.keys()
                if 'urgent' in key or 'error' in key
            )
            
            # Calcular tasa de éxito (simulada)
            success_rate = 95.5  # Porcentaje simulado
            
            # Calcular tiempo de respuesta promedio (simulado)
            avg_response_time = 2.3  # Segundos simulados
            
            # Estadísticas por tipo
            type_stats = {}
            for key in notification_service.last_notifications.keys():
                notification_type = key.split('_')[0] if '_' in key else 'unknown'
                type_stats[notification_type] = type_stats.get(notification_type, 0) + 1
            
            # Estadísticas por prioridad
            priority_stats = {
                'urgent': 0,
                'high': 0,
                'medium': 0,
                'low': 0
            }
            
            for key in notification_service.last_notifications.keys():
                if 'urgent' in key:
                    priority_stats['urgent'] += 1
                elif 'high' in key:
                    priority_stats['high'] += 1
                elif 'medium' in key:
                    priority_stats['medium'] += 1
                else:
                    priority_stats['low'] += 1
            
            stats = {
                'total_notifications': total_notifications,
                'urgent_notifications': urgent_notifications,
                'success_rate': success_rate,
                'avg_response_time': avg_response_time,
                'type_stats': type_stats,
                'priority_stats': priority_stats,
                'last_updated': timezone.now().isoformat()
            }
            
            return JsonResponse({
                'success': True,
                'stats': stats
            })
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class StrategicNotificationManagementView(View):
    """
    Vista para gestión de notificaciones.
    """
    
    def post(self, request, *args, **kwargs):
        """
        Gestiona operaciones de notificaciones.
        """
        try:
            data = json.loads(request.body)
            action = data.get('action')
            
            if action == 'clear':
                # Limpiar notificaciones antiguas
                task = cleanup_old_notifications.delay(days=30)
                
                return JsonResponse({
                    'success': True,
                    'message': 'Limpieza iniciada',
                    'task_id': task.id
                })
            
            elif action == 'report':
                # Generar reporte
                business_unit = data.get('business_unit')
                days = data.get('days', 7)
                
                task = generate_notification_report.delay(
                    business_unit=business_unit,
                    days=days
                )
                
                return JsonResponse({
                    'success': True,
                    'message': 'Reporte generado',
                    'task_id': task.id
                })
            
            elif action == 'test':
                # Enviar notificación de prueba
                notification_service = StrategicNotificationService()
                
                # Importar asyncio para manejar async
                import asyncio
                
                # Ejecutar envío de prueba
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    loop.run_until_complete(
                        notification_service.send_manual_notification(
                            title='Notificación de Prueba',
                            message='Esta es una notificación de prueba del sistema estratégico.',
                            recipients=['super_admins'],
                            priority='medium'
                        )
                    )
                finally:
                    loop.close()
                
                return JsonResponse({
                    'success': True,
                    'message': 'Notificación de prueba enviada'
                })
            
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Acción no válida'
                }, status=400)
                
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'JSON inválido'
            }, status=400)
        except Exception as e:
            logger.error(f"Error en gestión de notificaciones: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500)

@login_required
@user_passes_test(is_super_admin)
def notification_config_view(request):
    """
    Vista para configurar notificaciones.
    """
    if request.method == 'POST':
        try:
            # Obtener configuración del formulario
            auto_monitoring = request.POST.get('auto_monitoring') == 'on'
            email_notifications = request.POST.get('email_notifications') == 'on'
            telegram_notifications = request.POST.get('telegram_notifications') == 'on'
            whatsapp_notifications = request.POST.get('whatsapp_notifications') == 'on'
            
            # Guardar configuración (implementar según necesidades)
            # Por ahora solo log
            logger.info(f"Configuración actualizada: auto={auto_monitoring}, email={email_notifications}")
            
            return JsonResponse({
                'success': True,
                'message': 'Configuración actualizada'
            })
            
        except Exception as e:
            logger.error(f"Error actualizando configuración: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500)
    
    # GET: mostrar formulario de configuración
    return render(request, 'admin/notification_config.html')

@login_required
@user_passes_test(is_super_admin)
def notification_logs_view(request):
    """
    Vista para ver logs de notificaciones.
    """
    try:
        # Obtener parámetros
        days = int(request.GET.get('days', 7))
        notification_type = request.GET.get('type')
        business_unit = request.GET.get('business_unit')
        
        # Crear instancia del servicio
        notification_service = StrategicNotificationService()
        
        # Filtrar notificaciones por fecha
        cutoff_date = timezone.now() - timedelta(days=days)
        recent_notifications = {
            key: timestamp for key, timestamp in notification_service.last_notifications.items()
            if timestamp >= cutoff_date
        }
        
        # Filtrar por tipo si se especifica
        if notification_type:
            recent_notifications = {
                key: timestamp for key, timestamp in recent_notifications.items()
                if key.startswith(notification_type)
            }
        
        # Convertir a lista ordenada
        logs = []
        for key, timestamp in recent_notifications.items():
            logs.append({
                'key': key,
                'timestamp': timestamp.isoformat(),
                'type': key.split('_')[0] if '_' in key else 'unknown',
                'business_unit': business_unit or 'all'
            })
        
        # Ordenar por timestamp
        logs.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return JsonResponse({
            'success': True,
            'logs': logs,
            'total': len(logs)
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo logs: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500) 