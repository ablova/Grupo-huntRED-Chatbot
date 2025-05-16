# app/models.py
    
from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.postgres.fields import ArrayField
from django.db.models import JSONField
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models.signals import post_save
from django.dispatch import receiver
from urllib.parse import urlparse
from asgiref.sync import sync_to_async
from django.contrib.auth.models import AbstractUser, BaseUserManager, User
from django.utils.translation import gettext_lazy as _
from datetime import datetime, timedelta
import re
import uuid
import logging
import requests
logger=logging.getLogger(__name__)
ROLE_CHOICES=[('SUPER_ADMIN','Super Administrador'),('BU_COMPLETE','Consultor BU Completo'),('BU_DIVISION','Consultor BU División')]

# Estados para Propuestas
PROPOSAL_STATUS_CHOICES = [
    ('DRAFT', 'Borrador'),
    ('SENT', 'Enviada'),
    ('ACCEPTED', 'Aceptada'),
    ('REJECTED', 'Rechazada')
]

# Estados para Contratos
CONTRATO_STATUS_CHOICES = [
    ('PENDING_APPROVAL', 'Pendiente de Aprobación'),
    ('APPROVED', 'Aprobado'),
    ('SIGNED', 'Firmado'),
    ('REJECTED', 'Rechazado')
]

# Eventos que activan hitos de pago
TRIGGER_EVENT_CHOICES = [
    ('CONTRACT_SIGNING', 'Firma del contrato'),
    ('START_DATE', 'Fecha de inicio'),
    ('MILESTONE_1', 'Hitos de proyecto'),
    ('CUSTOM_EVENT', 'Evento personalizado')
]

# Estados de pagos
PAYMENT_STATUS_CHOICES = [
    ('PENDING', 'Pendiente'),
    ('PAID', 'Pagado'),
    ('OVERDUE', 'Vencido'),
    ('CANCELLED', 'Cancelado')
]

# Estados de Feedback
FEEDBACK_STATUS_CHOICES = [
    ('PENDING', 'Pendiente'),
    ('COMPLETED', 'Completado'),
    ('SKIPPED', 'Omitido')
]

# Tipos de Feedback
FEEDBACK_TYPE_CHOICES = [
    ('INTERVIEW', 'Entrevista'),
    ('CANDIDATE', 'Candidato'),
    ('PROPOSAL', 'Propuesta'),
    ('HIRE', 'Contratación')
]

# Resultados de Feedback
FEEDBACK_RESULT_CHOICES = [
    ('YES', 'Sí'),
    ('NO', 'No'),
    ('PARTIAL', 'Parcial'),
    ('NOT_APPLICABLE', 'No Aplica')
]

# Permisos
PERMISSION_CHOICES=[('ALL_ACCESS','Acceso Total'),('BU_ACCESS','Acceso a BU'),('DIVISION_ACCESS','Acceso a División')]

# Canales de Notificación
NOTIFICATION_CHANNEL_CHOICES = [
    ('WHATSAPP', 'WhatsApp'),
    ('TELEGRAM', 'Telegram'),
    ('EMAIL', 'Email'),
    ('SLACK', 'Slack'),
    ('NTFY', 'ntfy.sh')
]

# Estados de Notificación
NOTIFICATION_STATUS_CHOICES = [
    ('PENDING', 'Pendiente'),
    ('SENT', 'Enviada'),
    ('DELIVERED', 'Entregada'),
    ('READ', 'Leída'),
    ('FAILED', 'Fallida')
]

# Tipos de Notificación
NOTIFICATION_TYPE_CHOICES = [
    ('FEEDBACK', 'Feedback'),
    ('MATCHING', 'Matching'),
    ('PROPOSAL', 'Propuesta'),
    ('HIRE', 'Contratación'),
    ('SYSTEM', 'Sistema')
]

class NotificationChannel(models.Model):
    """Modelo para configurar canales de notificación por Business Unit."""
    
    business_unit = models.ForeignKey(
        'BusinessUnit',
        on_delete=models.CASCADE,
        related_name='notification_channels',
        help_text="Business Unit asociada a este canal"
    )
    
    channel = models.CharField(
        max_length=20,
        choices=NOTIFICATION_CHANNEL_CHOICES,
        help_text="Canal de notificación"
    )
    
    enabled = models.BooleanField(
        default=True,
        help_text="¿Este canal está habilitado para esta BU?"
    )
    
    config = models.JSONField(
        default=dict,
        help_text="Configuración específica del canal (tokens, URLs, etc.)"
    )
    
    priority = models.IntegerField(
        default=10,
        help_text="Prioridad del canal (menor número = mayor prioridad)"
    )
    
    class Meta:
        verbose_name = "Canal de Notificación"
        verbose_name_plural = "Canales de Notificación"
        unique_together = ['business_unit', 'channel']
        ordering = ['business_unit', 'priority']
        
    def __str__(self):
        return f"{self.business_unit.name} - {self.channel}"

class Notification(models.Model):
    """Modelo para manejar todas las notificaciones del sistema."""
    
    recipient = models.ForeignKey(
        'Person',
        on_delete=models.CASCADE,
        related_name='notifications',
        help_text="Destinatario de la notificación"
    )
    
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPE_CHOICES,
        help_text="Tipo de notificación"
    )
    
    channel = models.CharField(
        max_length=20,
        choices=NOTIFICATION_CHANNEL_CHOICES,
        help_text="Canal utilizado para enviar la notificación"
    )
    
    status = models.CharField(
        max_length=20,
        choices=NOTIFICATION_STATUS_CHOICES,
        default='PENDING',
        help_text="Estado de la notificación"
    )
    
    content = models.TextField(
        help_text="Contenido de la notificación"
    )
    
    metadata = models.JSONField(
        default=dict,
        help_text="Datos adicionales de la notificación"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Notificación"
        verbose_name_plural = "Notificaciones"
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.notification_type} - {self.recipient.nombre} ({self.channel})"

class Feedback(models.Model):
    """Modelo para almacenar feedback de candidatos y entrevistas."""
    
    # Relaciones
    candidate = models.ForeignKey(
        'Person', 
        on_delete=models.CASCADE,
        related_name='feedbacks',
        help_text="Candidato asociado al feedback"
    )
    
    interviewer = models.ForeignKey(
        'Person', 
        on_delete=models.SET_NULL,
        null=True,
        related_name='given_feedbacks',
        help_text="Entrevistador que proporcionó el feedback"
    )
    
    # Tipos de Feedback
    feedback_type = models.CharField(
        max_length=20,
        choices=FEEDBACK_TYPE_CHOICES,
        default='INTERVIEW',
        help_text="Tipo de feedback (entrevista, candidato, propuesta, etc.)"
    )
    
    # Estado del Feedback
    status = models.CharField(
        max_length=20,
        choices=FEEDBACK_STATUS_CHOICES,
        default='PENDING',
        help_text="Estado del feedback"
    )
    
    # Resultados
    is_candidate_liked = models.CharField(
        max_length=20,
        choices=FEEDBACK_RESULT_CHOICES,
        default='NOT_APPLICABLE',
        help_text="¿El candidato/a le gustó al entrevistador?"
    )
    
    meets_requirements = models.CharField(
        max_length=20,
        choices=FEEDBACK_RESULT_CHOICES,
        default='NOT_APPLICABLE',
        help_text="¿El candidato cumple con los requerimientos?"
    )
    
    # Detalles adicionales
    missing_requirements = models.TextField(
        blank=True,
        null=True,
        help_text="Descripción de los requisitos que faltan"
    )
    
    additional_comments = models.TextField(
        blank=True,
        null=True,
        help_text="Comentarios adicionales del entrevistador"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Índices
    class Meta:
        indexes = [
            models.Index(fields=['candidate', 'status']),
            models.Index(fields=['feedback_type', 'status']),
            models.Index(fields=['created_at', 'status'])
        ]
        verbose_name = "Feedback"
        verbose_name_plural = "Feedbacks"
        ordering = ['-created_at']
        
    def __str__(self):
        return f"Feedback {self.id} - {self.candidate.nombre} ({self.feedback_type})"
    
    def get_status_display(self):
        """Obtiene el estado formateado."""
        return dict(FEEDBACK_STATUS_CHOICES).get(self.status, self.status)
    
    def get_result_display(self, field):
        """Obtiene el resultado formateado para un campo específico."""
        return dict(FEEDBACK_RESULT_CHOICES).get(getattr(self, field), getattr(self, field))
    
    def mark_as_completed(self):
        """Marca el feedback como completado."""
        self.status = 'COMPLETED'
        self.save(update_fields=['status'])
    
    def skip_feedback(self):
        """Omite el feedback."""
        self.status = 'SKIPPED'
        self.save(update_fields=['status'])

USER_STATUS_CHOICES=[('ACTIVE','Activo'),('INACTIVE','Inactivo'),('PENDING_APPROVAL','Pendiente de Aprobación')]
VERIFICATION_STATUS_CHOICES=[('PENDING','Pendiente'),('APPROVED','Aprobado'),('REJECTED','Rechazado')]
DOCUMENT_TYPE_CHOICES=[('ID','Identificación'),('CURP','CURP'),('RFC','RFC'),('PASSPORT','Pasaporte')]
USER_AGENTS=[
    "Mozilla/5.0 (Android 10; Mobile; rv:88.0) Gecko/88.0 Firefox/88.0",
    "Mozilla/5.0 (Linux; Android 10; SM-A505FN) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.93 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13.6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14.6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/114.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15.7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15.7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15.7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15.7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; AS; rv:11.0) like Gecko",
    "Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.51",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:88.0) Gecko/20100101 Firefox/88.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/114.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.85 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0",
    "Mozilla/5.0 (iPad; CPU OS 14_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 18_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1"
]
PLATFORM_CHOICES=[
    ("workday","Workday"),
    ("phenom_people","Phenom People"),
    ("oracle_hcm","Oracle HCM"),
    ("sap_successfactors","SAP SuccessFactors"),
    ("adp","ADP"),
    ("peoplesoft","PeopleSoft"),
    ("meta4","Meta4"),
    ("cornerstone","Cornerstone"),
    ("ukg","UKG"),
    ("linkedin","LinkedIn"),
    ("indeed","Indeed"),
    ("greenhouse","Greenhouse"),
    ("glassdoor","Glassdoor"),
    ("computrabajo","Computrabajo"),
    ("accenture","Accenture"),
    ("santander","Santander"),
    ("eightfold_ai","EightFold AI"),
    ("default","Default"),
    ("flexible","Flexible"),
]
OFERTA_STATUS_CHOICES=[
    ('pending','Pendiente'),
    ('sent','Enviada'),
    ('signed','Firmada'),
    ('rejected','Rechazada'),
    ('expired','Expirada'),
]
COMUNICATION_CHOICES=[
    ('whatsapp','WhatsApp'),
    ('telegram','Telegram'),
    ('messenger','Messenger'),
    ('instagram','Instagram'),
    ('slack','Slack'),
    ('email','Email'),
    ('incode','INCODE Verification'),
    ('blacktrust','BlackTrust Verification'),
    ('paypal','PayPal Payment Gateway'),
    ('stripe','Stripe Payment Gateway'),
    ('mercado_pago','MercadoPago Payment Gateway'),
    ('linkedin','LinkedIn Job Posting'),
]
API_CATEGORY_CHOICES=[
    ('VERIFICATION','Verificación de Identidad'),
    ('BACKGROUND_CHECK','Verificación de Antecedentes'),
    ('MESSAGING','Envío de Mensajes'),
    ('EMAIL','Envío de Email'),
    ('SOCIAL_MEDIA','Redes Sociales'),
    ('SCRAPING','Extracción de Datos'),
    ('AI','Inteligencia Artificial'),
    ('PAYMENT_GATEWAY','Pasarela de Pago'),
    ('REPORTING','Generación de Reportes'),
    ('ANALYTICS','Análisis de Datos'),
    ('STORAGE','Almacenamiento'),
    ('PAYMENT_GATEWAY','Pasarela de Pagos'),
    ('OTHER','Otro')
]
BUSINESS_UNIT_CHOICES=[
    ('huntRED','huntRED'),
    ('huntRED_executive','huntRED Executive'),
    ('huntu','huntU'),
    ('amigro','Amigro'),
    ('sexsi','SexSI'),
]
DIVISION_CHOICES=[
    ('RECRUITING','Recruiting'),
    ('TECH','Tecnología'),
    ('HR','Recursos Humanos'),
    ('FINANCE','Finanzas'),
    ('MARKETING','Marketing'),
    ('OPERATIONS','Operaciones'),
]
INTENT_TYPE_CHOICES=[
    ('SYSTEM','Sistema'),
    ('USER','Usuario'),
    ('BUSINESS','Negocio'),
    ('FALLBACK','Respuesta por defecto'),
]
STATE_TYPE_CHOICES=[
    ('INITIAL','Inicial'),
    ('PROFILE','Perfil'),
    ('SEARCH','Búsqueda'),
    ('APPLY','Aplicación'),
    ('INTERVIEW','Entrevista'),
    ('OFFER','Oferta'),
    ('HIRED','Contratado'),
    ('IDLE','Inactivo'),
]
TRANSITION_TYPE_CHOICES=[
    ('IMMEDIATE','Inmediato'),
    ('CONDITIONAL','Condicional'),
    ('TIME_BASED','Basado en tiempo'),
    ('EVENT_BASED','Basado en evento'),
]
CONDITION_TYPE_CHOICES=[
    ('PROFILE_COMPLETE','Perfil completo'),
    ('HAS_APPLIED','Ha aplicado'),
    ('HAS_INTERVIEW','Tiene entrevista'),
    ('HAS_OFFER','Tiene oferta'),
    ('HAS_PROFILE','Tiene perfil'),
    ('HAS_CV','Tiene CV'),
    ('HAS_TEST','Tiene prueba'),
]

class BusinessUnit(models.Model):
    name=models.CharField(max_length=50,choices=BUSINESS_UNIT_CHOICES,unique=True)
    description=models.TextField(blank=True)
    admin_phone=models.CharField(max_length=20,null=True,blank=True)
    whatsapp_enabled=models.BooleanField(default=True)
    telegram_enabled=models.BooleanField(default=True)
    messenger_enabled=models.BooleanField(default=True)
    instagram_enabled=models.BooleanField(default=True)
    scrapping_enabled=models.BooleanField(default=True)
    scraping_domains=models.ManyToManyField('DominioScraping',related_name="business_units",blank=True)
    wordpress_base_url=models.URLField(
        max_length=255,
        help_text="URL base de la API de WordPress (ej: https://huntu.mx/wp-json/wp/v2)",
        null=True,
        blank=True
    )
    wordpress_auth_token=models.CharField(
        max_length=500,
        help_text="Token JWT para autenticación con WordPress",
        null=True,
        blank=True
    )
    ntfy_topic=models.CharField(max_length=100,blank=True,null=True,default=None,help_text="Tema de ntfy.sh específico para esta unidad de negocio. Si no se define, usa el tema general.")
    pricing_config = models.JSONField(default=dict, blank=True, help_text="Configuración de pricing por BU.")
    def __str__(self):
        return dict(BUSINESS_UNIT_CHOICES).get(self.name,self.name)
    def get_ntfy_topic(self):
        from django.conf import settings
        return self.ntfy_topic or Configuracion.objects.first().get_ntfy_topic() or settings.NTFY_DEFAULT_TOPIC
    def get_notification_recipients(self):
        recipients={}
        if self.admin_phone:
            recipients['phone']=self.admin_phone
        if self.admin_email:
            recipients['email']=self.admin_email
        return recipients
    def get_email_template_path(self):
        sanitized_name=re.sub(r'\W+','',self.name).lower()
        return f'emails/template_{sanitized_name}.html'
    @property
    def admin_email(self):
        try:
            config=self.configuracionbu
            if config and config.dominio_bu:
                parsed_url=urlparse(config.dominio_bu)
                domain=parsed_url.netloc or parsed_url.path
                domain=domain.replace('www.','')
                return f'hola@{domain}'
        except ConfiguracionBU.DoesNotExist:
            pass
        return None
    def save(self,*args,**kwargs):
        super().save(*args,**kwargs)
        if not hasattr(self,'configuracionbu'):
            ConfiguracionBU.objects.create(business_unit=self)
            logger.info(f"Creada ConfiguracionBU por defecto para {self.name}")

