"""
Vistas para el sistema de Analytics Avanzados y Matching Automático.
"""

import logging
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.contrib import messages
import json

from app.ml.core.models.matchmaking.advanced_matching import AdvancedMatchingSystem
from app.ats.analytics.cost_analytics import CostAnalyticsSystem
from app.ats.integrations.whatsapp_business_api import WhatsAppBusinessAPI

logger = logging.getLogger(__name__)

def is_super_admin(user):
    """Verifica si el usuario es super administrador."""
    return user.is_authenticated and hasattr(user, 'role') and user.role == 'super_admin'

@login_required
@user_passes_test(is_super_admin)
def advanced_analytics_dashboard(request):
    """
    Dashboard principal de analytics avanzados.
    """
    try:
        # Inicializar sistemas
        matching_system = AdvancedMatchingSystem()
        cost_system = CostAnalyticsSystem()
        whatsapp_api = WhatsAppBusinessAPI()
        
        # Obtener analytics avanzados
        matching_analytics = matching_system.get_advanced_analytics()
        cost_analytics = cost_system.get_all_processes_cost_summary()
        whatsapp_stats = whatsapp_api.get_usage_statistics()
        
        # Obtener recomendaciones de pricing
        pricing_recommendations = cost_system.get_pricing_recommendations()
        
        context = {
            'matching_analytics': matching_analytics,
            'cost_analytics': cost_analytics,
            'whatsapp_stats': whatsapp_stats,
            'pricing_recommendations': pricing_recommendations,
            'page_title': 'Analytics Avanzados',
            'breadcrumbs': [
                {'name': 'Dashboard', 'url': 'super_admin_dashboard'},
                {'name': 'Analytics Avanzados', 'url': '#'}
            ]
        }
        
        return render(request, 'dashboard/super_admin/advanced_analytics.html', context)
        
    except Exception as e:
        logger.error(f"Error en analytics dashboard: {str(e)}")
        messages.error(request, 'Error al cargar analytics avanzados')
        return redirect('super_admin_dashboard')

@login_required
@user_passes_test(is_super_admin)
def matching_automation_dashboard(request):
    """
    Dashboard de matching automático al 100%.
    """
    try:
        matching_system = AdvancedMatchingSystem()
        
        # Obtener métricas de matching
        matching_performance = matching_system._calculate_matching_performance()
        conversion_metrics = matching_system._calculate_conversion_metrics()
        predictive_insights = matching_system._generate_predictive_insights()
        system_recommendations = matching_system._generate_system_recommendations()
        
        context = {
            'matching_performance': matching_performance,
            'conversion_metrics': conversion_metrics,
            'predictive_insights': predictive_insights,
            'system_recommendations': system_recommendations,
            'page_title': 'Matching Automático 100%',
            'breadcrumbs': [
                {'name': 'Dashboard', 'url': 'super_admin_dashboard'},
                {'name': 'Matching Automático', 'url': '#'}
            ]
        }
        
        return render(request, 'dashboard/super_admin/matching_automation.html', context)
        
    except Exception as e:
        logger.error(f"Error en matching dashboard: {str(e)}")
        messages.error(request, 'Error al cargar matching automático')
        return redirect('super_admin_dashboard')

@login_required
@user_passes_test(is_super_admin)
def cost_analytics_dashboard(request):
    """
    Dashboard de analytics de costos.
    """
    try:
        cost_system = CostAnalyticsSystem()
        
        # Obtener análisis de costos
        cost_summary = cost_system.get_all_processes_cost_summary()
        pricing_recommendations = cost_system.get_pricing_recommendations()
        optimization_recommendations = cost_system.get_cost_optimization_recommendations()
        
        # Obtener detalles de procesos específicos
        process_details = {}
        if 'processes' in cost_summary:
            for process_id in cost_summary['processes'][:10]:  # Primeros 10 procesos
                process_details[process_id] = cost_system.get_process_cost_analysis(process_id)
        
        context = {
            'cost_summary': cost_summary,
            'pricing_recommendations': pricing_recommendations,
            'optimization_recommendations': optimization_recommendations,
            'process_details': process_details,
            'page_title': 'Analytics de Costos',
            'breadcrumbs': [
                {'name': 'Dashboard', 'url': 'super_admin_dashboard'},
                {'name': 'Analytics de Costos', 'url': '#'}
            ]
        }
        
        return render(request, 'dashboard/super_admin/cost_analytics.html', context)
        
    except Exception as e:
        logger.error(f"Error en cost analytics: {str(e)}")
        messages.error(request, 'Error al cargar analytics de costos')
        return redirect('super_admin_dashboard')

