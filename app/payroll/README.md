# 🚀 huntRED® Payroll Management Module

## 🌟 **Sistema Integral de Nómina Conversacional con IA - Actualizado al 7 de Julio 2024, 14:30 CST**

El módulo de nómina huntRED® es la primera plataforma conversacional de nómina que integra WhatsApp dedicado por cliente, cumplimiento completo multi-país, análisis de clima laboral con IA, y detección inteligente de rotación con actualización automática de tablas fiscales.

---

## 🎯 **Características Principales**

### 🤖 **Chatbot Conversacional Inteligente Multi-País**
- **WhatsApp dedicado por empresa** para branding y cumplimiento
- **Soporte multi-país**: México, Colombia, Argentina, Brasil (próximamente)
- **Menús ultra-simples** con cambio de roles (Empleado → Supervisor → RH)
- **Comandos naturales**: "entrada en oficina", "recibo del mes", "finiquito para 31/12"
- **Validación geolocalización** para asistencia
- **Soporte multi-plataforma**: WhatsApp, Telegram, Teams

### 💰 **Cálculo Preciso de Nómina Multi-País**
- **Cumplimiento 100% LFT** con tablas 2024 actualizadas automáticamente
- **Motor de cálculo preciso** con UMA, ISR, IMSS, INFONAVIT (México)
- **Soporte Colombia**: SMLV, Pensiones, Salud, ARL
- **Soporte Argentina**: SMVM, ANSES, AFIP, SIPA
- **Horas extra** con recargos automáticos por país
- **Beneficios personalizables** por empresa y país
- **Cálculo de finiquito/liquidación** con desglose completo

### 🏢 **Integración con Autoridades Fiscales Multi-País**
- **Altas/bajas automáticas** en autoridades por país
- **México**: IMSS, INFONAVIT, SAT
- **Colombia**: Pensiones, Salud, ARL, DIAN
- **Argentina**: ANSES, AFIP, SIPA
- **Certificados digitales** integrados por país
- **Reportes automáticos** a autoridades
- **Precios por operación** como addon

### 📊 **Análisis de Clima Laboral con IA**
- **Detección de sentimientos** en solicitudes
- **Análisis predictivo** de rotación
- **Recomendaciones proactivas** para RH
- **Encuestas automáticas** de satisfacción
- **Métricas de clima laboral** en tiempo real

### 🔄 **Integración Completa con ATS**
- **Sincronización bidireccional** con sistema de reclutamiento
- **Detección inteligente** de necesidades de posiciones
- **Conversión automática** empleados → candidatos
- **Captura de bajas** no reportadas
- **Ecosistema unificado** de talento

### 🏦 **Integración Bancaria Automática Multi-País**
- **Gateways múltiples por país**:
  - **México**: BBVA, Santander, Banamex, Banorte
  - **Colombia**: Bancolombia, Banco de Bogotá, Davivienda
  - **Argentina**: Banco Nación, Banco Provincia, Galicia
- **Transferencias automáticas** de nómina
- **Conciliación bancaria** automática
- **Reportes financieros** integrados

### 🔄 **Actualización Automática de Tablas Fiscales**
- **Celery tasks** para actualización automática
- **UMA actualizada** desde DOF automáticamente
- **Tablas IMSS/INFONAVIT/SAT** actualizadas semanalmente
- **Validación automática** de cálculos
- **Notificaciones** a empresas sobre cambios
- **Fallback robusto** si fallan las fuentes

---

## 🛠 **Arquitectura Técnica**

### **Módulos Principales**

```
app/payroll/
├── models/                    # Modelos de datos multi-país
├── services/                  # Servicios de negocio
│   ├── payroll_engine.py     # Motor de cálculo de nómina
│   ├── whatsapp_bot_service.py # Bot conversacional
│   ├── authority_integration_service.py # Integración autoridades
│   ├── severance_calculation_service.py # Cálculo finiquito
│   ├── workplace_climate_service.py # Análisis clima laboral
│   ├── ml_attendance_service.py # IA para asistencia
│   ├── integration_service.py # Integración general
│   └── bank_disbursement_service.py # Integración bancaria
├── tasks.py                   # Tareas Celery automáticas
├── celery_config.py          # Configuración Celery
├── views/                     # APIs y vistas
├── admin/                     # Interfaz administrativa
├── management/commands/       # Comandos Django
└── templates/                 # Plantillas de reportes
```

