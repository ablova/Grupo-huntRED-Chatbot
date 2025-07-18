# app/payroll/models.py
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
from django.conf import settings

from app.models import BusinessUnit
from app.models import Vacante as Job, Person as Candidate  # Integración ATS
from app.ats.models import Assessment, Interview  # Integración ATS
from . import (
    PAYROLL_STATUSES, EMPLOYEE_TYPES, PAYROLL_FREQUENCIES,
    ATTENDANCE_STATUSES, REQUEST_TYPES, REQUEST_STATUSES,
    PAYROLL_ROLES, SUPPORTED_COUNTRIES
)
# Importación corregida - el modelo PermisoEspecial se define al final del archivo

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
            models.Index(fields=['country_code'], name='payroll_comp_country_idx'),
            models.Index(fields=['is_active'], name='payroll_comp_active_idx'),
            models.Index(fields=['business_unit'], name='payroll_comp_bu_idx'),
            models.Index(fields=['ats_integration_enabled'], name='payroll_comp_ats_idx'),
            models.Index(fields=['ml_attendance_mode'], name='payroll_comp_ml_idx'),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.country_code})"
    
    def clean(self):
        """Validaciones del modelo"""
        from . import COUNTRY_CONFIG
        if self.country_code not in COUNTRY_CONFIG:
            raise ValidationError(f"País no soportado: {self.country_code}")
        
        if not self.whatsapp_webhook_token:
            raise ValidationError("Token de webhook WhatsApp es requerido")
    
    def get_country_config(self):
        """Obtiene configuración del país"""
        from . import COUNTRY_CONFIG
        return COUNTRY_CONFIG.get(self.country_code, {})
    
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
            models.Index(fields=['employee_number'], name='payroll_emp_num_idx'),
            models.Index(fields=['email'], name='payroll_emp_email_idx'),
            models.Index(fields=['is_active'], name='payroll_emp_active_idx'),
            models.Index(fields=['company'], name='payroll_emp_comp_idx'),
            models.Index(fields=['supervisor'], name='payroll_emp_sup_idx'),
            models.Index(fields=['ats_candidate_id'], name='payroll_emp_ats_idx'),
            models.Index(fields=['ml_confidence_score'], name='payroll_emp_ml_idx'),
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
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Aprobado por")
    
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
            models.Index(fields=['company', 'status'], name='payroll_period_comp_stat_idx'),
            models.Index(fields=['start_date', 'end_date'], name='payroll_period_dates_idx'),
            models.Index(fields=['attendance_accuracy'], name='payroll_period_acc_idx'),
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
            models.Index(fields=['period', 'employee'], name='payroll_calc_per_emp_idx'),
            models.Index(fields=['calculation_date'], name='payroll_calc_date_idx'),
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
            models.Index(fields=['employee', 'date'], name='payroll_att_emp_date_idx'),
            models.Index(fields=['status'], name='payroll_att_status_idx'),
            models.Index(fields=['check_in_time'], name='payroll_att_checkin_idx'),
            models.Index(fields=['ml_anomaly_detected'], name='payroll_att_ml_anom_idx'),
            models.Index(fields=['ml_confidence'], name='payroll_att_ml_conf_idx'),
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
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Aprobado por")
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
            models.Index(fields=['employee', 'status'], name='payroll_req_emp_stat_idx'),
            models.Index(fields=['request_type'], name='payroll_req_type_idx'),
            models.Index(fields=['start_date', 'end_date'], name='payroll_req_dates_idx'),
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
            models.Index(fields=['company', 'is_active'], name='payroll_ml_comp_active_idx'),
            models.Index(fields=['model_type'], name='payroll_ml_type_idx'),
            models.Index(fields=['accuracy'], name='payroll_ml_acc_idx'),
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
            models.Index(fields=['table_type', 'is_active'], name='payroll_tax_type_active_idx'),
            models.Index(fields=['effective_date'], name='payroll_tax_eff_date_idx'),
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
            models.Index(fields=['country_code', 'is_active'], name='payroll_uma_country_idx'),
            models.Index(fields=['year'], name='payroll_uma_year_idx'),
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
            models.Index(fields=['update_type', 'country_code'], name='payroll_tax_upd_type_idx'),
            models.Index(fields=['created_at'], name='payroll_tax_upd_created_idx'),
            models.Index(fields=['success'], name='payroll_tax_upd_success_idx'),
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
            models.Index(fields=['validation_type', 'company'], name='payroll_tax_val_type_idx'),
            models.Index(fields=['validation_status'], name='payroll_tax_val_status_idx'),
            models.Index(fields=['created_at'], name='payroll_tax_val_created_idx'),
        ]
    
    def __str__(self):
        return f"{self.validation_type} - {self.company.name} - {self.validation_status}"


def create_default_data():
    """Crear datos por defecto del sistema"""
    logger.info("Creando datos por defecto del sistema de nómina...")
    
    # Aquí se pueden crear configuraciones por defecto
    # como templates de mensajes, configuraciones de países, etc.
    pass


