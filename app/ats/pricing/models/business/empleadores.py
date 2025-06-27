"""
Modelos para empleadores y empleados migrados.
"""
from django.db import models
from django.utils import timezone
import uuid

from app.models import Person, BusinessUnit


class Empleador(models.Model):
    """Modelo para empleadores migrado desde el módulo anterior."""
    
    ESTADO_CHOICES = [
        ('activo', 'Activo'),
        ('inactivo', 'Inactivo'),
        ('pendiente', 'Pendiente'),
        ('suspendido', 'Suspendido'),
    ]
    
    JOB_TYPE_CHOICES = [
        ('full_time', 'Tiempo Completo'),
        ('part_time', 'Tiempo Parcial'),
        ('contract', 'Contrato'),
        ('freelance', 'Freelance'),
        ('internship', 'Prácticas'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    persona = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='empleadores')
    whatsapp = models.CharField(max_length=20, blank=True, null=True)
    
    # Información fiscal
    razon_social = models.CharField(max_length=200, help_text="Razón social de la empresa")
    rfc = models.CharField(max_length=13, blank=True, null=True, help_text="RFC de la empresa")
    direccion_fiscal = models.TextField(blank=True, null=True)
    
    # Información bancaria
    clabe = models.CharField(max_length=18, blank=True, null=True, help_text="CLABE bancaria")
    banco = models.CharField(max_length=100, blank=True, null=True, help_text="Banco")
    
    # Información de contacto
    img_company = models.ImageField(upload_to='empleadores/', blank=True, null=True)
    sitio_web = models.URLField(blank=True, null=True)
    telefono_oficina = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    
    # Estado
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='activo')
    
    # Documentos
    documento_identidad = models.FileField(upload_to='empleadores/documentos/', blank=True, null=True)
    comprobante_domicilio = models.FileField(upload_to='empleadores/documentos/', blank=True, null=True)
    
    # Campos adicionales para oportunidades
    job_id = models.CharField(max_length=100, blank=True, null=True)
    url_name = models.CharField(max_length=100, blank=True, null=True)
    salary = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    job_type = models.CharField(max_length=20, choices=JOB_TYPE_CHOICES, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    required_skills = models.TextField(blank=True, null=True)
    experience_required = models.TextField(blank=True, null=True)
    job_description = models.TextField(blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    # Fechas
    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'pricing_empleador'
        verbose_name = 'Empleador'
        verbose_name_plural = 'Empleadores'
    
    def __str__(self):
        return f"{self.razon_social} - {self.persona.nombre_completo}"
    
    @property
    def nombre_completo(self):
        """Obtiene el nombre completo del empleador."""
        return f"{self.razon_social} ({self.persona.nombre_completo})"
    
    def get_contact_info(self):
        """Obtiene información de contacto del empleador."""
        return {
            'nombre': self.razon_social,
            'persona': self.persona.nombre_completo,
            'whatsapp': self.whatsapp,
            'telefono': self.telefono_oficina,
            'email': self.persona.email,
            'sitio_web': self.sitio_web,
            'direccion': self.address,
        }
    
    def get_fiscal_info(self):
        """Obtiene información fiscal del empleador."""
        return {
            'rfc': self.rfc,
            'razon_social': self.razon_social,
            'direccion_fiscal': self.direccion_fiscal,
        }
    
    def get_bank_info(self):
        """Obtiene información bancaria del empleador."""
        return {
            'banco': self.banco,
            'clabe': self.clabe,
        }


class Empleado(models.Model):
    """Modelo para empleados migrado desde el módulo anterior."""
    
    ESTADO_CHOICES = [
        ('activo', 'Activo'),
        ('inactivo', 'Inactivo'),
        ('pendiente', 'Pendiente'),
        ('suspendido', 'Suspendido'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    persona = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='empleados')
    
    # Información laboral
    nss = models.CharField(max_length=11, blank=True, null=True, help_text="Número de Seguridad Social")
    ocupacion = models.CharField(max_length=100, blank=True, null=True, help_text="Ocupación o puesto")
    
    # Información bancaria
    clabe = models.CharField(max_length=18, blank=True, null=True, help_text="CLABE bancaria")
    banco = models.CharField(max_length=100, blank=True, null=True, help_text="Banco")
    
    # Estado
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='activo')
    
    # Fechas
    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'pricing_empleado'
        verbose_name = 'Empleado'
        verbose_name_plural = 'Empleados'
    
    def __str__(self):
        return f"{self.persona.nombre_completo} - {self.ocupacion or 'Sin ocupación'}"
    
    @property
    def nombre_completo(self):
        """Obtiene el nombre completo del empleado."""
        return self.persona.nombre_completo
    
    def get_contact_info(self):
        """Obtiene información de contacto del empleado."""
        return {
            'nombre': self.persona.nombre_completo,
            'email': self.persona.email,
            'telefono': self.persona.telefono,
            'ocupacion': self.ocupacion,
        }
    
    def get_labor_info(self):
        """Obtiene información laboral del empleado."""
        return {
            'nss': self.nss,
            'ocupacion': self.ocupacion,
            'estado': self.estado,
        }
    
    def get_bank_info(self):
        """Obtiene información bancaria del empleado."""
        return {
            'banco': self.banco,
            'clabe': self.clabe,
        } 