# app/ats/publish/models.py
from django.db import models
from django.utils import timezone
from django.conf import settings
from app.models import JobOpportunity

class ChannelType(models.Model):
    """
    Tipos de canales disponibles
    """
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField()
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class Channel(models.Model):
    """
    Representa un canal específico para publicación
    """
    type = models.ForeignKey(ChannelType, on_delete=models.CASCADE)
    identifier = models.CharField(max_length=255)  # ID único del canal
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    metadata = models.JSONField(default=dict)
    
    class Meta:
        unique_together = ('type', 'identifier')
    
    def __str__(self):
        return f"{self.type.name} - {self.name}"

class ChannelCredential(models.Model):
    """
    Credenciales específicas por canal
    """
    channel = models.OneToOneField(Channel, on_delete=models.CASCADE)
    api_key = models.CharField(max_length=255, blank=True)
    access_token = models.CharField(max_length=255, blank=True)
    secret_key = models.CharField(max_length=255, blank=True)
    webhook_url = models.URLField(blank=True)
    refresh_token = models.CharField(max_length=255, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def is_expired(self):
        return self.expires_at and self.expires_at < timezone.now()
    
    def update_credentials(self, credentials: dict):
        for key, value in credentials.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.save()

class ChannelAnalytics(models.Model):
    """
    Métricas por canal
    """
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE)
    date = models.DateField()
    impressions = models.IntegerField(default=0)
    clicks = models.IntegerField(default=0)
    engagement_rate = models.FloatField(default=0.0)
    followers_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('channel', 'date')

class ChannelSubscription(models.Model):
    """
    Suscripciones a canales por usuario
    """
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ('channel', 'user')

class Bot(models.Model):
    """
    Bots interactivos
    """
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    description = models.TextField()
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    metadata = models.JSONField(default=dict)
    
    def __str__(self):
        return self.name

class BotCommand(models.Model):
    """
    Comandos disponibles para el bot
    """
    bot = models.ForeignKey(Bot, on_delete=models.CASCADE)
    command = models.CharField(max_length=50)
    description = models.TextField()
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('bot', 'command')

class BotResponse(models.Model):
    """
    Respuestas predefinidas para comandos
    """
    command = models.ForeignKey(BotCommand, on_delete=models.CASCADE)
    response_type = models.CharField(max_length=50, choices=[
        ('text', 'Texto'),
        ('image', 'Imagen'),
        ('video', 'Video'),
        ('document', 'Documento'),
        ('interactive', 'Interactivo')
    ])
    content = models.TextField()
    media_url = models.URLField(blank=True)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

# ===== NUEVOS MODELOS PARA MARKETING AVANZADO =====

class MarketingCampaign(models.Model):
    """
    Campañas de marketing avanzadas con integración AURA
    """
    CAMPAIGN_TYPES = [
        ('launch', 'Lanzamiento'),
        ('awareness', 'Concienciación'),
        ('conversion', 'Conversión'),
        ('retention', 'Retención'),
        ('retargeting', 'Retargeting'),
        ('event', 'Evento'),
        ('webinar', 'Webinar'),
        ('content', 'Contenido'),
    ]
    
    CAMPAIGN_STATUS = [
        ('draft', 'Borrador'),
        ('scheduled', 'Programada'),
        ('active', 'Activa'),
        ('paused', 'Pausada'),
        ('completed', 'Completada'),
        ('cancelled', 'Cancelada'),
    ] 
    
    name = models.CharField(max_length=255)
    description = models.TextField()
    campaign_type = models.CharField(max_length=20, choices=CAMPAIGN_TYPES)
    status = models.CharField(max_length=20, choices=CAMPAIGN_STATUS, default='draft')
    
    # Fechas y programación
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Presupuesto y objetivos
    budget = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    target_leads = models.IntegerField(default=0)
    target_conversions = models.IntegerField(default=0)
    
    # Configuración AURA
    use_aura_segmentation = models.BooleanField(default=True)
    aura_segments = models.JSONField(default=list)  # Segmentos de AURA aplicados
    aura_predictions = models.JSONField(default=dict)  # Predicciones de AURA
    
    # Configuración de canales
    channels = models.ManyToManyField(Channel, through='CampaignChannel')
    
    # Métricas y resultados
    analytics = models.JSONField(default=dict)
    
    def __str__(self):
        return f"{self.name} ({self.get_campaign_type_display()})"
    
    def is_active(self):
        now = timezone.now()
        return self.status == 'active' and self.start_date <= now <= self.end_date
    
    def get_roi(self):
        """Calcula el ROI de la campaña"""
        if not self.budget or self.budget == 0:
            return 0
        revenue = self.analytics.get('revenue', 0)
        return ((revenue - float(self.budget)) / float(self.budget)) * 100

class CampaignChannel(models.Model):
    """
    Asociación entre campaña y canales con configuración específica
    """
    campaign = models.ForeignKey(MarketingCampaign, on_delete=models.CASCADE)
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pendiente'),
        ('scheduled', 'Programado'),
        ('published', 'Publicado'),
        ('failed', 'Fallido')
    ])
    scheduled_at = models.DateTimeField(null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    analytics = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('campaign', 'channel')

class AudienceSegment(models.Model):
    """
    Segmentos de audiencia creados con AURA
    """
    SEGMENT_TYPES = [
        ('demographic', 'Demográfico'),
        ('behavioral', 'Conductual'),
        ('professional', 'Profesional'),
        ('company', 'Empresa'),
        ('industry', 'Industria'),
        ('location', 'Ubicación'),
        ('aura_predicted', 'Predicción AURA'),
    ]
    
    name = models.CharField(max_length=255)
    description = models.TextField()
    segment_type = models.CharField(max_length=20, choices=SEGMENT_TYPES)
    
    # Criterios de segmentación
    criteria = models.JSONField(default=dict)
    
    # Datos de AURA
    aura_analysis = models.JSONField(default=dict)
    predicted_size = models.IntegerField(default=0)
    actual_size = models.IntegerField(default=0)
    
    # Configuración
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_segment_type_display()})"

