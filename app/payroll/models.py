"""
Modelos del Sistema de Nómina huntRED®
Modelos críticos para gestión de nómina con WhatsApp dedicado por cliente
INTEGRADO CON ATS Y ML
"""
import uuid
import logging
from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from app.models import BusinessUnit
from app.ats.models import Job, Candidate, Assessment, Interview  # Integración ATS
from . import (
    PAYROLL_STATUSES, EMPLOYEE_TYPES, PAYROLL_FREQUENCIES,
    ATTENDANCE_STATUSES, REQUEST_TYPES, REQUEST_STATUSES,
    PAYROLL_ROLES, SUPPORTED_COUNTRIES
)

logger = logging.getLogger(__name__)


class PayrollCompany(models.Model):
    """
    Empresa cliente del sistema de nómina con WhatsApp dedicado
    INTEGRADO CON ATS PARA ECOSISTEMA UNIFICADO
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, verbose_name="Nombre de la empresa")
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE, verbose_name="Unidad de negocio")
    
    # Configuración de WhatsApp dedicado
    whatsapp_webhook_token = models.CharField(max_length=255, unique=True, verbose_name="Token webhook WhatsApp")
    whatsapp_phone_number = models.CharField(max_length=20, verbose_name="Número WhatsApp")
    whatsapp_business_name = models.CharField(max_length=100, verbose_name="Nombre del negocio WhatsApp")
    
    # Configuración de país y compliance
    country_code = models.CharField(max_length=3, default='MEX', verbose_name="Código de país")
    currency = models.CharField(max_length=3, default='MXN', verbose_name="Moneda")
    payroll_frequency = models.CharField(max_length=20, choices=PAYROLL_FREQUENCIES, default='monthly')
    
    # Configuración de precios
    pricing_tier = models.CharField(max_length=20, default='starter', verbose_name="Tier de precios")
    price_per_employee = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio por empleado")
    
    # Servicios premium activos
    premium_services = models.JSONField(default=dict, verbose_name="Servicios premium")
    
    # Configuración de mensajería
    messaging_config = models.JSONField(default=dict, verbose_name="Configuración de mensajería")
    
    # INTEGRACIÓN CON ATS
    ats_integration_enabled = models.BooleanField(default=True, verbose_name="Integración ATS activa")
    ats_company_id = models.UUIDField(null=True, blank=True, verbose_name="ID empresa en ATS")
    ats_sync_enabled = models.BooleanField(default=True, verbose_name="Sincronización ATS activa")
    
    # CONFIGURACIÓN ML Y AI
    ml_attendance_mode = models.CharField(
        max_length=20, 
        choices=[
            ('precise', 'Preciso y Sistemático'),
            ('ml_learning', 'ML con Aprendizaje'),
            ('random_ml', 'Aleatorio con ML'),
            ('hybrid', 'Híbrido (Preciso + ML)')
        ],
        default='hybrid',
        verbose_name="Modo de Asistencia ML"
    )
    ml_accuracy_threshold = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=85.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Umbral de Precisión ML (%)"
    )
    ml_learning_enabled = models.BooleanField(default=True, verbose_name="Aprendizaje ML activo")
    ml_training_data_days = models.IntegerField(default=90, verbose_name="Días de datos de entrenamiento")
    
    # Estado
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Empresa de Nómina"
        verbose_name_plural = "Empresas de Nómina"
        db_table = 'payroll_company'
        indexes = [
            models.Index(fields=['country_code']),
            models.Index(fields=['is_active']),
            models.Index(fields=['business_unit']),
            models.Index(fields=['ats_integration_enabled']),
            models.Index(fields=['ml_attendance_mode']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.country_code})"
    
    def clean(self):
        """Validaciones del modelo"""
        if self.country_code not in SUPPORTED_COUNTRIES:
            raise ValidationError(f"País no soportado: {self.country_code}")
        
        if not self.whatsapp_webhook_token:
            raise ValidationError("Token de webhook WhatsApp es requerido")
    
    def get_country_config(self):
        """Obtiene configuración del país"""
        return SUPPORTED_COUNTRIES.get(self.country_code, {})
    
    def get_employee_count(self):
        """Obtiene número de empleados activos"""
        return self.employees.filter(is_active=True).count()
    
    def calculate_monthly_revenue(self):
        """Calcula revenue mensual"""
        employee_count = self.get_employee_count()
        return employee_count * self.price_per_employee
    
    def get_ats_jobs(self):
        """Obtiene trabajos activos en ATS"""
        if not self.ats_integration_enabled:
            return Job.objects.none()
        
        return Job.objects.filter(
            company_id=self.ats_company_id,
            status='active'
        )
    
    def get_ats_candidates(self):
        """Obtiene candidatos en ATS"""
        if not self.ats_integration_enabled:
            return Candidate.objects.none()
        
        return Candidate.objects.filter(
            job__company_id=self.ats_company_id
        )


class PayrollEmployee(models.Model):
    """
    Empleado del sistema de nómina
    INTEGRADO CON ATS PARA CARRERA PROFESIONAL
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(PayrollCompany, on_delete=models.CASCADE, related_name='employees', verbose_name="Empresa")
    
    # Información básica
    employee_number = models.CharField(max_length=50, unique=True, verbose_name="Número de empleado")
    first_name = models.CharField(max_length=100, verbose_name="Nombre")
    last_name = models.CharField(max_length=100, verbose_name="Apellido")
    email = models.EmailField(verbose_name="Email")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Teléfono")
    whatsapp_number = models.CharField(max_length=20, blank=True, verbose_name="WhatsApp")
    
    # Información laboral
    hire_date = models.DateField(verbose_name="Fecha de contratación")
    job_title = models.CharField(max_length=100, verbose_name="Puesto")
    department = models.CharField(max_length=100, verbose_name="Departamento")
    employee_type = models.CharField(max_length=20, choices=EMPLOYEE_TYPES, default='permanent')
    
    # Información salarial
    monthly_salary = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Salario mensual")
    hourly_rate = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True, verbose_name="Tarifa por hora")
    
    # Información bancaria
    bank_name = models.CharField(max_length=100, blank=True, verbose_name="Banco")
    account_number = models.CharField(max_length=50, blank=True, verbose_name="Número de cuenta")
    clabe = models.CharField(max_length=18, blank=True, verbose_name="CLABE")
    
    # Información fiscal (México)
    rfc = models.CharField(max_length=13, blank=True, verbose_name="RFC")
    curp = models.CharField(max_length=18, blank=True, verbose_name="CURP")
    nss = models.CharField(max_length=11, blank=True, verbose_name="NSS")
    
    # Información de supervisor
    supervisor = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Supervisor")
    
    # Configuración de asistencia
    office_location = models.JSONField(default=dict, verbose_name="Ubicación de oficina")
    working_hours = models.JSONField(default=dict, verbose_name="Horario de trabajo")
    
    # INTEGRACIÓN CON ATS - CARRERA PROFESIONAL
    ats_candidate_id = models.UUIDField(null=True, blank=True, verbose_name="ID candidato en ATS")
    ats_job_id = models.UUIDField(null=True, blank=True, verbose_name="ID trabajo en ATS")
    career_profile = models.JSONField(default=dict, verbose_name="Perfil de carrera profesional")
    skills_assessment = models.JSONField(default=dict, verbose_name="Evaluación de habilidades")
    performance_history = models.JSONField(default=dict, verbose_name="Historial de desempeño")
    
    # ML Y AI - COMPORTAMIENTO DE ASISTENCIA
    attendance_pattern = models.JSONField(default=dict, verbose_name="Patrón de asistencia ML")
    ml_confidence_score = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Score de confianza ML"
    )
    attendance_anomalies = models.JSONField(default=list, verbose_name="Anomalías de asistencia")
    
    # Estado
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Empleado"
        verbose_name_plural = "Empleados"
        db_table = 'payroll_employee'
        indexes = [
            models.Index(fields=['employee_number']),
            models.Index(fields=['email']),
            models.Index(fields=['is_active']),
            models.Index(fields=['company']),
            models.Index(fields=['supervisor']),
            models.Index(fields=['ats_candidate_id']),
            models.Index(fields=['ml_confidence_score']),
        ]
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.employee_number})"
    
    def clean(self):
        """Validaciones del modelo"""
        country_config = self.company.get_country_config()
        required_fields = country_config.get('required_fields', [])
        
        for field in required_fields:
            if field == 'rfc' and not self.rfc:
                raise ValidationError("RFC es requerido para México")
            elif field == 'curp' and not self.curp:
                raise ValidationError("CURP es requerido para México")
            elif field == 'nss' and not self.nss:
                raise ValidationError("NSS es requerido para México")
            elif field == 'clabe' and not self.clabe:
                raise ValidationError("CLABE es requerido para México")
    
    def get_full_name(self):
        """Obtiene nombre completo"""
        return f"{self.first_name} {self.last_name}"
    
    def get_whatsapp_contact(self):
        """Obtiene contacto de WhatsApp"""
        return self.whatsapp_number or self.phone
    
    def calculate_hourly_rate(self):
        """Calcula tarifa por hora"""
        if self.hourly_rate:
            return self.hourly_rate
        
        # Calcular basado en salario mensual y horas de trabajo
        working_hours = self.working_hours.get('hours_per_day', 8)
        working_days = self.working_hours.get('days_per_month', 22)
        total_hours = working_hours * working_days
        
        if total_hours > 0:
            return self.monthly_salary / Decimal(str(total_hours))
        return Decimal('0')
    
    def get_ats_candidate(self):
        """Obtiene candidato asociado en ATS"""
        if not self.ats_candidate_id:
            return None
        
        try:
            return Candidate.objects.get(id=self.ats_candidate_id)
        except Candidate.DoesNotExist:
            return None
    
    def get_ats_job(self):
        """Obtiene trabajo asociado en ATS"""
        if not self.ats_job_id:
            return None
        
        try:
            return Job.objects.get(id=self.ats_job_id)
        except Job.DoesNotExist:
            return None
    
    def update_career_profile(self):
        """Actualiza perfil de carrera con datos de nómina"""
        # Obtener datos de desempeño
        attendance_records = self.attendance_records.all()
        payroll_calculations = self.payroll_calculations.all()
        
        # Calcular métricas
        total_days = attendance_records.count()
        present_days = attendance_records.filter(status='present').count()
        attendance_rate = (present_days / total_days * 100) if total_days > 0 else 0
        
        avg_salary = payroll_calculations.aggregate(
            avg_salary=models.Avg('gross_income')
        )['avg_salary'] or 0
        
        # Actualizar perfil
        self.career_profile.update({
            'attendance_rate': float(attendance_rate),
            'avg_salary': float(avg_salary),
            'total_experience_days': total_days,
            'last_updated': timezone.now().isoformat()
        })
        self.save()
    
    def get_ml_attendance_prediction(self, date):
        """Predice asistencia usando ML"""
        from .services.ml_attendance_service import MLAttendanceService
        
        ml_service = MLAttendanceService(self.company)
        return ml_service.predict_attendance(self, date)


