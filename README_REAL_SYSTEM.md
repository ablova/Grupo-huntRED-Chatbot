# Ghuntred-v2 - Real HR Technology Platform

## 🎉 Sistema REAL con Base de Datos

Este es el sistema **REAL** de Ghuntred-v2 que incluye:

- ✅ **Base de datos PostgreSQL real** con SQLAlchemy
- ✅ **API endpoints funcionales** que persisten datos
- ✅ **Sistema de nómina real** con cálculos de México 2024
- ✅ **Bot de WhatsApp funcional** con autenticación de base de datos
- ✅ **Servicios de empleados reales** con CRUD completo
- ✅ **Reportes y analytics reales** con datos persistentes

## 🚀 Inicio Rápido

### 1. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 2. Configurar Base de Datos

Instalar PostgreSQL y crear la base de datos:

```sql
CREATE DATABASE ghuntred_db;
CREATE USER ghuntred WITH PASSWORD 'ghuntred_password';
GRANT ALL PRIVILEGES ON DATABASE ghuntred_db TO ghuntred;
```

### 3. Configurar Variables de Entorno

Copiar y configurar el archivo de entorno:

```bash
cp .env.example .env
# Editar .env con tus configuraciones
```

### 4. Inicializar y Ejecutar

```bash
python start_real_system.py
```

El script te preguntará si quieres inicializar la base de datos con datos de prueba.

## 📊 Datos de Prueba

El sistema crea automáticamente:

### 🏢 Empresa
- **HuntRED® México** (ID: huntred_mx)

### 👥 Empleados de Prueba

| Nombre | Email | Teléfono | Rol | Departamento |
|--------|-------|----------|-----|--------------|
| Carlos Rodríguez | carlos.rodriguez@huntred.com | +525512345678 | CEO | Dirección General |
| María González | maria.gonzalez@huntred.com | +525587654321 | HR Manager | Recursos Humanos |
| Juan Pérez | juan.perez@huntred.com | +525555123456 | IT Supervisor | Tecnología |
| Ana López | ana.lopez@huntred.com | +525555234567 | Senior Developer | Tecnología |
| Luis Martínez | luis.martinez@huntred.com | +525555345678 | Full Stack Developer | Tecnología |

### 💰 Registros de Nómina
- Cálculos reales con **México 2024 compliance**
- IMSS, ISR, INFONAVIT calculados correctamente
- Historial de pagos por empleado

## 🌐 API Endpoints Reales

### 👥 Empleados
```bash
# Listar empleados de la empresa
GET /api/v1/companies/huntred_mx/employees

# Obtener empleado específico
GET /api/v1/employees/{employee_id}

# Crear nuevo empleado
POST /api/v1/employees

# Actualizar empleado
PUT /api/v1/employees/{employee_id}

# Buscar empleados
GET /api/v1/employees/search/huntred_mx?query=Ana
```

### 💰 Nómina
```bash
# Calcular nómina de empleado
POST /api/v1/payroll/calculate

# Historial de nómina
GET /api/v1/payroll/history/{employee_id}

# Procesar nómina masiva
POST /api/v1/payroll/bulk-process/huntred_mx

# Resumen de nómina de empresa
GET /api/v1/payroll/summary/huntred_mx
```

### 💬 WhatsApp Bot
```bash
# Autenticar usuario por teléfono
POST /api/v1/whatsapp/authenticate/+525512345678

# Obtener recibo para WhatsApp
GET /api/v1/whatsapp/payslip/{employee_id}

# Webhook de WhatsApp
POST /api/v1/webhooks/whatsapp/huntred_mx
```

## 💬 Comandos del Bot de WhatsApp

### Comandos Básicos
- `hola` - Saludo inicial
- `menu` - Ver todas las opciones
- `recibo` - Ver último recibo de nómina
- `saldo` - Consultar información salarial
- `perfil` - Ver información personal
- `ayuda` - Obtener ayuda

### Comandos de Supervisores/HR
- `equipo` - Ver empleados a cargo
- `reportes` - Generar reportes ejecutivos

## 🧪 Pruebas del Sistema

### 1. Probar API de Empleados

```bash
# Listar empleados
curl http://localhost:8000/api/v1/companies/huntred_mx/employees

# Buscar empleado
curl "http://localhost:8000/api/v1/employees/search/huntred_mx?query=Carlos"
```

### 2. Probar Cálculo de Nómina

```bash
curl -X POST http://localhost:8000/api/v1/payroll/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "employee_id": "emp_001",
    "pay_period_start": "2024-01-01",
    "pay_period_end": "2024-01-31",
    "overtime_hours": 8,
    "bonuses": 2000
  }'
```