class JobBoard(models.Model):
    """
    Plataformas de job boards para publicación
    """
    JOB_BOARD_TYPES = [
        ('indeed', 'Indeed'),
        ('glassdoor', 'Glassdoor'),
        ('monster', 'Monster'),
        ('ziprecruiter', 'ZipRecruiter'),
        ('careerbuilder', 'CareerBuilder'),
        ('simplyhired', 'SimplyHired'),
        ('dice', 'Dice'),
        ('angel_list', 'AngelList'),
        ('stack_overflow', 'Stack Overflow'),
        ('github_jobs', 'GitHub Jobs'),
        ('custom', 'Personalizado'),
    ]
    
    name = models.CharField(max_length=255)
    job_board_type = models.CharField(max_length=20, choices=JOB_BOARD_TYPES)
    api_endpoint = models.URLField(blank=True)
    api_key = models.CharField(max_length=255, blank=True)
    api_secret = models.CharField(max_length=255, blank=True)
    
    # Configuración
    active = models.BooleanField(default=True)
    auto_publish = models.BooleanField(default=False)
    sync_frequency = models.IntegerField(default=3600)  # segundos
    
    # Métricas
    total_posts = models.IntegerField(default=0)
    success_rate = models.FloatField(default=0.0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_job_board_type_display()})"

class RetargetingCampaign(models.Model):
    """
    Campañas de retargeting basadas en comportamiento
    """
    RETARGETING_TYPES = [
        ('website_visitors', 'Visitantes del Sitio'),
        ('email_opens', 'Aperturas de Email'),
        ('social_engagement', 'Engagement en Redes'),
        ('job_applications', 'Aplicaciones a Trabajos'),
        ('cart_abandonment', 'Abandono de Carrito'),
        ('aura_predicted', 'Predicción AURA'),
    ]
    
    name = models.CharField(max_length=255)
    description = models.TextField()
    retargeting_type = models.CharField(max_length=20, choices=RETARGETING_TYPES)
    
    # Configuración
    lookback_days = models.IntegerField(default=30)
    frequency_cap = models.IntegerField(default=3)  # veces por día
    budget = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Segmentos objetivo
    target_segments = models.ManyToManyField(AudienceSegment)
    
    # Estado
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_retargeting_type_display()})"

class GoogleCalendarIntegration(models.Model):
    """
    Integración con Google Calendar para calendarización
    """
    calendar_id = models.CharField(max_length=255)
    calendar_name = models.CharField(max_length=255)
    timezone = models.CharField(max_length=50, default='America/Mexico_City')
    
    # Configuración de sincronización
    sync_events = models.BooleanField(default=True)
    auto_schedule = models.BooleanField(default=False)
    
    # Credenciales
    access_token = models.CharField(max_length=255, blank=True)
    refresh_token = models.CharField(max_length=255, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.calendar_name} ({self.calendar_id})"

class MarketingEvent(models.Model):
    """
    Eventos de marketing programados en Google Calendar
    """
    EVENT_TYPES = [
        ('webinar', 'Webinar'),
        ('live_demo', 'Demo en Vivo'),
        ('workshop', 'Taller'),
        ('conference', 'Conferencia'),
        ('meetup', 'Meetup'),
        ('product_launch', 'Lanzamiento de Producto'),
        ('campaign_launch', 'Lanzamiento de Campaña'),
    ]
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    
    # Fechas
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    
    # Ubicación
    location = models.CharField(max_length=255, blank=True)
    is_virtual = models.BooleanField(default=True)
    meeting_url = models.URLField(blank=True)
    
    # Integración con Google Calendar
    google_calendar = models.ForeignKey(GoogleCalendarIntegration, on_delete=models.CASCADE, null=True, blank=True)
    google_event_id = models.CharField(max_length=255, blank=True)
    
    # Campaña asociada
    campaign = models.ForeignKey(MarketingCampaign, on_delete=models.CASCADE, null=True, blank=True)
    
    # Estado
    status = models.CharField(max_length=20, choices=[
        ('draft', 'Borrador'),
        ('scheduled', 'Programado'),
        ('live', 'En Vivo'),
        ('completed', 'Completado'),
        ('cancelled', 'Cancelado'),
    ], default='draft')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.title} ({self.get_event_type_display()})"

class ContentTemplate(models.Model):
    """
    Plantillas de contenido para campañas
    """
    TEMPLATE_TYPES = [
        ('email', 'Email'),
        ('social_post', 'Post de Redes'),
        ('ad_copy', 'Copia de Anuncio'),
        ('landing_page', 'Landing Page'),
        ('webinar', 'Webinar'),
        ('case_study', 'Caso de Éxito'),
    ]
    
    name = models.CharField(max_length=255)
    description = models.TextField()
    template_type = models.CharField(max_length=20, choices=TEMPLATE_TYPES)
    
    # Contenido
    subject = models.CharField(max_length=255, blank=True)
    content = models.TextField()
    variables = models.JSONField(default=list)  # Variables disponibles
    
    # Configuración
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_template_type_display()})"

