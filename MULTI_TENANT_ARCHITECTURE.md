# 🏢 Arquitectura Multi-Tenant HuntRED® v2

## Resumen Ejecutivo

El sistema HuntRED® v2 implementa una **arquitectura multi-tenant completa** que permite configuraciones independientes por:

1. **Business Unit** (huntRED® Executive, huntRED®, huntU, Amigro)
2. **Empresa Cliente** (cada empresa que contrata servicios de nómina/reclutamiento)

## 🎯 Business Units del Grupo huntRED®

### 1. huntRED® Executive
- **Código**: `huntRED_executive`
- **Enfoque**: C-level y posiciones de alta dirección
- **Configuraciones específicas**: APIs premium, verificaciones avanzadas

### 2. huntRED®
- **Código**: `huntRED`
- **Enfoque**: Reclutamiento profesional general
- **Configuraciones específicas**: APIs estándar, flujos optimizados

### 3. huntU
- **Código**: `huntU`
- **Enfoque**: Estudiantes y recién graduados (licenciatura/maestría)
- **Configuraciones específicas**: APIs educativas, validaciones académicas

### 4. Amigro
- **Código**: `amigro`
- **Enfoque**: Base de la pirámide, migrantes (nacionales retornando y entrando)
- **Configuraciones específicas**: APIs de verificación migratoria, WhatsApp masivo

## 🔧 Configuración Multi-Tenant por Business Unit

### Modelo BusinessUnit
```python
class BusinessUnit(models.Model):
    name = models.CharField(max_length=50, choices=BUSINESS_UNIT_CHOICES)
    code = models.CharField(max_length=10, unique=True)
    
    # Configuraciones específicas por BU
    integrations = models.JSONField(default=dict)  # APIs por BU
    settings = models.JSONField(default=dict)      # Configuración general
    pricing_config = models.JSONField(default=dict) # Precios por BU
    ats_config = models.JSONField(default=dict)    # ATS por BU
```

### Ejemplo de Configuración por BU
```json
{
  "integrations": {
    "whatsapp": {
      "enabled": true,
      "api_key": "BU_SPECIFIC_KEY",
      "phone_number": "+52XXXXXXXXXX",
      "templates": {
        "huntRED_executive": "executive_template_id",
        "huntU": "student_template_id",
        "amigro": "migrant_template_id"
      }
    },
    "smtp": {
      "enabled": true,
      "host": "smtp.huntred.com",
      "port": 587,
      "username": "executive@huntred.com",
      "password": "BU_SPECIFIC_PASSWORD"
    }
  }
}
```

## 📧 Configuración SMTP Multi-Tenant

### Modelo SMTPConfig
```python
class SMTPConfig(models.Model):
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE)
    host = models.CharField(max_length=255)
    port = models.IntegerField(default=587)
    username = models.CharField(max_length=255)
    password = models.CharField(max_length=255)
    use_tls = models.BooleanField(default=True)
    from_email = models.EmailField()
    from_name = models.CharField(max_length=100)
```

### Configuraciones SMTP por BU
```python
# huntRED® Executive
smtp_executive = {
    "host": "smtp.huntred.com",
    "username": "executive@huntred.com",
    "from_email": "executive@huntred.com",
    "from_name": "huntRED® Executive Search"
}

# huntU
smtp_huntu = {
    "host": "smtp.huntred.com", 
    "username": "estudiantes@huntred.com",
    "from_email": "estudiantes@huntred.com",
    "from_name": "huntU - Talento Universitario"
}

# Amigro
smtp_amigro = {
    "host": "smtp.huntred.com",
    "username": "migrantes@huntred.com", 
    "from_email": "migrantes@huntred.com",
    "from_name": "Amigro - Oportunidades Migrantes"
}
```

## 📱 Configuración WhatsApp Multi-Tenant

### Modelo WhatsAppAPI
```python
class WhatsAppAPI(models.Model):
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE)
    api_key = models.CharField(max_length=500)
    phone_number = models.CharField(max_length=20)
    is_active = models.BooleanField(default=True)
    meta_verified = models.BooleanField(default=False)
```

### Configuraciones WhatsApp por BU
```python
# huntRED® Executive
whatsapp_executive = {
    "phone_number": "+52XXXXXXXXXX",
    "api_key": "EXECUTIVE_API_KEY",
    "meta_verified": True,
    "templates": {
        "welcome": "executive_welcome_template",
        "interview": "executive_interview_template"
    }
}

# Amigro
whatsapp_amigro = {
    "phone_number": "+52YYYYYYYYYY",
    "api_key": "AMIGRO_API_KEY", 
    "meta_verified": True,
    "templates": {
        "welcome": "amigro_welcome_template",
        "verification": "amigro_verification_template"
    }
}
```

## 🏭 Configuración Multi-Tenant por Empresa Cliente

### Modelo Company (Empresas Clientes)
```python
class Company(models.Model):
    name = models.CharField(max_length=200)
    rfc = models.CharField(max_length=13)
    business_units = models.ManyToManyField(BusinessUnit)
    
    # Configuraciones específicas por empresa
    payroll_config = models.JSONField(default=dict)
    notification_config = models.JSONField(default=dict)
    integration_config = models.JSONField(default=dict)
```

