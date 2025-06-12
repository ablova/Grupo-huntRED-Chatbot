"""
Recipient-specific notification modules for the Grupo huntRED® Chatbot.

This package contains notification handlers organized by recipient type:
- CandidateNotifier: For candidate-facing notifications
- ClientNotifier: For client-facing notifications
- PabloNotifier: For system monitoring and control (previously InternalNotifier)
- ManagerNotifier: For manager/team lead notifications
"""

# Import recipient modules
from .candidate import CandidateNotifier
from .client import ClientNotifier
from .pablo import PabloNotifier as InternalNotifier  # Alias for backward compatibility
from .manager import ManagerNotifier

__all__ = [
    'CandidateNotifier',
    'ClientNotifier',
    'PabloNotifier',
    'InternalNotifier',  # Backward compatibility
    'ManagerNotifier',
]
