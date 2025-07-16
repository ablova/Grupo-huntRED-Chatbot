from django.contrib import admin
from django.urls import path
from django.template.response import TemplateResponse
from app.payroll.models import EmployeeShift, PayrollEmployee
from django.utils.html import format_html

class ShiftDashboardAdmin(admin.ModelAdmin):
    change_list_template = "admin/shift_dashboard.html"
    model = EmployeeShift

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('dashboard/', self.admin_site.admin_view(self.dashboard_view), name='shift_dashboard'),
        ]
        return custom_urls + urls

    def dashboard_view(self, request):
        # Obtener turnos y empleados para la semana
        empleados = PayrollEmployee.objects.all()
        turnos = EmployeeShift.objects.all()
        context = dict(
            self.admin_site.each_context(request),
            empleados=empleados,
            turnos=turnos,
        )
        return TemplateResponse(request, "admin/shift_dashboard.html", context)

admin.site.register(EmployeeShift, ShiftDashboardAdmin) 