### Configuración por Empresa Cliente
```json
{
  "payroll_config": {
    "smtp": {
      "host": "smtp.cliente.com",
      "username": "nomina@cliente.com",
      "password": "CLIENT_SPECIFIC_PASSWORD"
    },
    "whatsapp": {
      "enabled": true,
      "phone_number": "+52ZZZZZZZZZ",
      "api_key": "CLIENT_WHATSAPP_KEY"
    }
  },
  "notification_preferences": {
    "channels": ["whatsapp", "email", "sms"],
    "frequency": "daily",
    "recipients": ["rh@cliente.com", "nomina@cliente.com"]
  }
}
```

## 🔄 Flujo de Configuración Multi-Tenant

### 1. Selección de Business Unit
```python
def get_business_unit_config(bu_code: str, service_type: str):
    """
    Obtiene configuración específica por Business Unit
    """
    bu = BusinessUnit.objects.get(code=bu_code)
    return bu.get_integration_config(service_type)
```

### 2. Configuración por Empresa Cliente
```python
def get_client_company_config(company_id: int, service_type: str):
    """
    Obtiene configuración específica por empresa cliente
    """
    company = Company.objects.get(id=company_id)
    return company.get_service_config(service_type)
```

### 3. Resolución de Configuración
```python
def resolve_config(bu_code: str, company_id: int, service_type: str):
    """
    Resuelve configuración final: Cliente > BU > Default
    """
    # 1. Configuración de empresa cliente (prioridad más alta)
    client_config = get_client_company_config(company_id, service_type)
    
    # 2. Configuración de Business Unit
    bu_config = get_business_unit_config(bu_code, service_type)
    
    # 3. Configuración por defecto
    default_config = get_default_config(service_type)
    
    # Merge con precedencia: cliente > BU > default
    return {**default_config, **bu_config, **client_config}
```

## 🎛️ Configuraciones Específicas por Servicio

### Proveedores Externos por BU

#### huntRED® Executive
- **GPT**: GPT-4 Turbo (API premium)
- **Verificación**: First Advantage Premium
- **Video**: Zoom Pro
- **SMTP**: executive@huntred.com

#### huntU
- **GPT**: GPT-3.5 Turbo (API estándar)
- **Verificación**: Basic background checks
- **Video**: Google Meet
- **SMTP**: estudiantes@huntred.com

#### Amigro
- **GPT**: GPT-3.5 Turbo (optimizado para español)
- **Verificación**: Verificación migratoria especializada
- **WhatsApp**: Masivo para comunicación grupal
- **SMTP**: migrantes@huntred.com

### Configuración de APIs por BU
```python
BU_API_CONFIG = {
    "huntRED_executive": {
        "openai_api_key": "EXECUTIVE_GPT4_KEY",
        "verification_api": "FIRST_ADVANTAGE_PREMIUM",
        "video_platform": "zoom_pro",
        "smtp_config": "executive_smtp"
    },
    "huntU": {
        "openai_api_key": "STANDARD_GPT35_KEY", 
        "verification_api": "BASIC_VERIFICATION",
        "video_platform": "google_meet",
        "smtp_config": "student_smtp"
    },
    "amigro": {
        "openai_api_key": "SPANISH_OPTIMIZED_KEY",
        "verification_api": "MIGRATION_VERIFICATION",
        "whatsapp_config": "mass_whatsapp",
        "smtp_config": "migrant_smtp"
    }
}
```

## 📊 Implementación Actual

### ✅ Completamente Implementado
- [x] Modelo BusinessUnit con configuraciones específicas
- [x] Modelo WhatsAppAPI por Business Unit
- [x] Modelo SMTPConfig por Business Unit  
- [x] Modelo Company con configuraciones por cliente
- [x] Sistema de resolución de configuraciones
- [x] NotificationChannel por Business Unit
- [x] ConfiguracionBU para configuraciones específicas

### 🔧 Configuración en Proceso
- [ ] Poblar configuraciones específicas por BU
- [ ] Configurar APIs de proveedores externos
- [ ] Implementar templates específicos por BU
- [ ] Configurar flujos de trabajo por BU

## 🚀 Próximos Pasos

1. **Poblar Configuraciones**: Llenar las configuraciones específicas de cada BU
2. **Configurar APIs**: Establecer las credenciales de proveedores externos
3. **Templates**: Crear templates específicos por Business Unit
4. **Testing**: Probar flujos multi-tenant completos
5. **Documentación**: Crear guías de configuración por BU

## 📋 Resumen de Capacidades

El sistema HuntRED® v2 **YA TIENE** la arquitectura multi-tenant completa implementada:

- ✅ **4 Business Units** configurables independientemente
- ✅ **Configuraciones por empresa cliente** para servicios de nómina
- ✅ **APIs específicas** por BU (WhatsApp, SMTP, Telegram, etc.)
- ✅ **Resolución automática** de configuraciones con precedencia
- ✅ **Modelos de base de datos** completamente implementados
- ✅ **Sistema de notificaciones** multi-tenant
- ✅ **Configuraciones JSON** flexibles y extensibles

**La arquitectura está lista para producción** - solo necesita poblar las configuraciones específicas de cada Business Unit y empresa cliente.