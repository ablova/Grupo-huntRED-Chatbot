# huntRED® v2 - Task System
"""
Complete task system for huntRED® v2 with Celery integration
Migrated from original system for full functionality
"""

from .base import with_retry, task_logger
from .notifications import *
from .ml import *
from .scraping import *
from .onboarding import *
from .reports import *
from .maintenance import *
from .messaging import *

__all__ = [
    # Base utilities
    'with_retry', 'task_logger',
    
    # Notification tasks
    'send_whatsapp_message_task', 'send_telegram_message_task', 
    'send_messenger_message_task', 'send_email_task',
    'send_ntfy_notification_task', 'optimize_communication_task',
    
    # ML/AI tasks
    'train_ml_task', 'train_matchmaking_model_task', 
    'predict_top_candidates_task', 'retrain_ml_scraper',
    'analyze_social_profiles_task', 'process_cv_analysis_task',
    
    # Scraping tasks
    'ejecutar_scraping', 'procesar_scraping_dominio',
    'verificar_dominios_scraping', 'execute_email_scraper',
    'process_cv_emails_task', 'procesar_sublinks_task',
    
    # Payroll tasks
    'calculate_payroll_task', 'process_bulk_payroll_task',
    'generate_payslips_task', 'send_payroll_notifications_task',
    
    # Onboarding tasks
    'process_client_feedback_task', 'update_client_metrics_task',
    'generate_client_feedback_reports_task', 'process_onboarding_ml_data_task',
    
    # Report tasks
    'generate_weekly_report_task', 'generate_conversion_funnel_report_task',
    'generate_scraping_efficiency_report_task', 'generate_payroll_reports_task',
    
    # Maintenance tasks
    'cleanup_old_logs', 'cleanup_temp_files', 'cleanup_old_cache',
    'run_maintenance_tasks', 'backup_database_task',
    
    # Messaging tasks
    'process_whatsapp_webhook_task', 'process_telegram_webhook_task',
    'update_conversation_state_task', 'analyze_message_sentiment_task',
]