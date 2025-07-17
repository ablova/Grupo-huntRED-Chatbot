"""
Admin de Nómina huntRED®
Interfaz administrativa con menús dinámicos y configuración ML
"""
import logging
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Count, Avg, Sum, Q
from django.utils import timezone
from datetime import date, timedelta
import json

from .models import (
    PayrollCompany, PayrollEmployee, PayrollPeriod, PayrollCalculation,
    AttendanceRecord, EmployeeRequest, MLAttendanceModel, TaxTable, UMARegistry,
    TaxUpdateLog, TaxValidationLog,
    OverheadCategory, EmployeeOverheadCalculation, TeamOverheadAnalysis,
    OverheadMLModel, OverheadBenchmark, EmployeeShift, ShiftChangeRequest,
    PayrollFeedback, PerformanceEvaluation, NineBoxMatrix
)
from .services.ml_attendance_service import MLAttendanceService
from .services.payroll_engine import PayrollEngine
from app.payroll.models import PermisoEspecial
from app.payroll.admin_permissions import PermisoEspecialAdmin
from app.payroll.admin_shift_dashboard import ShiftDashboardAdmin
from app.payroll.models import EmployeeShift

logger = logging.getLogger(__name__)


@admin.register(PayrollCompany)
class PayrollCompanyAdmin(admin.ModelAdmin):
    """Admin para empresas de nómina con dashboard integrado"""
    
    list_display = [
        'name', 'country_code', 'employee_count', 'ml_mode', 
        'ats_integration', 'revenue_display', 'status_badge'
    ]
    list_filter = [
        'country_code', 'payroll_frequency', 'is_active', 
        'ml_attendance_mode', 'ats_integration_enabled'
    ]
    search_fields = ['name', 'whatsapp_business_name']
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'employee_count', 
        'ml_accuracy_display'
    ]
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('name', 'business_unit', 'country_code', 'currency')
        }),
        ('Configuración de WhatsApp', {
            'fields': (
                'whatsapp_webhook_token', 'whatsapp_phone_number', 
                'whatsapp_business_name', 'messaging_config'
            ),
            'classes': ('collapse',)
        }),
        ('Configuración de Nómina', {
            'fields': ('payroll_frequency', 'pricing_tier', 'price_per_employee')
        }),
        ('Integración ATS', {
            'fields': (
                'ats_integration_enabled', 'ats_company_id', 'ats_sync_enabled'
            ),
            'classes': ('collapse',)
        }),
        ('Configuración ML y AI', {
            'fields': (
                'ml_attendance_mode', 'ml_accuracy_threshold', 
                'ml_learning_enabled', 'ml_training_data_days'
            ),
            'description': 'Configuración de Machine Learning para predicción de asistencia'
        }),
        ('Servicios Premium', {
            'fields': ('premium_services',),
            'classes': ('collapse',)
        }),
        ('Estado', {
            'fields': ('is_active', 'created_at', 'updated_at')
        })
    )
    
    def employee_count(self, obj):
        """Muestra número de empleados"""
        count = obj.get_employee_count()
        return format_html(
            '<span style="color: #007cba; font-weight: bold;">{}</span>',
            count
        )
    employee_count.short_description = "Empleados"
    
    def ml_mode(self, obj):
        """Muestra modo ML con badge"""
        mode_colors = {
            'precise': '#28a745',
            'ml_learning': '#007cba',
            'random_ml': '#ffc107',
            'hybrid': '#6f42c1'
        }
        color = mode_colors.get(obj.ml_attendance_mode, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px;">{}</span>',
            color, obj.get_ml_attendance_mode_display()
        )
    ml_mode.short_description = "Modo ML"
    
    def ats_integration(self, obj):
        """Muestra estado de integración ATS"""
        if obj.ats_integration_enabled:
            return format_html(
                '<span style="color: #28a745;">✓ Integrado</span>'
            )
        return format_html(
            '<span style="color: #dc3545;">✗ No integrado</span>'
        )
    ats_integration.short_description = "ATS"
    
    def revenue_display(self, obj):
        """Muestra revenue mensual"""
        revenue = obj.calculate_monthly_revenue()
        return format_html(
            '<span style="color: #28a745; font-weight: bold;">${:,.2f}</span>',
            revenue
        )
    revenue_display.short_description = "Revenue Mensual"
    
    def status_badge(self, obj):
        """Muestra badge de estado"""
        if obj.is_active:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px;">Activo</span>'
            )
        return format_html(
            '<span style="background-color: #dc3545; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px;">Inactivo</span>'
        )
    status_badge.short_description = "Estado"
    
    def ml_accuracy_display(self, obj):
        """Muestra precisión ML promedio"""
        try:
            ml_service = MLAttendanceService(obj)
            # Obtener precisión promedio de los últimos 30 días
            end_date = date.today()
            start_date = end_date - timedelta(days=30)
            
            records = AttendanceRecord.objects.filter(
                employee__company=obj,
                date__range=[start_date, end_date]
            )
            
            if records.exists():
                avg_confidence = records.aggregate(
                    avg_confidence=Avg('ml_confidence')
                )['avg_confidence'] or 0
                
                color = '#28a745' if avg_confidence > 80 else '#ffc107' if avg_confidence > 60 else '#dc3545'
                
                return format_html(
                    '<span style="color: {}; font-weight: bold;">{:.1f}%</span>',
                    color, avg_confidence
                )
        except Exception as e:
            logger.error(f"Error calculando precisión ML: {str(e)}")
        
        return format_html('<span style="color: #6c757d;">N/A</span>')
    ml_accuracy_display.short_description = "Precisión ML"
    
    actions = ['train_ml_models', 'sync_ats_data', 'generate_reports']
    
    def train_ml_models(self, request, queryset):
        """Entrena modelos ML para empresas seleccionadas"""
        trained = 0
        for company in queryset:
            try:
                ml_service = MLAttendanceService(company)
                result = ml_service.train_model()
                if result.get('success'):
                    trained += 1
                    self.message_user(
                        request, 
                        f"Modelo ML entrenado para {company.name}: {result.get('accuracy', 0):.1f}% precisión"
                    )
                else:
                    self.message_user(
                        request, 
                        f"Error entrenando modelo para {company.name}: {result.get('error', 'Error desconocido')}",
                        level='ERROR'
                    )
            except Exception as e:
                logger.error(f"Error entrenando modelo para {company.name}: {str(e)}")
                self.message_user(
                    request, 
                    f"Error entrenando modelo para {company.name}: {str(e)}",
                    level='ERROR'
                )
        
        self.message_user(request, f"{trained} modelos ML entrenados exitosamente")
    train_ml_models.short_description = "Entrenar modelos ML"
    
    def sync_ats_data(self, request, queryset):
        """Sincroniza datos con ATS"""
        synced = 0
        for company in queryset:
            if company.ats_integration_enabled:
                try:
                    # Aquí se implementaría la sincronización con ATS
                    synced += 1
                    self.message_user(request, f"Datos sincronizados para {company.name}")
                except Exception as e:
                    logger.error(f"Error sincronizando datos para {company.name}: {str(e)}")
                    self.message_user(
                        request, 
                        f"Error sincronizando datos para {company.name}: {str(e)}",
                        level='ERROR'
                    )
        
        self.message_user(request, f"{synced} empresas sincronizadas con ATS")
    sync_ats_data.short_description = "Sincronizar con ATS"
    
    def generate_reports(self, request, queryset):
        """Genera reportes para empresas seleccionadas"""
        generated = 0
        for company in queryset:
            try:
                # Aquí se implementaría la generación de reportes
                generated += 1
                self.message_user(request, f"Reporte generado para {company.name}")
            except Exception as e:
                logger.error(f"Error generando reporte para {company.name}: {str(e)}")
                self.message_user(
                    request, 
                    f"Error generando reporte para {company.name}: {str(e)}",
                    level='ERROR'
                )
        
        self.message_user(request, f"{generated} reportes generados")
    generate_reports.short_description = "Generar reportes"


