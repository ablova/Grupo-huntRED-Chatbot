# /home/pablo/app/com/pricing/feedback_models.py
"""
Re-exportación de modelos de feedback desde app.models.
Este archivo existe para mantener la compatibilidad con el código existente.
"""

from app.ats.pricing.models.feedback import ProposalFeedback, MeetingRequest

__all__ = ['ProposalFeedback', 'MeetingRequest']
