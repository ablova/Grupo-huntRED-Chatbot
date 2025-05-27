# /home/pablo/app/com/chatbot/validation/__init__.py
"""
Módulo de validación para el chatbot.
"""

from django.conf import settings
# Eliminar la importación directa de BusinessUnit
# from app.models import BusinessUnit
# Eliminada importación a nivel de módulo para evitar dependencias circulares
# from app.com.chatbot.validation.truth_analyzer import TruthAnalyzer

# Inicializar truth_analyzer como None
truth_analyzer = None

def get_truth_analyzer():
    """
    Obtiene la instancia del analizador de verdad.
    Si no está inicializado, lo inicializa con la unidad de negocio por defecto.
    Si no puede inicializarlo, retorna None y registra el error.
    """
    global truth_analyzer
    if truth_analyzer is None:
        try:
            # Importar BusinessUnit dentro de la función para lazy loading
            from app.models import BusinessUnit
            
            # Intentar obtener la unidad de negocio por defecto
            default_business_unit = BusinessUnit.objects.get(name="amigro")
            # Importación justo antes de usar para evitar dependencias circulares
            from app.com.chatbot.validation.truth_analyzer import TruthAnalyzer
            truth_analyzer = TruthAnalyzer(business_unit=default_business_unit)
        except Exception as e:
            # Manejo de errores más amplio
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Error al inicializar TruthAnalyzer: {e}")
            
            # Intento alternativo seguro
            try:
                from app.models import BusinessUnit
                default_bu = BusinessUnit.objects.first()
                if default_bu:
                    # Solo importamos TruthAnalyzer si tenemos un BusinessUnit válido
                    from app.com.chatbot.validation.truth_analyzer import TruthAnalyzer
                    truth_analyzer = TruthAnalyzer(business_unit=default_bu)
            except Exception as e2:
                # Si todo falla, registramos el error y devolvemos None
                logger.error(f"No se pudo inicializar TruthAnalyzer: {e2}")
                # No intentamos crear un TruthAnalyzer sin BusinessUnit ya que su constructor lo requiere
    return truth_analyzer

__all__ = ['get_truth_analyzer']