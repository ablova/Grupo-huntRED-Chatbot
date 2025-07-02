"""
🎯 Vistas para Optimización de Comunicación

Este módulo proporciona endpoints para:
- Optimizar notificaciones en tiempo real
- Analizar sentimientos de comunicación
- Obtener perfiles de comunicación de usuarios
- Probar diferentes estrategias de comunicación
"""

import logging
import json
from typing import Dict, Any, List
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.utils import timezone

from app.middleware.communication_optimization import optimize_notification_for_user
from app.ml.aura.predictive.sentiment_analyzer import SentimentAnalyzer
from app.models import Person, Notification, BusinessUnit
from app.decorators import check_role_access

logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["POST"])
@login_required
@check_role_access(["Super Admin", "Consultant BU Complete", "Consultant BU Division"])
def optimize_notification_view(request):
    """
    Optimiza una notificación basándose en el perfil del usuario.
    
    POST /api/communication/optimize/
    {
        "user_id": 123,
        "notification_type": "reminder",
        "content": "Recordatorio de tu entrevista mañana",
        "business_unit": "huntRED"
    }
    """
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        notification_type = data.get('notification_type', 'general')
        content = data.get('content', '')
        business_unit = data.get('business_unit')
        
        if not user_id or not content:
            return JsonResponse({
                'error': 'user_id y content son requeridos'
            }, status=400)
        
        # Optimizar la notificación
        optimization_result = optimize_notification_for_user(
            user_id=user_id,
            notification_type=notification_type,
            content=content,
            business_unit=business_unit
        )
        
        return JsonResponse({
            'success': True,
            'optimization_result': optimization_result,
            'timestamp': timezone.now().isoformat()
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'JSON inválido en el body'
        }, status=400)
    except Exception as e:
        logger.error(f"Error optimizing notification: {e}")
        return JsonResponse({
            'error': f'Error interno: {str(e)}'
        }, status=500)

