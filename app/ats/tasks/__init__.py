"""Módulo de tareas."""

from .proposal_tasks import (
    send_proposal_notification,
    update_proposal_status
)
from .interview_tasks import (
    schedule_interview,
    send_interview_reminder
)
from .offer_tasks import (
    send_offer_notification,
    process_offer_response
)
from .onboarding_tasks import (
    start_onboarding_process,
    send_welcome_email
)

__all__ = [
    'send_proposal_notification',
    'update_proposal_status',
    'schedule_interview',
    'send_interview_reminder',
    'send_offer_notification',
    'process_offer_response',
    'start_onboarding_process',
    'send_welcome_email'
] 