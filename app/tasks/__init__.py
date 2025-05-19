"""
Módulo centralizado de tareas asíncronas para Grupo huntRED.
Este archivo registra todas las tareas disponibles en el sistema.
Sigue la estructura modular de Django y las reglas globales de Grupo huntRED.
"""

# Importar tareas básicas y utilidades
from app.tasks.base import with_retry, add

# Importar tareas de cada dominio para registrarlas en Celery
from app.tasks.chatbot import *
from app.tasks.ml import *
from app.tasks.payments import *
from app.tasks.onboarding import *
from app.tasks.notifications import *
from app.tasks.reports import *
from app.tasks.scraping import *

# Cualquier tarea que aún no se ha migrado a los módulos específicos
# debería ser importada directamente desde app.tasks
# Esta sección se eliminará cuando todas las tareas se hayan migrado

# Ejemplo:
# from app.tasks import legacy_task

# Lista de todas las tareas disponibles
__all__ = [
    # Tareas básicas
    'with_retry', 'add',
    
    # Tareas de Chatbot
    'process_message', 'analyze_intent', 'generate_response', 'retry_failed_messages',
    
    # Tareas de ML
    'update_embeddings', 'process_matching', 'train_model', 'train_ml_task',
    'ejecutar_ml', 'train_matchmaking_model_task', 'predict_top_candidates_task',
    
    # Tareas de Pagos
    'process_payment_webhook', 'send_payment_reminder', 'update_payment_status',
    
    # Tareas de Notificaciones
    'send_notification', 'aggregate_notifications', 'send_whatsapp_message_task',
    'send_telegram_message_task', 'send_messenger_message_task', 'send_linkedin_login_link',
    'send_ntfy_notification',
    
    # Tareas de Onboarding
    'process_client_feedback_task', 'update_client_metrics_task', 
    'generate_client_feedback_reports_task', 'process_onboarding_ml_data_task',
    'generate_employee_satisfaction_reports_task',
    
    # Tareas de Scraping
    'ejecutar_scraping', 'retrain_ml_scraper', 'verificar_dominios_scraping',
    'procesar_scraping_dominio', 'procesar_sublinks_task', 'execute_ml_and_scraping',
    'execute_email_scraper', 'process_cv_emails_task',
    
    # Tareas de Reportes
    'generate_weekly_report_task', 'generate_scraping_efficiency_report_task',
    'generate_conversion_funnel_report_task'
]
