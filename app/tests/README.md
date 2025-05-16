# Tests de Grupo huntRED® AI System

## Configuración Centralizada

Se ha implementado un archivo de configuración centralizada para todos los tests:
`app/tests/test_config.py`

Este archivo contiene los datos de contacto para pruebas, que pueden ser utilizados en cualquier test que requiera un destinatario.

## Datos de Contacto para Pruebas

- **WhatsApp**: +525518490291
- **Telegram ID**: 871198362
- **Email Personal**: ablova@gmail.com
- **Email Corporativo**: pablo@huntred.com

## Cómo Usar la Configuración

Para usar estos datos en cualquier test del sistema, simplemente importa el archivo de configuración:

```python
from app.tests.test_config import (
    TEST_WHATSAPP,
    TEST_TELEGRAM_ID,
    TEST_EMAIL_PERSONAL,
    TEST_EMAIL_CORPORATE
)
```

### Ejemplo de Uso en Tests

```python
# En cualquier archivo de test
import pytest
from app.tests.test_config import TEST_WHATSAPP, TEST_EMAIL_CORPORATE

def test_send_notification():
    # Crear un destinatario con los datos de prueba
    recipient = Person.objects.create(
        nombre="Usuario Prueba",
        phone=TEST_WHATSAPP,
        email=TEST_EMAIL_CORPORATE
    )
    
    # Realizar la prueba con el destinatario
    result = send_notification(recipient, "Mensaje de prueba")
    assert result is True
```

## Fixtures Comunes

Para tests que requieran modelos preconfigurados, se recomienda crear fixtures usando los datos de configuración:

```python
@pytest.fixture
def test_user():
    from app.tests.test_config import TEST_WHATSAPP, TEST_EMAIL_CORPORATE, TEST_USER_NAME
    
    user, created = Person.objects.get_or_create(
        phone=TEST_WHATSAPP,
        defaults={
            'nombre': TEST_USER_NAME,
            'email': TEST_EMAIL_CORPORATE
        }
    )
    return user
```

## Reglas para Tests

1. **Usar Datos Centralizados**: Siempre utilizar los datos de contacto desde `test_config.py` para cualquier prueba que envíe notificaciones reales.
   
2. **Mock para Producción**: En entornos de producción, usar los mocks definidos en `MOCK_RESPONSES` para evitar envíos reales.

3. **Limpieza**: Asegurar que cada test deje el sistema en estado limpio después de ejecutarse.

4. **Async Testing**: Para tests asíncronos, usar `pytest.mark.asyncio` y manejar correctamente los contextos asíncronos.

## Ejecutar Tests

```bash
# Todos los tests
python -m pytest

# Tests específicos
python -m pytest app/tests/test_notification_service.py

# Filtrar por marca
python -m pytest -m "not external_api"
```

## Configuración de Pytest

El archivo `pytest.ini` en la raíz del proyecto contiene la configuración para ejecutar los tests, incluyendo marcadores para categorizar y filtrar tests.

```ini
[pytest]
DJANGO_SETTINGS_MODULE = ai_huntred.settings
python_files = test_*.py
markers =
    slow: marks tests as slow
    external_api: marks tests that use external APIs
    notifications: marks tests related to the notification system
    feedback: marks tests related to the feedback system
```
