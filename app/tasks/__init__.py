# app/tasks/__init__.py
"""
Paquete de tareas de la aplicación.
"""
from app.tasks.onboarding import send_satisfaction_survey_task
from app.tasks.notifications.bulk import send_bulk_notifications_task

__all__ = [
    'send_satisfaction_survey_task',
    'send_bulk_notifications_task',
] 