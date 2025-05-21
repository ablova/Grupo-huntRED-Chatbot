# Guía de Migración para el Módulo de Valores

Este documento proporciona instrucciones para actualizar el código existente para usar el nuevo módulo de valores consolidado.

## Cambios Principales

1. **Estructura de Archivos**:
   - `/app/com/chatbot/values/` - Nuevo paquete que contiene la implementación consolidada
     - `__init__.py` - API pública del módulo
     - `core.py` - Clases y funcionalidad principal
     - `integrations.py` - Integraciones con el flujo del chatbot

2. **Clases y Funciones Renombradas/Eliminadas**:
   - `ValuesManager` → `ValuesPrinciples`
   - `EnhancedValuesIntegration` → Integrado en `ValuesPrinciples`
   - `ValuesIntegrator` → Integrado en `ValuesChatMiddleware`

## Pasos de Migración

### 1. Actualizar Importaciones

**Antes**:
```python
from app.com.chatbot.core.values import ValuesManager
from app.com.chatbot.core.values_enhanced import EnhancedValuesIntegration
from app.com.chatbot.core.values_integrations import ValuesChatMiddleware
```

**Después**:
```python
from app.com.chatbot.values import (
    ValuesPrinciples,
    ValuesChatMiddleware,
    values_principles,
    values_middleware
)
```

### 2. Actualizar Uso de Clases

**Antes**:
```python
manager = ValuesManager()
enhanced = EnhancedValuesIntegration()
```

**Después**:
```python
# Usar la instancia global o crear una nueva
principles = values_principles  # o ValuesPrinciples()
middleware = values_middleware  # o ValuesChatMiddleware(principles)
```

### 3. Actualizar Llamadas a Métodos

**Antes**:
```python
context = await ValuesIntegrator.detect_emotional_context(message)
response = await ValuesIntegrator.enhance_response(response, context)
```

**Después**:
```python
# Usando el middleware
result = await values_middleware.process_message(message_text, user_data)
response = await values_middleware.enhance_response(original_response, result['values_metadata'])
```

## Ejemplo Completo

**Antes**:
```python
from app.com.chatbot.core.values_integrations import ValuesChatMiddleware

class MyChatHandler:
    async def handle_message(self, message, user_data, state_manager):
        # Procesar mensaje
        processed = await ValuesChatMiddleware.process_message(
            message.text, 
            user_data, 
            state_manager
        )
        
        # Generar respuesta
        response = "Tu respuesta aquí"
        
        # Mejorar respuesta
        enhanced_response = await ValuesChatMiddleware.enhance_response(
            response, 
            state_manager
        )
        
        return enhanced_response
```

**Después**:
```python
from app.com.chatbot.values import values_middleware

class MyChatHandler:
    async def handle_message(self, message, user_data, state_manager):
        # Procesar mensaje con el nuevo middleware
        processed = await values_middleware.process_message(
            message.text,
            user_data,
            state_manager
        )
        
        # Generar respuesta
        response = "Tu respuesta aquí"
        
        # Mejorar respuesta usando los metadatos de valores
        enhanced_response = await values_middleware.enhance_response(
            response,
            processed.get('values_metadata', {})
        )
        
        return enhanced_response
```

## Notas Adicionales

1. **Compatibilidad**: El nuevo módulo mantiene compatibilidad con la mayoría de las firmas de métodos existentes.

2. **Rendimiento**: La nueva implementación incluye optimizaciones de rendimiento, incluyendo un sistema de caché mejorado.

3. **Pruebas**: Se recomienda probar exhaustivamente las interacciones del chatbot después de la migración.

4. **Depuración**: Se ha mejorado el registro (logging) para facilitar la depuración de problemas.

Para obtener más ayuda, consulte la documentación del módulo o contacte al equipo de desarrollo.
