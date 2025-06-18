# app/ats/chatbot/message_service.py
"""Backward-compatibility shim for MessageService.

Some legacy modules import `MessageService` from the path
`app.ats.chatbot.message_service`.  The implementation was later moved to
`app.ats.integrations.services.message`.  This stub re-exports the class so
that older imports continue to work without modifications.
"""

from __future__ import annotations

from app.ats.integrations.services.message import MessageService as _MessageService

__all__ = ["MessageService"]

# Public alias
MessageService = _MessageService