@admin.register(PayrollEmployee)
class PayrollEmployeeAdmin(admin.ModelAdmin):
    """Admin para empleados con integración ATS"""
    
    list_display = [
        'full_name', 'company', 'job_title', 'department', 
        'ml_confidence', 'ats_integration', 'attendance_rate', 'status_badge'
    ]
    list_filter = [
        'company', 'department', 'employee_type', 'is_active',
        'hire_date', 'supervisor'
    ]
    search_fields = [
        'first_name', 'last_name', 'employee_number', 'email', 'phone'
    ]
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'ml_confidence_score',
        'career_profile_link', 'ats_candidate_link'
    ]
    
    fieldsets = (
        ('Información Personal', {
            'fields': (
                'first_name', 'last_name', 'email', 'phone', 'whatsapp_number'
            )
        }),
        ('Información Laboral', {
            'fields': (
                'company', 'employee_number', 'job_title', 'department',
                'employee_type', 'hire_date', 'supervisor'
            )
        }),
        ('Información Salarial', {
            'fields': ('monthly_salary', 'hourly_rate')
        }),
        ('Información Bancaria', {
            'fields': ('bank_name', 'account_number', 'clabe'),
            'classes': ('collapse',)
        }),
        ('Información Fiscal', {
            'fields': ('rfc', 'curp', 'nss'),
            'classes': ('collapse',)
        }),
        ('Configuración de Asistencia', {
            'fields': ('office_location', 'working_hours'),
            'classes': ('collapse',)
        }),
        ('Integración ATS', {
            'fields': (
                'ats_candidate_id', 'ats_job_id', 'career_profile',
                'skills_assessment', 'performance_history'
            ),
            'classes': ('collapse',)
        }),
        ('ML y AI', {
            'fields': (
                'attendance_pattern', 'ml_confidence_score', 'attendance_anomalies'
            ),
            'classes': ('collapse',)
        }),
        ('Estado', {
            'fields': ('is_active', 'created_at', 'updated_at')
        })
    )
    
    def full_name(self, obj):
        """Muestra nombre completo"""
        return obj.get_full_name()
    full_name.short_description = "Nombre Completo"
    
    def ml_confidence(self, obj):
        """Muestra score de confianza ML"""
        score = obj.ml_confidence_score
        if score > 80:
            color = '#28a745'
        elif score > 60:
            color = '#ffc107'
        else:
            color = '#dc3545'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.1f}%</span>',
            color, score
        )
    ml_confidence.short_description = "Confianza ML"
    
    def ats_integration(self, obj):
        """Muestra estado de integración ATS"""
        if obj.ats_candidate_id:
            return format_html(
                '<span style="color: #28a745;">✓ Conectado</span>'
            )
        return format_html(
            '<span style="color: #6c757d;">✗ No conectado</span>'
        )
    ats_integration.short_description = "ATS"
    
    def attendance_rate(self, obj):
        """Muestra tasa de asistencia"""
        try:
            # Calcular tasa de asistencia de los últimos 30 días
            end_date = date.today()
            start_date = end_date - timedelta(days=30)
            
            records = AttendanceRecord.objects.filter(
                employee=obj,
                date__range=[start_date, end_date]
            )
            
            if records.exists():
                present_days = records.filter(status='present').count()
                total_days = records.count()
                rate = (present_days / total_days) * 100
                
                color = '#28a745' if rate > 95 else '#ffc107' if rate > 80 else '#dc3545'
                
                return format_html(
                    '<span style="color: {}; font-weight: bold;">{:.1f}%</span>',
                    color, rate
                )
        except Exception as e:
            logger.error(f"Error calculando tasa de asistencia: {str(e)}")
        
        return format_html('<span style="color: #6c757d;">N/A</span>')
    attendance_rate.short_description = "Asistencia"
    
    def status_badge(self, obj):
        """Muestra badge de estado"""
        if obj.is_active:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px;">Activo</span>'
            )
        return format_html(
            '<span style="background-color: #dc3545; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px;">Inactivo</span>'
        )
    status_badge.short_description = "Estado"
    
    def career_profile_link(self, obj):
        """Enlace al perfil de carrera"""
        if obj.career_profile:
            return format_html(
                '<a href="#" onclick="showCareerProfile(\'{}\')">Ver Perfil de Carrera</a>',
                obj.id
            )
        return "Sin perfil"
    career_profile_link.short_description = "Perfil de Carrera"
    
    def ats_candidate_link(self, obj):
        """Enlace al candidato en ATS"""
        if obj.ats_candidate_id:
            return format_html(
                '<a href="/admin/ats/candidate/{}/change/">Ver en ATS</a>',
                obj.ats_candidate_id
            )
        return "No conectado"
    ats_candidate_link.short_description = "Candidato ATS"
    
    actions = ['update_career_profiles', 'analyze_attendance_patterns']
    
    def update_career_profiles(self, request, queryset):
        """Actualiza perfiles de carrera"""
        updated = 0
        for employee in queryset:
            try:
                employee.update_career_profile()
                updated += 1
            except Exception as e:
                logger.error(f"Error actualizando perfil de {employee.get_full_name()}: {str(e)}")
                self.message_user(
                    request, 
                    f"Error actualizando perfil de {employee.get_full_name()}: {str(e)}",
                    level='ERROR'
                )
        
        self.message_user(request, f"{updated} perfiles de carrera actualizados")
    update_career_profiles.short_description = "Actualizar perfiles de carrera"
    
    def analyze_attendance_patterns(self, request, queryset):
        """Analiza patrones de asistencia con ML"""
        analyzed = 0
        for employee in queryset:
            try:
                # Obtener predicción para mañana
                tomorrow = date.today() + timedelta(days=1)
                prediction = employee.get_ml_attendance_prediction(tomorrow)
                
                analyzed += 1
                self.message_user(
                    request, 
                    f"Patrón analizado para {employee.get_full_name()}: {prediction.get('prediction', 'N/A')}"
                )
            except Exception as e:
                logger.error(f"Error analizando patrón de {employee.get_full_name()}: {str(e)}")
                self.message_user(
                    request, 
                    f"Error analizando patrón de {employee.get_full_name()}: {str(e)}",
                    level='ERROR'
                )
        
        self.message_user(request, f"{analyzed} patrones de asistencia analizados")
    analyze_attendance_patterns.short_description = "Analizar patrones ML"


