class MLValidator:
    """
    Clase base para validación de modelos ML.
    """
    def __init__(self):
        pass

    def validate(self, model, data):
        """
        Método de validación genérico.
        """
        return True

__all__ = ['MLValidator'] 