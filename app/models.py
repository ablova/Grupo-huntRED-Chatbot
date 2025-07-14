# app/models.py
    
import os
import logging
from typing import Dict, Any, List, Optional
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.contrib.postgres.fields import ArrayField
from django.db.models import JSONField
from django.utils import timezone
from django.utils.functional import cached_property
from enum import Enum

# Importar modelos culturales
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models.signals import post_save
from django.dispatch import receiver
from urllib.parse import urlparse
from asgiref.sync import sync_to_async
from django.contrib.auth.models import AbstractUser, BaseUserManager, User
from django.utils.translation import gettext_lazy as _
from datetime import datetime, timedelta, date
from functools import lru_cache

# Importar el modelo CustomUser centralizado
from app.ats.accounts.models import CustomUser

# Import NotificationService
# Notification service is now imported lazily in methods to avoid circular imports

logger = logging.getLogger(__name__)
from typing import Dict, List, Optional, Union, Any, Tuple
from django.urls import reverse
from django.core.cache import cache
import json
import re
import uuid
import logging
import requests

from django.utils import timezone as now
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

# Permisos
PERMISSION_CHOICES=[('ALL_ACCESS','Acceso Total'),('BU_ACCESS','Acceso a BU'),('DIVISION_ACCESS','Acceso a División'),('VIEW_REPORTS','Ver Reportes'),('MANAGE_USERS','Gestionar Usuarios'),('EDIT_CONTENT','Editar Contenido')]
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
    ('SERVICIOS FINANCIEROS','Servicios Financieros / Banca / Seguros'),
    ('LEGAL','Legal'),
    ('HEALTHCARE','HealthCare / Farma'),
    ('ENERGIA','Energía / Oil & Gas'),
    ('FINANZAS','Finanzas & Contabilidad'),
    ('VENTAS','Ventas & Mercadotecnia'),
    ('MANUFACTURA','Manufactura e Industria / Procurement'),
    ('TECNOLOGIA','Tecnología'),
    ('SUSTENTABILIDAD','Sustentabilidad'),
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
    """Modelo principal de Unidad de Negocio que centraliza toda la funcionalidad relacionada."""
    
    # Identificación y Estado
    name = models.CharField(
        max_length=50,
        choices=BUSINESS_UNIT_CHOICES,
        unique=True,
        db_index=True,
        help_text="Nombre de la unidad de negocio"
    )
    code = models.CharField(
        max_length=10,
        unique=True,
        db_index=True,
        help_text="Código único de la unidad de negocio"
    )
    description = models.TextField(
        blank=True,
        help_text="Descripción detallada de la unidad de negocio"
    )
    active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Indica si la unidad de negocio está activa"
    )
    
    # Configuración General
    business_settings = models.JSONField(
        default=dict,
        help_text="""Configuración general de la unidad de negocio:
        {
            'general': {
                'timezone': 'America/Mexico_City',
                'language': 'es',
                'currency': 'MXN',
                'date_format': 'DD/MM/YYYY',
                'time_format': '24h'
            },
            'notifications': {
                'email_enabled': true,
                'sms_enabled': true,
                'push_enabled': true,
                'notification_channels': ['email', 'sms', 'push'],
                'notification_templates': {
                    'welcome': 'template_id',
                    'reminder': 'template_id'
                }
            },
            'security': {
                'password_policy': {
                    'min_length': 8,
                    'require_special_chars': true,
                    'require_numbers': true,
                    'require_uppercase': true
                },
                'session_timeout': 30,
                'max_login_attempts': 5,
                '2fa_required': false
            },
            'branding': {
                'logo_url': 'url',
                'primary_color': '#000000',
                'secondary_color': '#FFFFFF',
                'font_family': 'Arial',
                'custom_css': 'css_string'
            }
        }"""
    )
    
    # Integraciones
    integrations = models.JSONField(
        default=dict,
        help_text="""Configuración de integraciones:
        {
            'whatsapp': {
                'enabled': true,
                'api_key': 'key',
                'phone_number': 'number',
                'templates': {
                    'welcome': 'template_id',
                    'reminder': 'template_id'
                }
            },
            'telegram': {
                'enabled': true,
                'bot_token': 'token',
                'channel_id': 'id',
                'commands': {
                    'start': 'command_id',
                    'help': 'command_id'
                }
            },
            'messenger': {
                'enabled': true,
                'page_id': 'id',
                'access_token': 'token',
                'greeting_text': 'text'
            },
            'instagram': {
                'enabled': true,
                'account_id': 'id',
                'access_token': 'token'
            },
            'wordpress': {
                'enabled': true,
                'base_url': 'url',
                'auth_token': 'token',
                'endpoints': {
                    'posts': 'endpoint',
                    'pages': 'endpoint'
                }
            },
            'linkedin': {
                'enabled': true,
                'client_id': 'id',
                'client_secret': 'secret',
                'access_token': 'token'
            },
            'indeed': {
                'enabled': true,
                'publisher_id': 'id',
                'api_key': 'key'
            },
            'glassdoor': {
                'enabled': true,
                'partner_id': 'id',
                'api_key': 'key'
            }
        }"""
    )
    
    # Pricing y Servicios
    pricing_config = models.JSONField(
        default=dict,
        help_text="""Configuración de precios y servicios:
        {
            'services': {
                'recruitment': {
                    'base_price': 1000,
                    'currency': 'MXN',
                    'payment_terms': 'net30',
                    'features': ['feature1', 'feature2'],
                    'tiers': {
                        'basic': {
                            'price': 1000,
                            'features': ['feature1']
                        },
                        'premium': {
                            'price': 2000,
                            'features': ['feature1', 'feature2']
                        }
                    }
                },
                'consulting': {
                    'hourly_rate': 100,
                    'currency': 'MXN',
                    'minimum_hours': 10
                }
            },
            'discounts': {
                'volume': {
                    'threshold': 5,
                    'percentage': 10
                },
                'loyalty': {
                    'years': 1,
                    'percentage': 5
                }
            },
            'payment_methods': {
                'credit_card': true,
                'bank_transfer': true,
                'paypal': true
            }
        }"""
    )
    
    # Configuración de ATS
    ats_config = models.JSONField(
        default=dict,
        help_text="""Configuración del sistema ATS:
        {
            'workflow': {
                'stages': ['screening', 'interview', 'offer'],
                'default_stage': 'screening',
                'auto_advance': true,
                'notifications': {
                    'stage_change': true,
                    'new_candidate': true
                }
            },
            'scoring': {
                'criteria': ['experience', 'skills', 'education'],
                'weights': {
                    'experience': 0.4,
                    'skills': 0.4,
                    'education': 0.2
                },
                'threshold': 0.7
            },
            'automation': {
                'auto_screening': true,
                'auto_interview_scheduling': true,
                'auto_rejection': true,
                'auto_followup': true
            },
            'templates': {
                'job_description': 'template_id',
                'offer_letter': 'template_id',
                'rejection_email': 'template_id'
            }
        }"""
    )
    
    # Configuración de Analytics
    analytics_config = models.JSONField(
        default=dict,
        help_text="""Configuración de analytics:
        {
            'metrics': {
                'recruitment': {
                    'time_to_hire': true,
                    'cost_per_hire': true,
                    'quality_of_hire': true
                },
                'candidate': {
                    'application_rate': true,
                    'acceptance_rate': true,
                    'dropout_rate': true
                },
                'business': {
                    'revenue': true,
                    'profit_margin': true,
                    'customer_satisfaction': true
                }
            },
            'reporting': {
                'frequency': 'weekly',
                'recipients': ['email1', 'email2'],
                'formats': ['pdf', 'excel']
            },
            'dashboards': {
                'recruitment': ['metric1', 'metric2'],
                'business': ['metric1', 'metric2']
            }
        }"""
    )
    
    # Configuración de Learning
    learning_config = models.JSONField(
        default=dict,
        help_text="""Configuración del sistema de aprendizaje:
        {
            'courses': {
                'enabled': true,
                'categories': ['technical', 'soft_skills'],
                'completion_criteria': {
                    'min_score': 70,
                    'attendance_required': true
                }
            },
            'certifications': {
                'enabled': true,
                'validity_period': 365,
                'renewal_required': true
            },
            'assessments': {
                'frequency': 'monthly',
                'types': ['quiz', 'project', 'interview'],
                'passing_score': 70
            }
        }"""
    )
    
    # Relaciones
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='owned_business_units',
        db_index=True,
        help_text="Usuario propietario de la unidad de negocio"
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='BusinessUnitMembership',
        related_name='business_units',
        help_text="Miembros de la unidad de negocio"
    )
    
    # Campos de Integración
    wordpress_base_url = models.URLField(
        max_length=255,
        help_text="URL base de la API de WordPress",
        null=True,
        blank=True
    )
    wordpress_auth_token = models.CharField(
        max_length=500,
        help_text="Token JWT para autenticación con WordPress",
        null=True,
        blank=True
    )
    ntfy_topic = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        default=None,
        help_text="Tema de ntfy.sh específico para esta unidad de negocio"
    )
    
    # Campos de Comunicación
    admin_phone = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text="Teléfono del administrador"
    )
    whatsapp_enabled = models.BooleanField(
        default=True,
        help_text="¿WhatsApp está habilitado?"
    )
    telegram_enabled = models.BooleanField(
        default=True,
        help_text="¿Telegram está habilitado?"
    )
    messenger_enabled = models.BooleanField(
        default=True,
        help_text="¿Messenger está habilitado?"
    )
    instagram_enabled = models.BooleanField(
        default=True,
        help_text="¿Instagram está habilitado?"
    )
    
    # Campos de Scraping
    scrapping_enabled = models.BooleanField(
        default=True,
        help_text="¿El scraping está habilitado?"
    )
    scraping_domains = models.ManyToManyField(
        'DominioScraping',
        related_name="business_units",
        blank=True,
        help_text="Dominios permitidos para scraping"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Unidad de Negocio"
        verbose_name_plural = "Unidades de Negocio"
        ordering = ['name']
        indexes = [
            models.Index(fields=['name', 'code']),
            models.Index(fields=['active', 'created_at']),
            models.Index(fields=['owner', 'active']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    # Métodos de Configuración
    def get_settings(self, section=None, key=None, default=None):
        """Obtiene configuración específica con caché."""
        cache_key = f'business_unit_settings_{self.id}'
        settings = cache.get(cache_key)
        
        if settings is None:
            settings = self.business_settings
            cache.set(cache_key, settings, 3600)  # Cache por 1 hora
            
        if section is None:
            return settings
            
        section_data = settings.get(section, {})
        if key is None:
            return section_data
            
        return section_data.get(key, default)
    
    def set_settings(self, section, key, value):
        """Actualiza configuración específica y limpia caché."""
        if section not in self.business_settings:
            self.business_settings[section] = {}
        self.business_settings[section][key] = value
        self.save(update_fields=['business_settings', 'updated_at'])
        self._clear_caches()
    
    # Métodos de Integración
    def get_integration_config(self, platform):
        """Obtiene configuración de integración específica."""
        return self.integrations.get(platform, {})
    
    def set_integration_config(self, platform, config):
        """Actualiza configuración de integración específica."""
        self.integrations[platform] = config
        self.save(update_fields=['integrations', 'updated_at'])
        self._clear_caches()
    
    # Métodos de Pricing
    def get_pricing_config(self, service_type=None):
        """Obtiene configuración de pricing."""
        if service_type is None:
            return self.pricing_config
        return self.pricing_config.get(service_type, {})
    
    def set_pricing_config(self, service_type, config):
        """Actualiza configuración de pricing."""
        self.pricing_config[service_type] = config
        self.save(update_fields=['pricing_config', 'updated_at'])
        self._clear_caches()
    
    # Métodos de ATS
    def get_ats_config(self, section=None):
        """Obtiene configuración del ATS."""
        if section is None:
            return self.ats_config
        return self.ats_config.get(section, {})
    
    def set_ats_config(self, section, config):
        """Actualiza configuración del ATS."""
        self.ats_config[section] = config
        self.save(update_fields=['ats_config', 'updated_at'])
        self._clear_caches()
    
    # Métodos de Analytics
    def get_analytics_config(self, section=None):
        """Obtiene configuración de analytics."""
        if section is None:
            return self.analytics_config
        return self.analytics_config.get(section, {})
    
    def set_analytics_config(self, section, config):
        """Actualiza configuración de analytics."""
        self.analytics_config[section] = config
        self.save(update_fields=['analytics_config', 'updated_at'])
        self._clear_caches()
    
    # Métodos de Learning
    def get_learning_config(self, section=None):
        """Obtiene configuración de learning."""
        if section is None:
            return self.learning_config
        return self.learning_config.get(section, {})
    
    def set_learning_config(self, section, config):
        """Actualiza configuración de learning."""
        self.learning_config[section] = config
        self.save(update_fields=['learning_config', 'updated_at'])
        self._clear_caches()
    
    # Métodos de Gestión de Miembros
    def get_members(self, role=None):
        """Obtiene miembros con caché."""
        cache_key = f'business_unit_members_{self.id}_{role or "all"}'
        members = cache.get(cache_key)
        
        if members is None:
            query = self.memberships.all()
            if role:
                query = query.filter(role=role)
            members = list(query)
            cache.set(cache_key, members, 3600)  # Cache por 1 hora
            
        return members
    
    def add_member(self, user, role='member', permissions=None):
        """Agrega un nuevo miembro."""
        membership = BusinessUnitMembership.objects.create(
            business_unit=self,
            user=user,
            role=role,
            permissions=permissions or {}
        )
        self._clear_caches()
        return membership
    
    def remove_member(self, user):
        """Elimina un miembro."""
        BusinessUnitMembership.objects.filter(
            business_unit=self,
            user=user
        ).delete()
        self._clear_caches()

    # Métodos de Estado
    @property
    def is_active(self):
        """Verifica si la unidad está activa."""
        return self.active
    
    def activate(self):
        """Activa la unidad de negocio."""
        self.active = True
        self.save(update_fields=['active', 'updated_at'])
        self._clear_caches()
    
    def deactivate(self):
        """Desactiva la unidad de negocio."""
        self.active = False
        self.save(update_fields=['active', 'updated_at'])
        self._clear_caches()
    
    # Métodos de Utilidad
    def _clear_caches(self):
        """Limpia todas las cachés relacionadas con esta unidad."""
        cache.delete(f'business_unit_settings_{self.id}')
        cache.delete(f'business_unit_members_{self.id}')
        cache.delete(f'business_unit_integrations_{self.id}')
        cache.delete(f'business_unit_pricing_{self.id}')
        cache.delete(f'business_unit_ats_{self.id}')
        cache.delete(f'business_unit_analytics_{self.id}')
        cache.delete(f'business_unit_learning_{self.id}')
    
    def get_ntfy_topic(self):
        """Obtiene el tema de ntfy.sh."""
        return self.ntfy_topic or settings.DEFAULT_NTFY_TOPIC
    
    def get_notification_recipients(self):
        """Obtiene los destinatarios de notificaciones."""
        return [self.owner] + list(self.members.filter(is_active=True))
    
    def get_email_template_path(self):
        """Obtiene la ruta de la plantilla de email."""
        return f"emails/{self.code.lower()}/"

class BusinessUnitMembership(models.Model):
    """Modelo para gestionar la membresía de usuarios en unidades de negocio."""
    
    ROLE_CHOICES = [
        ('admin', 'Administrador'),
        ('manager', 'Gerente'),
        ('member', 'Miembro'),
        ('viewer', 'Solo Lectura'),
    ]
    
    business_unit = models.ForeignKey(
        BusinessUnit,
        on_delete=models.CASCADE,
        related_name='memberships',
        db_index=True
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='business_unit_memberships',
        db_index=True
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='member',
        db_index=True
    )
    permissions = models.JSONField(
        default=dict,
        help_text="Permisos específicos del miembro"
    )
    joined_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Membresía de Unidad de Negocio"
        verbose_name_plural = "Membresías de Unidades de Negocio"
        unique_together = ['business_unit', 'user']
        indexes = [
            models.Index(fields=['business_unit', 'role']),
            models.Index(fields=['user', 'role']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.business_unit.name} ({self.get_role_display()})"
    
    def has_permission(self, permission_key):
        """Verifica si el miembro tiene un permiso específico."""
        return self.permissions.get(permission_key, False)
    
    def grant_permission(self, permission_key):
        """Otorga un permiso específico."""
        if 'permissions' not in self.permissions:
            self.permissions['permissions'] = {}
        self.permissions['permissions'][permission_key] = True
        self.save(update_fields=['permissions', 'updated_at'])
        self.business_unit._clear_caches()
    
    def revoke_permission(self, permission_key):
        """Revoca un permiso específico."""
        if 'permissions' in self.permissions:
            self.permissions['permissions'][permission_key] = False
            self.save(update_fields=['permissions', 'updated_at'])
            self.business_unit._clear_caches()

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
    
    # Campos para grupos y familiares
    family_members = models.ManyToManyField(
        'self',
        through='FamilyRelationship',
        symmetrical=False,
        related_name='related_family_members',
        blank=True
    )
    
    group_work_history = models.JSONField(
        default=list,
        help_text="Historial de trabajo en grupo"
    )
    
    group_success_rate = models.FloatField(
        default=0.0,
        help_text="Tasa de éxito en trabajos grupales"
    )
    
    group_stability = models.FloatField(
        default=0.0,
        help_text="Estabilidad en grupos de trabajo"
    )
    
    community_integration = models.FloatField(
        default=0.0,
        help_text="Nivel de integración en la comunidad"
    )
    
    # Ya están definidos arriba
    # Conexiones sociales para SocialLink™ (principalmente para candidatos Amigro)
    # Métodos relacionados con referencias
    def get_references_given(self):
        """Obtiene todas las referencias que ha dado esta persona."""
        return self.references_given.all()
    
    def get_references_received(self):
        """Obtiene todas las referencias que ha recibido esta persona."""
        return self.references_received.all()
    
    def get_pending_reference_requests(self):
        """Obtiene las solicitudes de referencia pendientes de esta persona."""
        return self.references_given.filter(status='pending')
    
    def can_give_reference(self, candidate):
        """Verifica si esta persona puede dar una referencia al candidato."""
        # Aquí podrías agregar lógica adicional, como verificar si ya ha dado una referencia
        # o si existe alguna relación laboral previa
        return True
    
    def __str__(self):
        nombre_completo=f"{self.nombre} {self.apellido_paterno or ''} {self.apellido_materno or ''}".strip()
        return nombre_completo
    def is_profile_complete(self):
        required_fields=['nombre','apellido_paterno','email','phone','skills']
        missing_fields=[field for field in required_fields if not getattr(self,field,None)]
        return not missing_fields
    
    # Campos extendidos para análisis generacional y motivacional
    generational_insights = models.JSONField(null=True, blank=True)
    motivational_insights = models.JSONField(null=True, blank=True)
    work_style_preferences = models.JSONField(null=True, blank=True)
    
    def get_generational_profile(self):
        """Obtiene el perfil generacional basado en la edad y respuestas"""
        if not self.date_of_birth:
            return None
            
        birth_year = self.date_of_birth.year
        if 1946 <= birth_year <= 1964:
            return 'BB'  # Baby Boomers
        elif 1965 <= birth_year <= 1980:
            return 'X'   # Generación X
        elif 1981 <= birth_year <= 1996:
            return 'Y'   # Millennials
        elif 1997 <= birth_year <= 2012:
            return 'Z'   # Generación Z
        return None
    
    def get_motivational_profile(self):
        """Analiza las respuestas para determinar el perfil motivacional"""
        if not self.answers:
            return None
            
        profile = {
            'intrinsic': {
                'autonomy': 0,
                'mastery': 0,
                'purpose': 0
            },
            'extrinsic': {
                'recognition': 0,
                'compensation': 0,
                'status': 0
            }
        }
        
        # Analizar respuestas para determinar motivadores
        for answer in self.answers:
            if 'motivation' in answer.get('category', '').lower():
                # Lógica para analizar respuestas motivacionales
                pass
                
        return profile
    
    def get_work_style_preferences(self):
        """Analiza las preferencias de estilo de trabajo"""
        if not self.answers:
            return None
            
        preferences = {
            'collaboration': 0,
            'independence': 0,
            'structure': 0,
            'communication_style': None,
            'feedback_preference': None
        }
        
        # Analizar respuestas para determinar preferencias
        for answer in self.answers:
            if 'work_style' in answer.get('category', '').lower():
                # Lógica para analizar preferencias de trabajo
                pass
                
        return preferences
    
    def generate_generational_insights(self):
        """Genera insights generacionales basados en la evaluación"""
        generational_profile = self.get_generational_profile()
        motivational_profile = self.get_motivational_profile()
        work_preferences = self.get_work_style_preferences()
        
        if not all([generational_profile, motivational_profile, work_preferences]):
            return None
            
        insights = {
            'generational': {
                'generation': generational_profile,
                'work_preferences': work_preferences,
                'values': {
                    'career_growth': self.calculate_career_growth_importance(),
                    'social_impact': self.calculate_social_impact_importance(),
                    'financial_security': self.calculate_financial_security_importance()
                }
            },
            'motivational': motivational_profile,
            'work_style': work_preferences
        }
        
        self.generational_insights = insights
        self.save()
        
        return insights
    
    def calculate_career_growth_importance(self):
        """Calcula la importancia del crecimiento profesional"""
        # Implementar lógica basada en respuestas
        return 0
    
    def calculate_social_impact_importance(self):
        """Calcula la importancia del impacto social"""
        # Implementar lógica basada en respuestas
        return 0
    
    def calculate_financial_security_importance(self):
        """Calcula la importancia de la seguridad financiera"""
        # Implementar lógica basada en respuestas
        return 0

    completed_evaluations = models.JSONField(
        default=list,
        help_text="Lista de evaluaciones completadas por el usuario"
    )

class Skill(models.Model):
    """Modelo para habilidades y competencias."""
    
    CATEGORY_CHOICES = [
        ('technical', 'Técnica'),
        ('soft', 'Soft Skills'),
        ('language', 'Idioma'),
        ('certification', 'Certificación'),
        ('domain', 'Dominio'),
        ('other', 'Otro')
    ]
    
    LEVEL_CHOICES = [
        ('beginner', 'Principiante'),
        ('intermediate', 'Intermedio'),
        ('advanced', 'Avanzado'),
        ('expert', 'Experto')
    ]
    
    name = models.CharField(max_length=100, unique=True, help_text="Nombre de la habilidad")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, help_text="Categoría de la habilidad")
    description = models.TextField(blank=True, help_text="Descripción detallada de la habilidad")
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='intermediate', help_text="Nivel de competencia")
    years_experience = models.PositiveIntegerField(default=0, help_text="Años de experiencia requeridos")
    
    # Campos para análisis y recomendaciones
    demand_score = models.FloatField(default=0.0, help_text="Puntuación de demanda en el mercado (0-1)")
    growth_potential = models.FloatField(default=0.0, help_text="Potencial de crecimiento (0-1)")
    related_skills = models.ManyToManyField('self', blank=True, symmetrical=False, related_name='related_to')
    
    # Campos para integración con aprendizaje
    learning_resources = models.JSONField(default=list, help_text="Recursos de aprendizaje asociados")
    certification_required = models.BooleanField(default=False, help_text="¿Requiere certificación?")
    certification_providers = models.JSONField(default=list, help_text="Proveedores de certificación")
    
    # Campos para métricas y seguimiento
    usage_count = models.PositiveIntegerField(default=0, help_text="Número de veces que se ha utilizado")
    last_used = models.DateTimeField(null=True, blank=True, help_text="Última vez que se utilizó")
    
    # Campos de auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, help_text="¿La habilidad está activa?")
    
    class Meta:
        verbose_name = "Habilidad"
        verbose_name_plural = "Habilidades"
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['category']),
            models.Index(fields=['level']),
            models.Index(fields=['demand_score']),
            models.Index(fields=['is_active'])
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"
    
    def increment_usage(self):
        """Incrementa el contador de uso y actualiza la última fecha de uso."""
        self.usage_count += 1
        self.last_used = timezone.now()
        self.save(update_fields=['usage_count', 'last_used'])
    
    def get_related_skills(self):
        """Obtiene las habilidades relacionadas."""
        return self.related_skills.filter(is_active=True)
    
    def get_learning_resources(self):
        """Obtiene los recursos de aprendizaje asociados."""
        return self.learning_resources
    
    def get_certification_providers(self):
        """Obtiene los proveedores de certificación."""
        return self.certification_providers if self.certification_required else []
    
    def calculate_demand_score(self):
        """Calcula la puntuación de demanda basada en varios factores."""
        # Implementar lógica de cálculo
        pass
    
    def calculate_growth_potential(self):
        """Calcula el potencial de crecimiento basado en tendencias del mercado."""
        # Implementar lógica de cálculo
        pass

class SkillAssessment(models.Model):
    """Modelo para evaluaciones de habilidades."""
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    level = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Evaluación de Habilidad"
        verbose_name_plural = "Evaluaciones de Habilidades"

    def __str__(self):
        return f"{self.person} - {self.skill}"

# --- Compatibilidad histórica -------------------------------------------------
# Varios módulos antiguos (p. ej. TruthAnalyzer) esperan el modelo
# `PersonSkill` con la misma interfaz que `SkillAssessment`. Para evitar
# refactorizaciones masivas inmediatas, creamos un alias directo.
PersonSkill = SkillAssessment

# Alias para compatibilidad con importaciones existentes
Contact = Person

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
    legal_name = models.CharField(max_length=255, blank=True, null=True, help_text="Nombre legal de la empresa.")
    tax_id = models.CharField(max_length=50, blank=True, null=True, help_text="RFC o identificación fiscal.")
    industry = models.CharField(max_length=100, blank=True, null=True, help_text="Industria.")
    size = models.CharField(max_length=50, blank=True, null=True, help_text="Tamaño de la empresa, ej: 1-10, 11-50, 51-200, 201-500, 501+")
    location = models.CharField(max_length=100, blank=True, null=True, help_text="Ubicación principal.")
    address = models.TextField(blank=True, null=True, help_text="Dirección completa de la empresa.")
    city = models.CharField(max_length=100, blank=True, null=True, help_text="Ciudad.")
    state = models.CharField(max_length=100, blank=True, null=True, help_text="Estado o provincia.")
    country = models.CharField(max_length=100, blank=True, null=True, help_text="País.")
    website = models.URLField(max_length=200, blank=True, null=True, help_text="Sitio web corporativo.")
    description = models.TextField(blank=True, null=True, help_text="Descripción general de la empresa.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    indexes = [models.Index(fields=['name'])]

    def __str__(self):
        return self.name

    # Roles de contacto
    signer = models.ForeignKey('Person', on_delete=models.SET_NULL, null=True, blank=True, related_name='signed_companies', help_text="Persona que firma la propuesta")
    payment_responsible = models.ForeignKey('Person', on_delete=models.SET_NULL, null=True, blank=True, related_name='payment_companies', help_text="Responsable de pagos")
    fiscal_responsible = models.ForeignKey('Person', on_delete=models.SET_NULL, null=True, blank=True, related_name='fiscal_companies', help_text="Responsable fiscal")
    process_responsible = models.ForeignKey('Person', on_delete=models.SET_NULL, null=True, blank=True, related_name='process_companies', help_text="Responsable del proceso")
    report_invitees = models.ManyToManyField('Person', blank=True, related_name='report_companies', help_text="Personas invitadas a reportes (ej. Dir RH, CFO, etc)")
    # Preferencias de notificación
    notification_preferences = models.JSONField(default=dict, blank=True, help_text="Preferencias de notificación por tipo de evento y canal")

class FamilyRelationship(models.Model):
    """Modelo para gestionar relaciones familiares entre personas."""
    
    RELATIONSHIP_TYPES = [
        ('spouse', 'Cónyuge'),
        ('parent', 'Padre/Madre'),
        ('child', 'Hijo/Hija'),
        ('sibling', 'Hermano/Hermana'),
        ('cousin', 'Primo/Prima'),
        ('aunt_uncle', 'Tío/Tía'),
        ('nephew_niece', 'Sobrino/Sobrina'),
        ('grandparent', 'Abuelo/Abuela'),
        ('grandchild', 'Nieto/Nieta'),
        ('in_law', 'Familiar político'),
        ('other', 'Otro')
    ]
    
    person = models.ForeignKey(
        Person,
        on_delete=models.CASCADE,
        related_name='family_relationships'
    )
    
    related_person = models.ForeignKey(
        Person,
        on_delete=models.CASCADE,
        related_name='related_family_relationships'
    )
    
    relationship_type = models.CharField(
        max_length=20,
        choices=RELATIONSHIP_TYPES
    )
    
    is_verified = models.BooleanField(
        default=False,
        help_text="Indica si la relación ha sido verificada"
    )
    
    verification_date = models.DateTimeField(
        null=True,
        blank=True
    )
    
    notes = models.TextField(
        blank=True,
        help_text="Notas adicionales sobre la relación"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Relación Familiar"
        verbose_name_plural = "Relaciones Familiares"
        unique_together = ('person', 'related_person', 'relationship_type')
        indexes = [
            models.Index(fields=['person']),
            models.Index(fields=['related_person']),
            models.Index(fields=['relationship_type'])
        ]
    
    def __str__(self):
        return f"{self.person} - {self.get_relationship_type_display()} - {self.related_person}"
    
    def verify_relationship(self):
        """Marca la relación como verificada."""
        self.is_verified = True
        self.verification_date = timezone.now()
        self.save()

class MigrantSupportPlatform(models.Model):
    created_at=models.DateTimeField(auto_now_add=True)

class Provider(models.Model):
    """Modelo para proveedores de servicios de IA."""
    name = models.CharField(max_length=100, unique=True, help_text="Nombre del proveedor (ej: OpenAI, Mistral AI)")
    api_endpoint = models.URLField(help_text="URL base de la API del proveedor")
    models_endpoint = models.URLField(help_text="URL para obtener la lista de modelos disponibles")
    is_active = models.BooleanField(default=True, help_text="¿El proveedor está activo?")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Campos adicionales para configuración
    api_version = models.CharField(max_length=50, blank=True, null=True, help_text="Versión de la API")
    rate_limit = models.IntegerField(default=100, help_text="Límite de solicitudes por minuto")
    timeout = models.IntegerField(default=30, help_text="Timeout en segundos para las solicitudes")
    
    # Campos para métricas
    total_requests = models.IntegerField(default=0, help_text="Total de solicitudes realizadas")
    total_tokens = models.IntegerField(default=0, help_text="Total de tokens procesados")
    last_used = models.DateTimeField(null=True, blank=True, help_text="Última vez que se usó el proveedor")
    
    class Meta:
        verbose_name = "Proveedor de IA"
        verbose_name_plural = "Proveedores de IA"
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['is_active']),
            models.Index(fields=['last_used']),
        ]

    def __str__(self):
        return self.name

    def get_available_models(self):
        """Obtiene la lista de modelos disponibles del proveedor."""
        try:
            response = requests.get(
                self.models_endpoint,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error obteniendo modelos de {self.name}: {str(e)}")
            return []

    def increment_usage(self, tokens=0):
        """Incrementa el contador de uso del proveedor."""
        self.total_requests += 1
        self.total_tokens += tokens
        self.last_used = timezone.now()
        self.save(update_fields=['total_requests', 'total_tokens', 'last_used'])

class GptApi(models.Model):
    """Modelo para configuraciones de APIs de IA."""
    provider = models.ForeignKey(
        Provider,
        on_delete=models.CASCADE,
        related_name='apis',
        help_text="Proveedor asociado a esta API"
    )
    model = models.CharField(
        max_length=100,
        help_text="Nombre del modelo (ej: gpt-4, mistral-large)"
    )
    api_key = models.CharField(
        max_length=500,
        help_text="API key para autenticación"
    )
    max_tokens = models.IntegerField(
        default=2000,
        help_text="Máximo número de tokens por respuesta"
    )
    temperature = models.FloatField(
        default=0.7,
        validators=[MinValueValidator(0.0), MaxValueValidator(2.0)],
        help_text="Temperatura para la generación (0.0 - 2.0)"
    )
    top_p = models.FloatField(
        default=0.9,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Probabilidad acumulativa para la generación (0.0 - 1.0)"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="¿Esta configuración está activa?"
    )
    
    # Campos adicionales para configuración
    frequency_penalty = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(-2.0), MaxValueValidator(2.0)],
        help_text="Penalización por frecuencia (-2.0 - 2.0)"
    )
    presence_penalty = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(-2.0), MaxValueValidator(2.0)],
        help_text="Penalización por presencia (-2.0 - 2.0)"
    )
    stop_sequences = models.JSONField(
        default=list,
        blank=True,
        help_text="Secuencias de parada para la generación"
    )
    
    # Campos para métricas
    total_requests = models.IntegerField(
        default=0,
        help_text="Total de solicitudes realizadas"
    )
    total_tokens = models.IntegerField(
        default=0,
        help_text="Total de tokens procesados"
    )
    last_used = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Última vez que se usó esta configuración"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuración de API de IA"
        verbose_name_plural = "Configuraciones de APIs de IA"
        unique_together = ['provider', 'model']
        indexes = [
            models.Index(fields=['provider', 'model']),
            models.Index(fields=['is_active']),
            models.Index(fields=['last_used']),
        ]

    def __str__(self):
        return f"{self.provider.name} - {self.model}"

    def get_config(self):
        """Obtiene la configuración completa para la API."""
        return {
            'model': self.model,
            'max_tokens': self.max_tokens,
            'temperature': self.temperature,
            'top_p': self.top_p,
            'frequency_penalty': self.frequency_penalty,
            'presence_penalty': self.presence_penalty,
            'stop_sequences': self.stop_sequences
        }

    def increment_usage(self, tokens=0):
        """Incrementa el contador de uso de la API."""
        self.total_requests += 1
        self.total_tokens += tokens
        self.last_used = timezone.now()
        self.save(update_fields=['total_requests', 'total_tokens', 'last_used'])
        
        # También incrementa el uso del proveedor
        self.provider.increment_usage(tokens)

    def validate_config(self):
        """Valida la configuración de la API."""
        if self.temperature < 0.0 or self.temperature > 2.0:
            raise ValidationError("La temperatura debe estar entre 0.0 y 2.0")
        if self.top_p < 0.0 or self.top_p > 1.0:
            raise ValidationError("El top_p debe estar entre 0.0 y 1.0")
        if self.frequency_penalty < -2.0 or self.frequency_penalty > 2.0:
            raise ValidationError("La penalización por frecuencia debe estar entre -2.0 y 2.0")
        if self.presence_penalty < -2.0 or self.presence_penalty > 2.0:
            raise ValidationError("La penalización por presencia debe estar entre -2.0 y 2.0")

    def save(self, *args, **kwargs):
        """Valida la configuración antes de guardar."""
        self.validate_config()
        super().save(*args, **kwargs)

