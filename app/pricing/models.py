from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.cache import cache
from django.conf import settings
from django.core.exceptions import ValidationError

from app.models import User, Proposal
import uuid
import random
import string


class DiscountCoupon(models.Model):
    """
    Modelo para almacenar cupones de descuento con diferentes porcentajes.
    
    Atributos:
        user: Usuario al que se le asigna el cupón
        code: Código único del cupón
        discount_percentage: Porcentaje de descuento (1-100%)
        expiration_date: Fecha de expiración del cupón
        is_used: Indica si el cupón ha sido utilizado
        used_at: Fecha en que se utilizó el cupón (opcional)
        created_at: Fecha de creación del cupón
        proposal: Propuesta asociada al cupón (opcional)
        description: Descripción del cupón (opcional)
        max_uses: Número máximo de usos permitidos (por defecto 1)
        use_count: Número de veces que se ha usado el cupón
    """
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='pricing_discount_coupons',
        help_text="Usuario al que se le asigna el cupón"
    )
    code = models.CharField(
        max_length=20, 
        unique=True,
        help_text="Código único del cupón"
    )
    discount_percentage = models.PositiveIntegerField(
        validators=[
            MinValueValidator(1, message="El descuento mínimo es del 1%"),
            MaxValueValidator(100, message="El descuento máximo es del 100%")
        ],
        help_text="Porcentaje de descuento (1-100%)"
    )
    expiration_date = models.DateTimeField(
        help_text="Fecha de expiración del cupón"
    )
    is_used = models.BooleanField(
        default=False,
        help_text="Indica si el cupón ha sido utilizado"
    )
    used_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="Fecha en que se utilizó el cupón"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Fecha de creación del cupón"
    )
    proposal = models.ForeignKey(
        Proposal,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='discount_coupons',
        help_text="Propuesta asociada al cupón"
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Descripción del cupón"
    )
    max_uses = models.PositiveIntegerField(
        default=1,
        help_text="Número máximo de usos permitidos"
    )
    use_count = models.PositiveIntegerField(
        default=0,
        help_text="Número de veces que se ha usado el cupón"
    )
    
    class Meta:
        verbose_name = "Cupón de Descuento"
        verbose_name_plural = "Cupones de Descuento"
        ordering = ['-created_at', 'expiration_date']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['expiration_date']),
            models.Index(fields=['is_used']),
            models.Index(fields=['user']),
            models.Index(fields=['proposal']),
        ]
    
    def clean(self):
        """Validaciones adicionales del modelo."""
        super().clean()
        
        # Validar que la fecha de expiración sea futura
        if self.expiration_date and self.expiration_date <= timezone.now():
            raise ValidationError({
                'expiration_date': 'La fecha de expiración debe ser futura'
            })
            
        # Validar que el porcentaje esté en el rango permitido
        if not 1 <= self.discount_percentage <= 100:
            raise ValidationError({
                'discount_percentage': 'El porcentaje de descuento debe estar entre 1 y 100'
            })
    
    def save(self, *args, **kwargs):
        """Sobrescritura del método save para incluir validaciones."""
        self.full_clean()
        super().save(*args, **kwargs)
    
    def is_valid(self):
        """
        Verifica si el cupón es válido para su uso.
        
        Returns:
            bool: True si el cupón es válido, False en caso contrario
        """
        return (
            not self.is_used and 
            self.expiration_date > timezone.now() and
            self.use_count < self.max_uses
        )
    
    def mark_as_used(self):
        """
        Marca el cupón como utilizado.
        
        Returns:
            bool: True si se pudo marcar como usado, False si ya estaba usado
        """
        if not self.is_used and self.use_count < self.max_uses:
            self.use_count += 1
            self.is_used = (self.use_count >= self.max_uses)
            self.used_at = timezone.now() if self.is_used else None
            self.save(update_fields=['is_used', 'used_at', 'use_count'])
            return True
        return False
    
    def get_discount_amount(self, amount):
        """
        Calcula el monto del descuento para un monto dado.
        
        Args:
            amount: Monto al que se aplicará el descuento
            
        Returns:
            float: Monto del descuento
        """
        return (amount * self.discount_percentage) / 100
    
    def get_final_amount(self, amount):
        """
        Calcula el monto final después de aplicar el descuento.
        
        Args:
            amount: Monto original
            
        Returns:
            float: Monto final después del descuento
        """
        return max(amount - self.get_discount_amount(amount), 0)
    
    def get_status_display(self):
        """
        Obtiene el estado legible del cupón.
        
        Returns:
            str: Estado del cupón
        """
        if self.is_used or self.use_count >= self.max_uses:
            return "Usado"
        if self.expiration_date <= timezone.now():
            return "Expirado"
        return "Disponible"
    
    def get_time_remaining(self):
        """
        Obtiene el tiempo restante para que expire el cupón.
        
        Returns:
            timedelta: Tiempo restante hasta la expiración
        """
        return self.expiration_date - timezone.now()
    
    @classmethod
    def generate_coupon_code(cls, length=10):
        """
        Genera un código de cupón único.
        
        Args:
            length: Longitud del código (por defecto 10 caracteres)
            
        Returns:
            str: Código de cupón único
        """
        while True:
            # Generar un código aleatorio con letras mayúsculas y dígitos
            code = 'HUNT' + ''.join(
                random.choices(
                    string.ascii_uppercase + string.digits,
                    k=length
                )
            )
            
            # Verificar que el código no exista
            if not cls.objects.filter(code=code).exists():
                return code
    
    @classmethod
    def create_coupon(
        cls,
        user,
        discount_percentage=5,
        validity_hours=4,
        proposal=None,
        description=None,
        max_uses=1
    ):
        """
        Método de conveniencia para crear un nuevo cupón.
        
        Args:
            user: Usuario al que se le asigna el cupón
            discount_percentage: Porcentaje de descuento (1-100%)
            validity_hours: Horas de validez del cupón
            proposal: Propuesta asociada (opcional)
            description: Descripción del cupón (opcional)
            max_uses: Número máximo de usos permitidos
            
        Returns:
            DiscountCoupon: El cupón creado
        """
        expiration_date = timezone.now() + timezone.timedelta(hours=validity_hours)
        
        return cls.objects.create(
            user=user,
            code=cls.generate_coupon_code(),
            discount_percentage=discount_percentage,
            expiration_date=expiration_date,
            proposal=proposal,
            description=description or f"{discount_percentage}% de descuento",
            max_uses=max_uses
        )
    
    def __str__(self):
        return (
            f"Cupón {self.code} - {self.discount_percentage}% - "
            f"{self.get_status_display()} - "
            f"Usos: {self.use_count}/{self.max_uses} - "
            f"Vence: {self.expiration_date.strftime('%Y-%m-%d %H:%M')}"
        )


