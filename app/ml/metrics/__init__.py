class MetricsCalculator:
    """
    Clase base para cálculo de métricas ML.
    """
    def __init__(self):
        pass

    def calculate_metrics(self, y_true, y_pred):
        """
        Método genérico para calcular métricas.
        """
        return {}

__all__ = ['MetricsCalculator'] 