# Dashboard Avanzado para Consultores - Grupo huntRED®

## 📋 Descripción General

El Dashboard Avanzado para Consultores es una herramienta especializada que proporciona métricas personalizadas, insights de mercado y recomendaciones inteligentes para optimizar el rendimiento de los consultores de huntRED.

## 🎯 Características Principales

### 1. Métricas de Rendimiento Personalizadas
- **Score de Performance**: Puntuación general basada en conversiones, tiempo de contratación e ingresos
- **Tasa de Conversión**: Porcentaje de aplicaciones que resultan en contrataciones exitosas
- **Tiempo de Contratación**: Promedio de días desde la aplicación hasta la contratación
- **Ingresos Generados**: Total de ingresos generados por el consultor
- **Comparación con Equipo**: Posición del consultor respecto al equipo

### 2. Insights de Mercado en Tiempo Real
- **Análisis por Industria**: Tendencias y oportunidades por sector
- **Demanda de Talento**: Análisis de demanda de diferentes roles
- **Análisis de Salarios**: Comparación de rangos salariales por posición
- **Oportunidades Emergentes**: Nuevas tendencias y nichos de mercado

### 3. Analytics de Productividad
- **Actividades Diarias**: Seguimiento de aplicaciones, entrevistas y colocaciones
- **Tiempos de Respuesta**: Análisis de eficiencia en comunicación
- **Eficiencia por Canal**: Rendimiento en WhatsApp, email, LinkedIn, etc.
- **Tareas Completadas**: Seguimiento de objetivos y metas

### 4. Análisis de Competencia
- **Competidores Directos**: Análisis de la competencia en el mercado
- **Comparación de Servicios**: Diferenciación de servicios y propuestas
- **Análisis de Precios**: Estrategias de pricing de la competencia
- **Ventajas Competitivas**: Identificación de fortalezas únicas

### 5. Recomendaciones Inteligentes
- **Basadas en ML**: Recomendaciones personalizadas usando machine learning
- **Priorización**: Clasificación por impacto y esfuerzo requerido
- **Acciones Específicas**: Recomendaciones accionables y medibles
- **Seguimiento**: Tracking del progreso en las recomendaciones

## 🚀 Funcionalidades Avanzadas

### Dashboard Interactivo
```html
<!-- Ejemplo de uso del dashboard -->
<div class="consultant-dashboard">
    <div class="performance-score">
        <div class="score-circle">
            <div class="score-value">85</div>
        </div>
        <h5>Performance Score</h5>
    </div>
    
    <div class="metrics-grid">
        <!-- Métricas en tiempo real -->
    </div>
</div>
```

### APIs RESTful
```python
# Ejemplo de uso de las APIs
from app.ats.dashboard.consultant_advanced_dashboard import ConsultantAdvancedDashboard

# Inicializar dashboard
dashboard = ConsultantAdvancedDashboard(
    consultant_id="user_123",
    business_unit=business_unit
)

# Obtener métricas de rendimiento
performance_data = await dashboard.get_performance_metrics()

# Obtener recomendaciones
recommendations = await dashboard.get_recommendations()
```

### Endpoints Disponibles

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/consultant/dashboard/` | GET | Dashboard principal |
| `/consultant/api/performance/` | GET | Métricas de rendimiento |
| `/consultant/api/market-insights/` | GET | Insights de mercado |
| `/consultant/api/productivity/` | GET | Analytics de productividad |
| `/consultant/api/recommendations/` | GET | Recomendaciones |
| `/consultant/api/activities/` | GET | Actividades recientes |
| `/consultant/api/tasks/` | GET | Tareas próximas |
| `/consultant/api/action/` | POST | Ejecutar acciones |
| `/consultant/api/export/` | GET | Exportar datos |

## 📊 Métricas y KPIs

### Métricas de Rendimiento
- **Total de Aplicaciones**: Número de aplicaciones procesadas
- **Colocaciones Exitosas**: Contrataciones completadas
- **Tasa de Conversión**: (Colocaciones / Aplicaciones) × 100
- **Tiempo Promedio de Contratación**: Días desde aplicación hasta contratación
- **Ingresos Generados**: Total de ingresos por contrataciones

### Métricas de Productividad
- **Entrevistas Realizadas**: Número total de entrevistas
- **Tasa de Finalización**: Porcentaje de entrevistas completadas
- **Tiempo de Respuesta**: Promedio de horas para responder
- **Tareas Completadas**: Porcentaje de tareas finalizadas
- **Eficiencia por Canal**: Rendimiento en diferentes canales

### Métricas de Engagement
- **Actividad Reciente**: Número de actividades en el período
- **Interacciones con Candidatos**: Número de interacciones
- **Puntuación de Satisfacción**: Score de satisfacción de clientes
- **Nivel de Actividad**: Clasificación de actividad (bajo/medio/alto)

## 🎨 Personalización y Configuración

### Configuración de Métricas
```python
# Configurar métricas personalizadas
CUSTOM_METRICS = {
    'conversion_target': 20.0,  # Tasa de conversión objetivo
    'time_to_hire_target': 15,  # Días objetivo para contratación
    'response_time_target': 12,  # Horas objetivo de respuesta
    'revenue_target': 50000,     # Ingresos objetivo mensuales
}
```

### Personalización de Recomendaciones
```python
# Configurar tipos de recomendaciones
RECOMMENDATION_TYPES = {
    'performance': {
        'weight': 0.4,
        'threshold': 15.0,
        'actions': ['improve_screening', 'optimize_process']
    },
    'productivity': {
        'weight': 0.3,
        'threshold': 24.0,
        'actions': ['automate_responses', 'improve_followup']
    },
    'engagement': {
        'weight': 0.3,
        'threshold': 5.0,
        'actions': ['increase_activity', 'improve_communication']
    }
}
```

## 🔧 Instalación y Configuración

### 1. Instalar Dependencias
```bash
pip install -r requirements.txt
```

### 2. Configurar Base de Datos
```python
# settings.py
INSTALLED_APPS = [
    # ... otras apps
    'app.ats.dashboard',
]

