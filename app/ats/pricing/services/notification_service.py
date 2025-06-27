"""
Servicio de notificaciones integrado con el sistema existente.
Utiliza los módulos de notificaciones ya implementados en huntRED.
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from django.utils import timezone

from app.models import Person, BusinessUnit
from app.ats.pricing.models import PaymentTransaction, ScheduledPayment, ExternalServiceInvoice

logger = logging.getLogger(__name__)

class PricingNotificationService:
    """Servicio de notificaciones para el módulo de pricing."""
    
    def __init__(self, business_unit: BusinessUnit):
        self.business_unit = business_unit
    
    def notify_payment_received(
        self,
        transaction: PaymentTransaction,
        recipient: Person
    ) -> Dict[str, Any]:
        """
        Notifica cuando se recibe un pago.
        
        Args:
            transaction: Transacción de pago
            recipient: Persona que debe recibir la notificación
            
        Returns:
            Dict con resultado de la notificación
        """
        try:
            # Usar el sistema de notificaciones existente
            from app.ats.notifications.services import NotificationService
            
            notification_service = NotificationService()
            
            # Crear notificación
            notification_data = {
                'type': 'payment_received',
                'title': 'Pago Recibido',
                'message': f'Se ha recibido un pago de ${transaction.amount:,.2f} MXN',
                'recipient': recipient,
                'business_unit': self.business_unit,
                'metadata': {
                    'transaction_id': transaction.id,
                    'amount': float(transaction.amount),
                    'gateway': transaction.gateway,
                    'status': transaction.status,
                    'timestamp': transaction.created_at.isoformat()
                }
            }
            
            # Enviar notificación
            result = notification_service.send_notification(notification_data)
            
            # Log de la notificación
            logger.info(f"Notificación de pago enviada: {result}")
            
            return {
                'success': True,
                'notification_sent': True,
                'recipient': recipient.email,
                'timestamp': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error enviando notificación de pago: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def notify_payment_failed(
        self,
        transaction: PaymentTransaction,
        recipient: Person
    ) -> Dict[str, Any]:
        """
        Notifica cuando falla un pago.
        
        Args:
            transaction: Transacción de pago fallida
            recipient: Persona que debe recibir la notificación
            
        Returns:
            Dict con resultado de la notificación
        """
        try:
            from app.ats.notifications.services import NotificationService
            
            notification_service = NotificationService()
            
            notification_data = {
                'type': 'payment_failed',
                'title': 'Pago Fallido',
                'message': f'El pago de ${transaction.amount:,.2f} MXN ha fallado',
                'recipient': recipient,
                'business_unit': self.business_unit,
                'metadata': {
                    'transaction_id': transaction.id,
                    'amount': float(transaction.amount),
                    'gateway': transaction.gateway,
                    'error_message': transaction.error_message,
                    'timestamp': transaction.created_at.isoformat()
                }
            }
            
            result = notification_service.send_notification(notification_data)
            
            logger.info(f"Notificación de pago fallido enviada: {result}")
            
            return {
                'success': True,
                'notification_sent': True,
                'recipient': recipient.email,
                'timestamp': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error enviando notificación de pago fallido: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def notify_invoice_overdue(
        self,
        invoice: ExternalServiceInvoice,
        recipient: Person
    ) -> Dict[str, Any]:
        """
        Notifica cuando una factura está vencida.
        
        Args:
            invoice: Factura vencida
            recipient: Persona que debe recibir la notificación
            
        Returns:
            Dict con resultado de la notificación
        """
        try:
            from app.ats.notifications.services import NotificationService
            
            notification_service = NotificationService()
            
            # Calcular días de vencimiento
            days_overdue = (timezone.now().date() - invoice.due_date).days
            
            notification_data = {
                'type': 'invoice_overdue',
                'title': 'Factura Vencida',
                'message': f'La factura {invoice.invoice_number} está vencida por {days_overdue} días. Monto: ${invoice.total_amount:,.2f} MXN',
                'recipient': recipient,
                'business_unit': self.business_unit,
                'metadata': {
                    'invoice_id': invoice.id,
                    'invoice_number': invoice.invoice_number,
                    'amount': float(invoice.total_amount),
                    'days_overdue': days_overdue,
                    'due_date': invoice.due_date.isoformat(),
                    'client_name': invoice.service.client.name if invoice.service.client else 'N/A'
                }
            }
            
            result = notification_service.send_notification(notification_data)
            
            logger.info(f"Notificación de factura vencida enviada: {result}")
            
            return {
                'success': True,
                'notification_sent': True,
                'recipient': recipient.email,
                'days_overdue': days_overdue,
                'timestamp': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error enviando notificación de factura vencida: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def notify_scheduled_payment_due(
        self,
        scheduled_payment: ScheduledPayment,
        recipient: Person
    ) -> Dict[str, Any]:
        """
        Notifica cuando un pago programado está próximo a vencer.
        
        Args:
            scheduled_payment: Pago programado
            recipient: Persona que debe recibir la notificación
            
        Returns:
            Dict con resultado de la notificación
        """
        try:
            from app.ats.notifications.services import NotificationService
            
            notification_service = NotificationService()
            
            # Calcular días hasta el vencimiento
            days_until_due = (scheduled_payment.next_payment_date - timezone.now().date()).days
            
            notification_data = {
                'type': 'scheduled_payment_due',
                'title': 'Pago Programado Próximo',
                'message': f'El pago programado "{scheduled_payment.name}" vence en {days_until_due} días. Monto: ${scheduled_payment.amount:,.2f} MXN',
                'recipient': recipient,
                'business_unit': self.business_unit,
                'metadata': {
                    'scheduled_payment_id': scheduled_payment.id,
                    'name': scheduled_payment.name,
                    'amount': float(scheduled_payment.amount),
                    'days_until_due': days_until_due,
                    'next_payment_date': scheduled_payment.next_payment_date.isoformat(),
                    'beneficiary_name': scheduled_payment.beneficiary_name
                }
            }
            
            result = notification_service.send_notification(notification_data)
            
            logger.info(f"Notificación de pago programado enviada: {result}")
            
            return {
                'success': True,
                'notification_sent': True,
                'recipient': recipient.email,
                'days_until_due': days_until_due,
                'timestamp': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error enviando notificación de pago programado: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def notify_provider_validation_failed(
        self,
        provider: Person,
        validation_result: Dict[str, Any],
        recipient: Person
    ) -> Dict[str, Any]:
        """
        Notifica cuando falla la validación de un proveedor.
        
        Args:
            provider: Proveedor con validación fallida
            validation_result: Resultado de la validación
            recipient: Persona que debe recibir la notificación
            
        Returns:
            Dict con resultado de la notificación
        """
        try:
            from app.ats.notifications.services import NotificationService
            
            notification_service = NotificationService()
            
            notification_data = {
                'type': 'provider_validation_failed',
                'title': 'Validación de Proveedor Fallida',
                'message': f'La validación del proveedor {provider.name} ha fallado',
                'recipient': recipient,
                'business_unit': self.business_unit,
                'metadata': {
                    'provider_id': provider.id,
                    'provider_name': provider.name,
                    'rfc': provider.rfc,
                    'validation_status': validation_result.get('overall_status'),
                    'blocking_issues': validation_result.get('blocking_issues', []),
                    'recommendations': validation_result.get('recommendations', [])
                }
            }
            
            result = notification_service.send_notification(notification_data)
            
            logger.info(f"Notificación de validación de proveedor enviada: {result}")
            
            return {
                'success': True,
                'notification_sent': True,
                'recipient': recipient.email,
                'validation_status': validation_result.get('overall_status'),
                'timestamp': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error enviando notificación de validación de proveedor: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def notify_cfdi_generation_failed(
        self,
        invoice: ExternalServiceInvoice,
        error_message: str,
        recipient: Person
    ) -> Dict[str, Any]:
        """
        Notifica cuando falla la generación de CFDI.
        
        Args:
            invoice: Factura con error en CFDI
            error_message: Mensaje de error
            recipient: Persona que debe recibir la notificación
            
        Returns:
            Dict con resultado de la notificación
        """
        try:
            from app.ats.notifications.services import NotificationService
            
            notification_service = NotificationService()
            
            notification_data = {
                'type': 'cfdi_generation_failed',
                'title': 'Error en Generación CFDI',
                'message': f'Error generando CFDI para la factura {invoice.invoice_number}',
                'recipient': recipient,
                'business_unit': self.business_unit,
                'metadata': {
                    'invoice_id': invoice.id,
                    'invoice_number': invoice.invoice_number,
                    'error_message': error_message,
                    'client_name': invoice.service.client.name if invoice.service.client else 'N/A',
                    'amount': float(invoice.total_amount)
                }
            }
            
            result = notification_service.send_notification(notification_data)
            
            logger.info(f"Notificación de error CFDI enviada: {result}")
            
            return {
                'success': True,
                'notification_sent': True,
                'recipient': recipient.email,
                'error_message': error_message,
                'timestamp': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error enviando notificación de error CFDI: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def notify_high_risk_client(
        self,
        client: Person,
        risk_data: Dict[str, Any],
        recipient: Person
    ) -> Dict[str, Any]:
        """
        Notifica sobre clientes de alto riesgo.
        
        Args:
            client: Cliente de alto riesgo
            risk_data: Datos del análisis de riesgo
            recipient: Persona que debe recibir la notificación
            
        Returns:
            Dict con resultado de la notificación
        """
        try:
            from app.ats.notifications.services import NotificationService
            
            notification_service = NotificationService()
            
            notification_data = {
                'type': 'high_risk_client',
                'title': 'Cliente de Alto Riesgo Detectado',
                'message': f'El cliente {client.name} ha sido identificado como de alto riesgo',
                'recipient': recipient,
                'business_unit': self.business_unit,
                'metadata': {
                    'client_id': client.id,
                    'client_name': client.name,
                    'risk_level': risk_data.get('risk_level'),
                    'overdue_amount': risk_data.get('overdue_amount'),
                    'overdue_ratio': risk_data.get('overdue_ratio'),
                    'recommendations': risk_data.get('recommendations', [])
                }
            }
            
            result = notification_service.send_notification(notification_data)
            
            logger.info(f"Notificación de cliente de alto riesgo enviada: {result}")
            
            return {
                'success': True,
                'notification_sent': True,
                'recipient': recipient.email,
                'risk_level': risk_data.get('risk_level'),
                'timestamp': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error enviando notificación de cliente de alto riesgo: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_bulk_notifications(
        self,
        notification_type: str,
        recipients: List[Person],
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Envía notificaciones masivas.
        
        Args:
            notification_type: Tipo de notificación
            recipients: Lista de destinatarios
            data: Datos de la notificación
            
        Returns:
            Dict con resultado de las notificaciones
        """
        try:
            from app.ats.notifications.services import NotificationService
            
            notification_service = NotificationService()
            
            results = []
            success_count = 0
            error_count = 0
            
            for recipient in recipients:
                try:
                    notification_data = {
                        'type': notification_type,
                        'title': data.get('title', 'Notificación'),
                        'message': data.get('message', ''),
                        'recipient': recipient,
                        'business_unit': self.business_unit,
                        'metadata': data.get('metadata', {})
                    }
                    
                    result = notification_service.send_notification(notification_data)
                    
                    if result.get('success'):
                        success_count += 1
                    else:
                        error_count += 1
                    
                    results.append({
                        'recipient': recipient.email,
                        'success': result.get('success', False),
                        'error': result.get('error')
                    })
                    
                except Exception as e:
                    error_count += 1
                    results.append({
                        'recipient': recipient.email,
                        'success': False,
                        'error': str(e)
                    })
            
            logger.info(f"Notificaciones masivas enviadas: {success_count} exitosas, {error_count} fallidas")
            
            return {
                'success': True,
                'total_recipients': len(recipients),
                'success_count': success_count,
                'error_count': error_count,
                'results': results,
                'timestamp': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error enviando notificaciones masivas: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_notification_history(
        self,
        notification_type: str = None,
        recipient: Person = None,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> Dict[str, Any]:
        """
        Obtiene historial de notificaciones.
        
        Args:
            notification_type: Tipo de notificación a filtrar
            recipient: Destinatario a filtrar
            start_date: Fecha de inicio
            end_date: Fecha de fin
            
        Returns:
            Dict con historial de notificaciones
        """
        try:
            from app.ats.notifications.models import Notification
            
            # Construir filtros
            filters = {'business_unit': self.business_unit}
            
            if notification_type:
                filters['type'] = notification_type
            
            if recipient:
                filters['recipient'] = recipient
            
            if start_date:
                filters['created_at__gte'] = start_date
            
            if end_date:
                filters['created_at__lte'] = end_date
            
            # Obtener notificaciones
            notifications = Notification.objects.filter(**filters).order_by('-created_at')
            
            # Convertir a lista de diccionarios
            notification_list = []
            for notification in notifications:
                notification_list.append({
                    'id': notification.id,
                    'type': notification.type,
                    'title': notification.title,
                    'message': notification.message,
                    'recipient': notification.recipient.email if notification.recipient else 'N/A',
                    'status': notification.status,
                    'created_at': notification.created_at.isoformat(),
                    'metadata': notification.metadata
                })
            
            return {
                'success': True,
                'notifications': notification_list,
                'total_count': len(notification_list),
                'filters_applied': {
                    'notification_type': notification_type,
                    'recipient': recipient.email if recipient else None,
                    'start_date': start_date.isoformat() if start_date else None,
                    'end_date': end_date.isoformat() if end_date else None
                }
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo historial de notificaciones: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            } 