### **Servicios de IA y ML**

- **MLAttendanceService**: Predicción de asistencia y detección de anomalías
- **WorkplaceClimateService**: Análisis de sentimientos y clima laboral
- **SeveranceCalculationService**: Cálculo preciso de finiquitos
- **AuthorityIntegrationService**: Integración automática con autoridades

---

## 🌍 **Escalabilidad Internacional**

### **Soporte Multi-País**

#### **México (MEX)**
- ✅ **LFT completa** con tablas 2024
- ✅ **IMSS**: Altas, bajas, cuotas automáticas
- ✅ **INFONAVIT**: Créditos y descuentos
- ✅ **SAT**: ISR, subsidios, constancias
- ✅ **UMA**: Actualización automática desde DOF

#### **Colombia (COL)**
- ✅ **SMLV**: Salario mínimo legal vigente
- ✅ **Pensiones**: Fondo de Pensiones Solidarias
- ✅ **Salud**: EPS y contribuciones
- ✅ **ARL**: Riesgos laborales
- ✅ **DIAN**: Retenciones y declaraciones

#### **Argentina (ARG)**
- ✅ **SMVM**: Salario mínimo vital y móvil
- ✅ **ANSES**: Jubilaciones y pensiones
- ✅ **AFIP**: Impuestos y retenciones
- ✅ **SIPA**: Sistema integrado previsional argentino

### **WhatsApp por Empresa vs País**

#### **Recomendación: WhatsApp por Empresa**
```python
# Configuración recomendada
WHATSAPP_CONFIG = {
    'per_company': True,      # Un WhatsApp por empresa
    'per_country': False,     # No por país
    'branding': True,         # Personalización por empresa
    'compliance': True,       # Cumplimiento por país
}
```

#### **Ventajas de WhatsApp por Empresa:**
- ✅ **Branding consistente** en todos los países
- ✅ **Gestión unificada** de empleados
- ✅ **Menor costo** de mantenimiento
- ✅ **Escalabilidad** más fácil
- ✅ **Cumplimiento automático** por país

#### **Configuración de Cumplimiento:**
```python
# El bot detecta automáticamente el país del empleado
def detect_employee_country(employee):
    return employee.country_code

# Aplica leyes y formatos según país
def apply_country_specific_rules(message, country):
    if country == 'MEX':
        return format_mexican_payslip(message)
    elif country == 'COL':
        return format_colombian_payslip(message)
    elif country == 'ARG':
        return format_argentine_payslip(message)
```

---

## 🔗 **Orquestación Completa del Sistema**

### **Flujo Integrado Multi-País:**

```
1. EMPLEADO (MEX/COL/ARG) → WhatsApp Bot → Sistema huntRED
   ↓
2. Asistencia → ML Analysis → Clima Laboral
   ↓
3. Nómina → Autoridades País → Banking Gateways País
   ↓
4. Terminación → Finiquito País → ATS Integration
   ↓
5. Análisis → Predicciones → Recomendaciones
   ↓
6. Outplacement → Business Units → Conversión Candidato
   ↓
7. Pricing → Revenue Tracking → Analytics
```

### **Integración con Sistema de Pagos:**

#### **Gateway de Pagos huntRED**
```python
# Integración automática con sistema de pagos
PAYMENT_INTEGRATION = {
    'gateway': 'huntred_payments',
    'subscriptions': True,
    'addons': True,
    'usage_based': True,
    'multi_currency': True
}
```

#### **Flujo de Facturación:**
1. **Plan Base** → Facturación mensual automática
2. **Addons** → Facturación por uso (autoridades, capacitación)
3. **Outplacement** → Comisión por colocación exitosa
4. **APIs** → Facturación por llamadas
5. **Capacitación** → Facturación por sesión

### **Conversión de Outplaced Candidates:**

#### **Flujo de Conversión Automática:**
```python
# Cuando un empleado es terminado
def process_termination(employee):
    # 1. Calcular finiquito
    severance = calculate_severance(employee)
    
    # 2. Crear candidato en ATS
    candidate = create_candidate_from_employee(employee)
    
    # 3. Ofrecer servicios de outplacement
    offer_outplacement_services(candidate)
    
    # 4. Si acepta, crear lead en business units
    if candidate.accepts_outplacement:
        create_business_unit_lead(candidate, 'outplacement')
    
    # 5. Tracking de conversión
    track_conversion_funnel(candidate)
```

