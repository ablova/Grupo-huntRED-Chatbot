from django.db import migrations
import re

def update_imports(apps, schema_editor):
    """
    Actualiza las referencias de importación en los archivos Python
    """
    # Patrones de búsqueda y reemplazo
    patterns = [
        (
            r'from app\.ats\.chatbot\.integrations\.services import',
            'from app.ats.integrations.services import'
        ),
        (
            r'from app\.ats\.publish\.integrations import',
            'from app.ats.integrations.services import'
        ),
        (
            r'from app\.ats\.publish\.integrations\.base_integration import',
            'from app.ats.integrations.services import'
        )
    ]

    # Archivos a actualizar
    files_to_update = [
        'app/ats/chatbot/core/chatbot.py',
        'app/ats/chatbot/core/gpt.py',
        'app/ats/chatbot/core/intents_handler.py',
        'app/ats/chatbot/components/chat_state_manager.py',
        'app/ats/chatbot/workflow/business_units/amigro/amigro.py',
        'app/ats/chatbot/workflow/business_units/huntred/huntred.py',
        'app/ats/chatbot/workflow/business_units/huntred_executive.py',
        'app/ats/chatbot/workflow/business_units/huntu/huntu.py',
        'app/ats/chatbot/workflow/business_units/sexsi/sexsi.py',
        'app/ats/chatbot/workflow/common/common.py',
        'app/ats/chatbot/workflow/common/jobs/jobs.py',
        'app/ats/publish/integrations/linkedin.py',
        'app/ats/publish/integrations/whatsapp.py',
        'app/ats/publish/integrations/telegram.py',
        'app/ats/publish/integrations/slack.py',
        'app/ats/publish/integrations/instagram.py',
        'app/ats/publish/integrations/email.py',
        'app/ats/publish/import_config.py'
    ]

    for file_path in files_to_update:
        try:
            with open(file_path, 'r') as file:
                content = file.read()

            # Aplicar cada patrón de reemplazo
            for pattern, replacement in patterns:
                content = re.sub(pattern, replacement, content)

            with open(file_path, 'w') as file:
                file.write(content)

        except FileNotFoundError:
            print(f"Archivo no encontrado: {file_path}")
        except Exception as e:
            print(f"Error actualizando {file_path}: {str(e)}")

def reverse_imports(apps, schema_editor):
    """
    Revierte los cambios en las referencias de importación
    """
    # Patrones de búsqueda y reemplazo (invertidos)
    patterns = [
        (
            r'from app\.ats\.integrations\.services import',
            'from app.ats.integrations.services import'
        )
    ]

    # Archivos a revertir
    files_to_update = [
        'app/ats/chatbot/core/chatbot.py',
        'app/ats/chatbot/core/gpt.py',
        'app/ats/chatbot/core/intents_handler.py',
        'app/ats/chatbot/components/chat_state_manager.py',
        'app/ats/chatbot/workflow/business_units/amigro/amigro.py',
        'app/ats/chatbot/workflow/business_units/huntred/huntred.py',
        'app/ats/chatbot/workflow/business_units/huntred_executive.py',
        'app/ats/chatbot/workflow/business_units/huntu/huntu.py',
        'app/ats/chatbot/workflow/business_units/sexsi/sexsi.py',
        'app/ats/chatbot/workflow/common/common.py',
        'app/ats/chatbot/workflow/common/jobs/jobs.py',
        'app/ats/publish/integrations/linkedin.py',
        'app/ats/publish/integrations/whatsapp.py',
        'app/ats/publish/integrations/telegram.py',
        'app/ats/publish/integrations/slack.py',
        'app/ats/publish/integrations/instagram.py',
        'app/ats/publish/integrations/email.py',
        'app/ats/publish/import_config.py'
    ]

    for file_path in files_to_update:
        try:
            with open(file_path, 'r') as file:
                content = file.read()

            # Aplicar cada patrón de reemplazo
            for pattern, replacement in patterns:
                content = re.sub(pattern, replacement, content)

            with open(file_path, 'w') as file:
                file.write(content)

        except FileNotFoundError:
            print(f"Archivo no encontrado: {file_path}")
        except Exception as e:
            print(f"Error actualizando {file_path}: {str(e)}")

class Migration(migrations.Migration):
    dependencies = [
        ('integrations', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(update_imports, reverse_imports),
    ] 