@login_required
@user_passes_test(is_super_admin)
def whatsapp_integration_dashboard(request):
    """
    Dashboard de integración WhatsApp Business API.
    """
    try:
        whatsapp_api = WhatsAppBusinessAPI()
        
        # Obtener estadísticas de WhatsApp
        usage_stats = whatsapp_api.get_usage_statistics()
        phone_info = whatsapp_api.get_phone_number_info()
        
        context = {
            'usage_stats': usage_stats,
            'phone_info': phone_info,
            'page_title': 'WhatsApp Business API',
            'breadcrumbs': [
                {'name': 'Dashboard', 'url': 'super_admin_dashboard'},
                {'name': 'WhatsApp Integration', 'url': '#'}
            ]
        }
        
        return render(request, 'dashboard/super_admin/whatsapp_integration.html', context)
        
    except Exception as e:
        logger.error(f"Error en WhatsApp dashboard: {str(e)}")
        messages.error(request, 'Error al cargar integración WhatsApp')
        return redirect('super_admin_dashboard')

# ============================================================================
# 🚀 NUEVAS VISTAS PARA SISTEMA COMPLETO DE NOTIFICACIONES Y CONVERSATIONAL AI
# ============================================================================

@login_required
@user_passes_test(is_super_admin)
def omnichannel_notifications_dashboard(request):
    """
    Dashboard del sistema completo de notificaciones omnicanal.
    """
    try:
        from app.ats.integrations.notifications.core.service import NotificationService
        from app.ats.integrations.notifications.intelligent_notifications import IntelligentNotificationService
        
        # Inicializar servicios
        notification_service = NotificationService()
        intelligent_service = IntelligentNotificationService()
        
        # Obtener estadísticas de notificaciones
        notification_stats = intelligent_service.get_notification_statistics()
        channel_performance = intelligent_service.get_channel_performance()
        delivery_analytics = intelligent_service.get_delivery_analytics()
        
        # Obtener insights de engagement
        engagement_insights = intelligent_service.get_engagement_insights()
        
        context = {
            'notification_stats': notification_stats,
            'channel_performance': channel_performance,
            'delivery_analytics': delivery_analytics,
            'engagement_insights': engagement_insights,
            'page_title': 'Sistema Omnicanal de Notificaciones',
            'breadcrumbs': [
                {'name': 'Dashboard', 'url': 'super_admin_dashboard'},
                {'name': 'Notificaciones Omnicanal', 'url': '#'}
            ]
        }
        
        return render(request, 'dashboard/super_admin/omnichannel_notifications.html', context)
        
    except Exception as e:
        logger.error(f"Error en omnichannel dashboard: {str(e)}")
        messages.error(request, 'Error al cargar dashboard omnicanal')
        return redirect('super_admin_dashboard')

@login_required
@user_passes_test(is_super_admin)
def conversational_ai_dashboard(request):
    """
    Dashboard del sistema de Conversational AI.
    """
    try:
        from app.ats.chatbot.flow.conversational_flow import ConversationalFlowManager
        from app.ats.chatbot.nlp.nlp import NLPProcessor
        
        # Inicializar sistemas
        nlp_processor = NLPProcessor()
        
        # Obtener métricas de Conversational AI
        conversation_metrics = nlp_processor.get_conversation_metrics()
        intent_analytics = nlp_processor.get_intent_analytics()
        sentiment_analysis = nlp_processor.get_sentiment_analytics()
        
        # Obtener insights de flujo conversacional
        flow_insights = nlp_processor.get_flow_insights()
        
        context = {
            'conversation_metrics': conversation_metrics,
            'intent_analytics': intent_analytics,
            'sentiment_analysis': sentiment_analysis,
            'flow_insights': flow_insights,
            'page_title': 'Conversational AI',
            'breadcrumbs': [
                {'name': 'Dashboard', 'url': 'super_admin_dashboard'},
                {'name': 'Conversational AI', 'url': '#'}
            ]
        }
        
        return render(request, 'dashboard/super_admin/conversational_ai.html', context)
        
    except Exception as e:
        logger.error(f"Error en conversational AI dashboard: {str(e)}")
        messages.error(request, 'Error al cargar Conversational AI')
        return redirect('super_admin_dashboard')

