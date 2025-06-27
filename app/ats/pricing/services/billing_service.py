# /home/pablo/app/ats/pricing/services/billing_service.py
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from datetime import timedelta
from decimal import Decimal
from django.db import transaction
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from typing import Dict, Any, List, Optional

from app.models import PaymentSchedule, PaymentNotification, BusinessUnit, Person, Service, Invoice, LineItem, Order, DiscountCoupon
from app.ats.pricing.models import PricingCalculation, PricingPayment
from app.ats.pricing.services.pricing_service import PricingService
from app.ats.pricing.services.discount_service import DiscountService

class BillingService:
    """
    Servicio para manejar la facturación y cobranza
    """
    
    def __init__(self):
        self.pricing_service = PricingService()
        self.discount_service = DiscountService()
    
    @staticmethod
    def calculate_annual_salary(monthly_salary: Decimal, bonus_months: Decimal = Decimal('0')) -> Decimal:
        """
        Calcula el salario anual incluyendo aguinaldo y bonos
        
        Args:
            monthly_salary: Salario mensual
            bonus_months: Meses de bono adicionales
            
        Returns:
            Decimal: Salario anual calculado
        """
        # 12 meses + 1 mes de aguinaldo + meses de bono
        total_months = Decimal('13') + bonus_months
        return monthly_salary * total_months

    @staticmethod
    def create_service_calculation(
        position: str,
        monthly_salary: Decimal,
        bonus_months: Decimal,
        fee_percentage: str,
        custom_fee: Decimal = None,
        payment_structure: str = 'standard'
    ) -> PricingCalculation:
        """
        Crea un nuevo cálculo de servicio y sus pagos asociados
        """
        # Calcular salario anual
        annual_salary = BillingService.calculate_annual_salary(monthly_salary, bonus_months)
        
        # Calcular honorarios totales
        total_fee = (annual_salary * Decimal(fee_percentage)) / Decimal('100')
        
        # Crear el cálculo
        service = PricingCalculation.objects.create(
            position=position,
            monthly_salary=monthly_salary,
            bonus_months=bonus_months,
            annual_salary=annual_salary,
            fee_percentage=fee_percentage,
            total_fee=total_fee,
            custom_fee=custom_fee,
            payment_structure=payment_structure
        )
        
        # Crear los pagos según la estructura
        if payment_structure == 'standard':
            # 25% Retainer + 75% Placement
            PricingPayment.objects.create(
                service=service,
                concept='retainer',
                amount=(total_fee * Decimal('25')) / Decimal('100'),
                due_date=timezone.now().date()
            )
            PricingPayment.objects.create(
                service=service,
                concept='placement',
                amount=(total_fee * Decimal('75')) / Decimal('100'),
                due_date=timezone.now().date() + timezone.timedelta(days=30)
            )
        elif payment_structure == 'extended':
            # 17.5% x 2 Retainer + 65% Placement
            PricingPayment.objects.create(
                service=service,
                concept='retainer',
                amount=(total_fee * Decimal('17.5')) / Decimal('100'),
                due_date=timezone.now().date()
            )
            PricingPayment.objects.create(
                service=service,
                concept='retainer',
                amount=(total_fee * Decimal('17.5')) / Decimal('100'),
                due_date=timezone.now().date() + timezone.timedelta(days=15)
            )
            PricingPayment.objects.create(
                service=service,
                concept='placement',
                amount=(total_fee * Decimal('65')) / Decimal('100'),
                due_date=timezone.now().date() + timezone.timedelta(days=30)
            )
        else:  # recurring
            # 35% Retainer + 65% Placement (3 pagos)
            PricingPayment.objects.create(
                service=service,
                concept='retainer',
                amount=(total_fee * Decimal('35')) / Decimal('100'),
                due_date=timezone.now().date()
            )
            PricingPayment.objects.create(
                service=service,
                concept='placement',
                amount=(total_fee * Decimal('32.5')) / Decimal('100'),
                due_date=timezone.now().date() + timezone.timedelta(days=30)
            )
            PricingPayment.objects.create(
                service=service,
                concept='placement',
                amount=(total_fee * Decimal('32.5')) / Decimal('100'),
                due_date=timezone.now().date() + timezone.timedelta(days=60)
            )
        
        return service

    @staticmethod
    def create_payment_schedule(calculation: PricingCalculation) -> list:
        """
        Crea el calendario de pagos según la estructura seleccionada
        
        Args:
            calculation: Instancia de PricingCalculation
            
        Returns:
            list: Lista de PaymentSchedule creados
        """
        payments = []
        today = timezone.now().date()
        
        if calculation.payment_structure == 'standard':
            # Retainer (25%)
            payments.append(PaymentSchedule.objects.create(
                service_calculation=calculation,
                payment_type='retainer',
                amount=calculation.retainer_amount,
                due_date=today,
                payment_number=1
            ))
            
            # Placement (75%)
            payments.append(PaymentSchedule.objects.create(
                service_calculation=calculation,
                payment_type='placement',
                amount=calculation.placement_amount,
                due_date=today + timedelta(days=30),  # 30 días después
                payment_number=2
            ))
            
        elif calculation.payment_structure == 'extended':
            # Retainer 1 (17.5%)
            payments.append(PaymentSchedule.objects.create(
                service_calculation=calculation,
                payment_type='retainer',
                amount=calculation.retainer_amount / Decimal('2'),
                due_date=today,
                payment_number=1
            ))
            
            # Retainer 2 (17.5%)
            payments.append(PaymentSchedule.objects.create(
                service_calculation=calculation,
                payment_type='retainer',
                amount=calculation.retainer_amount / Decimal('2'),
                due_date=today + timedelta(days=30),
                payment_number=2
            ))
            
            # Placement (65%)
            payments.append(PaymentSchedule.objects.create(
                service_calculation=calculation,
                payment_type='placement',
                amount=calculation.placement_amount,
                due_date=today + timedelta(days=60),
                payment_number=3
            ))
            
        else:  # recurring
            # Retainer (35%)
            payments.append(PaymentSchedule.objects.create(
                service_calculation=calculation,
                payment_type='retainer',
                amount=calculation.retainer_amount,
                due_date=today,
                payment_number=1
            ))
            
            # Placement dividido en 3 pagos (65%)
            placement_amount = calculation.placement_amount / Decimal('3')
            for i in range(3):
                payments.append(PaymentSchedule.objects.create(
                    service_calculation=calculation,
                    payment_type='placement',
                    amount=placement_amount,
                    due_date=today + timedelta(days=30 * (i + 1)),
                    payment_number=i + 2
                ))
        
        return payments

    @staticmethod
    def send_payment_notification(
        payment: PaymentSchedule,
        notification_type: str,
        recipient_email: str,
        subject: str,
        message: str,
        attachments: list = None
    ) -> PaymentNotification:
        """
        Envía una notificación de pago
        
        Args:
            payment: Instancia de PaymentSchedule
            notification_type: Tipo de notificación
            recipient_email: Email del destinatario
            subject: Asunto del correo
            message: Mensaje del correo
            attachments: Lista de archivos adjuntos
            
        Returns:
            PaymentNotification: Instancia creada
        """
        # Crear notificación
        notification = PaymentNotification.objects.create(
            payment_schedule=payment,
            notification_type=notification_type,
            recipient_email=recipient_email,
            subject=subject,
            message=message,
            attachments=attachments or []
        )
        
        # Enviar correo
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            cc=notification.cc_list,
            fail_silently=True
        )
        
        # Actualizar estado del pago
        if notification_type == 'invoice':
            payment.invoice_sent = True
            payment.invoice_sent_date = timezone.now()
            payment.status = 'sent'
            payment.save()
        
        return notification

    @staticmethod
    def check_overdue_payments() -> list:
        """
        Verifica pagos vencidos y envía notificaciones
        
        Returns:
            list: Lista de pagos vencidos
        """
        today = timezone.now().date()
        overdue_payments = PaymentSchedule.objects.filter(
            due_date__lt=today,
            status__in=['pending', 'sent']
        )
        
        for payment in overdue_payments:
            # Enviar notificación de vencimiento
            BillingService.send_payment_notification(
                payment=payment,
                notification_type='overdue',
                recipient_email=payment.service_calculation.client_email,
                subject='Pago Vencido',
                message=f'El pago por {payment.amount} está vencido desde {payment.due_date}'
            )
            
            # Actualizar estado
            payment.status = 'overdue'
            payment.save()
        
        return overdue_payments

    @staticmethod
    def send_payment_receipt(payment):
        """
        Envía recibo de pago
        
        Args:
            payment: Instancia de PaymentSchedule
        """
        if payment.status != 'paid':
            return
        
        # Enviar notificación
        BillingService.send_payment_notification(
            payment=payment,
            notification_type='receipt',
            recipient_email=payment.service_calculation.client_email,
            subject='Recibo de Pago',
            message=f'Recibo por el pago de {payment.amount} realizado el {payment.paid_date}'
        )

    @staticmethod
    def get_payment_stats():
        """
        Obtiene estadísticas de pagos
        
        Returns:
            dict: Estadísticas de pagos
        """
        today = timezone.now().date()
        
        return {
            'total_pending': PaymentSchedule.objects.filter(
                status='pending'
            ).count(),
            'total_overdue': PaymentSchedule.objects.filter(
                status='overdue'
            ).count(),
            'total_paid': PaymentSchedule.objects.filter(
                status='paid'
            ).count(),
            'total_amount_pending': PaymentSchedule.objects.filter(
                status__in=['pending', 'sent']
            ).aggregate(
                total=Sum('amount')
            )['total'] or 0,
            'total_amount_overdue': PaymentSchedule.objects.filter(
                status='overdue'
            ).aggregate(
                total=Sum('amount')
            )['total'] or 0,
            'total_amount_paid': PaymentSchedule.objects.filter(
                status='paid'
            ).aggregate(
                total=Sum('amount')
            )['total'] or 0
        } 

    def create_order(
        self,
        client: Person,
        business_unit: BusinessUnit,
        service: Service,
        title: str,
        description: str,
        estimated_amount: Decimal,
        assigned_to: Optional[Person] = None,
        due_date: Optional[timezone.datetime] = None,
        requirements: List[str] = None,
        deliverables: List[str] = None,
        created_by: Optional[User] = None
    ) -> Order:
        """
        Crea una nueva orden de servicio.
        
        Args:
            client: Cliente que solicita el servicio
            business_unit: Unidad de negocio
            service: Servicio a prestar
            title: Título de la orden
            description: Descripción detallada
            estimated_amount: Monto estimado
            assigned_to: Persona asignada al trabajo
            due_date: Fecha de vencimiento
            requirements: Lista de requisitos
            deliverables: Lista de entregables
            created_by: Usuario que crea la orden
            
        Returns:
            Order: Orden creada
        """
        with transaction.atomic():
            order = Order.objects.create(
                client=client,
                business_unit=business_unit,
                service=service,
                title=title,
                description=description,
                estimated_amount=estimated_amount,
                assigned_to=assigned_to,
                due_date=due_date,
                requirements=requirements or [],
                deliverables=deliverables or [],
                created_by=created_by
            )
            
            # Aplicar lógica de pricing si es necesario
            if service:
                pricing_data = self.pricing_service.get_pricing_strategy(service, business_unit)
                if pricing_data:
                    order.estimated_amount = pricing_data.get('final_price', estimated_amount)
                    order.save(update_fields=['estimated_amount'])
            
            return order
    
    def create_invoice_from_order(self, order: Order) -> Invoice:
        """
        Crea una factura a partir de una orden completada.
        
        Args:
            order: Orden completada
            
        Returns:
            Invoice: Factura creada
        """
        if order.status != 'completed':
            raise ValidationError("Solo se pueden facturar órdenes completadas")
        
        with transaction.atomic():
            # Crear pago asociado
            payment = Pago.objects.create(
                monto=order.actual_amount or order.estimated_amount,
                moneda=order.currency,
                estado='pendiente',
                fecha_creacion=timezone.now()
            )
            
            # Crear factura
            invoice = Invoice.objects.create(
                payment=payment,
                service=order.service,
                business_unit=order.business_unit,
                subtotal=order.actual_amount or order.estimated_amount,
                total_amount=order.actual_amount or order.estimated_amount,
                currency=order.currency,
                status='draft',
                created_by=order.created_by
            )
            
            # Crear concepto de factura
            LineItem.objects.create(
                invoice=invoice,
                service=order.service,
                description=order.title,
                quantity=1,
                unit_price=order.actual_amount or order.estimated_amount,
                subtotal=order.actual_amount or order.estimated_amount,
                total_amount=order.actual_amount or order.estimated_amount
            )
            
            # Actualizar estado de la orden
            order.status = 'invoiced'
            order.save(update_fields=['status'])
            
            # Calcular totales de la factura
            invoice.calculate_totals()
            
            return invoice
    
    def create_invoice(
        self,
        client: Person,
        business_unit: BusinessUnit,
        service: Service,
        amount: Decimal,
        description: str,
        line_items: List[Dict[str, Any]] = None,
        discount_coupon: Optional[DiscountCoupon] = None,
        created_by: Optional[User] = None
    ) -> Invoice:
        """
        Crea una factura directamente sin orden.
        
        Args:
            client: Cliente
            business_unit: Unidad de negocio
            service: Servicio facturado
            amount: Monto total
            description: Descripción de la factura
            line_items: Lista de conceptos
            discount_coupon: Cupón de descuento
            created_by: Usuario que crea la factura
            
        Returns:
            Invoice: Factura creada
        """
        with transaction.atomic():
            # Aplicar descuento si existe
            final_amount = amount
            discount_amount = Decimal('0')
            
            if discount_coupon and discount_coupon.is_valid():
                discount_amount = amount * (discount_coupon.discount_percentage / 100)
                final_amount = amount - discount_amount
                
                # Marcar cupón como usado
                discount_coupon.mark_as_used()
            
            # Crear pago
            payment = Pago.objects.create(
                monto=final_amount,
                moneda='MXN',
                estado='pendiente',
                fecha_creacion=timezone.now()
            )
            
            # Crear factura
            invoice = Invoice.objects.create(
                payment=payment,
                service=service,
                business_unit=business_unit,
                subtotal=amount,
                discount_amount=discount_amount,
                total_amount=final_amount,
                currency='MXN',
                status='draft',
                created_by=created_by
            )
            
            # Crear conceptos si se proporcionan
            if line_items:
                for item in line_items:
                    LineItem.objects.create(
                        invoice=invoice,
                        service=service,
                        description=item.get('description', ''),
                        quantity=item.get('quantity', 1),
                        unit_price=item.get('unit_price', 0),
                        subtotal=item.get('subtotal', 0),
                        total_amount=item.get('total_amount', 0)
                    )
            else:
                # Crear concepto por defecto
                LineItem.objects.create(
                    invoice=invoice,
                    service=service,
                    description=description,
                    quantity=1,
                    unit_price=amount,
                    subtotal=amount,
                    total_amount=final_amount
                )
            
            # Calcular totales
            invoice.calculate_totals()
            
            return invoice
    
    def process_payment(self, invoice: Invoice, payment_method: str, payment_data: Dict[str, Any]) -> bool:
        """
        Procesa el pago de una factura.
        
        Args:
            invoice: Factura a pagar
            payment_method: Método de pago
            payment_data: Datos del pago
            
        Returns:
            bool: True si el pago fue exitoso
        """
        try:
            with transaction.atomic():
                # Actualizar pago
                payment = invoice.payment
                payment.estado = 'pagado'
                payment.fecha_pago = timezone.now()
                payment.metodo_pago = payment_method
                payment.datos_pago = payment_data
                payment.save()
                
                # Marcar factura como pagada
                invoice.mark_as_paid()
                
                # Enviar a finanzas si está configurado
                if invoice.auto_send_to_finances:
                    invoice.send_to_finances()
                
                return True
                
        except Exception as e:
            # Registrar error
            invoice.audit_log.append({
                'timestamp': timezone.now().isoformat(),
                'action': 'payment_failed',
                'error': str(e),
                'payment_method': payment_method
            })
            invoice.save(update_fields=['audit_log'])
            return False
    
    def generate_invoice_pdf(self, invoice: Invoice) -> str:
        """
        Genera el PDF de una factura.
        
        Args:
            invoice: Factura
            
        Returns:
            str: Ruta del archivo PDF generado
        """
        # Implementar generación de PDF
        # Por ahora retornamos una ruta dummy
        return f"invoices/pdf/{invoice.invoice_number}.pdf"
    
    def generate_invoice_xml(self, invoice: Invoice) -> str:
        """
        Genera el XML CFDI de una factura.
        
        Args:
            invoice: Factura
            
        Returns:
            str: Contenido XML del CFDI
        """
        if not invoice.electronic_billing_enabled:
            return None
        
        # Implementar generación de XML CFDI
        # Por ahora retornamos un XML dummy
        xml_content = f"""
        <?xml version="1.0" encoding="UTF-8"?>
        <cfdi:Comprobante xmlns:cfdi="http://www.sat.gob.mx/cfd/3" 
                          Version="3.3" 
                          Fecha="{invoice.issue_date.strftime('%Y-%m-%dT%H:%M:%S')}"
                          Sello=""
                          NoCertificado=""
                          Certificado=""
                          SubTotal="{invoice.subtotal}"
                          Moneda="{invoice.currency}"
                          Total="{invoice.total_amount}"
                          TipoDeComprobante="I"
                          FormaPago="01"
                          MetodoPago="PUE"
                          LugarExpedicion="06500">
            <!-- Contenido del CFDI -->
        </cfdi:Comprobante>
        """
        
        invoice.cfdi_xml = xml_content
        invoice.save(update_fields=['cfdi_xml'])
        
        return xml_content
    
    def get_invoice_summary(self, business_unit: BusinessUnit, start_date: timezone.datetime, end_date: timezone.datetime) -> Dict[str, Any]:
        """
        Obtiene un resumen de facturas para un período.
        
        Args:
            business_unit: Unidad de negocio
            start_date: Fecha de inicio
            end_date: Fecha de fin
            
        Returns:
            Dict: Resumen de facturas
        """
        invoices = Invoice.objects.filter(
            business_unit=business_unit,
            issue_date__range=[start_date, end_date]
        )
        
        total_invoiced = sum(invoice.total_amount for invoice in invoices)
        total_paid = sum(invoice.total_amount for invoice in invoices if invoice.status == 'paid')
        total_pending = sum(invoice.total_amount for invoice in invoices if invoice.status == 'pending')
        
        return {
            'total_invoices': invoices.count(),
            'total_invoiced': total_invoiced,
            'total_paid': total_paid,
            'total_pending': total_pending,
            'payment_rate': (total_paid / total_invoiced * 100) if total_invoiced > 0 else 0,
            'invoices_by_status': {
                'draft': invoices.filter(status='draft').count(),
                'pending': invoices.filter(status='pending').count(),
                'paid': invoices.filter(status='paid').count(),
                'cancelled': invoices.filter(status='cancelled').count(),
            }
        }
    
    def get_order_summary(self, business_unit: BusinessUnit, start_date: timezone.datetime, end_date: timezone.datetime) -> Dict[str, Any]:
        """
        Obtiene un resumen de órdenes para un período.
        
        Args:
            business_unit: Unidad de negocio
            start_date: Fecha de inicio
            end_date: Fecha de fin
            
        Returns:
            Dict: Resumen de órdenes
        """
        orders = Order.objects.filter(
            business_unit=business_unit,
            requested_date__range=[start_date, end_date]
        )
        
        total_estimated = sum(order.estimated_amount for order in orders)
        total_actual = sum(order.actual_amount for order in orders if order.actual_amount)
        completed_orders = orders.filter(status='completed').count()
        
        return {
            'total_orders': orders.count(),
            'total_estimated': total_estimated,
            'total_actual': total_actual,
            'completed_orders': completed_orders,
            'completion_rate': (completed_orders / orders.count() * 100) if orders.count() > 0 else 0,
            'orders_by_status': {
                'draft': orders.filter(status='draft').count(),
                'pending': orders.filter(status='pending').count(),
                'approved': orders.filter(status='approved').count(),
                'in_progress': orders.filter(status='in_progress').count(),
                'completed': orders.filter(status='completed').count(),
                'cancelled': orders.filter(status='cancelled').count(),
            }
        } 