class Campaign(models.Model):
    """
    Modelo para campañas de marketing y publicidad
    """
    name = models.CharField(max_length=255)
    description = models.TextField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=[
        ('draft', 'Borrador'),
        ('active', 'Activa'),
        ('completed', 'Completada'),
        ('cancelled', 'Cancelada')
    ], default='draft')
    budget = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    target_audience = models.JSONField(default=dict)
    analytics = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Integración con CVs ciegos
    enable_blind_integration = models.BooleanField(default=False)
    blind_content = models.JSONField(default=dict)
    last_updated = models.DateTimeField(null=True, blank=True)
    
    def update_blind_content(self, content: dict):
        """
        Actualiza el contenido para CVs ciegos
        """
        self.blind_content = content
        self.last_updated = timezone.now()
        self.save()
    
    def is_active(self):
        """
        Verifica si la campaña está activa
        """
        now = timezone.now()
        return self.status == 'active' and self.start_date <= now <= self.end_date

    def __str__(self):
        return self.name

class CampaignApproval(models.Model):
    """
    Modelo para workflow de aprobación y firma digital de campañas.
    """
    APPROVAL_STATUS_CHOICES = [
        ('pending', 'Pendiente de Aprobación'),
        ('reviewing', 'En Revisión'),
        ('approved', 'Aprobada'),
        ('rejected', 'Rechazada'),
        ('expired', 'Expirada'),
        ('cancelled', 'Cancelada'),
    ]
    
    APPROVAL_LEVEL_CHOICES = [
        ('consultant', 'Consultor'),
        ('supervisor', 'Supervisor'),
        ('admin', 'Administrador'),
        ('system', 'Sistema Automático'),
    ]
    
    # Relación con la campaña
    campaign = models.ForeignKey(
        MarketingCampaign, 
        on_delete=models.CASCADE,
        related_name='approvals'
    )
    
    # Estado del workflow
    status = models.CharField(
        max_length=20,
        choices=APPROVAL_STATUS_CHOICES,
        default='pending'
    )
    
    # Nivel de aprobación requerido
    required_level = models.CharField(
        max_length=20,
        choices=APPROVAL_LEVEL_CHOICES,
        default='consultant'
    )
    
    # Usuarios involucrados
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='campaign_approvals_created'
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='campaign_approvals_reviewed'
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='campaign_approvals_approved'
    )
    
    # Fechas del workflow
    created_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    # Comentarios y feedback
    submission_notes = models.TextField(blank=True)
    review_notes = models.TextField(blank=True)
    approval_notes = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)
    
    # Firma digital
    digital_signature = models.TextField(blank=True)  # Hash de la firma
    signature_timestamp = models.DateTimeField(null=True, blank=True)
    signature_ip = models.GenericIPAddressField(null=True, blank=True)
    signature_user_agent = models.TextField(blank=True)
    
    # Metadata para auditoría
    approval_metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Aprobación de Campaña'
        verbose_name_plural = 'Aprobaciones de Campañas'
    
    def __str__(self):
        return f"Aprobación {self.id} - {self.campaign.name} ({self.get_status_display()})"
    
    def generate_digital_signature(self, user, ip_address=None, user_agent=None):
        """
        Genera firma digital para la aprobación.
        """
        import hashlib
        import json
        from django.utils import timezone
        
        # Crear payload para la firma
        payload = {
            'campaign_id': self.campaign.id,
            'approval_id': self.id,
            'user_id': user.id,
            'username': user.username,
            'timestamp': timezone.now().isoformat(),
            'status': self.status,
            'campaign_content_hash': self._get_campaign_content_hash()
        }
        
        # Generar hash
        signature_data = json.dumps(payload, sort_keys=True)
        signature_hash = hashlib.sha256(signature_data.encode()).hexdigest()
        
        # Guardar firma
        self.digital_signature = signature_hash
        self.signature_timestamp = timezone.now()
        self.signature_ip = ip_address
        self.signature_user_agent = user_agent
        self.approval_metadata['signature_payload'] = payload
        
        self.save()
        
        return signature_hash
    
    def _get_campaign_content_hash(self):
        """
        Genera hash del contenido de la campaña para integridad.
        """
        import hashlib
        import json
        
        content_data = {
            'name': self.campaign.name,
            'description': self.campaign.description,
            'campaign_type': self.campaign.campaign_type,
            'target_segments': list(self.campaign.target_segments.values_list('id', flat=True)),
            'content_templates': list(self.campaign.content_templates.values_list('id', flat=True)),
            'scheduled_date': self.campaign.scheduled_date.isoformat() if self.campaign.scheduled_date else None,
            'budget': str(self.campaign.budget) if self.campaign.budget else None
        }
        
        content_json = json.dumps(content_data, sort_keys=True)
        return hashlib.sha256(content_json.encode()).hexdigest()
    
    def can_be_approved_by(self, user):
        """
        Verifica si un usuario puede aprobar esta campaña.
        """
        from django.contrib.auth.models import Group
        
        # Superusuarios pueden aprobar todo
        if user.is_superuser:
            return True
        
        # Verificar nivel de aprobación requerido
        if self.required_level == 'system':
            return False  # Solo el sistema puede aprobar
        
        # Verificar grupos de usuario
        user_groups = user.groups.all()
        
        if self.required_level == 'admin':
            return user_groups.filter(name='Administradores').exists()
        elif self.required_level == 'supervisor':
            return user_groups.filter(name__in=['Administradores', 'Supervisores']).exists()
        elif self.required_level == 'consultant':
            return user_groups.filter(name__in=['Administradores', 'Supervisores', 'Consultores']).exists()
        
        return False
    
    def approve(self, user, notes='', ip_address=None, user_agent=None):
        """
        Aprueba la campaña.
        """
        from django.utils import timezone
        
        if not self.can_be_approved_by(user):
            raise PermissionError("No tienes permisos para aprobar esta campaña")
        
        self.status = 'approved'
        self.approved_by = user
        self.approved_at = timezone.now()
        self.approval_notes = notes
        
        # Generar firma digital
        self.generate_digital_signature(user, ip_address, user_agent)
        
        # Activar la campaña
        self.campaign.status = 'active'
        self.campaign.save()
        
        self.save()
        
        return True
    
    def reject(self, user, reason='', ip_address=None, user_agent=None):
        """
        Rechaza la campaña.
        """
        from django.utils import timezone
        
        if not self.can_be_approved_by(user):
            raise PermissionError("No tienes permisos para rechazar esta campaña")
        
        self.status = 'rejected'
        self.reviewed_by = user
        self.reviewed_at = timezone.now()
        self.rejection_reason = reason
        
        # Generar firma digital
        self.generate_digital_signature(user, ip_address, user_agent)
        
        self.save()
        
        return True

