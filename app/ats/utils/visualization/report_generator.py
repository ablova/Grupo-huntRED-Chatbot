from django.db.models import Count, Avg, Max, Min
from app.ats.utils.models.models import Conversation, Message, Notification, WorkflowState, Metric
from datetime import datetime, timedelta
import logging

logger = logging.getLogger('app.ats.utils.visualization')

class ReportGenerator:
    """Generador de reportes para el módulo de comunicaciones."""
    
    def __init__(self, date_range: tuple = None):
        self.start_date, self.end_date = date_range or self._get_default_date_range()
        
    def _get_default_date_range(self) -> tuple:
        """Obtiene el rango de fechas por defecto (últimos 30 días)."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        return start_date, end_date
    
    def generate_conversation_metrics(self) -> dict:
        """Genera métricas de conversaciones."""
        conversations = Conversation.objects.filter(
            timestamp__range=(self.start_date, self.end_date)
        )
        
        return {
            'total': conversations.count(),
            'by_channel': conversations.values('channel').annotate(count=Count('id')),
            'by_state': conversations.values('state').annotate(count=Count('id')),
            'avg_messages': conversations.annotate(
                message_count=Count('message')
            ).aggregate(avg=Avg('message_count'))['avg']
        }
    
    def generate_message_metrics(self) -> dict:
        """Genera métricas de mensajes."""
        messages = Message.objects.filter(
            timestamp__range=(self.start_date, self.end_date)
        )
        
        return {
            'total': messages.count(),
            'by_direction': messages.values('direction').annotate(count=Count('id')),
            'by_status': messages.values('status').annotate(count=Count('id')),
            'response_time': messages.filter(
                direction='out'
            ).annotate(
                response_time=Max('timestamp') - Min('timestamp')
            ).aggregate(avg=Avg('response_time'))['avg']
        }
    
    def generate_notification_metrics(self) -> dict:
        """Genera métricas de notificaciones."""
        notifications = Notification.objects.filter(
            timestamp__range=(self.start_date, self.end_date)
        )
        
        return {
            'total': notifications.count(),
            'by_type': notifications.values('type').annotate(count=Count('id')),
            'by_channel': notifications.values('channel').annotate(count=Count('id')),
            'success_rate': notifications.filter(
                status='sent'
            ).count() / notifications.count() if notifications.count() > 0 else 0
        }
    
    def generate_workflow_metrics(self) -> dict:
        """Genera métricas del flujo de trabajo."""
        workflow_states = WorkflowState.objects.filter(
            timestamp__range=(self.start_date, self.end_date)
        )
        
        return {
            'total_transitions': workflow_states.count(),
            'by_state': workflow_states.values('state').annotate(count=Count('id')),
            'avg_time_per_state': workflow_states.values('state').annotate(
                avg_time=Avg('timestamp')
            )
        }
    
    def generate_overall_metrics(self) -> dict:
        """Genera métricas generales del sistema."""
        metrics = Metric.objects.filter(
            timestamp__range=(self.start_date, self.end_date)
        )
        
        return {
            'total_metrics': metrics.count(),
            'by_name': metrics.values('name').annotate(count=Count('id')),
            'trend': metrics.order_by('timestamp').values('name', 'value', 'timestamp')
        }
    
    def generate_comprehensive_report(self) -> dict:
        """Genera un reporte completo de todas las métricas."""
        try:
            return {
                'date_range': {
                    'start': self.start_date.isoformat(),
                    'end': self.end_date.isoformat()
                },
                'conversations': self.generate_conversation_metrics(),
                'messages': self.generate_message_metrics(),
                'notifications': self.generate_notification_metrics(),
                'workflow': self.generate_workflow_metrics(),
                'overall': self.generate_overall_metrics()
            }
        except Exception as e:
            logger.error(f"Error generating comprehensive report: {str(e)}")
            return {'error': str(e)}