class WhatsAppAPI(models.Model):
    """Modelo para configuración de WhatsApp."""
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE)
    api_key = models.CharField(max_length=500)
    phone_number = models.CharField(max_length=20)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    meta_verified = models.BooleanField(
        default=False,
        help_text="Indica si la cuenta de WhatsApp tiene Meta Verified badge"
    )
    meta_verified_since = models.DateTimeField(
        null=True, blank=True,
        help_text="Fecha en que se obtuvo la verificación de Meta"
    )
    meta_verified_badge_url = models.URLField(
        null=True, blank=True,
        help_text="URL del badge de verificación de Meta"
    )

    class Meta:
        verbose_name = "API de WhatsApp"
        verbose_name_plural = "APIs de WhatsApp"

    def __str__(self):
        return f"{self.business_unit.name} - {self.phone_number}"

class TelegramAPI(models.Model):
    """Modelo para configuración de Telegram."""
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE)
    bot_token = models.CharField(max_length=500)
    chat_id = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "API de Telegram"
        verbose_name_plural = "APIs de Telegram"

    def __str__(self):
        return f"{self.business_unit.name} - {self.chat_id}"

class DominioScraping(models.Model):
    """Modelo para dominios de scraping."""
    domain = models.URLField(unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Dominio de Scraping"
        verbose_name_plural = "Dominios de Scraping"

    def __str__(self):
        return self.domain

class Vacante(models.Model):
    titulo = models.CharField(max_length=1000)
    empresa = models.ForeignKey('Empleador', on_delete=models.CASCADE, related_name='vacantes')
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE, related_name='vacantes', null=True, blank=True)
    proposal = models.ForeignKey('Proposal', on_delete=models.SET_NULL, null=True, blank=True, related_name='vacancies')
    # Campo original (mantenido para compatibilidad)
    salario = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    # Nuevos campos para rango salarial
    salario_minimo = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    salario_maximo = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
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

class Vacancy(models.Model):
    """Modelo para vacantes."""
    title = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=50)
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Vacante"
        verbose_name_plural = "Vacantes"

    def __str__(self):
        return self.name

class Opportunity(models.Model):
    """Modelo para oportunidades."""
    title = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=50)
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Oportunidad"
        verbose_name_plural = "Oportunidades"

    def __str__(self):
        return self.name

class MilkyLeak(models.Model):
    """Modelo para el sistema de leaks."""
    title = models.CharField(max_length=200)
    content = models.TextField()
    source = models.CharField(max_length=100)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Leak"
        verbose_name_plural = "Leaks"

    def __str__(self):
        return self.name

class WorkflowStage(models.Model):
    """Modelo para etapas del flujo de trabajo."""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    order = models.IntegerField()
    duration_days = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Etapa de Flujo"
        verbose_name_plural = "Etapas de Flujo"
        ordering = ['order']

    def __str__(self):
        return self.name

class PublicationChannel(models.Model):
    """Modelo para canales de publicación."""
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Canal de Publicación"
        verbose_name_plural = "Canales de Publicación"

    def __str__(self):
        return self.name

class PublicationRecord(models.Model):
    """Modelo para registros de publicaciones."""
    vacancy = models.ForeignKey('Vacante', on_delete=models.CASCADE)
    channel = models.ForeignKey(PublicationChannel, on_delete=models.CASCADE)
    status = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Registro de Publicación"
        verbose_name_plural = "Registros de Publicación"

    def __str__(self):
        return f"{self.vacancy.title} - {self.channel.name}"

class Proposal(models.Model):
    """Modelo para propuestas."""
    title = models.CharField(max_length=200)
    content = models.TextField()
    status = models.CharField(max_length=50, choices=PROPOSAL_STATUS_CHOICES)
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    qr_code = models.ImageField(upload_to='proposals/qr/', null=True, blank=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='proposals')
    business_units = models.ManyToManyField(BusinessUnit, related_name='proposals')
    vacancies = models.ManyToManyField('Vacante', related_name='proposals')
    pricing_total = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    pricing_details = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = "Propuesta"
        verbose_name_plural = "Propuestas"

    def __str__(self):
        return self.name

class Invoice(models.Model):
    """Modelo para facturas con soporte para facturación electrónica y compliance."""
    
    # Relaciones principales
    payment = models.ForeignKey('app.Pago', on_delete=models.CASCADE, related_name='invoices')
    service = models.ForeignKey('Service', on_delete=models.CASCADE, related_name='invoices', null=True, blank=True)
    business_unit = models.ForeignKey('BusinessUnit', on_delete=models.CASCADE, related_name='invoices')
    
    # Información básica
    invoice_number = models.CharField(max_length=100, unique=True, help_text="Número de factura")
    folio = models.CharField(max_length=50, blank=True, help_text="Folio interno")
    
    # Estados
    STATUS_CHOICES = [
        ('draft', 'Borrador'),
        ('pending', 'Pendiente'),
        ('sent', 'Enviada'),
        ('paid', 'Pagada'),
        ('cancelled', 'Cancelada'),
        ('expired', 'Expirada'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Fechas
    issue_date = models.DateTimeField(auto_now_add=True, help_text="Fecha de emisión")
    due_date = models.DateTimeField(null=True, blank=True, help_text="Fecha de vencimiento")
    payment_date = models.DateTimeField(null=True, blank=True, help_text="Fecha de pago")
    
    # Montos
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default='MXN')
    
    # Datos fiscales del emisor (empresa)
    issuer_rfc = models.CharField(max_length=13, blank=True, help_text="RFC del emisor")
    issuer_name = models.CharField(max_length=200, blank=True, help_text="Razón social del emisor")
    issuer_address = models.TextField(blank=True, help_text="Dirección fiscal del emisor")
    issuer_regime = models.CharField(max_length=50, blank=True, help_text="Régimen fiscal del emisor")
    
    # Datos fiscales del receptor (cliente)
    receiver_rfc = models.CharField(max_length=13, blank=True, help_text="RFC del receptor")
    receiver_name = models.CharField(max_length=200, blank=True, help_text="Razón social del receptor")
    receiver_address = models.TextField(blank=True, help_text="Dirección fiscal del receptor")
    receiver_use = models.CharField(max_length=50, blank=True, help_text="Uso CFDI del receptor")
    
    # Facturación electrónica
    cfdi_uuid = models.CharField(max_length=36, blank=True, help_text="UUID del CFDI")
    cfdi_xml = models.TextField(blank=True, help_text="XML del CFDI")
    cfdi_pdf = models.FileField(upload_to='invoices/pdf/', blank=True, help_text="PDF de la factura")
    sat_status = models.CharField(max_length=20, blank=True, help_text="Estado en el SAT")
    
    # Configuración de facturación
    electronic_billing_enabled = models.BooleanField(default=True, help_text="¿Facturación electrónica habilitada?")
    auto_send_to_finances = models.BooleanField(default=True, help_text="¿Enviar automáticamente a finanzas?")
    finances_email = models.EmailField(default='finanzas@huntRED.com', help_text="Email de finanzas")
    
    # Compliance y auditoría
    audit_log = models.JSONField(default=list, help_text="Registro de cambios")
    compliance_notes = models.TextField(blank=True, help_text="Notas de compliance")
    
    # Metadatos
    notes = models.TextField(blank=True, help_text="Notas adicionales")
    terms_conditions = models.TextField(blank=True, help_text="Términos y condiciones")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_invoices')

    class Meta:
        verbose_name = "Factura"
        verbose_name_plural = "Facturas"
        ordering = ['-issue_date']
        indexes = [
            models.Index(fields=['invoice_number']),
            models.Index(fields=['status']),
            models.Index(fields=['issue_date']),
            models.Index(fields=['cfdi_uuid']),
            models.Index(fields=['business_unit']),
        ]

    def __str__(self):
        return f"Factura {self.invoice_number} - {self.total_amount} {self.currency}"
    
    def save(self, *args, **kwargs):
        # Calcular total si no está establecido
        if not self.total_amount:
            self.total_amount = self.subtotal + self.tax_amount - self.discount_amount
        
        # Generar número de factura si no existe
        if not self.invoice_number:
            self.invoice_number = self.generate_invoice_number()
        
        # Registrar cambio en audit_log
        self.audit_log.append({
            'timestamp': timezone.now().isoformat(),
            'action': 'updated' if self.pk else 'created',
            'user': getattr(self.created_by, 'username', 'system') if self.created_by else 'system',
            'changes': self._get_changes()
        })
        
        super().save(*args, **kwargs)
    
    def generate_invoice_number(self):
        """Genera un número de factura único."""
        from datetime import datetime
        year = datetime.now().year
        month = datetime.now().month
        
        # Buscar el último número de factura del mes
        last_invoice = Invoice.objects.filter(
            invoice_number__startswith=f"F{year}{month:02d}"
        ).order_by('-invoice_number').first()
        
        if last_invoice:
            try:
                last_number = int(last_invoice.invoice_number[-4:])
                new_number = last_number + 1
            except ValueError:
                new_number = 1
        else:
            new_number = 1
        
        return f"F{year}{month:02d}{new_number:04d}"
    
    def _get_changes(self):
        """Obtiene los cambios realizados en el modelo."""
        if not self.pk:  # Nueva instancia
            return {'created': True}
        
        # Para instancias existentes, comparar con la versión anterior
        try:
            old_instance = Invoice.objects.get(pk=self.pk)
            changes = {}
            for field in ['status', 'total_amount', 'cfdi_uuid']:
                old_value = getattr(old_instance, field)
                new_value = getattr(self, field)
                if old_value != new_value:
                    changes[field] = {'old': old_value, 'new': new_value}
            return changes
        except Invoice.DoesNotExist:
            return {'created': True}
    
    def calculate_totals(self):
        """Calcula los totales de la factura."""
        # Obtener todos los conceptos de la factura
        line_items = self.line_items.all()
        
        self.subtotal = sum(item.subtotal for item in line_items)
        self.tax_amount = sum(item.tax_amount for item in line_items)
        self.discount_amount = sum(item.discount_amount for item in line_items)
        self.total_amount = self.subtotal + self.tax_amount - self.discount_amount
        
        self.save(update_fields=['subtotal', 'tax_amount', 'discount_amount', 'total_amount'])
    
    def send_to_finances(self):
        """Envía la factura al departamento de finanzas."""
        if not self.auto_send_to_finances:
            return False
        
        # Aquí implementarías la lógica para enviar a finanzas@huntRED.com
        # Por ahora, solo registramos la acción
        self.audit_log.append({
            'timestamp': timezone.now().isoformat(),
            'action': 'sent_to_finances',
            'user': 'system',
            'email': self.finances_email
        })
        self.save(update_fields=['audit_log'])
        return True
    
    def generate_pdf(self):
        """Genera el PDF de la factura."""
        # Implementar generación de PDF
        pass
    
    def generate_xml(self):
        """Genera el XML para facturación electrónica."""
        if not self.electronic_billing_enabled:
            return None
        
        # Implementar generación de XML CFDI
        pass
    
    def mark_as_paid(self):
        """Marca la factura como pagada."""
        self.status = 'paid'
        self.payment_date = timezone.now()
        self.save(update_fields=['status', 'payment_date'])
    
    def cancel(self, reason=""):
        """Cancela la factura."""
        self.status = 'cancelled'
        self.compliance_notes = f"Cancelada: {reason}"
        self.save(update_fields=['status', 'compliance_notes'])

class LineItem(models.Model):
    """Modelo para conceptos de factura (líneas de factura)."""
    
    # Relaciones
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='line_items')
    service = models.ForeignKey('Service', on_delete=models.CASCADE, related_name='line_items', null=True, blank=True)
    
    # Información del concepto
    description = models.TextField(help_text="Descripción del concepto")
    product_key = models.CharField(max_length=20, blank=True, help_text="Clave del producto/servicio SAT")
    unit_key = models.CharField(max_length=20, blank=True, help_text="Clave de unidad SAT")
    
    # Cantidades y precios
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1, help_text="Cantidad")
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, help_text="Precio unitario")
    
    # Montos
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Subtotal sin impuestos")
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Monto de impuestos")
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Monto de descuento")
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Total del concepto")
    
    # Impuestos
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=16, help_text="Tasa de impuesto (%)")
    tax_type = models.CharField(max_length=20, default='IVA', help_text="Tipo de impuesto")
    
    # Metadatos
    notes = models.TextField(blank=True, help_text="Notas adicionales")
    metadata = models.JSONField(default=dict, help_text="Datos adicionales")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Concepto de Factura"
        verbose_name_plural = "Conceptos de Factura"
        ordering = ['invoice', 'created_at']
        indexes = [
            models.Index(fields=['invoice']),
            models.Index(fields=['service']),
        ]

    def __str__(self):
        return f"{self.description} - {self.quantity} x {self.unit_price}"
    
    def save(self, *args, **kwargs):
        # Calcular montos si no están establecidos
        if not self.subtotal:
            self.subtotal = self.quantity * self.unit_price
        
        if not self.tax_amount:
            self.tax_amount = self.subtotal * (self.tax_rate / 100)
        
        if not self.total_amount:
            self.total_amount = self.subtotal + self.tax_amount - self.discount_amount
        
        super().save(*args, **kwargs)
    
    def calculate_totals(self):
        """Recalcula todos los totales del concepto."""
        self.subtotal = self.quantity * self.unit_price
        self.tax_amount = self.subtotal * (self.tax_rate / 100)
        self.total_amount = self.subtotal + self.tax_amount - self.discount_amount
        self.save(update_fields=['subtotal', 'tax_amount', 'total_amount'])

