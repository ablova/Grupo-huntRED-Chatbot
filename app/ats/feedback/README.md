# Sistema Integral de Retroalimentación de Grupo huntRED®

Sistema completo para capturar, gestionar y analizar retroalimentación en cada etapa del proceso de servicio, desde propuestas hasta evaluaciones finales.

## Estructura del Sistema

```
app/com/feedback/
├── __init__.py          # Configuración básica y constantes
├── apps.py              # Configuración de Django App
├── celery_config.py     # Configuración de tareas programadas
├── completion_tracker.py # Gestión de retroalimentación post-servicio
├── feedback_models.py   # Modelos para todas las etapas de feedback
├── ongoing_tracker.py   # Gestión de retroalimentación durante servicio
├── process_views.py     # Vistas relacionadas con procesos específicos
├── reminder_system.py   # Sistema centralizado de recordatorios
├── signals.py           # Automatización por eventos del sistema
├── tasks.py             # Tareas asíncronas programadas
├── urls.py              # Configuración de rutas URL
└── views.py             # Vistas principales del sistema
```

## Características Principales

### 1. Retroalimentación en Todas las Etapas
- **Pre-servicio**: Evaluación de propuestas y cotizaciones
- **Durante el servicio**: Monitoreo en hitos clave
- **Post-servicio**: Evaluación final y testimoniales

### 2. Sistema Avanzado de Recordatorios
- Seguimiento automático de solicitudes no respondidas
- Envío multicanal (email, WhatsApp)
- Escalamiento a supervisores según tiempos de espera

### 3. Análisis y Visualización
- Panel unificado con métricas clave
- Gráficos de tendencias y distribución
- Exportación de insights y reportes

### 4. Integración con Sistemas Existentes
- Conexión con propuestas (`app.ats.pricing`)
- Integración con mensajería (`app.ats.chatbot`)
- Uso de la infraestructura Redis existente

## Lineamientos Técnicos

Este sistema sigue estrictamente las reglas globales de arquitectura de Grupo huntRED®:

1. **Estructura de Directorios**: Mantiene la organización existente
2. **Patrones de Nombrado**: Consistentes con el resto del sistema
3. **Gestión Asíncrona**: Uso de Celery y Redis para operaciones en background
4. **Comentarios de Código**: Formato estándar con gerundios/participios
5. **Control de Acceso**: Restricción por roles de consultor según BU

## Integración en el Flujo de Trabajo

El sistema se integra en los siguientes puntos del flujo de trabajo:

1. Envío de propuestas -> Solicitud de retroalimentación inicial
2. Hitos de servicio -> Evaluación continua
3. Finalización de servicio -> Evaluación final y testimoniales

## Configuración y Mantenimiento

Para instrucciones detalladas de implementación, consulte:
- `setup_instructions.md` - Guía de instalación
- `celery_config.py` - Configuración de tareas programadas

---

**Desarrollado por**: Grupo huntRED® Engineering Team  
**Fecha**: 18 de Mayo, 2025
