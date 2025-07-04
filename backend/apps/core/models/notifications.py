"""
Notification Models - Sistema huntRED® v2
Sistema completo de notificaciones multi-canal con templates y automatización.
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.contrib.postgres.fields import ArrayField
from typing import Dict, List, Any, Optional
import uuid
import json


class NotificationChannel(models.Model):
    """
    Canal de notificación configurado por Business Unit.
    """
    
    # === IDENTIFICACIÓN ===
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, help_text="Nombre del canal")
    
    # === TIPO DE CANAL ===
    CHANNEL_TYPE_CHOICES = [
        ('email', 'Email'),
        ('whatsapp', 'WhatsApp'),
        ('telegram', 'Telegram'),
        ('slack', 'Slack'),
        ('discord', 'Discord'),
        ('sms', 'SMS'),
        ('push', 'Push Notification'),
        ('in_app', 'In-App Notification'),
        ('webhook', 'Webhook'),
        ('api', 'API Call'),
        ('custom', 'Personalizado')
    ]
    channel_type = models.CharField(max_length=20, choices=CHANNEL_TYPE_CHOICES,
                                  db_index=True, help_text="Tipo de canal")
    
    # === BUSINESS UNIT ===
    business_unit = models.ForeignKey('BusinessUnit', on_delete=models.CASCADE,
                                    related_name='notification_channels',
                                    help_text="Business Unit propietaria")
    
    # === CONFIGURACIÓN DEL CANAL ===
    config = models.JSONField(default=dict, blank=True, help_text="""
    Configuración específica del canal:
    {
        'email': {
            'smtp_host': 'smtp.gmail.com',
            'smtp_port': 587,
            'username': 'user@domain.com',
            'password': 'encrypted_password',
            'use_tls': true,
            'from_email': 'noreply@huntred.com',
            'from_name': 'huntRED® System'
        },
        'whatsapp': {
            'api_url': 'https://graph.facebook.com/v18.0',
            'access_token': 'encrypted_token',
            'phone_number_id': '123456789',
            'business_account_id': '987654321',
            'webhook_verify_token': 'verify_token'
        },
        'telegram': {
            'bot_token': 'encrypted_token',
            'chat_id': '-1001234567890',
            'parse_mode': 'HTML'
        },
        'slack': {
            'webhook_url': 'https://hooks.slack.com/services/...',
            'channel': '#general',
            'username': 'huntRED Bot',
            'icon_emoji': ':robot_face:'
        }
    }
    """)
    
    # === ESTADO Y CONFIGURACIÓN ===
    is_active = models.BooleanField(default=True, db_index=True,
                                  help_text="¿El canal está activo?")
    is_default = models.BooleanField(default=False,
                                   help_text="¿Es el canal por defecto para este tipo?")
    
    # === LÍMITES Y CONTROL ===
    priority = models.PositiveSmallIntegerField(default=10,
                                              help_text="Prioridad del canal (menor = mayor prioridad)")
    rate_limit_per_minute = models.PositiveIntegerField(default=100,
                                                      help_text="Límite de mensajes por minuto")
    rate_limit_per_hour = models.PositiveIntegerField(default=1000,
                                                    help_text="Límite de mensajes por hora")
    rate_limit_per_day = models.PositiveIntegerField(default=10000,
                                                   help_text="Límite de mensajes por día")
    
    # === POLÍTICA DE REINTENTOS ===
    retry_policy = models.JSONField(default=dict, blank=True, help_text="""
    Política de reintentos:
    {
        'max_attempts': 3,
        'retry_delays': [60, 300, 900],  // seconds
        'backoff_factor': 2,
        'retry_on_errors': ['timeout', 'rate_limit', 'server_error']
    }
    """)
    
    # === FILTROS Y CONDICIONES ===
    filters = models.JSONField(default=dict, blank=True, help_text="""
    Filtros para este canal:
    {
        'notification_types': ['interview', 'offer', 'reminder'],
        'priority_levels': ['high', 'urgent'],
        'business_hours_only': true,
        'exclude_weekends': false,
        'recipient_types': ['candidate', 'hr_manager'],
        'custom_conditions': []
    }
    """)
    
    # === MÉTRICAS ===
    total_sent = models.PositiveIntegerField(default=0,
                                           help_text="Total de notificaciones enviadas")
    total_failed = models.PositiveIntegerField(default=0,
                                             help_text="Total de fallos")
    success_rate = models.FloatField(default=0.0,
                                   validators=[MinValueValidator(0), MaxValueValidator(1)],
                                   help_text="Tasa de éxito")
    avg_delivery_time = models.FloatField(default=0.0,
                                        help_text="Tiempo promedio de entrega en segundos")
    
    # === TIMESTAMPS ===
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_used = models.DateTimeField(null=True, blank=True,
                                   help_text="Última vez que se usó")
    
    class Meta:
        verbose_name = "Canal de Notificación"
        verbose_name_plural = "Canales de Notificación"
        ordering = ['business_unit', 'priority', 'name']
        unique_together = ['business_unit', 'channel_type', 'name']
        indexes = [
            models.Index(fields=['business_unit', 'channel_type', 'is_active']),
            models.Index(fields=['priority', 'is_default']),
            models.Index(fields=['success_rate', 'total_sent']),
        ]
    
    def __str__(self):
        return f"{self.business_unit.name} - {self.name} ({self.get_channel_type_display()})"
    
    def update_metrics(self, success: bool, delivery_time: float = 0):
        """Actualiza las métricas del canal."""
        if success:
            self.total_sent += 1
            # Actualizar tiempo promedio de entrega
            if self.total_sent == 1:
                self.avg_delivery_time = delivery_time
            else:
                self.avg_delivery_time = (
                    (self.avg_delivery_time * (self.total_sent - 1) + delivery_time) / self.total_sent
                )
        else:
            self.total_failed += 1
        
        # Calcular tasa de éxito
        total_attempts = self.total_sent + self.total_failed
        if total_attempts > 0:
            self.success_rate = self.total_sent / total_attempts
        
        self.last_used = timezone.now()
        self.save(update_fields=['total_sent', 'total_failed', 'success_rate', 
                               'avg_delivery_time', 'last_used'])
    
    def can_send_notification(self, notification_type: str, priority: str) -> bool:
        """Verifica si el canal puede enviar una notificación específica."""
        filters = self.filters
        
        # Verificar tipos de notificación permitidos
        allowed_types = filters.get('notification_types', [])
        if allowed_types and notification_type not in allowed_types:
            return False
        
        # Verificar niveles de prioridad
        allowed_priorities = filters.get('priority_levels', [])
        if allowed_priorities and priority not in allowed_priorities:
            return False
        
        # Verificar horario de trabajo
        if filters.get('business_hours_only', False):
            current_hour = timezone.now().hour
            if not (9 <= current_hour <= 18):  # 9 AM - 6 PM
                return False
        
        # Verificar fines de semana
        if filters.get('exclude_weekends', False):
            current_weekday = timezone.now().weekday()
            if current_weekday >= 5:  # Saturday = 5, Sunday = 6
                return False
        
        return True
    
    def get_retry_delay(self, attempt: int) -> int:
        """Calcula el delay para el siguiente intento."""
        retry_policy = self.retry_policy
        delays = retry_policy.get('retry_delays', [60, 300, 900])
        
        if attempt < len(delays):
            return delays[attempt]
        
        # Usar backoff exponencial si no hay más delays definidos
        backoff_factor = retry_policy.get('backoff_factor', 2)
        last_delay = delays[-1] if delays else 60
        return last_delay * (backoff_factor ** (attempt - len(delays) + 1))


class NotificationTemplate(models.Model):
    """
    Template para notificaciones con soporte para múltiples canales.
    """
    
    # === IDENTIFICACIÓN ===
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, db_index=True,
                          help_text="Nombre del template")
    description = models.TextField(blank=True,
                                 help_text="Descripción del template")
    
    # === TIPO DE NOTIFICACIÓN ===
    NOTIFICATION_TYPE_CHOICES = [
        ('welcome', 'Bienvenida'),
        ('interview_scheduled', 'Entrevista Programada'),
        ('interview_reminder', 'Recordatorio de Entrevista'),
        ('interview_cancelled', 'Entrevista Cancelada'),
        ('offer_sent', 'Oferta Enviada'),
        ('offer_accepted', 'Oferta Aceptada'),
        ('offer_rejected', 'Oferta Rechazada'),
        ('document_request', 'Solicitud de Documentos'),
        ('background_check', 'Verificación de Antecedentes'),
        ('reference_request', 'Solicitud de Referencias'),
        ('workflow_stage_change', 'Cambio de Etapa'),
        ('deadline_reminder', 'Recordatorio de Fecha Límite'),
        ('task_assigned', 'Tarea Asignada'),
        ('task_completed', 'Tarea Completada'),
        ('assessment_invitation', 'Invitación a Evaluación'),
        ('feedback_request', 'Solicitud de Feedback'),
        ('status_update', 'Actualización de Estado'),
        ('system_alert', 'Alerta del Sistema'),
        ('custom', 'Personalizada')
    ]
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPE_CHOICES,
                                       db_index=True, help_text="Tipo de notificación")
    
    # === CANAL ESPECÍFICO ===
    channel = models.ForeignKey(NotificationChannel, on_delete=models.CASCADE,
                              related_name='templates',
                              help_text="Canal para el que está diseñado este template")
    
    # === CONTENIDO DEL TEMPLATE ===
    subject = models.CharField(max_length=300, blank=True,
                             help_text="Asunto (para email, etc.)")
    content = models.TextField(help_text="Contenido del mensaje con variables")
    
    # === CONTENIDO RICO ===
    html_content = models.TextField(blank=True,
                                  help_text="Contenido HTML (para email)")
    
    # === VARIABLES DISPONIBLES ===
    variables = models.JSONField(default=list, blank=True, help_text="""
    Variables disponibles en el template:
    [
        {
            'name': 'candidate_name',
            'type': 'string',
            'description': 'Nombre del candidato',
            'required': true,
            'default': ''
        },
        {
            'name': 'interview_date',
            'type': 'datetime',
            'description': 'Fecha de la entrevista',
            'required': false,
            'format': '%Y-%m-%d %H:%M'
        }
    ]
    """)
    
    # === CONFIGURACIÓN ESPECÍFICA ===
    config = models.JSONField(default=dict, blank=True, help_text="""
    Configuración específica del template:
    {
        'priority': 'normal',
        'expires_after_hours': 48,
        'requires_confirmation': false,
        'auto_retry': true,
        'track_opens': true,
        'track_clicks': true,
        'attachments_allowed': false,
        'formatting': {
            'markdown': true,
            'html': false,
            'emoji': true
        }
    }
    """)
    
    # === ESTADO ===
    is_active = models.BooleanField(default=True, db_index=True)
    is_default = models.BooleanField(default=False,
                                   help_text="¿Es el template por defecto para este tipo?")
    
    # === MÉTRICAS ===
    usage_count = models.PositiveIntegerField(default=0,
                                            help_text="Número de veces utilizado")
    success_rate = models.FloatField(default=0.0,
                                   validators=[MinValueValidator(0), MaxValueValidator(1)])
    
    # === TIMESTAMPS ===
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                 related_name='created_notification_templates')
    
    class Meta:
        verbose_name = "Template de Notificación"
        verbose_name_plural = "Templates de Notificación"
        ordering = ['notification_type', 'name']
        unique_together = ['channel', 'notification_type', 'name']
        indexes = [
            models.Index(fields=['notification_type', 'channel', 'is_active']),
            models.Index(fields=['is_default', 'usage_count']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.get_notification_type_display()} ({self.channel.channel_type})"
    
    def render(self, context: Dict[str, Any]) -> Dict[str, str]:
        """Renderiza el template con las variables del contexto."""
        import re
        
        # Renderizar subject
        rendered_subject = self.subject
        for var_name, var_value in context.items():
            pattern = r'\{\{\s*' + re.escape(var_name) + r'\s*\}\}'
            rendered_subject = re.sub(pattern, str(var_value), rendered_subject)
        
        # Renderizar content
        rendered_content = self.content
        for var_name, var_value in context.items():
            pattern = r'\{\{\s*' + re.escape(var_name) + r'\s*\}\}'
            rendered_content = re.sub(pattern, str(var_value), rendered_content)
        
        # Renderizar HTML content si existe
        rendered_html = ""
        if self.html_content:
            rendered_html = self.html_content
            for var_name, var_value in context.items():
                pattern = r'\{\{\s*' + re.escape(var_name) + r'\s*\}\}'
                rendered_html = re.sub(pattern, str(var_value), rendered_html)
        
        return {
            'subject': rendered_subject,
            'content': rendered_content,
            'html_content': rendered_html
        }
    
    def validate_context(self, context: Dict[str, Any]) -> List[str]:
        """Valida que el contexto tenga todas las variables requeridas."""
        errors = []
        
        for variable in self.variables:
            var_name = variable.get('name')
            required = variable.get('required', False)
            
            if required and var_name not in context:
                errors.append(f"Variable requerida '{var_name}' no encontrada")
        
        return errors
    
    def duplicate(self, new_name: str, channel=None):
        """Duplica el template con un nuevo nombre."""
        return NotificationTemplate.objects.create(
            name=new_name,
            description=f"Copia de {self.description}",
            notification_type=self.notification_type,
            channel=channel or self.channel,
            subject=self.subject,
            content=self.content,
            html_content=self.html_content,
            variables=self.variables.copy(),
            config=self.config.copy(),
            created_by=None
        )


class Notification(models.Model):
    """
    Notificación individual enviada o por enviar.
    """
    
    # === IDENTIFICACIÓN ===
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # === DESTINATARIO ===
    recipient = models.ForeignKey('Person', on_delete=models.CASCADE,
                                related_name='notifications',
                                help_text="Destinatario de la notificación")
    recipient_email = models.EmailField(blank=True,
                                      help_text="Email específico del destinatario")
    recipient_phone = models.CharField(max_length=20, blank=True,
                                     help_text="Teléfono específico del destinatario")
    
    # === TIPO Y CANAL ===
    notification_type = models.CharField(max_length=30,
                                       choices=NotificationTemplate.NOTIFICATION_TYPE_CHOICES,
                                       db_index=True)
    channel = models.ForeignKey(NotificationChannel, on_delete=models.CASCADE,
                              related_name='notifications')
    template = models.ForeignKey(NotificationTemplate, on_delete=models.SET_NULL,
                               null=True, blank=True,
                               related_name='notifications')
    
    # === PRIORIDAD ===
    PRIORITY_CHOICES = [
        ('low', 'Baja'),
        ('normal', 'Normal'),
        ('high', 'Alta'),
        ('urgent', 'Urgente'),
        ('critical', 'Crítica')
    ]
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES,
                              default='normal', db_index=True)
    
    # === CONTENIDO ===
    subject = models.CharField(max_length=300, blank=True)
    content = models.TextField(help_text="Contenido final de la notificación")
    html_content = models.TextField(blank=True, help_text="Contenido HTML")
    
    # === ESTADO ===
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('queued', 'En Cola'),
        ('sending', 'Enviando'),
        ('sent', 'Enviada'),
        ('delivered', 'Entregada'),
        ('failed', 'Falló'),
        ('cancelled', 'Cancelada'),
        ('expired', 'Expirada')
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES,
                            default='pending', db_index=True)
    
    # === DATOS ADICIONALES ===
    context_data = models.JSONField(default=dict, blank=True,
                                  help_text="Datos de contexto utilizados")
    metadata = models.JSONField(default=dict, blank=True,
                              help_text="Metadata adicional")
    
    # === CONTROL DE ENVÍO ===
    scheduled_for = models.DateTimeField(null=True, blank=True, db_index=True,
                                       help_text="Fecha programada para envío")
    expires_at = models.DateTimeField(null=True, blank=True, db_index=True,
                                    help_text="Fecha de expiración")
    
    # === REINTENTOS ===
    retry_count = models.PositiveSmallIntegerField(default=0,
                                                 help_text="Número de intentos realizados")
    max_retries = models.PositiveSmallIntegerField(default=3,
                                                 help_text="Máximo número de reintentos")
    next_retry_at = models.DateTimeField(null=True, blank=True,
                                       help_text="Próximo intento programado")
    
    # === RESULTADOS ===
    sent_at = models.DateTimeField(null=True, blank=True, db_index=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True,
                                 help_text="Fecha de lectura/apertura")
    clicked_at = models.DateTimeField(null=True, blank=True,
                                    help_text="Fecha de clic en enlaces")
    
    # === ERRORES ===
    error_message = models.TextField(blank=True,
                                   help_text="Mensaje de error si falló")
    error_code = models.CharField(max_length=50, blank=True,
                                help_text="Código de error específico")
    
    # === RELACIONES ===
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                 related_name='created_notifications')
    workflow_instance = models.ForeignKey('WorkflowInstance', on_delete=models.SET_NULL,
                                        null=True, blank=True,
                                        related_name='notifications',
                                        help_text="Workflow asociado")
    
    # === TIMESTAMPS ===
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Notificación"
        verbose_name_plural = "Notificaciones"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'status']),
            models.Index(fields=['notification_type', 'channel']),
            models.Index(fields=['priority', 'scheduled_for']),
            models.Index(fields=['status', 'retry_count']),
            models.Index(fields=['expires_at', 'status']),
        ]
    
    def __str__(self):
        return f"{self.get_notification_type_display()} -> {self.recipient} ({self.get_status_display()})"
    
    def mark_as_sent(self):
        """Marca la notificación como enviada."""
        self.status = 'sent'
        self.sent_at = timezone.now()
        self.save(update_fields=['status', 'sent_at'])
        
        # Actualizar métricas del canal
        self.channel.update_metrics(success=True)
    
    def mark_as_delivered(self):
        """Marca la notificación como entregada."""
        self.status = 'delivered'
        self.delivered_at = timezone.now()
        self.save(update_fields=['status', 'delivered_at'])
    
    def mark_as_failed(self, error_message: str, error_code: str = ""):
        """Marca la notificación como fallida."""
        self.status = 'failed'
        self.error_message = error_message
        self.error_code = error_code
        self.save(update_fields=['status', 'error_message', 'error_code'])
        
        # Actualizar métricas del canal
        self.channel.update_metrics(success=False)
    
    def mark_as_read(self):
        """Marca la notificación como leída."""
        if not self.read_at:
            self.read_at = timezone.now()
            self.save(update_fields=['read_at'])
    
    def mark_as_clicked(self):
        """Marca que se hizo clic en la notificación."""
        if not self.clicked_at:
            self.clicked_at = timezone.now()
            self.save(update_fields=['clicked_at'])
    
    def schedule_retry(self):
        """Programa el siguiente intento de envío."""
        if self.retry_count >= self.max_retries:
            self.mark_as_failed("Maximum retries exceeded")
            return False
        
        delay = self.channel.get_retry_delay(self.retry_count)
        self.next_retry_at = timezone.now() + timezone.timedelta(seconds=delay)
        self.retry_count += 1
        self.status = 'queued'
        self.save(update_fields=['next_retry_at', 'retry_count', 'status'])
        return True
    
    def can_send_now(self) -> bool:
        """Verifica si la notificación puede enviarse ahora."""
        if self.status not in ['pending', 'queued']:
            return False
        
        if self.expires_at and timezone.now() > self.expires_at:
            self.status = 'expired'
            self.save(update_fields=['status'])
            return False
        
        if self.scheduled_for and timezone.now() < self.scheduled_for:
            return False
        
        return True
    
    def get_delivery_time(self) -> Optional[float]:
        """Calcula el tiempo de entrega en segundos."""
        if self.sent_at and self.delivered_at:
            return (self.delivered_at - self.sent_at).total_seconds()
        return None
    
    def get_read_time(self) -> Optional[float]:
        """Calcula el tiempo hasta lectura en segundos."""
        if self.sent_at and self.read_at:
            return (self.read_at - self.sent_at).total_seconds()
        return None


class NotificationQueue(models.Model):
    """
    Cola de procesamiento de notificaciones.
    """
    
    # === IDENTIFICACIÓN ===
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True,
                          help_text="Nombre de la cola")
    description = models.TextField(blank=True)
    
    # === CONFIGURACIÓN ===
    QUEUE_TYPE_CHOICES = [
        ('immediate', 'Inmediata'),
        ('batch', 'Por Lotes'),
        ('scheduled', 'Programada'),
        ('priority', 'Por Prioridad')
    ]
    queue_type = models.CharField(max_length=20, choices=QUEUE_TYPE_CHOICES,
                                default='immediate')
    
    # === LÍMITES DE PROCESAMIENTO ===
    max_concurrent_jobs = models.PositiveIntegerField(default=10,
                                                    help_text="Máximo de trabajos concurrentes")
    batch_size = models.PositiveIntegerField(default=50,
                                           help_text="Tamaño del lote para procesamiento")
    processing_interval_seconds = models.PositiveIntegerField(default=60,
                                                            help_text="Intervalo de procesamiento")
    
    # === ESTADO ===
    is_active = models.BooleanField(default=True, db_index=True)
    is_paused = models.BooleanField(default=False, db_index=True)
    
    # === MÉTRICAS ===
    total_processed = models.PositiveIntegerField(default=0)
    total_failed = models.PositiveIntegerField(default=0)
    current_queue_size = models.PositiveIntegerField(default=0)
    avg_processing_time = models.FloatField(default=0.0)
    
    # === TIMESTAMPS ===
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Cola de Notificaciones"
        verbose_name_plural = "Colas de Notificaciones"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_queue_type_display()})"
    
    def add_notification(self, notification: Notification):
        """Añade una notificación a la cola."""
        NotificationQueueItem.objects.create(
            queue=self,
            notification=notification,
            priority=self._calculate_priority(notification)
        )
        self.current_queue_size += 1
        self.save(update_fields=['current_queue_size'])
    
    def _calculate_priority(self, notification: Notification) -> int:
        """Calcula la prioridad numérica de una notificación."""
        priority_map = {
            'critical': 1,
            'urgent': 2,
            'high': 3,
            'normal': 4,
            'low': 5
        }
        return priority_map.get(notification.priority, 4)
    
    def get_next_batch(self) -> List[Notification]:
        """Obtiene el siguiente lote de notificaciones para procesar."""
        items = self.queue_items.filter(
            status='pending'
        ).order_by('priority', 'created_at')[:self.batch_size]
        
        return [item.notification for item in items]
    
    def mark_processed(self, notification: Notification, success: bool):
        """Marca una notificación como procesada."""
        try:
            item = self.queue_items.get(notification=notification)
            item.status = 'processed' if success else 'failed'
            item.processed_at = timezone.now()
            item.save()
            
            if success:
                self.total_processed += 1
            else:
                self.total_failed += 1
            
            self.current_queue_size = max(0, self.current_queue_size - 1)
            self.last_processed_at = timezone.now()
            self.save(update_fields=['total_processed', 'total_failed', 
                                   'current_queue_size', 'last_processed_at'])
        except NotificationQueueItem.DoesNotExist:
            pass


class NotificationQueueItem(models.Model):
    """
    Item individual en una cola de notificaciones.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    queue = models.ForeignKey(NotificationQueue, on_delete=models.CASCADE,
                            related_name='queue_items')
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE,
                                   related_name='queue_items')
    
    priority = models.PositiveSmallIntegerField(default=4,
                                              help_text="Prioridad numérica (1=más alta)")
    
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('processing', 'Procesando'),
        ('processed', 'Procesado'),
        ('failed', 'Falló')
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES,
                            default='pending', db_index=True)
    
    retry_count = models.PositiveSmallIntegerField(default=0)
    error_message = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Item de Cola"
        verbose_name_plural = "Items de Cola"
        ordering = ['priority', 'created_at']
        unique_together = ['queue', 'notification']
        indexes = [
            models.Index(fields=['queue', 'status', 'priority']),
        ]
    
    def __str__(self):
        return f"{self.queue.name} - {self.notification.id} (P:{self.priority})"