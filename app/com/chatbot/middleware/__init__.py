"""
Middleware para el sistema de chatbot.

Este paquete contiene middlewares para interceptar y procesar mensajes
antes de que lleguen al flujo principal del chatbot.
"""

from .notification_handler import NotificationMiddleware

__all__ = ['NotificationMiddleware']
