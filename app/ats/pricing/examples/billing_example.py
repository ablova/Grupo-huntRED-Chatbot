"""
Ejemplo de uso del sistema completo de facturación, órdenes y contabilidad.
"""
from decimal import Decimal
from django.utils import timezone
from django.contrib.auth.models import User

from app.models import BusinessUnit, Person, Service, DiscountCoupon
from app.ats.pricing.services.billing_service import BillingService
from app.ats.pricing.services.discount_service import DiscountService
from app.ats.accounting.models import Account, Transaction, JournalEntry


def create_sample_billing_workflow():
    """
    Ejemplo completo del flujo de facturación:
    1. Crear orden de servicio
    2. Trabajar en la orden
    3. Completar orden y generar factura
    4. Procesar pago
    5. Registrar en contabilidad
    """
    
    # Obtener datos de ejemplo (asumiendo que existen)
    try:
        business_unit = BusinessUnit.objects.first()
        client = Person.objects.first()
        service = Service.objects.first()
        user = User.objects.first()
        
        if not all([business_unit, client, service, user]):
            print("❌ Faltan datos de ejemplo. Asegúrate de tener BusinessUnit, Person, Service y User creados.")
            return
        
    except Exception as e:
        print(f"❌ Error obteniendo datos de ejemplo: {e}")
        return
    
    # Inicializar servicios
    billing_service = BillingService()
    discount_service = DiscountService()
    
    print("🚀 Iniciando flujo de facturación...")
    
    # 1. CREAR ORDEN DE SERVICIO
    print("\n📋 1. Creando orden de servicio...")
    
    order = billing_service.create_order(
        client=client,
        business_unit=business_unit,
        service=service,
        title="Reclutamiento de Desarrollador Senior",
        description="Búsqueda y selección de desarrollador senior con experiencia en Python/Django",
        estimated_amount=Decimal('15000.00'),
        assigned_to=client,  # Por simplicidad, asignamos al cliente
        due_date=timezone.now() + timezone.timedelta(days=30),
        requirements=[
            "Experiencia en Python/Django",
            "Mínimo 5 años de experiencia",
            "Inglés intermedio"
        ],
        deliverables=[
            "CVs preseleccionados",
            "Evaluación técnica",
            "Candidato final recomendado"
        ],
        created_by=user
    )
    
    print(f"✅ Orden creada: {order.order_number}")
    print(f"   Estado: {order.get_status_display()}")
    print(f"   Monto estimado: ${order.estimated_amount:,.2f}")
    
    # 2. APROBAR Y TRABAJAR EN LA ORDEN
    print("\n🔧 2. Aprobando y trabajando en la orden...")
    
    order.approve()
    print(f"✅ Orden aprobada")
    
    order.start_work()
    print(f"✅ Trabajo iniciado")
    
    # Simular progreso
    print(f"   Progreso: {order.get_progress_percentage()}%")
    
    # 3. COMPLETAR ORDEN Y GENERAR FACTURA
    print("\n✅ 3. Completando orden y generando factura...")
    
    actual_amount = Decimal('14500.00')  # Monto real (menor al estimado)
    order.complete(actual_amount=actual_amount)
    
    print(f"✅ Orden completada")
    print(f"   Monto real: ${order.actual_amount:,.2f}")
    print(f"   Ahorro: ${order.estimated_amount - order.actual_amount:,.2f}")
    
    # La factura se genera automáticamente
    invoice = order.invoices.first()
    if invoice:
        print(f"✅ Factura generada: {invoice.invoice_number}")
        print(f"   Total: ${invoice.total_amount:,.2f}")
    
    # 4. APLICAR DESCUENTO (OPCIONAL)
    print("\n🎫 4. Aplicando descuento...")
    
    # Crear cupón de descuento
    discount_coupon = discount_service.generate_discount_coupon(
        user=user,
        discount_percentage=10,
        validity_hours=24,
        description="Descuento por primera compra"
    )
    
    print(f"✅ Cupón creado: {discount_coupon.code}")
    print(f"   Descuento: {discount_coupon.discount_percentage}%")
    print(f"   Válido hasta: {discount_coupon.expiration_date}")
    
    # 5. PROCESAR PAGO
    print("\n💳 5. Procesando pago...")
    
    payment_data = {
        'payment_method': 'credit_card',
        'card_last4': '1234',
        'transaction_id': 'TXN123456789'
    }
    
    success = billing_service.process_payment(
        invoice=invoice,
        payment_method='credit_card',
        payment_data=payment_data
    )
    
    if success:
        print("✅ Pago procesado exitosamente")
        print(f"   Estado de factura: {invoice.get_status_display()}")
    else:
        print("❌ Error procesando pago")
    
    # 6. REGISTRAR EN CONTABILIDAD
    print("\n📊 6. Registrando en contabilidad...")
    
    # Crear cuentas contables básicas si no existen
    cash_account, _ = Account.objects.get_or_create(
        code='1001',
        defaults={
            'name': 'Efectivo en Banco',
            'account_type': 'asset',
            'category': 'cash',
            'business_unit': business_unit,
            'created_by': user
        }
    )
    
    sales_account, _ = Account.objects.get_or_create(
        code='4001',
        defaults={
            'name': 'Ventas de Servicios',
            'account_type': 'revenue',
            'category': 'sales',
            'business_unit': business_unit,
            'created_by': user
        }
    )
    
    # Crear asiento contable
    journal_entry = JournalEntry.objects.create(
        business_unit=business_unit,
        entry_type='sale',
        description=f"Venta de servicio - Factura {invoice.invoice_number}",
        reference=invoice.invoice_number,
        created_by=user
    )
    
    # Crear transacciones del asiento
    Transaction.objects.create(
        journal_entry=journal_entry,
        debit_account=cash_account,
        credit_account=sales_account,
        amount=invoice.total_amount,
        description=f"Cobro por factura {invoice.invoice_number}",
        transaction_type='receipt',
        business_unit=business_unit,
        reference_type='invoice',
        reference_id=invoice.id,
        created_by=user
    )
    
    # Registrar el asiento
    journal_entry.post(user)
    
    print(f"✅ Asiento contable registrado: {journal_entry.entry_number}")
    print(f"   Débito: ${journal_entry.get_total_debits():,.2f}")
    print(f"   Crédito: ${journal_entry.get_total_credits():,.2f}")
    
    # 7. GENERAR REPORTES
    print("\n📈 7. Generando reportes...")
    
    # Resumen de facturas
    start_date = timezone.now() - timezone.timedelta(days=30)
    end_date = timezone.now()
    
    invoice_summary = billing_service.get_invoice_summary(business_unit, start_date, end_date)
    order_summary = billing_service.get_order_summary(business_unit, start_date, end_date)
    
    print("📊 Resumen de Facturas (últimos 30 días):")
    print(f"   Total facturas: {invoice_summary['total_invoices']}")
    print(f"   Total facturado: ${invoice_summary['total_invoiced']:,.2f}")
    print(f"   Total pagado: ${invoice_summary['total_paid']:,.2f}")
    print(f"   Tasa de pago: {invoice_summary['payment_rate']:.1f}%")
    
    print("\n📋 Resumen de Órdenes (últimos 30 días):")
    print(f"   Total órdenes: {order_summary['total_orders']}")
    print(f"   Total estimado: ${order_summary['total_estimated']:,.2f}")
    print(f"   Total real: ${order_summary['total_actual']:,.2f}")
    print(f"   Órdenes completadas: {order_summary['completed_orders']}")
    print(f"   Tasa de completado: {order_summary['completion_rate']:.1f}%")
    
    # 8. BALANCES DE CUENTAS
    print("\n💰 8. Balances de cuentas:")
    
    cash_balance = cash_account.get_balance_as_of_today()
    sales_balance = sales_account.get_balance_as_of_today()
    
    print(f"   Efectivo en Banco: ${cash_balance:,.2f}")
    print(f"   Ventas de Servicios: ${sales_balance:,.2f}")
    
    print("\n🎉 ¡Flujo de facturación completado exitosamente!")