class Person(models.Model):
    number_interaction = models.IntegerField(default=0)
    ref_num = models.CharField(max_length=50, blank=True, null=True, help_text="Número de referencia para identificar origen del registro")
    nombre = models.CharField(max_length=100)
    apellido_paterno = models.CharField(max_length=200, blank=True, null=True)
    apellido_materno = models.CharField(max_length=200, blank=True, null=True)
    nacionalidad = models.CharField(max_length=100, blank=True, null=True)
    fecha_nacimiento = models.DateField(blank=True, null=True)
    sexo = models.CharField(max_length=20, choices=[('M', 'Masculino'), ('F', 'Femenino'), ('O', 'Otro')], blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    company_email = models.EmailField(blank=True, null=True, help_text="Correo empresarial del contacto.")
    phone = models.CharField(max_length=40, blank=True, null=True)
    linkedin_url = models.URLField(max_length=200, blank=True, null=True, help_text="URL del perfil de LinkedIn")
    preferred_language = models.CharField(max_length=5, default='es_MX', help_text="Ej: es_MX, en_US")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    tos_accepted = models.BooleanField(default=False)
    JOB_SEARCH_STATUS_CHOICES = [
        ('activa', 'Activa'),
        ('pasiva', 'Pasiva'),
        ('local', 'Local'),
        ('remota', 'Remota'),
        ('no_busca', 'No en búsqueda'),
    ]
    job_search_status = models.CharField(max_length=20, choices=JOB_SEARCH_STATUS_CHOICES, blank=True, null=True, help_text="Estado actual de la búsqueda de empleo.")
    skills = models.TextField(blank=True, null=True, help_text="Listado libre de skills del candidato.")
    experience_years = models.IntegerField(blank=True, null=True, help_text="Años totales de experiencia.")
    desired_job_types = models.CharField(max_length=100, blank=True, null=True, help_text="Tipos de trabajo deseados, ej: tiempo completo, medio tiempo, freelance.")
    cv_file = models.FileField(upload_to='person_files/', blank=True, null=True, help_text="CV u otro documento del candidato.")
    cv_parsed = models.BooleanField(default=False, help_text="Indica si el CV ha sido analizado.")
    cv_analysis = models.JSONField(blank=True, null=True, help_text="Datos analizados del CV.")
    salary_data = models.JSONField(default=dict, blank=True, help_text="Información salarial, beneficios y expectativas.")
    personality_data = models.JSONField(default=dict, blank=True, help_text="Perfil de personalidad.")
    experience_data = models.JSONField(default=dict, blank=True, help_text="Experiencia profesional detallada.")
    metadata = models.JSONField(default=dict, blank=True, help_text="Información adicional del candidato.")
    hire_date = models.DateField(null=True, blank=True)
    points = models.IntegerField(default=0)
    badges = models.ManyToManyField('Badge', blank=True)
    current_stage = models.ForeignKey('WorkflowStage', on_delete=models.SET_NULL, null=True, blank=True, related_name='candidatos')
    openness = models.FloatField(default=0)
    conscientiousness = models.FloatField(default=0)
    extraversion = models.FloatField(default=0)
    agreeableness = models.FloatField(default=0)
    neuroticism = models.FloatField(default=0)
    social_connections = models.ManyToManyField('self', through='SocialConnection', symmetrical=False, related_name='connected_to')
    
    # Campos para activación de WhatsApp
    whatsapp_enabled = models.BooleanField(default=False, help_text="¿WhatsApp está activado para este usuario?")
    whatsapp_activation_token = models.CharField(max_length=36, blank=True, null=True, help_text="Token de activación para WhatsApp")
    whatsapp_activation_expires = models.DateTimeField(blank=True, null=True, help_text="Fecha de expiración del token de activación")
    
    # Ya están definidos arriba
    # Conexiones sociales para SocialLink™ (principalmente para candidatos Amigro)
    def __str__(self):
        nombre_completo=f"{self.nombre} {self.apellido_paterno or ''} {self.apellido_materno or ''}".strip()
        return nombre_completo
    def is_profile_complete(self):
        required_fields=['nombre','apellido_paterno','email','phone','skills']
        missing_fields=[field for field in required_fields if not getattr(self,field,None)]
        return not missing_fields

class SocialConnection(models.Model):
    """Modelo para almacenar conexiones sociales entre candidatos (SocialLink™).
    Principalmente utilizado para candidatos de Amigro que vienen en grupos."""
    
    RELATIONSHIP_CHOICES = [
        ('friend', 'Amigo'),
        ('family', 'Familiar'),
        ('colleague', 'Colega'),
        ('classmate', 'Compañero de estudios'),
        ('referral', 'Referido')
    ]
    
    from_person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='outgoing_connections')
    to_person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='incoming_connections')
    relationship_type = models.CharField(max_length=50, choices=RELATIONSHIP_CHOICES)
    strength = models.PositiveSmallIntegerField(
        default=1, 
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Fortaleza de la relación (1-5)"
    )
    description = models.TextField(blank=True, null=True, help_text="Descripción adicional de la relación")
    verified = models.BooleanField(default=False, help_text="Indica si la relación ha sido verificada por ambas partes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Conexión Social"
        verbose_name_plural = "Conexiones Sociales"
        unique_together = ('from_person', 'to_person')  # Evita duplicados
        indexes = [models.Index(fields=['from_person']), models.Index(fields=['to_person'])]
    
    def __str__(self):
        return f"{self.from_person} → {self.to_person} ({self.get_relationship_type_display()})"
    
    def save(self, *args, **kwargs):
        # Si ambas personas pertenecen a unidades de negocio diferentes, verificar compatibilidad
        if self.from_person.business_unit and self.to_person.business_unit and \
           self.from_person.business_unit != self.to_person.business_unit:
            # Si alguno es Amigro, permitir la conexión, de lo contrario validar
            if not (self.from_person.business_unit.name.lower() == 'amigro' or \
                   self.to_person.business_unit.name.lower() == 'amigro'):
                logger.warning(f"Intento de conexión entre BUs diferentes: {self.from_person.business_unit} y {self.to_person.business_unit}")
                # No lanzamos error, solo registramos la advertencia
        super().save(*args, **kwargs)

class Company(models.Model):
    name = models.CharField(max_length=255, unique=True, help_text="Nombre de la empresa.")
    industry = models.CharField(max_length=100, blank=True, null=True, help_text="Industria.")
    size = models.CharField(max_length=50, blank=True, null=True, help_text="Tamaño de la empresa, ej: 1-10, 11-50, 51-200, 201-500, 501+")
    location = models.CharField(max_length=100, blank=True, null=True, help_text="Ubicación principal.")
    website = models.URLField(max_length=200, blank=True, null=True, help_text="Sitio web corporativo.")
    description = models.TextField(blank=True, null=True, help_text="Descripción general de la empresa.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    indexes = [models.Index(fields=['name'])]

    def __str__(self):
        return self.name

class Worker(models.Model):
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='workers')
    company = models.ForeignKey('Company', on_delete=models.CASCADE, related_name='workers')
    name=models.CharField(max_length=100)
    whatsapp=models.CharField(max_length=20,blank=True,null=True)
    img_company=models.CharField(max_length=500,blank=True,null=True)
    job_id=models.CharField(max_length=100,blank=True,null=True)
    url_name=models.CharField(max_length=100,blank=True,null=True)
    salary=models.CharField(max_length=100,blank=True,null=True)
    job_type=models.CharField(max_length=100,blank=True,null=True)
    address=models.CharField(max_length=200,blank=True,null=True)
    longitude=models.CharField(max_length=100,blank=True,null=True)
    latitude=models.CharField(max_length=100,blank=True,null=True)
    required_skills=models.TextField(blank=True,null=True)
    experience_required=models.IntegerField(blank=True,null=True)
    job_description=models.TextField(blank=True,null=True)
    metadata=models.JSONField(default=dict,blank=True,help_text="Información adicional del puesto: sectores, requerimientos, etc.")
    class Meta:
        indexes=[
            models.Index(fields=['name']),
            models.Index(fields=['job_id']),
            models.Index(fields=['company']),
        ]
    def __str__(self):
        return str(self.name)

class Vacante(models.Model):
    titulo = models.CharField(max_length=1000)
    empresa = models.ForeignKey(Worker, on_delete=models.CASCADE)
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE, related_name='vacantes', null=True, blank=True)
    proposal = models.ForeignKey('Proposal', on_delete=models.SET_NULL, null=True, blank=True, related_name='vacancies')
    salario = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    ubicacion = models.CharField(max_length=300, blank=True, null=True)
    modalidad = models.CharField(max_length=50, choices=[
        ('presencial', 'Presencial'),
        ('remoto', 'Remoto'),
        ('hibrido', 'Híbrido')
    ], null=True, blank=True)
    remote_friendly = models.BooleanField(default=False)
    descripcion = models.TextField(max_length=3000, blank=True)
    requisitos = models.TextField(blank=True, null=True)
    beneficios = models.TextField(blank=True, null=True)
    skills_required = models.JSONField(default=list)
    activa = models.BooleanField(default=True)
    fecha_publicacion = models.DateTimeField()
    fecha_scraping = models.DateTimeField(auto_now_add=True)
    current_stage = models.ForeignKey('WorkflowStage', on_delete=models.SET_NULL, null=True, blank=True, related_name='vacantes')
    numero_plazas = models.IntegerField(default=1, help_text="Número total de plazas disponibles")
    plazas_restantes = models.IntegerField(default=1, help_text="Número de plazas aún disponibles")
    procesamiento_count = models.IntegerField(default=0, help_text="Número de candidatos en proceso")
    publicar_en = models.JSONField(default=list, help_text="Plataformas donde se publicará la vacante")
    frecuencia_publicacion = models.IntegerField(default=1, help_text="Frecuencia de publicación en días")
    max_candidatos = models.IntegerField(default=100, help_text="Máximo número de candidatos a aceptar")
    dominio_origen = models.ForeignKey('DominioScraping', on_delete=models.SET_NULL, null=True)
    url_original = models.URLField(max_length=1000, blank=True, null=True)
    sentiment = models.CharField(max_length=20, blank=True, null=True)
    job_classification = models.CharField(max_length=100, blank=True, null=True)
    requiere_prueba_personalidad = models.BooleanField(default=False)
    # Campos de LinkedIn (temporalmente deshabilitados hasta obtener acceso a la API)
    linkedin_job_id = models.CharField(
        max_length=100, 
        blank=True, 
        null=True, 
        help_text="ID de la publicación en LinkedIn (temporalmente no disponible)"
    )
    linkedin_status = models.CharField(
        max_length=20,
        choices=[
            ('not_posted', 'No publicado'),
            ('manual', 'Publicado manualmente')
        ],
        default='not_posted',
        help_text="Estado de la publicación en LinkedIn (temporalmente solo manual)"
    )
    # Origen de la vacante
    ORIGEN_CHOICES = [
        ('manual', 'Creada manualmente'),
        ('scraping', 'Obtenida por scraping'),
        ('email', 'Obtenida por email'),
        ('wordpress', 'Sincronizada de WordPress')
    ]
    origen = models.CharField(
        max_length=20,
        choices=ORIGEN_CHOICES,
        default='manual',
        help_text="Origen de la vacante (manual, scraping, email o wordpress)"
    )
    unique_together = ['titulo', 'empresa', 'url_original']
    ordering = ['-fecha_publicacion']
    def __str__(self):
        return f"{self.titulo} - {self.empresa}"

# Propuestas y Contratos
class Proposal(models.Model):
    qr_code = models.ImageField(upload_to='proposals/qr/', null=True, blank=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='proposals', help_text="Empresa asociada.")
    business_units = models.ManyToManyField(BusinessUnit, related_name='proposals', help_text="BUs involucradas en la propuesta.")
    vacancies = models.ManyToManyField('Vacante', related_name='proposals', help_text="Vacantes incluidas en la propuesta.")
    pricing_total = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Costo total de la propuesta.")
    pricing_details = models.JSONField(default=dict, blank=True, help_text="Desglose de pricing por vacante y BU.")
    status = models.CharField(max_length=20, choices=PROPOSAL_STATUS_CHOICES, default='DRAFT')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=['company', 'status'])]

    def __str__(self):
        return f"Propuesta para {self.company} - {self.get_status_display()}"

class Contrato(models.Model):
    proposal = models.OneToOneField(Proposal, on_delete=models.CASCADE, related_name='contrato', help_text="Propuesta asociada.")
    pdf_file = models.FileField(upload_to='contratos/%Y/%m/%d/', help_text="PDF del contrato.")
    status = models.CharField(max_length=20, choices=CONTRATO_STATUS_CHOICES, default='PENDING_APPROVAL')
    superuser_signature = models.BooleanField(default=False, help_text="Aprobación del superuser.")
    client_signature = models.BooleanField(default=False, help_text="Firma del cliente.")
    signers = models.ManyToManyField(Person, related_name='signed_contratos', help_text="Firmantes del cliente.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=['proposal', 'status'])]

    def __str__(self):
        return f"Contrato para {self.proposal.company} - {self.get_status_display()}"

# Pagos

# Configuraciones de Talento

class WeightingModel(models.Model):
    """Modelo de ponderación dinámica por nivel de posición y Business Unit."""
    business_unit = models.ForeignKey(
        BusinessUnit,
        on_delete=models.CASCADE,
        related_name='weightings',
        help_text="Business Unit asociada a esta ponderación"
    )
    position_level = models.CharField(
        max_length=50,
        choices=[
            ('entry_level', 'Nivel de entrada'),
            ('operativo', 'Nivel operativo'),
            ('gerencia_media', 'Gerencia media'),
            ('alta_direccion', 'Alta dirección')
        ],
        help_text="Nivel de posición para esta ponderación"
    )
    
    # Ponderaciones dinámicas
    weight_skills = models.FloatField(
        default=0.4,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Peso de las habilidades técnicas"
    )
    weight_experience = models.FloatField(
        default=0.3,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Peso de la experiencia"
    )
    weight_culture = models.FloatField(
        default=0.2,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Peso del fit cultural"
    )
    weight_location = models.FloatField(
        default=0.1,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Peso de la ubicación"
    )
    
    # Ponderaciones específicas por nivel
    culture_importance = models.FloatField(
        default=0.3,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Importancia del fit cultural para este nivel"
    )
    experience_requirement = models.FloatField(
        default=0.5,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Requisito de experiencia para este nivel"
    )
    
    # Campos de auditoría
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_weightings'
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='updated_weightings'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Modelo de Ponderación"
        verbose_name_plural = "Modelos de Ponderación"
        unique_together = ['business_unit', 'position_level']
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['business_unit', 'position_level']),
            models.Index(fields=['business_unit', 'updated_at']),
            models.Index(fields=['position_level', 'updated_at'])
        ]
    
    def __str__(self):
        return f"Ponderación {self.position_level} para {self.business_unit.name}"
    
    def clean(self):
        """Validaciones adicionales."""
        super().clean()
        
        # Validar que las ponderaciones sumen 1
        total_weight = (
            self.weight_skills +
            self.weight_experience +
            self.weight_culture +
            self.weight_location
        )
        
        if abs(total_weight - 1.0) > 0.01:
            raise ValidationError(
                "Las ponderaciones deben sumar 1"
            )
            
        # Validar que los valores estén dentro de rangos razonables
        if self.culture_importance > 0.6 and self.position_level != 'alta_direccion':
            raise ValidationError(
                "La importancia cultural no puede ser tan alta para este nivel"
            )
            
        if self.experience_requirement > 0.7 and self.position_level == 'entry_level':
            raise ValidationError(
                "El requisito de experiencia es demasiado alto para nivel de entrada"
            )
    
    def save(self, *args, **kwargs):
        """Valida y guarda el modelo."""
        self.full_clean()
        super().save(*args, **kwargs)
    
    def get_weights(self) -> Dict:
        """Devuelve las ponderaciones como un diccionario."""
        return {
            'skills': self.weight_skills,
            'experience': self.weight_experience,
            'culture': self.weight_culture,
            'location': self.weight_location,
            'culture_importance': self.culture_importance,
            'experience_requirement': self.experience_requirement
        }

    @classmethod
    def get_cached_weights(cls, business_unit: str, position_level: str) -> Optional[Dict]:
        """Obtiene ponderaciones desde cache o base de datos."""
        cache_key = f"weighting:{business_unit}:{position_level}"
        cached = cache.get(cache_key)
        
        if cached:
            return json.loads(cached)
            
        try:
            weighting = cls.objects.get(
                business_unit__name=business_unit,
                position_level=position_level
            )
            weights = weighting.get_weights()
            
            # Almacenar en cache por 1 hora
            cache.set(cache_key, json.dumps(weights), 3600)
            return weights
            
        except cls.DoesNotExist:
            return None