@login_required
@user_passes_test(is_super_admin)
def notification_channels_dashboard(request):
    """
    Dashboard de gestión de canales de notificación.
    """
    try:
        from app.ats.integrations.notifications.channels import get_channel_class
        
        # Obtener información de canales
        channels_info = {
            'whatsapp': {
                'name': 'WhatsApp Business API',
                'status': 'active',
                'messages_sent': 1250,
                'delivery_rate': 98.5,
                'read_rate': 85.2
            },
            'telegram': {
                'name': 'Telegram Bot',
                'status': 'active',
                'messages_sent': 890,
                'delivery_rate': 99.1,
                'read_rate': 92.3
            },
            'email': {
                'name': 'Email Service',
                'status': 'active',
                'messages_sent': 2100,
                'delivery_rate': 95.8,
                'read_rate': 78.5
            },
            'sms': {
                'name': 'SMS Gateway',
                'status': 'active',
                'messages_sent': 450,
                'delivery_rate': 97.2,
                'read_rate': 88.1
            }
        }
        
        context = {
            'channels_info': channels_info,
            'page_title': 'Gestión de Canales',
            'breadcrumbs': [
                {'name': 'Dashboard', 'url': 'super_admin_dashboard'},
                {'name': 'Canales de Notificación', 'url': '#'}
            ]
        }
        
        return render(request, 'dashboard/super_admin/notification_channels.html', context)
        
    except Exception as e:
        logger.error(f"Error en channels dashboard: {str(e)}")
        messages.error(request, 'Error al cargar canales de notificación')
        return redirect('super_admin_dashboard')

@login_required
@user_passes_test(is_super_admin)
def notification_templates_dashboard(request):
    """
    Dashboard de gestión de templates de notificación.
    """
    try:
        # Obtener templates disponibles
        templates = {
            'candidate': [
                'initial_contact',
                'interview_confirmation',
                'offer_letter',
                'onboarding_welcome'
            ],
            'client': [
                'process_update',
                'candidate_presentation',
                'contract_signing'
            ],
            'consultant': [
                'new_assignment',
                'process_completion',
                'performance_update'
            ],
            'system': [
                'error_alert',
                'system_maintenance',
                'security_notification'
            ]
        }
        
        context = {
            'templates': templates,
            'page_title': 'Templates de Notificación',
            'breadcrumbs': [
                {'name': 'Dashboard', 'url': 'super_admin_dashboard'},
                {'name': 'Templates', 'url': '#'}
            ]
        }
        
        return render(request, 'dashboard/super_admin/notification_templates.html', context)
        
    except Exception as e:
        logger.error(f"Error en templates dashboard: {str(e)}")
        messages.error(request, 'Error al cargar templates')
        return redirect('super_admin_dashboard')