# Configuración del dashboard
DASHBOARD_CONFIG = {
    'consultant_dashboard': {
        'enabled': True,
        'cache_ttl': 300,  # 5 minutos
        'refresh_interval': 600,  # 10 minutos
    }
}
```

### 3. Configurar URLs
```python
# urls.py
from django.urls import path, include

urlpatterns = [
    # ... otras URLs
    path('consultant/', include('app.urls.consultant_dashboard')),
]
```

### 4. Ejecutar Migraciones
```bash
python manage.py makemigrations
python manage.py migrate
```

## 📈 Uso y Ejemplos

### Ejemplo 1: Obtener Métricas de Rendimiento
```python
from app.ats.dashboard.consultant_advanced_dashboard import ConsultantAdvancedDashboard

async def get_consultant_performance(consultant_id: str):
    dashboard = ConsultantAdvancedDashboard(consultant_id=consultant_id)
    
    # Obtener métricas
    performance = await dashboard.get_performance_metrics()
    
    print(f"Tasa de conversión: {performance['conversion_rate']}%")
    print(f"Tiempo promedio: {performance['avg_time_to_hire_days']} días")
    print(f"Ingresos: ${performance['revenue_generated']}")
    
    return performance
```

### Ejemplo 2: Generar Recomendaciones
```python
async def generate_recommendations(consultant_id: str):
    dashboard = ConsultantAdvancedDashboard(consultant_id=consultant_id)
    
    # Obtener recomendaciones
    recommendations = await dashboard.get_recommendations()
    
    for rec in recommendations:
        print(f"Recomendación: {rec['title']}")
        print(f"Prioridad: {rec['priority']}")
        print(f"Acción: {rec['action']}")
        print(f"Impacto esperado: {rec['expected_impact']}")
    
    return recommendations
```

### Ejemplo 3: Análisis de Mercado
```python
async def analyze_market_insights(consultant_id: str):
    dashboard = ConsultantAdvancedDashboard(consultant_id=consultant_id)
    
    # Obtener insights de mercado
    market_data = await dashboard.get_market_insights()
    
    print(f"Score de mercado: {market_data['market_score']}")
    print(f"Oportunidades emergentes: {len(market_data['emerging_opportunities'])}")
    
    return market_data
```

## 🛠️ Comandos de Gestión

### Generar Insights para Consultores
```bash
# Generar insights para todos los consultores
python manage.py generate_consultant_insights

# Generar insights para un consultor específico
python manage.py generate_consultant_insights --consultant-id=123

# Generar insights para una unidad de negocio
python manage.py generate_consultant_insights --business-unit=huntRED

# Generar con recomendaciones
python manage.py generate_consultant_insights --generate-recommendations

# Exportar datos
python manage.py generate_consultant_insights --export-data

