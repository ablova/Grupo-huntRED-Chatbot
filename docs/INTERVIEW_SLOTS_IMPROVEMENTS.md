# 🎯 Mejoras al Sistema de Slots de Entrevistas

## Resumen Ejecutivo

Se han implementado mejoras significativas al sistema de agenda y slots para entrevistas en la plataforma de Grupo huntRED®, enfocadas en **automatización**, **control** y **escalabilidad**. Las mejoras incluyen soporte para slots grupales, generación automática de slots, mejor experiencia en chatbot y dashboard avanzado de gestión.

## 🚀 Características Principales

### 1. **Slots Grupales Automáticos**
- **Activación automática**: Se habilitan slots grupales cuando una vacante tiene ≥3 plazas
- **Gestión inteligente**: Los candidatos se asignan automáticamente a slots grupales existentes o se crean nuevos
- **Cupo dinámico**: Control automático de cupos disponibles y ocupación
- **Compatibilidad**: Mantiene compatibilidad con entrevistas individuales tradicionales

### 2. **Generación Automática de Slots**
- **Comando de gestión**: `python manage.py generate_interview_slots`
- **Configuración flexible**: Duración, horarios, días hábiles, máximo por día
- **Integración con Google Calendar**: Creación automática de eventos en calendarios externos
- **Prevención de duplicados**: Verificación de slots existentes antes de crear nuevos

### 3. **Experiencia Mejorada en Chatbot**
- **Slots inteligentes**: Muestra slots grupales e individuales con información detallada
- **Botones interactivos**: Interfaz mejorada con botones y opciones claras
- **Mensajes personalizados**: Diferentes mensajes para slots grupales vs individuales
- **Alternativas cuando no hay slots**: Opciones para dejar preferencias, llamadas informativas, etc.

### 4. **Dashboard Avanzado de Gestión**
- **Vista unificada**: Gestión de slots grupales e individuales en una sola interfaz
- **Filtros avanzados**: Por unidad de negocio, vacante, tipo de sesión, fechas
- **Estadísticas en tiempo real**: Métricas de ocupación, confirmaciones, participantes
- **Acciones en lote**: Generación masiva de slots, edición, eliminación

## 📋 Arquitectura Técnica

### Modelos Principales

#### Event (app/ats/utils/Events.py)
```python
class Event(models.Model):
    # Campos existentes...
    session_type = models.CharField(choices=[
        ("individual", "Individual"),
        ("grupal", "Grupal"),
    ])
    cupo_maximo = models.PositiveIntegerField(help_text="Máximo de participantes")
    event_mode = models.CharField(choices=[
        ("presencial", "Presencial"),
        ("virtual", "Virtual"),
        ("hibrido", "Híbrido"),
    ])
    
    def lugares_disponibles(self) -> int:
        """Calcula cupos disponibles para slots grupales"""
```

#### EventParticipant (app/ats/utils/Events.py)
```python
class EventParticipant(models.Model):
    event = models.ForeignKey(Event, related_name='participants')
    person = models.ForeignKey('app.Person')
    status = models.CharField(choices=EventStatus.choices)
    notes = models.TextField()
```

### Servicios Principales

#### InterviewService (app/ats/services/interview_service.py)
```python
class InterviewService:
    async def generate_interview_slots(self, vacancy, start_date, end_date, ...)
    async def get_available_slots_for_vacancy(self, vacancy, ...)
    async def book_slot_for_candidate(self, person, vacancy, slot_id, ...)
    async def schedule_interview(self, person, vacancy, interview_date, ...)
```

### Lógica de Negocio

#### Determinación de Slots Grupales
```python
def requiere_slots_grupales(vacante) -> bool:
    """Determina si una vacante debe usar slots grupales"""
    return getattr(vacante, 'numero_plazas', 1) >= 3
```

## 🎮 Uso del Sistema

### 1. Generación de Slots

#### Comando de Gestión
```bash
# Generar slots para todas las vacantes activas
python manage.py generate_interview_slots

# Generar slots para una vacante específica
python manage.py generate_interview_slots --vacancy-id 123

# Generar slots para una unidad de negocio
python manage.py generate_interview_slots --business-unit "Tecnología"

# Simular generación sin crear slots
python manage.py generate_interview_slots --dry-run

# Forzar regeneración de slots existentes
python manage.py generate_interview_slots --force
```

#### Parámetros Disponibles
- `--vacancy-id`: ID de vacante específica
- `--business-unit`: Nombre de unidad de negocio
- `--start-date`: Fecha de inicio (YYYY-MM-DD)
- `--end-date`: Fecha de fin (YYYY-MM-DD)
- `--slot-duration`: Duración en minutos (default: 45)
- `--max-slots-per-day`: Máximo por día (default: 8)
- `--force`: Forzar regeneración
- `--dry-run`: Simular sin crear

### 2. Dashboard de Gestión

#### Acceso
```
/dashboard/slots/
```

#### Funcionalidades
- **Filtros**: Unidad de negocio, vacante, tipo de sesión, fechas
- **Estadísticas**: Total slots, grupales, individuales, confirmados, participantes
- **Acciones**: Ver detalles, editar, eliminar, generar nuevos slots
- **Analytics**: Ocupación, tendencias, métricas de rendimiento

