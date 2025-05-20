# app/models.py

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.contrib.postgres.fields import ArrayField
# Usar JSONField de django.db.models que es la versión actual
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
from typing import Dict, List, Optional, Union, Any, Tuple
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

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('El email es obligatorio')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'SUPER_ADMIN')
        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
    email = models.EmailField(_('email address'), unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='BU_DIVISION')
    status = models.CharField(max_length=20, choices=USER_STATUS_CHOICES, default='ACTIVE')
    business_unit = models.ForeignKey('BusinessUnit', on_delete=models.SET_NULL, null=True, blank=True, related_name='users')
    division = models.ForeignKey('Division', on_delete=models.SET_NULL, null=True, blank=True, related_name='users')
    
    objects = CustomUserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        permissions = [
            ('can_manage_users', 'Puede gestionar usuarios'),
            ('can_view_reports', 'Puede ver reportes'),
            ('can_manage_business_unit', 'Puede gestionar unidad de negocio')
        ]

    def __str__(self):
        return self.email

    @property
    def is_super_admin(self):
        return self.role == 'SUPER_ADMIN'

    @property
    def is_consultant_complete(self):
        return self.role == 'BU_COMPLETE'

    @property
    def is_consultant_division(self):
        return self.role == 'BU_DIVISION'

    def has_bu_access(self, business_unit):
        if self.is_super_admin:
            return True
        return self.business_unit == business_unit

    def has_division_access(self, division):
        if self.is_super_admin or self.is_consultant_complete:
            return True
        return self.division == division