class WeightingHistory(models.Model):
    """Historial de cambios en ponderaciones."""
    weighting = models.ForeignKey(
        WeightingModel,
        on_delete=models.CASCADE,
        related_name='history'
    )
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    changes = models.JSONField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Historial de Ponderación"
        verbose_name_plural = "Historiales de Ponderación"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['weighting', 'timestamp']),
            models.Index(fields=['changed_by', 'timestamp'])
        ]
    
    def __str__(self):
        return f"Cambio en {self.weighting} el {self.timestamp}"

class TalentConfig(models.Model):
    """Configuración dinámica para análisis de talento por Business Unit."""
    business_unit = models.OneToOneField(
        BusinessUnit,
        on_delete=models.CASCADE,
        related_name='talent_config',
        help_text="Business Unit asociada a esta configuración"
    )
    
    # Configuración general
    default_weights = models.ForeignKey(
        WeightingModel,
        on_delete=models.SET_NULL,
        null=True,
        related_name='default_config',
        help_text="Ponderaciones por defecto para este BU"
    )
    
    # Parámetros de análisis
    time_window_days = models.IntegerField(
        default=30,
        validators=[MinValueValidator(1)],
        help_text="Ventana de tiempo para análisis de mensajes (en días)"
    )
    min_interactions = models.IntegerField(
        default=5,
        validators=[MinValueValidator(1)],
        help_text="Número mínimo de interacciones para análisis"
    )
    sentiment_threshold = models.FloatField(
        default=0.7,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Umbral de sentimiento para considerar positivo"
    )
    
    # Parámetros de matching
    match_threshold = models.FloatField(
        default=0.75,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Umbral mínimo para considerar un match exitoso"
    )
    
    # Configuración de personalidad
    personality_importance = models.FloatField(
        default=0.3,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Importancia de la personalidad en el matching"
    )
    
    # Parámetros de optimización
    cache_ttl = models.IntegerField(
        default=3600,
        validators=[MinValueValidator(300)],
        help_text="Tiempo de vida del cache (en segundos)"
    )
    batch_size = models.IntegerField(
        default=100,
        validators=[MinValueValidator(1)],
        help_text="Tamaño del batch para procesamiento asíncrono"
    )
    
    # Campos de auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Configuración de Talento"
        verbose_name_plural = "Configuraciones de Talento"
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"Config {self.business_unit.name}"
    
    def get_position_level(self, experience_years: int) -> str:
        """Determina el nivel de posición basado en años de experiencia."""
        if experience_years >= 15:
            return 'alta_direccion'
        elif experience_years >= 8:
            return 'gerencia_media'
        elif experience_years >= 2:
            return 'operativo'
        return 'entry_level'
    
    def get_weighting(self, position_level: str) -> Optional[WeightingModel]:
        """Obtiene el modelo de ponderación para un nivel de posición."""
        try:
            return WeightingModel.objects.get(
                business_unit=self.business_unit,
                position_level=position_level
            )
        except WeightingModel.DoesNotExist:
            return None

# Análisis de Oportunidades

OPPORTUNITY_STATUS_CHOICES = [
    ('NEW', 'Nueva'),
    ('ANALYZING', 'En Análisis'),
    ('READY', 'Lista para Contacto'),
    ('IN_PROGRESS', 'En Progreso'),
    ('CLOSED', 'Cerrada')
]

STRATEGY_TYPE_CHOICES = [
    ('INTERNATIONAL_EXPANSION', 'Expansión Internacional'),
    ('PRODUCT_INNOVATION', 'Innovación de Producto'),
    ('TALENT_ACQUISITION', 'Adquisición de Talento'),
    ('DIGITAL_TRANSFORMATION', 'Transformación Digital'),
    ('OPERATIONAL_EXCELLENCE', 'Excelencia Operativa')
]

ACTION_TYPE_CHOICES = [
    ('EMAIL', 'Email'),
    ('MEETING', 'Reunión'),
    ('CALL', 'Llamada'),
    ('WEBINAR', 'Webinar'),
    ('DEMO', 'Demostración')
]

class OpportunityAnalysis(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='opportunity_analyses')
    status = models.CharField(max_length=20, choices=OPPORTUNITY_STATUS_CHOICES, default='NEW')
    priority = models.IntegerField(default=0, help_text="Prioridad de la oportunidad (0-100)")
    value_proposition = models.TextField(blank=True, null=True)
    key_contacts = models.ManyToManyField(Person, related_name='opportunities')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-priority', '-created_at']
        
    def __str__(self):
        return f"{self.company.name} - {self.get_status_display()}"

class AIStrategy(models.Model):
    opportunity = models.ForeignKey(OpportunityAnalysis, on_delete=models.CASCADE, related_name='strategies')
    strategy_type = models.CharField(max_length=50, choices=STRATEGY_TYPE_CHOICES)
    value_proposition = models.TextField()
    relevant_bu = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE, related_name='strategies')
    success_factors = models.JSONField(default=dict)
    source_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.opportunity.company.name} - {self.get_strategy_type_display()}"

class ActionPlan(models.Model):
    opportunity = models.ForeignKey(OpportunityAnalysis, on_delete=models.CASCADE, related_name='action_plans')
    action_type = models.CharField(max_length=20, choices=ACTION_TYPE_CHOICES)
    description = models.TextField()
    assigned_to = models.ForeignKey(Person, on_delete=models.SET_NULL, null=True, related_name='assigned_actions')
    due_date = models.DateTimeField()
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.opportunity.company.name} - {self.get_action_type_display()}"

# Pagos
class PaymentMilestone(models.Model):
    contrato = models.ForeignKey(Contrato, on_delete=models.CASCADE, related_name='payment_milestones', help_text="Contrato asociado.")
    name = models.CharField(max_length=100, help_text="Nombre del hito (ej. Inicio).")
    percentage = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)], help_text="Porcentaje del total.")
    trigger_event = models.CharField(max_length=50, choices=TRIGGER_EVENT_CHOICES, help_text="Evento que activa el hito.")
    due_date_offset = models.IntegerField(default=7, help_text="Días desde el evento para vencimiento.")
    amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Monto calculado.")
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=['contrato', 'status'])]

    def __str__(self):
        return f"{self.name} - {self.contrato}"
class Application(models.Model):
    user=models.ForeignKey(Person,on_delete=models.CASCADE,related_name='applications')
    vacancy=models.ForeignKey(Vacante,on_delete=models.CASCADE,related_name='applications')
    status=models.CharField(max_length=20,choices=[('applied','Applied'),('interview','Interview'),('rejected','Rejected'),('hired','Hired')],default='applied')
    applied_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    additional_notes=models.TextField(blank=True,null=True)
    def __str__(self):
        return f"{self.user} - {self.vacancy} - {self.status}"

class EntrevistaTipo(models.Model):
    TIPO_CHOICES=[('presencial','Presencial'),('virtual','Virtual'),('panel','Panel'),('otro','Otro')]
    nombre=models.CharField(max_length=50,choices=TIPO_CHOICES)
    descripcion=models.TextField(blank=True,null=True)
    def __str__(self):
        return self.nombre

class Entrevista(models.Model):
    candidato=models.ForeignKey(Person,on_delete=models.CASCADE,related_name='entrevistas')
    vacante=models.ForeignKey(Vacante,on_delete=models.CASCADE,related_name='entrevistas')
    tipo=models.ForeignKey(EntrevistaTipo,on_delete=models.SET_NULL,null=True)
    fecha=models.DateTimeField()
    resultado=models.CharField(max_length=50,choices=[('pendiente','Pendiente'),('aprobado','Aprobado'),('rechazado','Rechazado')],default='pendiente')
    comentarios=models.TextField(blank=True,null=True)
    def __str__(self):
        return f"Entrevista de {self.candidato.nombre} para {self.vacante.titulo}"

class OfertaEstado(models.Model):
    nombre=models.CharField(max_length=50)
    descripcion=models.TextField(blank=True,null=True)
    def __str__(self):
        return self.nombre

class CartaOfertaManager(models.Manager):
    def crear_carta_oferta(self,user,vacancy,salary,benefits,start_date,end_date=None):
        if not user.is_complete_profile():
            raise ValueError("El perfil del usuario debe estar completo para crear una carta de oferta.")
        estado_pendiente,_=OfertaEstado.objects.get_or_create(nombre='pendiente',defaults={'descripcion':'Oferta pendiente de aceptación'})
        carta=self.create(user=user,vacancy=vacancy,salary=salary,benefits=benefits,start_date=start_date,end_date=end_date or (start_date+timedelta(days=365)),status=estado_pendiente)
        return carta

class CartaOferta(models.Model):
    user=models.ForeignKey(Person,on_delete=models.CASCADE,related_name='cartas_oferta')
    vacancy=models.ForeignKey(Vacante,on_delete=models.CASCADE,related_name='cartas_oferta')
    salary=models.DecimalField(max_digits=10,decimal_places=2)
    benefits=models.TextField()
    start_date=models.DateField()
    end_date=models.DateField()
    status=models.CharField(max_length=20,choices=OFERTA_STATUS_CHOICES,default='pending')
    canal_envio=models.CharField(max_length=20,choices=COMUNICATION_CHOICES,null=True,blank=True)
    fecha_envio=models.DateTimeField(null=True,blank=True)
    fecha_firma=models.DateTimeField(null=True,blank=True)
    pdf_file=models.FileField(upload_to='cartas_oferta/',null=True,blank=True)
    entrevista=models.ForeignKey(Entrevista,on_delete=models.SET_NULL,null=True,blank=True,related_name='cartas_oferta')
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    objects=CartaOfertaManager()
    class Meta:
        ordering=['-created_at']
        unique_together=['user','vacancy']
    def marcar_como_firmada(self):
        try:
            self.status='signed'
            self.fecha_firma=timezone.now()
            self.save()
            application=Application.objects.filter(user=self.user,vacancy=self.vacancy).first()
            if application:
                application.status='hired'
                application.save()
            chat_state=ChatState.objects.filter(person=self.user,business_unit=self.vacancy.business_unit).first()
            if chat_state:
                chat_state.state='HIRED'
                chat_state.last_transition=timezone.now()
                chat_state.save()
        except Exception as e:
            logger.error(f"Error marcando carta como firmada: {str(e)}")
            raise
    def rechazar(self):
        try:
            self.status='rejected'
            self.save()
            application=Application.objects.filter(user=self.user,vacancy=self.vacancy).first()
            if application:
                application.status='rejected'
                application.save()
        except Exception as e:
            logger.error(f"Error rechazando carta: {str(e)}")
            raise
    def get_status_badge(self):
        badge_colors={'pending':'warning','sent':'info','signed':'success','rejected':'danger','expired':'secondary'}
        return badge_colors.get(self.status,'secondary')
    def get_status_display(self):
        for value,display in OFERTA_STATUS_CHOICES:
            if value==self.status:
                return display
        return self.status
    def __str__(self):
        return f"Carta de Oferta para {self.user.nombre} - {self.vacancy.titulo} ({self.status})"

class JobTracker(models.Model):
    OPERATION_STATUS_CHOICES=[('not_started','No Iniciado'),('in_progress','En Progreso'),('completed','Completado'),('on_hold','En Espera')]
    opportunity=models.OneToOneField(Vacante,on_delete=models.CASCADE,related_name='job_tracker')
    status=models.CharField(max_length=20,choices=OPERATION_STATUS_CHOICES,default='not_started')
    start_date=models.DateField(auto_now_add=True)
    end_date=models.DateField(null=True,blank=True)
    def __str__(self):
        return f"Job Tracker para {self.opportunity.titulo}"
    def handle_job_tracker_status_change(sender,instance,**kwargs):
        if instance.status=='completed':
            print(f"El JobTracker para {instance.opportunity} ha sido completado.")

class Interview(models.Model):
    INTERVIEW_TYPE_CHOICES=[('presencial','Presencial'),('virtual','Virtual'),('panel','Panel')]
    person=models.ForeignKey(Person,on_delete=models.CASCADE)
    interviewer=models.ForeignKey(Person,on_delete=models.CASCADE,related_name='conducted_interviews',blank=True,null=True)
    job=models.ForeignKey(Worker,on_delete=models.CASCADE)
    interview_date=models.DateTimeField()
    application_date=models.DateTimeField(auto_now_add=True)
    slot=models.CharField(max_length=50)
    candidate_latitude=models.CharField(max_length=100,blank=True,null=True)
    candidate_longitude=models.CharField(max_length=100,blank=True,null=True)
    location_verified=models.BooleanField(default=False)
    interview_type=models.CharField(max_length=20,choices=INTERVIEW_TYPE_CHOICES,default='presencial')
    candidate_confirmed=models.BooleanField(default=False)
    def days_until_interview(self):
        return (self.interview_date-timezone.now()).days

class PricingBaseline(models.Model):
    BUSINESS_UNIT_CHOICES = [
        ('huntred', 'Huntred'),
        ('client', 'Cliente')
    ]
    bu = models.CharField(max_length=50, choices=BUSINESS_UNIT_CHOICES)
    model = models.CharField(max_length=20, choices=[('fixed', 'Precio Fijo'), ('percentage', 'Porcentaje')])
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    empresa=models.CharField(max_length=75,unique=True,blank=True,null=True)
    dominio=models.URLField(max_length=255,unique=True)
    company_name=models.CharField(max_length=255,blank=True)
    email_scraping_enabled=models.BooleanField(default=False)
    valid_senders=models.JSONField(default=list)
    plataforma=models.CharField(max_length=100,choices=PLATFORM_CHOICES,blank=True,null=True)
    estado=models.CharField(max_length=20,choices=[("definido","Definido"),("libre","Indefinido")],default="libre")
    verificado=models.BooleanField(default=False)
    activo=models.BooleanField(default=True)
    cookies=models.JSONField(blank=True,null=True)
    frecuencia_scraping=models.IntegerField(default=24)
    mensaje_error=models.TextField(blank=True,null=True)
    ultima_verificacion=models.DateTimeField(blank=True,null=True)
    creado_en=models.DateTimeField(auto_now_add=True)
    actualizado_en=models.DateTimeField(auto_now=True)
    selector_titulo=models.CharField(max_length=200,null=True,blank=True)
    selector_descripcion=models.CharField(max_length=200,null=True,blank=True)
    selector_ubicacion=models.CharField(max_length=200,null=True,blank=True)
    selector_salario=models.CharField(max_length=200,null=True,blank=True)
    tipo_selector=models.CharField(max_length=20,choices=[('css','CSS'),('xpath','XPath')],default='css')
    mapeo_configuracion=models.JSONField(null=True,blank=True,help_text="Configuración personalizada (selectores, paginación, etc.)")
    def generar_correo_asignado(self):
        configuracion=ConfiguracionBU.objects.filter(scraping_domains__dominio=self.dominio).first()
        dominio_bu=configuracion.dominio_bu if configuracion else "huntred.com"
        return f"{self.empresa.lower()}@{dominio_bu}" if self.empresa else None
    def __str__(self):
        return f"{self.dominio} ({self.plataforma})"
    def detectar_plataforma(self):
        if self.plataforma:
            logger.info(f"Plataforma ya definida manualmente: {self.plataforma}")
            return
        url_lower=self.dominio.lower()
        patrones={
            'workday':r'workday\.com',
            'oracle_hcm':r'oracle\.com',
            'sap_successfactors':r'sap\.com',
            'cornerstone':r'cornerstoneondemand\.com',
            'amigro':r'amigro\.org',
        }
        for plataforma,patron in patrones.items():
            if re.search(patron,url_lower):
                self.plataforma=plataforma
                self.verificado=True
                logger.info(f"Plataforma detectada automáticamente: {plataforma}")
                return
        self.plataforma="otro"
        self.verificado=False
        logger.warning(f"No se detectó una plataforma conocida para: {self.dominio}")
    def clean(self):
        self.detectar_plataforma()
    def save(self,*args,**kwargs):
        self.clean()
        super().save(*args,**kwargs)
    class Meta:
        indexes=[models.Index(fields=['dominio'])]