class Order(models.Model):
    """Modelo para órdenes de servicio (punto intermedio antes de facturar)."""
    
    ORDER_TYPE_CHOICES = [
        ('service', 'Servicio'),
        ('consulting', 'Consultoría'),
        ('recruitment', 'Reclutamiento'),
        ('assessment', 'Evaluación'),
        ('other', 'Otro'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Borrador'),
        ('pending', 'Pendiente'),
        ('approved', 'Aprobada'),
        ('in_progress', 'En Progreso'),
        ('completed', 'Completada'),
        ('cancelled', 'Cancelada'),
        ('invoiced', 'Facturada'),
    ]
    
    # Información básica
    order_number = models.CharField(max_length=100, unique=True, help_text="Número de orden")
    title = models.CharField(max_length=200, help_text="Título de la orden")
    description = models.TextField(help_text="Descripción detallada")
    order_type = models.CharField(max_length=20, choices=ORDER_TYPE_CHOICES, help_text="Tipo de orden")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Relaciones
    client = models.ForeignKey('Person', on_delete=models.CASCADE, related_name='orders', help_text="Cliente")
    business_unit = models.ForeignKey('BusinessUnit', on_delete=models.CASCADE, related_name='orders')
    service = models.ForeignKey('Service', on_delete=models.CASCADE, related_name='orders', null=True, blank=True)
    assigned_to = models.ForeignKey('Person', on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_orders', help_text="Persona asignada")
    
    # Fechas
    requested_date = models.DateTimeField(auto_now_add=True, help_text="Fecha de solicitud")
    due_date = models.DateTimeField(null=True, blank=True, help_text="Fecha de vencimiento")
    completed_date = models.DateTimeField(null=True, blank=True, help_text="Fecha de completado")
    
    # Montos
    estimated_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Monto estimado")
    actual_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Monto real")
    currency = models.CharField(max_length=3, default='MXN')
    
    # Configuración
    auto_invoice = models.BooleanField(default=True, help_text="¿Generar factura automáticamente al completar?")
    send_to_finances = models.BooleanField(default=True, help_text="¿Enviar a finanzas al completar?")
    
    # Metadatos
    requirements = models.JSONField(default=list, help_text="Requisitos específicos")
    deliverables = models.JSONField(default=list, help_text="Entregables esperados")
    notes = models.TextField(blank=True, help_text="Notas adicionales")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_orders')

    class Meta:
        verbose_name = "Orden de Servicio"
        verbose_name_plural = "Órdenes de Servicio"
        ordering = ['-requested_date']
        indexes = [
            models.Index(fields=['order_number']),
            models.Index(fields=['status']),
            models.Index(fields=['client']),
            models.Index(fields=['business_unit']),
            models.Index(fields=['requested_date']),
        ]

    def __str__(self):
        return f"Orden {self.order_number} - {self.title}"
    
    def save(self, *args, **kwargs):
        # Generar número de orden si no existe
        if not self.order_number:
            self.order_number = self.generate_order_number()
        
        super().save(*args, **kwargs)
    
    def generate_order_number(self):
        """Genera un número de orden único."""
        from datetime import datetime
        year = datetime.now().year
        month = datetime.now().month
        
        # Buscar el último número de orden del mes
        last_order = Order.objects.filter(
            order_number__startswith=f"O{year}{month:02d}"
        ).order_by('-order_number').first()
        
        if last_order:
            try:
                last_number = int(last_order.order_number[-4:])
                new_number = last_number + 1
            except ValueError:
                new_number = 1
        else:
            new_number = 1
        
        return f"O{year}{month:02d}{new_number:04d}"
    
    def approve(self):
        """Aprueba la orden."""
        self.status = 'approved'
        self.save(update_fields=['status'])
    
    def start_work(self):
        """Inicia el trabajo en la orden."""
        self.status = 'in_progress'
        self.save(update_fields=['status'])
    
    def complete(self, actual_amount=None):
        """Completa la orden."""
        self.status = 'completed'
        self.completed_date = timezone.now()
        
        if actual_amount is not None:
            self.actual_amount = actual_amount
        
        self.save(update_fields=['status', 'completed_date', 'actual_amount'])
        
        # Generar factura automáticamente si está configurado
        if self.auto_invoice:
            self.generate_invoice()
    
    def generate_invoice(self):
        """Genera una factura para esta orden."""
        from app.ats.pricing.services.billing_service import BillingService
        
        billing_service = BillingService()
        invoice = billing_service.create_invoice_from_order(self)
        return invoice
    
    def cancel(self, reason=""):
        """Cancela la orden."""
        self.status = 'cancelled'
        self.notes = f"{self.notes}\n\nCancelada: {reason}"
        self.save(update_fields=['status', 'notes'])
    
    def get_progress_percentage(self):
        """Calcula el porcentaje de progreso basado en el estado."""
        progress_map = {
            'draft': 0,
            'pending': 10,
            'approved': 25,
            'in_progress': 60,
            'completed': 100,
            'cancelled': 0,
            'invoiced': 100,
        }
        return progress_map.get(self.status, 0)

class LinkedInMessageTemplate(models.Model):
    """Modelo para plantillas de mensajes de LinkedIn.
    
    Este modelo está optimizado para crear mensajes estructurados y personalizados
    para LinkedIn, siguiendo las mejores prácticas de la plataforma para maximizar
    la tasa de respuesta y evitar ser marcado como spam.
    
    Los mensajes pueden incluir variables dinámicas como:
    - {name}: Nombre del destinatario
    - {company}: Empresa actual del destinatario
    - {skills}: Habilidades relevantes del destinatario
    - {job_count}: Número de ofertas de trabajo relevantes
    - {ai_insight}: Insight personalizado generado por IA
    - {position}: Posición actual del destinatario
    - {industry}: Industria del destinatario
    - {mutual_connections}: Conexiones en común
    - {personalized_note}: Nota personalizada basada en el perfil
    """
    name = models.CharField(max_length=200, help_text="Nombre descriptivo de la plantilla")
    template = models.TextField(help_text="Texto de la plantilla con variables entre llaves, ej: {name}")
    is_active = models.BooleanField(default=True, help_text="Indica si esta plantilla está activa para uso")
    
    # Opciones de personalización
    include_skills = models.BooleanField(default=False, help_text="Incluir habilidades relevantes del destinatario")
    include_job_count = models.BooleanField(default=False, help_text="Incluir número de ofertas relevantes")
    include_ai_insight = models.BooleanField(default=False, help_text="Incluir insight personalizado generado por IA")
    include_mutual_connections = models.BooleanField(default=False, help_text="Mencionar conexiones en común")
    include_personalized_note = models.BooleanField(default=False, help_text="Incluir nota personalizada basada en el perfil")
    
    # Metadatos
    target_audience = models.CharField(max_length=100, blank=True, null=True, help_text="Audiencia objetivo de esta plantilla")
    purpose = models.CharField(max_length=100, blank=True, null=True, 
                             choices=[
                                 ('recruitment', 'Reclutamiento'),
                                 ('networking', 'Networking'),
                                 ('sales', 'Ventas'),
                                 ('partnership', 'Alianzas'),
                                 ('other', 'Otro')
                             ],
                             help_text="Propósito principal de esta plantilla")
    
    # Estadísticas de rendimiento
    send_count = models.IntegerField(default=0, help_text="Número de veces que se ha enviado esta plantilla")
    response_count = models.IntegerField(default=0, help_text="Número de respuestas recibidas")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Plantilla de Mensaje LinkedIn"
        verbose_name_plural = "Plantillas de Mensajes LinkedIn"

    def __str__(self):
        return self.name

class LinkedInInvitationSchedule(models.Model):
    """Modelo para programación de invitaciones de LinkedIn."""
    template = models.ForeignKey(LinkedInMessageTemplate, on_delete=models.CASCADE)
    schedule_time = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Programación de Invitación LinkedIn"
        verbose_name_plural = "Programaciones de Invitaciones LinkedIn"

    def __str__(self):
        return f"{self.template.title} - {self.schedule_time}"

class EstadoPerfil(models.TextChoices):
    ACTIVO = 'activo', 'Activo'
    INACTIVO = 'inactivo', 'Inactivo'
    SUSPENDIDO = 'suspendido', 'Suspendido'

class TipoDocumento(models.TextChoices):
    RFC = 'rfc', 'RFC'
    CURP = 'curp', 'CURP'
    DNI = 'dni', 'DNI'
    PASAPORTE = 'pasaporte', 'Pasaporte'

class ChatSession(models.Model):
    """Modelo para sesiones de chat."""
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    status = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Sesión de Chat"
        verbose_name_plural = "Sesiones de Chat"

    def __str__(self):
        return f"{self.person} - {self.created_at}"

class ChatMessage(models.Model):
    """Modelo para mensajes de chat."""
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE)
    content = models.TextField()
    is_bot = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Mensaje de Chat"
        verbose_name_plural = "Mensajes de Chat"

    def __str__(self):
        return f"{self.session} - {self.created_at}"

class DocumentVerification(models.Model):
    """Modelo para verificación de documentos."""
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    document_type = models.CharField(max_length=50)
    document_number = models.CharField(max_length=50)
    document_front = models.ImageField(upload_to='documents/', null=True, blank=True)
    document_back = models.ImageField(upload_to='documents/', null=True, blank=True)
    selfie = models.ImageField(upload_to='selfies/', null=True, blank=True)
    status = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Verificación de Documento"
        verbose_name_plural = "Verificaciones de Documentos"

    def __str__(self):
        return f"{self.person} - {self.document_type}"

class JobSatisfaction(models.Model):
    """Modelo para almacenar información sobre la satisfacción laboral de una persona."""
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='job_satisfactions')
    survey_date = models.DateTimeField(auto_now_add=True)
    
    compensation_satisfaction = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], null=True, blank=True)
    work_life_balance = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], null=True, blank=True)
    growth_opportunities = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], null=True, blank=True)
    management_satisfaction = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], null=True, blank=True)
    peer_relationships = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], null=True, blank=True)
    job_security = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], null=True, blank=True)
    
    overall_satisfaction = models.FloatField(null=True, blank=True)
    
    retention_risk = models.FloatField(null=True, blank=True)  # 0-1, donde 1 es alto riesgo
    retention_factors = models.JSONField(default=dict, blank=True)  # Factores que afectan la retención
    recommendations = models.JSONField(default=dict, blank=True)  # Recomendaciones para mejorar
    
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Satisfacción laboral"
        verbose_name_plural = "Satisfacciones laborales"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=['person']),
            models.Index(fields=['survey_date']),
            models.Index(fields=['overall_satisfaction']),
            models.Index(fields=['retention_risk'])
        ]
        
    def __str__(self):
        return f"Satisfacción laboral de {self.person} - {self.survey_date}"
        
    def calculate_overall_satisfaction(self):
        scores = [
            self.compensation_satisfaction,
            self.work_life_balance,
            self.growth_opportunities,
            self.management_satisfaction,
            self.peer_relationships,
            self.job_security
        ]
        valid_scores = [s for s in scores if s is not None]
        if valid_scores:
            return sum(valid_scores) / len(valid_scores)
        return None
        
    def save(self, *args, **kwargs):
        self.overall_satisfaction = self.calculate_overall_satisfaction()
        super().save(*args, **kwargs)

class PerformanceReview(models.Model):
    """Modelo para evaluaciones de desempeño de colaboradores."""
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='performance_reviews')
    reviewer = models.ForeignKey(Person, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviews_given')
    
    review_date = models.DateTimeField()
    period_start = models.DateField()
    period_end = models.DateField()
    
    technical_skills = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], null=True, blank=True)
    communication = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], null=True, blank=True)
    teamwork = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], null=True, blank=True)
    leadership = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], null=True, blank=True)
    initiative = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], null=True, blank=True)
    adaptability = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], null=True, blank=True)
    goal_achievement = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], null=True, blank=True)
    
    overall_score = models.FloatField(null=True, blank=True)
    
    strengths = models.TextField(blank=True)
    areas_for_improvement = models.TextField(blank=True)
    development_plan = models.TextField(blank=True)
    
    STATUS_CHOICES = [
        ('draft', 'Borrador'),
        ('in_review', 'En revisión'),
        ('reviewed', 'Revisado'),
        ('acknowledged', 'Reconocido'),
        ('completed', 'Completado'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Evaluación de desempeño"
        verbose_name_plural = "Evaluaciones de desempeño"
        ordering = ["-review_date"]
        indexes = [
            models.Index(fields=['person']),
            models.Index(fields=['reviewer']),
            models.Index(fields=['review_date']),
            models.Index(fields=['status'])
        ]
        
    def __str__(self):
        return f"Evaluación de {self.person} - {self.review_date}"
        
    def calculate_overall_score(self):
        scores = [
            self.technical_skills,
            self.communication,
            self.teamwork,
            self.leadership,
            self.initiative,
            self.adaptability,
            self.goal_achievement
        ]
        valid_scores = [s for s in scores if s is not None]
        if valid_scores:
            return sum(valid_scores) / len(valid_scores)
        return None
        
    def save(self, *args, **kwargs):
        self.overall_score = self.calculate_overall_score()
        super().save(*args, **kwargs)

class Manager(models.Model):
    """Modelo para gestores/supervisores de personas."""
    person = models.OneToOneField(Person, on_delete=models.CASCADE, related_name='manager_profile')
    
    title = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    level = models.CharField(max_length=50, blank=True, null=True)  # Nivel jerárquico
    
    direct_reports = models.ManyToManyField(Person, related_name='managers', blank=True)
    
    MANAGEMENT_STYLES = [
        ('directive', 'Directivo'),
        ('coaching', 'Coaching'),
        ('supportive', 'De apoyo'),
        ('delegative', 'Delegativo'),
        ('participative', 'Participativo'),
        ('transformational', 'Transformacional'),
        ('transactional', 'Transaccional'),
        ('servant', 'Servicial'),
        ('laissez_faire', 'Laissez-faire'),
        ('democratic', 'Democrático')
    ]
    management_style = models.CharField(max_length=20, choices=MANAGEMENT_STYLES, blank=True, null=True)
    
    years_management_experience = models.PositiveIntegerField(default=0)
    strengths = models.TextField(blank=True)
    development_areas = models.TextField(blank=True)
    
    team_retention_rate = models.FloatField(null=True, blank=True)  # Porcentaje
    team_satisfaction_score = models.FloatField(null=True, blank=True)  # 0-5
    performance_score = models.FloatField(null=True, blank=True)  # 0-5
    
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Manager"
        verbose_name_plural = "Managers"
        indexes = [
            models.Index(fields=['person']),
            models.Index(fields=['department']),
            models.Index(fields=['management_style']),
            models.Index(fields=['team_retention_rate'])
        ]
        
    def __str__(self):
        return f"{self.person} - {self.title}"
        
    def calculate_team_metrics(self):
        """Calcula métricas del equipo basadas en datos de satisfacción y desempeño."""
        team_members = self.direct_reports.all()
        if not team_members:
            return
            
        # Calcular tasa de retención
        total_members = team_members.count()
        active_members = team_members.filter(job_satisfactions__isnull=False).count()
        if total_members > 0:
            self.team_retention_rate = (active_members / total_members) * 100
            
        # Calcular satisfacción promedio
        satisfaction_scores = []
        for member in team_members:
            latest_satisfaction = member.job_satisfactions.order_by('-survey_date').first()
            if latest_satisfaction and latest_satisfaction.overall_satisfaction:
                satisfaction_scores.append(latest_satisfaction.overall_satisfaction)
        if satisfaction_scores:
            self.team_satisfaction_score = sum(satisfaction_scores) / len(satisfaction_scores)
            
        # Calcular desempeño promedio
        performance_scores = []
        for member in team_members:
            latest_review = member.performance_reviews.order_by('-review_date').first()
            if latest_review and latest_review.overall_score:
                performance_scores.append(latest_review.overall_score)
        if performance_scores:
            self.performance_score = sum(performance_scores) / len(performance_scores)
            
        self.save()

class InterventionAction(models.Model):
    """Modelo para acciones de intervención de retención o desarrollo de talento."""
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='interventions')
    created_by = models.ForeignKey(Person, on_delete=models.SET_NULL, null=True, blank=True, related_name='interventions_created')
    
    ACTION_TYPES = [
        ('retention', 'Retención'),
        ('development', 'Desarrollo'),
        ('performance', 'Desempeño'),
        ('compensation', 'Compensación'),
        ('wellbeing', 'Bienestar'),
        ('career', 'Carrera'),
        ('recognition', 'Reconocimiento'),
        ('conflict', 'Resolución de conflicto'),
        ('other', 'Otro')
    ]
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    
    title = models.CharField(max_length=100)
    description = models.TextField()
    priority = models.CharField(max_length=10, choices=[
        ('low', 'Baja'),
        ('medium', 'Media'),
        ('high', 'Alta'),
        ('critical', 'Crítica')
    ], default='medium')
    
    created_date = models.DateTimeField(auto_now_add=True)
    scheduled_date = models.DateField(null=True, blank=True)
    completion_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('planned', 'Planificada'),
        ('in_progress', 'En progreso'),
        ('completed', 'Completada'),
        ('cancelled', 'Cancelada'),
        ('postponed', 'Pospuesta')
    ], default='planned')
    
    outcome = models.TextField(blank=True)
    effectiveness_rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], null=True, blank=True)
    follow_up_date = models.DateField(null=True, blank=True)
    follow_up_notes = models.TextField(blank=True)
    
    related_review = models.ForeignKey('PerformanceReview', on_delete=models.SET_NULL, null=True, blank=True, related_name='interventions')
    assigned_mentor = models.ForeignKey('Mentor', on_delete=models.SET_NULL, null=True, blank=True, related_name='mentor_interventions')
    
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.SET_NULL, null=True, blank=True)
    tags = models.JSONField(default=list, blank=True)  # Lista de etiquetas para categorizar
    
    class Meta:
        verbose_name = "Acción de intervención"
        verbose_name_plural = "Acciones de intervención"
        ordering = ["-created_date"]
        indexes = [
            models.Index(fields=['person']),
            models.Index(fields=['action_type']),
            models.Index(fields=['status']),
            models.Index(fields=['priority']),
            models.Index(fields=['scheduled_date'])
        ]
        
    def __str__(self):
        return f"{self.action_type} - {self.title} para {self.person}"
        
    def mark_as_completed(self, effectiveness_rating=None, outcome=None):
        """Marca la intervención como completada y registra su efectividad."""
        self.status = 'completed'
        self.completion_date = timezone.now().date()
        if effectiveness_rating is not None:
            self.effectiveness_rating = effectiveness_rating
        if outcome is not None:
            self.outcome = outcome
        self.save()

class Activity(models.Model):
    """Modelo para actividades y eventos relacionados con una persona."""
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='activities')
    
    ACTIVITY_TYPES = [
        ('login', 'Inicio de sesión'),
        ('logout', 'Cierre de sesión'),
        ('profile_update', 'Actualización de perfil'),
        ('application', 'Postulación'),
        ('interview', 'Entrevista'),
        ('assessment', 'Evaluación'),
        ('message', 'Mensaje'),
        ('document', 'Documento'),
        ('feedback', 'Retroalimentación'),
        ('other', 'Otro')
    ]
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    
    timestamp = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True)
    details = models.JSONField(default=dict, blank=True)  # Detalles adicionales en formato JSON
    
    related_entity_type = models.CharField(max_length=50, blank=True, null=True)  # Ej: 'vacante', 'mensaje', etc.
    related_entity_id = models.PositiveIntegerField(blank=True, null=True)  # ID de la entidad relacionada
    
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        verbose_name = "Actividad"
        verbose_name_plural = "Actividades"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=['person']),
            models.Index(fields=['activity_type']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['related_entity_type', 'related_entity_id'])
        ]
        
    def __str__(self):
        return f"{self.get_activity_type_display()} de {self.person} - {self.timestamp}"

class Team(models.Model):
    """Modelo para equipos."""
    name = models.CharField(max_length=100)
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Equipo"
        verbose_name_plural = "Equipos"

    def __str__(self):
        return self.name

class TeamMember(models.Model):
    """Modelo para miembros de equipo."""
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    role = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Miembro de Equipo"
        verbose_name_plural = "Miembros de Equipo"

    def __str__(self):
        return f"{self.team} - {self.person}"

class AnalyticsReport(models.Model):
    """Modelo para reportes analíticos."""
    title = models.CharField(max_length=200)
    content = models.JSONField()
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Reporte Analítico"
        verbose_name_plural = "Reportes Analíticos"

    def __str__(self):
        return self.name

class Contract(models.Model):
    """Modelo para contratos."""
    title = models.CharField(max_length=200)
    content = models.TextField()
    status = models.CharField(max_length=50, choices=CONTRATO_STATUS_CHOICES)
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Contrato"
        verbose_name_plural = "Contratos"

    def __str__(self):
        return self.name

class UserPermission(models.Model):
    """Modelo para permisos de usuario."""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    permission = models.CharField(max_length=50, choices=PERMISSION_CHOICES)
    business_unit = models.ForeignKey('BusinessUnit', on_delete=models.CASCADE, null=True, blank=True)
    division = models.ForeignKey('Division', on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Permiso de Usuario"
        verbose_name_plural = "Permisos de Usuario"

    def __str__(self):
        return f"{self.user} - {self.permission}"

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
    """
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='discount_coupons',
        help_text="Usuario al que se le asigna el cupón"
    )
    code = models.CharField(
        max_length=10, 
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
        'Proposal',
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
        """
        Validaciones adicionales del modelo.
        """
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
        """
        Sobrescritura del método save para incluir validaciones.
        """
        self.full_clean()
        super().save(*args, **kwargs)
    
    def is_valid(self):
        """
        Verifica si el cupón es válido para su uso.
        
        Returns:
            bool: True si el cupón es válido, False en caso contrario
        """
        return not self.is_used and self.expiration_date > timezone.now()
    
    def mark_as_used(self):
        """
        Marca el cupón como utilizado.
        
        Returns:
            bool: True si se pudo marcar como usado, False si ya estaba usado
        """
        if not self.is_used:
            self.is_used = True
            self.used_at = timezone.now()
            self.save(update_fields=['is_used', 'used_at'])
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
        if self.is_used:
            return "Usado"
        if self.expiration_date <= timezone.now():
            return "Expirado"
        return "Disponible"
    
    @classmethod
    def generate_coupon_code(cls, length=10):
        """
        Genera un código de cupón único.
        
        Args:
            length: Longitud del código (por defecto 10 caracteres)
            
        Returns:
            str: Código de cupón único
        """
        import random
        import string
        
        while True:
            # Generar un código aleatorio con letras mayúsculas y dígitos
            code = ''.join(
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
        description=None
    ):
        """
        Método de conveniencia para crear un nuevo cupón.
        
        Args:
            user: Usuario al que se le asigna el cupón
            discount_percentage: Porcentaje de descuento (1-100%)
            validity_hours: Horas de validez del cupón
            proposal: Propuesta asociada (opcional)
            description: Descripción del cupón (opcional)
            
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
            description=description
        )
    
    def __str__(self):
        return (
            f"Cupón {self.code} - {self.discount_percentage}% - "
            f"{self.get_status_display()} - "
            f"Vence: {self.expiration_date.strftime('%Y-%m-%d %H:%M')}"
        )

    def get_time_remaining(self):
        """
        Obtiene el tiempo restante hasta la expiración del cupón.
        
        Returns:
            str: Tiempo restante en formato legible
        """
        if self.is_used:
            return "Cupón ya utilizado"
        
        if self.expiration_date <= timezone.now():
            return "Cupón expirado"
        
        remaining = self.expiration_date - timezone.now()
        
        if remaining.days > 0:
            return f"{remaining.days} días"
        elif remaining.seconds > 3600:
            hours = remaining.seconds // 3600
            return f"{hours} horas"
        elif remaining.seconds > 60:
            minutes = remaining.seconds // 60
            return f"{minutes} minutos"
        else:
            return "Menos de 1 minuto"
    
    def __str__(self):
        return (
            f"Cupón {self.code} - {self.discount_percentage}% - "
            f"{self.get_status_display()} - "
            f"Vence: {self.expiration_date.strftime('%Y-%m-%d %H:%M')}"
        )

