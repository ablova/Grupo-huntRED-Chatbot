import logging
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from django.db import DatabaseError
from django.db.utils import OperationalError
from django.utils.translation import gettext_lazy as _
from ai_huntred.config.monitoring import MonitoringConfig

# Obtener emails de alerta desde la configuración
ALERT_EMAILS = MonitoringConfig.get_config()['ALERT_CONFIG']['ALERT_EMAILS']

logger = logging.getLogger(__name__)

class ErrorHandlerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
            return response
        except Exception as e:
            return self.handle_exception(request, e)

    def handle_exception(self, request, exception):
        """Maneja excepciones y retorna una respuesta apropiada."""
        status_code = 500
        error_type = type(exception).__name__
        
        # Loggear el error
        logger.error(
            f"Error {error_type} en {request.path}: {str(exception)}",
            exc_info=True,
            extra={'request': request}
        )

        # Manejar errores específicos
        if isinstance(exception, PermissionDenied):
            status_code = 403
            error_message = _('Access denied')
        elif isinstance(exception, (DatabaseError, OperationalError)):
            status_code = 503
            error_message = _('Database error')
            self.send_alert(f"Database error: {str(exception)}")
        else:
            error_message = _('An unexpected error occurred')
            
            # Notificar errores críticos
            if status_code == 500:
                self.send_alert(f"Internal server error: {str(exception)}")

        # Retornar respuesta JSON
        return JsonResponse({
            'error': error_message,
            'code': error_type,
            'timestamp': datetime.now().isoformat()
        }, status=status_code)

    def send_alert(self, message):
        """Envía una alerta por email si está configurado."""
        if ALERT_EMAILS:
            from django.core.mail import send_mail
            try:
                send_mail(
                    subject='[huntRED] Sistema: Error Crítico',
                    message=message,
                    from_email=None,  # Usará DEFAULT_FROM_EMAIL
                    recipient_list=ALERT_EMAILS,
                    fail_silently=False
                )
            except Exception as e:
                logger.error(f"Error sending alert email: {str(e)}")