class DominioScraping(models.Model):
    empresa=models.CharField(max_length=75,unique=True,blank=True,null=True)
    dominio=models.URLField(max_length=255,unique=True)
    company_name=models.CharField(max_length=255,blank=True)
    email_scraping_enabled=models.BooleanField(default=False)
    valid_senders=models.JSONField(default=list)
    plataforma=models.CharField(max_length=100,choices=PLATFORM_CHOICES,blank=True,null=True)
    estado=models.CharField(max_length=20,choices=[("definido","Definido"),("libre","Indefinido")],default="libre")
    verificado=models.BooleanField(default=False)
    activo=models.BooleanField(default=True)
    cookies=models.JSONField(blank=True,null=True)
    frecuencia_scraping=models.IntegerField(default=24)
    mensaje_error=models.TextField(blank=True,null=True)
    ultima_verificacion=models.DateTimeField(blank=True,null=True)
    creado_en=models.DateTimeField(auto_now_add=True)
    actualizado_en=models.DateTimeField(auto_now=True)
    selector_titulo=models.CharField(max_length=200,null=True,blank=True)
    selector_descripcion=models.CharField(max_length=200,null=True,blank=True)
    selector_ubicacion=models.CharField(max_length=200,null=True,blank=True)
    selector_salario=models.CharField(max_length=200,null=True,blank=True)
    tipo_selector=models.CharField(max_length=20,choices=[('css','CSS'),('xpath','XPath')],default='css')
    mapeo_configuracion=models.JSONField(null=True,blank=True,help_text="Configuración personalizada (selectores, paginación, etc.)")
    def generar_correo_asignado(self):
        configuracion=ConfiguracionBU.objects.filter(scraping_domains__dominio=self.dominio).first()
        dominio_bu=configuracion.dominio_bu if configuracion else "huntred.com"
        return f"{self.empresa.lower()}@{dominio_bu}" if self.empresa else None
    def __str__(self):
        return f"{self.dominio} ({self.plataforma})"
    def detectar_plataforma(self):
        if self.plataforma:
            logger.info(f"Plataforma ya definida manualmente: {self.plataforma}")
            return
        url_lower=self.dominio.lower()
        patrones={
            'workday':r'workday\.com',
            'oracle_hcm':r'oracle\.com',
            'sap_successfactors':r'sap\.com',
            'cornerstone':r'cornerstoneondemand\.com',
            'amigro':r'amigro\.org',
        }
        for plataforma,patron in patrones.items():
            if re.search(patron,url_lower):
                self.plataforma=plataforma
                self.verificado=True
                logger.info(f"Plataforma detectada automáticamente: {plataforma}")
                return
        self.plataforma="otro"
        self.verificado=False
        logger.warning(f"No se detectó una plataforma conocida para: {self.dominio}")
    def clean(self):
        self.detectar_plataforma()
    def save(self,*args,**kwargs):
        self.clean()
        super().save(*args,**kwargs)
    class Meta:
        indexes=[models.Index(fields=['dominio'])]

class ConfiguracionScraping(models.Model):
    dominio=models.ForeignKey(DominioScraping,on_delete=models.CASCADE)
    campo=models.CharField(max_length=50)
    selector=models.CharField(max_length=200)
    tipo_selector=models.CharField(max_length=20,choices=[('css','CSS'),('xpath','XPath')])
    transformacion=models.CharField(max_length=100,null=True,blank=True)

class Certificate(models.Model):
    """
    Modelo para certificados de contratos.
    """
    contrato = models.OneToOneField(
        Contrato,
        on_delete=models.CASCADE,
        related_name='certificate'
    )
    certificate_hash = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    certificate_url = models.URLField()
    
    def verify(self):
        """
        Verifica la integridad y timestamp del certificado.
        
        Returns:
            tuple: (bool, str) - (estado, mensaje)
        """
        try:
            # Verificar hash
            cert_hash = self.certificate_hash
            timestamp = ots.Timestamp.from_hex(cert_hash)
            
            # Verificar timestamp
            now = timezone.now()
            if timestamp.timestamp > now:
                return False, "El timestamp es posterior a la fecha actual"
                
            # Verificar integridad
            if not timestamp.verify():
                return False, "El certificado ha sido modificado"
                
            return True, "Certificado válido"
                
        except Exception as e:
            return False, f"Error al verificar el certificado: {str(e)}"

    def get_status_display(self):
        return dict(self.STATUS_CHOICES).get(self.status, 'Desconocido')

class ConfiguracionBU(models.Model):
    business_unit=models.OneToOneField(BusinessUnit,on_delete=models.CASCADE)
    logo_url=models.URLField(default="https://huntred.com/logo.png")
    direccion_bu=models.CharField(max_length=255,default="Av. Santa Fe #428, Torre 3, Piso 15, CDMX")
    telefono_bu=models.CharField(max_length=20,default="+5255 59140089")
    correo_bu=models.CharField(max_length=20,default="hola@huntred.com")
    jwt_token=models.CharField(max_length=255,blank=True,null=True,default="...")
    dominio_bu=models.URLField(max_length=255,blank=True,null=True)
    dominio_rest_api=models.URLField(max_length=255,blank=True,null=True)
    scraping_domains=models.ManyToManyField('DominioScraping',related_name='configuracion_business_units',blank=True,help_text="Selecciona los dominios de scraping asociados a esta unidad de negocio.")
    smtp_host=models.CharField(max_length=255,blank=True,null=True)
    smtp_port=models.IntegerField(blank=True,null=True,default=587)
    smtp_username=models.CharField(max_length=255,blank=True,null=True)
    smtp_password=models.CharField(max_length=255,blank=True,null=True)
    smtp_use_tls=models.BooleanField(default=True)
    smtp_use_ssl=models.BooleanField(default=False)
    weight_location=models.IntegerField(default=10)
    weight_hard_skills=models.IntegerField(default=45)
    weight_soft_skills=models.IntegerField(default=35)
    weight_contract=models.IntegerField(default=10)
    
    # Campos para pagos
    stripe_api_key = models.CharField(max_length=255, blank=True, null=True)
    stripe_webhook_secret = models.CharField(max_length=255, blank=True, null=True)
    payment_terms = models.JSONField(default=dict, help_text="Términos de pago por tipo de servicio")
    
    # Campos para análisis
    open_threshold = models.DecimalField(max_digits=3, decimal_places=2, default=0.7)
    response_threshold = models.IntegerField(default=24, help_text="Horas")
    max_discount = models.DecimalField(max_digits=3, decimal_places=2, default=0.10)
    
    # Campos para X
    x_api_key = models.CharField(max_length=255, blank=True, null=True)
    x_api_secret = models.CharField(max_length=255, blank=True, null=True)
    x_access_token = models.CharField(max_length=255, blank=True, null=True)
    
    # Campos para Redis
    redis_host = models.CharField(max_length=255, default='localhost')
    redis_port = models.IntegerField(default=6379)
    redis_db = models.IntegerField(default=0)
    
    # Campos para Celery
    celery_broker_url = models.CharField(max_length=255, default='redis://localhost:6379/0')
    celery_result_backend = models.CharField(max_length=255, default='redis://localhost:6379/0')
    
    def get_payment_config(self):
        """Obtiene la configuración de pagos."""
        return {
            'stripe_api_key': self.stripe_api_key,
            'stripe_webhook_secret': self.stripe_webhook_secret,
            'payment_terms': self.payment_terms
        }
        
    def get_x_config(self):
        """Obtiene la configuración de X."""
        return {
            'api_key': self.x_api_key,
            'api_secret': self.x_api_secret,
            'access_token': self.x_access_token
        }
        
    def get_redis_config(self):
        """Obtiene la configuración de Redis."""
        return {
            'host': self.redis_host,
            'port': self.redis_port,
            'db': self.redis_db
        }
        
    def get_celery_config(self):
        """Obtiene la configuración de Celery."""
        return {
            'broker_url': self.celery_broker_url,
            'result_backend': self.celery_result_backend
        }
    def __str__(self):
        return f"Configuración de {self.business_unit.name if self.business_unit else 'Unidad de Negocio'}"
    def get_smtp_config(self):
        return {
            'host': self.smtp_host,
            'port': self.smtp_port,
            'username':self.smtp_username,
            'password':self.smtp_password,
            'use_tls':self.smtp_use_tls,
            'use_ssl':self.smtp_use_ssl
        }
    def calculate_tier(self,candidate_score:float):
        if candidate_score>=85:
            return "Tier 1 (Excelente)"
        elif candidate_score>=70:
            return "Tier 2 (Muy Bueno)"
        elif candidate_score>=55:
            return "Tier 3 (Bueno)"
        elif candidate_score>=40:
            return "Tier 4 (Regular)"
        else:
            return "Tier 5 (Necesita Mejora)"
    def _load_weights(self):
        try:
            config=ConfiguracionBU.objects.get(business_unit=self.business_unit)
            return {
                "ubicacion":config.weight_location or 10,
                "hard_skills":config.weight_hard_skills or 45,
                "soft_skills":config.weight_soft_skills or 35,
                "tipo_contrato":config.weight_contract or 10,
                "personalidad":config.weight_personality or 15,
            }
        except ConfiguracionBU.DoesNotExist:
            return {
                "ubicacion":5,
                "hard_skills":45,
                "soft_skills":35,
                "tipo_contrato":5,
                "personalidad":10,
            }
    def get_weights(self,position_level):
        if position_level=="gerencia_media":
            return {**self.weights,"soft_skills":40,"hard_skills":40,"ubicacion":10,"personalidad":20}
        elif position_level=="alta_direccion":
            return {**self.weights,"soft_skills":45,"hard_skills":30,"ubicacion":10,"personalidad":25}
        elif position_level=="operativo":
            return {**self.weights,"ubicacion":15,"hard_skills":50,"soft_skills":25,"personalidad":10}
        return self.weights

class InternalDocumentSignature(models.Model):
    """
    Modelo para manejar firmas digitales internas de documentos.
    """
    STATUS_CHOICES = [
        ('draft', 'Borrador'),
        ('pending', 'Pendiente'),
        ('signed_by_creator', 'Firmado por Creador'),
        ('signed_by_reviewer', 'Firmado por Revisor'),
        ('completed', 'Completado'),
        ('cancelled', 'Cancelado')
    ]

    creator = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='created_signatures')
    reviewer = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='reviewed_signatures', null=True, blank=True)
    document_name = models.CharField(max_length=200)
    document_description = models.TextField()
    document_file = models.FileField(upload_to='internal_documents/')
    signature_method = models.CharField(
        max_length=20, 
        choices=(
            ("digital", "Firma Digital"), 
            ("electronic", "Firma Electrónica")
        ),
        default="digital"
    )
    
    # Firma y validaciones
    is_signed_by_creator = models.BooleanField(default=False)
    is_signed_by_reviewer = models.BooleanField(default=False)
    creator_signature = models.ImageField(upload_to='internal_signatures/', null=True, blank=True)
    reviewer_signature = models.ImageField(upload_to='internal_signatures/', null=True, blank=True)
    
    # Seguridad y control
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    token_expiry = models.DateTimeField()
    
    # Estado y timestamps
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Relación con Business Unit
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE, related_name='internal_signatures')
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['creator', 'document_file']

    def __str__(self):
        return f"Firma #{self.id} - {self.document_name}"

    def save(self, *args, **kwargs):
        if not self.token_expiry:
            self.token_expiry = timezone.now() + timedelta(hours=24)
        super().save(*args, **kwargs)

    def is_token_valid(self):
        return timezone.now() < self.token_expiry

    def get_status_display(self):
        return dict(self.STATUS_CHOICES).get(self.status, 'Desconocido')

    def mark_as_signed_by_creator(self):
        self.is_signed_by_creator = True
        self.status = 'signed_by_creator'
        self.save()

    def mark_as_signed_by_reviewer(self):
        self.is_signed_by_reviewer = True
        self.status = 'completed'
        self.save()

    def cancel(self):
        self.status = 'cancelled'
        self.save()

    def get_absolute_url(self):
        return reverse('internal_signature_detail', kwargs={'pk': self.pk})

class WorkflowStage(models.Model):
    name=models.CharField(max_length=100)
    description=models.TextField(blank=True,null=True)
    business_unit=models.ForeignKey(BusinessUnit,on_delete=models.CASCADE,related_name='workflow_stages')
    order=models.PositiveIntegerField()
    class Meta:
        ordering=['order']
    def __str__(self):
        return f"{self.name} ({self.business_unit.name})"

class RegistroScraping(models.Model):
    dominio=models.ForeignKey(DominioScraping,on_delete=models.CASCADE)
    fecha_inicio=models.DateTimeField(auto_now_add=True)
    fecha_fin=models.DateTimeField(null=True)
    vacantes_encontradas=models.IntegerField(default=0)
    estado=models.CharField(max_length=50,choices=[('exitoso','Exitoso'),('fallido','Fallido'),('parcial','Parcial')])
    error_log=models.TextField(blank=True,null=True)
    def __str__(self):
        return f"Registro {self.dominio.empresa} - {self.estado} - {self.fecha_inicio}"

class IntentPattern(models.Model):
    name=models.CharField(max_length=100,unique=True)
    description=models.TextField(blank=True,null=True)
    patterns=models.TextField(help_text="Patrones de regex separados por nueva línea")
    responses=models.JSONField(default=dict,help_text="Respuestas por canal y unidad de negocio")
    priority=models.IntegerField(default=50)
    enabled=models.BooleanField(default=True)
    type=models.CharField(max_length=20,choices=INTENT_TYPE_CHOICES,default='USER')
    business_units=models.ManyToManyField(BusinessUnit,related_name='intent_patterns')
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    class Meta:
        ordering=('-priority','name')
    def __str__(self):
        return f"{self.name} ({self.type})"
    def get_patterns_list(self):
        return self.patterns.split('\n') if self.patterns else []

class StateTransition(models.Model):
    current_state=models.CharField(max_length=50,choices=STATE_TYPE_CHOICES)
    next_state=models.CharField(max_length=50,choices=STATE_TYPE_CHOICES)
    conditions=models.JSONField(default=list,help_text="Condiciones para la transición")
    type=models.CharField(max_length=20,choices=TRANSITION_TYPE_CHOICES,default='IMMEDIATE')
    business_unit=models.ForeignKey(BusinessUnit,on_delete=models.CASCADE,related_name='state_transitions')
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    class Meta:
        unique_together=('current_state','next_state','business_unit')
    def __str__(self):
        return f"{self.business_unit.name}: {self.current_state} -> {self.next_state}"

