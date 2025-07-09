# app/payroll/tasks/report_tasks.py

from celery import shared_task
from django.contrib.auth import get_user_model
import logging
from app.payroll.models import PayrollCompany
from app.payroll.services.rh_email_reports_service import RHEmailReportsService
from app.payroll.services.whatsapp_reports_service import WhatsAppReportsService

logger = logging.getLogger(__name__)


@shared_task
def send_weekly_rh_summary(company_id):
    company = PayrollCompany.objects.get(id=company_id)
    emails = [u.email for u in get_user_model().objects.filter(company=company, is_staff=True)]
    RHEmailReportsService(company).send_weekly_summary(emails)


@shared_task
def send_daily_pulse_whatsapp(company_id):
    company = PayrollCompany.objects.get(id=company_id)
    wa = WhatsAppReportsService()
    # Supervisores top-level
    supervisors = company.employees.filter(supervisor__isnull=True)
    for sup in supervisors:
        wa.get_daily_pulse_supervisor(sup)  # aquí iría la llamada a API-WhatsApp
    wa.get_daily_pulse_rh(company)