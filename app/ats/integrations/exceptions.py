from rest_framework.exceptions import APIException
from rest_framework import status

class IntegrationError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Error en la integración'
    default_code = 'integration_error'

class IntegrationNotFound(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'Integración no encontrada'
    default_code = 'integration_not_found'

class IntegrationConfigError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Error en la configuración de la integración'
    default_code = 'integration_config_error'

class WebhookError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Error en el webhook'
    default_code = 'webhook_error' 