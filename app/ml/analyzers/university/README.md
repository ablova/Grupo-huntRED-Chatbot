# Analizador de Universidades

Este módulo proporciona funcionalidades para analizar preferencias universitarias en descripciones de trabajo y CVs.

## Características

- Extracción de nombres de universidades
- Análisis de rankings universitarios
- Almacenamiento de preferencias
- Soporte para múltiples campus
- Integración con QS World University Rankings API

## Estructura

```
app/ml/analyzers/university/
├── __init__.py
├── analyzer.py
├── rankings.py
├── storage.py
└── tests.py
```

## Uso

```python
from app.ml.analyzers.university import UniversityAnalyzer

# Crear instancia del analizador
analyzer = UniversityAnalyzer()

# Analizar descripción de trabajo
result = await analyzer.analyze(job_description)

# Resultado incluye:
# - Universidades mencionadas
# - Rankings
# - Preferencias
# - Metadatos
```

## Modelos

### University

```python
class University(models.Model):
    name = models.CharField(max_length=255)
    normalized_name = models.CharField(max_length=255)
    abbreviations = models.JSONField(default=list)
    country = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    ranking_data = models.JSONField(default=dict)
```

### UniversityCampus

```python
class UniversityCampus(models.Model):
    university = models.ForeignKey(University, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
```

## API

### UniversityAnalyzer

- `analyze(job_description: str) -> Dict[str, Any]`: Analiza preferencias universitarias
- `_analyze_rankings(universities: List[Dict[str, Any]]) -> Dict[str, Any]`: Analiza rankings
- `_analyze_preferences(job_description: str) -> Dict[str, Any]`: Analiza preferencias

### UniversityRankingsAnalyzer

- `get_university_ranking(university_name: str) -> Dict[str, Any]`: Obtiene ranking
- `analyze_university_metrics(university_data: Dict[str, Any]) -> Dict[str, Any]`: Analiza métricas

### UniversityPreferenceStorage

- `store_for_analysis(data: Dict[str, Any]) -> None`: Almacena datos
- `get_university_data(university_name: str) -> Dict[str, Any]`: Obtiene datos

## Tests

```bash
pytest app/ml/analyzers/university/tests.py
```

## Configuración

1. Añadir `QS_UNIVERSITY_RANKINGS_API_KEY` en settings.py
2. Ejecutar migraciones
3. Poblar datos iniciales de universidades

## Próximos Pasos

1. Mejorar extracción de universidades
2. Implementar análisis de preferencias
3. Optimizar almacenamiento
4. Añadir más tests
5. Mejorar documentación 