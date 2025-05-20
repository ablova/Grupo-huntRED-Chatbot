# /home/pablo/app/com/chatbot/validation/__init__.py
"""
Módulo de validación para el chatbot.
"""

from django.conf import settings
from app.models import BusinessUnit
from app.com.chatbot.validation.truth_analyzer import TruthAnalyzer

# Inicializar truth_analyzer como None
truth_analyzer = None

def get_truth_analyzer():
    """
    Obtiene la instancia del analizador de verdad.
    Si no está inicializado, lo inicializa con la unidad de negocio por defecto.
    """
    global truth_analyzer
    if truth_analyzer is None:
        try:
            # Intentar obtener la unidad de negocio por defecto
            default_business_unit = BusinessUnit.objects.get(name="amigro")
            truth_analyzer = TruthAnalyzer(business_unit=default_business_unit)
        except BusinessUnit.DoesNotExist:
            # Si no existe, usar una unidad de negocio genérica
            truth_analyzer = TruthAnalyzer(business_unit=BusinessUnit.objects.first())
    return truth_analyzer

__all__ = ['get_truth_analyzer']