class CampaignMetrics(models.Model):
    """
    Modelo para métricas avanzadas de campañas.
    """
    # Relación con la campaña
    campaign = models.ForeignKey(
        MarketingCampaign,
        on_delete=models.CASCADE,
        related_name='metrics'
    )
    
    # Métricas de alcance
    total_sent = models.IntegerField(default=0)
    total_delivered = models.IntegerField(default=0)
    total_opened = models.IntegerField(default=0)
    total_clicked = models.IntegerField(default=0)
    total_converted = models.IntegerField(default=0)
    
    # Métricas de engagement
    open_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    click_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    conversion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    engagement_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Métricas de ROI
    total_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    roi = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    cost_per_conversion = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Métricas de audiencia
    unique_recipients = models.IntegerField(default=0)
    new_subscribers = models.IntegerField(default=0)
    unsubscribes = models.IntegerField(default=0)
    bounces = models.IntegerField(default=0)
    
    # Métricas de timing
    best_send_time = models.TimeField(null=True, blank=True)
    best_day_of_week = models.IntegerField(null=True, blank=True)  # 0=Monday, 6=Sunday
    average_open_time = models.DurationField(null=True, blank=True)
    
    # Métricas de contenido
    most_clicked_link = models.URLField(blank=True)
    most_engaged_segment = models.ForeignKey(
        AudienceSegment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='most_engaged_campaigns'
    )
    
    # Métricas de AURA
    aura_prediction_accuracy = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    aura_optimization_impact = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    aura_recommendation_followed = models.BooleanField(default=False)
    
    # Fechas de medición
    measurement_date = models.DateField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    # Metadata adicional
    metrics_metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-measurement_date']
        verbose_name = 'Métrica de Campaña'
        verbose_name_plural = 'Métricas de Campañas'
        unique_together = ['campaign', 'measurement_date']
    
    def __str__(self):
        return f"Métricas {self.campaign.name} - {self.measurement_date}"
    
    def calculate_engagement_score(self):
        """
        Calcula score de engagement basado en múltiples factores.
        """
        # Fórmula: (open_rate * 0.3) + (click_rate * 0.4) + (conversion_rate * 0.3)
        self.engagement_score = (
            self.open_rate * 0.3 +
            self.click_rate * 0.4 +
            self.conversion_rate * 0.3
        )
        return self.engagement_score
    
    def calculate_roi(self):
        """
        Calcula ROI de la campaña.
        """
        if self.total_spent > 0:
            self.roi = ((self.total_revenue - self.total_spent) / self.total_spent) * 100
        return self.roi
    
    def calculate_cost_per_conversion(self):
        """
        Calcula costo por conversión.
        """
        if self.total_converted > 0:
            self.cost_per_conversion = self.total_spent / self.total_converted
        return self.cost_per_conversion
    
    def update_metrics(self, new_data):
        """
        Actualiza métricas con nuevos datos.
        """
        for key, value in new_data.items():
            if hasattr(self, key):
                setattr(self, key, value)
        
        # Recalcular métricas derivadas
        self.calculate_engagement_score()
        self.calculate_roi()
        self.calculate_cost_per_conversion()
        
        self.save()

class CampaignAuditLog(models.Model):
    """
    Modelo para auditoría completa de campañas.
    """
    ACTION_CHOICES = [
        ('created', 'Creada'),
        ('updated', 'Actualizada'),
        ('submitted', 'Enviada para Aprobación'),
        ('reviewed', 'Revisada'),
        ('approved', 'Aprobada'),
        ('rejected', 'Rechazada'),
        ('activated', 'Activada'),
        ('paused', 'Pausada'),
        ('cancelled', 'Cancelada'),
        ('completed', 'Completada'),
        ('metrics_updated', 'Métricas Actualizadas'),
    ]
    
    # Relación con la campaña
    campaign = models.ForeignKey(
        MarketingCampaign,
        on_delete=models.CASCADE,
        related_name='audit_logs'
    )
    
    # Usuario que realizó la acción
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    # Detalles de la acción
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    action_timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Cambios realizados
    previous_state = models.JSONField(default=dict, blank=True)
    new_state = models.JSONField(default=dict, blank=True)
    changes_summary = models.TextField(blank=True)
    
    # Comentarios adicionales
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-action_timestamp']
        verbose_name = 'Log de Auditoría de Campaña'
        verbose_name_plural = 'Logs de Auditoría de Campañas'
    
    def __str__(self):
        return f"{self.campaign.name} - {self.get_action_display()} - {self.action_timestamp}"
    
    @classmethod
    def log_action(cls, campaign, user, action, previous_state=None, new_state=None, notes='', ip_address=None, user_agent=None):
        """Método de clase para registrar acciones de auditoría"""
        return cls.objects.create(
            campaign=campaign,
            user=user,
            action=action,
            previous_state=previous_state or {},
            new_state=new_state or {},
            notes=notes,
            ip_address=ip_address,
            user_agent=user_agent
        )

