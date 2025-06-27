# Guía de Integración de Pagos y Facturación Electrónica

## 📋 Resumen Ejecutivo

Este sistema proporciona una integración completa para:
- **Gateways de pago** (Stripe, PayPal, Conekta, bancos mexicanos)
- **Facturación electrónica CFDI** con timbrado automático
- **Procesamiento de webhooks** para confirmaciones automáticas
- **Gestión de cuentas bancarias** y transferencias
- **Configuración de PAC** (Proveedores Autorizados de Certificación)

---

## 🏗️ Arquitectura del Sistema

### Componentes Principales

```
📁 app/ats/payments/
├── 📄 models.py                    # Modelos de datos
├── 📄 admin.py                     # Interfaz de administración
├── 📄 views.py                     # Views del frontend
├── 📄 urls.py                      # Rutas de la aplicación
└── 📁 services/
    ├── 📄 payment_processing_service.py    # Procesamiento de pagos
    └── 📄 electronic_billing_service.py    # Facturación electrónica
```

### Modelos Clave

1. **PaymentGateway**: Configuración de gateways de pago
2. **BankAccount**: Cuentas bancarias
3. **PaymentTransaction**: Transacciones de pago
4. **PACConfiguration**: Configuración de PAC para facturación electrónica

---

## 💳 Gateways de Pago Soportados

### Gateways Internacionales
- **Stripe**: Tarjetas de crédito/débito, pagos internacionales
- **PayPal**: Pagos digitales, transferencias
- **Conekta**: Pagos en México, OXXO, transferencias
- **MercadoPago**: Pagos en Latinoamérica

### Bancos Mexicanos
- **Banorte**: Transferencias SPEI, pagos con tarjeta
- **Banamex**: Transferencias, pagos en línea
- **BBVA**: Transferencias, pagos digitales
- **HSBC**: Transferencias, pagos corporativos
- **Santander**: Transferencias, pagos empresariales

### Configuración de Gateway

```python
# Ejemplo: Configurar Stripe
gateway = PaymentGateway.objects.create(
    name="Stripe Production",
    gateway_type="stripe",
    status="active",
    api_key="sk_live_...",
    api_secret="sk_live_...",
    webhook_url="https://tu-dominio.com/webhook/stripe/",
    webhook_secret="whsec_...",
    supported_currencies=["MXN", "USD"],
    supported_payment_methods=["credit_card", "debit_card"],
    processing_fee_percentage=Decimal("2.9"),
    processing_fee_fixed=Decimal("0.30")
)
```

---

## 🏦 Gestión de Cuentas Bancarias

### Tipos de Cuenta
- **Cuenta Corriente**: Para operaciones diarias
- **Cuenta de Ahorro**: Para reservas
- **Cuenta Empresarial**: Para operaciones comerciales
- **Cuenta de Nómina**: Para pagos de personal

### Configuración de Cuenta

```python
# Ejemplo: Configurar cuenta bancaria
account = BankAccount.objects.create(
    account_name="Cuenta Principal HuntRED",
    account_number="1234567890",
    clabe="012345678901234567",
    account_type="business",
    bank="banorte",
    is_active=True,
    is_primary=True
)
```

---

## 📄 Facturación Electrónica CFDI

### Flujo Completo

1. **Generación de XML CFDI 3.3**
2. **Firma digital** con certificado SAT
3. **Timbrado** con PAC autorizado
4. **Generación de PDF** con QR
5. **Envío automático** al cliente

### Configuración de PAC

```python
# Ejemplo: Configurar Facturama
pac_config = PACConfiguration.objects.create(
    name="Facturama Production",
    pac_type="facturama",
    status="active",
    api_url="https://api.facturama.mx",
    api_key="tu_api_key",
    api_secret="tu_api_secret",
    username="tu_usuario",
    password="tu_password"
)
```

### PACs Soportados
- **Facturama**: Uno de los más populares en México
- **Solución Factible**: API robusta y confiable
- **Edicom**: Soluciones empresariales
- **SW**: Software de escritorio
- **Finkok**: Servicios en la nube

---

## 🔄 Flujo de Procesamiento de Pagos

### 1. Creación de Intención de Pago

```python
# Crear servicio de procesamiento
payment_service = PaymentProcessingService(business_unit)

# Crear intención de pago
result = payment_service.create_payment_intent(
    invoice=invoice,
    gateway=gateway,
    payment_method='credit_card',
    amount=invoice.total_amount
)
```