class Coupon(models.Model):
    """Modelo para cupones."""
    code = models.CharField(max_length=50, unique=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Cupón"
        verbose_name_plural = "Cupones"

    def __str__(self):
        return self.code


class Coupons(models.Model):
    """Modelo avanzado para cupones de descuento con soporte para monto fijo y porcentaje."""
    # Información básica
    code = models.CharField(
        max_length=50, 
        unique=True,
        verbose_name="Código",
        help_text="Código único del cupón"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Descripción",
        help_text="Descripción del cupón"
    )
    
    # Tipo y valor del cupón
    TYPE_CHOICES = [
        ('fixed', 'Monto Fijo ($)'),
        ('percentage', 'Porcentaje (%)')
    ]
    type = models.CharField(
        max_length=20, 
        choices=TYPE_CHOICES,
        default='percentage',
        verbose_name="Tipo",
        help_text="Tipo de descuento: monto fijo o porcentaje"
    )
    value = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Valor",
        help_text="Valor del descuento (monto o porcentaje según el tipo)"
    )
    
    # Validez y uso
    valid_until = models.DateTimeField(
        verbose_name="Válido hasta",
        help_text="Fecha de expiración del cupón"
    )
    max_uses = models.PositiveIntegerField(
        default=1,
        verbose_name="Usos máximos",
        help_text="Número máximo de veces que se puede usar este cupón"
    )
    current_uses = models.PositiveIntegerField(
        default=0,
        verbose_name="Usos actuales",
        help_text="Número de veces que se ha usado este cupón"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Activo",
        help_text="Indica si el cupón está activo"
    )
    
    # Relaciones
    bu = models.ForeignKey(
        BusinessUnit, 
        on_delete=models.CASCADE,
        verbose_name="Unidad de negocio",
        related_name="coupons"
    )
    
    # Campos para segmentación y campañas
    campaign = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        verbose_name="Campaña",
        help_text="Campaña asociada al cupón"
    )
    bundle = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        verbose_name="Bundle",
        help_text="Bundle o paquete asociado al cupón"
    )
    
    # Campos de auditoría
    created_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name="Creado"
    )
    last_updated = models.DateTimeField(
        auto_now=True, 
        verbose_name="Última actualización"
    )
    
    class Meta:
        verbose_name = "Cupón de Pricing"
        verbose_name_plural = "Cupones de Pricing"
        ordering = ['-created_at', 'code']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['valid_until']),
            models.Index(fields=['is_active']),
            models.Index(fields=['bu', 'is_active']),
            models.Index(fields=['campaign']),
            models.Index(fields=['bundle']),
        ]
    
    def __str__(self):
        return f"{self.code} - {self.get_value_display()}"
    
    def get_value_display(self):
        """Obtiene el valor del cupón en formato legible."""
        if self.type == 'fixed':
            return f"${self.value}"
        return f"{self.value}%"
    
    def is_valid(self):
        """Verifica si el cupón es válido para su uso."""
        now = timezone.now()
        return (
            self.is_active and 
            self.valid_until > now and 
            (self.current_uses < self.max_uses)
        )
    
    def calculate_discount(self, amount):
        """Calcula el descuento para un monto dado."""
        if not self.is_valid():
            return 0
            
        if self.type == 'fixed':
            return min(self.value, amount)  # No descontar más que el monto total
        else:  # percentage
            return (amount * self.value) / 100
    
    def apply_discount(self, amount):
        """Aplica el descuento y aumenta el contador de usos."""
        if not self.is_valid():
            return amount
            
        discount = self.calculate_discount(amount)
        self.current_uses += 1
        self.save(update_fields=['current_uses', 'last_updated'])
        
        return max(amount - discount, 0)  # No permitir montos negativos

class TalentAnalysisRequest(models.Model):
    """Modelo para solicitudes de análisis de talento."""
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    status = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Solicitud de Análisis de Talento"
        verbose_name_plural = "Solicitudes de Análisis de Talento"

    def __str__(self):
        return f"{self.person} - {self.status}"

class ServiceCalculation(models.Model):
    """Modelo para cálculos de servicios y precios."""
    
    service = models.ForeignKey(
        'Service',
        on_delete=models.CASCADE,
        related_name='calculations',
        help_text="Servicio asociado"
    )
    
    base_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Precio base del servicio"
    )
    
    calculation_type = models.CharField(
        max_length=50,
        choices=[
            ('FIXED', 'Precio Fijo'),
            ('HOURLY', 'Por Hora'),
            ('DAILY', 'Por Día'),
            ('MONTHLY', 'Por Mes'),
            ('PROJECT', 'Por Proyecto'),
            ('PERCENTAGE', 'Porcentaje')
        ],
        help_text="Tipo de cálculo de precio"
    )
    
    variables = models.JSONField(
        default=dict,
        help_text="Variables utilizadas en el cálculo"
    )
    
    formula = models.TextField(
        help_text="Fórmula de cálculo"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Cálculo de Servicio"
        verbose_name_plural = "Cálculos de Servicios"
        
    def __str__(self):
        return f"{self.service.name} - {self.get_calculation_type_display()}"

class PaymentSchedule(models.Model):
    """Modelo para programación de pagos."""
    
    service = models.ForeignKey(
        'Service',
        on_delete=models.CASCADE,
        related_name='payment_schedules',
        help_text="Servicio asociado"
    )
    
    client = models.ForeignKey(
        'Person',
        on_delete=models.CASCADE,
        related_name='payment_schedules',
        help_text="Cliente"
    )
    
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Monto total a pagar"
    )
    
    schedule_type = models.CharField(
        max_length=20,
        choices=[
            ('SINGLE', 'Pago Único'),
            ('INSTALLMENTS', 'Pagos Parciales'),
            ('RECURRING', 'Pago Recurrente')
        ],
        help_text="Tipo de programación"
    )
    
    start_date = models.DateField(
        help_text="Fecha de inicio de pagos"
    )
    
    end_date = models.DateField(
        null=True,
        blank=True,
        help_text="Fecha de finalización (si aplica)"
    )
    
    frequency = models.CharField(
        max_length=20,
        choices=[
            ('DAILY', 'Diario'),
            ('WEEKLY', 'Semanal'),
            ('MONTHLY', 'Mensual'),
            ('QUARTERLY', 'Trimestral'),
            ('YEARLY', 'Anual')
        ],
        help_text="Frecuencia de pagos"
    )
    
    status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pendiente'),
            ('ACTIVE', 'Activo'),
            ('COMPLETED', 'Completado'),
            ('CANCELLED', 'Cancelado')
        ],
        default='PENDING',
        help_text="Estado de la programación"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Programación de Pago"
        verbose_name_plural = "Programaciones de Pagos"
        
    def __str__(self):
        return f"{self.client.nombre} - {self.service.name} ({self.get_schedule_type_display()})"

class PaymentNotification(models.Model):
    """Modelo para notificaciones de pago."""
    
    payment = models.ForeignKey(
        'Payment',
        on_delete=models.CASCADE,
        related_name='notifications',
        help_text="Pago asociado"
    )
    
    notification_type = models.CharField(
        max_length=20,
        choices=[
            ('DUE', 'Pago Próximo'),
            ('OVERDUE', 'Pago Vencido'),
            ('PAID', 'Pago Realizado'),
            ('FAILED', 'Pago Fallido'),
            ('REFUNDED', 'Pago Reembolsado')
        ],
        help_text="Tipo de notificación"
    )
    
    recipient = models.ForeignKey(
        'Person',
        on_delete=models.CASCADE,
        related_name='payment_notifications',
        help_text="Destinatario de la notificación"
    )
    
    message = models.TextField(
        help_text="Mensaje de la notificación"
    )
    
    sent_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha y hora de envío"
    )
    
    status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pendiente'),
            ('SENT', 'Enviado'),
            ('FAILED', 'Fallido'),
            ('READ', 'Leído')
        ],
        default='PENDING',
        help_text="Estado de la notificación"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Notificación de Pago"
        verbose_name_plural = "Notificaciones de Pagos"
        
    def __str__(self):
        return f"{self.get_notification_type_display()} - {self.payment}"

class Payment(models.Model):
    """Modelo para pagos."""
    
    schedule = models.ForeignKey(
        PaymentSchedule,
        on_delete=models.CASCADE,
        related_name='payments',
        help_text="Programación de pago asociada"
    )
    
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Monto del pago"
    )
    
    due_date = models.DateField(
        help_text="Fecha de vencimiento"
    )
    
    payment_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha y hora del pago"
    )
    
    payment_method = models.CharField(
        max_length=20,
        choices=[
            ('CASH', 'Efectivo'),
            ('CARD', 'Tarjeta'),
            ('TRANSFER', 'Transferencia'),
            ('CHECK', 'Cheque'),
            ('CRYPTO', 'Criptomoneda')
        ],
        help_text="Método de pago"
    )
    
    status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pendiente'),
            ('PAID', 'Pagado'),
            ('OVERDUE', 'Vencido'),
            ('FAILED', 'Fallido'),
            ('REFUNDED', 'Reembolsado')
        ],
        default='PENDING',
        help_text="Estado del pago"
    )
    
    transaction_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="ID de la transacción"
    )
    
    notes = models.TextField(
        blank=True,
        help_text="Notas adicionales"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Pago"
        verbose_name_plural = "Pagos"
        
    def __str__(self):
        return f"{self.schedule.client.nombre} - {self.amount} ({self.get_status_display()})"

class PremiumAddon(models.Model):
    """Modelo para addons premium."""
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Addon Premium"
        verbose_name_plural = "Addons Premium"

    def __str__(self):
        return self.name

class PricingBaseline(models.Model):
    """Modelo para precios base."""
    service_type = models.CharField(max_length=100)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Precio Base"
        verbose_name_plural = "Precios Base"

    def __str__(self):
        return f"{self.service_type} - {self.base_price}"

class PaymentMilestone(models.Model):
    """Modelo para hitos de pago."""
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()
    status = models.CharField(max_length=50, choices=PAYMENT_STATUS_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Hito de Pago"
        verbose_name_plural = "Hitos de Pago"

    def __str__(self):
        return f"{self.contract} - {self.amount}"

class ConfiguracionBU(models.Model):
    """Modelo para configuración de Business Units."""
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE)
    config = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuración de BU"
        verbose_name_plural = "Configuraciones de BU"

    def __str__(self):
        return f"{self.business_unit} - {self.created_at}"

class Reference(models.Model):
    """
    Modelo para gestionar referencias laborales de candidatos.
    """
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('in_progress', 'En Progreso'),
        ('completed', 'Completada'),
        ('expired', 'Expirada'),
        ('declined', 'Rechazada')
    ]

    # Relaciones
    candidate = models.ForeignKey(
        'Person',
        on_delete=models.CASCADE,
        related_name='references_received',
        help_text="Persona que está siendo referenciada"
    )
    reference = models.ForeignKey(
        'Person',
        on_delete=models.PROTECT,
        related_name='references_given',
        help_text="Persona que proporciona la referencia"
    )
    
    # Información básica
    relationship = models.CharField(
        max_length=100,
        help_text="Relación laboral (ej: 'Jefe Directo', 'Colega', 'Subordinado')"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text="Estado actual de la referencia"
    )
    
    # Metadatos
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Datos adicionales como respuestas del formulario, análisis, etc."
    )
    feedback = models.TextField(
        blank=True,
        null=True,
        help_text="Comentarios adicionales"
    )
    
    # Fechas importantes
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    response_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha en que se completó la referencia"
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha de expiración de la solicitud"
    )
    
    class Meta:
        verbose_name = "Referencia"
        verbose_name_plural = "Referencias"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['candidate']),
            models.Index(fields=['reference']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at'])
        ]
        
    def __str__(self):
        return f"Referencia de {self.reference} para {self.candidate}"
        
    def save(self, *args, **kwargs):
        # Si se está completando la referencia, establecer la fecha de respuesta
        if self.status == 'completed' and not self.response_date:
            self.response_date = timezone.now()
        super().save(*args, **kwargs)
        
    def is_expired(self):
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False
        
    def get_absolute_url(self):
        return f"/references/{self.id}/"
        
    def get_responses(self):
        return self.responses.all()
        
    def get_analysis(self):
        return self.metadata.get('analysis', {})
        
    def get_verification_status(self):
        return self.metadata.get('verification_status', 'pending')
        
    def get_score(self):
        return self.metadata.get('score', 0)
        
    def get_competencies(self):
        return self.metadata.get('competencies', [])
        
    def get_insights(self):
        return self.metadata.get('insights', {})

class ReferenceResponse(models.Model):
    """
    Modelo para almacenar respuestas individuales a preguntas de referencia.
    """
    reference = models.ForeignKey(
        'Reference',
        on_delete=models.CASCADE,
        related_name='responses',
        help_text="Referencia a la que pertenece esta respuesta"
    )
    
    question_id = models.CharField(
        max_length=100,
        help_text="Identificador único de la pregunta"
    )
    
    question_text = models.TextField(
        help_text="Texto completo de la pregunta"
    )
    
    response_type = models.CharField(
        max_length=50,
        default='text',
        help_text="Tipo de respuesta (text, number, select, multi_select, rating, etc.)"
    )
    
    response_value = models.JSONField(
        help_text="Valor de la respuesta (puede ser texto, número, lista, etc.)"
    )
    
    analysis = models.JSONField(
        default=dict,
        blank=True,
        help_text="Análisis de la respuesta (sentimiento, temas clave, etc.)"
    )
    
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Metadatos adicionales de la respuesta"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Respuesta de Referencia"
        verbose_name_plural = "Respuestas de Referencia"
        ordering = ['reference', 'question_id']
        unique_together = ['reference', 'question_id']
        
    def __str__(self):
        return f"Respuesta de {self.reference} - {self.question_id}"
        
    def get_response_display(self):
        if self.response_type == 'text':
            return str(self.response_value)
        elif self.response_type == 'number':
            return str(self.response_value)
        elif self.response_type == 'select':
            return str(self.response_value)
        elif self.response_type == 'multi_select':
            return ', '.join(str(x) for x in self.response_value)
        elif self.response_type == 'rating':
            return f"{self.response_value}/5"
        return str(self.response_value)

class SuccessionReadinessAssessment(models.Model):
    """Modelo para evaluar la preparación de un candidato para roles de sucesión."""
    
    candidate = models.ForeignKey(
        'Person',
        on_delete=models.CASCADE,
        related_name='succession_assessments',
        help_text="Candidato evaluado"
    )
    
    target_position = models.CharField(
        max_length=100,
        help_text="Posición objetivo para la sucesión"
    )
    
    readiness_score = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Puntuación general de preparación (0-100)"
    )
    
    technical_readiness = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Preparación técnica (0-100)"
    )
    
    leadership_readiness = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Preparación para liderazgo (0-100)"
    )
    
    cultural_fit = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Ajuste cultural (0-100)"
    )
    
    development_areas = models.JSONField(
        default=list,
        help_text="Áreas de desarrollo identificadas"
    )
    
    risk_factors = models.JSONField(
        default=dict,
        help_text="Factores de riesgo identificados"
    )
    
    recommendations = models.TextField(
        blank=True,
        null=True,
        help_text="Recomendaciones para el desarrollo"
    )
    
    assessed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='conducted_assessments',
        help_text="Usuario que realizó la evaluación"
    )
    
    assessment_date = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Evaluación de Preparación"
        verbose_name_plural = "Evaluaciones de Preparación"
        ordering = ['-assessment_date']
        
    def __str__(self):
        return f"Evaluación de {self.candidate} para {self.target_position}"
        
    def save(self, *args, **kwargs):
        # Calcular puntuación general si no está establecida
        if not self.readiness_score:
            self.readiness_score = (
                self.technical_readiness * 0.4 +
                self.leadership_readiness * 0.4 +
                self.cultural_fit * 0.2
            )
        super().save(*args, **kwargs)

@receiver(post_save, sender=SuccessionReadinessAssessment)
def update_candidate_status(sender, instance, created, **kwargs):
    """Actualiza el estado del candidato cuando se crea una nueva evaluación."""
    if created:
        candidate = instance.candidate
        if instance.readiness_score >= 80:
            candidate.metadata['succession_status'] = 'ready'
        elif instance.readiness_score >= 60:
            candidate.metadata['succession_status'] = 'developing'
        else:
            candidate.metadata['succession_status'] = 'needs_development'
        candidate.save()

# Tipos de mentoría
MENTORING_TYPE_CHOICES = [
    ('CAREER', 'Carrera'),
    ('TECHNICAL', 'Habilidades técnicas'),
    ('LEADERSHIP', 'Liderazgo'),
    ('ENTREPRENEURSHIP', 'Emprendimiento'),
    ('WORK_LIFE', 'Equilibrio vida-trabajo'),
    ('NETWORKING', 'Networking')
]

# Estados de sesión de mentoría
MENTORING_SESSION_STATUS_CHOICES = [
    ('SCHEDULED', 'Programada'),
    ('COMPLETED', 'Completada'),
    ('CANCELLED', 'Cancelada'),
    ('IN_PROGRESS', 'En Progreso')
]

class Mentor(models.Model):
    """Modelo para profesionales que dan mentorías a otros.
    
    Un Mentor es una Person vinculada a una Company que ofrece orientación
    y apoyo a otros profesionales (mentees) basado en su experiencia.
    """
    person = models.OneToOneField(
        'Person',
        on_delete=models.CASCADE,
        related_name='mentor_profile',
        help_text="Persona que actúa como mentor"
    )
    
    company = models.ForeignKey(
        'Company',
        on_delete=models.CASCADE,
        related_name='mentors',
        help_text="Empresa a la que pertenece el mentor"
    )
    
    specialty = models.CharField(
        max_length=100,
        help_text="Especialidad principal del mentor"
    )
    
    years_experience = models.PositiveIntegerField(
        default=0,
        help_text="Años de experiencia profesional"
    )
    
    rating = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0), MaxValueValidator(5.0)],
        help_text="Puntuación promedio (0-5)"
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="¿El mentor está activo y disponible?"
    )
    
    mentoring_types = ArrayField(
        models.CharField(max_length=20, choices=MENTORING_TYPE_CHOICES),
        default=list,
        help_text="Tipos de mentoría que ofrece"
    )
    
    expertise_areas = ArrayField(
        models.CharField(max_length=100),
        default=list,
        help_text="Áreas de expertise específicas"
    )
    
    # Área de descripción y estilo
    bio = models.TextField(
        blank=True,
        help_text="Biografía y experiencia relevante"
    )
    
    teaching_style = models.CharField(
        max_length=50,
        default="Balanced",
        help_text="Estilo de enseñanza predominante"
    )
    
    personality_type = models.CharField(
        max_length=50,
        default="Analytical",
        help_text="Tipo de personalidad predominante"
    )
    
    # Disponibilidad y preferencias
    availability = models.JSONField(
        default=dict,
        help_text="Disponibilidad horaria del mentor"
    )
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Recomendador (debe ser de la misma organización)
    recommended_by = models.ForeignKey(
        'Person',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='mentor_recommendations',
        help_text="Persona que recomendó al mentor (debe ser de la misma organización)"
    )
    
    class Meta:
        verbose_name = "Mentor"
        verbose_name_plural = "Mentores"
        indexes = [
            models.Index(fields=['person']),
            models.Index(fields=['company']),
            models.Index(fields=['is_active']),
            models.Index(fields=['rating'])
        ]
    
    def __str__(self):
        return f"Mentor: {self.person} ({self.specialty})"
    
    def get_skills(self):
        """Obtiene las habilidades del mentor."""
        return self.mentor_skills.all()
    
    def get_sessions(self):
        """Obtiene las sesiones del mentor."""
        return self.mentor_sessions.all()
    
    def to_dict(self):
        """Convierte el objeto a diccionario para API."""
        return {
            'id': self.id,
            'name': str(self.person),
            'specialty': self.specialty,
            'years_experience': self.years_experience,
            'rating': self.rating,
            'is_active': self.is_active,
            'mentoring_types': self.mentoring_types,
            'expertise_areas': self.expertise_areas,
            'teaching_style': self.teaching_style,
            'personality_type': self.personality_type
        }

class MentorSkill(models.Model):
    """Modelo para habilidades específicas de un mentor.
    
    Representa una habilidad que posee un mentor, con su nivel de dominio
    y años de experiencia en esa habilidad específica.
    """
    mentor = models.ForeignKey(
        'Mentor',
        on_delete=models.CASCADE,
        related_name='mentor_skills',
        help_text="Mentor que posee esta habilidad"
    )
    
    skill = models.ForeignKey(
        'Skill',
        on_delete=models.CASCADE,
        related_name='mentor_skills',
        help_text="Habilidad específica"
    )
    
    proficiency_level = models.PositiveIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Nivel de dominio (0-100)"
    )
    
    years = models.PositiveIntegerField(
        default=0,
        help_text="Años de experiencia con esta habilidad"
    )
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Habilidad de Mentor"
        verbose_name_plural = "Habilidades de Mentores"
        unique_together = ['mentor', 'skill']
        indexes = [
            models.Index(fields=['mentor']),
            models.Index(fields=['skill']),
            models.Index(fields=['proficiency_level'])
        ]
    
    def __str__(self):
        return f"{self.skill} ({self.proficiency_level}%)"
    
    def to_dict(self):
        """Convierte el objeto a diccionario para API."""
        return {
            'id': self.id,
            'name': str(self.skill),
            'level': self.proficiency_level,
            'years': self.years
        }

class MentorSession(models.Model):
    """Modelo para sesiones de mentoría.
    
    Representa una sesión programada o completada entre un mentor y un mentee,
    con información sobre objetivos, resultados y retroalimentación.
    """
    mentor = models.ForeignKey(
        'Mentor',
        on_delete=models.CASCADE,
        related_name='mentor_sessions',
        help_text="Mentor que imparte la sesión"
    )
    
    mentee = models.ForeignKey(
        'Person',
        on_delete=models.CASCADE,
        related_name='mentee_sessions',
        help_text="Persona que recibe la mentoría"
    )
    
    scheduled_date = models.DateTimeField(
        help_text="Fecha y hora programada para la sesión"
    )
    
    duration = models.PositiveIntegerField(
        default=60,
        help_text="Duración en minutos"
    )
    
    status = models.CharField(
        max_length=20,
        choices=MENTORING_SESSION_STATUS_CHOICES,
        default='SCHEDULED',
        help_text="Estado actual de la sesión"
    )
    
    goal = models.CharField(
        max_length=255,
        help_text="Objetivo principal de la sesión"
    )
    
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Notas previas o agenda de la sesión"
    )
    
    # Campos para sesiones completadas
    completed_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha y hora real de finalización"
    )
    
    rating = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        help_text="Valoración de la sesión (0-5)"
    )
    
    feedback = models.TextField(
        blank=True,
        help_text="Retroalimentación sobre la sesión"
    )
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Sesión de Mentoría"
        verbose_name_plural = "Sesiones de Mentoría"
        indexes = [
            models.Index(fields=['mentor']),
            models.Index(fields=['mentee']),
            models.Index(fields=['scheduled_date']),
            models.Index(fields=['status'])
        ]
        ordering = ['-scheduled_date']
    
    def __str__(self):
        return f"Sesión: {self.mentor.person} - {self.mentee} ({self.scheduled_date.strftime('%Y-%m-%d')})"
    
    def to_dict(self):
        """Convierte el objeto a diccionario para API."""
        return {
            'id': self.id,
            'mentor_id': self.mentor.id,
            'mentee_id': self.mentee.id,
            'scheduled_date': self.scheduled_date.isoformat(),
            'duration': self.duration,
            'status': self.status,
            'goal': self.goal,
            'notes': self.notes,
            'completed_date': self.completed_date.isoformat() if self.completed_date else None,
            'rating': self.rating,
            'feedback': self.feedback
        }
    
    def mark_as_completed(self, rating=None, feedback=None):
        """Marca la sesión como completada con retroalimentación opcional."""
        self.status = 'COMPLETED'
        self.completed_date = timezone.now()
        if rating is not None:
            self.rating = rating
        if feedback is not None:
            self.feedback = feedback
        self.save()