class PayrollPeriod(models.Model):
    """
    Período de nómina
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(PayrollCompany, on_delete=models.CASCADE, related_name='payroll_periods', verbose_name="Empresa")
    
    # Información del período
    period_name = models.CharField(max_length=100, verbose_name="Nombre del período")
    start_date = models.DateField(verbose_name="Fecha de inicio")
    end_date = models.DateField(verbose_name="Fecha de fin")
    frequency = models.CharField(max_length=20, choices=PAYROLL_FREQUENCIES, verbose_name="Frecuencia")
    
    # Estado del período
    status = models.CharField(max_length=20, choices=PAYROLL_STATUSES, default='draft', verbose_name="Estado")
    
    # Totales
    total_employees = models.IntegerField(default=0, verbose_name="Total empleados")
    total_gross = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Total bruto")
    total_net = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Total neto")
    total_taxes = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Total impuestos")
    
    # Fechas importantes
    calculation_date = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de cálculo")
    approval_date = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de aprobación")
    disbursement_date = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de dispersión")
    
    # Usuario que aprobó
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Aprobado por")
    
    # ML Y AI - ANÁLISIS DEL PERÍODO
    ml_analysis = models.JSONField(default=dict, verbose_name="Análisis ML del período")
    attendance_accuracy = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Precisión de asistencia (%)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Período de Nómina"
        verbose_name_plural = "Períodos de Nómina"
        db_table = 'payroll_period'
        unique_together = ['company', 'start_date', 'end_date']
        indexes = [
            models.Index(fields=['company', 'status']),
            models.Index(fields=['start_date', 'end_date']),
            models.Index(fields=['attendance_accuracy']),
        ]
    
    def __str__(self):
        return f"{self.period_name} - {self.company.name}"
    
    def get_working_days(self):
        """Obtiene días laborables del período"""
        from datetime import timedelta
        days = 0
        current_date = self.start_date
        while current_date <= self.end_date:
            if current_date.weekday() < 5:  # Lunes a viernes
                days += 1
            current_date += timedelta(days=1)
        return days
    
    def calculate_ml_analysis(self):
        """Calcula análisis ML del período"""
        from .services.ml_attendance_service import MLAttendanceService
        
        ml_service = MLAttendanceService(self.company)
        analysis = ml_service.analyze_period(self)
        
        self.ml_analysis = analysis
        self.attendance_accuracy = analysis.get('accuracy', 0)
        self.save()


class PayrollCalculation(models.Model):
    """
    Cálculo individual de nómina por empleado
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    period = models.ForeignKey(PayrollPeriod, on_delete=models.CASCADE, related_name='calculations', verbose_name="Período")
    employee = models.ForeignKey(PayrollEmployee, on_delete=models.CASCADE, related_name='payroll_calculations', verbose_name="Empleado")
    
    # Percepciones
    base_salary = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Salario base")
    overtime_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0, verbose_name="Horas extra")
    overtime_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Monto horas extra")
    bonuses = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Bonos")
    commissions = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Comisiones")
    other_income = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Otros ingresos")
    gross_income = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Ingreso bruto")
    
    # Deducciones
    isr_withheld = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="ISR retenido")
    imss_employee = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="IMSS empleado")
    infonavit_employee = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="INFONAVIT empleado")
    loan_deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Deducciones préstamos")
    advance_deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Deducciones adelantos")
    other_deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Otras deducciones")
    total_deductions = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Total deducciones")
    
    # Neto a pagar
    net_pay = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Neto a pagar")
    
    # Aportaciones patronales
    imss_employer = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="IMSS patrón")
    infonavit_employer = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="INFONAVIT patrón")
    total_employer_cost = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Costo total patrón")
    
    # Metadatos
    calculation_date = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de cálculo")
    calculation_version = models.CharField(max_length=20, default='1.0', verbose_name="Versión de cálculo")
    
    class Meta:
        verbose_name = "Cálculo de Nómina"
        verbose_name_plural = "Cálculos de Nómina"
        db_table = 'payroll_calculation'
        unique_together = ['period', 'employee']
        indexes = [
            models.Index(fields=['period', 'employee']),
            models.Index(fields=['calculation_date']),
        ]
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.period.period_name}"
    
    def save(self, *args, **kwargs):
        """Calcula automáticamente totales antes de guardar"""
        # Calcular ingreso bruto
        self.gross_income = (
            self.base_salary + 
            self.overtime_amount + 
            self.bonuses + 
            self.commissions + 
            self.other_income
        )
        
        # Calcular total deducciones
        self.total_deductions = (
            self.isr_withheld + 
            self.imss_employee + 
            self.infonavit_employee + 
            self.loan_deductions + 
            self.advance_deductions + 
            self.other_deductions
        )
        
        # Calcular neto a pagar
        self.net_pay = self.gross_income - self.total_deductions
        
        # Calcular costo total patrón
        self.total_employer_cost = (
            self.gross_income + 
            self.imss_employer + 
            self.infonavit_employer
        )
        
        super().save(*args, **kwargs)