### 3. Probar Bot de WhatsApp

```bash
# Simular mensaje de WhatsApp
curl -X POST http://localhost:8000/api/v1/webhooks/whatsapp/huntred_mx \
  -H "Content-Type: application/json" \
  -d '{
    "From": "whatsapp:+525512345678",
    "Body": "recibo"
  }'
```

## 📋 Funcionalidades Implementadas

### ✅ Sistema de Empleados
- [x] CRUD completo de empleados
- [x] Búsqueda y filtrado
- [x] Jerarquía organizacional
- [x] Validación de datos
- [x] Carga masiva de empleados

### ✅ Sistema de Nómina
- [x] Cálculos México 2024 (UMA, IMSS, ISR)
- [x] Horas extra automáticas
- [x] Bonos y comisiones
- [x] Deducciones personalizadas
- [x] Historial de pagos
- [x] Reportes ejecutivos

### ✅ Bot de WhatsApp
- [x] Autenticación por teléfono
- [x] Consulta de recibos
- [x] Información personal
- [x] Comandos por rol
- [x] Reportes para managers

### ✅ Base de Datos
- [x] Modelos SQLAlchemy completos
- [x] Relaciones entre entidades
- [x] Migraciones automáticas
- [x] Datos de prueba
- [x] Respaldos automáticos

## 🔧 Configuración Avanzada

### Variables de Entorno Importantes

```env
# Base de datos
DATABASE_URL=postgresql://ghuntred:ghuntred_password@localhost:5432/ghuntred_db

# WhatsApp
WHATSAPP_VERIFY_TOKEN=tu_token_de_verificacion
WHATSAPP_ACCESS_TOKEN=tu_token_de_acceso

# Twilio (para WhatsApp)
TWILIO_ACCOUNT_SID=tu_account_sid
TWILIO_AUTH_TOKEN=tu_auth_token
```

### Estructura de la Base de Datos

```
companies
├── employees
│   ├── payroll_records
│   ├── attendance_records
│   └── overtime_requests
├── chat_sessions
├── chat_messages
└── system_settings
```

## 🐛 Solución de Problemas

### Error de Conexión a Base de Datos
```bash
# Verificar que PostgreSQL esté ejecutándose
sudo service postgresql status

# Verificar configuración en .env
cat .env | grep DATABASE_URL
```

### Error en Cálculos de Nómina
- Verificar que el empleado exista en la base de datos
- Confirmar que las fechas estén en formato ISO (YYYY-MM-DD)
- Revisar que el salario mensual sea válido

### Error en Bot de WhatsApp
- Verificar que el número de teléfono esté registrado
- Confirmar que el empleado pertenezca a la empresa correcta
- Revisar logs del servidor para errores específicos

## 📈 Monitoreo y Logs

### Health Check
```bash
curl http://localhost:8000/health
```

### Logs de la Aplicación
Los logs se muestran en la consola con información detallada de:
- Conexiones de base de datos
- Cálculos de nómina
- Mensajes de WhatsApp
- Errores del sistema

## 🚀 Despliegue en Producción

### 1. Configurar PostgreSQL
```bash
# Instalar PostgreSQL
sudo apt install postgresql postgresql-contrib

# Configurar base de datos
sudo -u postgres createdb ghuntred_production
sudo -u postgres createuser ghuntred_prod
```

### 2. Configurar Variables de Producción
```env
DATABASE_URL=postgresql://ghuntred_prod:secure_password@localhost:5432/ghuntred_production
DEBUG=false
LOG_LEVEL=WARNING
```

### 3. Ejecutar con Gunicorn
```bash
pip install gunicorn
gunicorn src.main_real:app -w 4 -k uvicorn.workers.UvicornWorker
```

## 📞 Soporte

Para soporte técnico:
- 📧 Email: soporte@huntred.com
- 🌐 Web: https://huntred.com
- 📱 WhatsApp: +52 55 1234 5678

---

## 🎯 Diferencias con el Sistema Anterior

| Aspecto | Sistema Anterior | Sistema REAL |
|---------|------------------|--------------|
| Base de Datos | Mocks en memoria | PostgreSQL real |
| Empleados | Datos hardcodeados | CRUD completo |
| Nómina | Cálculos simulados | México 2024 real |
| WhatsApp | Respuestas fijas | Datos de BD |
| Persistencia | No | Sí |
| Escalabilidad | Limitada | Empresarial |

¡Ahora tienes un sistema **REAL** que funciona con datos persistentes y cálculos reales!