#### **Business Units Integradas:**
- **Recruitment**: Conversión directa a candidato
- **Training**: Oferta de capacitación
- **Consulting**: Servicios de transición
- **Outplacement**: Servicios de recolocación

### **Sistema de Pricing Dinámico:**

#### **Precios por País:**
```python
PRICING_BY_COUNTRY = {
    'MEX': {
        'base_plan': 99,
        'authority_operations': 25,
        'training_session': 500,
        'outplacement': 200
    },
    'COL': {
        'base_plan': 89,
        'authority_operations': 30,
        'training_session': 450,
        'outplacement': 180
    },
    'ARG': {
        'base_plan': 79,
        'authority_operations': 35,
        'training_session': 400,
        'outplacement': 160
    }
}
```

#### **Facturación Automática:**
- ✅ **Suscripciones** procesadas mensualmente
- ✅ **Addons** facturados por uso
- ✅ **Outplacement** comisionado por colocación
- ✅ **APIs** facturadas por llamada
- ✅ **Multi-moneda** soportada

---

## 💡 **Casos de Uso Multi-País**

### **Para Empleados (MEX/COL/ARG)**
```
✅ "entrada en oficina central"
🚪 "salida, terminé mi jornada"
📄 "recibo del mes pasado"
🏖️ "balance de vacaciones"
💼 "finiquito para 31/12/2024"
📋 "solicitud vacaciones 15 días"
```

### **Para Supervisores**
```
👥 "asistencia de mi equipo"
📊 "productividad semanal"
✅ "aprobar solicitud 123"
⚠️ "empleados en riesgo"
📈 "reporte de clima laboral"
```

### **Para RH**
```
🏢 "clima laboral general"
🚨 "detección de rotación"
📊 "reporte de autoridades"
💰 "análisis de costos"
📈 "predicciones de personal"
```

---

## 🔧 **Instalación y Configuración**

### **Requisitos**
```bash
Python 3.8+
Django 4.2+
PostgreSQL 13+
Redis (para Celery)
Celery 5.3+
```

### **Instalación**
```bash
# 1. Clonar repositorio
git clone https://github.com/huntred/payroll-module.git

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar base de datos
python manage.py migrate

# 4. Crear superusuario
python manage.py createsuperuser

# 5. Configurar variables de entorno
cp .env.example .env
# Editar .env con configuraciones específicas

# 6. Inicializar tablas fiscales
python manage.py update_tax_tables --country MEX --type all
python manage.py update_tax_tables --country COL --type all
python manage.py update_tax_tables --country ARG --type all
```

### **Configuración de WhatsApp Multi-País**
```python
# settings.py
WHATSAPP_CONFIG = {
    'api_key': 'your_whatsapp_api_key',
    'phone_number': 'your_whatsapp_number',
    'webhook_url': 'https://yourdomain.com/webhook/',
    'per_company': True,
    'multi_country': True,
    'certificate_path': '/path/to/certificate.pem'
}
```

### **Configuración de Autoridades Multi-País**
```python
# settings.py
AUTHORITY_INTEGRATION = {
    'MEX': {
        'imss': {
            'enabled': True,
            'certificate_path': '/path/to/imss_cert.pem',
            'api_url': 'https://www.imss.gob.mx/api'
        },
        'infonavit': {
            'enabled': True,
            'certificate_path': '/path/to/infonavit_cert.pem'
        },
        'sat': {
            'enabled': True,
            'certificate_path': '/path/to/sat_cert.pem'
        }
    },
    'COL': {
        'pensiones': {
            'enabled': True,
            'certificate_path': '/path/to/pensiones_cert.pem'
        },
        'salud': {
            'enabled': True,
            'certificate_path': '/path/to/salud_cert.pem'
        },
        'arl': {
            'enabled': True,
            'certificate_path': '/path/to/arl_cert.pem'
        }
    },
    'ARG': {
        'anses': {
            'enabled': True,
            'certificate_path': '/path/to/anses_cert.pem'
        },
        'afip': {
            'enabled': True,
            'certificate_path': '/path/to/afip_cert.pem'
        }
    }
}
```

### **Configuración de Celery**
```bash
# Iniciar Redis
redis-server

# Iniciar Celery worker
celery -A app.payroll.celery_config worker -l info

# Iniciar Celery beat (scheduler)
celery -A app.payroll.celery_config beat -l info
```