class IntentTransition(models.Model):
    current_intent=models.ForeignKey(IntentPattern,on_delete=models.CASCADE,related_name='transitions_from')
    next_intent=models.ForeignKey(IntentPattern,on_delete=models.CASCADE,related_name='transitions_to')
    conditions=models.JSONField(default=list,help_text="Condiciones para la transición")
    type=models.CharField(max_length=20,choices=TRANSITION_TYPE_CHOICES,default='IMMEDIATE')
    business_unit=models.ForeignKey(BusinessUnit,on_delete=models.CASCADE,related_name='intent_transitions')
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    class Meta:
        unique_together=('current_intent','next_intent','business_unit')
    def __str__(self):
        return f"{self.business_unit.name}: {self.current_intent.name} -> {self.next_intent.name}"

class NotificationChannel(models.Model):
    CHANNEL_CHOICES = [
        ('WHATSAPP', 'WhatsApp'),
        ('EMAIL', 'Email'),
        ('SMS', 'SMS'),
        ('PUSH', 'Notificación Push')
    ]
    
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES)
    enabled = models.BooleanField(default=True)
    priority = models.IntegerField(default=1)
    config = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.channel} - {'Habilitado' if self.enabled else 'Deshabilitado'}"

class MetaAPI(models.Model):
    """Configuración de la API de Meta para WhatsApp Cloud API."""
    name = models.CharField(max_length=100, help_text="Nombre descriptivo")
    app_id = models.CharField(max_length=100, help_text="App ID de Meta")
    app_secret = models.CharField(max_length=100, help_text="App Secret de Meta")
    access_token = models.CharField(max_length=500, help_text="Access Token de WhatsApp Cloud API")
    phone_number_id = models.CharField(max_length=100, help_text="Phone Number ID asignado por Meta")
    phone_id_formatted = models.CharField(max_length=20, help_text="Número de teléfono formateado (ej: 5215512345678)")
    business_account_id = models.CharField(max_length=100, help_text="Business Account ID")
    webhook_verify_token = models.CharField(max_length=100, help_text="Token de verificación para Webhook")
    active = models.BooleanField(default=True, help_text="Indicador si esta configuración está activa")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Configuración Meta API"
        verbose_name_plural = "Configuraciones Meta API"
        
    def __str__(self):
        return f"{self.name} - {self.phone_id_formatted} ({'Activo' if self.active else 'Inactivo'})"
        
    def save(self, *args, **kwargs):
        # Solo puede haber una configuración activa a la vez
        if self.active:
            MetaAPI.objects.exclude(pk=self.pk).update(active=False)
        super().save(*args, **kwargs)

class WhatsAppConfig(models.Model):
    """Configuración de WhatsApp para notificaciones."""
    name = models.CharField(max_length=100, help_text="Nombre descriptivo")
    use_custom_activation_page = models.BooleanField(default=True, help_text="Usar página personalizada para activación")
    activation_url = models.URLField(help_text="URL base para activación personalizada", default="https://huntred.com/activate-whatsapp")
    template_namespace = models.CharField(max_length=100, help_text="Namespace para templates de WhatsApp", blank=True, null=True)
    template_language = models.CharField(max_length=10, default="es_MX", help_text="Idioma para templates de WhatsApp")
    active = models.BooleanField(default=True, help_text="Indicador si esta configuración está activa")
    
    # Plantillas registradas
    templates = models.JSONField(default=dict, blank=True, help_text="Plantillas registradas en WhatsApp API")
    
    # Configuración de rate limiting
    daily_message_limit = models.IntegerField(default=1000, help_text="Límite diario de mensajes")
    hourly_message_limit = models.IntegerField(default=100, help_text="Límite por hora de mensajes")
    cooldown_minutes = models.IntegerField(default=60, help_text="Tiempo de espera después de alcanzar límites")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Configuración WhatsApp"
        verbose_name_plural = "Configuraciones WhatsApp"
        
    def __str__(self):
        return f"{self.name} ({'Activo' if self.active else 'Inactivo'})"
        
    def save(self, *args, **kwargs):
        # Solo puede haber una configuración activa a la vez
        if self.active:
            WhatsAppConfig.objects.exclude(pk=self.pk).update(active=False)
        super().save(*args, **kwargs)

class MessageLog(models.Model):
    """Registro de mensajes enviados."""
    MESSAGE_TYPES = [
        ('WHATSAPP', 'WhatsApp'),
        ('EMAIL', 'Email'),
        ('SMS', 'SMS'),
        ('PUSH', 'Push')
    ]
    STATUS_CHOICES = [
        ('SENT', 'Enviado'),
        ('DELIVERED', 'Entregado'),
        ('READ', 'Leído'),
        ('FAILED', 'Fallido')
    ]
    phone = models.CharField(max_length=20, help_text="Número de teléfono", blank=True, null=True)
    email = models.EmailField(blank=True, null=True, help_text="Email de destino")
    recipient = models.ForeignKey('Person', on_delete=models.CASCADE, null=True, blank=True, related_name='messages')
    message = models.TextField(help_text="Contenido del mensaje")
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES, help_text="Tipo de mensaje")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SENT', help_text="Estado del mensaje")
    response_data = models.JSONField(default=dict, blank=True, help_text="Datos de respuesta de la API")
    sent_at = models.DateTimeField(auto_now_add=True, help_text="Fecha de envío")
    updated_at = models.DateTimeField(auto_now=True, help_text="Última actualización")
    
    class Meta:
        verbose_name = "Log de Mensajes"
        verbose_name_plural = "Logs de Mensajes"
        indexes = [
            models.Index(fields=['phone']),
            models.Index(fields=['email']),
            models.Index(fields=['status']),
            models.Index(fields=['message_type']),
            models.Index(fields=['sent_at'])
        ]
        
    def __str__(self):
        recipient = self.phone or self.email or (self.recipient.nombre if self.recipient else "Unknown")
        return f"{self.message_type} a {recipient} [{self.status}]"

class NotificationConfig(models.Model):
    """Configuración global del canal de notificaciones."""
    name = models.CharField(max_length=100, default="Canal de Notificaciones General")
    whatsapp_channel = models.OneToOneField(
        NotificationChannel,
        on_delete=models.CASCADE,
        related_name='notification_config',
        null=True,
        blank=True,
        help_text="Canal de WhatsApp configurado para notificaciones"
    )
    email_channel = models.OneToOneField(
        NotificationChannel,
        on_delete=models.CASCADE,
        related_name='email_config',
        null=True,
        blank=True,
        help_text="Canal de Email configurado para notificaciones"
    )
    default_channel = models.CharField(
        max_length=20,
        choices=NotificationChannel.CHANNEL_CHOICES,
        default='WHATSAPP',
        help_text="Canal por defecto para notificaciones"
    )
    retry_attempts = models.IntegerField(
        default=3,
        help_text="Número de intentos de reenvío"
    )
    retry_delay_minutes = models.IntegerField(
        default=5,
        help_text="Tiempo de espera entre reintentos (minutos)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Configuración de Notificaciones"
        verbose_name_plural = "Configuraciones de Notificaciones"
        
    def __str__(self):
        return self.name
        
    def get_default_channel(self):
        """Obtiene el canal por defecto habilitado."""
        channel = self.whatsapp_channel if self.default_channel == 'WHATSAPP' else self.email_channel
        return channel if channel and channel.enabled else None
        
    def get_enabled_channels(self):
        """Obtiene todos los canales habilitados."""
        channels = []
        if self.whatsapp_channel and self.whatsapp_channel.enabled:
            channels.append(self.whatsapp_channel)
        if self.email_channel and self.email_channel.enabled:
            channels.append(self.email_channel)
        return channels
        
    def update_channel_config(self, channel_type: str, config: dict):
        """Actualiza la configuración de un canal específico."""
        channel = self.whatsapp_channel if channel_type == 'WHATSAPP' else self.email_channel
        if channel:
            channel.config.update(config)
            channel.save()
            return True
        return False

class ChatState(models.Model):
    person=models.ForeignKey(Person,on_delete=models.CASCADE,related_name='chat_states')
    business_unit=models.ForeignKey(BusinessUnit,on_delete=models.CASCADE,related_name='chat_states')
    state=models.CharField(max_length=50,choices=STATE_TYPE_CHOICES,default='INITIAL')
    last_intent=models.ForeignKey(IntentPattern,on_delete=models.SET_NULL,null=True,blank=True,related_name='chat_states')
    conversation_history=models.JSONField(default=list)
    last_transition = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('person','business_unit')
        
    def __str__(self):
        return f"{self.person.nombre} - {self.business_unit.name} ({self.state})"
    def get_available_intents(self):
        current_state = self.state
        bu = self.business_unit
        transitions = StateTransition.objects.filter(current_state=current_state, business_unit=bu)
        available_intents = IntentPattern.objects.filter(business_units=bu, enabled=True)
        filtered_intents = [intent for intent in available_intents if IntentTransition.objects.filter(current_intent=intent, business_unit=bu).exists()]
        return filtered_intents
    def validate_transition(self, new_state):
        try:
            StateTransition.objects.get(current_state=self.state, next_state=new_state, business_unit=self.business_unit)
            return True
        except StateTransition.DoesNotExist:
            return False
    def transition_to(self, new_state):
        if self.validate_transition(new_state):
            self.state = new_state
            self.last_transition = timezone.now()
            self.save()
            return True
        return False
@receiver(post_save, sender=Person)
def create_chat_states(sender, instance, created, **kwargs):
    """
    Crea estados de chat iniciales para una nueva persona.
    """
    if created:
        for bu in BusinessUnit.objects.all():
            ChatState.objects.create(person=instance,business_unit=bu)
@receiver(post_save,sender=Application)
def update_chat_state_on_application(sender,instance,created,**kwargs):
    if created:
        chat_state=ChatState.objects.get(person=instance.user,business_unit=instance.vacancy.business_unit)
        chat_state.transition_to('APPLY')
@receiver(post_save,sender=Interview)
def update_chat_state_on_interview(sender,instance,created,**kwargs):
    if created:
        chat_state=ChatState.objects.get(person=instance.person,business_unit=instance.job.business_unit)
        chat_state.transition_to('INTERVIEW')
@receiver(post_save,sender=Application)
def update_chat_state_on_offer_accepted(sender,instance,**kwargs):
    if instance.status=='hired':
        chat_state=ChatState.objects.filter(person=instance.user,business_unit=instance.vacancy.business_unit).first()
        if chat_state:
            chat_state.state='HIRED'
            chat_state.last_transition=timezone.now()
            chat_state.save()

class CustomUserManager(BaseUserManager):
    def create_user(self,email,password=None,**extra_fields):
        if not email:
            raise ValueError(_('The Email must be set'))
        email=self.normalize_email(email)
        user=self.model(email=email,**extra_fields)
        user.set_password(password)
        user.save()
        return user
    def create_superuser(self,email,password,**extra_fields):
        extra_fields.setdefault('is_staff',True)
        extra_fields.setdefault('is_superuser',True)
        extra_fields.setdefault('role','SUPER_ADMIN')
        extra_fields.setdefault('status','ACTIVE')
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        return self.create_user(email,password,**extra_fields)

class CustomUser(AbstractUser):
    username=None
    email=models.EmailField(_('email address'),unique=True)
    role=models.CharField(max_length=20,choices=ROLE_CHOICES,default='BU_DIVISION')
    status=models.CharField(max_length=20,choices=USER_STATUS_CHOICES,default='PENDING_APPROVAL')
    verification_status=models.CharField(max_length=20,choices=VERIFICATION_STATUS_CHOICES,default='PENDING')
    business_unit=models.ForeignKey(BusinessUnit,on_delete=models.SET_NULL,null=True,blank=True)
    division=models.CharField(max_length=50,choices=DIVISION_CHOICES,blank=True,null=True)
    phone_number=models.CharField(max_length=20,blank=True,null=True)
    emergency_contact=models.CharField(max_length=20,blank=True,null=True)
    emergency_contact_name=models.CharField(max_length=100,blank=True,null=True)
    address=models.TextField(blank=True,null=True)
    date_of_birth=models.DateField(blank=True,null=True)
    USERNAME_FIELD='email'
    REQUIRED_FIELDS=['first_name','last_name']
    objects=CustomUserManager()
    class Meta:
        ordering=['-date_joined']
        verbose_name='Usuario'
        verbose_name_plural='Usuarios'
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"
    def has_bu_access(self,bu_name):
        if self.role=='SUPER_ADMIN':
            return True
        if self.business_unit and self.business_unit.name==bu_name:
            return True
        return False
    def has_division_access(self,division_name):
        if self.role=='SUPER_ADMIN':
            return True
        if self.division==division_name:
            return True
        return False
    def has_permission(self,permission):
        return self.userpermission_set.filter(permission=permission).exists()
    def clean(self):
        if not self.email:
            raise ValidationError(_('El email no puede estar vacío.'))
    def save(self,*args,**kwargs):
        self.full_clean()
        super().save(*args,**kwargs)

class UserPermission(models.Model):
    user=models.ForeignKey(CustomUser,on_delete=models.CASCADE,related_name='permissions')
    permission=models.CharField(max_length=50,choices=PERMISSION_CHOICES)
    business_unit=models.ForeignKey(BusinessUnit,on_delete=models.CASCADE,null=True,blank=True)
    division=models.CharField(max_length=50,choices=DIVISION_CHOICES,blank=True,null=True)
    class Meta:
        unique_together=('user','permission','business_unit','division')
        verbose_name='Permiso de Usuario'
        verbose_name_plural='Permisos de Usuarios'
    def __str__(self):
        return f"{self.user.email} - {self.permission}"

class FailedLoginAttempt(models.Model):
    email=models.EmailField()
    ip_address=models.GenericIPAddressField()
    user_agent=models.TextField()
    attempt_time=models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.email} - {self.attempt_time}"
    def clean(self):
        if not self.user_agent:
            raise ValidationError(_('El user_agent no puede estar vacío.'))
    def save(self,*args,**kwargs):
        self.full_clean()
        super().save(*args,**kwargs)

class UserActivityLog(models.Model):
    user=models.ForeignKey(CustomUser,on_delete=models.CASCADE,related_name='activity_logs')
    action=models.CharField(max_length=100)
    description=models.TextField()
    ip_address=models.GenericIPAddressField()
    user_agent=models.TextField()
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta:
        verbose_name='Registro de Actividad'
        verbose_name_plural='Registros de Actividad'
        ordering=['-created_at']
    def __str__(self):
        return f"{self.user.email} - {self.action} ({self.created_at})"
    def save(self,*args,**kwargs):
        if not self.user_agent:
            raise ValidationError(_('El user_agent no puede estar vacío.'))
        super().save(*args,**kwargs)
@receiver(post_save,sender=CustomUser)
@sync_to_async
def create_user_activity(sender,instance,created,**kwargs):
    if created:
        UserActivityLog.objects.create(
            user=instance,
            action='USER_CREATED',
            description=f'Nueva cuenta de usuario creada: {instance.email}',
            ip_address='127.0.0.1',
            user_agent='System'
        )
@receiver(post_save,sender=FailedLoginAttempt)
@sync_to_async
def log_failed_login(sender,instance,created,**kwargs):
    if created:
        UserActivityLog.objects.create(
            user=None,
            action='FAILED_LOGIN',
            description=f'Intento fallido de login desde {instance.ip_address}',
            ip_address=instance.ip_address,
            user_agent=instance.user_agent
        )
@receiver(post_save,sender=UserPermission)
@sync_to_async
def log_permission_change(sender,instance,created,**kwargs):
    action='PERMISSION_GRANTED' if created else 'PERMISSION_UPDATED'
    UserActivityLog.objects.create(
        user=instance.user,
        action=action,
        description=f'Permiso {instance.permission} actualizado',
        ip_address='127.0.0.1',
        user_agent='System'
    )

