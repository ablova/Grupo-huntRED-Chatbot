"""
💰 MODELOS DE RÉGIMEN FISCAL

Gestión de regímenes fiscales y obligaciones fiscales.
"""

from django.db import models
from decimal import Decimal

from app.models import BusinessUnit

class FiscalRegime(models.Model):
    """Régimen fiscal."""
    
    business_unit = models.ForeignKey(
        BusinessUnit,
        on_delete=models.CASCADE,
        related_name='fiscal_regimes'
    )
    
    # Información básica
    name = models.CharField(max_length=100, help_text="Nombre del régimen")
    description = models.TextField(help_text="Descripción del régimen")
    
    # Códigos fiscales
    sat_code = models.CharField(
        max_length=10,
        help_text="Código SAT del régimen"
    )
    regime_type = models.CharField(
        max_length=50,
        choices=[
            ('general', 'General de Ley Personas Morales'),
            ('simplified', 'Simplificado de Confianza'),
            ('small_taxpayer', 'Pequeño Contribuyente'),
            ('agricultural', 'Actividades Agrícolas'),
            ('fishing', 'Actividades Pesqueras'),
            ('transport', 'Transporte de Pasajeros'),
            ('other', 'Otro')
        ],
        help_text="Tipo de régimen fiscal"
    )
    
    # Configuración fiscal
    requires_iva_declaration = models.BooleanField(
        default=True,
        help_text="¿Requiere declaración de IVA?"
    )
    requires_isr_declaration = models.BooleanField(
        default=True,
        help_text="¿Requiere declaración de ISR?"
    )
    requires_ieps_declaration = models.BooleanField(
        default=False,
        help_text="¿Requiere declaración de IEPS?"
    )
    
    # Límites y umbrales
    income_limit = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Límite de ingresos para el régimen"
    )
    employee_limit = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Límite de empleados para el régimen"
    )
    
    # Estados
    is_active = models.BooleanField(default=True, help_text="¿Régimen activo?")
    is_default = models.BooleanField(default=False, help_text="¿Régimen por defecto?")
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Régimen Fiscal"
        verbose_name_plural = "Regímenes Fiscales"
        unique_together = ['business_unit', 'sat_code']
    
    def __str__(self):
        return f"{self.name} ({self.sat_code})"
    
    def get_declaration_requirements(self):
        """Obtiene los requisitos de declaración."""
        requirements = []
        
        if self.requires_iva_declaration:
            requirements.append('IVA')
        if self.requires_isr_declaration:
            requirements.append('ISR')
        if self.requires_ieps_declaration:
            requirements.append('IEPS')
        
        return requirements
    
    def is_eligible(self, annual_income=None, employee_count=None):
        """Verifica si es elegible para el régimen."""
        if self.income_limit and annual_income:
            if annual_income > self.income_limit:
                return False
        
        if self.employee_limit and employee_count:
            if employee_count > self.employee_limit:
                return False
        
        return True

class FiscalObligation(models.Model):
    """Obligación fiscal."""
    
    business_unit = models.ForeignKey(
        BusinessUnit,
        on_delete=models.CASCADE,
        related_name='fiscal_obligations'
    )
    
    # Información básica
    name = models.CharField(max_length=100, help_text="Nombre de la obligación")
    description = models.TextField(help_text="Descripción de la obligación")
    
    # Tipo de obligación
    obligation_type = models.CharField(
        max_length=50,
        choices=[
            ('declaration', 'Declaración'),
            ('payment', 'Pago'),
            ('information', 'Información'),
            ('certification', 'Certificación'),
            ('other', 'Otro')
        ],
        help_text="Tipo de obligación fiscal"
    )
    
    # Impuesto relacionado
    tax_type = models.CharField(
        max_length=20,
        choices=[
            ('iva', 'IVA'),
            ('isr', 'ISR'),
            ('ieps', 'IEPS'),
            ('ish', 'ISH'),
            ('other', 'Otro')
        ],
        help_text="Tipo de impuesto relacionado"
    )
    
    # Frecuencia
    frequency = models.CharField(
        max_length=20,
        choices=[
            ('monthly', 'Mensual'),
            ('quarterly', 'Trimestral'),
            ('semiannual', 'Semestral'),
            ('annual', 'Anual'),
            ('event_based', 'Por Evento')
        ],
        help_text="Frecuencia de la obligación"
    )
    
    # Fechas
    due_day = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Día de vencimiento (para obligaciones periódicas)"
    )
    due_month = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Mes de vencimiento (para obligaciones anuales)"
    )
    
    # Estados
    is_active = models.BooleanField(default=True, help_text="¿Obligación activa?")
    is_required = models.BooleanField(default=True, help_text="¿Obligación requerida?")
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Obligación Fiscal"
        verbose_name_plural = "Obligaciones Fiscales"
    
    def __str__(self):
        return f"{self.name} - {self.tax_type.upper()}"
    
    def get_next_due_date(self, from_date=None):
        """Obtiene la próxima fecha de vencimiento."""
        from django.utils import timezone
        from datetime import date, timedelta
        
        if not from_date:
            from_date = timezone.now().date()
        
        if self.frequency == 'monthly':
            # Próximo mes
            if from_date.month == 12:
                next_month = date(from_date.year + 1, 1, 1)
            else:
                next_month = date(from_date.year, from_date.month + 1, 1)
            
            # Ajustar al día de vencimiento
            if self.due_day:
                try:
                    return date(next_month.year, next_month.month, self.due_day)
                except ValueError:
                    # Si el día no existe en el mes, usar el último día
                    import calendar
                    last_day = calendar.monthrange(next_month.year, next_month.month)[1]
                    return date(next_month.year, next_month.month, last_day)
            else:
                return next_month
        
        elif self.frequency == 'quarterly':
            # Próximo trimestre
            current_quarter = (from_date.month - 1) // 3
            next_quarter_month = (current_quarter + 1) * 3 + 1
            
            if next_quarter_month > 12:
                next_quarter_month = 1
                next_year = from_date.year + 1
            else:
                next_year = from_date.year
            
            next_quarter_date = date(next_year, next_quarter_month, 1)
            
            if self.due_day:
                try:
                    return date(next_quarter_date.year, next_quarter_date.month, self.due_day)
                except ValueError:
                    import calendar
                    last_day = calendar.monthrange(next_quarter_date.year, next_quarter_date.month)[1]
                    return date(next_quarter_date.year, next_quarter_date.month, last_day)
            else:
                return next_quarter_date
        
        elif self.frequency == 'annual':
            # Próximo año
            if self.due_month and self.due_day:
                try:
                    return date(from_date.year + 1, self.due_month, self.due_day)
                except ValueError:
                    import calendar
                    last_day = calendar.monthrange(from_date.year + 1, self.due_month)[1]
                    return date(from_date.year + 1, self.due_month, last_day)
            else:
                return date(from_date.year + 1, 1, 1)
        
        return None
    
    def is_overdue(self, as_of_date=None):
        """Verifica si la obligación está vencida."""
        from django.utils import timezone
        
        if not as_of_date:
            as_of_date = timezone.now().date()
        
        next_due = self.get_next_due_date(as_of_date)
        if next_due:
            return as_of_date > next_due
        
        return False
    
    def get_days_until_due(self, as_of_date=None):
        """Obtiene los días hasta el vencimiento."""
        from django.utils import timezone
        from datetime import date
        
        if not as_of_date:
            as_of_date = timezone.now().date()
        
        next_due = self.get_next_due_date(as_of_date)
        if next_due:
            return (next_due - as_of_date).days
        
        return None 