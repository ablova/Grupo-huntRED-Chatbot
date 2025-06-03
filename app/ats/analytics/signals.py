from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from app.models import Opportunity, Contract, Vacancy
from app.ats.analytics.reports import AnalyticsEngine
from app.ats.utils.notification_handler import NotificationHandler

@receiver(post_save, sender=Opportunity)
def opportunity_saved(sender, instance, created, **kwargs):
    """
    Maneja el evento de creación o actualización de una oportunidad.
    
    Args:
        sender: Modelo que envía la señal
        instance: Instancia del modelo
        created: Booleano que indica si es una nueva instancia
    """
    if created:
        # Notificar nueva oportunidad
        notification_handler = NotificationHandler()
        message = f"Nueva oportunidad scrapeada: {instance.title}"
        notification_handler.send_notification(
            recipient='pablo@huntred.com',
            message=message,
            subject='Nueva Oportunidad'
        )
        
@receiver(post_save, sender=Contract)
def contract_saved(sender, instance, created, **kwargs):
    """
    Maneja el evento de creación o actualización de un contrato.
    
    Args:
        sender: Modelo que envía la señal
        instance: Instancia del modelo
        created: Booleano que indica si es una nueva instancia
    """
    if created:
        # Actualizar métricas de conversión
        analytics = AnalyticsEngine()
        analytics.generate_opportunity_conversion_report()
        
@receiver(post_delete, sender=Vacancy)
def vacancy_deleted(sender, instance, **kwargs):
    """
    Maneja el evento de eliminación de una vacante.
    
    Args:
        sender: Modelo que envía la señal
        instance: Instancia del modelo
    """
    # Actualizar métricas relacionadas
    analytics = AnalyticsEngine()
    analytics.generate_industry_trends()