class Invitacion(models.Model):
    referrer=models.ForeignKey(Person,related_name='invitaciones_enviadas',on_delete=models.CASCADE)
    invitado=models.ForeignKey(Person,related_name='invitaciones_recibidas',on_delete=models.CASCADE)
    created_at=models.DateTimeField(auto_now_add=True)

class Division(models.Model):
    name=models.CharField(max_length=100,unique=True)
    skills=models.ManyToManyField('Skill',blank=True)
    def __str__(self):
        return self.name

class Skill(models.Model):
    name=models.CharField(max_length=100,unique=True)
    def __str__(self):
        return self.name

class Badge(models.Model):
    name=models.CharField(max_length=100)
    description=models.TextField()
    icon=models.ImageField(upload_to='badges/',null=True,blank=True)
    def __str__(self):
        return self.name

class DivisionTransition(models.Model):
    person=models.ForeignKey(Person,on_delete=models.CASCADE)
    from_division=models.CharField(max_length=50)
    to_division=models.CharField(max_length=50)
    success=models.BooleanField(default=True)
    date=models.DateTimeField(auto_now_add=True)

class ApiConfig(models.Model):
    business_unit=models.ForeignKey(BusinessUnit,related_name='api_configs',on_delete=models.CASCADE,null=True,blank=True,help_text="Si está vacío, la configuración es global para todas las unidades de negocio")
    api_type=models.CharField(max_length=50,choices=COMUNICATION_CHOICES)
    category=models.CharField(max_length=50,choices=API_CATEGORY_CHOICES,help_text="Categoría de la API para identificar su propósito principal")
    api_key=models.CharField(max_length=255,blank=True,null=True)
    api_secret=models.CharField(max_length=255,blank=True,null=True)
    additional_settings=models.JSONField(default=dict,blank=True,null=True)
    description=models.TextField(blank=True,null=True)
    enabled=models.BooleanField(default=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    
    @classmethod
    def get_config(cls, api_type, business_unit=None):
        """
        Obtiene la configuración de API más apropiada para el tipo y unidad de negocio especificados.
        Si no existe una configuración específica, retorna None.
        """
        try:
            if business_unit:
                return cls.objects.get(
                    api_type=api_type,
                    business_unit=business_unit,
                    enabled=True
                )
            else:
                return cls.objects.get(
                    api_type=api_type,
                    business_unit__isnull=True,
                    enabled=True
                )
        except cls.DoesNotExist:
            return None
    def __str__(self):
        return f"{self.business_unit.name if self.business_unit else 'Global'} - {self.api_type} - {self.description[:50]}"
    class Meta:
        verbose_name="API Configuration"
        verbose_name_plural="API Configurations"
        unique_together=['business_unit','api_type']
    def get_verification_settings(self):
        if self.api_type in ['incode','blacktrust']:
            return {
                'base_url':self.additional_settings.get('base_url',{
                    'incode':'https://api.incode.com',
                    'blacktrust':'https://api.blacktrust.com'
                }.get(self.api_type)),
                'timeout':self.additional_settings.get('timeout',30),
                'retry_count':self.additional_settings.get('retry_count',3),
                'verification_types':self.additional_settings.get('verification_types',{
                    'incode':['INE','ID','passport'],
                    'blacktrust':['criminal','credit','employment']
                }.get(self.api_type))
            }
        return self.additional_settings
    def get_payment_settings(self):
        if self.api_type in ['paypal','stripe','mercado_pago']:
            settings = {
                'base_url': self.additional_settings.get('base_url', {
                    'paypal': 'https://api.paypal.com',
                    'stripe': 'https://api.stripe.com',
                    'mercado_pago': 'https://api.mercadopago.com'
                }.get(self.api_type)),
                'timeout': self.additional_settings.get('timeout', 30),
                'retry_count': self.additional_settings.get('retry_count', 3),
                'webhook_url': self.additional_settings.get('webhook_url'),
                'currency': self.additional_settings.get('currency', 'MXN'),
                'environment': self.additional_settings.get('environment', 'production')
            }
            if self.api_type == 'stripe':
                settings['version'] = self.additional_settings.get('version', '2023-10-16')
            elif self.api_type == 'mercado_pago':
                settings['public_key'] = self.additional_settings.get('public_key')
            return settings
        return self.additional_settings
    def get_business_units(self):
        if self.business_unit:
            return [self.business_unit]
        return BusinessUnit.objects.all()

class MetaAPI(models.Model):
    business_unit=models.OneToOneField(BusinessUnit,on_delete=models.CASCADE,related_name='meta_api_config')
    app_id=models.CharField(max_length=255,default='662158495636216')
    app_secret=models.CharField(max_length=255,default='...')
    verify_token=models.CharField(max_length=255,default='amigro_secret_token')
    def __str__(self):
        return f"MetaAPI {self.business_unit.name} ({self.app_id})"

class WhatsAppAPI(models.Model):
    business_unit=models.ForeignKey(BusinessUnit,on_delete=models.CASCADE,related_name='whatsapp_apis',null=True,blank=True)
    name=models.CharField(max_length=50)
    phoneID=models.CharField(max_length=20,default='114521714899382')
    api_token=models.CharField(max_length=500,default='...')
    WABID=models.CharField(max_length=20,default='104851739211207')
    v_api=models.CharField(max_length=10,default='v22.0')
    meta_api=models.ForeignKey(MetaAPI,on_delete=models.CASCADE)
    is_active=models.BooleanField(default=True)
    def __str__(self):
        return f"{self.business_unit.name if self.business_unit else ''} - WhatsApp API {self.phoneID}"

class Template(models.Model):
    TEMPLATE_TYPES=[('FLOW','Flow'),('BUTTON','Button'),('URL','URL'),('IMAGE','Image')]
    whatsapp_api=models.ForeignKey(WhatsAppAPI,on_delete=models.CASCADE,related_name='templates')
    name=models.CharField(max_length=100)
    is_flow=models.BooleanField(default=False)
    template_type=models.CharField(max_length=20,choices=TEMPLATE_TYPES)
    image_url=models.URLField(blank=True,null=True)
    language_code=models.CharField(max_length=10,default='es_MX')
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    class Meta:
        unique_together=('whatsapp_api','name','language_code')
    def __str__(self):
        return f"{self.name} ({self.language_code}) - {self.whatsapp_api.business_unit.name if self.whatsapp_api.business_unit else 'Sin BU'}"

class MessengerAPI(models.Model):
    business_unit=models.ForeignKey(BusinessUnit,on_delete=models.CASCADE,related_name='messenger_apis',null=True,blank=True)
    page_id=models.CharField(max_length=255,unique=True)
    page_access_token=models.CharField(max_length=255)
    meta_api=models.ForeignKey(MetaAPI,on_delete=models.CASCADE)
    is_active=models.BooleanField(default=True)
    def __str__(self):
        return f"{self.business_unit.name if self.business_unit else ''} - Messenger API"

class InstagramAPI(models.Model):
    business_unit=models.ForeignKey(BusinessUnit,on_delete=models.CASCADE,related_name='instagram_apis',null=True,blank=True)
    app_id=models.CharField(max_length=255,default='1615393869401916')
    access_token=models.CharField(max_length=255,default='...')
    instagram_account_id=models.CharField(max_length=255,default='17841457231476550')
    meta_api=models.ForeignKey(MetaAPI,on_delete=models.CASCADE)
    is_active=models.BooleanField(default=True)
    def __str__(self):
        return f"{self.business_unit.name if self.business_unit else ''} - Instagram API"

class TelegramAPI(models.Model):
    business_unit=models.ForeignKey(BusinessUnit,on_delete=models.CASCADE,related_name='telegram_apis',null=True,blank=True)
    api_key=models.CharField(max_length=255)
    bot_name=models.CharField(max_length=255,blank=True,null=True)
    is_active=models.BooleanField(default=True)
    def __str__(self):
        return f"{self.business_unit.name if self.business_unit else ''} - Telegram Bot"

class SlackAPI(models.Model):
    business_unit=models.ForeignKey(BusinessUnit,on_delete=models.CASCADE)
    bot_token=models.CharField(max_length=255)
    is_active=models.BooleanField(default=True)

class Provider(models.Model):
    name=models.CharField(max_length=50,unique=True,verbose_name="Nombre del proveedor")
    api_endpoint=models.URLField(verbose_name="Endpoint de la API",help_text="URL base para interactuar con la API")
    models_endpoint=models.URLField(blank=True,null=True,verbose_name="Endpoint de modelos",help_text="URL para obtener modelos disponibles")
    class Meta:
        verbose_name="Proveedor de IA"
        verbose_name_plural="Proveedores de IA"
    def __str__(self):
        return self.name
    def fetch_models(self,api_token=None):
        if not self.models_endpoint or not api_token:
            return []
        try:
            headers={"Authorization":f"Bearer {api_token}"}
            response=requests.get(self.models_endpoint,headers=headers)
            response.raise_for_status()
            data=response.json()
            if self.name=="OpenAI":
                return [model["id"] for model in data["data"]]
            elif self.name=="Grok (X AI)":
                return data.get("models",[])
            elif self.name=="Google (Gemini)":
                return [model["name"] for model in data.get("models",[])]
            return []
        except Exception as e:
            logger.error(f"Error al obtener modelos de {self.name}: {e}")
            return []

class GptApi(models.Model):
    provider=models.ForeignKey(Provider,on_delete=models.CASCADE,verbose_name="Proveedor")
    model=models.CharField(max_length=100,verbose_name="Modelo específico",help_text="Ejemplo: gpt-4o, gemini-1.5-flash-001")
    is_active=models.BooleanField(default=False,verbose_name="Activo")
    api_token=models.CharField(max_length=255,blank=True,null=True,verbose_name="Token API")
    organization=models.CharField(max_length=100,blank=True,null=True,verbose_name="Organización")
    project=models.CharField(max_length=100,blank=True,null=True,verbose_name="Proyecto")
    max_tokens=models.IntegerField(default=1000,verbose_name="Máximo de tokens")
    temperature=models.FloatField(default=0.7,verbose_name="Temperatura")
    top_p=models.FloatField(default=1.0,verbose_name="Top P")
    prompts=models.JSONField(default=dict,blank=True,verbose_name="Prompts personalizados")
    tabiya_enabled=models.BooleanField(default=False,verbose_name="Tabiya habilitado")
    class Meta:
        verbose_name="Configuración de API GPT"
        verbose_name_plural="Configuraciones de API GPT"
    def __str__(self):
        return f"{self.model} ({self.provider.name}) - {'Activo' if self.is_active else 'Inactivo'}"
    def get_prompt(self,key,default=None):
        return self.prompts.get(key,default)
    def save(self,*args,**kwargs):
        if self.is_active:
            GptApi.objects.filter(is_active=True).exclude(id=self.id).update(is_active=False)
        super().save(*args,**kwargs)
    def available_models(self):
        return self.provider.fetch_models(self.api_token)

class Chat(models.Model):
    body=models.TextField(max_length=1000)
    SmsStatus=models.CharField(max_length=15,null=True,blank=True)
    From=models.CharField(max_length=15)
    To=models.CharField(max_length=15)
    ProfileName=models.CharField(max_length=50)
    ChannelPrefix=models.CharField(max_length=50)
    MessageSid=models.CharField(max_length=100,null=True,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    message_count=models.IntegerField(default=0)
    def __str__(self):
        return str(self.body)

class JobOpportunity(models.Model):
    title=models.CharField(max_length=255)
    description=models.TextField()
    requirements=models.TextField()
    location=models.CharField(max_length=255)
    salary=models.CharField(max_length=100,blank=True,null=True)
    status=models.CharField(max_length=20,choices=[
        ('DRAFT', 'Borrador'),
        ('ACTIVE', 'Activa'),
        ('PAUSED', 'En Pausa'),
        ('CLOSED', 'Cerrada')
    ], default='DRAFT')
    business_unit=models.ForeignKey(BusinessUnit,on_delete=models.CASCADE,related_name='job_opportunities')
    
    # Información de plazas
    numero_plazas=models.IntegerField(default=1, help_text="Número total de plazas disponibles")
    plazas_restantes=models.IntegerField(default=1, help_text="Número de plazas aún disponibles")
    
    # Información de contratación
    contrataciones_exitosas=models.IntegerField(default=0, help_text="Número de contrataciones exitosas")
    candidatos_aplicados=models.ManyToManyField('Person', through='JobApplication', related_name='opportunities_applied')
    
    # Información de publicación
    fecha_publicacion=models.DateTimeField(null=True, blank=True, help_text="Fecha de primera publicación")
    fecha_cierre=models.DateTimeField(null=True, blank=True, help_text="Fecha de cierre de la oportunidad")
    
    # Configuración de publicación
    publicar_en=models.JSONField(default=list, help_text="Plataformas donde se publicará la oportunidad")
    frecuencia_publicacion=models.IntegerField(default=1, help_text="Frecuencia de publicación en días")
    max_candidatos=models.IntegerField(default=100, help_text="Máximo número de candidatos a aceptar")
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    def get_publish_channels(self):
        from app.publish.models import Channel
        return Channel.objects.filter(business_unit=self.business_unit,is_active=True)
    def get_channel_config(self,channel_type):
        if channel_type=='WHATSAPP':
            return WhatsAppAPI.objects.filter(business_unit=self.business_unit,is_active=True).first()
        elif channel_type=='TELEGRAM':
            return TelegramAPI.objects.filter(business_unit=self.business_unit,is_active=True).first()
        return None

class SmtpConfig(models.Model):
    host=models.CharField(max_length=255)
    port=models.IntegerField()
    username=models.CharField(max_length=255)
    password=models.CharField(max_length=255,blank=True,null=True)
    use_tls=models.BooleanField(default=True)
    use_ssl=models.BooleanField(default=False)
    def __str__(self):
        return f"{self.host}:{self.port}"

class UserInteractionLog(models.Model):
    user_id=models.CharField(max_length=100,db_index=True)
    platform=models.CharField(max_length=50,blank=True,null=True)
    business_unit=models.ForeignKey(BusinessUnit,on_delete=models.SET_NULL,null=True,blank=True)
    timestamp=models.DateTimeField(auto_now_add=True)
    message_direction=models.CharField(max_length=10,choices=[('in','Inbound'),('out','Outbound')],default='in')
    def __str__(self):
        return f"{self.user_id} - {self.platform} - {self.timestamp}"

class ReporteScraping(models.Model):
    business_unit=models.ForeignKey(BusinessUnit,on_delete=models.CASCADE)
    fecha=models.DateField(default=timezone.now)
    vacantes_creadas=models.IntegerField(default=0)
    exitosos=models.IntegerField(default=0)
    fallidos=models.IntegerField(default=0)
    parciales=models.IntegerField(default=0)
    def __str__(self):
        return f"Reporte de Scraping - {self.business_unit.name} - {self.fecha}"

class EnhancedMLProfile(models.Model):
    user=models.OneToOneField(Person,on_delete=models.CASCADE,related_name='ml_profile')
    points=models.IntegerField(default=0)
    level=models.IntegerField(default=1)
    performance_score=models.FloatField(validators=[MinValueValidator(0.0),MaxValueValidator(100.0)],default=0.0)
    model_version=models.CharField(max_length=50,default='v1.0')
    last_prediction_timestamp=models.DateTimeField(null=True,blank=True)
    learning_potential=models.FloatField(default=0.5)
    feedback_count=models.IntegerField(default=0)
    improvement_suggestions=models.JSONField(null=True,blank=True)
    def update_performance_metrics(self,ml_insights):
        self.performance_score=ml_insights.get('score',0.0)
        self.skill_adaptability_index=ml_insights.get('adaptability',0.5)
        self.improvement_suggestions=ml_insights.get('recommendations',[])
        self.last_prediction_timestamp=timezone.now()
        self.save()
        logger.info(f"Actualizadas métricas de ML para {self.user}")
    def log_model_feedback(self,feedback_data):
        self.feedback_count+=1
        self.last_prediction_timestamp=timezone.now()
        self.save()
        logger.info(f"Feedback registrado para {self.user}: {feedback_data}")
    def __str__(self):
        return f"EnhancedMLProfile for {self.user.nombre} {self.user.apellido_paterno}"

class ModelTrainingLog(models.Model):
    business_unit=models.ForeignKey(BusinessUnit,on_delete=models.CASCADE)
    accuracy=models.FloatField()
    trained_at=models.DateTimeField(auto_now_add=True)
    model_version=models.CharField(max_length=50)

class QuarterlyInsight(models.Model):
    business_unit=models.ForeignKey(BusinessUnit,on_delete=models.CASCADE)
    insights_data=models.JSONField(null=True,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)

class MigrantSupportPlatform(models.Model):
    user=models.OneToOneField(Person,on_delete=models.CASCADE)
    preferred_locations=JSONField(default=list)
    work_authorization_status=models.CharField(max_length=50)
    language_proficiencies=JSONField(default=dict)
    family_members_seeking_work=models.IntegerField(default=0)
    network_connections=models.ManyToManyField('self',blank=True)
    cultural_training_completed=models.BooleanField(default=False)
    legal_support_needed=models.BooleanField(default=False)
    potential_business_units=models.ManyToManyField(BusinessUnit)
    def match_cross_unit_opportunities(self):
        matching_opportunities=[]
        for unit in self.potential_business_units.all():
            opportunities=self._find_opportunities_in_unit(unit)
            matching_opportunities.extend(opportunities)
        return matching_opportunities

class EnhancedNetworkGamificationProfile(models.Model):
    user=models.OneToOneField(Person,on_delete=models.CASCADE)
    professional_points=models.IntegerField(default=0)
    skill_endorsements=models.IntegerField(default=0)
    network_expansion_level=models.IntegerField(default=1)
    def award_points(self,activity_type):
        point_system={
            'profile_update':10,
            'skill_endorsement':15,
            'successful_referral':50,
            'completed_challenge':25,
            'connection_made':5
        }
        points=point_system.get(activity_type,0)
        self.professional_points+=points
        self._update_network_level()
        self.save()
    def _update_network_level(self):
        level_thresholds=[(100,2),(250,3),(500,4),(1000,5)]
        for threshold,level in level_thresholds:
            if self.professional_points>=threshold:
                self.network_expansion_level=level
    def generate_networking_challenges(self):
        challenges=[
            {
                'title':'Expand Your Network',
                'description':'Connect with 5 professionals in your industry',
                'points_reward':25,
                'deadline':timezone.now()+timezone.timedelta(days=30)
            },
            {
                'title':'Skill Showcase',
                'description':'Get 3 endorsements for a new skill',
                'points_reward':30,
                'deadline':timezone.now()+timezone.timedelta(days=45)
            }
        ]
        return challenges

class VerificationCode(models.Model):
    PURPOSE_CHOICES=[('update_whatsapp','Actualizar WhatsApp')]
    person=models.ForeignKey(Person,on_delete=models.CASCADE)
    key=models.UUIDField(default=uuid.uuid4,editable=False,unique=True)
    purpose=models.CharField(max_length=50,choices=PURPOSE_CHOICES)
    created_at=models.DateTimeField(auto_now_add=True)
    is_used=models.BooleanField(default=False)
    def __str__(self):
        return f"{self.person.first_name} {self.person.last_name} - {self.purpose} - {'Usado' if self.is_used else 'No usado'}"

class Interaction(models.Model):
    person=models.ForeignKey(Person,on_delete=models.CASCADE,related_name='interactions')
    timestamp=models.DateTimeField(auto_now_add=True)
    business_unit=models.ForeignKey(BusinessUnit,on_delete=models.SET_NULL,null=True,blank=True)
    chat_state=models.CharField(max_length=100,null=True,blank=True)
    def __str__(self):
        return f"Interacción de {self.person} en {self.timestamp}"

# Modelos de Pagos

class EstadoPerfil(models.TextChoices):
    ACTIVO = 'activo', 'Activo'
    INACTIVO = 'inactivo', 'Inactivo'
    SUSPENDIDO = 'suspendido', 'Suspendido'

class TipoDocumento(models.TextChoices):
    RFC = 'rfc', 'RFC'
    CURP = 'curp', 'CURP'
    DNI = 'dni', 'DNI'
    PASAPORTE = 'pasaporte', 'Pasaporte'

class Empleador(models.Model):
    persona = models.OneToOneField(Person, on_delete=models.CASCADE, related_name='empleador')
    
    # Información fiscal
    razon_social = models.CharField(max_length=255)
    rfc = models.CharField(max_length=13, unique=True)
    direccion_fiscal = models.TextField()
    
    # Información bancaria
    clabe = models.CharField(max_length=18, unique=True)
    banco = models.CharField(max_length=100)
    
    # Información de contacto
    sitio_web = models.URLField(null=True, blank=True)
    telefono_oficina = models.CharField(max_length=20)
    
    # Estado
    estado = models.CharField(max_length=20, choices=EstadoPerfil.choices, default=EstadoPerfil.ACTIVO)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    # Documentos
    documento_identidad = models.FileField(upload_to='empleadores/documentos/')
    comprobante_domicilio = models.FileField(upload_to='empleadores/documentos/')
    
    class Meta:
        ordering = ['-fecha_registro']
        verbose_name = 'Empleador'
        verbose_name_plural = 'Empleadores'

    def __str__(self):
        return self.razon_social

    def validar_documentos(self):
        """Valida que todos los documentos requeridos estén presentes y sean válidos"""
        return True  # Implementación pendiente

class Worker(models.Model):
    persona = models.OneToOneField(Person, on_delete=models.CASCADE, related_name='worker')
    
    # Información laboral
    nss = models.CharField(max_length=11, unique=True, null=True, blank=True)
    ocupacion = models.CharField(max_length=100)
    experiencia_anios = models.IntegerField(default=0)
    
    # Información bancaria
    clabe = models.CharField(max_length=18, unique=True)
    banco = models.CharField(max_length=100)
    
    # Estado
    estado = models.CharField(max_length=20, choices=EstadoPerfil.choices, default=EstadoPerfil.ACTIVO)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    # Documentos
    documento_identidad = models.FileField(upload_to='workers/documentos/')
    comprobante_domicilio = models.FileField(upload_to='workers/documentos/')
    
    class Meta:
        ordering = ['-fecha_registro']
        verbose_name = 'Worker'
        verbose_name_plural = 'Workers'

    def __str__(self):
        return f"{self.persona.nombre} {self.persona.apellido_paterno}"

    def validar_documentos(self):
        """Valida que todos los documentos requeridos estén presentes y sean válidos"""
        return True  # Implementación pendiente

class Oportuncupidad(models.Model):
    empleador = models.ForeignKey(Empleador, on_delete=models.CASCADE, related_name='oportunidades')
    titulo = models.CharField(max_length=255)
    descripcion = models.TextField()
    
    # Detalles del trabajo
    tipo_contrato = models.CharField(max_length=50, choices=[
        ('tiempo_completo', 'Tiempo Completo'),
        ('medio_tiempo', 'Medio Tiempo'),
        ('freelance', 'Freelance'),
        ('proyecto', 'Por Proyecto')
    ])
    salario_minimo = models.DecimalField(max_digits=10, decimal_places=2)
    salario_maximo = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Ubicación
    pais = models.CharField(max_length=50)
    ciudad = models.CharField(max_length=100)
    modalidad = models.CharField(max_length=50, choices=[
        ('presencial', 'Presencial'),
        ('remoto', 'Remoto'),
        ('hibrido', 'Híbrido')
    ])
    
    # Estado
    estado = models.CharField(max_length=20, choices=EstadoPerfil.choices, default=EstadoPerfil.ACTIVO)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-fecha_creacion']
        verbose_name = 'Oportunidad'
        verbose_name_plural = 'Oportunidades'

    def __str__(self):
        return self.titulo

class EstadoPago(models.TextChoices):
    PENDIENTE = 'pendiente', 'Pendiente'
    COMPLETADO = 'completado', 'Completado'
    FALLIDO = 'fallido', 'Fallido'
    RECHAZADO = 'rechazado', 'Rechazado'
    EN_PROCESO = 'en_proceso', 'En Proceso'
    REFUNDADO = 'reembolsado', 'Reembolsado'

class TipoPago(models.TextChoices):
    MONOEDO = 'monoedo', 'Pago Simple'
    MULTIEDO = 'multiedo', 'Pago Múltiple'
    RECURRENTE = 'recurrente', 'Pago Recurrente'
    PRUEBA = 'prueba', 'Pago de Prueba'

class MetodoPago(models.TextChoices):
    PAYPAL = 'paypal', 'PayPal'
    STRIPE = 'stripe', 'Stripe'
    MERCADOPAGO = 'mercadopago', 'MercadoPago'
    TRANSFERENCIA = 'transferencia', 'Transferencia Bancaria'
    CRYPTO = 'crypto', 'Criptomonedas'

class Pago(models.Model):
    empleador = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='pagos_enviados')
    vacante = models.ForeignKey(Vacante, on_delete=models.CASCADE, related_name='pagos')
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE, related_name='pagos_recibidos')
    
    # Información de la oportunidad
    oportunidad_id = models.CharField(max_length=100, db_index=True, help_text="ID único de la oportunidad")
    oportunidad_descripcion = models.TextField(help_text="Descripción detallada de la oportunidad")
    numero_plazas = models.IntegerField(default=1, help_text="Número de plazas o contrataciones asociadas")
    plazas_contratadas = models.IntegerField(default=0, help_text="Número de plazas ya contratadas")
    
    # Información de seguimiento
    referencia_cliente = models.CharField(max_length=100, null=True, blank=True, help_text="Referencia interna del cliente")
    numero_contrato = models.CharField(max_length=50, null=True, blank=True, help_text="Número de contrato asociado")
    
    # Información financiera
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    monto_por_plaza = models.DecimalField(max_digits=10, decimal_places=2, help_text="Monto base por plaza")
    moneda = models.CharField(max_length=3, default='USD')
    metodo = models.CharField(max_length=20, choices=MetodoPago.choices, default=MetodoPago.PAYPAL)
    tipo = models.CharField(max_length=20, choices=TipoPago.choices, default=TipoPago.MONOEDO)
    
    # Estado y seguimiento
    estado = models.CharField(max_length=20, choices=EstadoPago.choices, default=EstadoPago.PENDIENTE)
    intentos = models.IntegerField(default=0)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    fecha_procesamiento = models.DateTimeField(null=True, blank=True)
    
    # Información del gateway
    id_transaccion = models.CharField(max_length=255, null=True, blank=True)
    url_webhook = models.URLField(null=True, blank=True)
    webhook_payload = models.JSONField(null=True, blank=True)
    
    # Información adicional
    descripcion = models.TextField(null=True, blank=True)
    metadata = models.JSONField(default=dict)
    
    class Meta:
        ordering = ['-fecha_creacion']
        verbose_name = 'Pago'
        verbose_name_plural = 'Pagos'
        indexes = [
            models.Index(fields=['oportunidad_id']),
            models.Index(fields=['estado']),
            models.Index(fields=['fecha_procesamiento'])
        ]
    
    def __str__(self):
        return f'Pago #{self.id} - {self.empleador.nombre} -> {self.business_unit.name} (Oportunidad: {self.oportunidad_id})'
    
    def actualizar_estado(self, nuevo_estado, metadata=None):
        """Actualiza el estado del pago y crea un registro histórico."""
        historico = PagoHistorico.objects.create(
            pago=self,
            estado_anterior=self.estado,
            metadata=metadata or {}
        )
        self.estado = nuevo_estado
        self.fecha_actualizacion = timezone.now()
        self.save()
        return historico
    
    def marcar_como_completado(self, transaccion_id=None):
        self.estado = EstadoPago.COMPLETADO
        self.id_transaccion = transaccion_id
        self.save()

    def marcar_como_fallido(self, motivo=None):
        self.estado = EstadoPago.FALLIDO
        self.metadata['motivo_fallo'] = motivo
        self.save()

    def plazas_disponibles(self):
        """Devuelve el número de plazas disponibles para contratación."""
        return self.numero_plazas - self.plazas_contratadas
    
    def actualizar_plazas_contratadas(self, cantidad):
        """Actualiza el número de plazas contratadas."""
        if cantidad > self.plazas_disponibles():
            raise ValueError(f"No hay suficientes plazas disponibles. Disponibles: {self.plazas_disponibles()}")
        self.plazas_contratadas += cantidad
        self.save()
    
    def calcular_monto_total(self):
        """Calcula el monto total basado en el número de plazas."""
        return self.monto_por_plaza * self.numero_plazas

