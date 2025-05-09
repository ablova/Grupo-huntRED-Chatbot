from datetime import datetime, timedelta
from app.models import Person, EmailLog

class BehaviorAnalyzer:
    def __init__(self):
        self.open_threshold = 0.7
        self.response_threshold = 24  # horas
        
    def calculate_response_time(self, logs):
        """Calcula el tiempo promedio de respuesta en horas."""
        response_times = []
        for log in logs:
            if log.response_time:
                response_times.append(log.response_time.total_seconds() / 3600)
        return sum(response_times) / len(response_times) if response_times else self.response_threshold
        
    def calculate_open_rate(self, logs):
        """Calcula la tasa de apertura de correos."""
        total = len(logs)
        if not total:
            return 0
        opened = sum(1 for log in logs if log.opened)
        return opened / total
        
    def get_recommendation(self, response_time, open_rate):
        """Genera recomendaciones basadas en el comportamiento."""
        if response_time < self.response_threshold and open_rate > self.open_threshold:
            return 'high_engagement'
        elif response_time > self.response_threshold * 2:
            return 'slow_response'
        elif open_rate < self.open_threshold / 2:
            return 'low_open_rate'
        return 'normal'
        
    def analyze_email_behavior(self, person):
        """Analiza el comportamiento de correos de una persona."""
        logs = EmailLog.objects.filter(
            recipient=person,
            created_at__gte=datetime.now() - timedelta(days=7)
        ).order_by('-created_at')
        
        response_time = self.calculate_response_time(logs)
        open_rate = self.calculate_open_rate(logs)
        recommendation = self.get_recommendation(response_time, open_rate)
        
        return {
            'response_time': response_time,
            'open_rate': open_rate,
            'recommendation': recommendation,
            'last_email': logs.first().created_at if logs else None
        }