class OverheadCategory(models.Model):
    """
    Categorías de overhead configurables por empresa
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(PayrollCompany, on_delete=models.CASCADE, related_name='overhead_categories')
    
    # Configuración de categoría
    name = models.CharField(max_length=100, verbose_name="Nombre de categoría")
    description = models.TextField(blank=True, verbose_name="Descripción")
    calculation_method = models.CharField(
        max_length=50, 
        choices=[
            ('percentage', 'Porcentaje del salario'),
            ('fixed', 'Monto fijo'),
            ('formula', 'Fórmula personalizada'),
            ('ml_predicted', 'Predicción ML')
        ],
        default='percentage',
        verbose_name="Método de cálculo"
    )
    
    # Parámetros de cálculo
    default_rate = models.DecimalField(max_digits=8, decimal_places=4, default=0.0000, verbose_name="Tasa por defecto")
    min_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Monto mínimo")
    max_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name="Monto máximo")
    formula = models.TextField(blank=True, verbose_name="Fórmula personalizada")
    
    # AURA Integration
    aura_category = models.CharField(
        max_length=50,
        choices=[
            ('infrastructure', 'Infraestructura'),
            ('administrative', 'Administrativo'),
            ('benefits', 'Beneficios'),
            ('training', 'Capacitación'),
            ('technology', 'Tecnología'),
            ('social_impact', 'Impacto Social'),
            ('sustainability', 'Sustentabilidad'),
            ('wellbeing', 'Bienestar'),
            ('innovation', 'Innovación')
        ],
        default='administrative',
        verbose_name="Categoría AURA"
    )
    
    # ML Configuration
    ml_enabled = models.BooleanField(default=True, verbose_name="ML habilitado")
    ml_weight = models.DecimalField(max_digits=3, decimal_places=2, default=1.00, verbose_name="Peso ML")
    
    # Estado
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Categoría de Overhead"
        verbose_name_plural = "Categorías de Overhead"
        db_table = 'payroll_overhead_category'
        unique_together = ['company', 'name']
        indexes = [
            models.Index(fields=['company', 'is_active'], name='payroll_oh_cat_comp_idx'),
            models.Index(fields=['aura_category'], name='payroll_oh_cat_aura_idx'),
            models.Index(fields=['ml_enabled'], name='payroll_oh_cat_ml_idx'),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.company.name}"


class EmployeeOverheadCalculation(models.Model):
    """
    Cálculo de overhead individual por empleado con ML y AURA
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(PayrollEmployee, on_delete=models.CASCADE, related_name='overhead_calculations')
    period = models.ForeignKey(PayrollPeriod, on_delete=models.CASCADE, related_name='overhead_calculations')
    
    # Overhead detallado por categoría
    infrastructure_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Costo infraestructura")
    administrative_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Costo administrativo")
    benefits_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Costo beneficios")
    training_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Costo capacitación")
    technology_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Costo tecnología")
    
    # AURA Enhanced Categories
    social_impact_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Costo impacto social")
    sustainability_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Costo sustentabilidad")
    wellbeing_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Costo bienestar")
    innovation_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Costo innovación")
    
    # Totales
    traditional_overhead = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Overhead tradicional")
    aura_enhanced_overhead = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Overhead mejorado AURA")
    total_overhead = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Overhead total")
    overhead_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Porcentaje overhead")
    
    # ML Predictions and Optimizations
    ml_predicted_overhead = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Overhead predicho ML")
    ml_confidence_score = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Score confianza ML")
    ml_optimization_potential = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Potencial optimización ML")
    ml_recommendations = models.JSONField(default=dict, verbose_name="Recomendaciones ML")
    
    # AURA Analysis
    aura_ethics_score = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Score ética AURA")
    aura_fairness_score = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Score equidad AURA")
    aura_sustainability_score = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Score sustentabilidad AURA")
    aura_insights = models.JSONField(default=dict, verbose_name="Insights AURA")
    
    # Benchmarking
    industry_benchmark = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Benchmark industria")
    company_size_benchmark = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Benchmark tamaño empresa")
    regional_benchmark = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Benchmark regional")
    
    # Metadatos
    calculation_version = models.CharField(max_length=20, default='2.0', verbose_name="Versión cálculo")
    calculated_at = models.DateTimeField(auto_now_add=True, verbose_name="Calculado en")
    
    class Meta:
        verbose_name = "Cálculo Overhead Empleado"
        verbose_name_plural = "Cálculos Overhead Empleados"
        db_table = 'payroll_employee_overhead'
        unique_together = ['employee', 'period']
        indexes = [
            models.Index(fields=['employee', 'period'], name='payroll_emp_oh_emp_per_idx'),
            models.Index(fields=['ml_confidence_score'], name='payroll_emp_oh_ml_conf_idx'),
            models.Index(fields=['aura_ethics_score'], name='payroll_emp_oh_aura_idx'),
            models.Index(fields=['calculated_at'], name='payroll_emp_oh_calc_idx'),
        ]
    
    def __str__(self):
        return f"Overhead {self.employee.get_full_name()} - {self.period.period_name}"
    
    def calculate_total_cost(self):
        """Calcula costo total empleado + overhead"""
        return self.employee.monthly_salary + self.total_overhead
    
    def get_optimization_savings(self):
        """Calcula ahorros potenciales con optimización ML"""
        if self.ml_predicted_overhead > 0:
            return max(0, self.total_overhead - self.ml_predicted_overhead)
        return 0
    
    def get_aura_overall_score(self):
        """Calcula score general AURA"""
        scores = [self.aura_ethics_score, self.aura_fairness_score, self.aura_sustainability_score]
        valid_scores = [s for s in scores if s > 0]
        return sum(valid_scores) / len(valid_scores) if valid_scores else 0