class PagoRecurrente(models.Model):
    pago_base = models.OneToOneField(Pago, on_delete=models.CASCADE, related_name='recurrente')
    frecuencia = models.CharField(max_length=20, choices=[
        ('diario', 'Diario'),
        ('semanal', 'Semanal'),
        ('quincenal', 'Quincenal'),
        ('mensual', 'Mensual'),
        ('anual', 'Anual')
    ])
    fecha_proximo_pago = models.DateTimeField()
    fecha_fin = models.DateTimeField(null=True, blank=True)
    activo = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-fecha_proximo_pago']
        verbose_name = 'Pago Recurrente'
        verbose_name_plural = 'Pagos Recurrentes'

    def __str__(self):
        return f'Pago Recurrente #{self.pago_base.id}'

    def actualizar_proximo_pago(self):
        """Actualiza la fecha del próximo pago según la frecuencia."""
        if not self.activo:
            return
            
        if self.frecuencia == 'diario':
            self.fecha_proximo_pago += timedelta(days=1)
        elif self.frecuencia == 'semanal':
            self.fecha_proximo_pago += timedelta(days=7)
        elif self.frecuencia == 'quincenal':
            self.fecha_proximo_pago += timedelta(days=15)
        elif self.frecuencia == 'mensual':
            self.fecha_proximo_pago += timedelta(days=30)
        elif self.frecuencia == 'anual':
            self.fecha_proximo_pago += timedelta(days=365)
        self.save()

class PagoHistorico(models.Model):
    pago = models.ForeignKey(Pago, on_delete=models.CASCADE, related_name='historico')
    estado_anterior = models.CharField(max_length=20, choices=EstadoPago.choices)
    fecha_cambio = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict)
    
    class Meta:
        ordering = ['-fecha_cambio']
        verbose_name = 'Historial de Pago'
        verbose_name_plural = 'Historial de Pagos'

    def __str__(self):
        return f'Historial #{self.id} - Pago #{self.pago.id}'

class WebhookLog(models.Model):
    pago = models.ForeignKey(Pago, on_delete=models.CASCADE, related_name='webhook_logs')
    evento = models.CharField(max_length=50)
    payload = models.JSONField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    procesado = models.BooleanField(default=False)
    error = models.TextField(null=True, blank=True)
    
    class Meta:
        ordering = ['-fecha_creacion']
        verbose_name = 'Log de Webhook'
        verbose_name_plural = 'Logs de Webhooks'

    def __str__(self):
        return f'Webhook #{self.id} - {self.evento}'

# Modelos de Sexsi

def calculate_age(birth_date):
    """Calcula la edad dada una fecha de nacimiento."""
    today = date.today()
    age = today.year - birth_date.year
    if today.month < birth_date.month or (today.month == birth_date.month and today.day < birth_date.day):
        age -= 1
    return age

class SexsiConfig(models.Model):
    """
    Configuración exclusiva para el flujo SEXSI.
    Almacena los datos de integración para Hellosign y PayPal.
    """
    name = models.CharField(max_length=100, default="SEXSI Configuración")
    
    # Integración Hellosign
    hellosign_api_key = models.CharField(max_length=255, blank=True, null=True, help_text="API Key para Hellosign")
    hellosign_template_id = models.CharField(max_length=255, blank=True, null=True, help_text="ID de plantilla en Hellosign")
    
    # Integración PayPal (o similar)
    paypal_client_id = models.CharField(max_length=255, blank=True, null=True, help_text="Client ID de PayPal")
    paypal_client_secret = models.CharField(max_length=255, blank=True, null=True, help_text="Client Secret de PayPal")
    
    def __str__(self):
        return self.name

