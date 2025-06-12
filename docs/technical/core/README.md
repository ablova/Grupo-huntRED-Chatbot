# Módulo CORE

## Descripción General
El módulo CORE es el núcleo del sistema huntRED®, responsable de la gestión fundamental de vacantes, procesamiento de datos y sistema de eventos.

## Estructura del Módulo

### 1. Gestión de Vacantes (`app/core/vacancies/`)

#### 1.1 Modelos de Datos
- `Vacancy`: Modelo principal para gestión de vacantes
  - Campos principales:
    - `id`: Identificador único
    - `title`: Título de la vacante
    - `description`: Descripción detallada
    - `requirements`: Requisitos técnicos y funcionales
    - `status`: Estado actual (DRAFT, PUBLISHED, CLOSED, etc.)
    - `created_at`: Fecha de creación
    - `updated_at`: Fecha de última actualización
    - `business_unit`: Unidad de negocio asociada
    - `location`: Ubicación del puesto
    - `salary_range`: Rango salarial
    - `type`: Tipo de contrato (FULL_TIME, PART_TIME, etc.)

#### 1.2 Servicios
- `VacancyService`: Servicio principal de gestión de vacantes
  - Métodos principales:
    - `create_vacancy()`: Creación de nueva vacante
    - `update_vacancy()`: Actualización de vacante existente
    - `publish_vacancy()`: Publicación de vacante
    - `close_vacancy()`: Cierre de vacante
    - `get_vacancy_by_id()`: Obtención de vacante por ID
    - `search_vacancies()`: Búsqueda de vacantes

#### 1.3 Controladores
- `VacancyController`: Controlador REST para gestión de vacantes
  - Endpoints:
    - `POST /api/v1/vacancies`: Crear vacante
    - `PUT /api/v1/vacancies/{id}`: Actualizar vacante
    - `GET /api/v1/vacancies/{id}`: Obtener vacante
    - `GET /api/v1/vacancies`: Listar vacantes
    - `DELETE /api/v1/vacancies/{id}`: Eliminar vacante

### 2. Procesamiento de Datos (`app/core/data_processing/`)

#### 2.1 Pipeline de Datos
- `DataPipeline`: Pipeline principal de procesamiento
  - Componentes:
    - `DataValidator`: Validación de datos
    - `DataNormalizer`: Normalización de datos
    - `DataEnricher`: Enriquecimiento de datos
    - `DataStorage`: Almacenamiento de datos

#### 2.2 Validación
- `ValidationService`: Servicio de validación
  - Validaciones:
    - Formato de datos
    - Tipos de datos
    - Reglas de negocio
    - Integridad referencial

#### 2.3 Normalización
- `NormalizationService`: Servicio de normalización
  - Procesos:
    - Limpieza de datos
    - Estandarización de formatos
    - Corrección de errores
    - Enriquecimiento de datos

### 3. Sistema de Eventos (`app/core/events/`)

#### 3.1 Event Bus
- `EventBus`: Sistema de eventos
  - Características:
    - Publicación/Subscripción
    - Colas de eventos
    - Persistencia de eventos
    - Replay de eventos

#### 3.2 Eventos del Sistema
- Tipos de eventos:
  - `VacancyCreated`
  - `VacancyUpdated`
  - `VacancyPublished`
  - `VacancyClosed`
  - `ApplicationReceived`
  - `ApplicationStatusChanged`

#### 3.3 Handlers
- `EventHandler`: Manejadores de eventos
  - Funcionalidades:
    - Procesamiento de eventos
    - Notificaciones
    - Actualización de estado
    - Integración con servicios externos

## Flujos de Trabajo

### 1. Creación de Vacante
1. Validación de datos de entrada
2. Creación de registro en base de datos
3. Generación de eventos
4. Notificaciones a stakeholders

### 2. Publicación de Vacante
1. Validación de estado
2. Actualización de estado
3. Publicación en canales
4. Notificaciones

### 3. Procesamiento de Datos
1. Recepción de datos
2. Validación
3. Normalización
4. Almacenamiento
5. Notificación de eventos

## Integración con Otros Módulos

### 1. Machine Learning
- Integración con analizadores
- Procesamiento de datos para ML
- Feedback de modelos

### 2. ATS
- Sincronización de estados
- Compartir datos de candidatos
- Actualización de procesos

## Configuración

### 1. Variables de Entorno
```env
CORE_DB_HOST=localhost
CORE_DB_PORT=5432
CORE_DB_NAME=huntred_core
CORE_DB_USER=user
CORE_DB_PASSWORD=password
CORE_EVENT_BUS_HOST=localhost
CORE_EVENT_BUS_PORT=5672
```

### 2. Configuración de Servicios
```yaml
core:
  database:
    host: ${CORE_DB_HOST}
    port: ${CORE_DB_PORT}
    name: ${CORE_DB_NAME}
    user: ${CORE_DB_USER}
    password: ${CORE_DB_PASSWORD}
  events:
    host: ${CORE_EVENT_BUS_HOST}
    port: ${CORE_EVENT_BUS_PORT}
```

## Desarrollo

### 1. Requisitos
- Python 3.8+
- PostgreSQL 12+
- RabbitMQ 3.8+

### 2. Instalación
```bash
# Instalar dependencias
pip install -r requirements/core.txt

# Configurar base de datos
python manage.py migrate

# Iniciar servicios
python manage.py runserver
```

### 3. Testing
```bash
# Ejecutar tests unitarios
pytest tests/core/unit

# Ejecutar tests de integración
pytest tests/core/integration

# Ejecutar tests de sistema
pytest tests/core/system
```

## Monitoreo y Logging

### 1. Métricas
- Tiempo de respuesta
- Uso de recursos
- Tasa de errores
- Throughput

### 2. Logging
- Niveles de log
- Rotación de logs
- Búsqueda de logs
- Alertas

## Mantenimiento

### 1. Backup
- Frecuencia
- Retención
- Restauración

### 2. Actualizaciones
- Proceso de actualización
- Rollback
- Testing

## Seguridad

### 1. Autenticación
- JWT
- OAuth2
- API Keys

### 2. Autorización
- Roles
- Permisos
- ACL

### 3. Auditoría
- Logs de acceso
- Cambios de estado
- Acciones de usuarios 