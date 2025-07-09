# app/payroll/services/whatsapp_reports_service.py
"""
Reportes por WhatsApp para Empleado y Supervisor
(no incluye overhead, sólo asistencia y vacaciones)
"""
import logging
from typing import Dict
from django.utils import timezone
from django.db.models import Sum, Count
from app.payroll.models import (
    PayrollEmployee, AttendanceRecord, EmployeeRequest
)

logger = logging.getLogger(__name__)


class WhatsAppReportsService:
    # ─────────────────── Empleado
    def get_employee_report(self, employee: PayrollEmployee) -> Dict[str, str]:
        today = timezone.now().date()
        first = today.replace(day=1)
        rec = AttendanceRecord.objects.filter(employee=employee,
                                              date__range=[first, today])
        total_days = (today - first).days + 1
        present = rec.filter(status='present').count()
        absent = rec.filter(status='absent').count()
        late = rec.filter(status='late').count()
        rate = (present / total_days) * 100 if total_days else 0

        vac = EmployeeRequest.objects.filter(
            employee=employee, status='approved',
            request_type='vacation', start_date__year=today.year
        ).aggregate(days=Sum('days_requested'))['days'] or 0

        msg = (
            f"📊 *Reporte Personal*\n"
            f"Presente: {present}/{total_days}\n"
            f"Ausente: {absent}   Retardos: {late}\n"
            f"Puntualidad: {rate:.1f}%\n"
            f"Vacaciones tomadas este año: {vac}\n"
            f"_Generado {timezone.now():%d/%m/%Y %H:%M}_"
        )
        return {"type": "text", "text": msg}

    # ─────────────────── Supervisor
    def get_team_report(self, supervisor: PayrollEmployee) -> Dict[str, str]:
        team = PayrollEmployee.objects.filter(supervisor=supervisor, is_active=True)
        today = timezone.now().date()
        first = today.replace(day=1)
        rec = AttendanceRecord.objects.filter(employee__in=team, date__range=[first, today])
        present = rec.filter(status='present').count()
        absent = rec.filter(status='absent').count()
        rate = (present / (len(team) * ((today - first).days + 1))) * 100 if team else 0
        vac = EmployeeRequest.objects.filter(
            employee__in=team, status='approved',
            request_type='vacation', start_date__year=today.year
        ).aggregate(days=Sum('days_requested'))['days'] or 0

        msg = (
            f"📊 *Reporte Equipo*\n"
            f"Colaboradores: {len(team)}\n"
            f"Presentes hoy: {present}  Ausentes: {absent}\n"
            f"Asistencia mes: {rate:.1f}%\n"
            f"Vacaciones año: {vac}\n"
            f"_Generado {timezone.now():%d/%m/%Y %H:%M}_"
        )
        return {"type": "text", "text": msg}

    # ─────────────────── Daily Pulse
    def get_daily_pulse_supervisor(self, supervisor: PayrollEmployee) -> Dict[str, str]:
        today = timezone.now().date()
        team = PayrollEmployee.objects.filter(supervisor=supervisor, is_active=True)
        rec = AttendanceRecord.objects.filter(employee__in=team, date=today)
        msg = (
            f"📌 *Daily Pulse {today:%d/%m}*\n"
            f"Presentes: {rec.filter(status='present').count()}\n"
            f"Ausentes : {rec.filter(status='absent').count()}\n"
            f"Anomalías ML: {rec.filter(ml_anomaly_detected=True).count()}"
        )
        return {"type": "text", "text": msg}

    def get_daily_pulse_rh(self, company) -> Dict[str, str]:
        today = timezone.now().date()
        rec = AttendanceRecord.objects.filter(employee__company=company, date=today)
        pend = EmployeeRequest.objects.filter(employee__company=company, status='pending').count()
        msg = (
            f"📌 *Daily Pulse RH {company.name}*\n"
            f"Presentes: {rec.filter(status='present').count()}  "
            f"Ausentes: {rec.filter(status='absent').count()}\n"
            f"Anomalías ML: {rec.filter(ml_anomaly_detected=True).count()}\n"
            f"Solicitudes pendientes: {pend}"
        )
        return {"type": "text", "text": msg}