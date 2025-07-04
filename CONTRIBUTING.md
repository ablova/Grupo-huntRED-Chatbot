# Contributing to huntRED® v2

¡Gracias por tu interés en contribuir a huntRED® v2! Este documento te guiará a través del proceso de contribución.

## 📋 Tabla de Contenidos

- [Código de Conducta](#código-de-conducta)
- [Empezando](#empezando)
- [Proceso de Desarrollo](#proceso-de-desarrollo)
- [Estándares de Código](#estándares-de-código)
- [Testing](#testing)
- [Pull Requests](#pull-requests)
- [Reportar Issues](#reportar-issues)

## 🤝 Código de Conducta

Este proyecto adhiere al [Código de Conducta de huntRED](CODE_OF_CONDUCT.md). Al participar, se espera que respetes este código.

## 🚀 Empezando

### Prerrequisitos

- Python 3.9+
- PostgreSQL 14+
- Redis 6+
- Docker & Docker Compose
- Git

### Configuración del Entorno de Desarrollo

1. **Fork y clonar el repositorio**
   ```bash
   git clone https://github.com/tu-usuario/huntred-v2.git
   cd huntred-v2
   ```

2. **Crear entorno virtual**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # venv\Scripts\activate   # Windows
   ```

3. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

4. **Configurar variables de entorno**
   ```bash
   cp .env.example .env
   # Editar .env con tus configuraciones de desarrollo
   ```

5. **Configurar pre-commit hooks**
   ```bash
   pre-commit install
   ```

6. **Ejecutar con Docker (Recomendado)**
   ```bash
   docker-compose up -d
   ```

## 🔄 Proceso de Desarrollo

### Flujo de Git

1. **Crear una rama para tu feature**
   ```bash
   git checkout -b feature/mi-nueva-caracteristica
   ```

2. **Hacer cambios y commits**
   ```bash
   git add .
   git commit -m "feat: agregar nueva característica"
   ```

3. **Pushear la rama**
   ```bash
   git push origin feature/mi-nueva-caracteristica
   ```

4. **Crear Pull Request**

### Convenciones de Naming

- **Ramas**: `feature/descripcion`, `bugfix/descripcion`, `hotfix/descripcion`
- **Commits**: Seguir [Conventional Commits](https://www.conventionalcommits.org/)
  - `feat:` nueva característica
  - `fix:` corrección de bug
  - `docs:` cambios en documentación
  - `style:` cambios de formato
  - `refactor:` refactorización de código
  - `test:` agregar o corregir tests
  - `chore:` tareas de mantenimiento

## 📏 Estándares de Código

### Python

- **Formatter**: Black (configurado en `pyproject.toml`)
- **Linter**: Flake8 + isort
- **Type Checker**: MyPy
- **Docstrings**: Google Style

### Ejemplo de código bien formateado:

```python
from typing import Optional, List
import structlog

logger = structlog.get_logger()

class PayrollCalculator:
    """Calculator for payroll operations with Mexican compliance.
    
    This class handles all payroll calculations including taxes,
    deductions, and employer contributions according to Mexican
    labor law (LFT) and tax regulations.
    
    Attributes:
        company_id: Unique identifier for the company
        country_config: Configuration specific to the country
    """
    
    def __init__(self, company_id: str) -> None:
        """Initialize payroll calculator.
        
        Args:
            company_id: Unique identifier for the company
            
        Raises:
            ValueError: If company_id is empty or invalid
        """
        if not company_id:
            raise ValueError("company_id cannot be empty")
            
        self.company_id = company_id
        logger.info("PayrollCalculator initialized", company_id=company_id)
    
    def calculate_isr(self, gross_salary: float) -> float:
        """Calculate ISR (Income Tax) for Mexican employees.
        
        Args:
            gross_salary: Gross monthly salary in MXN
            
        Returns:
            Calculated ISR amount in MXN
            
        Raises:
            ValueError: If gross_salary is negative
        """
        if gross_salary < 0:
            raise ValueError("gross_salary must be non-negative")
            
        # Implementation here...
        return calculated_isr
```

### Configuración de herramientas

El proyecto incluye configuración automática en `pyproject.toml`:

```toml
[tool.black]
line-length = 88
target-version = ['py39']

[tool.isort]
profile = "black"
multi_line_output = 3

[tool.mypy]
python_version = "3.9"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

## 🧪 Testing

### Ejecutar Tests

```bash
# Tests unitarios
pytest tests/unit/

# Tests de integración
pytest tests/integration/

# Tests E2E
pytest tests/e2e/

# Todos los tests con coverage
pytest --cov=src tests/

# Tests específicos
pytest tests/unit/test_payroll_engine.py::test_calculate_isr
```

### Escribir Tests

#### Test Unitario Ejemplo:

```python
import pytest
from src.services.payroll_engine import PayrollEngine

class TestPayrollEngine:
    """Test suite for PayrollEngine class."""
    
    @pytest.fixture
    def payroll_engine(self):
        """Create PayrollEngine instance for testing."""
        return PayrollEngine(company_id="test_company")
    
    def test_calculate_isr_valid_salary(self, payroll_engine):
        """Test ISR calculation with valid salary."""
        # Arrange
        gross_salary = 25000.0
        expected_isr = 2072.97  # Expected ISR for 25k MXN
        
        # Act
        result = payroll_engine.calculate_isr(gross_salary)
        
        # Assert
        assert abs(result - expected_isr) < 0.01
    
    def test_calculate_isr_negative_salary_raises_error(self, payroll_engine):
        """Test that negative salary raises ValueError."""
        with pytest.raises(ValueError, match="gross_salary must be non-negative"):
            payroll_engine.calculate_isr(-1000.0)
```

#### Test de Integración Ejemplo:

```python
import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

class TestWhatsAppWebhook:
    """Integration tests for WhatsApp webhook endpoints."""
    
    def test_webhook_employee_checkin(self):
        """Test employee check-in via WhatsApp webhook."""
        # Arrange
        webhook_data = {
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [{
                            "from": "5215551234567",
                            "text": {"body": "entrada"},
                            "type": "text"
                        }]
                    }
                }]
            }]
        }
        
        # Act
        response = client.post(
            "/api/v1/whatsapp/webhook/test_company",
            json=webhook_data
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["status"] == "processed"
```

## 📝 Pull Requests

### Antes de enviar un PR

1. **Ejecutar todos los checks localmente**
   ```bash
   # Formato de código
   black src/ tests/
   isort src/ tests/
   
   # Linting
   flake8 src/ tests/
   
   # Type checking
   mypy src/
   
   # Tests
   pytest --cov=src tests/
   ```

2. **Actualizar documentación** si es necesario

3. **Agregar tests** para nueva funcionalidad

### Template de PR

```markdown
## Descripción
Breve descripción de los cambios realizados.

## Tipo de cambio
- [ ] Bug fix (cambio que corrige un issue sin romper funcionalidad existente)
- [ ] Nueva característica (cambio que agrega funcionalidad sin romper existente)
- [ ] Breaking change (fix o feature que causaría que funcionalidad existente no funcione como se espera)
- [ ] Actualización de documentación

## ¿Cómo ha sido probado?
Describe las pruebas que ejecutaste para verificar tus cambios.

## Checklist:
- [ ] Mi código sigue las convenciones de estilo del proyecto
- [ ] He realizado una auto-revisión de mi código
- [ ] He comentado mi código, particularmente en áreas difíciles de entender
- [ ] He realizado cambios correspondientes a la documentación
- [ ] Mis cambios no generan nuevas advertencias
- [ ] He agregado tests que prueban que mi fix es efectivo o que mi feature funciona
- [ ] Tests unitarios nuevos y existentes pasan localmente con mis cambios
```

## 🐛 Reportar Issues

### Antes de crear un issue

1. **Buscar issues existentes** para evitar duplicados
2. **Usar la versión más reciente** del código
3. **Revisar la documentación**

### Template de Bug Report

```markdown
**Describe el bug**
Una descripción clara y concisa del bug.

**Para Reproducir**
Pasos para reproducir el comportamiento:
1. Ir a '...'
2. Hacer click en '....'
3. Scroll down to '....'
4. Ver error

**Comportamiento esperado**
Una descripción clara y concisa de lo que esperabas que sucediera.

**Screenshots**
Si aplica, agregar screenshots para ayudar a explicar el problema.

**Entorno:**
 - OS: [e.g. Ubuntu 20.04]
 - Python version: [e.g. 3.9.7]
 - Browser: [e.g. chrome, safari]
 - Version: [e.g. 2.0.0]

**Contexto adicional**
Agregar cualquier otro contexto sobre el problema aquí.
```

### Template de Feature Request

```markdown
**¿Tu feature request está relacionado a un problema? Describe.**
Una descripción clara y concisa de cuál es el problema.

**Describe la solución que te gustaría**
Una descripción clara y concisa de lo que quieres que suceda.

**Describe alternativas que hayas considerado**
Una descripción clara y concisa de cualquier solución o feature alternativa que hayas considerado.

**Contexto adicional**
Agregar cualquier otro contexto o screenshots sobre el feature request aquí.
```

## 🏷️ Etiquetas y Milestones

### Etiquetas de Issues
- `bug` - Algo no está funcionando
- `enhancement` - Nueva característica o mejora
- `documentation` - Mejoras o adiciones a documentación
- `good first issue` - Bueno para colaboradores nuevos
- `help wanted` - Se necesita ayuda adicional
- `question` - Información adicional es solicitada

### Etiquetas de Prioridad
- `priority: high` - Alta prioridad
- `priority: medium` - Prioridad media
- `priority: low` - Baja prioridad

## 📚 Recursos Adicionales

- [Documentación Técnica](docs/technical-documentation.md)
- [Guía de Implementación](docs/implementation-guide.md)
- [API Documentation](http://localhost:8000/docs) (desarrollo)
- [WhatsApp Business API Docs](https://developers.facebook.com/docs/whatsapp)

## 🙋‍♀️ ¿Necesitas Ayuda?

Si tienes preguntas sobre el proceso de contribución:

1. **Crea un issue** con la etiqueta `question`
2. **Únete a nuestro Slack** (link en README)
3. **Contacta al equipo**: contributors@huntred.com

---

**¡Gracias por contribuir a huntRED® v2! Juntos estamos construyendo el futuro del trabajo conversacional.** 🚀