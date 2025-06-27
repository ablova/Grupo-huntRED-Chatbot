"""
Modelos para seguimiento de servicios externos de huntRED®.
"""
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid

from app.models import BusinessUnit, Person, Service


class ExternalServiceType(models.Model):
    """Tipos de servicios externos de huntRED®."""
    
    SERVICE_CATEGORIES = [
        ('recruitment', 'Reclutamiento'),
        ('headhunting', 'Headhunting'),
        ('assessment', 'Evaluación'),
        ('consulting', 'Consultoría'),
        ('training', 'Capacitación'),
        ('outplacement', 'Outplacement'),
        ('hr_audit', 'Auditoría RH'),
        ('compensation', 'Compensaciones'),
        ('organizational', 'Organizacional'),
        ('other', 'Otro'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, help_text="Nombre del tipo de servicio")
    category = models.CharField(max_length=20, choices=SERVICE_CATEGORIES)
    description = models.TextField(help_text="Descripción del servicio")
    
    # Configuración de precios
    base_price = models.DecimalField(
        max_digits=15, decimal_places=2, 
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Precio base del servicio"
    )
    price_type = models.CharField(
        max_length=20,
        choices=[
            ('fixed', 'Precio Fijo'),
            ('hourly', 'Por Hora'),
            ('percentage', 'Porcentaje'),
            ('commission', 'Comisión'),
            ('custom', 'Personalizado'),
        ],
        default='fixed'
    )
    
    # Configuración de facturación
    billing_frequency = models.CharField(
        max_length=20,
        choices=[
            ('one_time', 'Una Vez'),
            ('monthly', 'Mensual'),
            ('quarterly', 'Trimestral'),
            ('project', 'Por Proyecto'),
            ('milestone', 'Por Hito'),
        ],
        default='one_time'
    )
    
    # Estado
    is_active = models.BooleanField(default=True)
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'pricing_external_service_type'
        verbose_name = 'Tipo de Servicio Externo'
        verbose_name_plural = 'Tipos de Servicios Externos'
    
    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"


class ExternalService(models.Model):
    """Servicio externo de huntRED® con seguimiento completo."""
    
    STATUS_CHOICES = [
        ('prospecting', 'Prospección'),
        ('negotiation', 'Negociación'),
        ('active', 'Activo'),
        ('in_progress', 'En Progreso'),
        ('on_hold', 'En Pausa'),
        ('completed', 'Completado'),
        ('cancelled', 'Cancelado'),
        ('lost', 'Perdido'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Baja'),
        ('medium', 'Media'),
        ('high', 'Alta'),
        ('urgent', 'Urgente'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service_id = models.CharField(max_length=50, unique=True, help_text="ID único del servicio")
    
    # Información básica
    title = models.CharField(max_length=200, help_text="Título del servicio")
    description = models.TextField(help_text="Descripción detallada del servicio")
    service_type = models.ForeignKey(ExternalServiceType, on_delete=models.CASCADE)
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE)
    
    # Cliente y responsable
    client = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='external_services_client')
    responsible = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='external_services_responsible')
    assigned_team = models.ManyToManyField(Person, related_name='external_services_team', blank=True)
    
    # Estado y prioridad
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='prospecting')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    
    # Fechas
    start_date = models.DateTimeField(help_text="Fecha de inicio del servicio")
    end_date = models.DateTimeField(null=True, blank=True, help_text="Fecha de fin estimada")
    actual_end_date = models.DateTimeField(null=True, blank=True, help_text="Fecha de fin real")
    
    # Información financiera
    estimated_amount = models.DecimalField(
        max_digits=15, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Monto estimado del servicio"
    )
    actual_amount = models.DecimalField(
        max_digits=15, decimal_places=2,
        default=Decimal('0.00'),
        help_text="Monto real del servicio"
    )
    currency = models.CharField(max_length=3, default='MXN')
    
    # Configuración de facturación
    billing_structure = models.CharField(
        max_length=20,
        choices=[
            ('upfront', 'Anticipado'),
            ('milestone', 'Por Hitos'),
            ('monthly', 'Mensual'),
            ('upon_completion', 'Al Completar'),
            ('custom', 'Personalizado'),
        ],
        default='upon_completion'
    )
    
    # Requisitos y entregables
    requirements = models.JSONField(default=list, help_text="Lista de requisitos del servicio")
    deliverables = models.JSONField(default=list, help_text="Lista de entregables")
    
    # Seguimiento
    progress_percentage = models.DecimalField(
        max_digits=5, decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00')), MinValueValidator(Decimal('100.00'))],
        help_text="Porcentaje de progreso (0-100)"
    )
    
    # Notas y comentarios
    notes = models.TextField(blank=True, help_text="Notas internas")
    client_notes = models.TextField(blank=True, help_text="Notas del cliente")
    
    # Control
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(Person, on_delete=models.SET_NULL, null=True, blank=True, related_name='external_services_created')
    
    class Meta:
        db_table = 'pricing_external_service'
        verbose_name = 'Servicio Externo'
        verbose_name_plural = 'Servicios Externos'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.service_id} - {self.title}"
    
    def save(self, *args, **kwargs):
        if not self.service_id:
            self.service_id = f"EXT-{timezone.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"
        super().save(*args, **kwargs)
    
    def get_total_billed(self):
        """Obtiene el total facturado."""
        return self.invoices.filter(status='paid').aggregate(
            total=models.Sum('total_amount')
        )['total'] or Decimal('0.00')
    
    def get_pending_amount(self):
        """Obtiene el monto pendiente."""
        return self.actual_amount - self.get_total_billed()
    
    def update_progress(self, percentage: Decimal):
        """Actualiza el progreso del servicio."""
        self.progress_percentage = min(percentage, Decimal('100.00'))
        if percentage >= Decimal('100.00'):
            self.status = 'completed'
            self.actual_end_date = timezone.now()
        self.save()
    
    def add_milestone(self, title: str, description: str, due_date: timezone.datetime, amount: Decimal = None):
        """Agrega un hito al servicio."""
        return ExternalServiceMilestone.objects.create(
            service=self,
            title=title,
            description=description,
            due_date=due_date,
            amount=amount
        )