### 3. Chatbot Mejorado

#### Flujo de Usuario
1. **Selección de vacante**: El candidato elige una vacante
2. **Visualización de slots**: Se muestran slots disponibles con información detallada
3. **Reserva**: El candidato selecciona un slot (grupal o individual)
4. **Confirmación**: Mensaje personalizado según el tipo de slot
5. **Alternativas**: Si no hay slots, se ofrecen opciones alternativas

#### Mensajes Personalizados
- **Slots grupales**: Incluyen consejos específicos para entrevistas grupales
- **Slots individuales**: Información estándar de entrevistas individuales
- **Sin slots**: Opciones para dejar preferencias, llamadas informativas, etc.

## 🔧 Configuración

### 1. Configuración de Vacantes

Para habilitar slots grupales automáticamente:
```python
# En el modelo Vacante
numero_plazas = models.IntegerField(default=1)
# Si numero_plazas >= 3, se habilitan slots grupales automáticamente
```

### 2. Configuración de Google Calendar

```python
# En BusinessUnit
calendar_id = models.CharField(max_length=255, null=True, blank=True)

# En settings.py
DEFAULT_CALENDAR_ID = 'primary'
```

### 3. Configuración de Horarios

```python
# Horarios por defecto
HORARIO_INICIO = 9  # 9:00 AM
HORARIO_FIN = 17    # 5:00 PM
DURACION_SLOT = 45  # minutos
MAX_SLOTS_POR_DIA = 8
```

## 📊 Métricas y Analytics

### 1. Métricas Disponibles
- **Ocupación de slots**: Porcentaje de slots ocupados vs disponibles
- **Eficiencia grupal**: Comparación entre slots grupales e individuales
- **Tendencias temporales**: Slots por día de la semana, hora del día
- **Participación**: Número de participantes por slot

### 2. Dashboard de Analytics
```
/dashboard/slots/analytics/
```

Incluye:
- Gráficos de ocupación
- Análisis de tendencias
- Comparativas grupales vs individuales
- Métricas de rendimiento

## 🔄 Flujo de Trabajo

### 1. Configuración Inicial
1. Crear vacante con `numero_plazas` ≥ 3 para slots grupales
2. Configurar `calendar_id` en BusinessUnit si se usa Google Calendar
3. Ejecutar comando de generación de slots

### 2. Operación Diaria
1. **Monitoreo**: Revisar dashboard de slots
2. **Generación**: Ejecutar comando para nuevas vacantes
3. **Gestión**: Editar/eliminar slots según necesidad
4. **Analytics**: Revisar métricas de rendimiento

### 3. Interacción con Candidatos
1. **Chatbot**: Los candidatos ven slots disponibles
2. **Reserva**: Selección automática de slot apropiado
3. **Notificación**: Confirmación y recordatorios automáticos
4. **Seguimiento**: Tracking de asistencia y feedback

## 🛠️ Mantenimiento

### 1. Limpieza de Slots
```bash
# Eliminar slots pasados
python manage.py shell
>>> from app.ats.utils.Events import Event
>>> Event.objects.filter(end_time__lt=timezone.now()).delete()
```

### 2. Backup de Datos
```bash
# Exportar slots
python manage.py dumpdata app.ats.utils.Events --indent=2 > slots_backup.json
```

### 3. Monitoreo de Errores
- Logs en `app/ats/services/interview_service.py`
- Logs en `app/management/commands/generate_interview_slots.py`
- Métricas en dashboard de analytics

## 🚨 Consideraciones Importantes

### 1. Rendimiento
- Los slots se generan de forma asíncrona para evitar bloqueos
- Se implementa paginación en el dashboard para grandes volúmenes
- Caché de slots disponibles para mejorar respuesta del chatbot

### 2. Seguridad
- Verificación de permisos por unidad de negocio
- Validación de cupos antes de asignar candidatos
- Protección contra doble reserva

### 3. Escalabilidad
- El sistema maneja automáticamente slots grupales vs individuales
- Generación automática de slots según demanda
- Integración con múltiples calendarios externos

## 🔮 Próximas Mejoras

### 1. Funcionalidades Planificadas
- **IA para optimización**: Predicción de demanda y generación automática
- **Integración con más calendarios**: Outlook, Calendly, etc.
- **Notificaciones avanzadas**: SMS, push notifications
- **Analytics predictivos**: Predicción de ocupación y tendencias

### 2. Optimizaciones Técnicas
- **API REST**: Endpoints para integración externa
- **Webhooks**: Notificaciones en tiempo real
- **Microservicios**: Separación de servicios para mejor escalabilidad
- **Caché distribuido**: Mejora de rendimiento con Redis

## 📞 Soporte

Para soporte técnico o consultas sobre el sistema de slots:
- **Documentación**: Este archivo y comentarios en el código
- **Logs**: Revisar logs de Django para errores
- **Dashboard**: Usar analytics para diagnóstico
- **Comandos**: Usar `--help` en comandos de gestión

---

**Versión**: 1.0  
**Fecha**: Diciembre 2024  
**Autor**: Equipo de Desarrollo Grupo huntRED® 