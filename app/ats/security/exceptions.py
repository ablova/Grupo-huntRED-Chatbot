"""
Excepciones avanzadas de seguridad para canales de comunicación (alineado a Meta Conversations 2025).
"""

class SecurityPolicyViolation(Exception):
    """
    Excepción lanzada cuando se viola una política de seguridad en canales como WhatsApp (Meta Conversations 2025).
    Incluye mensaje y código de error opcional.
    """
    def __init__(self, message: str, code: int = None):
        super().__init__(message)
        self.code = code

    def __str__(self):
        base = super().__str__()
        return f"{base} (código: {self.code})" if self.code is not None else base

__all__ = ["SecurityPolicyViolation"] 