def create_sample_invoice_with_discount():
    """
    Ejemplo de creación de factura directa con descuento.
    """
    print("\n" + "="*60)
    print("🎫 EJEMPLO: Factura directa con descuento")
    print("="*60)
    
    try:
        business_unit = BusinessUnit.objects.first()
        client = Person.objects.first()
        service = Service.objects.first()
        user = User.objects.first()
        
        if not all([business_unit, client, service, user]):
            print("❌ Faltan datos de ejemplo.")
            return
            
    except Exception as e:
        print(f"❌ Error obteniendo datos: {e}")
        return
    
    billing_service = BillingService()
    discount_service = DiscountService()
    
    # Crear cupón de descuento
    discount_coupon = discount_service.generate_discount_coupon(
        user=user,
        discount_percentage=15,
        validity_hours=48,
        description="Descuento especial por volumen"
    )
    
    # Crear factura con descuento
    invoice = billing_service.create_invoice(
        client=client,
        business_unit=business_unit,
        service=service,
        amount=Decimal('25000.00'),
        description="Servicio de consultoría HR - Paquete Premium",
        line_items=[
            {
                'description': 'Análisis de estructura organizacional',
                'quantity': 1,
                'unit_price': 15000.00,
                'subtotal': 15000.00,
                'total_amount': 15000.00
            },
            {
                'description': 'Diseño de políticas de compensación',
                'quantity': 1,
                'unit_price': 10000.00,
                'subtotal': 10000.00,
                'total_amount': 10000.00
            }
        ],
        discount_coupon=discount_coupon,
        created_by=user
    )
    
    print(f"✅ Factura creada: {invoice.invoice_number}")
    print(f"   Subtotal: ${invoice.subtotal:,.2f}")
    print(f"   Descuento: ${invoice.discount_amount:,.2f}")
    print(f"   Total: ${invoice.total_amount:,.2f}")
    print(f"   Cupón aplicado: {discount_coupon.code}")


if __name__ == "__main__":
    print("🏢 SISTEMA DE FACTURACIÓN HUNTRED")
    print("="*60)
    
    # Ejecutar ejemplos
    create_sample_billing_workflow()
    create_sample_invoice_with_discount()
    
    print("\n" + "="*60)
    print("✅ Todos los ejemplos completados")
    print("="*60) 