# CustomUser moved to app/ats/accounts/models.py to avoid conflicts

class GenerationalProfile(models.Model):
    """Perfil generacional que analiza características según la generación del usuario."""
    
    GENERATION_CHOICES = [
        ('BB', 'Baby Boomers'),
        ('X', 'Generación X'),
        ('Y', 'Millennials'),
        ('Z', 'Generación Z'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    generation = models.CharField(max_length=2, choices=GENERATION_CHOICES)
    birth_year = models.IntegerField()
    
    # Preferencias Laborales
    work_life_balance_importance = models.IntegerField(default=0)  # 0-100
    tech_adoption_level = models.IntegerField(default=0)  # 0-100
    remote_work_preference = models.IntegerField(default=0)  # 0-100
    learning_style = models.CharField(max_length=50)
    
    # Valores y Expectativas
    career_growth_importance = models.IntegerField(default=0)  # 0-100
    social_impact_importance = models.IntegerField(default=0)  # 0-100
    financial_security_importance = models.IntegerField(default=0)  # 0-100
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Perfil Generacional"
        verbose_name_plural = "Perfiles Generacionales"
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['generation']),
            models.Index(fields=['birth_year'])
        ]
    
    def __str__(self):
        return f"Perfil Generacional de {self.user.username}"

class MotivationalProfile(models.Model):
    """Perfil motivacional que analiza factores intrínsecos y extrínsecos de motivación."""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    # Motivadores Intrínsecos
    autonomy_need = models.IntegerField(default=0)  # 0-100
    mastery_need = models.IntegerField(default=0)  # 0-100
    purpose_need = models.IntegerField(default=0)  # 0-100
    
    # Motivadores Extrínsecos
    recognition_importance = models.IntegerField(default=0)  # 0-100
    compensation_importance = models.IntegerField(default=0)  # 0-100
    status_importance = models.IntegerField(default=0)  # 0-100
    
    # Preferencias de Liderazgo
    leadership_style_preference = models.CharField(max_length=50)
    feedback_frequency_preference = models.CharField(max_length=50)
    decision_making_preference = models.CharField(max_length=50)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Perfil Motivacional"
        verbose_name_plural = "Perfiles Motivacionales"
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['leadership_style_preference'])
        ]
    
    def __str__(self):
        return f"Perfil Motivacional de {self.user.username}"

class CareerAspiration(models.Model):
    """Aspiraciones de carrera del usuario, incluyendo objetivos y preferencias."""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Objetivos de Carrera
    short_term_goal = models.TextField()
    long_term_goal = models.TextField()
    desired_position = models.CharField(max_length=100)
    desired_industry = models.CharField(max_length=100)
    
    # Preferencias de Desarrollo
    preferred_learning_methods = models.JSONField()
    desired_skills = models.JSONField()
    work_environment_preferences = models.JSONField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Aspiración de Carrera"
        verbose_name_plural = "Aspiraciones de Carrera"
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['desired_position']),
            models.Index(fields=['desired_industry'])
        ]
    
    def __str__(self):
        return f"Aspiraciones de {self.user.username}"

class WorkStylePreference(models.Model):
    """Preferencias de estilo de trabajo del usuario."""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    # Estilo de Trabajo
    collaboration_preference = models.IntegerField(default=0)  # 0-100
    independence_preference = models.IntegerField(default=0)  # 0-100
    structure_preference = models.IntegerField(default=0)  # 0-100
    
    # Comunicación
    communication_style = models.CharField(max_length=50)
    feedback_reception = models.CharField(max_length=50)
    conflict_resolution_style = models.CharField(max_length=50)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Preferencia de Estilo de Trabajo"
        verbose_name_plural = "Preferencias de Estilo de Trabajo"
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['communication_style'])
        ]
    
    def __str__(self):
        return f"Estilo de Trabajo de {self.user.username}"

class CulturalAlignment(models.Model):
    """Alineación cultural del usuario con la organización."""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    # Valores Organizacionales
    company_values_alignment = models.JSONField()
    team_culture_preference = models.JSONField()
    organizational_structure_preference = models.JSONField()
    
    # Adaptabilidad Cultural
    cultural_flexibility = models.IntegerField(default=0)  # 0-100
    change_adaptability = models.IntegerField(default=0)  # 0-100
    diversity_embracement = models.IntegerField(default=0)  # 0-100
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Alineación Cultural"
        verbose_name_plural = "Alineaciones Culturales"
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['cultural_flexibility'])
        ]
    
    def __str__(self):
        return f"Alineación Cultural de {self.user.username}"

class VerificationService(models.Model):
    """Modelo para servicios de verificación."""
    name = models.CharField(max_length=100)
    description = models.TextField()
    service_type = models.CharField(max_length=50, choices=[
        ('identity', 'Identidad'),
        ('background', 'Antecedentes'),
        ('education', 'Educación'),
        ('employment', 'Empleo'),
        ('other', 'Otro')
    ])
    provider = models.CharField(max_length=100)
    api_endpoint = models.URLField()
    api_key = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    additional_config = models.JSONField(default=dict, help_text="Configuración adicional")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Servicio de Verificación"
        verbose_name_plural = "Servicios de Verificación"
        ordering = ['name']
        
    def __str__(self):
        return self.name

class VerificationAddon(models.Model):
    """Modelo para complementos de verificación."""
    service = models.ForeignKey(VerificationService, on_delete=models.CASCADE, related_name='addons')
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration = models.PositiveIntegerField(help_text="Duración en días")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Complemento de Verificación"
        verbose_name_plural = "Complementos de Verificación"
        ordering = ['service', 'name']
        
    def __str__(self):
        return f"{self.service} - {self.name}"

class OpportunityVerificationPackage(models.Model):
    """Modelo para paquetes de verificación de oportunidades."""
    opportunity = models.ForeignKey('Opportunity', on_delete=models.CASCADE, related_name='verification_packages')
    service = models.ForeignKey(VerificationService, on_delete=models.CASCADE, related_name='packages')
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Paquete de Verificación"
        verbose_name_plural = "Paquetes de Verificación"
        unique_together = ['opportunity', 'service']
        
    def __str__(self):
        return f"{self.opportunity} - {self.service}"

class PackageAddonDetail(models.Model):
    """Modelo para detalles de complementos en paquetes de verificación."""
    package = models.ForeignKey(OpportunityVerificationPackage, on_delete=models.CASCADE, related_name='addon_details')
    addon = models.ForeignKey(VerificationAddon, on_delete=models.CASCADE, related_name='package_details')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_included = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Detalle de Complemento"
        verbose_name_plural = "Detalles de Complementos"
        unique_together = ['package', 'addon']
        
    def __str__(self):
        return f"{self.package} - {self.addon}"

class CandidateVerification(models.Model):
    """Modelo para verificaciones de candidatos."""
    candidate = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='verifications')
    package = models.ForeignKey(OpportunityVerificationPackage, on_delete=models.CASCADE, related_name='candidate_verifications')
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pendiente'),
        ('in_progress', 'En progreso'),
        ('completed', 'Completado'),
        ('failed', 'Fallido')
    ], default='pending')
    results = models.JSONField(default=dict, help_text="Resultados de la verificación")
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Verificación de Candidato"
        verbose_name_plural = "Verificaciones de Candidatos"
        ordering = ['-started_at']
        
    def __str__(self):
        return f"{self.candidate} - {self.package}"

class CandidateServiceResult(models.Model):
    """Modelo para resultados de servicios de verificación de candidatos."""
    verification = models.ForeignKey(CandidateVerification, on_delete=models.CASCADE, related_name='service_results')
    service = models.ForeignKey(VerificationService, on_delete=models.CASCADE, related_name='candidate_results')
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pendiente'),
        ('in_progress', 'En progreso'),
        ('completed', 'Completado'),
        ('failed', 'Fallido')
    ], default='pending')
    results = models.JSONField(default=dict, help_text="Resultados del servicio")
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Resultado de Servicio"
        verbose_name_plural = "Resultados de Servicios"
        ordering = ['-started_at']
        
    def __str__(self):
        return f"{self.verification} - {self.service}"

class SocialNetworkVerification(models.Model):
    """Modelo para verificaciones de redes sociales."""
    verification = models.ForeignKey(CandidateVerification, on_delete=models.CASCADE, related_name='social_verifications')
    network = models.CharField(max_length=50, choices=[
        ('linkedin', 'LinkedIn'),
        ('facebook', 'Facebook'),
        ('twitter', 'Twitter'),
        ('instagram', 'Instagram'),
        ('other', 'Otro')
    ])
    profile_url = models.URLField()
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pendiente'),
        ('in_progress', 'En progreso'),
        ('completed', 'Completado'),
        ('failed', 'Fallido')
    ], default='pending')
    results = models.JSONField(default=dict, help_text="Resultados de la verificación")
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Verificación de Red Social"
        verbose_name_plural = "Verificaciones de Redes Sociales"
        ordering = ['-started_at']
        
    def __str__(self):
        return f"{self.verification} - {self.network}"

class PaymentTransaction(models.Model):
    """Modelo para transacciones de pago."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    payment_method = models.CharField(max_length=50, choices=[
        ('credit_card', 'Tarjeta de Crédito'),
        ('debit_card', 'Tarjeta de Débito'),
        ('paypal', 'PayPal'),
        ('bank_transfer', 'Transferencia Bancaria'),
        ('other', 'Otro')
    ])
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pendiente'),
        ('completed', 'Completado'),
        ('failed', 'Fallido'),
        ('refunded', 'Reembolsado')
    ], default='pending')
    transaction_id = models.CharField(max_length=255, unique=True)
    payment_details = models.JSONField(default=dict, help_text="Detalles del pago")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Transacción de Pago"
        verbose_name_plural = "Transacciones de Pago"
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.user} - {self.amount} {self.currency}"

class Contrato(models.Model):
    """Modelo para gestionar contratos de trabajo."""
    
    oportunidad = models.ForeignKey('Oportunidad', on_delete=models.CASCADE)
    empleado = models.ForeignKey('Empleado', on_delete=models.CASCADE, related_name='contratos')
    status = models.CharField(max_length=20, choices=CONTRATO_STATUS_CHOICES, default='PENDING_APPROVAL')
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField(null=True, blank=True)
    salario = models.DecimalField(max_digits=10, decimal_places=2)
    documento = models.FileField(upload_to='contratos/')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Contrato"
        verbose_name_plural = "Contratos"
        ordering = ['-created_at']

    def __str__(self):
        return f"Contrato de {self.empleado} para {self.oportunidad}"

class EntrevistaTipo(models.Model):
    """Tipos de entrevistas disponibles."""
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    duracion_minutos = models.IntegerField(default=60)
    preguntas = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Tipo de Entrevista"
        verbose_name_plural = "Tipos de Entrevista"

    def __str__(self):
        return self.nombre

class Entrevista(models.Model):
    """Modelo para gestionar entrevistas."""
    candidato = models.ForeignKey('Person', on_delete=models.CASCADE)
    entrevistador = models.ForeignKey('Person', on_delete=models.CASCADE, related_name='entrevistas_realizadas')
    tipo = models.ForeignKey(EntrevistaTipo, on_delete=models.CASCADE)
    fecha = models.DateTimeField()
    notas = models.TextField(blank=True)
    resultado = models.CharField(max_length=20, choices=[
        ('PENDIENTE', 'Pendiente'),
        ('APROBADO', 'Aprobado'),
        ('RECHAZADO', 'Rechazado'),
        ('PENDIENTE_SEGUNDA', 'Pendiente Segunda Entrevista')
    ], default='PENDIENTE')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Entrevista"
        verbose_name_plural = "Entrevistas"
        ordering = ['-fecha']

    def __str__(self):
        return f"Entrevista de {self.candidato} con {self.entrevistador}"

class CartaOferta(models.Model):
    """Modelo para gestionar cartas de oferta."""
    candidato = models.ForeignKey('Person', on_delete=models.CASCADE)
    oportunidad = models.ForeignKey('Oportunidad', on_delete=models.CASCADE)
    salario = models.DecimalField(max_digits=10, decimal_places=2)
    beneficios = models.JSONField(default=dict)
    fecha_inicio = models.DateField()
    fecha_expiracion = models.DateField()
    estado = models.CharField(max_length=20, choices=[
        ('PENDIENTE', 'Pendiente'),
        ('ACEPTADA', 'Aceptada'),
        ('RECHAZADA', 'Rechazada'),
        ('EXPIRADA', 'Expirada')
    ], default='PENDIENTE')
    documento = models.FileField(upload_to='cartas_oferta/')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Carta de Oferta"
        verbose_name_plural = "Cartas de Oferta"
        ordering = ['-created_at']

    def __str__(self):
        return f"Carta de oferta para {self.candidato} - {self.oportunidad}"

class Application(models.Model):
    """Modelo para gestionar aplicaciones a oportunidades."""
    # Campos originales
    candidato = models.ForeignKey('Person', on_delete=models.CASCADE)
    oportunidad = models.ForeignKey('Oportunidad', on_delete=models.CASCADE)
    estado = models.CharField(max_length=20, choices=[
        ('PENDIENTE', 'Pendiente'),
        ('EN_REVISION', 'En Revisión'),
        ('ENTREVISTA', 'En Entrevista'),
        ('OFERTA', 'Oferta Enviada'),
        ('CONTRATADO', 'Contratado'),
        ('RECHAZADO', 'Rechazado')
    ], default='PENDIENTE')
    fecha_aplicacion = models.DateTimeField(auto_now_add=True)
    ultima_actualizacion = models.DateTimeField(auto_now=True)
    notas = models.TextField(blank=True)
    
    # Campos necesarios para el formulario (agregados)
    user = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, null=True, blank=True, related_name='applications')
    vacancy = models.ForeignKey('Vacante', on_delete=models.CASCADE, null=True, blank=True, related_name='applications')
    status = models.CharField(max_length=20, null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    interview_date = models.DateField(null=True, blank=True)
    expected_salary = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    current_salary = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    skills = models.TextField(blank=True, null=True)
    experience_years = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        verbose_name = "Aplicación"
        verbose_name_plural = "Aplicaciones"
        ordering = ['-fecha_aplicacion']
        unique_together = ['candidato', 'oportunidad']

    def __str__(self):
        return f"Aplicación de {self.candidato} a {self.oportunidad}"

class PaymentMilestone(models.Model):
    """Modelo para gestionar hitos de pago."""
    contrato = models.ForeignKey(Contrato, on_delete=models.CASCADE)
    descripcion = models.CharField(max_length=200)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_vencimiento = models.DateField()
    trigger_event = models.CharField(max_length=50, choices=TRIGGER_EVENT_CHOICES)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='PENDING')
    fecha_pago = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Hito de Pago"
        verbose_name_plural = "Hitos de Pago"
        ordering = ['fecha_vencimiento']

    def __str__(self):
        return f"Hito de pago: {self.descripcion} - {self.contrato}"

class WeightingModel(models.Model):
    """Modelo para gestionar modelos de ponderación de candidatos."""
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    factores = models.JSONField(default=dict)
    pesos = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Modelo de Ponderación"
        verbose_name_plural = "Modelos de Ponderación"

    def __str__(self):
        return self.nombre

class WeightingHistory(models.Model):
    """Historial de cambios en modelos de ponderación."""
    modelo = models.ForeignKey(WeightingModel, on_delete=models.CASCADE)
    cambios = models.JSONField()
    realizado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Historial de Ponderación"
        verbose_name_plural = "Historiales de Ponderación"
        ordering = ['-fecha']

    def __str__(self):
        return f"Cambios en {self.modelo} - {self.fecha}"

class TalentConfig(models.Model):
    """Configuración general del sistema de talento."""
    business_unit = models.ForeignKey('BusinessUnit', on_delete=models.CASCADE)
    config = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuración de Talento"
        verbose_name_plural = "Configuraciones de Talento"

    def __str__(self):
        return f"Configuración de {self.business_unit}"

class OpportunityAnalysis(models.Model):
    """Análisis de oportunidades de trabajo."""
    oportunidad = models.ForeignKey('Oportunidad', on_delete=models.CASCADE)
    analisis = models.JSONField(default=dict)
    recomendaciones = models.TextField()
    fecha_analisis = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Análisis de Oportunidad"
        verbose_name_plural = "Análisis de Oportunidades"
        ordering = ['-fecha_analisis']

    def __str__(self):
        return f"Análisis de {self.oportunidad}"

class AIStrategy(models.Model):
    """Estrategias de IA para el sistema."""
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    configuracion = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Estrategia de IA"
        verbose_name_plural = "Estrategias de IA"

    def __str__(self):
        return self.nombre

class ActionPlan(models.Model):
    """Planes de acción para candidatos."""
    candidato = models.ForeignKey('Person', on_delete=models.CASCADE)
    objetivo = models.CharField(max_length=200)
    acciones = models.JSONField(default=list)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    estado = models.CharField(max_length=20, choices=[
        ('PENDIENTE', 'Pendiente'),
        ('EN_PROGRESO', 'En Progreso'),
        ('COMPLETADO', 'Completado'),
        ('CANCELADO', 'Cancelado')
    ], default='PENDIENTE')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Plan de Acción"
        verbose_name_plural = "Planes de Acción"
        ordering = ['-fecha_inicio']

    def __str__(self):
        return f"Plan de acción para {self.candidato}"

class JobTracker(models.Model):
    """Seguimiento de trabajos y oportunidades."""
    candidato = models.ForeignKey('Person', on_delete=models.CASCADE)
    oportunidad = models.ForeignKey('Oportunidad', on_delete=models.CASCADE)
    estado = models.CharField(max_length=20, choices=[
        ('APLICADO', 'Aplicado'),
        ('ENTREVISTA', 'En Entrevista'),
        ('OFERTA', 'Oferta Recibida'),
        ('ACEPTADO', 'Aceptado'),
        ('RECHAZADO', 'Rechazado')
    ])
    notas = models.TextField(blank=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Seguimiento de Trabajo"
        verbose_name_plural = "Seguimientos de Trabajo"
        ordering = ['-fecha_actualizacion']

    def __str__(self):
        return f"Seguimiento de {self.candidato} - {self.oportunidad}"

INTERVIEW_TYPES = [
    ('phone', 'Teléfono'),
    ('video', 'Video-entrevista'),
    ('onsite', 'Presencial'),
]

INTERVIEW_STATUS = [
    ('scheduled', 'Programada'),
    ('in_progress', 'En curso'),
    ('completed', 'Completada'),
    ('canceled', 'Cancelada'),
]
class Interview(models.Model):
    """
    Modelo para gestionar las entrevistas de candidatos.
    """
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='interviews')
    vacancy = models.ForeignKey(Vacante, on_delete=models.CASCADE, related_name='interviews')
    interview_date = models.DateTimeField()
    interview_type = models.CharField(max_length=50, choices=INTERVIEW_TYPES)
    status = models.CharField(max_length=20, choices=INTERVIEW_STATUS, default='scheduled')
    location = models.JSONField(null=True, blank=True)  # Información de ubicación
    current_location = models.JSONField(null=True, blank=True)  # Ubicación actual del candidato
    location_status = models.CharField(max_length=20, choices=[
        ('en_traslado', 'En Traslado'),
        ('llegando_tarde', 'Llegando Tarde'),
        ('cerca', 'Cerca del Lugar')
    ], null=True, blank=True)
    estimated_arrival = models.DateTimeField(null=True, blank=True)
    delay_minutes = models.IntegerField(null=True, blank=True)
    delay_reason = models.TextField(null=True, blank=True)
    cancellation_reason = models.TextField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-interview_date']
        indexes = [
            models.Index(fields=['interview_date']),
            models.Index(fields=['status']),
            models.Index(fields=['location_status'])
        ]

    def __str__(self):
        return f"{self.person.full_name} - {self.vacancy.title} ({self.interview_date})"

    @property
    def is_delayed(self):
        """Verifica si la entrevista está retrasada."""
        if self.estimated_arrival and self.estimated_arrival > self.interview_date:
            return True
        return False

    @property
    def delay_time(self):
        """Calcula el tiempo de retraso en minutos."""
        if self.is_delayed:
            return int((self.estimated_arrival - self.interview_date).total_seconds() / 60)
        return 0

    def update_location(self, current_location, status=None):
        """
        Actualiza la ubicación actual del candidato.
        
        Args:
            current_location (dict): Información de ubicación actual
            status (str, optional): Estado de ubicación
        """
        self.current_location = current_location
        if status:
            self.location_status = status
        self.save()

    def mark_as_delayed(self, minutes, reason):
        """
        Marca la entrevista como retrasada.
        
        Args:
            minutes (int): Minutos de retraso
            reason (str): Razón del retraso
        """
        self.delay_minutes = minutes
        self.delay_reason = reason
        self.save()

class ConfiguracionScraping(models.Model):
    """Configuración para el scraping de datos."""
    dominio = models.ForeignKey('DominioScraping', on_delete=models.CASCADE)
    configuracion = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    ultima_ejecucion = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuración de Scraping"
        verbose_name_plural = "Configuraciones de Scraping"

    def __str__(self):
        return f"Configuración para {self.dominio}"

class Certificate(models.Model):
    """Certificaciones y títulos."""
    persona = models.ForeignKey('Person', on_delete=models.CASCADE)
    nombre = models.CharField(max_length=200)
    institucion = models.CharField(max_length=200)
    fecha_emision = models.DateField()
    fecha_expiracion = models.DateField(null=True, blank=True)
    credencial_id = models.CharField(max_length=100, blank=True)
    url_verificacion = models.URLField(blank=True)
    documento = models.FileField(upload_to='certificados/', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Certificado"
        verbose_name_plural = "Certificados"
        ordering = ['-fecha_emision']

    def __str__(self):
        return f"{self.nombre} - {self.persona}"

class InternalDocumentSignature(models.Model):
    """Firmas de documentos internos."""
    documento = models.FileField(upload_to='documentos_firmados/')
    tipo = models.CharField(max_length=50)
    firmado_por = models.ForeignKey('Person', on_delete=models.CASCADE)
    fecha_firma = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Firma de Documento Interno"
        verbose_name_plural = "Firmas de Documentos Internos"
        ordering = ['-fecha_firma']

    def __str__(self):
        return f"Firma de {self.firmado_por} - {self.tipo}"

class RegistroScraping(models.Model):
    """Registro de actividades de scraping."""
    dominio = models.ForeignKey('DominioScraping', on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)
    tipo = models.CharField(max_length=50)
    resultado = models.JSONField(default=dict)
    errores = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Registro de Scraping"
        verbose_name_plural = "Registros de Scraping"
        ordering = ['-fecha']

    def __str__(self):
        return f"Scraping de {self.dominio} - {self.fecha}"

class IntentPattern(models.Model):
    """Patrones de intención para el chatbot."""
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    patrones = models.JSONField(default=list)
    respuestas = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Patrón de Intención"
        verbose_name_plural = "Patrones de Intención"

    def __str__(self):
        return self.nombre

class StateTransition(models.Model):
    """Transiciones de estado para el chatbot."""
    estado_origen = models.CharField(max_length=50)
    estado_destino = models.CharField(max_length=50)
    condiciones = models.JSONField(default=dict)
    acciones = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Transición de Estado"
        verbose_name_plural = "Transiciones de Estado"
        unique_together = ['estado_origen', 'estado_destino']

    def __str__(self):
        return f"{self.estado_origen} -> {self.estado_destino}"

class IntentTransition(models.Model):
    """Transiciones basadas en intenciones."""
    intent_pattern = models.ForeignKey(IntentPattern, on_delete=models.CASCADE)
    estado_origen = models.CharField(max_length=50)
    estado_destino = models.CharField(max_length=50)
    prioridad = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Transición de Intención"
        verbose_name_plural = "Transiciones de Intención"
        ordering = ['-prioridad']

    def __str__(self):
        return f"{self.intent_pattern} - {self.estado_origen} -> {self.estado_destino}"

class ContextCondition(models.Model):
    """Condiciones de contexto para el flujo conversacional."""
    name = models.CharField(max_length=100, help_text="Nombre de la condición")
    intent = models.CharField(max_length=50, help_text="Intent asociado a esta condición")
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE, related_name='context_conditions')
    type = models.CharField(
        max_length=32,
        help_text="Tipo de condición: boolean, numeric, string, choice, date, json, expression, o personalizado."
    )
    value = models.TextField(help_text="Valor esperado para la condición (puede ser texto, número, JSON, expresión, etc.)")
    description = models.TextField(blank=True, help_text="Descripción de la condición")
    is_active = models.BooleanField(default=True, help_text="¿La condición está activa?")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Condición de Contexto"
        verbose_name_plural = "Condiciones de Contexto"
        unique_together = ['name', 'intent', 'business_unit']
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.intent}) - {self.business_unit.name}"

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
    business_unit = models.ForeignKey('BusinessUnit', on_delete=models.CASCADE, null=True, blank=True, related_name='message_logs', help_text="Unidad de negocio asociada al mensaje")
    channel = models.CharField(max_length=30, blank=True, null=True, help_text="Canal específico: whatsapp, messenger, instagram, telegram, etc.")
    template_name = models.CharField(max_length=100, blank=True, null=True, help_text="Nombre de la plantilla usada (si aplica)")
    meta_pricing_model = models.CharField(max_length=20, blank=True, null=True, help_text="Modelo de precios de Meta (CBP, PMP, etc.)")
    meta_pricing_type = models.CharField(max_length=20, blank=True, null=True, help_text="Tipo de mensaje según Meta (regular, free_customer_service, etc.)")
    meta_pricing_category = models.CharField(max_length=20, blank=True, null=True, help_text="Categoría de mensaje según Meta (marketing, utility, etc.)")
    meta_cost = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True, help_text="Costo real del mensaje según Meta")
    
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

class ChatState(models.Model):
    """Modelo para manejar el estado de las conversaciones del chatbot."""
    
    # Campos de identificación
    person = models.ForeignKey(
        Person,
        on_delete=models.CASCADE,
        related_name='chat_states',
        help_text="Persona asociada a la conversación"
    )
    
    business_unit = models.ForeignKey(
        BusinessUnit,
        on_delete=models.CASCADE,
        related_name='chat_states',
        help_text="Business Unit asociada a la conversación"
    )
    
    # Campos de estado
    state = models.CharField(
        max_length=50,
        choices=STATE_TYPE_CHOICES,
        default='INITIAL',
        help_text="Estado actual de la conversación"
    )
    
    last_intent = models.ForeignKey(
        IntentPattern,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='chat_states',
        help_text="Último intento reconocido"
    )
    
    # Campos de navegación
    menu_page = models.IntegerField(
        default=0,
        help_text="Página actual del menú"
    )
    
    last_menu = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Último menú visitado"
    )
    
    last_submenu = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Último submenú visitado"
    )
    
    # Campos de búsqueda
    search_term = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Término de búsqueda actual"
    )
    
    # Campos de historial
    conversation_history = models.JSONField(
        default=list,
        help_text="Historial de la conversación"
    )
    
    last_transition = models.DateTimeField(
        auto_now=True,
        help_text="Última transición de estado"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Estado de Chat"
        verbose_name_plural = "Estados de Chat"
        unique_together = ('person', 'business_unit')
        indexes = [
            models.Index(fields=["person", "business_unit"]),
            models.Index(fields=["state"]),
            models.Index(fields=["menu_page"]),
            models.Index(fields=["last_menu"]),
            models.Index(fields=["last_submenu"]),
            models.Index(fields=["last_transition"]),
        ]
        
    def __str__(self):
        return f"{self.person.nombre} - {self.business_unit.name} ({self.state})"
        
    def get_available_intents(self):
        """Obtiene los intents disponibles para el estado actual."""
        current_state = self.state
        bu = self.business_unit
        transitions = StateTransition.objects.filter(current_state=current_state, business_unit=bu)
        available_intents = IntentPattern.objects.filter(business_units=bu, enabled=True)
        filtered_intents = [intent for intent in available_intents if IntentTransition.objects.filter(current_intent=intent, business_unit=bu).exists()]
        return filtered_intents
        
    def validate_transition(self, new_state):
        """Valida si la transición al nuevo estado es permitida."""
        try:
            StateTransition.objects.get(current_state=self.state, next_state=new_state, business_unit=self.business_unit)
            return True
        except StateTransition.DoesNotExist:
            return False
            
    def transition_to(self, new_state):
        """Realiza la transición al nuevo estado si es válida."""
        if self.validate_transition(new_state):
            self.state = new_state
            self.last_transition = timezone.now()
            self.save()
            return True
        return False
        
    def reset_menu_state(self):
        """Resetea el estado de navegación del menú."""
        self.menu_page = 0
        self.last_menu = None
        self.last_submenu = None
        self.search_term = None
        self.save()
        
    def update_menu_state(self, menu: str = None, submenu: str = None, page: int = None):
        """Actualiza el estado de navegación del menú."""
        if menu is not None:
            self.last_menu = menu
        if submenu is not None:
            self.last_submenu = submenu
        if page is not None:
            self.menu_page = page
        self.save()
        
    def update_search_term(self, term: str):
        """Actualiza el término de búsqueda actual."""
        self.search_term = term
        self.save()

class FailedLoginAttempt(models.Model):
    """Registro de intentos fallidos de inicio de sesión."""
    email = models.EmailField()
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Intento fallido de inicio de sesión"
        verbose_name_plural = "Intentos fallidos de inicio de sesión"
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['ip_address']),
            models.Index(fields=['timestamp'])
        ]
        
    def __str__(self):
        return f"Intento fallido de {self.email} desde {self.ip_address}"

class UserActivityLog(models.Model):
    """Registro de actividad de usuarios."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activity_logs')
    action = models.CharField(max_length=100)
    details = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Log de actividad de usuario"
        verbose_name_plural = "Logs de actividad de usuarios"
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['action']),
            models.Index(fields=['timestamp'])
        ]
        
    def __str__(self):
        return f"{self.user.email} - {self.action}"