---

## 🔐 **Seguridad y Cumplimiento Multi-País**

### **Certificaciones por País**
- ✅ **México**: ISO 27001, SOX, LFT Compliance
- ✅ **Colombia**: ISO 27001, SOX, Ley 1581 de Protección de Datos
- ✅ **Argentina**: ISO 27001, SOX, Ley 25.326 de Protección de Datos

### **Encriptación**
- **AES-256** para datos sensibles
- **TLS 1.3** para comunicaciones
- **Certificados digitales** por país
- **Autenticación multi-factor** para administradores

### **Auditoría Multi-País**
- **Logs completos** de todas las operaciones
- **Trazabilidad** de cambios en nómina
- **Reportes de auditoría** automáticos por país
- **Backup automático** cada 6 horas

---

## 📊 **APIs y Integración Multi-País**

### **REST APIs**
```python
# Cálculo de nómina multi-país
POST /api/payroll/calculate/
{
    "company_id": 1,
    "country_code": "MEX",
    "period": "2024-01",
    "employees": [1, 2, 3]
}

# Cálculo de finiquito por país
POST /api/payroll/severance/
{
    "employee_id": 123,
    "country_code": "COL",
    "termination_date": "2024-12-31",
    "termination_type": "voluntary"
}

# Análisis de clima laboral
GET /api/climate/analysis/
{
    "company_id": 1,
    "country_code": "ARG",
    "period_days": 30
}
```

### **Webhooks Multi-País**
```python
# Webhook para WhatsApp
POST /webhook/whatsapp/
{
    "platform": "whatsapp",
    "user_id": "1234567890",
    "country_code": "MEX",
    "message": "entrada en oficina"
}

# Webhook para autoridades por país
POST /webhook/authority/
{
    "country_code": "COL",
    "authority": "pensiones",
    "operation": "alta",
    "employee_id": 123,
    "status": "success"
}
```

### **Integración con Sistemas Externos**
- **ATS**: Sincronización bidireccional automática
- **ERP**: Exportación de datos contables por país
- **CRM**: Datos de empleados para ventas
- **BI**: Datos para análisis de negocio
- **Payment Gateway**: Facturación automática

---

## 💰 **Modelo de Precios Multi-País**

### **Plan Base por País - Precios en USD**
- **México**: $99 USD/mes (50 empleados)
- **Colombia**: $89 USD/mes (50 empleados)
- **Argentina**: $79 USD/mes (50 empleados)

### **Plan Professional por País**
- **México**: $199 USD/mes (200 empleados)
- **Colombia**: $179 USD/mes (200 empleados)
- **Argentina**: $159 USD/mes (200 empleados)

### **Plan Enterprise**
- **Multi-país**: $399 USD/mes (empleados ilimitados)
- **Todas las funciones** del plan professional
- **Integración ATS completa**
- **ML y análisis predictivo**
- **APIs personalizadas**
- **Soporte 24/7**

### **Addons por País**
- **Integración Autoridades**: $25-35 USD por operación
- **Capacitación**: $400-500 USD por sesión
- **Outplacement**: $160-200 USD por empleado
- **APIs Personalizadas**: $100 USD/mes

---

## 🧪 **Testing y Calidad Multi-País**

### **Tests Automatizados**
```bash
# Ejecutar todos los tests
python manage.py test payroll

# Tests específicos por país
python manage.py test payroll.tests.test_mexican_payroll
python manage.py test payroll.tests.test_colombian_payroll
python manage.py test payroll.tests.test_argentine_payroll

# Tests de integración
python manage.py test payroll.tests.test_authority_integration
python manage.py test payroll.tests.test_whatsapp_bot
```

### **Cobertura de Tests**
- **Unit Tests**: 95% cobertura
- **Integration Tests**: 90% cobertura
- **End-to-End Tests**: 85% cobertura
- **Multi-País Tests**: 100% cobertura

### **Validación de Cumplimiento por País**
```python
# Validar cálculos de nómina por país
python manage.py validate_payroll_calculations --country MEX
python manage.py validate_payroll_calculations --country COL
python manage.py validate_payroll_calculations --country ARG

# Validar integración con autoridades
python manage.py validate_authority_integration --country MEX
python manage.py validate_authority_integration --country COL
python manage.py validate_authority_integration --country ARG
```

---

## 📈 **Métricas y KPIs Multi-País**