class TeamOverheadAnalysis(models.Model):
    """
    Análisis de overhead grupal/equipo con ML y AURA
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(PayrollCompany, on_delete=models.CASCADE, related_name='team_analyses')
    period = models.ForeignKey(PayrollPeriod, on_delete=models.CASCADE, related_name='team_analyses')
    
    # Información del equipo
    team_name = models.CharField(max_length=100, verbose_name="Nombre del equipo")
    department = models.CharField(max_length=100, verbose_name="Departamento")
    team_lead = models.ForeignKey(PayrollEmployee, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Líder del equipo")
    
    # Métricas del equipo
    team_size = models.IntegerField(verbose_name="Tamaño del equipo")
    total_salaries = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Total salarios")
    total_overhead = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Total overhead")
    overhead_per_employee = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Overhead por empleado")
    
    # Análisis AURA del equipo
    team_ethics_score = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Score ética equipo")
    team_diversity_score = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Score diversidad")
    team_sustainability_score = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Score sustentabilidad")
    team_innovation_score = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Score innovación")
    
    # ML Insights del equipo
    ml_efficiency_prediction = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Predicción eficiencia ML")
    ml_turnover_risk = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Riesgo rotación ML")
    ml_performance_forecast = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Pronóstico desempeño ML")
    ml_cost_optimization = models.JSONField(default=dict, verbose_name="Optimización costos ML")
    
    # Benchmarking y comparativas
    efficiency_score = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Score eficiencia")
    industry_percentile = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Percentil industria")
    company_ranking = models.IntegerField(default=0, verbose_name="Ranking en empresa")
    
    # AURA Premium Features (solo si tienen AURA)
    aura_holistic_assessment = models.JSONField(default=dict, verbose_name="Evaluación holística AURA")
    aura_energy_analysis = models.JSONField(default=dict, verbose_name="Análisis energético AURA")
    aura_compatibility_matrix = models.JSONField(default=dict, verbose_name="Matriz compatibilidad AURA")
    aura_growth_recommendations = models.JSONField(default=dict, verbose_name="Recomendaciones crecimiento AURA")
    
    # Estado y metadatos
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Análisis Overhead Equipo"
        verbose_name_plural = "Análisis Overhead Equipos"
        db_table = 'payroll_team_overhead_analysis'
        unique_together = ['company', 'team_name', 'period']
        indexes = [
            models.Index(fields=['company', 'period'], name='payroll_team_oh_comp_idx'),
            models.Index(fields=['department'], name='payroll_team_oh_dept_idx'),
            models.Index(fields=['efficiency_score'], name='payroll_team_oh_eff_idx'),
            models.Index(fields=['team_ethics_score'], name='payroll_team_oh_eth_idx'),
        ]
    
    def __str__(self):
        return f"Análisis {self.team_name} - {self.period.period_name}"
    
    def get_total_cost(self):
        """Calcula costo total del equipo"""
        return self.total_salaries + self.total_overhead
    
    def get_cost_per_employee(self):
        """Calcula costo promedio por empleado"""
        if self.team_size > 0:
            return self.get_total_cost() / self.team_size
        return 0
    
    def get_aura_overall_score(self):
        """Calcula score general AURA del equipo"""
        scores = [
            self.team_ethics_score, 
            self.team_diversity_score, 
            self.team_sustainability_score, 
            self.team_innovation_score
        ]
        valid_scores = [s for s in scores if s > 0]
        return sum(valid_scores) / len(valid_scores) if valid_scores else 0


class OverheadMLModel(models.Model):
    """
    Modelo de Machine Learning para predicción y optimización de overhead
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(PayrollCompany, on_delete=models.CASCADE, related_name='overhead_ml_models')
    
    # Configuración del modelo
    model_name = models.CharField(max_length=100, verbose_name="Nombre del modelo")
    model_type = models.CharField(
        max_length=30,
        choices=[
            ('random_forest', 'Random Forest'),
            ('neural_network', 'Neural Network'),
            ('gradient_boosting', 'Gradient Boosting'),
            ('lstm', 'LSTM'),
            ('transformer', 'Transformer'),
            ('hybrid_ml_aura', 'Híbrido ML + AURA'),
            ('aura_enhanced', 'AURA Enhanced')
        ],
        default='hybrid_ml_aura',
        verbose_name="Tipo de modelo"
    )
    
    # Métricas del modelo
    accuracy = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Precisión (%)")
    precision = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Precisión (%)")
    recall = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Recall (%)")
    f1_score = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="F1 Score")
    mse = models.DecimalField(max_digits=10, decimal_places=4, default=0, verbose_name="Mean Squared Error")
    
    # AURA Integration Metrics
    aura_ethics_compliance = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Cumplimiento ética AURA")
    aura_fairness_score = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Score equidad AURA")
    aura_bias_detection = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Detección sesgos AURA")
    
    # Datos de entrenamiento
    training_data_size = models.IntegerField(default=0, verbose_name="Tamaño datos entrenamiento")
    validation_data_size = models.IntegerField(default=0, verbose_name="Tamaño datos validación")
    test_data_size = models.IntegerField(default=0, verbose_name="Tamaño datos prueba")
    
    # Configuración y parámetros
    model_parameters = models.JSONField(default=dict, verbose_name="Parámetros del modelo")
    feature_importance = models.JSONField(default=dict, verbose_name="Importancia características")
    aura_weights = models.JSONField(default=dict, verbose_name="Pesos AURA")
    
    # Fechas de entrenamiento
    last_training_date = models.DateTimeField(null=True, blank=True, verbose_name="Última fecha entrenamiento")
    next_training_date = models.DateTimeField(null=True, blank=True, verbose_name="Próxima fecha entrenamiento")
    training_frequency_days = models.IntegerField(default=30, verbose_name="Frecuencia entrenamiento (días)")
    
    # Estado
    is_active = models.BooleanField(default=True, verbose_name="Modelo activo")
    is_production = models.BooleanField(default=False, verbose_name="En producción")
    version = models.CharField(max_length=20, default='1.0.0', verbose_name="Versión")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Modelo ML Overhead"
        verbose_name_plural = "Modelos ML Overhead"
        db_table = 'payroll_overhead_ml_model'
        indexes = [
            models.Index(fields=['company', 'is_active'], name='payroll_oh_ml_comp_idx'),
            models.Index(fields=['model_type'], name='payroll_oh_ml_type_idx'),
            models.Index(fields=['accuracy'], name='payroll_oh_ml_acc_idx'),
            models.Index(fields=['is_production'], name='payroll_oh_ml_prod_idx'),
        ]
    
    def __str__(self):
        return f"{self.model_name} ({self.model_type}) - {self.company.name}"
    
    def get_performance_score(self):
        """Calcula score general de desempeño"""
        metrics = [self.accuracy, self.precision, self.recall, self.f1_score]
        valid_metrics = [m for m in metrics if m > 0]
        return sum(valid_metrics) / len(valid_metrics) if valid_metrics else 0
    
    def get_aura_compliance_score(self):
        """Calcula score de cumplimiento AURA"""
        aura_metrics = [self.aura_ethics_compliance, self.aura_fairness_score, self.aura_bias_detection]
        valid_metrics = [m for m in aura_metrics if m > 0]
        return sum(valid_metrics) / len(valid_metrics) if valid_metrics else 0