class AttendanceRecord(models.Model):
    """
    Registro de asistencia con geolocalización
    INTEGRADO CON ML PARA PREDICCIÓN Y ANÁLISIS
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(PayrollEmployee, on_delete=models.CASCADE, related_name='attendance_records', verbose_name="Empleado")
    
    # Fecha y hora
    date = models.DateField(verbose_name="Fecha")
    check_in_time = models.DateTimeField(null=True, blank=True, verbose_name="Hora de entrada")
    check_out_time = models.DateTimeField(null=True, blank=True, verbose_name="Hora de salida")
    
    # Geolocalización
    check_in_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, verbose_name="Latitud entrada")
    check_in_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, verbose_name="Longitud entrada")
    check_out_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, verbose_name="Latitud salida")
    check_out_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, verbose_name="Longitud salida")
    
    # Estado
    status = models.CharField(max_length=20, choices=ATTENDANCE_STATUSES, default='present', verbose_name="Estado")
    
    # Horas trabajadas
    hours_worked = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Horas trabajadas")
    overtime_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Horas extra")
    
    # Metadatos
    check_in_method = models.CharField(max_length=20, default='whatsapp', verbose_name="Método de entrada")
    check_out_method = models.CharField(max_length=20, default='whatsapp', verbose_name="Método de salida")
    notes = models.TextField(blank=True, verbose_name="Notas")
    
    # ML Y AI - ANÁLISIS DE ASISTENCIA
    ml_prediction = models.JSONField(default=dict, verbose_name="Predicción ML")
    ml_confidence = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Confianza ML (%)"
    )
    ml_anomaly_detected = models.BooleanField(default=False, verbose_name="Anomalía ML detectada")
    ml_anomaly_type = models.CharField(max_length=50, blank=True, verbose_name="Tipo de anomalía")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Registro de Asistencia"
        verbose_name_plural = "Registros de Asistencia"
        db_table = 'payroll_attendance'
        unique_together = ['employee', 'date']
        indexes = [
            models.Index(fields=['employee', 'date']),
            models.Index(fields=['status']),
            models.Index(fields=['check_in_time']),
            models.Index(fields=['ml_anomaly_detected']),
            models.Index(fields=['ml_confidence']),
        ]
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.date}"
    
    def calculate_hours_worked(self):
        """Calcula horas trabajadas"""
        if self.check_in_time and self.check_out_time:
            duration = self.check_out_time - self.check_in_time
            hours = duration.total_seconds() / 3600
            self.hours_worked = Decimal(str(round(hours, 2)))
            
            # Calcular horas extra (más de 8 horas)
            if self.hours_worked > 8:
                self.overtime_hours = self.hours_worked - 8
            else:
                self.overtime_hours = 0
    
    def analyze_with_ml(self):
        """Analiza registro con ML"""
        from .services.ml_attendance_service import MLAttendanceService
        
        ml_service = MLAttendanceService(self.employee.company)
        analysis = ml_service.analyze_attendance_record(self)
        
        self.ml_prediction = analysis.get('prediction', {})
        self.ml_confidence = analysis.get('confidence', 0)
        self.ml_anomaly_detected = analysis.get('anomaly_detected', False)
        self.ml_anomaly_type = analysis.get('anomaly_type', '')
        self.save()


class EmployeeRequest(models.Model):
    """
    Solicitudes de empleados (vacaciones, permisos, etc.)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(PayrollEmployee, on_delete=models.CASCADE, related_name='requests', verbose_name="Empleado")
    
    # Información de la solicitud
    request_type = models.CharField(max_length=20, choices=REQUEST_TYPES, verbose_name="Tipo de solicitud")
    start_date = models.DateField(verbose_name="Fecha de inicio")
    end_date = models.DateField(verbose_name="Fecha de fin")
    days_requested = models.IntegerField(verbose_name="Días solicitados")
    
    # Detalles
    reason = models.TextField(verbose_name="Motivo")
    status = models.CharField(max_length=20, choices=REQUEST_STATUSES, default='pending', verbose_name="Estado")
    
    # Aprobación
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Aprobado por")
    approval_date = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de aprobación")
    approval_notes = models.TextField(blank=True, verbose_name="Notas de aprobación")
    
    # Metadatos
    created_via = models.CharField(max_length=20, default='whatsapp', verbose_name="Creado vía")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Solicitud de Empleado"
        verbose_name_plural = "Solicitudes de Empleados"
        db_table = 'payroll_employee_request'
        indexes = [
            models.Index(fields=['employee', 'status']),
            models.Index(fields=['request_type']),
            models.Index(fields=['start_date', 'end_date']),
        ]
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.get_request_type_display()}"