# ===== NUEVOS MODELOS PARA ANÁLISIS DE DOMINIOS Y FRECUENCIA =====

class DomainAnalysis(models.Model):
    """
    Análisis avanzado de dominios para prospección inteligente
    """
    DOMAIN_STATUS_CHOICES = [
        ('active', 'Activo'),
        ('inactive', 'Inactivo'),
        ('prospect', 'Prospecto'),
        ('client', 'Cliente'),
        ('churned', 'Perdido'),
        ('high_potential', 'Alto Potencial'),
    ]
    
    DOMAIN_INDUSTRY_CHOICES = [
        ('technology', 'Tecnología'),
        ('healthcare', 'Salud'),
        ('finance', 'Finanzas'),
        ('manufacturing', 'Manufactura'),
        ('retail', 'Retail'),
        ('education', 'Educación'),
        ('consulting', 'Consultoría'),
        ('startup', 'Startup'),
        ('enterprise', 'Empresa'),
        ('other', 'Otro'),
    ]
    
    # Información del dominio
    domain = models.CharField(max_length=255, unique=True)
    company_name = models.CharField(max_length=255)
    industry = models.CharField(max_length=20, choices=DOMAIN_INDUSTRY_CHOICES)
    status = models.CharField(max_length=20, choices=DOMAIN_STATUS_CHOICES, default='prospect')
    
    # Análisis de frecuencia y uso
    scraping_frequency = models.IntegerField(default=0)  # Veces que se ha hecho scraping
    last_scraping_date = models.DateTimeField(null=True, blank=True)
    total_vacancies_found = models.IntegerField(default=0)
    active_vacancies = models.IntegerField(default=0)
    
    # Métricas de engagement
    email_open_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    click_through_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    response_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Análisis AURA
    aura_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    aura_predictions = models.JSONField(default=dict)
    aura_recommendations = models.JSONField(default=list)
    
    # Información de contacto
    contact_emails = models.JSONField(default=list)
    contact_phones = models.JSONField(default=list)
    decision_makers = models.JSONField(default=list)
    
    # Historial de interacciones
    interaction_history = models.JSONField(default=list)
    last_contact_date = models.DateTimeField(null=True, blank=True)
    next_contact_date = models.DateTimeField(null=True, blank=True)
    
    # Scoring y priorización
    prospect_score = models.IntegerField(default=0)  # 0-100
    urgency_score = models.IntegerField(default=0)  # 0-100
    potential_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Configuración de campañas
    campaign_preferences = models.JSONField(default=dict)
    communication_preferences = models.JSONField(default=dict)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_analyzed = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-prospect_score', '-last_contact_date']
        verbose_name = 'Análisis de Dominio'
        verbose_name_plural = 'Análisis de Dominios'
    
    def __str__(self):
        return f"{self.company_name} ({self.domain}) - Score: {self.prospect_score}"
    
    def calculate_prospect_score(self):
        """Calcula el score de prospecto basado en múltiples factores"""
        score = 0
        
        # Frecuencia de scraping (indica actividad)
        if self.scraping_frequency > 10:
            score += 20
        elif self.scraping_frequency > 5:
            score += 15
        elif self.scraping_frequency > 0:
            score += 10
        
        # Vacantes activas (indica necesidad)
        if self.active_vacancies > 20:
            score += 25
        elif self.active_vacancies > 10:
            score += 20
        elif self.active_vacancies > 5:
            score += 15
        
        # Engagement (indica interés)
        if self.email_open_rate > 30:
            score += 15
        elif self.email_open_rate > 15:
            score += 10
        
        if self.click_through_rate > 5:
            score += 10
        elif self.click_through_rate > 2:
            score += 5
        
        # Score AURA
        score += int(self.aura_score * 20)
        
        # Recency (contacto reciente)
        if self.last_contact_date:
            days_since_contact = (timezone.now() - self.last_contact_date).days
            if days_since_contact < 7:
                score += 10
            elif days_since_contact < 30:
                score += 5
        
        self.prospect_score = min(score, 100)
        return self.prospect_score
    
    def get_next_action(self):
        """Determina la siguiente acción recomendada"""
        if self.prospect_score >= 80:
            return 'immediate_contact'
        elif self.prospect_score >= 60:
            return 'schedule_demo'
        elif self.prospect_score >= 40:
            return 'send_nurture_email'
        else:
            return 'research_more'

