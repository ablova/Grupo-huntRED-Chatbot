# app/ats/client_portal/models.py
from django.db import models
from django.conf import settings
from app.models import Company
from django.utils import timezone
from app.ats.utils.notification_service import NotificationService

class PortalAddon(models.Model):
    """Modelo para addons del portal del cliente."""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=32, unique=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    features = models.JSONField()  # Lista de características específicas
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Addon del Portal"
        verbose_name_plural = "Addons del Portal"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - ${self.price}"

class ClientPortalAccess(models.Model):
    """Modelo para acceso al portal del cliente."""
    TIER_CHOICES = [
        ('basic', 'Básico'),
        ('premium', 'Premium'),
        ('enterprise', 'Enterprise')
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    tier = models.CharField(max_length=20, choices=TIER_CHOICES, default='basic')
    addons = models.ManyToManyField(PortalAddon, blank=True)
    is_active = models.BooleanField(default=True)
    last_access = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Acceso al Portal"
        verbose_name_plural = "Accesos al Portal"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.get_tier_display()}"

    def get_available_features(self):
        """Obtiene las características disponibles según el tier y addons."""
        base_features = {
            'basic': [
                'view_active_vacancies',
                'view_documents',
                'basic_metrics'
            ],
            'premium': [
                'view_active_vacancies',
                'view_documents',
                'advanced_metrics',
                'market_benchmarks',
                'candidate_tracking',
                'feedback_system'
            ],
            'enterprise': [
                'view_active_vacancies',
                'view_documents',
                'advanced_metrics',
                'market_benchmarks',
                'candidate_tracking',
                'feedback_system',
                'custom_reports',
                'api_access',
                'priority_support'
            ]
        }

        features = set(base_features[self.tier])
        
        # Agregar características de addons
        for addon in self.addons.all():
            features.update(addon.features)
        
        return list(features)

    def has_feature(self, feature_code):
        """Verifica si el acceso tiene una característica específica."""
        return feature_code in self.get_available_features()

    def get_tier_display(self):
        """Obtiene el nombre legible del tier."""
        return dict(self.TIER_CHOICES).get(self.tier, 'Desconocido')

class AddonRequest(models.Model):
    """Modelo para solicitudes de addons del portal."""
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('approved', 'Aprobado'),
        ('rejected', 'Rechazado'),
        ('cancelled', 'Cancelado')
    ]
    
    portal_access = models.ForeignKey(
        ClientPortalAccess,
        on_delete=models.CASCADE,
        related_name='addon_requests'
    )
    addon = models.ForeignKey(
        PortalAddon,
        on_delete=models.CASCADE,
        related_name='requests'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='addon_requests'
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_addon_requests'
    )
    request_date = models.DateTimeField(auto_now_add=True)
    approval_date = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Solicitud de Addon"
        verbose_name_plural = "Solicitudes de Addons"
        ordering = ['-request_date']
    
    def __str__(self):
        return f"{self.addon.name} - {self.get_status_display()}"
    
    def approve(self, approved_by, notes=''):
        """Aprueba la solicitud de addon."""
        self.status = 'approved'
        self.approved_by = approved_by
        self.approval_date = timezone.now()
        self.notes = notes
        self.save()
        
        # Agregar addon al acceso del portal
        self.portal_access.addons.add(self.addon)
        
        # Notificar al usuario
        notification_service = NotificationService()
        notification_service.notify_addon_approved(self)
    
    def reject(self, approved_by, notes=''):
        """Rechaza la solicitud de addon."""
        self.status = 'rejected'
        self.approved_by = approved_by
        self.approval_date = timezone.now()
        self.notes = notes
        self.save()
        
        # Notificar al usuario
        notification_service = NotificationService()
        notification_service.notify_addon_rejected(self)
    
    def cancel(self):
        """Cancela la solicitud de addon."""
        self.status = 'cancelled'
        self.save()
        
        # Notificar al usuario
        notification_service = NotificationService()
        notification_service.notify_addon_cancelled(self) 