class NotificationChannel(models.Model):
    """Canal de notificación configurado para una unidad de negocio."""
    business_unit = models.ForeignKey(
        'BusinessUnit',
        on_delete=models.CASCADE,
        related_name='notification_channels'
    )
    channel_choices = [
        ('EMAIL', 'Correo Electrónico'),
        ('SMS', 'Mensaje de Texto'),
        ('WHATSAPP', 'WhatsApp'),
        ('PUSH', 'Notificación Push'),
        ('WEB', 'Notificación Web'),
        ('OTHER', 'Otro')
    ]
    channel = models.CharField(
        max_length=20,
        choices=channel_choices,
        help_text="Tipo de canal"
    )
    is_enabled = models.BooleanField(
        default=True,
        help_text="Indica si el canal está habilitado"
    )
    config = models.JSONField(
        default=dict,
        help_text="Configuración específica del canal"
    )
    priority = models.PositiveIntegerField(
        default=0,
        help_text="Prioridad del canal (menor número = mayor prioridad)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Canal de Notificación"
        verbose_name_plural = "Canales de Notificación"
        ordering = ['priority']
        indexes = [
            models.Index(fields=['business_unit']),
            models.Index(fields=['channel']),
            models.Index(fields=['is_enabled']),
            models.Index(fields=['priority'])
        ]
        unique_together = ['business_unit', 'channel']

    def __str__(self):
        return f"{self.get_channel_display()} - {self.business_unit}"

class Notification(models.Model):
    """Notificación enviada a un usuario."""
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    type_choices = [
        ('INFO', 'Información'),
        ('SUCCESS', 'Éxito'),
        ('WARNING', 'Advertencia'),
        ('ERROR', 'Error'),
        ('OTHER', 'Otro')
    ]
    notification_type = models.CharField(
        max_length=20,
        choices=type_choices,
        default='INFO',
        help_text="Tipo de notificación"
    )
    channel = models.ForeignKey(
        NotificationChannel,
        on_delete=models.PROTECT,
        related_name='notifications'
    )
    status_choices = [
        ('PENDING', 'Pendiente'),
        ('SENT', 'Enviada'),
        ('DELIVERED', 'Entregada'),
        ('READ', 'Leída'),
        ('FAILED', 'Fallida')
    ]
    status = models.CharField(
        max_length=20,
        choices=status_choices,
        default='PENDING',
        help_text="Estado de la notificación"
    )
    title = models.CharField(
        max_length=200,
        help_text="Título de la notificación"
    )
    content = models.TextField(
        help_text="Contenido de la notificación"
    )
    metadata = models.JSONField(
        default=dict,
        help_text="Metadatos adicionales"
    )
    sent_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha y hora de envío"
    )
    delivered_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha y hora de entrega"
    )
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha y hora de lectura"
    )
    error_message = models.TextField(
        blank=True,
        help_text="Mensaje de error si falló el envío"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Notificación"
        verbose_name_plural = "Notificaciones"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient']),
            models.Index(fields=['notification_type']),
            models.Index(fields=['channel']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at'])
        ]

    def __str__(self):
        return f"{self.title} - {self.get_notification_type_display()}"

    def mark_as_sent(self):
        self.status = 'SENT'
        self.sent_at = timezone.now()
        self.save(update_fields=['status', 'sent_at'])

    def mark_as_delivered(self):
        self.status = 'DELIVERED'
        self.delivered_at = timezone.now()
        self.save(update_fields=['status', 'delivered_at'])

    def mark_as_read(self):
        self.status = 'READ'
        self.read_at = timezone.now()
        self.save(update_fields=['status', 'read_at'])

    def mark_as_failed(self, error_message: str):
        self.status = 'FAILED'
        self.error_message = error_message
        self.save(update_fields=['status', 'error_message'])

    def get_delivery_time(self) -> Optional[timedelta]:
        if self.sent_at and self.delivered_at:
            return self.delivered_at - self.sent_at
        return None

    def get_read_time(self) -> Optional[timedelta]:
        if self.delivered_at and self.read_at:
            return self.read_at - self.delivered_at
        return None

class FeedbackType(models.Model):
    """Tipo de feedback."""
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Nombre del tipo de feedback"
    )
    description = models.TextField(
        blank=True,
        help_text="Descripción del tipo de feedback"
    )
    category_choices = [
        ('INTERVIEW', 'Entrevista'),
        ('ASSESSMENT', 'Evaluación'),
        ('PERFORMANCE', 'Rendimiento'),
        ('CULTURE', 'Cultura'),
        ('OTHER', 'Otro')
    ]
    category = models.CharField(
        max_length=20,
        choices=category_choices,
        default='OTHER',
        help_text="Categoría del feedback"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Indica si el tipo de feedback está activo"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Tipo de Feedback"
        verbose_name_plural = "Tipos de Feedback"
        ordering = ['category', 'name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['category']),
            models.Index(fields=['is_active'])
        ]

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"

class Feedback(models.Model):
    """Feedback sobre una persona."""
    person = models.ForeignKey(
        'Person',
        on_delete=models.CASCADE,
        related_name='feedbacks'
    )
    feedback_type = models.ForeignKey(
        FeedbackType,
        on_delete=models.PROTECT,
        related_name='feedbacks'
    )
    evaluator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='given_feedbacks'
    )
    status_choices = [
        ('PENDING', 'Pendiente'),
        ('IN_PROGRESS', 'En Progreso'),
        ('COMPLETED', 'Completado'),
        ('SKIPPED', 'Omitido')
    ]
    status = models.CharField(
        max_length=20,
        choices=status_choices,
        default='PENDING',
        help_text="Estado del feedback"
    )
    result_choices = [
        ('POSITIVE', 'Positivo'),
        ('NEUTRAL', 'Neutral'),
        ('NEGATIVE', 'Negativo'),
        ('NONE', 'Sin Resultado')
    ]
    result = models.CharField(
        max_length=20,
        choices=result_choices,
        default='NONE',
        help_text="Resultado del feedback"
    )
    score = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        help_text="Puntuación del feedback (0-10)"
    )
    strengths = models.TextField(
        blank=True,
        help_text="Puntos fuertes identificados"
    )
    areas_for_improvement = models.TextField(
        blank=True,
        help_text="Áreas de mejora identificadas"
    )
    comments = models.TextField(
        blank=True,
        help_text="Comentarios adicionales"
    )
    metadata = models.JSONField(
        default=dict,
        help_text="Metadatos adicionales"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha y hora de finalización"
    )

    class Meta:
        verbose_name = "Feedback"
        verbose_name_plural = "Feedbacks"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['person']),
            models.Index(fields=['feedback_type']),
            models.Index(fields=['evaluator']),
            models.Index(fields=['status']),
            models.Index(fields=['result']),
            models.Index(fields=['created_at'])
        ]

    def __str__(self):
        return f"Feedback de {self.person} - {self.get_feedback_type_display()}"

    def mark_as_completed(self):
        self.status = 'COMPLETED'
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'completed_at'])

    def skip_feedback(self):
        self.status = 'SKIPPED'
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'completed_at'])

    def get_status_display(self) -> str:
        return dict(self.status_choices).get(self.status, self.status)

    def get_result_display(self) -> str:
        return dict(self.result_choices).get(self.result, self.result)