class UsageFrequencyAnalysis(models.Model):
    """
    Análisis de frecuencia de uso del sistema por clientes
    """
    FREQUENCY_LEVEL_CHOICES = [
        ('very_high', 'Muy Alta'),
        ('high', 'Alta'),
        ('medium', 'Media'),
        ('low', 'Baja'),
        ('very_low', 'Muy Baja'),
        ('inactive', 'Inactivo'),
    ]
    
    # Relación con el dominio
    domain_analysis = models.ForeignKey(DomainAnalysis, on_delete=models.CASCADE, related_name='usage_analyses')
    
    # Métricas de uso
    login_frequency = models.IntegerField(default=0)  # Logins por mes
    feature_usage = models.JSONField(default=dict)  # Uso de características específicas
    session_duration = models.DurationField(null=True, blank=True)
    last_login = models.DateTimeField(null=True, blank=True)
    
    # Análisis de comportamiento
    usage_pattern = models.CharField(max_length=20, choices=FREQUENCY_LEVEL_CHOICES)
    preferred_features = models.JSONField(default=list)
    pain_points = models.JSONField(default=list)
    
    # Métricas de satisfacción
    satisfaction_score = models.DecimalField(max_digits=3, decimal_places=1, default=0)
    nps_score = models.IntegerField(null=True, blank=True)
    feedback_sentiment = models.CharField(max_length=20, default='neutral')
    
    # Análisis de retención
    churn_risk = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    retention_probability = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    
    # Recomendaciones de cross-selling
    cross_sell_opportunities = models.JSONField(default=list)
    upsell_potential = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Fechas
    analysis_date = models.DateField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-analysis_date']
        verbose_name = 'Análisis de Frecuencia de Uso'
        verbose_name_plural = 'Análisis de Frecuencias de Uso'
    
    def __str__(self):
        return f"{self.domain_analysis.company_name} - {self.get_usage_pattern_display()} - {self.analysis_date}"
    
    def calculate_churn_risk(self):
        """Calcula el riesgo de churn basado en patrones de uso"""
        risk = 0
        
        # Frecuencia de login
        if self.login_frequency == 0:
            risk += 0.8
        elif self.login_frequency < 5:
            risk += 0.6
        elif self.login_frequency < 10:
            risk += 0.3
        
        # Último login
        if self.last_login:
            days_since_login = (timezone.now() - self.last_login).days
            if days_since_login > 90:
                risk += 0.7
            elif days_since_login > 60:
                risk += 0.5
            elif days_since_login > 30:
                risk += 0.3
        
        # Satisfacción
        if self.satisfaction_score < 3:
            risk += 0.4
        elif self.satisfaction_score < 4:
            risk += 0.2
        
        self.churn_risk = min(risk, 1.0)
        self.retention_probability = 1 - self.churn_risk
        return self.churn_risk

class IntelligentProspecting(models.Model):
    """
    Sistema de prospección inteligente basado en análisis de dominios
    """
    PROSPECTING_STATUS_CHOICES = [
        ('research', 'Investigación'),
        ('qualified', 'Calificado'),
        ('contacted', 'Contactado'),
        ('meeting_scheduled', 'Reunión Programada'),
        ('proposal_sent', 'Propuesta Enviada'),
        ('negotiating', 'Negociando'),
        ('closed_won', 'Cerrado - Ganado'),
        ('closed_lost', 'Cerrado - Perdido'),
        ('nurturing', 'Nutriendo'),
    ]
    
    # Información del prospecto
    domain_analysis = models.ForeignKey(DomainAnalysis, on_delete=models.CASCADE, related_name='prospecting_efforts')
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Estado del proceso
    status = models.CharField(max_length=20, choices=PROSPECTING_STATUS_CHOICES, default='research')
    priority = models.CharField(max_length=10, choices=[
        ('high', 'Alta'),
        ('medium', 'Media'),
        ('low', 'Baja'),
    ], default='medium')
    
    # Información de contacto
    primary_contact = models.JSONField(default=dict)
    contact_history = models.JSONField(default=list)
    next_action = models.TextField(blank=True)
    next_action_date = models.DateTimeField(null=True, blank=True)
    
    # Análisis AURA para prospección
    aura_prospecting_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    aura_recommendations = models.JSONField(default=list)
    best_approach = models.CharField(max_length=50, blank=True)
    
    # Campañas aplicadas
    campaigns_applied = models.ManyToManyField(MarketingCampaign, blank=True)
    campaign_results = models.JSONField(default=dict)
    
    # Valor estimado
    estimated_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    probability_of_win = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    
    # Fechas
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_activity = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-priority', '-aura_prospecting_score', '-last_activity']
        verbose_name = 'Prospección Inteligente'
        verbose_name_plural = 'Prospecciones Inteligentes'
    
    def __str__(self):
        return f"{self.domain_analysis.company_name} - {self.get_status_display()} - Score: {self.aura_prospecting_score}"

