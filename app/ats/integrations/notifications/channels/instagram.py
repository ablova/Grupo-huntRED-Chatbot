# app/ats/integrations/notifications/channels/instagram.py
"""

InstagramNotificationChannel (LEGACY WRAPPER)
------------------------------------------------
Canal de notificaciones *legacy* para Instagram utilizado por
`ProcessNotificationManager`.  Ya existe la integración operativa en
`app/ats/integrations/channels/instagram/instagram.py`; este wrapper se
limita a delegar la llamada para evitar errores de importación mientras
mantenemos compatibilidad.

No introduce dependencias externas.  Si en el futuro se requiere acceso
al SDK oficial de Meta, se deberá integrar en el handler principal y
este archivo podrá eliminarse.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from asgiref.sync import sync_to_async

from app.models import BusinessUnit, InstagramAPI  # type: ignore[attr-defined]
from app.ats.integrations.notifications.core.base import BaseNotificationChannel

# Handler real
from app.ats.integrations.channels.instagram.instagram import (
    InstagramHandler as _RealInstagramHandler,
)

logger = logging.getLogger("notifications")


class InstagramNotificationChannel(BaseNotificationChannel):
    """Wrapper simplificado que delega en *InstagramHandler*."""

    def __init__(self, business_unit: BusinessUnit):
        super().__init__(business_unit)
        self._insta_cfg: Optional[InstagramAPI] = (
            business_unit.instagram_apis.filter(is_active=True).first()  # type: ignore[attr-defined]
        )
        self._handler: Optional[_RealInstagramHandler] = None
        if self._insta_cfg:
            self._handler = _RealInstagramHandler(self._insta_cfg)

    def is_enabled(self) -> bool:  # type: ignore[override]
        return bool(self._handler and self._insta_cfg and self._insta_cfg.is_active)

    async def send_notification(
        self,
        message: str,
        options: Optional[Dict[str, Any]] = None,
        priority: int = 0,
    ) -> Dict[str, Any]:
        """Envía un DM o comentario a través de Instagram.

        Args:
            message: Texto del mensaje.
            options: parámetros adicionales (por ahora sin uso).
            priority: usado para prefijar el mensaje.
        """
        if not self.is_enabled():
            return {"success": False, "error": "Instagram channel not enabled"}

        assert self._handler
        msg_fmt = self._format_message(message, priority)
        result = await self._handler.send_message_async(msg_fmt, options or {})
        await self.log_notification(msg_fmt, "SENT" if result.get("success") else "FAILED")
        return result
