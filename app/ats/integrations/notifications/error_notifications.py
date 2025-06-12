"""
Módulo para manejar notificaciones específicas de errores.
Incluye notificaciones para diferentes tipos de errores y unidades de negocio.
"""

import logging
import traceback
from typing import Dict, Any, Optional
from datetime import datetime
from .system_notifications import system_notifier

logger = logging.getLogger(__name__)

class ErrorNotifier:
    """Clase para manejar notificaciones específicas de errores."""
    
    async def notify_system_error(self,
                                error_message: str,
                                error_type: str,
                                stack_trace: Optional[str] = None,
                                business_unit: Optional[str] = None,
                                additional_details: Optional[Dict[str, Any]] = None) -> bool:
        """
        Notifica sobre un error del sistema.
        
        Args:
            error_message: Mensaje de error
            error_type: Tipo de error
            stack_trace: Traza del error
            business_unit: Unidad de negocio
            additional_details: Detalles adicionales
        """
        try:
            # Preparar mensaje de error
            message = (
                f"❌ *Error del Sistema*\n\n"
                f"📝 *Tipo de Error:* {error_type}\n"
                f"💬 *Mensaje:* {error_message}"
            )
            
            # Agregar stack trace si existe
            if stack_trace:
                message += f"\n\n*Stack Trace:*\n```\n{stack_trace}\n```"
            
            # Agregar detalles adicionales si existen
            if additional_details:
                message += "\n\n*Detalles Adicionales:*\n"
                for key, value in additional_details.items():
                    message += f"• {key}: {value}\n"
            
            return await system_notifier.send_notification(
                message=message,
                notification_type="error",
                business_unit=business_unit,
                additional_data={
                    "tipo_error": error_type,
                    "fecha_error": datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Error en notify_system_error: {str(e)}")
            return False
            
    async def notify_api_error(self,
                             error_message: str,
                             api_endpoint: str,
                             response_status: Optional[int] = None,
                             response_body: Optional[str] = None,
                             business_unit: Optional[str] = None,
                             additional_details: Optional[Dict[str, Any]] = None) -> bool:
        """
        Notifica sobre un error de API.
        
        Args:
            error_message: Mensaje de error
            api_endpoint: Endpoint de la API
            response_status: Código de estado de la respuesta
            response_body: Cuerpo de la respuesta
            business_unit: Unidad de negocio
            additional_details: Detalles adicionales
        """
        try:
            # Preparar mensaje de error de API
            message = (
                f"🌐 *Error de API*\n\n"
                f"🔗 *Endpoint:* {api_endpoint}\n"
                f"💬 *Mensaje:* {error_message}"
            )
            
            # Agregar código de estado si existe
            if response_status:
                message += f"\n📊 *Código de Estado:* {response_status}"
            
            # Agregar cuerpo de respuesta si existe
            if response_body:
                message += f"\n\n*Respuesta:*\n```\n{response_body}\n```"
            
            # Agregar detalles adicionales si existen
            if additional_details:
                message += "\n\n*Detalles Adicionales:*\n"
                for key, value in additional_details.items():
                    message += f"• {key}: {value}\n"
            
            return await system_notifier.send_notification(
                message=message,
                notification_type="error",
                business_unit=business_unit,
                additional_data={
                    "tipo_error": "api_error",
                    "endpoint": api_endpoint,
                    "fecha_error": datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Error en notify_api_error: {str(e)}")
            return False
            
    async def notify_database_error(self,
                                  error_message: str,
                                  operation: str,
                                  table: Optional[str] = None,
                                  query: Optional[str] = None,
                                  business_unit: Optional[str] = None,
                                  additional_details: Optional[Dict[str, Any]] = None) -> bool:
        """
        Notifica sobre un error de base de datos.
        
        Args:
            error_message: Mensaje de error
            operation: Operación que falló
            table: Tabla afectada
            query: Query que falló
            business_unit: Unidad de negocio
            additional_details: Detalles adicionales
        """
        try:
            # Preparar mensaje de error de base de datos
            message = (
                f"🗄️ *Error de Base de Datos*\n\n"
                f"⚙️ *Operación:* {operation}\n"
                f"💬 *Mensaje:* {error_message}"
            )
            
            # Agregar tabla si existe
            if table:
                message += f"\n📋 *Tabla:* {table}"
            
            # Agregar query si existe
            if query:
                message += f"\n\n*Query:*\n```sql\n{query}\n```"
            
            # Agregar detalles adicionales si existen
            if additional_details:
                message += "\n\n*Detalles Adicionales:*\n"
                for key, value in additional_details.items():
                    message += f"• {key}: {value}\n"
            
            return await system_notifier.send_notification(
                message=message,
                notification_type="error",
                business_unit=business_unit,
                additional_data={
                    "tipo_error": "database_error",
                    "operacion": operation,
                    "fecha_error": datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Error en notify_database_error: {str(e)}")
            return False
            
    async def notify_validation_error(self,
                                    error_message: str,
                                    field: str,
                                    value: Any,
                                    business_unit: Optional[str] = None,
                                    additional_details: Optional[Dict[str, Any]] = None) -> bool:
        """
        Notifica sobre un error de validación.
        
        Args:
            error_message: Mensaje de error
            field: Campo con error
            value: Valor inválido
            business_unit: Unidad de negocio
            additional_details: Detalles adicionales
        """
        try:
            # Preparar mensaje de error de validación
            message = (
                f"⚠️ *Error de Validación*\n\n"
                f"📝 *Campo:* {field}\n"
                f"💬 *Mensaje:* {error_message}\n"
                f"📊 *Valor:* {value}"
            )
            
            # Agregar detalles adicionales si existen
            if additional_details:
                message += "\n\n*Detalles Adicionales:*\n"
                for key, value in additional_details.items():
                    message += f"• {key}: {value}\n"
            
            return await system_notifier.send_notification(
                message=message,
                notification_type="error",
                business_unit=business_unit,
                additional_data={
                    "tipo_error": "validation_error",
                    "campo": field,
                    "fecha_error": datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Error en notify_validation_error: {str(e)}")
            return False

# Instancia global del notificador de errores
error_notifier = ErrorNotifier() 