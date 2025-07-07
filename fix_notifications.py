#!/usr/bin/env python3
"""
Script para aplicar el patrón MigrationHandler a todos los archivos de notificaciones.
Resuelve el problema del ciclo huevo-gallina en las migraciones de Django.
"""

import os
import re
import glob

def fix_notification_file(file_path):
    """Aplica el patrón MigrationHandler a un archivo de notificaciones."""
    print(f"Procesando: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Buscar líneas con inicializaciones globales
    pattern = r'(\w+_notifier)\s*=\s*(\w+NotificationService)\(BusinessUnit\.objects\.first\(\)\)'
    matches = re.findall(pattern, content)
    
    if not matches:
        print(f"  No se encontraron inicializaciones globales en {file_path}")
        return
    
    for notifier_name, service_name in matches:
        print(f"  Encontrado: {notifier_name} = {service_name}(BusinessUnit.objects.first())")
        
        # Eliminar la línea de inicialización global
        content = re.sub(
            rf'{notifier_name}\s*=\s*{service_name}\(BusinessUnit\.objects\.first\(\)\)',
            '',
            content
        )
        
        # Agregar el patrón MigrationHandler al final del archivo
        getter_code = f'''

# Instancia global del servicio de notificaciones
{notifier_name} = None

def get_{notifier_name}():
    global {notifier_name}
    if {notifier_name} is None:
        from app.models import BusinessUnit
        bu = BusinessUnit.objects.first()
        {notifier_name} = {service_name}(bu)
    return {notifier_name}
'''
        content += getter_code
    
    # Escribir el archivo corregido
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"  ✅ Corregido: {file_path}")

def main():
    """Función principal."""
    # Lista de archivos a procesar (basada en el resultado del find)
    notification_files = [
        "app/ats/integrations/notifications/google_chat_service_notifications.py",
        "app/ats/integrations/notifications/database_notifications.py",
        "app/ats/integrations/notifications/discord_service_notifications.py",
        "app/ats/integrations/notifications/api_notifications.py",
        "app/ats/integrations/notifications/placement_notifications.py",
        "app/ats/integrations/notifications/sms_service_notifications.py",
        "app/ats/integrations/notifications/whatsapp_service_notifications.py",
        "app/ats/integrations/notifications/process_notifications.py",
        "app/ats/integrations/notifications/email_service_notifications.py",
        "app/ats/integrations/notifications/system_notifications.py",
        "app/ats/integrations/notifications/performance_notifications.py",
        "app/ats/integrations/notifications/security_notifications.py",
        "app/ats/integrations/notifications/event_notifications.py",
        "app/ats/integrations/notifications/user_notifications.py",
        "app/ats/integrations/notifications/telegram_service_notifications.py",
        "app/ats/integrations/notifications/teams_service_notifications.py",
        "app/ats/integrations/notifications/queue_notifications.py",
        "app/ats/integrations/notifications/application_notifications.py",
        "app/ats/integrations/notifications/integration_notifications.py",
        "app/ats/integrations/notifications/maintenance_notifications.py",
        "app/ats/integrations/notifications/slack_service_notifications.py",
        "app/ats/integrations/notifications/web_service_notifications.py",
        "app/ats/integrations/notifications/payment_notifications.py",
        "app/ats/integrations/notifications/cache_notifications.py",
        "app/ats/integrations/notifications/metrics_notifications.py",
    ]
    
    print("🔧 Aplicando patrón MigrationHandler a archivos de notificaciones...")
    
    for file_path in notification_files:
        if os.path.exists(file_path):
            fix_notification_file(file_path)
        else:
            print(f"⚠️  Archivo no encontrado: {file_path}")
    
    print("\n✅ Proceso completado!")

if __name__ == "__main__":
    main() 