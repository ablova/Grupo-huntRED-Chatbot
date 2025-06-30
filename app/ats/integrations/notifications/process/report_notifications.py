import asyncio
from app.ats.integrations.notifications.recipients.manager import ManagerNotifier
from app.models import Person
from django.utils import timezone

async def send_weekly_reports():
    # Obtener super admin y consultores clave
    super_admins = Person.objects.filter(is_superuser=True)
    consultants = Person.objects.filter(groups__name__in=["Consultor Clave"])
    recipients = list(super_admins) + list(consultants)
    # Datos de ejemplo, reemplazar por lógica real
    report_data = {
        'pagos_recibidos': 10,
        'pagos_pendientes': 2,
        'total_monto': 150000,
        'semana': timezone.now().isocalendar()[1],
        'fecha': timezone.now().strftime('%Y-%m-%d')
    }
    for admin in recipients:
        notifier = ManagerNotifier(admin)
        await notifier.send_weekly_report(report_data, recipients=[admin])

# Para usar con Celery o como tarea asíncrona programada 