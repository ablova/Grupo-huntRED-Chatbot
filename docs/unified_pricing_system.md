# Sistema Unificado de Pricing & Pagos - Grupo huntRED®

## Resumen Ejecutivo

El Sistema Unificado de Pricing & Pagos es una solución integral que centraliza y unifica todos los aspectos relacionados con la gestión de precios, facturación y pagos en Grupo huntRED®. Este sistema integra los diferentes componentes existentes en una interfaz coherente y fácil de usar.

## Arquitectura del Sistema

### Componentes Principales

#### 1. Modelo Service (Nuevo)
- **Ubicación**: `app/models.py`
- **Propósito**: Modelo central para definir servicios ofrecidos por las unidades de negocio
- **Características**:
  - Tipos de servicio (reclutamiento, consultoría, análisis de talento, etc.)
  - Tipos de facturación (fijo, por hora, por día, por mes, por proyecto, porcentaje, recurrente)
  - Configuración de precios y características
  - Gestión de hitos de pago por defecto

#### 2. UnifiedPricingService
- **Ubicación**: `app/ats/pricing/services/unified_pricing_service.py`
- **Propósito**: Servicio principal que unifica toda la funcionalidad de pricing y pagos
- **Funcionalidades**:
  - Cálculo de precios con descuentos
  - Creación de programaciones de pago
  - Procesamiento de transacciones
  - Gestión de notificaciones
  - Dashboard de estadísticas

#### 3. Admin Unificado
- **Ubicación**: `app/ats/admin/pricing/unified_admin.py`
- **Propósito**: Interfaces administrativas para gestionar servicios y pagos
- **Características**:
  - Gestión de servicios
  - Administración de programaciones de pago
  - Control de pagos individuales
  - Dashboard de estadísticas

## Funcionalidades Principales

### 1. Gestión de Servicios

#### Creación de Servicios
```python
from app.models import Service, BusinessUnit
from app.ats.pricing.services import UnifiedPricingService

# Crear un servicio
service = Service.objects.create(
    name='Reclutamiento Especializado',
    description='Servicio completo de reclutamiento y selección',
    service_type='recruitment',
    billing_type='percentage',
    base_price=Decimal('15.00'),  # 15% del salario anual
    currency='MXN',
    business_unit=business_unit,
    features=['Análisis de perfil', 'Búsqueda de candidatos'],
    requirements=['Descripción de puesto', 'Perfil de competencias'],
    deliverables=['Reporte de candidatos', 'Evaluaciones técnicas']
)
```

#### Tipos de Servicio Disponibles
- `recruitment`: Reclutamiento Especializado
- `executive_search`: Búsqueda de Ejecutivos
- `talent_analysis`: Análisis de Talento 360°
- `consulting`: Consultoría de HR
- `outplacement`: Outplacement
- `training`: Capacitación
- `verification`: Verificación de Antecedentes
- `assessment`: Evaluación de Competencias

#### Tipos de Facturación
- `fixed`: Precio Fijo
- `hourly`: Por Hora
- `daily`: Por Día
- `monthly`: Por Mes
- `project`: Por Proyecto
- `percentage`: Porcentaje
- `recurring`: Recurrente

### 2. Cálculo de Precios

#### Cálculo Básico
```python
from app.ats.pricing.services import UnifiedPricingService

pricing_service = UnifiedPricingService()

# Calcular precio de un servicio
pricing = pricing_service.calculate_service_price(
    service=service,
    quantity=1,
    duration=20,  # Para servicios por hora/día/mes
    base_amount=Decimal('600000.00')  # Para servicios por porcentaje
)
```

#### Descuentos Aplicados
- **Descuento por Volumen**: 5% para 3+ unidades, 10% para 5+ unidades
- **Descuento por Lealtad**: Basado en historial del cliente
- **Descuento Estratégico**: Basado en estrategias de pricing
- **IVA**: 16% aplicado al subtotal final

### 3. Programación de Pagos

#### Creación de Programaciones
```python
# Crear programación de pagos
schedule = pricing_service.create_payment_schedule(
    service=service,
    client=client,
    total_amount=Decimal('90000.00'),
    payment_structure='standard'  # standard, extended, recurring
)
```

#### Estructuras de Pago Disponibles
- **Standard**: 25% anticipo + 75% final (30 días)
- **Extended**: 17.5% anticipo 1 + 17.5% anticipo 2 + 65% final
- **Recurring**: 35% anticipo + 32.5% pago 1 + 32.5% pago 2

### 4. Procesamiento de Pagos

#### Procesar un Pago
```python
# Procesar pago
transaction = pricing_service.process_payment(
    payment=payment,
    payment_method='TRANSFER',
    transaction_id='TXN_001',
    amount=Decimal('22500.00'),
    metadata={
        'payment_gateway': 'internal',
        'reference': 'REF_001'
    }
)
```

#### Estados de Pago
- `PENDING`: Pendiente
- `PAID`: Pagado
- `OVERDUE`: Vencido
- `FAILED`: Fallido
- `REFUNDED`: Reembolsado

### 5. Dashboard y Estadísticas

#### Obtener Estadísticas
```python
# Obtener datos del dashboard
stats = pricing_service.get_payment_dashboard_data(
    business_unit=business_unit,
    date_from=timezone.now().date() - timedelta(days=30),
    date_to=timezone.now().date()
)
```