class Division(models.Model):
    """División o departamento de una empresa."""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children')
    level = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "División"
        verbose_name_plural = "Divisiones"
        ordering = ['level', 'name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['parent']),
            models.Index(fields=['level']),
            models.Index(fields=['is_active'])
        ]

    def __str__(self):
        if self.parent:
            return f"{self.name} ({self.parent.name})"
        return self.name

    def get_ancestors(self) -> List['Division']:
        ancestors = []
        current = self.parent
        while current:
            ancestors.append(current)
            current = current.parent
        return ancestors

    def get_descendants(self) -> List['Division']:
        descendants = []
        for child in self.children.all():
            descendants.append(child)
            descendants.extend(child.get_descendants())
        return descendants

class BusinessUnit(models.Model):
    """Unidad de negocio."""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    division = models.ForeignKey(Division, on_delete=models.PROTECT, related_name='business_units')
    code = models.CharField(max_length=20, unique=True)
    is_active = models.BooleanField(default=True)
    config = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Unidad de Negocio"
        verbose_name_plural = "Unidades de Negocio"
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['code']),
            models.Index(fields=['division']),
            models.Index(fields=['is_active'])
        ]

    def __str__(self):
        return self.name

    def get_ntfy_topic(self) -> str:
        return f"huntred-{self.code.lower()}"

    def get_notification_recipients(self) -> List['Person']:
        from .models import Person
        return Person.objects.filter(
            business_unit=self,
            notification_preferences__isnull=False
        ).distinct()

    def get_email_template_path(self) -> str:
        return f"emails/{self.code.lower()}/"

    @property
    def admin_email(self) -> Optional[str]:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        admin = User.objects.filter(
            business_unit=self,
            role='BU_COMPLETE'
        ).first()
        return admin.email if admin else None

    def save(self, *args, **kwargs):
        if not self.name:
            raise ValidationError("El nombre de la unidad de negocio es obligatorio")
        super().save(*args, **kwargs)

class DocumentType(models.Model):
    """Tipo de documento."""
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Nombre del tipo de documento"
    )
    description = models.TextField(
        blank=True,
        help_text="Descripción del tipo de documento"
    )
    is_required = models.BooleanField(
        default=False,
        help_text="Indica si el documento es obligatorio"
    )
    max_size_mb = models.PositiveIntegerField(
        default=10,
        help_text="Tamaño máximo en MB"
    )
    allowed_extensions = ArrayField(
        models.CharField(max_length=10),
        default=list,
        help_text="Extensiones de archivo permitidas"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Tipo de Documento"
        verbose_name_plural = "Tipos de Documento"
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['is_required'])
        ]

    def __str__(self):
        return self.name

class Document(models.Model):
    """Documento adjunto a una persona."""
    person = models.ForeignKey(
        'Person',
        on_delete=models.CASCADE,
        related_name='documents'
    )
    document_type = models.ForeignKey(
        DocumentType,
        on_delete=models.PROTECT,
        related_name='documents'
    )
    file = models.FileField(
        upload_to='documents/%Y/%m/%d/',
        help_text="Archivo del documento"
    )
    title = models.CharField(
        max_length=200,
        help_text="Título del documento"
    )
    description = models.TextField(
        blank=True,
        help_text="Descripción del documento"
    )
    is_verified = models.BooleanField(
        default=False,
        help_text="Indica si el documento ha sido verificado"
    )
    verification_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha de verificación"
    )
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_documents',
        help_text="Usuario que verificó el documento"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Documento"
        verbose_name_plural = "Documentos"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['person']),
            models.Index(fields=['document_type']),
            models.Index(fields=['is_verified']),
            models.Index(fields=['created_at'])
        ]

    def __str__(self):
        return f"{self.title} - {self.document_type}"

    def clean(self):
        if self.file:
            # Verificar tamaño máximo
            if self.file.size > self.document_type.max_size_mb * 1024 * 1024:
                raise ValidationError(
                    f"El archivo excede el tamaño máximo permitido de {self.document_type.max_size_mb}MB"
                )
            
            # Verificar extensión
            ext = self.file.name.split('.')[-1].lower()
            if ext not in self.document_type.allowed_extensions:
                raise ValidationError(
                    f"Extensión no permitida. Extensiones permitidas: {', '.join(self.document_type.allowed_extensions)}"
                )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def verify(self, user):
        self.is_verified = True
        self.verification_date = timezone.now()
        self.verified_by = user
        self.save(update_fields=['is_verified', 'verification_date', 'verified_by'])

    def get_file_extension(self) -> str:
        return self.file.name.split('.')[-1].lower()

    def get_file_size_mb(self) -> float:
        return round(self.file.size / (1024 * 1024), 2)