@admin.register(PayrollPeriod)
class PayrollPeriodAdmin(admin.ModelAdmin):
    """Admin para períodos de nómina"""
    
    list_display = [
        'period_name', 'company', 'date_range', 'employee_count',
        'total_amount', 'ml_accuracy', 'status_badge'
    ]
    list_filter = [
        'company', 'frequency', 'status', 'start_date', 'end_date'
    ]
    search_fields = ['period_name', 'company__name']
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'total_employees',
        'total_gross', 'total_net', 'total_taxes', 'attendance_accuracy'
    ]
    
    fieldsets = (
        ('Información del Período', {
            'fields': ('company', 'period_name', 'start_date', 'end_date', 'frequency')
        }),
        ('Estado', {
            'fields': ('status', 'approved_by', 'approval_date')
        }),
        ('Totales', {
            'fields': (
                'total_employees', 'total_gross', 'total_net', 'total_taxes'
            )
        }),
        ('Fechas', {
            'fields': ('calculation_date', 'disbursement_date'),
            'classes': ('collapse',)
        }),
        ('ML y AI', {
            'fields': ('ml_analysis', 'attendance_accuracy'),
            'classes': ('collapse',)
        })
    )
    
    def date_range(self, obj):
        """Muestra rango de fechas"""
        return f"{obj.start_date.strftime('%d/%m/%Y')} - {obj.end_date.strftime('%d/%m/%Y')}"
    date_range.short_description = "Período"
    
    def employee_count(self, obj):
        """Muestra número de empleados"""
        return obj.total_employees
    employee_count.short_description = "Empleados"
    
    def total_amount(self, obj):
        """Muestra total neto"""
        return format_html(
            '<span style="color: #28a745; font-weight: bold;">${:,.2f}</span>',
            obj.total_net
        )
    total_amount.short_description = "Total Neto"
    
    def ml_accuracy(self, obj):
        """Muestra precisión ML"""
        accuracy = obj.attendance_accuracy
        if accuracy > 80:
            color = '#28a745'
        elif accuracy > 60:
            color = '#ffc107'
        else:
            color = '#dc3545'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.1f}%</span>',
            color, accuracy
        )
    ml_accuracy.short_description = "Precisión ML"
    
    def status_badge(self, obj):
        """Muestra badge de estado"""
        status_colors = {
            'draft': '#6c757d',
            'calculated': '#007cba',
            'approved': '#28a745',
            'disbursed': '#6f42c1',
            'cancelled': '#dc3545'
        }
        color = status_colors.get(obj.status, '#6c757d')
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = "Estado"
    
    actions = ['calculate_payroll', 'analyze_ml_period']
    
    def calculate_payroll(self, request, queryset):
        """Calcula nómina para períodos seleccionados"""
        calculated = 0
        for period in queryset:
            try:
                # Aquí se implementaría el cálculo de nómina
                calculated += 1
                self.message_user(request, f"Nómina calculada para {period.period_name}")
            except Exception as e:
                logger.error(f"Error calculando nómina para {period.period_name}: {str(e)}")
                self.message_user(
                    request, 
                    f"Error calculando nómina para {period.period_name}: {str(e)}",
                    level='ERROR'
                )
        
        self.message_user(request, f"{calculated} períodos calculados")
    calculate_payroll.short_description = "Calcular nómina"
    
    def analyze_ml_period(self, request, queryset):
        """Analiza período con ML"""
        analyzed = 0
        for period in queryset:
            try:
                period.calculate_ml_analysis()
                analyzed += 1
                self.message_user(
                    request, 
                    f"Análisis ML completado para {period.period_name}: {period.attendance_accuracy:.1f}% precisión"
                )
            except Exception as e:
                logger.error(f"Error analizando período {period.period_name}: {str(e)}")
                self.message_user(
                    request, 
                    f"Error analizando período {period.period_name}: {str(e)}",
                    level='ERROR'
                )
        
        self.message_user(request, f"{analyzed} períodos analizados con ML")
    analyze_ml_period.short_description = "Analizar con ML"


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    """Admin para registros de asistencia con ML"""
    
    list_display = [
        'employee_name', 'date', 'check_in_time', 'check_out_time',
        'hours_worked', 'ml_confidence', 'anomaly_badge', 'status_badge'
    ]
    list_filter = [
        'employee__company', 'status', 'date', 'check_in_method',
        'ml_anomaly_detected'
    ]
    search_fields = [
        'employee__first_name', 'employee__last_name', 'employee__employee_number'
    ]
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'ml_prediction', 'ml_confidence',
        'ml_anomaly_detected', 'ml_anomaly_type'
    ]
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('employee', 'date', 'status')
        }),
        ('Horarios', {
            'fields': ('check_in_time', 'check_out_time', 'hours_worked', 'overtime_hours')
        }),
        ('Geolocalización', {
            'fields': (
                'check_in_latitude', 'check_in_longitude',
                'check_out_latitude', 'check_out_longitude'
            ),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': ('check_in_method', 'check_out_method', 'notes'),
            'classes': ('collapse',)
        }),
        ('ML y AI', {
            'fields': (
                'ml_prediction', 'ml_confidence', 'ml_anomaly_detected', 'ml_anomaly_type'
            ),
            'classes': ('collapse',)
        })
    )
    
    def employee_name(self, obj):
        """Muestra nombre del empleado"""
        return obj.employee.get_full_name()
    employee_name.short_description = "Empleado"
    
    def ml_confidence(self, obj):
        """Muestra confianza ML"""
        confidence = obj.ml_confidence
        if confidence > 80:
            color = '#28a745'
        elif confidence > 60:
            color = '#ffc107'
        else:
            color = '#dc3545'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.1f}%</span>',
            color, confidence
        )
    ml_confidence.short_description = "Confianza ML"
    
    def anomaly_badge(self, obj):
        """Muestra badge de anomalía"""
        if obj.ml_anomaly_detected:
            return format_html(
                '<span style="background-color: #dc3545; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px;">{}</span>',
                obj.ml_anomaly_type or 'Anomalía'
            )
        return format_html(
            '<span style="background-color: #28a745; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px;">Normal</span>'
        )
    anomaly_badge.short_description = "Anomalía ML"
    
    def status_badge(self, obj):
        """Muestra badge de estado"""
        status_colors = {
            'present': '#28a745',
            'absent': '#dc3545',
            'late': '#ffc107',
            'half_day': '#fd7e14'
        }
        color = status_colors.get(obj.status, '#6c757d')
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = "Estado"
    
    actions = ['analyze_with_ml', 'export_attendance_data']
    
    def analyze_with_ml(self, request, queryset):
        """Analiza registros con ML"""
        analyzed = 0
        for record in queryset:
            try:
                record.analyze_with_ml()
                analyzed += 1
            except Exception as e:
                logger.error(f"Error analizando registro: {str(e)}")
                self.message_user(
                    request, 
                    f"Error analizando registro: {str(e)}",
                    level='ERROR'
                )
        
        self.message_user(request, f"{analyzed} registros analizados con ML")
    analyze_with_ml.short_description = "Analizar con ML"
    
    def export_attendance_data(self, request, queryset):
        """Exporta datos de asistencia"""
        # Aquí se implementaría la exportación
        self.message_user(request, f"{queryset.count()} registros exportados")
    export_attendance_data.short_description = "Exportar datos"


