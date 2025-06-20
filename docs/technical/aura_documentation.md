# AURA - Documentación Técnica

## 📋 Índice
1. [Visión General](#visión-general)
2. [Arquitectura del Sistema](#arquitectura-del-sistema)
3. [Componentes Principales](#componentes-principales)
4. [APIs REST](#apis-rest)
5. [Modelos GNN](#modelos-gnn)
6. [Conectores](#conectores)
7. [Dashboard Web](#dashboard-web)
8. [Tareas Asíncronas](#tareas-asíncronas)
9. [Configuración](#configuración)
10. [Guía de Uso](#guía-de-uso)
11. [Troubleshooting](#troubleshooting)

## 🎯 Visión General

**AURA (Advanced User Relationship Analytics)** es un sistema de inteligencia relacional que analiza redes profesionales utilizando modelos de Graph Neural Networks (GNN) y análisis multidimensional de compatibilidad.

### Características Principales
- **Análisis de Redes Profesionales**: Construcción y análisis de grafos de relaciones
- **Modelos GNN**: Detección de comunidades, análisis de influencia y predicción de compatibilidad
- **Conectores Externos**: Integración con LinkedIn, iCloud y otras plataformas
- **APIs REST**: Interfaz programática completa
- **Dashboard Web**: Visualización interactiva y análisis en tiempo real
- **Procesamiento Asíncrono**: Tareas de Celery para análisis pesados

## 🏗️ Arquitectura del Sistema

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

## 🔧 Componentes Principales

### 1. Motor Principal (`aura_engine.py`)
```python
class AuraEngine:
    """
    Motor principal de AURA que coordina todos los componentes
    """
    
    def __init__(self):
        self.graph_builder = GraphBuilder()
        self.connectors = ConnectorManager()
        self.gnn_models = GNNModelManager()
        self.analyzer = NetworkAnalyzer()
        self.cache = CacheManager()
```

**Funcionalidades:**
- Coordinación de análisis
- Gestión de caché
- Manejo de errores
- Logging y monitoreo

### 2. Constructor de Grafos (`graph_builder.py`)
```python
class GraphBuilder:
    """
    Construye grafos de red profesional desde múltiples fuentes
    """
    
    def build_network_graph(self, people_data, connections_data):
        """Construye grafo de red profesional"""
        
    def add_external_data(self, graph, external_data):
        """Añade datos de conectores externos"""
        
    def optimize_graph(self, graph):
        """Optimiza el grafo para análisis"""
```

### 3. Gestor de Conectores (`connectors/`)
```python
class ConnectorManager:
    """
    Gestiona conectores a plataformas externas
    """
    
    def __init__(self):
        self.linkedin_connector = LinkedInConnector()
        self.icloud_connector = iCloudConnector()
        self.connectors = {
            'linkedin': self.linkedin_connector,
            'icloud': self.icloud_connector
        }
```

## 🌐 APIs REST

### Endpoints Principales

#### Análisis de Personas
```http
GET /api/aura/person/{person_id}/
POST /api/aura/person/{person_id}/analyze/
GET /api/aura/person/{person_id}/network/
```

#### Análisis de Candidatos
```http
GET /api/aura/candidate/{candidate_id}/
POST /api/aura/candidate/{candidate_id}/match/
GET /api/aura/candidate/{candidate_id}/compatibility/
```

#### Análisis de Trabajos
```http
GET /api/aura/job/{job_id}/
POST /api/aura/job/{job_id}/analyze/
GET /api/aura/job/{job_id}/candidates/
```

#### Análisis de Redes
```http
GET /api/aura/network/insights/
GET /api/aura/network/communities/
GET /api/aura/network/influencers/
POST /api/aura/network/build/
```

#### Validaciones
```http
POST /api/aura/validate/person/{person_id}/
POST /api/aura/validate/candidate/{candidate_id}/
POST /api/aura/validate/job/{job_id}/
```

#### Métricas y Estado
```http
GET /api/aura/metrics/
GET /api/aura/health/
GET /api/aura/status/
```

### Ejemplos de Uso

#### Análisis Rápido de Persona
```python
import requests

# Análisis de persona
response = requests.get('/api/aura/person/123/')
data = response.json()

print(f"Aura Score: {data['aura_score']}")
print(f"Network Strength: {data['network_insights']['network_strength']}")
```

#### Construcción de Red
```python
# Construir red profesional
response = requests.post('/api/aura/network/build/', {
    'people_ids': [1, 2, 3, 4, 5],
    'include_external': True,
    'depth': 2
})
```

## 🧠 Modelos GNN

### 1. Modelo de Detección de Comunidades
```python
class CommunityDetectionModel:
    """
    Detecta comunidades en redes profesionales usando GNN
    """
    
    def __init__(self):
        self.model = self._build_model()
        
    def _build_model(self):
        """Construye modelo GNN para detección de comunidades"""
        return GraphSAGE(
            in_channels=64,
            hidden_channels=128,
            out_channels=32,
            num_layers=3
        )
```

### 2. Modelo de Análisis de Influencia
```python
class InfluenceAnalysisModel:
    """
    Analiza influencia de nodos en la red
    """
    
    def analyze_influence(self, graph, node_id):
        """Analiza influencia de un nodo específico"""
        
    def identify_influencers(self, graph, top_k=10):
        """Identifica top-k influenciadores"""
```

### 3. Modelo de Predicción de Compatibilidad
```python
class CompatibilityPredictionModel:
    """
    Predice compatibilidad entre candidatos y trabajos
    """
    
    def predict_compatibility(self, candidate_features, job_features):
        """Predice score de compatibilidad"""
        
    def get_compatibility_factors(self, candidate_id, job_id):
        """Obtiene factores de compatibilidad"""
```

## 🔌 Conectores

### LinkedIn Connector
```python
class LinkedInConnector:
    """
    Conector para LinkedIn API
    """
    
    def __init__(self):
        self.api_key = settings.LINKEDIN_API_KEY
        self.api_secret = settings.LINKEDIN_API_SECRET
        
    def get_profile_data(self, profile_url):
        """Obtiene datos de perfil de LinkedIn"""
        
    def get_connections(self, profile_id):
        """Obtiene conexiones de LinkedIn"""
        
    def get_company_data(self, company_id):
        """Obtiene datos de empresa"""
```

### iCloud Connector
```python
class iCloudConnector:
    """
    Conector para iCloud Contacts
    """
    
    def __init__(self):
        self.apple_id = settings.ICLOUD_APPLE_ID
        self.password = settings.ICLOUD_PASSWORD
        
    def get_contacts(self):
        """Obtiene contactos de iCloud"""
        
    def sync_contacts(self, local_contacts):
        """Sincroniza contactos locales con iCloud"""
```

## 🖥️ Dashboard Web

### Estructura de Templates
```
templates/ats/aura/
├── dashboard.html              # Dashboard principal
├── person_detail.html          # Detalle de persona
└── network_visualization.html  # Visualización de red
```

### Características del Dashboard
- **Métricas en Tiempo Real**: Actualización automática cada 5 minutos
- **Análisis Rápido**: Formulario para análisis inmediato
- **Estado de Componentes**: Monitoreo de salud del sistema
- **Visualización Interactiva**: Gráficos de red con D3.js y vis.js
- **Responsive Design**: Adaptable a móviles y tablets

### JavaScript Interactivo
```javascript
class AuraDashboard {
    constructor() {
        this.apiBase = '/api/aura/';
        this.init();
    }
    
    async analyzePerson() {
        // Análisis rápido de persona
    }
    
    async runHealthCheck() {
        // Verificación de salud del sistema
    }
    
    autoRefresh() {
        // Actualización automática de métricas
    }
}
```

## ⚡ Tareas Asíncronas

### Configuración de Celery
```python
# tasks/aura_tasks.py

@shared_task
def analyze_person_aura(person_id):
    """Análisis asíncrono de aura de persona"""
    
@shared_task
def build_network_graph(people_ids):
    """Construcción asíncrona de grafo de red"""
    
@shared_task
def validate_person_data(person_id):
    """Validación asíncrona de datos de persona"""
    
@shared_task
def sync_external_data():
    """Sincronización asíncrona de datos externos"""
```

### Colas de Trabajo
- **aura_analysis**: Análisis de personas y candidatos
- **aura_network**: Construcción y análisis de redes
- **aura_validation**: Validaciones de datos
- **aura_sync**: Sincronización con conectores externos

## ⚙️ Configuración

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

### Configuración de Django
```python
# settings/base.py

INSTALLED_APPS += [
    'app.aura',
]

# AURA Configuration
AURA_CONFIG = {
    'enabled': env.bool('AURA_ENABLED', default=True),
    'cache_ttl': env.int('AURA_CACHE_TTL', default=3600),
    'max_analysis_depth': env.int('AURA_MAX_ANALYSIS_DEPTH', default=3),
    'gnn_models': {
        'model_path': env('GNN_MODEL_PATH', default='models/'),
        'batch_size': env.int('GNN_BATCH_SIZE', default=32),
        'learning_rate': env.float('GNN_LEARNING_RATE', default=0.001),
    }
}
```

## 📖 Guía de Uso

### 1. Inicialización del Sistema
```python
from app.aura.engine import AuraEngine

# Inicializar motor AURA
aura_engine = AuraEngine()

# Verificar estado
health_status = aura_engine.check_health()
print(f"Estado: {health_status['overall_status']}")
```

### 2. Análisis de Persona
```python
# Análisis completo de persona
analysis = aura_engine.analyze_person(person_id=123)

print(f"Aura Score: {analysis.aura_score}")
print(f"Network Strength: {analysis.network_strength}")
print(f"Key Connections: {len(analysis.key_connections)}")
```

### 3. Construcción de Red
```python
# Construir red profesional
network = aura_engine.build_network(
    people_ids=[1, 2, 3, 4, 5],
    include_external=True,
    depth=2
)

print(f"Nodos: {network.node_count}")
print(f"Conexiones: {network.edge_count}")
print(f"Comunidades: {len(network.communities)}")
```

### 4. Análisis de Compatibilidad
```python
# Análisis de compatibilidad candidato-trabajo
compatibility = aura_engine.analyze_compatibility(
    candidate_id=123,
    job_id=456
)

print(f"Score de Compatibilidad: {compatibility.score}")
print(f"Factores: {compatibility.factors}")
```

### 5. Uso de APIs REST
```bash
# Análisis de persona
curl -X GET "http://localhost:8000/api/aura/person/123/"

# Construcción de red
curl -X POST "http://localhost:8000/api/aura/network/build/" \
  -H "Content-Type: application/json" \
  -d '{"people_ids": [1,2,3,4,5], "include_external": true}'

# Verificación de salud
curl -X GET "http://localhost:8000/api/aura/health/"
```

## 🔧 Troubleshooting

### Problemas Comunes

#### 1. Error de Conexión a Conectores
```python
# Verificar configuración de conectores
from app.aura.connectors import ConnectorManager

connector_manager = ConnectorManager()
linkedin_status = connector_manager.linkedin_connector.check_connection()
print(f"LinkedIn Status: {linkedin_status}")
```

#### 2. Error en Modelos GNN
```python
# Verificar modelos GNN
from app.aura.models.gnn import GNNModelManager

gnn_manager = GNNModelManager()
model_status = gnn_manager.check_models()
print(f"Model Status: {model_status}")
```

#### 3. Problemas de Caché
```python
# Limpiar caché
from app.aura.cache import CacheManager

cache_manager = CacheManager()
cache_manager.clear_all()
print("Cache limpiado")
```

#### 4. Errores de Tareas Asíncronas
```bash
# Verificar estado de Celery
celery -A ai_huntred status

# Ver logs de tareas
celery -A ai_huntred flower
```

### Logs y Monitoreo
```python
import logging

# Configurar logging para AURA
logger = logging.getLogger('aura')
logger.setLevel(logging.DEBUG)

# Ver logs en tiempo real
tail -f logs/aura.log
```

### Métricas de Rendimiento
```python
# Obtener métricas de rendimiento
from app.aura.metrics import MetricsCollector

metrics = MetricsCollector()
performance_metrics = metrics.get_performance_metrics()
print(f"Tiempo promedio de análisis: {performance_metrics['avg_analysis_time']}s")
```

## 🚀 Próximos Pasos

### Mejoras Planificadas
1. **Visualización 3D**: Implementar visualización 3D de redes
2. **Machine Learning Avanzado**: Modelos de deep learning más sofisticados
3. **Análisis Predictivo**: Predicción de movimientos en redes profesionales
4. **Integración con IA**: Integración con modelos de lenguaje para análisis de texto
5. **Mobile App**: Aplicación móvil para acceso en campo

### Optimizaciones
1. **Caché Inteligente**: Implementar caché predictivo
2. **Procesamiento Distribuido**: Distribuir análisis en múltiples nodos
3. **Compresión de Datos**: Optimizar almacenamiento de grafos
4. **API GraphQL**: Implementar GraphQL para consultas complejas

---

**AURA** - Sistema de Inteligencia Relacional de huntRED  
*Desarrollado con ❤️ para revolucionar el análisis de redes profesionales* 