class ExternalServiceMilestone(models.Model):
    """Hitos de un servicio externo."""
    
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('in_progress', 'En Progreso'),
        ('completed', 'Completado'),
        ('delayed', 'Retrasado'),
        ('cancelled', 'Cancelado'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service = models.ForeignKey(ExternalService, on_delete=models.CASCADE, related_name='milestones')
    
    # Información del hito
    title = models.CharField(max_length=200, help_text="Título del hito")
    description = models.TextField(help_text="Descripción del hito")
    milestone_number = models.IntegerField(help_text="Número secuencial del hito")
    
    # Estado
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Fechas
    due_date = models.DateTimeField(help_text="Fecha límite del hito")
    completed_date = models.DateTimeField(null=True, blank=True, help_text="Fecha de completado")
    
    # Monto
    amount = models.DecimalField(
        max_digits=15, decimal_places=2,
        null=True, blank=True,
        help_text="Monto asociado al hito"
    )
    
    # Control
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'pricing_external_service_milestone'
        verbose_name = 'Hito de Servicio Externo'
        verbose_name_plural = 'Hitos de Servicios Externos'
        ordering = ['milestone_number']
        unique_together = ['service', 'milestone_number']
    
    def __str__(self):
        return f"{self.service.service_id} - Hito {self.milestone_number}: {self.title}"
    
    def save(self, *args, **kwargs):
        if not self.milestone_number:
            # Asignar número secuencial
            last_milestone = ExternalServiceMilestone.objects.filter(
                service=self.service
            ).order_by('-milestone_number').first()
            self.milestone_number = (last_milestone.milestone_number + 1) if last_milestone else 1
        super().save(*args, **kwargs)
    
    def complete_milestone(self):
        """Marca el hito como completado."""
        self.status = 'completed'
        self.completed_date = timezone.now()
        self.save()
        
        # Actualizar progreso del servicio
        total_milestones = self.service.milestones.count()
        completed_milestones = self.service.milestones.filter(status='completed').count()
        progress_percentage = (completed_milestones / total_milestones) * 100
        self.service.update_progress(progress_percentage)


class ExternalServiceInvoice(models.Model):
    """Facturas de servicios externos."""
    
    STATUS_CHOICES = [
        ('draft', 'Borrador'),
        ('sent', 'Enviada'),
        ('paid', 'Pagada'),
        ('overdue', 'Vencida'),
        ('cancelled', 'Cancelada'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice_number = models.CharField(max_length=50, unique=True, help_text="Número de factura")
    service = models.ForeignKey(ExternalService, on_delete=models.CASCADE, related_name='invoices')
    
    # Información de facturación
    issue_date = models.DateTimeField(default=timezone.now, help_text="Fecha de emisión")
    due_date = models.DateTimeField(help_text="Fecha de vencimiento")
    paid_date = models.DateTimeField(null=True, blank=True, help_text="Fecha de pago")
    
    # Montos
    subtotal = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    tax_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    currency = models.CharField(max_length=3, default='MXN')
    
    # Estado
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Descripción
    description = models.TextField(help_text="Descripción de la factura")
    notes = models.TextField(blank=True, help_text="Notas adicionales")
    
    # Control
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(Person, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        db_table = 'pricing_external_service_invoice'
        verbose_name = 'Factura de Servicio Externo'
        verbose_name_plural = 'Facturas de Servicios Externos'
        ordering = ['-issue_date']
    
    def __str__(self):
        return f"{self.invoice_number} - {self.service.title}"
    
    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = f"EXT-INV-{timezone.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"
        super().save(*args, **kwargs)
    
    def mark_as_paid(self):
        """Marca la factura como pagada."""
        self.status = 'paid'
        self.paid_date = timezone.now()
        self.save()
    
    def is_overdue(self):
        """Verifica si la factura está vencida."""
        return self.status not in ['paid', 'cancelled'] and timezone.now() > self.due_date


class ExternalServiceActivity(models.Model):
    """Actividades y seguimiento de servicios externos."""
    
    ACTIVITY_TYPES = [
        ('call', 'Llamada'),
        ('meeting', 'Reunión'),
        ('email', 'Email'),
        ('proposal', 'Propuesta'),
        ('negotiation', 'Negociación'),
        ('delivery', 'Entrega'),
        ('follow_up', 'Seguimiento'),
        ('issue', 'Problema'),
        ('milestone', 'Hito'),
        ('other', 'Otro'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service = models.ForeignKey(ExternalService, on_delete=models.CASCADE, related_name='activities')
    
    # Información de la actividad
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    title = models.CharField(max_length=200, help_text="Título de la actividad")
    description = models.TextField(help_text="Descripción detallada")
    
    # Fechas
    activity_date = models.DateTimeField(default=timezone.now, help_text="Fecha de la actividad")
    duration_minutes = models.IntegerField(null=True, blank=True, help_text="Duración en minutos")
    
    # Participantes
    participants = models.ManyToManyField(Person, related_name='external_service_activities')
    
    # Resultados
    outcome = models.TextField(blank=True, help_text="Resultado de la actividad")
    next_actions = models.TextField(blank=True, help_text="Próximas acciones")
    
    # Control
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='external_service_activities_created')
    
    class Meta:
        db_table = 'pricing_external_service_activity'
        verbose_name = 'Actividad de Servicio Externo'
        verbose_name_plural = 'Actividades de Servicios Externos'
        ordering = ['-activity_date']
    
    def __str__(self):
        return f"{self.service.service_id} - {self.get_activity_type_display()}: {self.title}" 