#### Métricas Disponibles
- Total de pagos y montos
- Pagos realizados vs pendientes
- Pagos vencidos
- Programaciones activas vs completadas
- Estadísticas por unidad de negocio

## Integración con Componentes Existentes

### 1. Modelos Existentes Integrados
- `PaymentSchedule`: Programaciones de pago
- `Payment`: Pagos individuales
- `PaymentTransaction`: Transacciones de pago
- `PaymentNotification`: Notificaciones de pago
- `PaymentMilestone`: Hitos de pago
- `PricingCalculation`: Cálculos de pricing
- `PricingPayment`: Pagos de pricing

### 2. Servicios Existentes Integrados
- `BillingService`: Facturación y cobranza
- `ProgressiveBilling`: Facturación progresiva
- `VolumePricing`: Precios por volumen
- `RecurringServicePricing`: Precios de servicios recurrentes

## Uso en el Admin de Django

### 1. Gestión de Servicios
- Lista de servicios con filtros por tipo, estado y unidad de negocio
- Formulario completo para crear/editar servicios
- Vista de características, requisitos y entregables
- Configuración de precios y métodos de pago

### 2. Gestión de Pagos
- Lista de programaciones de pago con estadísticas
- Vista detallada de pagos individuales
- Acciones para marcar pagos como realizados
- Envío de recordatorios automáticos

### 3. Dashboard Integrado
- Estadísticas generales de servicios y pagos
- Métricas de pagos pendientes y vencidos
- Filtros por unidad de negocio y fechas
- Vista consolidada de transacciones

## Ejemplos de Uso

### Ejemplo 1: Servicio de Reclutamiento
```python
# 1. Crear servicio
recruitment_service = Service.objects.create(
    name='Reclutamiento Especializado',
    service_type='recruitment',
    billing_type='percentage',
    base_price=Decimal('15.00'),
    business_unit=huntred_bu
)

# 2. Calcular precio
pricing = pricing_service.calculate_service_price(
    service=recruitment_service,
    base_amount=Decimal('600000.00')  # Salario anual
)
# Resultado: 90,000 MXN (15% de 600,000)

# 3. Crear programación de pagos
schedule = pricing_service.create_payment_schedule(
    service=recruitment_service,
    client=client,
    total_amount=pricing['calculation']['total']
)
# Crea: 22,500 MXN (25%) + 67,500 MXN (75%)
```

### Ejemplo 2: Servicio de Consultoría
```python
# 1. Crear servicio
consulting_service = Service.objects.create(
    name='Consultoría de HR',
    service_type='consulting',
    billing_type='hourly',
    base_price=Decimal('800.00'),
    business_unit=huntred_bu
)

# 2. Calcular precio
pricing = pricing_service.calculate_service_price(
    service=consulting_service,
    duration=20  # 20 horas
)
# Resultado: 16,000 MXN + IVA

# 3. Crear programación de pagos
schedule = pricing_service.create_payment_schedule(
    service=consulting_service,
    client=client,
    total_amount=pricing['calculation']['total'],
    payment_structure='extended'
)
# Crea: 3 pagos escalonados
```

## Ventajas del Sistema Unificado

### 1. Centralización
- Un solo punto de entrada para todas las operaciones de pricing y pagos
- Eliminación de duplicación de código
- Consistencia en el manejo de datos

### 2. Flexibilidad
- Soporte para múltiples tipos de servicios y facturación
- Configuración personalizable por unidad de negocio
- Estructuras de pago flexibles

### 3. Escalabilidad
- Arquitectura modular que permite agregar nuevos tipos de servicios
- Sistema de plugins para integraciones externas
- Soporte para múltiples monedas y métodos de pago

### 4. Automatización
- Cálculo automático de precios con descuentos
- Generación automática de programaciones de pago
- Notificaciones automáticas de recordatorios

### 5. Transparencia
- Desglose detallado de precios
- Trazabilidad completa de transacciones
- Dashboard con métricas en tiempo real

## Próximos Pasos

### 1. Migración de Datos
- Migrar servicios existentes al nuevo modelo Service
- Consolidar programaciones de pago existentes
- Validar integridad de datos

### 2. Integración con Frontend
- Crear APIs REST para el sistema unificado
- Desarrollar interfaces de usuario modernas
- Implementar notificaciones en tiempo real

### 3. Funcionalidades Avanzadas
- Integración con pasarelas de pago externas
- Sistema de cupones y promociones
- Facturación automática
- Reportes avanzados

### 4. Optimización
- Caché de cálculos de precios
- Optimización de consultas de base de datos
- Monitoreo de rendimiento

## Conclusión

El Sistema Unificado de Pricing & Pagos representa un hito importante en la evolución de la plataforma de Grupo huntRED®. Al centralizar y unificar todos los aspectos relacionados con precios y pagos, el sistema proporciona una base sólida para el crecimiento futuro del negocio, mejorando la eficiencia operativa y la experiencia del usuario.

La arquitectura modular y las interfaces bien definidas permiten una fácil extensión y mantenimiento, mientras que la integración con componentes existentes asegura una transición suave y sin interrupciones en las operaciones actuales. 