class Invitacion(models.Model):
    """Modelo para gestionar invitaciones a usuarios."""
    email = models.EmailField()
    token = models.CharField(max_length=100, unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE, null=True, blank=True)
    division = models.ForeignKey('Division', on_delete=models.CASCADE, null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pendiente'),
        ('accepted', 'Aceptada'),
        ('expired', 'Expirada'),
        ('cancelled', 'Cancelada')
    ], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    accepted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Invitación"
        verbose_name_plural = "Invitaciones"
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['token']),
            models.Index(fields=['status'])
        ]
        
    def __str__(self):
        return f"Invitación para {self.email} ({self.role})"
        
    def is_expired(self):
        return timezone.now() > self.expires_at

class Division(models.Model):
    """Modelo para divisiones dentro de una unidad de negocio."""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    level = models.PositiveIntegerField(default=0)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "División"
        verbose_name_plural = "Divisiones"
        ordering = ['level', 'order', 'name']
        
    def __str__(self):
        return self.name

class Badge(models.Model):
    """Modelo para insignias y logros."""
    name = models.CharField(max_length=100)
    description = models.TextField()
    image = models.ImageField(upload_to='badges/')
    category = models.CharField(max_length=50, choices=[
        ('skill', 'Habilidad'),
        ('achievement', 'Logro'),
        ('social', 'Social'),
        ('special', 'Especial')
    ])
    points = models.PositiveIntegerField(default=0)
    requirements = models.JSONField(default=dict, help_text="Requisitos para obtener la insignia")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Insignia"
        verbose_name_plural = "Insignias"
        ordering = ['category', 'name']
        
    def __str__(self):
        return self.name

class DivisionTransition(models.Model):
    """Modelo para transiciones entre divisiones."""
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='division_transitions')
    from_division = models.ForeignKey(Division, on_delete=models.CASCADE, related_name='transitions_from')
    to_division = models.ForeignKey(Division, on_delete=models.CASCADE, related_name='transitions_to')
    transition_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pendiente'),
        ('approved', 'Aprobado'),
        ('rejected', 'Rechazado'),
        ('completed', 'Completado')
    ], default='pending')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_transitions')
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Transición de División"
        verbose_name_plural = "Transiciones de División"
        ordering = ['-transition_date']
        
    def __str__(self):
        return f"{self.person} - {self.from_division} a {self.to_division}"

class ApiConfig(models.Model):
    """Modelo para configuración de APIs externas."""
    name = models.CharField(max_length=100)
    api_type = models.CharField(max_length=50, choices=[
        ('rest', 'REST'),
        ('graphql', 'GraphQL'),
        ('soap', 'SOAP'),
        ('calendly', 'Calendly'),
        ('zapier', 'Zapier'),
        ('other', 'Otro')
    ])
    base_url = models.URLField()
    api_key = models.CharField(max_length=255, blank=True)
    secret_key = models.CharField(max_length=255, blank=True)
    additional_config = models.JSONField(default=dict, help_text="Configuración adicional específica de la API")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Configuración de API"
        verbose_name_plural = "Configuraciones de API"
        ordering = ['name']
        
    def __str__(self):
        return self.name

class MetaAPI(models.Model):
    """Modelo para configuración de Meta API."""
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE, related_name='meta_apis')
    app_id = models.CharField(max_length=255)
    app_secret = models.CharField(max_length=255)
    access_token = models.CharField(max_length=255)
    webhook_verify_token = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    additional_config = models.JSONField(default=dict, help_text="Configuración adicional")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Configuración de Meta API"
        verbose_name_plural = "Configuraciones de Meta API"
        unique_together = ['business_unit']
        
    def __str__(self):
        return f"Meta API - {self.business_unit}"

class WhatsAppConfig(models.Model):
    """Modelo para configuración de WhatsApp."""
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE, related_name='whatsapp_configs')
    phone_number = models.CharField(max_length=20)
    business_account_id = models.CharField(max_length=255)
    access_token = models.CharField(max_length=255)
    webhook_verify_token = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    additional_config = models.JSONField(default=dict, help_text="Configuración adicional")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Configuración de WhatsApp"
        verbose_name_plural = "Configuraciones de WhatsApp"
        unique_together = ['business_unit']
        
    def __str__(self):
        return f"WhatsApp - {self.business_unit}"

def default_field_map():
    """Valores por defecto para el mapeo de campos de WhatsApp a modelos internos."""
    return {
        "TextInput_531eb": "first_name",
        "TextInput_123ab": "last_name",
        "TextInput_999xx": "email",
        "TextInput_888yy": "phone"
    }

class Template(models.Model):
    """Modelo para plantillas de mensajes."""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    content = models.TextField()
    variables = models.JSONField(default=list, help_text="Variables disponibles en la plantilla")
    type = models.CharField(max_length=50, choices=[
        ('email', 'Email'),
        ('whatsapp', 'WhatsApp'),
        ('sms', 'SMS'),
        ('other', 'Otro')
    ])
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE, related_name='templates')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    field_map = models.JSONField(default=default_field_map, help_text="Mapeo de campos WhatsApp → modelo interno ")
    
    class Meta:
        verbose_name = "Plantilla"
        verbose_name_plural = "Plantillas"
        ordering = ['type', 'name']
    
    def __str__(self):
        return self.name

class MessengerAPI(models.Model):
    """Modelo para configuración de Messenger API."""
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE, related_name='messenger_apis')
    page_id = models.CharField(max_length=255)
    access_token = models.CharField(max_length=255)
    app_secret = models.CharField(max_length=255)
    webhook_verify_token = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    additional_config = models.JSONField(default=dict, help_text="Configuración adicional")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    meta_verified = models.BooleanField(
        default=False,
        help_text="Indica si la cuenta de Messenger tiene Meta Verified badge"
    )
    meta_verified_since = models.DateTimeField(
        null=True, blank=True,
        help_text="Fecha en que se obtuvo la verificación de Meta"
    )
    meta_verified_badge_url = models.URLField(
        null=True, blank=True,
        help_text="URL del badge de verificación de Meta"
    )
    
    class Meta:
        verbose_name = "Configuración de Messenger API"
        verbose_name_plural = "Configuraciones de Messenger API"
        unique_together = ['business_unit']
        
    def __str__(self):
        return f"Messenger API - {self.business_unit}"

class InstagramAPI(models.Model):
    """Modelo para configuración de Instagram API."""
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE, related_name='instagram_apis')
    account_id = models.CharField(max_length=255)
    access_token = models.CharField(max_length=255)
    username = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    additional_config = models.JSONField(default=dict, help_text="Configuración adicional")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    meta_verified = models.BooleanField(
        default=False,
        help_text="Indica si la cuenta de Instagram tiene Meta Verified badge"
    )
    meta_verified_since = models.DateTimeField(
        null=True, blank=True,
        help_text="Fecha en que se obtuvo la verificación de Meta"
    )
    meta_verified_badge_url = models.URLField(
        null=True, blank=True,
        help_text="URL del badge de verificación de Meta"
    )
    
    class Meta:
        verbose_name = "Configuración de Instagram API"
        verbose_name_plural = "Configuraciones de Instagram API"
        unique_together = ['business_unit']
        
    def __str__(self):
        return f"Instagram API - {self.business_unit}"

class SlackAPI(models.Model):
    """Modelo para configuración de Slack API."""
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE, related_name='slack_apis')
    workspace_id = models.CharField(max_length=255)
    bot_token = models.CharField(max_length=255)
    signing_secret = models.CharField(max_length=255)
    default_channel = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    additional_config = models.JSONField(default=dict, help_text="Configuración adicional")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Configuración de Slack API"
        verbose_name_plural = "Configuraciones de Slack API"
        unique_together = ['business_unit']
        
    def __str__(self):
        return f"Slack API - {self.business_unit}"

class Chat(models.Model):
    """Modelo para chats."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chats')
    title = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Chat"
        verbose_name_plural = "Chats"
        ordering = ['-updated_at']
        
    def __str__(self):
        return self.name

class JobOpportunity(models.Model):
    """Modelo para oportunidades de trabajo."""
    title = models.CharField(max_length=255)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='job_opportunities')
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE, related_name='job_opportunities')
    description = models.TextField()
    requirements = models.TextField()
    location = models.CharField(max_length=255)
    salary_range = models.CharField(max_length=100)
    job_type = models.CharField(max_length=50, choices=[
        ('full_time', 'Tiempo completo'),
        ('part_time', 'Tiempo parcial'),
        ('contract', 'Contrato'),
        ('internship', 'Pasantía'),
        ('other', 'Otro')
    ])
    is_remote = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Oportunidad de Trabajo"
        verbose_name_plural = "Oportunidades de Trabajo"
        ordering = ['-created_at']
        
    def __str__(self):
        return self.name

class SmtpConfig(models.Model):
    """Modelo para configuración de servidor SMTP."""
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE, related_name='smtp_configs')
    host = models.CharField(max_length=255)
    port = models.PositiveIntegerField()
    username = models.CharField(max_length=255)
    password = models.CharField(max_length=255)
    use_tls = models.BooleanField(default=True)
    from_email = models.EmailField()
    from_name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    additional_config = models.JSONField(default=dict, help_text="Configuración adicional")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Configuración SMTP"
        verbose_name_plural = "Configuraciones SMTP"
        unique_together = ['business_unit']
        
    def __str__(self):
        return f"SMTP - {self.business_unit}"

class UserInteractionLog(models.Model):
    """Modelo para registro de interacciones de usuario."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='interaction_logs')
    action = models.CharField(max_length=100)
    entity_type = models.CharField(max_length=50)
    entity_id = models.PositiveIntegerField()
    details = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Registro de Interacción"
        verbose_name_plural = "Registros de Interacción"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'action']),
            models.Index(fields=['entity_type', 'entity_id']),
            models.Index(fields=['timestamp'])
        ]
        
    def __str__(self):
        return f"{self.user} - {self.action}"

class ReporteScraping(models.Model):
    """Modelo para reportes de scraping."""
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE, related_name='scraping_reports')
    start_date = models.DateField()
    end_date = models.DateField()
    total_vacancies = models.PositiveIntegerField(default=0)
    total_errors = models.PositiveIntegerField(default=0)
    details = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Reporte de Scraping"
        verbose_name_plural = "Reportes de Scraping"
        ordering = ['-end_date']
        
    def __str__(self):
        return f"Reporte {self.start_date} - {self.end_date}"

class EnhancedMLProfile(models.Model):
    """Modelo para perfiles de machine learning mejorados."""
    person = models.OneToOneField(Person, on_delete=models.CASCADE, related_name='ml_profile')
    skills = models.JSONField(default=dict, help_text="Habilidades y competencias")
    experience = models.JSONField(default=dict, help_text="Experiencia laboral")
    personality = models.JSONField(default=dict, help_text="Rasgos de personalidad")
    job_preferences = models.JSONField(default=dict, help_text="Preferencias laborales")
    recommendations = models.JSONField(default=list, help_text="Recomendaciones")
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Perfil ML Mejorado"
        verbose_name_plural = "Perfiles ML Mejorados"
        
    def __str__(self):
        return f"Perfil ML - {self.person}"

class ModelTrainingLog(models.Model):
    """Modelo para registro de entrenamiento de modelos."""
    model_name = models.CharField(max_length=100)
    version = models.CharField(max_length=50)
    training_date = models.DateTimeField()
    metrics = models.JSONField(default=dict, help_text="Métricas de rendimiento")
    parameters = models.JSONField(default=dict, help_text="Parámetros del modelo")
    status = models.CharField(max_length=20, choices=[
        ('success', 'Éxito'),
        ('failed', 'Fallido'),
        ('in_progress', 'En progreso')
    ])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Registro de Entrenamiento"
        verbose_name_plural = "Registros de Entrenamiento"
        ordering = ['-training_date']
        
    def __str__(self):
        return f"{self.model_name} v{self.version}"

class QuarterlyInsight(models.Model):
    """Modelo para insights trimestrales."""
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE, related_name='quarterly_insights')
    quarter = models.PositiveIntegerField()
    year = models.PositiveIntegerField()
    metrics = models.JSONField(default=dict, help_text="Métricas del trimestre")
    market_trends = models.JSONField(default=dict, help_text="Tendencias del mercado")
    recommendations = models.JSONField(default=list, help_text="Recomendaciones")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Insight Trimestral"
        verbose_name_plural = "Insights Trimestrales"
        ordering = ['-year', '-quarter']
        unique_together = ['business_unit', 'quarter', 'year']
        
    def __str__(self):
        return f"Q{self.quarter} {self.year} - {self.business_unit}"

class VerificationCode(models.Model):
    """Modelo para códigos de verificación."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='verification_codes')
    code = models.CharField(max_length=6)
    purpose = models.CharField(max_length=50, choices=[
        ('email', 'Verificación de email'),
        ('phone', 'Verificación de teléfono'),
        ('password_reset', 'Restablecimiento de contraseña'),
        ('other', 'Otro')
    ])
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Código de Verificación"
        verbose_name_plural = "Códigos de Verificación"
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.user} - {self.purpose}"

class Interaction(models.Model):
    """Modelo para interacciones."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='interactions')
    type = models.CharField(max_length=50, choices=[
        ('view', 'Visualización'),
        ('click', 'Clic'),
        ('submit', 'Envío'),
        ('other', 'Otro')
    ])
    entity_type = models.CharField(max_length=50)
    entity_id = models.PositiveIntegerField()
    details = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Interacción"
        verbose_name_plural = "Interacciones"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'type']),
            models.Index(fields=['entity_type', 'entity_id']),
            models.Index(fields=['timestamp'])
        ]
        
    def __str__(self):
        return f"{self.user} - {self.type}"

class AgreementPreference(models.Model):
    """Modelo para preferencias de acuerdos."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='agreement_preferences')
    agreement_type = models.CharField(max_length=50, choices=[
        ('privacy', 'Privacidad'),
        ('terms', 'Términos y condiciones'),
        ('marketing', 'Marketing'),
        ('other', 'Otro')
    ])
    is_enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Preferencia de Acuerdo"
        verbose_name_plural = "Preferencias de Acuerdo"
        unique_together = ['user', 'agreement_type']
        
    def __str__(self):
        return f"{self.user} - {self.agreement_type}"



class OnboardingProcess(models.Model):
    """Modelo para procesos de onboarding."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='onboarding_processes')
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pendiente'),
        ('in_progress', 'En progreso'),
        ('completed', 'Completado'),
        ('failed', 'Fallido')
    ], default='pending')
    current_step = models.PositiveIntegerField(default=0)
    total_steps = models.PositiveIntegerField()
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Proceso de Onboarding"
        verbose_name_plural = "Procesos de Onboarding"
        ordering = ['-started_at']
        
    def __str__(self):
        return f"Onboarding - {self.user}"

class OnboardingTask(models.Model):
    """Modelo para tareas de onboarding."""
    process = models.ForeignKey(OnboardingProcess, on_delete=models.CASCADE, related_name='tasks')
    name = models.CharField(max_length=255)
    description = models.TextField()
    step = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pendiente'),
        ('in_progress', 'En progreso'),
        ('completed', 'Completado'),
        ('failed', 'Fallido')
    ], default='pending')
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Tarea de Onboarding"
        verbose_name_plural = "Tareas de Onboarding"
        ordering = ['process', 'step']
        
    def __str__(self):
        return f"{self.process} - {self.name}"

class Experience(models.Model):
    """Modelo para experiencias laborales."""
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='experiences')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='experiences')
    title = models.CharField(max_length=255)
    description = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=False)
    location = models.CharField(max_length=255)
    skills = models.ManyToManyField(Skill, related_name='experiences')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Experiencia"
        verbose_name_plural = "Experiencias"
        ordering = ['-start_date']
        
    def __str__(self):
        return f"{self.person} - {self.title} en {self.company}"

class NotificationLog(models.Model):
    """
    Registro de notificaciones enviadas.
    """
    notification = models.ForeignKey('Notification', on_delete=models.CASCADE)
    channel = models.CharField(max_length=50)
    status = models.CharField(max_length=20)
    sent_at = models.DateTimeField(auto_now_add=True)
    error_message = models.TextField(null=True, blank=True)
    metadata = models.JSONField(default=dict)

    class Meta:
        indexes = [
            models.Index(fields=['notification', 'channel']),
            models.Index(fields=['status', 'sent_at'])
        ]

    def __str__(self):
        return f"{self.notification} - {self.channel} ({self.status})"

class Assessment(models.Model):
    """Modelo para evaluaciones de candidatos."""
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='assessments')
    evaluator = models.ForeignKey(User, on_delete=models.CASCADE)
    score = models.IntegerField()
    feedback = models.TextField()
    status = models.CharField(max_length=50, choices=[
        ('pending', 'Pendiente'),
        ('completed', 'Completada'),
        ('cancelled', 'Cancelada')
    ])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Evaluación de {self.application.candidate} por {self.evaluator}"

class Offer(models.Model):
    """Modelo para ofertas de trabajo."""
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='offers')
    salary = models.DecimalField(max_digits=10, decimal_places=2)
    benefits = models.JSONField(default=dict)
    start_date = models.DateField()
    status = models.CharField(max_length=50, choices=[
        ('draft', 'Borrador'),
        ('sent', 'Enviada'),
        ('accepted', 'Aceptada'),
        ('rejected', 'Rechazada'),
        ('expired', 'Expirada')
    ])
    created_at = models.DateTimeField(auto_now_add=True)

# PARA EL MODULO DE NOTIFICACIONES
# Canales de Notificación
NOTIFICATION_CHANNEL_CHOICES = [
    ('EMAIL', 'Email'),
    ('SMS', 'SMS'),
    ('WHATSAPP', 'WhatsApp'),
    ('TELEGRAM', 'Telegram'),
    ('SLACK', 'Slack'),
    ('DISCORD', 'Discord'),
    ('TEAMS', 'Microsoft Teams'),
    ('WEB', 'Web'),
    ('API', 'API'),
    ('DATABASE', 'Base de Datos'),
    ('QUEUE', 'Cola'),
    ('CACHE', 'Caché')
]