# Modo dry-run (sin cambios)
python manage.py generate_consultant_insights --dry-run
```

### Opciones del Comando
- `--consultant-id`: ID específico del consultor
- `--business-unit`: Unidad de negocio específica
- `--period`: Período de análisis (7d, 30d, 90d)
- `--generate-recommendations`: Generar recomendaciones
- `--export-data`: Exportar datos a archivo
- `--dry-run`: Ejecutar sin hacer cambios

## 📱 Interfaz de Usuario

### Características del Dashboard
- **Diseño Responsivo**: Adaptable a diferentes dispositivos
- **Tema Moderno**: Interfaz limpia y profesional
- **Gráficos Interactivos**: Visualizaciones dinámicas con Chart.js
- **Notificaciones en Tiempo Real**: Alertas y actualizaciones
- **Exportación de Datos**: Múltiples formatos (JSON, CSV, PDF)

### Componentes Principales
1. **Header con Score**: Puntuación general de performance
2. **Grid de Métricas**: KPIs principales en tarjetas
3. **Gráficos de Rendimiento**: Visualizaciones de tendencias
4. **Sidebar con Recomendaciones**: Lista de acciones sugeridas
5. **Actividades Recientes**: Timeline de actividades
6. **Tareas Próximas**: Lista de tareas pendientes

## 🔒 Seguridad y Permisos

### Control de Acceso
```python
# Verificar permisos de consultor
def is_consultant(user):
    return hasattr(user, 'is_consultant') and user.is_consultant

# Decorador para vistas
@login_required
@user_passes_test(is_consultant)
def consultant_dashboard(request):
    # Vista del dashboard
    pass
```

### Validación de Datos
- Verificación de permisos por consultor
- Validación de parámetros de entrada
- Sanitización de datos de salida
- Logging de actividades sensibles

## 📊 Integración con Otros Sistemas

### Integración con Calendly
```python
from app.ats.integrations.calendly_integration import CalendlyIntegration

# Sincronizar calendario
calendly = CalendlyIntegration(business_unit=business_unit)
result = await calendly.sync_calendar(user_uri)
```

### Integración con Zapier
```python
from app.ats.integrations.zapier_integration import ZapierIntegration

# Crear campaña de marketing
zapier = ZapierIntegration(business_unit=business_unit)
result = await zapier.create_marketing_campaign(
    campaign_name="Nuevos Candidatos",
    target_audience=candidates,
    campaign_type="email"
)
```

### Notificaciones Inteligentes
```python
from app.ats.integrations.notifications.intelligent_notifications import IntelligentNotificationService

# Enviar notificación inteligente
notification_service = IntelligentNotificationService(business_unit=business_unit)
result = await notification_service.send_intelligent_notification(
    recipient=consultant,
    notification_type="performance_update",
    context=performance_data
)
```

## 🚀 Optimización y Rendimiento

### Caché Inteligente
```python
# Configuración de caché
CACHE_CONFIG = {
    'performance_metrics': 600,      # 10 minutos
    'market_insights': 1800,         # 30 minutos
    'productivity_analytics': 900,   # 15 minutos
    'recommendations': 1200,         # 20 minutos
    'activities': 300,               # 5 minutos
    'tasks': 300,                    # 5 minutos
}
```

### Optimización de Consultas
- Uso de `select_related` y `prefetch_related`
- Consultas agregadas para métricas
- Paginación de resultados grandes
- Índices de base de datos optimizados

### Monitoreo de Rendimiento
```python
# Métricas de rendimiento
PERFORMANCE_METRICS = {
    'query_time_threshold': 1.0,     # segundos
    'cache_hit_rate_target': 0.8,    # 80%
    'response_time_target': 2.0,     # segundos
}
```

## 🐛 Troubleshooting

### Problemas Comunes

#### 1. Error de Permisos
```
Error: Acceso denegado
Solución: Verificar que el usuario tenga rol de consultor
```

#### 2. Datos No Cargados
```
Error: Error cargando datos
Solución: Verificar conexión a base de datos y permisos
```

#### 3. Caché No Funcionando
```
Error: Datos desactualizados
Solución: Limpiar caché y verificar configuración
```

### Logs y Debugging
```python
import logging

logger = logging.getLogger(__name__)

# Logging de errores
logger.error(f"Error en dashboard: {str(e)}")

# Logging de métricas
logger.info(f"Métricas calculadas: {metrics}")
```

## 📚 Recursos Adicionales

### Documentación Relacionada
- [Guía de Integración con Calendly](./calendly_integration.md)
- [Sistema de Notificaciones Inteligentes](./intelligent_notifications.md)
- [API de Recomendaciones](./recommendations_api.md)

### Enlaces Útiles
- [Documentación de Chart.js](https://www.chartjs.org/docs/)
- [Guía de Django REST Framework](https://www.django-rest-framework.org/)
- [Documentación de Redis](https://redis.io/documentation)

### Soporte
- **Email**: soporte@huntred.com
- **Slack**: #consultant-dashboard
- **Documentación**: docs.huntred.com

---

**Versión**: 1.0.0  
**Última Actualización**: {{ current_date }}  
**Autor**: Equipo huntRED® 