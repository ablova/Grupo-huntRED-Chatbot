# app/ats/tasks/__init__.py
"""Módulo de tareas."""

# Servicios de Notificaciones
from app.ats.integrations.notifications.process.interview_notifications import (
    InterviewNotificationService
)

from app.ats.integrations.notifications.process_notifications import (
    ProcessNotificationManager
)

from app.ats.integrations.notifications.process.offer_notifications import (
    OfferNotificationService
)

from app.ats.integrations.notifications.process.onboarding_notifications import (
    OnboardingNotificationService
)

# Controladores y Servicios Principales
from app.ats.onboarding.onboarding_controller import (
    OnboardingController
)

# Importaciones circulares movidas dentro de funciones
def get_proposal_service():
    from app.ats.services import ProposalService
    return ProposalService

def get_interview_service():
    from app.ats.services import InterviewService
    return InterviewService

def get_offer_service():
    from app.ats.services import OfferService
    return OfferService

def get_onboarding_service():
    from app.ats.services import OnboardingService
    return OnboardingService

# Tareas de Propuestas
from app.ats.proposals.tasks import (
    send_proposal_email,
    generate_monthly_report
)

# Tareas de Feedback y Satisfacción
from app.ats.onboarding.client_feedback_tasks import (
    send_client_feedback_survey_task,
    check_pending_client_feedback_task,
    generate_client_feedback_reports_task,
    analyze_client_feedback_trends_task
)

# Tareas de Entrevistas
# TODO: Implementar módulo de entrevistas
# from app.ats.interviews.tasks import (
#     schedule_interview,
#     send_interview_reminder,
#     process_interview_feedback
# )

# Tareas de Ofertas
# TODO: Implementar módulo de ofertas
# from app.ats.offers.tasks import (
#     send_offer_notification,
#     process_offer_response,
#     generate_offer_letter
# )

# Tareas de Onboarding
from app.ats.onboarding.tasks import (
    start_onboarding_process,
    send_welcome_email,
    schedule_onboarding_tasks,
    process_onboarding_documents,
    send_check_in_reminder,
    send_satisfaction_survey_reminder,
    generate_client_satisfaction_report,
    schedule_follow_up_sequence
)

__all__ = [
    # Servicios de Notificaciones
    'InterviewNotificationService',  # Maneja notificaciones generales de entrevistas
    'ProcessNotificationManager',    # Maneja notificaciones con análisis de ubicación
    'OfferNotificationService',      # Maneja notificaciones de ofertas
    'OnboardingNotificationService', # Maneja notificaciones de onboarding
    
    # Controladores y Servicios Principales
    'OnboardingController',
    'get_proposal_service',
    'get_interview_service',
    'get_offer_service',
    'get_onboarding_service',
    
    # Tareas de Propuestas
    'send_proposal_email',
    'generate_monthly_report',
    
    # Tareas de Feedback y Satisfacción
    'send_client_feedback_survey_task',
    'check_pending_client_feedback_task',
    'generate_client_feedback_reports_task',
    'analyze_client_feedback_trends_task',
    
    # Tareas de Entrevistas
    # 'schedule_interview',
    # 'send_interview_reminder',
    # 'process_interview_feedback',
    
    # Tareas de Ofertas
    # 'send_offer_notification',
    # 'process_offer_response',
    # 'generate_offer_letter',
    
    # Tareas de Onboarding
    'start_onboarding_process',
    'send_welcome_email',
    'schedule_onboarding_tasks',
    'process_onboarding_documents',
    'send_check_in_reminder',
    'send_satisfaction_survey_reminder',
    'generate_client_satisfaction_report',
    'schedule_follow_up_sequence'
] 