class OverheadBenchmark(models.Model):
    """
    Benchmarks de overhead por industria, región y tamaño de empresa
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Categorización
    industry = models.CharField(max_length=100, verbose_name="Industria")
    region = models.CharField(max_length=100, verbose_name="Región")
    company_size_range = models.CharField(
        max_length=20,
        choices=[
            ('1-10', '1-10 empleados'),
            ('11-50', '11-50 empleados'),
            ('51-200', '51-200 empleados'),
            ('201-500', '201-500 empleados'),
            ('501-1000', '501-1000 empleados'),
            ('1000+', '1000+ empleados')
        ],
        verbose_name="Rango tamaño empresa"
    )
    
    # Benchmarks por categoría
    infrastructure_benchmark = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Benchmark infraestructura (%)")
    administrative_benchmark = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Benchmark administrativo (%)")
    benefits_benchmark = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Benchmark beneficios (%)")
    training_benchmark = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Benchmark capacitación (%)")
    technology_benchmark = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Benchmark tecnología (%)")
    
    # AURA Enhanced Benchmarks
    social_impact_benchmark = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Benchmark impacto social (%)")
    sustainability_benchmark = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Benchmark sustentabilidad (%)")
    wellbeing_benchmark = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Benchmark bienestar (%)")
    innovation_benchmark = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Benchmark innovación (%)")
    
    # Totales
    total_overhead_benchmark = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Benchmark overhead total (%)")
    aura_enhanced_benchmark = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Benchmark AURA (%)")
    
    # Métricas estadísticas
    percentile_25 = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Percentil 25")
    percentile_50 = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Percentil 50")
    percentile_75 = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Percentil 75")
    percentile_90 = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Percentil 90")
    
    # Metadatos
    data_source = models.CharField(max_length=100, default='market_research', verbose_name="Fuente de datos")
    sample_size = models.IntegerField(default=0, verbose_name="Tamaño muestra")
    confidence_level = models.DecimalField(max_digits=5, decimal_places=2, default=95.00, verbose_name="Nivel confianza (%)")
    last_updated = models.DateTimeField(auto_now=True, verbose_name="Última actualización")
    
    # Estado
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Benchmark Overhead"
        verbose_name_plural = "Benchmarks Overhead"
        db_table = 'payroll_overhead_benchmark'
        unique_together = ['industry', 'region', 'company_size_range']
        indexes = [
            models.Index(fields=['industry'], name='payroll_oh_bm_industry_idx'),
            models.Index(fields=['region'], name='payroll_oh_bm_region_idx'),
            models.Index(fields=['company_size_range'], name='payroll_oh_bm_size_idx'),
            models.Index(fields=['total_overhead_benchmark'], name='payroll_oh_bm_total_idx'),
        ]
    
    def __str__(self):
        return f"Benchmark {self.industry} - {self.region} - {self.company_size_range}"
    
    def get_benchmark_range(self):
        """Obtiene rango de benchmark (P25-P75)"""
        return {
            'min': self.percentile_25,
            'max': self.percentile_75,
            'median': self.percentile_50,
            'top_decile': self.percentile_90
        } 

# ============================================================================
# NUEVOS MODELOS PARA GESTIÓN DE TURNOS Y HORARIOS
# ============================================================================

class EmployeeShift(models.Model):
    """
    Modelo para gestión de turnos y horarios de empleados
    """
    SHIFT_TYPES = [
        ('morning', 'Matutino'),
        ('afternoon', 'Vespertino'),
        ('night', 'Nocturno'),
        ('rotating', 'Rotativo'),
        ('flexible', 'Flexible'),
        ('remote', 'Remoto'),
        ('hybrid', 'Híbrido'),
    ]
    
    SHIFT_STATUS = [
        ('active', 'Activo'),
        ('inactive', 'Inactivo'),
        ('temporary', 'Temporal'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(PayrollEmployee, on_delete=models.CASCADE, related_name='shifts', verbose_name="Empleado")
    
    # Información del turno
    shift_name = models.CharField(max_length=100, verbose_name="Nombre del turno")
    shift_type = models.CharField(max_length=20, choices=SHIFT_TYPES, verbose_name="Tipo de turno")
    status = models.CharField(max_length=20, choices=SHIFT_STATUS, default='active', verbose_name="Estado")
    
    # Horarios
    start_time = models.TimeField(verbose_name="Hora de inicio")
    end_time = models.TimeField(verbose_name="Hora de fin")
    break_start = models.TimeField(null=True, blank=True, verbose_name="Inicio de descanso")
    break_end = models.TimeField(null=True, blank=True, verbose_name="Fin de descanso")
    
    # Días de trabajo
    work_days = models.JSONField(default=list, verbose_name="Días de trabajo")  # [1,2,3,4,5] para L-V
    
    # Ubicación
    location = models.JSONField(default=dict, verbose_name="Ubicación del turno")
    is_location_variable = models.BooleanField(default=False, verbose_name="Ubicación variable")
    
    # Configuración
    hours_per_day = models.DecimalField(max_digits=4, decimal_places=2, verbose_name="Horas por día")
    overtime_threshold = models.DecimalField(max_digits=4, decimal_places=2, default=8.0, verbose_name="Umbral horas extra")
    
    # Fechas
    effective_date = models.DateField(verbose_name="Fecha efectiva")
    end_date = models.DateField(null=True, blank=True, verbose_name="Fecha de fin")
    
    # Aprobación
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Aprobado por")
    approval_date = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de aprobación")
    
    # Notas
    notes = models.TextField(blank=True, verbose_name="Notas")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Turno de Empleado"
        verbose_name_plural = "Turnos de Empleados"
        db_table = 'payroll_employee_shift'
        indexes = [
            models.Index(fields=['employee', 'effective_date'], name='payroll_shift_emp_date_idx'),
            models.Index(fields=['shift_type'], name='payroll_shift_type_idx'),
            models.Index(fields=['status'], name='payroll_shift_status_idx'),
        ]
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.shift_name}"
    
    def get_current_shift(self, date=None):
        """Obtiene el turno actual para una fecha"""
        if not date:
            date = timezone.now().date()
        
        return EmployeeShift.objects.filter(
            employee=self.employee,
            effective_date__lte=date,
            end_date__isnull=True
        ).first()
    
    def get_weekly_schedule(self, week_start_date):
        """Obtiene horario semanal"""
        from datetime import timedelta
        
        schedule = {}
        for i in range(7):
            current_date = week_start_date + timedelta(days=i)
            day_of_week = current_date.weekday()
            
            if day_of_week in self.work_days:
                schedule[current_date] = {
                    'start_time': self.start_time,
                    'end_time': self.end_time,
                    'break_start': self.break_start,
                    'break_end': self.break_end,
                    'location': self.location,
                    'hours': self.hours_per_day
                }
        
        return schedule


class ShiftChangeRequest(models.Model):
    """
    Solicitudes de cambio de turno
    """
    REQUEST_TYPES = [
        ('temporary', 'Cambio temporal'),
        ('permanent', 'Cambio permanente'),
        ('swap', 'Intercambio'),
        ('emergency', 'Emergencia'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('approved', 'Aprobada'),
        ('rejected', 'Rechazada'),
        ('cancelled', 'Cancelada'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(PayrollEmployee, on_delete=models.CASCADE, related_name='shift_requests', verbose_name="Empleado")
    
    # Información de la solicitud
    request_type = models.CharField(max_length=20, choices=REQUEST_TYPES, verbose_name="Tipo de solicitud")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Estado")
    
    # Fechas del cambio
    start_date = models.DateField(verbose_name="Fecha de inicio")
    end_date = models.DateField(verbose_name="Fecha de fin")
    
    # Turno solicitado
    requested_shift = models.ForeignKey(EmployeeShift, on_delete=models.CASCADE, verbose_name="Turno solicitado")
    
    # Motivo
    reason = models.TextField(verbose_name="Motivo")
    emergency_details = models.TextField(blank=True, verbose_name="Detalles de emergencia")
    
    # Aprobación
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Aprobado por")
    approval_date = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de aprobación")
    approval_notes = models.TextField(blank=True, verbose_name="Notas de aprobación")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Solicitud de Cambio de Turno"
        verbose_name_plural = "Solicitudes de Cambio de Turno"
        db_table = 'payroll_shift_change_request'
        indexes = [
            models.Index(fields=['employee', 'status'], name='payroll_shift_req_emp_stat_idx'),
            models.Index(fields=['request_type'], name='payroll_shift_req_type_idx'),
            models.Index(fields=['start_date', 'end_date'], name='payroll_shift_req_dates_idx'),
        ]
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.get_request_type_display()}"


# ============================================================================
# MODELOS PARA FEEDBACK DE PAYROLL (EXTENSIÓN DEL SISTEMA EXISTENTE)
# ============================================================================

class PayrollFeedback(models.Model):
    """
    Feedback específico para el sistema de nómina
    Extiende el sistema de feedback existente
    """
    FEEDBACK_TYPES = [
        ('schedule', 'Horarios y Turnos'),
        ('supervisor', 'Supervisor'),
        ('hr', 'Recursos Humanos'),
        ('payroll', 'Nómina'),
        ('benefits', 'Beneficios'),
        ('workplace', 'Ambiente Laboral'),
        ('general', 'General'),
    ]
    
    PRIORITY_LEVELS = [
        ('low', 'Baja'),
        ('medium', 'Media'),
        ('high', 'Alta'),
        ('urgent', 'Urgente'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(PayrollEmployee, on_delete=models.CASCADE, related_name='payroll_feedback', verbose_name="Empleado")
    
    # Tipo y prioridad
    feedback_type = models.CharField(max_length=20, choices=FEEDBACK_TYPES, verbose_name="Tipo de feedback")
    priority = models.CharField(max_length=20, choices=PRIORITY_LEVELS, default='medium', verbose_name="Prioridad")
    
    # Contenido
    subject = models.CharField(max_length=200, verbose_name="Asunto")
    message = models.TextField(verbose_name="Mensaje")
    
    # Destinatarios
    send_to_supervisor = models.BooleanField(default=True, verbose_name="Enviar a supervisor")
    send_to_hr = models.BooleanField(default=False, verbose_name="Enviar a RRHH")
    
    # Estado
    is_anonymous = models.BooleanField(default=False, verbose_name="Anónimo")
    is_resolved = models.BooleanField(default=False, verbose_name="Resuelto")
    resolution_notes = models.TextField(blank=True, verbose_name="Notas de resolución")
    
    # Respuesta
    response_message = models.TextField(blank=True, verbose_name="Respuesta")
    responded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Respondido por")
    response_date = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de respuesta")
    
    # Metadatos
    created_via = models.CharField(max_length=20, default='whatsapp', verbose_name="Creado vía")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Feedback de Nómina"
        verbose_name_plural = "Feedback de Nómina"
        db_table = 'payroll_feedback'
        indexes = [
            models.Index(fields=['employee', 'feedback_type'], name='payroll_feedback_emp_type_idx'),
            models.Index(fields=['priority'], name='payroll_feedback_priority_idx'),
            models.Index(fields=['is_resolved'], name='payroll_feedback_resolved_idx'),
        ]
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.subject}"


class PerformanceEvaluation(models.Model):
    """
    Evaluaciones de desempeño periódicas
    """
    EVALUATION_TYPES = [
        ('quarterly', 'Trimestral'),
        ('semi_annual', 'Semestral'),
        ('annual', 'Anual'),
        ('probation', 'Período de prueba'),
        ('special', 'Especial'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Borrador'),
        ('in_progress', 'En progreso'),
        ('completed', 'Completada'),
        ('reviewed', 'Revisada'),
        ('approved', 'Aprobada'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(PayrollEmployee, on_delete=models.CASCADE, related_name='performance_evaluations', verbose_name="Empleado")
    evaluator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Evaluador")
    
    # Información de la evaluación
    evaluation_type = models.CharField(max_length=20, choices=EVALUATION_TYPES, verbose_name="Tipo de evaluación")
    evaluation_period_start = models.DateField(verbose_name="Inicio del período")
    evaluation_period_end = models.DateField(verbose_name="Fin del período")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name="Estado")
    
    # Calificaciones (1-5)
    job_knowledge = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], verbose_name="Conocimiento del trabajo")
    quality_of_work = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], verbose_name="Calidad del trabajo")
    quantity_of_work = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], verbose_name="Cantidad de trabajo")
    reliability = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], verbose_name="Confiabilidad")
    teamwork = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], verbose_name="Trabajo en equipo")
    communication = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], verbose_name="Comunicación")
    initiative = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], verbose_name="Iniciativa")
    leadership = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], verbose_name="Liderazgo")
    attendance = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], verbose_name="Asistencia")
    overall_rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], verbose_name="Calificación general")
    
    # Comentarios
    strengths = models.TextField(blank=True, verbose_name="Fortalezas")
    areas_for_improvement = models.TextField(blank=True, verbose_name="Áreas de mejora")
    goals = models.TextField(blank=True, verbose_name="Objetivos")
    comments = models.TextField(blank=True, verbose_name="Comentarios adicionales")
    
    # Aprobación
    employee_signature = models.BooleanField(default=False, verbose_name="Firma del empleado")
    employee_signature_date = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de firma empleado")
    supervisor_signature = models.BooleanField(default=False, verbose_name="Firma del supervisor")
    supervisor_signature_date = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de firma supervisor")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Evaluación de Desempeño"
        verbose_name_plural = "Evaluaciones de Desempeño"
        db_table = 'payroll_performance_evaluation'
        indexes = [
            models.Index(fields=['employee', 'evaluation_type'], name='payroll_perf_eval_emp_type_idx'),
            models.Index(fields=['status'], name='payroll_perf_eval_status_idx'),
            models.Index(fields=['overall_rating'], name='payroll_perf_eval_rating_idx'),
        ]
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.get_evaluation_type_display()} ({self.evaluation_period_start})"
    
    def calculate_overall_rating(self):
        """Calcula la calificación general promedio"""
        ratings = [
            self.job_knowledge, self.quality_of_work, self.quantity_of_work,
            self.reliability, self.teamwork, self.communication,
            self.initiative, self.leadership, self.attendance
        ]
        return sum(ratings) / len(ratings)


# ============================================================================
# MODELO PARA MATRIZ 9 BOXES
# ============================================================================

class NineBoxMatrix(models.Model):
    """
    Matriz 9 Boxes para gestión de talento
    """
    PERFORMANCE_LEVELS = [
        ('low', 'Bajo'),
        ('medium', 'Medio'),
        ('high', 'Alto'),
    ]
    
    POTENTIAL_LEVELS = [
        ('low', 'Bajo'),
        ('medium', 'Medio'),
        ('high', 'Alto'),
    ]
    
    BOX_CATEGORIES = [
        ('1', 'Estrella Emergente'),
        ('2', 'Alto Potencial'),
        ('3', 'Líder Estratégico'),
        ('4', 'Profesional Confiable'),
        ('5', 'Profesional Estable'),
        ('6', 'Profesional en Desarrollo'),
        ('7', 'Profesional Especializado'),
        ('8', 'Profesional Eficiente'),
        ('9', 'Profesional Básico'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(PayrollEmployee, on_delete=models.CASCADE, related_name='nine_box_evaluations', verbose_name="Empleado")
    evaluator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Evaluador")
    
    # Evaluación
    performance_level = models.CharField(max_length=10, choices=PERFORMANCE_LEVELS, verbose_name="Nivel de Desempeño")
    potential_level = models.CharField(max_length=10, choices=POTENTIAL_LEVELS, verbose_name="Nivel de Potencial")
    box_category = models.CharField(max_length=2, choices=BOX_CATEGORIES, verbose_name="Categoría 9 Boxes")
    
    # Métricas de evaluación
    performance_score = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(100)], verbose_name="Score de Desempeño")
    potential_score = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(100)], verbose_name="Score de Potencial")
    
    # Análisis detallado
    performance_factors = models.JSONField(default=dict, verbose_name="Factores de Desempeño")
    potential_factors = models.JSONField(default=dict, verbose_name="Factores de Potencial")
    
    # Recomendaciones
    development_plan = models.TextField(blank=True, verbose_name="Plan de Desarrollo")
    career_path = models.TextField(blank=True, verbose_name="Ruta de Carrera")
    retention_risk = models.CharField(max_length=20, choices=[
        ('low', 'Bajo'),
        ('medium', 'Medio'),
        ('high', 'Alto'),
        ('critical', 'Crítico'),
    ], verbose_name="Riesgo de Retención")
    
    # Acciones
    recommended_actions = models.JSONField(default=list, verbose_name="Acciones Recomendadas")
    timeline = models.CharField(max_length=50, blank=True, verbose_name="Timeline")
    
    # Seguimiento
    next_review_date = models.DateField(null=True, blank=True, verbose_name="Próxima Revisión")
    progress_notes = models.TextField(blank=True, verbose_name="Notas de Progreso")
    
    # Estado
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Matriz 9 Boxes"
        verbose_name_plural = "Matrices 9 Boxes"
        db_table = 'payroll_nine_box_matrix'
        indexes = [
            models.Index(fields=['employee', 'box_category'], name='payroll_nine_box_emp_cat_idx'),
            models.Index(fields=['performance_level', 'potential_level'], name='payroll_nine_box_perf_pot_idx'),
            models.Index(fields=['retention_risk'], name='payroll_nine_box_retention_idx'),
        ]
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - Box {self.box_category}"
    
    def get_box_description(self):
        """Obtiene la descripción de la categoría del box"""
        box_descriptions = {
            '1': 'Alto desempeño, alto potencial. Futuros líderes estratégicos.',
            '2': 'Alto desempeño, potencial medio. Líderes funcionales.',
            '3': 'Alto desempeño, bajo potencial. Especialistas técnicos.',
            '4': 'Desempeño medio, alto potencial. En desarrollo para liderazgo.',
            '5': 'Desempeño medio, potencial medio. Profesionales estables.',
            '6': 'Desempeño medio, bajo potencial. Necesita desarrollo.',
            '7': 'Bajo desempeño, alto potencial. Requiere coaching.',
            '8': 'Bajo desempeño, potencial medio. Necesita supervisión.',
            '9': 'Bajo desempeño, bajo potencial. Requiere acción inmediata.',
        }
        return box_descriptions.get(self.box_category, 'Categoría no definida')
    
    def calculate_box_category(self):
        """Calcula automáticamente la categoría del box basado en scores"""
        if self.performance_score >= 80 and self.potential_score >= 80:
            return '1'
        elif self.performance_score >= 80 and 60 <= self.potential_score < 80:
            return '2'
        elif self.performance_score >= 80 and self.potential_score < 60:
            return '3'
        elif 60 <= self.performance_score < 80 and self.potential_score >= 80:
            return '4'
        elif 60 <= self.performance_score < 80 and 60 <= self.potential_score < 80:
            return '5'
        elif 60 <= self.performance_score < 80 and self.potential_score < 60:
            return '6'
        elif self.performance_score < 60 and self.potential_score >= 80:
            return '7'
        elif self.performance_score < 60 and 60 <= self.potential_score < 80:
            return '8'
        else:
            return '9' 

# ============================================================================
# MODELO PARA PERMISOS ESPECIALES
# ============================================================================

class PermisoEspecial(models.Model):
    """
    Modelo para gestión de permisos especiales avanzados
    """
    PERMISO_TYPES = [
        ('maternity', 'Maternidad'),
        ('paternity', 'Paternidad'),
        ('illness', 'Enfermedad Prolongada'),
        ('home_office', 'Home Office'),
        ('license', 'Licencia'),
        ('promotion', 'Promoción'),
        ('recognition', 'Reconocimiento'),
        ('special_project', 'Proyecto Especial'),
        ('training', 'Capacitación'),
        ('other', 'Otro'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Borrador'),
        ('pending', 'Pendiente'),
        ('approved', 'Aprobado'),
        ('rejected', 'Rechazado'),
        ('cancelled', 'Cancelado'),
        ('completed', 'Completado'),
    ]
    
    PRIORITY_LEVELS = [
        ('low', 'Baja'),
        ('medium', 'Media'),
        ('high', 'Alta'),
        ('urgent', 'Urgente'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(PayrollEmployee, on_delete=models.CASCADE, related_name='permisos_especiales', verbose_name="Empleado")
    
    # Información del permiso
    permiso_type = models.CharField(max_length=20, choices=PERMISO_TYPES, verbose_name="Tipo de Permiso")
    title = models.CharField(max_length=200, verbose_name="Título del Permiso")
    description = models.TextField(verbose_name="Descripción")
    
    # Fechas
    start_date = models.DateField(verbose_name="Fecha de Inicio")
    end_date = models.DateField(verbose_name="Fecha de Fin")
    days_requested = models.IntegerField(verbose_name="Días Solicitados")
    
    # Estado y prioridad
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name="Estado")
    priority = models.CharField(max_length=20, choices=PRIORITY_LEVELS, default='medium', verbose_name="Prioridad")
    
    # Detalles específicos por tipo
    details = models.JSONField(default=dict, verbose_name="Detalles Específicos")
    
    # Documentación
    supporting_documents = models.JSONField(default=list, verbose_name="Documentos de Apoyo")
    medical_certificate = models.BooleanField(default=False, verbose_name="Certificado Médico")
    legal_documentation = models.BooleanField(default=False, verbose_name="Documentación Legal")
    
    # Aprobación workflow
    supervisor_approval = models.BooleanField(default=False, verbose_name="Aprobación Supervisor")
    hr_approval = models.BooleanField(default=False, verbose_name="Aprobación RRHH")
    management_approval = models.BooleanField(default=False, verbose_name="Aprobación Gerencia")
    
    # Usuarios que aprobaron
    approved_by_supervisor = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='permisos_aprobados_supervisor',
        verbose_name="Aprobado por Supervisor"
    )
    approved_by_hr = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='permisos_aprobados_hr',
        verbose_name="Aprobado por RRHH"
    )
    approved_by_management = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='permisos_aprobados_management',
        verbose_name="Aprobado por Gerencia"
    )
    
    # Fechas de aprobación
    supervisor_approval_date = models.DateTimeField(null=True, blank=True, verbose_name="Fecha Aprobación Supervisor")
    hr_approval_date = models.DateTimeField(null=True, blank=True, verbose_name="Fecha Aprobación RRHH")
    management_approval_date = models.DateTimeField(null=True, blank=True, verbose_name="Fecha Aprobación Gerencia")
    
    # Notas y comentarios
    supervisor_notes = models.TextField(blank=True, verbose_name="Notas del Supervisor")
    hr_notes = models.TextField(blank=True, verbose_name="Notas de RRHH")
    management_notes = models.TextField(blank=True, verbose_name="Notas de Gerencia")
    
    # Impacto en nómina
    salary_impact = models.JSONField(default=dict, verbose_name="Impacto en Salario")
    benefits_impact = models.JSONField(default=dict, verbose_name="Impacto en Beneficios")
    
    # Notificaciones
    notifications_sent = models.JSONField(default=list, verbose_name="Notificaciones Enviadas")
    
    # Metadatos
    created_via = models.CharField(max_length=20, default='admin', verbose_name="Creado vía")
    is_urgent = models.BooleanField(default=False, verbose_name="Urgente")
    requires_immediate_attention = models.BooleanField(default=False, verbose_name="Requiere Atención Inmediata")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Permiso Especial"
        verbose_name_plural = "Permisos Especiales"
        db_table = 'payroll_permiso_especial'
        indexes = [
            models.Index(fields=['employee', 'permiso_type'], name='payroll_permiso_emp_type_idx'),
            models.Index(fields=['status'], name='payroll_permiso_status_idx'),
            models.Index(fields=['priority'], name='payroll_permiso_priority_idx'),
            models.Index(fields=['start_date', 'end_date'], name='payroll_permiso_dates_idx'),
            models.Index(fields=['is_urgent'], name='payroll_permiso_urgent_idx'),
        ]
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.get_permiso_type_display()} ({self.start_date})"
    
    def get_approval_status(self):
        """Obtiene el estado de aprobación completo"""
        if self.status == 'draft':
            return 'Borrador'
        elif self.status == 'pending':
            if not self.supervisor_approval:
                return 'Pendiente Supervisor'
            elif not self.hr_approval:
                return 'Pendiente RRHH'
            elif not self.management_approval:
                return 'Pendiente Gerencia'
            else:
                return 'Pendiente Final'
        elif self.status == 'approved':
            return 'Aprobado'
        elif self.status == 'rejected':
            return 'Rechazado'
        elif self.status == 'cancelled':
            return 'Cancelado'
        elif self.status == 'completed':
            return 'Completado'
        return 'Desconocido'
    
    def can_approve(self, user):
        """Verifica si un usuario puede aprobar este permiso"""
        if not self.supervisor_approval and user == self.employee.supervisor:
            return True
        elif self.supervisor_approval and not self.hr_approval and user.has_perm('payroll.can_approve_hr'):
            return True
        elif self.hr_approval and not self.management_approval and user.has_perm('payroll.can_approve_management'):
            return True
        return False
    
    def approve(self, user):
        """Aprueba el permiso por el usuario especificado"""
        if user == self.employee.supervisor and not self.supervisor_approval:
            self.supervisor_approval = True
            self.approved_by_supervisor = user
            self.supervisor_approval_date = timezone.now()
        elif user.has_perm('payroll.can_approve_hr') and not self.hr_approval:
            self.hr_approval = True
            self.approved_by_hr = user
            self.hr_approval_date = timezone.now()
        elif user.has_perm('payroll.can_approve_management') and not self.management_approval:
            self.management_approval = True
            self.approved_by_management = user
            self.management_approval_date = timezone.now()
        
        # Si todas las aprobaciones están completas, cambiar estado
        if self.supervisor_approval and self.hr_approval and self.management_approval:
            self.status = 'approved'
        
        self.save()
    
    def reject(self, user, reason=""):
        """Rechaza el permiso"""
        self.status = 'rejected'
        if user == self.employee.supervisor:
            self.supervisor_notes = reason
        elif user.has_perm('payroll.can_approve_hr'):
            self.hr_notes = reason
        elif user.has_perm('payroll.can_approve_management'):
            self.management_notes = reason
        self.save()
    
    def get_days_remaining(self):
        """Calcula los días restantes del permiso"""
        today = timezone.now().date()
        if today > self.end_date:
            return 0
        return (self.end_date - today).days
    
    def is_active(self):
        """Verifica si el permiso está activo"""
        today = timezone.now().date()
        return self.start_date <= today <= self.end_date and self.status == 'approved'
    
    def get_impact_summary(self):
        """Obtiene un resumen del impacto del permiso"""
        return {
            'salary_impact': self.salary_impact,
            'benefits_impact': self.benefits_impact,
            'days_remaining': self.get_days_remaining(),
            'is_active': self.is_active(),
            'approval_status': self.get_approval_status()
        }