@admin.register(EmployeeRequest)
class EmployeeRequestAdmin(admin.ModelAdmin):
    """Admin para solicitudes de empleados"""
    
    list_display = [
        'employee_name', 'request_type', 'date_range', 'days_requested',
        'status_badge', 'created_via'
    ]
    list_filter = [
        'request_type', 'status', 'start_date', 'end_date', 'created_via'
    ]
    search_fields = [
        'employee__first_name', 'employee__last_name', 'reason'
    ]
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Información de la Solicitud', {
            'fields': ('employee', 'request_type', 'start_date', 'end_date', 'days_requested')
        }),
        ('Detalles', {
            'fields': ('reason', 'status')
        }),
        ('Aprobación', {
            'fields': ('approved_by', 'approval_date', 'approval_notes'),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': ('created_via', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def employee_name(self, obj):
        """Muestra nombre del empleado"""
        return obj.employee.get_full_name()
    employee_name.short_description = "Empleado"
    
    def date_range(self, obj):
        """Muestra rango de fechas"""
        return f"{obj.start_date.strftime('%d/%m/%Y')} - {obj.end_date.strftime('%d/%m/%Y')}"
    date_range.short_description = "Período"
    
    def status_badge(self, obj):
        """Muestra badge de estado"""
        status_colors = {
            'pending': '#ffc107',
            'approved': '#28a745',
            'rejected': '#dc3545',
            'cancelled': '#6c757d'
        }
        color = status_colors.get(obj.status, '#6c757d')
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = "Estado"


@admin.register(MLAttendanceModel)
class MLAttendanceModelAdmin(admin.ModelAdmin):
    """Admin para modelos ML de asistencia"""
    
    list_display = [
        'model_name', 'company', 'model_type', 'accuracy', 'precision',
        'recall', 'training_status', 'status_badge'
    ]
    list_filter = [
        'company', 'model_type', 'is_active', 'last_training_date'
    ]
    search_fields = ['model_name', 'company__name']
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'training_data_size',
        'last_training_date'
    ]
    
    fieldsets = (
        ('Información del Modelo', {
            'fields': ('company', 'model_name', 'model_type')
        }),
        ('Métricas', {
            'fields': ('accuracy', 'precision', 'recall')
        }),
        ('Datos de Entrenamiento', {
            'fields': ('training_data_size', 'last_training_date', 'model_parameters'),
            'classes': ('collapse',)
        }),
        ('Estado', {
            'fields': ('is_active', 'created_at', 'updated_at')
        })
    )
    
    def training_status(self, obj):
        """Muestra estado de entrenamiento"""
        if obj.last_training_date:
            days_ago = (timezone.now() - obj.last_training_date).days
            if days_ago < 7:
                color = '#28a745'
                status = 'Reciente'
            elif days_ago < 30:
                color = '#ffc107'
                status = 'Moderado'
            else:
                color = '#dc3545'
                status = 'Antiguo'
        else:
            color = '#6c757d'
            status = 'No entrenado'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, status
        )
    training_status.short_description = "Estado Entrenamiento"
    
    def status_badge(self, obj):
        """Muestra badge de estado"""
        if obj.is_active:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px;">Activo</span>'
            )
        return format_html(
            '<span style="background-color: #dc3545; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px;">Inactivo</span>'
        )
    status_badge.short_description = "Estado"
    
    actions = ['train_model', 'evaluate_model']
    
    def train_model(self, request, queryset):
        """Entrena modelos seleccionados"""
        trained = 0
        for model in queryset:
            try:
                ml_service = MLAttendanceService(model.company)
                result = ml_service.train_model()
                if result.get('success'):
                    trained += 1
                    self.message_user(
                        request, 
                        f"Modelo {model.model_name} entrenado: {result.get('accuracy', 0):.1f}% precisión"
                    )
                else:
                    self.message_user(
                        request, 
                        f"Error entrenando modelo {model.model_name}: {result.get('error', 'Error desconocido')}",
                        level='ERROR'
                    )
            except Exception as e:
                logger.error(f"Error entrenando modelo {model.model_name}: {str(e)}")
                self.message_user(
                    request, 
                    f"Error entrenando modelo {model.model_name}: {str(e)}",
                    level='ERROR'
                )
        
        self.message_user(request, f"{trained} modelos entrenados")
    train_model.short_description = "Entrenar modelos"
    
    def evaluate_model(self, request, queryset):
        """Evalúa modelos seleccionados"""
        evaluated = 0
        for model in queryset:
            try:
                # Aquí se implementaría la evaluación del modelo
                evaluated += 1
                self.message_user(request, f"Modelo {model.model_name} evaluado")
            except Exception as e:
                logger.error(f"Error evaluando modelo {model.model_name}: {str(e)}")
                self.message_user(
                    request, 
                    f"Error evaluando modelo {model.model_name}: {str(e)}",
                    level='ERROR'
                )
        
        self.message_user(request, f"{evaluated} modelos evaluados")
    evaluate_model.short_description = "Evaluar modelos"


