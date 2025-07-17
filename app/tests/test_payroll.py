import pytest
from django.test import TestCase
from django.utils import timezone
from app.payroll.models import EmployeeShift, PermisoEspecial
from app.payroll.services.shift_management_service import ShiftManagementService
from app.payroll.services.permiso_especial_service import PermisoEspecialService
from app.ats.integrations.services import MessageService
from app.models import BusinessUnit, Employee

class TestPayrollModels(TestCase):
    def setUp(self):
        self.business_unit = BusinessUnit.objects.create(name="BU Payroll", description="Payroll Unit")
        self.employee = Employee.objects.create(
            first_name="Juan", last_name="Pérez", employee_number="E001", business_unit=self.business_unit
        )

    def test_create_employee_shift(self):
        shift = EmployeeShift.objects.create(
            employee=self.employee,
            shift_name="Turno Mañana",
            shift_type="morning",
            start_time=timezone.now(),
            end_time=timezone.now(),
            status="active"
        )
        assert shift.id is not None
        assert shift.employee == self.employee

    def test_create_permiso_especial(self):
        permiso = PermisoEspecial.objects.create(
            employee=self.employee,
            permiso_type="maternity",
            status="pending",
            start_date=timezone.now(),
            end_date=timezone.now() + timezone.timedelta(days=30),
            reason="Licencia por maternidad"
        )
        assert permiso.id is not None
        assert permiso.employee == self.employee

class TestPayrollServices(TestCase):
    def setUp(self):
        self.business_unit = BusinessUnit.objects.create(name="BU Payroll", description="Payroll Unit")
        self.employee = Employee.objects.create(
            first_name="Ana", last_name="García", employee_number="E002", business_unit=self.business_unit
        )
        self.shift_service = ShiftManagementService()
        self.permiso_service = PermisoEspecialService()

    def test_shift_creation_service(self):
        shift = self.shift_service.create_shift(
            employee=self.employee,
            shift_name="Turno Tarde",
            shift_type="afternoon",
            start_time=timezone.now(),
            end_time=timezone.now() + timezone.timedelta(hours=8)
        )
        assert shift.id is not None
        assert shift.shift_type == "afternoon"

    def test_permiso_especial_service(self):
        permiso = self.permiso_service.solicitar_permiso(
            employee=self.employee,
            permiso_type="home_office",
            start_date=timezone.now(),
            end_date=timezone.now() + timezone.timedelta(days=2),
            reason="Trabajo remoto"
        )
        assert permiso.id is not None
        assert permiso.permiso_type == "home_office"

class TestPayrollCommunication(TestCase):
    def setUp(self):
        self.business_unit = BusinessUnit.objects.create(name="BU Payroll", description="Payroll Unit")
        self.employee = Employee.objects.create(
            first_name="Luis", last_name="Martínez", employee_number="E003", business_unit=self.business_unit
        )
        self.message_service = MessageService(self.business_unit)

    def test_send_shift_notification(self):
        # Simula el envío de notificación de turno por WhatsApp
        result = self.message_service.send_message(
            platform="whatsapp",
            user_id=str(self.employee.id),
            message="Tu turno ha sido actualizado."
        )
        assert result is True

    def test_send_permiso_notification(self):
        # Simula el envío de notificación de permiso especial
        result = self.message_service.send_message(
            platform="whatsapp",
            user_id=str(self.employee.id),
            message="Tu permiso especial ha sido registrado."
        )
        assert result is True

# Puedes añadir más tests para evaluaciones, dashboard y flujos avanzados según se requiera. 