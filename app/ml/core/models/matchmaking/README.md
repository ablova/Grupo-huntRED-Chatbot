# Sistema de Matchmaking - Arquitectura

## Estructura de Archivos

```
app/ml/core/models/matchmaking/
├── __init__.py         # Importaciones y configuración del módulo
├── factors.py          # Configuración y estructura de factores
├── factors_model.py    # Modelos de machine learning (PyTorch)
├── matchmaking.py      # Lógica principal de matchmaking
└── README.md           # Este archivo
```

## Separación de Responsabilidades

### 1. `factors.py` - Configuración y Estructura
**Propósito**: Define la estructura de datos y configuración de factores de matchmaking.

**Contenido**:
- `Factor`: Clase para definir factores individuales
- `FactorCategory`: Enum de categorías de factores
- `MatchmakingFactors`: Configuración de pesos y factores por business unit

**Características**:
- ✅ No requiere dependencias externas
- ✅ Siempre disponible
- ✅ Configuración por business unit
- ✅ Fácil de modificar y mantener

**Uso**:
```python
from app.ml.core.models.matchmaking import MatchmakingFactors

# Obtener factores para una business unit
factors = MatchmakingFactors.get_factors_for_business_unit('amigro')
```

### 2. `factors_model.py` - Modelos de Machine Learning
**Propósito**: Implementa los modelos de ML para matchmaking usando PyTorch.

**Contenido**:
- `FactorsMatchmakingModel`: Modelo principal de ML
- `FactorsEmbedder`: Generación de embeddings
- `FactorsEvaluator`: Evaluación de modelos

**Características**:
- 🔧 Requiere PyTorch (dependencia opcional)
- 🔧 Manejo de dependencias condicionales
- 🔧 Embeddings y procesamiento de características
- 🔧 Entrenamiento y predicción

**Uso**:
```python
from app.ml.core.models.matchmaking import FactorsMatchmakingModel, ML_AVAILABLE

if ML_AVAILABLE:
    model = FactorsMatchmakingModel()
    # Usar modelo...
else:
    # Fallback a lógica sin ML
    pass
```

### 3. `matchmaking.py` - Lógica Principal
**Propósito**: Lógica principal de matchmaking que coordina factores y modelos.

**Contenido**:
- `MatchmakingModel`: Clase base para matchmaking
- `MatchmakingEmbedder`: Clase base para embeddings
- Lógica de coordinación entre factores y ML

## Justificación de la Separación

### ✅ Ventajas de Mantener Separados

1. **Separación de Responsabilidades (SRP)**
   - Cada archivo tiene una responsabilidad específica
   - Cambios en configuración no afectan modelos ML
   - Actualizaciones de ML no modifican estructura de datos

2. **Dependencias Diferentes**
   - `factors.py`: Solo Python estándar
   - `factors_model.py`: Requiere PyTorch (pesado)
   - Permite importar configuración sin cargar ML

3. **Mantenibilidad**
   - Testing más fácil por separado
   - Debugging más sencillo
   - Código más legible y organizado

4. **Escalabilidad**
   - Múltiples implementaciones de ML posibles
   - Configuraciones flexibles por business unit
   - Fácil agregar nuevos factores

5. **Compatibilidad**
   - Funciona sin PyTorch (solo configuración)
   - Fallback graceful cuando ML no está disponible
   - Compatible con diferentes entornos

### ❌ Alternativa: Unificar en un solo archivo

**Problemas**:
- Archivo muy grande y difícil de mantener
- Dependencias pesadas siempre cargadas
- Difícil testing y debugging
- Violación del principio SRP
- Menos flexible para diferentes configuraciones

## Patrón de Uso Recomendado

```python
# 1. Importar configuración (siempre disponible)
from app.ml.core.models.matchmaking import MatchmakingFactors, ML_AVAILABLE

# 2. Obtener configuración de factores
factors = MatchmakingFactors.get_factors_for_business_unit('amigro')

# 3. Usar ML si está disponible
if ML_AVAILABLE:
    from app.ml.core.models.matchmaking import FactorsMatchmakingModel
    model = FactorsMatchmakingModel()
    # Lógica con ML...
else:
    # Lógica sin ML usando solo factores
    pass
```

## Modelos de Feedback

Los modelos de feedback en `app/models.py` también están correctamente separados:

- **`Feedback`** (línea 6104): Feedback interno del sistema (entrevistas, candidatos)
- **`ClientFeedback`** (línea 6539): Feedback de clientes externos (satisfacción)

Esta separación permite:
- Diferentes flujos de feedback
- Métricas específicas por tipo
- Reporting diferenciado
- Permisos y acceso diferentes

## Conclusión

La separación actual es **correcta y recomendada** porque:

1. ✅ Sigue principios SOLID
2. ✅ Mejora la mantenibilidad
3. ✅ Permite dependencias opcionales
4. ✅ Facilita testing y debugging
5. ✅ Es más escalable

**Recomendación**: Mantener la estructura actual y usar el patrón de importación condicional documentado. 