# Estados de Notificación
NOTIFICATION_STATUS_CHOICES = [
    ('PENDING', 'Pendiente'),
    ('SENT', 'Enviado'),
    ('FAILED', 'Fallido'),
    ('DELIVERED', 'Entregado'),
    ('READ', 'Leído'),
    ('CANCELLED', 'Cancelado')
]

# Tipos de Notificación
NOTIFICATION_TYPE_CHOICES = [
    ('SYSTEM', 'Sistema'),
    ('ALERT', 'Alerta'),
    ('UPDATE', 'Actualización'),
    ('REMINDER', 'Recordatorio'),
    ('WARNING', 'Advertencia'),
    ('ERROR', 'Error'),
    ('SUCCESS', 'Éxito'),
    ('INFO', 'Información')
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
    
    is_active = models.BooleanField(
        default=True,
        help_text="¿Este canal está activo?"
    )
    
    config = models.JSONField(
        default=dict,
        help_text="Configuración específica del canal (tokens, URLs, etc.)"
    )
    
    priority = models.IntegerField(
        default=10,
        help_text="Prioridad del canal (menor número = mayor prioridad)"
    )
    
    rate_limit = models.IntegerField(
        default=100,
        help_text="Límite de mensajes por minuto"
    )
    
    retry_policy = models.JSONField(
        default=dict,
        help_text="Política de reintentos (max_attempts, delay_minutes, etc.)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Canal de Notificación"
        verbose_name_plural = "Canales de Notificación"
        unique_together = ['business_unit', 'channel']
        ordering = ['business_unit', 'priority']
        
    def __str__(self):
        return f"{self.business_unit.name} - {self.channel}"

class NotificationTemplate(models.Model):
    """Modelo para plantillas de notificación."""
    
    name = models.CharField(
        max_length=100,
        help_text="Nombre de la plantilla"
    )
    
    type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPE_CHOICES,
        help_text="Tipo de notificación"
    )
    
    channel = models.ForeignKey(
        NotificationChannel,
        on_delete=models.CASCADE,
        related_name='templates',
        help_text="Canal asociado a esta plantilla"
    )
    
    subject = models.CharField(
        max_length=200,
        blank=True,
        help_text="Asunto de la notificación (para email, etc.)"
    )
    
    content = models.TextField(
        help_text="Contenido de la plantilla con variables"
    )
    
    variables = models.JSONField(
        default=list,
        help_text="Lista de variables disponibles en la plantilla"
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="¿La plantilla está activa?"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Plantilla de Notificación"
        verbose_name_plural = "Plantillas de Notificación"
        ordering = ['name']
        unique_together = ['name', 'type', 'channel']
        
    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"
        
    def render_content(self, context):
        """Renderiza el contenido de la plantilla con el contexto proporcionado."""
        from django.template import Template, Context
        template = Template(self.content)
        return template.render(Context(context))

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
    
    template = models.ForeignKey(
        'NotificationTemplate',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications',
        help_text="Plantilla utilizada para esta notificación"
    )
    
    metadata = models.JSONField(
        default=dict,
        help_text="Datos adicionales de la notificación"
    )
    
    sent_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha y hora en que se envió la notificación"
    )
    
    error_message = models.TextField(
        blank=True,
        help_text="Mensaje de error si falló el envío"
    )
    
    retry_count = models.IntegerField(
        default=0,
        help_text="Número de intentos de envío"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Notificación"
        verbose_name_plural = "Notificaciones"
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.get_notification_type_display()} - {self.recipient}"
        
    def mark_as_sent(self):
        """Marca la notificación como enviada."""
        self.status = 'SENT'
        self.sent_at = timezone.now()
        self.save(update_fields=['status', 'sent_at', 'updated_at'])
        
    def mark_as_failed(self, error_message):
        """Marca la notificación como fallida."""
        self.status = 'FAILED'
        self.error_message = error_message
        self.save(update_fields=['status', 'error_message', 'updated_at'])
        
    def increment_retry(self):
        """Incrementa el contador de reintentos."""
        self.retry_count += 1
        self.save(update_fields=['retry_count', 'updated_at'])

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
        choices=NOTIFICATION_CHANNEL_CHOICES,
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

#PARA MODULO DE FEEDBACK
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
        return f"Feedback de {self.interviewer} para {self.candidate} ({self.get_feedback_type_display()})"
        
    def get_status_display(self):
        return dict(FEEDBACK_STATUS_CHOICES).get(self.status, self.status)
        
    def get_result_display(self, field):
        return dict(FEEDBACK_RESULT_CHOICES).get(getattr(self, field), getattr(self, field))
        
    def mark_as_completed(self):
        self.status = 'COMPLETED'
        self.save()
        
    def skip_feedback(self):
        self.status = 'SKIPPED'
        self.save()

class Service(models.Model):
    """Modelo principal para servicios ofrecidos por las unidades de negocio."""
    
    SERVICE_TYPE_CHOICES = [
        ('recruitment', 'Reclutamiento Especializado'),
        ('executive_search', 'Búsqueda de Ejecutivos'),
        ('talent_analysis', 'Análisis de Talento 360°'),
        ('consulting', 'Consultoría de HR'),
        ('outplacement', 'Outplacement'),
        ('training', 'Capacitación'),
        ('verification', 'Verificación de Antecedentes'),
        ('assessment', 'Evaluación de Competencias'),
        ('other', 'Otro Servicio'),
    ]
    
    BILLING_TYPE_CHOICES = [
        ('fixed', 'Precio Fijo'),
        ('hourly', 'Por Hora'),
        ('daily', 'Por Día'),
        ('monthly', 'Por Mes'),
        ('project', 'Por Proyecto'),
        ('percentage', 'Porcentaje'),
        ('recurring', 'Recurrente'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Activo'),
        ('inactive', 'Inactivo'),
        ('draft', 'Borrador'),
        ('archived', 'Archivado'),
    ]
    
    # Información básica
    name = models.CharField(max_length=200, help_text="Nombre del servicio")
    description = models.TextField(help_text="Descripción detallada del servicio")
    service_type = models.CharField(
        max_length=50, 
        choices=SERVICE_TYPE_CHOICES,
        help_text="Tipo de servicio"
    )
    billing_type = models.CharField(
        max_length=20,
        choices=BILLING_TYPE_CHOICES,
        help_text="Tipo de facturación"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        help_text="Estado del servicio"
    )
    
    # Pricing
    base_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Precio base del servicio"
    )
    currency = models.CharField(
        max_length=3,
        default='MXN',
        help_text="Moneda del precio"
    )
    pricing_config = models.JSONField(
        default=dict,
        help_text="Configuración específica de precios"
    )
    
    # Business Unit
    business_unit = models.ForeignKey(
        'BusinessUnit',
        on_delete=models.CASCADE,
        related_name='services',
        help_text="Unidad de negocio que ofrece el servicio"
    )
    
    # Características
    features = models.JSONField(
        default=list,
        help_text="Lista de características del servicio"
    )
    requirements = models.JSONField(
        default=list,
        help_text="Requisitos para el servicio"
    )
    deliverables = models.JSONField(
        default=list,
        help_text="Entregables del servicio"
    )
    
    # Configuración de pagos
    payment_terms = models.CharField(
        max_length=50,
        default='net30',
        help_text="Términos de pago"
    )
    payment_methods = models.JSONField(
        default=list,
        help_text="Métodos de pago aceptados"
    )
    
    # Configuración de hitos
    default_milestones = models.JSONField(
        default=list,
        help_text="Hitos de pago por defecto"
    )
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_services'
    )
    
    class Meta:
        verbose_name = "Servicio"
        verbose_name_plural = "Servicios"
        ordering = ['name']
        indexes = [
            models.Index(fields=['service_type', 'status']),
            models.Index(fields=['business_unit', 'status']),
            models.Index(fields=['billing_type']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.business_unit.name}"
    
    def get_pricing_config(self, key=None, default=None):
        """Obtiene configuración de precios"""
        if key is None:
            return self.pricing_config
        return self.pricing_config.get(key, default)
    
    def set_pricing_config(self, key, value):
        """Establece configuración de precios"""
        self.pricing_config[key] = value
        self.save()
    
    def calculate_price(self, **kwargs):
        """Calcula el precio del servicio según el tipo de facturación"""
        if self.billing_type == 'fixed':
            return self.base_price
        elif self.billing_type == 'hourly':
            hours = kwargs.get('hours', 1)
            return self.base_price * hours
        elif self.billing_type == 'daily':
            days = kwargs.get('days', 1)
            return self.base_price * days
        elif self.billing_type == 'monthly':
            months = kwargs.get('months', 1)
            return self.base_price * months
        elif self.billing_type == 'percentage':
            base_amount = kwargs.get('base_amount', 0)
            return (self.base_price * base_amount) / 100
        elif self.billing_type == 'recurring':
            cycles = kwargs.get('cycles', 1)
            return self.base_price * cycles
        else:
            return self.base_price
    
    def is_available_for(self, business_unit):
        """Verifica si el servicio está disponible para una unidad de negocio"""
        return self.business_unit == business_unit and self.status == 'active'
    
    def get_payment_schedule(self, total_amount, payment_structure='standard'):
        """Genera un calendario de pagos para el servicio"""
        from app.ats.pricing.progressive_billing import ProgressiveBilling
        
        return ProgressiveBilling.generate_payment_schedule(
            business_unit_name=self.business_unit.name,
            start_date=timezone.now().date(),
            contract_amount=total_amount,
            service_type=self.service_type
        )

class EnhancedNetworkGamificationProfile(models.Model):
    """
    Perfil avanzado de gamificación para cada persona.
    Unifica puntos, nivel, experiencia, logros, badges, engagement, historial y timestamps.
    """
    person = models.OneToOneField('Person', on_delete=models.CASCADE, related_name='enhancednetworkgamificationprofile')
    points = models.IntegerField(default=0)
    level = models.IntegerField(default=1)
    experience = models.IntegerField(default=0)
    skill_endorsements = models.IntegerField(default=0)
    network_expansion_level = models.IntegerField(default=0)
    badges = models.ManyToManyField('Badge', blank=True, related_name='gamification_profiles')
    achievements = models.JSONField(default=list, blank=True, help_text="Lista de logros desbloqueados")
    engagement_score = models.FloatField(default=0.0)
    last_activity = models.DateTimeField(auto_now=True)
    history = models.JSONField(default=list, blank=True, help_text="Historial de actividades de gamificación")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def award_points(self, points, reason=None, metadata=None):
        self.points += points
        self.experience += points
        self.save()
        if reason or metadata:
            self.add_history('award_points', points, reason, metadata)

    def update_profile(self, skills=None, experience=None, education=None):
        # Lógica para actualizar perfil gamificado
        self.last_activity = timezone.now()
        self.save()
        self.add_history('update_profile', 0, 'profile_update', {'skills': skills, 'experience': experience, 'education': education})

    def check_achievements(self):
        # Lógica para verificar logros (placeholder, implementar según reglas)
        return []

    def award_achievements(self, achievements):
        for ach in achievements:
            if ach not in self.achievements:
                self.achievements.append(ach)
        self.save()
        self.add_history('award_achievements', 0, 'achievement', {'achievements': achievements})

    def update_ranking(self):
        # Lógica para actualizar ranking global (placeholder)
        pass

    def add_history(self, action, points, reason, metadata):
        entry = {
            'timestamp': timezone.now().isoformat(),
            'action': action,
            'points': points,
            'reason': reason,
            'metadata': metadata
        }
        self.history.append(entry)
        self.save()

    class Meta:
        verbose_name = "Perfil de Gamificación Avanzado"
        verbose_name_plural = "Perfiles de Gamificación Avanzados"
        indexes = [
            models.Index(fields=['points', 'level']),
            models.Index(fields=['engagement_score']),
        ]

    def __str__(self):
        return f"Gamificación de {self.person}"

# --- MIGRACIÓN TEMPORAL PARA CAMPOS META VERIFIED ---
def migrate_meta_verified_to_channels():
    from app.models import BusinessUnit, WhatsAppAPI, MessengerAPI, InstagramAPI
    for bu in BusinessUnit.objects.all():
        if hasattr(bu, 'meta_verified') and (
            bu.meta_verified or bu.meta_verified_since or bu.meta_verified_badge_url
        ):
            # WhatsApp
            wa = WhatsAppAPI.objects.filter(business_unit=bu).first()
            if wa:
                wa.meta_verified = bu.meta_verified
                wa.meta_verified_since = bu.meta_verified_since
                wa.meta_verified_badge_url = bu.meta_verified_badge_url
                wa.save()
            # Messenger
            ms = MessengerAPI.objects.filter(business_unit=bu).first()
            if ms:
                ms.meta_verified = bu.meta_verified
                ms.meta_verified_since = bu.meta_verified_since
                ms.meta_verified_badge_url = bu.meta_verified_badge_url
                ms.save()
            # Instagram
            ig = InstagramAPI.objects.filter(business_unit=bu).first()
            if ig:
                ig.meta_verified = bu.meta_verified
                ig.meta_verified_since = bu.meta_verified_since
                ig.meta_verified_badge_url = bu.meta_verified_badge_url
                ig.save()

class OffLimitsServiceType(Enum):
    HUMAN = "humano"
    HYBRID = "hibrido"
    AI = "ai"

class OffLimitsBusinessUnit(Enum):
    EXECUTIVE = "huntRED_executive"
    HUNTRED = "huntRED"
    HUNTU = "huntU"
    AMIGRO = "amigro"

# Tabla de períodos en meses
OFFLIMITS_PERIODS = {
    (OffLimitsBusinessUnit.EXECUTIVE.value, OffLimitsServiceType.HUMAN.value): 12,
    (OffLimitsBusinessUnit.EXECUTIVE.value, OffLimitsServiceType.HYBRID.value): 9,
    (OffLimitsBusinessUnit.EXECUTIVE.value, OffLimitsServiceType.AI.value): 8,
    (OffLimitsBusinessUnit.HUNTRED.value, OffLimitsServiceType.HUMAN.value): 12,
    (OffLimitsBusinessUnit.HUNTRED.value, OffLimitsServiceType.HYBRID.value): 6,
    (OffLimitsBusinessUnit.HUNTRED.value, OffLimitsServiceType.AI.value): 4,
    (OffLimitsBusinessUnit.HUNTU.value, OffLimitsServiceType.AI.value): 4,
    (OffLimitsBusinessUnit.AMIGRO.value, OffLimitsServiceType.AI.value): 3,
}

def calculate_offlimits_end_date(start_date, bu, service_type):
    months = OFFLIMITS_PERIODS.get((bu, service_type), 0)
    if months == 0:
        return start_date
    # Sumar meses a la fecha de inicio
    year = start_date.year + ((start_date.month - 1 + months) // 12)
    month = ((start_date.month - 1 + months) % 12) + 1
    day = min(start_date.day, 28)  # Evitar problemas con meses cortos
    return start_date.replace(year=year, month=month, day=day)

class OffLimitsRestriction(models.Model):
    company = models.ForeignKey('Company', on_delete=models.CASCADE, related_name='offlimits_restrictions')
    business_unit = models.CharField(max_length=32, choices=[(tag.value, tag.name) for tag in OffLimitsBusinessUnit])
    service_type = models.CharField(max_length=16, choices=[(tag.value, tag.name) for tag in OffLimitsServiceType])
    # El periodo inicia con el inicio del servicio de reclutamiento
    start_date = models.DateField(help_text="Fecha de inicio del servicio de reclutamiento (inicio del OffLimits)")
    end_date = models.DateField()
    process = models.ForeignKey('RecruitmentProcess', on_delete=models.CASCADE, related_name='offlimits_restrictions')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Restricción OffLimits"
        verbose_name_plural = "Restricciones OffLimits"
        indexes = [
            models.Index(fields=['company', 'business_unit', 'service_type', 'is_active']),
            models.Index(fields=['end_date']),
        ]
        unique_together = ('company', 'business_unit', 'service_type', 'process')

    def save(self, *args, **kwargs):
        if not self.end_date:
            self.end_date = calculate_offlimits_end_date(self.start_date, self.business_unit, self.service_type)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"OffLimits: {self.company} ({self.business_unit}, {self.service_type}) desde {self.start_date} hasta {self.end_date}"

# Constantes para feedback de clientes
CLIENT_FEEDBACK_PERIODS = [30, 90, 180, 365]  # Días para encuestas periódicas

class ClientFeedback(models.Model):
    """
    Modelo para encuestas de satisfacción de clientes.
    Permite medir la satisfacción del cliente con los servicios proporcionados.
    """
    
    STATUS_CHOICES = [
        ('PENDING', 'Pendiente'),
        ('SENT', 'Enviada'),
        ('COMPLETED', 'Completada'),
        ('EXPIRED', 'Expirada'),
        ('CANCELLED', 'Cancelada')
    ]
    
    # Relaciones principales
    empresa = models.ForeignKey(
        'Company',
        on_delete=models.CASCADE,
        related_name='client_feedbacks',
        help_text="Empresa cliente"
    )
    
    business_unit = models.ForeignKey(
        'BusinessUnit',
        on_delete=models.CASCADE,
        related_name='client_feedbacks',
        help_text="Unidad de negocio responsable"
    )
    
    respondent = models.ForeignKey(
        'Person',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='client_feedback_responses',
        help_text="Persona que responde la encuesta"
    )
    
    consultant = models.ForeignKey(
        'Person',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='client_feedback_consultations',
        help_text="Consultor responsable del servicio"
    )
    
    # Configuración de la encuesta
    period_days = models.IntegerField(
        default=30,
        help_text="Período en días desde el inicio del servicio"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING',
        help_text="Estado de la encuesta"
    )
    
    # Datos de envío
    token = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        help_text="Token de seguridad para la encuesta"
    )
    
    sent_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha de envío de la encuesta"
    )
    
    completed_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha de completado de la encuesta"
    )
    
    # Respuestas de la encuesta
    overall_satisfaction = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Satisfacción general (1-10)"
    )
    
    service_quality = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Calidad del servicio (1-10)"
    )
    
    communication = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Comunicación (1-10)"
    )
    
    value_for_money = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Relación calidad-precio (1-10)"
    )
    
    would_recommend = models.BooleanField(
        null=True,
        blank=True,
        help_text="¿Recomendaría nuestros servicios?"
    )
    
    # Comentarios
    positive_comments = models.TextField(
        blank=True,
        null=True,
        help_text="Aspectos positivos del servicio"
    )
    
    improvement_suggestions = models.TextField(
        blank=True,
        null=True,
        help_text="Sugerencias de mejora"
    )
    
    additional_comments = models.TextField(
        blank=True,
        null=True,
        help_text="Comentarios adicionales"
    )
    
    # Métricas calculadas
    satisfaction_score = models.FloatField(
        null=True,
        blank=True,
        help_text="Puntuación promedio de satisfacción"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Feedback de Cliente"
        verbose_name_plural = "Feedbacks de Clientes"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['empresa', 'business_unit']),
            models.Index(fields=['status']),
            models.Index(fields=['sent_date']),
            models.Index(fields=['completed_date']),
        ]
    
    def __str__(self):
        return f"Feedback de {self.empresa.name} - {self.get_status_display()}"
    
    def calculate_satisfaction_score(self):
        """Calcula la puntuación promedio de satisfacción."""
        scores = []
        if self.overall_satisfaction:
            scores.append(self.overall_satisfaction)
        if self.service_quality:
            scores.append(self.service_quality)
        if self.communication:
            scores.append(self.communication)
        if self.value_for_money:
            scores.append(self.value_for_money)
        
        if scores:
            self.satisfaction_score = sum(scores) / len(scores)
            self.save(update_fields=['satisfaction_score'])
        
        return self.satisfaction_score
    
    def mark_as_sent(self):
        """Marca la encuesta como enviada."""
        self.status = 'SENT'
        self.sent_date = timezone.now()
        self.save(update_fields=['status', 'sent_date'])
    
    def mark_as_completed(self):
        """Marca la encuesta como completada."""
        self.status = 'COMPLETED'
        self.completed_date = timezone.now()
        self.calculate_satisfaction_score()
        self.save(update_fields=['status', 'completed_date', 'satisfaction_score'])
    
    def is_expired(self):
        """Verifica si la encuesta ha expirado (30 días desde el envío)."""
        if not self.sent_date:
            return False
        return timezone.now() > self.sent_date + timedelta(days=30)
    
    def get_satisfaction_level(self):
        """Obtiene el nivel de satisfacción basado en la puntuación."""
        if not self.satisfaction_score:
            return None
        
        if self.satisfaction_score >= 9:
            return 'excellent'
        elif self.satisfaction_score >= 7:
            return 'good'
        elif self.satisfaction_score >= 5:
            return 'fair'
        else:
            return 'poor'


class ClientFeedbackSchedule(models.Model):
    """
    Modelo para programar encuestas de satisfacción de clientes.
    Permite configurar encuestas periódicas para cada cliente.
    """
    
    # Relaciones
    empresa = models.ForeignKey(
        'Company',
        on_delete=models.CASCADE,
        related_name='feedback_schedules',
        help_text="Empresa cliente"
    )
    
    business_unit = models.ForeignKey(
        'BusinessUnit',
        on_delete=models.CASCADE,
        related_name='feedback_schedules',
        help_text="Unidad de negocio responsable"
    )
    
    # Configuración de la programación
    start_date = models.DateTimeField(
        help_text="Fecha de inicio de la relación de servicio"
    )
    
    next_feedback_date = models.DateTimeField(
        help_text="Próxima fecha para enviar encuesta"
    )
    
    period_days = models.IntegerField(
        default=30,
        help_text="Período en días entre encuestas"
    )
    
    current_period_index = models.IntegerField(
        default=0,
        help_text="Índice del período actual en CLIENT_FEEDBACK_PERIODS"
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="¿La programación está activa?"
    )
    
    # Configuración adicional
    auto_send = models.BooleanField(
        default=True,
        help_text="¿Enviar encuestas automáticamente?"
    )
    
    reminder_enabled = models.BooleanField(
        default=True,
        help_text="¿Habilitar recordatorios?"
    )
    
    reminder_days = models.IntegerField(
        default=7,
        help_text="Días antes de enviar recordatorio"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Programación de Feedback de Cliente"
        verbose_name_plural = "Programaciones de Feedback de Clientes"
        unique_together = ['empresa', 'business_unit']
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['empresa', 'business_unit']),
            models.Index(fields=['next_feedback_date']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"Programación de feedback para {self.empresa.name} - {self.business_unit.name}"
    
    def advance_to_next_period(self):
        """Avanza al siguiente período de feedback."""
        self.current_period_index += 1
        
        # Si hemos completado todos los períodos, volver al primero
        if self.current_period_index >= len(CLIENT_FEEDBACK_PERIODS):
            self.current_period_index = 0
        
        # Calcular la próxima fecha
        self.period_days = CLIENT_FEEDBACK_PERIODS[self.current_period_index]
        self.next_feedback_date = timezone.now() + timedelta(days=self.period_days)
        
        self.save(update_fields=[
            'current_period_index', 
            'period_days', 
            'next_feedback_date'
        ])
    
    def is_due_for_feedback(self):
        """Verifica si es momento de enviar una encuesta."""
        return timezone.now() >= self.next_feedback_date
    
    def get_days_until_next_feedback(self):
        """Obtiene los días hasta la próxima encuesta."""
        if self.next_feedback_date:
            delta = self.next_feedback_date - timezone.now()
            return max(0, delta.days)
        return 0
    
    def deactivate(self):
        """Desactiva la programación."""
        self.is_active = False
        self.save(update_fields=['is_active'])
    
    def reactivate(self):
        """Reactiva la programación."""
        self.is_active = True
        self.save(update_fields=['is_active'])


class Metric(models.Model):
    """
    Modelo para almacenar métricas del sistema.
    Utilizado por app.ats.integrations.services.document.py y otros componentes de analítica.
    """
    name = models.CharField(max_length=100, help_text="Nombre de la métrica")
    category = models.CharField(
        max_length=50, 
        help_text="Categoría de la métrica (ej: rendimiento, sistema, negocio)",
        blank=True
    )
    value = models.FloatField(help_text="Valor numérico de la métrica")
    value_type = models.CharField(
        max_length=50,
        choices=[
            ('PERCENTAGE', 'Porcentaje'),
            ('COUNT', 'Conteo'),
            ('TIME', 'Tiempo'),
            ('CURRENCY', 'Moneda'),
            ('SCORE', 'Puntuación'),
            ('OTHER', 'Otro')
        ],
        default='COUNT',
        help_text="Tipo de valor de la métrica"
    )
    entity_type = models.CharField(
        max_length=100, 
        help_text="Tipo de entidad relacionada",
        blank=True
    )
    entity_id = models.CharField(
        max_length=100, 
        help_text="ID de la entidad relacionada",
        blank=True
    )
    metadata = JSONField(
        default=dict, 
        blank=True,
        help_text="Metadatos adicionales en formato JSON"
    )
    timestamp = models.DateTimeField(
        default=timezone.now,
        help_text="Momento en que se registró la métrica"
    )
    expires_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="Fecha opcional de expiración para la métrica"
    )
    business_unit = models.ForeignKey(
        'BusinessUnit',
        on_delete=models.CASCADE,
        related_name='metrics',
        null=True,
        blank=True,
        help_text="Unidad de negocio asociada (opcional)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Métrica"
        verbose_name_plural = "Métricas"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['name', 'category']),
            models.Index(fields=['entity_type', 'entity_id']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['business_unit']),
        ]
    
    def __str__(self):
        return f"{self.name}: {self.value} ({self.category})"
    
    def is_expired(self):
        """Verifica si la métrica ha expirado"""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False
    
    @classmethod
    def record(cls, name, value, category='', entity_type='', entity_id='', **kwargs):
        """Método de conveniencia para registrar una nueva métrica rápidamente"""
        metric = cls(
            name=name,
            value=value,
            category=category,
            entity_type=entity_type,
            entity_id=entity_id,
            **kwargs
        )
        metric.save()
        return metric


