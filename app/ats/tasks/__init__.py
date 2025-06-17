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

from app.ats.services import (
    ProposalService,
    InterviewService,
    OfferService,
    OnboardingService
)

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
from app.ats.interviews.tasks import (
    schedule_interview,
    send_interview_reminder,
    process_interview_feedback
)

# Tareas de Ofertas
from app.ats.offers.tasks import (
    send_offer_notification,
    process_offer_response,
    generate_offer_letter
)

# Tareas de Onboarding
from app.ats.onboarding.tasks import (
    start_onboarding_process,
    send_welcome_email,
    schedule_onboarding_tasks,
    process_onboarding_documents
)

__all__ = [
    # Servicios de Notificaciones
    'InterviewNotificationService',  # Maneja notificaciones generales de entrevistas
    'ProcessNotificationManager',    # Maneja notificaciones con análisis de ubicación
    'OfferNotificationService',      # Maneja notificaciones de ofertas
    'OnboardingNotificationService', # Maneja notificaciones de onboarding
    
    # Controladores y Servicios Principales
    'OnboardingController',
    'ProposalService',
    'InterviewService',
    'OfferService',
    'OnboardingService',
    
    # Tareas de Propuestas
    'send_proposal_email',
    'generate_monthly_report',
    
    # Tareas de Feedback y Satisfacción
    'send_client_feedback_survey_task',
    'check_pending_client_feedback_task',
    'generate_client_feedback_reports_task',
    'analyze_client_feedback_trends_task',
    
    # Tareas de Entrevistas
    'schedule_interview',
    'send_interview_reminder',
    'process_interview_feedback',
    
    # Tareas de Ofertas
    'send_offer_notification',
    'process_offer_response',
    'generate_offer_letter',
    
    # Tareas de Onboarding
    'start_onboarding_process',
    'send_welcome_email',
    'schedule_onboarding_tasks',
    'process_onboarding_documents'
] 