class MessageTemplate(models.Model):
    """Plantilla de mensaje."""
    name = models.CharField(max_length=100, unique=True)
    subject = models.CharField(max_length=200)
    body = models.TextField()
    variables = ArrayField(models.CharField(max_length=50), default=list)
    category_choices = [
        ('WELCOME', 'Bienvenida'),
        ('NOTIFICATION', 'Notificación'),
        ('REMINDER', 'Recordatorio'),
        ('ALERT', 'Alerta'),
        ('OTHER', 'Otro')
    ]
    category = models.CharField(max_length=20, choices=category_choices, default='OTHER')
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Plantilla de Mensaje"
        verbose_name_plural = "Plantillas de Mensaje"
        ordering = ['category', 'name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['category']),
            models.Index(fields=['is_active'])
        ]

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"

    def render(self, context: Dict[str, Any]) -> Tuple[str, str]:
        try:
            subject = self.subject.format(**context)
            body = self.body.format(**context)
            return subject, body
        except KeyError as e:
            raise ValidationError(f"Variable no encontrada en el contexto: {e}")

class Message(models.Model):
    """Mensaje enviado a una persona."""
    person = models.ForeignKey('Person', on_delete=models.CASCADE, related_name='messages')
    template = models.ForeignKey(MessageTemplate, on_delete=models.PROTECT, related_name='messages', null=True, blank=True)
    subject = models.CharField(max_length=200)
    body = models.TextField()
    channel_choices = [
        ('EMAIL', 'Correo Electrónico'),
        ('SMS', 'Mensaje de Texto'),
        ('WHATSAPP', 'WhatsApp'),
        ('PUSH', 'Notificación Push'),
        ('OTHER', 'Otro')
    ]
    channel = models.CharField(max_length=20, choices=channel_choices)
    status_choices = [
        ('PENDING', 'Pendiente'),
        ('SENT', 'Enviado'),
        ('DELIVERED', 'Entregado'),
        ('READ', 'Leído'),
        ('FAILED', 'Fallido')
    ]
    status = models.CharField(max_length=20, choices=status_choices, default='PENDING')
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Mensaje"
        verbose_name_plural = "Mensajes"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['person']),
            models.Index(fields=['template']),
            models.Index(fields=['channel']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at'])
        ]

    def __str__(self):
        return f"{self.subject} - {self.get_channel_display()}"

    def mark_as_sent(self):
        self.status = 'SENT'
        self.sent_at = timezone.now()
        self.save(update_fields=['status', 'sent_at'])

    def mark_as_delivered(self):
        self.status = 'DELIVERED'
        self.delivered_at = timezone.now()
        self.save(update_fields=['status', 'delivered_at'])

    def mark_as_read(self):
        self.status = 'READ'
        self.read_at = timezone.now()
        self.save(update_fields=['status', 'read_at'])

    def mark_as_failed(self, error_message: str):
        self.status = 'FAILED'
        self.error_message = error_message
        self.save(update_fields=['status', 'error_message'])

    def get_delivery_time(self) -> Optional[timedelta]:
        if self.sent_at and self.delivered_at:
            return self.delivered_at - self.sent_at
        return None

    def get_read_time(self) -> Optional[timedelta]:
        if self.delivered_at and self.read_at:
            return self.read_at - self.delivered_at
        return None