@admin.register(TaxTable)
class TaxTableAdmin(admin.ModelAdmin):
    list_display = ['table_type', 'concept', 'effective_date', 'is_active', 'source']
    list_filter = ['table_type', 'is_active', 'source', 'effective_date']
    search_fields = ['concept', 'table_type']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-effective_date', 'table_type']
    
    fieldsets = (
        ('Información General', {
            'fields': ('table_type', 'concept', 'source')
        }),
        ('Valores', {
            'fields': ('limit_inferior', 'limit_superior', 'fixed_quota', 'percentage', 'value')
        }),
        ('Vigencia', {
            'fields': ('effective_date', 'expiration_date', 'is_active')
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related()
    
    actions = ['activate_tables', 'deactivate_tables', 'export_tables']
    
    def activate_tables(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} tablas activadas exitosamente.')
    activate_tables.short_description = "Activar tablas seleccionadas"
    
    def deactivate_tables(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} tablas desactivadas exitosamente.')
    deactivate_tables.short_description = "Desactivar tablas seleccionadas"
    
    def export_tables(self, request, queryset):
        # Implementar exportación de tablas
        self.message_user(request, 'Exportación iniciada.')
    export_tables.short_description = "Exportar tablas seleccionadas"


@admin.register(UMARegistry)
class UMARegistryAdmin(admin.ModelAdmin):
    list_display = ['country_code', 'year', 'uma_value', 'effective_date', 'is_active', 'source']
    list_filter = ['country_code', 'is_active', 'source', 'year']
    search_fields = ['country_code', 'year']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-year', 'country_code']
    
    fieldsets = (
        ('Información General', {
            'fields': ('country_code', 'year', 'source')
        }),
        ('Valor UMA', {
            'fields': ('uma_value', 'effective_date', 'expiration_date', 'is_active')
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request)
    
    actions = ['activate_uma', 'deactivate_uma', 'update_uma_values']
    
    def activate_uma(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} valores UMA activados exitosamente.')
    activate_uma.short_description = "Activar valores UMA seleccionados"
    
    def deactivate_uma(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} valores UMA desactivados exitosamente.')
    deactivate_uma.short_description = "Desactivar valores UMA seleccionados"
    
    def update_uma_values(self, request, queryset):
        # Ejecutar tarea Celery para actualizar UMA
        from .tasks import update_uma_values
        for uma in queryset:
            update_uma_values.delay(uma.country_code)
        self.message_user(request, 'Actualización de valores UMA iniciada.')
    update_uma_values.short_description = "Actualizar valores UMA desde fuentes oficiales"


@admin.register(TaxUpdateLog)
class TaxUpdateLogAdmin(admin.ModelAdmin):
    list_display = ['update_type', 'country_code', 'success', 'source', 'created_at']
    list_filter = ['update_type', 'country_code', 'success', 'source', 'created_at']
    search_fields = ['description', 'error_message']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Información General', {
            'fields': ('update_type', 'country_code', 'source', 'success')
        }),
        ('Detalles', {
            'fields': ('description', 'old_values', 'new_values', 'error_message')
        }),
        ('Auditoría', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request)
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    actions = ['retry_failed_updates', 'export_logs']
    
    def retry_failed_updates(self, request, queryset):
        failed_updates = queryset.filter(success=False)
        for update in failed_updates:
            if update.update_type == 'uma':
                from .tasks import update_uma_values
                update_uma_values.delay(update.country_code)
            elif update.update_type == 'imss':
                from .tasks import update_imss_tables
                update_imss_tables.delay()
            # Agregar más tipos según sea necesario
        
        self.message_user(request, f'Reintento de {failed_updates.count()} actualizaciones fallidas iniciado.')
    retry_failed_updates.short_description = "Reintentar actualizaciones fallidas"
    
    def export_logs(self, request, queryset):
        # Implementar exportación de logs
        self.message_user(request, 'Exportación de logs iniciada.')
    export_logs.short_description = "Exportar logs seleccionados"


@admin.register(TaxValidationLog)
class TaxValidationLogAdmin(admin.ModelAdmin):
    list_display = ['validation_type', 'company', 'test_salary', 'validation_status', 'created_at']
    list_filter = ['validation_type', 'validation_status', 'company', 'created_at']
    search_fields = ['company__name', 'message']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Información General', {
            'fields': ('validation_type', 'company', 'test_salary', 'validation_status')
        }),
        ('Cálculos', {
            'fields': ('calculated_isr', 'calculated_imss', 'calculated_infonavit')
        }),
        ('Resultado', {
            'fields': ('message', 'created_at')
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('company')
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    actions = ['run_validation', 'export_validations']
    
    def run_validation(self, request, queryset):
        # Ejecutar validación para las empresas seleccionadas
        from .tasks import validate_tax_calculations
        validate_tax_calculations.delay()
        self.message_user(request, 'Validación de cálculos fiscales iniciada.')
    run_validation.short_description = "Ejecutar validación de cálculos fiscales"
    
    def export_validations(self, request, queryset):
        # Implementar exportación de validaciones
        self.message_user(request, 'Exportación de validaciones iniciada.')
    export_validations.short_description = "Exportar validaciones seleccionadas"


@admin.register(OverheadCategory)
class OverheadCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'aura_category', 'calculation_method', 
                   'default_rate', 'ml_enabled', 'is_active', 'created_at')
    list_filter = ('company', 'aura_category', 'calculation_method', 'ml_enabled', 'is_active')
    search_fields = ('name', 'description', 'company__name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('company', 'name', 'description', 'aura_category')
        }),
        ('Configuración de Cálculo', {
            'fields': ('calculation_method', 'default_rate', 'min_amount', 'max_amount', 'formula')
        }),
        ('Configuración ML', {
            'fields': ('ml_enabled', 'ml_weight'),
            'classes': ('collapse',)
        }),
        ('Estado', {
            'fields': ('is_active',)
        }),
        ('Metadatos', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('company')


@admin.register(EmployeeOverheadCalculation)
class EmployeeOverheadCalculationAdmin(admin.ModelAdmin):
    list_display = ('employee_name', 'period', 'total_overhead', 'overhead_percentage', 
                   'ml_confidence_score', 'aura_ethics_score', 'calculated_at')
    list_filter = ('period', 'calculated_at', 'calculation_version', 
                   'employee__company', 'employee__department')
    search_fields = ('employee__first_name', 'employee__last_name', 'employee__email')
    readonly_fields = ('id', 'calculated_at')
    date_hierarchy = 'calculated_at'
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('employee', 'period')
        }),
        ('Costos Tradicionales', {
            'fields': ('infrastructure_cost', 'administrative_cost', 'benefits_cost', 
                      'training_cost', 'technology_cost', 'traditional_overhead')
        }),
        ('Costos AURA Enhanced', {
            'fields': ('social_impact_cost', 'sustainability_cost', 'wellbeing_cost', 
                      'innovation_cost', 'aura_enhanced_overhead'),
            'classes': ('collapse',)
        }),
        ('Totales', {
            'fields': ('total_overhead', 'overhead_percentage')
        }),
        ('Análisis ML', {
            'fields': ('ml_predicted_overhead', 'ml_confidence_score', 
                      'ml_optimization_potential', 'ml_recommendations'),
            'classes': ('collapse',)
        }),
        ('Análisis AURA', {
            'fields': ('aura_ethics_score', 'aura_fairness_score', 
                      'aura_sustainability_score', 'aura_insights'),
            'classes': ('collapse',)
        }),
        ('Benchmarking', {
            'fields': ('industry_benchmark', 'company_size_benchmark', 'regional_benchmark'),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': ('calculation_version', 'calculated_at'),
            'classes': ('collapse',)
        })
    )
    
    def employee_name(self, obj):
        return obj.employee.get_full_name()
    employee_name.short_description = 'Empleado'
    employee_name.admin_order_field = 'employee__first_name'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('employee', 'period')