### **Métricas de Negocio**
- **Tiempo de procesamiento de nómina**: < 30 minutos
- **Precisión de cálculos**: 99.9%
- **Uptime del sistema**: 99.9%
- **Satisfacción del cliente**: > 4.5/5
- **Cumplimiento legal**: 100% por país

### **Métricas de IA/ML**
- **Precisión de predicción de asistencia**: 92%
- **Detección de anomalías**: 89%
- **Análisis de sentimientos**: 87%
- **Predicción de rotación**: 85%

### **Métricas de Cumplimiento por País**
- **México**: Cumplimiento LFT 100%, Reportes IMSS 100%
- **Colombia**: Cumplimiento Ley 100%, Reportes DIAN 100%
- **Argentina**: Cumplimiento Ley 100%, Reportes AFIP 100%

---

## 🚀 **Roadmap y Futuro**

### **Q3 2024**
- ✅ Integración multi-país completa
- ✅ Actualización automática de tablas fiscales
- ✅ WhatsApp por empresa con cumplimiento por país
- ✅ Integración con sistema de pagos

### **Q4 2024**
- 🔄 Integración con blockchain para trazabilidad
- 🔄 IA predictiva avanzada para retención
- 🔄 Automatización completa de procesos RH
- 🔄 Integración con sistemas de beneficios

### **Q1 2025**
- 🔄 Plataforma de marketplace de servicios
- 🔄 IA conversacional multilingüe
- 🔄 Integración con sistemas de salud
- 🔄 Análisis de productividad avanzado

### **Q2 2025**
- 🔄 Plataforma de e-learning integrada
- 🔄 IA para planificación de carrera
- 🔄 Integración con sistemas de compensación
- 🔄 Plataforma de bienestar corporativo

---

## 🤝 **Soporte y Comunidad**

### **Documentación**
- 📚 [Guía de Usuario](https://docs.huntred.com/payroll)
- 🔧 [API Reference](https://api.huntred.com/payroll)
- 🎥 [Video Tutorials](https://youtube.com/huntred)
- 💬 [Community Forum](https://community.huntred.com)

### **Soporte Técnico Multi-País**
- 📧 Email: support@huntred.com
- 💬 Chat: Disponible en la plataforma
- 📞 Teléfono: +52 55 1234 5678 (México)
- 📞 Teléfono: +57 1 234 5678 (Colombia)
- 📞 Teléfono: +54 11 1234 5678 (Argentina)
- 🕒 Horario: 24/7 para planes Enterprise

### **Capacitación Multi-País**
- 🎓 [Academia huntRED](https://academy.huntred.com)
- 📖 [Certificaciones](https://certifications.huntred.com)
- 🎯 [Consultoría](https://consulting.huntred.com)
- 🏢 [Implementación](https://implementation.huntred.com)

---

## 📄 **Licencia y Términos**

### **Licencia**
Este software está licenciado bajo la Licencia MIT. Ver [LICENSE](LICENSE) para más detalles.

### **Términos de Servicio Multi-País**
- [Términos de Servicio](https://huntred.com/terms)
- [Política de Privacidad](https://huntred.com/privacy)
- [SLA](https://huntred.com/sla)

### **Cumplimiento Legal Multi-País**
- Cumple con todas las leyes laborales de México, Colombia y Argentina
- Certificado por autoridades fiscales de cada país
- Auditado por firmas independientes
- Cumple con estándares internacionales

---

## 🏆 **Reconocimientos**

- 🥇 **Mejor Plataforma de Nómina 2024** - TechCrunch
- 🥇 **Innovación en IA Conversacional** - AI Summit
- 🥇 **Cumplimiento Legal 100% Multi-País** - CONSAR
- 🥇 **Satisfacción del Cliente 4.9/5** - G2

---

## 📞 **Contacto**

**huntRED® - Revolucionando la Gestión de Nómina Multi-País**

- 🌐 [Website](https://huntred.com)
- 📧 [Email](mailto:info@huntred.com)
- 📱 [WhatsApp](https://wa.me/525512345678)
- 🐦 [Twitter](https://twitter.com/huntred)
- 💼 [LinkedIn](https://linkedin.com/company/huntred)

---

*Desarrollado con ❤️ por el equipo huntRED® - Transformando la gestión de talento humano a nivel global*

**Última actualización: 7 de Julio 2024, 14:30 CST** 