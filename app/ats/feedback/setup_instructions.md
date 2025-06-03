# Instrucciones de Implementación del Sistema de Feedback

Este documento contiene las instrucciones paso a paso para implementar el Sistema Integral de Retroalimentación en Grupo huntRED®.

## Pasos Previos a la Implementación

### 1. Verificar Dependencias 

Asegúrese de que las siguientes dependencias estén instaladas:

```bash
pip install celery==5.2.7
pip install redis==4.3.4
pip install django-celery-beat==2.3.0
```

### 2. Configuración de Redis

Verifique que Redis esté correctamente configurado en `settings.py`:

```python
# Configuración de Redis
REDIS_URL = 'redis://localhost:6379/0'  # Ajustar según su entorno
```

## Implementación del Sistema

### 1. Registrar la Aplicación

Agregue 'app.ats.feedback' a INSTALLED_APPS en `ai_huntred/settings.py`:

```python
INSTALLED_APPS = [
    # Otras aplicaciones...
    'app.ats.feedback.apps.FeedbackConfig',
]
```

### 2. Configurar Celery

Actualice su archivo `celery.py` principal para incluir las tareas programadas:

```python
from app.ats.feedback.celery_config import CELERY_BEAT_SCHEDULE_FEEDBACK

# Después de la configuración app.conf.beat_schedule existente:
app.conf.beat_schedule.update(CELERY_BEAT_SCHEDULE_FEEDBACK)
```

### 3. Ejecutar Migraciones

```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Agregar Enlace al Dashboard Principal

Añada el siguiente enlace en su plantilla de dashboard principal:

```html
<a href="{% url 'feedback:dashboard' %}" class="menu-item">
    <i class="fas fa-chart-line"></i> Sistema de Retroalimentación
</a>
```

## Verificación Post-Implementación

### 1. Verificar URLs

Asegúrese de que las siguientes URLs sean accesibles:

- `/feedback/` - Dashboard principal del sistema
- `/feedback/list/` - Lista de todas las retroalimentaciones
- `/feedback/suggestions/` - Lista de sugerencias de mejora

### 2. Verificar Tareas Celery

Compruebe que las tareas programadas estén registradas:

```bash
celery -A ai_huntred inspect registered
```

Debería ver las tareas del módulo `app.ats.feedback.tasks`.

### 3. Probar el Flujo Completo

1. Genere una propuesta de prueba
2. Verifique que se envíe una solicitud de retroalimentación
3. Complete un formulario de retroalimentación mediante el enlace de token
4. Verifique que aparezca en el panel de control

## Contacto para Soporte

Si surge algún problema durante la implementación, contacte al equipo de desarrollo en:
- Email: desarrollo@huntred.com
- Slack: #canal-feedback-system

---

**Desarrollado por**: Grupo huntRED® Engineering Team  
**Fecha**: 18 de Mayo, 2025
