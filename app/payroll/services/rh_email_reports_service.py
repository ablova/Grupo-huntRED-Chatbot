#app/payroll/services/rh_email_reports_service.py

"""
Servicio de e-mail semanal para RH / Directivos
"""
import logging
from typing import List
from django.conf import settings
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.utils import timezone

from app.payroll.models import PayrollCompany, AttendanceRecord, EmployeeRequest

logger = logging.getLogger(__name__)


class RHEmailReportsService:
    def __init__(self, company: PayrollCompany):
        self.company = company

    # contexto
    def context(self):
        today = timezone.now().date()
        week_start = today - timezone.timedelta(days=today.weekday())
        rec = AttendanceRecord.objects.filter(employee__company=self.company,
                                              date__range=[week_start, today])
        return {
            "company": self.company,
            "week_start": week_start,
            "week_end": today,
            "present": rec.filter(status='present').count(),
            "absent": rec.filter(status='absent').count(),
            "late": rec.filter(status='late').count(),
            "vacations": EmployeeRequest.objects.filter(
                employee__company=self.company, status='approved',
                request_type='vacation', start_date__range=[week_start, today]
            ).count(),
            "pending_requests":
                EmployeeRequest.objects.filter(employee__company=self.company,
                                               status='pending').count(),
            "generated": timezone.now()
        }

    # envío
    def send_weekly_summary(self, to_emails: List[str]):
        ctx = self.context()
        html = render_to_string("emails/rh_weekly_summary.html", ctx)
        text = render_to_string("emails/rh_weekly_summary.txt", ctx)
        msg = EmailMultiAlternatives(
            subject=f"Resumen semanal RH – {self.company.name}",
            body=text,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=to_emails
        )
        msg.attach_alternative(html, "text/html")
        msg.send()
        logger.info("Resumen RH enviado a %s", to_emails)