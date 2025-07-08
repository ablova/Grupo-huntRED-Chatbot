from rest_framework import serializers
from django.contrib.auth.models import User
from app.payroll.models import (
    Company, Employee, PayrollRecord, AttendanceRecord, Benefit,
    PayrollPeriod, PayrollCalculation, TaxTable, AuthorityIntegration
)


class UserSerializer(serializers.ModelSerializer):
    """Serializer para usuarios."""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class CompanySerializer(serializers.ModelSerializer):
    """Serializer para empresas."""
    class Meta:
        model = Company
        fields = [
            'id', 'name', 'tax_id', 'country', 'address', 'phone', 'email',
            'website', 'industry', 'size', 'founded_date', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class EmployeeSerializer(serializers.ModelSerializer):
    """Serializer para empleados."""
    company_name = serializers.CharField(source='company.name', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Employee
        fields = [
            'id', 'company', 'company_name', 'employee_id', 'first_name',
            'last_name', 'full_name', 'email', 'phone', 'position',
            'department', 'department_name', 'hire_date', 'salary',
            'currency', 'country', 'status', 'is_active', 'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_full_name(self, obj):
        """Obtiene nombre completo del empleado."""
        return f"{obj.first_name} {obj.last_name}".strip()
    
    def validate_employee_id(self, value):
        """Valida que el ID de empleado sea único en la empresa."""
        company = self.initial_data.get('company')
        if company and Employee.objects.filter(
            company=company, employee_id=value
        ).exists():
            raise serializers.ValidationError(
                "Ya existe un empleado con este ID en la empresa."
            )
        return value


class PayrollRecordSerializer(serializers.ModelSerializer):
    """Serializer para registros de nómina."""
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    company_name = serializers.CharField(source='employee.company.name', read_only=True)
    
    class Meta:
        model = PayrollRecord
        fields = [
            'id', 'employee', 'employee_name', 'company_name', 'period_start',
            'period_end', 'gross_salary', 'net_salary', 'total_deductions',
            'total_bonuses', 'total_benefits', 'total_taxes', 'total_contributions',
            'status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class AttendanceRecordSerializer(serializers.ModelSerializer):
    """Serializer para registros de asistencia."""
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    
    class Meta:
        model = AttendanceRecord
        fields = [
            'id', 'employee', 'employee_name', 'date', 'check_in_time',
            'check_out_time', 'status', 'location', 'notes', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def validate(self, data):
        """Valida que no haya registros duplicados para el mismo empleado y fecha."""
        employee = data.get('employee')
        date = data.get('date')
        
        if employee and date:
            existing_record = AttendanceRecord.objects.filter(
                employee=employee, date=date
            ).first()
            
            if existing_record and self.instance != existing_record:
                raise serializers.ValidationError(
                    "Ya existe un registro de asistencia para este empleado en esta fecha."
                )
        
        return data


class BenefitSerializer(serializers.ModelSerializer):
    """Serializer para beneficios."""
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    
    class Meta:
        model = Benefit
        fields = [
            'id', 'employee', 'employee_name', 'name', 'benefit_type',
            'description', 'monthly_value', 'is_active', 'start_date',
            'end_date', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class PayrollPeriodSerializer(serializers.ModelSerializer):
    """Serializer para períodos de nómina."""
    company_name = serializers.CharField(source='company.name', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.username', read_only=True)
    
    class Meta:
        model = PayrollPeriod
        fields = [
            'id', 'company', 'company_name', 'name', 'start_date', 'end_date',
            'status', 'total_employees', 'total_gross', 'total_net',
            'approved_by', 'approved_by_name', 'approved_at', 'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class PayrollCalculationSerializer(serializers.ModelSerializer):
    """Serializer para cálculos de nómina."""
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    
    class Meta:
        model = PayrollCalculation
        fields = [
            'id', 'employee', 'employee_name', 'period', 'gross_salary',
            'net_salary', 'deductions', 'bonuses', 'taxes', 'contributions',
            'benefits', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class TaxTableSerializer(serializers.ModelSerializer):
    """Serializer para tablas fiscales."""
    class Meta:
        model = TaxTable
        fields = [
            'id', 'country', 'year', 'table_type', 'data', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class AuthorityIntegrationSerializer(serializers.ModelSerializer):
    """Serializer para integración con autoridades."""
    class Meta:
        model = AuthorityIntegration
        fields = [
            'id', 'company', 'authority_type', 'authority_name', 'api_key',
            'api_secret', 'endpoint_url', 'is_active', 'last_sync',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# Serializers para reportes y analytics
class PayrollSummarySerializer(serializers.Serializer):
    """Serializer para resumen de nómina."""
    total_employees = serializers.IntegerField()
    total_gross = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_net = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_deductions = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_bonuses = serializers.DecimalField(max_digits=15, decimal_places=2)
    average_salary = serializers.DecimalField(max_digits=15, decimal_places=2)


class AttendanceSummarySerializer(serializers.Serializer):
    """Serializer para resumen de asistencia."""
    total_records = serializers.IntegerField()
    present_days = serializers.IntegerField()
    absent_days = serializers.IntegerField()
    late_days = serializers.IntegerField()
    attendance_rate = serializers.FloatField()


class EmployeeDashboardSerializer(serializers.Serializer):
    """Serializer para dashboard de empleados."""
    employee = EmployeeSerializer()
    attendance_summary = AttendanceSummarySerializer()
    payslip_summary = serializers.DictField()
    benefits_summary = serializers.DictField()
    performance_metrics = serializers.DictField()


class PayrollAnalyticsSerializer(serializers.Serializer):
    """Serializer para analytics de nómina."""
    monthly_trend = serializers.ListField()
    total_employees = serializers.IntegerField()
    average_salary = serializers.DecimalField(max_digits=15, decimal_places=2)
    salary_distribution = serializers.DictField()


class AttendanceAnalyticsSerializer(serializers.Serializer):
    """Serializer para analytics de asistencia."""
    summary = AttendanceSummarySerializer()
    attendance_rate = serializers.FloatField()
    total_employees = serializers.IntegerField()
    daily_trend = serializers.ListField()


class BenefitsAnalyticsSerializer(serializers.Serializer):
    """Serializer para analytics de beneficios."""
    total_benefits = serializers.IntegerField()
    total_value = serializers.DecimalField(max_digits=15, decimal_places=2)
    average_per_employee = serializers.DecimalField(max_digits=15, decimal_places=2)
    utilization_rate = serializers.FloatField()


# Serializers para webhooks
class WebhookEventSerializer(serializers.Serializer):
    """Serializer para eventos de webhooks."""
    event_type = serializers.CharField(max_length=100)
    event_data = serializers.DictField()
    timestamp = serializers.DateTimeField()
    source = serializers.CharField(max_length=100)


class WebhookSubscriptionSerializer(serializers.Serializer):
    """Serializer para suscripciones de webhooks."""
    url = serializers.URLField()
    event_types = serializers.ListField(child=serializers.CharField())
    is_active = serializers.BooleanField(default=True)
    secret_key = serializers.CharField(max_length=255, required=False)


# Serializers para integraciones
class WhatsAppMessageSerializer(serializers.Serializer):
    """Serializer para mensajes de WhatsApp."""
    employee_id = serializers.UUIDField()
    message = serializers.CharField()
    message_type = serializers.ChoiceField(
        choices=['text', 'document', 'image', 'template'],
        default='text'
    )
    template_data = serializers.DictField(required=False)


class BankingTransferSerializer(serializers.Serializer):
    """Serializer para transferencias bancarias."""
    employee_id = serializers.UUIDField()
    amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    currency = serializers.CharField(max_length=3, default='MXN')
    description = serializers.CharField(max_length=255)
    reference = serializers.CharField(max_length=100, required=False)


class AuthorityReportSerializer(serializers.Serializer):
    """Serializer para reportes a autoridades."""
    report_type = serializers.CharField(max_length=100)
    report_data = serializers.DictField()
    authority = serializers.CharField(max_length=100)
    period_start = serializers.DateField()
    period_end = serializers.DateField()


# Serializers para acciones rápidas
class QuickActionSerializer(serializers.Serializer):
    """Serializer para acciones rápidas."""
    action_type = serializers.CharField(max_length=100)
    employee_id = serializers.UUIDField()
    data = serializers.DictField(required=False)


class PayslipRequestSerializer(serializers.Serializer):
    """Serializer para solicitudes de recibo."""
    employee_id = serializers.UUIDField()
    period = serializers.CharField(max_length=7)  # YYYY-MM
    format = serializers.ChoiceField(
        choices=['pdf', 'email', 'whatsapp'],
        default='pdf'
    )


class AttendanceReportSerializer(serializers.Serializer):
    """Serializer para reportes de asistencia."""
    employee_id = serializers.UUIDField()
    date = serializers.DateField()
    status = serializers.ChoiceField(
        choices=['present', 'absent', 'late', 'vacation', 'sick']
    )
    location = serializers.CharField(max_length=255, required=False)
    notes = serializers.CharField(max_length=500, required=False)


class BenefitRequestSerializer(serializers.Serializer):
    """Serializer para solicitudes de beneficios."""
    employee_id = serializers.UUIDField()
    benefit_type = serializers.CharField(max_length=100)
    description = serializers.CharField(max_length=500)
    requested_value = serializers.DecimalField(
        max_digits=15, decimal_places=2, required=False
    )


# Serializers para filtros y búsquedas
class EmployeeFilterSerializer(serializers.Serializer):
    """Serializer para filtros de empleados."""
    company_id = serializers.UUIDField(required=False)
    department_id = serializers.UUIDField(required=False)
    status = serializers.CharField(max_length=20, required=False)
    position = serializers.CharField(max_length=100, required=False)
    hire_date_from = serializers.DateField(required=False)
    hire_date_to = serializers.DateField(required=False)
    salary_min = serializers.DecimalField(
        max_digits=15, decimal_places=2, required=False
    )
    salary_max = serializers.DecimalField(
        max_digits=15, decimal_places=2, required=False
    )


class PayrollFilterSerializer(serializers.Serializer):
    """Serializer para filtros de nómina."""
    company_id = serializers.UUIDField(required=False)
    period_start = serializers.DateField(required=False)
    period_end = serializers.DateField(required=False)
    status = serializers.CharField(max_length=20, required=False)
    employee_id = serializers.UUIDField(required=False)


class AttendanceFilterSerializer(serializers.Serializer):
    """Serializer para filtros de asistencia."""
    company_id = serializers.UUIDField(required=False)
    employee_id = serializers.UUIDField(required=False)
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)
    status = serializers.CharField(max_length=20, required=False)
    department_id = serializers.UUIDField(required=False)


# Serializers para exportación
class ExportSerializer(serializers.Serializer):
    """Serializer para exportación de datos."""
    format = serializers.ChoiceField(
        choices=['csv', 'xlsx', 'pdf', 'json'],
        default='xlsx'
    )
    filters = serializers.DictField(required=False)
    include_headers = serializers.BooleanField(default=True)
    date_format = serializers.CharField(max_length=20, default='YYYY-MM-DD')


# Serializers para notificaciones
class NotificationSerializer(serializers.Serializer):
    """Serializer para notificaciones."""
    recipient_id = serializers.UUIDField()
    notification_type = serializers.CharField(max_length=100)
    title = serializers.CharField(max_length=255)
    message = serializers.CharField()
    data = serializers.DictField(required=False)
    priority = serializers.ChoiceField(
        choices=['low', 'medium', 'high', 'urgent'],
        default='medium'
    )


# Serializers para auditoría
class AuditLogSerializer(serializers.Serializer):
    """Serializer para logs de auditoría."""
    user_id = serializers.IntegerField()
    action = serializers.CharField(max_length=100)
    model = serializers.CharField(max_length=100)
    object_id = serializers.CharField(max_length=100)
    changes = serializers.DictField()
    timestamp = serializers.DateTimeField()
    ip_address = serializers.IPAddressField(required=False)
    user_agent = serializers.CharField(max_length=500, required=False) 