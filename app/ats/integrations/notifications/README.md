# Sistema de Notificaciones de Grupo huntRED®

Este documento describe la arquitectura y el uso del sistema de notificaciones del Grupo huntRED®.

## Estructura de Directorios

```
app/ats/integrations/notifications/
├── __init__.py
├── channels/           # Implementaciones específicas de canales (email, whatsapp, telegram)
├── core/              # Lógica central del sistema de notificaciones
├── process/           # Procesos de notificación (vacantes, entrevistas, etc.)
├── services/          # Servicios de notificación
├── templates/         # Plantillas para diferentes tipos de notificaciones
└── recipients/        # Módulos específicos por tipo de destinatario
    ├── __init__.py
    ├── candidate.py   # Notificaciones para candidatos
    ├── client.py      # Notificaciones para clientes
    ├── internal.py    # Notificaciones internas (equipo)
    └── manager.py     # Notificaciones para gerentes
```

## Módulos de Destinatarios

### CandidateNotifier

Maneja notificaciones para candidatos, como actualizaciones de estado, programación de entrevistas y ofertas.

**Ejemplo de uso:**
```python
from app.ats.integrations.notifications.recipients import CandidateNotifier
from app.models import Person, Vacancy

# Obtener el candidato y la vacante
candidate = Person.objects.get(email='candidato@ejemplo.com')
vacancy = Vacancy.objects.get(id=123)

# Crear notificador
notifier = CandidateNotifier(candidate)

# Enviar notificación de nueva oferta
await notifier.send_offer_notification(
    vacancy=vacancy,
    offer_details={
        'position': 'Desarrollador Senior',
        'salary': '$$$',
        'start_date': '2023-01-15',
        'offer_letter_url': 'https://example.com/offer/123'
    }
)
```

### ClientNotifier

Maneja notificaciones para clientes, como nuevos candidatos, retroalimentación de entrevistas y decisiones de contratación.

**Ejemplo de uso:**
```python
from app.ats.integrations.notifications.recipients import ClientNotifier
from app.models import Person, Vacancy

# Obtener el cliente y la vacante
client = Person.objects.get(email='cliente@empresa.com')
vacancy = Vacancy.objects.get(id=123)

# Crear notificador
notifier = ClientNotifier(client)

# Enviar notificación de nuevo candidato
await notifier.send_new_candidate_submission(
    candidate=Person.objects.get(email='candidato@ejemplo.com'),
    vacancy=vacancy,
    resume_url='https://example.com/resumes/123'
)
```

### InternalNotifier

Maneja notificaciones internas del equipo, como asignaciones de tareas, alertas del sistema y métricas de rendimiento.

**Ejemplo de uso:**
```python
from app.ats.integrations.notifications.recipients import InternalNotifier
from app.models import Person

# Crear notificador para el equipo
notifier = InternalNotifier()

# Enviar alerta del sistema
await notifier.send_system_alert(
    alert_type='database_error',
    message='Error de conexión a la base de datos',
    severity='critical',
    related_object=some_database_object
)
```

### ManagerNotifier

Maneja notificaciones para gerentes y líderes de equipo, incluyendo métricas de rendimiento, solicitudes de aprobación y actualizaciones importantes.

**Ejemplo de uso:**
```python
from app.ats.integrations.notifications.recipients import ManagerNotifier
from app.models import Person, Team

# Obtener el gerente y el equipo
manager = Person.objects.get(email='gerente@empresa.com')
team = Team.objects.get(id=456)

# Crear notificador
notifier = ManagerNotifier(manager)

# Enviar informe de rendimiento del equipo
await notifier.send_team_performance_report(
    team=team,
    metrics={
        'hires_this_month': 5,
        'open_positions': 3,
        'candidates_in_pipeline': 12,
        'time_to_hire_avg': '15 días'
    },
    time_period='monthly'
)
```

## Canales de Notificación

El sistema soporta múltiples canales de notificación:

- **Email**: Para notificaciones formales y detalladas
- **WhatsApp**: Para notificaciones urgentes o informales
- **Telegram**: Para notificaciones internas del equipo

Los canales se pueden especificar al enviar notificaciones, y el sistema manejará automáticamente el formato adecuado para cada canal.

## Plantillas

Las plantillas de notificación se encuentran en el directorio `templates/` y están organizadas por tipo de destinatario y tipo de notificación. Las plantillas soportan variables de contexto para personalizar el contenido.

## Configuración

La configuración del sistema de notificaciones se maneja a través de las variables de entorno de Django. Las configuraciones clave incluyen:

- `DEFAULT_NOTIFICATION_CHANNELS`: Canales predeterminados a usar
- `NOTIFICATION_RATE_LIMIT`: Límite de tasa para evitar envíos excesivos
- `EMAIL_NOTIFICATIONS_ENABLED`: Habilitar/deshabilitar notificaciones por correo electrónico

## Pruebas

Las pruebas unitarias y de integración para el sistema de notificaciones se encuentran en:

```
app/tests/
├── test_notifications/
│   ├── test_candidate_notifications.py
│   ├── test_client_notifications.py
│   ├── test_internal_notifications.py
│   └── test_manager_notifications.py
```

## Mejoras Futuras

- [ ] Implementar soporte para notificaciones push
- [ ] Añadir más plantillas predefinidas
- [ ] Mejorar el sistema de plantillas con soporte para más variables
- [ ] Implementar un sistema de preferencias de notificación por usuario