class TeamEvaluation(models.Model):
    """
    Modelo para gestionar evaluaciones de equipo ofrecidas como promoción.
    """
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('in_progress', 'En Progreso'),
        ('completed', 'Completada'),
        ('expired', 'Expirada'),
        ('canceled', 'Cancelada'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='team_evaluations',
        help_text="Usuario que solicita la evaluación"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Fecha de creación de la evaluación"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Última actualización"
    )
    expires_at = models.DateTimeField(
        help_text="Fecha de expiración de la oferta"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text="Estado actual de la evaluación"
    )
    team_size = models.PositiveIntegerField(
        default=10,
        help_text="Número de miembros del equipo a evaluar"
    )
    discount_percentage = models.PositiveIntegerField(
        default=100,
        validators=[MaxValueValidator(100)],
        help_text="Porcentaje de descuento aplicado"
    )
    coupon = models.OneToOneField(
        DiscountCoupon,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='team_evaluation',
        help_text="Cupón asociado a esta evaluación"
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Datos adicionales de la evaluación"
    )
    
    class Meta:
        verbose_name = "Evaluación de Equipo"
        verbose_name_plural = "Evaluaciones de Equipo"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['user']),
        ]
    
    def clean(self):
        """Validaciones adicionales."""
        super().clean()
        
        if self.expires_at and self.expires_at <= timezone.now():
            raise ValidationError({
                'expires_at': 'La fecha de expiración debe ser futura'
            })
    
    def is_active(self):
        """Verifica si la evaluación está activa."""
        return self.status in ['pending', 'in_progress'] and self.expires_at > timezone.now()
    
    def get_time_remaining(self):
        """Obtiene el tiempo restante para completar la evaluación."""
        return self.expires_at - timezone.now()
    
    def mark_as_completed(self):
        """Marca la evaluación como completada."""
        if self.status in ['pending', 'in_progress']:
            self.status = 'completed'
            self.save(update_fields=['status', 'updated_at'])
            return True
        return False
    
    def cancel(self):
        """Cancela la evaluación."""
        if self.status in ['pending', 'in_progress']:
            self.status = 'canceled'
            self.save(update_fields=['status', 'updated_at'])
            return True
        return False
    
    def __str__(self):
        return f"Evaluación para {self.team_size} miembros - {self.get_status_display()}"


