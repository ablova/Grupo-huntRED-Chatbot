# app/ats/notifications/__init__.py
"""
Sistema de Notificaciones para huntRED®

Este módulo proporciona notificaciones específicas para diferentes procesos:
- Notificaciones de reclutamiento
- Notificaciones de análisis
- Notificaciones de mercado
- Notificaciones de entrevistas
"""

from .recruitment_notifications import RecruitmentNotifier

__all__ = [
    'RecruitmentNotifier',
] 