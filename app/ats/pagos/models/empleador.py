from django.db import models
from django.utils import timezone
from app.models import Person

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

# Modelo para personas físicas que trabajan (empleados)
class Empleado(models.Model):
    persona = models.OneToOneField(Person, on_delete=models.CASCADE, related_name='empleado')
    
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
    documento_identidad = models.FileField(upload_to='empleados/documentos/')
    comprobante_domicilio = models.FileField(upload_to='empleados/documentos/')
    
    class Meta:
        ordering = ['-fecha_registro']
        verbose_name = 'Empleado'
        verbose_name_plural = 'Empleados'

    def __str__(self):
        return f"{self.persona.nombre} {self.persona.apellido_paterno}"

    def validar_documentos(self):
        """Valida que todos los documentos requeridos estén presentes y sean válidos"""
        return True  # Implementación pendiente

class Oportunidad(models.Model):
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