class MLAttendanceModel(models.Model):
    """
    Modelo de ML para predicción de asistencia
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(PayrollCompany, on_delete=models.CASCADE, related_name='ml_models', verbose_name="Empresa")
    
    # Configuración del modelo
    model_name = models.CharField(max_length=100, verbose_name="Nombre del modelo")
    model_type = models.CharField(
        max_length=20,
        choices=[
            ('random_forest', 'Random Forest'),
            ('neural_network', 'Neural Network'),
            ('gradient_boosting', 'Gradient Boosting'),
            ('lstm', 'LSTM'),
            ('hybrid', 'Híbrido')
        ],
        verbose_name="Tipo de modelo"
    )
    
    # Métricas del modelo
    accuracy = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Precisión (%)"
    )
    precision = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Precisión (%)"
    )
    recall = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Recall (%)"
    )
    
    # Datos del modelo
    training_data_size = models.IntegerField(default=0, verbose_name="Tamaño datos entrenamiento")
    last_training_date = models.DateTimeField(null=True, blank=True, verbose_name="Última fecha de entrenamiento")
    model_parameters = models.JSONField(default=dict, verbose_name="Parámetros del modelo")
    
    # Estado
    is_active = models.BooleanField(default=True, verbose_name="Modelo activo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Modelo ML de Asistencia"
        verbose_name_plural = "Modelos ML de Asistencia"
        db_table = 'payroll_ml_attendance_model'
        indexes = [
            models.Index(fields=['company', 'is_active']),
            models.Index(fields=['model_type']),
            models.Index(fields=['accuracy']),
        ]
    
    def __str__(self):
        return f"{self.model_name} - {self.company.name}"


class TaxTable(models.Model):
    """
    Tabla de impuestos y contribuciones
    """
    TABLE_TYPES = [
        ('sat_isr_mensual', 'SAT ISR Mensual'),
        ('sat_isr_anual', 'SAT ISR Anual'),
        ('sat_subsidios', 'SAT Subsidios'),
        ('imss_cuotas', 'IMSS Cuotas'),
        ('imss_riesgos', 'IMSS Riesgos de Trabajo'),
        ('imss_retiro', 'IMSS Retiro'),
        ('infonavit_creditos', 'INFONAVIT Créditos'),
        ('infonavit_descuentos', 'INFONAVIT Descuentos'),
        ('col_pensiones', 'Colombia Pensiones'),
        ('col_salud', 'Colombia Salud'),
        ('arg_anses', 'Argentina ANSES'),
        ('arg_afip', 'Argentina AFIP'),
    ]
    
    table_type = models.CharField(max_length=50, choices=TABLE_TYPES)
    concept = models.CharField(max_length=100)
    limit_inferior = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    limit_superior = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    fixed_quota = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    percentage = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    value = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    effective_date = models.DateField()
    expiration_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    source = models.CharField(max_length=50, default='manual')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'payroll_tax_tables'
        unique_together = ['table_type', 'concept', 'effective_date']
        indexes = [
            models.Index(fields=['table_type', 'is_active']),
            models.Index(fields=['effective_date']),
        ]
    
    def __str__(self):
        return f"{self.get_table_type_display()} - {self.concept} ({self.effective_date})"


class UMARegistry(models.Model):
    """
    Registro de valores UMA por país y año
    """
    country_code = models.CharField(max_length=3, choices=SUPPORTED_COUNTRIES)
    year = models.IntegerField()
    uma_value = models.DecimalField(max_digits=10, decimal_places=2)
    effective_date = models.DateField()
    expiration_date = models.DateField(null=True, blank=True)
    source = models.CharField(max_length=50, default='DOF')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'payroll_uma_registry'
        unique_together = ['country_code', 'year']
        indexes = [
            models.Index(fields=['country_code', 'is_active']),
            models.Index(fields=['year']),
        ]
    
    def __str__(self):
        return f"UMA {self.country_code} {self.year}: {self.uma_value}"


class TaxUpdateLog(models.Model):
    """
    Log de actualizaciones fiscales
    """
    UPDATE_TYPES = [
        ('uma', 'UMA'),
        ('imss', 'IMSS'),
        ('infonavit', 'INFONAVIT'),
        ('sat', 'SAT'),
        ('col_pensiones', 'Colombia Pensiones'),
        ('col_salud', 'Colombia Salud'),
        ('arg_anses', 'Argentina ANSES'),
        ('arg_afip', 'Argentina AFIP'),
    ]
    
    update_type = models.CharField(max_length=20, choices=UPDATE_TYPES)
    country_code = models.CharField(max_length=3, choices=SUPPORTED_COUNTRIES)
    description = models.TextField()
    old_values = models.JSONField(null=True, blank=True)
    new_values = models.JSONField(null=True, blank=True)
    success = models.BooleanField(default=True)
    error_message = models.TextField(null=True, blank=True)
    source = models.CharField(max_length=50, default='celery')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'payroll_tax_update_log'
        indexes = [
            models.Index(fields=['update_type', 'country_code']),
            models.Index(fields=['created_at']),
            models.Index(fields=['success']),
        ]
    
    def __str__(self):
        return f"{self.get_update_type_display()} {self.country_code} - {self.created_at}"


class TaxValidationLog(models.Model):
    """
    Log de validaciones fiscales
    """
    VALIDATION_TYPES = [
        ('isr', 'ISR'),
        ('imss', 'IMSS'),
        ('infonavit', 'INFONAVIT'),
        ('uma', 'UMA'),
        ('general', 'General'),
    ]
    
    validation_type = models.CharField(max_length=20, choices=VALIDATION_TYPES)
    company = models.ForeignKey(PayrollCompany, on_delete=models.CASCADE)
    test_salary = models.DecimalField(max_digits=10, decimal_places=2)
    calculated_isr = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    calculated_imss = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    calculated_infonavit = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    validation_status = models.CharField(max_length=20, choices=[
        ('ok', 'OK'),
        ('warning', 'Warning'),
        ('error', 'Error'),
    ])
    message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'payroll_tax_validation_log'
        indexes = [
            models.Index(fields=['validation_type', 'company']),
            models.Index(fields=['validation_status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.validation_type} - {self.company.name} - {self.validation_status}"


def create_default_data():
    """Crear datos por defecto del sistema"""
    logger.info("Creando datos por defecto del sistema de nómina...")
    
    # Aquí se pueden crear configuraciones por defecto
    # como templates de mensajes, configuraciones de países, etc.
    pass 