class CrossSellingOpportunity(models.Model):
    """
    Oportunidades de cross-selling basadas en análisis de uso
    """
    OPPORTUNITY_TYPE_CHOICES = [
        ('feature_upgrade', 'Actualización de Característica'),
        ('service_expansion', 'Expansión de Servicio'),
        ('addon_purchase', 'Compra de Add-on'),
        ('plan_upgrade', 'Actualización de Plan'),
        ('new_service', 'Nuevo Servicio'),
        ('consulting', 'Consultoría'),
        ('training', 'Capacitación'),
    ]
    
    PRIORITY_CHOICES = [
        ('critical', 'Crítico'),
        ('high', 'Alto'),
        ('medium', 'Medio'),
        ('low', 'Bajo'),
    ]
    
    # Relación con el análisis de uso
    usage_analysis = models.ForeignKey(UsageFrequencyAnalysis, on_delete=models.CASCADE, related_name='cross_selling_opportunities')
    
    # Información de la oportunidad
    opportunity_type = models.CharField(max_length=20, choices=OPPORTUNITY_TYPE_CHOICES)
    title = models.CharField(max_length=255)
    description = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    
    # Análisis AURA
    aura_relevance_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    aura_timing_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    aura_approach_recommendation = models.JSONField(default=dict)
    
    # Valor y probabilidad
    estimated_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    probability_of_success = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    
    # Estado
    status = models.CharField(max_length=20, choices=[
        ('identified', 'Identificada'),
        ('presented', 'Presentada'),
        ('negotiating', 'Negociando'),
        ('closed_won', 'Cerrada - Ganada'),
        ('closed_lost', 'Cerrada - Perdida'),
        ('postponed', 'Pospuesta'),
    ], default='identified')
    
    # Campañas asociadas
    campaigns = models.ManyToManyField(MarketingCampaign, blank=True)
    
    # Fechas
    identified_date = models.DateTimeField(auto_now_add=True)
    presented_date = models.DateTimeField(null=True, blank=True)
    expected_close_date = models.DateTimeField(null=True, blank=True)
    closed_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-priority', '-aura_relevance_score', '-estimated_value']
        verbose_name = 'Oportunidad de Cross-Selling'
        verbose_name_plural = 'Oportunidades de Cross-Selling'
    
    def __str__(self):
        return f"{self.usage_analysis.domain_analysis.company_name} - {self.title} - {self.get_opportunity_type_display()}"

# ===== MODELOS PARA GANTT CHART DE EJECUCIÓN =====

class CampaignExecutionPhase(models.Model):
    """
    Fases de ejecución de campañas para el Gantt chart
    """
    PHASE_TYPES = [
        ('planning', 'Planificación'),
        ('preparation', 'Preparación'),
        ('execution', 'Ejecución'),
        ('monitoring', 'Monitoreo'),
        ('optimization', 'Optimización'),
        ('analysis', 'Análisis'),
        ('follow_up', 'Seguimiento'),
    ]
    
    # Relación con la campaña
    campaign = models.ForeignKey(MarketingCampaign, on_delete=models.CASCADE, related_name='execution_phases')
    
    # Información de la fase
    name = models.CharField(max_length=255)
    description = models.TextField()
    phase_type = models.CharField(max_length=20, choices=PHASE_TYPES)
    
    # Fechas de ejecución
    planned_start = models.DateTimeField()
    planned_end = models.DateTimeField()
    actual_start = models.DateTimeField(null=True, blank=True)
    actual_end = models.DateTimeField(null=True, blank=True)
    
    # Dependencias
    dependencies = models.ManyToManyField('self', blank=True, symmetrical=False)
    
    # Estado
    status = models.CharField(max_length=20, choices=[
        ('not_started', 'No Iniciada'),
        ('in_progress', 'En Progreso'),
        ('completed', 'Completada'),
        ('delayed', 'Retrasada'),
        ('cancelled', 'Cancelada'),
    ], default='not_started')
    
    # Progreso
    progress_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Recursos asignados
    assigned_users = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True)
    required_resources = models.JSONField(default=list)
    
    # Métricas de la fase
    phase_metrics = models.JSONField(default=dict)
    
    # Orden de ejecución
    execution_order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['campaign', 'execution_order', 'planned_start']
        verbose_name = 'Fase de Ejecución'
        verbose_name_plural = 'Fases de Ejecución'
    
    def __str__(self):
        return f"{self.campaign.name} - {self.name} ({self.get_status_display()})"
    
    def is_delayed(self):
        """Verifica si la fase está retrasada"""
        if self.status == 'not_started' and timezone.now() > self.planned_start:
            return True
        if self.status == 'in_progress' and timezone.now() > self.planned_end:
            return True
        return False
    
    def calculate_progress(self):
        """Calcula el progreso de la fase"""
        if self.status == 'completed':
            self.progress_percentage = 100
        elif self.status == 'not_started':
            self.progress_percentage = 0
        elif self.status == 'in_progress':
            if self.planned_start and self.planned_end:
                total_duration = (self.planned_end - self.planned_start).total_seconds()
                elapsed = (timezone.now() - self.planned_start).total_seconds()
                if total_duration > 0:
                    self.progress_percentage = min((elapsed / total_duration) * 100, 100)
        
        return self.progress_percentage

class CampaignTask(models.Model):
    """
    Tareas específicas dentro de cada fase de ejecución
    """
    TASK_TYPES = [
        ('content_creation', 'Creación de Contenido'),
        ('design', 'Diseño'),
        ('scheduling', 'Programación'),
        ('publishing', 'Publicación'),
        ('monitoring', 'Monitoreo'),
        ('analysis', 'Análisis'),
        ('optimization', 'Optimización'),
        ('communication', 'Comunicación'),
        ('coordination', 'Coordinación'),
    ]
    
    PRIORITY_CHOICES = [
        ('critical', 'Crítico'),
        ('high', 'Alto'),
        ('medium', 'Medio'),
        ('low', 'Bajo'),
    ]
    
    # Relación con la fase
    phase = models.ForeignKey(CampaignExecutionPhase, on_delete=models.CASCADE, related_name='tasks')
    
    # Información de la tarea
    title = models.CharField(max_length=255)
    description = models.TextField()
    task_type = models.CharField(max_length=20, choices=TASK_TYPES)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    
    # Fechas
    planned_start = models.DateTimeField()
    planned_end = models.DateTimeField()
    actual_start = models.DateTimeField(null=True, blank=True)
    actual_end = models.DateTimeField(null=True, blank=True)
    
    # Estado
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pendiente'),
        ('in_progress', 'En Progreso'),
        ('completed', 'Completada'),
        ('blocked', 'Bloqueada'),
        ('cancelled', 'Cancelada'),
    ], default='pending')
    
    # Asignación
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Dependencias
    dependencies = models.ManyToManyField('self', blank=True, symmetrical=False)
    
    # Progreso y métricas
    progress_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    estimated_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    actual_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Comentarios y notas
    notes = models.TextField(blank=True)
    completion_notes = models.TextField(blank=True)
    
    # Orden dentro de la fase
    task_order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['phase', 'task_order', 'planned_start']
        verbose_name = 'Tarea de Campaña'
        verbose_name_plural = 'Tareas de Campaña'
    
    def __str__(self):
        return f"{self.phase.name} - {self.title} ({self.get_status_display()})"
    
    def is_overdue(self):
        """Verifica si la tarea está vencida"""
        if self.status in ['pending', 'in_progress'] and timezone.now() > self.planned_end:
            return True
        return False
    
    def can_start(self):
        """Verifica si la tarea puede iniciar (dependencias cumplidas)"""
        for dependency in self.dependencies.all():
            if dependency.status != 'completed':
                return False
        return True