class PromotionBanner(models.Model):
    """
    Modelo para gestionar banners promocionales en la plataforma.
    """
    title = models.CharField(
        max_length=100,
        help_text="Título del banner"
    )
    subtitle = models.CharField(
        max_length=200,
        blank=True,
        help_text="Subtítulo o descripción corta"
    )
    content = models.TextField(
        help_text="Contenido detallado de la promoción (HTML permitido)"
    )
    image = models.ImageField(
        upload_to='promotions/banners/',
        null=True,
        blank=True,
        help_text="Imagen del banner (opcional)"
    )
    start_date = models.DateTimeField(
        help_text="Fecha y hora de inicio de la promoción"
    )
    end_date = models.DateTimeField(
        help_text="Fecha y hora de finalización de la promoción"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Indica si el banner está activo"
    )
    priority = models.PositiveIntegerField(
        default=0,
        help_text="Prioridad de visualización (mayor número = mayor prioridad)"
    )
    target_url = models.URLField(
        blank=True,
        null=True,
        help_text="URL a la que redirigir al hacer clic en el banner"
    )
    button_text = models.CharField(
        max_length=50,
        default="¡Aprovechar Ahora!",
        help_text="Texto del botón de acción"
    )
    badge_text = models.CharField(
        max_length=30,
        blank=True,
        null=True,
        help_text="Texto de la etiqueta (ej: '¡Nuevo!', '¡Oferta!', etc.)"
    )
    badge_style = models.CharField(
        max_length=20,
        default="primary",
        choices=[
            ('primary', 'Primario'),
            ('secondary', 'Secundario'),
            ('success', 'Éxito'),
            ('danger', 'Peligro'),
            ('warning', 'Advertencia'),
            ('info', 'Informativo'),
            ('light', 'Claro'),
            ('dark', 'Oscuro'),
        ],
        help_text="Estilo de la etiqueta"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Banner Promocional"
        verbose_name_plural = "Banners Promocionales"
        ordering = ['-priority', '-start_date']
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['start_date', 'end_date']),
        ]
    
    def __str__(self):
        return self.title
    
    def is_currently_active(self):
        """Verifica si el banner debe mostrarse actualmente."""
        now = timezone.now()
        return (
            self.is_active and
            self.start_date <= now <= self.end_date
        )
    
    def days_remaining(self):
        """Devuelve los días restantes para que termine la promoción."""
        if not self.is_currently_active():
            return 0
        delta = self.end_date - timezone.now()
        return max(delta.days, 0)
    
    def hours_remaining(self):
        """Devuelve las horas restantes para que termine la promoción."""
        if not self.is_currently_active():
            return 0
        delta = self.end_date - timezone.now()
        return max(int(delta.total_seconds() // 3600), 0)
    
    def get_badge_style_class(self):
        """Devuelve la clase CSS correspondiente al estilo de la etiqueta."""
        return f"badge bg-{self.badge_style}"
    
    def get_countdown_data(self):
        """
        Devuelve los datos para el contador regresivo.
        
        Returns:
            dict: Datos para inicializar el contador
        """
        if not self.is_currently_active():
            return None
            
        return {
            'end_date': self.end_date.isoformat(),
            'days_remaining': self.days_remaining(),
            'hours_remaining': self.hours_remaining() % 24,
            'minutes_remaining': int((self.end_date - timezone.now()).total_seconds() // 60) % 60,
            'seconds_remaining': int((self.end_date - timezone.now()).total_seconds() % 60)
        }