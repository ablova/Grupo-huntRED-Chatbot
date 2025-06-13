from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from datetime import timedelta
from decimal import Decimal

from app.models import ServiceCalculation, PaymentSchedule, PaymentNotification, Payment

class BillingService:
    """
    Servicio para manejar la facturación y cobranza
    """
    
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
    ) -> ServiceCalculation:
        """
        Crea un nuevo cálculo de servicio y sus pagos asociados
        """
        # Calcular salario anual
        annual_salary = BillingService.calculate_annual_salary(monthly_salary, bonus_months)
        
        # Calcular honorarios totales
        total_fee = (annual_salary * Decimal(fee_percentage)) / Decimal('100')
        
        # Crear el cálculo
        service = ServiceCalculation.objects.create(
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
            Payment.objects.create(
                service=service,
                concept='retainer',
                amount=(total_fee * Decimal('25')) / Decimal('100'),
                due_date=timezone.now().date()
            )
            Payment.objects.create(
                service=service,
                concept='placement',
                amount=(total_fee * Decimal('75')) / Decimal('100'),
                due_date=timezone.now().date() + timezone.timedelta(days=30)
            )
        elif payment_structure == 'extended':
            # 17.5% x 2 Retainer + 65% Placement
            Payment.objects.create(
                service=service,
                concept='retainer',
                amount=(total_fee * Decimal('17.5')) / Decimal('100'),
                due_date=timezone.now().date()
            )
            Payment.objects.create(
                service=service,
                concept='retainer',
                amount=(total_fee * Decimal('17.5')) / Decimal('100'),
                due_date=timezone.now().date() + timezone.timedelta(days=15)
            )
            Payment.objects.create(
                service=service,
                concept='placement',
                amount=(total_fee * Decimal('65')) / Decimal('100'),
                due_date=timezone.now().date() + timezone.timedelta(days=30)
            )
        else:  # recurring
            # 35% Retainer + 65% Placement (3 pagos)
            Payment.objects.create(
                service=service,
                concept='retainer',
                amount=(total_fee * Decimal('35')) / Decimal('100'),
                due_date=timezone.now().date()
            )
            Payment.objects.create(
                service=service,
                concept='placement',
                amount=(total_fee * Decimal('32.5')) / Decimal('100'),
                due_date=timezone.now().date() + timezone.timedelta(days=30)
            )
            Payment.objects.create(
                service=service,
                concept='placement',
                amount=(total_fee * Decimal('32.5')) / Decimal('100'),
                due_date=timezone.now().date() + timezone.timedelta(days=60)
            )
        
        return service

    @staticmethod
    def create_payment_schedule(calculation: ServiceCalculation) -> list:
        """
        Crea el calendario de pagos según la estructura seleccionada
        
        Args:
            calculation: Instancia de ServiceCalculation
            
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
            list: Lista de notificaciones enviadas
        """
        today = timezone.now().date()
        overdue_payments = PaymentSchedule.objects.filter(
            due_date__lt=today,
            status__in=['pending', 'scheduled', 'sent']
        )
        
        notifications = []
        for payment in overdue_payments:
            # Actualizar estado
            payment.status = 'overdue'
            payment.save()
            
            # Enviar notificación
            notification = BillingService.send_payment_notification(
                payment=payment,
                notification_type='overdue',
                recipient_email=payment.service_calculation.client_email,
                subject=f'Pago Vencido - {payment.service_calculation.position}',
                message=f'''
                Estimado cliente,
                
                Le informamos que el pago programado para el {payment.due_date} está vencido.
                
                Detalles del pago:
                - Monto: ${payment.amount}
                - Tipo: {payment.get_payment_type_display()}
                - Fecha de vencimiento: {payment.due_date}
                
                Por favor, proceda con el pago lo antes posible.
                
                Saludos cordiales,
                Equipo huntRED
                '''
            )
            notifications.append(notification)
        
        return notifications

    @staticmethod
    def send_payment_receipt(payment):
        """
        Envía un recibo de pago al cliente
        """
        context = {
            'payment': payment,
            'service': payment.service,
            'company_name': settings.COMPANY_NAME,
            'company_email': settings.COMPANY_EMAIL,
            'company_phone': settings.COMPANY_PHONE,
            'company_address': settings.COMPANY_ADDRESS
        }
        
        # Renderizar el template del correo
        html_message = render_to_string('pricing/email/receipt.html', context)
        
        # Enviar el correo
        send_mail(
            subject=f'Recibo - {payment.get_concept_display()} - {payment.service.position}',
            message='',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.CLIENT_EMAIL],
            html_message=html_message
        )

    @staticmethod
    def get_payment_stats():
        """
        Obtiene estadísticas de pagos
        """
        payments = Payment.objects.all()
        
        return {
            'pending_total': sum(p.amount for p in payments.filter(status='pending')),
            'sent_total': sum(p.amount for p in payments.filter(status='sent')),
            'received_total': sum(p.amount for p in payments.filter(status='received')),
            'overdue_total': sum(p.amount for p in payments.filter(status='overdue')),
            'pending_payments': payments.filter(status='pending'),
            'sent_payments': payments.filter(status='sent'),
            'received_payments': payments.filter(status='received'),
            'overdue_payments': payments.filter(status='overdue')
        } 