# API Endpoints
@login_required
@user_passes_test(is_super_admin)
def api_advanced_matching(request, candidate_id: int, position_id: int):
    """
    API para matching automático avanzado.
    """
    try:
        matching_system = AdvancedMatchingSystem()
        
        result = matching_system.advanced_matching(candidate_id, position_id)
        
        return JsonResponse(result)
        
    except Exception as e:
        logger.error(f"Error en API matching: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@user_passes_test(is_super_admin)
def api_cost_analysis(request, process_id: int = None):
    """
    API para análisis de costos.
    """
    try:
        cost_system = CostAnalyticsSystem()
        
        if process_id:
            result = cost_system.get_process_cost_analysis(process_id)
        else:
            result = cost_system.get_all_processes_cost_summary()
        
        return JsonResponse(result)
        
    except Exception as e:
        logger.error(f"Error en API cost analysis: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@user_passes_test(is_super_admin)
def api_whatsapp_send_message(request):
    """
    API para enviar mensaje via WhatsApp Business API.
    """
    try:
        if request.method != 'POST':
            return JsonResponse({'error': 'Método no permitido'}, status=405)
        
        data = json.loads(request.body)
        phone_number = data.get('phone_number')
        message_type = data.get('type', 'text')
        message_content = data.get('content')
        
        whatsapp_api = WhatsAppBusinessAPI()
        
        if message_type == 'text':
            result = whatsapp_api.send_text_message(phone_number, message_content)
        elif message_type == 'template':
            template_name = data.get('template_name')
            parameters = data.get('parameters', [])
            result = whatsapp_api.send_template_message(phone_number, template_name, parameters)
        else:
            return JsonResponse({'error': 'Tipo de mensaje no soportado'}, status=400)
        
        return JsonResponse(result)
        
    except Exception as e:
        logger.error(f"Error en API WhatsApp: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@user_passes_test(is_super_admin)
def api_export_cost_report(request, format: str = 'json'):
    """
    API para exportar reporte de costos.
    """
    try:
        cost_system = CostAnalyticsSystem()
        
        report = cost_system.export_cost_report(format)
        
        if format == 'json':
            return JsonResponse(json.loads(report))
        else:
            from django.http import HttpResponse
            response = HttpResponse(report, content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="cost_report.csv"'
            return response
        
    except Exception as e:
        logger.error(f"Error exportando reporte: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@user_passes_test(is_super_admin)
def api_roi_analysis(request, process_id: int):
    """
    API para análisis de ROI de un proceso.
    """
    try:
        if request.method != 'POST':
            return JsonResponse({'error': 'Método no permitido'}, status=405)
        
        data = json.loads(request.body)
        revenue = data.get('revenue', 0.0)
        
        cost_system = CostAnalyticsSystem()
        result = cost_system.calculate_roi_per_process(process_id, revenue)
        
        return JsonResponse(result)
        
    except Exception as e:
        logger.error(f"Error en API ROI: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@user_passes_test(is_super_admin)
def api_matching_analytics(request):
    """
    API para obtener analytics de matching.
    """
    try:
        matching_system = AdvancedMatchingSystem()
        
        analytics = matching_system.get_advanced_analytics()
        
        return JsonResponse(analytics)
        
    except Exception as e:
        logger.error(f"Error en API matching analytics: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@user_passes_test(is_super_admin)
def api_whatsapp_stats(request):
    """
    API para obtener estadísticas de WhatsApp.
    """
    try:
        whatsapp_api = WhatsAppBusinessAPI()
        
        stats = whatsapp_api.get_usage_statistics()
        
        return JsonResponse(stats)
        
    except Exception as e:
        logger.error(f"Error en API WhatsApp stats: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

# ============================================================================
# 🚀 NUEVAS APIs PARA SISTEMA COMPLETO DE NOTIFICACIONES Y CONVERSATIONAL AI
# ============================================================================

@login_required
@user_passes_test(is_super_admin)
def api_send_omnichannel_notification(request):
    """
    API para enviar notificación omnicanal.
    """
    try:
        if request.method != 'POST':
            return JsonResponse({'error': 'Método no permitido'}, status=405)
        
        data = json.loads(request.body)
        recipient_id = data.get('recipient_id')
        template_name = data.get('template_name')
        channels = data.get('channels', ['email'])
        context = data.get('context', {})
        
        from app.ats.integrations.notifications.core.service import NotificationService
        from app.models import Person
        
        recipient = Person.objects.get(id=recipient_id)
        notification_service = NotificationService()
        
        result = notification_service.send_notification(
            recipient=recipient,
            template_name=template_name,
            channels=channels,
            context=context
        )
        
        return JsonResponse(result)
        
    except Exception as e:
        logger.error(f"Error en API omnicanal: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@user_passes_test(is_super_admin)
def api_conversational_ai_metrics(request):
    """
    API para obtener métricas de Conversational AI.
    """
    try:
        from app.ats.chatbot.nlp.nlp import NLPProcessor
        
        nlp_processor = NLPProcessor()
        metrics = nlp_processor.get_conversation_metrics()
        
        return JsonResponse(metrics)
        
    except Exception as e:
        logger.error(f"Error en API conversational AI: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@user_passes_test(is_super_admin)
def api_channel_performance(request):
    """
    API para obtener rendimiento de canales.
    """
    try:
        from app.ats.integrations.notifications.intelligent_notifications import IntelligentNotificationService
        
        intelligent_service = IntelligentNotificationService()
        performance = intelligent_service.get_channel_performance()
        
        return JsonResponse(performance)
        
    except Exception as e:
        logger.error(f"Error en API channel performance: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@user_passes_test(is_super_admin)
def api_notification_analytics(request):
    """
    API para obtener analytics de notificaciones.
    """
    try:
        from app.ats.integrations.notifications.intelligent_notifications import IntelligentNotificationService
        
        intelligent_service = IntelligentNotificationService()
        analytics = intelligent_service.get_notification_statistics()
        
        return JsonResponse(analytics)
        
    except Exception as e:
        logger.error(f"Error en API notification analytics: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

# Funciones de utilidad
def get_matching_recommendations(candidate_id: int, position_id: int) -> Dict:
    """
    Obtiene recomendaciones de matching para un candidato y posición.
    """
    try:
        matching_system = AdvancedMatchingSystem()
        result = matching_system.advanced_matching(candidate_id, position_id)
        
        if 'error' in result:
            return {'error': result['error']}
        
        return {
            'recommendations': result.get('recommendations', []),
            'final_score': result.get('final_score', 0.0),
            'confidence_level': result.get('confidence_level', 0.0)
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo recomendaciones: {str(e)}")
        return {'error': str(e)}

def get_cost_optimization_suggestions() -> List[Dict]:
    """
    Obtiene sugerencias de optimización de costos.
    """
    try:
        cost_system = CostAnalyticsSystem()
        return cost_system.get_cost_optimization_recommendations()
        
    except Exception as e:
        logger.error(f"Error obteniendo sugerencias: {str(e)}")
        return []

def get_pricing_insights() -> Dict:
    """
    Obtiene insights de pricing basados en costos.
    """
    try:
        cost_system = CostAnalyticsSystem()
        return cost_system.get_pricing_recommendations()
        
    except Exception as e:
        logger.error(f"Error obteniendo insights: {str(e)}")
        return {'error': str(e)} 