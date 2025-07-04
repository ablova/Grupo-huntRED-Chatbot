"""
Company Model - Sistema huntRED® v2
Modelo completo para empresas con roles específicos y configuraciones avanzadas.
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator, URLValidator
from django.utils import timezone
from typing import Dict, Any, List
import uuid


class Company(models.Model):
    """
    Modelo principal para empresas en el sistema huntRED®.
    Incluye configuraciones avanzadas y roles específicos.
    """
    
    # === IDENTIFICACIÓN ===
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True, db_index=True,
                          help_text="Nombre de la empresa")
    legal_name = models.CharField(max_length=255, blank=True, null=True,
                                help_text="Razón social de la empresa")
    tax_id = models.CharField(max_length=50, blank=True, null=True, unique=True,
                            help_text="RFC o identificación fiscal")
    
    # === INFORMACIÓN GENERAL ===
    industry = models.CharField(max_length=100, blank=True, null=True,
                              help_text="Industria")
    
    SIZE_CHOICES = [
        ('startup', 'Startup (1-10)'),
        ('small', 'Pequeña (11-50)'),
        ('medium', 'Mediana (51-200)'),
        ('large', 'Grande (201-1000)'),
        ('enterprise', 'Corporativo (1000+)'),
    ]
    size = models.CharField(max_length=20, choices=SIZE_CHOICES, blank=True, null=True,
                          help_text="Tamaño de la empresa")
    
    employee_count = models.PositiveIntegerField(blank=True, null=True,
                                               help_text="Número exacto de empleados")
    
    # === UBICACIÓN ===
    location = models.CharField(max_length=100, blank=True, null=True,
                              help_text="Ubicación principal")
    headquarters = models.CharField(max_length=200, blank=True, null=True,
                                  help_text="Sede central")
    additional_locations = models.JSONField(default=list, blank=True,
                                          help_text="Ubicaciones adicionales")
    
    # === CONTACTO ===
    website = models.URLField(max_length=200, blank=True, null=True,
                            validators=[URLValidator()],
                            help_text="Sitio web corporativo")
    main_phone = models.CharField(max_length=20, blank=True, null=True,
                                help_text="Teléfono principal")
    main_email = models.EmailField(blank=True, null=True,
                                 help_text="Email principal")
    
    # === DESCRIPCIÓN Y CULTURA ===
    description = models.TextField(blank=True, null=True,
                                 help_text="Descripción general de la empresa")
    mission = models.TextField(blank=True, null=True,
                             help_text="Misión de la empresa")
    vision = models.TextField(blank=True, null=True,
                            help_text="Visión de la empresa")
    values = models.JSONField(default=list, blank=True,
                            help_text="Valores corporativos")
    culture_description = models.TextField(blank=True, null=True,
                                         help_text="Descripción de la cultura empresarial")
    
    # === ROLES DE CONTACTO ===
    signer = models.ForeignKey('Person', on_delete=models.SET_NULL, null=True, blank=True,
                             related_name='signed_companies',
                             help_text="Persona que firma contratos")
    payment_responsible = models.ForeignKey('Person', on_delete=models.SET_NULL, null=True, blank=True,
                                          related_name='payment_companies',
                                          help_text="Responsable de pagos")
    fiscal_responsible = models.ForeignKey('Person', on_delete=models.SET_NULL, null=True, blank=True,
                                         related_name='fiscal_companies',
                                         help_text="Responsable fiscal")
    process_responsible = models.ForeignKey('Person', on_delete=models.SET_NULL, null=True, blank=True,
                                          related_name='process_companies',
                                          help_text="Responsable del proceso de reclutamiento")
    hr_manager = models.ForeignKey('Person', on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='hr_managed_companies',
                                 help_text="Gerente de Recursos Humanos")
    ceo = models.ForeignKey('Person', on_delete=models.SET_NULL, null=True, blank=True,
                          related_name='ceo_companies',
                          help_text="CEO o Director General")
    
    # === INVITADOS A REPORTES ===
    report_invitees = models.ManyToManyField('Person', blank=True,
                                           related_name='report_companies',
                                           help_text="Personas invitadas a reportes (Dir RH, CFO, etc)")
    
    # === CONFIGURACIÓN DE RECLUTAMIENTO ===
    recruitment_config = models.JSONField(default=dict, blank=True, help_text="""
    Configuración de procesos de reclutamiento:
    {
        'preferred_channels': ['linkedin', 'indeed', 'internal'],
        'hiring_process_stages': ['screening', 'interview1', 'technical', 'final'],
        'approval_levels': {
            'junior': 'hr_manager',
            'senior': 'department_head',
            'executive': 'ceo'
        },
        'background_check_required': true,
        'reference_check_required': true,
        'skills_assessment_required': false,
        'culture_fit_assessment': true,
        'probation_period_days': 90,
        'notice_period_days': 30
    }
    """)
    
    # === CONFIGURACIÓN DE COMUNICACIÓN ===
    communication_config = models.JSONField(default=dict, blank=True, help_text="""
    Configuración de comunicación:
    {
        'preferred_channels': ['email', 'whatsapp', 'teams'],
        'business_hours': {
            'start': '09:00',
            'end': '18:00',
            'timezone': 'America/Mexico_City'
        },
        'response_time_sla': {
            'urgent': 2,  // hours
            'normal': 24, // hours
            'low': 72     // hours
        },
        'escalation_rules': {
            'no_response_hours': 48,
            'escalate_to': 'process_responsible'
        }
    }
    """)
    
    # === PREFERENCIAS DE NOTIFICACIÓN ===
    notification_preferences = models.JSONField(default=dict, blank=True, help_text="""
    Preferencias de notificación por tipo de evento y canal:
    {
        'new_candidate': {
            'channels': ['email', 'whatsapp'],
            'recipients': ['hr_manager', 'process_responsible']
        },
        'interview_scheduled': {
            'channels': ['email', 'calendar'],
            'recipients': ['interviewer', 'candidate']
        },
        'offer_sent': {
            'channels': ['email'],
            'recipients': ['hr_manager', 'hiring_manager']
        },
        'contract_signed': {
            'channels': ['email', 'whatsapp'],
            'recipients': ['hr_manager', 'fiscal_responsible']
        }
    }
    """)
    
    # === CONFIGURACIÓN FINANCIERA ===
    financial_config = models.JSONField(default=dict, blank=True, help_text="""
    Configuración financiera y de facturación:
    {
        'billing_address': {
            'street': '',
            'city': '',
            'state': '',
            'postal_code': '',
            'country': 'Mexico'
        },
        'payment_terms': 'net30',
        'preferred_payment_method': 'bank_transfer',
        'currency': 'MXN',
        'tax_rate': 16.0,
        'credit_limit': 0,
        'payment_history': []
    }
    """)
    
    # === CONFIGURACIÓN DE SERVICIOS ===
    services_config = models.JSONField(default=dict, blank=True, help_text="""
    Configuración de servicios contratados:
    {
        'active_services': ['recruitment', 'talent_analysis'],
        'service_levels': {
            'recruitment': 'premium',
            'talent_analysis': 'standard'
        },
        'custom_requirements': {
            'industry_specific': true,
            'confidentiality_level': 'high',
            'reporting_frequency': 'weekly'
        }
    }
    """)
    
    # === MÉTRICAS Y KPIs ===
    metrics = models.JSONField(default=dict, blank=True, help_text="""
    Métricas y KPIs de la empresa:
    {
        'time_to_hire': 0,
        'cost_per_hire': 0,
        'quality_of_hire': 0,
        'retention_rate': 0,
        'satisfaction_score': 0,
        'referral_rate': 0
    }
    """)
    
    # === ESTADO Y CONFIGURACIÓN ===
    STATUS_CHOICES = [
        ('active', 'Activo'),
        ('inactive', 'Inactivo'),
        ('prospect', 'Prospecto'),
        ('suspended', 'Suspendido'),
        ('archived', 'Archivado'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='prospect',
                            db_index=True, help_text="Estado de la empresa")
    
    TIER_CHOICES = [
        ('basic', 'Básico'),
        ('standard', 'Estándar'),
        ('premium', 'Premium'),
        ('enterprise', 'Empresarial'),
    ]
    tier = models.CharField(max_length=20, choices=TIER_CHOICES, default='basic',
                          help_text="Nivel de servicio")
    
    is_client = models.BooleanField(default=False, db_index=True,
                                  help_text="¿Es cliente activo?")
    is_partner = models.BooleanField(default=False,
                                   help_text="¿Es socio estratégico?")
    is_confidential = models.BooleanField(default=False,
                                        help_text="¿Requiere confidencialidad especial?")
    
    # === RELACIONES COMERCIALES ===
    business_unit = models.ForeignKey('BusinessUnit', on_delete=models.SET_NULL,
                                    null=True, blank=True, related_name='companies',
                                    help_text="Unidad de negocio asignada")
    account_manager = models.ForeignKey(User, on_delete=models.SET_NULL,
                                      null=True, blank=True,
                                      related_name='managed_companies',
                                      help_text="Gestor de cuenta asignado")
    parent_company = models.ForeignKey('self', on_delete=models.SET_NULL,
                                     null=True, blank=True,
                                     related_name='subsidiaries',
                                     help_text="Empresa matriz")
    
    # === EVALUACIÓN Y SCORING ===
    credit_score = models.PositiveSmallIntegerField(default=50,
                                                  validators=[MinValueValidator(0), MaxValueValidator(100)],
                                                  help_text="Score crediticio (0-100)")
    risk_level = models.CharField(max_length=20, 
                                choices=[('low', 'Bajo'), ('medium', 'Medio'), ('high', 'Alto')],
                                default='medium', help_text="Nivel de riesgo")
    satisfaction_score = models.FloatField(default=0.0,
                                         validators=[MinValueValidator(0), MaxValueValidator(10)],
                                         help_text="Score de satisfacción (0-10)")
    
    # === TIMESTAMPS ===
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)
    last_interaction = models.DateTimeField(null=True, blank=True,
                                          help_text="Última interacción con la empresa")
    
    class Meta:
        verbose_name = "Empresa"
        verbose_name_plural = "Empresas"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['name', 'status']),
            models.Index(fields=['industry', 'size']),
            models.Index(fields=['is_client', 'status']),
            models.Index(fields=['business_unit', 'tier']),
            models.Index(fields=['account_manager', 'last_interaction']),
        ]
    
    def __str__(self):
        return self.name
    
    @property
    def is_active_client(self):
        """Verifica si es un cliente activo."""
        return self.is_client and self.status == 'active'
    
    @property
    def primary_contact(self):
        """Retorna el contacto principal (process_responsible o hr_manager)."""
        return self.process_responsible or self.hr_manager
    
    def get_notification_recipients(self, event_type: str) -> List['Person']:
        """Obtiene los destinatarios de notificaciones para un tipo de evento."""
        recipients = []
        if event_type in self.notification_preferences:
            config = self.notification_preferences[event_type]
            recipient_roles = config.get('recipients', [])
            
            for role in recipient_roles:
                person = getattr(self, role, None)
                if person:
                    recipients.append(person)
        
        return recipients
    
    def get_notification_channels(self, event_type: str) -> List[str]:
        """Obtiene los canales de notificación para un tipo de evento."""
        if event_type in self.notification_preferences:
            return self.notification_preferences[event_type].get('channels', ['email'])
        return ['email']
    
    def update_last_interaction(self):
        """Actualiza la fecha de última interacción."""
        self.last_interaction = timezone.now()
        self.save(update_fields=['last_interaction'])
    
    def get_hiring_approval_person(self, position_level: str) -> 'Person':
        """Obtiene la persona que debe aprobar una contratación según el nivel."""
        approval_config = self.recruitment_config.get('approval_levels', {})
        approver_role = approval_config.get(position_level, 'hr_manager')
        return getattr(self, approver_role, None)
    
    def calculate_metrics(self) -> Dict[str, float]:
        """Calcula métricas actuales de la empresa."""
        # Implementar cálculo de métricas basado en datos históricos
        return {
            'time_to_hire': self._calculate_time_to_hire(),
            'cost_per_hire': self._calculate_cost_per_hire(),
            'quality_of_hire': self._calculate_quality_of_hire(),
            'retention_rate': self._calculate_retention_rate(),
            'satisfaction_score': float(self.satisfaction_score),
            'referral_rate': self._calculate_referral_rate()
        }
    
    def _calculate_time_to_hire(self) -> float:
        """Calcula el tiempo promedio de contratación."""
        # Implementar lógica basada en ofertas cerradas
        return 0.0
    
    def _calculate_cost_per_hire(self) -> float:
        """Calcula el costo promedio por contratación."""
        # Implementar lógica basada en servicios facturados
        return 0.0
    
    def _calculate_quality_of_hire(self) -> float:
        """Calcula la calidad promedio de contrataciones."""
        # Implementar lógica basada en evaluaciones de desempeño
        return 0.0
    
    def _calculate_retention_rate(self) -> float:
        """Calcula la tasa de retención."""
        # Implementar lógica basada en seguimiento post-contratación
        return 0.0
    
    def _calculate_referral_rate(self) -> float:
        """Calcula la tasa de referidos."""
        # Implementar lógica basada en referencias generadas
        return 0.0
    
    def validate_tier_capabilities(self):
        """Valida que las capacidades solicitadas estén disponibles en el tier."""
        tier_capabilities = {
            'basic': ['recruitment'],
            'standard': ['recruitment', 'talent_analysis'],
            'premium': ['recruitment', 'talent_analysis', 'executive_search', 'consulting'],
            'enterprise': ['recruitment', 'talent_analysis', 'executive_search', 'consulting', 'custom']
        }
        
        active_services = self.services_config.get('active_services', [])
        allowed_services = tier_capabilities.get(self.tier, [])
        
        invalid_services = [service for service in active_services if service not in allowed_services]
        if invalid_services:
            raise ValidationError(f"Los servicios {invalid_services} no están disponibles en el tier {self.tier}")
    
    def save(self, *args, **kwargs):
        """Override save para validaciones personalizadas."""
        self.validate_tier_capabilities()
        super().save(*args, **kwargs)