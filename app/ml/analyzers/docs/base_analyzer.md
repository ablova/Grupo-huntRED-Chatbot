# Base Analyzer

## Descripción General
El BaseAnalyzer es la clase abstracta fundamental que proporciona la estructura base para todos los analizadores en el sistema de evaluación de Grupo huntRED®. Esta clase implementa funcionalidades comunes y define la interfaz que todos los analizadores especializados deben seguir.

## Características Principales

### 1. Sistema de Caché
- Tiempo de caché configurable (por defecto 1 hora)
- Generación automática de claves de caché
- Sistema de invalidación basado en datos
- Soporte para prefijos personalizados

### 2. Manejo de Errores
- Sistema de logging integrado
- Resultados por defecto en caso de error
- Validación de datos de entrada
- Mensajes de error descriptivos

### 3. Contexto de Unidad de Negocio
- Soporte para análisis contextualizado
- Manejo flexible de unidades de negocio
- Normalización de nombres de unidades

## Métodos Principales

### analyze(data: Dict, business_unit: Optional[BusinessUnit]) -> Dict
Método abstracto que debe ser implementado por todos los analizadores.

#### Parámetros:
- `data`: Diccionario con datos a analizar
- `business_unit`: Unidad de negocio opcional para contexto

### get_cache_key(data: Dict, prefix: str = "analysis") -> str
Genera una clave única para el sistema de caché.

### get_cached_result(data: Dict, prefix: str = "analysis") -> Optional[Dict]
Recupera resultados del caché si están disponibles.

### set_cached_result(data: Dict, result: Dict, prefix: str = "analysis") -> None
Almacena resultados en el caché.

### validate_input(data: Dict) -> Tuple[bool, str]
Valida que los datos de entrada cumplan con los requisitos mínimos.

## Implementación de Analizadores

### Estructura Básica
```python
from app.ml.analyzers.base_analyzer import BaseAnalyzer

class MiAnalizador(BaseAnalyzer):
    def __init__(self):
        super().__init__()
        self.cache_timeout = 7200  # 2 horas
        
    def get_required_fields(self) -> List[str]:
        return ['campo1', 'campo2']
        
    def analyze(self, data: Dict, business_unit: Optional[BusinessUnit] = None) -> Dict:
        # Implementación del análisis
        pass
```

## Mejoras Propuestas

### 1. Sistema de Métricas
- Implementar métricas de rendimiento
- Agregar telemetría
- Mejorar el sistema de logging

### 2. Validación de Datos
- Implementar validación con Pydantic
- Agregar validación de tipos más estricta
- Mejorar el manejo de casos edge

### 3. Sistema de Caché
- Implementar caché multinivel
- Mejorar la invalidación de caché
- Agregar sistema de versionado

### 4. Documentación
- Mejorar docstrings
- Agregar ejemplos de uso
- Documentar casos de uso comunes

## Consideraciones Técnicas

### Rendimiento
- Optimizado para análisis rápidos
- Sistema de caché eficiente
- Manejo de memoria optimizado

### Seguridad
- Validación de datos de entrada
- Manejo seguro de caché
- Logging seguro

### Extensibilidad
- Fácil de extender
- Interfaz clara
- Documentación completa

## Próximos Pasos
1. Implementar sistema de métricas
2. Mejorar validación de datos
3. Optimizar sistema de caché
4. Mejorar documentación
5. Agregar más ejemplos de uso 