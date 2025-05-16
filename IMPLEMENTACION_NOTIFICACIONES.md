# Guía de Implementación: Sistema de Notificaciones y Feedback

## Índice
1. [Introducción](#introducción)
2. [Requisitos Previos](#requisitos-previos)
3. [Pasos de Implementación](#pasos-de-implementación)
4. [Configuración de WhatsApp Business API](#configuración-de-whatsapp-business-api)
5. [Configuración de Notificaciones](#configuración-de-notificaciones)
6. [Configuración de Feedback](#configuración-de-feedback)
7. [Pruebas y Validación](#pruebas-y-validación)
8. [Mantenimiento y Monitoreo](#mantenimiento-y-monitoreo)

## Introducción

Esta guía detalla el proceso de implementación del sistema integrado de notificaciones y feedback para Grupo huntRED®. Este sistema permite la comunicación unificada a través de múltiples canales (WhatsApp, correo electrónico) y la recolección de feedback estructurado para mejorar el matching de candidatos mediante machine learning.

## Requisitos Previos

### Tecnologías Necesarias
- Django 4.1+
- PostgreSQL 14+
- Redis 6+ (para tareas asíncronas)
- Python 3.9+
- httpx (para llamadas HTTP asíncronas)

### Cuentas Requeridas
- Cuenta de Meta Business
- WhatsApp Business API
- Cuenta de correo electrónico SMTP

## Pasos de Implementación

### 1. Preparación de la Base de Datos

```bash
# Aplicar migraciones para los nuevos modelos
python manage.py makemigrations app
python manage.py migrate
```

### 2. Actualización de Dependencias

Añadir las siguientes dependencias al archivo `requirements.txt`:

```
httpx>=0.23.0
django-async-redis>=0.1.4
cryptography>=39.0.0
```

Luego instalar:

```bash
pip install -r requirements.txt
```

### 3. Configuración del Entorno

Actualizar las variables de entorno en `.env`:

```bash
# WhatsApp API Configuration
WHATSAPP_API_VERSION=v19.0
WHATSAPP_API_URL=https://graph.facebook.com

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=mail.huntred.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=notificaciones@huntred.com
EMAIL_HOST_PASSWORD=**********
DEFAULT_FROM_EMAIL=Grupo huntRED® <notificaciones@huntred.com>
```

## Configuración de WhatsApp Business API

### 1. Creación de la Aplicación en Meta for Developers

1. Acceder a [Meta for Developers](https://developers.facebook.com/)
2. Crear una nueva aplicación de tipo "Business"
3. Añadir el producto "WhatsApp" a la aplicación
4. Configurar el número de teléfono de WhatsApp Business

### 2. Obtención de Credenciales

Obtener y guardar las siguientes credenciales:
- App ID
- App Secret
- Access Token (Permanente)
- Phone Number ID
- Business Account ID

### 3. Registro en la Base de Datos

Acceder al panel de administración y crear un nuevo registro en el modelo `MetaAPI`:

```
Ruta: http://tu-dominio.com/admin/app/metaapi/add/
```

Completar todos los campos con los datos obtenidos:
- Nombre descriptivo
- App ID
- App Secret
- Access Token
- Phone Number ID
- Phone ID Formatted (sin +, ej: 5215512345678)
- Business Account ID
- Webhook Verify Token (generar aleatorio)
- Activar (marcar como activo)

### 4. Configuración de WhatsApp

Crear una configuración en el modelo `WhatsAppConfig`:

```
Ruta: http://tu-dominio.com/admin/app/whatsappconfig/add/
```

Completar:
- Nombre descriptivo
- Usar página personalizada (sí/no)
- URL de activación (si se usa página personalizada)
- Configurar plantillas
- Límites de mensajes
- Activar (marcar como activo)

## Configuración de Notificaciones

### 1. Creación de Canales

Configurar los canales de notificación:

```
Ruta: http://tu-dominio.com/admin/app/notificationchannel/add/
```

Crear al menos estos canales:
1. WhatsApp (prioridad 1)
2. Email (prioridad 2)

### 2. Configuración General

Configurar la configuración general de notificaciones:

```
Ruta: http://tu-dominio.com/admin/app/notificationconfig/add/
```

Completar:
- Nombre: "Canal de Notificaciones General"
- Canal WhatsApp: Seleccionar el canal creado
- Canal Email: Seleccionar el canal creado
- Canal por defecto: WhatsApp
- Intentos de reenvío: 3
- Tiempo entre reintentos: 5 (minutos)

### 3. Plantillas de Notificación

Crear las plantillas HTML para cada tipo de notificación:

```
Ubicación: app/templates/notifications/
```

Crear al menos estas plantillas:
1. `feedback.html` - Para solicitudes de feedback
2. `interview.html` - Para recordatorios de entrevista
3. `activation.html` - Para activación de WhatsApp

## Configuración de Feedback

### 1. Integración con ML

Configurar la integración del feedback con el sistema ML:

1. Revisar los métodos de actualización de pesos en `FeedbackService`:
   - `_update_skill_weight`
   - `_update_experience_weight`
   - `_update_location_weight`

2. Implementar la lógica específica según los modelos ML existentes.

### 2. Plantillas de Feedback

Crear las plantillas para feedback:

```
Ubicación: app/templates/feedback/
```

1. `feedback_notification.html` - Plantilla para solicitar feedback
2. `whatsapp_activation_email.html` - Plantilla para activar WhatsApp

## Pruebas y Validación

### 1. Datos de Contacto para Pruebas

Utilizar los siguientes datos de contacto para todas las pruebas:

#### WhatsApp
```
Número: +525518490291
```

#### Telegram
```
ID: 871198362
```

#### Email
```
Personal: ablova@gmail.com
Corporativo: pablo@huntred.com
```

### 2. Pruebas Unitarias

Ejecutar pruebas unitarias para verificar el funcionamiento:

```bash
python manage.py test app.tests.test_notification_service
python manage.py test app.tests.test_feedback_service
python manage.py test app.tests.test_whatsapp_api
```

### 3. Pruebas de Integración

Realizar pruebas manuales:

1. **Envío de Notificación**:
   ```python
   from app.com.utils.notification_service import NotificationService
   from app.models import Person
   
   # Usar el destinatario de prueba
   recipient = Person.objects.get(phone='+525518490291')
   # Alternativa: Crear un destinatario de prueba si no existe
   # recipient, created = Person.objects.get_or_create(
   #     phone='+525518490291',
   #     defaults={
   #         'nombre': 'Pablo',
   #         'email': 'pablo@huntred.com',
   #         'telegram_id': '871198362',
   #         'whatsapp_enabled': True
   #     }
   # )
   
   # Crear instancia del servicio
   service = NotificationService()
   
   # Enviar notificación
   notification = await service.send_notification(
       recipient=recipient,
       notification_type='TEST',
       content='Esto es una notificación de prueba',
       metadata={'test': True}
   )
   ```

2. **Solicitud de Feedback**:
   ```python
   from app.com.utils.feedback_service import FeedbackService
   from app.models import Entrevista
   
   # Obtener una entrevista existente
   interview = Entrevista.objects.get(id=1)
   
   # Crear instancia del servicio
   service = FeedbackService('huntRED')
   
   # Enviar solicitud de feedback
   result = await service.send_feedback_notification(interview)
   ```

## Mantenimiento y Monitoreo

### 1. Monitoreo

Configurar monitoreo de mensajes y notificaciones:

1. Revisar regularmente el modelo `MessageLog` para verificar el estado de los mensajes:
   ```
   Ruta: http://tu-dominio.com/admin/app/messagelog/
   ```

2. Configurar alertas para fallos en el envío:
   ```python
   # Implementar en un cronjob
   from app.models import MessageLog
   from datetime import timedelta
   from django.utils import timezone
   
   # Buscar mensajes fallidos de las últimas 24 horas
   failed_messages = MessageLog.objects.filter(
       status='FAILED',
       sent_at__gte=timezone.now() - timedelta(days=1)
   ).count()
   
   # Enviar alerta si hay más de 10 mensajes fallidos
   if failed_messages > 10:
       # Enviar alerta al equipo
   ```

### 2. Optimización Continua

Revisar regularmente las estadísticas de entrega y engagement:

1. Tasa de entrega por canal
2. Tasa de apertura/interacción
3. Eficacia de las plantillas
4. Mejoras en el matching basadas en feedback

### 3. Actualización de Tokens

Configurar un recordatorio para actualizar los tokens de acceso:

```python
# Implementar en un cronjob
from app.models import MetaAPI
from datetime import timedelta
from django.utils import timezone

# Notificar 7 días antes de la expiración (si se usan tokens de corta duración)
meta_api = MetaAPI.objects.filter(active=True).first()
if meta_api and meta_api.token_expires_at < timezone.now() + timedelta(days=7):
    # Enviar notificación para renovar token
```

---

## Contacto y Soporte

Para soporte en la implementación, contactar a:
- Equipo de Desarrollo: desarrollo@huntred.com
- Administración de Sistemas: sistemas@huntred.com

## Documentación Adicional

- [API de WhatsApp Business](https://developers.facebook.com/docs/whatsapp/cloud-api)
- [Django Async](https://docs.djangoproject.com/en/4.2/topics/async/)
- [HTTPX Documentation](https://www.python-httpx.org/)
