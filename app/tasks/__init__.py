# app/tasks/__init__.py
"""
Paquete de tareas de la aplicación.
"""
from app.tasks.onboarding import send_satisfaction_survey_task
from app.tasks.notifications.bulk import send_bulk_notifications_task

# Tareas temporales para resolver importaciones
def send_interview_notification_task(*args, **kwargs):
    """Tarea temporal para notificaciones de entrevista."""
    pass

def schedule_interview_tracking_task(*args, **kwargs):
    """Tarea temporal para seguimiento de entrevistas."""
    pass

def train_ml_task(*args, **kwargs):
    """Tarea temporal para entrenamiento de ML."""
    pass

__all__ = [
    'send_satisfaction_survey_task',
    'send_bulk_notifications_task',
    'send_interview_notification_task',
    'schedule_interview_tracking_task',
    'train_ml_task',
] 