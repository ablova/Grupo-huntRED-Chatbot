# app/ats/sexsi/__init__.py
"""
Módulo SEXSI (Sistema de Experiencia y Satisfacción del Usuario).
"""

from .views import (
    sexsi_dashboard,
    sexsi_analytics,
    sexsi_reports,
    sexsi_settings
)

__all__ = [
    'sexsi_dashboard',
    'sexsi_analytics', 
    'sexsi_reports',
    'sexsi_settings'
] 