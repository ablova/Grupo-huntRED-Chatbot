# app/ats/integrations/notifications/channels/slack.py
"""SlackNotificationChannel

Canal de notificaciones para Slack que utiliza el token de bot
configurado en el modelo ``SlackAPI`` asociado a la *BusinessUnit*.

No introduce una dependencia dura: si ``slack_sdk`` no está instalado el
canal se marcará como inactivo y reportará el error correspondiente. De
esta forma evitamos bloqueos de importación en entornos sin dicha
librería, siguiendo la misma estrategia aplicada a Twilio.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from asgiref.sync import sync_to_async

from app.models import BusinessUnit, SlackAPI
from app.ats.integrations.notifications.core.base import BaseNotificationChannel

logger = logging.getLogger("notifications")

try:
    from slack_sdk import WebClient  # type: ignore
    from slack_sdk.errors import SlackApiError  # type: ignore
except ImportError:  # pragma: no cover – slack_sdk es opcional

    class WebClient:  # pylint: disable=too-few-public-methods
        """Stub vacía para evitar errores de importación."""

        def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: D401,E501
            raise RuntimeError("slack_sdk no está instalado")

    class SlackApiError(Exception):
        """Excepción stub para mantener la compatibilidad."""


class SlackNotificationChannel(BaseNotificationChannel):
    """Canal de notificaciones para Slack."""

    def __init__(self, business_unit: BusinessUnit):
        super().__init__(business_unit)
        self._slack_api_cfg: Optional[SlackAPI] = (
            business_unit.slack_apis.filter(is_active=True).first()
        )
        self._client: Optional[WebClient] = None

        if self._slack_api_cfg:
            try:
                self._client = WebClient(token=self._slack_api_cfg.bot_token)
            except RuntimeError:
                # slack_sdk no instalado
                self._client = None

    def is_enabled(self) -> bool:  # type: ignore[override]
        return bool(self._client and self._slack_api_cfg and self._slack_api_cfg.is_active)

    async def send_notification(
        self,
        message: str,
        options: Optional[Dict[str, Any]] = None,
        priority: int = 0,
    ) -> Dict[str, Any]:  # noqa: D401,E501
        """Envía un mensaje a un canal de Slack.

        Args:
            message: Contenido del mensaje.
            options: ``dict`` con opciones adicionales. Acepta:
                * ``channel`` – canal o user ID de destino; por defecto usa el
                  configurado en ``SlackAPI.default_channel``.
                * ``thread_ts`` – timestamp de hilo para responder dentro de un
                  thread existente.
            priority: Se utiliza para prefijar el mensaje (urgente, etc.).
        """
        message_fmt = self._format_message(message, priority)

        if not self.is_enabled():
            error_msg = "SlackNotificationChannel no está activo o slack_sdk ausente"
            logger.warning(error_msg)
            return {"success": False, "error": error_msg}

        channel = (
            options.get("channel") if options else None
        ) or self._slack_api_cfg.default_channel  # type: ignore[union-attr]
        thread_ts = options.get("thread_ts") if options else None

        try:
            assert self._client  # para mypy
            response = await sync_to_async(self._client.chat_postMessage)(
                channel=channel,
                text=message_fmt,
                thread_ts=thread_ts,
            )
            await self.log_notification(message_fmt, "SENT", {"channel": channel})
            return {"success": True, "response": dict(response.data)}
        except SlackApiError as exc:  # type: ignore[abstract]
            logger.error("Error enviando mensaje a Slack: %s", exc, exc_info=True)
            await self.log_notification(
                message_fmt,
                "FAILED",
                {"error": str(exc), "channel": channel},
            )
            return {"success": False, "error": str(exc)}