class Consultant(models.Model):
    """
    Modelo para almacenar información de consultores.
    Utilizado por app.ats.utils.google_calendar y otros componentes del sistema.
    """
    # Relaciones principales
    user = models.OneToOneField(
        'User', 
        on_delete=models.CASCADE,
        related_name='consultant_profile',
        help_text="Usuario asociado al consultor"
    )
    business_unit = models.ForeignKey(
        'BusinessUnit',
        on_delete=models.CASCADE,
        related_name='consultants',
        help_text="Unidad de negocio a la que pertenece el consultor"
    )
    
    # Campos básicos
    consultant_id = models.CharField(
        max_length=50,
        unique=True,
        help_text="ID único del consultor en el sistema"
    )
    title = models.CharField(
        max_length=100,
        help_text="Cargo o título del consultor",
        blank=True
    )
    department = models.CharField(
        max_length=100,
        help_text="Departamento al que pertenece",
        blank=True
    )
    is_senior = models.BooleanField(
        default=False,
        help_text="Indica si el consultor tiene rango senior"
    )
    specialties = models.JSONField(
        default=list,
        blank=True,
        help_text="Especialidades y áreas de experiencia del consultor"
    )
    
    # Configuraciones y preferencias
    calendar_settings = models.JSONField(
        default=dict,
        blank=True,
        help_text="Configuraciones de calendario y disponibilidad"
    )
    notification_settings = models.JSONField(
        default=dict,
        blank=True,
        help_text="Configuraciones de notificaciones"
    )
    google_credentials = models.TextField(
        blank=True,
        null=True,
        help_text="Credenciales de Google Calendar (encriptadas)"
    )
    
    # Campos de seguimiento
    active = models.BooleanField(
        default=True,
        help_text="Indica si el consultor está activo"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Consultor"
        verbose_name_plural = "Consultores"
        ordering = ['business_unit', '-is_senior', 'user__first_name']
        indexes = [
            models.Index(fields=['consultant_id']),
            models.Index(fields=['business_unit', 'is_senior']),
            models.Index(fields=['active']),
        ]
    
    def __str__(self):
        if hasattr(self, 'user') and self.user:
            return f"{self.user.get_full_name()} ({self.consultant_id})"
        return f"Consultor {self.consultant_id}"
    
    def get_calendar_credentials(self):
        """Obtiene las credenciales de calendario de Google"""
        if not self.google_credentials:
            return None
        
        try:
            # Aquí iría la lógica de descifrado si estuvieran encriptadas
            return self.google_credentials
        except Exception as e:
            logger.error(f"Error al obtener credenciales de calendario: {e}")
            return None
    
    def set_calendar_credentials(self, credentials):
        """Establece las credenciales de calendario de Google"""
        try:
            # Aquí iría la lógica de cifrado si fuera necesario
            self.google_credentials = credentials
            self.save(update_fields=['google_credentials', 'updated_at'])
            return True
        except Exception as e:
            logger.error(f"Error al guardar credenciales de calendario: {e}")
            return False


class NotificationPreference(models.Model):
    """
    Modelo para almacenar preferencias de notificación de usuarios.
    Utilizado principalmente para notificaciones relacionadas con slots de calendario y citas.
    """
    # Relaciones principales
    person = models.ForeignKey(
        'Person',
        on_delete=models.CASCADE,
        related_name='notification_preferences',
        help_text="Persona a la que pertenecen estas preferencias de notificación"
    )
    business_unit = models.ForeignKey(
        'BusinessUnit',
        on_delete=models.CASCADE,
        related_name='notification_preferences',
        null=True,
        blank=True,
        help_text="Unidad de negocio asociada a estas preferencias"
    )
    
    # Preferencias de notificación para slots de calendario
    notify_on_slot_available = models.BooleanField(
        default=False,
        help_text="Notificar cuando hay slots disponibles"
    )
    notify_on_slot_change = models.BooleanField(
        default=True,
        help_text="Notificar cuando hay cambios en los slots reservados"
    )
    notify_on_interview_reminder = models.BooleanField(
        default=True,
        help_text="Enviar recordatorios de entrevistas"
    )
    preferred_channels = models.JSONField(
        default=list,
        help_text="Canales preferidos para las notificaciones ['whatsapp', 'email', 'sms']"
    )
    
    # Detalles de la vacante/proceso relevante (si aplica)
    vacante = models.ForeignKey(
        'Vacante',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notification_preferences',
        help_text="Vacante asociada a estas preferencias de notificación"
    )
    preferred_days = models.JSONField(
        default=list,
        blank=True,
        help_text="Días preferidos para entrevistas ['MON', 'TUE', 'WED', 'THU', 'FRI']"
    )
    preferred_time_ranges = models.JSONField(
        default=list,
        blank=True,
        help_text="Rangos horarios preferidos [{'start': '09:00', 'end': '12:00'}, ...]"
    )
    
    # Seguimiento
    last_notification = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Última vez que se envió una notificación"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Preferencia de notificación"
        verbose_name_plural = "Preferencias de notificación"
        unique_together = [('person', 'vacante')]
        indexes = [
            models.Index(fields=['person']),
            models.Index(fields=['notify_on_slot_available']),
            models.Index(fields=['last_notification']),
        ]
    
    def __str__(self):
        return f"Preferencias de notificación: {self.person.name if hasattr(self.person, 'name') else 'Usuario'}"
    
    def update_last_notification(self):
        """Actualiza la marca de tiempo de la última notificación"""
        from django.utils import timezone
        self.last_notification = timezone.now()
        self.save(update_fields=['last_notification', 'updated_at'])
        return True

class Placement(models.Model):
    """Modelo para colocaciones de candidatos."""
    candidate = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='placements')
    position = models.ForeignKey(Vacante, on_delete=models.CASCADE, related_name='placements')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='placements')
    
    # Datos de colocación
    salary = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    
    # Estatus y seguimiento
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('active', 'Activo'),
        ('completed', 'Completado'),
        ('cancelled', 'Cancelado')
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.SET_NULL, null=True, blank=True)


class Addons(models.Model):
    """Modelo para complementos (addons) de precios."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, verbose_name="Nombre")
    description = models.TextField(blank=True, verbose_name="Descripción")
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(0)],
        verbose_name="Precio"
    )
    max_per_vacancy = models.PositiveIntegerField(
        default=1,
        verbose_name="Máximo por vacante",
        help_text="Número máximo de este complemento que se puede aplicar a una vacante"
    )
    active = models.BooleanField(default=True, verbose_name="Activo")
    for_ai_model = models.BooleanField(
        default=False, 
        verbose_name="Para modelo AI",
        help_text="Indica si este complemento es específico para el modelo de precios basado en AI"
    )
    bu = models.ForeignKey(
        BusinessUnit, 
        on_delete=models.CASCADE, 
        verbose_name="Unidad de negocio",
        related_name="addons"
    )
    
    # Configuración específica del addon (opcional)
    config = models.JSONField(default=dict, blank=True, verbose_name="Configuración")
    
    # Campos de auditoría
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creado")
    last_updated = models.DateTimeField(auto_now=True, verbose_name="Última actualización")
    
    class Meta:
        verbose_name = "Complemento"
        verbose_name_plural = "Complementos"
        ordering = ['name']
        indexes = [
            models.Index(fields=['active']),
            models.Index(fields=['for_ai_model']),
            models.Index(fields=['bu', 'active']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.price}"


# Alias para Payment como Pago para mantener compatibilidad con código existente
Pago = Payment  # Este alias permite importar 'Pago' desde app.models

class INCODEVerification(models.Model):
    """
    Modelo para verificaciones de identidad con INCODE.
    Addon premium para verificación biométrica y de documentos.
    """
    candidate = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='incode_verifications')
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE, related_name='incode_verifications')
    
    # Tipo de verificación
    verification_type = models.CharField(max_length=50, choices=[
        ('identity', 'Verificación de Identidad'),
        ('document', 'Verificación de Documento'),
        ('biometric', 'Verificación Biométrica'),
        ('comprehensive', 'Verificación Integral'),
        ('liveness', 'Detección de Vida'),
        ('face_match', 'Coincidencia Facial')
    ], default='identity')
    
    # Estado del proceso
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pendiente'),
        ('in_progress', 'En progreso'),
        ('completed', 'Completado'),
        ('failed', 'Fallido'),
        ('expired', 'Expirado')
    ], default='pending')
    
    # Resultados y métricas
    confidence_score = models.FloatField(null=True, blank=True, help_text="Puntuación de confianza (0-1)")
    risk_score = models.FloatField(null=True, blank=True, help_text="Puntuación de riesgo (0-1)")
    verification_data = models.JSONField(default=dict, help_text="Datos de verificación de INCODE")
    results = models.JSONField(default=dict, help_text="Resultados detallados")
    
    # Documentos y archivos
    document_front = models.FileField(upload_to='incode/documents/', null=True, blank=True)
    document_back = models.FileField(upload_to='incode/documents/', null=True, blank=True)
    selfie_image = models.FileField(upload_to='incode/selfies/', null=True, blank=True)
    
    # Información del documento
    document_type = models.CharField(max_length=50, choices=[
        ('ine', 'INE/IFE'),
        ('passport', 'Pasaporte'),
        ('driver_license', 'Licencia de Conducir'),
        ('curp', 'CURP'),
        ('other', 'Otro')
    ], null=True, blank=True)
    document_number = models.CharField(max_length=50, null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Metadata
    incode_session_id = models.CharField(max_length=255, null=True, blank=True)
    webhook_received = models.BooleanField(default=False)
    retry_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        verbose_name = "Verificación INCODE"
        verbose_name_plural = "Verificaciones INCODE"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['candidate', 'status']),
            models.Index(fields=['business_unit', 'status']),
            models.Index(fields=['created_at', 'status']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"INCODE {self.verification_type} - {self.candidate} ({self.status})"
    
    def is_expired(self):
        """Verifica si la verificación ha expirado."""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False
    
    def get_confidence_level(self):
        """Obtiene el nivel de confianza en texto."""
        if not self.confidence_score:
            return "No disponible"
        
        if self.confidence_score >= 0.9:
            return "Muy Alto"
        elif self.confidence_score >= 0.8:
            return "Alto"
        elif self.confidence_score >= 0.7:
            return "Medio"
        elif self.confidence_score >= 0.6:
            return "Bajo"
        else:
            return "Muy Bajo"
    
    def get_risk_level(self):
        """Obtiene el nivel de riesgo en texto."""
        if not self.risk_score:
            return "No evaluado"
        
        if self.risk_score <= 0.2:
            return "Muy Bajo"
        elif self.risk_score <= 0.4:
            return "Bajo"
        elif self.risk_score <= 0.6:
            return "Medio"
        elif self.risk_score <= 0.8:
            return "Alto"
        else:
            return "Muy Alto"
    
    def calculate_price(self):
        """Calcula el precio basado en el tipo de verificación."""
        pricing = {
            'identity': 50.00,
            'document': 75.00,
            'biometric': 100.00,
            'comprehensive': 150.00,
            'liveness': 25.00,
            'face_match': 30.00
        }
        return pricing.get(self.verification_type, 50.00)

# ============================================================================
# MODELOS DE FEEDBACK COMPLETO
# ============================================================================

class Interview(models.Model):
    """Entrevista de candidato."""
    INTERVIEW_TYPES = [
        ('phone_screen', 'Preselección telefónica'),
        ('technical', 'Entrevista técnica'),
        ('behavioral', 'Entrevista conductual'),
        ('cultural', 'Entrevista cultural'),
        ('final', 'Entrevista final'),
        ('panel', 'Entrevista panel'),
        ('case_study', 'Estudio de caso'),
        ('coding', 'Prueba de programación'),
        ('presentation', 'Presentación'),
    ]
    
    STATUS_CHOICES = [
        ('scheduled', 'Programada'),
        ('in_progress', 'En progreso'),
        ('completed', 'Completada'),
        ('cancelled', 'Cancelada'),
        ('no_show', 'No se presentó'),
    ]
    
    candidate = models.ForeignKey('Person', on_delete=models.CASCADE, related_name='interviews')
    job = models.ForeignKey('Vacante', on_delete=models.CASCADE, related_name='interviews')
    interviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='interviews_conducted')
    interview_type = models.CharField(max_length=20, choices=INTERVIEW_TYPES)
    scheduled_date = models.DateTimeField()
    duration = models.IntegerField(help_text='Duración en minutos')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    location = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-scheduled_date']
    
    def __str__(self):
        return f"Entrevista {self.candidate.nombre} - {self.job.titulo}"

class InterviewFeedback(models.Model):
    """Feedback detallado de una entrevista."""
    HIRING_DECISIONS = [
        ('hire', 'Contratar'),
        ('no_hire', 'No contratar'),
        ('maybe', 'Considerar'),
        ('strong_hire', 'Contratar definitivamente'),
        ('strong_no_hire', 'No contratar definitivamente'),
    ]
    
    interview = models.OneToOneField(Interview, on_delete=models.CASCADE, related_name='feedback')
    interviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='interview_feedbacks')
    
    # Ratings principales
    overall_rating = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    technical_skills_rating = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    communication_rating = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    cultural_fit_rating = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    problem_solving_rating = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    
    # Evaluación cualitativa
    strengths = models.TextField(blank=True)
    weaknesses = models.TextField(blank=True)
    recommendations = models.TextField(blank=True)
    hiring_decision = models.CharField(max_length=20, choices=HIRING_DECISIONS)
    next_steps = models.TextField(blank=True)
    additional_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Feedback {self.interview.candidate.nombre} - {self.interview.job.titulo}"

class CompetencyEvaluation(models.Model):
    """Evaluación de competencias específicas en una entrevista."""
    feedback = models.ForeignKey(InterviewFeedback, on_delete=models.CASCADE, related_name='competency_evaluations')
    competency_name = models.CharField(max_length=100)
    rating = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    comments = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.competency_name} - {self.rating}/5"

class CandidateFeedback(models.Model):
    """Feedback general de un candidato (no específico de entrevista)."""
    candidate = models.ForeignKey('Person', on_delete=models.CASCADE, related_name='general_feedbacks')
    evaluator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='candidate_feedbacks')
    evaluation_date = models.DateTimeField(auto_now_add=True)
    
    # Evaluaciones
    overall_impression = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    technical_competence = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    communication_skills = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    teamwork_ability = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    problem_solving = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    learning_ability = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    cultural_fit = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    
    # Comentarios
    strengths = models.TextField(blank=True)
    areas_for_improvement = models.TextField(blank=True)
    recommendations = models.TextField(blank=True)
    would_recommend = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-evaluation_date']
    
    def __str__(self):
        return f"Feedback {self.candidate.nombre} - {self.evaluator.get_full_name()}"

class RecruitmentProcess(models.Model):
    """Proceso de reclutamiento completo."""
    STATUS_CHOICES = [
        ('active', 'Activo'),
        ('completed', 'Completado'),
        ('cancelled', 'Cancelado'),
        ('on_hold', 'En pausa'),
    ]
    
    job = models.ForeignKey('Vacante', on_delete=models.CASCADE, related_name='recruitment_processes')
    recruiter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='managed_processes')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True, blank=True)
    target_positions = models.IntegerField(default=1)
    filled_positions = models.IntegerField(default=0)
    total_candidates = models.IntegerField(default=0)
    total_interviews = models.IntegerField(default=0)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-start_date']
    
    def __str__(self):
        return f"Proceso {self.job.titulo} - {self.recruiter.get_full_name()}"

class ProcessFeedback(models.Model):
    """Feedback sobre el proceso de reclutamiento."""
    process = models.ForeignKey(RecruitmentProcess, on_delete=models.CASCADE, related_name='feedbacks')
    evaluator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='process_feedbacks')
    
    # Evaluaciones del proceso
    overall_satisfaction = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    communication_quality = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    process_efficiency = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    candidate_experience = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    transparency = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    speed_of_process = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    
    # Comentarios
    what_went_well = models.TextField(blank=True)
    what_could_improve = models.TextField(blank=True)
    suggestions = models.TextField(blank=True)
    would_recommend = models.BooleanField(default=False)
    additional_comments = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Feedback proceso {self.process.job.titulo}"

class BackgroundCheck(models.Model):
    """
    Modelo para verificaciones de antecedentes.
    Freemium en básico, Premium en profundo.
    """
    candidate = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='background_checks')
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE, related_name='background_checks')
    
    # Tipo de verificación
    check_type = models.CharField(max_length=50, choices=[
        ('basic', 'Básico (Freemium)'),
        ('standard', 'Estándar'),
        ('comprehensive', 'Comprehensivo (Premium)'),
        ('executive', 'Ejecutivo'),
        ('compliance', 'Compliance')
    ], default='basic')
    
    # Estado del proceso
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pendiente'),
        ('in_progress', 'En progreso'),
        ('completed', 'Completado'),
        ('failed', 'Fallido'),
        ('cancelled', 'Cancelado')
    ], default='pending')
    
    # Resultados y métricas
    risk_score = models.FloatField(null=True, blank=True, help_text="Puntuación de riesgo (0-1)")
    trust_score = models.FloatField(null=True, blank=True, help_text="Puntuación de confianza (0-1)")
    results = models.JSONField(default=dict, help_text="Resultados detallados")
    
    # Áreas verificadas
    areas_checked = models.JSONField(default=list, help_text="Áreas verificadas")
    flags_raised = models.JSONField(default=list, help_text="Alertas encontradas")
    
    # Información del candidato para verificación
    full_name = models.CharField(max_length=255)
    date_of_birth = models.DateField()
    national_id = models.CharField(max_length=50, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Metadata
    provider = models.CharField(max_length=100, default='internal', help_text="Proveedor de verificación")
    reference_id = models.CharField(max_length=255, null=True, blank=True)
    retry_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        verbose_name = "Verificación de Antecedentes"
        verbose_name_plural = "Verificaciones de Antecedentes"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['candidate', 'status']),
            models.Index(fields=['business_unit', 'check_type']),
            models.Index(fields=['created_at', 'status']),
        ]
    
    def __str__(self):
        return f"Background Check {self.check_type} - {self.candidate} ({self.status})"
    
    def is_freemium(self):
        """Verifica si es una verificación freemium."""
        return self.check_type == 'basic'
    
    def is_premium(self):
        """Verifica si es una verificación premium."""
        return self.check_type in ['comprehensive', 'executive', 'compliance']
    
    def get_risk_level(self):
        """Obtiene el nivel de riesgo en texto."""
        if not self.risk_score:
            return "No evaluado"
        
        if self.risk_score <= 0.2:
            return "Muy Bajo"
        elif self.risk_score <= 0.4:
            return "Bajo"
        elif self.risk_score <= 0.6:
            return "Medio"
        elif self.risk_score <= 0.8:
            return "Alto"
        else:
            return "Muy Alto"
    
    def get_trust_level(self):
        """Obtiene el nivel de confianza en texto."""
        if not self.trust_score:
            return "No evaluado"
        
        if self.trust_score >= 0.8:
            return "Muy Alto"
        elif self.trust_score >= 0.6:
            return "Alto"
        elif self.trust_score >= 0.4:
            return "Medio"
        elif self.trust_score >= 0.2:
            return "Bajo"
        else:
            return "Muy Bajo"
    
    def calculate_price(self):
        """Calcula el precio basado en el tipo de verificación."""
        pricing = {
            'basic': 0.00,  # Freemium
            'standard': 25.00,
            'comprehensive': 75.00,  # Premium
            'executive': 150.00,
            'compliance': 200.00
        }
        return pricing.get(self.check_type, 0.00)
    
    def get_areas_covered(self):
        """Obtiene las áreas cubiertas según el tipo de verificación."""
        coverage = {
            'basic': ['identity_verification', 'basic_criminal_check'],
            'standard': ['identity_verification', 'criminal_check', 'employment_verification'],
            'comprehensive': ['identity_verification', 'criminal_check', 'employment_verification', 'education_verification', 'credit_check'],
            'executive': ['identity_verification', 'criminal_check', 'employment_verification', 'education_verification', 'credit_check', 'media_check', 'social_media_check'],
            'compliance': ['identity_verification', 'criminal_check', 'employment_verification', 'education_verification', 'credit_check', 'media_check', 'social_media_check', 'regulatory_check']
        }
        return coverage.get(self.check_type, [])

class VerificationPackage(models.Model):
    """
    Modelo para paquetes de verificación que combinan INCODE y Background Check.
    """
    name = models.CharField(max_length=100)
    description = models.TextField()
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE, related_name='verification_packages')
    
    # Componentes del paquete
    include_incode = models.BooleanField(default=False)
    incode_type = models.CharField(max_length=50, choices=[
        ('identity', 'Verificación de Identidad'),
        ('comprehensive', 'Verificación Integral')
    ], null=True, blank=True)
    
    include_background_check = models.BooleanField(default=False)
    background_check_type = models.CharField(max_length=50, choices=[
        ('basic', 'Básico (Freemium)'),
        ('comprehensive', 'Comprehensivo (Premium)')
    ], null=True, blank=True)
    
    # Pricing
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    is_freemium = models.BooleanField(default=False)
    
    # Características
    features = models.JSONField(default=list, help_text="Lista de características incluidas")
    delivery_time = models.PositiveIntegerField(default=24, help_text="Tiempo de entrega en horas")
    
    # Estado
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Paquete de Verificación"
        verbose_name_plural = "Paquetes de Verificación"
        ordering = ['base_price']
    
    def __str__(self):
        return f"{self.name} - {self.business_unit}"
    
    def get_total_price(self):
        """Calcula el precio total del paquete."""
        if self.is_freemium:
            return 0.00
        return self.base_price
    
    def get_features_list(self):
        """Obtiene la lista de características en texto."""
        features = []
        
        if self.include_incode:
            features.append(f"Verificación INCODE: {self.incode_type}")
        
        if self.include_background_check:
            features.append(f"Background Check: {self.background_check_type}")
        
        features.extend(self.features)
        return features

# Aliases para compatibilidad con código existente
Client = Person
Role = BusinessUnitMembership