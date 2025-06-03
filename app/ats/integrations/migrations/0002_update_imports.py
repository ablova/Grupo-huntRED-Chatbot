"""
Migración para actualizar las importaciones de los módulos de integración
"""

import re
from django.db import migrations

def update_imports(apps, schema_editor):
    """
    Actualiza las importaciones en los archivos
    """
    # Patrones de búsqueda y reemplazo
    patterns = [
        # Servicios
        (
            r'from app\.ats\.chatbot\.integrations\.services import (.*)',
            r'from app.ats.integrations.services import \1'
        ),
        # Handlers
        (
            r'from app\.ats\.chatbot\.integrations\.(whatsapp|telegram|instagram|messenger|slack) import (.*)',
            r'from app.ats.integrations.handlers.\1 import \2'
        ),
        # Webhooks
        (
            r'from app\.ats\.chatbot\.integrations\.(whatsapp|telegram|instagram|messenger|slack)_webhook import (.*)',
            r'from app.ats.integrations.webhooks.\1 import \2'
        ),
        # Menú
        (
            r'from app\.ats\.chatbot\.integrations\.menu import (.*)',
            r'from app.ats.integrations.menu import \1'
        ),
        # Utils
        (
            r'from app\.ats\.chatbot\.integrations\.utils import (.*)',
            r'from app.ats.integrations.utils import \1'
        )
    ]
    
    # Lista de archivos a actualizar
    files_to_update = [
        'app/ats/chatbot/workflow/common/jobs/jobs.py',
        'app/ats/chatbot/workflow/business_units/huntu/huntu.py',
        'app/ats/chatbot/workflow/business_units/sexsi/sexsi.py',
        'app/ats/chatbot/workflow/business_units/huntred/huntred.py',
        'app/ats/chatbot/workflow/business_units/amigro/amigro.py',
        'app/ats/chatbot/workflow/common/common.py',
        'app/ats/chatbot/workflow/business_units/huntred_executive.py',
        'app/ats/chatbot/components/chat_state_manager.py',
        'app/ats/chatbot/middleware/notification_handler.py',
        'app/ats/chatbot/core/intents_handler.py',
        'app/ats/chatbot/core/gpt.py',
        'app/ats/chatbot/core/chatbot.py',
        'app/ats/views/proposals/views.py',
        'app/ats/views/main_views.py',
        'app/ats/views/chatbot_views.py',
        'app/ats/views/util_views.py',
        'app/ats/views/webhook_views.py',
        'app/ats/views/chatbot/views.py',
        'app/ats/sexsi/views.py',
        'app/ats/kanban/views.py',
        'app/ats/sexsi/tasks.py',
        'app/ats/admin.py'
    ]
    
    for file_path in files_to_update:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Aplicar cada patrón
            for pattern, replacement in patterns:
                content = re.sub(pattern, replacement, content)
                
            # Guardar los cambios
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
        except Exception as e:
            print(f"Error actualizando {file_path}: {str(e)}")

def reverse_imports(apps, schema_editor):
    """
    Revierte los cambios en las importaciones
    """
    # Patrones de búsqueda y reemplazo (inversos)
    patterns = [
        # Servicios
        (
            r'from app\.ats\.integrations\.services import (.*)',
            r'from app.ats.chatbot.integrations.services import \1'
        ),
        # Handlers
        (
            r'from app\.ats\.integrations\.handlers\.(whatsapp|telegram|instagram|messenger|slack) import (.*)',
            r'from app.ats.chatbot.integrations.\1 import \2'
        ),
        # Webhooks
        (
            r'from app\.ats\.integrations\.webhooks\.(whatsapp|telegram|instagram|messenger|slack) import (.*)',
            r'from app.ats.chatbot.integrations.\1_webhook import \2'
        ),
        # Menú
        (
            r'from app\.ats\.integrations\.menu import (.*)',
            r'from app.ats.chatbot.integrations.menu import \1'
        ),
        # Utils
        (
            r'from app\.ats\.integrations\.utils import (.*)',
            r'from app.ats.chatbot.integrations.utils import \1'
        )
    ]
    
    # Lista de archivos a actualizar
    files_to_update = [
        'app/ats/chatbot/workflow/common/jobs/jobs.py',
        'app/ats/chatbot/workflow/business_units/huntu/huntu.py',
        'app/ats/chatbot/workflow/business_units/sexsi/sexsi.py',
        'app/ats/chatbot/workflow/business_units/huntred/huntred.py',
        'app/ats/chatbot/workflow/business_units/amigro/amigro.py',
        'app/ats/chatbot/workflow/common/common.py',
        'app/ats/chatbot/workflow/business_units/huntred_executive.py',
        'app/ats/chatbot/components/chat_state_manager.py',
        'app/ats/chatbot/middleware/notification_handler.py',
        'app/ats/chatbot/core/intents_handler.py',
        'app/ats/chatbot/core/gpt.py',
        'app/ats/chatbot/core/chatbot.py',
        'app/ats/views/proposals/views.py',
        'app/ats/views/main_views.py',
        'app/ats/views/chatbot_views.py',
        'app/ats/views/util_views.py',
        'app/ats/views/webhook_views.py',
        'app/ats/views/chatbot/views.py',
        'app/ats/sexsi/views.py',
        'app/ats/kanban/views.py',
        'app/ats/sexsi/tasks.py',
        'app/ats/admin.py'
    ]
    
    for file_path in files_to_update:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Aplicar cada patrón
            for pattern, replacement in patterns:
                content = re.sub(pattern, replacement, content)
                
            # Guardar los cambios
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
        except Exception as e:
            print(f"Error actualizando {file_path}: {str(e)}")

class Migration(migrations.Migration):
    dependencies = [
        ('integrations', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(update_imports, reverse_imports),
    ] 