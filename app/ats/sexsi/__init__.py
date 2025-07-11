# app/ats/sexsi/__init__.py
"""
Módulo SEXSI (Sistema de Acuerdos Íntimos Consensuados).
Sistema para firma de acuerdos íntimos consensuados usando tecnología 
de firma electrónica y blockchain, alineado con las leyes sexuales de cada país.
"""

from .views import (
    sexsi_dashboard,
    create_agreement,
    sign_agreement,
    agreement_status,
    legal_compliance,
    process_payment,
    consent_form,
    mutual_agreement,
    agreement_detail,
    preference_selection
)

__all__ = [
    'sexsi_dashboard',
    'create_agreement',
    'sign_agreement', 
    'agreement_status',
    'legal_compliance',
    'process_payment',
    'consent_form',
    'mutual_agreement',
    'agreement_detail',
    'preference_selection'
] 