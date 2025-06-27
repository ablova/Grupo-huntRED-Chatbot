"""
Modelos para oportunidades y sincronización migrados.
"""
from django.db import models
from django.utils import timezone
import uuid

from app.models import BusinessUnit
from .empleadores import Empleador


class Oportunidad(models.Model):
    """Modelo para oportunidades de trabajo migrado desde el módulo anterior."""
    
    TIPO_CONTRATO_CHOICES = [
        ('indefinido', 'Indefinido'),
        ('determinado', 'Determinado'),
        ('por_obra', 'Por Obra'),
        ('temporal', 'Temporal'),
        ('practicas', 'Prácticas'),
        ('freelance', 'Freelance'),
    ]
    
    MODALIDAD_CHOICES = [
        ('presencial', 'Presencial'),
        ('remoto', 'Remoto'),
        ('hibrido', 'Híbrido'),
    ]
    
    ESTADO_CHOICES = [
        ('activo', 'Activo'),
        ('inactivo', 'Inactivo'),
        ('cerrado', 'Cerrado'),
        ('suspendido', 'Suspendido'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    titulo = models.CharField(max_length=200, help_text="Título de la oportunidad")
    descripcion = models.TextField(help_text="Descripción detallada de la oportunidad")
    empleador = models.ForeignKey(Empleador, on_delete=models.CASCADE, related_name='oportunidades')
    
    # Información del puesto
    tipo_contrato = models.CharField(max_length=20, choices=TIPO_CONTRATO_CHOICES)
    modalidad = models.CharField(max_length=20, choices=MODALIDAD_CHOICES)
    salario_minimo = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    salario_maximo = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    
    # Ubicación
    pais = models.CharField(max_length=100, default='México')
    estado = models.CharField(max_length=100, blank=True, null=True)
    ciudad = models.CharField(max_length=100, blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)
    codigo_postal = models.CharField(max_length=10, blank=True, null=True)
    
    # Requisitos
    experiencia_minima = models.CharField(max_length=100, blank=True, null=True)
    educacion_requerida = models.CharField(max_length=100, blank=True, null=True)
    habilidades_requeridas = models.TextField(blank=True, null=True)
    beneficios = models.TextField(blank=True, null=True)
    
    # Estado
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='activo')
    
    # Metadatos
    metadata = models.JSONField(default=dict, blank=True)
    
    # Fechas
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    fecha_cierre = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'pricing_oportunidad'
        verbose_name = 'Oportunidad'
        verbose_name_plural = 'Oportunidades'
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"{self.titulo} - {self.empleador.razon_social}"
    
    @property
    def salario_display(self):
        """Obtiene el rango de salario para mostrar."""
        if self.salario_minimo and self.salario_maximo:
            return f"${self.salario_minimo:,.2f} - ${self.salario_maximo:,.2f} MXN"
        elif self.salario_minimo:
            return f"Desde ${self.salario_minimo:,.2f} MXN"
        elif self.salario_maximo:
            return f"Hasta ${self.salario_maximo:,.2f} MXN"
        else:
            return "Salario a convenir"
    
    @property
    def ubicacion_display(self):
        """Obtiene la ubicación para mostrar."""
        location_parts = []
        if self.ciudad:
            location_parts.append(self.ciudad)
        if self.estado:
            location_parts.append(self.estado)
        if self.pais:
            location_parts.append(self.pais)
        
        return ", ".join(location_parts) if location_parts else "Ubicación no especificada"
    
    def get_basic_info(self):
        """Obtiene información básica de la oportunidad."""
        return {
            'id': str(self.id),
            'titulo': self.titulo,
            'empleador': self.empleador.razon_social,
            'tipo_contrato': self.tipo_contrato,
            'modalidad': self.modalidad,
            'salario': self.salario_display,
            'ubicacion': self.ubicacion_display,
            'estado': self.estado,
        }
    
    def get_full_info(self):
        """Obtiene información completa de la oportunidad."""
        return {
            'id': str(self.id),
            'titulo': self.titulo,
            'descripcion': self.descripcion,
            'empleador': {
                'razon_social': self.empleador.razon_social,
                'contacto': self.empleador.get_contact_info(),
            },
            'puesto': {
                'tipo_contrato': self.tipo_contrato,
                'modalidad': self.modalidad,
                'salario_minimo': float(self.salario_minimo) if self.salario_minimo else None,
                'salario_maximo': float(self.salario_maximo) if self.salario_maximo else None,
                'salario_display': self.salario_display,
            },
            'ubicacion': {
                'pais': self.pais,
                'estado': self.estado,
                'ciudad': self.ciudad,
                'direccion': self.direccion,
                'codigo_postal': self.codigo_postal,
                'display': self.ubicacion_display,
            },
            'requisitos': {
                'experiencia_minima': self.experiencia_minima,
                'educacion_requerida': self.educacion_requerida,
                'habilidades_requeridas': self.habilidades_requeridas,
                'beneficios': self.beneficios,
            },
            'estado': self.estado,
            'fechas': {
                'creacion': self.fecha_creacion.isoformat(),
                'actualizacion': self.fecha_actualizacion.isoformat(),
                'cierre': self.fecha_cierre.isoformat() if self.fecha_cierre else None,
            },
        }
    
    def close_opportunity(self):
        """Cierra la oportunidad."""
        self.estado = 'cerrado'
        self.fecha_cierre = timezone.now()
        self.save()
    
    def suspend_opportunity(self):
        """Suspende la oportunidad."""
        self.estado = 'suspendido'
        self.save()
    
    def activate_opportunity(self):
        """Activa la oportunidad."""
        self.estado = 'activo'
        self.save()


class PagoRecurrente(models.Model):
    """Modelo para pagos recurrentes migrado desde el módulo anterior."""
    
    FRECUENCIA_CHOICES = [
        ('semanal', 'Semanal'),
        ('quincenal', 'Quincenal'),
        ('mensual', 'Mensual'),
        ('trimestral', 'Trimestral'),
        ('semestral', 'Semestral'),
        ('anual', 'Anual'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pago_base = models.ForeignKey('app.PaymentMilestone', on_delete=models.CASCADE, related_name='pagos_recurrentes')
    frecuencia = models.CharField(max_length=20, choices=FRECUENCIA_CHOICES)
    fecha_proximo_pago = models.DateTimeField(help_text="Fecha del próximo pago")
    activo = models.BooleanField(default=True)
    
    # Metadatos
    metadata = models.JSONField(default=dict, blank=True)
    
    # Fechas
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'pricing_pago_recurrente'
        verbose_name = 'Pago Recurrente'
        verbose_name_plural = 'Pagos Recurrentes'
    
    def __str__(self):
        return f"Pago {self.pago_base.description} - {self.frecuencia}"
    
    def is_due(self):
        """Verifica si el pago está vencido."""
        return timezone.now() >= self.fecha_proximo_pago
    
    def calculate_next_payment_date(self):
        """Calcula la próxima fecha de pago."""
        from datetime import timedelta
        
        if self.frecuencia == 'semanal':
            return self.fecha_proximo_pago + timedelta(weeks=1)
        elif self.frecuencia == 'quincenal':
            return self.fecha_proximo_pago + timedelta(weeks=2)
        elif self.frecuencia == 'mensual':
            return self.fecha_proximo_pago + timedelta(days=30)
        elif self.frecuencia == 'trimestral':
            return self.fecha_proximo_pago + timedelta(days=90)
        elif self.frecuencia == 'semestral':
            return self.fecha_proximo_pago + timedelta(days=180)
        elif self.frecuencia == 'anual':
            return self.fecha_proximo_pago + timedelta(days=365)
        else:
            return self.fecha_proximo_pago + timedelta(days=30)


class SincronizacionLog(models.Model):
    """Log de sincronización con WordPress."""
    
    ESTADO_CHOICES = [
        ('EXITO', 'Éxito'),
        ('ERROR', 'Error'),
        ('PENDIENTE', 'Pendiente'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    oportunidad = models.ForeignKey(Oportunidad, on_delete=models.CASCADE, related_name='sincronizaciones')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES)
    mensaje = models.TextField(blank=True, null=True)
    
    # Metadatos de sincronización
    wordpress_post_id = models.IntegerField(blank=True, null=True)
    sync_data = models.JSONField(default=dict, blank=True)
    
    # Fechas
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'pricing_sincronizacion_log'
        verbose_name = 'Log de Sincronización'
        verbose_name_plural = 'Logs de Sincronización'
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"Sincronización {self.oportunidad.titulo} - {self.estado}"


class SincronizacionError(models.Model):
    """Errores de sincronización con WordPress."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    oportunidad = models.ForeignKey(Oportunidad, on_delete=models.CASCADE, related_name='errores_sincronizacion')
    mensaje = models.TextField(help_text="Mensaje de error")
    intento = models.IntegerField(default=1, help_text="Número de intento")
    resuelto = models.BooleanField(default=False, help_text="¿El error ha sido resuelto?")
    
    # Detalles del error
    error_type = models.CharField(max_length=100, blank=True, null=True)
    error_details = models.JSONField(default=dict, blank=True)
    
    # Fechas
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_resolucion = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'pricing_sincronizacion_error'
        verbose_name = 'Error de Sincronización'
        verbose_name_plural = 'Errores de Sincronización'
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"Error {self.oportunidad.titulo} - {self.mensaje[:50]}"
    
    def mark_as_resolved(self):
        """Marca el error como resuelto."""
        self.resuelto = True
        self.fecha_resolucion = timezone.now()
        self.save() 