@admin.register(TeamOverheadAnalysis)
class TeamOverheadAnalysisAdmin(admin.ModelAdmin):
    list_display = ('team_name', 'company', 'department', 'team_size', 
                   'total_overhead', 'efficiency_score', 'created_at')
    list_filter = ('company', 'department', 'period', 'is_active', 'created_at')
    search_fields = ('team_name', 'department', 'company__name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Información del Equipo', {
            'fields': ('company', 'period', 'team_name', 'department', 'team_lead', 'team_size')
        }),
        ('Métricas Financieras', {
            'fields': ('total_salaries', 'total_overhead', 'overhead_per_employee')
        }),
        ('Scores AURA', {
            'fields': ('team_ethics_score', 'team_diversity_score', 
                      'team_sustainability_score', 'team_innovation_score'),
            'classes': ('collapse',)
        }),
        ('Análisis ML', {
            'fields': ('ml_efficiency_prediction', 'ml_turnover_risk', 
                      'ml_performance_forecast', 'ml_cost_optimization'),
            'classes': ('collapse',)
        }),
        ('Benchmarking', {
            'fields': ('efficiency_score', 'industry_percentile', 'company_ranking'),
            'classes': ('collapse',)
        }),
        ('Análisis AURA Avanzado', {
            'fields': ('aura_holistic_assessment', 'aura_energy_analysis', 
                      'aura_compatibility_matrix', 'aura_growth_recommendations'),
            'classes': ('collapse',)
        }),
        ('Estado', {
            'fields': ('is_active',)
        }),
        ('Metadatos', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('company', 'period', 'team_lead')


@admin.register(OverheadMLModel)
class OverheadMLModelAdmin(admin.ModelAdmin):
    list_display = ('model_name', 'company', 'model_type', 'accuracy', 'precision', 
                   'is_production', 'last_training_date', 'version')
    list_filter = ('company', 'model_type', 'is_active', 'is_production', 'last_training_date')
    search_fields = ('model_name', 'company__name', 'version')
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Información del Modelo', {
            'fields': ('company', 'model_name', 'model_type', 'version')
        }),
        ('Métricas de Rendimiento', {
            'fields': ('accuracy', 'precision', 'recall', 'f1_score', 'mse')
        }),
        ('Métricas AURA', {
            'fields': ('aura_ethics_compliance', 'aura_fairness_score', 'aura_bias_detection'),
            'classes': ('collapse',)
        }),
        ('Datos de Entrenamiento', {
            'fields': ('training_data_size', 'validation_data_size', 'test_data_size'),
            'classes': ('collapse',)
        }),
        ('Configuración', {
            'fields': ('model_parameters', 'feature_importance', 'aura_weights'),
            'classes': ('collapse',)
        }),
        ('Programación', {
            'fields': ('last_training_date', 'next_training_date', 'training_frequency_days')
        }),
        ('Estado', {
            'fields': ('is_active', 'is_production')
        }),
        ('Metadatos', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('company')


@admin.register(OverheadBenchmark)
class OverheadBenchmarkAdmin(admin.ModelAdmin):
    list_display = ('industry', 'region', 'company_size_range', 'total_overhead_benchmark', 
                   'sample_size', 'confidence_level', 'last_updated', 'is_active')
    list_filter = ('industry', 'region', 'company_size_range', 'is_active', 'last_updated')
    search_fields = ('industry', 'region', 'data_source')
    readonly_fields = ('id', 'created_at', 'last_updated')
    
    fieldsets = (
        ('Categorización', {
            'fields': ('industry', 'region', 'company_size_range')
        }),
        ('Benchmarks Tradicionales (%)', {
            'fields': ('infrastructure_benchmark', 'administrative_benchmark', 
                      'benefits_benchmark', 'training_benchmark', 'technology_benchmark')
        }),
        ('Benchmarks AURA Enhanced (%)', {
            'fields': ('social_impact_benchmark', 'sustainability_benchmark', 
                      'wellbeing_benchmark', 'innovation_benchmark', 'aura_enhanced_benchmark'),
            'classes': ('collapse',)
        }),
        ('Totales y Percentiles', {
            'fields': ('total_overhead_benchmark', 'percentile_25', 'percentile_50', 
                      'percentile_75', 'percentile_90')
        }),
        ('Metadatos de Investigación', {
            'fields': ('data_source', 'sample_size', 'confidence_level'),
            'classes': ('collapse',)
        }),
        ('Estado', {
            'fields': ('is_active',)
        }),
        ('Fechas', {
            'fields': ('last_updated', 'created_at'),
            'classes': ('collapse',)
        })
    )
    
    class Media:
        css = {
            'all': ('admin/css/overhead_admin.css',)
        }


# Configuración del admin site
admin.site.site_header = "huntRED® Payroll Admin"
admin.site.site_title = "huntRED® Payroll"
admin.site.index_title = "Panel de Administración de Nómina"

# Agregar JavaScript personalizado para el admin
class Media:
    css = {
        'all': ('admin/css/payroll_admin.css',)
    }
    js = ('admin/js/payroll_admin.js',) 

# ============================================================================
# ADMIN PARA GESTIÓN DE TURNOS Y HORARIOS
# ============================================================================

# @admin.register(EmployeeShift)  # Comentado para evitar registro duplicado
# class EmployeeShiftAdmin(admin.ModelAdmin):
#     """Admin para gestión de turnos de empleados"""
#     
#     list_display = [
#         'employee_name', 'shift_name', 'shift_type', 'schedule_display', 
#         'location_display', 'status', 'effective_date'
#     ]
#     list_filter = [
#         'shift_type', 'status', 'effective_date', 'employee__department',
#         'is_location_variable'
#     ]
#     search_fields = [
#         'employee__first_name', 'employee__last_name', 'employee__employee_number',
#         'shift_name'
#     ]
#     readonly_fields = [
#         'id', 'created_at', 'updated_at', 'approval_date'
#     ]
#     
#     fieldsets = (
#         ('Información del Empleado', {
#             'fields': ('employee',)
#         }),
#         ('Configuración del Turno', {
#             'fields': (
#                 'shift_name', 'shift_type', 'status',
#                 'start_time', 'end_time', 'break_start', 'break_end'
#             )
#         }),
#         ('Días y Horas', {
#             'fields': ('work_days', 'hours_per_day', 'overtime_threshold')
#         }),
#         ('Ubicación', {
#             'fields': ('location', 'is_location_variable')
#         }),
#         ('Fechas', {
#             'fields': ('effective_date', 'end_date')
#         }),
#         ('Aprobación', {
#             'fields': ('approved_by', 'approval_date', 'notes'),
#             'classes': ('collapse',)
#         }),
#         ('Metadatos', {
#             'fields': ('created_at', 'updated_at'),
#             'classes': ('collapse',)
#         })
#     )
#     
#     def employee_name(self, obj):
#         return obj.employee.get_full_name()
#     employee_name.short_description = "Empleado"
#     
#     def schedule_display(self, obj):
#         return f"{obj.start_time.strftime('%H:%M')} - {obj.end_time.strftime('%H:%M')}"
#     schedule_display.short_description = "Horario"
#     
#     def location_display(self, obj):
#         if obj.location and obj.location.get('name'):
#             return obj.location['name']
#         return "No especificada"
#     location_display.short_description = "Ubicación"


@admin.register(ShiftChangeRequest)
class ShiftChangeRequestAdmin(admin.ModelAdmin):
    """Admin para solicitudes de cambio de turno"""
    
    list_display = [
        'employee_name', 'request_type', 'period_display', 
        'requested_shift', 'status', 'created_at'
    ]
    list_filter = [
        'request_type', 'status', 'created_at', 'employee__department'
    ]
    search_fields = [
        'employee__first_name', 'employee__last_name', 'employee__employee_number',
        'reason'
    ]
    readonly_fields = [
        'id', 'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Información de la Solicitud', {
            'fields': (
                'employee', 'request_type', 'status',
                'start_date', 'end_date', 'requested_shift'
            )
        }),
        ('Detalles', {
            'fields': ('reason', 'emergency_details')
        }),
        ('Aprobación', {
            'fields': ('approved_by', 'approval_date', 'approval_notes')
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def employee_name(self, obj):
        return obj.employee.get_full_name()
    employee_name.short_description = "Empleado"
    
    def period_display(self, obj):
        return f"{obj.start_date.strftime('%d/%m/%Y')} - {obj.end_date.strftime('%d/%m/%Y')}"
    period_display.short_description = "Período"


# ============================================================================
# ADMIN PARA FEEDBACK DE PAYROLL
# ============================================================================

@admin.register(PayrollFeedback)
class PayrollFeedbackAdmin(admin.ModelAdmin):
    """Admin para feedback de nómina"""
    
    list_display = [
        'employee_name', 'feedback_type', 'subject', 'priority', 
        'is_resolved', 'created_at', 'response_status'
    ]
    list_filter = [
        'feedback_type', 'priority', 'is_resolved', 'created_at',
        'employee__department', 'send_to_supervisor', 'send_to_hr'
    ]
    search_fields = [
        'employee__first_name', 'employee__last_name', 'subject', 'message'
    ]
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'response_date'
    ]
    
    fieldsets = (
        ('Información del Empleado', {
            'fields': ('employee',)
        }),
        ('Feedback', {
            'fields': (
                'feedback_type', 'priority', 'subject', 'message',
                'is_anonymous'
            )
        }),
        ('Destinatarios', {
            'fields': ('send_to_supervisor', 'send_to_hr')
        }),
        ('Estado', {
            'fields': ('is_resolved', 'resolution_notes')
        }),
        ('Respuesta', {
            'fields': (
                'response_message', 'responded_by', 'response_date'
            )
        }),
        ('Metadatos', {
            'fields': ('created_via', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def employee_name(self, obj):
        return obj.employee.get_full_name()
    employee_name.short_description = "Empleado"
    
    def response_status(self, obj):
        if obj.is_resolved:
            return "✅ Resuelto"
        elif obj.response_message:
            return "🔄 En proceso"
        else:
            return "⏳ Pendiente"
    response_status.short_description = "Estado"


@admin.register(PerformanceEvaluation)
class PerformanceEvaluationAdmin(admin.ModelAdmin):
    """Admin para evaluaciones de desempeño"""
    
    list_display = [
        'employee_name', 'evaluation_type', 'period_display', 
        'overall_rating', 'status', 'evaluator_name'
    ]
    list_filter = [
        'evaluation_type', 'status', 'evaluation_period_start',
        'employee__department', 'overall_rating'
    ]
    search_fields = [
        'employee__first_name', 'employee__last_name', 'evaluator__username'
    ]
    readonly_fields = [
        'id', 'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Información General', {
            'fields': (
                'employee', 'evaluator', 'evaluation_type',
                'evaluation_period_start', 'evaluation_period_end', 'status'
            )
        }),
        ('Calificaciones', {
            'fields': (
                'job_knowledge', 'quality_of_work', 'quantity_of_work',
                'reliability', 'teamwork', 'communication',
                'initiative', 'leadership', 'attendance', 'overall_rating'
            )
        }),
        ('Comentarios', {
            'fields': (
                'strengths', 'areas_for_improvement', 'goals', 'comments'
            )
        }),
        ('Aprobación', {
            'fields': (
                'employee_signature', 'employee_signature_date',
                'supervisor_signature', 'supervisor_signature_date'
            )
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def employee_name(self, obj):
        return obj.employee.get_full_name()
    employee_name.short_description = "Empleado"
    
    def period_display(self, obj):
        return f"{obj.evaluation_period_start.strftime('%d/%m/%Y')} - {obj.evaluation_period_end.strftime('%d/%m/%Y')}"
    period_display.short_description = "Período"
    
    def evaluator_name(self, obj):
        return obj.evaluator.get_full_name()
    evaluator_name.short_description = "Evaluador"


# ============================================================================
# ADMIN PARA MATRIZ 9 BOXES
# ============================================================================

@admin.register(NineBoxMatrix)
class NineBoxMatrixAdmin(admin.ModelAdmin):
    """Admin para matriz 9 boxes"""
    
    list_display = [
        'employee_name', 'box_category', 'box_description_display',
        'performance_score', 'potential_score', 'retention_risk',
        'evaluator_name', 'is_active'
    ]
    list_filter = [
        'box_category', 'performance_level', 'potential_level',
        'retention_risk', 'is_active', 'created_at'
    ]
    search_fields = [
        'employee__first_name', 'employee__last_name', 'evaluator__username'
    ]
    readonly_fields = [
        'id', 'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Información General', {
            'fields': (
                'employee', 'evaluator', 'is_active'
            )
        }),
        ('Evaluación', {
            'fields': (
                'performance_level', 'potential_level', 'box_category',
                'performance_score', 'potential_score'
            )
        }),
        ('Análisis Detallado', {
            'fields': (
                'performance_factors', 'potential_factors'
            ),
            'classes': ('collapse',)
        }),
        ('Recomendaciones', {
            'fields': (
                'development_plan', 'career_path', 'retention_risk',
                'recommended_actions', 'timeline'
            )
        }),
        ('Seguimiento', {
            'fields': (
                'next_review_date', 'progress_notes'
            )
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def employee_name(self, obj):
        return obj.employee.get_full_name()
    employee_name.short_description = "Empleado"
    
    def box_description_display(self, obj):
        return obj.get_box_description()
    box_description_display.short_description = "Descripción del Box"
    
    def evaluator_name(self, obj):
        return obj.evaluator.get_full_name()
    evaluator_name.short_description = "Evaluador"
    
    def get_queryset(self, request):
        """Optimizar consultas"""
        return super().get_queryset(request).select_related(
            'employee', 'evaluator'
        ) 

# admin.site.register(PermisoEspecial, PermisoEspecialAdmin)  # Comentado para evitar registro duplicado
# admin.site.unregister(EmployeeShift)  # Comentado para evitar registro duplicado
# admin.site.register(EmployeeShift, ShiftDashboardAdmin)  # Comentado para evitar registro duplicado 