### 2. Confirmación de Pago

```python
# Procesar confirmación desde gateway
success = payment_service.process_payment_confirmation(
    transaction_id="TXN123456",
    gateway_data={
        'status': 'success',
        'payment_intent_id': 'pi_123456',
        'amount': '1160.00',
        'currency': 'MXN'
    }
)
```

### 3. Facturación Electrónica Automática

```python
# Procesar facturación electrónica
electronic_billing = ElectronicBillingService(business_unit)
result = electronic_billing.process_electronic_invoice(invoice)

if result['success']:
    print(f"UUID: {result['uuid']}")
    print(f"PDF: {result['pdf']}")
```

---

## 🔗 Webhooks

### Configuración de Webhooks

Los webhooks permiten confirmaciones automáticas de pagos:

```python
# URL del webhook
https://tu-dominio.com/payments/webhook/{gateway_id}/

# Ejemplo para Stripe
https://tu-dominio.com/payments/webhook/1/
```

### Eventos Soportados

- **payment_intent.succeeded**: Pago completado
- **payment_intent.payment_failed**: Pago fallido
- **charge.refunded**: Reembolso procesado

### Verificación de Seguridad

```python
def _verify_webhook_signature(request, gateway):
    """Verifica la firma del webhook para seguridad."""
    # Implementar verificación específica del gateway
    # Stripe: verificar firma con webhook_secret
    # PayPal: verificar certificado SSL
    return True
```

---

## 🛠️ Configuración en Admin

### 1. Configurar Gateway

1. Ir a **Admin > Gateways de Pago**
2. Crear nuevo gateway
3. Configurar API keys y webhooks
4. Establecer comisiones y métodos de pago

### 2. Configurar Cuenta Bancaria

1. Ir a **Admin > Cuentas Bancarias**
2. Agregar cuenta con datos bancarios
3. Marcar como cuenta principal si es necesario

### 3. Configurar PAC

1. Ir a **Admin > Configuraciones de PAC**
2. Crear configuración con datos del PAC
3. Subir certificados (.cer y .key)
4. Probar conexión

---

## 📊 Dashboard y Reportes

### Dashboard Principal

- **Transacciones totales**: Número de transacciones procesadas
- **Transacciones completadas**: Pagos exitosos
- **Monto total**: Suma de todos los pagos
- **Gateways activos**: Gateways configurados y funcionando

### Reportes Disponibles

1. **Reporte de Transacciones**
   - Filtros por fecha, gateway, método de pago
   - Exportación a Excel/CSV
   - Análisis de comisiones

2. **Reporte de Facturación Electrónica**
   - Facturas timbradas vs no timbradas
   - UUIDs generados
   - Estado de envío al SAT

3. **Reporte de Conciliación**
   - Conciliación de pagos con facturas
   - Diferencias y discrepancias
   - Ajustes contables

---

## 🔧 Integración con Frontend

### URLs Disponibles

```python
# Dashboard
/payments/dashboard/

# Gateways
/payments/gateways/
/payments/gateways/create/
/payments/gateways/{id}/

# Transacciones
/payments/transactions/
/payments/transactions/{transaction_id}/

# Facturación electrónica
/payments/electronic-billing/
/payments/electronic-billing/{invoice_id}/

# Procesamiento de pagos
/payments/process-payment/{invoice_id}/
```

### Ejemplo de Procesamiento de Pago

```html
<!-- Formulario de pago -->
<form method="POST" action="{% url 'payments:process_payment' invoice.id %}">
    {% csrf_token %}
    <select name="gateway" required>
        {% for gateway in available_gateways %}
            <option value="{{ gateway.id }}">{{ gateway.name }}</option>
        {% endfor %}
    </select>
    
    <select name="payment_method" required>
        <option value="credit_card">Tarjeta de Crédito</option>
        <option value="debit_card">Tarjeta de Débito</option>
        <option value="bank_transfer">Transferencia Bancaria</option>
    </select>
    
    <button type="submit">Procesar Pago</button>
</form>
```

---

## 🚀 Script de Demostración

### Ejecutar Demo

```bash
# Ejecutar script de demostración
python scripts/payment_integration_example.py
```

### Lo que demuestra el script:

1. **Configuración automática** de business unit, usuario, cliente
2. **Creación de gateway** de pago (Stripe demo)
3. **Configuración de cuenta bancaria**
4. **Configuración de PAC** (Facturama demo)
5. **Creación de factura** con líneas detalladas
6. **Procesamiento completo** de pago
7. **Facturación electrónica** automática
8. **Simulación de webhooks**
9. **Reportes finales**

---

## 🔒 Seguridad

### Mejores Prácticas

1. **API Keys**: Almacenar en variables de entorno
2. **Webhooks**: Verificar firmas siempre
3. **Certificados**: Proteger archivos .cer y .key
4. **HTTPS**: Usar siempre en producción
5. **Logs**: Registrar todas las transacciones

### Configuración de Seguridad

```python
# settings.py
PAYMENT_SETTINGS = {
    'WEBHOOK_SECRET': os.environ.get('WEBHOOK_SECRET'),
    'STRIPE_SECRET_KEY': os.environ.get('STRIPE_SECRET_KEY'),
    'PAC_CERTIFICATE_PATH': os.environ.get('PAC_CERTIFICATE_PATH'),
    'PAC_KEY_PATH': os.environ.get('PAC_KEY_PATH'),
}
```

---

## 📈 Monitoreo y Alertas

### Métricas a Monitorear

1. **Tasa de éxito** de transacciones
2. **Tiempo de respuesta** de gateways
3. **Errores de timbrado** con PAC
4. **Webhooks fallidos**
5. **Comisiones** por gateway

### Alertas Recomendadas

- Transacciones fallidas > 5%
- Tiempo de respuesta > 30 segundos
- Errores de timbrado consecutivos
- Webhooks no recibidos en 24h

---

## 🔄 Mantenimiento

### Tareas Programadas

1. **Limpieza de logs**: Eliminar logs antiguos
2. **Backup de transacciones**: Respaldo diario
3. **Verificación de certificados**: Renovación automática
4. **Sincronización con SAT**: Verificar estado de facturas

### Comandos de Mantenimiento

```bash
# Limpiar transacciones antiguas
python manage.py cleanup_old_transactions

# Verificar certificados
python manage.py check_certificates

# Sincronizar con SAT
python manage.py sync_sat_status
```

---

## 🆘 Solución de Problemas

### Problemas Comunes

1. **Error de firma webhook**
   - Verificar webhook_secret
   - Revisar formato de datos

2. **Error de timbrado PAC**
   - Verificar certificados
   - Revisar configuración de PAC
   - Validar XML CFDI

3. **Transacción fallida**
   - Revisar logs del gateway
   - Verificar configuración de API
   - Validar datos de pago

### Logs de Debug

```python
import logging

logger = logging.getLogger('payments')

# En servicios
logger.info(f"Procesando pago: {transaction_id}")
logger.error(f"Error en gateway: {error}")
```

---

## 📞 Soporte

### Contacto
- **Email**: soporte@huntred.com
- **Documentación**: docs.huntred.com
- **GitHub**: github.com/huntred/payments

### Recursos Adicionales
- [Documentación del SAT](https://www.sat.gob.mx/)
- [Guía CFDI 3.3](https://www.sat.gob.mx/cfd)
- [API Stripe](https://stripe.com/docs/api)
- [API PayPal](https://developer.paypal.com/)

---

## 🎯 Próximos Pasos

### Implementación en Producción

1. **Configurar certificados reales** (.cer y .key del SAT)
2. **Integrar con PAC real** (Facturama, Solución Factible, etc.)
3. **Configurar gateways de pago reales** (Stripe, PayPal, etc.)
4. **Implementar generación de PDF real** (ReportLab, WeasyPrint)
5. **Configurar envío de emails real** (SMTP, servicios de email)
6. **Configurar monitoreo y alertas**
7. **Implementar backup y recuperación**
8. **Configurar SSL/TLS** para webhooks
9. **Implementar rate limiting** para APIs
10. **Configurar logs centralizados**

### Optimizaciones Futuras

- **Pagos recurrentes** (suscripciones)
- **Pagos en cuotas** (financiamiento)
- **Integración con contabilidad** (asientos automáticos)
- **Reportes avanzados** (analytics, BI)
- **API pública** para integraciones externas
- **Mobile SDK** para apps móviles
- **Pagos offline** (OXXO, 7-Eleven)
- **Criptomonedas** (Bitcoin, Ethereum) 