class CampaignMilestone(models.Model):
    """
    Hitos importantes en la ejecución de campañas
    """
    MILESTONE_TYPES = [
        ('kickoff', 'Inicio'),
        ('content_ready', 'Contenido Listo'),
        ('launch', 'Lanzamiento'),
        ('first_results', 'Primeros Resultados'),
        ('optimization', 'Optimización'),
        ('completion', 'Finalización'),
        ('analysis', 'Análisis Final'),
    ]
    
    # Relación con la campaña
    campaign = models.ForeignKey(MarketingCampaign, on_delete=models.CASCADE, related_name='milestones')
    
    # Información del hito
    name = models.CharField(max_length=255)
    description = models.TextField()
    milestone_type = models.CharField(max_length=20, choices=MILESTONE_TYPES)
    
    # Fecha objetivo
    target_date = models.DateTimeField()
    actual_date = models.DateTimeField(null=True, blank=True)
    
    # Estado
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pendiente'),
        ('achieved', 'Alcanzado'),
        ('missed', 'Perdido'),
        ('cancelled', 'Cancelado'),
    ], default='pending')
    
    # Métricas del hito
    milestone_metrics = models.JSONField(default=dict)
    
    # Comentarios
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['campaign', 'target_date']
        verbose_name = 'Hito de Campaña'
        verbose_name_plural = 'Hitos de Campaña'
    
    def __str__(self):
        return f"{self.campaign.name} - {self.name} ({self.get_status_display()})"
    
    def is_achieved(self):
        """Verifica si el hito ha sido alcanzado"""
        return self.status == 'achieved' and self.actual_date is not None
    
    def is_missed(self):
        """Verifica si el hito se ha perdido"""
        return self.status == 'pending' and timezone.now() > self.target_date

class CampaignGanttView(models.Model):
    """
    Vista configurada del Gantt chart para campañas
    """
    VIEW_TYPES = [
        ('timeline', 'Línea de Tiempo'),
        ('phases', 'Por Fases'),
        ('tasks', 'Por Tareas'),
        ('resources', 'Por Recursos'),
        ('milestones', 'Por Hitos'),
    ]
    
    # Configuración de la vista
    name = models.CharField(max_length=255)
    description = models.TextField()
    view_type = models.CharField(max_length=20, choices=VIEW_TYPES)
    
    # Campañas incluidas
    campaigns = models.ManyToManyField(MarketingCampaign, blank=True)
    
    # Configuración de visualización
    start_date = models.DateField()
    end_date = models.DateField()
    show_dependencies = models.BooleanField(default=True)
    show_critical_path = models.BooleanField(default=True)
    show_progress = models.BooleanField(default=True)
    
    # Filtros
    filters = models.JSONField(default=dict)
    
    # Configuración de colores
    color_scheme = models.JSONField(default=dict)
    
    # Usuario que creó la vista
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    # Fechas
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Vista Gantt de Campaña'
        verbose_name_plural = 'Vistas Gantt de Campañas'
    
    def __str__(self):
        return f"{self.name} ({self.get_view_type_display()})"
    
    def get_gantt_data(self):
        """Genera los datos para el Gantt chart"""
        gantt_data = {
            'phases': [],
            'tasks': [],
            'milestones': [],
            'dependencies': []
        }
        
        for campaign in self.campaigns.all():
            # Fases
            for phase in campaign.execution_phases.all():
                gantt_data['phases'].append({
                    'id': f"phase_{phase.id}",
                    'name': phase.name,
                    'start': phase.planned_start.isoformat(),
                    'end': phase.planned_end.isoformat(),
                    'progress': float(phase.progress_percentage),
                    'status': phase.status,
                    'campaign': campaign.name
                })
                
                # Tareas de la fase
                for task in phase.tasks.all():
                    gantt_data['tasks'].append({
                        'id': f"task_{task.id}",
                        'name': task.title,
                        'start': task.planned_start.isoformat(),
                        'end': task.planned_end.isoformat(),
                        'progress': float(task.progress_percentage),
                        'status': task.status,
                        'phase': phase.name,
                        'assigned_to': task.assigned_to.username if task.assigned_to else None
                    })
            
            # Hitos
            for milestone in campaign.milestones.all():
                gantt_data['milestones'].append({
                    'id': f"milestone_{milestone.id}",
                    'name': milestone.name,
                    'date': milestone.target_date.isoformat(),
                    'status': milestone.status,
                    'campaign': campaign.name
                })
        
        return gantt_data
