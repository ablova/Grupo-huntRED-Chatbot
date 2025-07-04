# LinkedIn Profile Analyzer - Guía de Uso

## Descripción
El `LinkedInProfileAnalyzer` es un analizador avanzado de perfiles de LinkedIn que integra extracción robusta, anti-detección y análisis de datos de perfiles.

## Características Principales

### 🔒 Anti-Detección
- Rotación automática de User Agents (usa la lista `USER_AGENTS` de `app.models`)
- Delays aleatorios entre requests (8-18 segundos por defecto)
- Rate limiting inteligente
- Cache para evitar requests duplicados

### 📊 Análisis Avanzado
- Extracción completa de datos del perfil
- Análisis de distribución de habilidades
- Análisis de tendencias de experiencia
- Generación de resúmenes estructurados

### 🔄 Integración con Django
- Enriquecimiento automático de modelos `Person`
- Búsqueda y creación de personas
- Transacciones atómicas para consistencia

## Ubicación
```
app/ml/analyzers/linkedin_profile_analyzer.py
```

## Uso Básico

### 1. Análisis Simple de Perfil
```python
from app.ml.analyzers.linkedin_profile_analyzer import LinkedInProfileAnalyzer
from app.models import BusinessUnit

# Crear instancia
business_unit = BusinessUnit.objects.get(name='huntRED')
analyzer = LinkedInProfileAnalyzer(business_unit)

# Analizar perfil
profile_data = await analyzer.analyze_profile(
    "https://www.linkedin.com/in/ejemplo"
)

# Obtener resumen
summary = analyzer.generate_profile_summary(profile_data)
```

### 2. Análisis con Enriquecimiento de Persona
```python
from app.ml.analyzers.linkedin_profile_analyzer import analyze_linkedin_profile

# Analizar y enriquecer automáticamente
person = await analyze_linkedin_profile(
    "https://www.linkedin.com/in/ejemplo",
    business_unit=business_unit,
    enrich_person=True
)
```

### 3. Análisis en Lote
```python
from app.ml.analyzers.linkedin_profile_analyzer import batch_analyze_profiles

urls = [
    "https://www.linkedin.com/in/perfil1",
    "https://www.linkedin.com/in/perfil2",
    "https://www.linkedin.com/in/perfil3"
]

results = await batch_analyze_profiles(
    urls,
    business_unit=business_unit,
    max_concurrent=3
)
```

## Estructura de Datos

### LinkedInProfileData
```python
@dataclass
class LinkedInProfileData:
    profile_url: str
    personal_info: Dict[str, Any]
    about: Optional[str]
    experience: List[Dict[str, Any]]
    education: List[Dict[str, Any]]
    skills: List[str]
    contact_info: Dict[str, Any]
    languages: List[str]
    certifications: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    publications: List[Dict[str, Any]]
    projects: List[Dict[str, Any]]
    volunteer_experience: List[Dict[str, Any]]
    honors_awards: List[Dict[str, Any]]
    organizations: List[Dict[str, Any]]
    scraped_at: datetime
    metadata: Dict[str, Any]
```

## Métodos Principales

### analyze_profile()
Analiza un perfil de LinkedIn y devuelve datos estructurados.

**Parámetros:**
- `profile_url`: URL del perfil
- `force_refresh`: Si True, ignora el cache
- `extract_contact`: Si True, extrae información de contacto

### enrich_person()
Enriquece un modelo Person con datos del perfil.

**Parámetros:**
- `person`: Instancia de Person
- `profile_data`: Datos del perfil
- `update_existing`: Si True, actualiza campos existentes

### analyze_skills_distribution()
Analiza la distribución de habilidades del perfil.

### analyze_experience_trends()
Analiza tendencias en la experiencia laboral.

### generate_profile_summary()
Genera un resumen completo del perfil.

## Configuración

### Variables de Entorno
```bash
LINKEDIN_USERNAME=tu_usuario
LINKEDIN_PASSWORD=tu_password
LINKEDIN_CLIENT_ID=tu_client_id
LINKEDIN_CLIENT_SECRET=tu_client_secret
```

### Configuración en LINKEDIN_CONFIG
```python
LINKEDIN_CONFIG = {
    'MIN_DELAY': 8,           # Delay mínimo entre requests
    'MAX_DELAY': 18,          # Delay máximo entre requests
    'CACHE_TIMEOUT': 86400,   # Tiempo de cache (24 horas)
    'HEADLESS': True,         # Modo headless del navegador
    'MAX_RETRIES': 3,         # Máximo de reintentos
    'RETRY_DELAY': 5,         # Delay entre reintentos
}
```

## Integración con Otros Analizadores

El `LinkedInProfileAnalyzer` se integra perfectamente con otros analizadores del sistema:

```python
from app.ml.analyzers import LinkedInProfileAnalyzer, PersonalityAnalyzer

# Análisis combinado
linkedin_data = await linkedin_analyzer.analyze_profile(profile_url)
personality_data = await personality_analyzer.analyze(linkedin_data)

# Integrar resultados
combined_analysis = {
    'linkedin': linkedin_data,
    'personality': personality_data
}
```

## Manejo de Errores

El analizador incluye manejo robusto de errores:

- Reintentos automáticos con backoff exponencial
- Fallback a Selenium si Playwright falla
- Logging detallado de errores
- Cache para evitar requests fallidos repetidos

## Consideraciones de Rendimiento

- **Rate Limiting**: Respeta límites de LinkedIn automáticamente
- **Cache**: Evita requests duplicados
- **Concurrencia**: Soporte para análisis en lote con límites configurables
- **Memory**: Limpieza automática de recursos del navegador

## Ejemplos de Uso Avanzado

### Análisis con Métricas Personalizadas
```python
analyzer = LinkedInProfileAnalyzer(business_unit)
profile_data = await analyzer.analyze_profile(profile_url)

# Análisis de habilidades
skills_analysis = analyzer.analyze_skills_distribution(profile_data)
print(f"Total skills: {skills_analysis['total_skills']}")
print(f"Top skills: {skills_analysis['top_skills']}")

# Análisis de experiencia
exp_analysis = analyzer.analyze_experience_trends(profile_data)
print(f"Total positions: {exp_analysis['total_positions']}")
print(f"Industries: {exp_analysis['industries']}")
```

### Creación Automática de Personas
```python
# Buscar o crear persona automáticamente
person = await analyzer.find_or_create_person(profile_data, business_unit)

if person:
    # Enriquecer con datos del perfil
    await analyzer.enrich_person(person, profile_data)
    print(f"Persona enriquecida: {person.nombre}")
```

## Troubleshooting

### Problemas Comunes

1. **Error de autenticación**: Verificar credenciales de LinkedIn
2. **Rate limiting**: Aumentar delays en la configuración
3. **Elementos no encontrados**: LinkedIn cambió la estructura HTML
4. **Timeout**: Aumentar timeouts en la configuración

### Logs
El analizador genera logs detallados que incluyen:
- Requests realizados
- Errores encontrados
- Estadísticas de uso
- Información de cache

## Contribución

Para contribuir al desarrollo del analizador:

1. Mantener compatibilidad con la API existente
2. Agregar tests para nuevas funcionalidades
3. Documentar cambios en la API
4. Seguir las convenciones de código del proyecto 