@require_http_methods(["GET"])
@login_required
@check_role_access(["Super Admin", "Consultant BU Complete", "Consultant BU Division"])
def get_user_communication_profile(request, user_id):
    """
    Obtiene el perfil de comunicación de un usuario.
    
    GET /api/communication/profile/{user_id}/
    """
    try:
        from app.middleware.communication_optimization import CommunicationOptimizationMiddleware
        
        # Crear instancia temporal del middleware para acceder a sus métodos
        middleware = CommunicationOptimizationMiddleware(lambda r: None)
        
        # Obtener perfil
        profile = middleware._get_user_communication_profile(user_id)
        
        return JsonResponse({
            'success': True,
            'user_id': user_id,
            'profile': profile,
            'timestamp': timezone.now().isoformat()
        })
        
    except Person.DoesNotExist:
        return JsonResponse({
            'error': f'Usuario {user_id} no encontrado'
        }, status=404)
    except Exception as e:
        logger.error(f"Error getting communication profile: {e}")
        return JsonResponse({
            'error': f'Error interno: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
@login_required
@check_role_access(["Super Admin", "Consultant BU Complete", "Consultant BU Division"])
def analyze_sentiment_view(request):
    """
    Analiza el sentimiento de un texto.
    
    POST /api/communication/analyze-sentiment/
    {
        "text": "Me siento muy frustrado con el proceso",
        "user_id": 123
    }
    """
    try:
        data = json.loads(request.body)
        text = data.get('text', '')
        user_id = data.get('user_id')
        
        if not text:
            return JsonResponse({
                'error': 'text es requerido'
            }, status=400)
        
        # Analizar sentimiento
        sentiment_analyzer = SentimentAnalyzer()
        sentiment_result = sentiment_analyzer.analyze_text_sentiment(text, user_id)
        
        return JsonResponse({
            'success': True,
            'text': text,
            'sentiment_analysis': {
                'sentiment_score': sentiment_result.sentiment_score,
                'sentiment_label': sentiment_result.sentiment_label,
                'confidence': sentiment_result.confidence,
                'categories': sentiment_result.categories,
                'keywords': sentiment_result.keywords
            },
            'timestamp': timezone.now().isoformat()
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'JSON inválido en el body'
        }, status=400)
    except Exception as e:
        logger.error(f"Error analyzing sentiment: {e}")
        return JsonResponse({
            'error': f'Error interno: {str(e)}'
        }, status=500)

@require_http_methods(["GET"])
@login_required
@check_role_access(["Super Admin", "Consultant BU Complete", "Consultant BU Division"])
def get_communication_analytics(request):
    """
    Obtiene analytics de comunicación para una unidad de negocio.
    
    GET /api/communication/analytics/?business_unit=huntRED&days=7
    """
    try:
        business_unit = request.GET.get('business_unit')
        days = int(request.GET.get('days', 7))
        
        if not business_unit:
            return JsonResponse({
                'error': 'business_unit es requerido'
            }, status=400)
        
        # Obtener notificaciones recientes
        cutoff_date = timezone.now() - timezone.timedelta(days=days)
        notifications = Notification.objects.filter(
            created_at__gte=cutoff_date
        )
        
        # Filtrar por unidad de negocio si se especifica
        if business_unit != 'all':
            # Aquí podrías filtrar por unidad de negocio si tienes esa relación
            pass
        
        # Calcular métricas
        total_notifications = notifications.count()
        sent_notifications = notifications.filter(status='SENT').count()
        failed_notifications = notifications.filter(status='FAILED').count()
        
        # Análisis por canal
        channel_stats = {}
        for notification in notifications:
            channel = notification.channel
            if channel not in channel_stats:
                channel_stats[channel] = {'total': 0, 'sent': 0, 'failed': 0}
            
            channel_stats[channel]['total'] += 1
            if notification.status == 'SENT':
                channel_stats[channel]['sent'] += 1
            elif notification.status == 'FAILED':
                channel_stats[channel]['failed'] += 1
        
        # Calcular tasas de éxito por canal
        for channel, stats in channel_stats.items():
            if stats['total'] > 0:
                stats['success_rate'] = round(stats['sent'] / stats['total'], 3)
            else:
                stats['success_rate'] = 0.0
        
        analytics = {
            'period': {
                'days': days,
                'start_date': cutoff_date.isoformat(),
                'end_date': timezone.now().isoformat()
            },
            'overall_stats': {
                'total_notifications': total_notifications,
                'sent_notifications': sent_notifications,
                'failed_notifications': failed_notifications,
                'success_rate': round(sent_notifications / total_notifications, 3) if total_notifications > 0 else 0.0
            },
            'channel_stats': channel_stats,
            'business_unit': business_unit
        }
        
        return JsonResponse({
            'success': True,
            'analytics': analytics,
            'timestamp': timezone.now().isoformat()
        })
        
    except ValueError:
        return JsonResponse({
            'error': 'days debe ser un número válido'
        }, status=400)
    except Exception as e:
        logger.error(f"Error getting communication analytics: {e}")
        return JsonResponse({
            'error': f'Error interno: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
@login_required
@check_role_access(["Super Admin", "Consultant BU Complete", "Consultant BU Division"])
def test_communication_strategies(request):
    """
    Prueba diferentes estrategias de comunicación.
    
    POST /api/communication/test-strategies/
    {
        "user_id": 123,
        "content": "Tu entrevista está programada para mañana",
        "strategies": ["empathetic", "professional", "casual"]
    }
    """
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        content = data.get('content', '')
        strategies = data.get('strategies', ['empathetic', 'professional', 'casual'])
        
        if not user_id or not content:
            return JsonResponse({
                'error': 'user_id y content son requeridos'
            }, status=400)
        
        # Aplicar diferentes estrategias
        strategy_results = {}
        
        for strategy in strategies:
            optimized_content = content
            
            if strategy == 'empathetic':
                optimized_content = f"Entiendo que esto es importante para ti. {content}"
            elif strategy == 'professional':
                optimized_content = f"Le informamos que {content.lower()}"
            elif strategy == 'casual':
                optimized_content = f"¡Hola! {content}"
            elif strategy == 'urgent':
                optimized_content = f"URGENTE: {content}"
            elif strategy == 'celebratory':
                optimized_content = f"¡Excelente! {content}"
            
            # Analizar sentimiento de la versión optimizada
            sentiment_analyzer = SentimentAnalyzer()
            sentiment_result = sentiment_analyzer.analyze_text_sentiment(optimized_content, user_id)
            
            strategy_results[strategy] = {
                'original_content': content,
                'optimized_content': optimized_content,
                'sentiment_analysis': {
                    'sentiment_score': sentiment_result.sentiment_score,
                    'sentiment_label': sentiment_result.sentiment_label,
                    'confidence': sentiment_result.confidence
                },
                'content_length': len(optimized_content),
                'word_count': len(optimized_content.split())
            }
        
        return JsonResponse({
            'success': True,
            'user_id': user_id,
            'strategies': strategy_results,
            'recommendation': _get_best_strategy(strategy_results),
            'timestamp': timezone.now().isoformat()
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'JSON inválido en el body'
        }, status=400)
    except Exception as e:
        logger.error(f"Error testing communication strategies: {e}")
        return JsonResponse({
            'error': f'Error interno: {str(e)}'
        }, status=500)

def _get_best_strategy(strategy_results: Dict[str, Any]) -> str:
    """Determina la mejor estrategia basándose en los resultados."""
    best_strategy = None
    best_score = -1
    
    for strategy, result in strategy_results.items():
        # Calcular score basándose en sentimiento y longitud
        sentiment_score = result['sentiment_analysis']['sentiment_score']
        confidence = result['sentiment_analysis']['confidence']
        
        # Score combinado
        score = (sentiment_score + 1) * confidence  # Normalizar sentimiento a 0-2
        
        if score > best_score:
            best_score = score
            best_strategy = strategy
    
    return best_strategy or 'professional'

@require_http_methods(["GET"])
@login_required
@check_role_access(["Super Admin", "Consultant BU Complete", "Consultant BU Division"])
def get_communication_recommendations(request, user_id):
    """
    Obtiene recomendaciones de comunicación para un usuario.
    
    GET /api/communication/recommendations/{user_id}/
    """
    try:
        from app.middleware.communication_optimization import CommunicationOptimizationMiddleware
        
        # Crear instancia temporal del middleware
        middleware = CommunicationOptimizationMiddleware(lambda r: None)
        
        # Obtener perfil del usuario
        user_profile = middleware._get_user_communication_profile(user_id)
        
        # Generar recomendaciones
        recommendations = []
        
        # Recomendaciones basadas en tasa de respuesta
        if user_profile['response_rate'] < 0.3:
            recommendations.append({
                'type': 'engagement',
                'priority': 'high',
                'title': 'Baja tasa de respuesta',
                'description': 'El usuario tiene una baja tasa de respuesta. Considera un enfoque más personalizado.',
                'suggestions': [
                    'Usa canales más personales como WhatsApp',
                    'Envía mensajes más breves y directos',
                    'Considera el timing de las notificaciones'
                ]
            })
        
        # Recomendaciones basadas en canales preferidos
        if 'whatsapp' in user_profile['preferred_channels'][:2]:
            recommendations.append({
                'type': 'channel',
                'priority': 'medium',
                'title': 'Preferencia por WhatsApp',
                'description': 'El usuario prefiere WhatsApp. Prioriza este canal para comunicaciones importantes.',
                'suggestions': [
                    'Usa WhatsApp para notificaciones urgentes',
                    'Mantén un tono más personal en WhatsApp',
                    'Responde rápidamente a mensajes de WhatsApp'
                ]
            })
        
        # Recomendaciones basadas en patrones de actividad
        activity_patterns = user_profile['activity_patterns']
        if activity_patterns['peak_hours']:
            recommendations.append({
                'type': 'timing',
                'priority': 'medium',
                'title': 'Horarios de actividad',
                'description': f'El usuario está más activo en las horas: {activity_patterns["peak_hours"]}',
                'suggestions': [
                    f'Envía notificaciones importantes entre las {min(activity_patterns["peak_hours"])}:00 y {max(activity_patterns["peak_hours"])}:00',
                    'Evita enviar notificaciones en horas tranquilas',
                    'Considera la zona horaria del usuario'
                ]
            })
        
        # Recomendaciones basadas en estilo de comunicación
        if user_profile['communication_style'] == 'professional':
            recommendations.append({
                'type': 'style',
                'priority': 'low',
                'title': 'Estilo profesional',
                'description': 'El usuario prefiere un estilo de comunicación profesional.',
                'suggestions': [
                    'Usa un tono formal y respetuoso',
                    'Incluye detalles técnicos cuando sea apropiado',
                    'Mantén un lenguaje corporativo'
                ]
            })
        
        return JsonResponse({
            'success': True,
            'user_id': user_id,
            'user_profile': user_profile,
            'recommendations': recommendations,
            'timestamp': timezone.now().isoformat()
        })
        
    except Person.DoesNotExist:
        return JsonResponse({
            'error': f'Usuario {user_id} no encontrado'
        }, status=404)
    except Exception as e:
        logger.error(f"Error getting communication recommendations: {e}")
        return JsonResponse({
            'error': f'Error interno: {str(e)}'
        }, status=500)

@method_decorator(login_required, name='dispatch')
@method_decorator(check_role_access(["Super Admin", "Consultant BU Complete", "Consultant BU Division"]), name='dispatch')
class CommunicationOptimizationDashboardView(View):
    """
    Dashboard para visualizar y gestionar la optimización de comunicaciones.
    """
    
    def get(self, request):
        """
        GET /api/communication/dashboard/
        """
        try:
            # Obtener estadísticas generales
            total_users = Person.objects.count()
            total_notifications = Notification.objects.count()
            recent_notifications = Notification.objects.filter(
                created_at__gte=timezone.now() - timezone.timedelta(days=7)
            ).count()
            
            # Obtener unidades de negocio
            business_units = BusinessUnit.objects.filter(active=True)
            bu_stats = []
            
            for bu in business_units:
                # Aquí podrías agregar estadísticas específicas por BU
                bu_stats.append({
                    'name': bu.name,
                    'code': bu.code,
                    'active': bu.active,
                    'notification_channels': {
                        'whatsapp': bu.whatsapp_enabled,
                        'telegram': bu.telegram_enabled,
                        'messenger': bu.messenger_enabled
                    }
                })
            
            dashboard_data = {
                'overview': {
                    'total_users': total_users,
                    'total_notifications': total_notifications,
                    'recent_notifications': recent_notifications,
                    'success_rate': self._calculate_overall_success_rate()
                },
                'business_units': bu_stats,
                'optimization_status': {
                    'enabled': True,
                    'last_optimization': timezone.now().isoformat(),
                    'active_strategies': ['sentiment_based', 'engagement_based', 'timing_based']
                }
            }
            
            return JsonResponse({
                'success': True,
                'dashboard': dashboard_data,
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error getting communication dashboard: {e}")
            return JsonResponse({
                'error': f'Error interno: {str(e)}'
            }, status=500)
    
    def _calculate_overall_success_rate(self) -> float:
        """Calcula la tasa de éxito general de las notificaciones."""
        try:
            total = Notification.objects.count()
            if total == 0:
                return 0.0
            
            sent = Notification.objects.filter(status='SENT').count()
            return round(sent / total, 3)
        except:
            return 0.0 