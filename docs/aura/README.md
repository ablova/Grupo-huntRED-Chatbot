# 🌟 AURA - Advanced User Relationship Analytics

> **Sistema de Inteligencia Relacional para huntRED**

[![AURA Status](https://img.shields.io/badge/AURA-Healthy-brightgreen)](https://github.com/huntRED/aura)
[![Python](https://img.shields.io/badge/Python-3.8+-blue)](https://python.org)
[![Django](https://img.shields.io/badge/Django-4.2+-green)](https://djangoproject.com)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

## 🎯 ¿Qué es AURA?

**AURA** es un sistema revolucionario de inteligencia relacional que utiliza **Graph Neural Networks (GNN)** y análisis multidimensional para mapear, analizar y optimizar redes profesionales.

### ✨ Características Principales

- 🧠 **Análisis de Redes Profesionales**: Construcción y análisis de grafos de relaciones
- 🤖 **Modelos GNN Avanzados**: Detección de comunidades, análisis de influencia y predicción de compatibilidad
- 🔌 **Conectores Externos**: Integración con LinkedIn, iCloud y otras plataformas
- 🌐 **APIs REST Completas**: Interfaz programática para integración
- 📊 **Dashboard Interactivo**: Visualización en tiempo real con gráficos avanzados
- ⚡ **Procesamiento Asíncrono**: Tareas de Celery para análisis pesados
- 🎨 **UI/UX Moderna**: Diseño responsive con animaciones fluidas

## 🚀 Instalación Rápida

### Prerrequisitos

```bash
# Python 3.8+
python --version

# Redis (para caché y Celery)
redis-server --version

# PostgreSQL (recomendado)
psql --version
```

### Instalación

```bash
# 1. Clonar el repositorio
git clone https://github.com/huntRED/Grupo-huntRED-Chatbot.git
cd Grupo-huntRED-Chatbot

# 2. Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus configuraciones

# 5. Ejecutar migraciones
python manage.py migrate

# 6. Crear superusuario
python manage.py createsuperuser

# 7. Iniciar servicios
redis-server &
celery -A ai_huntred worker -l info &
python manage.py runserver
```

### Variables de Entorno

```bash
# AURA Configuration
AURA_ENABLED=True
AURA_CACHE_TTL=3600
AURA_MAX_ANALYSIS_DEPTH=3

# External Connectors
LINKEDIN_API_KEY=your_linkedin_api_key
LINKEDIN_API_SECRET=your_linkedin_api_secret
ICLOUD_APPLE_ID=your_apple_id
ICLOUD_PASSWORD=your_app_specific_password

# GNN Models
GNN_MODEL_PATH=/path/to/models/
GNN_BATCH_SIZE=32
GNN_LEARNING_RATE=0.001

# Cache Configuration
REDIS_URL=redis://localhost:6379/0
CACHE_TTL=3600
```

## 📖 Guía de Uso

### 1. Dashboard Web

Accede al dashboard principal de AURA:

```bash
# Iniciar servidor
python manage.py runserver

# Navegar a
http://localhost:8000/ats/aura/dashboard/
```

**Características del Dashboard:**
- 📈 Métricas en tiempo real
- 🔍 Análisis rápido de personas
- 🏥 Estado de salud del sistema
- ⚡ Acciones rápidas
- 📊 Visualización de componentes

### 2. APIs REST

#### Análisis de Persona
```bash
# Obtener análisis completo
curl -X GET "http://localhost:8000/api/aura/person/123/" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Respuesta
{
  "aura_score": 0.85,
  "network_strength": 0.72,
  "reputation_score": 0.68,
  "key_connections": [...],
  "communities": [...],
  "recommendations": [...]
}
```

#### Construcción de Red
```bash
# Construir red profesional
curl -X POST "http://localhost:8000/api/aura/network/build/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "people_ids": [1, 2, 3, 4, 5],
    "include_external": true,
    "depth": 2
  }'
```

#### Verificación de Salud
```bash
# Verificar estado del sistema
curl -X GET "http://localhost:8000/api/aura/health/"

# Respuesta
{
  "overall_status": "healthy",
  "aura_engine": "healthy",
  "connectors": {
    "linkedin": "healthy",
    "icloud": "healthy"
  },
  "gnn_models": "healthy",
  "database_connection": "healthy"
}
```

### 3. Uso Programático

```python
from app.aura.engine import AuraEngine

# Inicializar motor AURA
aura_engine = AuraEngine()

# Análisis de persona
analysis = aura_engine.analyze_person(person_id=123)
print(f"Aura Score: {analysis.aura_score}")
print(f"Network Strength: {analysis.network_strength}")

# Construcción de red
network = aura_engine.build_network(
    people_ids=[1, 2, 3, 4, 5],
    include_external=True,
    depth=2
)
print(f"Nodos: {network.node_count}")
print(f"Conexiones: {network.edge_count}")

# Análisis de compatibilidad
compatibility = aura_engine.analyze_compatibility(
    candidate_id=123,
    job_id=456
)
print(f"Score de Compatibilidad: {compatibility.score}")
```

### 4. Tareas Asíncronas

```python
from app.tasks.aura_tasks import (
    analyze_person_aura,
    build_network_graph,
    validate_person_data,
    sync_external_data
)

# Análisis asíncrono
task = analyze_person_aura.delay(person_id=123)
result = task.get()  # Esperar resultado

# Construcción de red asíncrona
task = build_network_graph.delay([1, 2, 3, 4, 5])
result = task.get()

# Validación de datos
task = validate_person_data.delay(person_id=123)
result = task.get()

# Sincronización externa
task = sync_external_data.delay()
result = task.get()
```

## 🏗️ Arquitectura

### Componentes Principales

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   APIs REST     │    │   Motor AURA    │
│   Dashboard     │◄──►│   Endpoints     │◄──►│   Principal     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Celery        │    │   Conectores    │    │   Modelos GNN   │
│   Tasks         │    │   Externos      │    │   & Analytics   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Cache         │    │   Base de       │    │   Visualización │
│   Redis         │    │   Datos         │    │   de Redes      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Estructura de Archivos

```
app/aura/
├── __init__.py
├── engine.py                 # Motor principal
├── graph_builder.py          # Constructor de grafos
├── analyzer.py               # Analizador de redes
├── cache.py                  # Gestor de caché
├── metrics.py                # Recolector de métricas
├── connectors/               # Conectores externos
│   ├── __init__.py
│   ├── linkedin_connector.py
│   └── icloud_connector.py
├── models/                   # Modelos GNN
│   ├── __init__.py
│   └── gnn/
│       ├── __init__.py
│       ├── community_detection.py
│       ├── influence_analysis.py
│       └── compatibility_prediction.py
└── visualization/            # Visualización
    ├── __init__.py
    └── network_viz.py

app/templates/ats/aura/       # Templates HTML
├── dashboard.html
├── person_detail.html
└── network_visualization.html

static/
├── css/aura-dashboard.css    # Estilos CSS
└── js/aura-dashboard.js      # JavaScript

docs/
├── technical/aura_documentation.md
└── aura/README.md
```

## 🧪 Testing

### Ejecutar Tests

```bash
# Tests unitarios
python manage.py test app.tests.test_aura

# Tests con cobertura
coverage run --source='app/aura' manage.py test app.tests.test_aura
coverage report
coverage html

# Tests de integración
python manage.py test app.tests.integration.test_aura_integration

# Tests de APIs
python manage.py test app.tests.test_aura.AuraAPITestCase
```

### Tests Disponibles

- ✅ **Tests Unitarios**: Componentes individuales
- ✅ **Tests de Integración**: Flujos completos
- ✅ **Tests de APIs**: Endpoints REST
- ✅ **Tests de Vistas**: Templates y contexto
- ✅ **Tests de Tareas**: Celery tasks
- ✅ **Tests de Conectores**: Integración externa

## 📊 Monitoreo y Métricas

### Métricas Disponibles

```python
from app.aura.metrics import MetricsCollector

metrics = MetricsCollector()

# Métricas del sistema
system_metrics = metrics.collect_system_metrics()
print(f"Personas analizadas: {system_metrics['total_people_analyzed']}")
print(f"Conexiones analizadas: {system_metrics['total_connections_analyzed']}")
print(f"Comunidades detectadas: {system_metrics['communities_detected']}")

# Métricas de rendimiento
performance_metrics = metrics.collect_performance_metrics()
print(f"Tiempo promedio de análisis: {performance_metrics['avg_analysis_time']}s")
print(f"Tasa de hit de caché: {performance_metrics['cache_hit_rate']}%")
```

### Logs

```bash
# Ver logs de AURA
tail -f logs/aura.log

# Logs de Celery
celery -A ai_huntred flower

# Logs de Redis
redis-cli monitor
```

## 🔧 Configuración Avanzada

### Modelos GNN

```python
# Configuración de modelos
GNN_CONFIG = {
    'community_detection': {
        'model_type': 'GraphSAGE',
        'hidden_channels': 128,
        'num_layers': 3,
        'dropout': 0.2
    },
    'influence_analysis': {
        'model_type': 'GAT',
        'heads': 8,
        'hidden_channels': 64
    },
    'compatibility_prediction': {
        'model_type': 'GCN',
        'hidden_channels': 256,
        'num_layers': 4
    }
}
```

### Caché Inteligente

```python
# Configuración de caché
CACHE_CONFIG = {
    'default_ttl': 3600,
    'analysis_ttl': 1800,
    'network_ttl': 7200,
    'metrics_ttl': 300,
    'health_ttl': 60
}
```

### Conectores Externos

```python
# Configuración de conectores
CONNECTOR_CONFIG = {
    'linkedin': {
        'api_version': 'v2',
        'rate_limit': 100,
        'timeout': 30
    },
    'icloud': {
        'sync_interval': 3600,
        'max_contacts': 10000
    }
}
```

## 🚀 Despliegue

### Docker

```dockerfile
# Dockerfile para AURA
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN python manage.py collectstatic --noinput

EXPOSE 8000
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "ai_huntred.wsgi:application"]
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - redis
      - postgres
    environment:
      - REDIS_URL=redis://redis:6379/0
      - DATABASE_URL=postgresql://user:pass@postgres:5432/aura

  redis:
    image: redis:alpine
    ports:
      - "6379:6379"

  celery:
    build: .
    command: celery -A ai_huntred worker -l info
    depends_on:
      - redis
      - postgres

  postgres:
    image: postgres:13
    environment:
      - POSTGRES_DB=aura
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

## 🤝 Contribución

### Guías de Contribución

1. **Fork** el repositorio
2. **Crea** una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. **Commit** tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. **Push** a la rama (`git push origin feature/AmazingFeature`)
5. **Abre** un Pull Request

### Estándares de Código

```bash
# Formatear código
black app/aura/
isort app/aura/

# Linting
flake8 app/aura/
pylint app/aura/

# Type checking
mypy app/aura/
```

### Tests

```bash
# Ejecutar todos los tests
python manage.py test

# Tests específicos
python manage.py test app.tests.test_aura.AuraEngineTestCase
python manage.py test app.tests.test_aura.AuraAPITestCase
```

## 📚 Documentación

### Enlaces Útiles

- 📖 [Documentación Técnica](docs/technical/aura_documentation.md)
- 🎯 [Guía de APIs](docs/technical/aura_documentation.md#apis-rest)
- 🧠 [Modelos GNN](docs/technical/aura_documentation.md#modelos-gnn)
- 🔌 [Conectores](docs/technical/aura_documentation.md#conectores)
- 🖥️ [Dashboard](docs/technical/aura_documentation.md#dashboard-web)

### Ejemplos

- [Ejemplo de Análisis](docs/examples/analysis_example.py)
- [Ejemplo de API](docs/examples/api_example.py)
- [Ejemplo de Dashboard](docs/examples/dashboard_example.py)

## 🐛 Troubleshooting

### Problemas Comunes

#### 1. Error de Conexión a Redis
```bash
# Verificar Redis
redis-cli ping
# Debe responder: PONG

# Reiniciar Redis
sudo systemctl restart redis
```

#### 2. Error en Modelos GNN
```python
# Verificar modelos
from app.aura.models.gnn import GNNModelManager
gnn_manager = GNNModelManager()
status = gnn_manager.check_models()
print(f"Status: {status}")
```

#### 3. Problemas de Caché
```python
# Limpiar caché
from app.aura.cache import CacheManager
cache_manager = CacheManager()
cache_manager.clear_all()
```

#### 4. Errores de Celery
```bash
# Verificar Celery
celery -A ai_huntred status

# Ver logs
celery -A ai_huntred flower
```

### Logs de Debug

```python
import logging

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('aura')

# Ver logs en tiempo real
tail -f logs/aura.log
```

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo [LICENSE](LICENSE) para más detalles.

## 👥 Equipo

- **Desarrollador Principal**: huntRED Team
- **Arquitecto de IA**: huntRED AI Team
- **Diseñador UX/UI**: huntRED Design Team

## 🙏 Agradecimientos

- **PyTorch Geometric** por las implementaciones de GNN
- **NetworkX** por el análisis de grafos
- **D3.js** por la visualización de redes
- **Celery** por el procesamiento asíncrono
- **Redis** por el sistema de caché

---

**AURA** - Revolucionando el análisis de redes profesionales con IA avanzada 🚀

*Desarrollado con ❤️ por el equipo de huntRED* 