class ConsentAgreement(models.Model):
    """
    Modelo de Acuerdo de Consentimiento con doble validación de firma.
    """
    STATUS_CHOICES = [
        ('draft', 'Borrador'),
        ('pending', 'Pendiente'),
        ('signed_by_creator', 'Firmado por Anfitrión'),
        ('signed_by_invitee', 'Firmado por Invitado'),
        ('completed', 'Completado'),
        ('cancelled', 'Cancelado')
    ]

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_agreements')
    invitee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='invited_agreements', null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_of_encounter = models.DateTimeField()
    location = models.CharField(max_length=200)
    agreement_text = models.TextField()
    
    # Preferencias y prácticas
    preferences = models.ManyToManyField('Preference', related_name='agreements')
    
    # Firma y validaciones
    is_signed_by_creator = models.BooleanField(default=False)
    is_signed_by_invitee = models.BooleanField(default=False)
    creator_signature = models.ImageField(upload_to='signatures/', null=True, blank=True)
    invitee_signature = models.ImageField(upload_to='signatures/', null=True, blank=True)
    creator_selfie = models.ImageField(upload_to='selfies/', null=True, blank=True, help_text="Selfie del creador con identificación")
    invitee_selfie = models.ImageField(upload_to='selfies/', null=True, blank=True, help_text="Selfie del invitado con identificación")
    signature_method = models.CharField(
        max_length=20, 
        choices=(("hellosign", "Hellosign"), ("internal", "Desarrollo Interno")),
        default="internal",
        help_text="Método de firma elegido"
    )
    tos_accepted = models.BooleanField(default=False)
    
    # OTP y verificación de identidad
    otp_code = models.CharField(max_length=6, blank=True, null=True)
    otp_expiry = models.DateTimeField(null=True, blank=True)
    creator_id_document = models.ImageField(upload_to='id_documents/', null=True, blank=True)
    invitee_id_document = models.ImageField(upload_to='id_documents/', null=True, blank=True)
    
    # Seguridad y control de token
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    
    def default_token_expiry():
        return now() + timedelta(hours=36)

    token_expiry = models.DateTimeField(default=default_token_expiry)
    
    def clean(self):
        """Validaciones adicionales"""
        # Validaciones de duración
        if self.duration_type != 'single' and not self.duration_amount:
            raise ValidationError({'duration_amount': 'Debe especificar una cantidad de tiempo para duraciones no únicas.'})
        
        # Validación de fecha de encuentro
        if self.date_of_encounter < now():
            raise ValidationError({'date_of_encounter': 'La fecha del encuentro no puede estar en el pasado.'})
        
        # Validación de participantes
        if self.creator == self.invitee:
            raise ValidationError({'invitee': 'El invitado no puede ser el mismo que el creador del acuerdo.'})
        
        # Validación de firma
        if self.is_signed_by_creator and not self.creator_signature:
            raise ValidationError({'creator_signature': 'Debe cargar una firma para el creador si está marcado como firmado.'})
        if self.is_signed_by_invitee and not self.invitee_signature:
            raise ValidationError({'invitee_signature': 'Debe cargar una firma para el invitado si está marcado como firmado.'})
    
    def get_status_display(self):
        """Obtiene la representación legible del estado."""
        return dict(self.STATUS_CHOICES).get(self.status, 'Desconocido')
    
    def get_duration_display(self):
        """Obtiene la representación legible de la duración."""
        if self.duration_type == 'single':
            return "Encuentro Único"
        return f"{self.duration_amount} {self.get_duration_type_display()}"
    
    def get_absolute_url(self):
        """Obtiene la URL absoluta para este acuerdo."""
        return reverse('sexsi:agreement_detail', kwargs={'pk': self.pk})
    
    def generate_otp(self):
        """Genera un código OTP de 6 dígitos y lo almacena con una validez de 10 minutos."""
        self.otp_code = str(uuid.uuid4().int)[:6]
        self.otp_expiry = now() + timedelta(minutes=10)
        self.save()
        return self.otp_code
    
    def verify_otp(self, otp_input):
        """Verifica si el OTP ingresado es válido."""
        return self.otp_code == otp_input and now() < self.otp_expiry
    
    def is_valid_for_duration(self, preference):
        """Verifica si el acuerdo es válido para la duración de la preferencia."""
        if preference.duration == 'single' and self.duration_type != 'single':
            return False
        if preference.duration in ['short_term', 'long_term'] and self.duration_type == 'single':
            return False
        return True
    
    def __str__(self):
        return f"Acuerdo #{self.id} - {self.creator.username}"

class PaymentTransaction(models.Model):
    """
    Modelo para registrar la transacción de pago asociada al Acuerdo SEXSI.
    Permite almacenar el método, monto, ID de transacción (por PayPal u otro),
    y el estado del pago.
    """
    agreement = models.OneToOneField(ConsentAgreement, on_delete=models.CASCADE, related_name='payment')
    payment_method = models.CharField(max_length=50, default="PayPal", help_text="Método de pago")
    transaction_id = models.CharField(max_length=100, blank=True, null=True, help_text="ID de transacción del servicio de pago")
    transaction_status = models.CharField(max_length=50, default="pending", help_text="Estado del pago")
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Pago {self.id} para Acuerdo #{self.agreement.id}"

class DiscountCoupon(models.Model):
    """Modelo para almacenar cupones de descuento con diferentes porcentajes y un cupón de 100%."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='discount_coupons')
    code = models.CharField(max_length=10, unique=True)
    discount_percentage = models.PositiveIntegerField()
    expiration_date = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    def is_valid(self):
        return not self.is_used and self.expiration_date > now()
    
    def __str__(self):
        return f"Cupon {self.code} - {self.discount_percentage}% - {'Usado' if self.is_used else 'Disponible'}"

class VerificationService(models.Model):
    """
    Modelo que define los tipos de servicios de verificación disponibles.
    Ejemplos: TruthSense™ (identidad), SocialVerify™ (redes), BackgroundCheck (antecedentes), etc.
    """
    CATEGORY_CHOICES = [
        ('identity', 'Verificación de Identidad'),
        ('social', 'Verificación de Redes Sociales'),
        ('education', 'Verificación Educativa'),
        ('experience', 'Verificación de Experiencia'),
        ('background', 'Verificación de Antecedentes')
    ]
    
    name = models.CharField(max_length=128)
    code = models.CharField(max_length=32, unique=True)
    category = models.CharField(max_length=32, choices=CATEGORY_CHOICES)
    description = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Servicio de Verificación"
        verbose_name_plural = "Servicios de Verificación"
        ordering = ['category', 'name']
        indexes = [models.Index(fields=['category']), models.Index(fields=['code'])]
    
    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"

class VerificationAddon(models.Model):
    """
    Modelo que define addons de verificación disponibles para comprar.
    Cada addon tiene un precio y puede estar asociado a uno o más servicios.
    Los addons se organizan en niveles: basic, freemium, premium.
    """
    TIER_CHOICES = [
        ('basic', 'Básico'),
        ('freemium', 'Freemium'),
        ('premium', 'Premium')
    ]
    
    name = models.CharField(max_length=128)
    code = models.CharField(max_length=32, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    tier = models.CharField(max_length=32, choices=TIER_CHOICES, default='basic')
    description = models.TextField()
    services = models.ManyToManyField(VerificationService, related_name='addons')
    max_uses = models.PositiveIntegerField(default=1, help_text="Número máximo de veces que se puede usar este addon por paquete")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Addon de Verificación"
        verbose_name_plural = "Addons de Verificación"
        ordering = ['tier', 'price', 'name']
        indexes = [models.Index(fields=['tier']), models.Index(fields=['code'])]
    
    def __str__(self):
        return f"{self.name} ({self.get_tier_display()}) - ${self.price}"
    
    def get_tier_display(self):
        return dict(self.TIER_CHOICES).get(self.tier, 'Desconocido')

class OpportunityVerificationPackage(models.Model):
    """
    Modelo que representa un paquete de verificación para una oportunidad.
    Contiene la configuración de los addons seleccionados y el precio total.
    """
    opportunity = models.ForeignKey('Opportunity', on_delete=models.CASCADE, related_name='verification_packages')
    name = models.CharField(max_length=128)
    description = models.TextField(blank=True, null=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_packages')
    status = models.CharField(max_length=32, choices=[
        ('draft', 'Borrador'),
        ('active', 'Activo'),
        ('cancelled', 'Cancelado'),
        ('completed', 'Completado')
    ], default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Paquete de Verificación"
        verbose_name_plural = "Paquetes de Verificación"
        ordering = ['-created_at']
        indexes = [models.Index(fields=['opportunity']), models.Index(fields=['status'])]
    
    def __str__(self):
        return f"Paquete de verificación: {self.name} (Oportunidad: {self.opportunity.name})"

class PackageAddonDetail(models.Model):
    """
    Modelo que relaciona addons específicos con un paquete de verificación.
    Almacena el precio individual y cantidad de cada addon.
    """
    package = models.ForeignKey(OpportunityVerificationPackage, on_delete=models.CASCADE, related_name='addon_details')
    addon = models.ForeignKey(VerificationAddon, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Detalle de Addon"
        verbose_name_plural = "Detalles de Addons"
        unique_together = ('package', 'addon')
        indexes = [models.Index(fields=['package']), models.Index(fields=['addon'])]
    
    def __str__(self):
        return f"{self.addon.name} x{self.quantity} - ${self.subtotal}"
    
    def save(self, *args, **kwargs):
        # Calcular el subtotal automáticamente
        self.subtotal = self.unit_price * self.quantity
        super().save(*args, **kwargs)

class CandidateVerification(models.Model):
    """
    Modelo que relaciona un candidato con un paquete de verificación.
    Almacena el estado general de la verificación del candidato.
    """
    package = models.ForeignKey(OpportunityVerificationPackage, on_delete=models.CASCADE, related_name='candidate_verifications')
    candidate = models.ForeignKey('Person', on_delete=models.CASCADE, related_name='verifications')
    status = models.CharField(max_length=32, choices=[
        ('pending', 'Pendiente'),
        ('in_progress', 'En Proceso'),
        ('completed', 'Completado'),
        ('failed', 'Fallido')
    ], default='pending')
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='assigned_verifications')
    assigned_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    overall_score = models.FloatField(null=True, blank=True, help_text="Puntuación general de 0 a 1")
    verification_data = models.JSONField(default=dict, blank=True)
    
    class Meta:
        verbose_name = "Verificación de Candidato"
        verbose_name_plural = "Verificaciones de Candidatos"
        unique_together = ('package', 'candidate')
        indexes = [models.Index(fields=['package']), models.Index(fields=['candidate']), models.Index(fields=['status'])]
    
    def __str__(self):
        return f"Verificación: {self.candidate.name} ({self.get_status_display()})" 
    
    def mark_as_completed(self):
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()

class CandidateServiceResult(models.Model):
    """
    Modelo que almacena los resultados de cada servicio de verificación.
    Cada verificación de candidato puede tener múltiples resultados de servicios.
    """
    verification = models.ForeignKey(CandidateVerification, on_delete=models.CASCADE, related_name='service_results')
    service = models.ForeignKey(VerificationService, on_delete=models.CASCADE)
    addon = models.ForeignKey(VerificationAddon, on_delete=models.CASCADE, null=True)
    status = models.CharField(max_length=32, choices=[
        ('pending', 'Pendiente'),
        ('in_progress', 'En Proceso'),
        ('completed', 'Completado'),
        ('failed', 'Fallido')
    ], default='pending')
    score = models.FloatField(null=True, blank=True, help_text="Puntuación de 0 a 1")
    details = models.JSONField(default=dict, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Resultado de Servicio"
        verbose_name_plural = "Resultados de Servicios"
        unique_together = ('verification', 'service')
        indexes = [models.Index(fields=['verification']), models.Index(fields=['service']), models.Index(fields=['status'])]
    
    def __str__(self):
        return f"Resultado de {self.service.name} para {self.verification.candidate.name}"

class SocialNetworkVerification(models.Model):
    """
    Modelo para almacenar verificaciones específicas de redes sociales.
    Contiene información sobre la red, el perfil y los resultados de la verificación.
    """
    NETWORK_CHOICES = [
        ('linkedin', 'LinkedIn'),
        ('github', 'GitHub'),
        ('facebook', 'Facebook'),
        ('twitter', 'Twitter'),
        ('instagram', 'Instagram'),
        ('tiktok', 'TikTok'),
        ('youtube', 'YouTube'),
        ('other', 'Otra')
    ]
    
    service_result = models.ForeignKey(CandidateServiceResult, on_delete=models.CASCADE, related_name='social_verifications')
    network = models.CharField(max_length=32, choices=NETWORK_CHOICES)
    profile_url = models.URLField(max_length=255)
    profile_name = models.CharField(max_length=128, null=True, blank=True)
    followers_count = models.PositiveIntegerField(null=True, blank=True)
    verified_identity = models.BooleanField(default=False)
    account_age_days = models.PositiveIntegerField(null=True, blank=True)
    reputation_score = models.FloatField(null=True, blank=True)
    verification_data = models.JSONField(default=dict, blank=True)
    verified_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Verificación de Red Social"
        verbose_name_plural = "Verificaciones de Redes Sociales"
        unique_together = ('service_result', 'network', 'profile_url')
        indexes = [models.Index(fields=['service_result']), models.Index(fields=['network'])]
    
    def __str__(self):
        return f"Verificación de {self.get_network_display()} para {self.service_result.verification.candidate.name}"

class AgreementPreference(models.Model):
    """
    Modelo que representa la relación entre un acuerdo y sus preferencias,
    permitiendo almacenar información adicional sobre cada preferencia en el contexto del acuerdo.
    """
    agreement = models.ForeignKey('ConsentAgreement', on_delete=models.CASCADE)
    preference = models.ForeignKey('Preference', on_delete=models.CASCADE)
    is_required = models.BooleanField(default=True, help_text="Indica si esta preferencia es obligatoria para el acuerdo")
    notes = models.TextField(blank=True, null=True, help_text="Notas adicionales sobre esta preferencia en el contexto del acuerdo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('agreement', 'preference')
        ordering = ['preference__category', 'preference__name']

    def __str__(self):
        return f"{self.agreement} - {self.preference}"

class Preference(models.Model):
    """
    Modelo para almacenar preferencias de intimidad y prácticas.
    """
    PREFERENCE_TYPES = [
        ('common', 'Preferencias Comunes'),
        ('discrete', 'Preferencias Discretas'),
        ('advanced', 'Exploraciones Avanzadas'),
        ('exotic', 'Exploraciones Exóticas')
    ]

    code = models.CharField(max_length=10, unique=True, help_text="Código único de la preferencia")
    name = models.CharField(max_length=100, help_text="Nombre descriptivo de la preferencia")
    description = models.TextField(help_text="Descripción detallada de la preferencia")
    category = models.CharField(max_length=20, choices=PREFERENCE_TYPES)
    complexity_level = models.CharField(max_length=20, help_text="Nivel de complejidad de la práctica")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"

    def get_absolute_url(self):
        return reverse('sexsi:preference_detail', kwargs={'pk': self.pk})
    
    def is_compatible_with_duration(self, duration_type):
        """Verifica si esta preferencia es compatible con el tipo de duración del acuerdo."""
        if self.duration == 'single' and duration_type != 'single':
            return False
        if self.duration in ['short_term', 'long_term'] and duration_type == 'single':
            return False
        return True
    
    def get_category_display(self):
        """Obtiene la representación legible de la categoría."""
        return dict(self.PREFERENCE_TYPES).get(self.category, 'Desconocido')


# Importando el User estándar de Django para módulos como SEXSI
from django.contrib.auth.models import User